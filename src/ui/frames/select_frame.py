"""
select_frame.py — Sub-menu for AUTO mode, Manual Step Control, and Edit Time.
"""

import tkinter as tk
from tkinter import ttk

from src.ui.theme import Colors, Fonts
from src.ui.widgets import CardFrame


class SelectFrame(ttk.Frame):
    """Selection screen — choose between Auto, Manual Steps, or Edit Time."""

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app
        self._build()

    def _build(self):
        ttk.Label(
            self, text="Auto Mode Options", style="Title.TLabel"
        ).pack(pady=(40, 5))

        ttk.Label(
            self, text="Choose how you'd like to operate",
            style="Muted.TLabel"
        ).pack(pady=(0, 30))

        # ── Cards container ──────────────────────────────────────────
        container = ttk.Frame(self, style="TFrame")
        container.pack(expand=True)

        # ── AUTO cycle card ──────────────────────────────────────────
        auto_card = CardFrame(container)
        auto_card.pack(side="left", padx=15, pady=10)

        tk.Label(auto_card, text=">>", font=("Consolas", 28, "bold"),
                 bg=Colors.BG_PANEL, fg=Colors.ON).pack(pady=(8, 3))
        tk.Label(auto_card, text="AUTO CYCLE", font=Fonts.BUTTON_LG,
                 bg=Colors.BG_PANEL, fg=Colors.TEXT_PRIMARY).pack()
        tk.Label(auto_card, text="Full automated\nfiltration cycle",
                 font=Fonts.LABEL_SMALL, bg=Colors.BG_PANEL,
                 fg=Colors.TEXT_MUTED, justify="center").pack(pady=(3, 8))

        for w in auto_card.winfo_children():
            w.bind("<Button-1>", lambda e: self.app.start_auto_cycle())
        auto_card.bind("<Button-1>", lambda e: self.app.start_auto_cycle())
        auto_card.config(cursor="hand2")

        # ── Manual Step Control card ─────────────────────────────────
        msc_card = CardFrame(container)
        msc_card.pack(side="left", padx=15, pady=10)

        tk.Label(msc_card, text="[]", font=("Consolas", 28, "bold"),
                 bg=Colors.BG_PANEL, fg=Colors.INFO).pack(pady=(8, 3))
        tk.Label(msc_card, text="STEP CONTROL", font=Fonts.BUTTON_LG,
                 bg=Colors.BG_PANEL, fg=Colors.TEXT_PRIMARY).pack()
        tk.Label(msc_card, text="Run individual\nprocesses manually",
                 font=Fonts.LABEL_SMALL, bg=Colors.BG_PANEL,
                 fg=Colors.TEXT_MUTED, justify="center").pack(pady=(3, 8))

        for w in msc_card.winfo_children():
            w.bind("<Button-1>", lambda e: self.app.show_frame("manual_steps"))
        msc_card.bind("<Button-1>", lambda e: self.app.show_frame("manual_steps"))
        msc_card.config(cursor="hand2")

        # ── Edit Time card ───────────────────────────────────────────
        edit_card = CardFrame(container)
        edit_card.pack(side="left", padx=15, pady=10)

        tk.Label(edit_card, text="T:", font=("Consolas", 28, "bold"),
                 bg=Colors.BG_PANEL, fg=Colors.TRANSITION).pack(pady=(8, 3))
        tk.Label(edit_card, text="EDIT TIME", font=Fonts.BUTTON_LG,
                 bg=Colors.BG_PANEL, fg=Colors.TEXT_PRIMARY).pack()
        tk.Label(edit_card, text="Adjust process\ndurations",
                 font=Fonts.LABEL_SMALL, bg=Colors.BG_PANEL,
                 fg=Colors.TEXT_MUTED, justify="center").pack(pady=(3, 8))

        for w in edit_card.winfo_children():
            w.bind("<Button-1>", lambda e: self.app.show_frame("edit"))
        edit_card.bind("<Button-1>", lambda e: self.app.show_frame("edit"))
        edit_card.config(cursor="hand2")

    def on_show(self):
        self.app.topbar.set_subtitle("Auto Mode")
