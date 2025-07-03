#!/bin/bash
# Website Status Monitor - Auto Installation Script
# Downloads the latest release and sets up the application to run under screen
set -e

# Configuration
REPO_URL="https://github.com/craftybot-brr/website-status-monitor"
INSTALL_DIR="website-status-monitor"
SCREEN_SESSION="status-monitor"
SERVICE_PORT="${PORT:-80}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if command exists
has_command() {
    command -v "$1" >/dev/null 2>&1
}

# Install dependencies based on OS
install_dependencies() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_info "Installing dependencies for Linux..."
        
        # Detect package manager
        if has_command apt-get; then
            sudo apt-get update
            sudo apt-get install -y python3 python3-venv python3-pip screen wget unzip curl
        elif has_command yum; then
            sudo yum update -y
            sudo yum install -y python3 python3-venv python3-pip screen wget unzip curl
        elif has_command dnf; then
            sudo dnf update -y
            sudo dnf install -y python3 python3-venv python3-pip screen wget unzip curl
        elif has_command pacman; then
            sudo pacman -Sy --noconfirm python python-pip screen wget unzip curl
        else
            log_error "Unsupported Linux distribution. Please install python3, pip, screen, wget, and unzip manually."
            exit 1
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        log_info "Installing dependencies for macOS..."
        
        # Install Homebrew if not present
        if ! has_command brew; then
            log_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            # Add brew to PATH
            eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || true)"
            eval "$(/usr/local/bin/brew shellenv 2>/dev/null || true)"
        fi
        
        brew update
        brew install python screen wget
        
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Download and extract the repository
download_repo() {
    log_info "Downloading repository from $REPO_URL..."
    
    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"
    
    # Download the main branch as zip
    wget -O repo.zip "$REPO_URL/archive/refs/heads/main.zip"
    
    # Extract
    unzip -q repo.zip
    
    # Move to target directory
    if [[ -d "$INSTALL_DIR" ]]; then
        log_warning "Directory $INSTALL_DIR already exists. Backing up to ${INSTALL_DIR}.backup..."
        mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # The extracted directory is website-status-monitor-main
    if [[ -d "website-status-monitor-main" ]]; then
        mv website-status-monitor-main "$INSTALL_DIR"
    else
        log_error "Extracted directory website-status-monitor-main not found!"
        exit 1
    fi
    log_success "Repository downloaded and extracted to $INSTALL_DIR"
    
    # Cleanup
    rm -rf "$TEMP_DIR"
}

# Setup Python environment and install dependencies
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log_success "Python environment setup complete"
}

# Create start script
create_start_script() {
    log_info "Creating start script..."
    
    cat > start.sh << 'EOF'
#!/bin/bash
# Start script for Website Status Monitor
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
SCREEN_SESSION="status-monitor"
SERVICE_PORT="${PORT:-80}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if screen session exists
if screen -list | grep -q "$SCREEN_SESSION"; then
    log_error "Screen session '$SCREEN_SESSION' already exists!"
    echo "Use 'screen -r $SCREEN_SESSION' to attach to the existing session"
    echo "Or use './stop.sh' to stop the current session first"
    exit 1
fi

# Activate virtual environment
if [[ ! -d "venv" ]]; then
    log_error "Virtual environment not found. Please run the installation script first."
    exit 1
fi

source venv/bin/activate

# Start the application in screen
log_info "Starting Website Status Monitor in screen session '$SCREEN_SESSION'..."
log_info "Service will be available on port $SERVICE_PORT"
log_info "Access at: http://localhost:$SERVICE_PORT"
log_info "EC2 Monitor: http://localhost:$SERVICE_PORT/ec2"

screen -dmS "$SCREEN_SESSION" bash -c "
    source venv/bin/activate
    export PORT=$SERVICE_PORT
    python app.py
"

# Wait a moment for the service to start
sleep 2

# Check if the session is running
if screen -list | grep -q "$SCREEN_SESSION"; then
    log_success "Website Status Monitor started successfully!"
    echo ""
    echo "Commands:"
    echo "  View logs:    screen -r $SCREEN_SESSION"
    echo "  Detach:       Ctrl+A, then D"
    echo "  Stop service: ./stop.sh"
    echo "  Service URL:  http://localhost:$SERVICE_PORT"
    echo "  EC2 Monitor:  http://localhost:$SERVICE_PORT/ec2"
else
    log_error "Failed to start the service. Check the logs for errors."
    exit 1
fi
EOF

    chmod +x start.sh
    log_success "Start script created"
}

