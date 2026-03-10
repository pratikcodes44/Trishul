import urllib.request
import json
import random
import logging

class BountyScout:
    def __init__(self):
        # We now pull the raw JSON data to extract the official program URLs!
        self.h1_url = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/hackerone_data.json"
        self.bc_url = "https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/bugcrowd_data.json"

    def get_random_target(self):
        logging.info("Scouting HackerOne and Bugcrowd databases for a legal target...")
        programs = []
        
        # 1. Fetch HackerOne Data
        try:
            req = urllib.request.Request(self.h1_url)
            with urllib.request.urlopen(req) as response:
                h1_data = json.loads(response.read().decode('utf-8'))
                for program in h1_data:
                    url = program.get("url", "Unknown URL")
                    in_scope = program.get("targets", {}).get("in_scope", [])
                    
                    domains = []
                    for item in in_scope:
                        asset = item.get("asset_identifier", "")
                        if isinstance(asset, str) and asset.startswith("*."):
                            clean_domain = asset.replace('*.', '').replace('*', '')
                            if clean_domain:
                                domains.append(clean_domain)
                    
                    if domains:
                        programs.append({
                            "platform": "HackerOne",
                            "program_url": url,
                            "domains": domains
                        })
        except Exception as e:
            logging.error(f"Failed to fetch HackerOne data: {e}")

        # 2. Fetch Bugcrowd Data
        try:
            req = urllib.request.Request(self.bc_url)
            with urllib.request.urlopen(req) as response:
                bc_data = json.loads(response.read().decode('utf-8'))
                for program in bc_data:
                    url = program.get("url", "Unknown URL")
                    in_scope = program.get("targets", {}).get("in_scope", [])
                    
                    domains = []
                    for item in in_scope:
                        asset = item.get("target", "")
                        if isinstance(asset, str) and asset.startswith("*."):
                            clean_domain = asset.replace('*.', '').replace('*', '')
                            if clean_domain:
                                domains.append(clean_domain)
                    
                    if domains:
                        programs.append({
                            "platform": "Bugcrowd",
                            "program_url": url,
                            "domains": domains
                        })
        except Exception as e:
            logging.error(f"Failed to fetch Bugcrowd data: {e}")

        # 3. Pick a random program and a random domain
        if programs:
            chosen_program = random.choice(programs)
            chosen_domain = random.choice(chosen_program["domains"])
            
            return {
                "domain": chosen_domain,
                "url": chosen_program["program_url"],
                "platform": chosen_program["platform"]
            }
        else:
            logging.error("Scout failed to find any programs. Defaulting to fallback.")
            return {
                "domain": "yahoo.com",
                "url": "https://hackerone.com/yahoo",
                "platform": "HackerOne"
            }
