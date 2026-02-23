"""
main.py — Entry point for the UltraFiltration control system.
Run: python -m src.main  (from the project root)
"""

import sys
import logging
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import logger, IS_HARDWARE, IS_FULLSCREEN
from src.ui.app import App


def main():
    logger.info("=" * 60)
    logger.info("  UltraFiltration Control System")
    logger.info("  Hardware: %s  |  Fullscreen: %s", IS_HARDWARE, IS_FULLSCREEN)
    logger.info("=" * 60)

    app = App()
    app.run()


if __name__ == "__main__":
    main()
