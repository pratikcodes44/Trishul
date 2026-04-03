import subprocess
import logging
import sys

class KatanaRunner:
    def __init__(self):
        self.binary = "katana"

    # THE FIX: Added 'cookie=None' parameter
    def crawl(self, urls, cookie=None):
        if not urls:
            return []
        
        logging.info(f"Unleashing Katana to crawl {len(urls)} live targets for hidden endpoints...")
        
        cmd = [
            self.binary,
            "-silent",
            "-d", "3",          
            "-jc",              
            "-c", "50",         
            "-ct", "2",         
            "-timeout", "10"    
        ]
        
        # 🍪 THE AUTHENTICATION UPGRADE 🍪
        if cookie:
            logging.info("Katana: Injecting Session Cookie for authenticated deep crawling...")
            # SECURITY: Strip newlines/carriage returns to prevent header injection
            safe_cookie = cookie.replace('\n', '').replace('\r', '').replace('\t', '')
            if safe_cookie != cookie:
                logging.warning("⚠️  Removed invalid characters from cookie")
            cmd.extend(["-H", f"Cookie: {safe_cookie}"])
        
        deep_urls = []
        try:
            process = subprocess.run(
                cmd,
                input="\n".join(urls),
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                text=True,
                timeout=1800 
            )
            
            for line in process.stdout.splitlines():
                if line.strip():
                    deep_urls.append(line.strip())
                    
        except FileNotFoundError:
            logging.error(f"CRITICAL: Python cannot find the '{self.binary}' tool.")
        except subprocess.TimeoutExpired:
            logging.warning("Katana global timeout reached. Proceeding with what it found so far...")
        except Exception as e:
            logging.error(f"Unexpected Katana error: {e}")
            
        return list(set(deep_urls))
