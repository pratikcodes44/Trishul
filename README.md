# Bugbounty

## Description

A modular Python-based automated bug bounty reconnaissance pipeline. It includes structured wrapper scripts for executing reconnaissance binaries (`subfinder`, `httpx`, `nuclei`), managing discovered assets using a SQLite database, checking organizational scopes, updating templates automatically, and sending vulnerability alerts to Discord or Telegram channels.

## How to Run

1. Ensure the required external reconnaissance binaries are installed and accessible in your system's PATH.
2. Setup environment variables (e.g. `DISCORD_WEBHOOK_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`) for notifications if using `notifier.py`.
3. Run the specific modules or pipeline scripts using Python, e.g.:

   ```bash
   python subfinder_runner.py
   python live_host_prober.py
   python nuclei_runner.py
   ```

## Dependencies

- **Python 3.x**
- **Python Packages**:
  - `requests` (for webhooks and HTTP calls)
- **External Binaries**:
  - `subfinder`
  - `httpx`
  - `nuclei`
