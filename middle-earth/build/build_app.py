"""Bundle app/index.html, app/app.js and app/data.js into one self-contained page.

python build_app.py [out.html]   (default: ../dist/middle-earth-map-painter.html)
The page is written without <html>/<head>/<body>: the artifact host adds them.
--standalone also writes a version with its own document skeleton, for opening as a local file.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, '..', 'app')


def bundle():
    page = open(os.path.join(APP, 'index.html'), encoding='utf-8').read()
    data = open(os.path.join(APP, 'data.js'), encoding='utf-8').read().replace('</', '<\\/')
    app = open(os.path.join(APP, 'app.js'), encoding='utf-8').read()
    page = page.replace('<!--DATA-->', '<script>' + data + '</script>')
    page = page.replace('<!--APP-->', '<script>' + app + '</script>')
    return page


def standalone(page):
    head, rest = page.split('<style>', 1)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            + head + '<style>:root{padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}body{margin:0}[hidden]{display:none!important}'
            + rest.replace('</style>', '</style></head><body>', 1) + '</body></html>')


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out = args[0] if args else os.path.join(HERE, '..', 'dist', 'middle-earth-map-painter.html')
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    page = bundle()
    with open(out, 'w', encoding='utf-8') as f:
        f.write(page)
    print('wrote', out, '%.2f MB' % (len(page.encode()) / 1e6))
    if '--standalone' in sys.argv:
        sa = out.replace('.html', '.standalone.html')
        with open(sa, 'w', encoding='utf-8') as f:
            f.write(standalone(page))
        print('wrote', sa)
