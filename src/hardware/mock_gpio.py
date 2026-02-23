"""
mock_gpio.py — Simulated GPIO for development without hardware.
Logs all calls so you can verify logic on Windows/Mac/Linux.
"""

import logging
from src.config import PIN_MAP

logger = logging.getLogger("UltraFiltration.MockGPIO")


class MockGPIO:
    """Drop-in replacement for GPIOController that only logs."""

    def __init__(self):
        # Track simulated pin states: True = ON, False = OFF
        self._states: dict[int, bool] = {cid: False for cid in PIN_MAP}
        logger.info("MockGPIO initialized  (simulation mode — no real hardware)")

    def turn_on(self, channel_id: int) -> None:
        self._states[channel_id] = True
        logger.info("🟢  MOCK ON   channel=%d  (%s)", channel_id,
                     self._label(channel_id))

    def turn_off(self, channel_id: int) -> None:
        self._states[channel_id] = False
        logger.info("🔴  MOCK OFF  channel=%d  (%s)", channel_id,
                     self._label(channel_id))

    def is_on(self, channel_id: int) -> bool:
        return self._states.get(channel_id, False)

    def toggle(self, channel_id: int) -> bool:
        if self.is_on(channel_id):
            self.turn_off(channel_id)
            return False
        else:
            self.turn_on(channel_id)
            return True

    def all_off(self) -> None:
        for cid in PIN_MAP:
            self.turn_off(cid)
        logger.info("MOCK — ALL channels OFF")

    def shutdown(self) -> None:
        self.all_off()
        logger.info("MOCK — shutdown complete")

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _label(channel_id: int) -> str:
        from src.config import VALVE_LABELS
        return VALVE_LABELS.get(channel_id, f"Channel {channel_id}")
