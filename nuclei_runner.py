import subprocess
import logging
import json
import requests
import os
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from adaptive_rate_limiter import create_adaptive_limiter

logger = logging.getLogger(__name__)

class NucleiRunner:
    def __init__(self):
        # Pointing directly to the AI port discovered via your ss/lsof commands
        self.ai_url = os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/api/generate")
        self.model_name = os.getenv("OLLAMA_MODEL", "mistral:latest")
        self.error_threshold = 5
        
        # Progress tracking
        self.templates_loaded = 0
        self.requests_sent = 0
        self.requests_total = 0
        self.vulnerabilities_found = 0
        self.start_time = None
        self.rps = 0
        self.eta_seconds = 0
        self.current_template = ""
        self.is_scanning = False
        self.adaptive_limiter = None

    def ask_ai_for_evasion(self):
        """Reaches out to the local LLM to generate WAF bypass rate-limiting flags."""
        
        # Quick connectivity check (1 second timeout)
        try:
            logger.info("[NUCLEI DIAGNOSTIC] Testing AI engine connectivity...")
            test_response = requests.get(f"{self.ai_url.replace('/api/generate', '/api/tags')}", timeout=1)
            if test_response.status_code != 200:
                logger.warning("[NUCLEI DIAGNOSTIC] AI engine not responding properly. Using fallback evasion.")
                return "FALLBACK: -rl 5 -c 2"
        except requests.exceptions.RequestException as e:
            logger.warning(f"[NUCLEI DIAGNOSTIC] AI engine unreachable: {e}. Using fallback.")
            return "FALLBACK: -rl 5 -c 2"
        
        prompt = """
        You are an expert red team AI. The target WAF is blocking our Nuclei scan. 
        We need to slow down the scan to emulate human traffic.
        Reply ONLY with the exact Nuclei flags to set rate limiting to 5 and concurrency to 2.
        DO NOT output any explanation, markdown, or other text. 
        Format exactly like this: -rl 5 -c 2
        """
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        
        try:
            logging.info("🧠 Waking up AI Agent for Authorized Evasion Tactics...")
            logger.info("[NUCLEI DIAGNOSTIC] Sending AI request with 30s timeout...")
            # Reduced timeout from 300s to 30s
            response = requests.post(self.ai_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                ai_response = response.json().get("response", "").strip()
                logging.info(f"🤖 AI Brain Optimization Acquired: {ai_response}")
                
                # --- THE GUARDRAIL ---
                # If the AI hallucinates bad syntax, force the override to save the pipeline
                if "-rl" not in ai_response or "-c" not in ai_response:
                    logging.warning("⚠️ AI hallucinated bad flags. Forcing strict override.")
                    return "-rl 5 -c 2"
                
                return ai_response
            else:
                logging.error(f"AI API Error: {response.status_code}")
                return "-rl 5 -c 2"
                
        except requests.exceptions.Timeout:
            logger.warning("[NUCLEI DIAGNOSTIC] AI request timed out after 30s. Using fallback.")
            logging.info("🛡️ Using hardcoded fallback polite tactics...")
            return "-rl 5 -c 2"
        except Exception as e:
            logging.error(f"AI Brain offline or error: {e}")
            logger.warning(f"[NUCLEI DIAGNOSTIC] AI error: {type(e).__name__}")
            logging.info("🛡️ Using hardcoded fallback polite tactics...")
            return "-rl 5 -c 2"

    def _parse_progress(self, line):
        """Parse Nuclei stderr for progress information."""
        line = line.strip()
        if not line:
            return

        # Newer nuclei -stats emits JSON lines on stderr
        if line.startswith("{") and line.endswith("}"):
            try:
                stats = json.loads(line)
                if isinstance(stats, dict):
                    if "requests" in stats:
                        self.requests_sent = max(self.requests_sent, int(stats.get("requests", 0)))
                    if "total" in stats:
                        self.requests_total = max(self.requests_total, int(stats.get("total", 0)))
                    if "templates" in stats:
                        self.templates_loaded = max(self.templates_loaded, int(stats.get("templates", 0)))
                    if "matched" in stats:
                        self.vulnerabilities_found = max(
                            self.vulnerabilities_found,
                            int(stats.get("matched", 0)),
                        )
                    return
            except (ValueError, TypeError):
                pass

        # Extract templates loaded: [INF] Templates loaded for scan: 2543
        if 'Templates loaded' in line or 'templates loaded' in line:
            if match := re.search(r'(\d+)', line):
                self.templates_loaded = int(match.group(1))
                if self.templates_loaded > 0 and len(self.target_urls) > 0:
                    self.requests_total = self.templates_loaded * len(self.target_urls)
        
        # Extract current template being executed
        if 'Executing' in line and 'template' in line.lower():
            # Try to extract template name
            parts = line.split('/')
            if len(parts) > 0:
                self.current_template = parts[-1].strip()[:50]
        
        # Count executed templates (each line with template ID)
        if '[' in line and ']' in line and ('http' in line.lower() or 'matched' in line.lower()):
            self.requests_sent += 1
    
    def _calculate_metrics(self):
        """Calculate RPS and ETA."""
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        
        # If we have actual request counts, use them
        if self.requests_sent > 0 and elapsed > 0:
            self.rps = self.requests_sent / elapsed
        elif elapsed > 10:
            # Fallback: estimate based on typical Nuclei speed (50-150 req/s)
            # Use conservative estimate
            estimated_rps = 80
            estimated_sent = int(elapsed * estimated_rps)
            self.requests_sent = min(estimated_sent, self.requests_total)
            self.rps = estimated_rps
        
        if self.rps > 0 and self.requests_total > 0:
            remaining = self.requests_total - self.requests_sent
            self.eta_seconds = remaining / self.rps
        elif self.requests_total > 0 and elapsed > 0:
            # Fallback ETA calculation
            avg_time_per_template = 0.1  # 100ms per template average
            self.eta_seconds = self.requests_total * avg_time_per_template
    
    def get_progress_stats(self):
        """Return current progress statistics."""
        return {
            'templates_loaded': self.templates_loaded,
            'requests_sent': self.requests_sent,
            'requests_total': self.requests_total,
            'vulnerabilities': self.vulnerabilities_found,
            'rps': round(self.rps, 2),
            'eta_seconds': int(self.eta_seconds),
            'current_template': self.current_template,
            'is_scanning': self.is_scanning,
            'elapsed': int(time.time() - self.start_time) if self.start_time else 0,
            'target_urls': self.target_urls if hasattr(self, 'target_urls') else []
        }

    def _split_target_chunks(self, target_urls, chunk_count):
        if not target_urls:
            return []
        bounded_chunks = max(1, min(int(chunk_count), len(target_urls)))
        buckets = [[] for _ in range(bounded_chunks)]
        for index, url in enumerate(target_urls):
            buckets[index % bounded_chunks].append(url)
        return [bucket for bucket in buckets if bucket]

    def _recommend_adaptive_workers(self, chunk_count, total_targets):
        max_workers = max(1, int(os.getenv("TRISHUL_NUCLEI_MAX_WORKERS", "5")))
        max_allowed = max(1, min(chunk_count, max_workers))

        cpu_count = os.cpu_count() or 2
        load_avg = 0.0
        if hasattr(os, "getloadavg"):
            try:
                load_avg = float(os.getloadavg()[0])
            except OSError:
                load_avg = 0.0

        # Local heuristic baseline when AI is unavailable.
        if cpu_count > 0 and load_avg / cpu_count >= 0.9:
            heuristic = 1
        elif total_targets >= 220:
            heuristic = min(4, max_allowed)
        elif total_targets >= 120:
            heuristic = min(3, max_allowed)
        elif total_targets >= 60:
            heuristic = min(2, max_allowed)
        else:
            heuristic = 1

        prompt = (
            "Decide chunk worker count for nuclei scan.\n"
            "Return ONLY one integer.\n"
            f"Chunks: {chunk_count}\n"
            f"Targets: {total_targets}\n"
            f"CPU cores: {cpu_count}\n"
            f"Load average: {load_avg:.2f}\n"
            f"Max allowed workers: {max_allowed}\n"
            "Prefer stability when uncertain."
        )
        ai_text = None
        if self.model_name and self.ai_url:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "system": "Output only a single integer.",
                "options": {
                    "temperature": 0.0,
                    "num_predict": 6,
                },
            }
            try:
                response = requests.post(self.ai_url, json=payload, timeout=8)
                if response.status_code == 200:
                    ai_text = response.json().get("response", "").strip()
            except requests.RequestException:
                ai_text = None
        if ai_text:
            match = re.search(r"\d+", ai_text)
            if match:
                ai_workers = int(match.group(0))
                if ai_workers >= 1:
                    return min(max_allowed, ai_workers)

        return max(1, heuristic)

    def _select_chunk_workers(self, mode, chunk_count, total_targets):
        max_workers = max(1, int(os.getenv("TRISHUL_NUCLEI_MAX_WORKERS", "5")))
        max_allowed = max(1, min(chunk_count, max_workers))
        mode_normalized = (mode or "adaptive").strip().lower()
        if mode_normalized == "sequential":
            return 1
        if mode_normalized == "parallel":
            return max_allowed
        return self._recommend_adaptive_workers(chunk_count, total_targets)

    def _run_chunked_scan(self, target_urls, cookie=None, progress_callback=None, chunk_mode="adaptive", chunk_count=4):
        chunks = self._split_target_chunks(target_urls, chunk_count)
        if len(chunks) <= 1:
            return self.run_scan(
                target_urls,
                cookie=cookie,
                progress_callback=progress_callback,
                disable_chunking=True,
                file_suffix="single",
            )

        workers = self._select_chunk_workers(chunk_mode, len(chunks), len(target_urls))
        logger.info(
            "[NUCLEI CHUNK] Starting chunked scan mode=%s chunks=%s workers=%s targets=%s",
            chunk_mode,
            len(chunks),
            workers,
            len(target_urls),
        )

        self.target_urls = target_urls
        self.start_time = time.time()
        self.is_scanning = True
        self.templates_loaded = 0
        self.requests_sent = 0
        self.requests_total = 0
        self.vulnerabilities_found = 0
        self.current_template = ""

        aggregate_lock = threading.Lock()
        chunk_stats = {
            index: {
                "status": "pending",
                "requests_sent": 0,
                "requests_total": 0,
                "vulnerabilities": 0,
                "current_template": "",
                "target_count": len(chunk),
                "last_update": time.time(),
            }
            for index, chunk in enumerate(chunks)
        }
        findings_by_chunk = {index: [] for index in range(len(chunks))}

        def emit_progress():
            if not progress_callback:
                return
            with aggregate_lock:
                total_sent = sum(int(item["requests_sent"]) for item in chunk_stats.values())
                total_total = sum(int(item["requests_total"]) for item in chunk_stats.values())
                total_vulns = sum(int(item["vulnerabilities"]) for item in chunk_stats.values())
                templates_loaded = sum(
                    int(item["requests_total"] / item["target_count"])
                    for item in chunk_stats.values()
                    if int(item["target_count"]) > 0 and int(item["requests_total"]) > 0
                )
                completed_chunks = sum(1 for item in chunk_stats.values() if item["status"] == "completed")
                active_chunks = sum(1 for item in chunk_stats.values() if item["status"] == "running")
                current_templates = [str(item["current_template"]) for item in chunk_stats.values() if item["current_template"]]

                self.requests_sent = total_sent
                self.requests_total = total_total
                self.vulnerabilities_found = total_vulns
                self.templates_loaded = templates_loaded
                self.current_template = current_templates[0] if current_templates else ""
                self._calculate_metrics()

                aggregate_stats = self.get_progress_stats()
                aggregate_stats.update(
                    {
                        "chunk_mode": chunk_mode,
                        "total_chunks": len(chunks),
                        "completed_chunks": completed_chunks,
                        "active_chunks": active_chunks,
                        "workers": workers,
                        "chunk_statuses": {
                            str(idx): {
                                "status": item["status"],
                                "requests_sent": item["requests_sent"],
                                "requests_total": item["requests_total"],
                                "vulnerabilities": item["vulnerabilities"],
                                "target_count": item["target_count"],
                            }
                            for idx, item in chunk_stats.items()
                        },
                    }
                )
            progress_callback(aggregate_stats)

        def run_single_chunk(index, urls):
            runner = NucleiRunner()
            runner.error_threshold = self.error_threshold
            with aggregate_lock:
                chunk_stats[index]["status"] = "running"
                chunk_stats[index]["last_update"] = time.time()
            emit_progress()

            def chunk_progress(stats):
                with aggregate_lock:
                    chunk_stats[index]["status"] = "running"
                    chunk_stats[index]["requests_sent"] = int(stats.get("requests_sent", 0))
                    chunk_stats[index]["requests_total"] = int(stats.get("requests_total", 0))
                    chunk_stats[index]["vulnerabilities"] = int(stats.get("vulnerabilities", 0))
                    chunk_stats[index]["current_template"] = str(stats.get("current_template", ""))
                    chunk_stats[index]["last_update"] = time.time()
                emit_progress()

            results = runner.run_scan(
                urls,
                cookie=cookie,
                progress_callback=chunk_progress,
                disable_chunking=True,
                file_suffix=f"chunk_{index}",
            )
            with aggregate_lock:
                chunk_stats[index]["status"] = "completed"
                chunk_stats[index]["requests_sent"] = max(
                    chunk_stats[index]["requests_sent"],
                    int(runner.requests_sent),
                )
                chunk_stats[index]["requests_total"] = max(
                    chunk_stats[index]["requests_total"],
                    int(runner.requests_total),
                )
                chunk_stats[index]["vulnerabilities"] = len(results)
                chunk_stats[index]["last_update"] = time.time()
                findings_by_chunk[index] = results
            emit_progress()

        try:
            if workers <= 1:
                for chunk_index, chunk_urls in enumerate(chunks):
                    run_single_chunk(chunk_index, chunk_urls)
            else:
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = {
                        executor.submit(run_single_chunk, chunk_index, chunk_urls): chunk_index
                        for chunk_index, chunk_urls in enumerate(chunks)
                    }
                    for future in as_completed(futures):
                        chunk_index = futures[future]
                        try:
                            future.result()
                        except Exception as exc:
                            logger.error("[NUCLEI CHUNK] Chunk %s failed: %s", chunk_index, exc)
                            with aggregate_lock:
                                chunk_stats[chunk_index]["status"] = "failed"
                                chunk_stats[chunk_index]["last_update"] = time.time()
                            emit_progress()
                            raise
        finally:
            self.is_scanning = False
            emit_progress()

        all_findings = []
        for chunk_index in sorted(findings_by_chunk.keys()):
            all_findings.extend(findings_by_chunk[chunk_index])
        # Preserve deterministic order while dropping duplicate lines.
        all_findings = list(dict.fromkeys(all_findings))
        self.vulnerabilities_found = len(all_findings)
        return all_findings

    def run_scan(self, target_urls, cookie=None, progress_callback=None, disable_chunking=False, file_suffix=""):
        """
        Run Nuclei scan with real-time progress tracking.
        
        Args:
            target_urls: List of URLs to scan
            cookie: Optional cookie header
            progress_callback: Function to call with progress updates (receives stats dict)
        """
        chunk_mode = os.getenv("TRISHUL_NUCLEI_CHUNK_MODE", "adaptive").strip().lower()
        if chunk_mode not in {"single", "sequential", "parallel", "adaptive"}:
            chunk_mode = "adaptive"
        try:
            chunk_count = int(os.getenv("TRISHUL_NUCLEI_CHUNK_COUNT", "4"))
        except ValueError:
            chunk_count = 4
        chunk_count = max(2, min(chunk_count, 8))

        if not disable_chunking and chunk_mode != "single" and len(target_urls) >= chunk_count * 2:
            return self._run_chunked_scan(
                target_urls=target_urls,
                cookie=cookie,
                progress_callback=progress_callback,
                chunk_mode=chunk_mode,
                chunk_count=chunk_count,
            )

        self.target_urls = target_urls
        self.start_time = time.time()
        self.is_scanning = True
        self.templates_loaded = 0
        self.requests_sent = 0
        self.requests_total = 0
        self.vulnerabilities_found = 0
        self.current_template = ""

        safe_suffix = ""
        if file_suffix:
            safe_suffix = "_" + re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(file_suffix))
        target_file = f"live_targets{safe_suffix}.txt"
        output_file = f"nuclei_results{safe_suffix}.json"
        
        logger.info(f"[NUCLEI DIAGNOSTIC] Writing {len(target_urls)} URLs to {target_file}")
        # Use buffered writing for large URL lists
        with open(target_file, "w", buffering=8192) as f:
            f.writelines(f"{url}\n" for url in target_urls)
        
        file_size = os.path.getsize(target_file)
        logger.info(f"[NUCLEI DIAGNOSTIC] Target file written: {file_size} bytes")
        
        # --- PHASE 1: PRIMARY SCAN WITH ADAPTIVE RATE LIMITING ---
        base_cmd = ["nuclei", "-l", target_file, "-j", "-o", output_file, "-stats", "-silent"]
        scan_profile = os.getenv("TRISHUL_SCAN_PROFILE", "default").strip().lower()
        
        # Initialize adaptive rate limiter based on profile
        use_adaptive = os.getenv("TRISHUL_ADAPTIVE_RATE", "true").lower() == "true"
        
        if use_adaptive:
            # NEW: Adaptive rate limiting (safe + fast)
            logger.info("🎯 Enabling adaptive rate limiting (safe + fast mode)")
            
            if scan_profile in {"cdn-safe", "gentle", "safe"}:
                self.adaptive_limiter = create_adaptive_limiter("safe")
            elif scan_profile == "aggressive":
                self.adaptive_limiter = create_adaptive_limiter("aggressive")
            else:
                self.adaptive_limiter = create_adaptive_limiter("balanced")
            
            # Get initial rate from adaptive limiter
            rate_limit, concurrency = self.adaptive_limiter.get_nuclei_flags()
            base_cmd.extend(["-rl", rate_limit, "-c", concurrency, "-timeout", "10", "-retries", "1"])
            logger.info(
                f"[ADAPTIVE] Starting with {rate_limit} req/s, {concurrency} concurrency "
                f"(will auto-adjust based on server health)"
            )
        else:
            # OLD: Static rate limiting
            if scan_profile in {"cdn-safe", "gentle", "safe"}:
                base_cmd.extend(["-rl", "10", "-c", "8", "-timeout", "10", "-retries", "1"])
                logger.info("[NUCLEI DIAGNOSTIC] Using static CDN-safe profile (-rl 10 -c 8)")
            
        if cookie:
            # SECURITY: Strip newlines/carriage returns to prevent header injection
            safe_cookie = cookie.replace('\n', '').replace('\r', '').replace('\t', '')
            if safe_cookie != cookie:
                logging.warning("⚠️  Removed invalid characters from cookie")
            base_cmd.extend(["-H", f"Cookie: {safe_cookie}"])
            
        logging.info(f"🎯 Unleashing Sniper on {len(target_urls)} targets (Fast Mode)...")
        logging.info(f"📋 Expected total requests: {self.requests_total:,}")
        
        full_cmd = ' '.join(base_cmd)
        logger.info(f"[NUCLEI DIAGNOSTIC] Full command: {full_cmd}")
        
        # Read only stderr for stats/errors; drop stdout to avoid pipe backpressure deadlocks.
        logger.info("[NUCLEI DIAGNOSTIC] Starting Nuclei subprocess...")
        process = subprocess.Popen(
            base_cmd, 
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE, 
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        logger.info(f"[NUCLEI DIAGNOSTIC] Nuclei process started with PID: {process.pid}")
        
        error_count = 0
        waf_triggered = False
        
        # Monitor progress in separate thread (with adaptive rate updates)
        def monitor_progress():
            logger.info("[NUCLEI DIAGNOSTIC] Progress monitoring thread started")
            last_output_time = time.time()
            last_file_size = 0
            last_rate_update = time.time()
            
            while self.is_scanning and process.poll() is None:
                # Check for heartbeat via output file growth
                if os.path.exists(output_file):
                    current_size = os.path.getsize(output_file)
                    if current_size > last_file_size:
                        last_output_time = time.time()
                        last_file_size = current_size
                
                # Check if Nuclei has been silent for too long (5 minutes)
                silence_duration = time.time() - last_output_time
                if silence_duration > 300:  # 5 minutes
                    logger.warning(f"[NUCLEI DIAGNOSTIC] Nuclei silent for {int(silence_duration)}s, may be stuck")
                    # Don't kill immediately, just log warning
                    last_output_time = time.time()  # Reset to avoid spam
                
                self._calculate_metrics()
                
                # Update adaptive rate limiter status
                if self.adaptive_limiter and time.time() - last_rate_update > 10:
                    status = self.adaptive_limiter.get_status()
                    logger.info(
                        f"[ADAPTIVE] Rate: {status['current_rate']} req/s, "
                        f"AvgTime: {status['avg_response_time_ms']:.0f}ms, "
                        f"Success: {status['success_rate']:.1%}"
                    )
                    last_rate_update = time.time()
                
                if progress_callback:
                    progress_callback(self.get_progress_stats())
                time.sleep(0.5)  # Update twice per second
            logger.info("[NUCLEI DIAGNOSTIC] Progress monitoring thread stopped")
        
        progress_thread = threading.Thread(target=monitor_progress, daemon=True)
        progress_thread.start()
        logger.info("[NUCLEI DIAGNOSTIC] Progress thread started")
        
        # Read the terminal output in real-time to catch the WAF block
        logger.info("[NUCLEI DIAGNOSTIC] Starting to read Nuclei stderr output...")
        for line in process.stderr:
            # Parse progress information
            self._parse_progress(line)
            
            # Count vulnerabilities found
            if "[FOUND]" in line or "found" in line.lower() or "vulnerability" in line.lower():
                self.vulnerabilities_found += 1
            
            if "error" in line.lower() or "429" in line:
                error_count += 1
            
            # Log some lines for debugging (first 5)
            if self.requests_sent < 5:
                logging.debug(f"Nuclei: {line.strip()}")
            
            # The exact moment we hit the threshold, kill the fast scan
            if error_count >= self.error_threshold:
                logging.warning(f"🛑 WAF BLOCK DETECTED ({error_count} errors)! Halting attack...")
                process.terminate() 
                waf_triggered = True
                break
        
        logger.info("[NUCLEI DIAGNOSTIC] Finished reading stderr, waiting for process completion...")
        
        # Wait for process with timeout (2 hours max)
        try:
            logger.info("[NUCLEI DIAGNOSTIC] Calling process.wait() with 2-hour timeout...")
            exit_code = process.wait(timeout=7200)  # 2 hours = 7200 seconds
            logger.info(f"[NUCLEI DIAGNOSTIC] Nuclei process exited with code: {exit_code}")
        except subprocess.TimeoutExpired:
            logger.error("[NUCLEI DIAGNOSTIC] Nuclei scan exceeded 2-hour timeout! Terminating...")
            process.kill()
            process.wait()  # Clean up zombie process
            
            # Try to send stuck alert if gmail_notifier is available
            try:
                # Import here to avoid circular imports
                from gmail_notifier import get_notifier
                gmail_notifier = get_notifier()
                if gmail_notifier.enabled:
                    gmail_notifier.send_stuck_alert(
                        domain="target-domain",  # TODO: Pass domain parameter
                        phase_num=10,
                        phase_name="Vulnerability Scanning",
                        stuck_duration=7200
                    )
            except Exception as e:
                logger.error(f"Failed to send timeout alert: {e}")
            
            return []
        
        # Graceful degradation: Check if we got any results despite timeout/errors
        if waf_triggered and os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            if file_size > 0:
                logger.info("[NUCLEI DIAGNOSTIC] WAF triggered but partial results found, attempting to parse...")
                # Continue to parsing phase even after WAF trigger
        
        # --- PHASE 2: THE STEALTH COUNTER-ATTACK ---
        if waf_triggered:
            stealth_flags = self.ask_ai_for_evasion()
            logging.info(f"🥷 Initiating Stealth Counter-Attack...")
            
            # Reset progress for stealth mode
            self.requests_sent = 0
            self.start_time = time.time()
            
            # SECURITY: Validate AI response against whitelist to prevent command injection
            if re.match(r'^-[rc]l?\s+\d+(\s+-[rc]l?\s+\d+)*$', stealth_flags.strip()):
                stealth_args = stealth_flags.split()
            else:
                logging.warning(f"⚠️  AI returned invalid flags, using safe defaults: {stealth_flags}")
                stealth_args = ["-rl", "5", "-c", "2"]  # Safe fallback
            
            stealth_cmd = ["nuclei", "-l", target_file, "-j", "-o", output_file, "-stats"] + stealth_args
            
            if cookie:
                # SECURITY: Strip newlines/carriage returns to prevent header injection
                safe_cookie = cookie.replace('\n', '').replace('\r', '').replace('\t', '')
                if safe_cookie != cookie:
                    logging.warning("⚠️  Removed invalid characters from cookie")
                stealth_cmd.extend(["-H", f"Cookie: {safe_cookie}"])
            
            # Run with progress tracking
            stealth_process = subprocess.Popen(stealth_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
            
            for line in stealth_process.stderr:
                self._parse_progress(line)
                if "[FOUND]" in line or "found" in line.lower():
                    self.vulnerabilities_found += 1
            
            # Wait for stealth process with timeout
            logger.info("[NUCLEI DIAGNOSTIC] Starting stealth mode process.wait()...")
            try:
                exit_code = stealth_process.wait(timeout=3600)  # 1 hour for stealth
                logger.info(f"[NUCLEI DIAGNOSTIC] Stealth process exited with code: {exit_code}")
            except subprocess.TimeoutExpired:
                logger.error("[NUCLEI DIAGNOSTIC] Stealth scan timed out after 1 hour!")
                stealth_process.kill()
                stealth_process.wait()
                # Graceful degradation: Try to parse any partial results
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    logger.info("[NUCLEI DIAGNOSTIC] Stealth timed out but found partial results, attempting parse...")
                else:
                    return []
        
        self.is_scanning = False
        
        # --- PHASE 3: PARSING THE LOOT ---
        logger.info("[NUCLEI DIAGNOSTIC] Starting vulnerability parsing phase...")
        vulnerabilities = []
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            logger.info(f"[NUCLEI DIAGNOSTIC] Results file exists: {output_file} ({file_size} bytes)")
            
            if file_size > 50 * 1024 * 1024:  # 50MB threshold for large files
                logger.warning(f"[NUCLEI DIAGNOSTIC] Large results file detected ({file_size} bytes), using memory-efficient parsing")
                line_count = 0
                with open(output_file, "r") as f:
                    for line in f:
                        line_count += 1
                        if line_count > 10000:  # Memory limit
                            logger.warning("[NUCLEI DIAGNOSTIC] Line limit exceeded (10k), truncating results")
                            break
                        try:
                            # Validate JSON before adding
                            vuln_data = json.loads(line.strip())
                            vulnerabilities.append(line.strip())
                        except json.JSONDecodeError:
                            continue
            else:
                # Regular parsing for smaller files
                logger.info("[NUCLEI DIAGNOSTIC] Using regular JSON parsing for small file")
                with open(output_file, "r") as f:
                    for line in f:
                        try:
                            vuln_data = json.loads(line.strip())
                            # Return raw JSON string for downstream parsers
                            vulnerabilities.append(line.strip())
                        except json.JSONDecodeError:
                            continue
        else:
            logger.warning(f"[NUCLEI DIAGNOSTIC] Results file not found: {output_file}")
        
        logger.info(f"[NUCLEI DIAGNOSTIC] Parsing complete. Found {len(vulnerabilities)} vulnerabilities")
        
        self.vulnerabilities_found = len(vulnerabilities)
        if progress_callback:
            progress_callback(self.get_progress_stats())
        
        if 'waf_triggered' in locals() and waf_triggered:
            logger.info("[NUCLEI DIAGNOSTIC] Returning partial results due to WAF detection")

        # Backward-compatible return contract for callers in main.py
        return vulnerabilities
