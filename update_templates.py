"""
CRONTAB INSTRUCTION:
To schedule this script to run every day at 2:00 AM system time, open your server's crontab using `crontab -e` and add the exact instruction below:

0 2 * * * /usr/bin/env python3 /path/to/your/workspace/Bugbounty/update_templates.py
"""

import subprocess
import logging
import os
from notifier import ReconNotifier

# Configure logging to append to a local maintenance.log file
logging.basicConfig(
    filename='maintenance.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def notify_failure():
    """
    Sends a critical alert to Discord/Telegram via ReconNotifier.
    """
    error_msg = "⚠️ PIPELINE ERROR: Nuclei template update failed. Manual intervention required."
    
    # We use a mock vulnerability payload to utilize existing alert structure
    vuln_payload = {
        "info": {
            "name": error_msg,
            "severity": "critical",
            "description": "The automated Nuclei template update script encountered an error."
        },
        "matched-at": "Automated Maintenance Module"
    }

    # Detect platform configuration and send alerts
    discord_url = os.getenv("DISCORD_WEBHOOK_URL")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if discord_url:
        notifier = ReconNotifier("discord")
        notifier.send_vulnerability_alert(vuln_payload)
    
    if telegram_token and telegram_chat_id:
        notifier = ReconNotifier("telegram")
        notifier.send_vulnerability_alert(vuln_payload)
        
    if not discord_url and not (telegram_token and telegram_chat_id):
        logging.warning("Alert triggered but neither DISCORD_WEBHOOK_URL nor TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID are set in environment.")

def main():
    try:
        logging.info("Starting Nuclei template update...")
        
        # Execute the update command and capture both stdout and stderr
        result = subprocess.run(
            ['nuclei', '-ut'],
            capture_output=True,
            text=True
        )

        stdout = result.stdout.lower()
        stderr = result.stderr.lower()

        # Check for non-zero exit code (implies crash, missing binary, or network drop)
        if result.returncode != 0:
            logging.error(f"Nuclei update failed (Exit code: {result.returncode}). Stderr: {result.stderr.strip()}")
            notify_failure()
            return

        # Parse the output string to determine if an update actually occurred
        # Nuclei sometimes outputs to stderr for logs and stdout for results
        combined_output = stdout + stderr

        if "already up to date" in combined_output or "already updated" in combined_output or "latest version" in combined_output or "already up-to-date" in combined_output:
            logging.info("No new updates. Nuclei templates are already at the latest version.")
        elif "successfully" in combined_output or "downloaded" in combined_output or "updated" in combined_output:
            logging.info("Updated successfully.")
        else:
            # Fallback if format is unexpected but exit code was 0
            logging.info(f"Update executed. Output: {result.stdout.strip() or result.stderr.strip()}")

    except FileNotFoundError:
        logging.error("Nuclei binary not found. Is it installed and in PATH?")
        notify_failure()
    except Exception as e:
        logging.error(f"Unexpected exception during Nuclei update: {e}")
        notify_failure()

if __name__ == "__main__":
    main()
