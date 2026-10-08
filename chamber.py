#!/usr/bin/env python3
"""Design and render an enlarged House of Representatives chamber.

The room keeps the real House chamber's size (139 x 93 ft, 36 ft high) and its
Speaker's rostrum on the south wall. Inside it:

- the members sit in a raked bowl of curved rows facing the rostrum, split by
  radial aisles and one cross-aisle, with more seats than members (as today);
- a horseshoe public gallery of a few curved rows runs high up along the
  side and back walls, above the outer member rows.

    python chamber.py            # writes chamber/ plan + 3D views
    python chamber.py --plan     # just the floor plan (no browser needed)

Seats are coloured by party from parties/us-house.txt (left-wing parties on the
Speaker's right, as Democrats sit today).
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "chamber"
CACHE = ROOT / ".cache" / "chamber"
PARTIES_FILE = ROOT / "parties" / "us-house.txt"
THREE_URL = "https://cdn.jsdelivr.net/npm/three@0.149.0/build/three.min.js"

FT = 0.3048
# The room (metres). x runs west -> east, y south (rostrum wall) -> north, z up.
ROOM_W = 139 * FT
ROOM_D = 93 * FT
ROOM_H = 36 * FT
HALF_W = ROOM_W / 2

# Rostrum on the south wall, three tiers like today's.
ROSTRUM_W = 13.0
ROSTRUM_D = 4.6
SPEAKER = (0.0, 2.4)  # focal point the rows curve around

# Member seating bowl on the floor: a gentle rake, so the balcony can overhang it.
FIRST_ROW_R = 7.0       # radius of the first row from the Speaker
ROW_DEPTH = 0.85        # front-to-back spacing of rows
SEAT_WIDTH = 0.56       # centre-to-centre along a row
AISLE = 1.0             # radial aisle width
CROSS_AISLE_R = 16.0    # radius of the cross-aisle between the lower and upper bowl
CROSS_AISLE_W = 1.3
RISE_LOWER = 0.10       # height gained per row
RISE_UPPER = 0.12
WALKWAY = 1.0           # circulation along the walls on the floor level
MIN_ANGLE, MAX_ANGLE = 3.0, 177.0   # degrees from due east, seen from the Speaker
LOWER_AISLES = [30, 60, 90, 120, 150]                       # every 30 degrees near the well
UPPER_AISLES = [18, 36, 54, 72, 90, 108, 126, 144, 162]     # every 18 degrees further out

# Horseshoe balcony along the side and back walls: member rows at the front,
# then a cross-aisle, then the public gallery rows higher up at the back.
BALCONY_MEMBER_ROWS = 4
BALCONY_PUBLIC_ROWS = 3
BALCONY_ROW_DEPTH = 0.85
BALCONY_SEAT_WIDTH = 0.56
BALCONY_REAR_WALKWAY = 0.8
BALCONY_SPLIT_AISLE = 1.0
BALCONY_PARAPET = 0.45
BALCONY_FLOOR = 5.9         # front member row floor height
BALCONY_RISE = 0.40
BALCONY_SPLIT_STEP = 0.30   # extra step up to the public rows
BALCONY_START_Y = 9.0       # where the horseshoe begins along the side walls
BALCONY_CORNER_R = 9.0
BALCONY_SLAB = 0.35
HEADROOM = 2.1


def balcony_rows():
    """Rows from the front (lowest, members) to the back (highest, public)."""
    rows = []
    inset = BALCONY_REAR_WALKWAY + BALCONY_ROW_DEPTH / 2
    public = []
    for _ in range(BALCONY_PUBLIC_ROWS):
        public.append(inset)
        inset += BALCONY_ROW_DEPTH
    inset += BALCONY_SPLIT_AISLE - BALCONY_ROW_DEPTH / 2 + BALCONY_ROW_DEPTH / 2
    member = []
    for _ in range(BALCONY_MEMBER_ROWS):
        member.append(inset)
        inset += BALCONY_ROW_DEPTH
    z = BALCONY_FLOOR
    for m in reversed(member):
        rows.append({"inset": m, "z": round(z, 3), "kind": "member"})
        z += BALCONY_RISE
    z += BALCONY_SPLIT_STEP
    for pub in reversed(public):
        rows.append({"inset": pub, "z": round(z, 3), "kind": "public"})
        z += BALCONY_RISE
    return rows


def balcony_edge_inset():
    return max(r["inset"] for r in balcony_rows()) + BALCONY_ROW_DEPTH / 2 + BALCONY_PARAPET


def bowl_rows():
    """Return rows as dicts: radius, floor height, zone."""
    rows = []
    r, z = FIRST_ROW_R, 0.30
    zone = "lower"
    while True:
        if zone == "lower" and r + ROW_DEPTH / 2 > CROSS_AISLE_R - CROSS_AISLE_W / 2:
            zone = "upper"
            r = CROSS_AISLE_R + CROSS_AISLE_W / 2 + ROW_DEPTH / 2
            z += 0.35  # step up across the cross-aisle
        if r > math.hypot(HALF_W, ROOM_D):
            break
        rows.append({"r": r, "z": round(z, 3), "zone": zone})
        r += ROW_DEPTH
        z += RISE_LOWER if zone == "lower" else RISE_UPPER
    return rows


def seat_area():
    """Floor area where member seats may stand (inside the walkways, clear of the rostrum)."""
    inner = box(-HALF_W + WALKWAY, 0, HALF_W - WALKWAY, ROOM_D - WALKWAY)
    rostrum_clear = box(-ROSTRUM_W / 2 - 1.4, 0, ROSTRUM_W / 2 + 1.4, ROSTRUM_D + 1.6)
    return inner.difference(rostrum_clear)


def member_seats(rows):
    area = seat_area()
    sx, sy = SPEAKER
    seats = []
    for i, row in enumerate(rows):
        r = row["r"]
        aisles = LOWER_AISLES if row["zone"] == "lower" else UPPER_AISLES
        bounds = [MIN_ANGLE] + aisles + [MAX_ANGLE]
        # angular half-width of an aisle at this radius
        half_aisle = math.degrees(AISLE / 2 / r)
        for a0, a1 in zip(bounds, bounds[1:]):
            lo = a0 + (half_aisle if a0 != MIN_ANGLE else 0)
            hi = a1 - (half_aisle if a1 != MAX_ANGLE else 0)
            arc = math.radians(hi - lo) * r
            n = int(arc // SEAT_WIDTH)
            if n <= 0:
                continue
            step = math.degrees(SEAT_WIDTH / r)
            start = (lo + hi) / 2 - step * (n - 1) / 2
            for k in range(n):
                a = math.radians(start + k * step)
                x, y = sx + r * math.cos(a), sy + r * math.sin(a)
                # the whole chair (about 0.55 x 0.6 m) must fit
                if area.contains(Point(x, y).buffer(0.32)):
                    seats.append({"x": round(x, 3), "y": round(y, 3), "z": row["z"], "row": i,
                                  "angle": round(math.degrees(a), 3),
                                  "face": round(math.atan2(sy - y, sx - x), 4)})
    return seats


def horseshoe(inset, step=0.05):
    """Points (x, y, facing) along a horseshoe `inset` metres from the side and back walls."""
    left, right, back = -HALF_W + inset, HALF_W - inset, ROOM_D - inset
    rc = max(BALCONY_CORNER_R - inset, 0.5)
    pts = []
    y = BALCONY_START_Y
    while y < back - rc:
        pts.append((left, y, 0.0))
        y += step
    cx, cy = left + rc, back - rc
    n = max(int(math.pi / 2 * rc / step), 4)
    for k in range(n + 1):
        a = math.pi - (math.pi / 2) * k / n
        pts.append((cx + rc * math.cos(a), cy + rc * math.sin(a), a + math.pi))
    x = left + rc
    while x < right - rc:
        pts.append((x, back, -math.pi / 2))
        x += step
    cx = right - rc
    for k in range(n + 1):
        a = math.pi / 2 - (math.pi / 2) * k / n
        pts.append((cx + rc * math.cos(a), cy + rc * math.sin(a), a + math.pi))
    y = back - rc
    while y > BALCONY_START_Y:
        pts.append((right, y, math.pi))
        y -= step
    return pts


def balcony_seats():
    seats = []
    for i, row in enumerate(balcony_rows()):
        pts = horseshoe(row["inset"])
        length = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
        n = int((length - 1.2) // BALCONY_SEAT_WIDTH)
        first = (length - (n - 1) * BALCONY_SEAT_WIDTH) / 2
        targets = [first + k * BALCONY_SEAT_WIDTH for k in range(n)]
        dist, t = 0.0, 0
        for a, b in zip(pts, pts[1:]):
            seg = math.hypot(b[0] - a[0], b[1] - a[1])
            while t < len(targets) and targets[t] <= dist + seg:
                f = (targets[t] - dist) / seg if seg else 0
                x, y = a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1])
                seats.append({"x": round(x, 3), "y": round(y, 3), "z": row["z"], "row": i,
                              "kind": row["kind"], "face": round(a[2], 4)})
                t += 1
            dist += seg
    return seats


def balcony_outline(inset_outer, inset_inner):
    outer = [(x, y) for x, y, _ in horseshoe(inset_outer, 0.25)]
    inner = [(x, y) for x, y, _ in horseshoe(inset_inner, 0.25)]
    return Polygon(outer + inner[::-1]).buffer(0)


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
    his left, in the order of the party file, so each party gets a wedge that
    runs from the floor up into the balcony. The seats left over are the most
    remote ones (corners and the back balcony row).
    """
    sx, sy = SPEAKER
    total = sum(n for _, n, _ in parties)
    by_distance = sorted(range(len(seats)), key=lambda i: math.dist((seats[i]["x"], seats[i]["y"], seats[i]["z"]), (sx, sy, 2.2)))
    used = sorted(by_distance[:total], key=lambda i: math.atan2(seats[i]["y"] - sy, seats[i]["x"] - sx))
    assignment = [None] * len(seats)
    pos = 0
    for party_index, (_, n, _) in enumerate(parties):
        for i in used[pos:pos + n]:
            assignment[i] = party_index
        pos += n
    return assignment


