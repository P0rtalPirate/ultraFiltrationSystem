"""
auto_frame.py — Automated cycle display with rounded cards and progress bar.
Countdown starts when pump engages, ends when valves close.
Between processes the bar fills back up.
"""

import tkinter as tk
from tkinter import ttk

from src.config import VALVE_LABELS
from src.ui.theme import Colors, Fonts


# ─────────────────────────────────────────────────────────────────────────────
#  Rounded Valve Indicator (read-only)
# ─────────────────────────────────────────────────────────────────────────────
class IndicatorCard(tk.Canvas):
    """Compact rounded card showing valve ON/OFF state."""

    R = 14
    W = 130
    H = 50

    def __init__(self, parent, channel_id: int, **kwargs):
        super().__init__(
            parent, width=self.W, height=self.H,
            bg=Colors.BG_DARK, highlightthickness=0, **kwargs
        )
        self._cid = channel_id

        self._bg = self._round_rect(
            3, 3, self.W - 3, self.H - 3, self.R,
            fill=Colors.BG_PANEL, outline=Colors.CARD_BORDER, width=2
        )

        dot_r = 8
        dot_cx, dot_cy = 28, self.H // 2
        self._dot = self.create_oval(
            dot_cx - dot_r, dot_cy - dot_r,
            dot_cx + dot_r, dot_cy + dot_r,
            fill=Colors.OFF, outline="#662222", width=2
        )

        self._label = self.create_text(
            72, self.H // 2, text=VALVE_LABELS[channel_id],
            fill=Colors.TEXT_PRIMARY, font=Fonts.BODY_BOLD, anchor="center"
        )

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
            x2,y2-r, x2,y2, x2-r,y2,
            x1+r,y2, x1,y2, x1,y2-r,
            x1,y1+r, x1,y1, x1+r,y1,
        ]
        return self.create_polygon(pts, smooth=True, **kw)

    def set_state(self, is_on: bool):
        if is_on:
            self.itemconfig(self._bg, fill="#0a3d2a", outline=Colors.ON)
            self.itemconfig(self._dot, fill=Colors.ON, outline="#00cc66")
        else:
            self.itemconfig(self._bg, fill=Colors.BG_PANEL, outline=Colors.CARD_BORDER)
            self.itemconfig(self._dot, fill=Colors.OFF, outline="#662222")


# ─────────────────────────────────────────────────────────────────────────────
#  Rounded Progress Bar (full → empty countdown  /  empty → full refill)
# ─────────────────────────────────────────────────────────────────────────────
class RoundedProgressBar(tk.Canvas):
    """Rounded progress bar with countdown and refill modes."""

    BAR_H = 26
    RADIUS = 13

    def __init__(self, parent, width=600, **kwargs):
        super().__init__(
            parent, width=width, height=self.BAR_H + 10,
            bg=Colors.BG_DARK, highlightthickness=0, **kwargs
        )
        self._bar_width = width - 20
        self._x = 10
        self._y = 5
        self._total = 0
        self._remaining = 0
        self._job_id = None
        self._mode = "idle"  # "countdown", "refill", "idle"

        # Track
        self._track = self._round_rect(
            self._x, self._y,
            self._x + self._bar_width, self._y + self.BAR_H,
            self.RADIUS, fill=Colors.BG_SURFACE, outline=Colors.CARD_BORDER, width=1
        )

        # Fill
        self._fill = self._round_rect(
            self._x, self._y,
            self._x + self._bar_width, self._y + self.BAR_H,
            self.RADIUS, fill=Colors.BG_SURFACE, outline=""
        )

        # Text
        self._text = self.create_text(
            self._x + self._bar_width // 2, self._y + self.BAR_H // 2,
            text="", fill="#000000", font=("Segoe UI", 10, "bold")
        )

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
            x2,y2-r, x2,y2, x2-r,y2,
            x1+r,y2, x1,y2, x1,y2-r,
            x1,y1+r, x1,y1, x1+r,y1,
        ]
        return self.create_polygon(pts, smooth=True, **kw)

    # ── Countdown: full → empty ──────────────────────────────────────
    def start_countdown(self, total_seconds: int):
        """Drain the bar from full to empty over total_seconds."""
        self.cancel()
        self._mode = "countdown"
        self._total = total_seconds
        self._remaining = total_seconds
        self._tick_countdown()

    def _tick_countdown(self):
        if self._total <= 0:
            return

        fraction = max(0, self._remaining / self._total)
        fill_w = max(self.RADIUS * 2, self._bar_width * fraction)

        self._redraw_fill(fill_w, self._countdown_color(fraction))

        mins, secs = divmod(self._remaining, 60)
        hrs, mins = divmod(mins, 60)
        if hrs > 0:
            time_str = f"{hrs}h {mins:02d}m {secs:02d}s"
        elif mins > 0:
            time_str = f"{mins}m {secs:02d}s"
        else:
            time_str = f"{secs}s"
        self.itemconfig(self._text, text=time_str)

        if self._remaining <= 0:
            self._mode = "idle"
            return

        self._remaining -= 1
        self._job_id = self.after(1000, self._tick_countdown)

    def _countdown_color(self, fraction: float) -> str:
        if fraction > 0.5:
            return Colors.ON
        elif fraction > 0.2:
            return Colors.TRANSITION
        else:
            return Colors.OFF

    # ── Refill: empty → full ─────────────────────────────────────────
    def start_refill(self, duration_seconds: int, label: str = ""):
        """Fill the bar from empty to full over duration_seconds."""
        self.cancel()
        self._mode = "refill"
        self._total = duration_seconds
        self._remaining = 0  # starts empty
        self._refill_label = label
        self._tick_refill()

    def _tick_refill(self):
        if self._total <= 0:
            return

        fraction = min(1.0, self._remaining / self._total)
        fill_w = max(self.RADIUS * 2, self._bar_width * fraction)

        self._redraw_fill(fill_w, Colors.INFO)

        text = self._refill_label if self._refill_label else "Preparing..."
        self.itemconfig(self._text, text=text)

        if self._remaining >= self._total:
            self._mode = "idle"
            return

        self._remaining += 1
        self._job_id = self.after(1000, self._tick_refill)

    # ── Helpers ──────────────────────────────────────────────────────
    def _redraw_fill(self, fill_w: float, color: str):
        self.delete(self._fill)
        self._fill = self._round_rect(
            self._x, self._y,
            self._x + fill_w, self._y + self.BAR_H,
            self.RADIUS, fill=color, outline=""
        )
        self.tag_raise(self._text)

    def cancel(self):
        if self._job_id:
            self.after_cancel(self._job_id)
            self._job_id = None

    def reset(self):
        self.cancel()
        self._mode = "idle"
        self._redraw_fill(self.RADIUS * 2, Colors.BG_SURFACE)
        self.itemconfig(self._text, text="")


