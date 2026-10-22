"""Rebuild polls.csv from the Wikipedia seat-projection tables (parsed by parse_wiki.py).

Rules
- One row per poll; dates are the last day of fieldwork; Wikipedia table order (newest first).
- Values: integers are seats; anything in brackets -> first number x 1.2, rounded to 0.1; else blank.
- Columns map to series by header (renamed columns join their party's series). A merged cell goes
  to the one series its columns belong to (RZP+Zehut, Reserv.+NEP, the sub-columns under the
  "Joint List" header); a merged cell across two separate parties' headers is left out.
- A series only takes values from its start date (when the party became a list in its own right);
  for polls with scenario rows the row covering the most active series is used, the first on a tie.
- 2022 election row: RZP 7 and Otzma 6 seats as elected (the table shows their joint list's 14).
"""
import json, re, csv, sys, collections, datetime
from build import parse_val

SERIES = ["Likud", "Yesh Atid", "Blue & White", "Shas", "UTJ", "RZP-Zehut", "Otzma", "Yisrael Beiteinu",
          "Ra'am", "Hadash–Ta'al", "Labor", "Meretz", "Balad", "New Hope", "Dems", "Bennett 2026", "Yashar",
          "Reserv.-NEP", "Together", "Unity", "Amcha Yisrael", "Joint List", "Haredi Public"]
COLMAP = {
    'Likud': 'Likud', 'Yesh Atid': 'Yesh Atid', 'National Unity': 'Blue & White', 'Blue & White': 'Blue & White',
    'Shas': 'Shas', 'UTJ': 'UTJ', 'RZP': 'RZP-Zehut', 'RZP - Zehut#1': 'RZP-Zehut', 'RZP - Zehut#2': '+Zehut',
    'Zehut': '+Zehut', 'Otzma': 'Otzma', 'Yisrael Beiteinu': 'Yisrael Beiteinu',
    "Ra'am": "Ra'am", "Joint List/Ra'am": "Ra'am", "Hadash –Ta'al": "Hadash–Ta'al",
    "Joint List/Hadash –Ta'al": "Hadash–Ta'al", 'Labor': 'Labor', 'Meretz': 'Meretz', 'Balad': 'Balad',
    'Joint List/Balad': 'Balad', 'New Hope': 'New Hope', 'Dems': 'Dems', 'Bennett 2026': 'Bennett 2026',
    'Bennett party': 'Bennett 2026', 'Yashar': 'Yashar', 'Reserv.': 'Reserv.-NEP', 'Zionist Home': 'Reserv.-NEP',
    'Reserv. - NEP#1': 'Reserv.-NEP', 'Reserv. - NEP#2': '+NEP', 'Together': 'Together', 'Unity': 'Unity',
    'Amcha Yisrael': 'Amcha Yisrael', 'Winter party': 'Amcha Yisrael', 'Joint List': 'Joint List',
    'Haredi Public': 'Haredi Public', 'Hendel party': '-Hendel',
}
IGNORE = {'Fieldwork date', 'Polling firm', 'Publisher', 'Sample size', 'Others', 'Gov.', 'Lead'}
# first date of each series in the 5 Oct 2026 chart
START = {s: '2022-11-01' for s in SERIES}
START.update({'New Hope': '2024-03-13', 'Dems': '2024-07-04', 'Bennett 2026': '2025-05-07', 'Yashar': '2025-07-31',
              'Reserv.-NEP': '2025-08-20', 'Together': '2026-04-26', 'Unity': '2026-08-06',
              'Amcha Yisrael': '2026-08-09', 'Joint List': '2026-08-20', 'Haredi Public': '2026-09-07'})
MONTHS = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}

