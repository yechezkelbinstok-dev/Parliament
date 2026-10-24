"""Pull the vector layers out of the Middle-earth PDF.

Usage: python extract.py path/to/Map-of-Middle-Earth-3RD-Age.pdf

Writes into build/.cache/:
  full.svg, full_tp.svg  the page as SVG (text as text, and text as glyph paths)
  features.pkl           shapely geometry: land, sea, lakes, rivers, forest and range outlines
  labels.json            every map label with its position, grouped from single glyphs
  base.json              the original artwork split into layers, for the app
"""
import json, math, os, pickle, re, sys
import xml.etree.ElementTree as ET

import pymupdf
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from shapely import make_valid

sys.path.insert(0, os.path.dirname(__file__))
import mepdf

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '.cache')
NS = '{http://www.w3.org/2000/svg}'

# Path indices in the exported SVG (stable for this PDF).
FRAME = box(57.2773, 49.542, 2402.276, 1689.0293)
SEA_MAIN = 5
LAKES = {17: 'Nenuial', 724: 'Long Lake', 4104: 'Sea of Rhûn', 5119: 'Sea of Nurnen',
         5497: 'Sirannon Pool', 5564: 'Mirrormere'}
ISLANDS = {4467: 'Tolfalas', 5512: 'Himling'}
COAST = {6, 18, 725, 4105, 4468, 5120, 5498, 5513, 5565}
FRAME_LINES = {2}
FRAME_BLACK = 5468
ANDUIN_FILL = 4903
BLUE = ('#2fa3dc', '#27a3dc', '#5ba4d4')


def export_svg(pdf):
    os.makedirs(CACHE, exist_ok=True)
    page = pymupdf.open(pdf)[0]
    for name, tp in (('full.svg', False), ('full_tp.svg', True)):
        with open(os.path.join(CACHE, name), 'w') as f:
            f.write(page.get_svg_image(text_as_path=tp))
    # a 4x picture of the original, for dbg.py
    page.get_pixmap(matrix=pymupdf.Matrix(4, 4)).save(os.path.join(CACHE, 'ref4x.png'))


def poly(P, i):
    return unary_union([make_valid(Polygon(s)) for s, _ in P[i]['subs'] if len(s) >= 3])


def features(P):
    sea = poly(P, SEA_MAIN).intersection(FRAME)
    for i in ISLANDS:
        sea = sea.difference(poly(P, i))
    # the drawn sea stops a hair short of the frame in places: close those slivers of 'land'
    band = FRAME.difference(FRAME.buffer(-2.5))
    sea = unary_union([sea, sea.buffer(3.0).intersection(band)]).intersection(FRAME)
    sea = sea.simplify(0.1)
    lakes = {n: poly(P, i).simplify(0.1) for n, i in ((n, i) for i, n in LAKES.items())}
    water = unary_union([sea] + list(lakes.values()))
    land = FRAME.difference(water)
    rivers = {}
    for p in P:
        if p['stroke'] in BLUE and p['idx'] not in COAST | FRAME_LINES:
            for k, (s, _) in enumerate(p['subs']):
                if len(s) > 1:
                    rivers[(p['idx'], k)] = dict(line=LineString(s).simplify(0.1), w=p['sw'])
    trees, edges, mts = [], [], []
    for p in P:
        for s, _ in p['subs']:
            if len(s) < 2:
                continue
            if p['stroke'] == '#4e7559':
                if abs(p['sw'] - 0.69069) < 0.01:
                    trees.append(LineString(s).convex_hull.buffer(1.2))
                elif abs(p['sw'] - 1.38139) < 0.01:
                    edges.append(LineString(s).buffer(1.2))
            elif p['fill'] == '#d9b287' or p['stroke'] == '#d9b287':
                mts.append(LineString(s).buffer(0.8))
    forest = unary_union(trees + edges).buffer(3).buffer(-3.5).buffer(0.5)
    forest = [fill_holes(g) for g in getattr(forest, 'geoms', [forest]) if g.area > 60]
    mount = unary_union(mts)
    ranges = mount.buffer(12).buffer(-11).simplify(0.6)
    ranges = sorted((fill_holes(g) for g in getattr(ranges, 'geoms', [ranges]) if g.area > 150),
                    key=lambda g: -g.area)
    return dict(frame=FRAME, sea=sea, lakes=lakes, land=land, water=water, rivers=rivers,
                anduin_poly=poly(P, ANDUIN_FILL), forest=forest, ranges=ranges)


