"""
main_frame.py — Home screen with MANUAL / AUTO / EXIT buttons.
"""

import tkinter as tk
from tkinter import ttk
import os

from src.ui.theme import Colors, Fonts
from src.ui.widgets import CardFrame, ask_question


class MainFrame(ttk.Frame):
    """Home screen — the first thing the operator sees."""

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app
        self._build()

    def _build(self):
        # Title area
        title = ttk.Label(
            self, text="Control Panel", style="Title.TLabel",
        )
        title.pack(pady=(30, 8))

        subtitle = ttk.Label(
            self, text="Select operating mode",
            style="Muted.TLabel"
        )
        subtitle.pack(pady=(0, 30))

        # Button container
        btn_container = ttk.Frame(self, style="TFrame")
        btn_container.pack(expand=True)

        # ── MANUAL Button ────────────────────────────────────────────
        manual_card = CardFrame(btn_container)
        manual_card.pack(side="left", padx=20, pady=10)

        manual_icon = ttk.Label(
            manual_card, text="M", font=("Segoe UI", 28, "bold"),
            background=Colors.BG_PANEL, foreground=Colors.INFO
        )
        manual_icon.pack(pady=(8, 3))

        manual_title = ttk.Label(
            manual_card, text="MANUAL", font=Fonts.BUTTON_LG,
            background=Colors.BG_PANEL, foreground=Colors.TEXT_PRIMARY
        )
        manual_title.pack()

        manual_desc = ttk.Label(
            manual_card, text="Direct valve control",
            font=Fonts.LABEL_SMALL,
            background=Colors.BG_PANEL, foreground=Colors.TEXT_MUTED
        )
        manual_desc.pack(pady=(2, 10))

        # Make entire card clickable
        for widget in [manual_card, manual_icon, manual_title, manual_desc]:
            widget.bind("<Button-1>", lambda e: self.app.show_frame("manual"))

        manual_card.config(cursor="hand2")

        # ── AUTO Button ──────────────────────────────────────────────
        auto_card = CardFrame(btn_container)
        auto_card.pack(side="left", padx=20, pady=10)

        auto_icon = ttk.Label(
            auto_card, text="A", font=("Segoe UI", 28, "bold"),
            background=Colors.BG_PANEL, foreground=Colors.ON
        )
        auto_icon.pack(pady=(8, 3))

        auto_title = ttk.Label(
            auto_card, text="AUTO", font=Fonts.BUTTON_LG,
            background=Colors.BG_PANEL, foreground=Colors.TEXT_PRIMARY
        )
        auto_title.pack()

        auto_desc = ttk.Label(
            auto_card, text="Automated cycle",
            font=Fonts.LABEL_SMALL,
            background=Colors.BG_PANEL, foreground=Colors.TEXT_MUTED
        )
        auto_desc.pack(pady=(2, 10))

        for widget in [auto_card, auto_icon, auto_title, auto_desc]:
            widget.bind("<Button-1>", lambda e: self.app.show_frame("select"))

        auto_card.config(cursor="hand2")

        # ── EXIT Button ──────────────────────────────────────────────
        exit_card = CardFrame(btn_container)
        exit_card.pack(side="left", padx=20, pady=10)
        exit_card.config(highlightbackground=Colors.EXIT_BG)

        exit_icon = ttk.Label(
            exit_card, text="X", font=("Segoe UI", 28, "bold"),
            background=Colors.BG_PANEL, foreground=Colors.OFF
        )
        exit_icon.pack(pady=(8, 3))

        exit_title = ttk.Label(
            exit_card, text="EXIT", font=Fonts.BUTTON_LG,
            background=Colors.BG_PANEL, foreground=Colors.OFF
        )
        exit_title.pack()

        exit_desc = ttk.Label(
            exit_card, text="Shutdown system",
            font=Fonts.LABEL_SMALL,
            background=Colors.BG_PANEL, foreground=Colors.TEXT_MUTED
        )
        exit_desc.pack(pady=(2, 10))

        for widget in [exit_card, exit_icon, exit_title, exit_desc]:
            widget.bind("<Button-1>", lambda e: self._exit())

        exit_card.config(cursor="hand2")

    def _exit(self):
        if ask_question(self.app.root, "Exit", "Are you sure you want to shutdown?"):
            self.app.gpio.shutdown()
            from src.config import IS_HARDWARE
            if IS_HARDWARE:
                os.system("sudo shutdown -h now")
            else:
                self.app.root.destroy()

    def on_show(self):
        self.app.topbar.set_subtitle("Home")
