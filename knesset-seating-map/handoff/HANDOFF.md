# Hand-off: Knesset seating map — next job: measure the Speaker's position

The finished map and write-up live in the repo at `knesset-seating-map/`
(branch `ccr-ac96743a-yldxh6`). This package holds everything that was used
to make it, including the photos (not in the repo: they belong to their
photographers).

## The open task
The Speaker's dot is NOT measured. `work/makesvg2.py` hard-codes it at
x=0, y=-10.0 seat widths (`SPEAKER_Y`), copied roughly from where the dais
photo was taken (camera U1 centre ≈ (-0.12, -10.45, 2.3)). Everything else
comes from the fitted 3D model.

To measure it: mark the Speaker's chair (centre of the seat, or a point on it)
in photos with solved cameras — U3 (side gallery, Feb 2026, Speaker visible at
the dais on the left), A (2023 empty hall, back-right corner), P1 (opening
session 10 Nov 2026, back-right corner, high) — then triangulate with the
cameras in `work/fit6_v.npy` / `work/fit6.json` and the projection in
`work/cam2.py` (`project2`, `center2`). Assume x≈0 (hall axis) as a check.

## Coordinates and units
- Unit = one MK seat width. Origin = centre of the government table head (GH),
  y increases toward the back rows, Speaker at negative y. x<0 = coalition
  (left side in the map), x>0 = opposition.
- Model: `work/model4.py` (`_seg`, `feat`, `visible_kind`), parameters named in
  `work/model3.py` `SPEC`. Final fit: `work/fit6_v.npy` (first len(SPEC)
  entries = hall parameters, then cameras in order U1,U3,A,U2 (8 params each:
  rvec3, tvec3, f, k1) and P1 (11: + k2, cx_off, cy_off)). Same in fit6.json.
- `feat(..., kind='np')` = lit name display on the desk front;
  `kind='mon'` = desk screen. Dots in the map = desk point + 0.8 × outward
  normal (chair position, an estimate: `OFF` in makesvg2.py).

## Photos (`photos/`)
| file | what | camera |
|---|---|---|
| U1.jpg | from the Speaker's dais, Nov 2026, empty hall | solved |
| U3.jpg | side gallery (right), Feb 2026, 60th-anniversary session | solved |
| U2.jpg | side gallery (right, near dais), 2025 | solved |
| A.jpg | back-right corner, 2023, empty (Dreamstime preview) | solved |
| P1.jpg | back-right corner, high, opening session 10 Nov 2026 | solved (11-param lens) |
| P2.jpg | back-right corner, 2020 opening session | not used |
| P4.jpg | back-right corner, ~2012, empty, light carpet | not used |
| C.jpg, N1.png, N2.jpg | other small views | not used |

## Running the code
Python with numpy, scipy, opencv-python-headless, pillow. Run scripts from
inside `work/` with the photos copied/linked next to them (they open e.g.
`U1.jpg` by name). Key scripts: `joint6.py` (joint fit, writes fit6_v.npy),
`robust6.py` (leave-one-photo-out), `sym6.py` (left/right test),
`makesvg2.py fit6_v.npy out.svg` (builds the map; `render.js` renders it with
Playwright). Observation files: `obs.json` (U1,U3), `obs_A.json`,
`obs_U2.json`, `obs_extraB.json`, `obs_P1.json`. Seat occupants:
`names2026.py`; party colours: `parties.json`.
Many other files in `work/` are intermediate steps (detections `*L.json`,
`*M.json`, `det_*.json`; earlier fits `fit3/4/5`).

## Reference (`reference/`)
Official seating chart 10.11.2026 and Nov 2022; the old Commons SVG; the other
session's dot map; Knesset building PDFs (planning history, architecture); the
Knesset's own plenum photos (k*.jpg); current map and a check image.

## Results so far
Median reprojection error 2.4 px over 360 seat observations; leaving out any
one photo moves the map ≤0.22 seat widths; left/right agree within 0.24.
The only published dimension found: the stone wall behind the Speaker is
30 m × 7.5 m.