def build_layout():
    rows = bowl_rows()
    floor_seats = member_seats(rows)
    upper = balcony_seats()
    balcony_members = [s for s in upper if s["kind"] == "member"]
    public = [s for s in upper if s["kind"] == "public"]

    # Headroom: floor seats under the balcony need HEADROOM below its front underside.
    underside = BALCONY_FLOOR - BALCONY_SLAB
    footprint = balcony_outline(0, balcony_edge_inset())
    under = [underside - s["z"] for s in floor_seats if footprint.contains(Point(s["x"], s["y"]))]

    members = floor_seats + balcony_members
    parties = read_parties()
    for seat, p in zip(members, assign_parties(members, parties)):
        seat["party"] = p
    return {
        "room": {"w": ROOM_W, "d": ROOM_D, "h": ROOM_H},
        "rostrum": {"w": ROSTRUM_W, "d": ROSTRUM_D},
        "speaker": SPEAKER,
        "rows": rows,
        "floor_seats": floor_seats,
        "balcony_members": balcony_members,
        "public": public,
        "balcony_rows": balcony_rows(),
        "balcony": {"start_y": BALCONY_START_Y, "corner_r": BALCONY_CORNER_R, "slab": BALCONY_SLAB,
                    "edge_inset": balcony_edge_inset(), "row_depth": BALCONY_ROW_DEPTH,
                    "outline": [list(c) for c in footprint.exterior.coords]},
        "walkway": WALKWAY,
        "parties": [{"name": n, "seats": s, "color": c} for n, s, c in parties],
        "cross_aisle": {"r": CROSS_AISLE_R, "w": CROSS_AISLE_W},
        "headroom_min": min(under) if under else None,
        "under_balcony": len(under),
    }


