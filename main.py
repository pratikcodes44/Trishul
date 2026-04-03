import argparse
import logging
import sys
import os
import time
import threading

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskProgressColumn
    from rich.table import Table
    from rich.live import Live
    from rich.layout import Layout
    from rich import print as rprint
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.rule import Rule
    from rich import box
    from rich.align import Align
    import time as time_module
    RICH_AVAILABLE = True
    console = Console(force_terminal=True, force_interactive=True)
except ImportError:
    RICH_AVAILABLE = False
    console = None

try:
    from scope_checker import ScopeChecker
    from subfinder_runner import SubfinderRunner
    from asset_manager import AssetManager
    from port_scanner import PortScanner
    from live_host_prober import LiveHostProber
    from katana_runner import KatanaRunner
    from nuclei_runner import NucleiRunner
    from notifier import ReconNotifier
    from report_writer import ReportWriter
    from bounty_scout import BountyScout
    from ticket_writer import TicketWriter  
    from gau_runner import TimeMachine
    from discord_notifier import DiscordNotifier
    from osint.osint_gatherer import OSINTGatherer
    from subdomain_takeover import SubdomainTakeoverValidator
    from idor_tester import IDORTester
    from graphql_api_scanner import GraphQLAPIScanner
    from terminal_ui import StreamingUI, VulnerabilityDisplay
    from scope_validator import ScopeValidator
    from audit_logger import init_audit_logger, get_audit_logger
    from cdn_detector import CDNDetector, format_cdn_info
except ImportError as e:
    logging.error(f"Import Error: {e}")
    sys.exit(1)

BANNER = """
[bold cyan]
  ████████╗██████╗ ██╗███████╗██╗  ██╗██╗   ██╗██╗     
  ╚══██╔══╝██╔══██╗██║██╔════╝██║  ██║██║   ██║██║     
     ██║   ██████╔╝██║███████╗███████║██║   ██║██║     
     ██║   ██╔══██╗██║╚════██║██╔══██║██║   ██║██║     
     ██║   ██║  ██║██║███████║██║  ██║╚██████╔╝███████╗
     ╚═╝   ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
[/bold cyan]
[bold yellow]   🔱 AI-POWERED AUTONOMOUS SECURITY PLATFORM 🔱[/bold yellow]
[dim italic]      Enterprise Attack Surface Management | Bug Bounty Automation[/dim italic]
"""

