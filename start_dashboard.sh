#!/bin/bash

# 🎨 Start Frontend for Demo
# This script starts the unified Next.js frontend dashboard pages

echo "🎨 Starting Trishul Frontend..."
echo ""

cd "$(dirname "$0")" || exit

echo "📍 Location: $(pwd)"
echo "🔧 Starting on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd frontend || exit

# Start Next.js dashboard
npm run dev -- --port 3000
