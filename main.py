import argparse
import logging
import sys

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
except ImportError as e:
    logging.error(f"Import Error: {e}")
    sys.exit(1)

def main():
    # 🚀 RESTORED: Command Line Argument Parsing 🚀
    parser = argparse.ArgumentParser(description="Project Trishul - EASM & Bug Bounty Pipeline")
    parser.add_argument("-d", "--domain", help="Target domain to scan manually")
    parser.add_argument("-m", "--mode", help="Operating Mode: 1 (Enterprise) or 2 (Bounty). Default: 2", choices=['1', '2'])
    parser.add_argument("-c", "--cookie", help="Session cookie for authenticated scanning (Mode 1)")
    parser.add_argument("-y", "--yes", action="store_true", help="Auto-authorize weapons release (for automation)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize the Arsenal
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
    mode_choice = ""

    # 🚀 THE LOGIC SPLIT: CLI vs Interactive 🚀
    if args.domain:
        # If the user typed '-d', skip the menu entirely!
        target_domain = args.domain
        mode_choice = args.mode if args.mode else '2' # Default to Mode 2 if not specified
        
        if mode_choice == '1':
            platform = "Internal Enterprise Target (CLI Override)"
            program_url = "Internal Ticket System"
        else:
            platform = "Manual CLI Target"
            program_url = "N/A (Manual Override)"
            
        print(f"\n⚡ CLI OVERRIDE: Executing Mode {mode_choice} against {target_domain}")
        
    else:
        # If no flags were used, show the Interactive Menu
        print("\n" + "="*60)
        print(" 🔱 PROJECT TRISHUL: AUTONOMOUS CYBERSECURITY PLATFORM 🔱 ")
        print("="*60)
        print("  [1] VIRTUAL SECURITY ENGINEER (Enterprise/Internal Audit)")
        print("  [2] BUG BOUNTY HUNTER (Autonomous External Strike)")
        print("="*60)
        
        mode_choice = input("\nSelect Operating Mode [1 or 2]: ").strip()

        if mode_choice == '1':
            print("\n🛡️ INITIALIZING VIRTUAL SECURITY ENGINEER MODE...")
            target_domain = input("Enter the enterprise domain to audit (e.g., staging.company.com): ").strip()
            cookie_input = input("Enter valid Session Cookie for deep scanning (or press Enter to skip): ").strip()
            if cookie_input:
                cookie = cookie_input
                print("[+] Authenticated Scanning Enabled.")
            
            platform = "Internal Enterprise Target"
            program_url = "Internal Ticket System"
            
        elif mode_choice == '2':
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

    # The Target Summary
    print("\n" + "="*50)
    print(" 🎯 TRISHUL TARGET ACQUIRED")
    print("="*50)
    print(f"🏢 Platform    : {platform}")
    print(f"🌐 Target      : {target_domain}")
    if mode_choice == '2':
        print(f"🔗 Policy Link : {program_url}")
    print("="*50)

    # 🚀 RESTORED: The Authorization Check (Bypassed if -y is used) 🚀
    if not args.yes:
        choice = input(f"\nAuthorize weapons release on {target_domain}? [y/N]: ").strip().lower()
        if choice != 'y':
            print("Mission aborted. Returning to sleep mode.")
            sys.exit(0)

    logging.info(f"Weapons authorized. Initiating strike on: {target_domain}")

    try:
        # Phase 1: Discovery
        raw_subs = subfinder.discover_subdomains(target_domain)
        raw_subs.append(target_domain)
        raw_subs = list(set(raw_subs)) 
        
        in_scope = [s for s in raw_subs if scope_checker.is_in_scope(s, target_domain)]
        
        # Phase 2: Memory
        new_discoveries = asset_manager.insert_and_diff(in_scope)

        if new_discoveries:
            # Phase 3: The X-Ray
            targets_with_ports = scanner_ports.scan_ports(new_discoveries)

            if targets_with_ports:
                # Phase 4: The Flashlight
                live_results = prober.probe(targets_with_ports) 

                if live_results:
                    raw_urls = [line.split(" ")[1] for line in live_results if len(line.split(" ")) > 1 and line.split(" ")[1].startswith("http")]
                    
                    if raw_urls:
                        # Phase 5: The Spider & The Time Machine
                        deep_urls = crawler.crawl(raw_urls, cookie=cookie)
                        
                        historical_raw = time_machine.fetch_history(target_domain)
                        live_historical = []
                        
                        if historical_raw:
                            logging.info(f"Pulse checking {len(historical_raw)} historical URLs with HTTPX...")
                            historical_probed = prober.probe(historical_raw)
                            if historical_probed:
                                live_historical = [line.split(" ")[1] for line in historical_probed if len(line.split(" ")) > 1 and line.split(" ")[1].startswith("http")]
                        
                        all_target_urls = list(set(raw_urls + deep_urls + live_historical))
                        logging.info(f"Final Attack Surface: {len(all_target_urls)} live endpoints ready for the Sniper.")
                        
                        # Phase 6: The Sniper (Nuclei)
                        vulnerabilities = scanner.run_scan(all_target_urls, cookie=cookie)
                        
                        if vulnerabilities:
                            alert_system.send_alert(["🔥 **VULNERABILITIES DETECTED** 🔥"] + vulnerabilities)
                            
                            # Phase 7: The Scribe
                            if mode_choice == '1':
                                print("\n🎫 Enterprise Alert: Generating Internal Jira-Style Remediation Ticket...")
                                ticket_path = ticket_generator.generate_ticket(target_domain, vulnerabilities)
                                print(f"✅ TICKET GENERATED! Assigned to engineering team. Saved to: {ticket_path}")
                                
                                has_critical = any("critical" in str(v).lower() for v in vulnerabilities)
                                if has_critical:
                                    print("\n🚨 [FATAL EXCEPTION] CRITICAL VULNERABILITY DETECTED! 🚨")
                                    print("🧱 Trishul is executing a CI/CD Pipeline Block. Deployment HALTED.")
                                    sys.exit(1)
                            else:
                                report_path = reporter.generate_report(target_domain, vulnerabilities)
                                print(f"\n💰 BOUNTY SECURED! Report ready to submit: {report_path}")
                        else:
                            logging.info("Target neutralized. No critical bugs found.")
            else:
                logging.info("Target locked down. No open ports found.")
        else:
            logging.info("No new subdomains found. Universe is in balance.")

    except Exception as e:
        logging.error(f"Main Pipeline Failure: {e}")

if __name__ == "__main__":
    main()
