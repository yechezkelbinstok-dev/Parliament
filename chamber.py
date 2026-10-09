#!/usr/bin/env python3
"""Two designs for a House of Representatives of 1,527 members inside today's chamber.

Today's Hall of the House is 139 x 93 ft and 36 ft high, galleries included
(Glenn Brown, History of the United States Capitol). Both designs keep that
room and everything around it (the grand stairways and their murals, the
Speaker's Lobby, the cloakrooms) and rebuild only its inside, in its present
style. Members sit in oval rows around a long central floor, on two levels: a
lower bowl and a mezzanine over most of it. The public sits in a ring at the
top, behind a rail and a glass screen.

- oval: today's seat size (pairs 52 1/2 in wide, 33 in deep). The rows go all
  the way round, so the Speaker sits in the middle of the floor, with the flag,
  columns, fasces, clock and portraits moved onto a marble screen behind the chair.
- horseshoe: theatre-size seats. The rows stop short of the south wall, so
  today's rostrum, frontispiece and press gallery stay where they are.

    python chamber.py                                  # both designs: seat counts and every view
    python chamber.py --design oval --report           # just the seat counts
    python chamber.py --design horseshoe --views gallery-view --size 1280x720

Members' seats are coloured by party in the party views, from
parties/us-house.txt: left-wing parties from the Speaker's right (east, where
Democrats sit today) round to right-wing parties on his left.
"""

import argparse
import base64
import bisect
import json
import math
import sys
from pathlib import Path

from shapely.geometry import Polygon, box

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
# Today's hall. x runs west -> east, y south (rostrum wall) -> north, z up, metres.
HALL_W, HALL_D, HALL_H = 139 * FT, 93 * FT, 36 * FT
HALF_W = HALL_W / 2
CX, CY = 0.0, HALL_D / 2
WALK = 0.9                                   # walkway along the walls on every level
OUTER_A, OUTER_B = HALF_W - WALK, CY - WALK  # outer edge of the seating
SLAB = 0.45                                  # depth of a raised tier, floor to soffit
HEADROOM = 2.3                               # clear height under the mezzanine and the public ring
AISLES = 8                                   # radial aisles, evenly spaced round the oval
AISLE_W, CENTRE_AISLE_W = 1.1, 1.6           # the north and south aisles are wider, with a runner
PUBLIC = dict(seat_w=0.55, row_d=0.85, rows=3, rise=0.3)

DESIGNS = {
    "oval": dict(
        title="Oval, today's seats",
        seat_w=0.67, row_d=1.12,             # today's seats: pairs 52 1/2 x 33 in, rows ~44 in apart
        well=3.0,                            # half the width of the central floor
        mezz_from=0.2,                       # the mezzanine starts over the third lower row
        lower_rise=0.16, mezz_rise=0.28,
        cut=None, rostrum="centre"),
    "horseshoe": dict(
        title="Horseshoe, theatre seats",
        seat_w=0.58, row_d=0.92,             # theatre seats: 23 in wide, rows 3 ft apart
        well=4.5, mezz_from=0.15,
        lower_rise=0.16, mezz_rise=0.28,
        cut=8.0,                             # rows stop 8 m either side of the rostrum
        rostrum="wall"),
}
# Leadership tables in the first row either side of the north aisle (arc metres from the aisle).
TABLES = [(0.15, 3.75), (4.35, 7.95)]


class Oval:
    """Rows are parallel curves, a constant distance r outside the central floor,
    an ellipse a0 x b0 centred in the hall. t is the ellipse's angle parameter."""

    def __init__(self, a0, b0):
        self.a0, self.b0 = a0, b0

    def at(self, t, r):
        c, s = math.cos(t), math.sin(t)
        nx, ny = self.b0 * c, self.a0 * s
        n = math.hypot(nx, ny)
        nx, ny = nx / n, ny / n
        return CX + self.a0 * c + r * nx, CY + self.b0 * s + r * ny, nx, ny

    def polygon(self, n=720):
        return Polygon([(CX + self.a0 * math.cos(2 * math.pi * i / n), CY + self.b0 * math.sin(2 * math.pi * i / n))
                        for i in range(n)])

    def row(self, r, n=4000, start=1.5 * math.pi):
        """Points along the row at offset r, from the south going east, north, west."""
        ts = [start + 2 * math.pi * i / n for i in range(n + 1)]
        pts = [self.at(t, r) for t in ts]
        s = [0.0]
        for i in range(1, len(pts)):
            s.append(s[-1] + math.dist(pts[i][:2], pts[i - 1][:2]))
        return ts, pts, s


