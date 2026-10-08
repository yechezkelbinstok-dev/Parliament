#!/usr/bin/env python3
"""Design and render an enlarged House of Representatives chamber.

Today's Hall of the House is 139 x 93 ft and 36 ft high, galleries included,
in the middle of the House wing (238 ft 10 in x 142 ft 8 in outside). At real
seat sizes, with rows 44 in apart, it could hold about 880 members even if all
of it were seats, so 1,527 members cannot fit in it. This design takes the hall out to
almost the whole wing, keeping the outer walls and a corridor round the room,
and keeps the hall's look and fittings. There are no separate galleries: the
members' benches rise in one continuous bowl from the well, and a few rows of
public seating sit at the top behind a rail and a glass screen.

    python chamber.py            # print the seat counts and render every view
    python chamber.py --report   # just the seat counts
    python chamber.py --views gallery-view

Members' seats are coloured by party in the "party-seating" view, from
parties/us-house.txt (left-wing parties on the Speaker's right, where
Democrats sit today).
"""

import argparse
import base64
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "chamber"
CACHE = ROOT / ".cache" / "chamber"
PARTIES_FILE = ROOT / "parties" / "us-house.txt"
SCENE_FILE = ROOT / "chamber_scene.js"
THREE_BASE = "https://cdn.jsdelivr.net/npm/three@0.147.0/"
THREE_FILES = ["build/three.min.js", "examples/js/environments/RoomEnvironment.js",
               "examples/js/geometries/RoundedBoxGeometry.js",
               # ambient occlusion
               "examples/js/shaders/CopyShader.js", "examples/js/shaders/SAOShader.js",
               "examples/js/shaders/DepthLimitedBlurShader.js", "examples/js/shaders/UnpackDepthRGBAShader.js",
               "examples/js/postprocessing/EffectComposer.js", "examples/js/postprocessing/RenderPass.js",
               "examples/js/postprocessing/ShaderPass.js", "examples/js/postprocessing/SAOPass.js"]

FT = 0.3048
# x runs west -> east, y south (rostrum wall) -> north, z up, metres.
# Today's hall, galleries included (Glenn Brown, History of the United States Capitol),
# and the House wing around it.
TODAY_W, TODAY_D = 139 * FT, 93 * FT
WING_W, WING_D = (238 + 10 / 12) * FT, (142 + 8 / 12) * FT
# The new hall: the wing less its outer walls and a corridor round the room.
HALL_W = 210 * FT
HALL_D = 110 * FT
HALL_H = 36 * FT
HALF_W = HALL_W / 2

# Rostrum on the south wall, three tiers like today's.
ROSTRUM_W = 12.5
ROSTRUM_D = 5.2
SPEAKER = (0.0, 2.6)  # the rows curve around this point

# The members' bowl: curved benches on carpeted tiers.
FIRST_ROW_R = 6.8       # radius of the first bench from the Speaker
# Today's seats come in pairs 52 1/2 in wide and 33 in deep (House collection).
SEAT_WIDTH = 0.67       # one place, arm to arm
ROW_DEPTH = 1.12        # front of one bench to the next: the seat plus a passage
CENTRE_AISLE = 1.7      # the wide aisle between the parties, with its runner
AISLE = 1.05            # the other radial aisles
AISLES = [24, 46, 68, 112, 134, 156]   # degrees from due east, seen from the Speaker
MIN_ANGLE, MAX_ANGLE = 9.0, 171.0      # leaves a passage along the rostrum wall


def rise(row):
    """Height gained per tier: gentle near the well like today's floor,
    steeper further out where the galleries were."""
    if row < 9:
        return 0.16
    if row < 17:
        return 0.24
    return 0.34


# Leadership tables at the front of each side, as today.
TABLES = [(72, 87.2), (92.8, 108), (49, 65), (115, 131)]

# Public seating: a few curved rows around the top, behind a walnut rail.
TOP_AISLE = 1.2
PUBLIC_ROWS = 4
PUBLIC_ROW_DEPTH = 0.85
PUBLIC_RISE = 0.42
PUBLIC_SEAT_WIDTH = 0.55


