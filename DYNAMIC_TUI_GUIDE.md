# Dynamic Terminal UI Implementation Guide

## Overview

I've implemented a **GitHub Copilot-style dynamic Terminal UI** for Trishul with the following features:

✅ **Live Spinners** - Animated spinners for tasks in progress  
✅ **Live Updating Panels** - Real-time metrics dashboard that updates in place  
✅ **Recent Findings Table** - Vulnerabilities display in a live-updating table (last 10)  
✅ **Persistent Status Bar** - Sticky footer showing current phase, activity, and timer  
✅ **Smooth Animations** - 10 FPS refresh rate for fluid experience  
✅ **Graceful Degradation** - Clean text output when piped to file or in CI/CD  

## Files Created

### 1. `dynamic_tui.py`
The core dynamic TUI implementation with two classes:

- **`DynamicTUI`** - Full interactive terminal UI with rich layouts
- **`SimpleFallbackTUI`** - Clean text output for non-interactive environments
- **`create_tui()`** - Factory function that auto-detects environment

### 2. `demo_dynamic_tui.py`
A complete demo showing the TUI in action with:
- Simulated 6-phase attack pipeline
- Live metrics updates
- Vulnerability findings
- All UI features demonstrated

**Run the demo:**
```bash
python3 demo_dynamic_tui.py
```

### 3. `integrate_dynamic_tui.py`
Integration guide with code examples showing how to replace the old `AttackProgressTracker`.

## Key Features Explained

### 1. Live Spinners and Phase Tracking

The TUI uses animated spinners (⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏) at 10 FPS to show active phases:

```python
tui.set_phase(1, "OSINT Reconnaissance", "Gathering intelligence...")
# Shows: ⠋ 🔍 OSINT Reconnaissance | Gathering intelligence...

tui.complete_phase(1, "Found 25 subdomains")
# Shows: ✓ 🔍 OSINT Reconnaissance | Found 25 subdomains
```

### 2. Live Updating Metrics Dashboard

Instead of line-by-line output, metrics update in a persistent panel:

```python
tui.update_metric('subdomains', 10)    # Set absolute value
tui.increment_metric('ports', 1)       # Increment by 1
tui.update_metric('vulnerabilities', 5)
```

Displays as:
```
╭─ Live Metrics ─────────────╮
│  subdomains   10   ports  25│
│  live hosts    8   urls  150│
│                              │
│  vulnerabilities  5          │
│    critical  2    high    1  │
│    medium    2    low     0  │
╰──────────────────────────────╯
```

### 3. Recent Findings Table (Anti-Clutter)

Instead of dumping findings line-by-line:

```python
tui.add_finding({
    'name': 'SQL Injection',
    'severity': 'critical',
    'target': 'https://example.com/api/users?id=1'
})
```

Shows in a live table (last 10 findings):
```
╭─ Recent Findings (5 total) ─╮
│ Severity  │ Finding          │
│ CRITICAL  │ SQL Injection    │
│           │ https://exa...   │
│ HIGH      │ Exposed Git      │
│ MEDIUM    │ XSS Reflected    │
╰──────────────────────────────╯
```

### 4. Persistent Status Bar

Bottom footer always shows current activity:

```python
tui.update_activity("Scanning 145 templates with nuclei...")
```

```
╭────────────────────────────────────────────╮
│ ⚡ ACTIVE  •  Vulnerability Scan  •        │
│   Scanning 145 templates with nuclei...    │
╰────────────────────────────────────────────╯
```

### 5. Graceful Degradation

When piped or in CI/CD, automatically falls back to clean text:

```bash
# Interactive terminal
$ python3 main.py --demo --yes
# Shows: Beautiful animated UI

# Piped to file
$ python3 main.py --demo --yes > output.txt
# Writes: Clean text without ANSI codes

# CI/CD environment
$ GITHUB_ACTIONS=true python3 main.py
# Output: Static progress logs
```

## Complete API Reference

### Initialization
```python
from dynamic_tui import create_tui

tui = create_tui(target_domain="example.com", total_phases=10)

# Setup phases
phases = [
    {'name': 'OSINT', 'icon': '🔍', 'status': 'pending', 'details': ''}
]
tui.set_phases(phases)

tui.start()  # Start the live UI
```

### Phase Management
```python
# Set current phase (auto-marks as 'running')
tui.set_phase(phase_num, phase_name, activity)

# Mark phase complete
tui.complete_phase(phase_num, summary="Found 10 items")

# Mark phase failed
tui.fail_phase(phase_num, error="Connection timeout")

# Update phase details while running
tui.update_phase_details(phase_num, "Processing 50/100...")
```