def interp(xs, ys, x):
    i = min(max(bisect.bisect_left(xs, x), 1), len(xs) - 1)
    x0, x1 = xs[i - 1], xs[i]
    f = 0 if x1 == x0 else (x - x0) / (x1 - x0)
    return ys[i - 1] + f * (ys[i] - ys[i - 1])


def read_parties():
    parties = []
    for line in PARTIES_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" in line.split(",")[0]:
            continue
        name, seats, color = [f.strip() for f in line.rsplit(",", 2)]
        parties.append((name, int(seats), color))
    return parties


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


class Design:
    def __init__(self, name):
        self.name = name
        self.p = DESIGNS[name]
        p = self.p
        b0 = p["well"]
        self.oval = Oval(b0 + OUTER_A - OUTER_B, b0)
        self.depth = OUTER_B - b0             # how deep the band of seating is
        self.cut_y = CY - b0                   # the horseshoe's open end reaches the central floor
        self.speaker = (CX, CY) if p["rostrum"] == "centre" else (0.0, 2.6)
        self.parties = read_parties()
        self.target = sum(n for _, n, _ in self.parties)
        self.hall = box(-HALF_W, 0, HALF_W, HALL_D)
        self.region = self.hall
        if p["cut"]:
            self.region = self.hall.difference(box(-p["cut"], 0, p["cut"], self.cut_y))
        self.aisles = self.aisle_positions()
        self.rows = self.build_rows()
        self.benches, self.tables = self.place_seats()
        self.assign_parties()

    def keep(self, x, y):
        cut = self.p["cut"]
        return not (cut and abs(x - CX) < cut and y < self.cut_y)

    def aisle_positions(self):
        """Evenly spaced round the middle of the band, one at the north and one at the south."""
        ts, pts, s = self.oval.row(self.depth / 2, start=0.0)
        out = []
        for k in range(AISLES):
            frac = (0.25 + k / AISLES) % 1.0
            t = interp(s, ts, frac * s[-1])
            centre = abs(math.sin(t)) > 0.999
            out.append({"t": round(t % (2 * math.pi), 5), "w": CENTRE_AISLE_W if centre else AISLE_W})
        return out

    def build_rows(self):
        p, rows = self.p, []
        d = p["row_d"]
        k, r = 0, d / 2
        while r + d / 2 <= self.depth + 1e-9:
            rows.append({"level": "lower", "kind": "member", "r": r, "z": round(0.15 + k * p["lower_rise"], 3),
                         "depth": d, "seat_w": p["seat_w"], "index": k})
            k, r = k + 1, r + d

        def clear_above(r0, r1, below):
            """Lowest floor for a raised tier over offsets r0..r1, given the rows below it."""
            under = [b["z"] for b in below if b["r"] + b["depth"] / 2 > r0 and b["r"] - b["depth"] / 2 < r1]
            return max(under, default=0) + HEADROOM + SLAB

        lower = list(rows)
        m0 = p["mezz_from"] * self.depth
        j, r, z = 0, m0 + d / 2, None
        while r + d / 2 <= self.depth + 1e-9:
            zmin = clear_above(r - d / 2, r + d / 2, lower)
            z = zmin if z is None else max(zmin, z + p["mezz_rise"])
            rows.append({"level": "mezzanine", "kind": "member", "r": r, "z": round(z, 3), "depth": d,
                         "seat_w": p["seat_w"], "index": j})
            j, r = j + 1, r + d
        mezz = [row for row in rows if row["level"] == "mezzanine"]
        pd = PUBLIC["row_d"]
        r, z = self.depth - PUBLIC["rows"] * pd + pd / 2, None
        for i in range(PUBLIC["rows"]):
            zmin = clear_above(r - pd / 2, r + pd / 2, mezz)
            z = zmin if z is None else max(zmin, z + PUBLIC["rise"])
            rows.append({"level": "public", "kind": "public", "r": r, "z": round(z, 3), "depth": pd,
                         "seat_w": PUBLIC["seat_w"], "index": i})
            r += pd
        return rows

    def place_seats(self):
        """Seats along each row, in benches between the aisles (and the open end)."""
        benches, tables = [], []
        for row in self.rows:
            r, w = row["r"], row["seat_w"]
            ts, pts, s = self.oval.row(r)
            blocked = []
            for a in self.aisles:
                t = (a["t"] - 1.5 * math.pi) % (2 * math.pi) + 1.5 * math.pi
                sa = interp(ts, s, t)
                blocked += [(sa - a["w"] / 2, sa + a["w"] / 2), (sa - a["w"] / 2 + s[-1], sa + a["w"] / 2 + s[-1]),
                            (sa - a["w"] / 2 - s[-1], sa + a["w"] / 2 - s[-1])]
            if row["level"] == "lower" and row["index"] == 0:
                north = next(a for a in self.aisles if abs(a["t"] - math.pi / 2) < 1e-3)
                sn = interp(ts, s, north["t"] + 2 * math.pi)
                for t0, t1 in TABLES:
                    for side in (-1, 1):
                        a0, a1 = sorted((sn + side * (north["w"] / 2 + t0), sn + side * (north["w"] / 2 + t1)))
                        blocked.append((a0, a1))
                        tables.append({"r": r, "z": row["z"], "t0": round(interp(s, ts, a0), 5),
                                       "t1": round(interp(s, ts, a1), 5)})
            free = [self.keep(x, y) and not any(b0 <= si <= b1 for b0, b1 in blocked)
                    for (x, y, _, _), si in zip(pts, s)]
            runs, start = [], None
            for i, f in enumerate(free + [False]):
                if f and start is None:
                    start = i
                elif not f and start is not None:
                    runs.append((s[start], s[i - 1]))
                    start = None
            for s0, s1 in runs:
                n = int((s1 - s0 + 1e-9) // w)
                if n < 1:
                    continue
                first = (s0 + s1) / 2 - w * (n - 1) / 2
                seats = []
                for i in range(n):
                    t = interp(s, ts, first + i * w)
                    x, y, nx, ny = self.oval.at(t, r)
                    seats.append({"x": round(x, 3), "y": round(y, 3), "z": row["z"], "t": round(t, 5),
                                  "face": round(math.atan2(-ny, -nx), 4), "level": row["level"], "kind": row["kind"],
                                  "row": row["index"], "end_lo": i == 0, "end_hi": i == n - 1})
                benches.append({"level": row["level"], "kind": row["kind"], "r": r, "z": row["z"], "depth": row["depth"],
                                "seat_w": w, "t0": round(interp(s, ts, first - w / 2), 5),
                                "t1": round(interp(s, ts, first + w * (n - 0.5)), 5), "seats": seats})
        return benches, tables

    def seats(self, kind):
        return [s for b in self.benches if b["kind"] == kind for s in b["seats"]]

    def assign_parties(self):
        """Members get the seats nearest the Speaker; the parties then fill them round the oval
        from the south-east (the Speaker's right) by way of the north to the south-west."""
        members = self.seats("member")
        sx, sy = self.speaker
        near = sorted(members, key=lambda s: math.dist((s["x"], s["y"], s["z"]), (sx, sy, 2.0)))[:self.target]
        near.sort(key=lambda s: s["t"])
        pos = 0
        for index, (_, n, _) in enumerate(self.parties):
            for s in near[pos:pos + n]:
                s["party"] = index
            pos += n

    # ------------------------------------------------------------ geometry for the 3D model

    def bands(self):
        """Carpeted tiers. Lower tiers stand on the floor; raised ones are slabs with a soffit.
        The outermost tier of each level runs on to the walls."""
        E = self.oval.polygon()
        out = []
        for level in ("lower", "mezzanine", "public"):
            rows = [r for r in self.rows if r["level"] == level]
            for i, row in enumerate(rows):
                o0 = row["r"] - row["depth"] / 2
                inner = E if o0 < 1e-6 else E.buffer(o0, 64)
                outer = self.hall if i + 1 == len(rows) else E.buffer(rows[i + 1]["r"] - rows[i + 1]["depth"] / 2, 64)
                geom = outer.difference(inner).intersection(self.region)
                out.append({"level": level, "z0": 0 if level == "lower" else round(row["z"] - SLAB, 3), "z": row["z"],
                            "polys": polygons(geom)})
        return out

    def fronts(self):
        """The mezzanine's and the public ring's front parapets (the public one carries a glass screen)."""
        out = []
        for level in ("mezzanine", "public"):
            first = next(r for r in self.rows if r["level"] == level)
            out.append({"level": level, "r": round(first["r"] - first["depth"] / 2, 3),
                        "z0": round(first["z"] - SLAB - 0.25, 3), "z1": round(first["z"] + 0.95, 3),
                        "glass": level == "public"})
        return out

    def screens(self, bands):
        """Walnut screens along both sides of the horseshoe's open end."""
        cut = self.p["cut"]
        if not cut:
            return []
        out = []
        for side in (-1, 1):
            strip = box(side * cut - 0.09, 0, side * cut + 0.09, self.cut_y)
            for band in bands:
                for poly in band["polys"]:
                    g = Polygon(poly["outer"], poly["holes"]).intersection(strip)
                    if not g.is_empty and g.area > 0.005:
                        out.append({"level": band["level"], "z0": band["z0"], "z": band["z"], "polys": polygons(g)})
        return out

    def runners(self):
        """The centre aisles' runners as (y, z) profiles along x = 0: up the north aisle of the
        lower bowl, and either up the south aisle too (oval) or from the rostrum (horseshoe)."""
        lower = [r for r in self.rows if r["level"] == "lower"]
        b0 = self.oval.b0

        def climb(sign):
            pts, z = [], 0.0
            for row in lower:
                y = CY + sign * (b0 + row["r"] - row["depth"] / 2)
                pts += [[round(y, 3), z], [round(y, 3), row["z"]]]
                z = row["z"]
            pts.append([round(CY + sign * (b0 + self.depth), 3), z])
            return pts

        if self.p["rostrum"] == "wall":
            return [[[6.0, 0.0]] + climb(1)]
        # from the central rostrum out to both centre aisles
        return [[[CY + 1.8, 0.0]] + climb(1), [[CY - 2.0, 0.0]] + climb(-1)]

    def layout(self):
        bands = self.bands()
        members, public = self.seats("member"), self.seats("public")
        return {
            "design": self.name, "title": self.p["title"], "rostrum": self.p["rostrum"],
            "hall": {"w": HALL_W, "d": HALL_D, "h": HALL_H},
            "centre": [CX, CY], "oval": {"a0": self.oval.a0, "b0": self.oval.b0, "depth": self.depth},
            "cut": [self.p["cut"], self.cut_y] if self.p["cut"] else None,
            "speaker": list(self.speaker),
            "rows": self.rows, "aisles": self.aisles, "benches": self.benches, "tables": self.tables,
            "bands": bands, "fronts": self.fronts(), "screens": self.screens(bands), "runners": self.runners(),
            "parties": [{"name": n, "seats": s, "color": c} for n, s, c in self.parties],
            "counts": {"members": len(members), "public": len(public), "target": self.target},
        }

    def report(self):
        members = self.seats("member")
        lower = sum(1 for s in members if s["level"] == "lower")
        public = self.seats("public")
        press = press_seats(self.name)
        top = max(r["z"] for r in self.rows)
        print(f"{self.name} ({self.p['title']}): seats {self.p['seat_w'] / 0.0254:.0f} in wide, rows "
              f"{self.p['row_d'] / 0.0254:.0f} in apart; central floor {2 * self.oval.a0:.1f} x {2 * self.oval.b0:.1f} m")
        print(f"  members: {len(members)} seats for {self.target} ({len(members) - self.target} spare): "
              f"{lower} in the lower bowl, {len(members) - lower} on the mezzanine")
        print(f"  public: {len(public)}; press: {press}; total {len(members) + len(public) + press}; "
              f"top row {top:.2f} m up, {HALL_H - top:.2f} m below the ceiling")


def press_seats(name):
    """Today's press gallery above the rostrum survives in the horseshoe, narrowed to the
    open end. Mirrors the seat placement in chamber_scene.js."""
    if DESIGNS[name]["rostrum"] != "wall":
        return 0
    half = press_half_width(name)
    xs, x = [], -half + 0.6
    while x <= half - 0.6 + 1e-9:
        xs.append(x)
        x += 0.55
    return 3 * sum(1 for x in xs if abs(x) >= 0.6)


def press_half_width(name):
    return DESIGNS[name]["cut"] - 0.4


# ---------------------------------------------------------------- rendering

def views(d):
    """Camera positions for a design (x east, y north from the rostrum wall, z up)."""
    centre = d.p["rostrum"] == "centre"
    pub = next(r for r in d.rows if r["level"] == "public")
    rostrum = (0, CY - 0.6, 2.2) if centre else (0, 2.6, 2.4)
    north_floor = CY + d.oval.b0
    # just in front of the public ring's glass screen: at the north aisle, and on the east side
    p0 = pub["r"] - pub["depth"] / 2 - 0.3
    over = (0, north_floor + p0, pub["z"] + 2.3)
    east = (CX + d.oval.a0 + p0, CY + 1.5, pub["z"] + 2.3)
    mezz = next(r for r in d.rows if r["level"] == "mezzanine")
    balcony = (0, north_floor + mezz["r"] - mezz["depth"] / 2 - 0.3, mezz["z"] + 1.1)
    return {
        "gallery-view": dict(eye=over, target=(0, rostrum[1], 0.8), fov=72),
        "side-view": dict(eye=east, target=(-5.0, CY - 1.5, 0.6) if centre else (-4.0, 3.5, 1.2), fov=66),
        "floor-view": dict(eye=(-2.4, north_floor + 1.2, 1.55), target=(0.5, rostrum[1], 2.2), fov=62),
        "speaker-view": dict(eye=(0, CY - 0.9, 3.0), target=(0, HALL_D, 3.6), fov=76) if centre
        else dict(eye=(0, 1.6, 4.3), target=(0, HALL_D, 3.4), fov=74),
        "party-lower": dict(eye=(0, CY - 6, 40), target=(0, CY + 0.5, 0), fov=44, colors="party",
                            hide=["ceiling", "mezzanine", "public"]),
        "party-mezzanine": dict(eye=(0, CY - 6, 40), target=(0, CY + 0.5, 0), fov=44, colors="party",
                                hide=["ceiling", "public"]),
        "sotu-gallery": dict(eye=over, target=(0, rostrum[1], 1.2), fov=64, sotu=True),
        # the television camera's shot, from the front of the mezzanine on the north side
        "sotu-president": dict(eye=balcony, target=rostrum, fov=34 if centre else 24, sotu=True),
        # over the President's shoulder
        "sotu-rostrum": dict(eye=(4.2, CY - 3.6, 6.4), target=(-1.0, CY + 8, 0.8), fov=70, sotu=True) if centre
        else dict(eye=(1.4, 0.5, 8.9), target=(0, CY - 2.5, 0.6), fov=70, sotu=True),
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


def render_views(layout, view_defs, names, size=(2560, 1440)):
    from playwright.sync_api import sync_playwright

    scripts = "".join(f'<script src="{p.as_uri()}"></script>' for p in three_scripts())
    OUT_DIR.mkdir(exist_ok=True)
    written = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"])
        for name in names:
            stem = f"{layout['design']}-{name}"
            page_html = (f'<!doctype html><html><body style="margin:0;background:#000">'
                         f'<canvas id="c" width="{size[0]}" height="{size[1]}"></canvas>'
                         f'<script>window.LAYOUT = {json.dumps(layout)}; window.VIEW = {json.dumps(view_defs[name])};</script>'
                         f'{scripts}<script src="{SCENE_FILE.as_uri()}"></script></body></html>')
            page_file = CACHE / f"{stem}.html"
            page_file.write_text(page_html, encoding="utf-8")
            page = browser.new_page(viewport={"width": size[0], "height": size[1]})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(page_file.as_uri())
            try:
                page.wait_for_function("window.RENDERED === true || window.FAILED", timeout=900_000)
            finally:
                if errors:
                    raise RuntimeError(f"{stem}: {errors}")
            out = OUT_DIR / f"{stem}.png"
            data_url = page.evaluate("document.getElementById('c').toDataURL('image/png')")
            out.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
            written.append(out)
            page.close()
        browser.close()
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--design", choices=list(DESIGNS), nargs="*", default=list(DESIGNS))
    parser.add_argument("--report", action="store_true", help="only print seat counts")
    parser.add_argument("--views", nargs="*", help="views to render (default: all)")
    parser.add_argument("--size", default="2560x1440", help="image size, e.g. 1280x720 for a quick preview")
    args = parser.parse_args()
    size = tuple(int(v) for v in args.size.split("x"))
    for name in args.design:
        d = Design(name)
        d.report()
        if len(d.seats("member")) < d.target:
            print("  not enough seats for every member", file=sys.stderr)
        if args.report:
            continue
        v = views(d)
        for path in render_views(d.layout(), v, args.views or list(v), size):
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
