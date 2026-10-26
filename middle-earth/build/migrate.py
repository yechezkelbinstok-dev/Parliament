"""Let maps saved with an earlier build of the regions open in this one.

python migrate.py old.html [older.html ...]     (earlier dist/middle-earth-map-painter.html files)

Writes .cache/migrate.json: for each earlier build, and every cell of the current build, the cell of the
old build under it. export.py ships the tables, and the app uses them to carry an old map's colours over.
"""
import json, os, pickle, re, sys

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '.cache')
NUM = re.compile(r'-?\d+(?:\.\d+)?')


def rings(path):
    """Rings of one encoded cell: absolute start, then relative steps."""
    out = []
    for part in path.split('z'):
        if not part.startswith('M') or 'l' not in part:
            continue
        head, steps = part[1:].split('l', 1)
        x, y = map(float, NUM.findall(head))
        pts = [(x, y)]
        v = list(map(float, NUM.findall(steps)))
        for dx, dy in zip(v[0::2], v[1::2]):
            x += dx; y += dy
            pts.append((x, y))
        if len(pts) >= 3:
            out.append(Polygon(pts).buffer(0))
    return out


def table(old_html, R):
    html = open(old_html, encoding='utf8').read()
    i = html.index('window.ME_DATA=') + len('window.ME_DATA=')
    j = html.index(';\n', i)
    old = json.loads(html[i:j])
    paths = old['cells']['path']
    geoms, owner = [], []
    for k, p in enumerate(paths):
        for r in rings(p):
            geoms.append(r); owner.append(k)
    tree = STRtree(geoms)
    owner = np.array(owner)
    pts = [c['poly'].representative_point() for c in R['cells']]
    out = []
    for p in pts:
        hits = tree.query(p, predicate='within')
        # a cell drawn with holes counts by the even-odd rule, as the browser fills it
        cnt = {}
        for h in hits:
            cnt[owner[h]] = cnt.get(owner[h], 0) + 1
        inside = [k for k, n in cnt.items() if n % 2]
        if inside:
            out.append(int(inside[0]))
        else:
            out.append(int(owner[tree.nearest(p)]))
    print(old_html, 'old cells', len(paths), 'new cells', len(out), 'mapped by containment',
          sum(1 for p in pts if len(tree.query(p, predicate='within'))), 'of', len(pts))
    return {'n': len(paths), 'map': out}


def main(files):
    R = pickle.load(open(os.path.join(CACHE, 'regions.pkl'), 'rb'))
    tables = {}
    for f in files:
        t = table(f, R)
        if t['n'] != len(R['cells']):
            tables[t['n']] = t
    json.dump(list(tables.values()), open(os.path.join(CACHE, 'migrate.json'), 'w'))


if __name__ == '__main__':
    main(sys.argv[1:])
