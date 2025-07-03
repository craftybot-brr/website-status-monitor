#!/bin/bash
# Quick installer for Website Status Monitor
# This script downloads and runs the full installation

set -e

REPO_URL="https://github.com/craftybot-brr/website-status-monitor"
INSTALLER_URL="$REPO_URL/raw/main/install.sh"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "🌐 Website Status Monitor - Quick Installer"
echo "============================================"
echo -e "${NC}"

echo -e "${YELLOW}ℹ️  Downloading installer...${NC}"

# Download and run the installer
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$INSTALLER_URL" | bash
elif command -v wget >/dev/null 2>&1; then
    wget -qO- "$INSTALLER_URL" | bash
else
    echo -e "${RED}❌ Neither curl nor wget found. Please install one of them first.${NC}"
    exit 1
fi
