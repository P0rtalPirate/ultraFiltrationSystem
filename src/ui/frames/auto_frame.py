"""
auto_frame.py — Automated cycle display with rounded cards and progress bar.
Countdown starts when pump engages, ends when valves close.
Between processes the bar fills back up.

Includes a persistent toggle button (bottom-right) that swaps the valve/pump
card grid with the live system diagram SVG. The preference is stored in
.uf_prefs.json and survives Pi reboots.

Fallback: If cairosvg fails (common on Windows without Cairo DLLs), 
a native Tkinter SVG-to-Canvas renderer is used.
This version includes advanced real-time animations for flow and levels.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import math

from src.config import VALVE_LABELS, get_svg_view_pref, set_svg_view_pref
from src.ui.theme import Colors, Fonts

# Project root for locating the SVG file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SVG_PATH = _PROJECT_ROOT / "branding" / "system_diagram.svg"


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

    def start_countdown(self, total_seconds: int):
        self.cancel()
        self._mode = "countdown"
        self._total = total_seconds
        self._remaining = total_seconds
        self._tick_countdown()

    def _tick_countdown(self):
        if self._total <= 0: return
        fraction = max(0, self._remaining / self._total)
        fill_w = max(self.RADIUS * 2, self._bar_width * fraction)
        self._redraw_fill(fill_w, self._countdown_color(fraction))
        
        mins, secs = divmod(self._remaining, 60)
        self.itemconfig(self._text, text=f"{mins}m {secs:02d}s" if mins > 0 else f"{secs}s")

        if self._remaining <= 0:
            self._mode = "idle"
            return
        self._remaining -= 1
        self._job_id = self.after(1000, self._tick_countdown)

    def _countdown_color(self, fraction: float) -> str:
        if fraction > 0.5: return Colors.ON
        return Colors.TRANSITION if fraction > 0.2 else Colors.OFF

    def start_refill(self, duration_seconds: int, label: str = ""):
        self.cancel()
        self._mode = "refill"
        self._total = duration_seconds
        self._remaining = 0
        self._refill_label = label
        self._tick_refill()

    def _tick_refill(self):
        if self._total <= 0: return
        fraction = min(1.0, self._remaining / self._total)
        fill_w = max(self.RADIUS * 2, self._bar_width * fraction)
        self._redraw_fill(fill_w, Colors.INFO)
        self.itemconfig(self._text, text=self._refill_label or "Preparing...")
        if self._remaining >= self._total:
            self._mode = "idle"
            return
        self._remaining += 1
        self._job_id = self.after(1000, self._tick_refill)

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
#  SVG Diagram Canvas (with Live Animations)
# ─────────────────────────────────────────────────────────────────────────────
class SvgDiagramCanvas(tk.Canvas):
    """
    Renders and animates the system_diagram.svg.
    Uses Native Tkinter renderer for high-performance real-time animations.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent, bg=Colors.BG_DARK, highlightthickness=0, **kwargs
        )
        self._states = {i: False for i in range(1, 8)} 
        self._template_xml = ""
        self._anim_tick = 0
        self._last_w, self._last_h = 0, 0
        
        try:
            with open(_SVG_PATH, "r") as f:
                self._template_xml = f.read()
        except Exception:
            self._template_xml = ""

        self._start_animation()
        self.bind("<Configure>", self._on_resize)

    def update_state(self, channel_id: int, is_on: bool):
        if self._states.get(channel_id) == is_on:
            return
        self._states[channel_id] = is_on
        # No need to refresh immediately, the animation loop handles it

    def _start_animation(self):
        """Update animation tick and redraw."""
        self._anim_tick = (self._anim_tick + 1) % 60
        self._redraw()
        self.after(50, self._start_animation) # 20 FPS

    def _on_resize(self, event):
        if event:
            self._last_w, self._last_h = event.width, event.height
        self._redraw()

    def _redraw(self):
        """Main redraw loop."""
        if not self._template_xml or self._last_w == 0:
            return
            
        self.delete("all")
        self._render_native(self._last_w, self._last_h)

    def _render_native(self, canvas_w, canvas_h):
        """Parses and draws SVG nodes with custom animations."""
        try:
            svg_w, svg_h = 900, 560
            scale = min(canvas_w / svg_w, canvas_h / svg_h) * 1.05
            ox = (canvas_w - svg_w * scale) / 2
            oy = (canvas_h - svg_h * scale) / 2

            clean_xml = re.sub(r'xmlns="[^"]+"', '', self._template_xml)
            root = ET.fromstring(clean_xml)

            def process_node(node, tx=0, ty=0, cid=None):
                ltx, lty = tx, ty
                lcid = cid
                
                trans = node.get("transform", "")
                if "translate" in trans:
                    m = re.search(r'translate\(([^,)]+),?([^)]+)?\)', trans)
                    if m:
                        ltx += float(m.group(1))
                        lty += float(m.group(2) or 0)
                
                nid = node.get("id", "")
                if nid.startswith("v_") or nid.startswith("p_"):
                    try: lcid = int(nid.split("_")[1])
                    except: pass

                tag = node.tag
                fill = node.get("fill", "")
                is_on = lcid and self._states.get(lcid, False)

                # ── Custom Animations ───────────────────────────────────────
                
                # 1. Pump Pulsing
                pulse_scale = 1.0
                if tag in ["circle", "rect"] and lcid in [6, 7] and is_on:
                    pulse_scale = 1.0 + 0.08 * math.sin(self._anim_tick * 0.4)

                # 2. Tank Levels (Dynamic fill)
                if nid.endswith("_level"):
                    current_level = 0.8 if nid == "dmf_level" else 0.2
                    # Simulate level movement
                    if self._states.get(6) and nid == "dmf_level": 
                        current_level -= 0.1 * (self._anim_tick / 60) # draining
                    if self._states.get(7) and nid == "uf_level":
                        current_level += 0.1 * (self._anim_tick / 60) # filling
                    current_level = max(0.05, min(0.95, current_level))
                    
                    h_total = float(node.get("height", 0))
                    y_total = float(node.get("y", 0))
                    h_now = h_total * current_level
                    y_now = y_total + (h_total - h_now)
                    
                    x = (float(node.get("x",0)) + ltx) * scale + ox
                    y = y_now * scale + (lty * scale) + oy
                    w = float(node.get("width",0)) * scale
                    h = h_now * scale
                    self.create_rectangle(x, y, x+w, y+h, fill="#00d4ff", stipple="gray50", outline="")

                # ── Drawing ──────────────────────────────────────────────────
                
                color = "#00ff88" if is_on else fill
                if "url(" in str(color): color = "#1a4272"
                
                if tag == "rect":
                    x = (float(node.get("x",0)) + ltx) * scale + ox
                    y = (float(node.get("y",0)) + lty) * scale + oy
                    w = float(node.get("width",0)) * scale * pulse_scale
                    h = float(node.get("height",0)) * scale * pulse_scale
                    if color and color != "none":
                        if is_on:
                            self.create_rectangle(x-1, y-1, x+w+1, y+h+1, outline="#00ff88", width=1)
                        self.create_rectangle(x, y, x+w, y+h, fill=color, outline="", width=0)
                        
                        # Flow Animation
                        flowing, direction = self._get_flow_state(nid)
                        if flowing:
                            self._draw_flow(x, y, w, h, scale, direction)

                elif tag == "circle":
                    cx = (float(node.get("cx",0)) + ltx) * scale + ox
                    cy = (float(node.get("cy",0)) + lty) * scale + oy
                    r = float(node.get("r",0)) * scale * pulse_scale
                    if color and color != "none":
                        self.create_oval(cx-r, cy-r, cx+r, cy+r, fill=color, outline="", width=0)

                elif tag == "ellipse":
                    cx = (float(node.get("cx",0)) + ltx) * scale + ox
                    cy = (float(node.get("cy",0)) + lty) * scale + oy
                    rx = float(node.get("rx",0)) * scale
                    ry = float(node.get("ry",0)) * scale
                    if color and color != "none":
                        self.create_oval(cx-rx, cy-ry, cx+rx, cy+ry, fill=color, outline="", width=0)

                elif tag == "polygon":
                    pts = node.get("points", "").strip().split()
                    coords = []
                    for p in pts:
                        px, py = map(float, p.split(","))
                        coords.extend([(px+ltx)*scale+ox, (py+lty)*scale+oy])
                    if color and color != "none":
                        self.create_polygon(coords, fill=color, outline="", width=0)

                elif tag == "text":
                    tx_x = (float(node.get("x",0)) + ltx) * scale + ox
                    tx_y = (float(node.get("y",0)) + lty) * scale + oy
                    f_size = max(7, int(float(node.get("font-size", 12)) * scale * 0.8))
                    f_color = "#ffffff" if is_on else (node.get("fill") or "#bcd6f0")
                    self.create_text(tx_x, tx_y, text=node.text, fill=f_color, font=("Segoe UI", f_size, "bold"))

                for child in node:
                    process_node(child, ltx, lty, lcid)

            for child in root: process_node(child)

        except Exception as e:
            print(f"Canvas Render Error: {e}")

    def _get_flow_state(self, pipe_id: str) -> tuple[bool, str]:
        """Returns (is_flowing, direction) for a pipe ID."""
        p1 = self._states.get(6)
        p2 = self._states.get(7)
        v1, v2, v3, v4, v5 = [self._states.get(i) for i in range(1, 6)]
        
        # Directions: 'right', 'left', 'down', 'up'
        if pipe_id == "p_dmf_suction_v": return (p1, 'up')
        if pipe_id == "p_dmf_suction_h": return (p1, 'right')
        if pipe_id == "p_feed_line": return (p1 and (v1 or v2), 'right')
        if pipe_id == "p_bypass_v": return (p1 and v2, 'up')
        if pipe_id == "p_bypass_h": return (p1 and v2, 'right')
        if pipe_id == "p_header_v": return (p1 and (v1 or v2), 'up')
        if pipe_id == "p_header_h": return (p1 and (v1 or v2), 'right') # simplified
        if pipe_id == "p_pp2_suction": return (p2, 'down')
        if pipe_id == "p_permeate": return (p1 and v3, 'right')
        if pipe_id == "p_drain": return (p1 and v3, 'down')
        if pipe_id.startswith("p_pp2_disch"): return (p2, 'right' if "h" in pipe_id else 'down')
        
        return (False, 'right')

    def _draw_flow(self, x, y, w, h, scale, direction: str):
        """Draws moving dashes inside a pipe rectangle respecting direction."""
        offset = (self._anim_tick * 2) % 20
        flow_color = "#ffffff"
        dash_len = 8 * scale
        gap_len = 12 * scale
        
        if direction in ['right', 'left']:
            cy = y + h/2
            step = (dash_len + gap_len)
            shift = (offset * scale) if direction == 'right' else (-offset * scale)
            for dx in range(int(-step), int(w + step), int(step)):
                x_pos = x + dx + shift
                if x <= x_pos <= x + w:
                    x_end = min(x + w, x_pos + dash_len) if direction == 'right' else max(x, x_pos - dash_len)
                    self.create_line(x_pos, cy, x_end, cy, fill=flow_color, width=2, capstyle="round")
        else:
            cx = x + w/2
            step = (dash_len + gap_len)
            shift = (offset * scale) if direction == 'down' else (-offset * scale)
            for dy in range(int(-step), int(h + step), int(step)):
                y_pos = y + dy + shift
                if y <= y_pos <= y + h:
                    y_end = min(y + h, y_pos + dash_len) if direction == 'down' else max(y, y_pos - dash_len)
                    self.create_line(cx, y_pos, cx, y_end, fill=flow_color, width=2, capstyle="round")


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
        self._svg_view: bool = get_svg_view_pref()
        self._build()

    def _build(self):
        self._process_label = ttk.Label(self, text="Initializing...", style="Status.TLabel", font=Fonts.HEADING)
        self._process_label.pack(pady=(15, 10))

        self._content_frame = ttk.Frame(self, style="TFrame")
        self._content_frame.pack(fill="both", expand=True)

        self._card_grid = ttk.Frame(self._content_frame, style="TFrame")
        for r_ids in [[1,2,3,4], [5,6,7]]:
            row = ttk.Frame(self._card_grid, style="TFrame")
            row.pack(pady=6)
            for cid in r_ids:
                card = IndicatorCard(row, cid)
                card.pack(side="left", padx=5)
                self._cards[cid] = card

        self._svg_canvas = SvgDiagramCanvas(self._content_frame, width=760, height=300)

        self._progress = RoundedProgressBar(self, width=580)
        self._progress.pack(pady=(15, 5))

        self._time_label = ttk.Label(self, text="", style="Muted.TLabel")
        self._time_label.pack(pady=(0, 4))

        self._toggle_btn = tk.Button(
            self, text=self._toggle_label(), command=self._on_toggle,
            bg=Colors.BG_PANEL, fg=Colors.INFO, activebackground=Colors.BG_SURFACE,
            activeforeground=Colors.INFO, relief="flat", bd=0, padx=10, pady=4,
            font=("Segoe UI", 9, "bold"), cursor="hand2"
        )
        self._toggle_btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        self._apply_view()

    def _toggle_label(self) -> str:
        return "🗺  Diagram View" if not self._svg_view else "⚙  Status View"

    def _on_toggle(self):
        self._svg_view = not self._svg_view
        set_svg_view_pref(self._svg_view)
        self._toggle_btn.config(text=self._toggle_label())
        self._apply_view()

    def _apply_view(self):
        if self._svg_view:
            self._card_grid.pack_forget()
            self._svg_canvas.pack(fill="both", expand=True, padx=10)
        else:
            self._svg_canvas.pack_forget()
            self._card_grid.pack(expand=True)

    def on_process_start(self, name: str, duration_ms: int = 0):
        display = name.replace("_", " ").title()
        self._process_label.config(text=f">>  {display}  —  Opening valves", foreground=Colors.TRANSITION)
        self._progress.start_refill(5, label="Opening valves...")

    def on_pump_start(self, name: str, countdown_ms: int = 0):
        display = name.replace("_", " ").title()
        self._process_label.config(text=f">>  {display}  —  Running", foreground=Colors.ON)
        if countdown_ms > 0: self._progress.start_countdown(countdown_ms // 1000)

    def on_process_end(self, name: str):
        self._process_label.config(text=f"OK  {name.replace('_',' ').title()} complete", foreground=Colors.TEXT_MUTED)
        self._progress.reset()

    def on_valve_change(self, channel_id: int, is_on: bool):
        if channel_id in self._cards: self._cards[channel_id].set_state(is_on)
        self._svg_canvas.update_state(channel_id, is_on)

    def go_back(self):
        if self._back_locked: return
        self._back_locked = True
        self._progress.reset()
        self.app.process_manager.stop_current_process(callback=self._on_fully_stopped)

    def _on_fully_stopped(self):
        for card in self._cards.values(): card.set_state(False)
        for cid in range(1, 8): self._svg_canvas.update_state(cid, False)
        self._back_locked = False
        self.app.show_frame("select")

    def on_show(self):
        self.app.topbar.set_subtitle("Auto Cycle")
        for card in self._cards.values(): card.set_state(False)
        for cid in range(1, 8): self._svg_canvas.update_state(cid, False)
        self._progress.reset()
        self._svg_view = get_svg_view_pref()
        self._toggle_btn.config(text=self._toggle_label())
        self._apply_view()
