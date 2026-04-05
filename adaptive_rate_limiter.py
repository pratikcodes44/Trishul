#!/usr/bin/env python3
"""
Adaptive Rate Limiter for Nuclei
=================================

Intelligent rate limiting that balances speed and stealth:
- Starts at safe rate (10 req/sec)
- Monitors server health (response times, error rates)
- Gradually increases speed if server handles well
- Backs off immediately if server shows stress
- Respects Retry-After headers (429/503 responses)
- Uses jitter to appear human-like
- Avoids DoS while maximizing speed

Philosophy: "Go as fast as the server allows, but never break it."
"""

import time
import random
import threading
import logging
from collections import deque
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ServerHealthMetrics:
    """Server health indicators."""
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    rate_limit_hits: int = 0
    server_errors: int = 0
    successful_requests: int = 0
    total_requests: int = 0


class AdaptiveRateLimiter:
    """
    Intelligent rate limiter that adapts to server capacity.
    
    How it works:
    1. Start at safe baseline (10 req/sec)
    2. Monitor server response times and errors
    3. If server healthy → increase rate by 10%
    4. If server stressed → decrease rate by 50%
    5. Respect 429/503 responses (back off completely)
    6. Add jitter to requests (appear human-like)
    
    Benefits:
    - Fast when server can handle it
    - Safe when server is stressed
    - No DoS risk
    - Evades rate limit detection
    """
    
    def __init__(
        self,
        initial_rate: int = 10,
        min_rate: int = 5,
        max_rate: int = 150,
        adaptation_interval: int = 30,
        jitter_percentage: float = 0.2
    ):
        """
        Initialize adaptive rate limiter.
        
        Args:
            initial_rate: Starting requests per second (default: 10)
            min_rate: Minimum allowed rate (default: 5)
            max_rate: Maximum allowed rate (default: 150)
            adaptation_interval: Seconds between rate adjustments (default: 30)
            jitter_percentage: Random delay variation 0.0-1.0 (default: 0.2 = ±20%)
        """
        self.current_rate = initial_rate
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.adaptation_interval = adaptation_interval
        self.jitter_percentage = jitter_percentage
        
        # Health monitoring
        self.response_times = deque(maxlen=100)  # Last 100 requests
        self.error_counts = deque(maxlen=100)
        self.rate_limit_hits = 0
        self.server_errors = 0
        self.successful_requests = 0
        self.total_requests = 0
        
        # Baseline metrics (for comparison)
        self.baseline_response_time = None
        self.baseline_established = False
        
        # Thread control
        self.lock = threading.Lock()
        self.last_adaptation_time = time.time()
        self.last_request_time = 0
        
        # Backoff state
        self.in_backoff = False
        self.backoff_until = 0
        
        logger.info(
            f"🎯 Adaptive Rate Limiter initialized: "
            f"{initial_rate} req/s (range: {min_rate}-{max_rate})"
        )
    
    def wait_for_slot(self) -> float:
        """
        Wait before making next request (adaptive + jitter).
        
        Returns:
            Actual delay applied (seconds)
        """
        with self.lock:
            # Check if in forced backoff (from 429/503)
            if self.in_backoff:
                wait_time = max(0, self.backoff_until - time.time())
                if wait_time > 0:
                    logger.debug(f"⏸️  In backoff mode, waiting {wait_time:.1f}s")
                    time.sleep(wait_time)
                    return wait_time
                else:
                    # Backoff period ended
                    self.in_backoff = False
                    logger.info("▶️  Backoff period ended, resuming requests")
            
            # Calculate base delay for current rate
            base_delay = 1.0 / self.current_rate
            
            # Add jitter (randomize ±20% by default)
            jitter_amount = base_delay * self.jitter_percentage
            jitter = random.uniform(-jitter_amount, jitter_amount)
            actual_delay = max(0, base_delay + jitter)
            
            # Ensure minimum spacing from last request
            time_since_last = time.time() - self.last_request_time
            if time_since_last < actual_delay:
                sleep_time = actual_delay - time_since_last
                time.sleep(sleep_time)
            else:
                sleep_time = 0
            
            self.last_request_time = time.time()
            
            # Periodically adapt rate based on server health
            if time.time() - self.last_adaptation_time > self.adaptation_interval:
                self._adapt_rate()
            
            return sleep_time
    
    def record_request(
        self,
        response_time: float,
        status_code: int,
        retry_after: Optional[int] = None
    ):
        """
        Record request result for health monitoring.
        
        Args:
            response_time: Request duration in seconds
            status_code: HTTP status code (200, 429, 500, etc.)
            retry_after: Retry-After header value (seconds) if present
        """
        with self.lock:
            self.total_requests += 1
            self.response_times.append(response_time)
            
            # Track errors
            is_error = False
            if status_code == 429:
                # Rate limited!
                self.rate_limit_hits += 1
                is_error = True
                logger.warning(
                    f"⚠️  Rate limit hit (429)! "
                    f"Current rate: {self.current_rate} req/s"
                )
                
                # Enter backoff mode
                backoff_duration = retry_after if retry_after else 60
                self._trigger_backoff(backoff_duration)
                
            elif status_code in {503, 502, 504}:
                # Server overloaded
                self.server_errors += 1
                is_error = True
                logger.warning(
                    f"⚠️  Server error ({status_code})! "
                    f"Reducing rate immediately"
                )
                # Immediate aggressive backoff
                self._reduce_rate(factor=0.3)
                
            elif 500 <= status_code < 600:
                # Other server errors
                self.server_errors += 1
                is_error = True
                
            elif 200 <= status_code < 300:
                # Success
                self.successful_requests += 1
            
            self.error_counts.append(1 if is_error else 0)
            
            # Establish baseline on first successful requests
            if not self.baseline_established and len(self.response_times) >= 10:
                self.baseline_response_time = self._calculate_avg_response_time()
                self.baseline_established = True
                logger.info(
                    f"📊 Baseline established: "
                    f"{self.baseline_response_time*1000:.0f}ms avg response time"
                )
    
    def _trigger_backoff(self, duration: int):
        """Enter backoff mode (pause all requests)."""
        self.in_backoff = True
        self.backoff_until = time.time() + duration
        logger.warning(
            f"🛑 Entering backoff mode for {duration}s "
            f"(server requested pause)"
        )
        # Reset to safe rate after backoff
        self.current_rate = max(self.min_rate, self.current_rate * 0.5)
    
    def _adapt_rate(self):
        """
        Adjust rate based on server health metrics.
        
        Strategy:
        - If server healthy → increase rate by 10%
        - If server stressed → decrease rate by 50%
        - If errors high → aggressive decrease
        """
        if len(self.response_times) < 10:
            # Not enough data yet
            return
        
        metrics = self._calculate_health_metrics()
        old_rate = self.current_rate
        
        # Decision logic
        if metrics.error_rate > 0.05:  # >5% errors
            # Server is struggling - slow down significantly
            self._reduce_rate(factor=0.5)
            logger.warning(
                f"📉 Server stressed (error rate: {metrics.error_rate:.1%}), "
                f"reducing rate: {old_rate} → {self.current_rate} req/s"
            )
            
        elif self.baseline_established:
            current_avg = metrics.avg_response_time
            baseline = self.baseline_response_time
            
            # Check if response times degraded
            if current_avg > baseline * 1.5:
                # Response times increased 50% - server slowing down
                self._reduce_rate(factor=0.7)
                logger.warning(
                    f"📉 Response times increased "
                    f"({baseline*1000:.0f}ms → {current_avg*1000:.0f}ms), "
                    f"reducing rate: {old_rate} → {self.current_rate} req/s"
                )
                
            elif current_avg < baseline * 1.1 and metrics.error_rate < 0.01:
                # Server handling well - carefully increase speed
                self._increase_rate(factor=1.1)
                logger.info(
                    f"📈 Server healthy, increasing rate: "
                    f"{old_rate} → {self.current_rate} req/s"
                )
        
        self.last_adaptation_time = time.time()
    
    def _increase_rate(self, factor: float = 1.1):
        """Increase rate by factor (capped at max_rate)."""
        new_rate = min(self.max_rate, self.current_rate * factor)
        self.current_rate = int(new_rate)
    
    def _reduce_rate(self, factor: float = 0.7):
        """Reduce rate by factor (capped at min_rate)."""
        new_rate = max(self.min_rate, self.current_rate * factor)
        self.current_rate = int(new_rate)
    
    def _calculate_health_metrics(self) -> ServerHealthMetrics:
        """Calculate current server health metrics."""
        if not self.response_times:
            return ServerHealthMetrics()
        
        avg_response_time = self._calculate_avg_response_time()
        error_rate = sum(self.error_counts) / len(self.error_counts) if self.error_counts else 0.0
        
        return ServerHealthMetrics(
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            rate_limit_hits=self.rate_limit_hits,
            server_errors=self.server_errors,
            successful_requests=self.successful_requests,
            total_requests=self.total_requests
        )
    
    def _calculate_avg_response_time(self) -> float:
        """Calculate average response time from recent requests."""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

    def maybe_adapt_now(self):
        """Trigger adaptation when the adaptation interval has elapsed."""
        with self.lock:
            if self.in_backoff:
                return
            if time.time() - self.last_adaptation_time < self.adaptation_interval:
                return
            self._adapt_rate()
    
    def get_status(self) -> Dict:
        """
        Get current rate limiter status.
        
        Returns:
            Dict with current rate, metrics, and health status
        """
        with self.lock:
            metrics = self._calculate_health_metrics()
            
            return {
                'current_rate': self.current_rate,
                'min_rate': self.min_rate,
                'max_rate': self.max_rate,
                'in_backoff': self.in_backoff,
                'avg_response_time_ms': metrics.avg_response_time * 1000,
                'error_rate': metrics.error_rate,
                'success_rate': (
                    metrics.successful_requests / metrics.total_requests 
                    if metrics.total_requests > 0 else 0.0
                ),
                'total_requests': metrics.total_requests,
                'rate_limit_hits': metrics.rate_limit_hits,
                'server_errors': metrics.server_errors
            }
    
    def get_nuclei_flags(self) -> Tuple[str, str]:
        """
        Get recommended Nuclei flags for current rate.
        
        Returns:
            Tuple of (rate_limit_flag, concurrency_flag)
        """
        with self.lock:
            # Concurrency scales with rate (but capped)
            # Rule of thumb: concurrency = rate / 2 (but min 5, max 50)
            concurrency = max(5, min(50, self.current_rate // 2))
            
            return (str(self.current_rate), str(concurrency))


def create_adaptive_limiter(profile: str = "balanced") -> AdaptiveRateLimiter:
    """
    Create adaptive rate limiter with preset profile.
    
    Args:
        profile: "safe", "balanced", or "aggressive"
    
    Returns:
        Configured AdaptiveRateLimiter instance
    """
    profiles = {
        "safe": {
            "initial_rate": 10,
            "min_rate": 5,
            "max_rate": 50,
            "adaptation_interval": 30,
            "jitter_percentage": 0.3  # More randomness = more human-like
        },
        "balanced": {
            "initial_rate": 20,
            "min_rate": 10,
            "max_rate": 150,
            "adaptation_interval": 20,
            "jitter_percentage": 0.2
        },
        "aggressive": {
            "initial_rate": 50,
            "min_rate": 20,
            "max_rate": 500,
            "adaptation_interval": 10,
            "jitter_percentage": 0.1
        }
    }
    
    config = profiles.get(profile, profiles["balanced"])
    logger.info(f"🎯 Creating adaptive rate limiter with '{profile}' profile")
    
    return AdaptiveRateLimiter(**config)


if __name__ == "__main__":
    # Demo: Simulate adaptive rate limiting
    logging.basicConfig(level=logging.INFO)
    
    limiter = create_adaptive_limiter("balanced")
    
    print("\n" + "="*70)
    print("ADAPTIVE RATE LIMITER SIMULATION")
    print("="*70)
    
    # Simulate 100 requests with varying server conditions
    for i in range(100):
        delay = limiter.wait_for_slot()
        
        # Simulate request
        if i < 30:
            # Phase 1: Server healthy
            response_time = random.uniform(0.1, 0.3)
            status_code = 200
        elif i < 50:
            # Phase 2: Server slowing down
            response_time = random.uniform(0.3, 0.6)
            status_code = 200
        elif i < 55:
            # Phase 3: Rate limit hit!
            response_time = 0.1
            status_code = 429
            limiter.record_request(response_time, status_code, retry_after=5)
            print(f"\n⚠️  Request {i}: Rate limited! Backing off...\n")
            continue
        else:
            # Phase 4: Server recovered
            response_time = random.uniform(0.1, 0.25)
            status_code = 200
        
        limiter.record_request(response_time, status_code)
        
        if i % 10 == 0:
            status = limiter.get_status()
            print(
                f"Request {i:3d}: "
                f"Rate={status['current_rate']:3d} req/s, "
                f"AvgTime={status['avg_response_time_ms']:.0f}ms, "
                f"Errors={status['error_rate']:.1%}"
            )
    
    print("\n" + "="*70)
    print("FINAL STATUS:")
    print("="*70)
    final_status = limiter.get_status()
    for key, value in final_status.items():
        print(f"  {key}: {value}")
