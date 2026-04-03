#!/bin/bash

echo "🔱 Trishul AI-Powered Security Platform - Quick Start"
echo "=================================================="
echo ""

# Check Python version
python3 --version || { echo "❌ Python 3 required"; exit 1; }

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt --quiet

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Available Commands:"
echo ""
echo "1. Launch AI Dashboard:"
echo "   streamlit run ai_dashboard.py"
echo ""
echo "2. Start SaaS API Server:"
echo "   python3 api_server.py"
echo ""
echo "3. Run Main Scanner:"
echo "   python3 main.py --target example.com"
echo ""
echo "4. View API Documentation:"
echo "   python3 api_server.py (then visit http://localhost:8000/api/docs)"
echo ""
echo "5. Test AI Engine:"
echo "   python3 ai_engine.py"
echo ""
echo "=================================================="
echo "🎯 For Hackathon Demo:"
echo "   1. Run: streamlit run ai_dashboard.py"
echo "   2. Show AI-powered vulnerability analysis"
echo "   3. Demo real-time risk scoring"
echo "=================================================="