def report(layout):
    floor, bal, pub = layout["floor_seats"], layout["balcony_members"], layout["public"]
    total = sum(p["seats"] for p in layout["parties"])
    members = len(floor) + len(bal)
    print(f"room {ROOM_W:.1f} x {ROOM_D:.1f} x {ROOM_H:.1f} m")
    print(f"floor: {len(floor)} seats in {len(layout['rows'])} rows, top row at {max(s['z'] for s in floor):.2f} m")
    print(f"balcony: {len(bal)} member seats, {len(pub)} public seats; "
          f"edge {layout['balcony']['edge_inset']:.2f} m from the walls; "
          f"top public row floor {max(r['z'] for r in layout['balcony_rows']):.2f} m")
    print(f"member seats {members} for {total} members ({members - total} spare)")
    print(f"headroom under the balcony: min {layout['headroom_min']:.2f} m over {layout['under_balcony']} seats")


# ---------------------------------------------------------------- geometry for the 3D model

def polygons(geom):
    """Shapely geometry -> list of {outer, holes} with rounded coordinates."""
    if geom.is_empty:
        return []
    parts = getattr(geom, "geoms", [geom])
    out = []
    for g in parts:
        if g.geom_type != "Polygon" or g.area < 0.01:
            continue
        g = g.simplify(0.01)
        out.append({"outer": [[round(x, 3), round(y, 3)] for x, y in g.exterior.coords],
                    "holes": [[[round(x, 3), round(y, 3)] for x, y in h.coords] for h in g.interiors]})
    return out


