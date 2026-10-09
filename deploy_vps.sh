#!/bin/bash
# ==============================================================================
# AI UGC Video Generator - Complete 24/7 VPS Setup Script (Ubuntu/Debian)
# ==============================================================================
set -e

echo "🚀 [1/6] Updating system and installing essential packages..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y wget curl unzip git ffmpeg xvfb x11vnc python3 python3-pip python3-venv

echo "🌐 [2/6] Installing Google Chrome Stable..."
if ! command -v google-chrome &> /dev/null; then
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo dpkg -i google-chrome-stable_current_amd64.deb || sudo apt -f install -y
    rm google-chrome-stable_current_amd64.deb
fi

echo "📦 [3/6] Installing Node.js & Flow Connector CLI..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi
sudo npm install -g flow-connector-cli

echo "🐍 [4/6] Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

CURRENT_USER=$(whoami)
APP_DIR=$(pwd)

echo "🖥️ [5/6] Creating Virtual Display + Chrome Service (flow-chrome.service)..."
sudo bash -c "cat <<EOF > /etc/systemd/system/flow-chrome.service
[Unit]
Description=Virtual Xvfb Display + Chrome for Google Flow
After=network.target

[Service]
Type=simple
User=${CURRENT_USER}
Environment=\"DISPLAY=:99\"
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1920x1080x24
ExecStart=/usr/bin/google-chrome --no-first-run --no-default-browser-check --disable-gpu --user-data-dir=/home/${CURRENT_USER}/.config/google-chrome \"https://flow.google.com\"
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

echo "🤖 [6/6] Creating Telegram Bot & Bridge Service (ai-ugc-bot.service)..."
sudo bash -c "cat <<EOF > /etc/systemd/system/ai-ugc-bot.service
[Unit]
Description=AI UGC Telegram Bot & Generator Daemon
After=network.target flow-chrome.service

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${APP_DIR}
Environment=\"PATH=${APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin\"
ExecStartPre=/usr/local/bin/flow-auto bridge start
ExecStart=${APP_DIR}/venv/bin/python ${APP_DIR}/telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
echo ""
echo "=========================================================================="
echo "✅ Setup Complete!"
echo "👉 Next step: Sync your logged-in Google Chrome profile to /home/${CURRENT_USER}/.config/google-chrome"
echo "   Then start the services with:"
echo "   sudo systemctl enable --now flow-chrome"
echo "   sudo systemctl enable --now ai-ugc-bot"
echo "=========================================================================="
