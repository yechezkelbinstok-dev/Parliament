#!/usr/bin/env python3
"""Draw a seating plan seat by seat: one dot per member, where they actually sit.

For chambers that are not a hemicycle or Westminster benches (such as the
Knesset's plenum), the seats are given as straight blocks:

    party: Likud, #1f5aa5
    block: Back row 1 | 151.4,56 | 944.6,56
    Likud: Member's name
    -

"block: name | x,y | x,y" is a line of seats from the first seat's centre to
the last one's; the seat lines that follow fill it in order. A seat line is
"Party: member" or "-" for a seat with no member (it keeps its place but gets
no dot). Lines starting with "#" are comments. Settings: "title: ...",
"radius: 13" (dot radius), "center: 548" (centre line; frames the plan
symmetrically around it), "legend: yes/no".
"""

import argparse
from html import escape
from math import ceil
from pathlib import Path
import sys

MARGIN = 8
TITLE_FONT_SIZE = 22
LEGEND_FONT_SIZE = 15
LEGEND_ROW_HEIGHT = 22
LEGEND_COLUMNS = 3
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "diagrams"


def parse_point(text: str) -> tuple[float, float]:
    x, y = text.split(",")
    return float(x), float(y)


def parse_input(text: str, overrides: list[str] = ()) -> tuple[dict, list, dict]:
    """Return (parties name -> colour, seats [(x, y, party, member)], settings)."""
    settings = {"title": "", "radius": 13.0, "center": None, "legend": True}
    parties, seats = {}, []
    block = None  # [name, start, end, seat lines]

    def close_block():
        if block is None:
            return
        name, (x1, y1), (x2, y2), lines = block
        if not lines:
            raise SystemExit(f"block {name!r} has no seats")
        n = len(lines)
        for i, line in enumerate(lines):
            t = i / (n - 1) if n > 1 else 0
            x, y = x1 + t * (x2 - x1), y1 + t * (y2 - y1)
            if line != "-":
                party, member = (s.strip() for s in line.split(":", 1))
                if party not in parties:
                    raise SystemExit(f"unknown party {party!r} in block {name!r}")
                seats.append((x, y, party, member))

    def apply_setting(key: str, value: str) -> bool:
        if key == "title":
            settings["title"] = value
        elif key == "radius":
            settings["radius"] = float(value)
        elif key == "center":
            settings["center"] = float(value) if value else None
        elif key == "legend":
            settings["legend"] = value.lower() in ("yes", "true", "1", "on")
        else:
            return False
        return True

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "party":
            name, colour = (s.strip() for s in value.rsplit(",", 1))
            parties[name] = colour
        elif key == "block":
            close_block()
            name, start, end = (s.strip() for s in value.split("|"))
            block = [name, parse_point(start), parse_point(end), []]
        elif block is None and apply_setting(key, value):
            pass
        elif block is not None:
            block[3].append(line)
        else:
            raise SystemExit(f"cannot read line: {raw!r}")
    close_block()
    for override in overrides:
        key, _, value = override.partition("=")
        if not apply_setting(key.strip().lower(), value.strip()):
            raise SystemExit(f"unknown setting {key!r}")
    return parties, seats, settings


def build_svg(parties: dict, seats: list, settings: dict) -> str:
    r = settings["radius"]
    xs, ys = [s[0] for s in seats], [s[1] for s in seats]
    left, right = min(xs) - r - MARGIN, max(xs) + r + MARGIN
    if settings["center"] is not None:  # frame symmetrically around the centre line
        half = max(settings["center"] - left, right - settings["center"])
        left, right = settings["center"] - half, settings["center"] + half
    top, bottom = min(ys) - r - MARGIN, max(ys) + r + MARGIN
    width = right - left

    counts = {p: sum(1 for s in seats if s[2] == p) for p in parties}
    shown = [p for p in parties if counts[p]]
    title_h = TITLE_FONT_SIZE + 16 if settings["title"] else 0
    legend_rows = ceil(len(shown) / LEGEND_COLUMNS) if settings["legend"] else 0
    legend_h = legend_rows * LEGEND_ROW_HEIGHT + 12 if legend_rows else 0
    height = (bottom - top) + title_h + legend_h

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" width="{width:.0f}" height="{height:.0f}" '
           f'viewBox="{left:.2f} {top - title_h:.2f} {width:.2f} {height:.2f}">',
           "    <!-- Created with seating_plan.py -->"]
    if settings["title"]:
        out.append(f'    <text x="{left + width / 2:.2f}" y="{top - title_h + TITLE_FONT_SIZE + 4:.2f}" '
                   f'style="font-size:{TITLE_FONT_SIZE}px;font-weight:bold;text-anchor:middle;font-family:sans-serif">'
                   f'{escape(settings["title"])}</text>')
    for p in shown:
        out.append(f'    <g style="fill:{parties[p]}" id="{escape(p.replace(" ", "-").replace(chr(39), ""))}">')
        out.append(f"        <title>{escape(p)} ({counts[p]})</title>")
        for x, y, party, member in seats:
            if party == p:
                out.append(f'        <circle cx="{x:.2f}" cy="{y:.2f}" r="{r:.2f}"><title>{escape(member)} ({escape(p)})</title></circle>')
        out.append("    </g>")
    if legend_rows:
        col_w = (width - 2 * MARGIN) / LEGEND_COLUMNS
        y0 = bottom + 8
        out.append(f'    <g style="font-size:{LEGEND_FONT_SIZE}px;font-family:sans-serif">')
        for i, p in enumerate(shown):  # column by column, so it reads top to bottom
            col, row = divmod(i, legend_rows)
            x = left + MARGIN + col * col_w
            y = y0 + row * LEGEND_ROW_HEIGHT
            out.append(f'        <circle cx="{x + 7:.2f}" cy="{y + 8:.2f}" r="7" style="fill:{parties[p]}"/>')
            out.append(f'        <text x="{x + 20:.2f}" y="{y + 13:.2f}">{escape(p)} ({counts[p]})</text>')
        out.append("    </g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="seating plan file")
    parser.add_argument("-o", "--output", type=Path, help="output SVG (default: diagrams/<input name>.svg)")
    parser.add_argument("-s", "--set", action="append", default=[], metavar="KEY=VALUE",
                        help="override a setting from the file, e.g. -s legend=no -s title= (repeatable)")
    parser.add_argument("--png", action="store_true", help="also write a PNG next to the SVG (needs cairosvg)")
    parser.add_argument("--scale", type=float, default=2, help="PNG size multiplier (default: 2)")
    args = parser.parse_args()

    parties, seats, settings = parse_input(args.input.read_text(encoding="utf-8"), args.set)
    output = args.output or DEFAULT_OUTPUT_DIR / (args.input.stem + ".svg")
    svg = build_svg(parties, seats, settings)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    counts = ", ".join(f"{p} {sum(1 for s in seats if s[2] == p)}" for p in parties)
    print(f"wrote {output} ({len(seats)} seats: {counts})")
    if args.png:
        try:
            import cairosvg
        except ImportError:
            print("error: PNG export needs cairosvg (pip install cairosvg)", file=sys.stderr)
            return 1
        png = output.with_suffix(".png")
        cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png), scale=args.scale, background_color="white")
        print(f"wrote {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
