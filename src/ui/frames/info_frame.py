"""
info_frame.py — System Diagram Info screen.
Shows the engineering diagram full-screen.
Company branding is drawn as an overlay in the bottom-right corner.
The SVG's own header/footer branding is skipped.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import logging

logger = logging.getLogger("UltraFiltration.Info")

def _find_project_root():
    """Navigate up from this file until we find the 'branding' directory."""
    curr = Path(__file__).resolve().parent
    for _ in range(6):
        if (curr / "branding").exists():
            return curr
        curr = curr.parent
    # Fallback to the old logic if branding folder not found nearby
    return Path(__file__).resolve().parent.parent.parent.parent

_PROJECT_ROOT = _find_project_root()
_SVG_PATH = _PROJECT_ROOT / "branding" / "system_diagram.svg"

# These y-values identify the separator lines we want to skip (SVG coords)
_SKIP_LINE_Y = {72.0, 542.0}
# Footer text that belongs to the original SVG branding
_SKIP_TEXT = {"Process Flow Diagram · Raj Enterprices · v1.0"}

# SVG group positions (translate x,y) → channel_id for live flow highlighting
# Channel 1–5 = valves V1–V5, 6 = PP1, 7 = PP2
_CHANNEL_POSITIONS = {
    (320, 396): 1,   # V1
    (216, 330): 2,   # V2
    (510, 396): 3,   # V3
    (676, 330): 4,   # V4
    (802, 132): 5,   # V5
    (22, 386): 6,    # PP1
    (721, 290): 7,   # PP2
}

# Colors for live state
_LIVE_ON_FILL = "#00cc66"
_LIVE_ON_OUTLINE = "#00ff88"
_LIVE_OFF_FILL = None   # use original
_LIVE_OFF_OUTLINE = None

# Pipe flow animation — high contrast so flow is clearly visible
_PIPE_FLOW_COLOR = "#00ffcc"      # bright neon cyan "water"
_PIPE_FLOW_INTERVAL_MS = 50       # fast update for smooth movement

# Default directions for each pipe segment (0-17)
# (dx, dy): 1 = positive, -1 = negative, 0 = no movement in that axis
_PIPE_DIRECTIONS = {
    0: (0, -1),   # DMF suction (vert) -> UP to pump
    1: (1, 0),    # DMF suction (horiz) -> RIGHT to pump
    2: (1, 0),    # Main feed line -> RIGHT
    3: (0, -1),   # V2 bypass (vert) -> UP
    4: (1, 0),    # V2 bypass (horiz) -> RIGHT
    5: (0, -1),   # UF outlet (vert) -> UP to header
    6: (1, 0),    # Top header -> RIGHT
    7: (0, 1),    # PP2 suction (vert) -> DOWN
    8: (0, 1),    # V5 drop (vert) -> DOWN
    9: (1, 0),    # Permeate line -> RIGHT
    10: (0, 1),   # Drain drop (vert) -> DOWN
    11: (1, 0),   # PP2 discharge (horiz) -> RIGHT
    12: (0, 1),   # PP2 discharge (vert) -> DOWN to tank
    13: (0, 1),   # V4 column (vert) -> DOWN
    14: (-1, 0),  # V4 return (horiz) -> LEFT to permeate
    15: (1, -1),  # Corner elbows...
    16: (1, 1),
    17: (-1, 1),
}

# Pipe segment indices match SVG <g id="pipes"> rect order (0-based).
# Which pipe indices have flow when channel (1–7) is open. Union of active channels = flow path.
_PIPE_FLOW_BY_CHANNEL = {
    6: {0, 1, 2},           # PP1: DMF suction, feed line
    7: {7, 8, 11, 12},      # PP2: suction, V5 drop, discharge to tank
    1: {2, 5, 6, 7},        # V1: feed, UF outlet, top header
    2: {2, 3, 4, 15},       # V2: feed, left bypass, elbow
    3: {2, 9, 10},          # V3: feed, permeate, drain
    4: {6, 7, 13, 14, 17},  # V4: top header, right column, elbow
    5: {6, 7, 8, 16},       # V5: top header, bypass drop, elbow
}


class SvgViewerCanvas(tk.Canvas):
    """
    Lightweight static SVG renderer for the system_diagram.svg.
    - Skips the top-left branding group and footer lines/text.
    - Draws a compact company watermark in the bottom-right corner.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#0b1020", highlightthickness=0, **kwargs)
        self._xml = ""
        self._gradients: dict[str, str] = {}

        logger.debug(f"SVG Search Path: {_SVG_PATH}")

        try:
            if _SVG_PATH.exists():
                self._xml = _SVG_PATH.read_text(encoding="utf-8").strip()
                if self._xml:
                    logger.info(f"Loaded SVG: {_SVG_PATH} ({len(self._xml)} bytes)")
                    self._parse_gradients()
                else:
                    logger.error(f"SVG file is empty: {_SVG_PATH}")
            else:
                logger.error(f"SVG file not found at: {_SVG_PATH}")
                self._xml = ""
        except Exception as e:
            logger.error(f"Error reading SVG: {e}")
            self._xml = ""

        self.bind("<Configure>", self._on_resize)

    # ── Gradient colour extraction ─────────────────────────────────────────
    def _parse_gradients(self):
        clean = re.sub(r'xmlns="[^"]+"', "", self._xml)
        try:
            root = ET.fromstring(clean)
            for grad in root.findall(".//linearGradient"):
                gid = grad.get("id", "")
                stops = grad.findall("stop")
                if stops:
                    mid = len(stops) // 2
                    color = stops[mid].get("stop-color", "#1a4272")
                    self._gradients[f"url(#{gid})"] = color
        except Exception:
            pass

    def _on_resize(self, event):
        self.delete("all")
        if self._xml:
            self._render(event.width, event.height)
        else:
            self.create_text(
                event.width // 2, event.height // 2,
                text="system_diagram.svg not found",
                fill="#ff4444", font=("DejaVu Sans", 14, "bold")
            )

    # ── Core renderer ──────────────────────────────────────────────────────
    def _render(self, cw, ch, channel_items=None, pipe_items=None):
        """Core rendering logic. If channel_items is a dict, it is filled with
        canvas item IDs per channel (1–7). If pipe_items is a list, append (item_id, default_fill)
        for each pipe rect (elements inside <g id="pipes">)."""
        if not self._xml:
            return

        # Expand diagram to fill the full canvas
        svg_w, svg_h = 900, 560
        scale = min(cw / svg_w, ch / svg_h) * 0.97
        ox = (cw - svg_w * scale) / 2
        oy = (ch - svg_h * scale) / 2

        # 1. Draw branding first (independent of SVG parsing)
        self._draw_branding(cw, ch, scale, ox, oy)

        # 2. Try to parse and draw the SVG nodes
        clean = re.sub(r'xmlns="[^"]+"', "", self._xml)
        try:
            root = ET.fromstring(clean)
        except Exception as e:
            print(f"DEBUG: SVG Parse Error: {e}")
            self.create_text(
                cw // 2, ch // 2 + 40,
                text=f"SVG Parse Error: {str(e)[:50]}...",
                fill="#ff8800", font=("DejaVu Sans", 10)
            )
            return

        def resolve_color(fill: str) -> str:
            if not fill or fill == "none": return ""
            if fill.startswith("url("): return self._gradients.get(fill, "#1a4272")
            return fill

        def is_branding_group(node) -> bool:
            """Return True for the top-left <g transform='translate(28,18)'> branding block."""
            trans = node.get("transform", "")
            if "translate(28,18)" not in trans:
                return False
            for child in node.iter():
                if child.tag == "text" and child.text and "Raj" in child.text:
                    return True
            return False

        def record_item(item_id, cid):
            if item_id is not None and cid is not None and channel_items is not None:
                channel_items.setdefault(cid, []).append(item_id)

        def record_pipe_item(item_id, fill_color):
            if item_id is not None and pipe_items is not None and fill_color:
                pipe_items.append((item_id, fill_color, len(pipe_items)))

        def draw(node, tx=0.0, ty=0.0, channel_id=None, in_pipes=False):
            if node.tag == "g" and is_branding_group(node):
                return

            trans = node.get("transform", "")
            next_tx, next_ty = tx, ty
            if "translate" in trans:
                m = re.search(r'translate\(([^,)]+),?\s*([^)]+)?\)', trans)
                if m:
                    next_tx = tx + float(m.group(1))
                    next_ty = ty + float(m.group(2) or 0)

            next_in_pipes = in_pipes or (node.tag == "g" and node.get("id") == "pipes")

            next_channel = channel_id
            if channel_items is not None:
                key = (round(next_tx), round(next_ty))
                if key in _CHANNEL_POSITIONS:
                    next_channel = _CHANNEL_POSITIONS[key]

            tag = node.tag
            fill = resolve_color(node.get("fill", ""))
            stroke = node.get("stroke", "")
            sw = float(node.get("stroke-width", 0) or 0)

            def sx(v): return (float(v) + next_tx) * scale + ox
            def sy(v): return (float(v) + next_ty) * scale + oy
            def ss(v): return float(v) * scale

            if tag == "rect":
                if node.get("fill") == "none" and node.get("stroke") == "#101a2e":
                    pass
                else:
                    x, y = sx(node.get("x", 0)), sy(node.get("y", 0))
                    w, h = ss(node.get("width", 0)), ss(node.get("height", 0))
                    kw = dict(outline=stroke if stroke else "", width=ss(sw) if sw else 0)
                    if fill: kw["fill"] = fill
                    item_id = self.create_rectangle(x, y, x + w, y + h, **kw)
                    record_item(item_id, next_channel)
                    if in_pipes and fill:
                        record_pipe_item(item_id, fill)

            elif tag in ("circle", "ellipse"):
                if tag == "circle":
                    cx, cy, rx, ry = sx(node.get("cx", 0)), sy(node.get("cy", 0)), ss(node.get("r", 0)), ss(node.get("r", 0))
                else:
                    cx, cy, rx, ry = sx(node.get("cx", 0)), sy(node.get("cy", 0)), ss(node.get("rx", 0)), ss(node.get("ry", 0))
                kw = dict(outline=stroke if stroke else "", width=ss(sw) if sw else 0)
                if fill: kw["fill"] = fill
                item_id = self.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, **kw)
                record_item(item_id, next_channel)

            elif tag == "polygon":
                pts_raw = node.get("points", "").strip().split()
                coords = []
                for p in pts_raw:
                    if "," in p:
                        px, py = p.split(",")
                        coords.extend([sx(px), sy(py)])
                if coords and fill:
                    item_id = self.create_polygon(coords, fill=fill, outline="", width=0)
                    record_item(item_id, next_channel)

            elif tag == "line":
                y1 = float(node.get("y1", -1))
                y2 = float(node.get("y2", -1))
                if y1 not in _SKIP_LINE_Y and y2 not in _SKIP_LINE_Y:
                    item_id = self.create_line(
                        sx(node.get("x1", 0)), sy(node.get("y1", 0)),
                        sx(node.get("x2", 0)), sy(node.get("y2", 0)),
                        fill=stroke or "#ffffff", width=max(1, ss(sw))
                    )
                    record_item(item_id, next_channel)

            elif tag == "text":
                txt = (node.text or "").strip()
                if txt not in _SKIP_TEXT:
                    fsize = max(7, int(float(node.get("font-size", 12)) * scale * 0.85))
                    fcolor = node.get("fill", "#c0d8f0") or "#c0d8f0"
                    anchor_map = {"middle": "center", "start": "w", "end": "e"}
                    anchor = anchor_map.get(node.get("text-anchor", "start"), "w")
                    item_id = self.create_text(
                        sx(node.get("x", 0)), sy(node.get("y", 0)),
                        text=txt, fill=fcolor,
                        font=("DejaVu Sans", fsize, "bold"),
                        anchor=anchor
                    )
                    record_item(item_id, next_channel)

            elif tag == "path":
                nums = list(map(float, re.findall(r'-?\d+\.?\d*', node.get("d", ""))))
                coords = []
                for i in range(0, len(nums) - 1, 2):
                    coords.extend([sx(nums[i]), sy(nums[i + 1])])
                if len(coords) >= 4:
                    if fill:
                        item_id = self.create_polygon(coords, fill=fill, outline="", width=0, smooth=True)
                        record_item(item_id, next_channel)
                    if stroke:
                        item_id = self.create_line(coords, fill=stroke, width=max(1, ss(sw)), smooth=True)
                        record_item(item_id, next_channel)

            for child in node:
                draw(child, next_tx, next_ty, next_channel, next_in_pipes)

        for child in root:
            draw(child)

    def _draw_branding(self, cw, ch, scale, ox, oy):
        """Company name only."""
        lx = 28 * scale + ox
        ly = 11 * scale + oy
        lh = 44 * scale   # header zone height

        # ── Company name ──────────────────────────────────────────────────────
        name_size = max(12, round(32 * scale * 0.82))
        self.create_text(
            lx, ly + lh * 0.5,  # Centered vertically in the header zone
            text="Raj Enterprices", anchor="w",
            fill="#d4eaf8", font=("DejaVu Sans", name_size, "bold")
        )


