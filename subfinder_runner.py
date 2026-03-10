import subprocess
import logging
from typing import List

from scope_checker import ScopeChecker

class SubfinderRunner:
    """
    A secure wrapper for the BlackArch subfinder binary.
    Executes subfinder, captures the output, and filters subdomains strictly 
    using the ScopeChecker class to ensure they fall within the root domain's scope.
    """
    def __init__(self, timeout: int = 300):
        self.scope_checker = ScopeChecker()
        self.timeout = timeout

    def discover_subdomains(self, root_domain: str) -> List[str]:
        """
        Executes subfinder for the given root domain and returns a clean, 
        deduplicated list of in-scope subdomains.
        """
        if not root_domain:
            return []

        command = ["subfinder", "-d", root_domain, "-silent"]
        
        try:
            # Execute subfinder safely using subprocess.run
            result = subprocess.run(
                command,
                capture_output=True,
                timeout=self.timeout,
                check=False
            )
            
            # Decode the byte output to a UTF-8 string
            output = result.stdout.decode('utf-8', errors='replace')
            
        except FileNotFoundError:
            logging.error("Subfinder binary not found. Please ensure it is installed and in your PATH.")
            return []
        except subprocess.TimeoutExpired:
            logging.error(f"Subfinder execution timed out after {self.timeout} seconds for domain {root_domain}.")
            return []
        except Exception as e:
            logging.error(f"Unexpected error executing subfinder: {e}")
            return []

        # Split output by newlines to create a Python list of discovered subdomains
        raw_subdomains = output.splitlines()
        
        valid_subdomains_set = set()
        
        # Mandatory Filtering: Pass every single one through the is_in_scope() method
        for subdomain in raw_subdomains:
            subdomain = subdomain.strip()
            if subdomain and self.scope_checker.is_in_scope(subdomain, root_domain):
                valid_subdomains_set.add(subdomain)
                
        # Return a deduplicated, clean list containing ONLY the subdomains that passed the scope check
        return list(valid_subdomains_set)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    runner = SubfinderRunner(timeout=60)
    print("SubfinderRunner initialized successfully.")
    # Example usage:
    # root = "example.com"
    # res = runner.discover_subdomains(root)
    # print(f"Found {len(res)} valid subdomains for {root}: {res}")
