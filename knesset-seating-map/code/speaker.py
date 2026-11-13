"""Measure the Speaker's position from the photos, using the fitted cameras.

    python3 speaker.py

The marks below were read off the photos (pixel coordinates in each photo as
used in the fit). No seat observation covers the Speaker, so these are separate.
"""
import json, numpy as np
from scipy.optimize import least_squares
from cam2 import project2
fit = json.load(open('fit.json'))
SIZE = {'U1': (2048, 1366), 'U3': (2048, 1366), 'A': (1600, 1157), 'U2': (2048, 1366), 'P1': (2048, 1365)}
def proj(p, X): return project2(np.atleast_2d(X), np.array(fit['cameras'][p]), *SIZE[p])[0][0]
def triangulate(marks):
    """3D point whose projections best match the marks; returns the point and the misfit in px."""
    r = lambda X: np.concatenate([proj(p, X) - uv for p, uv in marks.items()])
    X = least_squares(r, np.array([0.0, -10.0, 1.0])).x
    return X, np.linalg.norm(r(X).reshape(-1, 2), axis=1)
def on_plane(p, uv, x=0.0):
    """(y, z) of the point on the plane X = x that the photo shows at uv."""
    return least_squares(lambda yz: proj(p, np.array([x, *yz])) - uv, np.array([-10.0, 1.5])).x

# The Knesset emblem on the front of the dais (centre of the menorah), seen from three sides.
EMBLEM = {'A': (537, 475), 'P1': (682, 688.5), 'U3': (497, 842)}
# Head of the Speaker, seated in the Speaker's chair (U3, February 2026).
SPEAKER_HEAD_U3 = (370, 711)
# Heads of the three people seated along the dais in U2 (2025). U2 looks along the dais,
# so these give the distance along the hall almost whatever chair each person is in.
DAIS_HEADS_U2 = {'nearest': (212, 680), 'middle': (203, 651), 'farthest': (213, 632)}

if __name__ == '__main__':
    X, e = triangulate(EMBLEM)
    print(f'emblem on the dais front: x={X[0]:.2f} y={X[1]:.2f} z={X[2]:.2f} (misfit {np.round(e, 1)} px)')
    y, z = on_plane('U3', SPEAKER_HEAD_U3)
    print(f"Speaker's head, on the axis: y={y:.2f} z={z:.2f}")
    for dx in (-0.3, 0.3):
        print(f'  if {dx:+.1f} off the axis: y={on_plane("U3", SPEAKER_HEAD_U3, dx)[0]:.2f}')
    for k, uv in DAIS_HEADS_U2.items():
        print(f'U2 dais head ({k}): y={on_plane("U2", uv, 0.0)[0]:.2f} at x=0, '
              f'{on_plane("U2", uv, -2.0)[0]:.2f} at x=-2, {on_plane("U2", uv, 2.0)[0]:.2f} at x=+2')
