"""
manual_frame.py — Direct valve toggle with touch-friendly card controls.
Each card is the button — tap anywhere on it to toggle.
"""

import tkinter as tk
from tkinter import ttk

from src.config import VALVE_LABELS
from src.ui.theme import Colors, Fonts
from src.ui.widgets import LEDIndicator


class ValveCard(tk.Canvas):
    """A rounded, touch-friendly card that acts as a toggle button."""

    CORNER_RADIUS = 18
    WIDTH = 105
    HEIGHT = 130

    def __init__(self, parent, channel_id: int, on_toggle, **kwargs):
        super().__init__(
            parent, width=self.WIDTH, height=self.HEIGHT,
            bg=Colors.BG_DARK, highlightthickness=0, **kwargs
        )
        self._cid = channel_id
        self._is_on = False
        self._on_toggle = on_toggle

        # Draw rounded rectangle background
        self._bg_rect = self._rounded_rect(
            4, 4, self.WIDTH - 4, self.HEIGHT - 4,
            self.CORNER_RADIUS, fill=Colors.BG_PANEL, outline=Colors.CARD_BORDER, width=2
        )

        # LED dot
        cx = self.WIDTH // 2
        dot_y = 32
        dot_r = 10
        self._glow = self.create_oval(
            cx - dot_r - 4, dot_y - dot_r - 4,
            cx + dot_r + 4, dot_y + dot_r + 4,
            fill=Colors.BG_PANEL, outline="", width=0
        )
        self._dot = self.create_oval(
            cx - dot_r, dot_y - dot_r,
            cx + dot_r, dot_y + dot_r,
            fill=Colors.OFF, outline="#662222", width=2
        )

        # Label
        self._label = self.create_text(
            cx, 68, text=VALVE_LABELS[channel_id],
            fill=Colors.TEXT_PRIMARY, font=Fonts.BODY_BOLD, anchor="center"
        )

        # Status text
        self._status = self.create_text(
            cx, 100, text="OFF",
            fill=Colors.OFF, font=("Segoe UI", 12, "bold"), anchor="center"
        )

        # Make clickable
        self.bind("<Button-1>", lambda e: self._on_toggle(self._cid))
        self.config(cursor="hand2")

    def _rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle on the canvas."""
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2, y1, x2, y1 + r,
            x2, y2 - r,
            x2, y2, x2 - r, y2,
            x1 + r, y2,
            x1, y2, x1, y2 - r,
            x1, y1 + r,
            x1, y1, x1 + r, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def set_state(self, is_on: bool):
        self._is_on = is_on
        if is_on:
            self.itemconfig(self._bg_rect, fill="#0a3d2a", outline=Colors.ON)
            self.itemconfig(self._dot, fill=Colors.ON, outline="#00cc66")
            self.itemconfig(self._glow, fill="#003322")
            self.itemconfig(self._status, text="ON", fill=Colors.ON)
        else:
            self.itemconfig(self._bg_rect, fill=Colors.BG_PANEL, outline=Colors.CARD_BORDER)
            self.itemconfig(self._dot, fill=Colors.OFF, outline="#662222")
            self.itemconfig(self._glow, fill=Colors.BG_PANEL)
            self.itemconfig(self._status, text="OFF", fill=Colors.OFF)


class ManualFrame(ttk.Frame):
    """Manual control — toggle individual valves/pumps with visual feedback."""

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app
        self._cards: dict[int, ValveCard] = {}
        self._locked = False
        self._build()

    def _build(self):
        # Title
        ttk.Label(
            self, text="Manual Valve Control", style="Heading.TLabel"
        ).pack(pady=(15, 5))

        ttk.Label(
            self, text="Tap a card to toggle ON / OFF",
            style="Muted.TLabel"
        ).pack(pady=(0, 15))

        # ── Valve grid ───────────────────────────────────────────────
        grid_frame = ttk.Frame(self, style="TFrame")
        grid_frame.pack(expand=True)

        # Row 1: Valves 1–4
        row1 = ttk.Frame(grid_frame, style="TFrame")
        row1.pack(pady=8)
        for cid in [1, 2, 3, 4]:
            card = ValveCard(row1, cid, self._toggle)
            card.pack(side="left", padx=6)
            self._cards[cid] = card

        # Row 2: Valve 5, Pump 1, Pump 2
        row2 = ttk.Frame(grid_frame, style="TFrame")
        row2.pack(pady=8)
        for cid in [5, 6, 7]:
            card = ValveCard(row2, cid, self._toggle)
            card.pack(side="left", padx=6)
            self._cards[cid] = card

        # ── Countdown label ──────────────────────────────────────────
        self._countdown_label = ttk.Label(
            self, text="", style="Status.TLabel",
            font=Fonts.HEADING, foreground=Colors.TRANSITION
        )
        self._countdown_label.pack(pady=(5, 5))
        self._countdown_job = None

    def _toggle(self, channel_id: int):
        if self._locked:
            return
        is_on = self.app.gpio.toggle(channel_id)
        self._cards[channel_id].set_state(is_on)

    def go_back(self):
        """Safely close all valves with countdown, then navigate back."""
        self._locked = True
        # Turn off pumps first
        self.app.gpio.turn_off(6)
        self.app.gpio.turn_off(7)
        self._cards[6].set_state(False)
        self._cards[7].set_state(False)

        self._run_countdown(5)

    def _run_countdown(self, remaining: int):
        if remaining <= 0:
            for cid in [1, 2, 3, 4, 5]:
                self.app.gpio.turn_off(cid)
                self._cards[cid].set_state(False)
            self._countdown_label.config(text="")
            self._locked = False
            self.app.show_frame("main")
            return
        self._countdown_label.config(
            text=f"Closing valves in {remaining}s...",
            foreground=Colors.TRANSITION
        )
        self._countdown_job = self.after(1000, self._run_countdown, remaining - 1)

    def on_show(self):
        self.app.topbar.set_subtitle("Manual Control")
        # Sync card states with actual GPIO
        for cid in self._cards:
            self._cards[cid].set_state(self.app.gpio.is_on(cid))
