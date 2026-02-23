"""
widgets.py — Reusable styled widgets for the UltraFiltration UI.
"""

import tkinter as tk
from tkinter import ttk
from time import strftime
from src.ui.theme import Colors, Fonts


# ─────────────────────────────────────────────────────────────────────────────
#  LED Indicator (Canvas-drawn circle with glow effect)
# ─────────────────────────────────────────────────────────────────────────────
class LEDIndicator(tk.Canvas):
    """Circular LED indicator that glows green (ON) or dims red (OFF)."""

    def __init__(self, parent, label_text="", size=36, **kwargs):
        super().__init__(parent, width=size + 80, height=size + 20,
                         bg=Colors.BG_DARK, highlightthickness=0, **kwargs)
        self._size = size
        self._is_on = False
        cx, cy = size // 2 + 5, size // 2 + 5

        # Outer glow ring
        self._glow = self.create_oval(
            cx - size // 2 - 3, cy - size // 2 - 3,
            cx + size // 2 + 3, cy + size // 2 + 3,
            fill=Colors.BG_DARK, outline=Colors.BG_DARK, width=0
        )
        # Main LED circle
        self._led = self.create_oval(
            cx - size // 2, cy - size // 2,
            cx + size // 2, cy + size // 2,
            fill=Colors.OFF, outline="#333333", width=2
        )
        # Inner highlight (specular)
        hs = size // 4
        self._highlight = self.create_oval(
            cx - hs, cy - hs - size // 6,
            cx + hs, cy,
            fill="", outline="", width=0
        )
        # Label
        if label_text:
            self.create_text(
                cx + size // 2 + 12, cy,
                text=label_text, anchor="w",
                fill=Colors.TEXT_PRIMARY, font=Fonts.BODY_BOLD
            )

        self.set_state(False)

    def set_state(self, is_on: bool) -> None:
        self._is_on = is_on
        if is_on:
            self.itemconfig(self._led, fill=Colors.ON, outline="#00cc66")
            self.itemconfig(self._glow, fill="#003322", outline="#004433")
            self.itemconfig(self._highlight, fill="#66ffbb")
        else:
            self.itemconfig(self._led, fill=Colors.OFF, outline="#662222")
            self.itemconfig(self._glow, fill=Colors.BG_DARK, outline=Colors.BG_DARK)
            self.itemconfig(self._highlight, fill="")

    def set_transition(self) -> None:
        """Set amber color for transitioning state."""
        self.itemconfig(self._led, fill=Colors.TRANSITION, outline="#cc8800")
        self.itemconfig(self._glow, fill="#332200", outline="#443300")
        self.itemconfig(self._highlight, fill="#ffcc66")


# ─────────────────────────────────────────────────────────────────────────────
#  Top Bar (shared clock + title across all frames)
# ─────────────────────────────────────────────────────────────────────────────
class TopBar(ttk.Frame):
    """Persistent top bar with title and real-time clock."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TopBar.TFrame", **kwargs)

        # Title
        self._title_label = ttk.Label(
            self, text="UltraFiltration", style="Title.TLabel"
        )
        self._title_label.configure(background=Colors.TOPBAR_BG)
        self._title_label.pack(side="left", padx=15, pady=8)

        # Separator dot
        sep = ttk.Label(self, text="•", style="Muted.TLabel")
        sep.configure(background=Colors.TOPBAR_BG)
        sep.pack(side="left", padx=5)

        # Subtitle (changes per frame)
        self._subtitle = ttk.Label(self, text="Home", style="TLabel")
        self._subtitle.configure(
            background=Colors.TOPBAR_BG,
            foreground=Colors.TEXT_MUTED,
            font=Fonts.BODY
        )
        self._subtitle.pack(side="left", padx=5, pady=8)

        # Clock
        self._clock = ttk.Label(self, style="Clock.TLabel")
        self._clock.pack(side="right", padx=15, pady=8)

        self._tick()

    def set_subtitle(self, text: str) -> None:
        self._subtitle.config(text=text)

    def _tick(self) -> None:
        self._clock.config(text=strftime("%I:%M:%S %p   %d/%m/%Y"))
        self.after(1000, self._tick)


# ─────────────────────────────────────────────────────────────────────────────
#  Bottom Navigation Bar
# ─────────────────────────────────────────────────────────────────────────────
class BottomNavBar(ttk.Frame):
    """Persistent bottom navigation with large touch-friendly buttons."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="NavBar.TFrame", **kwargs)
        self._buttons: dict[str, ttk.Button] = {}

    def add_button(self, key: str, text: str, command, side="left",
                   style="Nav.TButton") -> ttk.Button:
        btn = ttk.Button(self, text=text, command=command, style=style)
        btn.pack(side=side, padx=8, pady=6, fill="y")
        self._buttons[key] = btn
        return btn

    def set_button_state(self, key: str, state: str) -> None:
        if key in self._buttons:
            self._buttons[key].config(state=state)


