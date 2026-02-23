#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# setup.sh — Raspberry Pi setup script for UltraFiltration
# Run: sudo bash setup.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="ultrafiltration"
USER_NAME="${SUDO_USER:-pi}"
PYTHON="python3"

echo "╔══════════════════════════════════════════════════╗"
echo "║   UltraFiltration — Raspberry Pi Setup           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. System packages ──────────────────────────────────────────────────────
echo "▶  Installing system packages..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv python3-tk python3-pil python3-pil.imagetk

# ── 2. Python dependencies ──────────────────────────────────────────────────
echo "▶  Installing Python packages..."
cd "$SCRIPT_DIR"
$PYTHON -m pip install --break-system-packages -r requirements.txt 2>/dev/null || \
    $PYTHON -m pip install -r requirements.txt

# ── 3. Create .env for production ───────────────────────────────────────────
echo "▶  Creating production .env..."
cat > "$SCRIPT_DIR/.env" << 'EOF'
# Production configuration for Raspberry Pi
UF_HARDWARE_CONNECTED=true
UF_DISPLAY_FULLSCREEN=true
UF_LOG_LEVEL=INFO
EOF

# ── 4. Add user to GPIO group ───────────────────────────────────────────────
echo "▶  Adding $USER_NAME to gpio group..."
usermod -a -G gpio "$USER_NAME" 2>/dev/null || true

# ── 5. Install systemd service ──────────────────────────────────────────────
echo "▶  Installing systemd service..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=UltraFiltration Control System
After=graphical.target
Wants=graphical.target

[Service]
Type=simple
User=$USER_NAME
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/$USER_NAME/.Xauthority
WorkingDirectory=$SCRIPT_DIR
ExecStart=$PYTHON -m src.main
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
EOF

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}.service"

# ── 6. Disable screen blanking ──────────────────────────────────────────────
echo "▶  Disabling screen blanking..."
if [ -f /etc/lightdm/lightdm.conf ]; then
    if ! grep -q "xserver-command" /etc/lightdm/lightdm.conf; then
        sed -i '/^\[Seat:\*\]/a xserver-command=X -s 0 -dpms' /etc/lightdm/lightdm.conf
    fi
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   Setup complete!                                ║"
echo "║                                                  ║"
echo "║   Start now:     sudo systemctl start $SERVICE_NAME  ║"
echo "║   Auto-boot:     ENABLED                         ║"
echo "║   View logs:     journalctl -u $SERVICE_NAME -f  ║"
echo "║                                                  ║"
echo "║   Reboot to test auto-start:  sudo reboot        ║"
echo "╚══════════════════════════════════════════════════╝"
