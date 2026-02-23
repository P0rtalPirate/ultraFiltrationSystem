"""
manual_steps_frame.py — Run individual processes with compact rounded cards.
"""

import tkinter as tk
from tkinter import ttk

from src.ui.theme import Colors, Fonts
from src.ui.widgets import LEDIndicator, show_info, show_warning
from src.config import VALVE_LABELS


class ProcessCard(tk.Canvas):
    """Compact rounded card for a filtration process."""

    R = 12
    W = 400
    H = 55

    def __init__(self, parent, proc_id: str, label: str, icon: str,
                 on_click, **kwargs):
        super().__init__(
            parent, width=self.W, height=self.H,
            bg=Colors.BG_DARK, highlightthickness=0, **kwargs
        )
        self._proc_id = proc_id
        self._state = "idle"  # idle, running, stopping

        # Rounded background
        self._bg = self._round_rect(
            3, 3, self.W - 3, self.H - 3, self.R,
            fill=Colors.BG_SURFACE, outline=Colors.CARD_BORDER, width=2
        )

        # Icon tag
        self._icon = self.create_text(
            40, self.H // 2, text=f"[{icon}]",
            fill=Colors.TEXT_ACCENT, font=("Consolas", 12, "bold")
        )

        # Label
        self._label = self.create_text(
            90, self.H // 2, text=label, anchor="w",
            fill=Colors.TEXT_PRIMARY, font=Fonts.BUTTON
        )

        # Status text (right side)
        self._status = self.create_text(
            self.W - 20, self.H // 2, text="", anchor="e",
            fill=Colors.TEXT_MUTED, font=Fonts.LABEL_SMALL
        )

        self.bind("<Button-1>", lambda e: on_click(self._proc_id))
        self.config(cursor="hand2")

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
            x2,y2-r, x2,y2, x2-r,y2,
            x1+r,y2, x1,y2, x1,y2-r,
            x1,y1+r, x1,y1, x1+r,y1,
        ]
        return self.create_polygon(pts, smooth=True, **kw)

    def set_idle(self):
        self._state = "idle"
        self.itemconfig(self._bg, fill=Colors.BG_SURFACE, outline=Colors.CARD_BORDER)
        self.itemconfig(self._status, text="", fill=Colors.TEXT_MUTED)

    def set_running(self):
        self._state = "running"
        self.itemconfig(self._bg, fill="#0a3d2a", outline=Colors.ON)
        self.itemconfig(self._status, text="RUNNING", fill=Colors.ON)

    def set_starting(self):
        self._state = "starting"
        self.itemconfig(self._bg, fill="#3d3000", outline=Colors.TRANSITION)
        self.itemconfig(self._status, text="STARTING...", fill=Colors.TRANSITION)

    def set_stopping(self):
        self._state = "stopping"
        self.itemconfig(self._bg, fill="#3d1500", outline=Colors.TRANSITION)
        self.itemconfig(self._status, text="STOPPING...", fill=Colors.TRANSITION)


class ManualStepsFrame(ttk.Frame):
    """Manual step control — start/stop individual filtration processes."""

    PROCESSES = [
        ("fast_rinse",   "Fast Rinse",   "FR"),
        ("service",      "Service",      "SV"),
        ("back_wash",    "Back Wash",    "BW"),
        ("forward_wash", "Forward Wash", "FW"),
    ]

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app
        self._current: str | None = None
        self._locked = False
        self._cards: dict[str, ProcessCard] = {}
        self._leds: dict[int, LEDIndicator] = {}
        self._build()

    def _build(self):
        # ── Status label ─────────────────────────────────────────────
        self._status = ttk.Label(
            self, text="Select a process to start",
            style="Status.TLabel", font=Fonts.HEADING
        )
        self._status.pack(pady=(8, 5))

        # ── Content area ─────────────────────────────────────────────
        content = ttk.Frame(self, style="TFrame")
        content.pack(expand=True, fill="both", padx=10)

        # Left: process cards
        left = ttk.Frame(content, style="TFrame")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        for proc_id, label, icon in self.PROCESSES:
            card = ProcessCard(left, proc_id, label, icon, self._toggle_process)
            card.pack(pady=3)
            self._cards[proc_id] = card

        # Right: valve status indicators (compact)
        right = ttk.Frame(content, style="TFrame")
        right.pack(side="right", fill="y", padx=(8, 0))

        ttk.Label(right, text="Valves", style="Heading.TLabel").pack(pady=(0, 4))
        for cid in range(1, 8):
            led = LEDIndicator(right, label_text=VALVE_LABELS[cid], size=14)
            led.pack(anchor="w", pady=1)
            self._leds[cid] = led

    def _toggle_process(self, proc_id: str):
        if self._locked:
            return

        if self._current is None:
            self._start_process(proc_id)
        elif self._current == proc_id:
            self._stop_process(proc_id)
        else:
            show_info(
                self.app.root, "Process Running",
                "Please stop the current process first."
            )

    def _start_process(self, proc_id: str):
        self._current = proc_id
        self._locked = True
        self._cards[proc_id].set_starting()
        display = proc_id.replace("_", " ").title()
        self._status.config(text=f"Starting: {display}", foreground=Colors.TRANSITION)

        pm = self.app.process_manager
        pm.on_valve_change = self._on_valve_change
        pm.on_process_start = self._on_started
        pm.start_single_process(proc_id)

    def _on_started(self, name: str, duration_ms: int = 0):
        display = name.replace("_", " ").title()
        self._status.config(text=f">>  {display} — Running", foreground=Colors.ON)
        if name in self._cards:
            self._cards[name].set_running()
        self._locked = False

    def _stop_process(self, proc_id: str):
        self._locked = True
        self._cards[proc_id].set_stopping()
        display = proc_id.replace("_", " ").title()

        # Start visible countdown
        self._stop_remaining = 5
        self._stopping_proc = proc_id
        self._stopping_display = display
        self._tick_stop()

        self.app.process_manager.stop_current_process(callback=self._on_fully_stopped)

    def _tick_stop(self):
        if self._stop_remaining <= 0:
            return
        self._status.config(
            text=f"Stopping: {self._stopping_display}...  {self._stop_remaining}s",
            foreground=Colors.TRANSITION
        )
        self._stop_remaining -= 1
        self._stop_job = self.after(1000, self._tick_stop)

    def _on_fully_stopped(self):
        if hasattr(self, "_stop_job"):
            try:
                self.after_cancel(self._stop_job)
            except Exception:
                pass
        self._status.config(text="Select a process to start",
                            foreground=Colors.TEXT_PRIMARY)
        if hasattr(self, "_stopping_proc") and self._stopping_proc in self._cards:
            self._cards[self._stopping_proc].set_idle()
        for led in self._leds.values():
            led.set_state(False)
        self._current = None
        self._locked = False

    def _on_valve_change(self, channel_id: int, is_on: bool):
        if channel_id in self._leds:
            self._leds[channel_id].set_state(is_on)

    def go_back(self):
        if self._locked:
            show_warning(self.app.root, "Wait", "Please wait for the process to finish.")
            return

        if self._current:
            self._stop_process(self._current)
            self.after(6000, lambda: self.app.show_frame("select"))
        else:
            self.app.show_frame("select")

    def on_show(self):
        self.app.topbar.set_subtitle("Step Control")
        for card in self._cards.values():
            card.set_idle()
        self._status.config(text="Select a process to start",
                            foreground=Colors.TEXT_PRIMARY)
