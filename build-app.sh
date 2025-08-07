#!/bin/bash

# AMRS Maintenance Tracker - Build Script
# This script builds a complete, self-contained Electron application

set -e

echo "🚀 Building AMRS Maintenance Tracker Electron App..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this script from the project root."
    exit 1
fi

# Check if Node.js and npm are installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is required but not installed."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is required but not installed."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Create portable Python environment
echo "🐍 Creating portable Python environment..."
python3 bundle-python.py

# Verify Python environment was created
if [ ! -d "python" ]; then
    echo "❌ Error: Failed to create Python environment"
    exit 1
fi

echo "✅ Python environment created successfully"

# Test the Flask app briefly
echo "🧪 Testing Flask app..."
timeout 10s python3 app.py &
FLASK_PID=$!
sleep 5

# Check if Flask is running on port 10000
if curl -s http://localhost:10000 > /dev/null; then
    echo "✅ Flask app test passed"
else
    echo "⚠️  Flask app test failed, but continuing..."
fi

# Kill the test Flask process
kill $FLASK_PID 2>/dev/null || true
sleep 2

# Build the Electron app for the current platform
echo "📱 Building Electron application..."
case "$(uname -s)" in
    Darwin*)
        echo "🍎 Building for macOS..."
        npm run build:mac
        ;;
    Linux*)
        echo "🐧 Building for Linux..."
        npm run build:linux
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        echo "🪟 Building for Windows..."
        npm run build:win
        ;;
    *)
        echo "❓ Unknown platform, building for current platform..."
        npm run dist
        ;;
esac

echo ""
echo "🎉 Build completed successfully!"
echo "📁 Built applications can be found in the 'dist' directory"
echo ""
echo "🔧 To test the app locally, run: npm start"
echo "📦 To build for all platforms, run: npm run dist"
echo ""