def end_date(cell, article):
    """Last day of fieldwork from the displayed text; year from the sort key, checked against the article."""
    txt = cell['text'].replace('–', '-').replace('—', '-')
    last = txt.split('-')[-1].strip()
    m = re.match(r'(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?', last)
    day, mon = int(m.group(1)), MONTHS[m.group(2)[:3].lower()]
    year = int(m.group(3)) if m.group(3) else None
    sort = cell['sort']
    if year is None and sort:
        year = int(sort[:4])
    allowed = {'2026': {2026}, '2025': {2025}, '2024': {2024}, '2022-23': {2022, 2023}}[article]
    if year not in allowed:
        year = max(allowed) if article != '2022-23' else int(sort[:4])
    return datetime.date(year, mon, day).isoformat()

def row_values(r):
    cols, cells = r['cols'], r['cells']
    vals, raw_inactive = {}, set()
    j = 0
    while j < len(cells):
        c = cells[j]
        if c is None or j >= len(cols) or c['dup'] == 'col':
            j += 1; continue
        span = cols[j:j + c['colspan']]
        j += 1
        if any(n in IGNORE for n in span):
            continue
        targets = {COLMAP.get(n, '?' + n) for n in span}
        unknown = [t for t in targets if t.startswith('?')]
        if unknown:
            raise SystemExit(f'unmapped column {unknown} in {r["article"]} table {r["table"]}')
        charted = {t for t in targets if t in SERIES}
        if len(span) > 1 and len(charted) > 1:
            if all(n.startswith('Joint List') for n in span):
                charted = {'Joint List'}
            else:
                continue                      # merged across separate parties
        if len(charted) != 1:
            continue                          # Zehut / NEP alone, hypothetical Hendel party
        s = charted.pop()
        kind, v = parse_val(c['text'])
        if kind == 'seats':
            vals[s] = v
        elif kind == 'pct':
            vals[s] = round(v * 1.2 + 1e-9, 1)
    return vals

def build(rows_json):
    R = json.load(open(rows_json))
    polls, cur = [], None
    for r in R:
        d = r['cells'][0]
        if d is None or 'Likud' not in r['cols']:
            continue
        li = r['cols'].index('Likud')
        lk = r['cells'][li] if li < len(r['cells']) else None
        if lk is None or lk['colspan'] > 3:
            continue                          # note rows
        if d['dup'] != 'row' or cur is None:
            cur = {'article': r['article'], 'table': r['table'], 'date': end_date(d, r['article']),
                   'firm': r['cells'][1]['text'], 'publisher': r['cells'][2]['text'] if r['cells'][2] else '',
                   'rows': []}
            polls.append(cur)
        cur['rows'].append(r)
    out = []
    for p in polls:
        election = 'election' in (p['firm'] + ' ' + p['publisher']).lower()
        cands = []
        for k, r in enumerate(p['rows']):
            v = row_values(r)
            active = {s: x for s, x in v.items() if p['date'] >= START[s]}
            inactive = len(v) - len(active)
            cands.append((len(active) - 100 * inactive, -k, k, active))
        score, _, k, vals = max(cands)
        if election:
            vals = dict(vals, **{'RZP-Zehut': 7.0, 'Otzma': 6.0})
        out.append({'date': p['date'], 'firm': 'Election' if election else p['firm'], 'publisher': p['publisher'],
                    'vals': vals, 'row': k, 'nrows': len(p['rows']), 'src': f"{p['article']} t{p['table']}"})
    return out

if __name__ == '__main__':
    polls = build(sys.argv[1])
    json.dump(polls, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
    def fmt(v): return '' if v is None else (str(int(v)) if float(v).is_integer() else f"{v:g}")
    with open(sys.argv[3], 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['Date', 'Polling firm'] + SERIES)
        for p in polls:
            w.writerow([p['date'], p['firm']] + [fmt(p['vals'].get(s)) for s in SERIES])
    print(len(polls), 'polls;', sum(1 for p in polls if p['nrows'] > 1), 'with scenario rows;',
          sum(1 for p in polls if p['row'] > 0), 'using a non-first row')