def fill_holes(g, keep=4000):
    """Outlines of forests and ranges: drop the small gaps between trees or peaks."""
    return Polygon(g.exterior, [h for h in g.interiors if Polygon(h).area > keep])


def glyph_extents():
    """Left and right edge (in em) of each glyph as drawn, by <text> order."""
    root = ET.parse(os.path.join(CACHE, 'full_tp.svg')).getroot()
    defs = {p.get('id'): p.get('d') for p in root.iter(NS + 'path') if p.get('id')}
    ext = {}
    out = []
    for u in root.iter(NS + 'use'):
        gid = u.get('{http://www.w3.org/1999/xlink}href')[1:]
        if gid not in ext:
            xs = [x for pts, _ in mepdf.parse_d(defs[gid]) for x, _ in pts]
            ext[gid] = (min(xs), max(xs)) if xs else (0.0, 0.3)
        out.append(ext[gid])
    return out


def labels(svgfile):
    """Group the per-glyph <text> elements into labels; keeps the glyph order index."""
    root = ET.parse(svgfile).getroot()
    EXT = glyph_extents()
    items = []
    for gi, t in enumerate(root.iter(NS + 'text')):
        a, b, c, d, e, f = mepdf.parse_matrix(t.get('transform'))
        for sp in t:
            xs = [float(v) for v in sp.get('x').split()]
            y = float(sp.get('y'))
            for k, ch in enumerate(sp.text or ''):
                x = xs[k] if k < len(xs) else xs[-1]
                items.append(dict(ch=ch, gi=gi, x=a * x + c * y + e, y=b * x + d * y + f,
                                  size=float(t.get('font-size')), ang=math.degrees(math.atan2(b, a)),
                                  dx=a, dy=b, ext=EXT[gi] if gi < len(EXT) else (0.0, 0.5)))
    groups, cur = [], None
    for it in items:
        if cur:
            prev = cur[-1]
            gap = math.hypot(it['x'] - prev['x'], it['y'] - prev['y'])
            turn = abs((it['ang'] - prev['ang'] + 180) % 360 - 180)
            # offset of this glyph from the last one's baseline: another line means another label
            off = abs(-(it['x'] - prev['x']) * prev['dy'] + (it['y'] - prev['y']) * prev['dx'])
            if abs(it['size'] - prev['size']) < 0.6 and gap < it['size'] * 1.25 and turn < 25 and off < it['size'] * 0.45:
                # blank space between the end of the last glyph and the start of this one, along the baseline
                along = (it['x'] - prev['x']) * prev['dx'] + (it['y'] - prev['y']) * prev['dy']
                blank = along - prev['ext'][1] * prev['size'] + it['ext'][0] * it['size']
                it['blank'] = blank / it['size']
                cur.append(it)
                continue
            groups.append(cur)
        cur = [it]
    groups.append(cur)
    out = []
    for g in groups:
        caps = all(not i['ch'].isalpha() or i['ch'].isupper() for i in g)
        cut = 0.6 if caps else 0.3  # capitals on the map are tracked out wide
        text = ''.join((' ' if i.get('blank', 0) > cut and i['ch'] != ' ' and g[k - 1]['ch'] != ' ' else '') + i['ch']
                       for k, i in enumerate(g))
        out.append(dict(text=' '.join(text.split()), size=round(g[0]['size'], 1),
                        x=round(sum(i['x'] for i in g) / len(g), 1), y=round(sum(i['y'] for i in g) / len(g), 1),
                        glyphs=sorted({i['gi'] for i in g})))
    return out


