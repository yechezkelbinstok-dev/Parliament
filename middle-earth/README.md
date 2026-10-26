# Middle-earth Map Painter

A MapChart-style colouring map of Middle-earth in the late Third Age. Click a region to paint it at one of four levels:

| Level | Count | What it is |
| --- | ---: | --- |
| Realms | 50 | Gondor, Rohan, Mordor, Lindon, the Shire, the seas and lakes, … |
| Provinces | 154 | Anfalas, Westfold, Lebennin, the Farthings, Nurn, Gorgoroth, … |
| Districts | 741 | Named places (Edoras, Pelargir, Hobbiton, …), river vales, woods, hills, coasts and compass divisions |
| Grid | 6,375 | Small cells inside every district, for the finest detail |

Realm and province borders follow the lore: rivers, mountain crests and feet, forest eaves, roads and coasts named as borders in the books (the Isen and the Adorn for Rohan's west, the Mering Stream between Rohan and Gondor, the crest of the Ephel Dúath for Mordor, …), with a drawn line only where no feature is given. They sit on the base map's own rivers, coasts and outlines, so the colours fit it without seams. Below the province level the divisions follow the land, not canon.

The page has a legend you can name, undo and redo, search, quick fills (every realm, province or district in distinct colours, or the War of the Ring), map files and map codes for saving and sharing, and PNG or SVG export with an optional title and legend. Region names keep clear of the map's own lettering and are left out where the map already prints them.

## Base map

The base art and coastlines come from *Map of Middle-Earth, 3rd Age*: physical design by Chris Taylor, political designations by Chris Guerette, based on the works of J.R.R. Tolkien. It is free for personal use, so this repository holds only the code and the region definitions. The PDF, everything extracted from it (`build/.cache/`, `app/data.js`) and the bundled page (`dist/`) stay out of git.

## Building

Needs Python 3 with `pymupdf`, `shapely`, `scipy`, `numpy` and `networkx`.

```sh
cd middle-earth/build
python extract.py path/to/Map-of-Middle-Earth-3RD-Age.pdf   # vector layers, coast, rivers, forests, ranges, labels
python build_regions.py --cells                               # realms, provinces, districts and grid cells
python migrate.py old.html                                    # optional: let maps saved with an earlier build open
python export.py                                              # app/data.js
python build_app.py --standalone                              # dist/middle-earth-map-painter(.standalone).html
```

`dist/middle-earth-map-painter.standalone.html` opens directly in a browser. The other file is the same page without the document skeleton, for hosting as an artifact.

## How the regions are made

- `defs.py` lists the realms and provinces, each with a few label points, and the border network (`LINES`): rivers, roads, and forest or mountain outlines taken from the map by reference, crests run along the middle of a range, and drawn lines where lore names no feature.
- `build_regions.py` turns that network into faces: every province is exactly the faces its label points fall in, and it warns about any face with no province or two, and any line that divides nothing. Only open sea is shared out by nearness. It then splits every province into districts, first along rivers, forest edges and mountain feet, then evenly, with named places (`HINTS`) as seeds of their own. Districts take the name of a place, river, wood, hill or coast in them, with compass names only as a last resort. The grid is a relaxed Voronoi tiling of each district.
- `export.py` packs the geometry for the app, with a few candidate spots for each name and the boxes of the map's own lettering, so names can be placed clear of it.
- `audit.py LEVEL x0 y0 x1 y1 out.png 1600 names` colours every unit of a level over the original map; `dbg.py x0 y0 x1 y1 out.png 25 1600 feat,net,bad` draws the map's features, the border network and any faulty faces; `where.py` prints a land and water mask.
