"""Parse the seat-projection poll tables of the Wikipedia articles (Parsoid HTML from action=render)."""
import re, json, sys
from bs4 import BeautifulSoup, NavigableString, Tag

def cell_text(td):
    # drop references / footnote markers
    td = BeautifulSoup(str(td), 'lxml').find(['td','th'])
    for sup in td.find_all('sup'):
        sup.decompose()
    for st in td.find_all('style'):
        st.decompose()
    t = td.get_text(' ', strip=True)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def expand(table):
    """Return list of rows; each row is list of dicts (one per grid column)."""
    rows = []
    pending = {}  # col -> (cell dict, remaining rows)
    trs = table.find_all('tr')
    for r_i, tr in enumerate(trs):
        cells = [c for c in tr.find_all(['td','th'], recursive=False)]
        row = {}
        col = 0
        def skip_pending():
            nonlocal col
            while col in pending:
                cd, rem = pending[col]
                row[col] = dict(cd, dup='row')
                if rem - 1 <= 0: del pending[col]
                else: pending[col] = (cd, rem - 1)
                col += 1
        for c in cells:
            skip_pending()
            cs = int(re.sub(r'\D', '', c.get('colspan', '1')) or 1)
            rs = int(re.sub(r'\D', '', c.get('rowspan', '1')) or 1)
            cd = {'tag': c.name, 'text': cell_text(c), 'colspan': cs, 'rowspan': rs,
                  'sort': c.get('data-sort-value'), 'style': c.get('style', ''), 'id': c.get('id'), 'dup': None}
            for k in range(cs):
                row[col] = dict(cd, dup=('col' if k > 0 else None), sub=k)
                if rs > 1:
                    pending[col] = (dict(cd, sub=k), rs - 1)
                col += 1
        skip_pending()
        # trailing pending beyond last cell
        while pending and max(pending) >= col:
            skip_pending()
            if col not in pending and pending and max(pending) > col:
                col += 1
            elif col not in pending:
                break
        if row:
            n = max(row) + 1
            rows.append([row.get(i) for i in range(n)])
        else:
            rows.append([])
    return rows

def parse_article(fn, label):
    soup = BeautifulSoup(open(fn).read(), 'lxml')
    out = []
    # walk all elements in document order to know section headings
    tables = []
    heading = []
    for el in soup.find_all(['h2', 'h3', 'h4', 'table']):
        if el.name in ('h2', 'h3', 'h4'):
            lvl = int(el.name[1])
            heading = heading[:lvl - 2] + [el.get_text(' ', strip=True)]
        elif 'wikitable' in (el.get('class') or []):
            tables.append((list(heading), el))
    t_i = 0
    for head, tb in tables:
        if not head or 'Seat projections' not in head[0]:
            continue
        rows = expand(tb)
        # header rows = rows consisting only of th
        hdr = []
        body = []
        for r in rows:
            if r and all(c is not None and c['tag'] == 'th' for c in r) and not body:
                hdr.append(r)
            else:
                body.append(r)
        if not hdr:
            continue
        t_i += 1
        ncol = max(len(r) for r in hdr)
        names = []
        for j in range(ncol):
            c = hdr[0][j] if j < len(hdr[0]) else None
            nm = c['text'] if c else ''
            subs = []
            for h in hdr[1:]:
                cc = h[j] if j < len(h) else None
                if cc and cc['dup'] != 'row' and cc['text'] and cc['text'] != nm:
                    subs.append(cc['text'])
            if subs:
                nm = nm + '/' + subs[0]
            elif c and c['colspan'] > 1:
                nm = f"{nm}#{c.get('sub',0)+1}"
            names.append(nm)
        for r_i, r in enumerate(body):
            if not r:
                continue
            rec = {'article': label, 'table': t_i, 'section': ' / '.join(head), 'row': r_i, 'cols': names, 'cells': r}
            out.append(rec)
    return out

if __name__ == '__main__':
    allrecs = []
    for fn, label in [('main.render.html', '2026'), ('y2025.render.html', '2025'), ('y2024.render.html', '2024'), ('y2022_23.render.html', '2022-23')]:
        recs = parse_article(sys.argv[1] + '/' + fn, label)
        allrecs += recs
        print(label, len(recs), file=sys.stderr)
    json.dump(allrecs, open(sys.argv[2], 'w'), ensure_ascii=False)