def region():
    """Where tiers may be built: the hall, minus the rostrum and the passage
    along the rostrum wall."""
    hall = box(-HALF_W, 0, HALF_W, HALL_D)
    sx, sy = SPEAKER
    far = 200
    pts = [(sx, sy)] + [(sx + far * math.cos(math.radians(a)), sy + far * math.sin(math.radians(a)))
                        for a in [MIN_ANGLE + k * (MAX_ANGLE - MIN_ANGLE) / 64 for k in range(65)]]
    sector = Polygon(pts)
    rostrum = box(-ROSTRUM_W / 2 - 1.2, 0, ROSTRUM_W / 2 + 1.2, ROSTRUM_D + 0.8)
    return hall.intersection(sector).difference(rostrum)


SEAT_REGION = None


def seat_fits(x, y):
    global SEAT_REGION
    if SEAT_REGION is None:
        SEAT_REGION = region().buffer(-0.75)   # keep a walkway along the walls
    return SEAT_REGION.contains(Point(x, y))


def bench_row(r, z, row, width, kind):
    """Seats along one curved row, split into benches between the aisles."""
    sx, sy = SPEAKER
    bounds = [MIN_ANGLE] + AISLES + [90.0] + [MAX_ANGLE]
    bounds = sorted(set(bounds))
    seats = []
    for a0, a1 in zip(bounds, bounds[1:]):
        def half(a):
            if a in (MIN_ANGLE, MAX_ANGLE):
                return 0.0
            w = CENTRE_AISLE if a == 90.0 else AISLE
            return math.degrees(w / 2 / r)
        lo, hi = a0 + half(a0), a1 - half(a1)
        spans = [(lo, hi)]
        if kind == "member" and row == 0:
            # the leadership tables take the front row's place
            for t0, t1 in TABLES:
                spans = [piece for s0, s1 in spans for piece in
                         ([(s0, s1)] if t1 <= s0 or t0 >= s1 else [(s0, t0), (t1, s1)]) if piece[1] > piece[0]]
        for s0, s1 in spans:
            n = int(math.radians(s1 - s0) * r // width)
            if n <= 0:
                continue
            step = math.degrees(width / r)
            start = (s0 + s1) / 2 - step * (n - 1) / 2
            bench = []
            for k in range(n):
                a = math.radians(start + k * step)
                x, y = sx + r * math.cos(a), sy + r * math.sin(a)
                if seat_fits(x, y):
                    bench.append({"x": round(x, 3), "y": round(y, 3), "z": round(z, 3), "row": row,
                                  "angle": round(math.degrees(a), 3), "face": round(math.atan2(sy - y, sx - x), 4),
                                  "kind": kind})
                elif bench:
                    break
            # mark bench ends so the model can close them with an arm
            for i, s in enumerate(bench):
                s["end_lo"] = i == 0
                s["end_hi"] = i == len(bench) - 1
            seats.extend(bench)
    return seats


def build_rows(target):
    """Member rows until every member has a seat, then a cross-aisle and the public rows.
    The outer rows run on into the corners of the room."""
    rows, seats = [], []
    r, z = FIRST_ROW_R, 0.20
    i = 0
    while True:
        row_seats = bench_row(r, z, i, SEAT_WIDTH, "member")
        if not row_seats and i > 3:
            break
        rows.append({"r": r, "z": round(z, 3), "kind": "member", "depth": ROW_DEPTH})
        seats.extend(row_seats)
        if len(seats) >= target:
            break
        z += rise(i)
        r += ROW_DEPTH
        i += 1
    members = len(seats)
    # cross-aisle at the top of the members' bowl, then the public rows
    r += ROW_DEPTH / 2 + TOP_AISLE + PUBLIC_ROW_DEPTH / 2
    z += rise(i) + 0.15
    aisle = {"r_in": rows[-1]["r"] + ROW_DEPTH / 2, "r_out": r - PUBLIC_ROW_DEPTH / 2,
             "z": round(rows[-1]["z"] + 0.05, 3)}
    for k in range(PUBLIC_ROWS):
        row_seats = bench_row(r, z, len(rows), PUBLIC_SEAT_WIDTH, "public")
        rows.append({"r": r, "z": round(z, 3), "kind": "public", "depth": PUBLIC_ROW_DEPTH})
        seats.extend(row_seats)
        r += PUBLIC_ROW_DEPTH
        z += PUBLIC_RISE
    return rows, seats[:members], seats[members:], aisle


def read_parties():
    parties = []
    for line in PARTIES_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" in line.split(",")[0]:
            continue
        name, seats, color = [f.strip() for f in line.rsplit(",", 2)]
        parties.append((name, int(seats), color))
    return parties


def assign_parties(seats, parties):
    """Give members the seats nearest the Speaker, then hand those out by angle.

    Parties fill from the Speaker's right (east, where Democrats sit today) to
    his left, in the order of the party file. The spare seats are the most
    remote ones, at the top of the bowl.
    """
    sx, sy = SPEAKER
    total = sum(n for _, n, _ in parties)
    by_distance = sorted(range(len(seats)), key=lambda i: math.dist((seats[i]["x"], seats[i]["y"], seats[i]["z"]), (sx, sy, 2.2)))
    used = sorted(by_distance[:total], key=lambda i: seats[i]["angle"])
    assignment = [None] * len(seats)
    pos = 0
    for party_index, (_, n, _) in enumerate(parties):
        for i in used[pos:pos + n]:
            assignment[i] = party_index
        pos += n
    return assignment


# ---------------------------------------------------------------- geometry for the 3D model

def polygons(geom):
    if geom.is_empty:
        return []
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if g.geom_type != "Polygon" or g.area < 0.01:
            continue
        g = g.simplify(0.01)
        out.append({"outer": [[round(x, 3), round(y, 3)] for x, y in g.exterior.coords],
                    "holes": [[[round(x, 3), round(y, 3)] for x, y in h.coords] for h in g.interiors]})
    return out


def annulus(r_in, r_out):
    sx, sy = SPEAKER
    return Point(sx, sy).buffer(r_out, 256).difference(Point(sx, sy).buffer(max(r_in, 0.01), 256))


def tier_bands(rows, aisle):
    """Carpeted platforms: one per row, the cross-aisle, and the top walkway."""
    area = region()
    bands = []
    for i, row in enumerate(rows):
        r_in = row["r"] - row["depth"] / 2
        if i + 1 < len(rows):
            nxt = rows[i + 1]
            r_out = nxt["r"] - nxt["depth"] / 2
        else:
            r_out = 200
        if row["kind"] == "member" and i + 1 < len(rows) and rows[i + 1]["kind"] == "public":
            r_out = aisle["r_out"]   # this tier runs on into the cross-aisle
        bands.append({"z": row["z"], "polys": polygons(annulus(r_in, r_out).intersection(area))})
    return bands


def rails(rows, aisle):
    """Walnut rail between the members' bowl and the public rows."""
    public = next(r for r in rows if r["kind"] == "public")
    r = public["r"] - public["depth"] / 2
    return {"z0": aisle["z"], "z": round(aisle["z"] + 1.0, 3),
            "polys": polygons(annulus(r - 0.12, r).intersection(region()))}


def leadership_tables(rows):
    sx, sy = SPEAKER
    r = rows[0]["r"]
    out = []
    for a0, a1 in TABLES:
        pts_out = [(sx + (r + 0.42) * math.cos(math.radians(a)), sy + (r + 0.42) * math.sin(math.radians(a)))
                   for a in [a0 + k * (a1 - a0) / 24 for k in range(25)]]
        pts_in = [(sx + (r - 0.42) * math.cos(math.radians(a)), sy + (r - 0.42) * math.sin(math.radians(a)))
                  for a in [a1 - k * (a1 - a0) / 24 for k in range(25)]]
        mid = math.radians((a0 + a1) / 2)
        out.append({"z": rows[0]["z"], "polys": polygons(Polygon(pts_out + pts_in)),
                    "r": r, "a0": a0, "a1": a1,
                    "lectern": [round(sx + r * math.cos(mid), 3), round(sy + r * math.sin(mid), 3)],
                    "face": round(math.atan2(-math.sin(mid), -math.cos(mid)), 4)})
    return out


def build_layout():
    parties = read_parties()
    rows, members, public, aisle = build_rows(sum(n for _, n, _ in parties))
    for seat, p in zip(members, assign_parties(members, parties)):
        seat["party"] = p
    return {
        "hall": {"w": HALL_W, "d": HALL_D, "h": HALL_H},
        "rostrum": {"w": ROSTRUM_W, "d": ROSTRUM_D},
        "speaker": SPEAKER,
        "rows": rows,
        "members": members,
        "public": public,
        "aisle": aisle,
        "parties": [{"name": n, "seats": s, "color": c} for n, s, c in parties],
        "seat_width": SEAT_WIDTH, "public_seat_width": PUBLIC_SEAT_WIDTH,
        "centre_aisle": CENTRE_AISLE, "aisle_width": AISLE, "aisles": AISLES,
        "angles": [MIN_ANGLE, MAX_ANGLE],
        "clearance": [ROSTRUM_W / 2 + 1.2, ROSTRUM_D + 0.8],
    }


def runner(rows, aisle):
    """The centre aisle's runner: one strip per tier, from the well to the top."""
    sx, sy = SPEAKER
    strips = [{"y0": ROSTRUM_D + 0.8, "y1": sy + rows[0]["r"] - rows[0]["depth"] / 2, "z": 0.0}]
    for i, row in enumerate(rows):
        if row["kind"] != "member":
            break
        y0 = sy + row["r"] - row["depth"] / 2
        if i + 1 < len(rows) and rows[i + 1]["kind"] == "member":
            y1 = sy + rows[i + 1]["r"] - rows[i + 1]["depth"] / 2
        else:
            y1 = sy + aisle["r_out"]
        strips.append({"y0": round(y0, 3), "y1": round(y1, 3), "z": row["z"]})
    return strips


def side_screens(rows, aisle):
    """Walnut screens stepping up along both open ends of the bowl."""
    sx, sy = SPEAKER
    bands = tier_bands(rows, aisle)
    screens = []
    for angle in (MIN_ANGLE, MAX_ANGLE):
        a = math.radians(angle)
        ray = Polygon([(sx, sy), (sx + 200 * math.cos(a), sy + 200 * math.sin(a)),
                       (sx + 200 * math.cos(a) + 0.01, sy + 200 * math.sin(a) + 0.01)]).buffer(0.09)
        for band in bands:
            for poly in band["polys"]:
                g = Polygon(poly["outer"]).intersection(ray)
                if not g.is_empty and g.area > 0.005:
                    screens.append({"z": band["z"], "polys": polygons(g)})
    return screens


def model_data(layout):
    data = dict(layout)
    data["bands"] = tier_bands(layout["rows"], layout["aisle"])
    data["rail"] = rails(layout["rows"], layout["aisle"])
    data["tables"] = leadership_tables(layout["rows"])
    data["runner"] = runner(layout["rows"], layout["aisle"])
    data["screens"] = side_screens(layout["rows"], layout["aisle"])
    return data


def report(layout):
    members, public, rows = layout["members"], layout["public"], layout["rows"]
    total = sum(p["seats"] for p in layout["parties"])
    member_rows = [r for r in rows if r["kind"] == "member"]
    print(f"hall {HALL_W / FT:.0f} x {HALL_D / FT:.0f} ft ({HALL_W:.1f} x {HALL_D:.1f} m), {HALL_H / FT:.0f} ft high; "
          f"today's hall is {TODAY_W / FT:.0f} x {TODAY_D / FT:.0f} ft, the House wing {WING_W / FT:.0f} x {WING_D / FT:.0f} ft")
    print(f"members' bowl: {len(member_rows)} tiers of benches, rising to {member_rows[-1]['z']:.2f} m; "
          f"{len(members)} seats for {total} members ({len(members) - total} spare)")
    print(f"public: {len(public)} seats in {PUBLIC_ROWS} rows, top row at {rows[-1]['z']:.2f} m "
          f"({HALL_H - rows[-1]['z']:.2f} m below the ceiling)")
    print(f"total seats: {len(members) + len(public)}")


# ---------------------------------------------------------------- rendering

# Camera positions (x east, y north from the rostrum wall, z up).
VIEWS = {
    "gallery-view": dict(eye=(0, HALL_D - 2.6, 8.7), target=(0, 6.0, 0.4), fov=66),
    "side-view": dict(eye=(28.6, 23.6, 9.2), target=(-3.0, 5.0, 1.2), fov=60),
    "floor-view": dict(eye=(-4.6, 9.2, 1.55), target=(1.5, 2.6, 2.0), fov=62),
    "speaker-view": dict(eye=(0, 1.6, 4.3), target=(0, 24, 3.4), fov=74),
    "party-seating": dict(eye=(0, 3, 44), target=(0, 18.5, 0), fov=50, colors="party", hide=["ceiling"]),
    # a joint session: every seat taken, the President at the rostrum
    "sotu-gallery": dict(eye=(0, HALL_D - 2.6, 8.7), target=(0, 4.0, 1.4), fov=60, sotu=True),
    "sotu-rostrum": dict(eye=(1.4, 0.5, 8.9), target=(0, 11.5, 0.6), fov=70, sotu=True),
    "sotu-president": dict(eye=(0, 16.5, 3.4), target=(0, 2.0, 2.4), fov=30, sotu=True),
}


def three_scripts():
    CACHE.mkdir(parents=True, exist_ok=True)
    import requests
    paths = []
    for f in THREE_FILES:
        path = CACHE / ("r147-" + Path(f).name)
        if not path.exists():
            response = requests.get(THREE_BASE + f, timeout=60)
            response.raise_for_status()
            path.write_bytes(response.content)
        paths.append(path)
    return paths


def render_views(layout, names, size=(2560, 1440)):
    from playwright.sync_api import sync_playwright

    scripts = "".join(f'<script src="{p.as_uri()}"></script>' for p in three_scripts())
    OUT_DIR.mkdir(exist_ok=True)
    written = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"])
        for name in names:
            page_html = (f'<!doctype html><html><body style="margin:0;background:#000">'
                         f'<canvas id="c" width="{size[0]}" height="{size[1]}"></canvas>'
                         f'<script>window.LAYOUT = {json.dumps(layout)}; window.VIEW = {json.dumps(VIEWS[name])};</script>'
                         f'{scripts}<script src="{SCENE_FILE.as_uri()}"></script></body></html>')
            page_file = CACHE / f"{name}.html"
            page_file.write_text(page_html, encoding="utf-8")
            page = browser.new_page(viewport={"width": size[0], "height": size[1]})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(page_file.as_uri())
            try:
                page.wait_for_function("window.RENDERED === true || window.FAILED", timeout=900_000)
            finally:
                if errors:
                    raise RuntimeError(f"{name}: {errors}")
            out = OUT_DIR / f"chamber-{name}.png"
            data_url = page.evaluate("document.getElementById('c').toDataURL('image/png')")
            out.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
            written.append(out)
            page.close()
        browser.close()
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", action="store_true", help="only print seat counts")
    parser.add_argument("--views", nargs="*", default=list(VIEWS), help=f"views to render ({', '.join(VIEWS)})")
    parser.add_argument("--size", default="2560x1440", help="image size, e.g. 1280x720 for a quick preview")
    args = parser.parse_args()
    layout = build_layout()
    report(layout)
    if args.report:
        return 0
    size = tuple(int(v) for v in args.size.split("x"))
    for path in render_views(model_data(layout), args.views, size):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
