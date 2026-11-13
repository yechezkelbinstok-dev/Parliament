"""Measure the Speaker's position from the photos, using the fitted cameras (fit.json).

    python3 speaker.py

The marks below were read off the photos (pixel coordinates in each photo as used
in the fit). No seat observation covers the Speaker, so these are kept separate.
"""
import json, numpy as np, cv2
from scipy.optimize import least_squares
from cam2 import project2, center2
from model6 import feat
from joint7 import SIZE
fit = json.load(open('fit.json'))
def proj(cam, size, X): return project2(np.atleast_2d(X), np.asarray(cam, float), *size)[0][0]
def P(p, X): return proj(fit['cameras'][p], SIZE[p], X)
def triangulate(marks, err=2.0):
    """3D point whose projections best match the marks; misfit in px and 1-sigma for `err` px marks."""
    r = lambda X: np.concatenate([(P(p, X) - uv)*2048/SIZE[p][0] for p, uv in marks.items()])
    s = least_squares(r, np.array([0.0, -10.0, 1.0]))
    sd = np.sqrt(np.diag(np.linalg.pinv(s.jac.T @ s.jac)))*err
    return s.x, np.linalg.norm(r(s.x).reshape(-1, 2), axis=1), sd
def on_plane(p, uv, x=0.0):
    """(y, z) of the point on the plane X = x that photo p shows at uv."""
    return least_squares(lambda yz: P(p, np.array([x, *yz])) - uv, np.array([-10.0, 1.5])).x

# The Knesset emblem on the front of the dais (centre of the menorah).
EMBLEM = {'A': (537, 475), 'P1': (682, 688.5), 'U3': (497, 842), 'N26': (1131, 503)}
# Opening session, 10 Nov 2026: two chairs stood side by side at the top of the dais.
OPENING = {'dark-haired man': {'P1': (617.5, 600), 'N26': (1196, 411)},
           'bald man':        {'P1': (659.5, 592.5), 'N26': (1251, 422)}}
# The Speaker's head, seated in the Speaker's chair (U3, February 2026).
SPEAKER_HEAD_U3 = (370, 711)
# Heads of the three people seated along the dais in U2 (2025); U2 looks along the dais.
DAIS_HEADS_U2 = {'nearest': (212, 680), 'middle': (203, 651), 'farthest': (213, 632)}
# HDR: empty hall, front-on from the back gallery (1100 x 732; not in the hall fit).
# Its camera is solved from the dark screens of back rows B1-B3 (seat 0 = rightmost) and the emblem.
HDR_SIZE = (1100, 732)
HDR_SCREENS = {'B1': [(666.5, 561.5), (621, 563.5), (574.5, 564.5), (533, 564.5), (485.5, 563.5), (440.5, 562)],
               'B2': [(739, 590), (686, 594), (632.5, 596), (577.5, 599), (527.5, 599), (473, 596), (420, 594), (369, 590.5)],
               'B3': [(834.5, 627), (775, 634.5), (713, 639.5), (648.5, 644.5), (582.5, 648), (519, 648), (453, 645), (390, 640), (329, 635), (270.5, 628.5)]}
HDR_EMBLEM = (555.4, 441.7)
HDR_CHAIR_TOP = (556.9, 405.5)     # top of the Speaker's chair back, its middle

def hdr_camera(emblem):
    q = fit['params']
    X = np.array([feat(el, i, q, 'mon') for el, pts in HDR_SCREENS.items() for i in range(len(pts))])
    U = np.array([uv for pts in HDR_SCREENS.values() for uv in pts])
    C = np.array([0, 16, 4.5]); fw = np.array([0, -6, 0.5]) - C; fw /= np.linalg.norm(fw)
    rt = np.cross(fw, [0, 0, 1.0]); rt /= np.linalg.norm(rt); R = np.stack([rt, np.cross(fw, rt), fw]); rv, _ = cv2.Rodrigues(R)
    c0 = np.concatenate([rv.ravel(), -R @ C, [580, -0.2, 0, 0, -200]])
    lo = [-10]*3 + [-300]*3 + [100, -1.5, -1.5, -400, -400]; hi = [10]*3 + [300]*3 + [8000, 1.5, 1.5, 400, 400]
    def r(c): return np.concatenate([(project2(X, c, *HDR_SIZE)[0] - U).ravel(), (proj(c, HDR_SIZE, emblem) - HDR_EMBLEM)*3])
    s = least_squares(r, c0, bounds=(lo, hi), loss='soft_l1', f_scale=2)
    return s.x, np.linalg.norm(r(s.x)[:-2].reshape(-1, 2), axis=1)

if __name__ == '__main__':
    E, e, sd = triangulate(EMBLEM)
    print(f'emblem on the dais front (4 photos): x={E[0]:+.2f}±{sd[0]:.2f} y={E[1]:.2f}±{sd[1]:.2f} z={E[2]:.2f}  misfit {np.round(e, 1)} px')
    for k in EMBLEM:
        X, _, _ = triangulate({p: uv for p, uv in EMBLEM.items() if p != k}); print(f'   without {k:3s}: x={X[0]:+.2f} y={X[1]:.2f}')
    heads = {}
    for who, m in OPENING.items():
        X, e, sd = triangulate(m); heads[who] = X
        print(f'opening session, {who}: x={X[0]:+.2f}±{sd[0]:.2f} y={X[1]:.2f}±{sd[1]:.2f} z={X[2]:.2f}  misfit {np.round(e, 1)} px')
    a, b = heads.values(); print(f'   the two chairs: midpoint x={(a[0]+b[0])/2:+.2f} y={(a[1]+b[1])/2:.2f}, {np.linalg.norm(a[:2]-b[:2]):.2f} apart')
    y, z = on_plane('U3', SPEAKER_HEAD_U3); print(f"Speaker's head in his chair (U3), on the axis: y={y:.2f} z={z:.2f}")
    for k, uv in DAIS_HEADS_U2.items():
        print(f'U2 dais head ({k}): y={on_plane("U2", uv)[0]:.2f} at x=0, {on_plane("U2", uv, -2)[0]:.2f} at x=-2, {on_plane("U2", uv, 2)[0]:.2f} at x=+2')
    c, e = hdr_camera(E)
    print(f'HDR camera: back-row screens median {np.median(e):.2f} px, centre {np.round(center2(c), 2)}')
    for yy in (-10.0, -10.5):
        x, z = least_squares(lambda xz: proj(c, HDR_SIZE, np.array([xz[0], yy, xz[1]])) - HDR_CHAIR_TOP, np.array([0.0, 1.7])).x
        print(f"HDR: Speaker's chair (top of back) at x={x:+.3f} if y={yy}")