def annulus(r_in, r_out):
    sx, sy = SPEAKER
    return Point(sx, sy).buffer(r_out, 256).difference(Point(sx, sy).buffer(max(r_in, 0.01), 256))


def bowl_bands(rows):
    """Stepped platforms of the floor bowl: one band per row plus the cross-aisle."""
    room = box(-HALF_W, 0, HALF_W, ROOM_D)
    keep_clear = box(-ROSTRUM_W / 2 - 1.4, 0, ROSTRUM_W / 2 + 1.4, ROSTRUM_D + 1.6)
    region = room.difference(keep_clear)
    bands = []
    last_r = rows[-1]["r"]
    for i, row in enumerate(rows):
        r = row["r"]
        outer = r + ROW_DEPTH / 2 if i < len(rows) - 1 else max(last_r + 30, 60)
        if i + 1 < len(rows) and rows[i + 1]["zone"] != row["zone"]:
            # this row's band runs on into the cross-aisle, the next row steps up from there
            outer = rows[i + 1]["r"] - ROW_DEPTH / 2
        bands.append({"z": row["z"], "polys": polygons(annulus(r - ROW_DEPTH / 2, outer).intersection(region))})
    return bands


def balcony_bands():
    rows = balcony_rows()
    d = BALCONY_ROW_DEPTH
    underside = BALCONY_FLOOR - BALCONY_SLAB
    bands = []
    members = [r for r in rows if r["kind"] == "member"]
    public = [r for r in rows if r["kind"] == "public"]
    for r in rows:
        bands.append({"z0": underside, "z": r["z"], "polys": polygons(balcony_outline(r["inset"] - d / 2, r["inset"] + d / 2))})
    # aisle between member and public rows, and the walkway at the back
    gap_outer = public[0]["inset"] + d / 2
    gap_inner = members[-1]["inset"] - d / 2
    bands.append({"z0": underside, "z": round(members[-1]["z"] + 0.15, 3),
                  "polys": polygons(balcony_outline(gap_outer, gap_inner))})
    bands.append({"z0": underside, "z": public[-1]["z"],
                  "polys": polygons(balcony_outline(0, public[-1]["inset"] - d / 2))})
    # parapet in front of the first member row
    front = members[0]
    edge = balcony_edge_inset()
    parapet = {"z0": underside, "z": round(front["z"] + 0.95, 3),
               "polys": polygons(balcony_outline(edge - 0.18, edge))}
    floor_front = {"z0": underside, "z": front["z"],
                   "polys": polygons(balcony_outline(front["inset"] + d / 2, edge - 0.18))}
    return bands + [floor_front], parapet



