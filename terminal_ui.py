"""
Enhanced Terminal UI with streaming effects and interactive elements.
Makes the terminal feel alive like a modern AI assistant.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
from rich.live import Live
from rich.layout import Layout
import time
import sys

class StreamingUI:
    """Provides streaming text effects for terminal output."""
    
    def __init__(self, console=None):
        self.console = console or Console()
        
    def stream_text(self, text: str, style: str = "white", delay: float = 0.02):
        """Stream text character by character for AI-like effect."""
        for char in text:
            self.console.print(char, end="", style=style)
            time.sleep(delay)
        self.console.print()  # Newline at end
    
    def thinking_animation(self, duration: float = 2.0, message: str = "Analyzing"):
        """Show thinking animation with dots."""
        with self.console.status(f"[cyan]{message}...[/cyan]", spinner="dots") as status:
            time.sleep(duration)
    
    def success(self, message: str):
        """Display success message."""
        self.console.print(f"[bold green]✓[/bold green] {message}")
    
    def error(self, message: str):
        """Display error message."""
        self.console.print(f"[bold red]✗[/bold red] {message}")
    
    def warning(self, message: str):
        """Display warning message."""
        self.console.print(f"[bold yellow]⚠[/bold yellow] {message}")
    
    def info(self, message: str):
        """Display info message."""
        self.console.print(f"[cyan]ℹ[/cyan] {message}")
    
    def section_header(self, title: str):
        """Display a section header."""
        self.console.print()
        self.console.rule(f"[bold cyan]{title}[/bold cyan]", style="cyan")
        self.console.print()
    
    def code_block(self, code: str, language: str = "python"):
        """Display a syntax-highlighted code block."""
        from rich.syntax import Syntax
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, border_style="dim", box=box.ROUNDED))
    
    def data_table(self, title: str, headers: list, rows: list, style: str = "cyan"):
        """Display data in a formatted table."""
        table = Table(title=title, border_style=style, box=box.ROUNDED)
        
        for header in headers:
            table.add_column(header, style="white")
        
        for row in rows:
            table.add_row(*[str(cell) for cell in row])
        
        self.console.print(table)
    
    def progress_bar(self, tasks: list, total: int = 100):
        """Display a progress bar for multiple tasks."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            task_ids = []
            for task_name in tasks:
                task_ids.append(progress.add_task(task_name, total=total))
            
            # Simulate progress
            for i in range(total):
                for task_id in task_ids:
                    progress.update(task_id, advance=1)
                time.sleep(0.01)
    
    def panel_message(self, message: str, title: str = "", style: str = "cyan"):
        """Display message in a styled panel."""
        self.console.print(Panel(
            message,
            title=title,
            border_style=style,
            box=box.DOUBLE,
            padding=(1, 2)
        ))
    
    def interactive_prompt(self, question: str, choices: list = None):
        """Display an interactive prompt."""
        self.console.print(f"\n[bold yellow]❓ {question}[/bold yellow]")
        
        if choices:
            for i, choice in enumerate(choices, 1):
                self.console.print(f"  [cyan]{i}.[/cyan] {choice}")
            self.console.print()
        
        return self.console.input("[bold]→ [/bold]")
    
    def celebration(self, message: str):
        """Display a celebration message with emojis."""
        self.console.print()
        self.console.print(Panel(
            f"[bold green]🎉 {message} 🎉[/bold green]",
            border_style="green",
            box=box.DOUBLE_EDGE,
            padding=(1, 4)
        ))
        self.console.print()


