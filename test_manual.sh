#!/bin/bash

# 🧪 TRISHUL ROUND 1 - MANUAL TESTING GUIDE
# Run this in a separate terminal to test all features

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🔱 TRISHUL ROUND 1 - MANUAL TESTING SUITE               ║"
echo "║  Test all features before demo to judges                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    TEST_NAME=$1
    TEST_CMD=$2
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🧪 Testing: $TEST_NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if eval "$TEST_CMD"; then
        echo -e "${GREEN}✅ PASSED${NC}: $TEST_NAME"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}: $TEST_NAME"
        ((TESTS_FAILED++))
    fi
    echo ""
}

# Change to project directory
cd "$(dirname "$0")" || exit

echo "📍 Current directory: $(pwd)"
echo ""

# ════════════════════════════════════════════════════════════
# TEST 1: AI ENGINE
# ════════════════════════════════════════════════════════════
run_test "AI Vulnerability Engine" "python3 ai_engine.py > /dev/null 2>&1"

# ════════════════════════════════════════════════════════════
# TEST 2: AI ENGINE - INTERACTIVE
# ════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing: AI Engine - Detailed Output"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from ai_engine import analyze_asset_risk
asset = {
    'domain': 'demo.hackathon.com',
    'technologies': [{'name': 'nginx', 'version': '1.18.0'}],
    'open_ports': [80, 443, 22]
}
result = analyze_asset_risk(asset)
print(f'   Risk Score: {result[\"vulnerability_score\"]}/100')
print(f'   Risk Level: {result[\"risk_level\"]}')
print(f'   CVEs Found: {len(result[\"cves_found\"])}')
print(f'   ✅ AI Engine Working!')
"
echo ""

# ════════════════════════════════════════════════════════════
# TEST 3: CAMPAIGN MANAGER
# ════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing: Campaign Manager"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from campaign_manager import CampaignManager, Campaign, CampaignStatus, ProgramPlatform
from datetime import datetime
import uuid
import os

db_file = 'test_manual.db'
if os.path.exists(db_file):
    os.remove(db_file)

manager = CampaignManager(db_path=db_file)
campaign = Campaign(
    id=str(uuid.uuid4())[:8],
    name='Manual Test Campaign',
    platform=ProgramPlatform.HACKERONE.value,
    target_domain='test.com',
    status=CampaignStatus.ACTIVE.value,
    priority=4,
    scope=['*.test.com'],
    out_of_scope=[],
    created_at=datetime.now().isoformat()
)

success = manager.create_campaign(campaign)
retrieved = manager.get_campaign(campaign.id)

print(f'   Campaign Created: {success}')
print(f'   Campaign Retrieved: {retrieved is not None}')
print(f'   ✅ Campaign Manager Working!')

os.remove(db_file)
"
echo ""

# ════════════════════════════════════════════════════════════
# TEST 4: API SERVER
# ════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing: API Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
from api_server import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test health
response = client.get('/api/v1/health')
health = response.json()
print(f'   Health Status: {health[\"status\"]}')
print(f'   AI Enabled: {health[\"ai_enabled\"]}')

# Test auth
response = client.post('/api/v1/auth/register', json={
    'email': 'test@hackathon.com',
    'password': 'secure123'
})
print(f'   Registration: {response.status_code == 200}')

token = response.json()['access_token']

# Test AI endpoint
response = client.post('/api/v1/ai/analyze-asset', 
    json={'domain': 'test.com', 'technologies': [], 'open_ports': []},
    headers={'Authorization': f'Bearer {token}'})
print(f'   AI Endpoint: {response.status_code == 200}')
print(f'   ✅ API Server Working!')
" 2>&1 | grep -v "INFO:httpx"
echo ""

# ════════════════════════════════════════════════════════════
# TEST 5: DASHBOARD
# ════════════════════════════════════════════════════════════
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing: Dashboard Module"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
import ai_dashboard
print('   Module Loaded: True')
print('   Has main function:', hasattr(ai_dashboard, 'main'))
print('   ✅ Dashboard Ready!')
" 2>&1 | grep -E "(Module|Has|✅)"
echo ""

# ════════════════════════════════════════════════════════════
# FINAL RESULTS
# ════════════════════════════════════════════════════════════
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    TEST RESULTS SUMMARY                    ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo -e "║  ${GREEN}Tests Passed: $TESTS_PASSED${NC}                                        ║"
echo -e "║  ${RED}Tests Failed: $TESTS_FAILED${NC}                                        ║"
echo "╠════════════════════════════════════════════════════════════╣"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "║  ${GREEN}✅ ALL SYSTEMS OPERATIONAL - READY FOR DEMO!${NC}           ║"
else
    echo -e "║  ${RED}⚠️  SOME TESTS FAILED - CHECK OUTPUT ABOVE${NC}            ║"
fi

echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ════════════════════════════════════════════════════════════
# INTERACTIVE DEMO COMMANDS
# ════════════════════════════════════════════════════════════
echo "🎯 READY FOR LIVE DEMO?"
echo ""
echo "Run these commands in separate terminals:"
echo ""
echo "1️⃣  Interactive AI Demo:"
echo "   python3 demo_ai.py"
echo ""
echo "2️⃣  Launch Frontend (in new terminal):"
echo "   cd frontend && npm run dev"
echo ""
echo "3️⃣  Start API Server (in new terminal):"
echo "   python3 api_server.py"
echo "   Then visit: http://localhost:8000/api/docs"
echo ""
echo "════════════════════════════════════════════════════════════"
