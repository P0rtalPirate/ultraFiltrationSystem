#!/bin/bash

# UltraFiltration Automated Installer
# Tested on Raspberry Pi OS (Bullseye/Bookworm)

set -e

echo "🚀 Starting UltraFiltration installation..."

# 1. Update system and install dependencies
echo "📦 Installing system dependencies (Tkinter, Python3)..."
sudo apt-get update
sudo apt-get install -y python3-tk python3-pip python3-venv git

# 2. Clone repository if not already in the folder
INSTALL_DIR="$HOME/ultraFiltrationSystem"
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📂 Cloning repository..."
    git clone https://github.com/P0rtalPirate/ultraFiltrationSystem.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 3. Set up Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
echo "🛠️ Installing Python packages..."
pip install --upgrade pip
pip install .

# 5. Create default .env if missing
if [ ! -f ".env" ]; then
    echo "📝 Creating default .env configuration..."
    cat > .env <<EOF
# UltraFiltration Configuration
UF_HARDWARE_CONNECTED=true
UF_DISPLAY_FULLSCREEN=true
UF_SHOW_CURSOR=false
UF_LOG_LEVEL=INFO
EOF
fi

# 6. Install Systemd Service for Bootup
echo "⚙️ Configuring systemd boot service..."
SERVICE_FILE="/etc/systemd/system/ultrafiltration.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=UltraFiltration Control System
After=graphical.target

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=$HOME/.Xauthority
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3 -m src.main
Restart=always
User=$(whoami)

[Install]
WantedBy=graphical.target
EOF

# 7. Enable and Start service
echo "🔄 Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable ultrafiltration.service

echo ""
echo "✅ Installation Complete!"
echo "-------------------------------------------------------"
echo "The system is now set to start automatically on boot."
echo "To start now, run: sudo systemctl start ultrafiltration"
echo "To check logs, run: journalctl -u ultrafiltration -f"
echo "-------------------------------------------------------"
