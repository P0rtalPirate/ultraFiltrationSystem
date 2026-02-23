"""
process_manager.py — Encapsulates the filtration cycle logic.
Independent of UI — communicates via callbacks.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("UltraFiltration.Process")

# ── Timing persistence (JSON instead of pickle) ─────────────────────────────
_TIMINGS_FILE = Path(__file__).resolve().parent.parent.parent / "timings.json"


def load_timings() -> dict:
    """Load saved timings or return defaults."""
    from src.config import DEFAULT_TIMINGS
    if _TIMINGS_FILE.exists():
        try:
            with open(_TIMINGS_FILE, "r") as f:
                saved = json.load(f)
            logger.info("Loaded timings from %s", _TIMINGS_FILE)
            return {**DEFAULT_TIMINGS, **saved}
        except Exception as e:
            logger.warning("Failed to load timings: %s — using defaults", e)
    return dict(DEFAULT_TIMINGS)


def save_timings(timings: dict) -> None:
    """Persist timings to JSON."""
    try:
        with open(_TIMINGS_FILE, "w") as f:
            json.dump(timings, f, indent=2)
        logger.info("Saved timings to %s", _TIMINGS_FILE)
    except Exception as e:
        logger.error("Failed to save timings: %s", e)


class ProcessManager:
    """
    Manages the filtration cycle sequence.
    Uses a Tkinter widget's `.after()` for scheduling — pass in any widget.
    """

    # Process valve/pump configurations
    # Each process: (valves_to_open_first, pump_channel, valves_to_close_at_end)
    PROCESS_CONFIG = {
        "fast_rinse":   {"valves": [2, 3], "pump": 6},
        "service":      {"valves": [1, 5], "pump": 6},
        "back_wash":    {"valves": [3],    "pump": 7},
        "forward_wash": {"valves": [1, 4], "pump": 6, "extra_valve": 5},
    }

    PROCESS_ORDER = ["fast_rinse", "service", "back_wash", "forward_wash"]

    def __init__(self, gpio, scheduler_widget):
        """
        Args:
            gpio: GPIOController or MockGPIO instance.
            scheduler_widget: Any Tkinter widget to call .after() on.
        """
        self.gpio = gpio
        self.widget = scheduler_widget
        self.timings = load_timings()
        self._pending_jobs: list = []
        self._current_process: str | None = None
        self._running = False

        # Callbacks the UI can register
        self.on_process_start = None   # (process_name: str, duration_ms: int) -> None
        self.on_pump_start = None      # (process_name: str, countdown_ms: int) -> None
        self.on_process_end = None     # (process_name: str) -> None
        self.on_valve_change = None    # (channel_id: int, is_on: bool) -> None
        self.on_cycle_complete = None  # () -> None

    # ── Public API ───────────────────────────────────────────────────────

    @property
    def current_process(self) -> str | None:
        return self._current_process

    @property
    def is_running(self) -> bool:
        return self._running

    def start_auto_cycle(self) -> None:
        """Start the full auto cycle from fast_rinse."""
        self._running = True
        self._run_process("fast_rinse", auto_next=True)

    def start_single_process(self, name: str) -> None:
        """Start a single process (manual step control)."""
        if name not in self.PROCESS_CONFIG:
            logger.error("Unknown process: %s", name)
            return
        self._running = True
        self._run_process(name, auto_next=False)

    def stop_current_process(self, callback=None) -> None:
        """Gracefully stop the current process with pump-off delay."""
        self._cancel_all_jobs()
        self._running = False

        if self._current_process:
            cfg = self.PROCESS_CONFIG[self._current_process]
            # Turn off pump first
            self._gpio_off(cfg["pump"])
            # After delay, turn off valves
            self._schedule(5000, lambda: self._close_all_and_notify(callback))
        else:
            if callback:
                callback()

    def stop_immediately(self) -> None:
        """Emergency stop — cancel everything instantly."""
        self._cancel_all_jobs()
        self._running = False
        self.gpio.all_off()
        for cid in range(1, 8):
            self._notify_valve(cid, False)
        self._current_process = None

    def update_timings(self, new_timings: dict) -> None:
        """Update and persist timings."""
        self.timings.update(new_timings)
        save_timings(self.timings)

    def reset_timings(self) -> None:
        """Reset to factory defaults."""
        from src.config import DEFAULT_TIMINGS
        self.timings = dict(DEFAULT_TIMINGS)
        save_timings(self.timings)

    # ── Internal logic ───────────────────────────────────────────────────

    def _run_process(self, name: str, auto_next: bool) -> None:
        """Execute a single named process."""
        self._current_process = name
        cfg = self.PROCESS_CONFIG[name]
        t = self.timings[name]

        logger.info("STARTING: %s  (duration=%dms)", name, t)
        if self.on_process_start:
            self.on_process_start(name, t)

        # 1. Open valves
        for v in cfg["valves"]:
            self._gpio_on(v)

        # 2. After PUMP_ENGAGE_DELAY, start pump
        pump_delay = 5000
        # Countdown duration = process time + valve close delay
        countdown_ms = t + 5000
        if "extra_valve" in cfg:
            countdown_ms = t + 10000

        def _pump_on():
            self._gpio_on(cfg["pump"])
            if self.on_pump_start:
                self.on_pump_start(name, countdown_ms)

        self._schedule(pump_delay, _pump_on)

        # 3. After process duration, stop pump
        self._schedule(pump_delay + t, lambda: self._gpio_off(cfg["pump"]))

        # 4. After close delay, close valves
        close_time = pump_delay + t + 5000
        for v in cfg["valves"]:
            self._schedule(close_time, lambda vid=v: self._gpio_off(vid))

        # Handle forward_wash extra valve (Valve 5 opens at the end)
        if "extra_valve" in cfg:
            ev = cfg["extra_valve"]
            self._schedule(pump_delay + t + 5000, lambda: self._gpio_on(ev))
            self._schedule(pump_delay + t + 10000, lambda: self._gpio_off(ev))
            close_time = pump_delay + t + 10000

        # 5. Notify end and optionally start next
        def finish():
            logger.info("FINISHED: %s", name)
            if self.on_process_end:
                self.on_process_end(name)
            if auto_next and self._running:
                next_name = self._next_process(name)
                self._run_process(next_name, auto_next=True)
            else:
                self._current_process = None
                self._running = False
                if self.on_cycle_complete:
                    self.on_cycle_complete()

        self._schedule(close_time, finish)

    def _next_process(self, current: str) -> str:
        """Get the next process in the cycle (wraps around)."""
        idx = self.PROCESS_ORDER.index(current)
        # After forward_wash, go back to service (skip fast_rinse on repeat)
        if current == "forward_wash":
            return "service"
        return self.PROCESS_ORDER[(idx + 1) % len(self.PROCESS_ORDER)]

    def _gpio_on(self, channel_id: int) -> None:
        self.gpio.turn_on(channel_id)
        self._notify_valve(channel_id, True)

    def _gpio_off(self, channel_id: int) -> None:
        self.gpio.turn_off(channel_id)
        self._notify_valve(channel_id, False)

    def _notify_valve(self, channel_id: int, is_on: bool) -> None:
        if self.on_valve_change:
            self.on_valve_change(channel_id, is_on)

    def _close_all_and_notify(self, callback=None) -> None:
        """Close all valves and notify."""
        self.gpio.all_off()
        for cid in range(1, 8):
            self._notify_valve(cid, False)
        old = self._current_process
        self._current_process = None
        if self.on_process_end and old:
            self.on_process_end(old)
        if callback:
            callback()

    # ── Scheduling helpers ───────────────────────────────────────────────

    def _schedule(self, delay_ms: int, func) -> None:
        job_id = self.widget.after(delay_ms, func)
        self._pending_jobs.append(job_id)

    def _cancel_all_jobs(self) -> None:
        for job_id in self._pending_jobs:
            try:
                self.widget.after_cancel(job_id)
            except Exception:
                pass
        self._pending_jobs.clear()
