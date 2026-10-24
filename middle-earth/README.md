# Middle-earth Map Painter

A MapChart-style colouring map of Middle-earth in the late Third Age. Click a region to paint it at one of four levels:

| Level | Count | What it is |
| --- | ---: | --- |
| Realms | 51 | Gondor, Rohan, Mordor, Lindon, the Shire, the seas and lakes, … |
| Provinces | 207 | Anfalas, Westfold, Lebennin, the Farthings, Nurn, Gorgoroth, … |
| Districts | 978 | Named places (Edoras, Pelargir, Hobbiton, …), river vales, highlands and compass divisions |
| Grid | 6,393 | Small cells inside every district, for the finest detail |

Borders follow the rivers, coasts, forest edges and mountain feet of the base map, so the colours sit on it without seams. Below the province level the divisions follow the land, not canon.

The page has a legend you can name, undo and redo, search, quick fills (every realm, province or district in distinct colours, or the War of the Ring), map files and map codes for saving and sharing, and PNG or SVG export with an optional title and legend.

## Base map

The base art and coastlines come from *Map of Middle-Earth, 3rd Age*: physical design by Chris Taylor, political designations by Chris Guerette, based on the works of J.R.R. Tolkien. It is free for personal use, so this repository holds only the code and the region definitions. The PDF, everything extracted from it (`build/.cache/`, `app/data.js`) and the bundled page (`dist/`) stay out of git.

## Building

Needs Python 3 with `pymupdf`, `shapely`, `scipy`, `numpy` and `networkx`.

```sh
cd middle-earth/build
python extract.py path/to/Map-of-Middle-Earth-3RD-Age.pdf   # vector layers, coast, rivers, forests, ranges, labels
python build_regions.py --cells                               # realms, provinces, districts and grid cells
python export.py                                              # app/data.js
python build_app.py --standalone                              # dist/middle-earth-map-painter(.standalone).html
```

`dist/middle-earth-map-painter.standalone.html` opens directly in a browser. The other file is the same page without the document skeleton, for hosting as an artifact.

## How the regions are made

- `defs.py` lists the realms and provinces, each grown from a few seed points, plus the border network: rivers and forest or mountain outlines taken from the map by reference, and a few hand-drawn lines (the Shire and its farthings, Mordor's open eastern side).
- `build_regions.py` cuts the land and sea along that network, shares each compartment out between the seeds inside it with wiggly Voronoi borders, then splits every province into districts: first along rivers, forest edges and mountain feet, then evenly, with named places (`HINTS`) as seeds of their own. Districts without a place name are named after a river they follow or their compass direction. The grid is a relaxed Voronoi tiling of each district.
- `dbg.py x0 y0 x1 y1 out.png 25 1600 regions,seeds,dnames` draws the current borders over the map for checking; `where.py` prints a land and water mask.
