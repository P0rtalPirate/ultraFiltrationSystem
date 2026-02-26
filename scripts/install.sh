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
                        python3-dev build-essential libpython3-dev patchelf \
                        xserver-xorg xinit openbox plymouth plymouth-themes zstd \
                        xserver-xorg-legacy python3-rpi.gpio unclutter

# Configure X11 to allow non-console users to start X server
echo "allowed_users=anybody" | sudo tee /etc/X11/Xwrapper.config

# Add user to video and input groups for X11/GUI access
sudo usermod -a -G video,input $(whoami)

# 2. Clone or Restore repository
INSTALL_DIR="$HOME/ultraFiltrationSystem"
if [ ! -d "$INSTALL_DIR/.git" ] && [ ! -d "$INSTALL_DIR/src" ]; then
    echo "📂 Source missing or wiped. (Re)Cloning repository..."
    # If directory exists but no .git, we might be in a wiped state. 
    # Move existing files to a temp area to avoid git clone conflicts
    if [ -d "$INSTALL_DIR" ]; then
        mv "$INSTALL_DIR" "${INSTALL_DIR}_backup_$(date +%s)"
    fi
    git clone https://github.com/P0rtalPirate/ultraFiltrationSystem.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# 3. Set up Virtual Environment
echo "🐍 Preparing environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install . ordered-set nuitka zstandard  # nuitka and deps for building

# 4. Branded Boot Splash Screen using system_diagram.png
echo "🎨 Configuring Boot Splash Screen (Raj Enterprices)..."

THEME_DIR="/usr/share/plymouth/themes/ultrafiltration"
PNG_SRC="$INSTALL_DIR/branding/system_diagram.png"

if [ -f "$PNG_SRC" ]; then
    echo "   🖼️  system_diagram.png found. Setting up Plymouth theme..."

    # Install Plymouth if not already present
    sudo apt-get install -y --no-install-recommends plymouth plymouth-themes

    # Create theme directory
    sudo mkdir -p "$THEME_DIR"

    # Copy diagram image as the splash background
    sudo cp "$PNG_SRC" "$THEME_DIR/splash.png"

    # Write the Plymouth script (centers the image on-screen)
    sudo tee "$THEME_DIR/ultrafiltration.script" > /dev/null <<'PLYSCRIPT'
wallpaper_image = Image("splash.png");
screen_width = Window.GetWidth();
screen_height = Window.GetHeight();
img_width = wallpaper_image.GetWidth();
img_height = wallpaper_image.GetHeight();
scale = Math.Min(screen_width / img_width, screen_height / img_height);
scaled_width = img_width * scale;
scaled_height = img_height * scale;
x = (screen_width - scaled_width) / 2;
y = (screen_height - scaled_height) / 2;
wallpaper_sprite = Sprite(wallpaper_image.Scale(scaled_width, scaled_height));
wallpaper_sprite.SetPosition(x, y, -100);
PLYSCRIPT

    # Write the Plymouth theme config
    sudo tee "$THEME_DIR/ultrafiltration.plymouth" > /dev/null <<'PLYCONF'
[Plymouth Theme]
Name=UltraFiltration
Description=Raj Entreprices System Diagram Splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/ultrafiltration
ScriptFile=/usr/share/plymouth/themes/ultrafiltration/ultrafiltration.script
PLYCONF

    # Set as the default Plymouth theme
    sudo plymouth-set-default-theme ultrafiltration

    # Hide boot logs in cmdline.txt
    CMDLINE="/boot/firmware/cmdline.txt"
    if [ ! -f "$CMDLINE" ]; then CMDLINE="/boot/cmdline.txt"; fi
    if [ -f "$CMDLINE" ]; then
        # Add splash flags (only if not already present)
        if ! grep -q "quiet" "$CMDLINE"; then
            sudo sed -i 's/$/ quiet splash plymouth.ignore-serial-consoles logo.nologo vt.global_cursor_default=0/' "$CMDLINE"
            echo "   ✔  Boot flags added to $CMDLINE"
        fi
    fi

    # Regenerate initramfs so Plymouth is included in the boot sequence
    sudo update-initramfs -u
    echo "   ✅ Boot splash installed successfully!"
else
    echo "   ⚠️  branding/system_diagram.png not found. Skipping splash setup."
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
    rm -rf *.build/ *.dist/ *.onefile-build/
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

# Start X with Openbox
echo "🖥️  Configuring Kiosk Mode..."
mkdir -p ~/.config/openbox

# Custom Openbox RC to hide window borders
cat > ~/.config/openbox/rc.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<openbox_config>
  <applications>
    <application class="*">
      <decor>no</decor>
      <fullscreen>yes</fullscreen>
    </application>
  </applications>
</openbox_config>
EOF

cat > ~/.config/openbox/autostart <<EOF
# ── Disable screen blanking and DPMS ───────────────────────────────────────
xset s off &
xset -dpms &
xset s noblank &

# Hide cursor after 0 seconds of inactivity
unclutter -idle 0 &

# Start UltraFiltration Binary in Fullscreen
$INSTALL_DIR/ultra-filt &
EOF

# ── Disable screen blanking (kernel + raspi-config layers) ─────────────────
echo "🖥️  Disabling screen blanking (kernel and Pi config)..."

# Layer 1: raspi-config non-interactive
sudo raspi-config nonint do_blanking 1 2>/dev/null || true

# Layer 2: Kernel boot parameter
CMDLINE=/boot/cmdline.txt
if [ -f "$CMDLINE" ] && ! grep -q "consoleblank=0" "$CMDLINE"; then
    sudo sed -i 's/$/ consoleblank=0/' "$CMDLINE"
    echo "   ✔  consoleblank=0 added to $CMDLINE"
fi

echo "   ✔  Screen blanking fully disabled."

# Create .xinitrc for startx/xinit fallback
cat > ~/.xinitrc <<EOF
exec openbox-session
EOF

# 9. Install Systemd Service for Bootup
echo "⚙️  Configuring systemd boot service..."
SERVICE_FILE="/etc/systemd/system/ultrafiltration.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=UltraFiltration Control System (Raj Enterprices)
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$INSTALL_DIR
Environment=DISPLAY=:0
Environment=XAUTHORITY=$HOME/.Xauthority
ExecStartPre=/usr/bin/rm -f /tmp/.X0-lock
ExecStart=/usr/bin/xinit /usr/bin/openbox-session -- :0 -nolisten tcp vt7 -nocursor
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 10. Enable and Start service
sudo systemctl daemon-reload
sudo systemctl enable ultrafiltration.service
sudo systemctl start ultrafiltration.service

echo ""
echo "✅ Deployment Complete!"
echo "-------------------------------------------------------"
echo "Code is now COMPILED and PROTECTED as a binary."
echo "Source code has been DELETED from the Pi."
echo "System will boot directly into binary on next restart."
echo "-------------------------------------------------------"
