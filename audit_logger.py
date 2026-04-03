#!/usr/bin/env python3
"""
Audit Logger - Legal compliance logging for all HTTP requests
Provides audit trail for accountability and legal defense
"""

import json
import os
import getpass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from threading import Lock


class AuditLogger:
    """Thread-safe audit logger for security testing"""
    
    def __init__(self, log_file: str = "audit_log.jsonl", enabled: bool = True):
        """
        Initialize audit logger
        
        Args:
            log_file: Path to audit log file (JSONL format)
            enabled: Enable/disable logging
        """
        self.log_file = log_file
        self.enabled = enabled
        self.lock = Lock()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.operator = getpass.getuser()
        
        if enabled:
            self._initialize_log()
    
    def _initialize_log(self):
        """Initialize log file with session header"""
        log_dir = Path(self.log_file).parent
        if log_dir and not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        
        # Write session start marker
        self._write_log({
            'event': 'session_start',
            'session_id': self.session_id,
            'operator': self.operator,
            'timestamp': datetime.now().isoformat(),
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        })
    
    def _write_log(self, entry: Dict[str, Any]):
        """Write log entry to file (thread-safe)"""
        if not self.enabled:
            return
        
        with self.lock:
            try:
                with open(self.log_file, 'a') as f:
                    json.dump(entry, f)
                    f.write('\n')
            except Exception as e:
                # Don't let logging failures break the scan
                print(f"⚠️  Audit log error: {e}")
    
    def log_request(self, 
                    method: str,
                    url: str,
                    status_code: Optional[int] = None,
                    response_time: Optional[float] = None,
                    error: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None):
        """
        Log HTTP request for audit trail
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            status_code: HTTP response code
            response_time: Request duration in seconds
            error: Error message if request failed
            metadata: Additional context (headers, parameters, etc.)
        """
        entry = {
            'event': 'http_request',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'operator': self.operator,
            'method': method,
            'url': url,
            'status_code': status_code,
            'response_time_ms': int(response_time * 1000) if response_time else None,
            'error': error,
            'metadata': metadata or {}
        }
        
        self._write_log(entry)
    
    def log_finding(self,
                    vulnerability_type: str,
                    severity: str,
                    url: str,
                    details: Dict[str, Any]):
        """
        Log vulnerability finding
        
        Args:
            vulnerability_type: Type of vulnerability (XSS, SQLi, etc.)
            severity: CRITICAL, HIGH, MEDIUM, LOW
            url: Affected URL
            details: Finding details (evidence, impact, etc.)
        """
        entry = {
            'event': 'vulnerability_found',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'operator': self.operator,
            'type': vulnerability_type,
            'severity': severity,
            'url': url,
            'details': details
        }
        
        self._write_log(entry)
    
    def log_scope_validation(self, target: str, in_scope: bool, reason: str = ""):
        """Log scope validation checks"""
        entry = {
            'event': 'scope_validation',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'target': target,
            'in_scope': in_scope,
            'reason': reason
        }
        
        self._write_log(entry)
    
    def log_consent(self, consent_given: bool, disclaimer_text: str):
        """Log legal consent acceptance"""
        entry = {
            'event': 'legal_consent',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'operator': self.operator,
            'consent_given': consent_given,
            'disclaimer_version': 'v1.0',
            'disclaimer_text': disclaimer_text
        }
        
        self._write_log(entry)
    
    def log_scan_start(self, target: str, mode: str, options: Dict[str, Any]):
        """Log scan initialization"""
        entry = {
            'event': 'scan_start',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'operator': self.operator,
            'target': target,
            'mode': mode,
            'options': options
        }
        
        self._write_log(entry)
    
    def log_scan_complete(self, target: str, duration: float, findings_count: int):
        """Log scan completion"""
        entry = {
            'event': 'scan_complete',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'target': target,
            'duration_seconds': duration,
            'findings_count': findings_count
        }
        
        self._write_log(entry)
    
    def log_error(self, error_type: str, message: str, context: Optional[Dict] = None):
        """Log errors and exceptions"""
        entry = {
            'event': 'error',
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'message': message,
            'context': context or {}
        }
        
        self._write_log(entry)
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.enabled or not Path(self.log_file).exists():
            return {}
        
        stats = {
            'session_id': self.session_id,
            'requests': 0,
            'findings': 0,
            'errors': 0
        }
        
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('session_id') != self.session_id:
                        continue
                    
                    event = entry.get('event')
                    if event == 'http_request':
                        stats['requests'] += 1
                    elif event == 'vulnerability_found':
                        stats['findings'] += 1
                    elif event == 'error':
                        stats['errors'] += 1
                except:
                    continue
        
        return stats
    
    def close(self):
        """Close audit log session"""
        if self.enabled:
            summary = self.get_session_summary()
            self._write_log({
                'event': 'session_end',
                'session_id': self.session_id,
                'timestamp': datetime.now().isoformat(),
                'summary': summary
            })


# Global audit logger instance
_global_logger: Optional[AuditLogger] = None


def init_audit_logger(log_file: str = "audit_log.jsonl", enabled: bool = True):
    """Initialize global audit logger"""
    global _global_logger
    _global_logger = AuditLogger(log_file, enabled)
    return _global_logger


def get_audit_logger() -> Optional[AuditLogger]:
    """Get global audit logger instance"""
    return _global_logger


def log_request(*args, **kwargs):
    """Convenience function for logging requests"""
    if _global_logger:
        _global_logger.log_request(*args, **kwargs)


def log_finding(*args, **kwargs):
    """Convenience function for logging findings"""
    if _global_logger:
        _global_logger.log_finding(*args, **kwargs)


if __name__ == "__main__":
    # Demo
    print("=== Audit Logger Demo ===\n")
    
    logger = AuditLogger("test_audit.jsonl")
    
    logger.log_scan_start("example.com", "enterprise", {"timeout": 30})
    logger.log_request("GET", "https://example.com", 200, 0.245)
    logger.log_request("GET", "https://example.com/api", 404, 0.123)
    logger.log_finding("XSS", "HIGH", "https://example.com/search", {
        "parameter": "q",
        "payload": "<script>alert(1)</script>"
    })
    logger.log_scan_complete("example.com", 120.5, 1)
    
    summary = logger.get_session_summary()
    print(f"Session Summary: {summary}")
    
    logger.close()
    
    print(f"\n✓ Audit log written to: test_audit.jsonl")
    print("View with: cat test_audit.jsonl | jq")
