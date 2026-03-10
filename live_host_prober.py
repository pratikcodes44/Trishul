import subprocess
import json
import logging

class LiveHostProber:
    def __init__(self, timeout=3600): # Increased to 1 hour for massive targets
        self.timeout = timeout
        self.binary = "httpx-pd" # The strict Arch Linux name

    def probe(self, subdomains):
        if not subdomains:
            return []
        
        logging.info(f"Firing the flashlight ({self.binary}) at {len(subdomains)} targets...")
        
        cmd = [
            self.binary,
            "-json",
            "-silent",
            "-title",
            "-status-code"
        ]
        
        live_hosts = []
        try:
            # Pass the subdomains directly into the BlackArch tool
            process = subprocess.run(
                cmd,
                input="\n".join(subdomains),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Sift through the results to format them nicely
            for line in process.stdout.splitlines():
                try:
                    data = json.loads(line)
                    url = data.get("url")
                    status = data.get("status_code", 0)
                    title = data.get("title", "No Title")
                    
                    if url:
                        # Formats it like: [200] https://admin.tesla.com (Tesla Login)
                        live_hosts.append(f"[{status}] {url} - {title}")
                except json.JSONDecodeError:
                    continue
                    
        except FileNotFoundError:
            logging.error(f"CRITICAL: Python still cannot find '{self.binary}'.")
        except subprocess.TimeoutExpired:
            logging.error(f"Prober timed out after {self.timeout} seconds.")
        except Exception as e:
            logging.error(f"Unexpected Prober error: {e}")
            
        return live_hosts
