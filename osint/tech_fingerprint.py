"""
Technology Fingerprinting
Detects CMS, frameworks, and server technologies
"""

import requests
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class TechFingerprint:
    """
    Detect technology stack of web applications.
    Identifies CMS, JavaScript frameworks, server software, etc.
    """
    
    def __init__(self):
        self.signatures = {
            # CMS Signatures
            'WordPress': [
                '/wp-content/',
                '/wp-includes/',
                'wp-json',
            ],
            'Drupal': [
                '/sites/default/',
                'Drupal',
                '/node/',
            ],
            'Joomla': [
                '/components/',
                'Joomla',
                '/templates/',
            ],
            'Magento': [
                '/skin/frontend/',
                'Mage.Cookies',
            ],
            # Frameworks
            'React': [
                'react',
                '_react',
            ],
            'Angular': [
                'ng-version',
                'angular',
            ],
            'Vue.js': [
                'vue',
                '__vue__',
            ],
            'jQuery': [
                'jquery',
            ],
        }
        
        self.header_signatures = {
            'server': 'Server',
            'x-powered-by': 'X-Powered-By',
            'x-aspnet-version': 'X-AspNet-Version',
            'x-generator': 'X-Generator',
        }
    
    def detect(self, domain: str) -> Dict:
        """
        Detect technologies used by target domain.
        
        Args:
            domain: Target domain (can include protocol)
        
        Returns:
            Dictionary of detected technologies
        """
        technologies = {
            'cms': [],
            'frameworks': [],
            'server': '',
            'languages': [],
        }
        
        # Ensure domain has protocol
        if not domain.startswith('http'):
            domain = f"https://{domain}"
        
        try:
            logger.info(f"🔧 Fingerprinting technologies on {domain}...")
            
            response = requests.get(domain, timeout=10, verify=False, allow_redirects=True)
            
            # Check response body for signatures
            body = response.text.lower()
            
            for tech, patterns in self.signatures.items():
                for pattern in patterns:
                    if pattern.lower() in body:
                        if tech in ['WordPress', 'Drupal', 'Joomla', 'Magento']:
                            technologies['cms'].append(tech)
                        else:
                            technologies['frameworks'].append(tech)
                        break  # Don't count the same tech multiple times
            
            # Check headers
            for header_key, header_name in self.header_signatures.items():
                value = response.headers.get(header_name, '')
                if value:
                    if header_key == 'server':
                        technologies['server'] = value
                    else:
                        technologies['languages'].append(value)
            
            # Deduplicate
            technologies['cms'] = list(set(technologies['cms']))
            technologies['frameworks'] = list(set(technologies['frameworks']))
            technologies['languages'] = list(set(technologies['languages']))
            
            total_found = len(technologies['cms']) + len(technologies['frameworks']) + (1 if technologies['server'] else 0)
            logger.info(f"✅ Technology Detection: Found {total_found} technologies")
            
        except requests.RequestException as e:
            logger.debug(f"Technology fingerprinting failed for {domain}: {e}")
        
        return technologies
    
    def detect_server_version(self, headers: Dict) -> str:
        """Extract server software and version from headers."""
        server = headers.get('Server', '')
        powered_by = headers.get('X-Powered-By', '')
        
        return f"{server} {powered_by}".strip()