# Create stop script
create_stop_script() {
    log_info "Creating stop script..."
    
    cat > stop.sh << 'EOF'
#!/bin/bash
# Stop script for Website Status Monitor

SCREEN_SESSION="status-monitor"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if screen session exists
if ! screen -list | grep -q "$SCREEN_SESSION"; then
    log_error "Screen session '$SCREEN_SESSION' not found!"
    exit 1
fi

log_info "Stopping Website Status Monitor..."

# Kill the screen session
screen -S "$SCREEN_SESSION" -X quit

# Wait a moment
sleep 1

# Verify it's stopped
if ! screen -list | grep -q "$SCREEN_SESSION"; then
    log_success "Website Status Monitor stopped successfully!"
else
    log_error "Failed to stop the service. You may need to manually kill the process."
    exit 1
fi
EOF

    chmod +x stop.sh
    log_success "Stop script created"
}

# Create status script
create_status_script() {
    log_info "Creating status script..."
    
    cat > status.sh << 'EOF'
#!/bin/bash
# Status script for Website Status Monitor

SCREEN_SESSION="status-monitor"
SERVICE_PORT="${PORT:-80}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Website Status Monitor - Service Status${NC}"
echo "========================================"

# Check if screen session exists
if screen -list | grep -q "$SCREEN_SESSION"; then
    echo -e "Status: ${GREEN}RUNNING${NC}"
    echo -e "Screen Session: ${GREEN}$SCREEN_SESSION${NC}"
    echo -e "Port: ${GREEN}$SERVICE_PORT${NC}"
    echo -e "URLs:"
    echo -e "  Main Monitor: ${BLUE}http://localhost:$SERVICE_PORT${NC}"
    echo -e "  EC2 Monitor:  ${BLUE}http://localhost:$SERVICE_PORT/ec2${NC}"
    echo ""
    echo "Commands:"
    echo "  View logs: screen -r $SCREEN_SESSION"
    echo "  Stop:      ./stop.sh"
else
    echo -e "Status: ${RED}STOPPED${NC}"
    echo ""
    echo "Commands:"
    echo "  Start: ./start.sh"
fi

echo ""
echo "Recent screen sessions:"
screen -list 2>/dev/null || echo "No screen sessions found"
EOF

    chmod +x status.sh
    log_success "Status script created"
}

# Main installation process
main() {
    echo -e "${BLUE}"
    echo "🌐 Website Status Monitor - Auto Installer"
    echo "==========================================="
    echo -e "${NC}"
    
    log_info "Starting installation process..."
    
    # Check for required commands
    if ! has_command python3; then
        log_warning "Python 3 not found. Installing dependencies..."
        install_dependencies
    fi
    
    if ! has_command screen; then
        log_warning "Screen not found. Installing dependencies..."
        install_dependencies
    fi
    
    if ! has_command wget; then
        log_warning "wget not found. Installing dependencies..."
        install_dependencies
    fi
    
    # Download repository
    download_repo
    
    # Setup environment
    setup_python_env
    
    # Create management scripts
    create_start_script
    create_stop_script
    create_status_script
    
    # Create README
    cat > README_INSTALLATION.md << 'EOF'
# Website Status Monitor - Installation

This directory contains the Website Status Monitor application with management scripts.

## Quick Start

```bash
# Start the service
./start.sh

# Check status
./status.sh

# Stop the service
./stop.sh
```

## Manual Management

```bash
# Attach to the running service (view logs)
screen -r status-monitor

# Detach from screen session (leave it running)
# Press: Ctrl+A, then D

# List all screen sessions
screen -list
```

## Service Information

- **Main Monitor**: http://localhost:80
- **EC2 Monitor**: http://localhost:80/ec2
- **Screen Session**: status-monitor
- **Port**: 80 (configurable via PORT environment variable)

## Features

- **Website Monitoring**: Monitor 40 popular websites across 4 categories
- **EC2 Endpoint Monitoring**: Monitor AWS EC2 regional endpoints worldwide
- **Real-time Updates**: Status updates every 60 seconds
- **TCP Connectivity**: Reliable connection testing for cloud services
- **Responsive UI**: Clean, modern interface

## Customization

- Edit `app.py` to modify monitored websites or endpoints
- Set `PORT` environment variable to change the service port
- Modify monitoring intervals in the application code

## Troubleshooting

1. **Service won't start**: Check if port is already in use
2. **Permission errors**: Ensure scripts are executable (`chmod +x *.sh`)
3. **Python errors**: Verify virtual environment is properly activated
4. **Network issues**: Check firewall settings for the service port

For more information, visit: https://github.com/craftybot-brr/website-status-monitor
EOF
    
    log_success "Installation completed successfully!"
    echo ""
    echo -e "${GREEN}🎉 Website Status Monitor is ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. cd $INSTALL_DIR"
    echo "2. ./start.sh"
    echo "3. Open http://localhost:$SERVICE_PORT in your browser"
    echo ""
    echo "Management commands:"
    echo "  ./start.sh  - Start the service"
    echo "  ./stop.sh   - Stop the service" 
    echo "  ./status.sh - Check service status"
    echo ""
    echo "Access your monitors at:"
    echo "  Main: http://localhost:$SERVICE_PORT"
    echo "  EC2:  http://localhost:$SERVICE_PORT/ec2"
}

# Run main function
main "$@"
