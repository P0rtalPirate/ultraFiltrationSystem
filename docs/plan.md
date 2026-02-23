# UltraFiltration Project — Improvement Roadmap

## Current State Summary

The project is a single-file Tkinter application (`ValveInterface.py`, ~937 lines) that controls 5 solenoid valves and 2 pumps via Raspberry Pi GPIO. It has:
- **Main Frame** — MANUAL / AUTO / EXIT buttons
- **Manual Frame** — Direct toggle of 7 GPIO channels (Valve 1-5, Pump 1-2)
- **Auto Frame** — Automated cycle: Fast Rinse → Service → Back Wash → Forward Wash → loop
- **Select Frame** — Sub-menu for AUTO, Manual Step Control, and Edit Time
- **Manual Steps Frame** — Start/stop individual processes
- **Edit Frame** — On-screen numpad to adjust process durations (HH:MM:SS)

Timer durations are stored in `.p` pickle files for persistence.

---

## Phase 1 — Hardware Abstraction & Dev Mode

### Goal
Allow the entire UI to run **without a Raspberry Pi** by mocking GPIO calls.

### Details
| Item | Description |
|---|---|
| `.env` file | Add `UF_HARDWARE_CONNECTED=false` to disable real GPIO |
| Mock GPIO module | When `UF_HARDWARE_CONNECTED=false`, replace `RPi.GPIO` with a stub that logs calls to console |
| `python-dotenv` | Load `.env` at startup via `load_dotenv()` |

### Benefit
- Develop and test the UI on **any** Windows/Mac/Linux machine
- Deploy to Pi by setting `UF_HARDWARE_CONNECTED=true` (or removing the variable)

---

## Phase 2 — Code Quality & Architecture

### Modularization
Break the monolith into clean modules:

```
oldCode/
├── main.py              # Entry point
├── config.py            # .env loading, constants, GPIO pin map
├── hardware/
│   ├── __init__.py
│   ├── gpio_controller.py   # Real GPIO wrapper
│   └── mock_gpio.py         # Simulated GPIO (logs to console)
├── processes/
│   ├── __init__.py
│   └── process_manager.py   # Fast Rinse, Service, Back/Forward Wash
├── ui/
│   ├── __init__.py
│   ├── app.py               # Tk root, frame management
│   ├── main_frame.py
│   ├── manual_frame.py
│   ├── auto_frame.py
│   ├── select_frame.py
│   ├── manual_steps_frame.py
│   ├── edit_frame.py
│   └── widgets.py           # Reusable styled widgets
├── .env
├── requirements.txt
└── setup.sh
```

### Other Improvements
- Replace `print()` with Python `logging` module
- Replace pickle files with a JSON config for readability
- Add proper error handling around GPIO operations
- Use classes instead of global variables for state management

---

## Phase 3 — UI / UX Improvements

### Current Pain Points
1. **Plain default Tkinter look** — grey system widgets, no visual hierarchy
2. **Duplicated clock code** — 5 identical `time()` functions for each frame
3. **Hard-coded positioning** — magic numbers for `relx`, `rely`, `vmargin` etc.
4. **No status feedback** — valve states only shown by button color (red/green)
5. **Small touch targets** — some buttons may be hard to tap on a touchscreen
6. **No visual flow diagram** — operator can't see the *system* (which valve feeds where)

### Planned UI Improvements

| Area | Current | Improved |
|---|---|---|
| **Theme** | Default grey Tkinter | Dark industrial theme with `ttk.Style` — dark background, high-contrast accent colors, rounded buttons |
| **Color Scheme** | Red/Green/Yellow only | Consistent palette: dark slate background, neon-green for ON, soft red for OFF, amber for transitioning, blue for informational |
| **Fonts** | System default `calibri` | Modern monospace for values (e.g. `JetBrains Mono`), clean sans-serif for labels |
| **Valve Indicators** | Colored buttons | LED-style circular indicators with glow effect + label |
| **Process Status** | Plain text label | Progress bar or animated indicator showing current step in the cycle |
| **Clock** | 5 duplicate label/functions | Single shared clock widget placed on a persistent top bar across all frames |
| **Navigation** | Small "Back" button at bottom | Persistent bottom navigation bar with icons and larger touch-friendly buttons (min 48×48 px) |
| **Touch UX** | Standard button sizes | All interactive elements ≥ 60px tall for reliable touch input on a 7" screen |
| **Edit Frame** | On-screen numpad with tiny buttons | Larger numpad with responsive visual feedback on press, plus +/- stepper buttons as alternative |
| **System Diagram** | None | A simple pipe/valve diagram on the main or auto frame showing which valves and pumps are active in real time |
| **Transitions** | Instant frame switch | Smooth fade or slide transitions between frames |
| **Countdown Timer** | Small text in corner | Full-width animated countdown bar with seconds display |

### Implementation Approach
- Use `tkinter.ttk` with custom `Style` for consistent theming
- Use `Canvas` for LED indicators and system diagram
- Create a reusable `StyledButton` widget class
- Use a persistent `TopBar` (clock + title) and `BottomBar` (navigation) shared across frames

---

## Phase 4 — Deployment & Automation

### Setup Script (`setup.sh`)
```
- Install system packages: python3-tk, python3-pip, python3-pil, python3-pil.imagetk
- Install pip packages: python-dotenv, RPi.GPIO (on Pi only)
- Set X11/Wayland for kiosk mode
- Create .env with UF_HARDWARE_CONNECTED=true
- Install systemd service
- Enable service for auto-start
```

### Systemd Service (`ultrafiltration.service`)
- Start the app after graphical target is reached
- Restart on crash (`Restart=on-failure`)
- Run as the `pi` user (not root, but with GPIO group access)

### Kiosk Mode
- Disable screen blanking
- Hide cursor (already done in code: `cursor = "none"`)
- Auto-login to desktop and launch app fullscreen

---

## Phase 5 — Future Enhancements (Out of Scope for Now)
- Web-based dashboard alongside Tkinter (Flask/FastAPI)
- Remote monitoring via MQTT
- Data logging (cycle counts, runtime hours)
- OTA update mechanism
