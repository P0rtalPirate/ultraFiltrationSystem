#!/bin/bash
# setup_splash.sh — Install system_diagram.png as the Pi Boot Splash
# Run on the Raspberry Pi:  bash scripts/setup_splash.sh
# Tested on Raspberry Pi OS Lite 64-bit

set -e

INSTALL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PNG_SRC="$INSTALL_DIR/branding/system_diagram.png"
THEME_DIR="/usr/share/plymouth/themes/ultrafiltration"

echo "🎨 UltraFiltration — Boot Splash Setup"
echo "======================================="

# ── Verify image exists ────────────────────────────────────────────────────
if [ ! -f "$PNG_SRC" ]; then
    echo "❌ ERROR: branding/system_diagram.png not found at $PNG_SRC"
    exit 1
fi
echo "   ✔  Found: $PNG_SRC"

# ── Install Plymouth ────────────────────────────────────────────────────────
echo "📦 Installing Plymouth..."
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends plymouth plymouth-themes
echo "   ✔  Plymouth installed."

# ── Create theme directory ─────────────────────────────────────────────────
sudo mkdir -p "$THEME_DIR"
sudo cp "$PNG_SRC" "$THEME_DIR/splash.png"
echo "   ✔  Image copied to Plymouth theme directory."

# ── Write Plymouth script (auto-scales image to screen) ───────────────────
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
echo "   ✔  Plymouth render script created."

# ── Write theme .plymouth descriptor ─────────────────────────────────────
sudo tee "$THEME_DIR/ultrafiltration.plymouth" > /dev/null <<'PLYCONF'
[Plymouth Theme]
Name=UltraFiltration
Description=Raj Entreprices System Diagram Boot Splash
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/ultrafiltration
ScriptFile=/usr/share/plymouth/themes/ultrafiltration/ultrafiltration.script
PLYCONF
echo "   ✔  Plymouth theme descriptor created."

# ── Set as default theme ───────────────────────────────────────────────────
sudo plymouth-set-default-theme ultrafiltration
echo "   ✔  Theme set as default."

# ── Patch cmdline.txt to hide boot logs ───────────────────────────────────
echo "📝 Patching boot command line to hide console logs..."
CMDLINE="/boot/firmware/cmdline.txt"
if [ ! -f "$CMDLINE" ]; then CMDLINE="/boot/cmdline.txt"; fi

if [ -f "$CMDLINE" ]; then
    if grep -q "quiet" "$CMDLINE"; then
        echo "   ⚠️  'quiet' already present in $CMDLINE — skipping cmdline patch."
    else
        sudo cp "$CMDLINE" "${CMDLINE}.bak"   # backup first
        sudo sed -i 's/$/ quiet splash plymouth.ignore-serial-consoles logo.nologo vt.global_cursor_default=0/' "$CMDLINE"
        echo "   ✔  Boot flags added. Original backed up to ${CMDLINE}.bak"
    fi
else
    echo "   ⚠️  cmdline.txt not found. Please add these flags manually:"
    echo "       quiet splash plymouth.ignore-serial-consoles logo.nologo vt.global_cursor_default=0"
fi

# ── Regenerate initramfs ────────────────────────────────────────────────────
echo "🔄 Updating initramfs (this takes 30–60 seconds)..."
sudo update-initramfs -u
echo "   ✔  initramfs updated."

echo ""
echo "✅ Boot splash setup complete!"
echo "   Reboot the Pi to see the splash screen:"
echo "   sudo reboot"
