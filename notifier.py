import requests
import json
import logging
import os

class ReconNotifier:
    def __init__(self, platform="discord"):
        self.platform = platform
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "") 

    def send_alert(self, message_list):
        if not self.webhook_url:
            logging.warning("No valid Discord webhook URL found. Skipping alert.")
            return

        # Combine the list into one giant block of text
        full_message = "\n".join(message_list)
        
        # Discord's strict limit is 2000 chars. We chunk it at 1900 to be safe.
        chunk_size = 1900
        chunks = [full_message[i:i + chunk_size] for i in range(0, len(full_message), chunk_size)]

        for chunk in chunks:
            payload = {
                "content": f"```\n{chunk}\n```"
            }
            try:
                response = requests.post(
                    self.webhook_url, 
                    data=json.dumps(payload), 
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code == 204:
                    logging.info("Discord chunk sent successfully.")
                else:
                    logging.error(f"Failed to send Discord alert: {response.status_code}")
            except Exception as e:
                logging.error(f"Discord Webhook Error: {e}")
