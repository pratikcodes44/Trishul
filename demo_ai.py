#!/usr/bin/env python3
"""
Trishul AI Demo - Quick demonstration of AI capabilities
=========================================================
Run this to quickly showcase AI features for the hackathon.
"""

import json
from ai_engine import analyze_asset_risk, batch_analyze_assets
from campaign_manager import Campaign, CampaignManager, CampaignStatus, ProgramPlatform
from datetime import datetime
import uuid

def print_banner():
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║   🔱 TRISHUL AI SECURITY PLATFORM - DEMO SHOWCASE       ║
    ║   🤖 AI-Powered Vulnerability Intelligence              ║
    ╚══════════════════════════════════════════════════════════╝
    """)

def demo_ai_analysis():
    print("\n" + "="*60)
    print("🤖 DEMO 1: AI Vulnerability Analysis")
    print("="*60 + "\n")
    
    # Sample asset with known vulnerabilities
    asset = {
        'domain': 'api.example.com',
        'technologies': [
            {'name': 'nginx', 'version': '1.18.0'},
            {'name': 'wordpress', 'version': '5.7'},
            {'name': 'jenkins', 'version': '2.303'}
        ],
        'open_ports': [80, 443, 22, 3306, 6379]
    }
    
    print(f"📌 Analyzing: {asset['domain']}")
    print(f"📦 Technologies: {len(asset['technologies'])} detected")
    print(f"🔓 Open Ports: {len(asset['open_ports'])}")
    print("\n⏳ Running AI analysis...")
    
    # Perform AI analysis
    result = analyze_asset_risk(asset)
    
    print(f"\n{'='*60}")
    print("🎯 AI ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"🎲 Vulnerability Score: {result['vulnerability_score']}/100")
    print(f"📊 Risk Level: {result['risk_level']}")
    print(f"⚡ Exploit Likelihood: {result['exploit_likelihood']}")
    
    if result['cves_found']:
        print(f"\n🔴 CVEs Detected:")
        for cve in result['cves_found']:
            print(f"   • {cve}")
    
    print(f"\n🧠 AI Summary:")
    print(f"   {result['ai_analysis']}")
    
    print(f"\n📋 Security Issues Found:")
    for i, reason in enumerate(result['reasons'], 1):
        print(f"   {i}. {reason}")
    
    print(f"\n💡 AI Recommendations:")
    for i, rec in enumerate(result['recommendations'][:3], 1):
        print(f"   {i}. {rec}")
    
    return result

def demo_batch_analysis():
    print("\n" + "="*60)
    print("🤖 DEMO 2: Batch AI Analysis (Multiple Assets)")
    print("="*60 + "\n")
    
    assets = [
        {
            'domain': 'api.acme.com',
            'technologies': [{'name': 'nginx', 'version': '1.18.0'}],
            'open_ports': [80, 443, 22, 3306]
        },
        {
            'domain': 'admin.acme.com',
            'technologies': [{'name': 'apache', 'version': '2.4.48'}],
            'open_ports': [80, 443, 3389]
        },
        {
            'domain': 'dev.acme.com',
            'technologies': [{'name': 'jenkins', 'version': '2.303'}],
            'open_ports': [8080, 22]
        },
        {
            'domain': 'mail.acme.com',
            'technologies': [],
            'open_ports': [80, 443]
        }
    ]
    
    print(f"📊 Analyzing {len(assets)} assets simultaneously...")
    print("⏳ AI processing...\n")
    
    batch_result = batch_analyze_assets(assets)
    
    print(f"{'='*60}")
    print("📈 BATCH ANALYSIS SUMMARY")
    print(f"{'='*60}")
    print(f"Total Assets: {batch_result['total_assets']}")
    print(f"Average Risk Score: {batch_result['average_risk_score']}/100")
    print(f"🔴 Critical Risk Assets: {batch_result['critical_assets']}")
    print(f"🟠 High Risk Assets: {batch_result['high_risk_assets']}")
    
    print(f"\n📊 Detailed Results:")
    print(f"{'='*60}")
    
    for result in batch_result['detailed_results']:
        asset_name = result['asset']
        analysis = result['analysis']
        
        risk_icon = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(analysis['risk_level'], '⚪')
        
        print(f"\n{risk_icon} {asset_name}")
        print(f"   Score: {analysis['vulnerability_score']}/100 | Risk: {analysis['risk_level']}")
        print(f"   Issues: {len(analysis['reasons'])}")

def demo_campaign_manager():
    print("\n" + "="*60)
    print("🎯 DEMO 3: Multi-Campaign Management")
    print("="*60 + "\n")
    
    import os
    # Use temp file-based DB for demo
    db_file = 'demo_campaigns.db'
    if os.path.exists(db_file):
        os.remove(db_file)
    
    manager = CampaignManager(db_path=db_file)  # File-based DB for demo
    
    # Create sample campaigns
    campaigns_data = [
        {
            'name': 'Acme Corp Bug Bounty',
            'platform': ProgramPlatform.HACKERONE.value,
            'target': 'acme.com',
            'priority': 5,
            'vulnerabilities': 12,
            'critical': 3
        },
        {
            'name': 'TechStart Security Program',
            'platform': ProgramPlatform.BUGCROWD.value,
            'target': 'techstart.io',
            'priority': 4,
            'vulnerabilities': 8,
            'critical': 1
        },
        {
            'name': 'FinanceApp Private Program',
            'platform': ProgramPlatform.INTIGRITI.value,
            'target': 'financeapp.com',
            'priority': 3,
            'vulnerabilities': 5,
            'critical': 0
        }
    ]
    
    print("📝 Creating campaigns...\n")
    
    for data in campaigns_data:
        campaign = Campaign(
            id=str(uuid.uuid4())[:8],
            name=data['name'],
            platform=data['platform'],
            target_domain=data['target'],
            status=CampaignStatus.ACTIVE.value,
            priority=data['priority'],
            scope=[f"*.{data['target']}", data['target']],
            out_of_scope=[],
            created_at=datetime.now().isoformat(),
            vulnerabilities_found=data['vulnerabilities'],
            critical_count=data['critical'],
            bounty_earned=data['critical'] * 500 + (data['vulnerabilities'] - data['critical']) * 100
        )
        
        # Calculate AI priority
        campaign.ai_priority_score = manager.calculate_ai_priority(campaign)
        manager.create_campaign(campaign)
        
        print(f"✅ {data['name']}")
        print(f"   Platform: {data['platform']} | Target: {data['target']}")
        print(f"   AI Priority Score: {campaign.ai_priority_score:.1f}/100")
        print(f"   Findings: {data['vulnerabilities']} ({data['critical']} critical)")
        print(f"   Estimated Bounty: ${campaign.bounty_earned:.2f}\n")
    
    # Get dashboard stats
    stats = manager.get_dashboard_stats()
    
    print(f"{'='*60}")
    print("📊 CAMPAIGN DASHBOARD")
    print(f"{'='*60}")
    print(f"Active Campaigns: {stats['active_campaigns']}")
    print(f"Total Vulnerabilities: {stats['total_vulnerabilities']}")
    print(f"Critical Issues: {stats['critical_vulnerabilities']}")
    print(f"Total Bounty Earned: ${stats['total_bounty_earned']:.2f}")
    print(f"Top Priority: {stats['top_priority_campaign']} ({stats['top_priority_score']:.1f}/100)")
    
    # Cleanup
    if os.path.exists(db_file):
        os.remove(db_file)

def main():
    print_banner()
    
    print("🎬 Welcome to the Trishul AI Demo!")
    print("This demonstration showcases the AI-powered capabilities\n")
    
    input("Press ENTER to start Demo 1: AI Vulnerability Analysis...")
    demo_ai_analysis()
    
    input("\n\nPress ENTER to continue to Demo 2: Batch Analysis...")
    demo_batch_analysis()
    
    input("\n\nPress ENTER to continue to Demo 3: Campaign Management...")
    demo_campaign_manager()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETE!")
    print("="*60)
    print("""
🚀 Next Steps:
    
1. Launch AI Dashboard:
   streamlit run ai_dashboard.py
   
2. Start API Server:
   python3 api_server.py
   Visit: http://localhost:8000/api/docs
   
3. Run Full Scan:
   python3 main.py -d example.com

🔱 Trishul - AI-Powered Security Platform
    """)

if __name__ == "__main__":
    main()
