"""
Smart AI-Powered Watchdog for Stuck Detection
Uses AI to analyze request activity and determine if attack is truly stuck
"""
import time
import threading
import logging
import json
from collections import deque
import statistics
from typing import Any, Dict, Optional
from ai_engine import LocalLLMProvider

logger = logging.getLogger(__name__)


class SmartWatchdog:
    """
    AI-powered watchdog that monitors request activity intelligently.
    Only triggers stuck alert when ZERO requests for sustained period.
    """
    
    def __init__(
        self,
        target_domain: str,
        gmail_notifier,
        zero_activity_threshold: int = 60,
        require_ai_verdict: bool = True,
    ):
        """
        Initialize smart watchdog.
        
        Args:
            target_domain: Target domain being scanned
            gmail_notifier: Gmail notifier instance
            zero_activity_threshold: Seconds of zero activity before alert (default: 60)
        """
        self.target_domain = target_domain
        self.gmail_notifier = gmail_notifier
        self.zero_activity_threshold = zero_activity_threshold
        self.require_ai_verdict = require_ai_verdict
        
        # Activity tracking
        self.request_history = deque(maxlen=120)  # Last 2 minutes of samples
        self.last_request_count = 0
        self.current_request_count = 0
        self.last_activity_time = time.time()
        self.zero_activity_duration = 0
        
        # Phase tracking
        self.current_phase = 0
        self.current_phase_name = "Initialization"
        self.phase_start_time = time.time()
        
        # Thread control
        self.running = False
        self.thread = None
        self.alert_sent_for_phase = -1
        
        # AI analysis
        self.activity_window_size = 30  # Analyze last 30 seconds
        self.min_phase_stuck_seconds = 600  # Non-request phases need long delay before candidate
        self.phase10_warmup_seconds = 120
        self.ai_check_interval = 20
        self.last_ai_check_time = 0.0
        self.last_ai_verdict: Dict[str, Any] = {
            "stuck": False,
            "confidence": 0.0,
            "reason": "not evaluated",
        }
        self.ai_provider = LocalLLMProvider()
        
    def start(self):
        """Start the smart watchdog thread."""
        if self.running:
            logger.warning("Smart watchdog already running")
            return
        
        self.running = True
        self.last_activity_time = time.time()
        self.thread = threading.Thread(target=self._ai_monitor, daemon=True, name="SmartWatchdog")
        self.thread.start()
        logger.info(f"🤖 AI-Powered Smart Watchdog started (zero-activity threshold: {self.zero_activity_threshold}s)")
    
    def stop(self):
        """Stop the watchdog thread."""
        self.running = False
        if self.thread:
            logger.info("🤖 AI-Powered Smart Watchdog stopped")
    
    def update_progress(self, phase_num: int, phase_name: str = ""):
        """
        Called by main pipeline when phase progresses.
        
        Args:
            phase_num: Current phase number
            phase_name: Optional phase name
        """
        self.current_phase = phase_num
        if phase_name:
            self.current_phase_name = phase_name
        self.phase_start_time = time.time()
        
        # Reset alert tracking when we progress to a new phase
        if phase_num != self.alert_sent_for_phase:
            self.alert_sent_for_phase = -1
            self.zero_activity_duration = 0  # Reset zero activity counter
        
        # Mark activity (phase transition counts as activity)
        self.last_activity_time = time.time()
    
    def record_phase_change(self, phase_num: int, phase_name: str = ""):
        """
        Alias for update_progress() for backward compatibility.
        Records when phases change during the attack pipeline.
        
        Args:
            phase_num: Current phase number (1-10)
            phase_name: Optional phase name (e.g., "Subdomain Discovery")
        """
        self.update_progress(phase_num, phase_name)
    
    def record_request_activity(self, request_count: int):

        """
        Record current request count from scanning tools.
        Called by nuclei progress callback or other scanners.
        
        Args:
            request_count: Total requests sent so far
        """
        self.current_request_count = request_count
        
        # If we got new requests, reset zero activity tracking
        if request_count > self.last_request_count:
            self.last_activity_time = time.time()
            self.zero_activity_duration = 0
        
        # Record activity sample
        self.request_history.append({
            'timestamp': time.time(),
            'count': request_count,
            'delta': request_count - self.last_request_count
        })
        
        self.last_request_count = request_count
    
    def _analyze_activity(self):
        """
        AI-powered activity analysis.
        Returns True if genuinely stuck, False if still active.
        """
        now = time.time()
        
        # Get recent activity (last 30 seconds)
        recent_activity = [
            sample for sample in self.request_history 
            if now - sample['timestamp'] <= self.activity_window_size
        ]
        
        if not recent_activity:
            return False
        
        # Calculate request deltas (new requests per sample)
        deltas = [sample['delta'] for sample in recent_activity]
        
        # AI Logic: Check for sustained zero activity
        total_new_requests = sum(deltas)
        
        if total_new_requests == 0:
            # ZERO requests in recent window - potentially stuck
            self.zero_activity_duration += 1  # Increment each check cycle
            
            # But allow for slow phases (like DNS resolution, port scanning)
            # Only alert if ZERO activity for full threshold period
            if self.zero_activity_duration >= (self.zero_activity_threshold / 2):  # 2 samples per second
                return True
            else:
                logger.debug(
                    f"[AI-WATCHDOG] Zero activity for {self.zero_activity_duration * 0.5:.0f}s "
                    f"(threshold: {self.zero_activity_threshold}s)"
                )
                return False
        else:
            # Active requests detected - NOT stuck
            self.zero_activity_duration = 0
            
            # Calculate activity rate
            avg_delta = statistics.mean(deltas) if deltas else 0
            logger.debug(
                f"[AI-WATCHDOG] Active: {total_new_requests} requests in last {self.activity_window_size}s "
                f"(avg: {avg_delta:.1f} req/sample)"
            )
            return False

    def _phase_based_candidate(self) -> bool:
        """
        For phases where request counters are unavailable, detect potential stall
        from elapsed phase time instead of immediate zero-request behavior.
        """
        now = time.time()
        phase_elapsed = now - self.phase_start_time
        time_since_last = now - self.last_activity_time

        # Phase 10 can be legitimately slow at startup.
        threshold = self.min_phase_stuck_seconds
        if self.current_phase == 10:
            threshold = max(threshold, self.phase10_warmup_seconds + self.zero_activity_threshold)

        return phase_elapsed >= threshold and time_since_last >= self.zero_activity_threshold

    def _build_ai_prompt(self, stuck_duration: float, activity_based: bool) -> str:
        status = self.get_status()
        payload = {
            "target": self.target_domain,
            "phase_num": self.current_phase,
            "phase_name": self.current_phase_name,
            "phase_elapsed_seconds": int(time.time() - self.phase_start_time),
            "stuck_duration_seconds": int(stuck_duration),
            "recent_request_count_30s": status.get("recent_request_count", 0),
            "time_since_last_activity_seconds": int(status.get("time_since_last_activity", 0)),
            "activity_based_trigger": activity_based,
            "zero_activity_threshold_seconds": self.zero_activity_threshold,
        }
        return (
            "You are deciding if a security scan phase is truly stuck.\n"
            "Return STRICT JSON only: {\"stuck\": true|false, \"confidence\": 0..1, \"reason\": \"short\"}.\n"
            "Mark stuck=true ONLY if confidence >= 0.8 and there is no meaningful progress.\n"
            "Prefer false when uncertain or when scan could be slow but active.\n"
            f"Data: {json.dumps(payload)}"
        )

    def _ai_stuck_verdict(self, stuck_duration: float, activity_based: bool) -> Dict[str, Any]:
        """
        Ask local AI if candidate should be treated as truly stuck.
        Falls back to safe behavior (not stuck) on parse/availability issues.
        """
        if not self.require_ai_verdict:
            return {"stuck": True, "confidence": 1.0, "reason": "ai gate disabled"}

        now = time.time()
        if now - self.last_ai_check_time < self.ai_check_interval:
            return self.last_ai_verdict

        self.last_ai_check_time = now
        if not self.ai_provider.is_available():
            verdict = {
                "stuck": False,
                "confidence": 0.0,
                "reason": "ai unavailable; suppressing alert",
            }
            self.last_ai_verdict = verdict
            return verdict

        raw = self.ai_provider.generate(
            prompt=self._build_ai_prompt(stuck_duration, activity_based),
            system_prompt="Output valid JSON only.",
            temperature=0.0,
            max_tokens=120,
        )
        if not raw:
            verdict = {
                "stuck": False,
                "confidence": 0.0,
                "reason": "empty ai response; suppressing alert",
            }
            self.last_ai_verdict = verdict
            return verdict

        try:
            data = json.loads(raw)
            stuck = bool(data.get("stuck", False))
            confidence = float(data.get("confidence", 0.0))
            reason = str(data.get("reason", ""))
            verdict = {"stuck": stuck and confidence >= 0.8, "confidence": confidence, "reason": reason}
            self.last_ai_verdict = verdict
            return verdict
        except (ValueError, TypeError):
            verdict = {
                "stuck": False,
                "confidence": 0.0,
                "reason": "invalid ai json; suppressing alert",
            }
            self.last_ai_verdict = verdict
            return verdict
    
    def _ai_monitor(self):
        """Background AI monitoring loop."""
        while self.running:
            time.sleep(0.5)  # Check every 0.5 seconds for precise tracking
            
            if not self.running:
                break
            
            # Candidate detection: request-activity for phase 10, phase-time fallback otherwise.
            activity_candidate = self._analyze_activity() if self.current_phase == 10 else False
            phase_candidate = self._phase_based_candidate() if self.current_phase != 10 else False
            is_stuck_candidate = activity_candidate or phase_candidate
            
            # If AI determines we're stuck and haven't alerted for this phase
            if is_stuck_candidate and self.alert_sent_for_phase != self.current_phase:
                stuck_duration = time.time() - self.last_activity_time
                verdict = self._ai_stuck_verdict(stuck_duration, activity_candidate)
                if not verdict.get("stuck", False):
                    logger.info(
                        "🤖 AI verdict for phase %s (%s): NOT stuck (confidence=%.2f, reason=%s)",
                        self.current_phase,
                        self.current_phase_name,
                        float(verdict.get("confidence", 0.0)),
                        verdict.get("reason", ""),
                    )
                    continue
                
                logger.warning(
                    f"🤖 AI-WATCHDOG ALERT: Phase {self.current_phase} ({self.current_phase_name}) "
                    f"has ZERO request activity for {int(stuck_duration)}s"
                )
                
                # Send email alert
                try:
                    self.gmail_notifier.send_stuck_alert(
                        domain=self.target_domain,
                        phase_num=self.current_phase,
                        phase_name=self.current_phase_name,
                        stuck_duration=stuck_duration
                    )
                    self.alert_sent_for_phase = self.current_phase
                    logger.info(f"✉️  AI-determined stuck alert sent for Phase {self.current_phase}")
                except Exception as e:
                    logger.error(f"Failed to send AI-watchdog alert: {e}")
    
    def get_status(self):
        """Get current watchdog status for debugging."""
        now = time.time()
        recent_activity = [
            sample for sample in self.request_history 
            if now - sample['timestamp'] <= self.activity_window_size
        ]
        
        total_requests = sum(sample['delta'] for sample in recent_activity)
        time_since_last = now - self.last_activity_time
        
        return {
            'zero_activity_duration': self.zero_activity_duration * 0.5,  # Convert to seconds
            'time_since_last_activity': time_since_last,
            'recent_request_count': total_requests,
            'current_phase': self.current_phase,
            'current_phase_name': self.current_phase_name,
            'phase_elapsed_seconds': now - self.phase_start_time,
            'threshold': self.zero_activity_threshold,
            'is_active': total_requests > 0,
            'ai_verdict': self.last_ai_verdict,
        }
