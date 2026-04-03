#!/usr/bin/env python3
"""
Quick test of enhanced Nuclei runner
"""

import sys
import time
from nuclei_runner import NucleiRunner

def progress_callback(stats):
    """Print progress updates."""
    print(f"\r🎯 Progress: {stats['requests_sent']:,}/{stats['requests_total']:,} | "
          f"RPS: {stats['rps']} | ETA: {stats['eta_seconds']}s | "
          f"Vulns: {stats['vulnerabilities']} | "
          f"Progress: {stats['requests_sent']/max(stats['requests_total'],1)*100:.1f}%", 
          end='', flush=True)

if __name__ == "__main__":
    print("🔱 Testing Enhanced Nuclei Runner\n")
    
    # Test URLs
    test_urls = [
        "http://testphp.vulnweb.com",
        "http://testphp.vulnweb.com/artists.php",
        "http://testphp.vulnweb.com/login.php",
    ]
    
    print(f"Testing with {len(test_urls)} URLs...\n")
    
    runner = NucleiRunner()
    
    print("Starting scan with progress tracking...")
    print("=" * 70)
    
    start = time.time()
    results = runner.run_scan(test_urls, progress_callback=progress_callback)
    elapsed = time.time() - start
    
    print(f"\n\n" + "=" * 70)
    print(f"✅ Scan complete in {elapsed:.1f} seconds")
    print(f"🐛 Vulnerabilities found: {len(results)}")
    
    if results:
        print("\n📋 Findings:")
        for i, result in enumerate(results[:5], 1):
            print(f"  {i}. {result[:100]}...")
    else:
        print("\n✅ No vulnerabilities found (or templates not loaded)")
