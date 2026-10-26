"""Audit pictures: every unit of one level filled with its own colour over the original map.

python audit.py LEVEL x0 y0 x1 y1 out.png [maxpx] [names]
LEVEL is realm, province, district or cell. 'names' adds unit names.
"""
import colorsys, os, pickle, sys
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont
from shapely.ops import unary_union, polylabel

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import defs
from geom import polys

Image.MAX_IMAGE_PIXELS = None
C = os.path.join(HERE, '.cache')


def units(level, R):
    if level == 'province':
        return {pid: (defs.PROV[pid]['name'], g) for pid, g in R['prov'].items()}
    if level == 'realm':
        acc = defaultdict(list)
        for pid, g in R['prov'].items():
            acc[defs.PROV[pid]['realm']].append(g)
        return {rid: (defs.REALMS[rid], unary_union(v)) for rid, v in acc.items()}
    if level == 'district':
        return {d['id']: (d['name'], d['poly']) for d in R['districts']}
    return {c['id']: (str(c['id']), c['poly']) for c in R['cells']}


def colours(us):
    """Greedy colouring so touching units differ; hues spread over a golden-angle sequence."""
    keys = list(us)
    geoms = [us[k][1].buffer(0.3) for k in keys]
    from shapely.strtree import STRtree
    tree = STRtree(geoms)
    col = {}
    pal = [colorsys.hsv_to_rgb((i * 0.618034) % 1, 0.55 + 0.25 * (i % 2), 0.95) for i in range(14)]
    for i in sorted(range(len(keys)), key=lambda i: -geoms[i].area):
        taken = {col.get(keys[j]) for j in tree.query(geoms[i], predicate='intersects') if j != i}
        for k in range(len(pal)):
            if k not in taken:
                col[keys[i]] = k
                break
        else:
            col[keys[i]] = i % len(pal)
    return {k: tuple(int(255 * v) for v in pal[c]) for k, c in col.items()}


def main(level, x0, y0, x1, y1, out, maxpx=1600, names=False):
    R = pickle.load(open(os.path.join(C, 'regions.pkl'), 'rb'))
    us = units(level, R)
    im = Image.open(os.path.join(C, 'ref4x.png')).convert('RGB')
    S = im.width / 2448
    crop = im.crop((int(x0 * S), int(y0 * S), int(x1 * S), int(y1 * S)))
    k = min(1.0, maxpx / max(crop.width, crop.height))
    crop = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS).convert('RGBA')
    sc = S * k
    T = lambda x, y: ((x - x0) * sc, (y - y0) * sc)
    layer = Image.new('RGBA', crop.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(layer)
    cols = colours(us)
    from shapely.geometry import box
    view = box(x0, y0, x1, y1)
    vis = {kk: v for kk, v in us.items() if v[1].intersects(view)}
    for kk, (nm, g) in vis.items():
        for p in polys(g):
            dr.polygon([T(*q) for q in p.exterior.coords], fill=cols[kk] + (120,))
            for hole in p.interiors:
                dr.polygon([T(*q) for q in hole.coords], fill=(0, 0, 0, 0))
    out_im = Image.alpha_composite(crop, layer)
    dr = ImageDraw.Draw(out_im)
    for kk, (nm, g) in vis.items():
        for p in polys(g):
            dr.line([T(*q) for q in p.exterior.coords], fill=(20, 20, 20, 255), width=1)
    if names:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 12 if level != 'realm' else 15)
        for kk, (nm, g) in vis.items():
            for j, p in enumerate(sorted(polys(g), key=lambda p: -p.area)):
                if j > 0 and p.area < 200:
                    continue
                c = polylabel(p, tolerance=0.5)
                if not view.contains(c):
                    continue
                X, Y = T(c.x, c.y)
                label = nm if j == 0 else nm + ' *'
                w = dr.textlength(label, font=f)
                dr.rectangle([X - w / 2 - 2, Y - 8, X + w / 2 + 2, Y + 8], fill=(255, 255, 255, 200))
                dr.text((X - w / 2, Y - 7), label, fill=(0, 0, 0, 255), font=f)
    out_im.convert('RGB').save(out)


if __name__ == '__main__':
    a = sys.argv
    main(a[1], *map(float, a[2:6]), a[6], int(a[7]) if len(a) > 7 and a[7].isdigit() else 1600, 'names' in a)