SCENE_JS = r"""
THREE.ColorManagement.legacyMode = false;
const L = window.LAYOUT, VIEW = window.VIEW;
const W = L.room.w, D = L.room.d, H = L.room.h, HW = W / 2;
const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(1);
renderer.setSize(canvas.width, canvas.height, false);
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#1b1d22');

// plan (x east, y north, z up) -> three (x, up, -north)
const V = (x, y, z) => new THREE.Vector3(x, z, -y);
const mat = (color, opts = {}) => new THREE.MeshStandardMaterial(Object.assign({color, roughness: 0.8, metalness: 0}, opts));

function shapeFrom(poly) {
  const s = new THREE.Shape(poly.outer.map(([x, y]) => new THREE.Vector2(x, y)));
  for (const h of poly.holes) s.holes.push(new THREE.Path(h.map(([x, y]) => new THREE.Vector2(x, y))));
  return s;
}
function extrude(polys, z0, z1, material) {
  const group = new THREE.Group();
  if (z1 - z0 < 0.005) z1 = z0 + 0.005;
  for (const poly of polys) {
    const g = new THREE.ExtrudeGeometry(shapeFrom(poly), {depth: z1 - z0, bevelEnabled: false, curveSegments: 1});
    g.rotateX(-Math.PI / 2);
    g.translate(0, z0, 0);
    const m = new THREE.Mesh(g, material);
    m.castShadow = true; m.receiveShadow = true;
    group.add(m);
  }
  scene.add(group);
  return group;
}
function boxAt(x, y, z, w, d, h, material, rotY = 0) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), material);
  m.position.copy(V(x, y, z + h / 2));
  m.rotation.y = rotY;
  m.castShadow = true; m.receiveShadow = true;
  scene.add(m);
  return m;
}
function star(g, cx, cy, r) {
  g.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.4 : r;
    g.lineTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a));
  }
  g.closePath(); g.fill();
}
function canvasTexture(w, h, draw) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.encoding = THREE.sRGBEncoding; t.anisotropy = 8;
  return t;
}

// ---------- room
const carpet = mat('#20305e', {roughness: 0.95});
const wallMat = mat('#e6dcc6', {roughness: 0.9});
const woodMat = mat('#5b3a24', {roughness: 0.6});
const marbleMat = mat('#efe9dc', {roughness: 0.35});
const goldMat = mat('#c9a24a', {roughness: 0.35, metalness: 0.6});
const stepMat = mat('#283a70', {roughness: 0.95});
const balconyMat = mat('#e9e0cb', {roughness: 0.85});

const floor = new THREE.Mesh(new THREE.PlaneGeometry(W, D), carpet);
floor.rotation.x = -Math.PI / 2; floor.position.copy(V(0, D / 2, 0)); floor.receiveShadow = true; scene.add(floor);

const walls = {};
function wall(name, x, y, w, rotY) {
  const g = new THREE.Group();
  const panel = new THREE.Mesh(new THREE.PlaneGeometry(w, H), wallMat);
  panel.position.y = H / 2; panel.receiveShadow = true; g.add(panel);
  const wains = new THREE.Mesh(new THREE.BoxGeometry(w, 1.25, 0.06), woodMat);
  wains.position.set(0, 0.62, 0.03); g.add(wains);
  // pilasters
  const n = Math.round(w / 4.6);
  for (let i = 0; i <= n; i++) {
    const px = -w / 2 + i * (w / n);
    const pil = new THREE.Mesh(new THREE.BoxGeometry(0.55, H, 0.18), marbleMat);
    pil.position.set(px, H / 2, 0.09); pil.receiveShadow = true; g.add(pil);
  }
  const cornice = new THREE.Mesh(new THREE.BoxGeometry(w, 0.45, 0.35), marbleMat);
  cornice.position.set(0, H - 0.25, 0.17); g.add(cornice);
  const trim = new THREE.Mesh(new THREE.BoxGeometry(w, 0.08, 0.38), goldMat);
  trim.position.set(0, H - 0.5, 0.19); g.add(trim);
  g.position.copy(V(x, y, 0)); g.rotation.y = rotY;
  scene.add(g); walls[name] = g;
}
wall('south', 0, 0, W, Math.PI);
wall('north', 0, D, W, 0);
wall('west', -HW, D / 2, D, Math.PI / 2);
wall('east', HW, D / 2, D, -Math.PI / 2);

// doors along the floor level
const doorMat = mat('#3a2416', {roughness: 0.5});
for (const [x, y, rot] of [[0, D - 0.04, Math.PI], [-HW + 0.04, 6, Math.PI / 2], [HW - 0.04, 6, -Math.PI / 2], [-10, D - 0.04, Math.PI], [10, D - 0.04, Math.PI]]) {
  const dmesh = new THREE.Mesh(new THREE.BoxGeometry(2.2, 3.0, 0.08), doorMat);
  dmesh.position.copy(V(x, y, 1.5)); dmesh.rotation.y = rot; scene.add(dmesh);
}

// ceiling with the stained-glass skylight
const ceiling = new THREE.Group();
const ceil = new THREE.Mesh(new THREE.PlaneGeometry(W, D), mat('#d9cfb8', {roughness: 0.9}));
ceil.rotation.x = Math.PI / 2; ceil.position.copy(V(0, D / 2, H)); ceiling.add(ceil);
const skyTex = canvasTexture(1024, 640, (g, w, h) => {
  g.fillStyle = '#cdb67a'; g.fillRect(0, 0, w, h);
  const cols = 12, rows = 7;
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    const x = i * w / cols, y = j * h / rows;
    g.fillStyle = (i + j) % 2 ? '#e8d9a8' : '#f2e6bd'; g.fillRect(x + 6, y + 6, w / cols - 12, h / rows - 12);
  }
  g.fillStyle = '#f7efd2'; g.beginPath(); g.ellipse(w / 2, h / 2, 150, 120, 0, 0, Math.PI * 2); g.fill();
  g.strokeStyle = '#9c7a2e'; g.lineWidth = 10; g.stroke();
  g.fillStyle = '#9c7a2e'; star(g, w / 2, h / 2, 80);
});
const sky = new THREE.Mesh(new THREE.PlaneGeometry(W * 0.55, D * 0.5), new THREE.MeshStandardMaterial({map: skyTex, emissive: '#fff4d6', emissiveMap: skyTex, emissiveIntensity: 0.9}));
sky.rotation.x = Math.PI / 2; sky.position.copy(V(0, D * 0.55, H - 0.02)); ceiling.add(sky);
for (let i = -4; i <= 4; i++) {  // coffers
  const beam = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.4, D), marbleMat); beam.position.copy(V(i * W / 9, D / 2, H - 0.2)); ceiling.add(beam);
}
for (let j = 1; j < 6; j++) {
  const beam = new THREE.Mesh(new THREE.BoxGeometry(W, 0.4, 0.35), marbleMat); beam.position.copy(V(0, j * D / 6, H - 0.2)); ceiling.add(beam);
}
scene.add(ceiling);

// ---------- rostrum
const rw = L.rostrum.w, rd = L.rostrum.d;
boxAt(0, rd / 2, 0, rw, rd, 0.75, woodMat);
boxAt(0, rd / 2 + 0.02, 0, rw - 0.6, 0.05, 0.6, marbleMat).position.z = -(rd + 0.02);
boxAt(0, (rd - 1.0) / 2, 0.75, rw * 0.7, rd - 1.0, 0.75, woodMat);
boxAt(0, (rd - 2.3) / 2, 1.5, rw * 0.38, rd - 2.3, 0.8, woodMat);
boxAt(0, 0.6, 2.3, 1.1, 0.7, 1.5, mat('#3b2214'));                 // Speaker's chair
boxAt(0, rd + 0.01, 0.15, rw, 0.04, 0.5, goldMat);
const flagTex = canvasTexture(950, 500, (g, w, h) => {
  for (let i = 0; i < 13; i++) { g.fillStyle = i % 2 ? '#ffffff' : '#b22234'; g.fillRect(0, i * h / 13, w, h / 13 + 1); }
  g.fillStyle = '#3c3b6e'; g.fillRect(0, 0, w * 0.4, h * 7 / 13);
  g.fillStyle = '#fff';
  for (let r = 0; r < 9; r++) for (let c = 0; c < (r % 2 ? 5 : 6); c++) star(g, (c + (r % 2 ? 1 : 0.5)) * w * 0.4 / 6, (r + 1) * h * 7 / 13 / 10, 9);
});
const flag = new THREE.Mesh(new THREE.PlaneGeometry(5.4, 2.85), new THREE.MeshStandardMaterial({map: flagTex, roughness: 0.9, side: THREE.DoubleSide}));
flag.position.copy(V(0, 0.22, 5.2)); flag.rotation.y = Math.PI; scene.add(flag);
const mottoTex = canvasTexture(1400, 120, (g, w, h) => {
  g.fillStyle = '#e6dcc6'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#a8862f'; g.font = 'bold 82px Georgia, serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('IN GOD WE TRUST', w / 2, h / 2 + 4);
});
const motto = new THREE.Mesh(new THREE.PlaneGeometry(9, 0.77), new THREE.MeshStandardMaterial({map: mottoTex}));
motto.position.copy(V(0, 0.4, 7.75)); motto.rotation.y = Math.PI; scene.add(motto);
for (const x of [-4.2, -3.2, 3.2, 4.2]) boxAt(x, 0.35, 0, 0.7, 0.7, 7.0, marbleMat);
boxAt(0, 0.35, 7.0, 9.8, 0.75, 0.45, marbleMat);
// lecterns and tables in the well
for (const x of [-3.4, 3.4]) { boxAt(x, 6.2, 0, 1.0, 0.7, 1.15, woodMat); boxAt(x, 8.0, 0, 3.4, 1.0, 0.76, woodMat); }

// ---------- bowl and balcony
for (const b of L.bowl_bands) extrude(b.polys, 0, b.z, stepMat);
L.balcony_bands.forEach((b, i) => extrude(b.polys, b.z0, b.z, i === L.balcony_bands.length - 1 ? balconyMat : stepMat));
extrude(L.parapet.polys, L.parapet.z0, L.parapet.z, balconyMat);
// gilded rail on the parapet
extrude(L.parapet.polys, L.parapet.z, L.parapet.z + 0.07, goldMat);

// ---------- seats
function chairGeometry(w, depth, seatH, backH) {
  const parts = [
    new THREE.BoxGeometry(depth, 0.12, w).translate(0, seatH, 0),
    new THREE.BoxGeometry(0.1, backH, w).translate(-depth / 2 + 0.05, seatH + backH / 2, 0),
    new THREE.BoxGeometry(depth * 0.8, 0.06, 0.06).translate(0, seatH + 0.2, w / 2 - 0.03),
    new THREE.BoxGeometry(depth * 0.8, 0.06, 0.06).translate(0, seatH + 0.2, -w / 2 + 0.03),
    new THREE.CylinderGeometry(0.05, 0.08, seatH, 8).translate(0, seatH / 2, 0),
  ].map(g => g.toNonIndexed());
  const pos = [], norm = [];
  for (const g of parts) { pos.push(...g.attributes.position.array); norm.push(...g.attributes.normal.array); }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(norm, 3));
  return geo;
}
const chair = chairGeometry(0.5, 0.5, 0.46, 0.62);
function placeSeats(list, colorOf) {
  const mesh = new THREE.InstancedMesh(chair, new THREE.MeshStandardMaterial({roughness: 0.55}), list.length);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), one = new THREE.Vector3(1, 1, 1);
  list.forEach((s, i) => {
    q.setFromAxisAngle(up, s.face);
    m4.compose(V(s.x, s.y, s.z), q, one);
    mesh.setMatrixAt(i, m4);
    mesh.setColorAt(i, new THREE.Color(colorOf(s)));
  });
  mesh.castShadow = true; mesh.receiveShadow = true;
  scene.add(mesh);
}
const spare = '#6b5a4a';
const partyColor = s => s.party == null ? spare : L.parties[s.party].color;
const leather = s => '#2c3d73';
const colorOf = VIEW.colors === 'party' ? partyColor : leather;
placeSeats(L.floor_seats, colorOf);
placeSeats(L.balcony_members, colorOf);
placeSeats(L.public, () => '#7d2230');

// ---------- light
scene.add(new THREE.HemisphereLight('#fff6e6', '#8a7b66', 0.75));
const sun = new THREE.DirectionalLight('#fff3dd', 1.25);
sun.position.copy(V(-6, D * 0.65, 40)); sun.target.position.copy(V(0, D / 2, 0));
sun.castShadow = true; sun.shadow.mapSize.set(4096, 4096);
Object.assign(sun.shadow.camera, {left: -30, right: 30, top: 30, bottom: -30, near: 1, far: 80});
sun.shadow.bias = -0.0004;
scene.add(sun, sun.target);
const fill = new THREE.PointLight('#ffe9c4', 0.35, 60); fill.position.copy(V(0, 4, 8)); scene.add(fill);

// ---------- view
for (const name of VIEW.hide || []) { if (name === 'ceiling') ceiling.visible = false; else walls[name].visible = false; }
const cam = VIEW.ortho
  ? new THREE.OrthographicCamera(-VIEW.ortho * canvas.width / canvas.height, VIEW.ortho * canvas.width / canvas.height, VIEW.ortho, -VIEW.ortho, 0.1, 200)
  : new THREE.PerspectiveCamera(VIEW.fov, canvas.width / canvas.height, 0.1, 200);
cam.position.copy(V(...VIEW.eye));
if (VIEW.ortho) cam.up.set(0, 0, -1);
cam.lookAt(V(...VIEW.target));
renderer.render(scene, cam);
window.RENDERED = true;
"""

