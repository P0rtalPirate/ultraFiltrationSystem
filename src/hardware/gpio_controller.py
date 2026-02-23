"""
gpio_controller.py — Real RPi.GPIO wrapper for production on Raspberry Pi.
"""

import logging
import RPi.GPIO as GPIO
from src.config import PIN_MAP

logger = logging.getLogger("UltraFiltration.GPIO")


class GPIOController:
    """Thin wrapper around RPi.GPIO with a clean interface."""

    def __init__(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        # Initialize all mapped pins as OUTPUT, HIGH (relays OFF)
        for pin in PIN_MAP.values():
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
        logger.info("GPIOController initialized  |  pins=%s", list(PIN_MAP.values()))

    # ── Single-channel operations ────────────────────────────────────────

    def turn_on(self, channel_id: int) -> None:
        """Activate a valve/pump (relay LOW = ON)."""
        pin = PIN_MAP[channel_id]
        GPIO.output(pin, GPIO.LOW)
        logger.debug("ON   channel=%d  pin=%d", channel_id, pin)

    def turn_off(self, channel_id: int) -> None:
        """Deactivate a valve/pump (relay HIGH = OFF)."""
        pin = PIN_MAP[channel_id]
        GPIO.output(pin, GPIO.HIGH)
        logger.debug("OFF  channel=%d  pin=%d", channel_id, pin)

    def is_on(self, channel_id: int) -> bool:
        """Check if a channel is currently active (LOW = on)."""
        pin = PIN_MAP[channel_id]
        return GPIO.input(pin) == GPIO.LOW

    def toggle(self, channel_id: int) -> bool:
        """Toggle a channel. Returns the new state (True = ON)."""
        if self.is_on(channel_id):
            self.turn_off(channel_id)
            return False
        else:
            self.turn_on(channel_id)
            return True

    # ── Bulk operations ──────────────────────────────────────────────────

    def all_off(self) -> None:
        """Turn off all channels (safe state)."""
        for cid in PIN_MAP:
            self.turn_off(cid)
        logger.info("ALL channels OFF")

    def shutdown(self) -> None:
        """Turn everything off. Called on app exit."""
        self.all_off()
        logger.info("GPIO shutdown complete")
