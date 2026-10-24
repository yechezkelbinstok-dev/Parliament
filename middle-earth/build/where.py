"""python where.py x0 y0 x1 y1 step  -> land/water mask; or: python where.py reps"""
import pickle, sys
from shapely.geometry import Point
F = pickle.load(open('.cache/features.pkl', 'rb'))
if sys.argv[1] == 'reps':
    for i, g in enumerate(F['ranges']):
        r = g.representative_point(); print('M%d' % i, (round(r.x), round(r.y)), [round(v) for v in g.bounds])
    for i, g in enumerate(F['forest']):
        r = g.representative_point(); print('F%d' % i, (round(r.x), round(r.y)), [round(v) for v in g.bounds])
else:
    x0, y0, x1, y1, st = map(float, sys.argv[1:6])
    land = F['land']
    print('     ' + ''.join(str(int(x0 + i * st))[-3:-2] if i % 5 == 0 else ' ' for i in range(int((x1 - x0) / st) + 1)))
    y = y0
    while y <= y1:
        x = x0; row = ''
        while x <= x1:
            row += '#' if land.contains(Point(x, y)) else '~'
            x += st
        print('%4d %s' % (y, row)); y += st
