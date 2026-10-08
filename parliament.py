#!/usr/bin/env python3
"""Make a hemicycle parliament diagram from a plain-text list of parties.

Each party goes on its own line, in seating order from left to right:

    Party name, seats, color

The color can be a hex code (#E4003B, E4003B) or a CSS color name (red).
Lines starting with "#" are comments. Optional settings can be given as
"key: value" lines (see SETTINGS below), e.g. "title: House of Commons 2024".

Seat layout is done by parliamentarch, the library behind
https://parliamentdiagram.toolforge.org (github.com/slashme/parliamentdiagram).
"""

import argparse
from html import escape
from math import ceil
from pathlib import Path
import re
import sys

from parliamentarch.geometry import FillingStrategy, get_nrows_from_nseats, get_row_thickness, get_seats_centers
from parliamentarch.svg import SeatData, dispatch_seats, get_grouped_svg

CANVAS_SIZE = 175  # parliamentarch's default: diagram is 2*CANVAS_SIZE wide
MARGIN = 5
SEAT_RADIUS_FACTOR = 0.8  # 1 = neighboring seats touch
TITLE_FONT_SIZE = 14
LEGEND_FONT_SIZE = 9
LEGEND_ROW_HEIGHT = 13
SWATCH_SIZE = 8
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "diagrams"

