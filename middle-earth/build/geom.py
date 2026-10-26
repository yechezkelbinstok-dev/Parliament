"""Geometry helpers for building the region map: wiggly borders, splitting, merging."""
import hashlib, math, random

import shapely
from shapely.geometry import LineString, MultiLineString, MultiPoint, Point, Polygon, MultiPolygon, GeometryCollection
from shapely.ops import linemerge, polygonize, unary_union, substring


def polys(g):
    """Iterate the polygons in any geometry."""
    if g is None or g.is_empty:
        return []
    if g.geom_type == 'Polygon':
        return [g]
    if hasattr(g, 'geoms'):
        out = []
        for x in g.geoms:
            out += polys(x)
        return out
    return []


def lines(g):
    if g is None or g.is_empty:
        return []
    if g.geom_type in ('LineString', 'LinearRing'):
        return [LineString(g.coords)]
    if g.geom_type == 'Polygon':
        return [LineString(g.exterior.coords)] + [LineString(h.coords) for h in g.interiors]
    if hasattr(g, 'geoms'):
        out = []
        for x in g.geoms:
            out += lines(x)
        return out
    return []


def _rng(a, b, salt=''):
    key = sorted([(round(a[0], 1), round(a[1], 1)), (round(b[0], 1), round(b[1], 1))])
    h = hashlib.md5((repr(key) + salt).encode()).hexdigest()
    return random.Random(int(h[:12], 16))


def wiggle(coords, frac=0.09, amax=7.0, seg=2.0, salt=''):
    """Midpoint displacement along a polyline; endpoints stay put. Same result in either direction."""
    coords = [tuple(c) for c in coords]
    if len(coords) < 2:
        return coords
    flip = coords[0] > coords[-1]
    if flip:
        coords = coords[::-1]
    rnd = _rng(coords[0], coords[-1], salt)
    out = [coords[0]]

    def rec(a, b, depth):
        L = math.dist(a, b)
        if L < seg or depth > 12:
            out.append(b)
            return
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        d = rnd.uniform(-1, 1) * min(amax, frac * L) * (0.75 ** depth)
        m = ((a[0] + b[0]) / 2 + nx * d, (a[1] + b[1]) / 2 + ny * d)
        rec(a, m, depth + 1)
        rec(m, b, depth + 1)

    for a, b in zip(coords, coords[1:]):
        rec(a, b, 0)
    return out[::-1] if flip else out


def chaikin(coords, n=3):
    pts = [tuple(c) for c in coords]
    for _ in range(n):
        if len(pts) < 3:
            break
        new = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            new.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            new.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        new.append(pts[-1])
        pts = new
    return pts


def extend(coords, d=1.5):
    """Push both ends outward a little so they cross whatever they were meant to meet."""
    c = [tuple(x) for x in coords]
    if len(c) < 2:
        return c
    def ext(p, q):
        L = math.dist(p, q) or 1
        return (p[0] + (p[0] - q[0]) / L * d, p[1] + (p[1] - q[1]) / L * d)
    return [ext(c[0], c[1])] + c + [ext(c[-1], c[-2])]


def snap_ends(coords, target, tol=14.0, over=1.5):
    """Move each end onto the nearest point of target (if within tol), then overshoot slightly."""
    c = [tuple(x) for x in coords]
    for end in (0, -1):
        p = Point(c[end])
        if target is None or target.is_empty:
            continue
        dd = target.distance(p)
        if dd <= tol:
            q = shapely.ops.nearest_points(target, p)[0]
            prev = c[1] if end == 0 else c[-2]
            L = math.dist((q.x, q.y), prev) or 1
            qq = (q.x + (q.x - prev[0]) / L * over, q.y + (q.y - prev[1]) / L * over)
            if end == 0:
                c = [qq, (q.x, q.y)] + c[1:]
            else:
                c = c[:-1] + [(q.x, q.y), qq]
    return c


