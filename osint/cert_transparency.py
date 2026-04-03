"""
Certificate Transparency Log Scanner
Queries CT logs for subdomain discovery
"""

import requests
import logging
from typing import List, Set

logger = logging.getLogger(__name__)


class CertTransparency:
    """
    Query Certificate Transparency logs to discover subdomains.
    CT logs reveal ALL subdomains that have ever had SSL certificates issued.
    """
    
    def __init__(self):
        self.sources = [
            "https://crt.sh/?q=%.{domain}&output=json",
            "https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains=true&expand=dns_names"
        ]
    
    def query(self, domain: str) -> Set[str]:
        """
        Query Certificate Transparency logs for subdomains.
        
        Args:
            domain: Root domain to search
        
        Returns:
            Set of discovered subdomains
        """
        subdomains = set()
        
        # Query crt.sh
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            logger.info(f"📜 Querying Certificate Transparency logs for {domain}...")
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    for entry in data:
                        name_value = entry.get('name_value', '')
                        
                        # CT logs can return multiple names separated by newlines
                        for name in name_value.split('\n'):
                            name = name.strip().lower()
                            
                            # Clean wildcard certificates
                            if name.startswith('*.'):
                                name = name[2:]
                            
                            # Only add if it's a subdomain of target
                            if name.endswith(domain) and name != domain:
                                subdomains.add(name)
                    
                    logger.info(f"✅ crt.sh: Found {len(subdomains)} unique subdomains")
                    
                except ValueError:
                    logger.warning("Failed to parse crt.sh JSON response")
            else:
                logger.warning(f"crt.sh returned status {response.status_code}")
                
        except requests.RequestException as e:
            logger.error(f"Certificate Transparency query failed: {e}")
        
        # Add root domain
        subdomains.add(domain)
        
        return subdomains
    
    def query_certspotter(self, domain: str) -> Set[str]:
        """
        Query Certspotter API (alternative CT log source).
        Note: Requires API key for high-volume queries.
        """
        subdomains = set()
        
        try:
            url = f"https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains=true&expand=dns_names"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                for entry in data:
                    dns_names = entry.get('dns_names', [])
                    for name in dns_names:
                        name = name.strip().lower()
                        if name.startswith('*.'):
                            name = name[2:]
                        if name.endswith(domain):
                            subdomains.add(name)
                
                logger.info(f"✅ Certspotter: Found {len(subdomains)} subdomains")
            
        except requests.RequestException as e:
            logger.debug(f"Certspotter query failed (this is optional): {e}")
        
        return subdomains
