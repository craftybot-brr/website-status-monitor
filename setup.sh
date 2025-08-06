#!/bin/bash
# Setup script for Website Status Monitor on Debian 12

# Exit immediately on error, undefined variable, or pipe failure
set -euo pipefail

# Display a helpful error message if something fails
handle_error() {
    local exit_code=$1
    local line_no=$2
    echo "Error: command exited with status ${exit_code} at line ${line_no}." >&2
    exit "$exit_code"
}
trap 'handle_error $? $LINENO' ERR

# Ensure required commands are available
for cmd in sudo apt-get python3 pip; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Required command '$cmd' not found. Please install it before running this script." >&2
        exit 1
    fi
done

# Ensure running on Debian/Ubuntu-based system
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. Activate the virtual environment with 'source venv/bin/activate' and run 'python app.py' to start the server."
