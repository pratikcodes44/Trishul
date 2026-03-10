import os
import time
import logging
import requests
from typing import List

logger = logging.getLogger(__name__)

class ReconNotifier:
    """
    ReconNotifier formats and sends lists of discovered in-scope 
    subdomains to a configured messaging platform (Discord or Telegram).
    """

    def __init__(self, platform: str):
        """
        Initializes the ReconNotifier.
        
        :param platform: 'discord' or 'telegram'
        """
        self.platform = platform.lower()
        if self.platform not in ["discord", "telegram"]:
            raise ValueError("Platform must be 'discord' or 'telegram'.")
            
        # Safely load configuration from environment variables
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Early warnings if environment variables are missing
        if self.platform == "discord" and not self.discord_webhook_url:
            logger.warning("DISCORD_WEBHOOK_URL environment variable is not set.")
        elif self.platform == "telegram" and not (self.telegram_bot_token and self.telegram_chat_id):
            logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables are not set.")

    def send_alert(self, new_discoveries: List[str]):
        """
        Takes a list of newly discovered subdomains and sends them in chunks 
        to the pre-configured messaging platform.
        """
        if not new_discoveries:
            logger.info("No new discoveries to report.")
            return

        # Batch alerts to handle cases with hundreds of discoveries without breaking platform limits
        chunk_size = 20
        chunks = [new_discoveries[i:i + chunk_size] for i in range(0, len(new_discoveries), chunk_size)]
        
        logger.info(f"Sending {len(new_discoveries)} discoveries in {len(chunks)} chunks via {self.platform.capitalize()}.")

        for index, chunk in enumerate(chunks):
            if self.platform == "discord":
                self._send_discord(chunk)
            elif self.platform == "telegram":
                self._send_telegram(chunk)

            # Throttle between chunks to avoid rate-limiting bans (429 Too Many Requests)
            if index < len(chunks) - 1:
                logger.debug("Sleeping for 2 seconds to avoid rate limiting...")
                time.sleep(2)

    def _send_discord(self, subdomains: List[str]):
        """Internal format and send to Discord Webhook."""
        if not self.discord_webhook_url:
            logger.error("Cannot send Discord alert: DISCORD_WEBHOOK_URL is missing.")
            return

        # Formatting with Discord Markdown
        lines = ["🚨 **New Subdomains Discovered!** 🚨", ""]
        for domain in subdomains:
            lines.append(f"• **{domain}**")
            
        payload = {"content": "\n".join(lines)}
        
        try:
            response = requests.post(self.discord_webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully sent Discord chunk of {len(subdomains)} domains.")
        except requests.exceptions.RequestException as e:
            status_code = getattr(getattr(e, 'response', None), 'status_code', 'Unknown')
            logger.error(f"Failed to send Discord alert chunk (HTTP {status_code}): {e}")

    def _send_telegram(self, subdomains: List[str]):
        """Internal format and send to Telegram Bot API."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.error("Cannot send Telegram alert: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
            return

        # Formatting using Telegram Markdown legacy parser. 
        # Note: Escaping underscores is necessary because legacy Markdown breaks if unescaped underscores exist.
        lines = ["🚨 *New Subdomains Discovered!* 🚨", ""]
        for domain in subdomains:
            # Escape underscore to prevent parsing errors
            safe_domain = domain.replace("_", "\\_")
            lines.append(f"• *{safe_domain}*")
            
        message = "\n".join(lines)
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"  # Standard Markdown syntax
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully sent Telegram chunk of {len(subdomains)} domains.")
        except requests.exceptions.RequestException as e:
            status_code = getattr(getattr(e, 'response', None), 'status_code', 'Unknown')
            logger.error(f"Failed to send Telegram alert chunk (HTTP {status_code}): {e}")

    def send_vulnerability_alert(self, vuln_data: dict):
        """
        Parses Nuclei vulnerability data and sends an alert if severity is sufficient.
        """
        if not isinstance(vuln_data, dict):
            logger.error("Expected vuln_data to be a dictionary.")
            return

        # Fault-Tolerant Parsing: safe fallbacks for every single key extraction
        info = vuln_data.get("info", {})
        name = info.get("name", "Unknown Vulnerability")
        severity = info.get("severity", "info").lower()
        matched_at = vuln_data.get("matched-at", "Unknown URL")
        
        description = info.get("description", "No description provided.")
        extracted_results = vuln_data.get("extracted-results", [])

        # Strict severity filtering
        allowed_severities = ["medium", "high", "critical"]
        if severity not in allowed_severities:
            logger.info(f"Silently logging {severity} finding to the database without triggering a phone notification: {name}")
            return

        if self.platform == "discord":
            self._send_discord_vuln(name, matched_at, severity)
        elif self.platform == "telegram":
            self._send_telegram_vuln(name, matched_at, severity)

    def _send_discord_vuln(self, name: str, matched_at: str, severity: str):
        """Internal format and send vulnerability to Discord Webhook using Embeds."""
        if not self.discord_webhook_url:
            logger.error("Cannot send Discord alert: DISCORD_WEBHOOK_URL is missing.")
            return

        color_map = {
            "critical": 16711680,  # Red
            "high": 16753920,      # Orange
            "medium": 16776960     # Yellow
        }
        color = color_map.get(severity, 16777215)  # Default white/unknown color

        payload = {
            "embeds": [
                {
                    "title": name,
                    "description": matched_at,
                    "color": color
                }
            ]
        }

        try:
            response = requests.post(self.discord_webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully sent Discord vulnerability embed for: {name}")
        except requests.exceptions.RequestException as e:
            status_code = getattr(getattr(e, 'response', None), 'status_code', 'Unknown')
            logger.error(f"Failed to send Discord vulnerability embed (HTTP {status_code}): {e}")

    def _send_telegram_vuln(self, name: str, matched_at: str, severity: str):
        """Internal format and send vulnerability to Telegram Bot API."""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.error("Cannot send Telegram alert: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
            return

        safe_name = name.replace("_", "\\_")
        safe_url = matched_at.replace("_", "\\_")
        
        lines = [
            "🚨 *Vulnerability Discovered!* 🚨",
            "",
            f"• *Name:* {safe_name}",
            f"• *Severity:* {severity.capitalize()}",
            f"• *URL:* {safe_url}"
        ]
        
        message = "\n".join(lines)
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"Successfully sent Telegram vulnerability alert for: {name}")
        except requests.exceptions.RequestException as e:
            status_code = getattr(getattr(e, 'response', None), 'status_code', 'Unknown')
            logger.error(f"Failed to send Telegram vulnerability alert (HTTP {status_code}): {e}")

