import subprocess
import logging

class PortScanner:
    def __init__(self, timeout=3600):
        self.binary = "naabu"
        self.timeout = timeout

    def scan_ports(self, domains):
        if not domains:
            return []
        
        logging.info(f"Firing the X-Ray (Naabu) at {len(domains)} targets to find hidden ports...")
        
        # -silent for clean output, -top-ports 100 for a fast, lethal scan
        # -c 50 limits concurrent connections to avoid crashing your router
        cmd = [
            self.binary,
            "-silent",
            "-top-ports", "100",
            "-c", "50"
        ]
        
        active_ports = []
        try:
            # Pass the raw, in-scope domains directly into Naabu
            process = subprocess.run(
                cmd,
                input="\n".join(domains),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Grab every domain:port combination Naabu finds
            for line in process.stdout.splitlines():
                clean_target = line.strip()
                if clean_target:
                    active_ports.append(clean_target)
                    
        except FileNotFoundError:
            logging.error(f"CRITICAL: Python cannot find the '{self.binary}' tool.")
        except subprocess.TimeoutExpired:
            logging.error("Naabu port scan timed out.")
        except Exception as e:
            logging.error(f"Unexpected Naabu error: {e}")
            
        unique_targets = list(set(active_ports))
        logging.info(f"Naabu discovered {len(unique_targets)} open ports across the infrastructure!")
        return unique_targets
