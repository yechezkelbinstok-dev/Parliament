# Opinion polls Israel 2026

Rebuilds [File:Opinion polls Israel 2026.svg](https://commons.wikimedia.org/wiki/File:Opinion_polls_Israel_2026.svg)
(seat projections since the 2022 election, LOESS trend per party) and updates it with new polls.

- `opinion_polls_israel_2026.R`: the chart script (ggplot2 + svglite)
- `polls.csv`: one row per poll, newest first, 2022 election result last
- `Opinion polls Israel 2026.svg`: the current output

Compared with the version uploaded on 5 Oct 2026, the legend is a single column and uses the party
names from the column headers of the Wikipedia poll tables (Otzma, RZP, Dems, Reserv., ...) instead
of codes like `NU.BW` and `Res.ZH`. Two series cover a party whose column was renamed:
Blue & White (National Unity until mid-2025) and Reserv. (Zionist Home in July–September 2026,
Reserv.–NEP since).

## Check against the original

The rows of `polls.csv` up to 4 Oct 2026 are the data in the 5 Oct upload, read back from that SVG.
With the original legend settings (the script as of commit `372e321`) it reproduces that file
byte for byte (MD5 `351713575c214b772a046e151333a136`), so the data, LOESS spans and styling match.

## Running it

Needs R with **ggplot2 3.4.x**, **svglite 2.1.x**, the **Arial** font and a UTF-8 locale (the
default on macOS, Linux and Windows with R 4.2 or later). ggplot2 3.5 or later draws the legend
differently. One way to get that setup:

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
- Merged cells: RZP–Zehut → `RZP`, Reserv.–NEP → `Reserv.`.
- If a poll has several scenario rows, use the one that includes all the parties in the chart.
- Blue & White withdrew on 19 Oct 2026, so it is blank from then on.

The LOESS spans per party are kept as in the original. Scenario polls are not included.
