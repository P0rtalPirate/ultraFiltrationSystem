"""
app.py — Main application class. Creates the Tk root, applies theme,
manages frame navigation, and wires up the ProcessManager.
"""

import tkinter as tk
from tkinter import ttk
import logging

from src.config import IS_FULLSCREEN, SHOW_CURSOR, SCREEN_WIDTH, SCREEN_HEIGHT, get_gpio
from src.ui.theme import apply_theme, Colors
from src.ui.widgets import TopBar, BottomNavBar
from src.processes.process_manager import ProcessManager

from src.ui.frames.main_frame import MainFrame
from src.ui.frames.manual_frame import ManualFrame
from src.ui.frames.auto_frame import AutoFrame
from src.ui.frames.select_frame import SelectFrame
from src.ui.frames.manual_steps_frame import ManualStepsFrame
from src.ui.frames.edit_frame import EditFrame
from src.ui.frames.info_frame import InfoFrame

logger = logging.getLogger("UltraFiltration.App")


class App:
    """Root application — manages frames, GPIO, and process lifecycle."""

    def __init__(self):
        # ── Tk root ──────────────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("UltraFiltration Control System")

        # Get actual screen dimensions if fullscreen, otherwise use defaults
        if IS_FULLSCREEN:
            self.root.attributes("-fullscreen", True)
            width = self.root.winfo_screenwidth()
            height = self.root.winfo_screenheight()
        else:
            width = SCREEN_WIDTH
            height = SCREEN_HEIGHT

        self.root.geometry(f"{width}x{height}")
        self.root.configure(bg=Colors.BG_DARK)
        self.root.resizable(False, False)

        if not SHOW_CURSOR:
            self.root.config(cursor="none")
            # Force cursor hiding on all frames
            self.root.bind("<Motion>", lambda e: self.root.config(cursor="none"))

        # ── Theme ────────────────────────────────────────────────────
        self.style = apply_theme(self.root)

        # ── GPIO ─────────────────────────────────────────────────────
        self.gpio = get_gpio()

        # ── Layout: topbar + content + navbar ────────────────────────
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Top bar
        self.topbar = TopBar(self.root)
        self.topbar.grid(row=0, column=0, sticky="ew")

        # Content area (frames stack here)
        self._content = ttk.Frame(self.root, style="TFrame")
        self._content.grid(row=1, column=0, sticky="nsew")
        self._content.rowconfigure(0, weight=1)
        self._content.columnconfigure(0, weight=1)

        # Bottom nav bar
        self.navbar = BottomNavBar(self.root)
        self.navbar.grid(row=2, column=0, sticky="ew")

        self._back_btn = self.navbar.add_button(
            "back", "◀  Back", self._go_back, side="left"
        )

        # ── Frames ───────────────────────────────────────────────────
        self.frames: dict[str, ttk.Frame] = {}
        self._current_frame: str | None = None

        self._create_frames()

        # ── Process Manager ──────────────────────────────────────────
        self.process_manager = ProcessManager(self.gpio, self.root)

        # ── Show home ────────────────────────────────────────────────
        self.show_frame("main")
        logger.info("App initialized successfully")

    def _create_frames(self):
        frame_classes = {
            "main":          MainFrame,
            "manual":        ManualFrame,
            "auto":          AutoFrame,
            "select":        SelectFrame,
            "manual_steps":  ManualStepsFrame,
            "edit":          EditFrame,
            "info":          InfoFrame,
        }
        for name, cls in frame_classes.items():
            frame = cls(self._content, self)
            frame.grid(row=0, column=0, sticky="nsew")
            self.frames[name] = frame

    def show_frame(self, name: str):
        """Raise a frame to the top and call its on_show hook."""
        frame = self.frames[name]
        frame.tkraise()
        self._current_frame = name

        if hasattr(frame, "on_show"):
            frame.on_show()

        # Show/hide back button based on frame
        if name == "main":
            self._back_btn.pack_forget()
        else:
            self._back_btn.pack(side="left", padx=8, pady=6, fill="y")

        logger.debug("Showing frame: %s", name)

    def _go_back(self):
        """Navigate back — delegates to the current frame's go_back if it has one."""
        frame = self.frames.get(self._current_frame)

        if frame and hasattr(frame, "go_back"):
            frame.go_back()
        else:
            # Default back navigation
            back_map = {
                "manual":        "main",
                "select":        "main",
                "auto":          "select",
                "manual_steps":  "select",
                "edit":          "select",
                "info":          "select",
            }
            target = back_map.get(self._current_frame, "main")
            self.show_frame(target)

    def start_auto_cycle(self):
        """Launch the automatic filtration cycle."""
        auto_frame = self.frames["auto"]
        self.show_frame("auto")

        # Wire auto frame as callback receiver
        self.process_manager.on_process_start = auto_frame.on_process_start
        self.process_manager.on_pump_start = auto_frame.on_pump_start
        self.process_manager.on_process_end = auto_frame.on_process_end
        self.process_manager.on_valve_change = auto_frame.on_valve_change

        self.process_manager.start_auto_cycle()

    def run(self):
        """Start the Tkinter event loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("KeyboardInterrupt — shutting down")
        finally:
            self.gpio.shutdown()
