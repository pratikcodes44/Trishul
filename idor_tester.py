"""
IDOR (Insecure Direct Object Reference) Auto-Tester
Tests for authorization bypass and horizontal/vertical privilege escalation.
"""

import requests
import re
import logging
import time
from typing import List, Dict, Tuple, Set
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import json
from difflib import SequenceMatcher

class IDORTester:
    """
    Automated IDOR vulnerability tester.
    Fuzzes ID parameters and detects authorization bypass issues.
    """
    
    # Common parameter names that might contain IDs
    ID_PARAMETERS = [
        'id', 'user_id', 'userId', 'user', 'uid', 'account_id', 'accountId',
        'order_id', 'orderId', 'invoice_id', 'invoiceId', 'doc_id', 'docId',
        'file_id', 'fileId', 'message_id', 'messageId', 'post_id', 'postId',
        'comment_id', 'commentId', 'product_id', 'productId', 'item_id', 'itemId',
        'customer_id', 'customerId', 'ticket_id', 'ticketId', 'case_id', 'caseId',
        'profile_id', 'profileId', 'member_id', 'memberId', 'player_id', 'playerId'
    ]
    
    # Sensitive data indicators in responses
    SENSITIVE_INDICATORS = [
        'email', 'phone', 'address', 'ssn', 'password', 'credit_card', 
        'api_key', 'token', 'secret', 'private', 'salary', 'balance',
        'account_number', 'dob', 'birth', 'admin', 'role', 'permission'
    ]
    
    def __init__(self, max_fuzz_range: int = 20, request_delay: float = 0.5):
        """
        Initialize IDOR tester.
        
        Args:
            max_fuzz_range: Maximum number of IDs to fuzz per parameter (default: 20, reduced from 100 for legal compliance)
            request_delay: Delay between requests in seconds (default: 0.5s for rate limit respect)
        """
        self.max_fuzz_range = max_fuzz_range
        self.request_delay = request_delay
        self.tested_urls = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Trishul Security Scanner)'
        })
        self.request_count = 0
        
    def test_urls(self, urls: List[str], cookies: Dict = None) -> List[Dict]:
        """
        Test a list of URLs for IDOR vulnerabilities.
        
        Args:
            urls: List of URLs to test
            cookies: Optional authentication cookies
            
        Returns:
            List of IDOR findings
        """
        if cookies:
            self.session.cookies.update(cookies)
            
        findings = []
        
        for url in urls:
            if url in self.tested_urls:
                continue
                
            self.tested_urls.add(url)
            
            try:
                # Extract and test ID parameters
                result = self._test_single_url(url)
                if result:
                    findings.extend(result)
                    for finding in result:
                        logging.warning(f"🚨 IDOR FOUND: {finding['url']} - {finding['description']}")
            except Exception as e:
                logging.debug(f"Error testing {url}: {e}")
                
        return findings
    
    def _test_single_url(self, url: str) -> List[Dict]:
        """Test a single URL for IDOR vulnerabilities."""
        findings = []
        
        # Parse URL
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Find ID parameters in query string
        for param_name in query_params:
            if self._is_id_parameter(param_name):
                original_value = query_params[param_name][0]
                
                # Try to parse as integer
                try:
                    original_id = int(original_value)
                    result = self._fuzz_numeric_id(url, param_name, original_id)
                    if result:
                        findings.extend(result)
                except ValueError:
                    # Not a numeric ID, might be UUID or hash
                    logging.debug(f"Non-numeric ID in {param_name}: {original_value}")
                    
        # Also check path parameters (e.g., /api/user/123/profile)
        path_parts = parsed.path.split('/')
        for i, part in enumerate(path_parts):
            if part.isdigit():
                result = self._fuzz_path_id(url, i, int(part))
                if result:
                    findings.extend(result)
                    
        return findings
    
    def _is_id_parameter(self, param_name: str) -> bool:
        """Check if parameter name looks like an ID parameter."""
        param_lower = param_name.lower()
        return any(id_param in param_lower for id_param in self.ID_PARAMETERS)
    
    def _fuzz_numeric_id(self, url: str, param_name: str, original_id: int) -> List[Dict]:
        """
        Fuzz numeric ID parameter with different values.
        
        Tests for:
        - Horizontal privilege escalation (accessing other users' data)
        - Information disclosure
        """
        findings = []
        
        # Get baseline response
        try:
            baseline_response = self.session.get(url, timeout=10, allow_redirects=False)
            baseline_status = baseline_response.status_code
            baseline_content = baseline_response.text
            baseline_length = len(baseline_content)
            
            # Skip if original request failed
            if baseline_status in [401, 403, 404]:
                return findings
                
        except Exception as e:
            logging.debug(f"Baseline request failed for {url}: {e}")
            return findings
        
        # Test sequential IDs around the original
        test_ids = self._generate_test_ids(original_id)
        
        for test_id in test_ids:
            if test_id == original_id:
                continue
                
            try:
                # Rate limiting - respect target's resources
                time.sleep(self.request_delay)
                self.request_count += 1
                
                # Replace ID in URL
                test_url = self._replace_param_value(url, param_name, str(test_id))
                
                # Make request
                test_response = self.session.get(test_url, timeout=10, allow_redirects=False)
                
                # Analyze response
                if self._is_idor_vulnerable(baseline_response, test_response):
                    severity = self._assess_severity(test_response.text)
                    
                    findings.append({
                        'type': 'IDOR',
                        'url': url,
                        'vulnerable_url': test_url,
                        'parameter': param_name,
                        'original_id': original_id,
                        'leaked_id': test_id,
                        'severity': severity,
                        'description': f'Horizontal privilege escalation via {param_name}',
                        'evidence': f'Successfully accessed ID {test_id} (original: {original_id})',
                        'status_code': test_response.status_code,
                        'response_length': len(test_response.text),
                        'cvss': 8.2 if severity == 'CRITICAL' else 6.5,
                        'impact': 'Unauthorized access to other users\' data',
                        'remediation': 'Implement proper authorization checks before returning sensitive data'
                    })
                    
                    # Limit findings per URL to avoid noise
                    if len(findings) >= 3:
                        break
                        
            except Exception as e:
                logging.debug(f"Error testing ID {test_id}: {e}")
                continue
                
        return findings
    
    def _fuzz_path_id(self, url: str, position: int, original_id: int) -> List[Dict]:
        """Fuzz ID in URL path (e.g., /api/user/123/profile)."""
        findings = []
        
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        
        # Get baseline
        try:
            baseline_response = self.session.get(url, timeout=10)
            if baseline_response.status_code in [401, 403, 404]:
                return findings
        except:
            return findings
        
        # Test a few IDs
        test_ids = self._generate_test_ids(original_id, count=10)
        
        for test_id in test_ids:
            if test_id == original_id:
                continue
                
            # Rate limiting
            time.sleep(self.request_delay)
            self.request_count += 1
            
            # Replace ID in path
            new_parts = path_parts.copy()
            new_parts[position] = str(test_id)
            new_path = '/'.join(new_parts)
            
            test_url = urlunparse((
                parsed.scheme, parsed.netloc, new_path,
                parsed.params, parsed.query, parsed.fragment
            ))
            
            try:
                test_response = self.session.get(test_url, timeout=10)
                
                if self._is_idor_vulnerable(baseline_response, test_response):
                    severity = self._assess_severity(test_response.text)
                    
                    findings.append({
                        'type': 'IDOR',
                        'url': url,
                        'vulnerable_url': test_url,
                        'parameter': f'path[{position}]',
                        'original_id': original_id,
                        'leaked_id': test_id,
                        'severity': severity,
                        'description': 'Path-based IDOR vulnerability',
                        'evidence': f'Accessed different user data via path ID {test_id}',
                        'cvss': 7.5,
                        'impact': 'Unauthorized data access'
                    })
                    
                    if len(findings) >= 2:
                        break
                        
            except:
                continue
                
        return findings
    
    def _generate_test_ids(self, original_id: int, count: int = None) -> List[int]:
        """Generate list of IDs to test."""
        if count is None:
            count = min(self.max_fuzz_range, 50)
            
        test_ids = set()
        
        # Sequential IDs around the original
        test_ids.update(range(max(1, original_id - 10), original_id))
        test_ids.update(range(original_id + 1, original_id + count))
        
        # Common IDs
        test_ids.update([1, 2, 3, 100, 1000])
        
        return sorted(list(test_ids))[:count]
    
    def _replace_param_value(self, url: str, param_name: str, new_value: str) -> str:
        """Replace parameter value in URL."""
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        query_params[param_name] = [new_value]
        
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, new_query, parsed.fragment
        ))
    
    def _is_idor_vulnerable(self, baseline_response, test_response) -> bool:
        """
        Determine if test response indicates IDOR vulnerability.
        
        Checks:
        - Different successful response (200) with similar content
        - Content length similarity
        - Different data but similar structure
        """
        # Both must be successful
        if test_response.status_code not in [200, 201]:
            return False
            
        # Must not be error pages
        if test_response.status_code == baseline_response.status_code == 200:
            base_len = len(baseline_response.text)
            test_len = len(test_response.text)
            
            # Similar length (within 20% variance)
            length_ratio = test_len / base_len if base_len > 0 else 0
            if 0.8 <= length_ratio <= 1.2 and test_len > 100:
                
                # Check if content is actually different (not same data)
                similarity = self._content_similarity(
                    baseline_response.text,
                    test_response.text
                )
                
                # 30-95% similar = different data, same structure = IDOR
                if 0.3 <= similarity <= 0.95:
                    return True
                    
        return False
    
    def _content_similarity(self, text1: str, text2: str) -> float:
        """Calculate content similarity ratio (0-1)."""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _assess_severity(self, response_text: str) -> str:
        """Assess severity based on response content."""
        text_lower = response_text.lower()
        
        # Check for sensitive data indicators
        sensitive_count = sum(
            1 for indicator in self.SENSITIVE_INDICATORS
            if indicator in text_lower
        )
        
        if sensitive_count >= 3:
            return 'CRITICAL'
        elif sensitive_count >= 1:
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def generate_report(self, findings: List[Dict]) -> str:
        """Generate formatted report of IDOR findings."""
        if not findings:
            return "✅ No IDOR vulnerabilities found."
            
        report = f"\n🚨 IDOR VULNERABILITIES FOUND: {len(findings)}\n"
        report += "=" * 70 + "\n\n"
        
        for finding in findings:
            report += f"🎯 Type: {finding['type']}\n"
            report += f"   URL: {finding['url']}\n"
            report += f"   Parameter: {finding['parameter']}\n"
            report += f"   Original ID: {finding['original_id']}\n"
            report += f"   Leaked ID: {finding['leaked_id']}\n"
            report += f"   Severity: {finding['severity']} (CVSS {finding['cvss']})\n"
            report += f"   Description: {finding['description']}\n"
            report += f"   Evidence: {finding['evidence']}\n"
            report += f"   Impact: {finding['impact']}\n"
            if 'remediation' in finding:
                report += f"   Fix: {finding['remediation']}\n"
            report += "-" * 70 + "\n"
            
        return report


def test_idor_tester():
    """Test the IDOR tester."""
    tester = IDORTester(max_fuzz_range=20)
    
    # Test with sample URLs
    test_urls = [
        'http://testphp.vulnweb.com/userinfo.php?user=1',
    ]
    
    findings = tester.test_urls(test_urls)
    print(tester.generate_report(findings))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_idor_tester()