class VulnerabilityDisplay:
    """Specialized display for vulnerability findings."""
    
    def __init__(self, console=None):
        self.console = console or Console()
    
    def display_finding(self, finding: dict):
        """Display a single vulnerability finding with rich formatting."""
        
        # Color code by severity
        severity_colors = {
            'CRITICAL': 'bold red',
            'HIGH': 'red',
            'MEDIUM': 'yellow',
            'LOW': 'blue',
            'INFO': 'cyan'
        }
        
        severity = finding.get('severity', 'INFO')
        color = severity_colors.get(severity, 'white')
        
        # Create finding panel
        content = Table.grid(padding=(0, 2))
        content.add_column(style="dim cyan")
        content.add_column(style="white")
        
        content.add_row("Type:", finding.get('type', 'Unknown'))
        content.add_row("Severity:", f"[{color}]{severity}[/{color}]")
        
        if 'url' in finding:
            content.add_row("URL:", finding['url'])
        
        if 'cvss' in finding:
            content.add_row("CVSS:", f"[bold]{finding['cvss']}[/bold]")
        
        if 'description' in finding:
            content.add_row("Description:", finding['description'])
        
        if 'evidence' in finding:
            content.add_row("Evidence:", f"[dim]{finding['evidence']}[/dim]")
        
        if 'impact' in finding:
            content.add_row("Impact:", finding['impact'])
        
        if 'remediation' in finding:
            content.add_row("Fix:", f"[green]{finding['remediation']}[/green]")
        
        self.console.print(Panel(
            content,
            title=f"[bold]{finding.get('type', 'Vulnerability')}[/bold]",
            border_style=color,
            box=box.ROUNDED,
            padding=(1, 2)
        ))
    
    def display_summary(self, findings: list):
        """Display summary of all findings."""
        
        if not findings:
            self.console.print("[green]✓ No vulnerabilities found![/green]")
            return
        
        # Count by severity
        severity_counts = {}
        for finding in findings:
            sev = finding.get('severity', 'INFO')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        # Create summary table
        summary = Table(title="🚨 Vulnerability Summary", border_style="red", box=box.DOUBLE)
        summary.add_column("Severity", style="bold")
        summary.add_column("Count", justify="right", style="bold white")
        summary.add_column("CVSS Range", style="dim")
        
        severity_order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
        cvss_ranges = {
            'CRITICAL': '9.0-10.0',
            'HIGH': '7.0-8.9',
            'MEDIUM': '4.0-6.9',
            'LOW': '0.1-3.9',
            'INFO': '0.0'
        }
        
        for sev in severity_order:
            if sev in severity_counts:
                count = severity_counts[sev]
                color = {
                    'CRITICAL': 'bold red',
                    'HIGH': 'red',
                    'MEDIUM': 'yellow',
                    'LOW': 'blue',
                    'INFO': 'cyan'
                }[sev]
                
                summary.add_row(
                    f"[{color}]{sev}[/{color}]",
                    f"[{color}]{count}[/{color}]",
                    cvss_ranges[sev]
                )
        
        summary.add_row("", "", "")
        summary.add_row(
            "[bold]TOTAL",
            f"[bold]{len(findings)}[/bold]",
            ""
        )
        
        self.console.print()
        self.console.print(summary)
        self.console.print()


# Quick test
if __name__ == "__main__":
    ui = StreamingUI()
    
    ui.section_header("Trishul Terminal UI Demo")
    ui.stream_text("Welcome to the enhanced terminal interface!", style="bold cyan")
    ui.info("System initialized successfully")
    ui.success("All modules loaded")
    ui.warning("This is a demo mode")
    
    ui.thinking_animation(1, "Scanning target")
    
    ui.data_table(
        "Sample Findings",
        ["ID", "Type", "Severity"],
        [
            ["1", "SQL Injection", "CRITICAL"],
            ["2", "XSS", "HIGH"],
            ["3", "IDOR", "MEDIUM"]
        ]
    )
    
    vuln_display = VulnerabilityDisplay()
    vuln_display.display_finding({
        'type': 'IDOR',
        'severity': 'HIGH',
        'url': 'https://target.com/api/user/123',
        'cvss': 7.5,
        'description': 'Horizontal privilege escalation',
        'evidence': 'Accessed user 456 data',
        'impact': 'Unauthorized data access',
        'remediation': 'Implement proper authorization checks'
    })
    
    ui.celebration("Demo Complete!")
