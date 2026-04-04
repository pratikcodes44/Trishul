"""
GitHub Secret and Code Scanner
Searches GitHub for leaked credentials and internal documentation
"""

import requests
import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)


class GitHubHunter:
    """
    Search GitHub for leaked secrets, API keys, and sensitive information.
    Uses GitHub Code Search API and common patterns.
    """
    
    def __init__(self):
        self.api_token = os.getenv("GITHUB_TOKEN", "")  # Optional but recommended
        self.search_patterns = [
            'password OR api_key OR secret',
            'extension:env OR extension:config',
            'extension:yml OR extension:yaml',
            'aws_access_key OR aws_secret',
            'Bearer OR Authorization',
        ]
    
    def search(self, domain: str) -> List[Dict]:
        """
        Search GitHub for potential leaks related to target domain.
        
        Args:
            domain: Target domain to search
        
        Returns:
            List of findings with repo, file, and leak type
        """
        findings = []
        
        logger.info(f"🔎 Searching GitHub for {domain} leaks...")
        
        for pattern in self.search_patterns:
            try:
                query = f'"{domain}" {pattern}'
                url = f"https://api.github.com/search/code?q={query}&per_page=10"
                
                headers = {}
                if self.api_token:
                    headers['Authorization'] = f'token {self.api_token}'
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    
                    for item in items:
                        finding = {
                            'repo': item.get('repository', {}).get('full_name', 'Unknown'),
                            'file': item.get('path', 'Unknown'),
                            'url': item.get('html_url', ''),
                            'pattern': pattern,
                        }
                        findings.append(finding)
                
                elif response.status_code == 403:
                    logger.warning("GitHub API rate limit reached. Set GITHUB_TOKEN environment variable for higher limits.")
                    break
                    
            except requests.RequestException as e:
                logger.debug(f"GitHub search failed for pattern '{pattern}': {e}")
        
        logger.info(f"✅ GitHub: Found {len(findings)} potential leaks")
        return findings
    
    def search_repos(self, domain: str) -> List[str]:
        """
        Find GitHub repositories that mention the target domain.
        """
        repos = []
        
        try:
            query = f'"{domain}" in:readme OR in:description'
            url = f"https://api.github.com/search/repositories?q={query}&per_page=20"
            
            headers = {}
            if self.api_token:
                headers['Authorization'] = f'token {self.api_token}'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                for item in items:
                    repo_name = item.get('full_name')
                    if repo_name:
                        repos.append(repo_name)
            
            logger.info(f"📦 Found {len(repos)} related repositories")
            
        except requests.RequestException as e:
            logger.debug(f"GitHub repo search failed: {e}")
        
        return repos
