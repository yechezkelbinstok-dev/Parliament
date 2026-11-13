# Leave one photo out: refit without it and measure how far each map dot moves.
import json, numpy as np
from joint7 import Joint, init, load_obs, NM
from model6 import _seg, COUNTS
OFF = 0.8
def dots(q):
    out = {}
    for el, n in COUNTS.items():
        for i in range(n):
            p, nrm, z = _seg(el, i, q); out[(el, i)] = p + OFF*nrm
    return out
q0, cams = init(); allobs = load_obs()
full = json.load(open('fit.json'))['params']; D0 = dots(full)
for p in ['U1', 'U3', 'A', 'U2', 'P1', 'N26']:
    PH = [x for x in ['U1', 'U3', 'A', 'U2', 'P1', 'N26'] if x != p]
    J = Joint(PH, cams); obs = [o for o in allobs if o['photo'] in PH]
    v = J.fit(J.pack(q0, cams), obs).x; q, _ = J.unpack(v); D = dots(q)
    mv = np.array([np.linalg.norm(D[k] - D0[k]) for k in D0])
    print(f'without {p:3s}: median move {np.median(mv):.3f}  max {mv.max():.3f}  cb {q["cb"]:.3f}')
