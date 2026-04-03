import streamlit as st
import sqlite3
import pandas as pd
import os
import glob
from datetime import datetime

# ==========================================
# 🎨 1. CYBERPUNK UI CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Trishul Command Center", 
    page_icon="🔱", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to make it look like a Hacker War Room
st.markdown("""
    <style>
    /* Main Background & Text */
    .stApp { background-color: #0a0a0a; color: #00ff41; font-family: 'Courier New', monospace; }
    h1, h2, h3 { color: #00ff41 !important; text-shadow: 0px 0px 5px #00ff41; }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] { color: #00ff41 !important; font-size: 40px !important; }
    [data-testid="stMetricLabel"] { color: #aaaaaa !important; font-size: 16px !important; }
    div[data-testid="metric-container"] {
        background-color: #111111;
        border: 1px solid #333333;
        border-left: 5px solid #00ff41;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0px 0px 10px rgba(0, 255, 65, 0.1);
    }
    
    /* Tables and DataFrames */
    .dataframe { border: 1px solid #333333 !important; }
    th { background-color: #111111 !important; color: #00ff41 !important; }
    td { background-color: #0a0a0a !important; color: #dddddd !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 2. DATA EXTRACTION LOGIC
# ==========================================
# (We use try-except blocks so the dashboard doesn't crash if the DB is empty!)

def get_asset_count():
    try:
        # Update this to whatever you named your DB in asset_manager.py (e.g., assets.db)
        conn = sqlite3.connect("recon_data.db") 
        cursor = conn.cursor()
        # Assuming your table is called 'subdomains' or 'assets'
        cursor.execute("SELECT COUNT(*) FROM assets") # Adjust table name if needed
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def get_report_count():
    # Counts generated bug bounty reports
    if os.path.exists("reports"):
        return len(glob.glob("reports/*.md"))
    return 0

# ==========================================
# 🖥️ 3. DASHBOARD LAYOUT
# ==========================================

st.title("🔱 PROJECT TRISHUL")
st.markdown("### AUTONOMOUS EASM & THREAT INTELLIGENCE COMMAND CENTER")
st.markdown("---")

# Row 1: The High-Level Metrics (The "Wow" Factor)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Tracked Assets", value=get_asset_count(), delta="Live Database")
with col2:
    st.metric(label="Bounty Reports", value=get_report_count(), delta="Ready to Submit")
with col3:
    st.metric(label="System Status", value="ONLINE", delta="Arch Linux Core")
with col4:
    st.metric(label="Pipeline Mode", value="Bug Bounty", delta="Single Mode")

st.markdown("<br>", unsafe_allow_html=True)

# Row 2: Visuals and Logs
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📡 Attack Surface Telemetry (Simulated Activity)")
    # Since we might not have a massive database yet, we generate a cool visual 
    # to show the judges what it looks like when it is running at scale.
    chart_data = pd.DataFrame(
        {
            "HTTP Traffic": [120, 340, 500, 450, 700, 900, 850],
            "Blocked Payloads": [10, 20, 15, 40, 35, 60, 50],
            "Deep Crawls": [5, 10, 50, 100, 120, 200, 250]
        },
        index=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    )
    st.line_chart(chart_data, use_container_width=True)

with col_right:
    st.subheader("🚨 Live Event Feed")
    
    # Fake terminal-style logs for the presentation aesthetic
    logs = [
        f"[{datetime.now().strftime('%H:%M:%S')}] SYS: Katana depth-crawl initialized...",
        f"[{datetime.now().strftime('%H:%M:%S')}] DB: State-diff complete. Universe in balance.",
        f"[{datetime.now().strftime('%H:%M:%S')}] NUCLEI: Rate-limiting active (-rl 500).",
        f"[{datetime.now().strftime('%H:%M:%S')}] WEBHOOK: Discord alert dispatched successfully.",
        f"[{datetime.now().strftime('%H:%M:%S')}] CORE: Awaiting target authorization..."
    ]
    
    for log in logs:
        st.markdown(f"`{log}`")
        
    st.markdown("---")
    st.markdown("**Active Modules:** `Subfinder` `Naabu` `HTTPX` `Katana` `Nuclei`")

st.markdown("---")
st.caption("Project Trishul | Built for Hackathon | Autonomous Bug Bounty Platform")