VIEWS = {
    "gallery-view": dict(eye=(0, ROOM_D - 3.6, 10.3), target=(0, 4.5, 0.0), fov=64, colors="party"),
    "speaker-view": dict(eye=(0, 1.2, 4.6), target=(0, 20, 2.5), fov=80, colors="party"),
    "cutaway": dict(eye=(26, 44, 40), target=(0, 12, 0), fov=40, colors="party", hide=["ceiling", "north", "east"]),
    "chamber": dict(eye=(-17.5, ROOM_D - 3.2, 10.4), target=(5, 3.5, 0.5), fov=66, colors="leather"),
}


def render_views(layout, names, size=(2560, 1440)):
    from playwright.sync_api import sync_playwright
    import requests

    CACHE.mkdir(parents=True, exist_ok=True)
    three = CACHE / "three.min.js"
    if not three.exists():
        three.write_bytes(requests.get(THREE_URL, timeout=60).content)
    OUT_DIR.mkdir(exist_ok=True)
    written = []
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--ignore-gpu-blocklist"])
        for name in names:
            page_html = (f'<!doctype html><html><body style="margin:0;background:#000">'
                         f'<canvas id="c" width="{size[0]}" height="{size[1]}"></canvas>'
                         f'<script>window.LAYOUT = {json.dumps(layout)}; window.VIEW = {json.dumps(VIEWS[name])};</script>'
                         f'<script src="{three.as_uri()}"></script><script>{SCENE_JS}</script></body></html>')
            page_file = CACHE / f"{name}.html"
            page_file.write_text(page_html, encoding="utf-8")
            page = browser.new_page(viewport={"width": size[0], "height": size[1]})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(page_file.as_uri())
            page.wait_for_function("window.RENDERED === true", timeout=300_000)
            if errors:
                raise RuntimeError(f"{name}: {errors}")
            out = OUT_DIR / f"chamber-{name}.png"
            page.locator("#c").screenshot(path=str(out))
            written.append(out)
            page.close()
        browser.close()
    return written


def model_data(layout):
    bands, parapet = balcony_bands()
    data = dict(layout)
    data["bowl_bands"] = bowl_bands(layout["rows"])
    data["balcony_bands"] = bands
    data["parapet"] = parapet
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", action="store_true", help="only print seat counts")
    parser.add_argument("--views", nargs="*", default=list(VIEWS), help=f"views to render ({', '.join(VIEWS)})")
    args = parser.parse_args()
    layout = build_layout()
    report(layout)
    if args.report:
        return 0
    for path in render_views(model_data(layout), args.views):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
