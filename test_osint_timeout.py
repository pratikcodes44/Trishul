#!/usr/bin/env python3
"""
Quick test to verify OSINT timeout fixes work
"""
import logging
logging.basicConfig(level=logging.INFO)

from osint.osint_gatherer import OSINTGatherer

def test_callback(module, status, count=0):
    print(f"[{status.upper()}] {module}: {count if count else ''}")

print("Testing OSINT with zurich.com.au (the domain that was hanging)...")
print("This should complete in <15 seconds even if CT logs timeout\n")

gatherer = OSINTGatherer("zurich.com.au")

import time
start = time.time()

try:
    findings = gatherer.gather_all(progress_callback=test_callback)
    elapsed = time.time() - start
    
    print(f"\n✅ OSINT completed in {elapsed:.1f} seconds")
    print(f"   Subdomains: {len(findings.get('subdomains', []))}")
    print(f"   GitHub leaks: {len(findings.get('github_leaks', []))}")
    print(f"   Cloud buckets: {len(findings.get('cloud_buckets', []))}")
    
except Exception as e:
    elapsed = time.time() - start
    print(f"\n❌ OSINT failed after {elapsed:.1f} seconds: {e}")