# ─────────────────────────────────────────────────────────────────────────────
#  Countdown Bar (animated progress indicator)
# ─────────────────────────────────────────────────────────────────────────────
class CountdownBar(ttk.Frame):
    """Full-width animated countdown with seconds display."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style="TFrame", **kwargs)

        self._label = ttk.Label(self, text="", style="Countdown.TLabel")
        self._label.pack(pady=(5, 2))

        self._progress = ttk.Progressbar(
            self, orient="horizontal", length=400, mode="determinate",
            style="Countdown.Horizontal.TProgressbar"
        )
        self._progress.pack(fill="x", padx=20, pady=(0, 5))

        self._total = 0
        self._remaining = 0
        self._job_id = None
        self._callback = None

    def start_countdown(self, seconds: int, callback=None) -> None:
        """Start a countdown from `seconds` down to 0."""
        self._total = seconds
        self._remaining = seconds
        self._callback = callback
        self._progress["maximum"] = seconds
        self._progress["value"] = seconds
        self._tick_down()

    def cancel(self) -> None:
        if self._job_id:
            self.after_cancel(self._job_id)
            self._job_id = None
        self._label.config(text="")
        self._progress["value"] = 0

    def _tick_down(self) -> None:
        if self._remaining <= 0:
            self._label.config(text="")
            self._progress["value"] = 0
            if self._callback:
                self._callback()
            return
        self._label.config(text=f"{self._remaining}s")
        self._progress["value"] = self._remaining
        self._remaining -= 1
        self._job_id = self.after(1000, self._tick_down)


# ─────────────────────────────────────────────────────────────────────────────
#  Styled Card Frame
# ─────────────────────────────────────────────────────────────────────────────
class CardFrame(tk.Frame):
    """A rounded-corner card panel."""

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            bg=Colors.BG_PANEL,
            highlightbackground=Colors.CARD_BORDER,
            highlightthickness=1,
            padx=15, pady=10,
            **kwargs
        )


# ─────────────────────────────────────────────────────────────────────────────
#  Custom Themed Dialog (replaces messagebox)
# ─────────────────────────────────────────────────────────────────────────────
class CustomDialog(tk.Toplevel):
    """Dark-themed modal dialog matching the app's industrial look."""

    ICONS = {
        "info":     ("ℹ", Colors.INFO),
        "warning":  ("⚠", Colors.TRANSITION),
        "error":    ("✖", Colors.OFF),
        "question": ("?", Colors.ON),
    }

    def __init__(self, parent, title="Dialog", message="",
                 dialog_type="info", buttons=None, callback=None):
        """
        Args:
            parent: Parent widget.
            title: Dialog title text.
            message: Body message text.
            dialog_type: 'info', 'warning', 'error', or 'question'.
            buttons: List of button labels, e.g. ["Yes", "No"] or ["OK"].
                     Defaults to ["OK"].
            callback: Called with the button label that was pressed.
        """
        super().__init__(parent)
        self.result = None
        self._callback = callback

        if buttons is None:
            buttons = ["OK"]

        # ── Window setup ─────────────────────────────────────────────
        self.title(title)
        self.configure(bg=Colors.BG_DARK)
        self.resizable(False, False)
        self.overrideredirect(True)  # Remove OS title bar

        # ── Outer border frame ───────────────────────────────────────
        border = tk.Frame(
            self, bg=Colors.CARD_BORDER, padx=2, pady=2
        )
        border.pack(fill="both", expand=True)

        container = tk.Frame(border, bg=Colors.BG_PANEL, padx=30, pady=20)
        container.pack(fill="both", expand=True)

        # ── Title row ────────────────────────────────────────────────
        title_frame = tk.Frame(container, bg=Colors.BG_PANEL)
        title_frame.pack(fill="x", pady=(0, 15))

        tk.Label(
            title_frame, text=title,
            font=Fonts.HEADING, fg=Colors.TEXT_ACCENT,
            bg=Colors.BG_PANEL
        ).pack(side="left")

        # ── Icon + message ───────────────────────────────────────────
        body = tk.Frame(container, bg=Colors.BG_PANEL)
        body.pack(fill="x", pady=(0, 20))

        icon_char, icon_color = self.ICONS.get(dialog_type, self.ICONS["info"])
        tk.Label(
            body, text=icon_char,
            font=("Segoe UI", 28), fg=icon_color,
            bg=Colors.BG_PANEL
        ).pack(side="left", padx=(0, 15))

        tk.Label(
            body, text=message,
            font=Fonts.BODY, fg=Colors.TEXT_PRIMARY,
            bg=Colors.BG_PANEL, wraplength=320,
            justify="left"
        ).pack(side="left", fill="x", expand=True)

        # ── Separator line ───────────────────────────────────────────
        tk.Frame(
            container, bg=Colors.CARD_BORDER, height=1
        ).pack(fill="x", pady=(0, 15))

        # ── Buttons ──────────────────────────────────────────────────
        btn_frame = tk.Frame(container, bg=Colors.BG_PANEL)
        btn_frame.pack(fill="x")

        # Button color scheme
        btn_colors = {
            "Yes":    (Colors.ON, "#000000"),
            "OK":     (Colors.INFO, "#000000"),
            "No":     (Colors.OFF, "#ffffff"),
            "Cancel": (Colors.BG_SURFACE, Colors.TEXT_PRIMARY),
        }

        for label in buttons:
            bg, fg = btn_colors.get(label, (Colors.BG_SURFACE, Colors.TEXT_PRIMARY))
            btn = tk.Button(
                btn_frame, text=label,
                font=Fonts.BUTTON, fg=fg, bg=bg,
                activebackground=bg, activeforeground=fg,
                relief="flat", cursor="hand2",
                width=10, height=1,
                command=lambda lbl=label: self._on_press(lbl)
            )
            btn.pack(side="right", padx=5)

        # ── Center on parent ─────────────────────────────────────────
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        dw = self.winfo_reqwidth()
        dh = self.winfo_reqheight()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")

        # Make modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _on_press(self, label: str):
        self.result = label
        self.grab_release()
        self.destroy()
        if self._callback:
            self._callback(label)

    def wait_for_result(self) -> str | None:
        """Block until dialog is closed. Returns the button label pressed."""
        self.wait_window()
        return self.result


# ── Convenience functions (drop-in replacements for messagebox) ──────────────

def show_info(parent, title: str, message: str):
    """Show an info dialog with an OK button."""
    dlg = CustomDialog(parent, title, message, dialog_type="info")
    dlg.wait_for_result()


def ask_question(parent, title: str, message: str) -> bool:
    """Show a Yes/No question dialog. Returns True if 'Yes' was pressed."""
    dlg = CustomDialog(
        parent, title, message,
        dialog_type="question", buttons=["No", "Yes"]
    )
    return dlg.wait_for_result() == "Yes"


def show_warning(parent, title: str, message: str):
    """Show a warning dialog with an OK button."""
    dlg = CustomDialog(
        parent, title, message, dialog_type="warning"
    )
    dlg.wait_for_result()