# ─────────────────────────────────────────────────────────────────────────────
#  Auto Frame
# ─────────────────────────────────────────────────────────────────────────────
class AutoFrame(ttk.Frame):
    """Displays the automated filtration cycle with live status."""

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app
        self._cards: dict[int, IndicatorCard] = {}
        self._back_locked = False
        self._build()

    def _build(self):
        # Status header
        self._process_label = ttk.Label(
            self, text="Initializing...", style="Status.TLabel",
            font=Fonts.HEADING
        )
        self._process_label.pack(pady=(15, 10))

        # Valve indicators
        grid = ttk.Frame(self, style="TFrame")
        grid.pack(expand=True)

        row1 = ttk.Frame(grid, style="TFrame")
        row1.pack(pady=6)
        for cid in [1, 2, 3, 4]:
            card = IndicatorCard(row1, cid)
            card.pack(side="left", padx=5)
            self._cards[cid] = card

        row2 = ttk.Frame(grid, style="TFrame")
        row2.pack(pady=6)
        for cid in [5, 6, 7]:
            card = IndicatorCard(row2, cid)
            card.pack(side="left", padx=5)
            self._cards[cid] = card

        # Rounded progress bar
        self._progress = RoundedProgressBar(self, width=580)
        self._progress.pack(pady=(15, 5))

        # Info label
        self._time_label = ttk.Label(self, text="", style="Muted.TLabel")
        self._time_label.pack(pady=(0, 10))

    # ── Callbacks from ProcessManager ────────────────────────────────

    def on_process_start(self, name: str, duration_ms: int = 0):
        """Valves opened — label updates, bar refills to show transition."""
        display = name.replace("_", " ").title()
        self._process_label.config(
            text=f">>  {display}  —  Opening valves",
            foreground=Colors.TRANSITION
        )
        # Refill bar during the 5s valve pre-open phase
        self._progress.start_refill(5, label="Opening valves...")
        self._time_label.config(text=f"Process: {display}")

    def on_pump_start(self, name: str, countdown_ms: int = 0):
        """Pump engaged — start the real countdown (pump ON → valves close)."""
        display = name.replace("_", " ").title()
        self._process_label.config(
            text=f">>  {display}  —  Running",
            foreground=Colors.ON
        )
        if countdown_ms > 0:
            total_secs = countdown_ms // 1000
            self._progress.start_countdown(total_secs)
            self._time_label.config(
                text=f"Process: {display}  |  Duration: {self._fmt(total_secs)}"
            )

    def on_process_end(self, name: str):
        """Valves closed — process complete."""
        display = name.replace("_", " ").title()
        self._process_label.config(
            text=f"OK  {display} complete",
            foreground=Colors.TEXT_MUTED
        )
        self._progress.reset()
        self._time_label.config(text="Waiting for next process...")

    def on_valve_change(self, channel_id: int, is_on: bool):
        if channel_id in self._cards:
            self._cards[channel_id].set_state(is_on)

    def go_back(self):
        if self._back_locked:
            return
        self._back_locked = True
        self._progress.cancel()
        self._progress.reset()
        self._time_label.config(text="")

        # Stop the process manager (pumps off, then valves after delay)
        self.app.process_manager.stop_current_process(callback=self._on_fully_stopped)

        # Show a visible countdown
        self._stop_remaining = 5
        self._tick_stop()

    def _tick_stop(self):
        if self._stop_remaining <= 0:
            return
        self._process_label.config(
            text=f"Stopping...  {self._stop_remaining}s",
            foreground=Colors.TRANSITION
        )
        self._stop_remaining -= 1
        self._stop_job = self.after(1000, self._tick_stop)

    def _on_fully_stopped(self):
        if hasattr(self, "_stop_job"):
            self.after_cancel(self._stop_job)
        self._process_label.config(text="Stopped", foreground=Colors.TEXT_MUTED)
        for card in self._cards.values():
            card.set_state(False)
        self._back_locked = False
        self.app.show_frame("select")

    def on_show(self):
        self.app.topbar.set_subtitle("Auto Cycle")
        self._process_label.config(
            text="Starting cycle...", foreground=Colors.INFO
        )
        for card in self._cards.values():
            card.set_state(False)
        self._progress.reset()
        self._time_label.config(text="")

    @staticmethod
    def _fmt(secs: int) -> str:
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}h {m:02d}m {s:02d}s"
        return f"{m}m {s:02d}s"
