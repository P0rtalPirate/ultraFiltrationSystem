# Raspberry Pi Boot Splash Setup Guide 🚀

To replace the default Raspberry Pi boot screen with your system diagram, follow these steps. This guide is specifically for **Raspberry Pi OS Lite (64-bit)**.

## 1. Convert SVG to PNG
Raspberry Pi boot tools (like Plymouth) require a static image (PNG). You can convert the `boot_splash.svg` I created into a high-quality PNG directly on your Pi:

```bash
# Install conversion tool
sudo apt-get update
sudo apt-get install -y inkscape

# Convert SVG to 1920x1080 PNG
inkscape --export-type=png --export-filename=splash.png --export-width=1920 --export-height=1080 branding/boot_splash.svg
```

## 2. Install Plymouth
Plymouth is the software that manages the splash screen during boot.

```bash
sudo apt-get install -y plymouth plymouth-themes
```

## 3. Create a Custom Theme
1. Create a folder for your theme:
   ```bash
   sudo mkdir -p /usr/share/plymouth/themes/ultrafiltration
   ```
2. Move your `splash.png` into that folder:
   ```bash
   sudo cp splash.png /usr/share/plymouth/themes/ultrafiltration/
   ```
3. Create the theme configuration file:
   ```bash
   sudo nano /usr/share/plymouth/themes/ultrafiltration/ultrafiltration.plymouth
   ```
4. Paste the following:
   ```ini
   [Plymouth Theme]
   Name=UltraFiltration
   Description=System Diagram Splash
   ModuleName=script

   [script]
   ImageDir=/usr/share/plymouth/themes/ultrafiltration
   ScriptFile=/usr/share/plymouth/themes/ultrafiltration/ultrafiltration.script
   ```

## 4. Set as Default & Update
```bash
# Set theme
sudo plymouth-set-default-theme ultrafiltration

# Update initramfs (crucial)
sudo update-initramfs -u
```

## 5. Enable Splash in Boot Config
Edit `/boot/cmdline.txt` (or `/boot/firmware/cmdline.txt` on newer OS):
```bash
sudo nano /boot/firmware/cmdline.txt
```
Add these parameters to the end of the line (keep it all on ONE line):
`quiet splash plymouth.ignore-serial-consoles logo.nologo vt.global_cursor_default=0`

## 6. Reboot
```bash
sudo reboot
```

---
> [!TIP]
> If you don't want to install Plymouth, you can also use a simpler tool called `fbi` (FrameBuffer Imageviewer) by creating a systemd service that runs early in the boot process.
