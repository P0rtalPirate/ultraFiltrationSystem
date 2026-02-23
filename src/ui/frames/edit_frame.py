"""
edit_frame.py — Adjust process durations with a large numpad.
"""

import math
import tkinter as tk
from tkinter import ttk

from src.ui.theme import Colors, Fonts
from src.ui.widgets import ask_question, show_info


class EditFrame(ttk.Frame):
    """Edit time intervals for each filtration process."""

    PROCESSES = ["fast_rinse", "service", "back_wash", "forward_wash"]
    DISPLAY_NAMES = {
        "fast_rinse":   "Fast Rinse",
        "service":      "Service",
        "back_wash":    "Back Wash",
        "forward_wash": "Forward Wash",
    }

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app
        self._active_field = None  # Currently selected time field
        self._time_fields: dict[str, dict[str, tk.Button]] = {}  # proc -> {hr, m, s}
        self._build()

    def _build(self):
        ttk.Label(
            self, text="Edit Process Durations", style="Title.TLabel"
        ).pack(pady=(12, 8))

        content = ttk.Frame(self, style="TFrame")
        content.pack(expand=True, fill="both", padx=15)

        # ── Left: time table ─────────────────────────────────────────
        left = ttk.Frame(content, style="TFrame")
        left.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Header row
        header = ttk.Frame(left, style="TFrame")
        header.pack(fill="x", pady=(0, 5))
        ttk.Label(header, text="Process", style="Heading.TLabel",
                  width=16).pack(side="left")
        for unit in ["HR", "MIN", "SEC"]:
            ttk.Label(header, text=unit, style="Muted.TLabel",
                      width=6, anchor="center").pack(side="left", padx=4)

        # Process rows
        for proc in self.PROCESSES:
            self._create_time_row(left, proc)

        # Action buttons
        action_row = ttk.Frame(left, style="TFrame")
        action_row.pack(fill="x", pady=(15, 0))

        apply_btn = tk.Button(
            action_row, text="APPLY", font=Fonts.BUTTON,
            bg="#0a4d33", fg=Colors.ON,
            activebackground="#0d6b44", activeforeground=Colors.ON,
            relief="flat", padx=20, pady=8, cursor="hand2",
            command=self._apply
        )
        apply_btn.pack(side="left", padx=5)

        reset_btn = tk.Button(
            action_row, text="RESET", font=Fonts.BUTTON,
            bg=Colors.BG_SURFACE, fg=Colors.TRANSITION,
            activebackground=Colors.BG_HOVER,
            relief="flat", padx=20, pady=8, cursor="hand2",
            command=self._reset
        )
        reset_btn.pack(side="left", padx=5)

        # ── Right: numpad ────────────────────────────────────────────
        right = tk.Frame(content, bg=Colors.BG_PANEL,
                         highlightbackground=Colors.CARD_BORDER,
                         highlightthickness=1, padx=10, pady=10)
        right.pack(side="right", fill="y", padx=(15, 0))

        numpad_title = tk.Label(right, text="Numpad", font=Fonts.HEADING,
                                bg=Colors.BG_PANEL, fg=Colors.TEXT_PRIMARY)
        numpad_title.pack(pady=(0, 8))

        numpad_grid = tk.Frame(right, bg=Colors.BG_PANEL)
        numpad_grid.pack()

        for i, num in enumerate([1, 2, 3, 4, 5, 6, 7, 8, 9, None, 0, "DEL"]):
            row, col = divmod(i, 3)
            if num is None:
                tk.Frame(numpad_grid, width=65, height=55,
                         bg=Colors.BG_PANEL).grid(row=row, column=col, padx=3, pady=3)
                continue
            btn = tk.Button(
                numpad_grid,
                text=str(num),
                font=Fonts.NUMPAD,
                width=4, height=2,
                bg=Colors.BG_SURFACE, fg=Colors.TEXT_PRIMARY,
                activebackground=Colors.BG_HOVER,
                activeforeground=Colors.TEXT_PRIMARY,
                relief="flat", cursor="hand2",
                command=lambda n=num: self._numpad_press(n)
            )
            btn.grid(row=row, column=col, padx=3, pady=3)

    def _create_time_row(self, parent, proc: str):
        row = ttk.Frame(parent, style="TFrame")
        row.pack(fill="x", pady=3)

        # Process name
        tk.Label(
            row, text=self.DISPLAY_NAMES[proc],
            font=Fonts.BODY_BOLD, bg=Colors.BG_DARK, fg=Colors.TEXT_PRIMARY,
            width=16, anchor="w"
        ).pack(side="left")

        self._time_fields[proc] = {}

        for unit in ["hr", "m", "s"]:
            btn = tk.Button(
                row, text="0", width=5, font=Fonts.NUMPAD,
                bg=Colors.BG_SURFACE, fg=Colors.TEXT_PRIMARY,
                activebackground=Colors.TEXT_ACCENT,
                relief="flat", cursor="hand2",
                command=lambda p=proc, u=unit: self._select_field(p, u)
            )
            btn.pack(side="left", padx=4)
            self._time_fields[proc][unit] = btn

    def _select_field(self, proc: str, unit: str):
        # Deselect previous
        if self._active_field:
            ap, au = self._active_field
            old_btn = self._time_fields[ap][au]
            if old_btn["text"] == "":
                old_btn.config(text="0")
            old_btn.config(bg=Colors.BG_SURFACE)

        # Select new
        btn = self._time_fields[proc][unit]
        btn.config(text="", bg=Colors.TEXT_ACCENT)
        self._active_field = (proc, unit)

    def _numpad_press(self, value):
        if self._active_field is None:
            return
        proc, unit = self._active_field
        btn = self._time_fields[proc][unit]

        if value == "DEL":
            txt = btn["text"]
            btn.config(text=txt[:-1] if len(txt) > 0 else "")
        else:
            txt = btn["text"] + str(value)
            # Limit to 3 digits
            if len(txt) <= 3:
                btn.config(text=txt)

    def _get_ms(self, proc: str) -> int:
        """Get the time in milliseconds for a process from the UI fields."""
        fields = self._time_fields[proc]
        h = int(fields["hr"]["text"] or "0")
        m = int(fields["m"]["text"] or "0")
        s = int(fields["s"]["text"] or "0")
        return (h * 3600 + m * 60 + s) * 1000

    def _apply(self):
        if ask_question(self.app.root, "Confirm", "Apply new time intervals?"):
            new_timings = {}
            for proc in self.PROCESSES:
                new_timings[proc] = self._get_ms(proc)
            self.app.process_manager.update_timings(new_timings)
            show_info(self.app.root, "Updated", "Time intervals updated successfully.")

    def _reset(self):
        self.app.process_manager.reset_timings()
        self._load_current_timings()
        show_info(self.app.root, "Reset", "Time intervals reset to defaults.")

    def _load_current_timings(self):
        """Populate fields from current process manager timings."""
        timings = self.app.process_manager.timings
        for proc in self.PROCESSES:
            ms = timings.get(proc, 0)
            total_s = ms // 1000
            h = total_s // 3600
            m = (total_s % 3600) // 60
            s = total_s % 60
            self._time_fields[proc]["hr"].config(text=str(h))
            self._time_fields[proc]["m"].config(text=str(m))
            self._time_fields[proc]["s"].config(text=str(s))

    def go_back(self):
        if ask_question(
            self.app.root, "Save",
            "Save current time intervals before going back?"
        ):
            self._apply()
        self.app.show_frame("select")

    def on_show(self):
        self.app.topbar.set_subtitle("Edit Timings")
        self._active_field = None
        self._load_current_timings()