def print_banner():
    """Display the Trishul banner with animation."""
    if RICH_AVAILABLE:
        # Clear screen for clean start
        console.clear()
        
        # Animated banner reveal
        console.print(Panel(
            BANNER,
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        ))
        
        # System info
        import platform
        import sys
        
        info_table = Table(show_header=False, box=None, padding=(0, 1), border_style="dim")
        info_table.add_column("", style="dim cyan")
        info_table.add_column("", style="dim white")
        
        info_table.add_row("🖥️  System", f"{platform.system()} {platform.release()}")
        info_table.add_row("🐍 Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        info_table.add_row("🔧 Mode", "Interactive AI Assistant")
        info_table.add_row("⚡ Status", "[green]READY[/green]")
        
        console.print(info_table)
        console.print()
    else:
        print(BANNER)


def show_legal_disclaimer():
    """Display legal disclaimer and require consent"""
    disclaimer_text = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                          ⚖️  LEGAL DISCLAIMER ⚖️                           ║
╠═══════════════════════════════════════════════════════════════════════════╣
║                                                                           ║
║  You are about to perform security testing. By continuing, you confirm:  ║
║                                                                           ║
║  ✓ You have EXPLICIT WRITTEN AUTHORIZATION from the target owner         ║
║  ✓ Testing is within authorized scope of a bug bounty program            ║
║  ✓ You will comply with program rules and rate limits                    ║
║  ✓ You will NOT access, modify, or exfiltrate sensitive data             ║
║  ✓ You understand unauthorized testing may violate laws                  ║
║                                                                           ║
║  ⚠️  UNAUTHORIZED ACCESS TO COMPUTER SYSTEMS IS ILLEGAL                   ║
║                                                                           ║
║  This may violate:                                                        ║
║  • Computer Fraud and Abuse Act (CFAA) - USA - Up to 10 years prison    ║
║  • Computer Misuse Act 1990 - UK - Up to 2 years prison                 ║
║  • EU Cybercrime Directive - Criminal penalties vary by country          ║
║  • Local cybercrime laws in your jurisdiction                            ║
║                                                                           ║
║  THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY.                       ║
║  You assume ALL legal liability for your actions.                         ║
║                                                                           ║
║  Full terms: See TERMS_OF_SERVICE.md                                      ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""
    
    if RICH_AVAILABLE:
        console.print(disclaimer_text, style="bold yellow")
    else:
        print(disclaimer_text)
    
    print()
    response = input("I have authorization and agree to these terms (type 'I AGREE'): ").strip()
    
    # Log consent
    audit_logger = get_audit_logger()
    if audit_logger:
        audit_logger.log_consent(
            consent_given=(response == 'I AGREE'),
            disclaimer_text=disclaimer_text
        )
    
    if response != 'I AGREE':
        print("\n❌ Scan aborted. You must have authorization to proceed.")
        print("See TERMS_OF_SERVICE.md for details.\n")
        sys.exit(0)
    
    if RICH_AVAILABLE:
        console.print("✅ Consent recorded. Proceeding with scan...\n", style="green")
    else:
        print("✅ Consent recorded. Proceeding with scan...\n")


# Pipeline phases with their details
PIPELINE_PHASES = [
    {"name": "OSINT Reconnaissance", "tool": "Multi-Source", "icon": "🔍"},
    {"name": "Subdomain Discovery", "tool": "Subfinder", "icon": "🔍"},
    {"name": "Subdomain Takeover Check", "tool": "TakeoverValidator", "icon": "🎯"},
    {"name": "Port Scanning", "tool": "Naabu", "icon": "🔌"},
    {"name": "Live Host Probing", "tool": "HTTPX", "icon": "🌐"},
    {"name": "GraphQL/API Discovery", "tool": "GraphQLScanner", "icon": "📡"},
    {"name": "Web Crawling", "tool": "Katana", "icon": "🕷️"},
    {"name": "Historical Mining", "tool": "GAU", "icon": "⏳"},
    {"name": "IDOR Testing", "tool": "IDORTester", "icon": "🔓"},
    {"name": "Vulnerability Scan", "tool": "Nuclei", "icon": "🎯"},
]

class AttackProgressTracker:
    """Real-time progress tracker for the attack pipeline."""
    
    def __init__(self, target_domain):
        self.target_domain = target_domain
        self.start_time = None
        self.current_phase = 0
        self.total_phases = len(PIPELINE_PHASES)
        self.phase_stats = {}
        self.live_display = None
        self.is_running = False
        
        # Stats
        self.subdomains_found = 0
        self.ports_found = 0
        self.live_hosts = 0
        self.urls_crawled = 0
        self.historical_urls = 0
        self.vulnerabilities_found = 0
        self.current_targets = 0
        
    def generate_display(self):
        """Generate the live display with enhanced UI."""
        if not RICH_AVAILABLE:
            return ""
            
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        # Create main panel with gradient border
        layout = Layout()
        
        # Header with animated status
        header = Table.grid(padding=(0, 2))
        header.add_column(style="bold cyan", justify="left")
        header.add_column(style="bold white", justify="right")
        
        # Animated dots for "thinking" effect
        dots = "." * (int(elapsed * 2) % 4)
        header.add_row(
            f"🔱 [bold cyan]TRISHUL ACTIVE[/bold cyan] {dots}",
            f"[dim]Phase {self.current_phase}/{self.total_phases}[/dim]"
        )
        
        # Target info panel
        target_panel = Panel(
            f"[bold white]{self.target_domain}[/bold white]\n"
            f"[dim]⏱️  Elapsed: {self._format_time(elapsed)}[/dim]",
            title="🎯 [bold]Target[/bold]",
            border_style="cyan",
            box=box.ROUNDED
        )
        
        # Real-time findings with color coding
        findings_grid = Table.grid(padding=(0, 3))
        findings_grid.add_column(style="cyan", justify="left")
        findings_grid.add_column(style="bold white", justify="right")
        findings_grid.add_column(style="cyan", justify="left")
        findings_grid.add_column(style="bold white", justify="right")
        
        findings_grid.add_row(
            "🔍 Subdomains", f"[cyan]{self.subdomains_found}[/cyan]",
            "🔌 Ports", f"[cyan]{self.ports_found}[/cyan]"
        )
        findings_grid.add_row(
            "🌐 Live Hosts", f"[green]{self.live_hosts}[/green]",
            "🕷️  URLs", f"[yellow]{self.urls_crawled + self.historical_urls}[/yellow]"
        )
        findings_grid.add_row(
            "🐛 Vulnerabilities", 
            f"[bold red]{self.vulnerabilities_found}[/bold red]" if self.vulnerabilities_found > 0 else "[dim]0[/dim]",
            "🎯 Targets", 
            f"[magenta]{self.current_targets}[/magenta]" if self.current_targets > 0 else "[dim]0[/dim]"
        )
        
        findings_panel = Panel(
            findings_grid,
            title="📊 [bold]Live Metrics[/bold]",
            border_style="green",
            box=box.ROUNDED
        )
        
        # Phase pipeline with enhanced styling
        phase_table = Table(
            show_header=True, 
            header_style="bold magenta",
            border_style="dim cyan",
            box=box.SIMPLE_HEAD,
            expand=True,
            padding=(0, 1)
        )
        phase_table.add_column("", width=2, justify="center", style="dim")
        phase_table.add_column("Phase", width=28, no_wrap=True)
        phase_table.add_column("Status", width=18, justify="center")
        phase_table.add_column("Details", width=35, style="dim")
        
        for i, phase in enumerate(PIPELINE_PHASES):
            phase_num = i + 1
            
            if phase_num < self.current_phase:
                # Completed - green checkmark
                icon = "✓"
                status_icon = "●"
                status = "[green]COMPLETE[/green]"
                details = self.phase_stats.get(phase["name"], "")
                name_style = "dim green"
            elif phase_num == self.current_phase:
                # In progress - animated
                spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                spinner = spinner_frames[int(elapsed * 5) % len(spinner_frames)]
                icon = spinner
                status_icon = "◉"
                status = "[bold yellow]RUNNING[/bold yellow]"
                details = f"[yellow]{self.current_targets} targets active[/yellow]" if self.current_targets > 0 else "[yellow]Initializing...[/yellow]"
                name_style = "bold white"
            else:
                # Pending - dimmed
                icon = "○"
                status_icon = "○"
                status = "[dim]QUEUED[/dim]"
                details = "[dim]Awaiting...[/dim]"
                name_style = "dim"
            
            phase_table.add_row(
                icon,
                f"[{name_style}]{phase['icon']} {phase['name']}[/{name_style}]",
                f"{status_icon} {status}",
                details
            )
        
        # Combine everything
        from rich.columns import Columns
        
        top_panels = Columns([target_panel, findings_panel], equal=True, expand=True)
        
        # Final layout with panels
        final_display = Table.grid(padding=(1, 0))
        final_display.add_row(header)
        final_display.add_row(top_panels)
        final_display.add_row(
            Panel(
                phase_table,
                title="🚀 [bold]Attack Pipeline[/bold]",
                border_style="magenta",
                box=box.ROUNDED
            )
        )
        
        return Panel(
            final_display,
            border_style="bold cyan",
            box=box.DOUBLE_EDGE,
            padding=(1, 2)
        )
        
    
    def _format_time(self, seconds):
        """Format seconds into MM:SS or HH:MM:SS."""
        if seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours:02d}:{mins:02d}:{secs:02d}"
    
    def start(self):
        """Start the progress tracker."""
        self.start_time = time.time()
        self.is_running = True
        if RICH_AVAILABLE:
            self.live_display = Live(self.generate_display(), console=console, refresh_per_second=2)
            self.live_display.start()
    
    def stop(self):
        """Stop the progress tracker."""
        self.is_running = False
        if self.live_display:
            self.live_display.stop()
    
    def update(self):
        """Update the live display."""
        if self.live_display and RICH_AVAILABLE:
            self.live_display.update(self.generate_display())
    
    def set_phase(self, phase_num, details=""):
        """Set the current phase."""
        self.current_phase = phase_num
        if details and phase_num > 0:
            phase_name = PIPELINE_PHASES[phase_num - 1]["name"]
            self.phase_stats[phase_name] = details
        self.update()
    
    def set_targets(self, count):
        """Set the current number of targets being processed."""
        self.current_targets = count
        self.update()
    
    def log_finding(self, finding_type, count):
        """Log a finding."""
        if finding_type == "subdomains":
            self.subdomains_found = count
        elif finding_type == "ports":
            self.ports_found = count
        elif finding_type == "live_hosts":
            self.live_hosts = count
        elif finding_type == "urls":
            self.urls_crawled = count
        elif finding_type == "historical":
            self.historical_urls = count
        elif finding_type == "vulnerabilities":
            self.vulnerabilities_found = count
        self.update()
    
    def complete_phase(self, phase_num, summary=""):
        """Mark a phase as complete."""
        if phase_num > 0 and phase_num <= len(PIPELINE_PHASES):
            phase_name = PIPELINE_PHASES[phase_num - 1]["name"]
            self.phase_stats[phase_name] = summary
        self.current_targets = 0
        self.update()


