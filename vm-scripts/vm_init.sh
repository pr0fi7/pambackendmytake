#!/bin/bash
set -e

USERNAME="pam-admin"
PASSWORD="<PASSWORD>"  # Replace with a secure password and store in 1Password

SCRIPT_DIR="/usr/local/sbin/pam-scripts"

# Create an admin user
sudo useradd -m -s /bin/bash "$USERNAME"
sudo usermod -aG sudo "$USERNAME"
echo "$USERNAME:$PASSWORD" | sudo chpasswd

# --------------
# - Login with the pam-admin user
# --------------

sudo su - "$USERNAME"

# Install necessary packages
sudo apt-get update
sudo apt-get install -y curl git google-cloud-sdk

sudo mkdir -p $SCRIPT_DIR

# Pull Backend repo
GITHUB_TOKEN=$(gcloud secrets versions access latest --secret=pam-github-token)
git clone https://$GITHUB_TOKEN@github.com/Harmix/pam-backend-api.git

# Copy VM scripts
sudo cp pam-backend-api/vm-scripts/* $SCRIPT_DIR/
sudo chmod +x $SCRIPT_DIR/create_client.sh

gcloud config set project harmix-pam

# Install Node.js and Claude Code
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g @anthropic-ai/claude-code
