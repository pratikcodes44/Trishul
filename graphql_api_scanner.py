"""
GraphQL + API Security Scanner
Tests GraphQL endpoints, REST APIs, and discovers vulnerabilities.
"""

import requests
import json
import logging
import time
from typing import List, Dict, Set
from urllib.parse import urlparse, urljoin
import re

class GraphQLAPIScanner:
    """
    Comprehensive GraphQL and REST API security scanner.
    """
    
    # Common GraphQL endpoint paths
    GRAPHQL_PATHS = [
        '/graphql', '/graphiql', '/api/graphql', '/v1/graphql', 
        '/v2/graphql', '/query', '/api/query', '/console',
        '/graphql/console', '/graphql.php', '/gql', '/api/gql'
    ]
    
    # GraphQL introspection query
    INTROSPECTION_QUERY = """
    query IntrospectionQuery {
        __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
                ...FullType
            }
        }
    }
    fragment FullType on __Type {
        kind
        name
        description
        fields(includeDeprecated: true) {
            name
            description
            args {
                ...InputValue
            }
            type {
                ...TypeRef
            }
        }
    }
    fragment InputValue on __InputValue {
        name
        description
        type { ...TypeRef }
        defaultValue
    }
    fragment TypeRef on __Type {
        kind
        name
        ofType {
            kind
            name
            ofType {
                kind
                name
            }
        }
    }
    """
    
    # REST API patterns to test
    API_PATTERNS = [
        '/api', '/api/v1', '/api/v2', '/v1', '/v2', '/rest',
        '/api/users', '/api/admin', '/api/auth', '/api/login'
    ]
    
    def __init__(self, request_delay: float = 0.5):
        """
        Initialize GraphQL + API scanner.
        
        Args:
            request_delay: Delay between requests in seconds (default: 0.5s for rate limit respect)
        """
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Trishul Security Scanner)',
            'Content-Type': 'application/json'
        })
        self.discovered_endpoints = set()
        self.request_count = 0
    
    def _rate_limited_request(self, method, url, **kwargs):
        """Make rate-limited HTTP request"""
        time.sleep(self.request_delay)
        self.request_count += 1
        return self.session.request(method, url, **kwargs)
        
    def scan_target(self, base_url: str, cookies: Dict = None) -> List[Dict]:
        """
        Scan target for GraphQL and API vulnerabilities.
        
        Args:
            base_url: Base URL to scan
            cookies: Optional authentication cookies
            
        Returns:
            List of findings
        """
        if cookies:
            self.session.cookies.update(cookies)
            
        findings = []
        
        # Step 1: Discover GraphQL endpoints
        graphql_endpoints = self._discover_graphql_endpoints(base_url)
        
        # Step 2: Test each GraphQL endpoint
        for endpoint in graphql_endpoints:
            results = self._test_graphql_endpoint(endpoint)
            findings.extend(results)
            
        # Step 3: Discover REST API endpoints
        api_endpoints = self._discover_api_endpoints(base_url)
        
        # Step 4: Test REST APIs
        for endpoint in api_endpoints:
            results = self._test_rest_api(endpoint)
            findings.extend(results)
            
        return findings
    
    def _discover_graphql_endpoints(self, base_url: str) -> Set[str]:
        """Discover GraphQL endpoints by checking common paths."""
        endpoints = set()
        
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        for path in self.GRAPHQL_PATHS:
            url = urljoin(base, path)
            
            try:
                # Try GET request
                response = self.session.get(url, timeout=10)
                if self._is_graphql_endpoint(response):
                    endpoints.add(url)
                    logging.info(f"🔍 Found GraphQL endpoint: {url}")
                    continue
                    
                # Try POST with introspection
                response = self.session.post(
                    url,
                    json={'query': '{ __typename }'},
                    timeout=10
                )
                if self._is_graphql_endpoint(response):
                    endpoints.add(url)
                    logging.info(f"🔍 Found GraphQL endpoint: {url}")
                    
            except Exception as e:
                logging.debug(f"Error checking {url}: {e}")
                
        return endpoints
    
    def _is_graphql_endpoint(self, response) -> bool:
        """Check if response indicates a GraphQL endpoint."""
        if response.status_code == 200:
            try:
                data = response.json()
                # GraphQL responses have 'data' or 'errors' key
                if 'data' in data or 'errors' in data:
                    return True
            except:
                pass
                
            # Check content for GraphQL indicators
            content = response.text.lower()
            indicators = ['graphql', 'graphiql', '__schema', '__type', 'query', 'mutation']
            return sum(1 for ind in indicators if ind in content) >= 2
            
        return False
    
    def _test_graphql_endpoint(self, endpoint: str) -> List[Dict]:
        """Test a GraphQL endpoint for vulnerabilities."""
        findings = []
        
        # Test 1: Introspection enabled
        introspection_result = self._test_introspection(endpoint)
        if introspection_result:
            findings.append(introspection_result)
            
        # Test 2: Authorization bypass
        auth_result = self._test_graphql_auth_bypass(endpoint)
        if auth_result:
            findings.extend(auth_result)
            
        # Test 3: Query depth limit
        depth_result = self._test_query_depth_limit(endpoint)
        if depth_result:
            findings.append(depth_result)
            
        # Test 4: Field suggestions
        suggestion_result = self._test_field_suggestions(endpoint)
        if suggestion_result:
            findings.append(suggestion_result)
            
        return findings
    
    def _test_introspection(self, endpoint: str) -> Dict:
        """Test if GraphQL introspection is enabled."""
        try:
            response = self.session.post(
                endpoint,
                json={'query': self.INTROSPECTION_QUERY},
                timeout=15
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'data' in data and '__schema' in data['data']:
                        schema = data['data']['__schema']
                        types_count = len(schema.get('types', []))
                        
                        return {
                            'type': 'GraphQL Introspection Enabled',
                            'endpoint': endpoint,
                            'severity': 'MEDIUM',
                            'description': 'GraphQL introspection query is enabled',
                            'evidence': f'Exposed {types_count} schema types',
                            'impact': 'Attackers can enumerate entire API schema and discover hidden functionality',
                            'cvss': 5.3,
                            'remediation': 'Disable introspection in production environments',
                            'schema_types': types_count
                        }
                except:
                    pass
                    
        except Exception as e:
            logging.debug(f"Introspection test failed: {e}")
            
        return None
    
    def _test_graphql_auth_bypass(self, endpoint: str) -> List[Dict]:
        """Test for authorization bypass vulnerabilities."""
        findings = []
        
        # Test queries that might expose sensitive data without auth
        test_queries = [
            ('users', '{ users { id email name } }'),
            ('user', '{ user(id: 1) { id email name role } }'),
            ('admin', '{ admin { users { email } } }'),
            ('me', '{ me { id email role isAdmin } }'),
        ]
        
        for query_name, query in test_queries:
            try:
                response = self.session.post(
                    endpoint,
                    json={'query': query},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data'] and query_name in data['data']:
                        findings.append({
                            'type': 'GraphQL Authorization Bypass',
                            'endpoint': endpoint,
                            'severity': 'HIGH',
                            'description': f'Query "{query_name}" accessible without authentication',
                            'evidence': f'Successfully executed: {query}',
                            'query': query,
                            'response_data': str(data)[:200],
                            'cvss': 7.5,
                            'impact': 'Unauthorized access to sensitive data',
                            'remediation': 'Implement proper field-level authorization'
                        })
                        
            except Exception as e:
                logging.debug(f"Auth bypass test failed for {query_name}: {e}")
                
        return findings
    
    def _test_query_depth_limit(self, endpoint: str) -> Dict:
        """Test if query depth limits are enforced."""
        # Create deeply nested query
        deep_query = "{ user { friends { friends { friends { friends { friends { id } } } } } } }"
        
        try:
            response = self.session.post(
                endpoint,
                json={'query': deep_query},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and not ('errors' in data):
                    return {
                        'type': 'GraphQL Depth Limit Bypass',
                        'endpoint': endpoint,
                        'severity': 'MEDIUM',
                        'description': 'No query depth limit enforced',
                        'evidence': 'Deeply nested query executed successfully',
                        'cvss': 5.0,
                        'impact': 'Potential DoS via resource exhaustion',
                        'remediation': 'Implement query depth and complexity limits'
                    }
                    
        except Exception as e:
            logging.debug(f"Depth limit test failed: {e}")
            
        return None
    
    def _test_field_suggestions(self, endpoint: str) -> Dict:
        """Test if field suggestions leak schema information."""
        # Query with typo to trigger suggestions
        typo_query = "{ userz { id } }"
        
        try:
            response = self.session.post(
                endpoint,
                json={'query': typo_query},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'errors' in data:
                    error_msg = str(data['errors'])
                    # Check if error contains field suggestions
                    if 'did you mean' in error_msg.lower() or 'suggestion' in error_msg.lower():
                        return {
                            'type': 'GraphQL Field Suggestion Leak',
                            'endpoint': endpoint,
                            'severity': 'LOW',
                            'description': 'GraphQL provides field suggestions in errors',
                            'evidence': error_msg[:200],
                            'cvss': 3.1,
                            'impact': 'Information disclosure via error messages',
                            'remediation': 'Disable field suggestions in production'
                        }
                        
        except Exception as e:
            logging.debug(f"Field suggestion test failed: {e}")
            
        return None
    
    def _discover_api_endpoints(self, base_url: str) -> Set[str]:
        """Discover REST API endpoints."""
        endpoints = set()
        
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        for path in self.API_PATTERNS:
            url = urljoin(base, path)
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code in [200, 401, 403]:
                    endpoints.add(url)
                    logging.info(f"🔍 Found API endpoint: {url}")
                    
            except Exception as e:
                logging.debug(f"Error checking {url}: {e}")
                
        return endpoints
    
    def _test_rest_api(self, endpoint: str) -> List[Dict]:
        """Test REST API endpoint for common vulnerabilities."""
        findings = []
        
        # Test 1: HTTP methods
        method_result = self._test_http_methods(endpoint)
        if method_result:
            findings.extend(method_result)
            
        # Test 2: API documentation exposed
        docs_result = self._test_api_docs(endpoint)
        if docs_result:
            findings.append(docs_result)
            
        # Test 3: Mass assignment
        mass_assignment = self._test_mass_assignment(endpoint)
        if mass_assignment:
            findings.append(mass_assignment)
            
        return findings
    
    def _test_http_methods(self, endpoint: str) -> List[Dict]:
        """Test for insecure HTTP methods."""
        findings = []
        
        dangerous_methods = ['PUT', 'DELETE', 'PATCH']
        
        for method in dangerous_methods:
            try:
                response = self.session.request(method, endpoint, timeout=10)
                
                # Check if method is allowed (not 405 Method Not Allowed)
                if response.status_code not in [405, 501]:
                    findings.append({
                        'type': 'Insecure HTTP Method Allowed',
                        'endpoint': endpoint,
                        'severity': 'MEDIUM',
                        'description': f'HTTP {method} method is allowed',
                        'evidence': f'{method} {endpoint} returned {response.status_code}',
                        'method': method,
                        'cvss': 5.3,
                        'impact': 'Potential unauthorized data modification',
                        'remediation': 'Restrict HTTP methods to only those required'
                    })
                    
            except Exception as e:
                logging.debug(f"HTTP method test failed for {method}: {e}")
                
        return findings
    
    def _test_api_docs(self, endpoint: str) -> Dict:
        """Check if API documentation is exposed."""
        doc_paths = ['/docs', '/api-docs', '/swagger', '/swagger.json', '/openapi.json']
        
        parsed = urlparse(endpoint)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        for doc_path in doc_paths:
            url = urljoin(base, doc_path)
            
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    content = response.text.lower()
                    if any(x in content for x in ['swagger', 'openapi', 'api documentation']):
                        return {
                            'type': 'API Documentation Exposed',
                            'endpoint': url,
                            'severity': 'LOW',
                            'description': 'API documentation is publicly accessible',
                            'evidence': f'Found at {url}',
                            'cvss': 3.7,
                            'impact': 'Information disclosure of API structure',
                            'remediation': 'Restrict access to API documentation'
                        }
                        
            except:
                continue
                
        return None
    
    def _test_mass_assignment(self, endpoint: str) -> Dict:
        """Test for mass assignment vulnerability."""
        # Attempt to set privileged fields
        payloads = [
            {'role': 'admin', 'isAdmin': True},
            {'admin': True, 'superuser': True},
            {'permissions': ['admin', 'write', 'delete']}
        ]
        
        for payload in payloads:
            try:
                response = self.session.post(
                    endpoint,
                    json=payload,
                    timeout=10
                )
                
                # Check if the payload was accepted (200/201)
                if response.status_code in [200, 201]:
                    try:
                        resp_data = response.json()
                        # Check if privileged field appears in response
                        for key in payload.keys():
                            if key in str(resp_data):
                                return {
                                    'type': 'Mass Assignment Vulnerability',
                                    'endpoint': endpoint,
                                    'severity': 'HIGH',
                                    'description': 'API accepts privileged fields without validation',
                                    'evidence': f'Successfully sent: {payload}',
                                    'payload': payload,
                                    'cvss': 7.5,
                                    'impact': 'Privilege escalation via mass assignment',
                                    'remediation': 'Implement allowlist for accepted fields'
                                }
                    except:
                        pass
                        
            except Exception as e:
                logging.debug(f"Mass assignment test failed: {e}")
                
        return None
    
    def generate_report(self, findings: List[Dict]) -> str:
        """Generate formatted report."""
        if not findings:
            return "✅ No GraphQL/API vulnerabilities found."
            
        report = f"\n🚨 GRAPHQL/API VULNERABILITIES FOUND: {len(findings)}\n"
        report += "=" * 70 + "\n\n"
        
        for finding in findings:
            report += f"🎯 Type: {finding['type']}\n"
            report += f"   Endpoint: {finding['endpoint']}\n"
            report += f"   Severity: {finding['severity']} (CVSS {finding['cvss']})\n"
            report += f"   Description: {finding['description']}\n"
            report += f"   Evidence: {finding['evidence']}\n"
            report += f"   Impact: {finding['impact']}\n"
            report += f"   Fix: {finding['remediation']}\n"
            report += "-" * 70 + "\n"
            
        return report


def test_graphql_scanner():
    """Test the GraphQL scanner."""
    scanner = GraphQLAPIScanner()
    
    # Test with sample endpoint
    findings = scanner.scan_target('http://localhost:5000')
    print(scanner.generate_report(findings))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_graphql_scanner()
