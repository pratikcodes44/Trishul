#!/usr/bin/env python3
"""
Scope Validator - Ensures all targets are authorized for testing
Critical for legal compliance with bug bounty programs and CFAA
"""

import re
import sys
import fnmatch
from urllib.parse import urlparse
from typing import List, Optional
from pathlib import Path


class ScopeValidator:
    """Validates targets against authorized scope definitions"""
    
    def __init__(self, scope_file: Optional[str] = None, strict_mode: bool = True):
        """
        Initialize scope validator
        
        Args:
            scope_file: Path to file containing in-scope patterns
            strict_mode: If True, requires scope file and exits on out-of-scope
        """
        self.scope_file = scope_file
        self.strict_mode = strict_mode
        self.scope_patterns: List[str] = []
        self.out_of_scope_patterns: List[str] = []
        
        if scope_file:
            self._load_scope_file(scope_file)
    
    def _load_scope_file(self, filepath: str):
        """Load scope patterns from file"""
        if not Path(filepath).exists():
            print(f"❌ Scope file not found: {filepath}")
            sys.exit(1)
        
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Out-of-scope patterns start with !
                if line.startswith('!'):
                    self.out_of_scope_patterns.append(line[1:].strip())
                else:
                    self.scope_patterns.append(line)
        
        print(f"✓ Loaded {len(self.scope_patterns)} in-scope patterns")
        if self.out_of_scope_patterns:
            print(f"✓ Loaded {len(self.out_of_scope_patterns)} exclusion patterns")
    
    def validate_target(self, target: str) -> bool:
        """
        Validate if target is in authorized scope
        
        Args:
            target: Domain, URL, or IP to validate
            
        Returns:
            True if in scope, False otherwise
        """
        # No scope file = require explicit consent
        if not self.scope_file:
            if self.strict_mode:
                print("\n⚠️  WARNING: No scope file provided!")
                print("You are about to test targets without scope validation.")
                print("This could lead to unauthorized access violations.\n")
                response = input("Do you have explicit authorization? (type 'YES I DO'): ")
                if response != 'YES I DO':
                    print("❌ Scan aborted. Authorization required.")
                    sys.exit(0)
                return True
            else:
                # Non-strict mode allows proceeding with warning
                return True
        
        # Extract domain from URL if needed
        domain = self._extract_domain(target)
        
        # Check exclusions first (higher priority)
        for pattern in self.out_of_scope_patterns:
            if self._matches_pattern(domain, pattern):
                return False
        
        # Check in-scope patterns
        for pattern in self.scope_patterns:
            if self._matches_pattern(domain, pattern):
                return True
        
        return False
    
    def _extract_domain(self, target: str) -> str:
        """Extract domain from URL or return as-is if already a domain"""
        # If it looks like a URL, parse it
        if '://' in target:
            parsed = urlparse(target)
            return parsed.netloc or parsed.path
        
        # If it has a path, extract just the domain
        if '/' in target:
            return target.split('/')[0]
        
        return target
    
    def _matches_pattern(self, domain: str, pattern: str) -> bool:
        """
        Check if domain matches scope pattern
        
        Supports:
        - Exact matches: example.com
        - Wildcards: *.example.com
        - Subdomain wildcards: **.example.com (matches all levels)
        - CIDR notation: 192.168.1.0/24
        - Regex: regex:^.*\\.example\\.com$
        """
        # Exact match
        if domain == pattern:
            return True
        
        # Regex pattern
        if pattern.startswith('regex:'):
            regex = pattern[6:]
            return bool(re.match(regex, domain))
        
        # CIDR notation for IPs
        if '/' in pattern and self._is_ip(domain):
            return self._ip_in_cidr(domain, pattern)
        
        # Wildcard matching
        if '*' in pattern:
            # Convert ** to match any subdomain levels
            if pattern.startswith('**.'):
                # **.example.com matches api.v2.example.com
                base_domain = pattern[3:]
                return domain.endswith(base_domain) or domain == base_domain
            
            # Standard wildcard
            return fnmatch.fnmatch(domain, pattern)
        
        # Subdomain match (example.com matches api.example.com)
        if domain.endswith('.' + pattern):
            return True
        
        return False
    
    def _is_ip(self, address: str) -> bool:
        """Check if address is an IP"""
        return bool(re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', address))
    
    def _ip_in_cidr(self, ip: str, cidr: str) -> bool:
        """Check if IP is in CIDR range (basic implementation)"""
        try:
            import ipaddress
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
        except ImportError:
            # Fallback: just match the network prefix
            network = cidr.split('/')[0]
            prefix_len = int(cidr.split('/')[1])
            octets_to_match = prefix_len // 8
            
            ip_parts = ip.split('.')[:octets_to_match]
            net_parts = network.split('.')[:octets_to_match]
            
            return ip_parts == net_parts
    
    def validate_or_exit(self, target: str) -> bool:
        """
        Validate target or exit if out of scope (strict mode)
        
        Args:
            target: Target to validate
            
        Returns:
            True if validated (in strict mode, will exit if invalid)
        """
        is_valid = self.validate_target(target)
        
        if not is_valid:
            domain = self._extract_domain(target)
            print(f"\n❌ OUT OF SCOPE: {domain}")
            print(f"Target '{target}' is not in authorized scope.")
            
            if self.strict_mode:
                print("\n⚠️  Testing out-of-scope targets is illegal without authorization.")
                print("This may violate the Computer Fraud and Abuse Act (CFAA) or similar laws.\n")
                sys.exit(1)
            else:
                print("⚠️  Continuing anyway (non-strict mode)\n")
        
        return is_valid
    
    def get_scope_summary(self) -> dict:
        """Get summary of scope configuration"""
        return {
            'scope_file': self.scope_file,
            'strict_mode': self.strict_mode,
            'in_scope_patterns': len(self.scope_patterns),
            'exclusion_patterns': len(self.out_of_scope_patterns),
            'patterns': self.scope_patterns[:5]  # First 5 for display
        }


def create_example_scope_file(output_path: str = "scope.txt"):
    """Create an example scope file for users"""
    example_content = """# Trishul Scope File
# Define authorized testing targets
# Lines starting with # are comments
# Lines starting with ! are exclusions (out of scope)

# Exact domain
example.com

# All subdomains (wildcard)
*.example.com

# All subdomain levels (deep wildcard)
**.api.example.com

# Specific subdomain
staging.example.com

# IP addresses
192.168.1.100

# CIDR range
10.0.0.0/8

# Regex pattern (advanced)
regex:^.*\\.test\\.example\\.com$

# Exclusions (must NOT test these)
!production.example.com
!admin.example.com
!*.internal.example.com
"""
    
    with open(output_path, 'w') as f:
        f.write(example_content)
    
    print(f"✓ Created example scope file: {output_path}")
    print("Edit this file with your authorized targets before scanning.")


if __name__ == "__main__":
    # Demo and testing
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "create-example":
        create_example_scope_file()
        sys.exit(0)
    
    # Test validation
    print("=== Scope Validator Test ===\n")
    
    # Create test scope file
    test_scope = """example.com
*.example.com
192.168.1.0/24
!admin.example.com
"""
    with open('/tmp/test_scope.txt', 'w') as f:
        f.write(test_scope)
    
    validator = ScopeValidator('/tmp/test_scope.txt', strict_mode=False)
    
    test_cases = [
        ("example.com", True),
        ("api.example.com", True),
        ("deep.api.example.com", True),
        ("admin.example.com", False),  # Excluded
        ("other.com", False),
        ("192.168.1.50", True),
        ("192.168.2.50", False),
    ]
    
    print("Test Results:")
    for target, expected in test_cases:
        result = validator.validate_target(target)
        status = "✓" if result == expected else "✗"
        print(f"{status} {target}: {result} (expected {expected})")
    
    print("\nScope Summary:")
    summary = validator.get_scope_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
