# Joint fit of the hall model (model6: model4 + corner parameter cb) and all cameras.
# python3 joint7.py [photos] [tag]  -- default: all six photos, writes fit.json and fit_sd.json (1-sigma)
import numpy as np, json, sys, time
from scipy.optimize import least_squares
from model6 import SPEC, feat
import cam2
from cam2 import project2, center2
SIZE = {'U1': (2048, 1366), 'U3': (2048, 1366), 'A': (1600, 1157), 'U2': (2048, 1366), 'P1': (2048, 1365), 'N26': (1379, 919)}
NM = [s[0] for s in SPEC]; LOq = np.array([s[2] for s in SPEC]); HIq = np.array([s[3] for s in SPEC])
LO = cam2.LO.copy(); HI = cam2.HI.copy(); LO[9:11] = -1500; HI[9:11] = 1500
# A is cropped from a standard frame: its image centre can only have moved by the amount cut away
PP_LIMIT = {'A': (70.0, 25.0)}
FULL_LENS = ['A', 'P1', 'N26']
OBS_FILES = ['obs.json', 'obs_A.json', 'obs_U2.json', 'obs_extraB.json', 'obs_P1.json', 'obs_N26.json']
def load_obs(): return sum((json.load(open(f)) for f in OBS_FILES), [])
def init():
    fit = json.load(open('fit.json')); q0 = np.array([fit['params'].get(n, 0.0) for n in NM])
    cams = {p: np.array(c) for p, c in fit['cameras'].items()}
    # A is a crop (1600x1157, not 3:2), so like P1 and N26 it gets the full lens model with a free image centre
    for p in FULL_LENS: cams[p] = np.concatenate([cams[p], np.zeros(11 - len(cams[p]))]) if len(cams[p]) < 11 else cams[p]
    return q0, cams
class Joint:
    def __init__(s, PH, cams):
        s.PH = PH; s.sz = [len(cams[p]) for p in PH]
        s.lo = np.concatenate([LOq] + [LO[:n] for n in s.sz]); s.hi = np.concatenate([HIq] + [HI[:n] for n in s.sz])
        o = len(NM)
        for p, n in zip(PH, s.sz):
            if p in PP_LIMIT and n == 11: s.lo[o+9], s.hi[o+9] = -PP_LIMIT[p][0], PP_LIMIT[p][0]; s.lo[o+10], s.hi[o+10] = -PP_LIMIT[p][1], PP_LIMIT[p][1]
            o += n
    def pack(s, q0, cams): return np.concatenate([q0] + [cams[p] for p in s.PH])
    def unpack(s, v):
        q = dict(zip(NM, v[:len(NM)])); c = {}; o = len(NM)
        for p, n in zip(s.PH, s.sz): c[p] = v[o:o+n]; o += n
        return q, c
    def resid(s, v, obs):
        q, c = s.unpack(v); out = []
        for p in s.PH:
            ob = [x for x in obs if x['photo'] == p]
            if not ob: continue
            X = np.array([feat(x['el'], x['idx'], q, x['kind']) for x in ob]); uv, zc = project2(X, c[p], *SIZE[p])
            d = (uv - np.array([[x['u'], x['v']] for x in ob]))*(2048/SIZE[p][0]); d[zc <= 0.3] += 1000; out.append(d.ravel())
        return np.concatenate(out)
    def fit(s, v0, obs, nfev=20000):
        return least_squares(lambda v: s.resid(v, obs), np.clip(v0, s.lo, s.hi), bounds=(s.lo, s.hi), loss='soft_l1', f_scale=5, max_nfev=nfev, x_scale='jac')
def per_photo(J, v, obs):
    e = np.linalg.norm(J.resid(v, obs).reshape(-1, 2), axis=1); out = {}; i = 0
    for p in J.PH:
        n = sum(1 for x in obs if x['photo'] == p); out[p] = e[i:i+n]; i += n
    return e, out
if __name__ == '__main__':
    PH = sys.argv[1].split(',') if len(sys.argv) > 1 else ['U1', 'U3', 'A', 'U2', 'P1', 'N26']
    tag = sys.argv[2] if len(sys.argv) > 2 else 'fit'
    q0, cams = init(); J = Joint(PH, cams); obs = [o for o in load_obs() if o['photo'] in PH]
    t = time.time(); s = J.fit(J.pack(q0, cams), obs); v = s.x
    e, pp = per_photo(J, v, obs)
    print(f'{tag}: n {len(e)} median {np.median(e):.2f} rms {np.sqrt(np.mean(e**2)):.2f} ({time.time()-t:.0f}s)', {p: round(float(np.median(x)), 2) for p, x in pp.items()})
    q, c = J.unpack(v); print('cb = %.3f' % q['cb'])
    # 1-sigma from the Jacobian
    Jm = s.jac; r = s.fun; dof = max(1, len(r) - len(v)); s2 = float(r @ r)/dof
    try:
        cov = np.linalg.pinv(Jm.T @ Jm)*s2; sd = np.sqrt(np.diag(cov))[:len(NM)]
        print('cb sd %.3f' % sd[NM.index('cb')])
        json.dump(dict(zip(NM, map(float, sd))), open(f'{tag}_sd.json', 'w'))
    except Exception as ex: print('no cov', ex)
    fmt = '[rvec(3), tvec(3), f, k1] or [rvec(3), tvec(3), f, k1, k2, cx_offset, cy_offset]'
    json.dump({'params': {k: float(x) for k, x in q.items()}, 'cameras': {p: list(map(float, c[p])) for p in PH}, 'camera_format': fmt}, open(f'{tag}.json', 'w'), indent=1)
