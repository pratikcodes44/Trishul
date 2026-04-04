#!/bin/bash

# Trishul - Start Frontend (Unified Next.js Frontend)
# Run this in Terminal 2

echo "🔱 Starting Trishul Frontend (Unified Next.js UI)..."
echo ""

cd /home/manthan/Projects/Trishul/frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies first..."
    npm install
    echo ""
fi

# Start Next.js dev server
echo "🚀 Launching Next.js Development Server..."
echo "📍 UI will be available at: http://localhost:3000"
echo ""

npm run dev
