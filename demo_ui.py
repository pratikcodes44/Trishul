#!/usr/bin/env python3
"""
Quick demo of Trishul's enhanced terminal UI.
Shows off the new AI assistant-like interface.
"""

from terminal_ui import StreamingUI, VulnerabilityDisplay
from rich.console import Console
import time
import sys

def main():
    console = Console()
    ui = StreamingUI(console)
    vuln_display = VulnerabilityDisplay(console)
    
    # Clear and welcome
    console.clear()
    
    ui.panel_message(
        "[bold cyan]Welcome to Trishul[/bold cyan]\n\n"
        "An AI-powered autonomous security platform that feels [bold]alive[/bold].\n"
        "Watch as we demonstrate the enhanced terminal interface...",
        title="🔱 TRISHUL",
        style="cyan"
    )
    
    time.sleep(2)
    console.clear()
    
    # Simulate initialization
    ui.section_header("🚀 SYSTEM INITIALIZATION")
    
    ui.info("Loading security modules...")
    time.sleep(0.5)
    
    modules = [
        "Subdomain Discovery Engine",
        "AI WAF Evasion System",
        "IDOR Auto-Tester",
        "GraphQL Scanner",
        "Nuclei Vulnerability Engine"
    ]
    
    for module in modules:
        ui.success(f"{module} initialized")
        time.sleep(0.3)
    
    print()
    ui.stream_text(
        "All systems operational. Trishul is ready to hunt vulnerabilities.",
        style="bold green",
        delay=0.025
    )
    
    time.sleep(1)
    console.clear()
    
    # Simulate scanning
    ui.section_header("🎯 TARGET RECONNAISSANCE")
    
    ui.thinking_animation(2, "Analyzing target.com infrastructure")
    
    ui.data_table(
        "📊 Discovery Results",
        ["Metric", "Count", "Status"],
        [
            ["Subdomains Found", "247", "✓"],
            ["Open Ports", "18", "✓"],
            ["Live Hosts", "156", "✓"],
            ["Crawled Endpoints", "3,842", "✓"],
            ["API Endpoints", "42", "✓"]
        ],
        style="green"
    )
    
    time.sleep(1)
    
    print()
    ui.warning("⚠️  WAF detected on target")
    time.sleep(0.8)
    ui.info("🧠 Engaging AI evasion tactics...")
    time.sleep(1.5)
    ui.success("✓ Successfully bypassed rate limiting (-rl 5 -c 2)")
    
    time.sleep(1)
    console.clear()
    
    # Vulnerability findings
    ui.section_header("🚨 VULNERABILITY ASSESSMENT")
    
    ui.thinking_animation(1.5, "Running 10-phase attack pipeline")
    
    print()
    ui.stream_text(
        "Phase 3 complete: Subdomain takeover check...",
        style="yellow",
        delay=0.02
    )
    time.sleep(0.3)
    
    ui.stream_text(
        "Phase 6 complete: GraphQL introspection enabled...",
        style="yellow",
        delay=0.02
    )
    time.sleep(0.3)
    
    ui.stream_text(
        "Phase 9 complete: IDOR vulnerabilities detected...",
        style="yellow",
        delay=0.02
    )
    
    time.sleep(1)
    print()
    
    # Display findings
    ui.success("Scan complete! Displaying findings...")
    time.sleep(1)
    
    print()
    vuln_display.display_finding({
        'type': 'Subdomain Takeover',
        'severity': 'CRITICAL',
        'url': 'staging.target.com → dead-app.heroku.com',
        'cvss': 8.1,
        'description': 'Dangling CNAME pointing to unclaimed Heroku app',
        'evidence': 'HTTP 404: "No such app"',
        'impact': 'Attacker can serve malicious content on victim subdomain',
        'remediation': 'Remove dangling DNS record or claim the Heroku app'
    })
    
    print()
    vuln_display.display_finding({
        'type': 'GraphQL Introspection Enabled',
        'severity': 'MEDIUM',
        'url': 'https://target.com/graphql',
        'cvss': 5.3,
        'description': 'GraphQL introspection query exposed full API schema',
        'evidence': 'Found 247 types including User, Admin, Payment',
        'impact': 'Complete API schema disclosure enables targeted attacks',
        'remediation': 'Disable introspection in production'
    })
    
    print()
    vuln_display.display_finding({
        'type': 'IDOR - Horizontal Privilege Escalation',
        'severity': 'HIGH',
        'url': 'https://target.com/api/user?id=123',
        'cvss': 7.5,
        'description': 'User ID parameter allows unauthorized access',
        'evidence': 'Accessed ID 456 data: email, phone, address',
        'impact': 'Full PII disclosure for all users',
        'remediation': 'Implement authorization checks on user_id parameter'
    })
    
    time.sleep(1)
    print()
    
    # Summary
    all_findings = [
        {'severity': 'CRITICAL'},
        {'severity': 'CRITICAL'},
        {'severity': 'HIGH'},
        {'severity': 'HIGH'},
        {'severity': 'MEDIUM'},
        {'severity': 'MEDIUM'},
        {'severity': 'LOW'}
    ]
    
    vuln_display.display_summary(all_findings)
    
    time.sleep(1)
    
    # Final message
    ui.celebration("Security Assessment Complete!")
    
    ui.panel_message(
        "[bold white]7 vulnerabilities discovered[/bold white]\n"
        "→ 2 CRITICAL\n"
        "→ 2 HIGH\n"
        "→ 2 MEDIUM\n"
        "→ 1 LOW\n\n"
        "[dim]Reports generated and ready for submission[/dim]",
        title="📝 Summary",
        style="green"
    )
    
    print()
    ui.info("This is what Trishul's terminal interface looks like")
    ui.info("Every scan feels alive with real-time updates and AI interactions")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted")
        sys.exit(0)
