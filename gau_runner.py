import subprocess
import logging
import sys

class TimeMachine:
    def __init__(self):
        self.binary = "gau"
        # 🚀 THE SPEED FILTER: We drop these instantly so Nuclei doesn't waste time 🚀
        self.junk_extensions = [
            ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico", 
            ".css", ".woff", ".woff2", ".ttf", ".eot", 
            ".mp4", ".mp3", ".avi", ".pdf", ".txt"
        ]

    def fetch_history(self, target_domain):
        logging.info(f"Spinning up the Time Machine (gau) for {target_domain}...")
        
        # --threads 10: Makes it query the databases faster
        # --subs: Includes subdomains in the historical search
        cmd = [self.binary, "--threads", "10", "--subs", target_domain]
        
        historical_urls = []
        try:
            # We give gau a strict 5-minute timeout. It queries APIs, so it should be fast!
            process = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=sys.stderr, 
                text=True, 
                timeout=300
            )
            
            for line in process.stdout.splitlines():
                url = line.strip().lower()
                
                # The Filter Logic: Keep it if it doesn't end with a junk extension
                if url and not any(url.split("?")[0].endswith(ext) for ext in self.junk_extensions):
                    historical_urls.append(line.strip()) # Append the original casing
                    
        except FileNotFoundError:
            logging.error(f"CRITICAL: '{self.binary}' not found. Run: sudo pacman -S gau")
        except subprocess.TimeoutExpired:
            logging.warning("gau timeout reached. Using the historical data we found so far.")
        except Exception as e:
            logging.error(f"Unexpected gau error: {e}")
            
        # Deduplicate the list to save massive amounts of scanning time
        clean_urls = list(set(historical_urls))
        logging.info(f"Time Machine recovered {len(clean_urls)} clean, historical endpoints.")
        
        return clean_urls
