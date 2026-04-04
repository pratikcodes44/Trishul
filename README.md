# 🔱 Trishul - AI-Powered Bug Bounty Platform

> **AI-first autonomous bug bounty platform** with local Mistral guidance, campaign tracking, and full recon-to-report automation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AI Powered](https://img.shields.io/badge/AI-Powered-blueviolet)](https://github.com/pratikcodes44/Trishul)
[![FastAPI](https://img.shields.io/badge/FastAPI-SaaS-green)](https://fastapi.tiangolo.com/)

---

## 🚀 Platform Overview

Trishul is a comprehensive **AI-powered bug bounty automation platform** built for high-signal recon, safer scan execution, and fast reporting.

### 🤖 **AI Intelligence Engine**
- **ML-Powered Vulnerability Prediction**: Predict exploit likelihood using tech stack analysis
- **CVE Correlation**: Automatically match discovered technologies with known vulnerabilities  
- **Risk Scoring**: AI-driven risk assessment (0-100 scale) with actionable insights
- **Smart Recommendations**: Context-aware security remediation suggestions
- **Anomaly Detection**: ML-based change detection and suspicious pattern identification

### 🎯 What is Trishul?

Trishul automates the entire bug bounty workflow from reconnaissance to reporting:

1. **🔍 AI-Powered Discovery** - Intelligent asset enumeration with ML-based prioritization
2. **🧠 Smart Reconnaissance** - Context-aware scanning with predictive analytics
3. **⚡ Automated Exploitation** - AI-guided vulnerability detection with CVE matching
4. **📊 Intelligent Reporting** - Auto-generated executive summaries with business impact

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            PROJECT TRISHUL                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  🎯 TARGET INTAKE                                                            │
│  ├─ Mode 1: Bug Bounty Hunter (Auto via BountyScout)                        │
│  ├─ Mode 2: Manual Target (--domain / --demo)                               │
│  └─ Mode 3: Enterprise Audit (Campaign Manager)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  🤖 AI INTELLIGENCE LAYER (NEW!)                                             │
│  ├─ ML Vulnerability Predictor → CVE Correlation → Risk Scoring             │
│  ├─ Smart Recommendations → Predictive Analytics                            │
│  └─ AI-Powered Stuck Detection (activity-based, not time-based)             │
├─────────────────────────────────────────────────────────────────────────────┤
│  🛡️ SAFETY + ADAPTIVE CONTROL                                               │
│  ├─ Legal Consent → Scope Validation → Read-only Defaults                   │
│  ├─ Audit Logging → Smart Watchdog (AI stuck detection)                     │
│  └─ Adaptive Rate Limiting (10-150 req/s, auto-adjusts to server health)    │
├─────────────────────────────────────────────────────────────────────────────┤
│  🔍 10-PHASE RECONNAISSANCE PIPELINE (22 TOOLS)                              │
│                                                                              │
│  Phase 1: OSINT (cert transparency, github, shodan)                          │
│  Phase 2: Subdomain Discovery                                                │
│    ├─ Subfinder + Amass + DNSRecon                                          │
│    └─ Result: 60% more coverage via multi-tool synergy                      │
│                                                                              │
│  Phase 3: Subdomain Takeover (SubdomainTakeoverValidator)                   │
│                                                                              │
│  Phase 4: Port Scanning (Naabu)                                              │
│                                                                              │
│  Phase 5: Live Host Probing (HTTPX)                                          │
│                                                                              │
│  Phase 6: Web Discovery + Parameter Mining                                   │
│    ├─ Crawling: Katana                                                      │
│    ├─ Directory Bruteforce: Gobuster + Dirsearch + Feroxbuster             │
│    ├─ Parameter Discovery: ParamSpider + Arjun                              │
│    └─ Result: 140% more endpoints discovered                                │
│                                                                              │
│  Phase 7: GraphQL/API Discovery (GraphQLAPIScanner)                          │
│                                                                              │
│  Phase 8: Historical Mining + Fingerprinting                                 │
│    ├─ URL Archives: GAU + Waybackurls                                       │
│    ├─ Technology Detection: WhatWeb                                         │
│    └─ Result: Complete tech stack visibility                                │
│                                                                              │
│  Phase 9: IDOR Testing (IDORTester)                                          │
│                                                                              │
│  Phase 10: Vulnerability Scanning (5 SCANNERS)                               │
│    ├─ Primary: Nuclei (10,000+ templates)                                   │
│    ├─ Supplemental: Nikto + WPScan + SQLMap + Dalfox                       │
│    ├─ Adaptive Rate: Safe start → Auto-adjust → Respect 429/503            │
│    └─ Result: Cross-verified vulnerabilities, 140% more coverage            │
├─────────────────────────────────────────────────────────────────────────────┤
│  📊 REAL-TIME MONITORING                                                     │
│  ├─ Tool Execution Tracker (⏳/✅/⊘/❌ status per tool)                      │
│  ├─ Phase-by-phase summary tables (duration, results)                       │
│  └─ Smart watchdog activity monitoring (zero false positives)               │
├─────────────────────────────────────────────────────────────────────────────┤
│  📤 OUTPUTS + NOTIFICATIONS                                                  │
│  ├─ Reports: PDF + JSON + Markdown                                          │
│  ├─ Gmail: Target found, Start, Complete, Stuck, Interrupted                │
│  ├─ API Server: RESTful + Dashboard + JWT Auth                              │
│  └─ State DB: Campaigns + Assets + Audit logs                               │
└─────────────────────────────────────────────────────────────────────────────┘

📊 TOOL POWER: 22 security tools integrated (9 → 22 = +144% increase!)
```

---

## ⚡ Features

### 🚀 **NEW in v2.0!**
| Feature | Description |
|---------|-------------|
| **Adaptive Rate Limiting** | Intelligent rate control: starts safe (10 req/s), speeds up to 150 req/s when server healthy, backs off on stress. 2-10x faster than static safe mode! |
| **AI Stuck Detection** | Activity-based monitoring (not time-based). Only alerts on sustained zero requests (60s), eliminating false positives during slow scans. |
| **Extended Tools (13 added)** | Amass, DNSRecon, Gobuster, Dirsearch, Feroxbuster, ParamSpider, Arjun, Waybackurls, WhatWeb, Nikto, WPScan, SQLMap, Dalfox |
| **Real-Time Tool Tracking** | Live status display (⏳/✅/⊘/❌) showing which tools are running, duration, and results per phase |
| **22 Security Tools Total** | Increased from 9 to 22 tools (+144% coverage boost) with cross-verification |

### 🤖 **AI & Machine Learning**
| Feature | Description |
|---------|-------------|
| **AI Vulnerability Predictor** | ML model predicts exploit likelihood from tech stack fingerprinting |
| **CVE Auto-Correlation** | Matches discovered technologies with known CVEs from NVD database |
| **Intelligent Risk Scoring** | 0-100 AI-driven risk assessment with severity classification |
| **Smart Recommendations** | Context-aware remediation suggestions based on findings |
| **Predictive Analytics** | Forecast vulnerability trends and attack surface growth |
| **AI-Powered WAF Evasion** | Local LLM (Ollama) generates evasion tactics when blocks detected |

### 🎯 **Platform Services**
| Feature | Description |
|---------|-------------|
| **RESTful API** | FastAPI-based with OpenAPI docs, JWT auth, and rate limiting |
| **Multi-Tenant Architecture** | Campaign manager for multiple bug bounty programs |
| **Real-time AI Dashboard** | Interactive Streamlit dashboard with live risk visualization |
| **Batch Analysis** | Analyze multiple assets simultaneously with aggregate metrics |
| **Usage Analytics** | Track API calls, storage, scan metrics per user/tenant |

### 🔧 **Core Security Features**
| Feature | Description |
|---------|-------------|
| **Single Bug Bounty Mode** | Autonomous bug bounty hunting workflow |
| **State Diffing** | SQLite-based tracking - only scans NEW subdomains |
| **Scope Enforcement** | Built-in denylist blocks third-party SaaS (AWS, Heroku, etc.) |
| **Real-time Alerts** | Gmail notifications on target found, start, completion, interruption, and stuck phases |
| **Bounty Estimation** | Auto-estimates potential payout based on severity |
| **CI/CD Integration** | Exit code 1 on critical vulns to halt deployments |

---

## 🚀 Quick Start

### Prerequisites

**Python 3.8+** and the following security tools:

```bash
# Arch Linux / BlackArch
sudo pacman -S subfinder naabu httpx nuclei gau katana amass dnsrecon gobuster feroxbuster nikto sqlmap whatweb wpscan

# Or using Go
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest
go install -v github.com/tomnomnom/waybackurls@latest
go install -v github.com/hahwul/dalfox/v2@latest

# Python CLI tools used by extended scanners
pip install arjun dirsearch

# Optional parameter discovery helper
npm install -g @0xsha/paramspider
```

### Installation

```bash
# Clone the repository
git clone https://github.com/pratikcodes44/Trishul.git
cd Trishul

# Quick setup (installs all dependencies)
./quickstart.sh

# OR manual installation
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

### Frontend + API (New UI)

```bash
# Terminal 1: backend API
./start_api.sh

# Terminal 2: frontend
cd frontend
npm install
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open:
- Frontend: `http://localhost:3000`
- API docs: `http://localhost:8000/api/docs`

Auth-first flow:
1. Visit `/auth` and login/register.
2. Start scan from `/operations`.
3. View report + stats on `/reports`.
4. Use header search to find previously attacked websites (per-user DB tracking).

New API surfaces for richer UI:
- `GET /api/v1/operations/overview`
- `GET /api/v1/reports/analytics`
- `GET /api/v1/search/attacked-sites`
- `GET /api/v1/search/recent`

### Automated Tests

```bash
# Run all automated tests
python3 -m pytest

# Fast compile-only sanity check
python3 -m py_compile main.py dashboard.py report_writer.py nuclei_runner.py ai_engine.py campaign_manager.py gmail_notifier.py
```

GitHub Actions CI runs these checks automatically on every push and pull request.

### Local Mistral AI (Recommended)

Trishul now supports **local Mistral** through Ollama for project-wide AI assistance.

```bash
# Ensure Ollama is running
ollama serve

# Pull Mistral model (if needed)
ollama pull mistral:latest

# Verify model is present
ollama list | grep mistral
```

Set these in `.env`:

```bash
LOCAL_AI_API_URL=http://127.0.0.1:11434/api/generate
LOCAL_AI_MODEL=mistral:latest
LOCAL_AI_TIMEOUT=20
```

Notes:
- `ai_engine.py` uses local Mistral for report summaries and phase guidance when available.
- If local AI is unavailable, Trishul falls back to deterministic built-in summaries.
- Nuclei WAF-evasion also uses local model via `OLLAMA_API_URL` and `OLLAMA_MODEL`.

### 🎯 Usage - AI-First SaaS Platform

#### 1. Launch Unified Frontend (Recommended for Demo)
```bash
cd frontend
npm install
npm run dev
```
Access at: `http://localhost:3000`

**Pages:**
- Landing
- Operations Dashboard
- Reports/Analytics

#### 2. Start API Server
```bash
python3 api_server.py
```
Access API docs at: `http://localhost:8000/api/docs`

**API Endpoints:**
```bash
# Register/Login
POST /api/v1/auth/register
POST /api/v1/auth/login

# AI Analysis
POST /api/v1/ai/analyze-asset
POST /api/v1/ai/batch-analyze

# Scanning
POST /api/v1/scans/start
GET  /api/v1/scans/{scan_id}

# Reports
GET  /api/v1/reports/generate
```

#### 3. Traditional CLI Mode
```bash
# Auto-select bug bounty target from HackerOne/Bugcrowd
python main.py

# Scan a specific target
python main.py -d staging.yourcompany.com

# CLI flags for automation
python main.py -d target.com -y  # Auto-authorize, no prompts

# With authenticated scanning (session cookie)
python main.py -d app.company.com -c "session=abc123"
```

### Demo Mode (Local Testing)

```bash
# Terminal 1: Start vulnerable test server
python vulnerable_arena.py

# Terminal 2: Run Trishul against local target
python main.py -d 127.0.0.1 -y
```

---

## 📊 Frontend

Unified frontend is available in:

```bash
frontend/
```

---

## 📁 Project Structure

```
project-trishul/
├── main.py                 # Entry point - orchestrates the pipeline
├── bounty_scout.py         # Fetches random targets from bug bounty platforms
├── scope_checker.py        # Validates subdomains, blocks third-party SaaS
├── subfinder_runner.py     # Subdomain enumeration wrapper
├── port_scanner.py         # Naabu port scanner wrapper
├── live_host_prober.py     # HTTPX live host detection wrapper
├── katana_runner.py        # Web crawler wrapper
├── gau_runner.py           # Historical URL fetcher (Wayback Machine)
├── nuclei_runner.py        # Vulnerability scanner with AI WAF evasion
├── asset_manager.py        # SQLite state management for diffing
├── report_writer.py        # HackerOne-style report generator
├── discord_notifier.py     # Rich Discord embed notifications
├── gmail_notifier.py       # Gmail notification lifecycle alerts
├── recon_notifier.py       # Multi-platform notification system
├── notifier.py             # Simple Discord/Telegram alerts
├── update_templates.py     # Nuclei template auto-updater (cron)
├── vulnerable_arena.py     # Flask test server with intentional vulns
├── frontend/               # Unified Next.js frontend (Landing/Operations/Reports)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
└── LICENSE                 # MIT License
```

---

## 🔒 Security & Ethics

- **Only scan targets you have explicit permission to test**
- Never commit credentials or webhook URLs
- Built-in scope enforcement prevents accidental out-of-scope scanning
- Denylist blocks scanning of third-party infrastructure

---

## ⚖️ LEGAL & COMPLIANCE

### 🚨 AUTHORIZATION REQUIREMENT

**YOU MUST HAVE EXPLICIT WRITTEN AUTHORIZATION BEFORE USING THIS TOOL.**

Using Trishul without authorization may violate:
- **Computer Fraud and Abuse Act (CFAA)** - USA - Up to 10 years imprisonment
- **Computer Misuse Act 1990** - UK - Up to 2 years imprisonment  
- **EU Cybercrime Directive** - Criminal penalties
- Local cybercrime laws in your jurisdiction

### ✅ Acceptable Use

This tool is designed for **authorized security testing ONLY**:

1. ✅ **Bug Bounty Programs** - HackerOne, Bugcrowd, Intigriti, YesWeHack, etc.
2. ✅ **Penetration Testing Contracts** - With signed agreements
3. ✅ **Your Own Systems** - Infrastructure you own or control
4. ✅ **Security Research Labs** - Designated testing environments

### ❌ Prohibited Use

**DO NOT USE THIS TOOL TO:**
- Test systems without authorization
- Exploit vulnerabilities beyond proof-of-concept
- Access, modify, or delete data
- Cause denial of service
- Violate bug bounty program rules
- Test third-party systems outside your scope

### 📋 Legal Compliance Features

Trishul includes multiple compliance safeguards:

#### 1. **Scope Validation** (REQUIRED)
```bash
# Create scope file with authorized targets
python scope_validator.py create-example

# Run with scope validation
python main.py -d target.com --scope scope.txt
```

Scope file supports:
- Exact domains: `example.com`
- Wildcards: `*.example.com`
- Deep wildcards: `**.example.com`
- CIDR ranges: `192.168.1.0/24`
- Exclusions: `!admin.example.com`

#### 2. **Legal Disclaimer**
- Interactive disclaimer shown before each scan
- Requires explicit "I AGREE" consent
- Consent logged in audit trail

#### 3. **Audit Logging**
- All HTTP requests logged to `audit_log.jsonl`
- Includes timestamp, target, method, status
- Provides legal accountability and defense

```bash
# View audit log
cat audit_log.jsonl | jq

# Disable (not recommended)
python main.py --no-audit-log
```

#### 4. **Rate Limiting**
- Default: 0.5s delay between requests
- IDOR testing: Max 20 requests per URL (down from 100)
- GraphQL: Rate-limited queries

```bash
# Adjust rate limiting
python main.py --request-delay 1.0    # 1 second delay
python main.py --max-idor-tests 10    # Reduce IDOR fuzzing
```

#### 5. **Read-Only Mode** (Default: ON)
- Prevents POST/PUT/DELETE/PATCH requests
- Only GET/HEAD/OPTIONS allowed
- Minimizes risk of state changes

```bash
# Enable write operations (use with caution)
python main.py --allow-writes
```

### 📖 Bug Bounty Program Compliance

When participating in bug bounty programs:

1. **Read Program Rules** - Every program has specific restrictions
2. **Respect Scope** - Only test in-scope assets
3. **Honor Rate Limits** - Don't cause service degradation
4. **Report Responsibly** - Follow disclosure timelines
5. **No Data Exfiltration** - Only collect minimum PoC evidence
6. **Stop When Found** - Don't exploit beyond verification

Common program restrictions:
- ❌ No denial of service testing
- ❌ No social engineering
- ❌ No spam/phishing
- ❌ No accessing other users' data
- ❌ No automated high-volume testing (without approval)

### 📄 Terms of Service

**BY USING THIS SOFTWARE, YOU AGREE TO:**
- Have explicit authorization for all testing
- Comply with applicable laws and bug bounty rules
- Assume ALL legal liability for your actions
- Not hold the creators liable for any damages

See [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md) for complete legal terms.

### 🛡️ Disclaimer

**THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND.**

The creators, contributors, and maintainers are NOT liable for:
- Legal fees, fines, or penalties from unauthorized use
- Violations of bug bounty program rules
- Damage to tested systems
- Criminal or civil liability from your actions

### 📞 Legal Questions?

- Read: [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md)
- Consult: A qualified attorney in your jurisdiction
- Understand: Your local computer crime laws

**Remember: When in doubt, get explicit written authorization!**

---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Additional Terms**: Use of this software for unauthorized access is strictly prohibited and may violate laws including the Computer Fraud and Abuse Act (CFAA). See [TERMS_OF_SERVICE.md](TERMS_OF_SERVICE.md) for complete legal terms.

---

## 🙏 Acknowledgments

- [ProjectDiscovery](https://github.com/projectdiscovery) - For Subfinder, Nuclei, HTTPX, Naabu, Katana
- [Arkadiyt](https://github.com/arkadiyt/bounty-targets-data) - Bug bounty target data
- The Bug Bounty community