def catmull(pts, step=2.0):
    """Centripetal Catmull-Rom curve through the points, sampled about every `step`."""
    P = [tuple(map(float, p)) for p in pts]
    if len(P) < 3:
        return P
    P = [(2 * P[0][0] - P[1][0], 2 * P[0][1] - P[1][1])] + P + [(2 * P[-1][0] - P[-2][0], 2 * P[-1][1] - P[-2][1])]
    out = [P[1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        def tj(ti, a, b):
            return ti + max(math.dist(a, b), 1e-6) ** 0.5
        t0 = 0.0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        n = max(2, int(math.dist(p1, p2) / step))
        for k in range(1, n + 1):
            t = t1 + (t2 - t1) * k / n
            def lerp(a, b, ta, tb):
                w = (t - ta) / (tb - ta)
                return (a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w)
            a1 = lerp(p0, p1, t0, t1); a2 = lerp(p1, p2, t1, t2); a3 = lerp(p2, p3, t2, t3)
            b1 = lerp(a1, a2, t0, t2); b2 = lerp(a2, a3, t1, t3)
            out.append(lerp(b1, b2, t1, t2))
    return out


def snap_end(c, end, target, tol, over=1.5):
    """Bring one end of a polyline onto target if it is within tol, then run on past it a little."""
    c = [tuple(x) for x in c]
    p = Point(c[end])
    if target is None or target.is_empty or target.distance(p) > tol:
        return c
    q = shapely.ops.nearest_points(target, p)[0]
    prev = c[1] if end == 0 else c[-2]
    L = math.dist((q.x, q.y), prev) or 1
    qq = (q.x + (q.x - prev[0]) / L * over, q.y + (q.y - prev[1]) / L * over)
    if end == 0:
        return [qq, (q.x, q.y)] + (c[1:] if p.distance(q) > 1e-9 else c[1:])
    return c[:-1] + [(q.x, q.y), qq]


def faces_of(linework, within=None, min_area=0.0):
    fs = list(polygonize(unary_union(linework)))
    if within is not None:
        fs = [f for f in fs if within.contains(f.representative_point())]
    return [f for f in fs if f.area > min_area]


def merge_small(faces, keys, min_area, protect=None):
    """Merge faces smaller than min_area (or without key) into the neighbour sharing most border.
    Returns (faces, keys)."""
    import numpy as np
    faces = list(faces); keys = list(keys)
    n = len(faces)
    alive = np.ones(n, bool)
    B = np.array([f.bounds for f in faces]) if n else np.zeros((0, 4))
    def needs(i):
        return keys[i] is None or (faces[i].area < min_area and not (protect and protect(keys[i])))
    todo = sorted([i for i in range(n) if needs(i)], key=lambda i: faces[i].area)
    while todo:
        i = todo.pop(0)
        if not alive[i] or not needs(i):
            continue
        f = faces[i]
        b = B[i]
        cand = np.where(alive & (B[:, 0] <= b[2] + 0.1) & (B[:, 2] >= b[0] - 0.1) &
                        (B[:, 1] <= b[3] + 0.1) & (B[:, 3] >= b[1] - 0.1))[0]
        best, bl = None, 0.0
        fb = f.boundary
        for j in cand:
            if j == i:
                continue
            inter = fb.intersection(faces[j].buffer(0.05))
            L = 0 if inter.is_empty else inter.length
            if L > bl:
                bl, best = L, j
        if best is None:
            continue
        faces[best] = unary_union([faces[best], f]).buffer(0)
        B[best] = faces[best].bounds
        if keys[best] is None:
            keys[best] = keys[i]
        alive[i] = False
        if needs(best):
            todo.append(best)
            todo.sort(key=lambda k: faces[k].area)
    out = [(faces[i], keys[i]) for i in range(n) if alive[i]]
    return [f for f, _ in out], [k for _, k in out]


def voronoi_split(face, seeds, keys, frac=0.09, amax=7.0, salt='', wig=True):
    """Split polygon `face` among seed points; cells with the same key are joined.
    Returns dict key -> polygon (pieces), with wiggled borders between different keys."""
    if len(set(keys)) == 1:
        return {keys[0]: face}
    env = face.envelope.buffer(max(face.bounds[2] - face.bounds[0], face.bounds[3] - face.bounds[1]))
    vor = shapely.voronoi_polygons(MultiPoint(seeds), extend_to=env)
    cells = list(vor.geoms)
    owner = {}
    for c in cells:
        for i, s in enumerate(seeds):
            if c.contains(Point(s)) or c.distance(Point(s)) < 1e-9:
                owner[id(c)] = keys[i]
                break
    pieces = {}
    for c in cells:
        k = owner.get(id(c))
        if k is None:
            continue
        pieces.setdefault(k, []).append(c)
    pieces = {k: unary_union(v).intersection(face) for k, v in pieces.items()}
    if not wig:
        return pieces
    # internal borders between different keys
    inner = unary_union([p.boundary for p in pieces.values()])
    inner = inner.difference(face.boundary.buffer(0.01))
    merged = linemerge(lines(inner)) if not inner.is_empty else None
    work = [face.boundary]
    for ln in lines(merged):
        cs = list(ln.coords)
        if len(cs) < 2:
            continue
        w = wiggle(cs, frac=frac, amax=amax, salt=salt)
        # overshoot ends that sit on the face boundary so polygonize nodes them
        work.append(LineString(extend(w, 0.8)))
    sub = faces_of(work, within=face)
    out = {}
    for s in sub:
        best, ba = None, 0
        for k, p in pieces.items():
            a = s.intersection(p).area
            if a > ba:
                ba, best = a, k
        if best is not None:
            out.setdefault(best, []).append(s)
    return {k: unary_union(v) for k, v in out.items()}


def kmeans_points(poly, k, iters=40, seed=0, fixed=()):
    """Lloyd relaxation of k free points inside a polygon (sampled on a grid).
    `fixed` centres take part but never move; they come first in the result."""
    import numpy as np
    fixed = [tuple(p) for p in fixed]
    if k <= 0:
        return fixed
    minx, miny, maxx, maxy = poly.bounds
    step = math.sqrt(poly.area / max(500, 80 * (k + len(fixed))))
    xs = np.arange(minx + step / 2, maxx, step)
    ys = np.arange(miny + step / 2, maxy, step)
    X, Y = np.meshgrid(xs, ys)
    X, Y = X.ravel(), Y.ravel()
    inside = shapely.contains_xy(poly, X, Y)
    P = np.column_stack([X[inside], Y[inside]])
    if len(P) < k + len(fixed):
        rp = poly.representative_point()
        return fixed + [(rp.x, rp.y)] * k
    rnd = np.random.default_rng(seed)
    nf = len(fixed)
    if nf:
        cen = [np.array(p, float) for p in fixed]
        d2 = np.min([((P - c) ** 2).sum(1) for c in cen], axis=0)
    else:
        cen = [P[rnd.integers(len(P))]]
        d2 = ((P - cen[0]) ** 2).sum(1)
    while len(cen) < k + nf:
        j = int(np.argmax(d2))
        cen.append(P[j])
        d2 = np.minimum(d2, ((P - P[j]) ** 2).sum(1))
    C = np.array(cen, dtype=float)
    for _ in range(iters):
        D = ((P[:, None, :] - C[None, :, :]) ** 2).sum(2)
        lab = D.argmin(1)
        newC = C.copy()
        for i in range(nf, len(C)):
            m = lab == i
            if m.any():
                newC[i] = P[m].mean(0)
        moved = np.abs(newC - C).max()
        C = newC
        if moved < 0.05:
            break
    return fixed + [tuple(c) for c in C[nf:]]
