#!/usr/bin/env python3
"""
Demo script showing the Dynamic TUI in action
Run this to see how the GitHub Copilot-style UI works
"""

import time
import random
from dynamic_tui import create_tui

# Pipeline phases
DEMO_PHASES = [
    {"name": "OSINT Reconnaissance", "icon": "🔍"},
    {"name": "Subdomain Discovery", "icon": "🔍"},
    {"name": "Port Scanning", "icon": "🔌"},
    {"name": "Live Host Probing", "icon": "🌐"},
    {"name": "Web Crawling", "icon": "🕷️"},
    {"name": "Vulnerability Scan", "icon": "🎯"},
]

def demo_scan():
    """Demonstrate the dynamic TUI with a simulated scan."""
    
    # Create TUI
    tui = create_tui("example.com", total_phases=len(DEMO_PHASES))
    
    # Setup phases
    tui_phases = [
        {'name': phase['name'], 'icon': phase['icon'], 'status': 'pending', 'details': ''}
        for phase in DEMO_PHASES
    ]
    tui.set_phases(tui_phases)
    
    # Start the TUI
    tui.start()
    
    try:
        # Phase 1: OSINT
        tui.set_phase(1, "OSINT Reconnaissance", "Querying Certificate Transparency logs...")
        time.sleep(2)
        
        tui.update_activity("Searching GitHub for leaks...")
        for i in range(1, 8):
            tui.update_metric('subdomains', i)
            time.sleep(0.3)
        
        tui.complete_phase(1, "Found 7 subdomains")
        time.sleep(1)
        
        # Phase 2: Subdomain Discovery
        tui.set_phase(2, "Subdomain Discovery", "Running subfinder...")
        time.sleep(1)
        
        for i in range(8, 25):
            tui.update_metric('subdomains', i)
            tui.update_activity(f"Discovered {i} subdomains...")
            time.sleep(0.2)
        
        tui.complete_phase(2, "Found 24 subdomains")
        time.sleep(1)
        
        # Phase 3: Port Scanning
        tui.set_phase(3, "Port Scanning", "Scanning with naabu...")
        time.sleep(1)
        
        for i in range(1, 45):
            tui.update_metric('ports', i)
            tui.update_activity(f"Scanning ports... {i} open ports found")
            time.sleep(0.15)
        
        tui.complete_phase(3, "Found 44 open ports")
        time.sleep(1)
        
        # Phase 4: Live Host Probing
        tui.set_phase(4, "Live Host Probing", "Probing hosts with httpx...")
        time.sleep(1)
        
        for i in range(1, 16):
            tui.update_metric('live_hosts', i)
            tui.update_activity(f"Probing... {i} live hosts")
            time.sleep(0.2)
        
        tui.complete_phase(4, "Found 15 live hosts")
        time.sleep(1)
        
        # Phase 5: Web Crawling
        tui.set_phase(5, "Web Crawling", "Crawling with katana...")
        time.sleep(1)
        
        for i in range(1, 150, 5):
            tui.update_metric('urls', i)
            tui.update_activity(f"Crawling... {i} URLs discovered")
            time.sleep(0.1)
        
        tui.complete_phase(5, "Found 145 URLs")
        time.sleep(1)
        
        # Phase 6: Vulnerability Scanning
        tui.set_phase(6, "Vulnerability Scan", "Launching nuclei attack...")
        time.sleep(2)
        
        # Simulate finding vulnerabilities
        vulnerabilities = [
            {'name': 'Exposed Git Config', 'severity': 'high', 'target': 'https://example.com/.git/config'},
            {'name': 'SQL Injection', 'severity': 'critical', 'target': 'https://api.example.com/users?id=1'},
            {'name': 'XSS Reflected', 'severity': 'medium', 'target': 'https://example.com/search?q=test'},
            {'name': 'Directory Listing', 'severity': 'low', 'target': 'https://example.com/uploads/'},
            {'name': 'Clickjacking', 'severity': 'low', 'target': 'https://example.com/'},
            {'name': 'Missing Security Headers', 'severity': 'info', 'target': 'https://example.com/'},
            {'name': 'Open Redirect', 'severity': 'medium', 'target': 'https://example.com/redirect'},
            {'name': 'Sensitive Data Exposure', 'severity': 'high', 'target': 'https://example.com/api/debug'},
            {'name': 'CORS Misconfiguration', 'severity': 'medium', 'target': 'https://api.example.com/'},
            {'name': 'Server Version Disclosure', 'severity': 'info', 'target': 'https://example.com/'},
        ]
        
        for i, vuln in enumerate(vulnerabilities, 1):
            tui.add_finding(vuln)
            tui.update_activity(f"Scanning... {i}/{len(vulnerabilities)} templates")
            time.sleep(0.8)
        
        tui.complete_phase(6, f"Found {len(vulnerabilities)} vulnerabilities")
        time.sleep(2)
        
        # Final summary
        tui.update_activity("Scan complete! Generating report...")
        time.sleep(3)
        
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user")
    finally:
        # Stop the TUI
        tui.stop()
        
        # Print summary
        print("\n" + "="*60)
        print("  SCAN COMPLETE")
        print("="*60)
        print(f"  Target: example.com")
        print(f"  Subdomains: {tui.metrics['subdomains']}")
        print(f"  Ports: {tui.metrics['ports']}")
        print(f"  Live Hosts: {tui.metrics['live_hosts']}")
        print(f"  URLs: {tui.metrics['urls']}")
        print(f"  Vulnerabilities: {tui.metrics['vulnerabilities']}")
        print(f"    - Critical: {tui.metrics['critical']}")
        print(f"    - High: {tui.metrics['high']}")
        print(f"    - Medium: {tui.metrics['medium']}")
        print(f"    - Low: {tui.metrics['low']}")
        print(f"    - Info: {tui.metrics['info']}")
        print("="*60 + "\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  TRISHUL DYNAMIC TUI DEMO")
    print("  GitHub Copilot-style Terminal Experience")
    print("="*60)
    print("\n  This demo shows:")
    print("  ✓ Live spinners for active phases")
    print("  ✓ Real-time metrics updates")
    print("  ✓ Recent findings table")
    print("  ✓ Persistent status bar")
    print("  ✓ Smooth 10 FPS animations")
    print("\n  Press Ctrl+C to interrupt\n")
    
    input("Press Enter to start demo...")
    
    demo_scan()
