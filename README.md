## Connect to VM locally
1. Add `google_credentials.json` file to the base folder of this project.

2. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
```shell
# MacOS
brew install --cask google-cloud-sdk

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y google-cloud-sdk
```

3. Authenticate with Google Cloud
```shell
gcloud config set project harmix-pam
gcloud auth activate-service-account --key-file=google_credentials.json
```


## Run GitHub in VM
```
# 0) Prereqs
sudo apt update
sudo apt install -y git curl ca-certificates

# 1) Create a read-only Deploy Key for the repo (SSH keypair without passphrase)
mkdir -p ~/.ssh && chmod 700 ~/.ssh
ssh-keygen -t ed25519 -C "deploy-key@$(hostname)" -f ~/.ssh/id_deploy_repo -N ""
echo "👉 Add this PUBLIC key to GitHub → Repo → Settings → Deploy keys (Read-only):"
echo "-----8<-----"
cat ~/.ssh/id_deploy_repo.pub
echo "-----8<-----"

# Make GitHub known_hosts to avoid prompts
ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts

# 2) Git config to force this key for GitHub
cat >> ~/.ssh/config <<'EOF'
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_deploy_repo
  IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config

# 3) Clone the repo
mkdir pam-backend-api
git clone git@github.com:Harmix/pam-backend-api.git pam-backend-api

# 4) Set up the repo
cd pam-backend-api
sudo apt install python3.11-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

mkdir logs

nano .env


# 5) Run the app
screen -S new_screen

source venv/bin/activate
git pull
pkill uvicorn
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
uvicorn --host 0.0.0.0 --log-config log_config.yml --port 8000 src.main:app

# Then you press Ctrl + A + D for detaching, leave it run in background.


# 6) Kill current running API
ps aux | grep uvicorn
kill -9 PID
```