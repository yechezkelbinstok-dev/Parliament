# Parliament diagrams

Make a parliament seating diagram from a plain list of parties, either as a
hemicycle (arch) or in Westminster style (facing benches). Instead of
adding every party by hand in the [parliamentdiagram](https://github.com/slashme/parliamentdiagram)
web form, write them in a text file and run one command. The seat layout comes
from that tool (the [parliamentarch](https://pypi.org/project/parliamentarch/)
library for arches, its `westminster.py` for Westminster), so the diagrams look the same.

![Arch example](diagrams/uk-2024.png)
![Westminster example](diagrams/uk-reform-coalition.png)

## Setup

```sh
pip install -r requirements.txt
```

## Usage

1. Create a file in `parties/`, one party per line, **in seating order from left to right**:

   ```text
   title: My Parliament

   Greens, 12, #02A95B
   Social Democrats, 48, #E4003B
   Liberals, 20, #FAA61A
   Conservatives, 40, #0087DC
   ```

   Each line is `Party name, seats, color`. The color can be a hex code
   (`#E4003B` or `E4003B`) or a color name (`red`). Party names may contain
   commas. Lines starting with `#` are comments.

2. Run:

   ```sh
   python parliament.py parties/my-parliament.txt --png
   ```

   This writes `diagrams/my-parliament.svg` (and `.png` with `--png`).
   Use `-o some/path.svg` to write somewhere else, and `--scale` to change the
   PNG size (default 4, which gives a 1440px-wide image).

## Westminster style

Add `style: westminster` and put the bench at the end of each party line:
`government`, `opposition`, `crossbench` or `speaker`.

```text
title: House of Commons
style: westminster

Speaker, 1, black, speaker
Labour, 411, #E4003B, government
Conservative, 121, #0087DC, opposition
Liberal Democrats, 72, #FAA61A, opposition
```

The Speaker sits at the left end, the government on the bottom benches and the
opposition on the top benches, with cross-benchers on the right. Within each
bench, parties are seated in the order listed, starting next to the Speaker.

## Optional settings

Put any of these lines in the party file:

| Setting | Default | What it does |
| --- | --- | --- |
| `title: ...` | none | Title above the diagram |
| `style: westminster` | `arch` | Diagram style |
| `legend: no` | `yes` | Hide the legend under the diagram |

Arch style only:

| Setting | Default | What it does |
| --- | --- | --- |
| `number: no` | `yes` | Hide the total seat count in the middle |
| `dense: yes` | `no` | Fill the outer rows first, leaving the inner rows empty |
| `rows: 8` | automatic | Use at least this many rows (more rows = more spread out) |
| `span: 150` | `180` | Angle of the arc in degrees (180 = half circle) |

Westminster style only (defaults match the web tool):

| Setting | Default | What it does |
| --- | --- | --- |
| `corners: 0` | `1` | Seat corner roundness: 0 = squares, 0.5 or more = circles |
| `spacing: 0.2` | `0.1` | Gap between seats, from 0 (touching) to 0.99 |
| `cozy: no` | `yes` | `no` starts each party in a new column |
| `fullwidth: yes` | `no` | Make the smaller wing thinner so both span the full width |
| `wingrows: 6` | automatic | Rows of seats in each wing |
| `crossbench-columns: 3` | automatic | Columns of seats in the cross-bench |

Parties with 0 seats are left out of the diagram and the legend.
