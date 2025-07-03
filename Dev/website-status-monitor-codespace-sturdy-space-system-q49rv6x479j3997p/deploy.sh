#!/bin/bash

# Website Status Monitor - Deployment Script
# This script helps deploy the status monitor with optimal configuration

set -e

echo "🚀 Website Status Monitor - Deployment Script"
echo "=============================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

# Determine pip command
PIP_CMD="pip"
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
fi

echo "✅ pip found: $($PIP_CMD --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
$PIP_CMD install -r requirements.txt

# Set default environment variables
export FLASK_DEBUG=0
export PORT=80

echo ""
echo "⚙️  Configuration Options:"
echo "=========================="
echo "Port: $PORT (set PORT environment variable to change)"
echo "Debug: $FLASK_DEBUG (set FLASK_DEBUG=1 for development)"
echo ""

# Check if running as root for port 80
if [ "$PORT" = "80" ] && [ "$EUID" -ne 0 ]; then
    echo "⚠️  Warning: Port 80 requires root privileges"
    echo "   Options:"
    echo "   1. Run with sudo: sudo -E ./deploy.sh"
    echo "   2. Use different port: PORT=8080 ./deploy.sh"
    echo "   3. Continue anyway (will fail if port is restricted)"
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

# Check if Cloudflare configuration exists
if [ -f "CLOUDFLARE_CONFIG.md" ]; then
    echo "📚 Cloudflare configuration guide available in CLOUDFLARE_CONFIG.md"
    echo "   Configure your Cloudflare settings for optimal performance"
    echo ""
fi

# Run initial status check
echo "🔍 Running initial status check..."
python3 -c "
from app import update_status_data, PAGES
print(f'✅ Status monitor initialized successfully')
print(f'   Total pages: {len(PAGES)}')
print(f'   Total websites: {sum(len(p[\"websites\"]) for p in PAGES.values())}')
update_status_data()
print('✅ Initial status check completed')
"

echo ""
echo "🎉 Deployment completed successfully!"
echo "===================================="
echo ""
echo "📋 Next Steps:"
echo "1. Start the application:"
if [ "$PORT" = "80" ]; then
    echo "   sudo python3 app.py"
else
    echo "   python3 app.py"
fi
echo ""
echo "2. Access the dashboard:"
echo "   http://localhost:$PORT"
echo ""
echo "3. For production with Cloudflare:"
echo "   - Configure Page Rules (see CLOUDFLARE_CONFIG.md)"
echo "   - Set up proper DNS records"
echo "   - Enable SSL/TLS"
echo ""
echo "🔧 Useful Commands:"
echo "   Run in background: screen -S monitor -d -m python3 app.py"
echo "   Check logs: screen -r monitor"
echo "   Force refresh: Click 'Force Refresh' in web UI"
echo ""
echo "📖 Documentation:"
echo "   README.md - General setup and usage"
echo "   CLOUDFLARE_CONFIG.md - Cloudflare optimization"
echo ""
echo "🆘 Troubleshooting:"
echo "   - Check port availability: netstat -tlnp | grep :$PORT"
echo "   - Verify dependencies: pip list"
echo "   - Test API: curl http://localhost:$PORT/api/status"
echo ""

# Offer to start the application
read -p "Start the application now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Starting Website Status Monitor..."
    echo "   Press Ctrl+C to stop"
    echo "   Access at: http://localhost:$PORT"
    echo ""
    
    if [ "$PORT" = "80" ] && [ "$EUID" -ne 0 ]; then
        echo "⚠️  Attempting to start on port 80 without root privileges..."
        echo "   This may fail. Use 'sudo python3 app.py' if needed."
        echo ""
    fi
    
    python3 app.py
else
    echo "✅ Ready to start! Run: python3 app.py"
fi 