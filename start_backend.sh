#!/bin/bash

# Trishul - Start Backend (API Server)
# Run this in Terminal 1

echo "🔱 Starting Trishul Backend (API Server)..."
echo ""

cd /home/manthan/Projects/Trishul

# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
echo "🚀 Launching FastAPI Server..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/api/docs"
echo ""

python api_server.py
