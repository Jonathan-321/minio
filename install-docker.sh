#!/bin/bash

echo "🐳 Docker Installation Guide"
echo "============================="

# Check if Docker Desktop exists but is broken
if [ -d "/Applications/Docker.app" ]; then
    echo "📱 Docker Desktop found but may be corrupted"
    echo "🔄 Reinstalling Docker Desktop..."
    
    # Remove existing Docker Desktop
    echo "🗑️  Removing old Docker Desktop..."
    rm -rf /Applications/Docker.app
    
    # Clean up Docker data (optional)
    echo "🧹 Cleaning up Docker data..."
    rm -rf ~/Library/Group\ Containers/group.com.docker
    rm -rf ~/Library/Containers/com.docker.docker
fi

echo "📥 Installing Docker Desktop..."

# Download and install Docker Desktop
if command -v brew &> /dev/null; then
    echo "🍺 Installing via Homebrew..."
    brew install --cask docker
else
    echo "🌐 Please download Docker Desktop manually:"
    echo "   1. Go to: https://www.docker.com/products/docker-desktop/"
    echo "   2. Download Docker Desktop for Mac"
    echo "   3. Install the .dmg file"
    echo "   4. Start Docker Desktop from Applications"
fi

echo ""
echo "✅ After Docker Desktop is installed:"
echo "   1. Start Docker Desktop from Applications"
echo "   2. Wait for it to finish starting (whale icon in menu bar)"
echo "   3. Run: ./deploy-local.sh"
echo ""
echo "⚡ Quick test Docker:"
echo "   docker --version"
echo "   docker run hello-world"