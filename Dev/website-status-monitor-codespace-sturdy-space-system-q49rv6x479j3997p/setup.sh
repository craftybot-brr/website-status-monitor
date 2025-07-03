#!/bin/bash
# Setup script for Website Status Monitor on Debian 12
set -e

# Ensure running on Debian/Ubuntu-based system
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete. Activate the virtual environment with 'source venv/bin/activate' and run 'python app.py' to start the server."
echo "The monitor includes both website status checking (/) and AWS EC2 regional endpoint monitoring (/ec2)."
