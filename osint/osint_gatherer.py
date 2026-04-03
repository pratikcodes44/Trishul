"""
Main OSINT Orchestrator
Coordinates all passive intelligence gathering modules
"""

import logging
from typing import Dict, List, Set
from .cert_transparency import CertTransparency
from .github_hunter import GitHubHunter
from .cloud_enum import CloudEnumerator
from .dns_analyzer import DNSAnalyzer
from .tech_fingerprint import TechFingerprint

logger = logging.getLogger(__name__)


class OSINTGatherer:
    """
    Main orchestrator for OSINT reconnaissance.
    Runs all passive intelligence gathering before active scanning.
    """
    
    def __init__(self, target_domain: str):
        self.target_domain = target_domain
        self.findings = {
            'subdomains': set(),
            'emails': set(),
            'cloud_buckets': [],
            'github_leaks': [],
            'dns_records': {},
            'technologies': {},
            'ip_addresses': set(),
        }
        
        # Initialize modules
        self.cert_transparency = CertTransparency()
        self.github_hunter = GitHubHunter()
        self.cloud_enum = CloudEnumerator()
        self.dns_analyzer = DNSAnalyzer()
        self.tech_fingerprint = TechFingerprint()
    
    def gather_all(self, progress_callback=None) -> Dict:
        """
        Run all OSINT modules and aggregate findings.
        
        Args:
            progress_callback: Function to call with progress updates (module_name, status)
        
        Returns:
            Dictionary of all OSINT findings
        """
        logger.info(f"🔍 Starting OSINT reconnaissance on {self.target_domain}")
        
        # 1. Certificate Transparency Logs
        if progress_callback:
            progress_callback("cert_transparency", "running")
        try:
            ct_subdomains = self.cert_transparency.query(self.target_domain)
            self.findings['subdomains'].update(ct_subdomains)
            logger.info(f"📜 Certificate Transparency: Found {len(ct_subdomains)} subdomains")
            if progress_callback:
                progress_callback("cert_transparency", "done", len(ct_subdomains))
        except Exception as e:
            logger.error(f"Certificate Transparency failed: {e}")
            if progress_callback:
                progress_callback("cert_transparency", "error")
        
        # 2. GitHub Secret Scanning
        if progress_callback:
            progress_callback("github", "running")
        try:
            github_results = self.github_hunter.search(self.target_domain)
            self.findings['github_leaks'] = github_results
            logger.info(f"🔎 GitHub: Found {len(github_results)} potential leaks")
            if progress_callback:
                progress_callback("github", "done", len(github_results))
        except Exception as e:
            logger.error(f"GitHub scanning failed: {e}")
            if progress_callback:
                progress_callback("github", "error")
        
        # 3. Cloud Storage Enumeration
        if progress_callback:
            progress_callback("cloud", "running")
        try:
            buckets = self.cloud_enum.enumerate(self.target_domain)
            self.findings['cloud_buckets'] = buckets
            logger.info(f"☁️  Cloud Storage: Found {len(buckets)} accessible buckets")
            if progress_callback:
                progress_callback("cloud", "done", len(buckets))
        except Exception as e:
            logger.error(f"Cloud enumeration failed: {e}")
            if progress_callback:
                progress_callback("cloud", "error")
        
        # 4. DNS Deep Dive
        if progress_callback:
            progress_callback("dns", "running")
        try:
            dns_records = self.dns_analyzer.analyze(self.target_domain)
            self.findings['dns_records'] = dns_records
            
            # Extract emails from DNS records
            if 'mx' in dns_records:
                logger.info(f"📧 DNS: Found {len(dns_records['mx'])} MX records")
            
            if progress_callback:
                progress_callback("dns", "done", len(dns_records))
        except Exception as e:
            logger.error(f"DNS analysis failed: {e}")
            if progress_callback:
                progress_callback("dns", "error")
        
        # 5. Technology Fingerprinting (on discovered subdomains)
        if progress_callback:
            progress_callback("tech", "running")
        try:
            # Sample up to 10 subdomains for fingerprinting
            sample_domains = list(self.findings['subdomains'])[:10] if self.findings['subdomains'] else [self.target_domain]
            
            for domain in sample_domains:
                tech_stack = self.tech_fingerprint.detect(domain)
                if tech_stack:
                    self.findings['technologies'][domain] = tech_stack
            
            logger.info(f"🔧 Technology: Fingerprinted {len(self.findings['technologies'])} domains")
            if progress_callback:
                progress_callback("tech", "done", len(self.findings['technologies']))
        except Exception as e:
            logger.error(f"Technology fingerprinting failed: {e}")
            if progress_callback:
                progress_callback("tech", "error")
        
        logger.info(f"✅ OSINT reconnaissance complete")
        return self.findings
    
    def get_summary(self) -> Dict:
        """Return a summary of OSINT findings."""
        return {
            'subdomains_count': len(self.findings['subdomains']),
            'cloud_buckets_count': len(self.findings['cloud_buckets']),
            'github_leaks_count': len(self.findings['github_leaks']),
            'emails_count': len(self.findings['emails']),
            'technologies_count': len(self.findings['technologies']),
        }