class LiveFlowSvgCanvas(SvgViewerCanvas):
    """
    System diagram viewer with a particle-based live flow engine.
    - Tracks valve/pump states.
    - Solves flow paths based on 'pressure' from pumps.
    - Animates moving 'water slugs' along active pipe segments.
    """

    def __init__(self, parent, **kwargs):
        self._channel_items = {}  # channel_id -> list of canvas item ids
        self._channel_states = {i: False for i in range(1, 8)}
        self._pipe_data = []      # list of (item_id, fill_color, index)
        self._particles = []      # list of {id, pipe_idx, pix_offset, length}
        self._flow_anim_job = None
        super().__init__(parent, **kwargs)

    def _get_active_pipe_indices(self):
        """Solve for active pipe segments based on pump pressure and valve paths."""
        active = set()
        # Primary source: Pump 1 (Channel 6)
        p1_on = self._channel_states[6]
        
        if p1_on:
            active.update([0, 1, 2]) # Suction and main feed line
            # Path through V1 -> UF -> Header
            if self._channel_states[1]:
                active.update([5, 6])
            # Path through V2 bypass -> Header
            if self._channel_states[2]:
                active.update([3, 15, 4, 6])
            # Path through V3 -> Drain
            if self._channel_states[3]:
                active.update([9, 10])

        # Header has pressure if either V1 or V2 bypass is open + Pump 1 is on
        header_press = p1_on and (self._channel_states[1] or self._channel_states[2])
        
        if header_press:
            # Power users of the header
            if self._channel_states[7]: # PP2 discharge
                active.update([7, 11, 12])
            if self._channel_states[4]: # V4 flush
                active.update([13, 17, 14, 9, 10])
            if self._channel_states[5]: # V5 fill
                active.update([16, 8])
                
        return active

    def _on_resize(self, event):
        self._stop_flow()
        self.delete("all")
        self._channel_items = {i: [] for i in range(1, 8)}
        self._pipe_data = []
        self._particles = []

        if event.width < 10 or event.height < 10: return
        if not self._xml: return

        # Render returns pipe info into self._pipe_data
        self._render(
            event.width, event.height,
            channel_items=self._channel_items,
            pipe_items=self._pipe_data
        )
        
        # After rendering, we know where all pipes are.
        self._create_flow_particles()
        
        # Raise valve/pump items ABOVE the particles
        for item_list in self._channel_items.values():
            for item_id in item_list:
                self.tag_raise(item_id)
        
        # Restore state
        for cid, is_on in self._channel_states.items():
            self._apply_channel_style(cid, is_on)
        self._update_animation()

    def _render(self, cw, ch, channel_items=None, pipe_items=None):
        super()._render(cw, ch, channel_items, pipe_items)

    def _create_flow_particles(self):
        """Create hidden water slugs for every pipe segment."""
        self._particles = []
        for pipe in self._pipe_data:
            item_id, _, idx = pipe
            coords = self.coords(item_id)
            if len(coords) < 4: continue
            
            x1, y1, x2, y2 = coords
            pw, ph = x2-x1, y2-y1
            length = max(pw, ph)
            
            # Create 3 slugs per pipe segment
            for i in range(3):
                # Slug size: elongated in direction of flow
                if pw > ph: # Horizontal pipe
                    sw, sh = min(20, length*0.3), ph*0.6
                else: # Vertical pipe
                    sw, sh = pw*0.6, min(20, length*0.3)
                
                slug = self.create_rectangle(
                    0, 0, sw, sh,
                    fill=_PIPE_FLOW_COLOR, outline="", width=0,
                    state="hidden"
                )
                self._particles.append({
                    "id": slug,
                    "pipe_idx": idx,
                    "pix_offset": i * (length / 3.0),
                    "length": length,
                    "rect": (x1, y1, x2, y2)
                })

    def _tick_pipe_flow(self):
        """Move particles along active pipes with consistent pixel speed."""
        active = self._get_active_pipe_indices()
        # Get scale from a known pipe or just use 1.0 (speed feels more natural if constant)
        move_pixels = 4.0 
        
        for p in self._particles:
            idx = p["pipe_idx"]
            if idx in active:
                self.itemconfig(p["id"], state="normal")
                # Update pixel offset
                p["pix_offset"] = (p["pix_offset"] + move_pixels) % p["length"]
                
                x1, y1, x2, y2 = p["rect"]
                pw, ph = x2 - x1, y2 - y1
                dx, dy = _PIPE_DIRECTIONS.get(idx, (1, 0))
                
                sc = self.coords(p["id"])
                sw, sh = sc[2]-sc[0], sc[3]-sc[1]

                # Calculate current position based on direction
                if dx == 1: # Right
                    cx, cy = x1 + p["pix_offset"] - sw/2, y1 + ph/2 - sh/2
                elif dx == -1: # Left
                    cx, cy = x2 - p["pix_offset"] - sw/2, y1 + ph/2 - sh/2
                elif dy == 1: # Down
                    cx, cy = x1 + pw/2 - sw/2, y1 + p["pix_offset"] - sh/2
                else: # Up
                    cx, cy = x1 + pw/2 - sw/2, y2 - p["pix_offset"] - sh/2
                
                # Constrain to pipe bounds
                cx = max(x1, min(x2 - sw, cx))
                cy = max(y1, min(y2 - sh, cy))
                
                self.coords(p["id"], cx, cy, cx + sw, cy + sh)
            else:
                self.itemconfig(p["id"], state="hidden")
        
        self._flow_anim_job = self.after(_PIPE_FLOW_INTERVAL_MS, self._tick_pipe_flow)

    def _update_animation(self):
        if any(self._channel_states.values()):
            if not self._flow_anim_job:
                self._tick_pipe_flow()
        else:
            self._stop_flow()

    def _stop_flow(self):
        if self._flow_anim_job:
            self.after_cancel(self._flow_anim_job)
            self._flow_anim_job = None
        for p in self._particles:
            self.itemconfig(p["id"], state="hidden")

    def _apply_channel_style(self, cid, is_on):
        """Highlight active pumps/valves."""
        for item_id in self._channel_items.get(cid, []):
            try:
                if is_on:
                    self.itemconfig(item_id, fill=_LIVE_ON_FILL, outline=_LIVE_ON_OUTLINE)
                else:
                    self.itemconfig(item_id, fill="#152858", outline="#00d4ff")
            except tk.TclError: pass

    def update_channel_state(self, channel_id, is_on):
        if 1 <= channel_id <= 7:
            self._channel_states[channel_id] = is_on
            self._apply_channel_style(channel_id, is_on)
            self._update_animation()

    def _refresh_after_show(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        if w > 10 and h > 10:
            class Ev: pass
            e = Ev()
            e.width, e.height = w, h
            self._on_resize(e)


class InfoFrame(ttk.Frame):
    """Full-screen system diagram with branding in the corner."""

    def __init__(self, parent, app):
        super().__init__(parent, style="TFrame")
        self.app = app
        self._viewer = SvgViewerCanvas(self)
        self._viewer.pack(fill="both", expand=True)

    def on_show(self):
        self.app.topbar.set_subtitle("System Info")
        # Ensure dimensions are updated before rendering
        self.update_idletasks()
        self._viewer.after(100, self._force_redraw)

    def _force_redraw(self):
        w = self._viewer.winfo_width()
        h = self._viewer.winfo_height()
        if w > 1 and h > 1:
            self._viewer.delete("all")
            if self._viewer._xml:
                self._viewer._render(w, h)
            else:
                # If XML is missing, at least draw the branding
                scale = min(w / 900, h / 560) * 0.97
                ox = (w - 900 * scale) / 2
                oy = (h - 560 * scale) / 2
                self._viewer._draw_branding(w, h, scale, ox, oy)
        else:
            # Retry if dimensions still not ready
            self._viewer.after(100, self._force_redraw)


