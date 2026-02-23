# Automation Plan: Single-Command Setup

This document outlines how to transform the project so it can be installed and configured for auto-boot on a fresh Raspberry Pi with a single command.

## The Goal
The user should be able to run:
```bash
curl -sSL https://raw.githubusercontent.com/P0rtalPirate/ultraFiltrationSystem/main/scripts/install.sh | bash
```
And have the system automatically:
1. Clone the repo / Install the package.
2. Install system dependencies (`python3-tk`, `python3-pip`, `git`).
3. Set up a Python Virtual Environment.
4. Create a `.env` with default production settings.
5. Register a `systemd` service to start the app on boot.

---

## Required Components

### 1. `pyproject.toml` (or `setup.py`)
To make the project "pip installable", we need a packaging file. This allows libraries to be handled automatically and defines a command (e.g., `ultra-filt`) to launch the app.

### 2. `scripts/install.sh`
A bash script that handles the "heavy lifting" on the Linux side:
- Installs `python3-tk` (required for Tkinter, can't be installed via pip).
- Creates the `/etc/systemd/system/ultrafiltration.service`.
- Enables the service so it starts after the GUI is ready.

### 3. `scripts/ultrafiltration.service`
A template file for the bootup service.
```ini
[Unit]
Description=UltraFiltration Control System
After=graphical.target

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStart=/home/pi/ultraFiltrationSystem/venv/bin/python -m src.main
Restart=always
User=pi

[Install]
WantedBy=graphical.target
```

---

## Implementation Workflow (Next Steps)

1. **Add `pyproject.toml`**: Define dependencies like `python-dotenv`.
2. **Create `scripts/` folder**: Add the installer and service template.
3. **Update `README.md`**: Provide the one-liner installation command.

> [!IMPORTANT]
> Because Tkinter and Systemd require OS-level permissions (`sudo`), a pure `pip install` cannot fully set up the "bootup" part. The bash-bootstrap method is the standard professional way to handle this on Raspberry Pi.
