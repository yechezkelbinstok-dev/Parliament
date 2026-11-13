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
   seat spacing, platform heights) was fitted jointly with the cameras of six
   photos taken from different places:
   - from the Speaker's dais, November 2026 (`U1`);
   - from the right side gallery, February 2026 (`U3`) and 2025 (`U2`);
   - from the press corner at the back right, 2023 (`A`) and at the 26th
     Knesset's opening session, 10 November 2026 (`P1`, from higher up);
   - from the left side gallery at the same opening session (`N26`), the mirror
     view of `U3`.
   Seats are located in each photo by their lit name displays or desk screens;
   every observation is tied to a known seat (`obs*.json`, 413 in all). Screens
   partly hidden behind someone's head were left out, since only part of them
   shows. One `P1` observation had been tied to the wrong screen (B4.5 to the
   upper half of B4.6's screen, 25 px from where the model puts it) and was
   corrected. `P1` and `N26` appear perspective-corrected, so their cameras have an
   off-centre lens model (`cam2.py`). `A` is cropped (1600 × 1157, not the 3:2
   of a whole frame), so it gets the same lens model, with its image centre
   allowed to move only as far as the crop could have moved it (70 px across,
   25 px up or down). `U1`, `U2` and `U3` are whole frames with a centred lens.
3. **Corner seats**: in every photo, the two seats either side of each side-row
   bend showed up closer together than the regular seat pitch (the last seat of
   the front run toward the back, the first seat of the back run toward the
   front, by about 0.05 seat widths each). The corner desks are wedge-shaped.
   The model (`model6.py`) has one shared parameter for this: each of the two
   seats sits 0.064 ±0.004 seat widths closer to the bend. On the original five
   photos it lowers the median error from 2.28 to 1.97 px, and their value
   (0.063) matches the one with all six photos.
4. Units are one MK seat width; no published dimensions were used (none were
   found apart from the 30 m wall behind the Speaker). A dot map needs only
   proportions.

Two more photos from the same back-right corner (2012 and 2020) were left out:
they repeat a viewpoint already covered twice, and furniture changes since then
would have to be ruled out first. A wide front-on photo of the empty hall from
the back gallery (`HDR`) is used only for the Speaker (below): its screens are
switched off, so only the back rows can be located in it.

## Results (units: one MK seat width, ±1σ)

| quantity | value |
|---|---|
| bend of side rows (back part turns inward) | 13.8° ±0.4, 14.1° ±0.3, 15.1° ±0.3, 15.2° ±0.3 (inner → outer) |
| front part of side rows | parallel to the hall axis (within 0.5°) |
| side rows' bend points, distance from the axis | 4.46, 6.38, 8.32, 10.24 (±0.05, 0.07, 0.10, 0.12) |
| corner seats, closer to the bend than the pitch | 0.064 ±0.004 |
| government table: angled section | 14.4° ±0.4 from the axis |
| government table seat width | 0.695 straight, 0.542 angled, 0.604 head (±0.004–0.008) |
| back rows: distance behind the table head | 2.50, 4.46, 6.40, 8.35 (±0.02–0.04) |
| back rows: V-shape (each half tilted back) | 5.3° ±0.6, 5.3° ±0.3, 5.2° ±0.2, 5.7° ±0.3 |
| back-row seat width | 0.988 ±0.012 |

The model reproduces the 413 observed seat positions with a median error of
2.0 px (2048-px images).

The side rows' distance from the axis is the least certain part. It rests on
the photos that look along the hall (`U1`, `A`, `P1`), and they disagree a
little: without `P1` the outer rows come 0.47 closer to the axis, without `U1`
0.19 further out. The earlier five-photo fit gave the outer row 10.08 ±0.06,
but that precision came from treating `A` as a whole frame with a centred lens.

## The Speaker

No seat observation covers the Speaker, so the Speaker's place was measured
separately (`speaker.py`) with the fitted cameras.

Across the hall (x):

- The Knesset emblem on the front of the dais, marked in four photos (`A`,
  `P1`, `U3`, `N26`), triangulates to x = −0.01 ±0.02, y = −8.85. Leaving any
  one photo out moves it by at most 0.03.
- In the front-on photo (`HDR`), whose camera (solved from 24 back-row screens
  and the emblem) sits on the axis, the Speaker's chair stands directly above
  the emblem: x = −0.08 ±0.05.
- At the opening session two chairs stood side by side at the top of the dais.
  Triangulated from `P1` and `N26` without assuming anything about the axis,
  the two people seated there were at x = +0.50 and −0.54: placed evenly
  either side of the axis (midpoint −0.02).
- The Knesset's own panorama of the hall shows the Speaker's chair alone at the
  centre of the dais's top tier, and the official seating chart has the Speaker
  in the middle of the dais with a seat on each side.

Along the hall (y):

- The Speaker's head, seated in his chair in `U3` (February 2026): y = −10.12
  (±0.03 for a 3 px marking error). The top of his chair back is at −10.5.
- The two people at the top of the dais at the opening session (`P1` + `N26`):
  y = −9.90 and −10.19.
- In `U2` (2025), which looks along the dais, the three people seated there:
  y = −9.97 to −10.08.

The dot is drawn at x = 0, y = −10.1.

## Checks

- **Leave one photo out** (`robust7.py`): refit without each photo in turn and
  measure how far the map moves.

  | photo left out | median move | max move |
  |---|---|---|
  | dais, 2026 (`U1`) | 0.086 | 0.209 |
  | right side gallery, Feb 2026 (`U3`) | 0.075 | 0.138 |
  | right side gallery, 2025 (`U2`) | 0.038 | 0.092 |
  | back-right corner, 2023 (`A`) | 0.030 | 0.070 |
  | back-right corner, Nov 2026 (`P1`) | 0.209 | 0.504 |
  | left side gallery, Nov 2026 (`N26`) | 0.024 | 0.044 |

  The large moves are the side rows' distance from the axis (see Results). The
  corner-seat parameter stays between 0.059 and 0.066 whichever photo is left
  out. The government table has to be seen from the side: with only the dais
  photo's view of it, its depth cannot be pinned down. Four side photos see it.
- **Symmetry** (`sym7.py`, using `model6s.py`): fitting the left and right sides
  separately, matching seats agree to a median of 0.072 seat widths (max 0.19),
  and the bend angles to within 1.0°.

## Assumptions

- Left/right mirror symmetry (supported by the test above).
- Chairs are drawn 0.8 seat widths behind the desk front (estimated, not
  measured; ±0.2 would move every dot by the same amount).
- The Speaker's dot is where the Speaker's head is when seated, which is above
  the chair; an MK's dot is the chair itself, estimated from the desk.

## Files

The code and data are in `code/`.

The scripts were run in a working folder next to the photos, which are not
included here (they belong to their photographers); the fitted results are in
`fit.json`, and everything below runs from it.

- `model6.py` – the hall model (`model4.py` plus the corner seats);
  `model2.py` to `model5.py` – its earlier versions
- `cam2.py` – camera model; `joint7.py` – joint fit of model and cameras
  (writes `fit.json` and `fit_sd.json`, the 1σ of each parameter)
- `robust7.py`, `sym7.py` (with `model6s.py`) – leave-one-out and symmetry tests;
  `joint6.py`, `robust6.py`, `sym6.py` – the same for the earlier five-photo fit
- `obs.json`, `obs_A.json`, `obs_U2.json`, `obs_extraB.json`, `obs_P1.json`,
  `obs_N26.json` – seat observations
- `speaker.py` – the Speaker's position, from marks in the photos and the fitted cameras
- `names2026.py`, `parties.json`, `makesvg.py` – build the dot map from the fit:
  `python3 makesvg.py` in `code/` rewrites `knesset-26-seating.svg` from `fit.json`
  (`--no-number` leaves out the total); the PNG is a CairoSVG render
