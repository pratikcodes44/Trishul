#!/bin/bash

echo "🔱 Trishul Frontend - Quick Setup Script"
echo "=================================="
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo ""

# Check if we're in the frontend directory
if [ ! -f "package.json" ]; then
    echo "⚠️  Please run this script from the 'frontend' directory"
    exit 1
fi

echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Setup complete!"
    echo ""
    echo "🚀 To start the development server, run:"
    echo "   npm run dev"
    echo ""
    echo "📖 Then open http://localhost:3000 in your browser"
    echo ""
    echo "💡 Available routes:"
    echo "   /             - Landing"
    echo "   /operations   - Operations Dashboard"
    echo "   /reports      - Reports & Analytics"
    echo ""
else
    echo "❌ Installation failed. Please check the errors above."
    exit 1
fi
