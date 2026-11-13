# Knesset plenum: measured seating layout

`knesset-26-seating.svg` (with a `.png` render) is a dot map of the Knesset plenary hall whose
seat positions were **measured from photographs**, not copied from a schematic.
It shows the 120 MKs of the 26th Knesset; empty seats and ministers who are not
MKs are left blank, so every dot sits where its seat really is.

The total is written the way the Wikipedia arch diagrams write it: bold, a tenth
of the image's width, in the open middle that the seats wrap around. An arch
opens at the bottom, so its number sits there, level with the lowest seats; here
the horseshoe opens toward the Speaker, so the number sits in that opening, just
below the front ends of the rows: the top of the digits is level with the end
of the longest row. The space between the rows and the Speaker is to
scale: it is the floor in front of the Speaker's dais.

## How it was measured

1. **Structure** (which seats exist, how many per row) comes from the Knesset's
   official seating chart (updated 10.11.2026) and was confirmed in the photos:
   - side rows: 7, 9, 11, 13 seats per side, each two straight runs with one bend
     (4+3, 5+4, 6+5, 7+6 seats counted from the Speaker's end);
   - government table: each arm 6 straight seats then 5 angled seats, 5-seat head;
   - back rows: 6, 8, 10, 16 seats. The 16-seat last row was confirmed three ways:
     the names on its desks are centred on the hall's axis only with 16 seats,
     a 2026 side photo shows lit name displays at its far end, and a 2023 photo
     shows its desk and screens continuing to the near end.
2. **Geometry**: a parametric 3D model of the hall (bend angles, row positions,
   seat spacing, platform heights) was fitted jointly with the cameras of five
   photos taken from different places:
   - from the Speaker's dais, November 2026 (`U1`);
   - from the side gallery, February 2026 (`U3`) and 2025 (`U2`);
   - from the press corner at the back right, 2023 (`A`) and at the 26th
     Knesset's opening session, 10 November 2026 (`P1`, from higher up).
   Seats are located in each photo by their lit name displays or desk screens;
   every observation is tied to a known seat (`obs*.json`, 360 in all).
   `P1` appears perspective-corrected, so its camera has an off-centre lens
   model (`cam2.py`).
3. Units are one MK seat width; no published dimensions were used (none were
   found apart from the 30 m wall behind the Speaker). A dot map needs only
   proportions.

Two more photos from the same back-right corner (2012 and 2020) were left out:
they repeat a viewpoint already covered twice, and furniture changes since then
would have to be ruled out first.

## Results (units: one MK seat width, ±1σ)

| quantity | value |
|---|---|
| bend of side rows (back part turns inward) | 13.8° ±0.5, 14.1° ±0.3, 15.2° ±0.2, 14.9° ±0.3 (inner → outer) |
| front part of side rows | parallel to the hall axis (within 0.6°) |
| side rows' bend points, distance from the axis | 4.41, 6.30, 8.20, 10.08 (±0.03–0.06) |
| government table: angled section | 13.9° ±0.4 from the axis |
| government table seat width | 0.694 straight, 0.549 angled, 0.598 head (±0.006) |
| back rows: distance behind the table head | 2.49, 4.45, 6.39, 8.40 (±0.03–0.04) |
| back rows: V-shape (each half tilted back) | 5.4° ±0.6, 5.4° ±0.4, 5.2° ±0.2, 6.3° ±0.2 |
| back-row seat width | 0.972 ±0.007 |

The model reproduces the 360 observed seat positions with a median error of
2.4 px (2048-px images).

## The Speaker

No seat observation covers the Speaker, so the Speaker's place was measured
separately (`speaker.py`) with the fitted cameras:

- The Knesset emblem on the front of the dais, marked in three photos (`A`,
  `P1`, `U3`), triangulates to x = 0.02, y = −8.9: the dais is centred on the
  hall's axis, and the three cameras agree at that end of the hall (misfit
  ≤ 3 px).
- The Speaker's head, seated in the Speaker's chair in `U3` (February 2026),
  lies at y = −10.15 on the axis (±0.03 for a 3 px marking error; ±0.13 if he
  sat 0.3 seat widths off the axis). The top of his chair back is at −10.5.
- In `U2` (2025), which looks along the dais, the three people seated there
  have their heads at y = −10.0 to −10.2, whichever chair each is in.

The dot is drawn at y = −10.15 on the axis, where the Speaker sits. Before
this was measured it was placed at −10.0, roughly where the dais photo
(`U1`, camera at y = −10.45) was taken: 0.15 seat widths off.

## Checks

- **Leave one photo out** (`robust6.py`): refit without each photo in turn and
  measure how far the map moves.

  | photo left out | median move | max move |
  |---|---|---|
  | dais, 2026 | 0.036 | 0.069 |
  | side gallery, Feb 2026 | 0.122 | 0.223 |
  | side gallery, 2025 | 0.015 | 0.022 |
  | back-right corner, 2023 | 0.085 | 0.208 |
  | back-right corner, Nov 2026 | 0.070 | 0.130 |

  Hiding the back rows in both back-corner photos moves the map by at most 0.19.
  The government table has to be seen from the side: with only the dais photo's
  view of it, its depth cannot be pinned down. Three side photos see it.
- **Symmetry** (`sym6.py`, using `model5.py`): fitting the left and right sides
  separately, matching seats agree to a median of 0.10 seat widths (max 0.24),
  and the bend angles to within 1.3°.

## Assumptions

- Left/right mirror symmetry (supported by the test above).
- Chairs are drawn 0.8 seat widths behind the desk front (estimated, not
  measured; ±0.2 would move every dot by the same amount).
- The Speaker's chair is on the hall's axis, like the emblem on the dais front;
  the dot is the Speaker's seated head, the counterpart of an MK's chair.

## Files

The code and data are in `code/`.

The scripts were run in a working folder next to the photos, which are not
included here (they belong to their photographers); the fitted results are in
`fit.json`.

- `model2.py`, `model3.py`, `model4.py`, `model5.py` – the hall model
- `cam2.py` – camera model; `joint6.py` – joint fit of model and cameras
- `robust6.py`, `sym6.py` – leave-one-out and symmetry tests
- `obs.json`, `obs_A.json`, `obs_U2.json`, `obs_extraB.json`, `obs_P1.json` – seat observations
- `fit.json` – fitted parameters and cameras
- `speaker.py` – the Speaker's position, from marks in the photos and the fitted cameras
- `names2026.py`, `parties.json`, `makesvg.py` – build the dot map from the fit:
  `python3 makesvg.py` in `code/` rewrites `knesset-26-seating.svg` from `fit.json`
  (`--no-number` leaves out the total); the PNG is a CairoSVG render
