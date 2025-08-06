#!/usr/bin/env bash
# Simple deployment script for Website Status Monitor
# Sets up a virtual environment, installs dependencies and starts the app using Gunicorn.

set -euo pipefail

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Default configuration
PORT="${PORT:-8000}"

# Start application using Gunicorn
exec gunicorn -w 4 -b 0.0.0.0:"$PORT" app:app