def classify(p):
    f, s = p.get('fill'), p.get('stroke')
    w = float(p.get('stroke-width') or 0)
    if f == '#c7eafb':
        return 'water'
    if f in ('#fff9ea', '#fffbcc'):
        return 'paper'
    if s == '#4e7559':
        return 'marsh' if abs(w - 0.25) < 0.01 else 'forest'
    if s == '#d9b287' or f == '#d9b287':
        return 'mountain'
    if s in BLUE or f == '#2fa3dc':
        return 'river'
    if s == '#939598':
        return 'road'
    return 'symbol'


NUM = re.compile(r'-?\d*\.\d+(?:e-?\d+)?')


def short(d, nd=2):
    """Round the numbers in path data."""
    def r(m):
        v = round(float(m.group(0)), nd)
        t = ('%.*f' % (nd, v)).rstrip('0').rstrip('.')
        if t in ('-0', ''):
            t = '0'
        # a minus sign doubles as the separator between numbers: keep one
        return ' ' + t if m.group(0).startswith('-') and not t.startswith('-') else t
    return NUM.sub(r, d)


STYLE = ('fill', 'fill-rule', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'stroke-dasharray')
UNORDERED = {'mountain', 'forest', 'marsh', 'water', 'coast'}  # one colour each: drawing order does not matter


def base_layers(P, labs):
    """Original artwork grouped into layers of merged paths: {layer: [{a: attrs, t: transform, d: data}]}."""
    root = ET.parse(os.path.join(CACHE, 'full_tp.svg')).getroot()
    paths = list(root.iter(NS + 'path'))
    glyph_defs = {p.get('id'): p for p in paths if p.get('id')}
    drawn = [p for p in paths if not p.get('id')]
    layers = {}
    for i, p in enumerate(drawn):
        if i in (0, 1, 2) or i in FRAME_LINES:  # clip path, paper background and frame: drawn by the app
            continue
        c = classify(p)
        if i in COAST:
            c = 'coast'
        elif i in ISLANDS:
            c = 'island'
        elif i == FRAME_BLACK:
            c = 'frame'
        elif c == 'paper':
            c = 'symbol'
        pts = [q for s_, _ in P[i]['subs'] for q in s_]
        if c == 'symbol' and pts:
            xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
            if max(xs) < 640 and min(ys) > 1000:  # compass rose and scale bar, out in the sea
                c = 'decor'
        attrs = {k: p.get(k) for k in STYLE if p.get(k) is not None}
        if attrs.get('stroke-width'):
            attrs['stroke-width'] = str(round(float(attrs['stroke-width']), 3))
        key = (tuple(sorted(attrs.items())), p.get('transform'))
        groups = layers.setdefault(c, [])
        if c in UNORDERED:
            hit = next((g for g in groups if g['key'] == key), None)
        else:
            hit = groups[-1] if groups and groups[-1]['key'] == key else None
        if hit is None:
            hit = dict(key=key, a=attrs, t=p.get('transform'), d=[])
            groups.append(hit)
        hit['d'].append(short(p.get('d')))
    out = {k: [dict(a=g['a'], t=g['t'], d=''.join(g['d'])) for g in v] for k, v in layers.items()}
    uses = list(root.iter(NS + 'use'))
    gids, glyphs = {}, []
    lab_layers = {}
    for L in labs:
        kind = label_kind(L)
        us = []
        for gi in L['glyphs']:
            u = uses[gi]
            href = u.get('{http://www.w3.org/1999/xlink}href')[1:]
            if href not in gids:
                gids[href] = len(glyphs)
                glyphs.append(short(glyph_defs[href].get('d'), 4))
            m = [round(v, 3) for v in mepdf.parse_matrix(u.get('transform'))]
            us.append([gids[href]] + m)
        fill = uses[L['glyphs'][0]].get('fill') or '#231f20'
        lab_layers.setdefault(kind, []).append(dict(text=L['text'], x=L['x'], y=L['y'], f=fill, u=us))
    return dict(layers=out, labels=lab_layers, glyphs=glyphs)


