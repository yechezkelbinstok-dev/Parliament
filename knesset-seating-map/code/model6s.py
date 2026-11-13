# Asymmetric variant of model6 (left and right sides get their own parameters), for the symmetry test.
import numpy as np
import model5
from model5 import SPEC as SPEC5, COUNTS, NF, SIDES
SPEC = SPEC5 + [('cb', 0.06, -0.4, 0.4)]
def _seg(el, idx, q):
    p, n, z = model5._seg(el, idx, q)
    if el[0] in 'LR':
        sd = el[0]; k = int(el[1]); nF = NF[k]; s = SIDES[sd]
        if idx == nF - 1: p = p - q['cb']*np.array([s*np.sin(q[f'aF{k}{sd}']), -np.cos(q[f'aF{k}{sd}'])])
        elif idx == nF: p = p - q['cb']*np.array([-s*np.sin(q[f'aK{k}{sd}']), np.cos(q[f'aK{k}{sd}'])])
    return p, n, z
def feat(el, idx, q, kind='np'):
    p, n, z = _seg(el, idx, q)
    if kind == 'mon': p = p + q['dm']*n; z = z + q['hm']
    return np.array([p[0], p[1], z])
