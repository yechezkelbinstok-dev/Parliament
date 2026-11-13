# model4 plus one shared parameter 'cb': the two seats either side of each side-row bend
# sit cb seat widths closer to the bend than the regular pitch puts them (wedge-shaped corner desks).
import numpy as np
import model4
from model4 import COUNTS, NF, SIDES, project, cam_center
from model3 import SPEC as SPEC4
SPEC = SPEC4 + [('cb', 0.0, -0.4, 0.4)]
def _seg(el, idx, q):
    p, n, z = model4._seg(el, idx, q)
    if el[0] in 'LR' and q.get('cb', 0.0):
        k = int(el[1]); nF = NF[k]; s = SIDES[el[0]]
        if idx == nF - 1:   # last seat of the front part: move toward the bend along the front direction
            eF = np.array([s*np.sin(q[f'aF{k}']), -np.cos(q[f'aF{k}'])]); p = p - q['cb']*eF
        elif idx == nF:     # first seat of the back part: move toward the bend along the back direction
            eK = np.array([-s*np.sin(q[f'aK{k}']), np.cos(q[f'aK{k}'])]); p = p - q['cb']*eK
    return p, n, z
def feat(el, idx, q, kind='np'):
    p, n, z = _seg(el, idx, q)
    if kind == 'mon': p = p + q['dm']*n; z = z + q['hm']
    return np.array([p[0], p[1], z])
def visible_kind(el, idx, q, C):
    p, n, z = _seg(el, idx, q)
    return 'mon' if np.dot(C[:2]-p, n) > 0 else 'np'