# setting name -> (type, default)
SETTINGS = {
    "title": (str, ""),
    "rows": (int, 0),         # minimum number of rows; more rows = sparser
    "dense": (bool, False),   # fill outer rows first, leaving inner rows empty
    "span": (float, 180.0),   # arc angle in degrees (180 = half circle)
    "legend": (bool, True),
    "number": (bool, True),   # total seat count in the middle
}
SETTING_LINE = re.compile(rf"^\s*({'|'.join(SETTINGS)})\s*:\s*(.*)$", re.IGNORECASE)
HEX_COLOR = re.compile(r"^#?([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


class InputError(Exception):
    pass


def parse_bool(value: str) -> bool:
    lowered = value.strip().lower()
    if lowered in ("yes", "true", "on", "1"):
        return True
    if lowered in ("no", "false", "off", "0"):
        return False
    raise ValueError(f"expected yes/no, got {value!r}")


def normalize_color(color: str) -> str:
    color = color.strip()
    if HEX_COLOR.match(color):
        return "#" + color.removeprefix("#")
    if re.fullmatch(r"[a-zA-Z]+", color):
        return color.lower()  # CSS color name
    raise ValueError(f"not a hex code or color name: {color!r}")


def parse_input(text: str) -> tuple[list[tuple[str, int, str]], dict]:
    """Return ([(name, seats, color), ...], settings) from the input text."""
    parties = []
    settings = {key: default for key, (_, default) in SETTINGS.items()}

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        if match := SETTING_LINE.match(line):
            key, value = match.group(1).lower(), match.group(2).strip()
            kind = SETTINGS[key][0]
            try:
                settings[key] = parse_bool(value) if kind is bool else kind(value)
            except ValueError as e:
                raise InputError(f"line {lineno}: bad value for {key}: {e}") from None
            continue

        # Split from the right so party names may contain commas.
        fields = [f.strip() for f in line.rsplit(",", 2)]
        if len(fields) != 3 or not fields[0]:
            raise InputError(f"line {lineno}: expected 'Party name, seats, color', got {raw!r}")
        name, seats, color = fields
        try:
            seats = int(seats)
        except ValueError:
            raise InputError(f"line {lineno}: seat count must be a whole number, got {seats!r}") from None
        if seats < 0:
            raise InputError(f"line {lineno}: seat count can't be negative")
        try:
            color = normalize_color(color)
        except ValueError as e:
            raise InputError(f"line {lineno}: {e}") from None
        parties.append((name, seats, color))

    if not 0 < settings["span"] <= 180:
        raise InputError("span must be between 0 and 180 degrees")
    if not parties:
        raise InputError("no parties found")
    if sum(seats for _, seats, _ in parties) == 0:
        raise InputError("total number of seats is 0")
    return parties, settings


def legend_layout(labels: list[str]) -> tuple[int, float]:
    """Return (columns, column width) so the legend fits under the diagram."""
    char_width = LEGEND_FONT_SIZE * 0.6  # rough average for sans-serif
    item_width = SWATCH_SIZE + 4 + max(len(label) for label in labels) * char_width + 12
    available = 2 * CANVAS_SIZE
    ncols = max(1, min(len(labels), int(available // item_width)))
    return ncols, min(item_width, available / ncols)


def build_svg(parties: list[tuple[str, int, str]], settings: dict) -> str:
    shown = [(name, seats, color) for name, seats, color in parties if seats > 0]
    title = settings["title"]

    top = MARGIN + (TITLE_FONT_SIZE + 10 if title else 0)
    legend_items = []
    bottom = MARGIN
    if settings["legend"]:
        labels = [f"{name} ({seats})" for name, seats, _ in shown]
        ncols, col_width = legend_layout(labels)
        nrows = ceil(len(labels) / ncols)
        bottom = MARGIN + 10 + nrows * LEGEND_ROW_HEIGHT
        legend_items = (labels, ncols, nrows, col_width)

    # Same steps as parliamentarch.get_svg_from_attribution, except the seat size
    # accounts for the "rows" and "span" settings (upstream ignores them there,
    # which makes seats overlap).
    nseats = sum(seats for _, seats, _ in shown)
    nrows = max(settings["rows"], get_nrows_from_nseats(nseats, settings["span"]))
    centers = get_seats_centers(
        nseats,
        min_nrows=settings["rows"],
        filling_strategy=FillingStrategy.EMPTY_INNER if settings["dense"] else FillingStrategy.DEFAULT,
        span_angle=settings["span"],
    )
    attrib = {SeatData(name, color): seats for name, seats, color in shown}
    seats_by_party = dispatch_seats(attrib, sorted(centers, key=centers.__getitem__, reverse=True))
    svg = get_grouped_svg(
        seats_by_party,
        SEAT_RADIUS_FACTOR * get_row_thickness(nrows),
        canvas_size=CANVAS_SIZE,
        margins=(MARGIN, top, MARGIN, bottom),
        write_number_of_seats=settings["number"],
    )

    extra = []
    width = 2 * CANVAS_SIZE + 2 * MARGIN
    if title:
        extra.append(
            f'\n    <text x="{width / 2}" y="{MARGIN + TITLE_FONT_SIZE}" '
            f'style="font-size:{TITLE_FONT_SIZE}px;font-weight:bold;text-anchor:middle;'
            f'font-family:sans-serif">{escape(title)}</text>'
        )
    if legend_items:
        labels, ncols, nrows, col_width = legend_items
        x0 = MARGIN + (2 * CANVAS_SIZE - ncols * col_width) / 2
        y0 = top + CANVAS_SIZE + 10
        extra.append('\n    <g style="font-size:%spx;font-family:sans-serif">' % LEGEND_FONT_SIZE)
        # Fill column by column so the legend reads top-to-bottom in seating order.
        for i, (label, (_, _, color)) in enumerate(zip(labels, shown)):
            col, row = divmod(i, nrows)
            x = x0 + col * col_width
            y = y0 + row * LEGEND_ROW_HEIGHT
            extra.append(
                f'\n        <rect x="{x:.2f}" y="{y:.2f}" width="{SWATCH_SIZE}" height="{SWATCH_SIZE}" '
                f'rx="1.5" style="fill:{color};stroke:#888;stroke-width:0.5"/>'
                f'\n        <text x="{x + SWATCH_SIZE + 4:.2f}" y="{y + SWATCH_SIZE - 0.5:.2f}">{escape(label)}</text>'
            )
        extra.append("\n    </g>")

    head, tail = svg.rsplit("</svg>", 1)
    return head.rstrip() + "".join(extra) + "\n</svg>" + tail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="text file listing the parties")
    parser.add_argument("-o", "--output", type=Path,
                        help="SVG file to write (default: diagrams/<input name>.svg)")
    parser.add_argument("--png", action="store_true", help="also write a PNG next to the SVG (needs cairosvg)")
    parser.add_argument("--scale", type=float, default=4, help="PNG size multiplier (default: 4)")
    args = parser.parse_args()

    try:
        parties, settings = parse_input(args.input.read_text(encoding="utf-8"))
    except (OSError, InputError) as e:
        print(f"error: {args.input}: {e}", file=sys.stderr)
        return 1

    svg = build_svg(parties, settings)
    output = args.output or DEFAULT_OUTPUT_DIR / f"{args.input.stem}.svg"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    print(f"wrote {output} ({sum(s for _, s, _ in parties)} seats, {len(parties)} parties)")

    if args.png:
        try:
            import cairosvg
        except ImportError:
            print("error: PNG export needs cairosvg (pip install cairosvg)", file=sys.stderr)
            return 1
        png = output.with_suffix(".png")
        cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(png),
                         scale=args.scale, background_color="white")
        print(f"wrote {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
