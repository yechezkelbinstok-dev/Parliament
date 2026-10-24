"""Pack the region geometry and the base artwork into app/data.js for the coloring app."""
import json, math, os, pickle, sys, time
from collections import defaultdict

import numpy as np
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import linemerge, unary_union, polylabel
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import defs
from geom import polys, lines

CACHE = os.path.join(HERE, '.cache')
OUT = os.path.join(HERE, '..', 'app', 'data.js')


def enc_ring(coords):
    """Compact SVG path for one ring: absolute start, then relative steps at 0.1 pt."""
    pts = [(round(x * 10), round(y * 10)) for x, y in coords]
    out = []
    prev = None
    for p in pts:
        if p == prev:
            continue
        if prev is None:
            out.append('M%s %s' % (fmt(p[0]), fmt(p[1])))
            out.append('l')
        else:
            out.append(fmt_rel(p[0] - prev[0], p[1] - prev[1]))
        prev = p
    if len(out) < 4:  # fewer than two steps: nothing to draw
        return ''
    return out[0] + out[1] + ''.join(out[2:])


def fmt(v):
    s = '%.1f' % (v / 10)
    return s[:-2] if s.endswith('.0') else s


def fmt_rel(dx, dy):
    a, b = fmt(dx), fmt(dy)
    sep = '' if b.startswith('-') else ' '
    lead = '' if a.startswith('-') else ' '
    return lead + a + sep + b


def enc_poly(g, close=True):
    parts = []
    for p in polys(g):
        for r in [p.exterior] + list(p.interiors):
            s = enc_ring(list(r.coords)[:-1])
            if s:
                parts.append(s + 'z')
    return ''.join(parts)


def enc_lines(g):
    parts = []
    for ln in lines(g):
        cs = list(ln.coords)
        if len(cs) >= 2:
            parts.append(enc_ring(cs))
    return ''.join(parts)


def label_of(g):
    big = max(polys(g), key=lambda p: p.area)
    c = polylabel(big, tolerance=0.5)
    r = big.exterior.distance(c)
    for h in big.interiors:
        r = min(r, h.distance(c))
    # width available along the horizontal through the label point
    minx, miny, maxx, maxy = big.bounds
    chord = LineString([(minx - 1, c.y), (maxx + 1, c.y)]).intersection(big)
    w = 0
    for seg in lines(chord):
        if seg.distance(c) < 1e-6:
            w = seg.length
    return [round(c.x, 1), round(c.y, 1), round(r, 1), round(max(w, 2 * r), 1)]


