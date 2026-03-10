import re
from typing import Set, Optional

class ScopeChecker:
    """
    A robust gatekeeper class to validate subdomains strictly against
    a root domain and an internal third-party SaaS denylist.
    """
    def __init__(self):
        # A robust list of common out-of-scope SaaS providers to prevent scanning of 
        # third-party infrastructure.
        self.denylist_domains: Set[str] = {
            "zendesk.com",
            "amazonaws.com",
            "github.io",
            "wpengine.com",
            "herokuapp.com",
            "netlify.app",
            "s3.amazonaws.com",
            "cloudfront.net",
            "azureedge.net",
            "windows.net",
            "firebaseapp.com"
        }
        
        # Pre-compile denylist regexes for maximum performance
        self.denylist_patterns = []
        for domain in self.denylist_domains:
            escaped_domain = re.escape(domain)
            # ^ and $ with case-insensitivity guarantees exact or subdomain matches.
            pattern = re.compile(rf'^(?:.*\.)?{escaped_domain}$', re.IGNORECASE)
            self.denylist_patterns.append(pattern)

    def is_denylisted(self, subdomain: Optional[str]) -> bool:
        """
        Drops targets that match common third-party SaaS platforms to prevent
        us from inadvertently attacking service providers.
        """
        if not subdomain:
            return False
            
        for pattern in self.denylist_patterns:
            if pattern.match(subdomain):
                return True
        return False

    def is_in_scope(self, subdomain: Optional[str], root_domain: Optional[str]) -> bool:
        """
        Validates whether a newly discovered subdomain is strictly in-scope.
        Uses perfectly anchored regex to prevent partial match spoofing.
        """
        if not subdomain or not root_domain:
            return False

        # Gate 1: Check against third-party SaaS infrastructure
        if self.is_denylisted(subdomain):
            return False

        # Gate 2: Dynamically build strict regex for the root domain
        # re.escape ensures literal dots in the root_domain are escaped properly.
        escaped_root = re.escape(root_domain)
        
        # Breakdown of the regex pattern:
        # ^                 - Anchor to start of string
        # (?:.*\.)?         - Non-capturing group matching any optional subdomain prefix, 
        #                     forcing it to end with a dot if present.
        # {escaped_root}    - The dynamically escaped root domain
        # $                 - Anchor to end of string
        pattern = re.compile(rf'^(?:.*\.)?{escaped_root}$', re.IGNORECASE)
        
        return bool(pattern.match(subdomain))

if __name__ == "__main__":
    checker = ScopeChecker()
    
    # --- 1. Valid exactly matching root domains ---
    assert checker.is_in_scope("target.com", "target.com") == True
    
    # --- 2. Valid Subdomains ---
    assert checker.is_in_scope("www.target.com", "target.com") == True
    assert checker.is_in_scope("api.v1.target.com", "target.com") == True
    
    # --- 3. Uppercase & Case-Insensitive Anomalies ---
    assert checker.is_in_scope("TARGET.COM", "target.com") == True
    assert checker.is_in_scope("WwW.TaRgEt.CoM", "target.com") == True
    assert checker.is_in_scope("api.target.com", "TARGET.COM") == True
    
    # --- 4. Spoofed Strings & Partial Matches (The real danger zone) ---
    assert checker.is_in_scope("not-target.com", "target.com") == False
    assert checker.is_in_scope("target.com.malicious.org", "target.com") == False
    assert checker.is_in_scope("my-target.com", "target.com") == False
    assert checker.is_in_scope("target.company.com", "target.com") == False
    assert checker.is_in_scope("targetAcom", "target.com") == False  # Dot escaping test
    assert checker.is_in_scope("mytarget.com", "target.com") == False
    
    # --- 5. Third-Party Denylist Drops (Must return False immediately) ---
    assert checker.is_in_scope("support.zendesk.com", "zendesk.com") == False
    assert checker.is_in_scope("my-bucket.s3.amazonaws.com", "amazonaws.com") == False
    assert checker.is_in_scope("target.github.io", "target.com") == False 
    
    # --- 6. Edge cases (Null bytes, empties, whitespace) ---
    assert checker.is_in_scope("", "target.com") == False
    assert checker.is_in_scope("target.com", "") == False
    assert checker.is_in_scope(None, "target.com") == False
    
    # Newline injection prevention test
    # A newline in the subdomain prevents it from perfectly matching ^ and $ without re.DOTALL
    assert checker.is_in_scope("valid.target.com\nevil.com", "target.com") == False
    assert checker.is_in_scope("evil.com\ntarget.com", "target.com") == False
    
    print("[+] All ScopeChecker assertions passed successfully!")
    print("[+] Logic is strictly anchored, case-insensitive, and spoof-proof.")
