import argparse
import logging
import sys
import os
import time
import threading
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

# Rich console for beautiful output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TaskProgressColumn
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich import print as rprint
    from rich.markdown import Markdown
    from rich.syntax import Syntax
    from rich.tree import Tree
    from rich.rule import Rule
    from rich import box
    import time as time_module
    RICH_AVAILABLE = True
    console = Console()
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
    from report_writer import ReportWriter
    from bounty_scout import BountyScout
    from gau_runner import TimeMachine
    from gmail_notifier import get_notifier as get_gmail_notifier
    from osint.osint_gatherer import OSINTGatherer
    from subdomain_takeover import SubdomainTakeoverValidator
    from idor_tester import IDORTester
    from graphql_api_scanner import GraphQLAPIScanner
    from terminal_ui import StreamingUI, VulnerabilityDisplay
    from scope_validator import ScopeValidator
    from audit_logger import init_audit_logger, get_audit_logger
    from cdn_detector import CDNDetector, format_cdn_info
    from dynamic_tui import create_tui
    from ai_engine import analyze_asset_risk, batch_analyze_assets, ai_assistant
    from campaign_manager import campaign_manager, Campaign, CampaignStatus, ProgramPlatform
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
[dim italic]      AI-Powered Bug Bounty Automation Platform[/dim italic]
"""


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
    {"name": "Web Crawling", "tool": "Katana", "icon": "🕷️"},
    {"name": "GraphQL/API Discovery", "tool": "GraphQLScanner", "icon": "📡"},
    {"name": "Historical Mining", "tool": "GAU", "icon": "⏳"},
    {"name": "IDOR Testing", "tool": "IDORTester", "icon": "🔓"},
    {"name": "Vulnerability Scan", "tool": "Nuclei", "icon": "🎯"},
]

class AttackProgressTracker:
    """Single-live-display progress tracker with a clean Copilot-like layout."""
    
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
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
    def generate_display(self):
        """Generate a compact, non-overlapping live display."""
        if not RICH_AVAILABLE:
            return ""

        elapsed = time.time() - self.start_time if self.start_time else 0

        header = Text.from_markup(
            f"[bold bright_blue]→[/] [bold]Trishul[/] "
            f"[dim]phase {self.current_phase}/{self.total_phases} · {self._format_time(elapsed)}[/dim]"
        )
        target = Text.from_markup(f"[dim]target:[/] [cyan]{self.target_domain}[/cyan]")

        metrics = Table.grid(expand=True, padding=(0, 2))
        metrics.add_column(justify="right", style="dim")
        metrics.add_column(style="cyan")
        metrics.add_column(justify="right", style="dim")
        metrics.add_column(style="cyan")
        metrics.add_row("subdomains", str(self.subdomains_found), "ports", str(self.ports_found))
        metrics.add_row("live hosts", str(self.live_hosts), "urls", str(self.urls_crawled + self.historical_urls))
        metrics.add_row(
            "vulns",
            f"[red]{self.vulnerabilities_found}[/red]" if self.vulnerabilities_found > 0 else "0",
            "targets",
            str(self.current_targets),
        )

        phase_table = Table(show_header=False, box=None, expand=True, padding=(0, 1))
        phase_table.add_column(width=2, justify="center")
        phase_table.add_column(ratio=2)
        phase_table.add_column(ratio=3, style="dim")

        for i, phase in enumerate(PIPELINE_PHASES):
            phase_num = i + 1
            if phase_num < self.current_phase:
                icon = "[green]✓[/green]"
                details = self.phase_stats.get(phase["name"], "")
                name_style = "dim"
            elif phase_num == self.current_phase:
                spinner = self.spinner_frames[int(elapsed * 6) % len(self.spinner_frames)]
                icon = f"[yellow]{spinner}[/yellow]"
                details = f"[yellow]{self.current_targets} targets active[/yellow]" if self.current_targets > 0 else "[yellow]Initializing...[/yellow]"
                name_style = "bold white"
            else:
                icon = "[dim]○[/dim]"
                details = ""
                name_style = "dim"

            phase_table.add_row(
                icon,
                f"[{name_style}]{phase['icon']} {phase['name']}[/{name_style}]",
                details,
            )

        body = Table.grid(padding=(0, 0))
        body.add_column()
        body.add_row(header)
        body.add_row(target)
        body.add_row("")
        body.add_row(metrics)
        body.add_row("")
        body.add_row(Text.from_markup("[dim]pipeline[/dim]"))
        body.add_row(phase_table)

        return Panel(body, border_style="bright_blue", box=box.ROUNDED, padding=(0, 1))

    
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
            if self.live_display:
                self.live_display.stop()
            self.live_display = Live(self.generate_display(), console=console, refresh_per_second=8, transient=False)
            self.live_display.start()
    
    def stop(self):
        """Stop the progress tracker."""
        self.is_running = False
        if self.live_display:
            self.live_display.stop()
            self.live_display = None
    
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

    def set_phase_detail(self, phase_num, detail):
        """Update detail text for a phase while it is running."""
        if phase_num > 0 and phase_num <= len(PIPELINE_PHASES):
            phase_name = PIPELINE_PHASES[phase_num - 1]["name"]
            self.phase_stats[phase_name] = detail
        self.update()


class PhaseWatchdog:
    """
    Background watchdog thread to detect stuck phases.
    Sends email alert if no progress for specified timeout.
    """
    
    def __init__(self, target_domain: str, timeout: int = 300):
        """
        Initialize watchdog.
        
        Args:
            target_domain: Target domain being scanned
            timeout: Timeout in seconds (default: 300 = 5 minutes)
        """
        self.target_domain = target_domain
        self.timeout = timeout
        self.last_progress_time = time.time()
        self.current_phase = 0
        self.current_phase_name = "Initialization"
        self.running = False
        self.thread = None
        self.gmail_notifier = get_gmail_notifier()
        self.alert_sent_for_phase = -1  # Track which phase we already alerted for
        
    def start(self):
        """Start the watchdog thread."""
        if self.running:
            logger.warning("Watchdog already running")
            return
        
        self.running = True
        self.last_progress_time = time.time()
        self.thread = threading.Thread(target=self._monitor, daemon=True, name="PhaseWatchdog")
        self.thread.start()
        logger.info(f"🐕 Phase watchdog started (timeout: {self.timeout}s)")
    
    def stop(self):
        """Stop the watchdog thread."""
        self.running = False
        if self.thread:
            logger.info("🐕 Phase watchdog stopped")
    
    def update_progress(self, phase_num: int, phase_name: str = ""):
        """
        Called by main pipeline when phase progresses.
        
        Args:
            phase_num: Current phase number
            phase_name: Optional phase name
        """
        self.last_progress_time = time.time()
        self.current_phase = phase_num
        if phase_name:
            self.current_phase_name = phase_name
        else:
            if 0 < phase_num <= len(PIPELINE_PHASES):
                self.current_phase_name = PIPELINE_PHASES[phase_num - 1]["name"]
        
        # Reset alert tracking when we progress to a new phase
        if phase_num != self.alert_sent_for_phase:
            self.alert_sent_for_phase = -1
    
    def _monitor(self):
        """Background monitoring loop."""
        while self.running:
            time.sleep(30)  # Check every 30 seconds
            
            if not self.running:
                break
            
            elapsed_since_progress = time.time() - self.last_progress_time
            
            # If stuck and haven't sent alert for this phase yet
            if elapsed_since_progress > self.timeout and self.alert_sent_for_phase != self.current_phase:
                logger.warning(
                    f"⚠️  Phase {self.current_phase} ({self.current_phase_name}) "
                    f"stuck for {int(elapsed_since_progress)}s"
                )
                
                # Send email alert
                try:
                    self.gmail_notifier.send_stuck_alert(
                        domain=self.target_domain,
                        phase_num=self.current_phase,
                        phase_name=self.current_phase_name,
                        stuck_duration=elapsed_since_progress
                    )
                    self.alert_sent_for_phase = self.current_phase
                except Exception as e:
                    logger.error(f"Failed to send stuck alert: {e}")
                
                # Reset timer to avoid spam (send alert every timeout period)
                self.last_progress_time = time.time()


def print_banner():
    if RICH_AVAILABLE:
        console.print(Panel(
            BANNER,
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        ))
    else:
        print(BANNER)

def print_target_info(platform, target_domain, program_url):
    if RICH_AVAILABLE:
        table = Table(title="🎯 TARGET ACQUIRED", show_header=False, border_style="green")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("🏢 Platform", platform)
        table.add_row("🌐 Target", target_domain)
        if program_url:
            table.add_row("🔗 Policy Link", program_url)
        console.print(table)
    else:
        print("\n" + "="*50)
        print(" 🎯 TRISHUL TARGET ACQUIRED")
        print("="*50)
        print(f"🏢 Platform    : {platform}")
        print(f"🌐 Target      : {target_domain}")
        if program_url:
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
  python main.py                                    # Auto-select bug bounty target
  python main.py -d target.com -y                  # Scan specific target (no prompt)
  python main.py -d http://127.0.0.1:5000 --yes    # URL input supported
  python main.py --demo                             # Safe local demo
  python main.py -d target.com --scope scope.txt    # With scope validation
  python main.py -d target.com --read-only          # Read-only mode
        """
    )
    parser.add_argument("-d", "--domain", help="Target domain to scan")
    # Mode removed for hackathon - focusing on bug bounty only
    parser.add_argument("-c", "--cookie", help="Session cookie for authenticated scanning")
    parser.add_argument("-y", "--yes", action="store_true", help="Auto-authorize (no prompts)")
    parser.add_argument("--demo", action="store_true", help="Run demo against local vulnerable_arena.py")
    parser.add_argument("--scope", help="Scope file with authorized targets (RECOMMENDED)")
    parser.add_argument("--read-only", action="store_true", default=True, help="Read-only mode (no POST/PUT/DELETE) [default: ON]")
    parser.add_argument("--allow-writes", action="store_true", help="Allow POST/PUT/DELETE requests (use with caution)")
    parser.add_argument("--request-delay", type=float, default=0.5, help="Delay between requests in seconds (default: 0.5)")
    parser.add_argument("--max-idor-tests", type=int, default=20, help="Max IDOR fuzzing per URL (default: 20)")
    parser.add_argument("--no-audit-log", action="store_true", help="Disable audit logging (not recommended)")
    parser.add_argument("--skip-osint", action="store_true", help="Skip OSINT phase (faster, relies on subfinder only)")
    args = parser.parse_args()

    log_level_name = os.getenv("TRISHUL_LOG_LEVEL", "WARNING").upper()
    log_level = getattr(logging, log_level_name, logging.WARNING)
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
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
    scope_checker = ScopeChecker()
    subfinder = SubfinderRunner()
    asset_manager = AssetManager()
    scanner_ports = PortScanner()
    prober = LiveHostProber()
    crawler = KatanaRunner()
    scanner = NucleiRunner()
    time_machine = TimeMachine()           
    target_domain = ""
    program_url = ""
    platform = ""
    cookie = args.cookie 
    cdn_info = None

    # Demo mode - run against local vulnerable_arena.py
    if args.demo:
        target_domain = "127.0.0.1"  # Fixed: Remove port for proper scanning
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
        # Clean up the domain - remove http://, https://, trailing slashes, ports
        import re
        from urllib.parse import urlparse
        
        # Parse URL if it looks like a full URL
        if args.domain.startswith(('http://', 'https://')):
            parsed = urlparse(args.domain)
            # Get hostname (without port)
            target_domain = parsed.hostname or parsed.netloc.split(':')[0]
        else:
            # Remove port if present (e.g., "127.0.0.1:5000" → "127.0.0.1")
            target_domain = args.domain.split(':')[0]
        
        # Validate scope if enabled
        if scope_validator:
            is_valid = scope_validator.validate_or_exit(target_domain)
            if audit_logger:
                audit_logger.log_scope_validation(target_domain, is_valid, "Initial target validation")
        
        platform = "Manual CLI Target"
        program_url = "N/A (Manual Override)"
            
        if RICH_AVAILABLE:
            console.print(f"[green]⚡ CLI OVERRIDE:[/green] Bug Bounty mode against [cyan]{target_domain}[/cyan]")
        else:
            print(f"\n⚡ CLI OVERRIDE: Executing Bug Bounty mode against {target_domain}")
        
    else:
        # Auto-select bug bounty mode for hackathon
        logger.info("[DIAGNOSTIC] Entering auto-select bug bounty mode")
        if RICH_AVAILABLE:
            console.print("\n[green]🥷 INITIALIZING BUG BOUNTY HUNTER MODE...[/green]")
        else:
            print("\n🥷 INITIALIZING BUG BOUNTY HUNTER MODE...")
        logger.info("[DIAGNOSTIC] Calling scout.get_random_target()")
        target_data = scout.get_random_target()
        logger.info(f"[DIAGNOSTIC] Target data received: {target_data}")
        
        if not target_data:
            logging.error("Could not find a target. Exiting.")
            sys.exit(1)
        target_domain = target_data["domain"]
        program_url = target_data["url"]
        platform = target_data["platform"]
        logger.info(f"[DIAGNOSTIC] Target selected - Domain: {target_domain}, Platform: {platform}")

    logger.info("[DIAGNOSTIC] Printing target info")
    print_target_info(platform, target_domain, program_url)

    # CDN-aware safe profile detection (compliant throttling, no bypass behavior)
    try:
        cdn_detector = CDNDetector()
        cdn_info = cdn_detector.detect(target_domain)
        if cdn_info.detected:
            os.environ["TRISHUL_SCAN_PROFILE"] = "cdn-safe"
            if RICH_AVAILABLE:
                console.print(Panel(
                    format_cdn_info(cdn_info) + "\n\n[bold cyan]✓ Applying CDN-safe scan profile (throttled, low-noise).[/bold cyan]",
                    title="🛡️ CDN/WAF Awareness",
                    border_style="cyan",
                ))
            else:
                print(format_cdn_info(cdn_info))
                print("✓ Applying CDN-safe scan profile (throttled, low-noise).")
        else:
            os.environ["TRISHUL_SCAN_PROFILE"] = "default"
    except Exception as cdn_exc:
        logger.debug(f"CDN detection failed, continuing with default profile: {cdn_exc}")
        os.environ["TRISHUL_SCAN_PROFILE"] = "default"

    # Ask for confirmation (time box removed for cleaner UI)
    logger.info(f"[DIAGNOSTIC] Confirmation required: {not args.yes}")
    if not args.yes:
        logger.info("[DIAGNOSTIC] Awaiting user confirmation...")
        try:
            if RICH_AVAILABLE:
                user_response = console.input(
                    f"\n[yellow]Proceed with attack on [bold]{target_domain}[/bold]? [y/N]: [/yellow]"
                ).strip().lower()
            else:
                user_response = input(f"\nProceed with attack on {target_domain}? [y/N]: ").strip().lower()
            
            logger.info(f"[DIAGNOSTIC] User response received: '{user_response}'")
            proceed = user_response == "y"
            
            if not proceed:
                logger.info("[DIAGNOSTIC] User declined to proceed. Exiting gracefully.")
                if RICH_AVAILABLE:
                    console.print("[red]Mission aborted. Returning to sleep mode.[/red]")
                else:
                    print("Mission aborted. Returning to sleep mode.")
                sys.exit(0)
            
            logger.info("[DIAGNOSTIC] User confirmed. Proceeding with attack.")
        except (EOFError, KeyboardInterrupt) as e:
            logger.warning(f"[DIAGNOSTIC] Input interrupted: {type(e).__name__}")
            if RICH_AVAILABLE:
                console.print("\n[red]Attack cancelled by user.[/red]")
            else:
                print("\nAttack cancelled by user.")
            sys.exit(0)
    else:
        logger.info("[DIAGNOSTIC] Auto-confirmed with --yes flag")

    logger.info("[DIAGNOSTIC] Confirmation complete. Initializing attack...")
    if RICH_AVAILABLE:
        console.print(f"\n[green]✅ Weapons authorized. Initiating strike on: [bold]{target_domain}[/bold][/green]\n")
    else:
        logging.info(f"Weapons authorized. Initiating strike on: {target_domain}")

    # Log scan start
    attack_start_time = time.time()
    scan_start_time = attack_start_time  # Keep for backward compatibility
    
    # ========== CAMPAIGN MANAGEMENT ==========
    logger.info("📊 Initializing campaign tracking...")
    campaign_id = None
    try:
        import uuid
        campaign_id = str(uuid.uuid4())
        
        # Create campaign entry
        campaign = Campaign(
            id=campaign_id,
            name=f"{target_domain} - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            platform=(
                platform.lower()
                if isinstance(platform, str) and platform.lower() in {p.value for p in ProgramPlatform}
                else ProgramPlatform.CUSTOM.value
            ),
            target_domain=target_domain,
            status=CampaignStatus.ACTIVE.value,
            priority=4,  # High priority for active scans
            scope=[target_domain, f"*.{target_domain}"],
            out_of_scope=[],
            created_at=datetime.now().isoformat(),
            notes=f"Automated scan initiated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        campaign_manager.create_campaign(campaign)
        logger.info(f"✅ Campaign created: {campaign_id}")
        
        if RICH_AVAILABLE:
            console.print(f"\n[cyan]📊 Campaign ID:[/cyan] {campaign_id}")
            console.print(f"[cyan]🎯 Tracking:[/cyan] {target_domain}\n")
            
    except Exception as e:
        logger.warning(f"Campaign creation failed (non-critical): {e}")
        campaign_id = None
    
    # Initialize Gmail notifier
    gmail_notifier = get_gmail_notifier()
    
    # Send target found notification
    if gmail_notifier.enabled:
        logger.info("📧 Sending target discovery notification...")
        gmail_notifier.send_target_found(
            domain=target_domain,
            program_url=program_url if 'program_url' in locals() else "N/A",
            platform=platform if 'platform' in locals() else "Manual"
        )
    
    if audit_logger:
        audit_logger.log_scan_start(
            target=target_domain,
            mode="Bug Bounty",  # Always bug bounty for hackathon
            options={
                'platform': platform,
                'authenticated': bool(cookie),
                'read_only': read_only,
                'request_delay': args.request_delay,
                'max_idor_tests': args.max_idor_tests,
                'scope_file': args.scope if args.scope else None
            }
        )

    # Initialize dynamic TUI
    logger.info("[DIAGNOSTIC] Initializing dynamic TUI")
    tui = create_tui(target_domain, total_phases=len(PIPELINE_PHASES))
    
    # Setup phases for tracking
    tui_phases = [
        {'name': phase['name'], 'icon': phase['icon'], 'status': 'pending', 'details': ''}
        for phase in PIPELINE_PHASES
    ]
    tui.set_phases(tui_phases)
    
    try:
        # Start live TUI
        logger.info("[DIAGNOSTIC] Starting live TUI")
        tui.start()
        logger.info("[DIAGNOSTIC] TUI started successfully")
        
        # Initialize and start watchdog
        logger.info("[DIAGNOSTIC] Starting phase watchdog")
        watchdog = PhaseWatchdog(target_domain, timeout=300)  # 5 minutes
        watchdog.start()
        
        # Note: Using DynamicTUI for progress tracking instead of AttackProgressTracker to avoid conflicts
        
        # Send attack started notification
        if gmail_notifier.enabled:
            logger.info("📧 Sending attack start notification...")
            gmail_notifier.send_attack_started(target_domain, attack_start_time)

        # Print explicit AI wake-up message once at attack start
        if getattr(ai_assistant, "use_local_ai", False):
            if RICH_AVAILABLE:
                console.print("[bold cyan]🤖 AI has woke up (local Mistral is online).[/bold cyan]")
            else:
                print("🤖 AI has woke up (local Mistral is online).")
        else:
            if RICH_AVAILABLE:
                console.print("[yellow]🤖 AI wake-up skipped (local model unavailable, using fallback logic).[/yellow]")
            else:
                print("🤖 AI wake-up skipped (local model unavailable, using fallback logic).")

        def ai_phase_guidance(phase_num: int, phase_name: str, context: dict):
            """Show one-line local-AI guidance per phase without interrupting pipeline."""
            try:
                guidance = ai_assistant.generate_phase_guidance(phase_num, phase_name, context)
                if RICH_AVAILABLE:
                    console.print(f"[dim cyan]🤖 AI Phase {phase_num} Guidance:[/dim cyan] [dim]{guidance}[/dim]")
                else:
                    print(f"[AI][Phase {phase_num}] {guidance}")
            except Exception as ai_exc:
                logger.debug(f"AI phase guidance unavailable: {ai_exc}")
        
        # ========== PHASE 1: OSINT RECONNAISSANCE ==========
        logger.info("[DIAGNOSTIC] Entering Phase 1: OSINT Reconnaissance")
        watchdog.update_progress(1, "OSINT Reconnaissance")
        ai_phase_guidance(1, "OSINT Reconnaissance", {"target": target_domain, "skip_osint": args.skip_osint})
        osint_subdomains = set()
        
        if not args.skip_osint:
            tui.set_phase(1, "OSINT Reconnaissance", "Gathering passive intelligence")
            osint_gatherer = OSINTGatherer(target_domain)
            
            def osint_progress(module, status, count=0):
                """Callback for OSINT progress updates."""
                if status == "running":
                    tui.update_phase_details(1, f"[yellow]{module}...[/yellow]")
                elif status == "done":
                    tui.update_phase_details(1, f"[green]{module}: {count} items[/green]")
                elif status == "error":
                    tui.update_phase_details(1, f"[red]{module}: failed[/red]")
            
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
                
                tui.complete_phase(1, f"OSINT: {summary['subdomains_count']} subdomains")
            except Exception as e:
                logger.error(f"OSINT reconnaissance failed: {e}")
                tui.complete_phase(1, "OSINT: Failed (continuing with active recon)")
        else:
            # Skip OSINT - mark as complete immediately
            tui.set_phase(1, "OSINT Reconnaissance", "Skipped (--skip-osint flag)")
            tui.complete_phase(1, "OSINT: Skipped")
        
        # ========== PHASE 2: Subdomain Discovery (Active) ==========
        watchdog.update_progress(2, "Subdomain Discovery")
        tui.set_phase(2)
        ai_phase_guidance(2, "Subdomain Discovery", {"target": target_domain})
        # Update target count in TUI if method exists (Note: DynamicTUI may not have set_targets)
        
        tui.update_phase_details(2, "[yellow]subfinder running[/yellow]")
        raw_subs = subfinder.discover_subdomains(target_domain)
        
        # Merge OSINT and active subdomain discoveries
        raw_subs.extend(list(osint_subdomains))
        raw_subs.append(target_domain)
        raw_subs = list(set(raw_subs))
        
        in_scope = [s for s in raw_subs if scope_checker.is_in_scope(s, target_domain)]
        new_discoveries = asset_manager.insert_and_diff(in_scope)
        # Note: log_finding not available in DynamicTUI("subdomains", len(new_discoveries))
        tui.complete_phase(2, f"Found {len(new_discoveries)} new")

        # ========== PHASE 2.5: Subdomain Takeover Check ==========
        if new_discoveries:
            tui.set_phase(3)
            ai_phase_guidance(3, "Subdomain Takeover Check", {"new_discoveries": len(new_discoveries)})
            # Note: set_targets not available in DynamicTUI(len(new_discoveries))
            
            tui.update_phase_details(3, f"[yellow]checking {len(new_discoveries)} hosts[/yellow]")
            takeover_validator = SubdomainTakeoverValidator()
            takeover_findings = takeover_validator.check_subdomains(new_discoveries)
            
            if takeover_findings:
                # Note: log_finding not available in DynamicTUI("takeover_vulns", len(takeover_findings))
                if RICH_AVAILABLE:
                    console.print(f"[red]🚨 CRITICAL: {len(takeover_findings)} subdomain takeover vulnerabilities![/red]")
                    for finding in takeover_findings:
                        console.print(f"   [yellow]→ {finding['subdomain']} ({finding['provider']})[/yellow]")
                logger.warning(takeover_validator.generate_report(takeover_findings))
            
            tui.complete_phase(3, f"Found {len(takeover_findings)} takeovers" if takeover_findings else "No takeovers")

        if new_discoveries:
            # ========== PHASE 4: Port Scanning ==========
            watchdog.update_progress(4, "Port Scanning")
            tui.set_phase(4)
            ai_phase_guidance(4, "Port Scanning", {"hosts": len(new_discoveries)})
            # Note: set_targets not available in DynamicTUI(len(new_discoveries))
            
            tui.update_phase_details(4, f"[yellow]scanning {len(new_discoveries)} hosts[/yellow]")
            if cdn_info and cdn_info.detected:
                # Safe mode on CDN-protected targets: avoid aggressive full-port probing.
                assumed_ports = cdn_detector.get_assumed_ports(cdn_info)
                targets_with_ports = [f"{host}:{port}" for host in new_discoveries for port in assumed_ports]
            else:
                targets_with_ports = scanner_ports.scan_ports(new_discoveries)
            
            # Note: log_finding not available in DynamicTUI("ports", len(targets_with_ports))
            tui.complete_phase(4, f"{len(targets_with_ports)} open ports")

            if targets_with_ports:
                # ========== PHASE 5: Live Host Probing ==========
                watchdog.update_progress(5, "Live Host Probing")
                tui.set_phase(5)
                ai_phase_guidance(5, "Live Host Probing", {"targets_with_ports": len(targets_with_ports)})
                # Note: set_targets not available in DynamicTUI(len(targets_with_ports))
                
                tui.update_phase_details(5, f"[yellow]probing {len(targets_with_ports)} endpoints[/yellow]")
                live_results = prober.probe(targets_with_ports)
                
                if live_results:
                    raw_urls = [line.split(" ")[1] for line in live_results if len(line.split(" ")) > 1 and line.split(" ")[1].startswith("http")]
                    # Note: log_finding not available in DynamicTUI("live_hosts", len(raw_urls))
                    tui.complete_phase(5, f"{len(raw_urls)} live hosts")
                    
                    if raw_urls:
                        # ========== PHASE 6: Web Crawling ==========
                        watchdog.update_progress(6, "Web Crawling")
                        tui.set_phase(6)
                        ai_phase_guidance(6, "Web Crawling", {"live_hosts": len(raw_urls)})
                        # Note: set_targets not available in DynamicTUI(len(raw_urls))
                        
                        tui.update_phase_details(6, f"[yellow]scanning {len(raw_urls)} hosts[/yellow]")
                        deep_urls = crawler.crawl(raw_urls, cookie=cookie)
                        
                        # Note: log_finding not available in DynamicTUI("urls", len(deep_urls))
                        tui.complete_phase(6, f"{len(deep_urls)} endpoints")
                        
                        # ========== PHASE 7: GraphQL/API Discovery ==========
                        watchdog.update_progress(7, "GraphQL/API Discovery")
                        tui.set_phase(7)
                        ai_phase_guidance(7, "GraphQL/API Discovery", {"urls_sampled": min(len(raw_urls), 10)})
                        # Note: set_targets not available in DynamicTUI(len(raw_urls))
                        
                        graphql_findings = []
                        tui.update_phase_details(7, f"[yellow]crawling {len(raw_urls)} sites[/yellow]")
                        graphql_scanner = GraphQLAPIScanner()
                        for url in raw_urls[:10]:  # Limit to first 10 hosts for performance
                            try:
                                findings = graphql_scanner.scan_target(url, cookies={'session': cookie} if cookie else None)
                                graphql_findings.extend(findings)
                            except Exception as e:
                                logger.debug(f"GraphQL scan error on {url}: {e}")
                        
                        if graphql_findings:
                            # Note: log_finding not available in DynamicTUI("graphql_vulns", len(graphql_findings))
                            if RICH_AVAILABLE:
                                console.print(f"[red]🚨 Found {len(graphql_findings)} GraphQL/API vulnerabilities![/red]")
                            logger.warning(graphql_scanner.generate_report(graphql_findings))
                        
                        tui.complete_phase(7, f"Found {len(graphql_findings)} API vulns" if graphql_findings else "No API vulns")
                        
                        # ========== PHASE 8: Historical Mining ==========
                        watchdog.update_progress(8, "Historical Mining")
                        tui.set_phase(8)
                        ai_phase_guidance(8, "Historical Mining", {"domain": target_domain})
                        # Note: set_targets not available in DynamicTUI(1)
                        
                        tui.update_phase_details(8, "[yellow]mining wayback[/yellow]")
                        historical_raw = time_machine.fetch_history(target_domain)
                        
                        live_historical = []
                        
                        if historical_raw:
                            # Note: set_targets not available in DynamicTUI(len(historical_raw))
                            historical_probed = prober.probe(historical_raw)
                            if historical_probed:
                                live_historical = [line.split(" ")[1] for line in historical_probed if len(line.split(" ")) > 1 and line.split(" ")[1].startswith("http")]
                        
                        # Note: log_finding not available in DynamicTUI("historical", len(live_historical))
                        tui.complete_phase(8, f"{len(live_historical)} historical")
                        
                        all_target_urls = list(set(raw_urls + deep_urls + live_historical))
                        
                        # --- LOCAL DEMO TARGET OVERRIDE ---
                        if "127.0.0.1" in target_domain:
                            all_target_urls = [
                                "http://127.0.0.1:5000/.env",
                                "http://127.0.0.1:5000/.git/config",
                                "http://127.0.0.1:5000/api/v1/dev-config"
                            ]

                        # ========== PHASE 9: IDOR Testing ==========
                        watchdog.update_progress(9, "IDOR Testing")
                        tui.set_phase(9)
                        ai_phase_guidance(9, "IDOR Testing", {"targets_for_idor": min(len(all_target_urls), 50)})
                        # Note: set_targets not available in DynamicTUI(len(all_target_urls))
                        
                        idor_findings = []
                        if all_target_urls:
                            tui.update_phase_details(9, f"[yellow]testing {len(all_target_urls[:50])} urls[/yellow]")
                            # Apply safer rate profile on CDN-protected targets.
                            if cdn_info and cdn_info.detected:
                                idor_tester = IDORTester(max_fuzz_range=10, request_delay=max(args.request_delay, 1.0))
                            else:
                                idor_tester = IDORTester(max_fuzz_range=20, request_delay=max(args.request_delay, 0.5))
                            try:
                                idor_findings = idor_tester.test_urls(all_target_urls[:50], cookies={'session': cookie} if cookie else None)
                            except Exception as e:
                                logger.debug(f"IDOR testing error: {e}")
                            
                            if idor_findings:
                                # Note: log_finding not available in DynamicTUI("idor_vulns", len(idor_findings))
                                if RICH_AVAILABLE:
                                    console.print(f"[red]🚨 Found {len(idor_findings)} IDOR vulnerabilities![/red]")
                                logger.warning(idor_tester.generate_report(idor_findings))
                        
                        tui.complete_phase(9, f"Found {len(idor_findings)} IDORs" if idor_findings else "No IDORs")

                        # ========== PHASE 10: Vulnerability Scanning ==========
                        watchdog.update_progress(10, "Vulnerability Scanning")
                        tui.set_phase(10)
                        ai_phase_guidance(10, "Vulnerability Scanning", {"nuclei_targets": len(all_target_urls)})
                        # Note: set_targets not available in DynamicTUI(len(all_target_urls))
                        
                        tui.update_phase_details(10, f"[yellow]launching nuclei on {len(all_target_urls)} targets[/yellow]")
                        if RICH_AVAILABLE:
                            console.print(f"\n[bold yellow]🎯 PHASE 10: Launching Nuclei Attack on {len(all_target_urls)} targets...[/bold yellow]")

                        def nuclei_progress_callback(stats):
                            """Update existing live tracker details only (no nested Live panels)."""
                            sent = stats.get("requests_sent", 0)
                            total = stats.get("requests_total", 0)
                            vulns = stats.get("vulnerabilities", 0)
                            pct = int((sent / total) * 100) if total > 0 else 0
                            tui.update_phase_details(10, f"[yellow]{pct}% · {sent}/{total} · {vulns} vulns[/yellow]")
                        
                        vulnerabilities = scanner.run_scan(
                            all_target_urls, 
                            cookie=cookie,
                            progress_callback=nuclei_progress_callback
                        )
                        
                        # Show final results
                        if RICH_AVAILABLE:
                            console.print(f"\n[green]✅ Nuclei scan complete: {len(vulnerabilities)} vulnerabilities found![/green]\n")

                        # Note: log_finding not available in DynamicTUI("vulnerabilities", len(vulnerabilities))
                        tui.complete_phase(10, f"{len(vulnerabilities)} findings")
                        
                        # ========== AI RISK ASSESSMENT ==========
                        logger.info("🤖 Running AI-powered risk assessment...")
                        try:
                            # Prepare asset data for AI analysis
                            if isinstance(targets_with_ports, dict):
                                open_ports = list({
                                    port
                                    for host_ports in targets_with_ports.values()
                                    for port in host_ports
                                })
                            else:
                                open_ports = []
                                for target in (targets_with_ports or []):
                                    if isinstance(target, str) and ":" in target:
                                        port_part = target.rsplit(":", 1)[-1]
                                        if port_part.isdigit():
                                            open_ports.append(int(port_part))
                                open_ports = sorted(set(open_ports))

                            asset_data = {
                                'domain': target_domain,
                                'technologies': [],
                                'open_ports': open_ports,
                                'subdomains_count': len(new_discoveries) if 'new_discoveries' in locals() else 0,
                                'vulnerabilities_count': len(vulnerabilities),
                                'critical_vulns': len([v for v in vulnerabilities if 'critical' in str(v).lower()]),
                                'high_vulns': len([v for v in vulnerabilities if 'high' in str(v).lower()])
                            }
                            
                            ai_risk_analysis = analyze_asset_risk(asset_data)
                            
                            if RICH_AVAILABLE:
                                console.print("\n" + "="*70)
                                console.print(Panel(
                                    f"[bold cyan]🤖 AI Risk Assessment[/bold cyan]\n\n"
                                    f"[yellow]Vulnerability Score:[/yellow] {ai_risk_analysis['vulnerability_score']}/100\n"
                                    f"[yellow]Risk Level:[/yellow] {ai_risk_analysis['risk_level']} ({ai_risk_analysis['exploit_likelihood']} exploit likelihood)\n\n"
                                    f"{ai_risk_analysis['ai_analysis']}",
                                    title="🎯 AI Intelligence",
                                    border_style="cyan"
                                ))
                                
                                if ai_risk_analysis.get('reasons'):
                                    console.print("\n[bold yellow]📊 Risk Factors:[/bold yellow]")
                                    for reason in ai_risk_analysis['reasons']:
                                        console.print(f"  • {reason}")
                                        
                                if ai_risk_analysis.get('recommendations'):
                                    console.print("\n[bold green]✅ Recommendations:[/bold green]")
                                    for rec in ai_risk_analysis['recommendations'][:3]:
                                        console.print(f"  • {rec}")
                                console.print("="*70 + "\n")
                                
                        except Exception as e:
                            logger.warning(f"AI risk assessment failed: {e}")
                            if RICH_AVAILABLE:
                                console.print(f"[yellow]⚠️  AI risk assessment unavailable[/yellow]")
                        
                        # Stop progress display before printing results
                        tui.stop()
                        
                        if vulnerabilities:
                            has_critical = any("critical" in str(v).lower() for v in vulnerabilities)
                            if has_critical:
                                if campaign_id:
                                    try:
                                        campaign_record = campaign_manager.get_campaign(campaign_id)
                                        if campaign_record:
                                            campaign_record.status = CampaignStatus.COMPLETED.value
                                            campaign_record.last_scan = datetime.now().isoformat()
                                            campaign_record.total_assets = len(all_target_urls) if 'all_target_urls' in locals() else 0
                                            campaign_record.vulnerabilities_found = len(vulnerabilities)
                                            campaign_record.critical_count = len(
                                                [v for v in vulnerabilities if "critical" in str(v).lower()]
                                            )
                                            campaign_record.high_count = len(
                                                [v for v in vulnerabilities if "high" in str(v).lower()]
                                            )
                                            campaign_record.ai_priority_score = campaign_manager.calculate_ai_priority(campaign_record)
                                            campaign_manager.update_campaign(campaign_record)
                                    except Exception as e:
                                        logger.warning(f"Campaign update failed (non-critical): {e}")
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
                        tui.stop()
                        logging.info("No URLs found to scan.")
                else:
                    tui.stop()
                    logging.info("Target locked down. No live endpoints found.")
            else:
                tui.stop()
                logging.info("Target locked down. No open ports found.")
        else:
            tui.stop()
            logging.info("No new subdomains found. Universe is in balance.")
        
        # Log scan completion
        scan_duration = time.time() - attack_start_time
        
        # Stop watchdog
        if 'watchdog' in locals():
            watchdog.stop()

        # Update campaign with final scan statistics
        if campaign_id:
            try:
                campaign_record = campaign_manager.get_campaign(campaign_id)
                if campaign_record:
                    campaign_record.status = CampaignStatus.COMPLETED.value
                    campaign_record.last_scan = datetime.now().isoformat()
                    campaign_record.total_assets = len(all_target_urls) if 'all_target_urls' in locals() else 0
                    campaign_record.vulnerabilities_found = len(vulnerabilities) if 'vulnerabilities' in locals() else 0
                    campaign_record.critical_count = len(
                        [v for v in vulnerabilities if "critical" in str(v).lower()]
                    ) if 'vulnerabilities' in locals() else 0
                    campaign_record.high_count = len(
                        [v for v in vulnerabilities if "high" in str(v).lower()]
                    ) if 'vulnerabilities' in locals() else 0
                    campaign_record.ai_priority_score = campaign_manager.calculate_ai_priority(campaign_record)
                    campaign_manager.update_campaign(campaign_record)
            except Exception as e:
                logger.warning(f"Campaign update failed (non-critical): {e}")
        
        # Send completion notification with results
        if gmail_notifier.enabled:
            # Collect all vulnerabilities from the scan
            all_vulnerabilities = []
            
            # Get nuclei results if available
            if 'vulnerabilities' in locals():
                all_vulnerabilities = vulnerabilities
            
            # Get PDF report path if generated
            pdf_report_path = None
            reports_dir = Path("reports")
            if reports_dir.exists():
                # Look for both PDF and MD files for this domain
                safe_domain = target_domain.replace('.', '_').replace(':', '_')
                pdf_files = list(reports_dir.glob(f"*{safe_domain}*.pdf"))
                md_files = list(reports_dir.glob(f"*{safe_domain}*.md"))
                
                if pdf_files:
                    # Use most recent PDF file
                    pdf_report_path = str(sorted(pdf_files, key=os.path.getctime)[-1])
                    logger.info(f"[DIAGNOSTIC] Found PDF report: {pdf_report_path}")
                elif md_files:
                    # Use most recent MD file as attachment
                    pdf_report_path = str(sorted(md_files, key=os.path.getctime)[-1])
                    logger.info(f"[DIAGNOSTIC] Using MD report as attachment: {pdf_report_path}")
                else:
                    logger.warning("[DIAGNOSTIC] No report files found for domain")
            else:
                logger.warning("[DIAGNOSTIC] Reports directory not found")
            
            logger.info("📧 Sending attack completion notification...")
            gmail_notifier.send_attack_completed(
                domain=target_domain,
                elapsed_time=scan_duration,
                vulns=all_vulnerabilities,
                pdf_path=pdf_report_path
            )
        
        if audit_logger:
            # Count total findings (simplified - actual implementation would aggregate)
            audit_logger.log_scan_complete(
                target=target_domain,
                duration=scan_duration,
                findings_count=len(subdomain_results) if 'subdomain_results' in locals() else 0
            )
            audit_logger.close()

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        elapsed_time = time.time() - attack_start_time if 'attack_start_time' in locals() else 0
        current_phase = watchdog.current_phase if 'watchdog' in locals() else 0
        
        if 'watchdog' in locals():
            watchdog.stop()
        
        if 'tui' in locals():
            tui.stop()
        
        if 'gmail_notifier' in locals() and gmail_notifier.enabled:
            logger.info("📧 Sending attack interruption notification...")
            gmail_notifier.send_attack_interrupted(
                domain=target_domain if 'target_domain' in locals() else "unknown",
                elapsed_time=elapsed_time,
                current_phase=current_phase
            )

        if 'campaign_id' in locals() and campaign_id:
            try:
                campaign_record = campaign_manager.get_campaign(campaign_id)
                if campaign_record:
                    campaign_record.status = CampaignStatus.PAUSED.value
                    campaign_record.last_scan = datetime.now().isoformat()
                    campaign_record.notes = (
                        f"{campaign_record.notes}\nInterrupted by user at phase {current_phase} "
                        f"after {int(elapsed_time)}s."
                    ).strip()
                    campaign_record.ai_priority_score = campaign_manager.calculate_ai_priority(campaign_record)
                    campaign_manager.update_campaign(campaign_record)
            except Exception as e:
                logger.warning(f"Campaign interruption update failed (non-critical): {e}")
        
        logger.warning("Attack interrupted by user (Ctrl+C)")
        if RICH_AVAILABLE:
            console.print("\n[yellow]⚠️  Attack interrupted by user.[/yellow]")
        else:
            print("\n⚠️  Attack interrupted by user.")
        
        if audit_logger:
            audit_logger.log_error("user_interruption", "KeyboardInterrupt", {
                'target': target_domain if 'target_domain' in locals() else "unknown",
                'elapsed_time': elapsed_time,
                'phase': current_phase
            })
            audit_logger.close()
        
        sys.exit(1)
        
    except Exception as e:
        if 'watchdog' in locals():
            watchdog.stop()
            
        if 'tui' in locals():
            tui.stop()

        if 'campaign_id' in locals() and campaign_id:
            try:
                campaign_record = campaign_manager.get_campaign(campaign_id)
                if campaign_record:
                    campaign_record.status = CampaignStatus.PAUSED.value
                    campaign_record.last_scan = datetime.now().isoformat()
                    campaign_record.notes = (
                        f"{campaign_record.notes}\nPipeline failure: {str(e)}"
                    ).strip()
                    campaign_record.ai_priority_score = campaign_manager.calculate_ai_priority(campaign_record)
                    campaign_manager.update_campaign(campaign_record)
            except Exception as campaign_error:
                logger.warning(f"Campaign failure update failed (non-critical): {campaign_error}")
            
        logging.error(f"Main Pipeline Failure: {e}")
        
        # Log error
        if audit_logger:
            audit_logger.log_error("pipeline_failure", str(e), {'target': target_domain})
            audit_logger.close()

if __name__ == "__main__":
    main()
