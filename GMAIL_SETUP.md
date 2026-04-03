# Gmail Setup Guide for Trishul Notifications

## Quick Setup (2 minutes):

### 1. Enable Gmail App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-factor authentication** if not already enabled
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate app password for "Mail"
5. Copy the **16-character password** (not your regular Gmail password!)

### 2. Set Environment Variables
```bash
export EMAIL_USER="your-email@gmail.com"
export EMAIL_PASSWORD="your-16-char-app-password"
export EMAIL_RECIPIENT="notifications@example.com"  # Optional (defaults to EMAIL_USER)
```

### 3. Test Configuration
```bash
cd /path/to/Bugbounty
python3 gmail_notifier.py
```

## Email Notifications You'll Receive:

🎯 **Target Found** - When bug bounty target is discovered
🚀 **Attack Started** - When Phase 1 begins  
✅ **Attack Complete** - With timer, vulnerability list, and PDF report
⚠️ **Attack Interrupted** - If Ctrl+C is pressed
🚨 **Phase Stuck Alert** - If any phase has no progress for 5+ minutes

## Security Notes:
- Use Gmail **App Password**, NOT your regular password
- App passwords are 16 characters like: `abcd efgh ijkl mnop`
- Keep credentials in `.env` file (already in `.gitignore`)
- Only works with Gmail accounts with 2FA enabled

## Troubleshooting:
- "Authentication failed" → Check you're using app password, not regular password
- "SMTP connection failed" → Check firewall/network settings
- "Gmail disabled" → Set EMAIL_USER and EMAIL_PASSWORD environment variables

That's it! The system will now send you comprehensive email notifications throughout the entire attack process.