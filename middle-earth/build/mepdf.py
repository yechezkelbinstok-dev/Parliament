"""Parse the map SVG (exported from the PDF) into flattened geometry in page coordinates (y down)."""
import re, xml.etree.ElementTree as ET, math
NS = '{http://www.w3.org/2000/svg}'
TOK = re.compile(r'[MLHVCZmlhvcz]|-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')

def bez(p0, p1, p2, p3, tol=0.08):
    # adaptive flatten of a cubic; returns points after p0
    out = []
    def rec(a, b, c, d, depth):
        dx, dy = d[0]-a[0], d[1]-a[1]
        n = math.hypot(dx, dy) or 1e-9
        d1 = abs((b[0]-a[0])*dy - (b[1]-a[1])*dx)/n
        d2 = abs((c[0]-a[0])*dy - (c[1]-a[1])*dx)/n
        if depth > 12 or max(d1, d2) <= tol:
            out.append(d); return
        ab = ((a[0]+b[0])/2, (a[1]+b[1])/2); bc = ((b[0]+c[0])/2, (b[1]+c[1])/2); cd = ((c[0]+d[0])/2, (c[1]+d[1])/2)
        abc = ((ab[0]+bc[0])/2, (ab[1]+bc[1])/2); bcd = ((bc[0]+cd[0])/2, (bc[1]+cd[1])/2)
        m = ((abc[0]+bcd[0])/2, (abc[1]+bcd[1])/2)
        rec(a, ab, abc, m, depth+1); rec(m, bcd, cd, d, depth+1)
    rec(p0, p1, p2, p3, 0)
    return out

def parse_d(d, tol=0.08):
    """Returns list of (points, closed) subpaths in the path's own coordinates."""
    toks = TOK.findall(d)
    i = 0; subs = []; cur = None; pt = (0, 0); start = (0, 0); cmd = None
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t; i += 1
            if cmd in 'Zz':
                if cur is not None:
                    subs.append((cur, True)); cur = None
                pt = start
                continue
        if cmd == 'M':
            if cur is not None and len(cur) > 1: subs.append((cur, False))
            pt = (num(), num()); start = pt; cur = [pt]; cmd = 'L'
        elif cmd == 'L':
            pt = (num(), num()); cur.append(pt)
        elif cmd == 'H':
            pt = (num(), pt[1]); cur.append(pt)
        elif cmd == 'V':
            pt = (pt[0], num()); cur.append(pt)
        elif cmd == 'C':
            p1 = (num(), num()); p2 = (num(), num()); p3 = (num(), num())
            cur.extend(bez(pt, p1, p2, p3, tol)); pt = p3
        else:
            raise ValueError('cmd ' + str(cmd))
        if cur is None: cur = [pt]
    if cur is not None and len(cur) > 1: subs.append((cur, False))
    return subs

def parse_matrix(s):
    v = [float(x) for x in re.findall(r'-?[\d.]+(?:e-?\d+)?', s)]
    return v  # a b c d e f

def apply(m, pts):
    a, b, c, d, e, f = m
    return [(a*x + c*y + e, b*x + d*y + f) for x, y in pts]

def load(svgfile='full.svg', tol=0.08):
    root = ET.parse(svgfile).getroot()
    out = []
    for idx, p in enumerate(root.iter(NS + 'path')):
        m = parse_matrix(p.get('transform') or 'matrix(1,0,0,1,0,0)')
        subs = [(apply(m, pts), cl) for pts, cl in parse_d(p.get('d') or '', tol)]
        out.append(dict(idx=idx, fill=p.get('fill'), stroke=p.get('stroke'), sw=float(p.get('stroke-width') or 0),
                        dash=p.get('stroke-dasharray'), rule=p.get('fill-rule'), subs=subs, raw=p))
    return out

def texts(svgfile='full.svg'):
    root = ET.parse(svgfile).getroot()
    out = []
    for t in root.iter(NS + 'text'):
        m = parse_matrix(t.get('transform'))
        for sp in t:
            xs = [float(v) for v in sp.get('x').split()]
            y = float(sp.get('y'))
            pts = apply(m, [(xs[0], y)])
            out.append(dict(ch=sp.text, x=pts[0][0], y=pts[0][1], size=float(t.get('font-size')), m=m, weight=t.get('font-weight'),
                            fill=t.get('fill')))
    return out
