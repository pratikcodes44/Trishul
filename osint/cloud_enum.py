"""
Cloud Storage Enumerator
Discovers exposed S3, Azure Blob, and Google Cloud Storage buckets
"""

import requests
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)


class CloudEnumerator:
    """
    Enumerate cloud storage buckets for common naming patterns.
    Checks for public accessibility without downloading content.
    """
    
    def __init__(self):
        self.common_prefixes = [
            '',  # exact match
            'www-',
            'dev-',
            'staging-',
            'prod-',
            'production-',
            'test-',
            'backup-',
            'backups-',
            'data-',
            'static-',
            'assets-',
            'media-',
            'images-',
            'files-',
            'logs-',
        ]
        
        self.common_suffixes = [
            '',
            '-www',
            '-dev',
            '-staging',
            '-prod',
            '-production',
            '-backup',
            '-backups',
            '-data',
            '-static',
            '-assets',
        ]
    
    def enumerate(self, domain: str) -> List[Dict]:
        """
        Enumerate cloud storage buckets.
        
        Args:
            domain: Target domain
        
        Returns:
            List of found buckets with provider and accessibility info
        """
        found_buckets = []
        
        # Extract base name from domain
        base_name = domain.split('.')[0]
        
        logger.info(f"☁️  Enumerating cloud storage for {domain}...")
        
        # Test S3 buckets
        for prefix in self.common_prefixes[:5]:  # Limit to avoid noise
            for suffix in self.common_suffixes[:3]:
                bucket_name = f"{prefix}{base_name}{suffix}"
                
                # Check S3
                s3_result = self._check_s3(bucket_name)
                if s3_result:
                    found_buckets.append(s3_result)
                
                # Check Azure Blob
                azure_result = self._check_azure(bucket_name)
                if azure_result:
                    found_buckets.append(azure_result)
        
        logger.info(f"✅ Cloud Storage: Found {len(found_buckets)} accessible buckets")
        return found_buckets
    
    def _check_s3(self, bucket_name: str) -> Dict:
        """Check if S3 bucket exists and is accessible."""
        try:
            url = f"https://{bucket_name}.s3.amazonaws.com"
            response = requests.head(url, timeout=5, allow_redirects=True)
            
            # 200 = public access, 403 = exists but private, 404 = doesn't exist
            if response.status_code in [200, 403]:
                accessible = response.status_code == 200
                logger.info(f"🪣 Found S3 bucket: {bucket_name} (accessible: {accessible})")
                return {
                    'provider': 'AWS S3',
                    'bucket': bucket_name,
                    'url': url,
                    'accessible': accessible,
                    'status': response.status_code
                }
        except requests.RequestException:
            pass
        
        return None
    
    def _check_azure(self, bucket_name: str) -> Dict:
        """Check if Azure Blob Storage container exists."""
        try:
            url = f"https://{bucket_name}.blob.core.windows.net"
            response = requests.head(url, timeout=5, allow_redirects=True)
            
            if response.status_code in [200, 403]:
                accessible = response.status_code == 200
                logger.info(f"📦 Found Azure Blob: {bucket_name} (accessible: {accessible})")
                return {
                    'provider': 'Azure Blob',
                    'bucket': bucket_name,
                    'url': url,
                    'accessible': accessible,
                    'status': response.status_code
                }
        except requests.RequestException:
            pass
        
        return None
    
    def _check_gcs(self, bucket_name: str) -> Dict:
        """Check if Google Cloud Storage bucket exists."""
        try:
            url = f"https://storage.googleapis.com/{bucket_name}"
            response = requests.head(url, timeout=5, allow_redirects=True)
            
            if response.status_code in [200, 403]:
                accessible = response.status_code == 200
                logger.info(f"☁️  Found GCS bucket: {bucket_name} (accessible: {accessible})")
                return {
                    'provider': 'Google Cloud Storage',
                    'bucket': bucket_name,
                    'url': url,
                    'accessible': accessible,
                    'status': response.status_code
                }
        except requests.RequestException:
            pass
        
        return None
