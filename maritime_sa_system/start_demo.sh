#!/bin/bash

# Maritime Situation Awareness Layer - Quick Start Script
# This script sets up and launches the demo system

echo "=================================================="
echo "Maritime Situation Awareness Layer - Quick Start"
echo "=================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip first."
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "🧪 Running system tests..."
cd backend
python3 test_system.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ All tests passed!"
    echo ""
    echo "=================================================="
    echo "🚀 Starting Demo Server..."
    echo "=================================================="
    echo ""
    echo "The dashboard will be available at:"
    echo "👉 http://localhost:5000"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    # Start the server
    python3 demo_server.py
else
    echo ""
    echo "❌ System tests failed. Please check the output above."
    exit 1
fi