def main():
    t = time.time()
    R = pickle.load(open(os.path.join(CACHE, 'regions.pkl'), 'rb'))
    base = json.load(open(os.path.join(CACHE, 'base.json')))
    prov_ids = [pid for pid in defs.PROV if pid in R['prov']]
    realm_ids = [rid for rid in defs.REALMS if any(defs.PROV[p]['realm'] == rid for p in prov_ids)]
    p_index = {p: i for i, p in enumerate(prov_ids)}
    r_index = {r: i for i, r in enumerate(realm_ids)}
    D = R['districts']
    d_index = {d['id']: i for i, d in enumerate(D)}
    cells = R['cells']

    realm_geo = defaultdict(list)
    for pid in prov_ids:
        realm_geo[defs.PROV[pid]['realm']].append(R['prov'][pid])
    realm_geo = {k: unary_union(v) for k, v in realm_geo.items()}

    realms = [dict(n=defs.REALMS[r], w=int(r in defs.WATER), id=r, l=label_of(realm_geo[r])) for r in realm_ids]
    provinces = [dict(n=defs.PROV[p]['name'], r=r_index[defs.PROV[p]['realm']], id=p, l=label_of(R['prov'][p]))
                 for p in prov_ids]
    districts = [dict(n=d['name'], p=p_index[d['province']], l=label_of(d['poly'])) for d in D]
    log('labels', '%.1fs' % (time.time() - t))

    # cells, simplified a touch
    cell_d = []
    cell_path = []
    geoms = []
    for c in cells:
        g = c['poly'].simplify(0.12, preserve_topology=True)
        cell_d.append(d_index[c['district']])
        cell_path.append(enc_poly(g))
        geoms.append(c['poly'])
    log('cells', len(cells), '%.1fs' % (time.time() - t))

    # shared edges, classified by the highest level at which the two sides differ
    cell_realm = []
    cell_prov = []
    for i, c in enumerate(cells):
        p = districts[cell_d[i]]['p']
        cell_prov.append(p)
        cell_realm.append(provinces[p]['r'])
    tree = STRtree(geoms)
    net = shapely.union_all([g.boundary for g in geoms])
    segs = lines(net)
    mids, nl, nr = [], [], []
    for s in segs:
        cs = list(s.coords)
        k = len(cs) // 2
        a, b = cs[k - 1], cs[k] if len(cs) > 1 else cs[0]
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        L = math.dist(a, b) or 1
        nx, ny = -(b[1] - a[1]) / L * 0.02, (b[0] - a[0]) / L * 0.02
        nl.append(Point(mx + nx, my + ny)); nr.append(Point(mx - nx, my - ny))
    def side(pts):
        res = np.full(len(pts), -1)
        q = tree.query(pts, predicate='within')
        for i, j in zip(q[0], q[1]):
            res[i] = j
        return res
    L_, R_ = side(nl), side(nr)
    buckets = defaultdict(list)
    for s, a, b in zip(segs, L_, R_):
        if a < 0 or b < 0 or a == b:
            continue
        wa = realms[cell_realm[a]]['w']; wb = realms[cell_realm[b]]['w']
        if wa != wb:
            continue  # coastline: the base map draws it
        if cell_realm[a] != cell_realm[b]:
            lvl = 'realm'
        elif cell_prov[a] != cell_prov[b]:
            lvl = 'province'
        elif cell_d[a] != cell_d[b]:
            lvl = 'district'
        else:
            lvl = 'cell'
        buckets[(lvl, 'w' if wa else 'l')].append(s)
    edges = {}
    for (lvl, kind), ss in buckets.items():
        m = linemerge(ss)
        m = shapely.simplify(m, 0.12)
        edges[f'{lvl}_{kind}'] = enc_lines(m)
    log('edges', {k: len(v) for k, v in edges.items()}, '%.1fs' % (time.time() - t))

    # map lettering that names a place: remember the district under it, for search
    places = []
    for kind in ('place', 'region'):
        for L in base['labels'].get(kind, []):
            q = tree.query(Point(L['x'], L['y']), predicate='within')
            if len(q):
                places.append([L['text'], cell_d[int(q[0])]])
    # which units touch which, per level (for automatic colouring)
    adj = {'realm': set(), 'province': set(), 'district': set()}
    for s, a, b in zip(segs, L_, R_):
        if a < 0 or b < 0 or a == b:
            continue
        for lvl, ka, kb in (('realm', cell_realm[a], cell_realm[b]), ('province', cell_prov[a], cell_prov[b]),
                            ('district', cell_d[a], cell_d[b])):
            if ka != kb:
                adj[lvl].add((min(ka, kb), max(ka, kb)))
    adj = {k: [x for pair in sorted(v) for x in pair] for k, v in adj.items()}
    data = dict(
        realms=realms, provinces=provinces, districts=districts,
        cells=dict(d=cell_d, path=cell_path, a=[round(g.area, 1) for g in geoms]),
        edges=edges, adj=adj, places=places,
        frame=[57.2773, 49.542, 2402.276, 1689.0293],
        base=base['layers'], glyphs=base['glyphs'], labels=base['labels'],
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    js = 'window.ME_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n'
    with open(OUT, 'w') as f:
        f.write(js)
    log('wrote', OUT, '%.1f MB' % (len(js.encode()) / 1e6), '%.1fs' % (time.time() - t))


def log(*a):
    print(*a, flush=True)


if __name__ == '__main__':
    main()
