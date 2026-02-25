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

# ── 6. Disable screen blanking (multi-layer) ────────────────────────────────
echo "▶  Disabling screen blanking (all layers)..."

# Layer 1: raspi-config non-interactive (covers DPMS in raspi-config)
raspi-config nonint do_blanking 1 2>/dev/null || true

# Layer 2: lightdm — disable blanking for LightDM-based desktops
if [ -f /etc/lightdm/lightdm.conf ]; then
    if ! grep -q "xserver-command" /etc/lightdm/lightdm.conf; then
        sed -i '/^\[Seat:\*\]/a xserver-command=X -s 0 -dpms' /etc/lightdm/lightdm.conf
    fi
fi

# Layer 3: X session — disable blanking at X level for the running user
XSESSION_FILE="/home/${USER_NAME}/.xsessionrc"
if ! grep -q "xset s off" "$XSESSION_FILE" 2>/dev/null; then
    cat >> "$XSESSION_FILE" <<'XEOF'
# Disable screen blanking and DPMS (added by UltraFiltration setup)
xset s off
xset -dpms
xset s noblank
XEOF
fi
chown "${USER_NAME}:${USER_NAME}" "$XSESSION_FILE" 2>/dev/null || true

# Layer 4: Kernel level — prevent console blank at boot
CMDLINE=/boot/cmdline.txt
if [ -f "$CMDLINE" ] && ! grep -q "consoleblank=0" "$CMDLINE"; then
    sed -i 's/$/ consoleblank=0/' "$CMDLINE"
    echo "   ✔  Added consoleblank=0 to $CMDLINE"
fi

echo "   ✔  Screen blanking fully disabled."

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
