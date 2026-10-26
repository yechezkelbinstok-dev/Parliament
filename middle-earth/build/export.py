"""Pack the region geometry and the base artwork into app/data.js for the coloring app."""
import json, math, os, pickle, re, sys, time, unicodedata
from collections import defaultdict

import numpy as np
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import linemerge, unary_union, polylabel
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import defs
import mepdf
from geom import polys, lines

CACHE = os.path.join(HERE, '.cache')
OUT = os.path.join(HERE, '..', 'app', 'data.js')


def enc_ring(coords, min_steps=2):
    """Compact SVG path for one ring or line: absolute start, then relative steps at 0.1 pt.
    A ring needs two steps to enclose anything; a line needs one."""
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
    if len(out) < 2 + min_steps:
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
            parts.append(enc_ring(cs, 1))
    return ''.join(parts)


def chord_ends(poly, x, y):
    """Ends of the horizontal chord through (x, y) inside poly."""
    minx, _, maxx, _ = poly.bounds
    chord = LineString([(minx - 1, y), (maxx + 1, y)]).intersection(poly)
    for seg in lines(chord):
        if seg.distance(Point(x, y)) < 1e-6:
            xs = [c[0] for c in seg.coords]
            return min(xs), max(xs)
    return x, x


def label_cands(g, k=8):
    """Places a unit's name could go, best first: the pole of inaccessibility, then other roomy spots
    spread over the unit, each also centred on its chord. Each is [x, y, r, w]: r the distance to the
    nearest edge, w the width a name centred there has before it runs out of the unit.
    The app picks the biggest that keeps clear of the map's own lettering."""
    big = max(polys(g), key=lambda p: p.area)
    c0 = polylabel(big, tolerance=0.5)
    bd = big.boundary
    r0 = max(bd.distance(c0), 0.1)
    pts = [(c0.x, c0.y, r0)]
    minx, miny, maxx, maxy = big.bounds
    s = max(0.6, math.sqrt(big.area) / 10)
    X, Y = np.meshgrid(np.arange(minx + s / 2, maxx, s), np.arange(miny + s / 2, maxy, s))
    X, Y = X.ravel(), Y.ravel()
    inside = shapely.contains_xy(big, X, Y)
    X, Y = X[inside], Y[inside]
    if len(X):
        d = shapely.distance(bd, shapely.points(X, Y))
        for i in np.argsort(-d):
            if len(pts) >= k or d[i] < 0.3 * r0:
                break
            x, y = float(X[i]), float(Y[i])
            if all(math.hypot(x - cx, y - cy) > 0.9 * max(cr, d[i]) for cx, cy, cr in pts):
                pts.append((x, y, float(d[i])))
    out = []
    for x, y, r in pts:
        xl, xr = chord_ends(big, x, y)
        out.append([x, y, r, max(2 * min(x - xl, xr - x), 2 * r)])
        mx = (xl + xr) / 2
        if xr - xl > 0 and abs(mx - x) > 0.15 * (xr - xl):
            out.append([mx, y, max(bd.distance(Point(mx, y)), 0.1), xr - xl])
    return [[round(v, 1) for v in c] for c in out]


KIND_BIT = {'place': 1, 'region': 2, 'political': 2, 'decor': 4}
GENERIC = {'marsh', 'marshes', 'fields', 'field', 'downs', 'hills', 'hill', 'woods', 'wood', 'forest'}


def simple(t):
    t = unicodedata.normalize('NFD', t)
    t = ''.join(ch for ch in t if not unicodedata.combining(ch)).lower()
    t = re.sub(r'[^a-z0-9]+', ' ', t).strip()
    return re.sub(r'^the ', '', t)


