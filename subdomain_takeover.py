"""
Subdomain Takeover Validator
Detects dangling DNS records and verifies if subdomain takeover is possible.
"""

import dns.resolver
import requests
import logging
from typing import List, Dict, Tuple
import re

class SubdomainTakeoverValidator:
    """
    Validates if subdomains are vulnerable to takeover attacks.
    Checks for dangling CNAME records pointing to unclaimed services.
    """
    
    # Fingerprints for detecting unclaimed services
    FINGERPRINTS = {
        'github': {
            'cname_pattern': r'.*\.github\.(io|com)$',
            'error_indicators': [
                'There isn\'t a GitHub Pages site here',
                'For root URLs (like http://example.com/) you must provide an index.html file'
            ],
            'severity': 'CRITICAL',
            'description': 'GitHub Pages unclaimed'
        },
        'heroku': {
            'cname_pattern': r'.*\.herokuapp\.com$',
            'error_indicators': [
                'No such app',
                'There\'s nothing here, yet',
                'herokucdn.com/error-pages/no-such-app.html'
            ],
            'severity': 'CRITICAL',
            'description': 'Heroku app deleted'
        },
        'aws-s3': {
            'cname_pattern': r'.*\.s3.*\.amazonaws\.com$',
            'error_indicators': [
                'NoSuchBucket',
                'The specified bucket does not exist'
            ],
            'severity': 'CRITICAL',
            'description': 'AWS S3 bucket deleted'
        },
        'aws-eb': {
            'cname_pattern': r'.*\.elasticbeanstalk\.com$',
            'error_indicators': [
                'NXDOMAIN',
                'The AWS Elastic Beanstalk environment does not exist'
            ],
            'severity': 'CRITICAL',
            'description': 'AWS Elastic Beanstalk deleted'
        },
        'netlify': {
            'cname_pattern': r'.*\.netlify\.(app|com)$',
            'error_indicators': [
                'Not Found - Request ID',
                'Page not found'
            ],
            'severity': 'CRITICAL',
            'description': 'Netlify site unclaimed'
        },
        'vercel': {
            'cname_pattern': r'.*\.vercel\.app$',
            'error_indicators': [
                'The deployment could not be found on Vercel',
                '404: NOT_FOUND'
            ],
            'severity': 'CRITICAL',
            'description': 'Vercel deployment deleted'
        },
        'azure': {
            'cname_pattern': r'.*\.azurewebsites\.net$',
            'error_indicators': [
                'Error 404 - Web app not found',
                'This web app has been stopped'
            ],
            'severity': 'CRITICAL',
            'description': 'Azure Web App deleted'
        },
        'bitbucket': {
            'cname_pattern': r'.*\.bitbucket\.io$',
            'error_indicators': [
                'Repository not found'
            ],
            'severity': 'CRITICAL',
            'description': 'Bitbucket Pages unclaimed'
        },
        'shopify': {
            'cname_pattern': r'.*\.myshopify\.com$',
            'error_indicators': [
                'Sorry, this shop is currently unavailable',
                'Only one step left!'
            ],
            'severity': 'HIGH',
            'description': 'Shopify store unclaimed'
        },
        'tumblr': {
            'cname_pattern': r'.*\.tumblr\.com$',
            'error_indicators': [
                'Whatever you were looking for doesn\'t currently exist',
                'There\'s nothing here'
            ],
            'severity': 'HIGH',
            'description': 'Tumblr blog deleted'
        },
        'wordpress': {
            'cname_pattern': r'.*\.wordpress\.com$',
            'error_indicators': [
                'Do you want to register'
            ],
            'severity': 'HIGH',
            'description': 'WordPress.com site unclaimed'
        },
        'pantheon': {
            'cname_pattern': r'.*\.pantheonsite\.io$',
            'error_indicators': [
                '404 error unknown site'
            ],
            'severity': 'CRITICAL',
            'description': 'Pantheon site deleted'
        },
        'fastly': {
            'cname_pattern': r'.*\.fastly\.net$',
            'error_indicators': [
                'Fastly error: unknown domain'
            ],
            'severity': 'CRITICAL',
            'description': 'Fastly service misconfigured'
        },
        'zendesk': {
            'cname_pattern': r'.*\.zendesk\.com$',
            'error_indicators': [
                'Help Center Closed'
            ],
            'severity': 'MEDIUM',
            'description': 'Zendesk unclaimed'
        }
    }
    
    def __init__(self):
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5
        self.dns_resolver.lifetime = 5
        
    def check_subdomains(self, subdomains: List[str]) -> List[Dict]:
        """
        Check list of subdomains for takeover vulnerabilities.
        
        Args:
            subdomains: List of subdomain strings
            
        Returns:
            List of vulnerable subdomain findings
        """
        vulnerable = []
        
        for subdomain in subdomains:
            try:
                result = self._check_single_subdomain(subdomain)
                if result:
                    vulnerable.append(result)
                    logging.warning(f"🚨 TAKEOVER FOUND: {subdomain} → {result['description']}")
            except Exception as e:
                logging.debug(f"Error checking {subdomain}: {e}")
                
        return vulnerable
    
    def _check_single_subdomain(self, subdomain: str) -> Dict:
        """Check a single subdomain for takeover vulnerability."""
        
        # Step 1: Get CNAME record
        cname = self._get_cname(subdomain)
        if not cname:
            return None
            
        logging.debug(f"Found CNAME: {subdomain} → {cname}")
        
        # Step 2: Match against known vulnerable providers
        provider_info = self._match_provider(cname)
        if not provider_info:
            return None
            
        # Step 3: Verify if the service is unclaimed
        is_vulnerable, evidence = self._verify_unclaimed(subdomain, provider_info)
        
        if is_vulnerable:
            return {
                'subdomain': subdomain,
                'cname': cname,
                'provider': provider_info['name'],
                'severity': provider_info['severity'],
                'description': provider_info['description'],
                'evidence': evidence,
                'exploitation': f"Register service at {cname} to take control of {subdomain}",
                'cvss': 8.1 if provider_info['severity'] == 'CRITICAL' else 6.5,
                'impact': 'Remote attacker can serve arbitrary content on victim subdomain'
            }
            
        return None
    
    def _get_cname(self, subdomain: str) -> str:
        """Resolve CNAME record for subdomain."""
        try:
            answers = self.dns_resolver.resolve(subdomain, 'CNAME')
            if answers:
                cname = str(answers[0].target).rstrip('.')
                return cname
        except dns.resolver.NXDOMAIN:
            logging.debug(f"{subdomain} does not exist (NXDOMAIN)")
        except dns.resolver.NoAnswer:
            logging.debug(f"{subdomain} has no CNAME record")
        except dns.resolver.Timeout:
            logging.debug(f"DNS timeout for {subdomain}")
        except Exception as e:
            logging.debug(f"DNS error for {subdomain}: {e}")
            
        return None
    
    def _match_provider(self, cname: str) -> Dict:
        """Match CNAME against known vulnerable providers."""
        for provider_name, fingerprint in self.FINGERPRINTS.items():
            pattern = fingerprint['cname_pattern']
            if re.match(pattern, cname, re.IGNORECASE):
                return {
                    'name': provider_name,
                    'severity': fingerprint['severity'],
                    'description': fingerprint['description'],
                    'error_indicators': fingerprint['error_indicators']
                }
        return None
    
    def _verify_unclaimed(self, subdomain: str, provider_info: Dict) -> Tuple[bool, str]:
        """
        Verify if the service is actually unclaimed by checking HTTP response.
        
        Returns:
            (is_vulnerable, evidence_string)
        """
        try:
            # Try both HTTP and HTTPS
            for protocol in ['https', 'http']:
                try:
                    url = f"{protocol}://{subdomain}"
                    response = requests.get(
                        url,
                        timeout=10,
                        allow_redirects=True,
                        verify=False,
                        headers={'User-Agent': 'Mozilla/5.0 (Trishul Security Scanner)'}
                    )
                    
                    # Check response for error indicators
                    content = response.text
                    for indicator in provider_info['error_indicators']:
                        if indicator.lower() in content.lower():
                            return True, f"Found indicator '{indicator}' at {url}"
                    
                    # Check status code
                    if response.status_code in [404, 410]:
                        return True, f"HTTP {response.status_code} at {url}"
                        
                except requests.exceptions.SSLError:
                    continue  # Try HTTP if HTTPS fails
                except requests.exceptions.ConnectionError:
                    # Connection error might indicate unclaimed service
                    return True, f"Connection refused to {protocol}://{subdomain}"
                except requests.exceptions.Timeout:
                    continue
                    
        except Exception as e:
            logging.debug(f"Verification error for {subdomain}: {e}")
            
        return False, None
    
    def generate_report(self, findings: List[Dict]) -> str:
        """Generate a formatted report of takeover vulnerabilities."""
        if not findings:
            return "✅ No subdomain takeover vulnerabilities found."
            
        report = f"\n🚨 SUBDOMAIN TAKEOVER VULNERABILITIES FOUND: {len(findings)}\n"
        report += "=" * 70 + "\n\n"
        
        for finding in findings:
            report += f"🎯 Subdomain: {finding['subdomain']}\n"
            report += f"   Provider: {finding['provider']}\n"
            report += f"   CNAME: {finding['cname']}\n"
            report += f"   Severity: {finding['severity']} (CVSS {finding['cvss']})\n"
            report += f"   Status: {finding['description']}\n"
            report += f"   Evidence: {finding['evidence']}\n"
            report += f"   Exploit: {finding['exploitation']}\n"
            report += f"   Impact: {finding['impact']}\n"
            report += "-" * 70 + "\n"
            
        return report


def test_takeover_validator():
    """Test the subdomain takeover validator."""
    validator = SubdomainTakeoverValidator()
    
    # Test with known vulnerable patterns
    test_domains = [
        'abandoned-blog.example.com',  # Would need actual testing
    ]
    
    findings = validator.check_subdomains(test_domains)
    print(validator.generate_report(findings))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_takeover_validator()
