#!/bin/bash

# 🚀 Start API Server for Demo
# This script properly starts the FastAPI server

echo "🚀 Starting Trishul API Server..."
echo ""

cd "$(dirname "$0")" || exit

echo "📍 Location: $(pwd)"
echo "🔧 Starting on http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start with uvicorn directly
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