def lettering(base):
    """The map's own lettering: a box per run of glyphs (to keep region names clear of it), and every
    name it prints, including names set over two lines, with where it stands."""
    gbox = []
    for d in base['glyphs']:
        xs, ys = [], []
        for pts, _ in mepdf.parse_d(d, tol=0.02):
            xs += [p[0] for p in pts]; ys += [p[1] for p in pts]
        gbox.append((min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 0, 0))
    boxes = defaultdict(list)
    phrases = []
    for kind, labs in base['labels'].items():
        bit = KIND_BIT.get(kind)
        if not bit:
            continue
        for L in labs:
            run = None
            for gid, a, b, c, dd, e, f in L['u']:
                x0, y0, x1, y1 = gbox[gid]
                if x1 <= x0:
                    continue
                cs = [(a * x + c * y + e, b * x + dd * y + f) for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))]
                bx = [min(p[0] for p in cs), min(p[1] for p in cs), max(p[0] for p in cs), max(p[1] for p in cs)]
                straight = abs(b) < 1e-6 and abs(c) < 1e-6
                if run and straight and run[4] and abs(run[5] - f) < 0.01 and bx[0] - run[2] < abs(a) * 0.8:
                    run[0] = min(run[0], bx[0]); run[1] = min(run[1], bx[1])
                    run[2] = max(run[2], bx[2]); run[3] = max(run[3], bx[3])
                else:
                    if run:
                        boxes[bit].append(run[:4])
                    run = bx + [straight, f]
            if run:
                boxes[bit].append(run[:4])
            # 'NENUIAL (Lake Evendim)' prints two names
            parts = [simple(x) for x in re.split(r'[()]', L['text']) if simple(x)]
            phrases.append(dict(t=simple(L['text']), parts=parts, x=L['x'], y=L['y'], bit=bit,
                                size=abs(L['u'][0][1]) if L['u'] else 10))
    # names set over two lines: join each line with the one just below it
    two = []
    for p in phrases:
        for q in phrases:
            if q is p or q['bit'] != p['bit'] or abs(q['size'] - p['size']) > 0.5:
                continue
            dy = q['y'] - p['y']
            if 0 < dy < 1.6 * p['size'] and abs(q['x'] - p['x']) < 3 * p['size']:
                t = p['t'] + ' ' + q['t']
                two.append(dict(t=t, parts=[t], x=(p['x'] + q['x']) / 2, y=(p['y'] + q['y']) / 2,
                                bit=p['bit'], size=p['size']))
    flat = {bit: [round(v, 1) for bx in bs for v in bx] for bit, bs in boxes.items()}
    return flat, phrases + two


def dup_bits(name, g, phrases, min_size=0, near=2):
    """Which kinds of the map's lettering already print this unit's name inside it: the whole name,
    one of two names given as 'X (Y)', or the name less a word like Marshes or Downs."""
    n = simple(name)
    bits = 0
    for p in phrases:
        if p['size'] < min_size:
            continue
        hit = n in p['parts'] or n == p['t']
        if not hit:
            for t in p['parts']:
                if len(t) >= 4 and n.startswith(t + ' ') and all(w in GENERIC for w in n[len(t):].split()):
                    hit = True
        if hit and g.distance(Point(p['x'], p['y'])) < near:
            bits |= p['bit']
    return bits


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

    obst, phrases = lettering(base)
    wet = unary_union([R['prov'][p] for p in prov_ids if defs.PROV[p]['realm'] in defs.WATER])

    def water(g):
        return g.representative_point().within(wet)

    def unit(name, g, min_size=0, **kw):
        cands = label_cands(g)
        u = dict(n=name, **kw, l=cands[0])
        if len(cands) > 1:
            u['c'] = [v for c in cands[1:] for v in c]
        # a lake's name is often set beside it rather than on it
        x = dup_bits(name, g, phrases, min_size, near=45 if kw.get('w') or water(g) else 25)
        if x:
            u['x'] = x
        return u

    # a realm's name in big letters is not doubled by a small town of the same name
    realms = [unit(defs.REALMS[r], realm_geo[r], min_size=14, w=int(r in defs.WATER), id=r) for r in realm_ids]
    provinces = [unit(defs.PROV[p]['name'], R['prov'][p], r=r_index[defs.PROV[p]['realm']], id=p) for p in prov_ids]
    districts = [unit(d['name'], d['poly'], p=p_index[d['province']]) for d in D]
    log('labels', '%.1fs' % (time.time() - t), 'named by the map:',
        {lv: sum(1 for u in us if u.get('x')) for lv, us in (('realm', realms), ('province', provinces), ('district', districts))})

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
        edges=edges, adj=adj, places=places, obst={str(k): v for k, v in obst.items()},
        frame=[57.2773, 49.542, 2402.276, 1689.0293],
        base=base['layers'], glyphs=base['glyphs'], labels=base['labels'],
    )
    # maps saved with an earlier build of the regions (see migrate.py)
    mig = os.path.join(CACHE, 'migrate.json')
    if os.path.exists(mig):
        ms = [m for m in json.load(open(mig)) if len(m['map']) == len(cells)]
        if ms:
            data['migrate'] = ms
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    js = 'window.ME_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n'
    with open(OUT, 'w') as f:
        f.write(js)
    log('wrote', OUT, '%.1f MB' % (len(js.encode()) / 1e6), '%.1fs' % (time.time() - t))


def log(*a):
    print(*a, flush=True)


if __name__ == '__main__':
    main()
