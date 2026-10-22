# Opinion polls Israel 2026

Rebuilds [File:Opinion polls Israel 2026.svg](https://commons.wikimedia.org/wiki/File:Opinion_polls_Israel_2026.svg)
(seat projections since the 2022 election, LOESS trend per party) and updates it with new polls.

- `opinion_polls_israel_2026.R`: the chart script (ggplot2 + svglite)
- `polls.csv`: one row per poll, newest first, 2022 election result last
- `Opinion polls Israel 2026.svg`: the current output (polls up to 20 Oct 2026)

## Check against the original

`polls.csv` without its first 21 rows is the data in the version uploaded on 5 Oct 2026, read back
from that SVG. Running the script on those rows gives a file byte-identical to the Commons version
(MD5 `351713575c214b772a046e151333a136`), so the script, settings and package versions match.

## Running it

Needs R with **ggplot2 3.4.x**, **svglite 2.1.x** and the **Arial** font. Newer ggplot2
(3.5 or later) draws the legend differently. One way to get that setup:

```sh
micromamba create -n polls -c conda-forge "r-base=4.3" "r-ggplot2=3.4.4" "r-svglite=2.1.3" mscorefonts
micromamba run -n polls Rscript opinion_polls_israel_2026.R polls.csv "Opinion polls Israel 2026.svg"
```

## Adding polls

Add new rows at the top of `polls.csv`, in the order the Wikipedia table lists them (newest first).
Use the conventions already in the data:

- `Date` is the last day of fieldwork (`14–15 Oct` → `2026-10-15`).
- Seat numbers go in as they are.
- Anything in brackets is converted at 1.2 seats per percentage point, rounded to one decimal:
  `(2.5%)` → 3, `(1.9%)` → 2.3, `(<1%)` → 1.2, `(3)` → 3.6.
- N/A, `–` or no figure → leave blank.
- Merged cells: RZP–Zehut → `RZ`, Reservists–NEP → `Res.ZH`, Joint List → `JL`.
- If a poll has several scenario rows, use the one that includes all the parties in the chart.
- Blue & White (`NU.BW`) withdrew on 19 Oct 2026, so it is blank from then on.

The LOESS spans per party are kept as in the original. Scenario polls are not included.
