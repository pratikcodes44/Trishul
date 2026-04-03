# 🔱 Trishul - AI-Powered Security Platform

> **Next-Generation AI-First SaaS** - Enterprise Attack Surface Management & Autonomous Bug Bounty Hunting Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![AI Powered](https://img.shields.io/badge/AI-Powered-blueviolet)](https://github.com/pratikcodes44/Trishul)
[![FastAPI](https://img.shields.io/badge/FastAPI-SaaS-green)](https://fastapi.tiangolo.com/)

---

## 🚀 **NEW: AI-First SaaS Platform**

Trishul has evolved into a comprehensive **AI-powered security intelligence platform** designed for the modern bug bounty hunter and enterprise security team. Built for the 48-hour hackathon, we've integrated cutting-edge AI/ML capabilities with enterprise-grade SaaS architecture.

### 🤖 **AI Intelligence Engine**
- **ML-Powered Vulnerability Prediction**: Predict exploit likelihood using tech stack analysis
- **CVE Correlation**: Automatically match discovered technologies with known vulnerabilities  
- **Risk Scoring**: AI-driven risk assessment (0-100 scale) with actionable insights
- **Smart Recommendations**: Context-aware security remediation suggestions
- **Anomaly Detection**: ML-based change detection and suspicious pattern identification

### 🎯 **What is Trishul?**

Trishul is an **enterprise-grade, AI-powered security platform** that automates the entire bug bounty workflow from reconnaissance to reporting. Named after the legendary trident of Lord Shiva, it now strikes with AI precision across multiple dimensions:

1. **🔍 AI-Powered Discovery** - Intelligent asset enumeration with ML-based prioritization
2. **🧠 Smart Reconnaissance** - Context-aware scanning with predictive analytics
3. **⚡ Automated Exploitation** - AI-guided vulnerability detection with CVE matching
4. **📊 Intelligent Reporting** - Auto-generated executive summaries with business impact

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PROJECT TRISHUL                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐               │
│  │  Mode 1:     │    │  Mode 2:     │    │  Target      │               │
│  │  Enterprise  │    │  Bug Bounty  │    │  Acquisition │               │
│  │  Auditor     │    │  Hunter      │    │  (Manual)    │               │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘               │
│         │                   │                    │                       │
│         └───────────────────┼────────────────────┘                       │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 🤖 AI INTELLIGENCE LAYER (NEW!)                 │    │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌────────────────┐   │    │
│  │  │   ML    │  │   CVE   │  │   Risk   │  │   Predictive   │   │    │
│  │  │ Vuln    │→ │Correlat-│→ │ Scoring  │→ │   Analytics    │   │    │
│  │  │Predictor│  │  ion    │  │  Engine  │  │                │   │    │
│  │  └─────────┘  └─────────┘  └──────────┘  └────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    RECONNAISSANCE PIPELINE                       │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐ │    │
│  │  │Subfinder│→ │  Naabu  │→ │  HTTPX  │→ │ Katana  │→ │  GAU   │ │    │
│  │  │(Subs)   │  │(Ports)  │  │(Probe)  │  │(Crawl)  │  │(Hist.) │ │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                     STATE MANAGEMENT                             │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │    │
│  │  │ ScopeChecker │  │ AssetManager │  │ SQLite State DB      │   │    │
│  │  │ (Denylist)   │  │ (Diff Engine)│  │ (New vs Existing)    │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    VULNERABILITY SCANNER                         │    │
│  │  ┌──────────────────────────────────────────────────────────┐   │    │
│  │  │                      NUCLEI                               │   │    │
│  │  │  ┌─────────────┐    ┌─────────────────────────────────┐  │   │    │
│  │  │  │ Fast Scan   │ →  │ WAF Detected? → AI Evasion Mode │  │   │    │
│  │  │  │ (Aggressive)│    │ (Ollama LLM generates flags)    │  │   │    │
│  │  │  └─────────────┘    └─────────────────────────────────┘  │   │    │
│  │  └──────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                       OUTPUT LAYER                               │    │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │    │
│  │  │  Discord   │  │   Jira     │  │ HackerOne  │  │ AI Dash   │  │    │
│  │  │  Alerts    │  │  Tickets   │  │  Reports   │  │ + API     │  │    │
│  │  │            │  │  (Mode 1)  │  │  (Mode 2)  │  │ (SaaS)    │  │    │
│  │  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Features

### 🤖 **AI & Machine Learning** (NEW!)
| Feature | Description |
|---------|-------------|
| **AI Vulnerability Predictor** | ML model predicts exploit likelihood from tech stack fingerprinting |
| **CVE Auto-Correlation** | Matches discovered technologies with known CVEs from NVD database |
| **Intelligent Risk Scoring** | 0-100 AI-driven risk assessment with severity classification |
| **Smart Recommendations** | Context-aware remediation suggestions based on findings |
| **Predictive Analytics** | Forecast vulnerability trends and attack surface growth |

### 🎯 **Enterprise SaaS Platform** (NEW!)
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
| **Dual Mode Operation** | Enterprise security auditor OR autonomous bug bounty hunter |
| **AI-Powered WAF Evasion** | Local LLM (Ollama) generates evasion tactics when WAF blocks detected |
| **State Diffing** | SQLite-based tracking - only scans NEW subdomains |
| **Scope Enforcement** | Built-in denylist blocks third-party SaaS (AWS, Heroku, etc.) |
| **Compliance Mapping** | Enterprise mode maps vulnerabilities to SOC2/ISO-27001 controls |
| **Real-time Alerts** | Discord/Telegram notifications on vulnerability discovery |
| **Bounty Estimation** | Auto-estimates potential payout based on severity |
| **CI/CD Integration** | Exit code 1 on critical vulns to halt deployments |

---

## 🚀 Quick Start

### Prerequisites

**Python 3.8+** and the following security tools:

```bash
# Arch Linux / BlackArch
sudo pacman -S subfinder naabu httpx nuclei gau katana

# Or using Go
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest
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

### 🎯 Usage - AI-First SaaS Platform

#### 1. Launch AI Dashboard (Recommended for Demo)
```bash
streamlit run ai_dashboard.py
```
Access at: `http://localhost:8501`

**Features:**
- 🤖 Real-time AI vulnerability analysis
- 📊 Interactive risk visualization  
- 🎯 Predictive analytics dashboard
- 🔴 Critical security alerts

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
# Mode 2: Autonomous Bug Bounty Hunter (random target from HackerOne/Bugcrowd)
python main.py

# Mode 1: Enterprise Security Audit (specific target)
python main.py -d staging.yourcompany.com -m 1

# CLI flags for automation
python main.py -d target.com -m 2 -y  # Auto-authorize, no prompts

# With authenticated scanning (session cookie)
python main.py -d app.company.com -m 1 -c "session=abc123"
```

### Demo Mode (Local Testing)

```bash
# Terminal 1: Start vulnerable test server
python vulnerable_arena.py

# Terminal 2: Run Trishul against local target
python main.py -d 127.0.0.1 -m 1 -y
```

---

## 📊 Dashboard

Launch the cyberpunk-themed command center:

```bash
streamlit run dashboard.py
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
├── ticket_writer.py        # Jira-style ticket generator
├── discord_notifier.py     # Rich Discord embed notifications
├── recon_notifier.py       # Multi-platform notification system
├── notifier.py             # Simple Discord/Telegram alerts
├── update_templates.py     # Nuclei template auto-updater (cron)
├── vulnerable_arena.py     # Flask test server with intentional vulns
├── dashboard.py            # Streamlit monitoring dashboard
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
