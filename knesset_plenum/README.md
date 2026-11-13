# Knesset plenum: measured seating layout

`diagrams/knesset-26-seating.svg` is a dot map of the Knesset plenary hall whose
seat positions were **measured from photographs**, not copied from a schematic.
It shows the 120 MKs of the 26th Knesset; empty seats and ministers who are not
MKs are left blank, so every dot sits where its seat really is.

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
   seat spacing, platform heights) was fitted jointly with the cameras of four
   photos taken from different places:
   - from the Speaker's dais, November 2026 (`U1`),
   - from the side gallery, February 2026 (`U3`) and 2025 (`U2`),
   - from the back corner gallery, 2023 (`A`).
   Seats are located in each photo by their lit name displays or desk screens;
   every observation is tied to a known seat (`obs*.json`, 274 in all).
3. Units are one MK seat width; no published dimensions were used (none were
   found apart from the 30 m wall behind the Speaker). A dot map needs only
   proportions.

## Results (units: one MK seat width, ±1σ)

| quantity | value |
|---|---|
| bend of side rows (back part turns inward) | 13.8° ±0.5, 13.6° ±0.3, 15.1° ±0.3, 15.5° ±0.7 (inner → outer) |
| front part of side rows | parallel to the hall axis (within ~2°) |
| side rows' bend points, distance from the axis | 4.48, 6.36, 8.30, 10.17 (±0.04–0.08) |
| government table: angled section | 14.1° ±0.5 from the axis |
| government table seat width | 0.695 straight, 0.550 angled, 0.608 head (±0.007) |
| back rows: distance behind the table head | 2.48, 4.46, 6.42, 8.49 (±0.03–0.05) |
| back rows: V-shape (each half tilted back) | 5.2° ±0.6, 5.4° ±0.4, 5.0° ±0.3, 6.6° ±0.3 |
| back-row seat width | 0.990 ±0.009 |

The model reproduces the 274 observed seat positions with a median error of
2.3 px (2048-px images).

## Checks

- **Hold-out tests** (`robust5.py holdout`): leave out one photo's data for one
  part of the hall, refit, and see how far the map moves. Worst case 0.17 seat
  widths; the last back row, the outer rows and the government table each move
  0.01–0.13.
- **Symmetry** (`robust5.py asym`, using `model5.py`): fitting the left
  and right sides separately gives the same geometry within about 1° and
  0.15 seat widths wherever both sides are observed.

## Assumptions

- Left/right mirror symmetry (supported by the test above).
- Chairs are drawn 0.8 seat widths behind the desk front (estimated, not
  measured; ±0.2 would move every dot by the same amount).
- The Speaker's dot is placed at the photographer's position on the dais.

## Files

- `model2.py`, `model3.py`, `model4.py`, `model5.py` – the hall model
- `fitN.py` – joint fit of model and cameras; `robust5.py` – hold-out tests and uncertainties
- `obs.json`, `obs_A.json`, `obs_U2.json`, `obs_extraB.json` – seat observations
- `fit.json` – fitted parameters and cameras
- `names2026.py`, `parties.json`, `makesvg.py` – build the dot map from the fit
