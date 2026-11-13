# Knesset plenum: measured seating layout

`diagrams/knesset-26-seating.svg` is a dot map of the Knesset plenary hall whose
seat positions were **measured from photographs**, not copied from a schematic.

## How it was measured

1. **Structure** (which seats exist, how many per row) comes from the Knesset's
   official seating chart (updated 10.11.2026) and was confirmed in the photos:
   - side rows: 7, 9, 11, 13 seats per side, each two straight runs with one bend
     (4+3, 5+4, 6+5, 7+6 seats counted from the Speaker's end);
   - government table: each arm 6 straight seats then 5 angled seats, 5-seat head;
   - back rows: 6, 8, 10, 16 seats (the 16-seat last row was checked by reading the
     names on the desks: the occupied seats are centred on the hall's axis
     only if the row has 16 seats).
2. **Geometry**: a parametric 3D model of the hall (bend angles, row positions,
   seat spacing, platform heights) was fitted jointly with the cameras of three
   photos taken from different places:
   - from the Speaker's dais, November 2026 (`U1`),
   - from the side gallery, February 2026 (`U3`),
   - from the back corner gallery, 2023 (`A`).
   Seats are located in each photo by their lit name displays or desk screens;
   each observation is tied to a known seat (`obs.json`, `obs_A.json`).
3. Left/right mirror symmetry is assumed. Chairs are placed 0.8 seat-widths
   behind the desk front (estimated, not measured). The Speaker's position is
   approximate.

## Results (units: one MK seat width)

| quantity | value |
|---|---|
| bend of side rows (inward, back part) | 13.7°, 13.3°, 15.0°, 15.6° (inner → outer) |
| front part of side rows | parallel to the hall axis (within ~2°) |
| spacing between side rows | ≈ 1.9 |
| government table: angled section | 14.3° from the axis |
| government table seat width | 0.70 (straight), 0.54 (angled), 0.60 (head) |
| back rows: distance behind the table head | 2.5, 4.5, 6.4, 8.4 |
| back rows: V-shape (each half tilted back) | 5.2°, 5.3°, 4.9°, 6.0° |
| back-row seat width | 0.98 |

The model reproduces 219 observed seat positions in the three photos with a
median error of 2.3 px (2048-px images). Estimated uncertainty: about ±1° on
angles and ±0.03–0.4 seat widths on positions.

## Files

- `model2.py`, `model3.py`, `model4.py` – the parametric hall model
- `fitN.py` – joint fit of model and cameras
- `obs.json`, `obs_A.json` – seat observations (pixel positions with seat identity)
- `fit.json` – fitted parameters and cameras
- `names2026.py`, `parties.json`, `makesvg.py` – build the dot map from the fit
