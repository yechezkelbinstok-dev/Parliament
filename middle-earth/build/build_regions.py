"""Turn defs.py (realms, provinces, border lines, district names) into region geometry.

python build_regions.py            build everything, write .cache/regions.pkl and debug data
python build_regions.py --fast     provinces only (skip districts and cells)
"""
import importlib, math, os, pickle, sys, time
from collections import defaultdict

import shapely
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import substring, unary_union, linemerge
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geom
from geom import polys, lines

CACHE = os.path.join(HERE, '.cache')
TINY_LAKE = 120.0


def log(*a):
    print(*a, flush=True)


class Build:
    def __init__(self, defs):
        self.D = defs
        self.F = pickle.load(open(os.path.join(CACHE, 'features.pkl'), 'rb'))
        self.ranges = self.F['ranges']
        self.warn = []

    # ---------- hard lines ----------
    def river(self, idx, a=None, b=None, k=0):
        ln = self.F['rivers'][(idx, k)]['line']
        s0 = ln.project(Point(a)) if a else 0.0
        s1 = ln.project(Point(b)) if b else ln.length
        if s0 > s1:
            s0, s1 = s1, s0
        part = substring(ln, s0, s1)
        return list(part.coords)

    def ring_part(self, ring, a, b, via=None):
        """Part of a closed ring between the points nearest a and b (through `via` if given)."""
        ln = LineString(ring.coords) if ring.geom_type != 'LineString' else ring
        L = ln.length
        s0, s1 = ln.project(Point(a)), ln.project(Point(b))
        lo, hi = min(s0, s1), max(s0, s1)
        inner = substring(ln, lo, hi)
        outer = linemerge([substring(ln, hi, L), substring(ln, 0, lo)])
        if via is not None:
            pick = inner if inner.distance(Point(via)) < outer.distance(Point(via)) else outer
        else:
            pick = inner if inner.length <= outer.length else outer
        return list(lines(pick)[0].coords) if pick.geom_type != 'LineString' else list(pick.coords)

    def find(self, kind, pt):
        gs = self.F['forest'] if kind == 'forest' else self.ranges
        p = Point(pt)
        hit = [g for g in gs if g.contains(p)]
        if not hit:
            g = min(gs, key=lambda g: g.distance(p))
            self.warn.append(f'{kind} ref {pt} not inside any outline, using nearest ({g.distance(p):.1f} away)')
            return g
        return min(hit, key=lambda g: g.area)

    def anduin_axis(self):
        """Centre line of the broad lower Anduin (drawn as a filled shape on the map)."""
        import networkx as nx
        poly = self.F['anduin_poly'].buffer(0)
        poly = max(polys(poly), key=lambda p: p.area)
        bd = shapely.segmentize(poly.exterior, 0.8)
        edges = shapely.voronoi_polygons(shapely.MultiPoint(list(bd.coords)), only_edges=True)
        G = nx.Graph()
        prep = shapely.prepared.prep(poly)
        for e in lines(edges):
            if prep.contains(e):
                a, b = e.coords[0], e.coords[-1]
                a = (round(a[0], 3), round(a[1], 3)); b = (round(b[0], 3), round(b[1], 3))
                G.add_edge(a, b, weight=e.length)
        nodes = list(G.nodes)
        def near(p):
            return min(nodes, key=lambda n: (n[0] - p[0]) ** 2 + (n[1] - p[1]) ** 2)
        path = nx.shortest_path(G, near(self.D.ANDUIN_AXIS[0]), near(self.D.ANDUIN_AXIS[1]), weight='weight')
        ln = LineString(path).simplify(0.6)
        cs = geom.chaikin(list(ln.coords), 2)
        return [self.D.ANDUIN_AXIS[0]] + cs[1:-1] + [self.D.ANDUIN_AXIS[1]]

    def hard_lines(self):
        fixed = []
        land, water = self.F['land'], self.F['water']
        for p in polys(water):
            fixed += lines(p)
        fixed += lines(self.F['frame'])
        fixed_u = unary_union(fixed)
        specs = self.D.LINES
        raw = []
        for name, spec in specs:
            kind = spec[0]
            if kind == 'river':
                cs = self.river(*spec[1:])
                raw.append((name, cs, 'river'))
            elif kind in ('forest_at', 'range_at'):
                g = self.find(kind.split('_')[0], spec[1])
                opts = spec[2] if len(spec) > 2 else {}
                for m in opts.get('minus', []):
                    g = g.difference(Polygon(m))
                if 'clip' in opts:
                    g = g.intersection(Polygon(opts['clip']))
                g = max(polys(g), key=lambda p: p.area)
                for r in [g.exterior] + list(g.interiors):
                    raw.append((name, list(r.coords), 'ring'))
            elif kind in ('forest_part', 'range_part'):
                g = self.find(kind.split('_')[0], spec[1])
                cs = self.ring_part(g.exterior, spec[2], spec[3], spec[4] if len(spec) > 4 else None)
                raw.append((name, cs, 'part'))
            elif kind == 'anduin_axis':
                raw.append((name, self.anduin_axis(), 'river'))
            elif kind == 'hand':
                pts = spec[1]
                cs = geom.chaikin(pts, 3)
                cs = geom.wiggle(cs, frac=0.05, amax=2.2, seg=2.0, salt=name)
                raw.append((name, cs, 'hand'))
            else:
                raise ValueError(kind)
        # snap open ends to the rest of the network
        out = []
        allg = [fixed_u] + [LineString(cs) for _, cs, _ in raw]
        for i, (name, cs, kind) in enumerate(raw):
            if kind == 'ring':
                out.append(LineString(cs))
                continue
            others = unary_union([g for j, g in enumerate(allg) if j != i + 1])
            tol = self.D.SNAP.get(name, 16.0 if kind == 'hand' else 5.0)
            cs2 = geom.snap_ends(cs, others, tol=tol)
            out.append(LineString(cs2))
            if kind == 'hand':
                for end in (cs[0], cs[-1]):
                    if others.distance(Point(end)) > tol:
                        self.warn.append(f'line {name}: end {tuple(round(v) for v in end)} touches nothing '
                                         f'({others.distance(Point(end)):.0f} pt away)')
        self.hard = out
        self.fixed = fixed
        return fixed + out

    # ---------- provinces ----------
    def build_provinces(self):
        t = time.time()
        work = self.hard_lines()
        faces = geom.faces_of(work, within=self.F['frame'])
        tiny = [p for p in self.F['lakes'].values() if p.area < TINY_LAKE]
        faces = [f for f in faces if not any(t_.contains(f.representative_point()) for t_ in tiny)]
        log('faces', len(faces), '%.1fs' % (time.time() - t))
        seeds = []
        land = self.F['land']
        for pid, pdef in self.D.PROV.items():
            wet = pdef['realm'] in self.D.WATER
            for s in pdef['seeds']:
                if land.contains(Point(s)) == wet:
                    self.warn.append(f'seed on wrong medium: {pid} {s} ({"land" if not wet else "water"} expected)')
                    continue
                seeds.append((s, pid))
        tree = STRtree(faces)
        by_face = defaultdict(list)
        for s, pid in seeds:
            hit = [i for i in tree.query(Point(s)) if faces[i].contains(Point(s))]
            if not hit:
                self.warn.append(f'seed outside faces: {pid} {s}')
                continue
            by_face[hit[0]].append((s, pid))
        pieces, keys = [], []
        for i, f in enumerate(faces):
            ss = by_face.get(i)
            if not ss:
                pieces.append(f); keys.append(None)
                if f.area > 400:
                    c = f.representative_point()
                    self.warn.append(f'orphan face area {f.area:.0f} at ({c.x:.0f},{c.y:.0f})')
                continue
            split = geom.voronoi_split(f, [s for s, _ in ss], [p for _, p in ss], salt='p%d' % i,
                                       frac=0.10, amax=9.0)
            for k, g in split.items():
                for p in polys(g):
                    pieces.append(p); keys.append(k)
        log('pieces', len(pieces), '%.1fs' % (time.time() - t))
        pieces, keys = geom.merge_small(pieces, keys, min_area=6.0)
        prov = defaultdict(list)
        for p, k in zip(pieces, keys):
            prov[k].append(p)
        self.prov = {k: unary_union(v).buffer(0) for k, v in prov.items()}
        self.fold_fragments()
        for pid in self.D.PROV:
            if pid not in self.prov:
                self.warn.append(f'province without area: {pid}')
        for pid, g in self.prov.items():
            parts = polys(g)
            if len(parts) > 1 and not self.D.PROV[pid].get('multi'):
                small = sorted(p.area for p in parts)[:-1]
                self.warn.append(f'{pid} has {len(parts)} parts, minor areas {[round(a) for a in small]}')
        log('provinces', len(self.prov), '%.1fs' % (time.time() - t))

    def fold_fragments(self):
        """Give small detached bits of a province to the neighbour they share most border with."""
        for _ in range(3):
            moved = 0
            for pid in list(self.prov):
                g = self.prov[pid]
                parts = polys(g)
                if len(parts) < 2 or self.D.PROV[pid].get('multi'):
                    continue
                big = max(p.area for p in parts)
                keep = []
                for p in parts:
                    if p.area >= max(150.0, 0.15 * big):
                        keep.append(p)
                        continue
                    best, bl = None, 0.0
                    wet = self.D.PROV[pid]['realm'] in self.D.WATER
                    for qid, q in self.prov.items():
                        if qid == pid or not p.envelope.intersects(q.envelope):
                            continue
                        if (self.D.PROV[qid]['realm'] in self.D.WATER) != wet:
                            continue
                        inter = p.boundary.intersection(q.buffer(0.05))
                        L = 0 if inter.is_empty else inter.length
                        if L > bl:
                            bl, best = L, qid
                    if best is None:
                        keep.append(p)
                        continue
                    self.prov[best] = unary_union([self.prov[best], p]).buffer(0)
                    moved += 1
                self.prov[pid] = unary_union(keep).buffer(0)
            if not moved:
                break

    # ---------- districts ----------
    def internal_lines(self):
        """Natural features that make good district borders inside a province."""
        out = [r['line'] for r in self.F['rivers'].values()]
        for g in self.ranges + self.F['forest']:
            out.append(LineString(g.exterior.coords))
        return out

    def split_geo(self, poly, target, salt, hints):
        """Split one polygon along rivers, forest edges and mountain feet, then evenly.
        Named places (hints) inside become district seeds of their own. Returns [(polygon, name)]."""
        if poly.area < 1.6 * target and len(hints) < 2:
            return [(poly, hints[0][2] if hints else None)]
        faces = [poly]
        if poly.area >= 1.6 * target:
            idx = self.tree_lines.query(poly, predicate='intersects')
            cuts = [self.int_lines[i].intersection(poly) for i in idx]
            work = [poly.boundary] + [c for c in cuts if not c.is_empty]
            faces = geom.faces_of(work, within=poly) or [poly]
            faces, _ = geom.merge_small(faces, list(range(len(faces))), min_area=0.45 * target)
        out = []
        for j, f in enumerate(faces):
            hs = [h for h in hints if f.contains(Point(h[0], h[1]))]
            n = max(len(hs), int(round(f.area / target)))
            if n < 2:
                out.append((f, hs[0][2] if hs else None))
                continue
            pts = geom.kmeans_points(f, n - len(hs), seed=j, fixed=[(x, y) for x, y, _ in hs])
            split = geom.voronoi_split(f, pts, list(range(len(pts))), salt=f'{salt}-{j}', frac=0.09, amax=6.0)
            for k, g in split.items():
                for p in polys(g):
                    out.append((p, hs[k][2] if k < len(hs) else None))
        # fold slivers into their neighbours; a named piece keeps its name
        faces = [p for p, _ in out]
        keys = list(range(len(out)))
        merged, mk = geom.merge_small(faces, keys, min_area=0.08 * target)
        return [(p, out[k][1]) for p, k in zip(merged, mk)]

    def build_districts(self):
        t = time.time()
        self.int_lines = self.internal_lines()
        self.tree_lines = STRtree(self.int_lines)
        self.districts = []  # dict(id, name, province, poly)
        for pid, g in self.prov.items():
            pdef = self.D.PROV[pid]
            wet = pdef['realm'] in self.D.WATER
            target = self.D.DISTRICT_AREA * (self.D.WATER_FACTOR if wet else 1) * pdef.get('scale', 1.0)
            parts = polys(g)
            manual = self.D.DISTRICTS.get(pid)
            pieces = []
            if manual:
                for part in parts:
                    ss = [(pt, nm) for nm, pts in manual for pt in pts if part.contains(Point(pt))]
                    if not ss:
                        pieces.append((part, None))
                        continue
                    split = geom.voronoi_split(part, [p for p, _ in ss], [n for _, n in ss], salt=pid,
                                               frac=0.08, amax=4.0)
                    for nm, gg in split.items():
                        for p in polys(gg):
                            pieces.append((p, nm))
            else:
                for k, part in enumerate(parts):
                    hs = [h for h in self.D.HINTS if part.contains(Point(h[0], h[1]))]
                    if part.area < 0.12 * target and len(parts) > 1 and not hs:
                        pieces.append((part, None))  # sliver: joins a neighbour below
                        continue
                    pieces += self.split_geo(part, target, f'{pid}{k}', hs)
            # attach tiny unnamed slivers of manual provinces to the biggest named piece
            names = self.name_districts(pid, [p for p, _ in pieces], [n for _, n in pieces], g)
            merged = defaultdict(list)
            for (p, _), nm in zip(pieces, names):
                merged[nm].append(p)
            for nm, ps in merged.items():
                self.districts.append(dict(name=nm, province=pid, poly=unary_union(ps)))
        for i, d in enumerate(self.districts):
            d['id'] = 'd%d' % i
        log('districts', len(self.districts), '%.1fs' % (time.time() - t))

    def name_districts(self, pid, pieces, fixed, prov_poly):
        pname = self.D.PROV[pid]['name']
        if len(pieces) == 1:
            return [pname]
        names = list(fixed)
        # hint names
        for i, p in enumerate(pieces):
            if names[i]:
                continue
            for (x, y, nm) in self.D.HINTS:
                if p.contains(Point(x, y)) and nm not in names:
                    names[i] = nm
                    break
        # districts a named river runs through take the river's name
        taken = set(n for n in names if n) | set(p['name'] for p in self.D.PROV.values())
        want = {}
        for i, p in enumerate(pieces):
            if names[i]:
                continue
            core = p.buffer(-1.5)
            if core.is_empty:
                continue
            best, bl = None, 0.0
            for (idx, k), r in self.F['rivers'].items():
                nm = self.D.RIVERS.get(idx)
                if not nm or not r['line'].intersects(core):
                    continue
                L = r['line'].intersection(core).length
                if L > bl:
                    bl, best = L, nm
            if best and bl > 0.7 * math.sqrt(p.area):
                want.setdefault(best, []).append((bl, i))
        for nm, lst in want.items():
            lst.sort(reverse=True)
            label = nm if nm.endswith(('River', 'Running')) else f'{nm} Vale'
            if label in taken:
                label = f'Banks of the {nm}' if not nm.endswith(('River', 'Running')) else f'Banks of the {nm}'
            if label in taken:
                continue
            names[lst[0][1]] = label
            taken.add(label)
        # tiny pieces without names join their biggest neighbour's name
        c = prov_poly.centroid
        R = math.sqrt(prov_poly.area)
        mts = unary_union(self.ranges)
        frs = unary_union(self.F['forest'])
        wet = self.D.PROV[pid]['realm'] in self.D.WATER
        prov_mt = prov_poly.intersection(mts).area / prov_poly.area
        prov_fr = prov_poly.intersection(frs).area / prov_poly.area
        base = []
        for i, p in enumerate(pieces):
            if names[i]:
                base.append(None)
                continue
            desc = None
            if not wet:
                if prov_mt < 0.5 and p.intersection(mts).area / p.area > 0.55:
                    desc = 'Highlands'
                elif prov_fr < 0.5 and p.intersection(frs).area / p.area > 0.55:
                    desc = 'Woods'
            base.append(desc)
        # directional names
        groups = defaultdict(list)
        for i, p in enumerate(pieces):
            if names[i]:
                continue
            groups[base[i]].append(i)
        for desc, idx in groups.items():
            if len(idx) == 1 and desc:
                names[idx[0]] = f'{pname} {desc}'
                continue
            pts = [pieces[i].representative_point() for i in idx]
            cx = sum(p.x for p in pts) / len(pts); cy = sum(p.y for p in pts) / len(pts)
            if len(idx) == 1:
                cx, cy = c.x, c.y
            for i, dname in zip(idx, assign_directions([(p.x - cx, p.y - cy) for p in pts], R)):
                names[i] = compose(pname, dname, desc)
        return names

    # ---------- cells ----------
    def build_cells(self):
        t = time.time()
        self.cells = []
        for d in self.districts:
            wet = self.D.PROV[d['province']]['realm'] in self.D.WATER
            target = self.D.CELL_AREA * (self.D.WATER_FACTOR if wet else 1)
            k = 0
            for part in polys(d['poly']):
                n = int(round(part.area / target))
                if n < 2:
                    pieces = [part]
                else:
                    pts = geom.kmeans_points(part, n, seed=k)
                    pieces = []
                    for g in geom.voronoi_split(part, pts, list(range(n)), wig=False).values():
                        pieces += polys(g)
                for p in pieces:
                    if p.area < 0.5:
                        continue
                    self.cells.append(dict(district=d['id'], poly=p))
                    k += 1
        for i, c in enumerate(self.cells):
            c['id'] = i
        log('cells', len(self.cells), '%.1fs' % (time.time() - t))

    def debug_dump(self, extra=None):
        D = {}
        # province / realm edges for debug pictures
        def edges(groups):
            bs = [g.boundary for g in groups.values()]
            u = unary_union(bs)
            return [u]
        realms = defaultdict(list)
        for pid, g in self.prov.items():
            realms[self.D.PROV[pid]['realm']].append(g)
        realms = {k: unary_union(v) for k, v in realms.items()}
        D['province_edges'] = edges(self.prov)
        D['realm_edges'] = edges(realms)
        D['province_labels'] = []
        for pid, g in self.prov.items():
            big = max(polys(g), key=lambda p: p.area)
            c = shapely.ops.polylabel(big, tolerance=1.0)
            D['province_labels'].append((c.x, c.y, self.D.PROV[pid]['name']))
        D['seeds'] = [(s[0], s[1], pid) for pid, p in self.D.PROV.items() for s in p['seeds']]
        if extra:
            D.update(extra)
        pickle.dump(D, open(os.path.join(CACHE, 'dbg_regions.pkl'), 'wb'))


