#!/bin/bash

# Maritime Video Analysis System - Quick Start

echo "=================================================="
echo "Maritime Video Analysis System - Quick Start"
echo "=================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Install dependencies
echo "📦 Installing dependencies (including OpenCV)..."
pip3 install -q -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "=================================================="
echo "🚀 Starting Video Analysis Server..."
echo "=================================================="
echo ""
echo "The dashboard will be available at:"
echo "👉 http://localhost:5000"
echo ""
echo "Features:"
echo "  • Upload maritime video files (MP4, AVI, MOV, etc.)"
echo "  • Real-time SA layer analysis"
echo "  • Anomaly detection from video"
echo "  • Spoofing detection"
echo "  • Live alerts and statistics"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start server
cd backend
python3 video_server.py
