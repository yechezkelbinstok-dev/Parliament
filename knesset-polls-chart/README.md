# Opinion polls Israel 2026

Rebuilds [File:Opinion polls Israel 2026.svg](https://commons.wikimedia.org/wiki/File:Opinion_polls_Israel_2026.svg)
(seat projections since the 2022 election, LOESS trend per party) from the Wikipedia poll tables.

- `opinion_polls_israel_2026.R`: the chart script (ggplot2 + svglite)
- `rebuild.py`: turns the parsed Wikipedia tables into `polls.csv`
- `polls.csv`: one row per poll, newest first, 2022 election result last
- `Opinion polls Israel 2026.svg`: the current output

Compared with the version uploaded on 5 Oct 2026:

- The legend is one column, and each party is named as in the newest Wikipedia table where it has
  a column (Otzma, Dems, RZP-Zehut, Reserv.-NEP, ...), instead of codes like `NU.BW` and `Res.ZH`.
- The data is re-extracted from Wikipedia rather than carried over. That adds 11 polls the old
  chart lacked, follows Wikipedia where it has been corrected since, and treats merged cells the same
  way throughout.
- The styling, smoothing spans and series start dates are unchanged. With Basque mapping's data and
  the original legend (the script as of commit `372e321`), the script reproduces the 5 Oct file byte
  for byte (MD5 `351713575c214b772a046e151333a136`).

## Rules for `polls.csv`

- One row per poll in Wikipedia table order. `Date` is the last day of fieldwork (`14–15 Oct` →
  `2026-10-15`); the year is the article's, even where a hidden sort key disagrees.
- Seat numbers go in as they are. Anything in brackets is converted at 1.2 seats per percentage
  point, rounded to one decimal: `(2.5%)` → 3, `(1.9%)` → 2.3, `(<1%)` → 1.2, `(3)` → 3.6.
  N/A, `–` or no figure → blank.
- Renamed columns join one series: National Unity → Blue & White; RZP → RZP-Zehut;
  Reserv. and Zionist Home → Reserv.-NEP; Bennett party → Bennett 2026; Winter party → Amcha Yisrael.
- Merged cells: RZP+Zehut → RZP-Zehut, Reserv.+NEP → Reserv.-NEP, sub-columns under the Joint List
  header → Joint List. A cell merged across two separate parties (RZP+Otzma, Labor+Meretz) is left out.
- Each series starts on the date the original chart starts it (New Hope 2024-03-13, Dems 2024-07-04,
  Bennett 2026 2025-05-07, Yashar 2025-07-31, Reserv.-NEP 2025-08-20, Together 2026-04-26,
  Unity 2026-08-06, Amcha Yisrael 2026-08-09, Joint List 2026-08-20, Haredi Public 2026-09-07).
  Earlier figures for it are left out.
- Polls with several scenario rows: the row with the most started series, skipping rows that
  include a party before its start date; the first row on a tie.
- 2022 election row: RZP 7 and Otzma 6, as elected (the table shows their joint list's 14).
- Scenario polls (the separate section on Wikipedia) are not included.

## Updating

```sh
./fetch_tables.sh wiki                       # the four articles, rendered HTML
python3 parse_wiki.py wiki rows.json         # needs beautifulsoup4 and lxml
python3 rebuild.py rows.json polls.json polls.csv

micromamba create -n polls -c conda-forge "r-base=4.3" "r-ggplot2=3.4.4" "r-svglite=2.1.3" mscorefonts
LC_ALL=C.UTF-8 micromamba run -n polls Rscript opinion_polls_israel_2026.R polls.csv "Opinion polls Israel 2026.svg"
```

Check any new table layout (a new party column, a renamed header) before trusting the output:
`rebuild.py` stops with "unmapped column" when a header isn't in its column list, and a new party
also needs a colour, a span and a start date in the R script and `rebuild.py`.

Needs ggplot2 3.4.x, svglite 2.1.x, the Arial font and a UTF-8 locale; ggplot2 3.5 or later draws
the legend differently.
