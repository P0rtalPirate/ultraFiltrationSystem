#!/bin/bash

# UltraFiltration Advanced Installer (Raj Enterprices)
# Handles: Nuitka Compilation, Minimal GUI (Lite OS), and Branded Splash
# Tested on Raspberry Pi OS (Lite - 64-bit)

set -e

echo "🚀 Starting Advanced UltraFiltration Setup (Raj Enterprices)..."

# 1. Update system and install dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-tk python3-pip python3-venv git \
                        python3-dev build-essential libpython3-dev \
                        xserver-xorg xinit openbox plymouth plymouth-themes

# 2. Clone repository
INSTALL_DIR="$HOME/ultraFiltrationSystem"
if [ ! -d "$INSTALL_DIR" ]; then
    echo "📂 Cloning repository..."
    git clone https://github.com/P0rtalPirate/ultraFiltrationSystem.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 3. Set up Virtual Environment
echo "🐍 Preparing environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install . ordered-set nuitka  # nuitka and deps for building

# 4. Branded Splash Screen Setup (Optional/Placeholder)
echo "🎨 Configuring Branding (Raj Enterprices)..."
if [ -f "branding/logo.png" ]; then
    echo "🖼️  Setting up logo splash screen..."
    # Logic to copy logo to plymouth would go here
    # sudo cp branding/logo.png /usr/share/plymouth/themes/spinner/watermark.png
fi

# 5. Nuitka Compilation (The Protection Phase)
echo "🔒 Compiling project with Nuitka (This may take 10-20 minutes)..."
python3 -m nuitka --follow-imports \
                  --standalone \
                  --onefile \
                  --output-filename=ultra-filt \
                  src/main.py

# Verify binary
if [ -f "ultra-filt" ]; then
    echo "✅ Compilation successful: Binary created."
    
    # 6. Wipe Phase (Cleanup Source)
    echo "🧹 Wiping source code for security..."
    rm -rf src/
    rm -f pyproject.toml requirements.txt .gitignore README.md HARDWARE.md
    rm -rf .git/
else
    echo "❌ Compilation failed. Keeping source code for safety."
fi

# 7. Create default .env if missing
if [ ! -f ".env" ]; then
    cat > .env <<EOF
# UltraFiltration Configuration (Raj Enterprices)
UF_HARDWARE_CONNECTED=true
UF_DISPLAY_FULLSCREEN=true
UF_SHOW_CURSOR=false
UF_LOG_LEVEL=INFO
EOF
fi

# 8. Configure Minimal GUI (Openbox) to launch binary
echo "🖥️  Configuring Kiosk Mode..."
mkdir -p ~/.config/openbox
cat > ~/.config/openbox/autostart <<EOF
# Start UltraFiltration Binary in Fullscreen
$INSTALL_DIR/ultra-filt &
EOF

# 9. Install Systemd Service for Bootup
echo "⚙️  Configuring systemd boot service..."
SERVICE_FILE="/etc/systemd/system/ultrafiltration.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=UltraFiltration Control System (Raj Enterprices)
After=graphical.target

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=$HOME/.Xauthority
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/startx
Restart=always
User=$(whoami)

[Install]
WantedBy=graphical.target
EOF

# 10. Enable service
sudo systemctl daemon-reload
sudo systemctl enable ultrafiltration.service

echo ""
echo "✅ Deployment Complete!"
echo "-------------------------------------------------------"
echo "Code is now COMPILED and PROTECTED as a binary."
echo "Source code has been DELETED from the Pi."
echo "System will boot directly into binary on next restart."
echo "-------------------------------------------------------"
