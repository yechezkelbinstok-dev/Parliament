# Left/right test: fit the two sides with separate parameters and compare them.
import numpy as np, json
from scipy.optimize import least_squares
import model6s as M
from cam2 import project2
from joint7 import SIZE, LO, HI, PP_LIMIT, load_obs
fit = json.load(open('fit.json')); q7 = fit['params']; PH = list(fit['cameras']); cams = {p: np.array(fit['cameras'][p]) for p in PH}
obs = [o for o in load_obs() if o['photo'] in PH]
NM = [s[0] for s in M.SPEC]; lo = np.array([s[2] for s in M.SPEC]); hi = np.array([s[3] for s in M.SPEC])
x0 = np.array([q7[n] if n in q7 else q7[n[:-1]] for n in NM]); sz = [len(cams[p]) for p in PH]
L = np.concatenate([lo] + [LO[:n] for n in sz]); Hh = np.concatenate([hi] + [HI[:n] for n in sz])
o = len(NM)
for p, n in zip(PH, sz):
    if p in PP_LIMIT and n == 11: L[o+9], Hh[o+9] = -PP_LIMIT[p][0], PP_LIMIT[p][0]; L[o+10], Hh[o+10] = -PP_LIMIT[p][1], PP_LIMIT[p][1]
    o += n
def unpack(v):
    q = dict(zip(NM, v[:len(NM)])); c = {}; k = len(NM)
    for p, n in zip(PH, sz): c[p] = v[k:k+n]; k += n
    return q, c
def resid(v):
    q, c = unpack(v); out = []
    for p in PH:
        ob = [x for x in obs if x['photo'] == p]
        X = np.array([M.feat(x['el'], x['idx'], q, x['kind']) for x in ob]); uv, zc = project2(X, c[p], *SIZE[p])
        d = (uv - np.array([[x['u'], x['v']] for x in ob]))*(2048/SIZE[p][0]); d[zc <= 0.3] += 1000; out.append(d.ravel())
    return np.concatenate(out)
v0 = np.concatenate([x0] + [cams[p] for p in PH])
s = least_squares(resid, np.clip(v0, L, Hh), bounds=(L, Hh), loss='soft_l1', f_scale=5, max_nfev=20000, x_scale='jac')
q, _ = unpack(s.x); e = np.linalg.norm(resid(s.x).reshape(-1, 2), axis=1)
print('asymmetric fit median px', round(float(np.median(e)), 2))
for k in ['g2'] + [f'aK{k}' for k in range(1, 5)] + [f'xV{k}' for k in range(1, 5)] + [f'yV{k}' for k in range(1, 5)]:
    a, b = q[k+'L'], q[k+'R']; ang = k[:2] in ('g2', 'aK'); f = np.degrees if ang else (lambda x: x)
    print(f'{k:4s} left {f(a):7.2f}  right {f(b):7.2f}  diff {f(a-b):+6.2f}{" deg" if ang else " seat widths"}')
S = lambda el, i: M._seg(el, i, q)[0]
mm = [np.linalg.norm(S(el, i) - np.array([-S(er, i)[0], S(er, i)[1]])) for el, er in [('L1', 'R1'), ('L2', 'R2'), ('L3', 'R3'), ('L4', 'R4'), ('GL', 'GR')] for i in range(M.COUNTS[el])]
print('left vs mirrored right, all side-row and table seats: median %.3f, 90%% %.3f, max %.3f seat widths' % (np.median(mm), np.percentile(mm, 90), np.max(mm)))