POLITICAL = {'E', 'R', 'I', 'A', 'D', 'O', 'LIN', 'N', 'ANG', 'MAR', 'RHOVANION', 'ROHAN', 'GONDOR', 'MORDOR', 'RHÛN',
             'ARNOR', 'ANGMAR', 'RHUDAUR', 'CARDOLAN', 'ARTHEDAIN'}
REGION_NAMES = {'FORLINDON', 'HARLINDON', 'MINHIRIATH', 'ENEDWAITH', 'DUNLAND', 'HOLLIN', 'ANFALAS (Langstrand)',
                'LEBENNIN', 'BELFALAS', 'LAMEDON', 'SOUTH', 'N. ITHILIEN', 'SOUTH  ITHILIEN', 'NURN', 'KHAND',
                'NEAR HARAD', 'ANDRAST (Ras Morthil)', 'TOLFALAS', 'PINNATH GELLIN', 'FORODWAITH', 'THE SHIRE',
                'LÓRIEN', 'FANGORN', 'MIRKWOOD', 'IRON HILLS', 'Westfold', 'Eastfold', 'West', 'Emnet', 'East',
                'Anórien', 'The', 'Wold', 'Brown', 'Lands', 'Bight', 'UDÛN', 'Drúwaith Iaur', 'Dorwinion',
                'Westmarch', 'Plateau of Gorgoroth', 'Dagorlad', '(Battle Plain)', 'Nindalf', '(Wetwang)',
                'Dead Marshes', 'Trollshaws', 'Ettenmoors', 'Withered Heath', 'THE MORGAI', 'Lond', 'Daer'}
DECOR = {'MIDDLE–EARTH', 'in the Third Age', 'Physical Map Design by Chris Taylor',
         'Political Designations by Chris Guerette', 'Based Upon the Works of J.R.R. Tolkien',
         '0 mi.', '50 mi.', '100 mi.', '150 mi.', '200 mi.', '250 mi.', '100 leagues'}


def label_kind(L):
    t = L['text'].replace(' ', '')
    if t in {x.replace(' ', '') for x in DECOR}:
        return 'decor'
    if L['size'] >= 48 and t in POLITICAL:
        return 'political'
    if t == 'BELFALAS' and L['size'] < 20:  # the Bay of Belfalas, not the land
        return 'place'
    if t in {x.replace(' ', '') for x in REGION_NAMES} or (t == 'GONDOR' and L['size'] < 48) or (t == 'East' and L['size'] == 14):
        return 'region'
    return 'place'


def main(pdf):
    export_svg(pdf)
    P = mepdf.load(os.path.join(CACHE, 'full.svg'), tol=0.15)
    F = features(P)
    with open(os.path.join(CACHE, 'features.pkl'), 'wb') as f:
        pickle.dump(F, f)
    labs = labels(os.path.join(CACHE, 'full.svg'))
    with open(os.path.join(CACHE, 'labels.json'), 'w') as f:
        json.dump(labs, f, ensure_ascii=False, indent=0)
    base = base_layers(P, labs)
    with open(os.path.join(CACHE, 'base.json'), 'w') as f:
        json.dump(base, f, ensure_ascii=False)
    print('land parts', len(F['land'].geoms), 'rivers', len(F['rivers']), 'forests', len(F['forest']),
          'labels', len(labs), {k: len(v) for k, v in base['layers'].items()})


if __name__ == '__main__':
    main(sys.argv[1])
