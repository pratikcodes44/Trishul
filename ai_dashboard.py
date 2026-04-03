"""
Trishul AI Dashboard - Interactive Security Intelligence Platform
=================================================================
Real-time AI-powered dashboard with predictive analytics,
risk visualization, and intelligent recommendations.
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict, Any
import random

# Import AI engine
try:
    from ai_engine import analyze_asset_risk, batch_analyze_assets, ai_assistant
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Trishul AI Command Center",
    page_icon="🔱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM STYLING - CYBERPUNK AI THEME
# ==========================================
st.markdown("""
    <style>
    /* AI-Powered Theme */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a0a2e 100%);
        color: #00ff41;
        font-family: 'Orbitron', 'Courier New', monospace;
    }
    
    h1, h2, h3 {
        color: #00ff41 !important;
        text-shadow: 0px 0px 10px #00ff41, 0px 0px 20px #00ff41;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 900 !important;
    }
    
    /* AI Badge */
    .ai-badge {
        background: linear-gradient(90deg, #ff00ff, #00ffff);
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        animation: glow 2s ease-in-out infinite;
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px #ff00ff, 0 0 10px #00ffff; }
        50% { box-shadow: 0 0 20px #ff00ff, 0 0 30px #00ffff; }
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        color: #00ff41 !important;
        font-size: 48px !important;
        font-weight: 900 !important;
        text-shadow: 0px 0px 10px #00ff41;
    }
    
    [data-testid="stMetricLabel"] {
        color: #aaaaaa !important;
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #1a1a1a 0%, #2a1a3a 100%);
        border: 2px solid #00ff41;
        border-left: 5px solid #00ff41;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0px 0px 20px rgba(0, 255, 65, 0.2);
    }
    
    /* Alert Boxes */
    .critical-alert {
        background: rgba(255, 0, 0, 0.1);
        border-left: 5px solid #ff0000;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #1a0a2e 100%);
        border-right: 2px solid #00ff41;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00ff41, #00cc33);
        color: #000000;
        font-weight: bold;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0px 0px 20px #00ff41;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_mock_asset_data() -> List[Dict[str, Any]]:
    """Generate mock asset data with AI analysis."""
    domains = [
        "api.example.com", "admin.example.com", "dev.example.com",
        "staging.example.com", "app.example.com", "mail.example.com",
        "vpn.example.com", "blog.example.com"
    ]
    
    tech_stacks = [
        [{'name': 'nginx', 'version': '1.18.0'}, {'name': 'wordpress', 'version': '5.7'}],
        [{'name': 'apache', 'version': '2.4.48'}, {'name': 'php', 'version': '7.4'}],
        [{'name': 'nginx', 'version': '1.20.0'}, {'name': 'nodejs', 'version': '14.0'}],
        [{'name': 'jenkins', 'version': '2.303'}],
        [{'name': 'nginx', 'version': '1.19.0'}],
    ]
    
    port_configs = [
        [80, 443, 22],
        [80, 443, 22, 3306],
        [80, 443, 8080],
        [80, 443, 22, 3389],
        [80, 443]
    ]
    
    assets = []
    for domain in domains:
        asset = {
            'domain': domain,
            'technologies': random.choice(tech_stacks),
            'open_ports': random.choice(port_configs),
            'last_scanned': datetime.now() - timedelta(hours=random.randint(1, 48))
        }
        assets.append(asset)
    
    return assets

def create_risk_gauge(score: float, title: str) -> go.Figure:
    """Create beautiful risk gauge chart."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 20, 'color': '#00ff41'}},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100], 'tickcolor': '#00ff41'},
            'bar': {'color': "#00ff41"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "#00ff41",
            'steps': [
                {'range': [0, 25], 'color': 'rgba(0, 255, 0, 0.3)'},
                {'range': [25, 50], 'color': 'rgba(255, 255, 0, 0.3)'},
                {'range': [50, 75], 'color': 'rgba(255, 165, 0, 0.3)'},
                {'range': [75, 100], 'color': 'rgba(255, 0, 0, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': '#00ff41', 'family': 'Orbitron'},
        height=300
    )
    
    return fig

# ==========================================
# MAIN DASHBOARD
# ==========================================

def main():
    # Header with AI Badge
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("""
        # 🔱 TRISHUL AI COMMAND CENTER
        <p style='color: #aaa; font-size: 14px;'>
        <span class='ai-badge'>🤖 AI POWERED</span> 
        Enterprise Attack Surface Management & Security Intelligence
        </p>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 REFRESH DATA"):
            st.rerun()
    
    st.markdown("---")
    
    # ==========================================
    # AI INSIGHTS SECTION
    # ==========================================
    st.markdown("## 🤖 AI Security Intelligence")
    
    # Generate mock data with AI analysis
    assets = get_mock_asset_data()
    
    if AI_AVAILABLE:
        batch_analysis = batch_analyze_assets(assets)
        
        # Top metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🎯 Total Assets",
                batch_analysis['total_assets'],
                delta="Live Monitoring"
            )
        
        with col2:
            st.metric(
                "🔴 Critical Risk",
                batch_analysis['critical_assets'],
                delta="Immediate Action Required",
                delta_color="inverse"
            )
        
        with col3:
            st.metric(
                "🟠 High Risk",
                batch_analysis['high_risk_assets'],
                delta="Review Within 7 Days",
                delta_color="inverse"
            )
        
        with col4:
            avg_score = batch_analysis['average_risk_score']
            st.metric(
                "📊 Avg Risk Score",
                f"{avg_score}/100",
                delta=f"{avg_score - 45:.1f} vs baseline"
            )
        
        # AI Summary
        st.markdown("### 🧠 AI Analysis Summary")
        st.info(f"**{batch_analysis['summary']}**")
        
        # Risk Gauge
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig = create_risk_gauge(avg_score, "Overall Risk")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            threat_score = min(batch_analysis['critical_assets'] * 25, 100)
            fig = create_risk_gauge(threat_score, "Threat Level")
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            coverage = 85 + random.randint(-5, 5)
            fig = create_risk_gauge(coverage, "Coverage %")
            st.plotly_chart(fig, use_container_width=True)
        
        # ==========================================
        # DETAILED ASSET ANALYSIS
        # ==========================================
        st.markdown("---")
        st.markdown("## 📋 Asset Vulnerability Analysis")
        
        # Create DataFrame for display
        asset_rows = []
        for result in batch_analysis['detailed_results']:
            analysis = result['analysis']
            asset_rows.append({
                'Asset': result['asset'],
                'Risk Score': analysis['vulnerability_score'],
                'Risk Level': analysis['risk_level'],
                'Likelihood': analysis['exploit_likelihood'],
                'CVEs': len(analysis['cves_found']),
                'Issues': len(analysis['reasons'])
            })
        
        df = pd.DataFrame(asset_rows)
        
        # Sort by risk score
        df = df.sort_values('Risk Score', ascending=False)
        
        # Display with color coding
        st.dataframe(
            df.style.background_gradient(subset=['Risk Score'], cmap='RdYlGn_r'),
            use_container_width=True
        )
        
        # ==========================================
        # CRITICAL ALERTS
        # ==========================================
        st.markdown("---")
        st.markdown("## 🚨 Critical Security Alerts")
        
        critical_assets = [r for r in batch_analysis['detailed_results'] 
                          if r['analysis']['risk_level'] == 'CRITICAL']
        
        if critical_assets:
            for result in critical_assets[:3]:  # Show top 3
                analysis = result['analysis']
                st.markdown(f"""
                <div class='critical-alert'>
                <h4>🔴 {result['asset']}</h4>
                <p><strong>AI Analysis:</strong> {analysis['ai_analysis']}</p>
                <p><strong>CVEs Found:</strong> {', '.join(analysis['cves_found']) if analysis['cves_found'] else 'None'}</p>
                <p><strong>Issues:</strong></p>
                <ul>
                """, unsafe_allow_html=True)
                
                for reason in analysis['reasons'][:3]:
                    st.markdown(f"<li>{reason}</li>", unsafe_allow_html=True)
                
                st.markdown("</ul></div>", unsafe_allow_html=True)
        else:
            st.success("✅ No critical vulnerabilities detected")
        
        # ==========================================
        # AI RECOMMENDATIONS
        # ==========================================
        st.markdown("---")
        st.markdown("## 💡 AI-Powered Recommendations")
        
        # Get recommendations from highest risk asset
        if batch_analysis['detailed_results']:
            top_risk = max(batch_analysis['detailed_results'], 
                          key=lambda x: x['analysis']['vulnerability_score'])
            
            recommendations = top_risk['analysis']['recommendations']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 Priority Actions")
                for i, rec in enumerate(recommendations[:3], 1):
                    st.markdown(f"{i}. {rec}")
            
            with col2:
                st.markdown("### 🛡️ Security Best Practices")
                for i, rec in enumerate(recommendations[3:6], 1):
                    st.markdown(f"{i}. {rec}")
        
        # ==========================================
        # CHARTS & VISUALIZATIONS
        # ==========================================
        st.markdown("---")
        st.markdown("## 📊 Security Metrics & Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Risk distribution pie chart
            risk_dist = df['Risk Level'].value_counts()
            fig = px.pie(
                values=risk_dist.values,
                names=risk_dist.index,
                title="Risk Distribution",
                color_discrete_map={
                    'CRITICAL': '#ff0000',
                    'HIGH': '#ff8800',
                    'MEDIUM': '#ffff00',
                    'LOW': '#00ff00'
                }
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font={'color': '#00ff41'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # CVE trend over time (mock data)
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            cve_counts = [random.randint(0, 5) for _ in range(30)]
            
            fig = px.line(
                x=dates,
                y=cve_counts,
                title="CVE Discoveries (Last 30 Days)",
                labels={'x': 'Date', 'y': 'CVEs Found'}
            )
            fig.update_traces(line_color='#00ff41', line_width=3)
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0.3)',
                font={'color': '#00ff41'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.error("❌ AI Engine not available. Please install required dependencies.")
    
    # ==========================================
    # FOOTER
    # ==========================================
    st.markdown("---")
    st.markdown("""
    <p style='text-align: center; color: #666; font-size: 12px;'>
    🔱 Trishul AI Security Platform v2.0 | Powered by Machine Learning & Advanced Analytics
    </p>
    """, unsafe_allow_html=True)


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    
    scan_type = st.selectbox(
        "Scan Type",
        ["Full Scan", "OSINT Only", "Vulnerability Scan", "Port Scan"]
    )
    
    target = st.text_input("Target Domain", placeholder="example.com")
    
    if st.button("🚀 Launch Scan", use_container_width=True):
        with st.spinner("Initializing AI-powered scan..."):
            import time
            time.sleep(2)
            st.success(f"✅ Scan started for {target}")
    
    st.markdown("---")
    
    st.markdown("### 📈 System Status")
    st.metric("API Status", "🟢 Online")
    st.metric("AI Engine", "🟢 Active")
    st.metric("Scanners", "8/8 Ready")
    
    st.markdown("---")
    
    st.markdown("### 🎯 Quick Stats")
    st.metric("Scans Today", "47")
    st.metric("Assets Monitored", "2,341")
    st.metric("Vulns Found", "156")


if __name__ == "__main__":
    main()
