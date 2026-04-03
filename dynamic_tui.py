"""
Dynamic Terminal UI for Trishul - GitHub Copilot CLI-style experience
Provides live spinners, updating panels, status bar, and smooth animations
"""

import time
import sys
from typing import List, Dict, Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich import box
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class DynamicTUI:
    """
    GitHub Copilot-style dynamic Terminal UI with:
    - Live spinners for tasks in progress
    - Live updating panels/dashboards
    - Persistent status bar
    - Smooth ANSI redrawing
    - Graceful degradation for non-interactive environments
    """
    
    def __init__(self, target_domain: str, total_phases: int = 10):
        self.target_domain = target_domain
        self.total_phases = total_phases
        self.current_phase = 0
        self.current_phase_name = ""
        self.current_activity = "Initializing..."
        self.start_time = time.time()
        
        # Metrics
        self.metrics = {
            'subdomains': 0,
            'ports': 0,
            'live_hosts': 0,
            'urls': 0,
            'vulnerabilities': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        # Phase tracking
        self.phases = []  # List of dicts: {'name': str, 'status': 'pending'|'running'|'complete'|'failed', 'icon': str, 'details': str}
        self.phase_stats = {}
        
        # Vulnerability findings (for live table)
        self.recent_findings = []  # Last 10 findings
        self.max_findings_display = 10
        
        # Spinner frames
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_idx = 0
        
        # Console detection
        self.is_interactive = sys.stdout.isatty() and RICH_AVAILABLE
        self.console = Console() if RICH_AVAILABLE else None
        self.live = None
        self.layout = None
        
        if self.is_interactive:
            self._init_layout()
    
    def _init_layout(self):
        """Initialize the rich Layout with persistent sections."""
        self.layout = Layout()
        
        # Split into header, body, and footer
        self.layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Split body into left (phases) and right (metrics + findings)
        self.layout["body"].split_row(
            Layout(name="phases", ratio=2),
            Layout(name="metrics_and_findings", ratio=3)
        )
        
        # Split right side into metrics and findings
        self.layout["metrics_and_findings"].split_column(
            Layout(name="metrics", size=10),
            Layout(name="findings")
        )
    
    def start(self):
        """Start the live TUI."""
        if self.is_interactive:
            self.live = Live(
                self.layout,
                console=self.console,
                refresh_per_second=10,  # 10 FPS for smooth animations
                screen=False,  # Don't use alternate screen buffer
                transient=False  # Keep output visible after stop
            )
            self.live.start()
        else:
            # Fallback: print static header
            print(f"\n{'='*60}")
            print(f"  TRISHUL ATTACK INITIATED")
            print(f"  Target: {self.target_domain}")
            print(f"  Phases: {self.total_phases}")
            print(f"{'='*60}\n")
    
    def stop(self):
        """Stop the live TUI."""
        if self.live:
            self.live.stop()
            self.live = None
    
    def update(self):
        """Refresh the display with current state."""
        if not self.is_interactive:
            return  # No-op for non-interactive
        
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner_frames)
        
        # Update header
        self.layout["header"].update(self._render_header())
        
        # Update phases
        self.layout["phases"].update(self._render_phases())
        
        # Update metrics
        self.layout["metrics"].update(self._render_metrics())
        
        # Update findings
        self.layout["findings"].update(self._render_findings())
        
        # Update footer (status bar)
        self.layout["footer"].update(self._render_footer())
    
    def _render_header(self) -> Panel:
        """Render the header with Trishul branding."""
        elapsed = time.time() - self.start_time
        elapsed_str = self._format_time(elapsed)
        
        header_text = Text()
        header_text.append("→ ", style="bold bright_blue")
        header_text.append("Trishul", style="bold white")
        header_text.append(f" attacking ", style="dim")
        header_text.append(self.target_domain, style="cyan")
        header_text.append(f"  •  ", style="dim")
        header_text.append(f"Phase {self.current_phase}/{self.total_phases}", style="yellow")
        header_text.append(f"  •  ", style="dim")
        header_text.append(f"⏱ {elapsed_str}", style="dim")
        
        return Panel(
            Align.center(header_text),
            style="bright_blue",
            box=box.ROUNDED
        )
    
    def _render_phases(self) -> Panel:
        """Render the phase pipeline with live spinners."""
        table = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        table.add_column("Status", width=3, justify="center")
        table.add_column("Phase")
        table.add_column("Details", style="dim")
        
        for i, phase in enumerate(self.phases):
            phase_num = i + 1
            status = phase.get('status', 'pending')
            name = phase.get('name', '')
            icon = phase.get('icon', '')
            details = phase.get('details', '')
            
            # Status indicator
            if status == 'complete':
                status_icon = "[green]✓[/green]"
                name_style = "dim green"
            elif status == 'failed':
                status_icon = "[red]✗[/red]"
                name_style = "dim red"
            elif status == 'running':
                spinner = self.spinner_frames[self.spinner_idx]
                status_icon = f"[yellow]{spinner}[/yellow]"
                name_style = "bold white"
            else:  # pending
                status_icon = "[dim]○[/dim]"
                name_style = "dim"
            
            table.add_row(
                status_icon,
                f"[{name_style}]{icon} {name}[/{name_style}]",
                details if status == 'running' else (details if status == 'complete' else "")
            )
        
        return Panel(
            table,
            title="[bold]Attack Pipeline[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )
    
    def _render_metrics(self) -> Panel:
        """Render live metrics dashboard."""
        table = Table.grid(padding=(0, 2), expand=True)
        table.add_column(justify="right", style="dim")
        table.add_column(style="bold cyan")
        table.add_column(justify="right", style="dim")
        table.add_column(style="bold cyan")
        
        table.add_row(
            "subdomains",
            f"{self.metrics['subdomains']:,}",
            "ports",
            f"{self.metrics['ports']:,}"
        )
        table.add_row(
            "live hosts",
            f"{self.metrics['live_hosts']:,}",
            "urls",
            f"{self.metrics['urls']:,}"
        )
        table.add_row(
            "",
            "",
            "",
            ""
        )
        
        # Vulnerability breakdown
        total_vulns = self.metrics['vulnerabilities']
        if total_vulns > 0:
            table.add_row(
                "vulnerabilities",
                f"[bold red]{total_vulns:,}[/bold red]",
                "",
                ""
            )
            table.add_row(
                "  critical",
                f"[bold red]{self.metrics['critical']}[/bold red]" if self.metrics['critical'] > 0 else "0",
                "  high",
                f"[red]{self.metrics['high']}[/red]" if self.metrics['high'] > 0 else "0"
            )
            table.add_row(
                "  medium",
                f"[yellow]{self.metrics['medium']}[/yellow]" if self.metrics['medium'] > 0 else "0",
                "  low",
                f"[dim]{self.metrics['low']}[/dim]" if self.metrics['low'] > 0 else "0"
            )
        else:
            table.add_row(
                "vulnerabilities",
                "0",
                "",
                ""
            )
        
        return Panel(
            table,
            title="[bold]Live Metrics[/bold]",
            border_style="green",
            box=box.ROUNDED
        )
    
    def _render_findings(self) -> Panel:
        """Render recent vulnerability findings (updating in place)."""
        if not self.recent_findings:
            return Panel(
                Align.center("[dim]No vulnerabilities found yet...[/dim]"),
                title="[bold]Recent Findings[/bold]",
                border_style="yellow",
                box=box.ROUNDED
            )
        
        table = Table(show_header=True, box=box.SIMPLE, padding=(0, 1), expand=True)
        table.add_column("Severity", width=8, style="bold")
        table.add_column("Finding", overflow="fold")
        
        for finding in self.recent_findings[-self.max_findings_display:]:
            severity = finding.get('severity', 'info').upper()
            name = finding.get('name', 'Unknown')
            target = finding.get('target', '')
            
            # Color code severity
            if severity == 'CRITICAL':
                sev_style = "[bold red]CRITICAL[/bold red]"
            elif severity == 'HIGH':
                sev_style = "[red]HIGH[/red]"
            elif severity == 'MEDIUM':
                sev_style = "[yellow]MEDIUM[/yellow]"
            elif severity == 'LOW':
                sev_style = "[dim yellow]LOW[/dim yellow]"
            else:
                sev_style = "[dim]INFO[/dim]"
            
            # Truncate target if too long
            if target and len(target) > 40:
                target = target[:37] + "..."
            
            finding_text = f"{name}"
            if target:
                finding_text += f"\n[dim]{target}[/dim]"
            
            table.add_row(sev_style, finding_text)
        
        return Panel(
            table,
            title=f"[bold]Recent Findings[/bold] [dim]({len(self.recent_findings)} total)[/dim]",
            border_style="yellow",
            box=box.ROUNDED
        )
    
    def _render_footer(self) -> Panel:
        """Render persistent status bar."""
        status_text = Text()
        status_text.append("⚡ ", style="yellow")
        status_text.append("ACTIVE", style="bold yellow")
        status_text.append("  •  ", style="dim")
        
        if self.current_phase_name:
            status_text.append(f"{self.current_phase_name}", style="white")
            status_text.append("  •  ", style="dim")
        
        status_text.append(self.current_activity, style="cyan")
        
        return Panel(
            Align.center(status_text),
            style="dim",
            box=box.ROUNDED
        )
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds into HH:MM:SS or MM:SS."""
        if seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
    
    # Public API for updating state
    
    def set_phases(self, phases: List[Dict]):
        """Set the list of phases to track."""
        self.phases = phases
        self.update()
    
    def set_phase(self, phase_num: int, phase_name: str = "", activity: str = ""):
        """Update current phase."""
        self.current_phase = phase_num
        if phase_name:
            self.current_phase_name = phase_name
        if activity:
            self.current_activity = activity
        
        # Update phase status to 'running'
        if 0 < phase_num <= len(self.phases):
            self.phases[phase_num - 1]['status'] = 'running'
        
        self.update()
        
        # For non-interactive, print phase change
        if not self.is_interactive:
            print(f"\n{'='*60}")
            print(f"  PHASE {phase_num}/{self.total_phases}: {phase_name}")
            print(f"  {activity}")
            print(f"{'='*60}")
    
    def complete_phase(self, phase_num: int, summary: str = ""):
        """Mark a phase as complete."""
        if 0 < phase_num <= len(self.phases):
            self.phases[phase_num - 1]['status'] = 'complete'
            if summary:
                self.phases[phase_num - 1]['details'] = summary
        
        self.update()
        
        # For non-interactive
        if not self.is_interactive and summary:
            print(f"  ✓ {summary}")
    
    def fail_phase(self, phase_num: int, error: str = ""):
        """Mark a phase as failed."""
        if 0 < phase_num <= len(self.phases):
            self.phases[phase_num - 1]['status'] = 'failed'
            if error:
                self.phases[phase_num - 1]['details'] = error
        
        self.update()
        
        # For non-interactive
        if not self.is_interactive and error:
            print(f"  ✗ {error}")
    
    def update_activity(self, activity: str):
        """Update the current activity message."""
        self.current_activity = activity
        self.update()
    
    def update_phase_details(self, phase_num: int, details: str):
        """Update details for a specific phase."""
        if 0 < phase_num <= len(self.phases):
            self.phases[phase_num - 1]['details'] = details
        self.update()
    
    def update_metric(self, key: str, value: int):
        """Update a single metric."""
        if key in self.metrics:
            self.metrics[key] = value
            self.update()
    
    def increment_metric(self, key: str, delta: int = 1):
        """Increment a metric."""
        if key in self.metrics:
            self.metrics[key] += delta
            self.update()
            
            # For non-interactive, print milestone updates
            if not self.is_interactive and key in ['subdomains', 'ports', 'live_hosts', 'vulnerabilities']:
                if self.metrics[key] % 10 == 0:  # Every 10th item
                    print(f"  {key}: {self.metrics[key]}")
    
    def add_finding(self, finding: Dict):
        """
        Add a vulnerability finding.
        Expected keys: 'name', 'severity', 'target'
        """
        self.recent_findings.append(finding)
        
        # Increment vulnerability counters
        self.metrics['vulnerabilities'] += 1
        severity = finding.get('severity', 'info').lower()
        if severity in self.metrics:
            self.metrics[severity] += 1
        
        self.update()
        
        # For non-interactive, print findings
        if not self.is_interactive:
            sev = finding.get('severity', 'INFO').upper()
            name = finding.get('name', 'Unknown')
            target = finding.get('target', '')
            print(f"  [{sev}] {name}")
            if target:
                print(f"    {target}")


# Fallback for graceful degradation
class SimpleFallbackTUI:
    """Simple fallback TUI for non-interactive environments."""
    
    def __init__(self, target_domain: str, total_phases: int = 10):
        self.target_domain = target_domain
        self.total_phases = total_phases
        self.current_phase = 0
        self.metrics = {
            'subdomains': 0,
            'ports': 0,
            'live_hosts': 0,
            'urls': 0,
            'vulnerabilities': 0
        }
    
    def start(self):
        print(f"\n{'='*60}")
        print(f"  TRISHUL ATTACK INITIATED")
        print(f"  Target: {self.target_domain}")
        print(f"  Phases: {self.total_phases}")
        print(f"{'='*60}\n")
    
    def stop(self):
        print(f"\n{'='*60}")
        print(f"  SCAN COMPLETE")
        print(f"{'='*60}\n")
    
    def set_phases(self, phases):
        pass
    
    def set_phase(self, phase_num, phase_name="", activity=""):
        self.current_phase = phase_num
        print(f"\n{'='*60}")
        print(f"  PHASE {phase_num}/{self.total_phases}: {phase_name}")
        if activity:
            print(f"  {activity}")
        print(f"{'='*60}")
    
    def complete_phase(self, phase_num, summary=""):
        if summary:
            print(f"  ✓ {summary}")
    
    def fail_phase(self, phase_num, error=""):
        if error:
            print(f"  ✗ {error}")
    
    def update_activity(self, activity):
        pass
    
    def update_phase_details(self, phase_num, details):
        pass
    
    def update_metric(self, key, value):
        if key in self.metrics:
            self.metrics[key] = value
    
    def increment_metric(self, key, delta=1):
        if key in self.metrics:
            self.metrics[key] += delta
            if self.metrics[key] % 10 == 0:
                print(f"  {key}: {self.metrics[key]}")
    
    def add_finding(self, finding):
        self.metrics['vulnerabilities'] += 1
        sev = finding.get('severity', 'INFO').upper()
        name = finding.get('name', 'Unknown')
        target = finding.get('target', '')
        print(f"  [{sev}] {name}")
        if target:
            print(f"    {target}")
    
    def update(self):
        pass


def create_tui(target_domain: str, total_phases: int = 10):
    """Factory function to create appropriate TUI based on environment."""
    if sys.stdout.isatty() and RICH_AVAILABLE:
        return DynamicTUI(target_domain, total_phases)
    else:
        return SimpleFallbackTUI(target_domain, total_phases)
