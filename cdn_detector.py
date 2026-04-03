#!/usr/bin/env python3
"""
CDN Detection Module
Identifies if targets are behind CDN/WAF providers and adapts scanning strategy
"""

import socket
import requests
import dns.resolver
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging


@dataclass
class CDNInfo:
    """Information about detected CDN"""
    detected: bool
    provider: Optional[str]
    confidence: str  # HIGH, MEDIUM, LOW
    indicators: List[str]
    real_ips: List[str]
    recommended_strategy: str


class CDNDetector:
    """
    Detects CDN/WAF providers and recommends scanning strategies.
    Prevents aggressive scans from being blocked by CDN protections.
    """
    
    # CDN Provider Signatures
    CDN_PROVIDERS = {
        'cloudflare': {
            'headers': ['cf-ray', 'cf-cache-status', '__cfduid', 'cf-request-id'],
            'server_values': ['cloudflare'],
            'cname_patterns': [r'\.cloudflare\.', r'cloudflare-dns\.com'],
            'ip_ranges': ['104.16.0.0/12', '172.64.0.0/13', '173.245.48.0/20'],
            'asn': ['AS13335']
        },
        'cloudfront': {
            'headers': ['x-amz-cf-id', 'x-amz-cf-pop', 'x-cache'],
            'server_values': ['cloudfront', 'AmazonS3'],
            'cname_patterns': [r'\.cloudfront\.net$', r'\.awsglobalaccelerator\.com$'],
            'ip_ranges': [],  # AWS IPs are dynamic
            'asn': ['AS16509']
        },
        'akamai': {
            'headers': ['x-akamai-transformed', 'akamai-origin-hop', 'x-akamai-request-id'],
            'server_values': ['AkamaiGHost', 'Akamai'],
            'cname_patterns': [r'\.akamaiedge\.net$', r'\.akamai\.net$', r'\.akamaitechnologies\.com$'],
            'ip_ranges': [],
            'asn': ['AS20940', 'AS16625']
        },
        'fastly': {
            'headers': ['fastly-debug-path', 'fastly-debug-digest', 'x-fastly-request-id'],
            'server_values': ['Fastly'],
            'cname_patterns': [r'\.fastly\.net$', r'\.fastlylb\.net$'],
            'ip_ranges': ['23.235.32.0/20', '43.249.72.0/22'],
            'asn': ['AS54113']
        },
        'imperva': {
            'headers': ['x-iinfo', 'x-cdn'],
            'server_values': ['Imperva', 'Incapsula'],
            'cname_patterns': [r'\.incapdns\.net$'],
            'ip_ranges': [],
            'asn': ['AS19551']
        },
        'sucuri': {
            'headers': ['x-sucuri-id', 'x-sucuri-cache'],
            'server_values': ['Sucuri'],
            'cname_patterns': [r'\.sucuri\.net$'],
            'ip_ranges': [],
            'asn': []
        },
        'azure_cdn': {
            'headers': ['x-azure-ref', 'x-cache'],
            'server_values': ['Microsoft-Azure-CDN', 'ECAcc'],
            'cname_patterns': [r'\.azureedge\.net$', r'\.vo\.msecnd\.net$'],
            'ip_ranges': [],
            'asn': ['AS8075']
        },
        'google_cloud_cdn': {
            'headers': ['via', 'x-goog-generation', 'x-goog-metageneration'],
            'server_values': ['gfe', 'Google Frontend'],
            'cname_patterns': [r'\.googleusercontent\.com$'],
            'ip_ranges': [],
            'asn': ['AS15169']
        },
    }
    
    def __init__(self):
        """Initialize CDN detector"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Trishul Security Scanner - CDN Detection)'
        })
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 5
        self.resolver.lifetime = 5
    
    def detect(self, domain: str) -> CDNInfo:
        """
        Comprehensive CDN detection for a domain
        
        Args:
            domain: Target domain to check
            
        Returns:
            CDNInfo object with detection results
        """
        indicators = []
        detected_providers = []
        real_ips = []
        
        # Method 1: HTTP Headers Analysis
        provider, header_indicators = self._check_http_headers(domain)
        if provider:
            detected_providers.append(provider)
            indicators.extend(header_indicators)
        
        # Method 2: DNS CNAME Analysis
        provider, cname_indicators, cname_ips = self._check_dns_cname(domain)
        if provider:
            detected_providers.append(provider)
            indicators.extend(cname_indicators)
            real_ips.extend(cname_ips)
        
        # Method 3: Reverse DNS Analysis
        if not detected_providers:
            provider, rdns_indicators = self._check_reverse_dns(domain)
            if provider:
                detected_providers.append(provider)
                indicators.extend(rdns_indicators)
        
        # Consolidate results
        if detected_providers:
            primary_provider = max(set(detected_providers), key=detected_providers.count)
            confidence = self._calculate_confidence(len(indicators), detected_providers)
            strategy = self._get_recommended_strategy(primary_provider)
            
            return CDNInfo(
                detected=True,
                provider=primary_provider,
                confidence=confidence,
                indicators=list(set(indicators)),
                real_ips=list(set(real_ips)),
                recommended_strategy=strategy
            )
        else:
            return CDNInfo(
                detected=False,
                provider=None,
                confidence='NONE',
                indicators=[],
                real_ips=[],
                recommended_strategy='STANDARD'
            )
    
    def _check_http_headers(self, domain: str) -> Tuple[Optional[str], List[str]]:
        """Check HTTP response headers for CDN signatures"""
        indicators = []
        
        for protocol in ['https', 'http']:
            try:
                url = f"{protocol}://{domain}"
                response = self.session.get(url, timeout=10, verify=False, allow_redirects=True)
                headers = {k.lower(): v for k, v in response.headers.items()}
                
                # Check each CDN provider
                for provider, signatures in self.CDN_PROVIDERS.items():
                    for header in signatures['headers']:
                        if header.lower() in headers:
                            indicators.append(f"HTTP header: {header} = {headers[header.lower()]}")
                            return provider, indicators
                    
                    # Check Server header
                    server_header = headers.get('server', '').lower()
                    for server_value in signatures['server_values']:
                        if server_value.lower() in server_header:
                            indicators.append(f"Server header: {server_header}")
                            return provider, indicators
                
                # Generic CDN indicators
                if 'x-cache' in headers or 'x-cdn' in headers or 'via' in headers:
                    indicators.append(f"Generic CDN headers detected")
                
                break  # If HTTPS works, don't try HTTP
                
            except Exception as e:
                logging.debug(f"HTTP header check failed for {domain}: {e}")
                continue
        
        return None, indicators
    
    def _check_dns_cname(self, domain: str) -> Tuple[Optional[str], List[str], List[str]]:
        """Check DNS CNAME records for CDN patterns"""
        indicators = []
        ips = []
        
        try:
            # Get CNAME records
            answers = self.resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                cname = str(rdata.target).rstrip('.')
                indicators.append(f"CNAME: {cname}")
                
                # Check against known patterns
                for provider, signatures in self.CDN_PROVIDERS.items():
                    for pattern in signatures['cname_patterns']:
                        if re.search(pattern, cname, re.IGNORECASE):
                            return provider, indicators, ips
            
        except dns.resolver.NoAnswer:
            # No CNAME, try A records
            pass
        except dns.resolver.NXDOMAIN:
            logging.warning(f"Domain {domain} does not exist")
        except Exception as e:
            logging.debug(f"DNS CNAME check failed for {domain}: {e}")
        
        # Get A records (IP addresses)
        try:
            answers = self.resolver.resolve(domain, 'A')
            for rdata in answers:
                ip = str(rdata)
                ips.append(ip)
        except Exception as e:
            logging.debug(f"DNS A record check failed for {domain}: {e}")
        
        return None, indicators, ips
    
    def _check_reverse_dns(self, domain: str) -> Tuple[Optional[str], List[str]]:
        """Check reverse DNS for CDN indicators"""
        indicators = []
        
        try:
            # Get IP address
            ip = socket.gethostbyname(domain)
            
            # Reverse DNS lookup
            try:
                hostname = socket.gethostbyaddr(ip)[0]
                indicators.append(f"Reverse DNS: {hostname}")
                
                # Check against patterns
                for provider, signatures in self.CDN_PROVIDERS.items():
                    for pattern in signatures['cname_patterns']:
                        if re.search(pattern, hostname, re.IGNORECASE):
                            return provider, indicators
                
            except socket.herror:
                pass
                
        except Exception as e:
            logging.debug(f"Reverse DNS check failed for {domain}: {e}")
        
        return None, indicators
    
    def _calculate_confidence(self, indicator_count: int, providers: List[str]) -> str:
        """Calculate confidence level based on indicators"""
        if indicator_count >= 3 or len(set(providers)) == 1:
            return 'HIGH'
        elif indicator_count >= 2:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_recommended_strategy(self, provider: str) -> str:
        """Get recommended scanning strategy for detected CDN"""
        strategies = {
            'cloudflare': 'GENTLE_WEB_ONLY',
            'cloudfront': 'GENTLE_WEB_ONLY',
            'akamai': 'GENTLE_WEB_ONLY',
            'fastly': 'GENTLE_WEB_ONLY',
            'imperva': 'STEALTH_WEB_ONLY',
            'sucuri': 'STEALTH_WEB_ONLY',
            'azure_cdn': 'GENTLE_WEB_ONLY',
            'google_cloud_cdn': 'GENTLE_WEB_ONLY',
        }
        return strategies.get(provider, 'STANDARD')
    
    def get_assumed_ports(self, cdn_info: CDNInfo) -> List[int]:
        """
        Get assumed ports to test based on CDN detection
        
        Args:
            cdn_info: CDN detection results
            
        Returns:
            List of ports to assume are open
        """
        if cdn_info.detected:
            if cdn_info.recommended_strategy in ['GENTLE_WEB_ONLY', 'STEALTH_WEB_ONLY']:
                # CDN detected - assume standard web ports only
                return [80, 443]
            else:
                # Unknown CDN - test common web ports
                return [80, 443, 8080, 8443]
        else:
            # No CDN - can do full port scan
            return []  # Empty = do full scan


def format_cdn_info(cdn_info: CDNInfo) -> str:
    """Format CDN detection results for display"""
    if not cdn_info.detected:
        return "✓ No CDN detected - Full port scanning enabled"
    
    lines = [
        f"🛡️  CDN DETECTED: {cdn_info.provider.upper()}",
        f"   Confidence: {cdn_info.confidence}",
        f"   Strategy: {cdn_info.recommended_strategy}",
    ]
    
    if cdn_info.indicators:
        lines.append(f"   Indicators:")
        for indicator in cdn_info.indicators[:3]:  # Show top 3
            lines.append(f"     • {indicator}")
    
    if cdn_info.recommended_strategy in ['GENTLE_WEB_ONLY', 'STEALTH_WEB_ONLY']:
        lines.append(f"   ⚠️  Aggressive port scanning disabled (CDN protection)")
        lines.append(f"   ✓ Assuming standard web ports: 80, 443")
    
    return "\n".join(lines)


# Quick detection function
def quick_cdn_check(domain: str) -> bool:
    """
    Quick CDN check - returns True if CDN detected
    
    Args:
        domain: Domain to check
        
    Returns:
        True if CDN detected, False otherwise
    """
    detector = CDNDetector()
    cdn_info = detector.detect(domain)
    return cdn_info.detected


if __name__ == "__main__":
    # Demo
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cdn_detector.py <domain>")
        print("\nExample: python cdn_detector.py bose.com")
        sys.exit(1)
    
    domain = sys.argv[1]
    
    print(f"🔍 Detecting CDN for: {domain}\n")
    
    detector = CDNDetector()
    cdn_info = detector.detect(domain)
    
    print(format_cdn_info(cdn_info))
    
    if cdn_info.detected:
        print(f"\n📊 Recommended Ports: {detector.get_assumed_ports(cdn_info)}")
        
        if cdn_info.recommended_strategy == 'GENTLE_WEB_ONLY':
            print("\n💡 Recommendation:")
            print("   • Skip aggressive port scanning")
            print("   • Use HTTPX for web probing")
            print("   • Add delays between requests")
            print("   • Expect rate limiting")