ROMAN = ['', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']
WINDS = ['East', 'Northeast', 'North', 'Northwest', 'West', 'Southwest', 'South', 'Southeast']
WINDS16 = ['East', 'East-northeast', 'Northeast', 'North-northeast', 'North', 'North-northwest', 'Northwest',
           'West-northwest', 'West', 'West-southwest', 'Southwest', 'South-southwest', 'South', 'South-southeast',
           'Southeast', 'East-southeast']


def assign_directions(offsets, R):
    """Give each piece a distinct compass name, as close as possible to its real bearing.
    Up to 9 pieces use the eight winds plus Central; more add a 'Far' ring; any rest are numbered."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    n = len(offsets)
    if n == 0:
        return []
    dist = np.array([math.hypot(dx, dy) for dx, dy in offsets])
    ang = np.array([(math.degrees(math.atan2(-dy, dx)) + 360) % 360 for dx, dy in offsets])
    winds = WINDS if n <= 17 else WINDS16
    step = 360 / len(winds)
    slots = [('Central', None, 0)] + [(w, k * step, 1) for k, w in enumerate(winds)]
    if n > 9:
        slots += [('Far ' + w, k * step, 2) for k, w in enumerate(winds)]
    med = np.median(dist) if n > 9 else 0
    cost = np.zeros((n, len(slots)))
    for j, (_, a, ring) in enumerate(slots):
        if a is None:
            cost[:, j] = dist / (0.18 * R) * 60
        else:
            d = np.abs((ang - a + 180) % 360 - 180)
            cost[:, j] = d + (np.where(dist < 0.12 * R, 80, 0))
            if ring == 2:
                cost[:, j] += np.where(dist > med, 0, 70)
            elif n > 9:
                cost[:, j] += np.where(dist > med, 40, 0)
    rows, cols = linear_sum_assignment(cost) if n <= len(slots) else (np.arange(0), np.arange(0))
    out = [None] * n
    for r, c_ in zip(rows, cols):
        out[r] = slots[c_][0]
    k = 0
    for i in range(n):
        if out[i] is None:
            k += 1
            out[i] = f'Reach {ROMAN[k] if k < len(ROMAN) else k}'
    return out
PREFIXES = ('Northern ', 'Southern ', 'Eastern ', 'Western ', 'North ', 'South ', 'East ', 'West ', 'Upper ',
            'Lower ', 'Central ', 'Inner ', 'Far ', 'North-eastern ', 'South-eastern ')


def compose(pname, dname, desc):
    """'North' + 'Anfalas' -> 'North Anfalas'; keeps names that already carry a direction readable."""
    core = pname[4:] if pname.startswith('The ') else pname
    if pname.startswith(PREFIXES):
        nm = f'{pname} ({dname})' if dname != 'Central' else f'Central {core}'
        if dname == 'Central':
            nm = f'{pname} (Central)'
    else:
        nm = f'{dname} {core}'
    if desc:
        nm = f'{nm} {desc}' if not nm.endswith(')') else nm.replace(' (', f' {desc} (', 1)
    return nm


def main():
    import defs
    fast = '--fast' in sys.argv
    B = Build(defs)
    B.build_provinces()
    extra = {}
    if not fast:
        B.build_districts()
        extra['district_edges'] = [unary_union([d['poly'].boundary for d in B.districts])]
        extra['district_labels'] = []
        for d in B.districts:
            big = max(polys(d['poly']), key=lambda p: p.area)
            c = shapely.ops.polylabel(big, tolerance=1.0)
            extra['district_labels'].append((c.x, c.y, d['name']))
        if '--cells' in sys.argv:
            B.build_cells()
        pickle.dump(dict(prov=B.prov, districts=B.districts, cells=getattr(B, 'cells', None)),
                    open(os.path.join(CACHE, 'regions.pkl'), 'wb'))
    B.debug_dump(extra)
    for w in B.warn:
        log('WARN', w)


if __name__ == '__main__':
    main()
