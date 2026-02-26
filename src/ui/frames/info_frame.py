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

from src.ui.theme import Colors

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SVG_PATH = _PROJECT_ROOT / "branding" / "system_diagram.svg"

# These y-values identify the separator lines we want to skip (SVG coords)
_SKIP_LINE_Y = {72.0, 542.0}
# Footer text that belongs to the original SVG branding
_SKIP_TEXT = {"Process Flow Diagram · Raj Enterprices · v1.0"}


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

        try:
            self._xml = _SVG_PATH.read_text(encoding="utf-8")
            self._parse_gradients()
        except Exception:
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
    def _render(self, cw, ch):
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
            # Confirm it contains the company name text
            for child in node.iter():
                if child.tag == "text" and child.text and "Raj" in child.text:
                    return True
            return False

        def draw(node, tx=0.0, ty=0.0):
            # Skip branding group
            if node.tag == "g" and is_branding_group(node):
                return

            # Parse transform="translate(x,y)"
            trans = node.get("transform", "")
            if "translate" in trans:
                m = re.search(r'translate\(([^,)]+),?\s*([^)]+)?\)', trans)
                if m:
                    tx += float(m.group(1))
                    ty += float(m.group(2) or 0)

            tag = node.tag
            fill = resolve_color(node.get("fill", ""))
            stroke = node.get("stroke", "")
            sw = float(node.get("stroke-width", 0) or 0)

            def sx(v): return (float(v) + tx) * scale + ox
            def sy(v): return (float(v) + ty) * scale + oy
            def ss(v): return float(v) * scale

            if tag == "rect":
                # Skip the SVG border outline rect (fill=none, stroke=dark)
                if node.get("fill") == "none" and node.get("stroke") == "#101a2e":
                    return
                x, y = sx(node.get("x", 0)), sy(node.get("y", 0))
                w, h = ss(node.get("width", 0)), ss(node.get("height", 0))
                kw = dict(outline=stroke if stroke else "", width=ss(sw) if sw else 0)
                if fill: kw["fill"] = fill
                self.create_rectangle(x, y, x + w, y + h, **kw)

            elif tag in ("circle", "ellipse"):
                if tag == "circle":
                    cx, cy, rx, ry = sx(node.get("cx", 0)), sy(node.get("cy", 0)), ss(node.get("r", 0)), ss(node.get("r", 0))
                else:
                    cx, cy, rx, ry = sx(node.get("cx", 0)), sy(node.get("cy", 0)), ss(node.get("rx", 0)), ss(node.get("ry", 0))
                kw = dict(outline=stroke if stroke else "", width=ss(sw) if sw else 0)
                if fill: kw["fill"] = fill
                self.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, **kw)

            elif tag == "polygon":
                pts_raw = node.get("points", "").strip().split()
                coords = []
                for p in pts_raw:
                    if "," in p:
                        px, py = p.split(",")
                        coords.extend([sx(px), sy(py)])
                if coords and fill:
                    self.create_polygon(coords, fill=fill, outline="", width=0)

            elif tag == "line":
                # Skip the header and footer separator lines
                y1 = float(node.get("y1", -1))
                y2 = float(node.get("y2", -1))
                if y1 in _SKIP_LINE_Y or y2 in _SKIP_LINE_Y:
                    return
                self.create_line(
                    sx(node.get("x1", 0)), sy(node.get("y1", 0)),
                    sx(node.get("x2", 0)), sy(node.get("y2", 0)),
                    fill=stroke or "#ffffff", width=max(1, ss(sw))
                )

            elif tag == "text":
                txt = node.text or ""
                # Skip SVG's own footer text
                if txt in _SKIP_TEXT:
                    return
                fsize = max(7, int(float(node.get("font-size", 12)) * scale * 0.85))
                fcolor = node.get("fill", "#c0d8f0") or "#c0d8f0"
                anchor_map = {"middle": "center", "start": "w", "end": "e"}
                anchor = anchor_map.get(node.get("text-anchor", "start"), "w")
                self.create_text(
                    sx(node.get("x", 0)), sy(node.get("y", 0)),
                    text=txt, fill=fcolor,
                    font=("DejaVu Sans", fsize, "bold"),
                    anchor=anchor
                )

            elif tag == "path":
                nums = list(map(float, re.findall(r'-?\d+\.?\d*', node.get("d", ""))))
                coords = []
                for i in range(0, len(nums) - 1, 2):
                    coords.extend([sx(nums[i]), sy(nums[i + 1])])
                if len(coords) >= 4:
                    if fill:
                        self.create_polygon(coords, fill=fill, outline="", width=0, smooth=True)
                    if stroke:
                        self.create_line(coords, fill=stroke, width=max(1, ss(sw)), smooth=True)

            for child in node:
                draw(child, tx, ty)

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
            self._viewer._render(w, h)
        else:
            # Retry if dimensions still not ready
            self._viewer.after(100, self._force_redraw)
