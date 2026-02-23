# UltraFiltration Control System

A professional, touch-friendly control system for UltraFiltration water processing, built with Python and Tkinter.

![UI Preview](docs/ui_preview.png)

## Features
- **Touch-Optimized UI**: Large buttons, rounded cards, and smooth animations designed for 7" Raspberry Pi touchscreens (800x480).
- **Manual Control**: Direct toggle for individual valves and pumps with real-time status feedback.
- **Automated Cycles**: One-touch automated processes (Fast Rinse, Service, Back Wash, Forward Wash) with precise timing and safety interlocks.
- **Safe Shutdown**: Intelligent stopping sequence that turns off pumps before closing valves to prevent water hammer.
- **Themed Design**: Sleek dark industrial theme with custom modal dialogs and rounded progress bars.
- **Hardware Abstraction**: Dual-mode support (Real GPIO for Pi, Mock GPIO for development on PC/Mac).

## Project Structure
```text
UltraFiltration/
├── src/
│   ├── hardware/       # GPIO and Mock controllers
│   ├── processes/      # Automated cycle logic
│   ├── ui/             # Tkinter frames and themed widgets
│   ├── config.py       # Configuration and pin mapping
│   └── main.py         # Application entry point
├── docs/               # Documentation and diagrams
├── timings.json        # Adjustable process durations
└── .env                # Environment configuration
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/P0rtalPirate/ultraFiltrationSystem.git
   cd ultraFiltrationSystem
   ```

2. **Install dependencies**:
   ```bash
   pip install python-dotenv RPi.GPIO
   ```
   *Note: `RPi.GPIO` is only needed on the Raspberry Pi.*

3. **Configure the system**:
   Create a `.env` file or use the defaults in `src/config.py`.

4. **Run the application**:
   ```bash
   python -m src.main
   ```

## Hardware Setup
See [HARDWARE.md](HARDWARE.md) for detailed wiring diagrams and GPIO pin mappings.

## License
MIT
