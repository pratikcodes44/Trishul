#!/bin/bash

# 🎨 Start Dashboard for Demo
# This script properly starts the Streamlit dashboard

echo "🎨 Starting Trishul AI Dashboard..."
echo ""

cd "$(dirname "$0")" || exit

echo "📍 Location: $(pwd)"
echo "🔧 Starting on http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start streamlit
streamlit run ai_dashboard.py --server.port 8501 --server.address 0.0.0.0
