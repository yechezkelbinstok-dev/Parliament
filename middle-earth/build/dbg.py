"""Debug crops: python dbg.py x0 y0 x1 y1 out.png [grid] [maxpx] [layers]
layers: comma list of feat (rivers/forests/ranges ids), regions (latest build), labels"""
import sys, pickle, json, os
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
C = os.path.join(HERE, '.cache')

def rings(g):
    for p in getattr(g, 'geoms', [g]):
        if p.geom_type == 'Polygon':
            yield list(p.exterior.coords)
            for h in p.interiors: yield list(h.coords)
        elif p.geom_type in ('LineString', 'LinearRing'):
            yield list(p.coords)
        elif hasattr(p, 'geoms'):
            yield from rings(p)

def main(x0, y0, x1, y1, out, grid=25, maxpx=1600, layers='feat'):
    im = Image.open(os.path.join(C, 'ref4x.png')).convert('RGB')
    S = im.width / 2448
    c = im.crop((int(x0 * S), int(y0 * S), int(x1 * S), int(y1 * S)))
    k = min(1.0, maxpx / max(c.width, c.height))
    c = c.resize((int(c.width * k), int(c.height * k)), Image.LANCZOS)
    sc = S * k
    T = lambda x, y: ((x - x0) * sc, (y - y0) * sc)
    dr = ImageDraw.Draw(c, 'RGBA')
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 13)
    fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 11)
    L = layers.split(',')
    if 'feat' in L:
        F = pickle.load(open(os.path.join(C, 'features.pkl'), 'rb'))
        R = F['ranges']
        for i, g in enumerate(F['forest']):
            for r in rings(g): dr.line([T(*q) for q in r], fill=(0, 150, 0, 200), width=2)
            p = g.representative_point(); dr.text(T(p.x, p.y), 'F%d' % i, fill=(0, 100, 0, 255), font=f)
        for i, g in enumerate(R):
            for r in rings(g): dr.line([T(*q) for q in r], fill=(160, 70, 0, 220), width=2)
            p = g.representative_point(); dr.text(T(p.x, p.y), 'M%d' % i, fill=(130, 40, 0, 255), font=f)
        for (i, kk), r in F['rivers'].items():
            dr.line([T(*q) for q in r['line'].coords], fill=(230, 0, 0, 160), width=2)
            for t in (0.25, 0.75):
                m = r['line'].interpolate(t, normalized=True)
                if x0 <= m.x <= x1 and y0 <= m.y <= y1:
                    dr.text(T(m.x, m.y), '%d' % i, fill=(200, 0, 0, 255), font=f)
    if 'regions' in L and os.path.exists(os.path.join(C, 'dbg_regions.pkl')):
        D = pickle.load(open(os.path.join(C, 'dbg_regions.pkl'), 'rb'))
        for lvl, col, w in (('district', (40, 40, 200, 150), 1), ('province', (0, 0, 0, 230), 2), ('realm', (200, 0, 120, 255), 4)):
            for ln in D.get(lvl + '_edges', []):
                for r in rings(ln): dr.line([T(*q) for q in r], fill=col, width=w)
        for lvl, fnt, col in (('province', f, (0, 0, 0, 255)), ('district', fs, (30, 30, 160, 255))):
            if lvl + '_labels' not in D or (lvl == 'district' and 'dnames' not in L): continue
            for (x, y, name) in D[lvl + '_labels']:
                if x0 <= x <= x1 and y0 <= y <= y1:
                    X, Y = T(x, y); w = dr.textlength(name, font=fnt)
                    dr.rectangle([X - w / 2 - 2, Y - 8, X + w / 2 + 2, Y + 7], fill=(255, 255, 255, 170))
                    dr.text((X - w / 2, Y - 7), name, fill=col, font=fnt)
        for (x, y, name) in D.get('seeds', []):
            if 'seeds' in L and x0 <= x <= x1 and y0 <= y <= y1:
                X, Y = T(x, y); dr.ellipse([X - 3, Y - 3, X + 3, Y + 3], fill=(255, 0, 0, 255))
    if grid:
        g = grid
        gx = (int(x0 // g) + 1) * g
        while gx < x1:
            X = (gx - x0) * sc; dr.line([(X, 0), (X, c.height)], fill=(255, 0, 180, 70), width=1)
            dr.text((X + 2, 2), str(int(gx)), fill=(190, 0, 130, 255), font=fs); gx += g
        gy = (int(y0 // g) + 1) * g
        while gy < y1:
            Y = (gy - y0) * sc; dr.line([(0, Y), (c.width, Y)], fill=(255, 0, 180, 70), width=1)
            dr.text((2, Y + 2), str(int(gy)), fill=(190, 0, 130, 255), font=fs); gy += g
    c.save(out)

if __name__ == '__main__':
    a = sys.argv
    main(*map(float, a[1:5]), a[5], *(float(v) for v in a[6:8]), *a[8:9])
