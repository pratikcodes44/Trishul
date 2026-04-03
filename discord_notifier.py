import requests
import logging
import json

import os

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

    def send_alert(self, target, vulnerabilities):
        if self.webhook_url == "YOUR_WEBHOOK_URL_HERE" or not self.webhook_url:
            logging.warning("Discord Webhook URL not set. Skipping notification.")
            return

        if not vulnerabilities:
            logging.info("No vulnerabilities found. No alert sent.")
            return

        vuln_count = len(vulnerabilities)
        logging.info(f"📢 Pushing alert to Discord for {vuln_count} findings...")
        
        # Build the visual "Embed" for Discord
        embed = {
            "title": f"🎯 Target Compromised: {target}",
            "description": f"Trishul AI Agent has successfully completed the strike and identified **{vuln_count}** vulnerabilities.",
            "color": 16711680, # Hacker Red color code
            "fields": []
        }

        # We extract the details of the top 5 vulnerabilities to keep the message clean
        for v in vulnerabilities[:5]:
            try:
                data = json.loads(v)
                name = data.get("info", {}).get("name", "Unknown Vulnerability")
                severity = data.get("info", {}).get("severity", "info").upper()
                url = data.get("matched-at", "Unknown Endpoint")
                
                # Add a visually distinct block for each bug
                embed["fields"].append({
                    "name": f"[{severity}] {name}",
                    "value": f"```\n{url}\n```", # Formatted as code block
                    "inline": False
                })
            except json.JSONDecodeError:
                pass

        if vuln_count > 5:
            embed["fields"].append({
                "name": "...",
                "value": f"And **{vuln_count - 5}** more findings. Check the local JSON report for full details.",
                "inline": False
            })

        payload = {
            "username": "Project Trishul",
            "embeds": [embed]
        }

        # Fire the webhook
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code == 204:
                logging.info("🟢 Discord alert successfully delivered!")
            else:
                logging.error(f"Failed to send Discord alert: HTTP {response.status_code}")
        except Exception as e:
            logging.error(f"Discord connection failed: {e}")
