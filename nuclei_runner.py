import subprocess
import logging
import json
import requests
import os
import time
import re
import threading

class NucleiRunner:
    def __init__(self):
        # Pointing directly to the AI port discovered via your ss/lsof commands
        self.ai_url = "http://127.0.0.1:11434/api/generate"
        self.model_name = "xploiter/bugbounty-ai" 
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

    def ask_ai_for_evasion(self):
        """Reaches out to the local LLM to generate WAF bypass rate-limiting flags."""
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
            # 300 second timeout to account for heavy CPU/Memory load
            response = requests.post(self.ai_url, json=payload, timeout=300)
            
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
                
        except Exception as e:
            logging.error(f"AI Brain offline or timed out: {e}")
            logging.info("🛡️ Using hardcoded fallback polite tactics...")
            return "-rl 5 -c 2"

    def _parse_progress(self, line):
        """Parse Nuclei stderr for progress information."""
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

    def run_scan(self, target_urls, cookie=None, progress_callback=None):
        """
        Run Nuclei scan with real-time progress tracking.
        
        Args:
            target_urls: List of URLs to scan
            cookie: Optional cookie header
            progress_callback: Function to call with progress updates (receives stats dict)
        """
        self.target_urls = target_urls
        self.start_time = time.time()
        self.is_scanning = True
        self.vulnerabilities_found = 0
        
        target_file = "live_targets.txt"
        output_file = "nuclei_results.json"
        
        with open(target_file, "w") as f:
            for url in target_urls:
                f.write(url + "\n")
        
        # --- PHASE 1: THE LOUD SCAN ---
        base_cmd = ["nuclei", "-l", target_file, "-j", "-o", output_file, "-stats", "-silent"]
        if cookie:
            # SECURITY: Strip newlines/carriage returns to prevent header injection
            safe_cookie = cookie.replace('\n', '').replace('\r', '').replace('\t', '')
            if safe_cookie != cookie:
                logging.warning("⚠️  Removed invalid characters from cookie")
            base_cmd.extend(["-H", f"Cookie: {safe_cookie}"])
            
        logging.info(f"🎯 Unleashing Sniper on {len(target_urls)} targets (Fast Mode)...")
        logging.info(f"📋 Expected total requests: {self.requests_total:,}")
        
        # Run with both stdout and stderr captured
        process = subprocess.Popen(
            base_cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        error_count = 0
        waf_triggered = False
        
        # Monitor progress in separate thread
        def monitor_progress():
            while self.is_scanning and process.poll() is None:
                self._calculate_metrics()
                if progress_callback:
                    progress_callback(self.get_progress_stats())
                time.sleep(0.5)  # Update twice per second
        
        progress_thread = threading.Thread(target=monitor_progress, daemon=True)
        progress_thread.start()
        
        # Read the terminal output in real-time to catch the WAF block
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
        
        process.wait()
        
        # --- PHASE 2: THE STEALTH COUNTER-ATTACK ---
        if waf_triggered:
            stealth_flags = self.ask_ai_for_evasion()
            logging.info(f"🥷 Initiating Stealth Counter-Attack...")
            
            # Reset progress for stealth mode
            self.requests_sent = 0
            self.start_time = time.time()
            
            # SECURITY: Validate AI response against whitelist to prevent command injection
            import re
            validated_args = []
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
            
            stealth_process.wait()
        
        self.is_scanning = False
        
        # --- PHASE 3: PARSING THE LOOT ---
        vulnerabilities = []
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                for line in f:
                    try:
                        vuln_data = json.loads(line.strip())
                        # Return raw JSON string for downstream parsers
                        vulnerabilities.append(line.strip())
                    except json.JSONDecodeError:
                        continue
        
        self.vulnerabilities_found = len(vulnerabilities)
        if progress_callback:
            progress_callback(self.get_progress_stats())
                        
        return vulnerabilities