class NucleiProgressDisplay:
    """Real-time Nuclei scanner progress display."""
    
    def __init__(self):
        self.panel = None
        self.last_update = 0
        
    def create_display(self, stats):
        """Create Rich panel with Nuclei stats."""
        if not RICH_AVAILABLE:
            return None
        
        from rich.table import Table
        from rich.panel import Panel
        
        # Format ETA
        eta_minutes = stats['eta_seconds'] // 60
        eta_seconds = stats['eta_seconds'] % 60
        eta_str = f"{eta_minutes}m {eta_seconds}s" if eta_minutes > 0 else f"{eta_seconds}s"
        
        # Calculate progress percentage
        progress_pct = 0
        if stats['requests_total'] > 0:
            progress_pct = (stats['requests_sent'] / stats['requests_total']) * 100
        
        # Create progress bar
        bar_length = 40
        filled = int((progress_pct / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        # Build display table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Metric", style="cyan", width=20)
        table.add_column("Value", style="white")
        
        table.add_row("🎯 Targets:", str(len(stats.get('target_urls', [])) if 'target_urls' in stats else 'N/A'))
        table.add_row("📋 Templates:", f"{stats['templates_loaded']:,}")
        table.add_row("🔥 Requests Sent:", f"{stats['requests_sent']:,} / {stats['requests_total']:,}")
        table.add_row("⚡ Rate:", f"{stats['rps']} req/s")
        table.add_row("⏱️  ETA:", eta_str)
        table.add_row("🐛 Vulnerabilities:", f"[bold red]{stats['vulnerabilities']}[/]" if stats['vulnerabilities'] > 0 else "0")
        table.add_row("", "")
        table.add_row("Progress:", f"{bar} {progress_pct:.1f}%")
        
        if stats['current_template']:
            table.add_row("", "")
            table.add_row("💬 Current:", f"[cyan]{stats['current_template'][:50]}...[/]")
        
        # Add heartbeat
        elapsed = stats['elapsed']
        table.add_row("❤️  Activity:", f"{elapsed}s ago" if elapsed < 5 else "[dim]Active[/]")
        
        panel = Panel(
            table,
            title="[bold yellow]⚡ NUCLEI ATTACK METRICS ⚡[/]",
            border_style="yellow",
            padding=(0, 1)
        )
        
        return panel
    
    def update_display(self, live_display, stats):
        """Update the live display with new stats."""
        # Throttle updates to once per second
        current_time = time.time()
        if current_time - self.last_update < 1:
            return
        
        self.last_update = current_time
        panel = self.create_display(stats)
        if panel and live_display:
            live_display.update(panel)


def print_banner():
    if RICH_AVAILABLE:
        console.print(BANNER)
    else:
        print("\n" + "="*60)
        print(" 🔱 PROJECT TRISHUL: AUTONOMOUS CYBERSECURITY PLATFORM 🔱 ")
        print("="*60)

def print_target_info(platform, target_domain, program_url, mode_choice):
    if RICH_AVAILABLE:
        table = Table(title="🎯 TARGET ACQUIRED", show_header=False, border_style="green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("🏢 Platform", platform)
        table.add_row("🌐 Target", target_domain)
        if mode_choice == '2' and program_url:
            table.add_row("🔗 Policy Link", program_url)
        console.print(table)
    else:
        print("\n" + "="*50)
        print(" 🎯 TRISHUL TARGET ACQUIRED")
        print("="*50)
        print(f"🏢 Platform    : {platform}")
        print(f"🌐 Target      : {target_domain}")
        if mode_choice == '2':
            print(f"🔗 Policy Link : {program_url}")
        print("="*50)

def estimate_attack_time(target_domain, is_demo=False):
    """
    Estimates the total time required for the full reconnaissance pipeline.
    Returns estimated time in minutes and a breakdown of each phase.
    """
    # Time estimates per phase (in seconds) - based on typical scan times
    # These are conservative estimates for a medium-sized target
    
    if is_demo:
        # Demo mode is much faster (localhost, few endpoints)
        estimates = {
            "Subdomain Discovery (Subfinder)": 5,
            "Port Scanning (Naabu)": 10,
            "Live Host Probing (HTTPX)": 5,
            "Web Crawling (Katana)": 15,
            "Historical URL Mining (GAU)": 10,
            "Vulnerability Scanning (Nuclei)": 60,
        }
    else:
        # Real target estimates (can vary significantly based on target size)
        estimates = {
            "Subdomain Discovery (Subfinder)": 120,      # 2 min
            "Port Scanning (Naabu)": 180,                # 3 min  
            "Live Host Probing (HTTPX)": 120,            # 2 min
            "Web Crawling (Katana)": 300,                # 5 min
            "Historical URL Mining (GAU)": 180,          # 3 min
            "Vulnerability Scanning (Nuclei)": 600,      # 10 min (largest phase)
        }
    
    total_seconds = sum(estimates.values())
    total_minutes = total_seconds / 60
    
    return total_minutes, estimates

def format_time(seconds):
    """Formats seconds into a human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s" if secs > 0 else f"{mins}m"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"

def display_time_estimate(target_domain, is_demo=False):
    """
    Displays the estimated attack time and asks for user confirmation.
    Returns True if user confirms, False otherwise.
    """
    total_minutes, phase_estimates = estimate_attack_time(target_domain, is_demo)
    total_seconds = sum(phase_estimates.values())
    
    if RICH_AVAILABLE:
        console.print("\n[bold yellow]⏱️  ATTACK TIME ESTIMATION[/bold yellow]")
        
        table = Table(show_header=True, header_style="bold cyan", border_style="dim")
        table.add_column("Phase", style="white")
        table.add_column("Estimated Time", justify="right", style="green")
        
        for phase, seconds in phase_estimates.items():
            table.add_row(phase, format_time(seconds))
        
        table.add_row("─" * 35, "─" * 12, style="dim")
        table.add_row("[bold]TOTAL ESTIMATED TIME[/bold]", f"[bold yellow]{format_time(total_seconds)}[/bold yellow]")
        
        console.print(table)
        
        if is_demo:
            console.print("\n[dim]Note: Demo mode runs against localhost - actual time may be shorter.[/dim]")
        else:
            console.print("\n[dim]Note: Actual time may vary based on target size, network speed, and WAF presence.[/dim]")
        
        console.print(f"\n[yellow]Do you want to proceed with the attack on [bold]{target_domain}[/bold]?[/yellow]")
    else:
        print("\n" + "="*50)
        print(" ⏱️  ATTACK TIME ESTIMATION")
        print("="*50)
        
        for phase, seconds in phase_estimates.items():
            print(f"  {phase}: {format_time(seconds)}")
        
        print("-"*50)
        print(f"  TOTAL ESTIMATED TIME: {format_time(total_seconds)}")
        print("="*50)
        
        if is_demo:
            print("Note: Demo mode - actual time may be shorter.")
        else:
            print("Note: Actual time may vary based on target size and network.")
        
        print(f"\nDo you want to proceed with the attack on {target_domain}?")
    
    choice = input("[y/N]: ").strip().lower()
    return choice == 'y'

def main():
    parser = argparse.ArgumentParser(
        description="Project Trishul - EASM & Bug Bounty Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive mode
  python main.py -d target.com -m 2 -y              # Auto bug bounty mode
  python main.py -d staging.company.com -m 1        # Enterprise audit mode
  python main.py --demo                             # Safe local demo
  python main.py -d target.com --scope scope.txt    # With scope validation
  python main.py -d target.com --read-only          # Read-only mode
        """
    )
    parser.add_argument("-d", "--domain", help="Target domain to scan")
    parser.add_argument("-m", "--mode", choices=['1', '2'], default='2',
                        help="Mode: 1=Enterprise Audit, 2=Bug Bounty (default: 2)")
    parser.add_argument("-c", "--cookie", help="Session cookie for authenticated scanning")
    parser.add_argument("-y", "--yes", action="store_true", help="Auto-authorize (no prompts)")
    parser.add_argument("--demo", action="store_true", help="Run demo against local vulnerable_arena.py")
    parser.add_argument("--scope", help="Scope file with authorized targets (RECOMMENDED)")
    parser.add_argument("--read-only", action="store_true", default=True, help="Read-only mode (no POST/PUT/DELETE) [default: ON]")
    parser.add_argument("--allow-writes", action="store_true", help="Allow POST/PUT/DELETE requests (use with caution)")
    parser.add_argument("--request-delay", type=float, default=0.5, help="Delay between requests in seconds (default: 0.5)")
    parser.add_argument("--max-idor-tests", type=int, default=20, help="Max IDOR fuzzing per URL (default: 20)")
    parser.add_argument("--no-audit-log", action="store_true", help="Disable audit logging (not recommended)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize audit logger FIRST
    audit_enabled = not args.no_audit_log
    init_audit_logger("audit_log.jsonl", enabled=audit_enabled)
    audit_logger = get_audit_logger()
    
    if audit_enabled:
        print("✓ Audit logging enabled: audit_log.jsonl\n")
    else:
        print("⚠️  Audit logging DISABLED (not recommended for legal compliance)\n")
    
    print_banner()
    
    # Show legal disclaimer (REQUIRED)
    if not args.demo:
        show_legal_disclaimer()
    
    # Initialize scope validator
    scope_validator = None
    if args.scope:
        scope_validator = ScopeValidator(args.scope, strict_mode=True)
        print(f"✓ Scope validation enabled: {args.scope}\n")
    elif not args.demo:
        print("⚠️  WARNING: No scope file provided!")
        print("Use --scope flag to validate targets against authorized scope.")
        print("Example: python main.py -d target.com --scope scope.txt\n")
        response = input("Continue without scope validation? (type 'YES'): ").strip()
        if response != 'YES':
            print("❌ Scan aborted. Use --scope flag or create scope.txt")
            print("Run: python scope_validator.py create-example")
            sys.exit(0)
    
    # Read-only mode
    read_only = args.read_only and not args.allow_writes
    if read_only:
        print("✓ Read-only mode: POST/PUT/DELETE requests disabled\n")
    else:
        print("⚠️  Write operations enabled (use with caution)\n")
    
    scout = BountyScout()
    reporter = ReportWriter()
    ticket_generator = TicketWriter()  
    scope_checker = ScopeChecker()
    subfinder = SubfinderRunner()
    asset_manager = AssetManager()
    scanner_ports = PortScanner()
    prober = LiveHostProber()
    crawler = KatanaRunner()
    scanner = NucleiRunner()
    time_machine = TimeMachine()           
    alert_system = ReconNotifier("discord")

    target_domain = ""
    program_url = ""
    platform = ""
    cookie = args.cookie 
    mode_choice = args.mode

    # Demo mode - run against local vulnerable_arena.py
    if args.demo:
        target_domain = "127.0.0.1:5000"
        mode_choice = '1'
        platform = "🧪 LOCAL DEMO (vulnerable_arena.py)"
        program_url = "http://127.0.0.1:5000"
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                "[yellow]⚠️  DEMO MODE ACTIVE[/yellow]\n"
                "Ensure vulnerable_arena.py is running:\n"
                "[cyan]python vulnerable_arena.py[/cyan]",
                border_style="yellow"
            ))
        else:
            print("\n⚠️  DEMO MODE: Ensure vulnerable_arena.py is running!")
    elif args.domain:
        # Validate scope if enabled
        if scope_validator:
            is_valid = scope_validator.validate_or_exit(args.domain)
            if audit_logger:
                audit_logger.log_scope_validation(args.domain, is_valid, "Initial target validation")
        
        target_domain = args.domain
        mode_choice = args.mode if args.mode else '2' 
        
        if mode_choice == '1':
            platform = "Internal Enterprise Target (CLI Override)"
            program_url = "Internal Ticket System"
        else:
            platform = "Manual CLI Target"
            program_url = "N/A (Manual Override)"
            
        if RICH_AVAILABLE:
            console.print(f"[green]⚡ CLI OVERRIDE:[/green] Mode {mode_choice} against [cyan]{target_domain}[/cyan]")
        else:
            print(f"\n⚡ CLI OVERRIDE: Executing Mode {mode_choice} against {target_domain}")
        
    else:
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]Select Operating Mode:[/bold cyan]")
            console.print("  [1] 🛡️  VIRTUAL SECURITY ENGINEER (Enterprise/Internal Audit)")
            console.print("  [2] 🥷 BUG BOUNTY HUNTER (Autonomous External Strike)")
        else:
            print("  [1] VIRTUAL SECURITY ENGINEER (Enterprise/Internal Audit)")
            print("  [2] BUG BOUNTY HUNTER (Autonomous External Strike)")
        
        mode_choice = input("\nSelect Operating Mode [1 or 2]: ").strip()

        if mode_choice == '1':
            if RICH_AVAILABLE:
                console.print("\n[green]🛡️ INITIALIZING VIRTUAL SECURITY ENGINEER MODE...[/green]")
            else:
                print("\n🛡️ INITIALIZING VIRTUAL SECURITY ENGINEER MODE...")
            
            # SECURITY: Validate domain input
            import re
            while True:
                target_domain = input("Enter the enterprise domain to audit (e.g., staging.company.com): ").strip()
                # Basic domain validation (alphanumeric, dots, hyphens)
                if re.match(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', target_domain):
                    break
                print("❌ Invalid domain format. Please use format: example.com or subdomain.example.com")
            
            # SECURITY: Validate cookie input
            cookie_input = input("Enter valid Session Cookie for deep scanning (or press Enter to skip): ").strip()
            if cookie_input:
                # Strip control characters that could cause header injection
                cookie = cookie_input.replace('\n', '').replace('\r', '').replace('\t', '')
                if cookie != cookie_input:
                    print("⚠️  Removed invalid characters from cookie")
                print("[+] Authenticated Scanning Enabled.")
            platform = "Internal Enterprise Target"
            program_url = "Internal Ticket System"
        elif mode_choice == '2':
            if RICH_AVAILABLE:
                console.print("\n[green]🥷 INITIALIZING BUG BOUNTY HUNTER MODE...[/green]")
            else:
                print("\n🥷 INITIALIZING BUG BOUNTY HUNTER MODE...")
            target_data = scout.get_random_target()
            if not target_data:
                logging.error("Could not find a target. Exiting.")
                sys.exit(1)
            target_domain = target_data["domain"]
            program_url = target_data["url"]
            platform = target_data["platform"]
        else:
            print("Invalid choice. Shutting down.")
            sys.exit(1)

    print_target_info(platform, target_domain, program_url, mode_choice)

    # Show time estimation and ask for confirmation
    if not args.yes:
        is_demo = args.demo or "127.0.0.1" in target_domain
        if not display_time_estimate(target_domain, is_demo=is_demo):
            if RICH_AVAILABLE:
                console.print("[red]Mission aborted. Returning to sleep mode.[/red]")
            else:
                print("Mission aborted. Returning to sleep mode.")
            sys.exit(0)

    if RICH_AVAILABLE:
        console.print(f"\n[green]✅ Weapons authorized. Initiating strike on: [bold]{target_domain}[/bold][/green]\n")
    else:
        logging.info(f"Weapons authorized. Initiating strike on: {target_domain}")

    # Log scan start
    scan_start_time = time.time()
    if audit_logger:
        audit_logger.log_scan_start(
            target=target_domain,
            mode="Enterprise Audit" if mode_choice == '1' else "Bug Bounty",
            options={
                'platform': platform,
                'authenticated': bool(cookie),
                'read_only': read_only,
                'request_delay': args.request_delay,
                'max_idor_tests': args.max_idor_tests,
                'scope_file': args.scope if args.scope else None
            }
        )

    # Initialize progress tracker
    tracker = AttackProgressTracker(target_domain)
    
    try:
        # Start live progress display
        tracker.start()
        
        # ========== PHASE 0: OSINT RECONNAISSANCE ==========
        if RICH_AVAILABLE:
            console.print("\n[bold cyan]🔍 PHASE 0: Passive OSINT Reconnaissance[/bold cyan]")
        
        tracker.set_phase(1)
        osint_gatherer = OSINTGatherer(target_domain)
        
        osint_subdomains = set()
        
        def osint_progress(module, status, count=0):
            """Callback for OSINT progress updates."""
            if status == "running":
                tracker.update()
                if RICH_AVAILABLE:
                    console.print(f"[yellow]⚡ Running {module}...[/yellow]")
            elif status == "done":
                if RICH_AVAILABLE:
                    console.print(f"[green]✅ {module}: Found {count} items[/green]")
            elif status == "error":
                if RICH_AVAILABLE:
                    console.print(f"[red]❌ {module}: Failed[/red]")
        
        try:
            osint_findings = osint_gatherer.gather_all(progress_callback=osint_progress)
            osint_subdomains = osint_findings.get('subdomains', set())
            
            summary = osint_gatherer.get_summary()
            if RICH_AVAILABLE:
                osint_table = Table(title="🔍 OSINT SUMMARY", border_style="cyan")
                osint_table.add_column("Finding Type", style="cyan")
                osint_table.add_column("Count", style="green", justify="right")
                osint_table.add_row("📜 Subdomains (CT Logs)", str(summary['subdomains_count']))
                osint_table.add_row("🔎 GitHub Leaks", str(summary['github_leaks_count']))
                osint_table.add_row("☁️  Cloud Buckets", str(summary['cloud_buckets_count']))
                osint_table.add_row("🔧 Technologies", str(summary['technologies_count']))
                console.print(osint_table)
            
            tracker.complete_phase(1, f"OSINT: {summary['subdomains_count']} subdomains")
        except Exception as e:
            logger.error(f"OSINT reconnaissance failed: {e}")
            tracker.complete_phase(1, "OSINT: Failed (continuing with active recon)")
        
        # ========== PHASE 1: Subdomain Discovery (Active) ==========
        tracker.set_phase(2)
        tracker.set_targets(1)
        
        if RICH_AVAILABLE:
            with console.status("[cyan]🔍 Discovering subdomains (Subfinder)...") as status:
                raw_subs = subfinder.discover_subdomains(target_domain)
                status.update("[green]✅ Subfinder complete")
        else:
            raw_subs = subfinder.discover_subdomains(target_domain)
        
        # Merge OSINT and active subdomain discoveries
        raw_subs.extend(list(osint_subdomains))
        raw_subs.append(target_domain)
        raw_subs = list(set(raw_subs))
        
        in_scope = [s for s in raw_subs if scope_checker.is_in_scope(s, target_domain)]
        new_discoveries = asset_manager.insert_and_diff(in_scope)
        tracker.log_finding("subdomains", len(new_discoveries))
        tracker.complete_phase(2, f"Found {len(new_discoveries)} new")

        # ========== PHASE 2.5: Subdomain Takeover Check ==========
        if new_discoveries:
            tracker.set_phase(3)
            tracker.set_targets(len(new_discoveries))
            
            if RICH_AVAILABLE:
                with console.status(f"[cyan]🎯 Checking {len(new_discoveries)} subdomains for takeover...") as status:
                    takeover_validator = SubdomainTakeoverValidator()
                    takeover_findings = takeover_validator.check_subdomains(new_discoveries)
                    status.update(f"[green]✅ Takeover check complete")
            else:
                takeover_validator = SubdomainTakeoverValidator()
                takeover_findings = takeover_validator.check_subdomains(new_discoveries)
            
            if takeover_findings:
                tracker.log_finding("takeover_vulns", len(takeover_findings))
                if RICH_AVAILABLE:
                    console.print(f"[red]🚨 CRITICAL: {len(takeover_findings)} subdomain takeover vulnerabilities![/red]")
                    for finding in takeover_findings:
                        console.print(f"   [yellow]→ {finding['subdomain']} ({finding['provider']})[/yellow]")
                logger.warning(takeover_validator.generate_report(takeover_findings))
            
            tracker.complete_phase(3, f"Found {len(takeover_findings)} takeovers" if takeover_findings else "No takeovers")

        if new_discoveries:
            # ========== PHASE 3: Port Scanning ==========
            tracker.set_phase(4)
            tracker.set_targets(len(new_discoveries))
            
            if RICH_AVAILABLE:
                with console.status(f"[cyan]🔌 Scanning ports on {len(new_discoveries)} hosts...") as status:
                    targets_with_ports = scanner_ports.scan_ports(new_discoveries)
                    status.update(f"[green]✅ Found {len(targets_with_ports)} open ports")
            else:
                targets_with_ports = scanner_ports.scan_ports(new_discoveries)
            
            tracker.log_finding("ports", len(targets_with_ports))
            tracker.complete_phase(3, f"{len(targets_with_ports)} open ports")

            if targets_with_ports:
                # ========== PHASE 3: Live Host Probing ==========
                tracker.set_phase(4)
                tracker.set_targets(len(targets_with_ports))
                
                if RICH_AVAILABLE:
                    with console.status(f"[cyan]🌐 Probing {len(targets_with_ports)} hosts...") as status:
                        live_results = prober.probe(targets_with_ports)
                        status.update(f"[green]✅ Found {len(live_results)} live hosts")
                else:
                    live_results = prober.probe(targets_with_ports)
                
                if live_results:
                    raw_urls = [line.split(" ")[1] for line in live_results if len(line.split(" ")) > 1 and line.split(" ")[1].startswith("http")]
                    tracker.log_finding("live_hosts", len(raw_urls))
                    tracker.complete_phase(4, f"{len(raw_urls)} live hosts")
                    
                    if raw_urls:
                        # ========== PHASE 4: Web Crawling ==========
                        tracker.set_phase(5)
                        tracker.set_targets(len(raw_urls))
                        
                        if RICH_AVAILABLE:
                            with console.status(f"[cyan]🕷️  Crawling {len(raw_urls)} websites...") as status:
                                deep_urls = crawler.crawl(raw_urls, cookie=cookie)
                                status.update(f"[green]✅ Found {len(deep_urls)} endpoints")
                        else:
                            deep_urls = crawler.crawl(raw_urls, cookie=cookie)
                        
                        tracker.log_finding("urls", len(deep_urls))
                        tracker.complete_phase(5, f"{len(deep_urls)} endpoints")
                        
                        # ========== PHASE 5.5: GraphQL/API Discovery ==========
                        tracker.set_phase(6)
                        tracker.set_targets(len(raw_urls))
                        
                        graphql_findings = []
                        if RICH_AVAILABLE:
                            with console.status(f"[cyan]📡 Scanning {len(raw_urls)} hosts for GraphQL/API...") as status:
                                graphql_scanner = GraphQLAPIScanner()
                                for url in raw_urls[:10]:  # Limit to first 10 hosts for performance
                                    try:
                                        findings = graphql_scanner.scan_target(url, cookies={'session': cookie} if cookie else None)
                                        graphql_findings.extend(findings)
                                    except Exception as e:
                                        logger.debug(f"GraphQL scan error on {url}: {e}")
                                status.update(f"[green]✅ GraphQL/API scan complete")
                        else:
                            graphql_scanner = GraphQLAPIScanner()
                            for url in raw_urls[:10]:
                                try:
                                    findings = graphql_scanner.scan_target(url)
                                    graphql_findings.extend(findings)
                                except:
                                    pass
                        
                        if graphql_findings:
                            tracker.log_finding("graphql_vulns", len(graphql_findings))
                            if RICH_AVAILABLE:
                                console.print(f"[red]🚨 Found {len(graphql_findings)} GraphQL/API vulnerabilities![/red]")
                            logger.warning(graphql_scanner.generate_report(graphql_findings))
                        
                        tracker.complete_phase(6, f"Found {len(graphql_findings)} API vulns" if graphql_findings else "No API vulns")
                        
                        # ========== PHASE 6: Historical Mining ==========
                        tracker.set_phase(7)
                        tracker.set_targets(1)
                        
                        if RICH_AVAILABLE:
                            with console.status("[cyan]⏳ Mining Wayback Machine...") as status:
                                historical_raw = time_machine.fetch_history(target_domain)
                                status.update(f"[yellow]Probing historical endpoints...")
                        else:
                            historical_raw = time_machine.fetch_history(target_domain)
                        
                        live_historical = []
                        
                        if historical_raw:
                            tracker.set_targets(len(historical_raw))
                            historical_probed = prober.probe(historical_raw)
                            if historical_probed:
                                live_historical = [line.split(" ")[1] for line in historical_probed if len(line.split(" ")) > 1 and line.split(" ")[1].startswith("http")]
                        
                        tracker.log_finding("historical", len(live_historical))
                        tracker.complete_phase(7, f"{len(live_historical)} historical")
                        
                        all_target_urls = list(set(raw_urls + deep_urls + live_historical))
                        
                        # --- LOCAL DEMO TARGET OVERRIDE ---
                        if "127.0.0.1" in target_domain:
                            all_target_urls = [
                                "http://127.0.0.1:5000/.env",
                                "http://127.0.0.1:5000/.git/config",
                                "http://127.0.0.1:5000/api/v1/dev-config"
                            ]

                        # ========== PHASE 8: IDOR Testing ==========
                        tracker.set_phase(9)
                        tracker.set_targets(len(all_target_urls))
                        
                        idor_findings = []
                        if all_target_urls:
                            if RICH_AVAILABLE:
                                with console.status(f"[cyan]🔓 Testing {len(all_target_urls)} URLs for IDOR...") as status:
                                    idor_tester = IDORTester(max_fuzz_range=20)  # Limit fuzz range for speed
                                    try:
                                        idor_findings = idor_tester.test_urls(all_target_urls[:50], cookies={'session': cookie} if cookie else None)
                                    except Exception as e:
                                        logger.debug(f"IDOR testing error: {e}")
                                    status.update(f"[green]✅ IDOR testing complete")
                            else:
                                idor_tester = IDORTester(max_fuzz_range=20)
                                try:
                                    idor_findings = idor_tester.test_urls(all_target_urls[:50])
                                except:
                                    pass
                            
                            if idor_findings:
                                tracker.log_finding("idor_vulns", len(idor_findings))
                                if RICH_AVAILABLE:
                                    console.print(f"[red]🚨 Found {len(idor_findings)} IDOR vulnerabilities![/red]")
                                logger.warning(idor_tester.generate_report(idor_findings))
                        
                        tracker.complete_phase(9, f"Found {len(idor_findings)} IDORs" if idor_findings else "No IDORs")

                        # ========== PHASE 9: Vulnerability Scanning ==========
                        tracker.set_phase(10)
                        tracker.set_targets(len(all_target_urls))
                        
                        # Stop the main tracker to show Nuclei-specific display
                        tracker.stop()
                        
                        if RICH_AVAILABLE:
                            console.print(f"\n[bold yellow]🎯 PHASE 10: Launching Nuclei Attack on {len(all_target_urls)} targets...[/bold yellow]\n")
                        
                        # Enhanced Nuclei progress tracking
                        nuclei_display = NucleiProgressDisplay()
                        nuclei_live = None
                        
                        if RICH_AVAILABLE:
                            from rich.live import Live
                            nuclei_live = Live(console=console, refresh_per_second=2)
                            nuclei_live.start()
                        
                        def nuclei_progress_callback(stats):
                            """Update Nuclei progress display."""
                            if nuclei_live and RICH_AVAILABLE:
                                nuclei_display.update_display(nuclei_live, stats)
                        
                        vulnerabilities = scanner.run_scan(
                            all_target_urls, 
                            cookie=cookie,
                            progress_callback=nuclei_progress_callback
                        )
                        
                        if nuclei_live:
                            nuclei_live.stop()
                        
                        # Show final results
                        if RICH_AVAILABLE:
                            console.print(f"\n[green]✅ Nuclei scan complete: {len(vulnerabilities)} vulnerabilities found![/green]\n")
                        
                        tracker.start()  # Restart main tracker
                        tracker.log_finding("vulnerabilities", len(vulnerabilities))
                        tracker.complete_phase(7, f"{len(vulnerabilities)} findings")
                        
                        # Stop progress display before printing results
                        tracker.stop()
                        
                        if vulnerabilities:
                            # 📢 Fire the Discord Alert!
                            discord = DiscordNotifier()
                            discord.send_alert(target_domain, vulnerabilities)                            
                            
                            # Phase 7: The Scribe
                            if mode_choice == '1':
                                if RICH_AVAILABLE:
                                    console.print("\n[yellow]🎫 Enterprise Alert: Generating Internal Jira-Style Remediation Ticket...[/yellow]")
                                else:
                                    print("\n🎫 Enterprise Alert: Generating Internal Jira-Style Remediation Ticket...")
                                ticket_path = ticket_generator.generate_ticket(target_domain, vulnerabilities)
                                if RICH_AVAILABLE:
                                    console.print(f"[green]✅ TICKET GENERATED![/green] Saved to: [cyan]{ticket_path}[/cyan]")
                                else:
                                    print(f"✅ TICKET GENERATED! Assigned to engineering team. Saved to: {ticket_path}")
                                
                            has_critical = any("critical" in str(v).lower() for v in vulnerabilities)
                            if has_critical:
                                if RICH_AVAILABLE:
                                    console.print(Panel(
                                        "[bold red]🚨 CRITICAL VULNERABILITY DETECTED! 🚨[/bold red]\n"
                                        "Trishul is executing a CI/CD Pipeline Block.\n"
                                        "[bold]Deployment HALTED.[/bold]",
                                        border_style="red"
                                    ))
                                else:
                                    print("\n🚨 [FATAL EXCEPTION] CRITICAL VULNERABILITY DETECTED! 🚨")
                                    print("🛑 Trishul is executing a CI/CD Pipeline Block. Deployment HALTED.")
                                sys.exit(1)
                            else:
                                report_path = reporter.generate_report(target_domain, vulnerabilities)
                                if RICH_AVAILABLE:
                                    console.print(Panel(
                                        f"[bold green]💰 BOUNTY SECURED![/bold green]\n"
                                        f"Report ready to submit: [cyan]{report_path}[/cyan]\n"
                                        f"[dim]Vulnerabilities found: {len(vulnerabilities)}[/dim]",
                                        border_style="green"
                                    ))
                                else:
                                    print(f"\n💰 BOUNTY SECURED! Report ready to submit: {report_path}")
                        else:
                            if RICH_AVAILABLE:
                                console.print("[yellow]Target neutralized. No vulnerabilities found.[/yellow]")
                            else:
                                logging.info("Target neutralized. No vulnerabilities found.")
                    else:
                        tracker.stop()
                        logging.info("No URLs found to scan.")
                else:
                    tracker.stop()
                    logging.info("Target locked down. No live endpoints found.")
            else:
                tracker.stop()
                logging.info("Target locked down. No open ports found.")
        else:
            tracker.stop()
            logging.info("No new subdomains found. Universe is in balance.")
        
        # Log scan completion
        scan_duration = time.time() - scan_start_time
        if audit_logger:
            # Count total findings (simplified - actual implementation would aggregate)
            audit_logger.log_scan_complete(
                target=target_domain,
                duration=scan_duration,
                findings_count=len(subdomain_results) if 'subdomain_results' in locals() else 0
            )
            audit_logger.close()

    except Exception as e:
        tracker.stop()
        logging.error(f"Main Pipeline Failure: {e}")
        
        # Log error
        if audit_logger:
            audit_logger.log_error("pipeline_failure", str(e), {'target': target_domain})
            audit_logger.close()

if __name__ == "__main__":
    main()
