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
        self.notes = []

    # ---------- line primitives ----------
    def river(self, idx, a=None, b=None, k=0):
        return self.part_of(self.F['rivers'][(idx, k)]['line'], a, b)

    def road(self, idx, a=None, b=None, k=0):
        return self.part_of(self.F['roads'][(idx, k)], a, b)

    @staticmethod
    def part_of(ln, a=None, b=None):
        """Stretch of a line between the points nearest a and b (whole line if not given), in a-to-b order."""
        s0 = ln.project(Point(a)) if a else 0.0
        s1 = ln.project(Point(b)) if b else ln.length
        part = substring(ln, min(s0, s1), max(s0, s1))
        cs = list(part.coords)
        return cs if s0 <= s1 else cs[::-1]

    def ring_part(self, ring, a, b, via=None):
        """Part of a closed ring between the points nearest a and b (through `via` if given), in a-to-b order."""
        ln = LineString(ring.coords)
        L = ln.length
        s0, s1 = ln.project(Point(a)), ln.project(Point(b))
        lo, hi = min(s0, s1), max(s0, s1)
        inner = substring(ln, lo, hi)
        outer = linemerge([substring(ln, hi, L), substring(ln, 0, lo)])
        if via is not None:
            pick = inner if inner.distance(Point(via)) < outer.distance(Point(via)) else outer
        else:
            pick = inner if inner.length <= outer.length else outer
        cs = list(lines(pick)[0].coords) if pick.geom_type != 'LineString' else list(pick.coords)
        if math.dist(cs[0], ln.interpolate(s0).coords[0]) > math.dist(cs[-1], ln.interpolate(s0).coords[0]):
            cs = cs[::-1]
        return cs

    def find(self, kind, pt):
        gs = self.F['forest'] if kind == 'forest' else self.ranges
        p = Point(pt)
        hit = [g for g in gs if g.contains(p)]
        if not hit:
            g = min(gs, key=lambda g: g.distance(p))
            self.warn.append(f'{kind} ref {pt} not inside any outline, using nearest ({g.distance(p):.1f} away)')
            return g
        return min(hit, key=lambda g: g.area)

    def skel(self, g):
        """Medial-axis graph of a polygon (cached): Voronoi edges of its sampled outline that lie inside it."""
        import networkx as nx
        key = g.wkb
        if not hasattr(self, '_skel'):
            self._skel = {}
        if key in self._skel:
            return self._skel[key]
        pts = []
        for r in [g.exterior] + list(g.interiors):
            pts += list(shapely.segmentize(LineString(r.coords), 1.5).coords)
        edges = shapely.voronoi_polygons(shapely.MultiPoint(pts), only_edges=True)
        G = nx.Graph()
        prep = shapely.prepared.prep(g)
        for e in lines(edges):
            if prep.contains(e):
                a, b = e.coords[0], e.coords[-1]
                a = (round(a[0], 3), round(a[1], 3)); b = (round(b[0], 3), round(b[1], 3))
                G.add_edge(a, b, weight=e.length)
        import numpy as np
        nodes = list(G.nodes)
        self._skel[key] = (G, nodes, np.array(nodes))
        return self._skel[key]

    def spine(self, g, pts):
        """Path along the medial axis of g through the points nearest to pts, extended to the first and last."""
        import networkx as nx
        import numpy as np
        G, nodes, arr = self.skel(g)
        def near(p):
            return nodes[int(np.argmin(((arr - np.array(p)) ** 2).sum(1)))]
        path = []
        for a, b in zip(pts, pts[1:]):
            seg = nx.shortest_path(G, near(a), near(b), weight='weight')
            path += seg if not path else seg[1:]
        ln = LineString(path).simplify(0.5)
        cs = geom.chaikin(list(ln.coords), 2)
        return [tuple(pts[0])] + cs + [tuple(pts[-1])]

    def hand(self, name, pts, wig=1.0):
        """A drawn border through the given points: a smooth curve with a little natural unevenness."""
        cs = geom.catmull(pts, step=2.0)
        if wig:
            cs = geom.wiggle(cs, frac=0.04 * wig, amax=1.6 * wig, seg=2.0, salt=name)
        return cs

    def make_line(self, name, spec):
        """Coordinates for one border line spec; returns [(coords, closed)]."""
        kind = spec[0]
        if kind == 'river':
            return [(self.river(*spec[1:]), False)]
        if kind == 'road':
            return [(self.road(*spec[1:]), False)]
        if kind in ('foot', 'edge'):
            g = self.find('range' if kind == 'foot' else 'forest', spec[1])
            return [(self.ring_part(g.exterior, spec[2], spec[3], spec[4] if len(spec) > 4 else None), False)]
        if kind == 'buffer_at':
            g = self.find(spec[1], spec[2]).buffer(spec[3]).simplify(0.4)
            return [(list(g.exterior.coords), True)]
        if kind == 'hull_at':
            g = unary_union([self.find(spec[1], p) for p in spec[2]])
            g = shapely.concave_hull(g, ratio=spec[3] if len(spec) > 3 else 0.3).buffer(1.0).simplify(0.4)
            return [(list(g.exterior.coords), True)]
        if kind == 'union_at':
            r = spec[3] if len(spec) > 3 else 1.5
            parts = [self.find(spec[1], p) if not isinstance(p[0], str) else self.find(p[0], p[1]) for p in spec[2]]
            g = unary_union(parts).buffer(r).buffer(-r)
            g = max(polys(g), key=lambda p: p.area)
            return [(list(g.exterior.coords), True)]
        if kind in ('range_at', 'forest_at'):
            g = self.find(kind.split('_')[0], spec[1])
            opts = spec[2] if len(spec) > 2 else {}
            for m in opts.get('minus', []):
                g = g.difference(Polygon(m))
            for k2, p2 in opts.get('minus_at', []):
                # cut exactly along the other outline, so the two share one border with no gap between
                other = self.find(k2, p2)
                g = shapely.snap(g.difference(other), other.exterior, 0.3)
            if opts.get('to_water'):
                # an outline that stops just short of a shore is carried down to the water's edge
                d = opts['to_water']
                water = self.F['water']
                gap = g.buffer(d).intersection(water.buffer(d)).difference(water)
                g = unary_union([g, gap]).buffer(0.6).buffer(-0.6).difference(water)
            g = max(polys(g), key=lambda p: p.area)
            return [(list(r.coords), True) for r in [g.exterior] + list(g.interiors)]
        if kind == 'crest':
            return [(self.spine(self.find('range', spec[1]), spec[2]), False)]
        if kind == 'axis':
            poly = max(polys(self.F['anduin_poly'].buffer(0)), key=lambda p: p.area)
            return [(self.spine(poly, spec[1]), False)]
        if kind == 'hand':
            return [(self.hand(name, spec[1], spec[2] if len(spec) > 2 else 1.0), False)]
        if kind == 'poly':
            return [([tuple(p) for p in spec[1]], False)]
        raise ValueError(f'{name}: unknown line kind {kind}')

    def hard_lines(self):
        fixed = []
        for p in polys(self.F['water']):
            fixed += lines(p)
        fixed += lines(self.F['frame'])
        fixed_u = unary_union(fixed)
        raw = []
        for name, spec in self.D.LINES:
            for cs, closed in self.make_line(name, spec):
                raw.append((name, cs, 'ring' if closed else spec[0]))
        # ends that meet ends: make them one point exactly
        raw = [(n, [tuple(p) for p in cs], k) for n, cs, k in raw]
        ends = [(i, e, raw[i][1][e]) for i in range(len(raw)) if raw[i][2] != 'ring' for e in (0, -1)]
        parent = list(range(len(ends)))
        def root(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        for a in range(len(ends)):
            for b in range(a + 1, len(ends)):
                if ends[a][0] != ends[b][0] and math.dist(ends[a][2], ends[b][2]) < 3.0:
                    parent[root(a)] = root(b)
        groups = defaultdict(list)
        for a in range(len(ends)):
            groups[root(a)].append(a)
        joined = set()
        for g in groups.values():
            if len(g) < 2:
                continue
            mx = sum(ends[a][2][0] for a in g) / len(g); my = sum(ends[a][2][1] for a in g) / len(g)
            # a meeting point that sits on a third line (a coast, a river) goes exactly onto it
            members = {ends[a][0] for a in g}
            p = Point(mx, my)
            cands = [fixed_u] + [LineString(raw[j][1]) for j in range(len(raw)) if j not in members]
            near = min(cands, key=lambda L: L.distance(p))
            on_line = near.distance(p) < 2.5
            if on_line:
                q = shapely.ops.nearest_points(near, p)[0]
                mx, my = q.x, q.y
            for a in g:
                i, e, _ = ends[a]
                c = raw[i][1]
                c[e] = (mx, my)
                if on_line:
                    prev = c[1] if e == 0 else c[-2]
                    L = math.dist((mx, my), prev) or 1
                    over = (mx + (mx - prev[0]) / L * 1.5, my + (my - prev[1]) / L * 1.5)
                    if e == 0:
                        c.insert(0, over)
                    else:
                        c.append(over)
                joined.add((i, e if e == 0 else -1))
        # other open ends: bring them onto the nearest line and run on past it a little
        out = []
        allg = [fixed_u] + [LineString(cs) for _, cs, _ in raw]
        tree = STRtree(allg)
        for i, (name, cs, kind) in enumerate(raw):
            if kind == 'ring':
                out.append(LineString(cs))
                continue
            tol = self.D.SNAP.get(name, 6.0)
            c2 = list(cs)
            for end in (0, -1):
                if (i, end) in joined:
                    continue
                p = Point(c2[end])
                near = [j for j in tree.query(p.buffer(tol)) if j != i + 1]
                if not near:
                    continue
                others = unary_union([allg[j] for j in near])
                c2 = geom.snap_end(c2, end, others, tol)
            out.append(LineString(c2))
        self.hard = out
        self.hard_names = [name for name, _, _ in raw]
        self.hard_kinds = [kind for _, _, kind in raw]
        self.fixed = fixed
        return fixed + out

    def weak_lines(self):
        """Open lines that meet the rest of the network fewer than twice: they cannot divide anything."""
        allg = [unary_union(self.fixed)] + list(self.hard)
        tree = STRtree(allg)
        out = []
        for i, (ln, name, kind) in enumerate(zip(self.hard, self.hard_names, self.hard_kinds)):
            if kind == 'ring':
                continue
            pts = []
            for j in tree.query(ln, predicate='intersects'):
                if j == i + 1:
                    continue
                x = ln.intersection(allg[j])
                for g in getattr(x, 'geoms', [x]):
                    if g.is_empty:
                        continue
                    c = g.coords[0] if g.geom_type == 'Point' else g.coords[0]
                    pts.append(ln.project(Point(c)))
            pts = sorted(pts)
            distinct = [p for k, p in enumerate(pts) if k == 0 or p - pts[k - 1] > 1.0]
            if len(distinct) < 2:
                out.append((name, len(distinct)))
        return out

    def dangling(self):
        """Ends of open lines that cross nothing: such a line cannot close off a region there."""
        allg = [unary_union(self.fixed)] + list(self.hard)
        tree = STRtree(allg)
        out = []
        for i, (ln, name, kind) in enumerate(zip(self.hard, self.hard_names, self.hard_kinds)):
            if kind == 'ring':
                continue
            L = ln.length
            for end, piece in ((ln.coords[0], substring(ln, 0, min(L, 3.0))),
                               (ln.coords[-1], substring(ln, max(0, L - 3.0), L))):
                hit = [j for j in tree.query(piece.buffer(0.01), predicate='intersects') if j != i + 1]
                if not hit:
                    near = [j for j in tree.query(Point(end).buffer(50)) if j != i + 1]
                    d = min((allg[j].distance(Point(end)) for j in near), default=99)
                    out.append((name, tuple(round(v) for v in end), round(d, 1)))
        return out

    # ---------- provinces ----------
    def build_provinces(self):
        """Provinces are exactly the faces of the border network, each claimed by the label points inside it."""
        t = time.time()
        work = self.hard_lines()
        for name, n in self.weak_lines():
            self.warn.append(f'line {name} meets the other lines {n} time(s): it divides nothing')
        if '--ends' in sys.argv:
            for d in self.dangling():
                self.notes.append(f'line {d[0]}: loose end at {d[1]} ({d[2]} pt from the nearest line)')
        faces = geom.faces_of(work, within=self.F['frame'])
        tiny = [p for p in self.F['lakes'].values() if p.area < TINY_LAKE]
        faces = [f for f in faces if not any(t_.contains(f.representative_point()) for t_ in tiny)]
        land = self.F['land']
        wet_face = [not land.contains(f.representative_point()) for f in faces]
        # slivers left between near-parallel lines join the neighbour they share most border with
        keys = list(range(len(faces)))
        for i, f in enumerate(faces):
            if f.area < 12 or (f.area < 80 and 4 * math.pi * f.area / f.length ** 2 < 0.05):
                keys[i] = None
                if f.area > 4:
                    c = f.representative_point()
                    self.notes.append(f'sliver of {f.area:.0f} at ({c.x:.0f},{c.y:.0f}) joined to a neighbour')
        n0 = len(faces)
        faces, keys = geom.merge_small(faces, keys, min_area=0, group=wet_face)
        log('faces', n0, '->', len(faces), '%.1fs' % (time.time() - t))
        tree = STRtree(faces)
        claims = defaultdict(list)  # face -> [(point, pid)]
        for pid, pdef in self.D.PROV.items():
            wet = pdef['realm'] in self.D.WATER
            for s in pdef['seeds']:
                if land.contains(Point(s)) == wet:
                    self.warn.append(f'label point of {pid} at {s} is in {"water" if not wet else "land"}')
                    continue
                hit = [i for i in tree.query(Point(s)) if faces[i].contains(Point(s))]
                if not hit:
                    self.warn.append(f'label point of {pid} at {s} is on a line')
                    continue
                claims[hit[0]].append((s, pid))
        pieces, owner = [], []
        self.bad_faces = []
        for i, f in enumerate(faces):
            cl = claims.get(i, [])
            pids = sorted({p for _, p in cl})
            if not pids:
                c = f.representative_point()
                if f.area < 150:
                    self.notes.append(f'small unclaimed region of {f.area:.0f} at ({c.x:.0f},{c.y:.0f}) joins a neighbour')
                else:
                    self.warn.append(f'unclaimed region of {f.area:.0f} at ({c.x:.0f},{c.y:.0f})')
                    self.bad_faces.append(f)
                pieces.append(f); owner.append(None)
            elif len(pids) == 1:
                pieces.append(f); owner.append(pids[0])
            elif all(self.D.PROV[p].get('free') for p in pids):
                # no lore border here (open sea, empty waste): share the region out by nearness
                split = geom.voronoi_split(f, [s for s, _ in cl], [p for _, p in cl], salt='f%d' % i,
                                           frac=0.08, amax=7.0)
                for k, g in split.items():
                    for p in polys(g):
                        pieces.append(p); owner.append(k)
            else:
                c = f.representative_point()
                self.warn.append(f'{" and ".join(pids)} share one region near ({c.x:.0f},{c.y:.0f}): a border is missing')
                self.bad_faces.append(f)
                pieces.append(f); owner.append(pids[0])
        faces, owner = geom.merge_small(pieces, owner, min_area=0,
                                        group=[not land.contains(p.representative_point()) for p in pieces])
        prov = defaultdict(list)
        for f, k in zip(faces, owner):
            prov[k].append(f)
        self.prov = {}
        for k, v in prov.items():
            if k is None:
                continue
            g = unary_union(v).buffer(0)
            self.prov[k] = unary_union([p for p in polys(g) if p.area > 1.0])
        for pid in self.D.PROV:
            if pid not in self.prov:
                self.warn.append(f'province without area: {pid}')
        for pid, g in self.prov.items():
            parts = polys(g)
            if len(parts) > 1 and not self.D.PROV[pid].get('multi'):
                small = sorted(p.area for p in parts)[:-1]
                self.warn.append(f'{pid} is in {len(parts)} pieces, smaller ones {[round(a) for a in small]}')
        log('provinces', len(self.prov), '%.1fs' % (time.time() - t))

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
        self.used_names = {p['name'] for p in self.D.PROV.values()}
        self.river_list = [(idx, r['line']) for (idx, k), r in self.F['rivers'].items()]
        self.river_tree = STRtree([l for _, l in self.river_list])
        self.named_features = [(kind, self.find(kind, pt), nm) for kind, pt, nm in self.D.FEATURE_NAMES]
        def rim(g):
            return unary_union([LineString(r.coords) for p in polys(g) for r in [p.exterior] + list(p.interiors)]).buffer(1.0)
        self.sea_rim = rim(self.F['sea'])
        self.lake_rim = rim(unary_union(list(self.F['lakes'].values())))
        land = [(pid, g) for pid, g in self.prov.items() if self.D.PROV[pid]['realm'] not in self.D.WATER]
        self.land_provs = land
        self.land_tree = STRtree([g for _, g in land])
        # land first, so a sea district named after a coast never takes a name a land district needs
        order = sorted(self.prov, key=lambda pid: self.D.PROV[pid]['realm'] in self.D.WATER)
        for pid in order:
            g = self.prov[pid]
            pdef = self.D.PROV[pid]
            wet = pdef['realm'] in self.D.WATER
            target = self.D.DISTRICT_AREA * (self.D.WATER_FACTOR if wet else 1) * pdef.get('scale', 1.0)
            n_hints = sum(1 for h in self.D.HINTS if g.contains(Point(h[0], h[1])))
            target = max(target, g.area / (8 + n_hints))
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
            # a crumb cut off from the rest of its district joins the neighbour it shares most border with
            items = []
            for nm, ps in merged.items():
                parts_ = sorted(polys(unary_union(ps)), key=lambda p: -p.area)
                items += [(p, nm, nm if j == 0 or p.area >= 0.2 * target else None) for j, p in enumerate(parts_)]
            faces, keys = geom.merge_small([p for p, _, _ in items], [k for _, _, k in items], min_area=0)
            back = {id(p): nm for p, nm, _ in items}
            merged = defaultdict(list)
            for f, k in zip(faces, keys):
                merged[k if k is not None else back.get(id(f))].append(f)
            for nm, ps in merged.items():
                self.districts.append(dict(name=nm, province=pid, poly=unary_union(ps)))
        for i, d in enumerate(self.districts):
            d['id'] = 'd%d' % i
        log('districts', len(self.districts), '%.1fs' % (time.time() - t))

    def name_districts(self, pid, pieces, fixed, prov_poly):
        """Names for the districts of one province, each used once on the whole map: a lore place in it first,
        then a river through it, a named wood or range, the coast (or, at sea, the coast it lies off),
        and only then a compass point within the province."""
        pdef = self.D.PROV[pid]
        pname = pdef['name']
        n = len(pieces)
        if n == 1:
            return [pname]
        used = self.used_names
        names = [None] * n
        for i, nm in enumerate(fixed):
            if nm and nm not in used:
                names[i] = nm
                used.add(nm)
        for i, p in enumerate(pieces):
            if names[i]:
                continue
            for (x, y, nm) in self.D.HINTS:
                if nm not in used and p.contains(Point(x, y)):
                    names[i] = nm
                    used.add(nm)
                    break
        core_name = pname[4:] if pname.startswith('The ') else pname
        realm = pdef['realm']
        wet = realm in self.D.WATER
        cands = []
        for i, p in enumerate(pieces):
            if names[i]:
                continue
            s = math.sqrt(p.area)
            if wet:
                if realm in self.D.SEAS:
                    # open water takes the name of the coast it lies off
                    near = p.buffer(4.0)
                    for j in self.land_tree.query(near):
                        qid, q = self.land_provs[j]
                        L = q.boundary.intersection(near).length
                        if L > 0.25 * s:
                            cands.append((1.0 + L / s, i, self.D.SEA_NAMES.get(qid, f"{self.D.PROV[qid]['name']} Waters")))
                continue
            core = p.buffer(-1.5)
            if core.is_empty:
                continue
            lens = defaultdict(float)
            for j in self.river_tree.query(core):
                idx, line = self.river_list[j]
                nm = self.D.RIVERS.get(idx)
                if nm and nm not in pname:
                    lens[nm] += line.intersection(core).length
            for nm, L in lens.items():
                if L > 0.7 * s:
                    cands.append((1.0 + L / s, i, nm if nm.endswith(('River', 'Running')) else f'{nm} Vale'))
            for kind, g, fname in self.named_features:
                if not g.intersects(p):
                    continue
                cov = p.intersection(g).area / p.area
                if cov < 0.55 or prov_poly.intersection(g).area / prov_poly.area > 0.5:
                    continue
                inside = g.intersection(prov_poly).area / g.area
                label = fname if inside > 0.7 else f"{core_name} {'Woods' if kind == 'forest' else 'Highlands'}"
                cands.append((1.5 + cov, i, label))
            for rim_, word in ((self.sea_rim, 'Coast'), (self.lake_rim, 'Shore')):
                shore = p.boundary.intersection(rim_).length / p.length
                if shore > 0.15:
                    cands.append((0.5 + shore, i, f'{core_name} {word}'))
        cands.sort(key=lambda c: -c[0])
        for _, i, nm in cands:
            if names[i] or nm in used or nm == pname:
                continue
            names[i] = nm
            used.add(nm)
        rest = [i for i in range(n) if not names[i]]
        # more than the compass can name: the smallest join the neighbour they share most border with
        alias = {}
        while len(rest) > 9:
            i = min(rest, key=lambda k: pieces[k].area)
            others = [k for k in range(n) if k != i and k not in alias]
            j = max(others, key=lambda k: pieces[i].boundary.intersection(pieces[k].buffer(0.05)).length)
            alias[i] = j
            rest.remove(i)
        if rest:
            pts = [pieces[i].representative_point() for i in rest]
            c = prov_poly.centroid
            offs = [(p.x - c.x, p.y - c.y) for p in pts]
            paren = wet or ' of ' in pname or pname.startswith(DIR_WORDS)
            for i, d in zip(rest, assign_directions(offs, math.sqrt(prov_poly.area))):
                if paren:
                    nm = f'{pname} ({d})'
                else:
                    nm = f'{d} {core_name}'
                k = 2
                while nm in used:
                    nm = f'{nm.rsplit(" ~", 1)[0]} ~{k}'
                    k += 1
                names[i] = nm
                used.add(nm)
        for i in alias:
            j = i
            while j in alias:
                j = alias[j]
            names[i] = names[j]
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
                    # a cell that falls apart across a narrow neck leaves crumbs: they join a neighbour
                    pieces, _ = geom.merge_small(pieces, list(range(len(pieces))), min_area=0.3 * target)
                for p in pieces:
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


WINDS = ['East', 'Northeast', 'North', 'Northwest', 'West', 'Southwest', 'South', 'Southeast']
DIR_WORDS = ('Northern ', 'Southern ', 'Eastern ', 'Western ', 'North ', 'South ', 'East ', 'West ', 'Central ',
             'Upper ', 'Lower ', 'Far ')


def assign_directions(offsets, R):
    """A distinct compass point for each piece, as close as possible to its real bearing from the centre:
    the eight winds, and Central for a piece at the middle (only when there are four or more)."""
    import numpy as np
    from scipy.optimize import linear_sum_assignment
    n = len(offsets)
    if n == 0:
        return []
    dist = np.array([math.hypot(dx, dy) for dx, dy in offsets])
    ang = np.array([(math.degrees(math.atan2(-dy, dx)) + 360) % 360 for dx, dy in offsets])
    slots = [(w, k * 45.0) for k, w in enumerate(WINDS)]
    if n >= 4:
        slots.append(('Central', None))
    cost = np.zeros((n, len(slots)))
    for j, (_, a) in enumerate(slots):
        if a is None:
            cost[:, j] = dist / (0.15 * R) * 45
        else:
            d = np.abs((ang - a + 180) % 360 - 180)
            cost[:, j] = d + np.where(dist < 0.1 * R, 60, 0)
    if n > len(slots):
        raise ValueError(f'{n} districts need compass names but only {len(slots)} points exist')
    rows, cols = linear_sum_assignment(cost)
    out = [None] * n
    for r, c_ in zip(rows, cols):
        out[r] = slots[c_][0]
    return out


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
    else:
        pickle.dump(dict(prov=B.prov, districts=[], cells=None), open(os.path.join(CACHE, 'regions.pkl'), 'wb'))
    extra['net'] = [(n, list(l.coords)) for n, l in zip(B.hard_names, B.hard)]
    extra['bad'] = B.bad_faces
    B.debug_dump(extra)
    for w in B.warn:
        log('WARN', w)
    if '--notes' in sys.argv:
        for w in B.notes:
            log('NOTE', w)


if __name__ == '__main__':
    main()
