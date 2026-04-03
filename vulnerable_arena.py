from flask import Flask, request, jsonify, make_response
import time
import logging

# Disable Flask's default noisy logging so we only see our WAF alerts
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# ==========================================
# 🛡️ THE MINI-WAF (Rate Limiter)
# ==========================================
ip_tracker = {}
WAF_LIMIT = 2  # Max requests allowed...
WAF_WINDOW = 5  # ...within 5 seconds

@app.before_request
def waf_firewall():
    ip = request.remote_addr
    current_time = time.time()

    # Initialize IP tracking
    if ip not in ip_tracker:
        ip_tracker[ip] = []

    # Clean old requests outside the 5-second window
    ip_tracker[ip] = [t for t in ip_tracker[ip] if current_time - t < WAF_WINDOW]

    # Add current request
    ip_tracker[ip].append(current_time)

    # 🚨 WAF TRIGGER 🚨
    # If Trishul attacks too fast, the WAF catches it and drops the connection!
    if len(ip_tracker[ip]) > WAF_LIMIT:
        print(f"🛑 [WAF] Intrusion detected from {ip}! Dropping packets...")
        # We force a 5-second sleep to simulate a dropped packet. 
        # This causes Nuclei to register a "Timeout Error", triggering your AI Agent!
        time.sleep(5) 
        return make_response("WAF BLOCK: Malicious Activity Detected", 429)

# ==========================================
# 🎯 THE VULNERABLE ENDPOINTS (Bait)
# ==========================================

@app.route('/')
def index():
    # Katana will scrape this HTML comment and find the hidden API
    return "<h1>Welcome to the Trishul Target Arena</h1>"

@app.route('/robots.txt')
def robots():
    # Katana will read this and automatically crawl these restricted areas
    return "User-agent: *\nDisallow: /admin-dashboard-v2\nDisallow: /.env\nDisallow: /.git/"

@app.route('/.env')
def fake_env():
    # Nuclei's "exposed-panels" / "takeovers" tags will flag this as CRITICAL
    return "DB_HOST=10.0.0.5\nDB_USER=admin\nDB_PASSWORD=trishul_master_key_123\nAWS_SECRET=AKIA-FAKE-KEY-999"

@app.route('/.git/config')
def fake_git():
    # Nuclei's "exposure" tag will flag this as a source code leak
    return "[core]\n\trepositoryformatversion = 0\n\tfilemode = true\n\tbare = false\n[remote \"origin\"]\n\turl = https://github.com/charusat/internal-portal-private.git"

@app.route('/api/v1/dev-config')
def dev_config():
    # A hidden JSON endpoint
    return jsonify({"debug_mode": True, "admin_bypass": "enabled"})

@app.route('/admin-dashboard-v2')
def admin_panel():
    return "<h1>Admin Control Panel</h1><p>Welcome, root. System is vulnerable.</p>"

if __name__ == '__main__':
    print("==================================================")
    print(" 🎯 TRISHUL ARENA TARGET SERVER ONLINE")
    print(" 🛡️  Mini-WAF: ACTIVE (Limit: 20 req / 5 sec)")
    print(" 🌐 Target URL: http://127.0.0.1:5000")
    print("==================================================\n")
    app.run(host='0.0.0.0', port=5000, threaded=True)
