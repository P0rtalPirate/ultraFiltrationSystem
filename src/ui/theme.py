"""
theme.py — Dark industrial theme for the UltraFiltration UI.
Applies a ttk Style and exposes color/font constants.
"""

import tkinter as tk
from tkinter import ttk


# ── Color Palette ────────────────────────────────────────────────────────────
class Colors:
    BG_DARK      = "#0f0f1a"     # Deepest background
    BG_PANEL     = "#1a1a2e"     # Panel / card background
    BG_SURFACE   = "#16213e"     # Elevated surface
    BG_HOVER     = "#1f3460"     # Hover state

    ON           = "#00ff88"     # Neon green — valve/pump ON
    OFF          = "#ff4757"     # Soft red — valve/pump OFF
    TRANSITION   = "#ffa502"     # Amber — transitioning / starting / stopping
    INFO         = "#3498db"     # Blue — informational
    WARNING      = "#e67e22"     # Orange — warnings

    TEXT_PRIMARY = "#e8e8f0"     # Main text
    TEXT_MUTED   = "#7f8c9b"     # Secondary text
    TEXT_ACCENT  = "#00d2ff"     # Accent / links

    BUTTON_BG    = "#1e3a5f"     # Default button
    BUTTON_FG    = "#e8e8f0"
    BUTTON_HOVER = "#2d5f8a"
    BUTTON_PRESS = "#0d2137"

    NAV_BG       = "#0d0d1a"     # Bottom nav bar
    TOPBAR_BG    = "#0d0d1a"     # Top bar

    CARD_BORDER  = "#2a2a4a"     # Subtle border for cards
    DIVIDER      = "#2a2a4a"     # Horizontal dividers

    EXIT_BG      = "#8b0000"     # Exit / danger
    EXIT_HOVER   = "#a52a2a"


# ── Font Definitions ─────────────────────────────────────────────────────────
class Fonts:
    # These are defined as tuples suitable for Tkinter font arguments
    TITLE       = ("Segoe UI", 17, "bold")
    HEADING     = ("Segoe UI", 13, "bold")
    BODY        = ("Segoe UI", 11)
    BODY_BOLD   = ("Segoe UI", 11, "bold")
    BUTTON      = ("Segoe UI", 12, "bold")
    BUTTON_LG   = ("Segoe UI", 14, "bold")
    CLOCK       = ("Consolas", 14, "bold")
    TIMER_VALUE = ("Consolas", 22, "bold")
    LABEL_SMALL = ("Segoe UI", 10)
    NUMPAD      = ("Consolas", 14, "bold")
    STATUS      = ("Segoe UI", 13)
    COUNTDOWN   = ("Consolas", 24, "bold")


# ── Theme Application ────────────────────────────────────────────────────────
def apply_theme(root: tk.Tk) -> ttk.Style:
    """Apply the dark industrial theme to the entire application."""
    style = ttk.Style(root)
    style.theme_use("clam")  # Best base for dark theming

    # ── Global defaults ──────────────────────────────────────────────
    root.configure(bg=Colors.BG_DARK)
    root.option_add("*Background", Colors.BG_DARK)
    root.option_add("*Foreground", Colors.TEXT_PRIMARY)

    # ── TFrame ───────────────────────────────────────────────────────
    style.configure("TFrame", background=Colors.BG_DARK)
    style.configure("Card.TFrame", background=Colors.BG_PANEL)
    style.configure("Surface.TFrame", background=Colors.BG_SURFACE)
    style.configure("TopBar.TFrame", background=Colors.TOPBAR_BG)
    style.configure("NavBar.TFrame", background=Colors.NAV_BG)

    # ── TLabel ───────────────────────────────────────────────────────
    style.configure("TLabel",
                    background=Colors.BG_DARK,
                    foreground=Colors.TEXT_PRIMARY,
                    font=Fonts.BODY)
    style.configure("Title.TLabel",
                    font=Fonts.TITLE,
                    foreground=Colors.TEXT_ACCENT)
    style.configure("Heading.TLabel",
                    font=Fonts.HEADING,
                    foreground=Colors.TEXT_PRIMARY)
    style.configure("Muted.TLabel",
                    foreground=Colors.TEXT_MUTED,
                    font=Fonts.LABEL_SMALL)
    style.configure("Clock.TLabel",
                    font=Fonts.CLOCK,
                    foreground=Colors.TEXT_ACCENT,
                    background=Colors.TOPBAR_BG)
    style.configure("Status.TLabel",
                    font=Fonts.STATUS,
                    foreground=Colors.TEXT_PRIMARY,
                    background=Colors.BG_DARK)
    style.configure("Countdown.TLabel",
                    font=Fonts.COUNTDOWN,
                    foreground=Colors.TRANSITION,
                    background=Colors.BG_DARK)

    # ── TButton ──────────────────────────────────────────────────────
    style.configure("TButton",
                    font=Fonts.BUTTON,
                    background=Colors.BUTTON_BG,
                    foreground=Colors.BUTTON_FG,
                    borderwidth=0,
                    padding=(20, 12))
    style.map("TButton",
              background=[("active", Colors.BUTTON_HOVER),
                          ("pressed", Colors.BUTTON_PRESS)])

    style.configure("Large.TButton",
                    font=Fonts.BUTTON_LG,
                    padding=(30, 20))

    style.configure("Nav.TButton",
                    background=Colors.NAV_BG,
                    foreground=Colors.TEXT_PRIMARY,
                    font=Fonts.BODY_BOLD,
                    padding=(15, 10))
    style.map("Nav.TButton",
              background=[("active", Colors.BG_HOVER)])

    style.configure("Danger.TButton",
                    background=Colors.EXIT_BG,
                    foreground="#ffffff",
                    font=Fonts.BUTTON)
    style.map("Danger.TButton",
              background=[("active", Colors.EXIT_HOVER)])

    style.configure("ON.TButton",
                    background="#0a4d33",
                    foreground=Colors.ON,
                    font=Fonts.BUTTON)

    style.configure("OFF.TButton",
                    background="#4d0a1a",
                    foreground=Colors.OFF,
                    font=Fonts.BUTTON)

    style.configure("Numpad.TButton",
                    font=Fonts.NUMPAD,
                    background=Colors.BG_SURFACE,
                    foreground=Colors.TEXT_PRIMARY,
                    padding=(10, 8))
    style.map("Numpad.TButton",
              background=[("active", Colors.BG_HOVER)])

    # ── TProgressbar ─────────────────────────────────────────────────
    style.configure("Countdown.Horizontal.TProgressbar",
                    troughcolor=Colors.BG_SURFACE,
                    background=Colors.TRANSITION,
                    thickness=8)

    return style
