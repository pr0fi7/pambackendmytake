#!/bin/bash

CLIENT_NAME=$1
BACKEND_PORT=$2
ENVIRONMENT=$3

USERNAME="pam-$CLIENT_NAME"
PASSWORD=$(gcloud secrets versions access latest --secret=pam-agent-linux-user-password)
GCP_PROJECT_NAME="harmix-pam"


if [[ "$ENVIRONMENT" == "prod" ]]; then
    BACKEND_BRANCH="main"
    BACKEND_SECRET_NAME="pam-prod-backend-secrets"
else
    BACKEND_BRANCH="develop"
    BACKEND_SECRET_NAME="pam-uat-backend-secrets"
fi

if [ -z "$CLIENT_NAME" ]; then
    echo "Usage: create_client <client_name>"
    exit 1
fi

# Validate backend port
if [ -z "$BACKEND_PORT" ] || ! [[ "$BACKEND_PORT" =~ ^[0-9]+$ ]] || [ "$BACKEND_PORT" -lt 1024 ] || [ "$BACKEND_PORT" -gt 65535 ]; then
    echo "Usage: create_client <client_name> <backend_port>"
    echo "Backend port must be a number between 1024 and 65535"
    exit 1
fi

echo "[+] Creating user $USERNAME"

# Create user if not exists
if id "$USERNAME" &>/dev/null; then
    echo "[+] User already exists, skipping creation"
else
    sudo useradd -m -s /bin/bash "$USERNAME"
    sudo usermod -aG sudo "$USERNAME"
    echo "$USERNAME:$PASSWORD" | sudo chpasswd
fi

USER_HOME="/home/$USERNAME"
REPO_DIR="$USER_HOME/pam-claude-code"
BACKEND_DIR="$USER_HOME/pam-backend-api"

PAM_CLAUDE_CODE_BRANCH="claude-vertex-ai"

echo "[+] Installing as user: $USERNAME"

# Pull GitHub token
GITHUB_TOKEN=$(gcloud secrets versions access latest --secret=pam-github-token)

# Clone Claude repo
if [ ! -d "$REPO_DIR" ]; then
    sudo -u "$USERNAME" git clone \
        https://$GITHUB_TOKEN@github.com/Harmix/pam-claude-code.git \
        "$REPO_DIR"

    sudo -u "$USERNAME" git -C "$REPO_DIR" fetch --all
    sudo -u "$USERNAME" git -C "$REPO_DIR" checkout $PAM_CLAUDE_CODE_BRANCH
    sudo -u "$USERNAME" git -C "$REPO_DIR" pull origin $PAM_CLAUDE_CODE_BRANCH
fi

# ----- CLAUDE CONFIG -----
sudo -u "$USERNAME" bash -c "cat > $USER_HOME/.claude.json <<EOF
{
  \"theme\": \"dark\",
  \"hasCompletedOnboarding\": true,
  \"projects\": {
    \"$REPO_DIR\": {
      \"hasTrustDialogAccepted\": true
    }
  }
}
EOF"

echo "[+] Claude configuration done"

# ===== BACKEND API INSTALL =====
echo "[+] Setting up Backend API for $USERNAME"

# Clone backend repo
if [ ! -d "$BACKEND_DIR" ]; then
    sudo -u "$USERNAME" git clone \
        https://$GITHUB_TOKEN@github.com/Harmix/pam-backend-api.git \
        "$BACKEND_DIR"

    sudo -u "$USERNAME" git -C "$BACKEND_DIR" fetch --all
    sudo -u "$USERNAME" git -C "$BACKEND_DIR" switch -f $BACKEND_BRANCH
    sudo -u "$USERNAME" git -C "$BACKEND_DIR" pull origin $BACKEND_BRANCH
fi

sudo apt-get install -y python3.11-venv

# Create virtual environment
sudo -u "$USERNAME" bash -c "
    cd \"$BACKEND_DIR\" && \
    python3 -m venv venv && \
    source venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    mkdir -p logs
"

# Get secrets from GCP Secret Manager
SECRET_ENV=$(gcloud secrets versions access latest --secret=$BACKEND_SECRET_NAME)

# Non-secret environment variables
read -r -d '' NON_SECRET_ENV <<EOF
WORKING_DIR=/home/$USERNAME/pam-claude-code
AGENT_API=true
CENTRAL_API_USER_ID=[]
EOF

# ----- AUTOGENERATE .env -----
sudo -u "$USERNAME" bash -c "cat > $BACKEND_DIR/.env <<EOF
$SECRET_ENV

$NON_SECRET_ENV
EOF"

echo "[+] Backend .env generated"

# ===== SYSTEMD SERVICE =====
SERVICE_FILE="/etc/systemd/system/pam-$CLIENT_NAME-backend.service"

sudo bash -c "cat > $SERVICE_FILE <<EOF
[Unit]
Description=PAM Backend API for $USERNAME
After=network.target

[Service]
User=$USERNAME
WorkingDirectory=$BACKEND_DIR
EnvironmentFile=$BACKEND_DIR/.env
ExecStart=$BACKEND_DIR/venv/bin/uvicorn --host 0.0.0.0 --log-config $BACKEND_DIR/log_config.yml --port $BACKEND_PORT app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

# Enable + start service
sudo systemctl daemon-reload
sudo systemctl enable pam-$CLIENT_NAME-backend
sudo systemctl restart pam-$CLIENT_NAME-backend

echo "[+] Backend API service started and enabled"

echo "[+] Finished provisioning $USERNAME"
