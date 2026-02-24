# Professional Deployment: Compilation and OS Branding

This guide details the strategy for creating a professional, protected, and branded "appliance" experience on the Raspberry Pi.

## 1. Operating System Recommendation
**Recommended OS:** `Raspberry Pi OS Lite (64-bit)`

Why Lite?
- **Speed**: Boots significantly faster than the Desktop version.
- **Resource Usage**: Lower RAM/CPU overhead (no background desktop tasks).
- **Stability**: Minimal software means fewer updates and potential points of failure.

### Minimal GUI Setup
Since the app uses Tkinter, we need a GUI layer. Instead of a full desktop, the installer will set up a "Kiosk" environment:
- **X11**: The fundamental window system.
- **Openbox**: A super lightweight window manager used to launch just our app in fullscreen.

## 2. Branded Bootup (Splash Screen)
To hide the Pi boot messages and show your company logo:
1. **Plymouth**: We use this system tool to display a static image during the entire boot process.
2. **Setup**:
   - The installer will copy your logo to `/usr/share/plymouth/themes/`.
   - It will modify `/boot/cmdline.txt` to add `quiet splash logo.nologo`.
   - This hides all the "technical" text, showing only your logo from power-on until the app starts.

## 3. Nuitka Compilation & Protection
The installer will automate the transformation from source code to binary:
1. **Download**: Clones the repo.
2. **Compile**: Runs `nuitka --follow-imports --standalone --onefile src/main.py`.
3. **Outcome**: Creates a machine-code file `ultra-filt`.
4. **Cleanup**: Deletes all `.py` files and `.git` project history.
5. **Persistence**: Moves the binary to `/usr/local/bin/` so it is treated as a system command.

## 4. Single-Command Installer Logic
The updated `install.sh` will perform these steps in order:
1. **System Prep**: Install `python3-tk`, `xserver-xorg`, `openbox`, `plymouth`.
2. **Theme Prep**: Install custom Splash Screen (Company Logo).
3. **Build Phase**: Install Nuitka, compile code, and verify the binary.
4. **Wipe Phase**: Securely delete all source code.
5. **Boot Setup**: Configure `autostart` for Openbox to launch the binary in fullscreen immediately.

---

### Comparison: Standard vs. Branded
| Feature | Standard (Current) | Professional (Target) |
| :--- | :--- | :--- |
| **Boot Style** | Pi Logo + Linux Text | **Company Logo (Quiet Boot)** |
| **Code Security** | Readable `.py` files | **Encrypted Binary (C++)** |
| **Performance** | Desktop OS (~45s boot) | **Lite OS (~20s boot)** |
| **UX** | Main Desktop is visible | **Only the App is visible** |

> [!TIP]
> To support this, you should place your company logo (PNG format) in a `branding/` folder in the repository. The installer will then handle the rest.
