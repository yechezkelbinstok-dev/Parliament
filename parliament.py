#!/usr/bin/env python3
"""Make a parliament diagram from a plain-text list of parties.

Each party goes on its own line, in seating order:

    Party name, seats, color
    Party name, seats, color, bench     (Westminster style)

The color can be a hex code (#E4003B, E4003B) or a CSS color name (red).
Lines starting with "#" are comments. Optional settings can be given as
"key: value" lines (see SETTINGS below), e.g. "title: House of Commons 2024".

Two styles, the same as https://parliamentdiagram.toolforge.org
(github.com/slashme/parliamentdiagram):
- arch (default): a hemicycle, parties seated left to right. Seat layout
  is done by parliamentarch, the library that tool uses.
- westminster: two facing wings (government and opposition), an optional
  cross-bench and the Speaker. Seat layout is that tool's westminster.py.
"""

import argparse
from html import escape
from math import ceil
from pathlib import Path
import re
import sys

from parliamentarch.geometry import FillingStrategy, get_nrows_from_nseats, get_row_thickness, get_seats_centers
from parliamentarch.svg import SeatData, dispatch_seats, get_grouped_svg

import westminster

CANVAS_SIZE = 175  # parliamentarch's default: arch diagram is 2*CANVAS_SIZE wide
MARGIN = 5
MIN_WIDTH = 2 * CANVAS_SIZE + 2 * MARGIN
SEAT_RADIUS_FACTOR = 0.8  # 1 = neighboring seats touch
TITLE_FONT_SIZE = 14
LEGEND_FONT_SIZE = 9
LEGEND_ROW_HEIGHT = 13
SWATCH_SIZE = 8
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "diagrams"

STYLES = ("arch", "westminster")
# Westminster bench name -> group name used by westminster.py.
# The Speaker sits at the left end, so the government (on the Speaker's right)
# is the bottom wing and the opposition the top wing.
BENCHES = {
    "government": "right",
    "opposition": "left",
    "crossbench": "center",
    "speaker": "head",
}

