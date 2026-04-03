#!/usr/bin/env python3
"""
Integration script to replace AttackProgressTracker with DynamicTUI in main.py
This demonstrates how to use the new dynamic TUI system.
"""

# Example of how to integrate the new Dynamic TUI:

# 1. Import the new TUI
from dynamic_tui import create_tui, PIPELINE_PHASES

# 2. Replace tracker initialization with:
"""
# OLD:
tracker = AttackProgressTracker(target_domain)

# NEW:
tui = create_tui(target_domain, total_phases=len(PIPELINE_PHASES))

# Setup phases for tracking
tui_phases = [
    {'name': phase['name'], 'icon': phase['icon'], 'status': 'pending', 'details': ''}
    for phase in PIPELINE_PHASES
]
tui.set_phases(tui_phases)
"""

# 3. Replace tracker.start() with:
"""
# OLD:
tracker.start()

# NEW:
tui.start()
"""

# 4. Replace phase updates:
"""
# OLD:
tracker.set_phase(1)
tracker.set_targets(10)
tracker.set_phase_detail(1, "Running...")
tracker.log_finding("subdomains", 5)
tracker.complete_phase(1, "Found 5 subdomains")

# NEW:
tui.set_phase(1, "OSINT Reconnaissance", "Gathering intelligence...")
tui.update_activity("Scanning 10 targets")
tui.update_phase_details(1, "Processing subdomains")
tui.update_metric('subdomains', 5)
tui.complete_phase(1, "Found 5 subdomains")
"""

# 5. For vulnerability findings:
"""
# OLD:
tracker.log_finding("vulnerabilities", count)
# Then print each finding

# NEW:
tui.add_finding({
    'name': 'SQL Injection',
    'severity': 'critical',  # critical, high, medium, low, info
    'target': 'https://example.com/api/users'
})
"""

# 6. Replace tracker.stop() with:
"""
# OLD:
tracker.stop()

# NEW:
tui.stop()
"""

print("""
Dynamic TUI Integration Guide
==============================

The new DynamicTUI provides a GitHub Copilot-style experience with:

✅ Live spinners for tasks in progress
✅ Live updating metrics dashboard
✅ Recent findings table that updates in place
✅ Persistent status bar showing current activity
✅ Smooth 10 FPS animations
✅ Automatic graceful degradation for non-interactive environments

Installation:
No new dependencies needed - uses existing 'rich' library.

Key API methods:
- tui.set_phase(num, name, activity) - Update current phase
- tui.complete_phase(num, summary) - Mark phase as complete
- tui.fail_phase(num, error) - Mark phase as failed
- tui.update_activity(text) - Update status bar message
- tui.update_phase_details(num, text) - Update phase details
- tui.update_metric(key, value) - Set a metric value
- tui.increment_metric(key, delta) - Increment a metric
- tui.add_finding(dict) - Add a vulnerability finding

Metrics available:
- subdomains, ports, live_hosts, urls
- vulnerabilities (total)
- critical, high, medium, low, info (severity breakdown)

The TUI automatically:
- Detects if running in interactive terminal
- Falls back to clean text output if piped to file
- Handles terminal resize gracefully
- Updates at 10 FPS for smooth animations
""")
