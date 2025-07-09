#!/bin/bash

# Web Deployment Script for Electron-Python App
# This script builds and serves the web version of the app

set -e  # Exit on any error

echo "🚀 Starting web deployment..."

# Build the React app with Node.js OpenSSL legacy provider
echo "📦 Building React app..."
NODE_OPTIONS="--openssl-legacy-provider" npm run react-build

# Check if port 3001 is in use and kill existing processes
if lsof -i:3001 >/dev/null 2>&1; then
    echo "⚠️  Port 3001 is already in use. Killing existing processes..."
    lsof -ti:3001 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start the web server
echo "🌐 Starting web server on http://localhost:3001"
echo "   Main app: http://localhost:3001"
echo "   Demo page: http://localhost:3001/demo"
echo ""
echo "Press Ctrl+C to stop the server"

node serve-build.js