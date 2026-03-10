import subprocess
import logging
import sys
import json

class NucleiRunner:
    def __init__(self):
        self.binary = "nuclei"

    def run_scan(self, urls, cookie=None):
        if not urls:
            return []
            
        logging.info(f"Unleashing Nuclei on {len(urls)} live targets...")
        
        cmd = [
            self.binary,
            "-silent",
            "-stats", # 🚀 THE VISIBILITY FIX: Forces Nuclei to print live updates
            "-tags", "cve,default-logins,exposed-panels,misconfig,vulnerability,takeovers,exposure", 
            "-rl", "500",
            "-j"
        ]

        # Removed the heavy '-as' logic! Keep it fast!

        if cookie:
            logging.info("Nuclei: Injecting Session Cookie for authenticated vulnerability scanning...")
            cmd.extend(["-H", f"Cookie: {cookie}"])

        vulnerabilities = []
        try:
            # We let stderr flow directly to the terminal so you can see the -stats updates!
            process = subprocess.run(
                cmd,
                input="\n".join(urls),
                stdout=subprocess.PIPE,
                stderr=sys.stderr, 
                text=True
            )
            
            for line in process.stdout.splitlines():
                if line.strip():
                    try:
                        parsed = json.loads(line)
                        vulnerabilities.append(line.strip())
                    except json.JSONDecodeError:
                        pass
                        
        except FileNotFoundError:
            logging.error(f"CRITICAL: Python cannot find the '{self.binary}' tool.")
        except Exception as e:
            logging.error(f"Unexpected Nuclei error: {e}")
            
        return vulnerabilities
