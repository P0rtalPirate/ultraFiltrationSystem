"""
config.py — Central configuration for the UltraFiltration project.
Loads .env and exposes all settings + GPIO pin mapping.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env from the project root ──────────────────────────────────────────
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

# ── Feature Flags ────────────────────────────────────────────────────────────
IS_HARDWARE = os.getenv("UF_HARDWARE_CONNECTED", "true").lower() == "true"
IS_FULLSCREEN = os.getenv("UF_DISPLAY_FULLSCREEN", "true").lower() == "true"
SHOW_CURSOR = os.getenv("UF_SHOW_CURSOR", "true").lower() == "true"
LOG_LEVEL = os.getenv("UF_LOG_LEVEL", "INFO").upper()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("UltraFiltration")

# ── Display ──────────────────────────────────────────────────────────────────
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

# ── GPIO Pin Map ─────────────────────────────────────────────────────────────
# Valve/Pump logical ID → BCM pin number
PIN_MAP = {
    1: 27,   # Valve 1
    2: 3,    # Valve 2
    3: 22,   # Valve 3
    4: 18,   # Valve 4
    5: 23,   # Valve 5
    6: 24,   # Pump 1
    7: 25,   # Pump 2
}

VALVE_LABELS = {
    1: "Valve 1",
    2: "Valve 2",
    3: "Valve 3",
    4: "Valve 4",
    5: "Valve 5",
    6: "Pump 1",
    7: "Pump 2",
}

# Total number of GPIO channels we manage
ALL_CHANNEL_IDS = list(PIN_MAP.keys())

# ── Default Process Timings (milliseconds) ───────────────────────────────────
DEFAULT_TIMINGS = {
    "fast_rinse":   60_000,
    "service":      3_600_000,
    "back_wash":    60_000,
    "forward_wash": 60_000,
}

# Delay before pump engages / disengages (ms)
PUMP_ENGAGE_DELAY = 5_000
VALVE_CLOSE_DELAY = 5_000

# ── GPIO Backend Selection ───────────────────────────────────────────────────
def get_gpio():
    """Return the appropriate GPIO module based on configuration."""
    if IS_HARDWARE:
        from src.hardware.gpio_controller import GPIOController
        return GPIOController()
    else:
        from src.hardware.mock_gpio import MockGPIO
        return MockGPIO()


logger.info("Config loaded  |  hardware=%s  fullscreen=%s  log=%s",
            IS_HARDWARE, IS_FULLSCREEN, LOG_LEVEL)