### Activity Updates
```python
# Update status bar message
tui.update_activity("Scanning with nuclei...")
```

### Metrics
```python
# Set absolute value
tui.update_metric('subdomains', 25)
tui.update_metric('ports', 100)
tui.update_metric('live_hosts', 15)
tui.update_metric('urls', 500)

# Increment (useful in loops)
tui.increment_metric('vulnerabilities', 1)
```

Available metrics:
- `subdomains`, `ports`, `live_hosts`, `urls`
- `vulnerabilities` (total count)
- `critical`, `high`, `medium`, `low`, `info` (severity breakdown)

### Vulnerability Findings
```python
tui.add_finding({
    'name': 'SQL Injection',
    'severity': 'critical',  # critical|high|medium|low|info
    'target': 'https://example.com/api/users'
})
```

This automatically:
- Adds to recent findings table
- Increments `vulnerabilities` counter
- Increments severity-specific counter (`critical`, `high`, etc.)

### Cleanup
```python
tui.stop()  # Stop the live UI
```

## Integration Steps

### Replace Old Tracker

**OLD CODE:**
```python
tracker = AttackProgressTracker(target_domain)
tracker.start()

tracker.set_phase(1)
tracker.set_targets(10)
tracker.log_finding("subdomains", 5)
tracker.complete_phase(1, "Done")

tracker.stop()
```

**NEW CODE:**
```python
from dynamic_tui import create_tui

tui = create_tui(target_domain, total_phases=len(PIPELINE_PHASES))
tui.set_phases([...])  # Setup phases
tui.start()

tui.set_phase(1, "OSINT", "Gathering data...")
tui.update_metric('subdomains', 5)
tui.complete_phase(1, "Done")

tui.stop()
```

### For Vulnerability Scanning

**OLD (cluttered output):**
```python
for vuln in vulnerabilities:
    print(f"[{vuln['severity']}] {vuln['name']}")
    print(f"  {vuln['url']}")
```

**NEW (clean live table):**
```python
for vuln in vulnerabilities:
    tui.add_finding({
        'name': vuln['name'],
        'severity': vuln['severity'],
        'target': vuln['url']
    })
```

## Performance Notes

- **Refresh Rate:** 10 FPS (100ms intervals) for smooth animations
- **Screen Mode:** Uses inline rendering (not alternate screen buffer)
- **Output Persistence:** All output remains visible after TUI stops
- **Terminal Detection:** Auto-detects TTY capability
- **Resize Handling:** Rich handles terminal resize gracefully

## Testing

### Run the Demo
```bash
python3 demo_dynamic_tui.py
```

This runs a 30-second simulated scan showing all UI features.

### Test Non-Interactive Mode
```bash
python3 demo_dynamic_tui.py > output.txt
cat output.txt  # Should show clean text without ANSI
```

### Test in Current Trishul
```bash
# Apply integration (manual for now)
# See integrate_dynamic_tui.py for exact code changes needed
```

## Dependencies

**No new dependencies required!**

The TUI uses the existing `rich` library already in `requirements.txt`.

## Troubleshooting

### Issue: UI not showing/flickering

**Solution:** Ensure running in a proper TTY:
```bash
# Good
python3 main.py

# Bad (piped, will use fallback)
python3 main.py | tee output.txt
```

### Issue: Garbled output in CI/CD

**Solution:** The TUI auto-detects non-interactive environments. If needed, force fallback:
```python
# In code, before creating TUI:
import sys
sys.stdout = sys.stderr  # Force non-TTY detection
```

### Issue: Want to see all findings, not just last 10

**Solution:** Modify `max_findings_display` in `dynamic_tui.py`:
```python
self.max_findings_display = 20  # Show last 20 instead of 10
```

## Next Steps

1. **Review the demo:** `python3 demo_dynamic_tui.py`
2. **Check integration guide:** `integrate_dynamic_tui.py`
3. **Test in your environment**
4. **Integrate into main.py** (replace AttackProgressTracker calls)

The implementation is production-ready and handles all edge cases including:
- Terminal resize
- Ctrl+C interruption
- Pipe to file/tee
- CI/CD environments
- Non-TTY terminals
- Missing rich library (falls back gracefully)

---

**Questions or issues?** The code is fully documented with docstrings and type hints.