# setting name -> (type, default)
SETTINGS = {
    "title": (str, ""),
    "style": (str, "arch"),
    "legend": (bool, True),
    # arch style
    "rows": (int, 0),         # minimum number of rows; more rows = sparser
    "dense": (bool, False),   # fill outer rows first, leaving inner rows empty
    "span": (float, 180.0),   # arc angle in degrees (180 = half circle)
    "number": (bool, True),   # total seat count in the middle
    # westminster style (defaults match the upstream web form)
    "corners": (float, 1.0),  # corner radius: 0 = squares, 0.5 or more = circles
    "spacing": (float, 0.1),  # gap between seats: 0 = touching, up to 0.99
    "wingrows": (int, 0),     # rows per wing; 0 = automatic
    "crossbench-columns": (int, 0),  # 0 = automatic
    "fullwidth": (bool, False),  # make the smaller wing thinner so both span the full width
    "cozy": (bool, True),     # let parties share a column
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


def parse_input(text: str) -> tuple[list[tuple[str, int, str, str | None]], dict]:
    """Return ([(name, seats, color, bench), ...], settings) from the input text."""
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

        # Optional trailing bench, then split from the right so party names may contain commas.
        bench = None
        rest, _, last = line.rpartition(",")
        if last.strip().lower() in BENCHES:
            bench, line = last.strip().lower(), rest
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
        parties.append((name, seats, color, bench))

    settings["style"] = settings["style"].lower()
    if settings["style"] not in STYLES:
        raise InputError(f"style must be one of: {', '.join(STYLES)}")
    if settings["style"] == "westminster":
        for name, seats, _, bench in parties:
            if bench is None and seats:
                raise InputError(f"Westminster style needs a bench at the end of each party line "
                                 f"({', '.join(BENCHES)}); missing for {name!r}")
    if not 0 < settings["span"] <= 180:
        raise InputError("span must be between 0 and 180 degrees")
    if not parties:
        raise InputError("no parties found")
    if sum(p[1] for p in parties) == 0:
        raise InputError("total number of seats is 0")
    return parties, settings


def arch_svg(shown: list, settings: dict) -> tuple[str, float, float]:
    # Same steps as parliamentarch.get_svg_from_attribution, except the seat size
    # accounts for the "rows" and "span" settings (upstream ignores them there,
    # which makes seats overlap).
    nseats = sum(seats for _, seats, _, _ in shown)
    nrows = max(settings["rows"], get_nrows_from_nseats(nseats, settings["span"]))
    centers = get_seats_centers(
        nseats,
        min_nrows=settings["rows"],
        filling_strategy=FillingStrategy.EMPTY_INNER if settings["dense"] else FillingStrategy.DEFAULT,
        span_angle=settings["span"],
    )
    attrib = {SeatData(name, color): seats for name, seats, color, _ in shown}
    seats_by_party = dispatch_seats(attrib, sorted(centers, key=centers.__getitem__, reverse=True))
    svg = get_grouped_svg(
        seats_by_party,
        SEAT_RADIUS_FACTOR * get_row_thickness(nrows),
        canvas_size=CANVAS_SIZE,
        margins=MARGIN,
        write_number_of_seats=settings["number"],
    )
    return svg, 2 * CANVAS_SIZE + 2 * MARGIN, CANVAS_SIZE + 2 * MARGIN


def westminster_svg(shown: list, settings: dict) -> tuple[str, float, float]:
    spacing = max(0.0, min(settings["spacing"], 0.99))
    parties = {westminster.Party(name, seats, BENCHES[bench], color): 0
               for name, seats, color, bench in shown}
    sumdelegates = dict.fromkeys(("left", "right", "center", "head"), 0)
    for party in parties:
        sumdelegates[party.group] += party.num

    poslist, wingrows, radius, blocksize, width, height = westminster.seats(
        parties=parties,
        sumdelegates=sumdelegates,
        option_wingrows=settings["wingrows"] or None,
        cozy=settings["cozy"],
        fullwidth=settings["fullwidth"],
        centercols_raw=settings["crossbench-columns"] or None,
        option_radius=max(0.0, settings["corners"]),
        option_spacing=spacing,
    )
    svg = westminster.build_svg(
        parties=parties,
        poslist=poslist,
        blockside=blocksize * (1 - spacing),
        wingrows=wingrows,
        fullwidth_or_cozy=settings["fullwidth"] or settings["cozy"],
        radius=radius,
        svgwidth=width,
        svgheight=height,
    )
    return svg, width, height


def legend_layout(labels: list[str], available: float) -> tuple[int, float]:
    """Return (columns, column width) so the legend fits in the available width."""
    char_width = LEGEND_FONT_SIZE * 0.6  # rough average for sans-serif
    item_width = SWATCH_SIZE + 4 + max(len(label) for label in labels) * char_width + 12
    ncols = max(1, min(len(labels), int(available // item_width)))
    return ncols, min(item_width, available / ncols)


def add_title_and_legend(svg: str, width: float, height: float, shown: list, settings: dict) -> str:
    """Wrap a diagram SVG with the title above it and the legend below it."""
    inner = re.search(r"<svg\b[^>]*>(.*)</svg>", svg, re.DOTALL).group(1)
    total_width = max(width, MIN_WIDTH)
    top = TITLE_FONT_SIZE + 10 if settings["title"] else 0

    parts = [f'    <g transform="translate({(total_width - width) / 2:.2f},{top})">{inner}    </g>']
    total_height = top + height

    if settings["title"]:
        parts.append(
            f'    <text x="{total_width / 2:.2f}" y="{MARGIN + TITLE_FONT_SIZE}" '
            f'style="font-size:{TITLE_FONT_SIZE}px;font-weight:bold;text-anchor:middle;'
            f'font-family:sans-serif">{escape(settings["title"])}</text>'
        )

    if settings["legend"]:
        labels = [f"{name} ({seats})" for name, seats, _, _ in shown]
        available = total_width - 2 * MARGIN
        ncols, col_width = legend_layout(labels, available)
        nrows = ceil(len(labels) / ncols)
        x0 = MARGIN + (available - ncols * col_width) / 2
        y0 = top + height + 5
        parts.append(f'    <g style="font-size:{LEGEND_FONT_SIZE}px;font-family:sans-serif">')
        # Fill column by column so the legend reads top-to-bottom in seating order.
        for i, (label, (_, _, color, _)) in enumerate(zip(labels, shown)):
            col, row = divmod(i, nrows)
            x = x0 + col * col_width
            y = y0 + row * LEGEND_ROW_HEIGHT
            parts.append(
                f'        <rect x="{x:.2f}" y="{y:.2f}" width="{SWATCH_SIZE}" height="{SWATCH_SIZE}" '
                f'rx="1.5" style="fill:{color};stroke:#888;stroke-width:0.5"/>\n'
                f'        <text x="{x + SWATCH_SIZE + 4:.2f}" y="{y + SWATCH_SIZE - 0.5:.2f}">{escape(label)}</text>'
            )
        parts.append("    </g>")
        total_height += 10 + nrows * LEGEND_ROW_HEIGHT

    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{total_width:.1f}" height="{total_height:.1f}">\n'
        + "\n".join(parts)
        + "\n</svg>\n"
    )


def build_svg(parties: list, settings: dict) -> str:
    shown = [party for party in parties if party[1] > 0]
    make_diagram = westminster_svg if settings["style"] == "westminster" else arch_svg
    svg, width, height = make_diagram(shown, settings)
    return add_title_and_legend(svg, width, height, shown, settings)


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
    print(f"wrote {output} ({settings['style']}, {sum(p[1] for p in parties)} seats, {len(parties)} parties)")

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
