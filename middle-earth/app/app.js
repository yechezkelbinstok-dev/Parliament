/* Middle-earth Map Painter: colour realms, provinces, districts or grid cells on the Third Age map. */
(function () {
  'use strict';

  const D = window.ME_DATA;
  const NS = 'http://www.w3.org/2000/svg';
  const [FX0, FY0, FX1, FY1] = D.frame;
  const FW = FX1 - FX0, FH = FY1 - FY0;
  const SQMI = (250 / 315) ** 2; // the map's own scale bar: 250 miles over 315 points
  const LEVELS = ['realm', 'province', 'district', 'cell'];
  const LEVEL_LABEL = { realm: 'Realms', province: 'Provinces', district: 'Districts', cell: 'Grid' };
  const LEVEL_ONE = { realm: 'realm', province: 'province', district: 'district', cell: 'cell' };
  const STORE = 'me-map-painter-v1';
  const PAPER = '#fff9ea';

  const PALETTE = [
    '#b3261e', '#d9622b', '#e3a72f', '#7a9a2e', '#2e7d4f', '#1f7a8c', '#2f5d9b', '#5b3f8c',
    '#e8a598', '#f2b880', '#f3dc8b', '#c5d88a', '#9fd3b0', '#9ad1d4', '#a8c1e8', '#c7b3e5',
    '#6e1f1a', '#7a4a22', '#8c7a3c', '#3e5226', '#1d4733', '#24394f', '#3a3a44', '#151515',
  ];
  const SOFT = ['#e8a598', '#f2c48d', '#f3dc8b', '#c9dc8e', '#a3d4b2', '#9fd1d6', '#adc5ea', '#c9b6e6',
    '#e6b9cb', '#d8c39b', '#b8d6a0', '#f0b6a0'];

  const $ = (s) => document.querySelector(s);
  function svgEl(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    if (attrs) for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function h(tag, attrs, ...kids) {
    const e = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      if (k === 'class') e.className = attrs[k];
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), attrs[k]);
      else if (k === 'style') e.style.cssText = attrs[k];
      else e.setAttribute(k, attrs[k]);
    }
    for (const k of kids) if (k != null) e.append(k);
    return e;
  }
  const fmtInt = (n) => Math.round(n).toLocaleString('en-US');
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const norm = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

  // ---------------------------------------------------------------- model
  const N = D.cells.d.length;
  const cellDist = Int32Array.from(D.cells.d);
  const distProv = Int32Array.from(D.districts, (d) => d.p);
  const provRealm = Int32Array.from(D.provinces, (p) => p.r);
  const cellProv = new Int32Array(N), cellRealm = new Int32Array(N);
  for (let i = 0; i < N; i++) { cellProv[i] = distProv[cellDist[i]]; cellRealm[i] = provRealm[cellProv[i]]; }
  const cellArea = Float64Array.from(D.cells.a);
  const UNITS = { realm: D.realms, province: D.provinces, district: D.districts };
  const OWNER = { realm: cellRealm, province: cellProv, district: cellDist };
  const MEMBERS = {};
  for (const lv of ['realm', 'province', 'district']) {
    const lists = UNITS[lv].map(() => []);
    const own = OWNER[lv];
    for (let i = 0; i < N; i++) lists[own[i]].push(i);
    MEMBERS[lv] = lists.map((l) => Int32Array.from(l));
  }
  const cellNo = new Int32Array(N);
  MEMBERS.district.forEach((m) => m.forEach((c, k) => { cellNo[c] = k + 1; }));
  const unitOf = (lv, c) => (lv === 'cell' ? c : OWNER[lv][c]);
  const membersOf = (lv, u) => (lv === 'cell' ? Int32Array.of(u) : MEMBERS[lv][u]);
  const waterRealm = D.realms.map((r) => !!r.w);
  const isWaterUnit = (lv, u) => waterRealm[cellRealm[membersOf(lv, u)[0]]];
  const areaCache = new Map();
  function areaOf(lv, u) {
    const key = lv + u;
    if (!areaCache.has(key)) {
      let a = 0;
      for (const c of membersOf(lv, u)) a += cellArea[c];
      areaCache.set(key, a * SQMI);
    }
    return areaCache.get(key);
  }
  function unitTitle(lv, u) {
    return lv === 'cell' ? `Cell ${cellNo[u]}` : UNITS[lv][u].n;
  }
  function unitChain(lv, u) {
    const c = membersOf(lv, u)[0];
    const chain = [];
    if (lv === 'cell') chain.push(D.districts[cellDist[c]].n);
    if (lv === 'cell' || lv === 'district') chain.push(D.provinces[cellProv[c]].n);
    if (lv !== 'realm') chain.push(D.realms[cellRealm[c]].n);
    const title = unitTitle(lv, u);
    return chain.filter((n, i) => n !== title && n !== chain[i - 1]);
  }

  // ---------------------------------------------------------------- state
  const S = {
    title: 'Middle-earth',
    mode: 'province',
    tool: 'paint',
    brush: false,
    active: PALETTE[6],
    swatches: [],
    labels: {},
    cells: new Uint16Array(N),
    layers: { labels: true, places: true, political: false, terrain: true, rivers: true, roads: true, borders: 'mode', opacity: 100 },
  };
  function swatchIdx(hex) {
    hex = hex.toLowerCase();
    let i = S.swatches.indexOf(hex);
    if (i < 0) { S.swatches.push(hex); i = S.swatches.length - 1; }
    return i + 1;
  }
  const colorOf = (v) => (v ? S.swatches[v - 1] : null);

  // ---------------------------------------------------------------- svg scene
  const stage = $('#stage');
  const svg = $('#map');
  const defs = svgEl('defs', null, svg);
  D.glyphs.forEach((d, i) => svgEl('path', { id: 'g' + i, d }, defs));
  const world = svgEl('g', { id: 'world' }, svg);
  svgEl('rect', { x: FX0, y: FY0, width: FW, height: FH, fill: PAPER, 'pointer-events': 'none' }, world);

  function baseLayer(names, parent, attrs) {
    const g = svgEl('g', Object.assign({ 'pointer-events': 'none' }, attrs || {}), parent || world);
    for (const name of names) {
      for (const grp of D.base[name] || []) {
        const p = svgEl('path', { d: grp.d, transform: grp.t }, g);
        for (const k in grp.a) p.setAttribute(k, grp.a[k]);
      }
    }
    return g;
  }
  baseLayer(['water', 'island']);
  const cellsG = svgEl('g', { id: 'cells', 'pointer-events': 'all', 'stroke-width': '1.1', 'stroke-linejoin': 'round' }, world);
  const cellEls = new Array(N);
  {
    const frag = document.createDocumentFragment();
    for (let i = 0; i < N; i++) {
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', D.cells.path[i]);
      p.setAttribute('fill', 'none');
      p.setAttribute('vector-effect', 'non-scaling-stroke');
      p.__cell = i;
      frag.appendChild(p);
      cellEls[i] = p;
    }
    cellsG.appendChild(frag);
  }
  const coastG = baseLayer(['coast']);
  const riverG = baseLayer(['river']);
  const terrainG = svgEl('g', { 'pointer-events': 'none', style: 'mix-blend-mode:multiply' }, world);
  const mountG = baseLayer(['mountain', 'forest', 'marsh'], terrainG);
  const roadG = baseLayer(['road'], terrainG);
  baseLayer(['symbol'], terrainG);

  const EDGE = {
    realm_l: { w: 1.6, o: 0.92, c: '#2a211b' }, province_l: { w: 0.95, o: 0.78, c: '#2a211b' },
    district_l: { w: 0.6, o: 0.55, c: '#2a211b' }, cell_l: { w: 0.4, o: 0.38, c: '#2a211b' },
    realm_w: { w: 1.1, o: 0.6, c: '#245b85', dash: '6 3' }, province_w: { w: 0.85, o: 0.5, c: '#245b85', dash: '4 3' },
    district_w: { w: 0.6, o: 0.4, c: '#245b85', dash: '2 3' }, cell_w: { w: 0.4, o: 0.3, c: '#245b85', dash: '1 2' },
  };
  const edgeG = svgEl('g', { fill: 'none', 'pointer-events': 'none', 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }, world);
  const edgeEls = {}, caseEls = {};
  // a pale casing under realm and province lines keeps them readable on dark colours
  for (const key of ['province_l', 'realm_l']) {
    if (!D.edges[key]) continue;
    caseEls[key] = svgEl('path', {
      d: D.edges[key], stroke: PAPER, 'stroke-width': EDGE[key].w + 1.8, 'stroke-opacity': key === 'realm_l' ? 0.55 : 0.4,
      'vector-effect': 'non-scaling-stroke',
    }, edgeG);
  }
  for (const key of ['cell_w', 'district_w', 'province_w', 'realm_w', 'cell_l', 'district_l', 'province_l', 'realm_l']) {
    if (!D.edges[key]) continue;
    const st = EDGE[key];
    edgeEls[key] = svgEl('path', {
      d: D.edges[key], stroke: st.c, 'stroke-width': st.w, 'stroke-opacity': st.o,
      'vector-effect': 'non-scaling-stroke', 'stroke-dasharray': st.dash || 'none',
    }, edgeG);
  }
  const hoverPath = svgEl('path', { d: '', 'pointer-events': 'none', 'fill-opacity': '0.5', fill: '#000' }, world);

  function glyphLayer(kind, parent) {
    const g = svgEl('g', { 'pointer-events': 'none' }, parent || world);
    const frag = document.createDocumentFragment();
    for (const L of D.labels[kind] || []) {
      for (const u of L.u) {
        const e = document.createElementNS(NS, 'use');
        e.setAttribute('href', '#g' + u[0]);
        e.setAttribute('transform', 'matrix(' + u.slice(1).join(',') + ')');
        e.setAttribute('fill', L.f);
        frag.appendChild(e);
      }
    }
    g.appendChild(frag);
    return g;
  }
  const placeG = glyphLayer('place');
  // the map's own region and realm lettering, which the painted labels replace
  const politicalG = svgEl('g', { 'pointer-events': 'none' }, world);
  glyphLayer('region', politicalG);
  glyphLayer('political', politicalG);
  const regionLabelRoot = svgEl('g', { 'pointer-events': 'none' }, world);
  const decorG = baseLayer(['decor']);
  glyphLayer('decor', decorG);
  baseLayer(['frame']);

  // ---------------------------------------------------------------- region labels
  const measure = document.createElement('canvas').getContext('2d');
  const LABEL_FONT = {
    realm: { font: '700 100px "Alegreya SC", Georgia, serif', track: 0.14, max: 30, upper: true },
    province: { font: '500 100px "Alegreya SC", Georgia, serif', track: 0.06, max: 13 },
    district: { font: 'italic 500 100px "Alegreya", Georgia, serif', track: 0, max: 6.5 },
  };
  const labelGroups = {};
  function labelSize(lv, name, l) {
    const f = LABEL_FONT[lv];
    measure.font = f.font;
    const per = measure.measureText(name).width / 100 + f.track * Math.max(0, name.length - 1);
    const [, , r, w] = l;
    return Math.max(0.5, Math.min(f.max, (w * 0.88) / per, r * 1.55));
  }
  function buildLabels(lv) {
    if (labelGroups[lv]) labelGroups[lv].remove();
    const g = svgEl('g', null, regionLabelRoot);
    labelGroups[lv] = g;
    if (lv === 'cell') return g;
    const f = LABEL_FONT[lv];
    const frag = document.createDocumentFragment();
    UNITS[lv].forEach((unit, i) => {
      const name = f.upper ? unit.n.toUpperCase() : unit.n;
      const fs = labelSize(lv, name, unit.l);
      const t = document.createElementNS(NS, 'text');
      t.setAttribute('x', unit.l[0]);
      t.setAttribute('y', unit.l[1]);
      t.setAttribute('font-size', fs.toFixed(2));
      t.setAttribute('stroke-width', (fs * 0.2).toFixed(2));
      t.setAttribute('text-anchor', 'middle');
      t.setAttribute('dominant-baseline', 'central');
      t.setAttribute('class', `rlab ${lv}` + (isWaterUnit(lv, i) ? ' water' : ''));
      t.__dup = lv === 'realm' && isWaterUnit(lv, i); // the map already letters its seas and lakes
      t.textContent = name;
      t.__fs = fs;
      frag.appendChild(t);
    });
    g.appendChild(frag);
    return g;
  }
  function updateLabelVis() {
    for (const lv in labelGroups) labelGroups[lv].style.display = (lv === S.mode && S.layers.labels) ? '' : 'none';
    const g = labelGroups[S.mode];
    if (!g || !S.layers.labels) return;
    const k = cam.k;
    for (const t of g.children) {
      const px = t.__fs * k;
      t.style.display = px >= 7.5 && px <= 160 && !(t.__dup && S.layers.places) ? '' : 'none';
    }
  }

  // ---------------------------------------------------------------- camera
  let vw = 1, vh = 1;
  let cam = { x: FX0, y: FY0, k: 1 };
  let live = { ...cam };
  let fitK = 1;
  const MAXK = 10;
  function measureStage() {
    const r = stage.getBoundingClientRect();
    vw = Math.max(1, r.width); vh = Math.max(1, r.height);
    fitK = Math.min(vw / FW, vh / FH);
  }
  function fitView() {
    measureStage();
    const k = fitK * 0.98;
    live = { k, x: FX0 + FW / 2 - vw / 2 / k, y: FY0 + FH / 2 - vh / 2 / k };
    commitView();
  }
  function clampLive() {
    live.k = clamp(live.k, fitK * 0.6, MAXK);
    const w = vw / live.k, hh = vh / live.k;
    const mx = Math.min(w * 0.5, FW * 0.5), my = Math.min(hh * 0.5, FH * 0.5);
    live.x = clamp(live.x, FX0 - w + mx, FX1 - mx);
    live.y = clamp(live.y, FY0 - hh + my, FY1 - my);
  }
  let commitTimer = 0;
  function showLive(commitAfter) {
    clampLive();
    const s = live.k / cam.k;
    const tx = (cam.x - live.x) * live.k, ty = (cam.y - live.y) * live.k;
    svg.style.transform = `translate(${tx}px, ${ty}px) scale(${s})`;
    clearTimeout(commitTimer);
    if (commitAfter !== false) commitTimer = setTimeout(commitView, commitAfter || 170);
  }
  function commitView() {
    clearTimeout(commitTimer);
    clampLive();
    cam = { ...live };
    svg.setAttribute('viewBox', `${cam.x} ${cam.y} ${vw / cam.k} ${vh / cam.k}`);
    svg.style.transform = '';
    scaleBorders();
    updateLabelVis();
  }
  // lines thin out when the whole map is squeezed onto a small screen
  let borderF = 0;
  function scaleBorders() {
    const f = Math.round(clamp(Math.sqrt(cam.k / 0.45), 0.5, 1.15) * 20) / 20;
    if (f === borderF) return;
    borderF = f;
    for (const key in edgeEls) edgeEls[key].setAttribute('stroke-width', (EDGE[key].w * f).toFixed(2));
    for (const key in caseEls) caseEls[key].setAttribute('stroke-width', ((EDGE[key].w + 1.8) * f).toFixed(2));
  }
  function zoomAt(clientX, clientY, f, commitAfter) {
    const r = stage.getBoundingClientRect();
    const px = clientX - r.left, py = clientY - r.top;
    const mx = live.x + px / live.k, my = live.y + py / live.k;
    live.k = clamp(live.k * f, fitK * 0.6, MAXK);
    live.x = mx - px / live.k; live.y = my - py / live.k;
    showLive(commitAfter);
  }
  function zoomCenter(f) {
    const r = stage.getBoundingClientRect();
    zoomAt(r.left + r.width / 2, r.top + r.height / 2, f, 260);
  }
  function zoomTo(box) {
    measureStage();
    const pad = 1.35;
    const k = clamp(Math.min(vw / (box.width * pad), vh / (box.height * pad)), fitK, Math.min(MAXK, fitK * 14));
    live = { k, x: box.x + box.width / 2 - vw / 2 / k, y: box.y + box.height / 2 - vh / 2 / k };
    commitView();
  }

  // ---------------------------------------------------------------- painting & history
  const undoStack = [], redoStack = [];
  function setCells(idx, vals) {
    for (let k = 0; k < idx.length; k++) {
      const c = idx[k];
      S.cells[c] = vals[k];
      const col = colorOf(vals[k]);
      const e = cellEls[c];
      if (col) { e.setAttribute('fill', col); e.setAttribute('stroke', col); }
      else { e.setAttribute('fill', 'none'); e.setAttribute('stroke', 'none'); }
    }
  }
  function change(idx, val, label) {
    const keep = [], before = [], after = [];
    for (let k = 0; k < idx.length; k++) {
      const c = idx[k];
      const nv = typeof val === 'number' ? val : val[k];
      if (S.cells[c] !== nv) { keep.push(c); before.push(S.cells[c]); after.push(nv); }
    }
    if (!keep.length) return false;
    const rec = { idx: Int32Array.from(keep), before: Uint16Array.from(before), after: Uint16Array.from(after), label };
    setCells(rec.idx, rec.after);
    undoStack.push(rec);
    if (undoStack.length > 300) undoStack.shift();
    redoStack.length = 0;
    changed();
    return true;
  }
  function undo() {
    const rec = undoStack.pop();
    if (!rec) return;
    if (rec.recolor) { S.swatches[rec.recolor.v - 1] = rec.recolor.from; repaintAll(); }
    else setCells(rec.idx, rec.before);
    redoStack.push(rec);
    changed();
    note(`Undid ${rec.label || 'the last change'}`);
  }
  function redo() {
    const rec = redoStack.pop();
    if (!rec) return;
    if (rec.recolor) { S.swatches[rec.recolor.v - 1] = rec.recolor.to; repaintAll(); }
    else setCells(rec.idx, rec.after);
    undoStack.push(rec);
    changed();
    note(`Redid ${rec.label || 'the change'}`);
  }
  function repaintAll() {
    const idx = new Int32Array(N);
    for (let i = 0; i < N; i++) idx[i] = i;
    setCells(idx, S.cells.slice());
    hoverKey = null;
  }
  let legendQueued = false;
  function changed() {
    $('#undo').disabled = !undoStack.length;
    $('#redo').disabled = !redoStack.length;
    if (!legendQueued) { legendQueued = true; requestAnimationFrame(() => { legendQueued = false; renderLegend(); }); }
    scheduleSave();
  }

  function actOn(c, ev) {
    const lv = S.mode;
    const u = unitOf(lv, c);
    const cs = membersOf(lv, u);
    const name = unitTitle(lv, u);
    if (S.tool === 'pick' || ev.altKey) {
      const v = S.cells[c];
      if (v) { setActive(colorOf(v)); note(`Picked the colour of <b>${esc(name)}</b>`); }
      else note(`<b>${esc(name)}</b> has no colour yet`);
      if (S.tool === 'pick') setTool('paint');
      return;
    }
    let val = (S.tool === 'erase' || ev.button === 2) ? 0 : swatchIdx(S.active);
    if (val) {
      let same = true;
      for (const x of cs) if (S.cells[x] !== val) { same = false; break; }
      if (same) val = 0; // clicking a region already in this colour clears it
    }
    const did = change(cs, val, name);
    if (did) {
      const chain = unitChain(lv, u);
      note(`${val ? 'Painted' : 'Cleared'} <b>${esc(name)}</b>${chain.length ? ' · ' + esc(chain.join(' · ')) : ''}`);
    }
    hoverKey = null;
  }

  // brush strokes collect into one undo step
  let stroke = null;
  function brushStart() { stroke = { before: new Map(), val: S.tool === 'erase' ? 0 : swatchIdx(S.active), units: new Set() }; }
  function brushAt(c) {
    if (!stroke || c == null) return;
    const lv = S.mode, u = unitOf(lv, c);
    if (stroke.units.has(u)) return;
    stroke.units.add(u);
    const cs = membersOf(lv, u);
    const vals = [];
    for (const x of cs) { if (!stroke.before.has(x)) stroke.before.set(x, S.cells[x]); vals.push(stroke.val); }
    setCells(cs, vals);
  }
  function brushEnd() {
    if (!stroke) return;
    const idx = [], before = [], after = [];
    for (const [c, b] of stroke.before) if (b !== S.cells[c]) { idx.push(c); before.push(b); after.push(S.cells[c]); }
    if (idx.length) {
      undoStack.push({ idx: Int32Array.from(idx), before: Uint16Array.from(before), after: Uint16Array.from(after), label: 'the brush stroke' });
      redoStack.length = 0;
      changed();
      note(`${stroke.val ? 'Painted' : 'Cleared'} ${stroke.units.size} ${LEVEL_ONE[S.mode]}${stroke.units.size === 1 ? '' : 's'} with the brush`);
    }
    stroke = null;
  }

  // ---------------------------------------------------------------- hover & tooltip
  const tip = $('#tip');
  let hoverKey = null;
  const pathCache = new Map();
  function unitPath(lv, u) {
    if (lv === 'cell') return D.cells.path[u];
    const key = lv + u;
    let p = pathCache.get(key);
    if (!p) {
      const parts = [];
      for (const c of MEMBERS[lv][u]) parts.push(D.cells.path[c]);
      p = parts.join('');
      if (pathCache.size > 400) pathCache.clear();
      pathCache.set(key, p);
    }
    return p;
  }
  function hoverFill() {
    if (S.tool === 'erase') return '#ffffff';
    if (S.tool === 'pick') return '#ffffff';
    return S.active;
  }
  function setHover(c, clientX, clientY) {
    if (c == null) { if (hoverKey !== null) { hoverPath.setAttribute('d', ''); hoverKey = null; } tip.hidden = true; return; }
    const lv = S.mode, u = unitOf(lv, c), key = lv + ':' + u;
    if (key !== hoverKey) {
      hoverKey = key;
      hoverPath.setAttribute('d', unitPath(lv, u));
      hoverPath.setAttribute('fill', hoverFill());
      hoverPath.setAttribute('fill-opacity', S.tool === 'paint' ? '0.55' : '0.45');
      const chain = unitChain(lv, u);
      const v = S.cells[c];
      const painted = v ? (S.labels[colorOf(v)] || '') : '';
      tip.innerHTML = `<b>${esc(unitTitle(lv, u))}</b>` + (chain.length ? `<span>${esc(chain.join(' · '))}</span>` : '') +
        `<em>≈ ${fmtInt(areaOf(lv, u))} sq mi${painted ? ' · ' + esc(painted) : ''}</em>`;
    }
    if (clientX != null) {
      tip.hidden = false;
      const r = stage.getBoundingClientRect();
      let x = clientX - r.left + 16, y = clientY - r.top + 18;
      const tw = tip.offsetWidth, th = tip.offsetHeight;
      if (x + tw > r.width - 8) x = clientX - r.left - tw - 14;
      if (y + th > r.height - 8) y = clientY - r.top - th - 14;
      tip.style.left = x + 'px';
      tip.style.top = y + 'px';
    }
  }
  function cellAt(clientX, clientY) {
    const t = document.elementFromPoint(clientX, clientY);
    return t && t.__cell != null ? t.__cell : null;
  }

  // ---------------------------------------------------------------- pointer input
  const pointers = new Map();
  let gest = null;
  stage.addEventListener('contextmenu', (e) => { if (!e.target.closest('.float')) e.preventDefault(); });
  stage.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.float')) return;
    if (e.button === 1) return;
    stage.setPointerCapture(e.pointerId);
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (pointers.size === 1) {
      gest = { kind: 'press', sx: e.clientX, sy: e.clientY, lx: e.clientX, ly: e.clientY, moved: false, button: e.button,
        cell: cellAt(e.clientX, e.clientY), brush: S.brush && e.button === 0 && S.tool !== 'pick', type: e.pointerType };
      if (gest.brush) { brushStart(); brushAt(gest.cell); }
    } else if (pointers.size === 2) {
      if (gest && gest.brush) brushEnd();
      const [a, b] = [...pointers.values()];
      gest = { kind: 'pinch', d: Math.hypot(a.x - b.x, a.y - b.y), cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2 };
      hoverPath.setAttribute('d', ''); hoverKey = null; tip.hidden = true;
    }
  });
  stage.addEventListener('pointermove', (e) => {
    if (!pointers.has(e.pointerId)) {
      if (e.pointerType === 'mouse' && !e.target.closest('.float')) setHover(cellAt(e.clientX, e.clientY), e.clientX, e.clientY);
      return;
    }
    pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (!gest) return;
    if (gest.kind === 'pinch' && pointers.size >= 2) {
      const [a, b] = [...pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
      live.x -= (cx - gest.cx) / live.k; live.y -= (cy - gest.cy) / live.k;
      zoomAt(cx, cy, d / gest.d, false);
      gest.d = d; gest.cx = cx; gest.cy = cy;
      return;
    }
    if (gest.kind !== 'press') return;
    const dist = Math.hypot(e.clientX - gest.sx, e.clientY - gest.sy);
    if (!gest.moved && dist > (e.pointerType === 'mouse' ? 4 : 9)) {
      gest.moved = true;
      if (!gest.brush) { stage.classList.add('panning'); setHover(null); }
    }
    if (gest.brush) { brushAt(cellAt(e.clientX, e.clientY)); return; }
    if (gest.moved) {
      live.x -= (e.clientX - gest.lx) / live.k;
      live.y -= (e.clientY - gest.ly) / live.k;
      gest.lx = e.clientX; gest.ly = e.clientY;
      showLive(false);
      // when the drag has uncovered much of the screen, re-render to fill the gap
      if (Math.abs(live.x - cam.x) * live.k > vw * 0.35 || Math.abs(live.y - cam.y) * live.k > vh * 0.35) commitView();
    }
  });
  function endPointer(e) {
    if (!pointers.has(e.pointerId)) return;
    pointers.delete(e.pointerId);
    if (!gest) return;
    if (gest.kind === 'press') {
      if (gest.brush) brushEnd();
      else if (!gest.moved && e.type === 'pointerup' && gest.cell != null) {
        actOn(gest.cell, { button: gest.button, altKey: e.altKey });
        if (e.pointerType === 'mouse') setHover(gest.cell, e.clientX, e.clientY);
      }
      stage.classList.remove('panning');
      if (gest.moved) commitView();
      gest = null;
    } else if (gest.kind === 'pinch' && pointers.size < 2) {
      commitView();
      gest = pointers.size === 1 ? { kind: 'press', sx: 0, sy: 0, lx: [...pointers.values()][0].x, ly: [...pointers.values()][0].y, moved: true, cell: null } : null;
    }
  }
  stage.addEventListener('pointerup', endPointer);
  stage.addEventListener('pointercancel', endPointer);
  stage.addEventListener('pointerleave', (e) => { if (e.pointerType === 'mouse' && !pointers.size) setHover(null); });
  stage.addEventListener('wheel', (e) => {
    if (e.target.closest('.float')) return;
    e.preventDefault();
    const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? 400 : 1;
    const dy = e.deltaY * unit;
    zoomAt(e.clientX, e.clientY, Math.exp(-dy * (e.ctrlKey ? 0.012 : 0.0022)));
  }, { passive: false });
  $('#zin').onclick = () => zoomCenter(1.6);
  $('#zout').onclick = () => zoomCenter(1 / 1.6);
  $('#zfit').onclick = () => fitView();
  window.addEventListener('resize', () => {
    const cx = live.x + vw / 2 / live.k, cy = live.y + vh / 2 / live.k;
    const was = fitK;
    measureStage();
    live.k = live.k * (fitK / was);
    live.x = cx - vw / 2 / live.k; live.y = cy - vh / 2 / live.k;
    commitView();
  });

  // ---------------------------------------------------------------- status & toast
  const statusEl = $('#status');
  function esc(s) { return String(s).replace(/[&<>"]/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[m]); }
  function note(html) { statusEl.innerHTML = html; }
  let toastTimer = 0;
  function toast(msg) {
    const t = $('#toast');
    t.textContent = msg;
    t.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.hidden = true; }, 2600);
  }

  // ---------------------------------------------------------------- modes, tools, palette
  const modesEl = $('#modes');
  const counts = { realm: D.realms.length, province: D.provinces.length, district: D.districts.length, cell: N };
  for (const lv of LEVELS) {
    modesEl.append(h('button', { 'data-mode': lv, 'aria-pressed': 'false', title: `Paint whole ${LEVEL_ONE[lv]}s (${LEVELS.indexOf(lv) + 1})`, onclick: () => setMode(lv) },
      h('b', null, LEVEL_LABEL[lv]), h('span', null, fmtInt(counts[lv]))));
  }
  function setMode(lv) {
    S.mode = lv;
    for (const b of modesEl.children) b.setAttribute('aria-pressed', String(b.dataset.mode === lv));
    if (!labelGroups[lv]) buildLabels(lv);
    updateEdges();
    updateLabelVis();
    hoverKey = null; hoverPath.setAttribute('d', '');
    note(`Painting whole <b>${LEVEL_ONE[lv]}s</b>. ${lv === 'cell' ? 'The grid splits every district into small cells.' : ''}`);
    scheduleSave();
  }
  function updateEdges() {
    const m = S.layers.borders, depth = LEVELS.indexOf(S.mode);
    for (const key in edgeEls) {
      const i = LEVELS.indexOf(key.split('_')[0]);
      const show = m === 'all' || (m === 'mode' && i <= depth) || (m === 'realm' && i === 0);
      edgeEls[key].style.display = show ? '' : 'none';
      if (caseEls[key]) caseEls[key].style.display = show ? '' : 'none';
    }
  }
  function setTool(t) {
    S.tool = t;
    for (const b of document.querySelectorAll('.tool[data-tool]')) b.setAttribute('aria-pressed', String(b.dataset.tool === t));
    hoverKey = null;
  }
  for (const b of document.querySelectorAll('.tool[data-tool]')) b.onclick = () => setTool(b.dataset.tool);
  const brushBtn = $('#brushBtn');
  function setBrush(on) { S.brush = on; brushBtn.setAttribute('aria-pressed', String(on)); note(on ? 'Brush on: drag across the map to paint. Use two fingers or the zoom buttons to move.' : 'Brush off: drag moves the map.'); }
  brushBtn.onclick = () => setBrush(!S.brush);

  const swEl = $('#swatches'), mini = $('#miniSwatches');
  function colorName(hex) {
    const label = S.labels[hex];
    return label ? `${label} (${hex})` : hex;
  }
  function renderPalette() {
    swEl.textContent = '';
    mini.textContent = '';
    const extra = S.swatches.filter((c) => !PALETTE.includes(c));
    for (const c of PALETTE.concat(extra.slice(-8))) {
      const mk = () => h('button', { class: 'sw', style: `background:${c}`, 'aria-pressed': String(c === S.active), 'aria-label': colorName(c), title: colorName(c), onclick: () => { setActive(c); if (S.tool !== 'paint') setTool('paint'); } });
      swEl.append(mk());
    }
    for (const c of PALETTE.slice(0, 8).concat(PALETTE.slice(16, 18))) {
      mini.append(h('button', { class: 'sw', style: `background:${c}`, 'aria-pressed': String(c === S.active), 'aria-label': c, onclick: () => { setActive(c); if (S.tool !== 'paint') setTool('paint'); } }));
    }
    $('#activeName').innerHTML = `<span class="current"><i style="background:${S.active}"></i>${esc(S.labels[S.active] || S.active)}</span>`;
    $('#customColor').value = S.active;
  }
  function setActive(c) {
    S.active = c.toLowerCase();
    renderPalette();
    hoverKey = null;
    scheduleSave();
  }
  $('#customColor').addEventListener('input', (e) => setActive(e.target.value));

  // ---------------------------------------------------------------- legend
  const legendEl = $('#legend');
  function legendData() {
    const area = new Float64Array(S.swatches.length + 1);
    const realmArea = new Map();
    for (let i = 0; i < N; i++) {
      const v = S.cells[i];
      if (!v) continue;
      area[v] += cellArea[i];
      const key = v * 1000 + cellRealm[i];
      realmArea.set(key, (realmArea.get(key) || 0) + cellArea[i]);
    }
    const rows = [];
    for (let v = 1; v <= S.swatches.length; v++) {
      if (area[v] <= 0) continue;
      let best = -1, ba = 0;
      for (let r = 0; r < D.realms.length; r++) { const a = realmArea.get(v * 1000 + r) || 0; if (a > ba) { ba = a; best = r; } }
      rows.push({ v, hex: S.swatches[v - 1], area: area[v] * SQMI, hint: best >= 0 ? D.realms[best].n : '' });
    }
    return rows;
  }
  function renderLegend() {
    const rows = legendData();
    const focused = document.activeElement && document.activeElement.closest && document.activeElement.closest('#legend') ? document.activeElement.dataset.hex : null;
    legendEl.textContent = '';
    let total = 0;
    for (const r of rows) {
      total += r.area;
      const input = h('input', { type: 'text', value: S.labels[r.hex] || '', placeholder: r.hint ? `Name it, e.g. ${r.hint}` : 'Name this colour', 'aria-label': 'Legend name for ' + r.hex, 'data-hex': r.hex, maxlength: '60' });
      input.addEventListener('input', () => { S.labels[r.hex] = input.value; scheduleSave(); });
      input.addEventListener('change', () => renderPalette());
      const recolor = h('input', { type: 'color', class: 'recolor', value: r.hex, 'aria-label': 'Change this colour everywhere' });
      recolor.addEventListener('change', () => recolorSwatch(r.v, recolor.value));
      legendEl.append(h('li', null,
        h('button', { class: 'sw', style: `background:${r.hex}`, title: 'Paint with this colour', 'aria-label': 'Paint with ' + (S.labels[r.hex] || r.hex), onclick: () => { setActive(r.hex); setTool('paint'); } }),
        input,
        h('span', { class: 'meta' }, `${fmtInt(r.area)} sq mi`, h('br'),
          h('label', { style: 'position:relative;display:inline-block;cursor:pointer;color:var(--accent)' }, 'recolour', recolor))));
      if (focused === r.hex) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); }
    }
    $('#legendEmpty').hidden = rows.length > 0;
    $('#legendTotal').textContent = rows.length ? `${rows.length} colour${rows.length === 1 ? '' : 's'} · ${fmtInt(total)} sq mi` : '';
  }
  function recolorSwatch(v, hex) {
    hex = hex.toLowerCase();
    const from = S.swatches[v - 1];
    if (hex === from) return;
    const other = S.swatches.indexOf(hex);
    if (other >= 0) {
      const idx = [];
      for (let i = 0; i < N; i++) if (S.cells[i] === v) idx.push(i);
      change(idx, other + 1, 'the recolour');
    } else {
      S.swatches[v - 1] = hex;
      if (S.labels[from] && !S.labels[hex]) { S.labels[hex] = S.labels[from]; }
      repaintAll();
      undoStack.push({ recolor: { v, from, to: hex }, label: 'the recolour' });
      redoStack.length = 0;
      changed();
    }
    if (S.active === from) setActive(hex); else renderPalette();
  }

  // ---------------------------------------------------------------- quick fills
  function graphColor(lv, palette) {
    const units = UNITS[lv];
    const adj = units.map(() => new Set());
    const flat = D.adj[lv] || [];
    for (let i = 0; i < flat.length; i += 2) { adj[flat[i]].add(flat[i + 1]); adj[flat[i + 1]].add(flat[i]); }
    const order = units.map((_, i) => i).filter((i) => !isWaterUnit(lv, i)).sort((a, b) => adj[b].size - adj[a].size);
    const col = new Map();
    const used = new Array(palette.length).fill(0);
    for (const u of order) {
      const taken = new Set();
      for (const n of adj[u]) if (col.has(n)) taken.add(col.get(n));
      let best = -1;
      for (let k = 0; k < palette.length; k++) if (!taken.has(k) && (best < 0 || used[k] < used[best])) best = k;
      if (best < 0) best = u % palette.length;
      col.set(u, best); used[best]++;
    }
    const vals = new Uint16Array(N);
    const idxs = palette.map((c) => swatchIdx(c));
    for (const [u, k] of col) for (const c of MEMBERS[lv][u]) vals[c] = idxs[k];
    return vals;
  }
  const WAR = {
    free: ['gondor', 'rohan', 'lorien', 'woodland_realm', 'dale', 'erebor', 'iron_hills', 'shire', 'lindon', 'imladris', 'druedain', 'fangorn', 'woodmen', 'anduin_vales', 'bree', 'ered_luin'],
    shadow: ['mordor', 'isengard', 'dol_guldur', 'gundabad', 'near_harad', 'khand', 'rhun', 'dunland', 'harondor', 'hithaeglir', 'moria'],
  };
  function warVals() {
    const vals = new Uint16Array(N);
    const a = swatchIdx('#2f5d9b'), b = swatchIdx('#6e1f1a');
    S.labels['#2f5d9b'] = S.labels['#2f5d9b'] || 'Free Peoples';
    S.labels['#6e1f1a'] = S.labels['#6e1f1a'] || 'Sauron and his allies';
    D.realms.forEach((r, i) => {
      const v = WAR.free.includes(r.id) ? a : WAR.shadow.includes(r.id) ? b : 0;
      if (v) for (const c of MEMBERS.realm[i]) vals[c] = v;
    });
    return vals;
  }
  function fillAll(vals, label) {
    const idx = new Int32Array(N);
    for (let i = 0; i < N; i++) idx[i] = i;
    change(idx, vals, label);
    renderPalette();
  }
  for (const b of document.querySelectorAll('[data-fill]')) {
    b.onclick = () => {
      const k = b.dataset.fill;
      if (k === 'war') {
        fillAll(warVals(), 'the War of the Ring fill');
        if (/^Middle-earth$/.test(S.title)) setTitle('War of the Ring, T.A. 3019');
        note('Filled the realms by their side in the War of the Ring. Unaligned lands stay blank.');
      } else {
        fillAll(graphColor(k, SOFT), `the ${k} fill`);
        if (S.mode !== k) setMode(k);
        note(`Gave every ${k} a colour, with no two neighbours alike.`);
      }
    };
  }
  const clearBtn = $('#clearBtn');
  let clearArmed = 0;
  clearBtn.onclick = () => {
    if (Date.now() - clearArmed < 3500) {
      fillAll(new Uint16Array(N), 'clearing the map');
      clearArmed = 0; clearBtn.textContent = 'Clear map';
      note('Cleared the map. Undo brings it back.');
    } else {
      clearArmed = Date.now(); clearBtn.textContent = 'Click again to clear';
      setTimeout(() => { if (Date.now() - clearArmed >= 3400) clearBtn.textContent = 'Clear map'; }, 3600);
    }
  };

  // ---------------------------------------------------------------- layers
  const LY = { lyLabels: 'labels', lyPlaces: 'places', lyPolitical: 'political', lyTerrain: 'terrain', lyRivers: 'rivers', lyRoads: 'roads' };
  function applyLayers() {
    const L = S.layers;
    placeG.style.display = L.places ? '' : 'none';
    politicalG.style.display = L.political ? '' : 'none';
    mountG.style.display = L.terrain ? '' : 'none';
    riverG.style.display = L.rivers ? '' : 'none';
    roadG.style.display = L.roads ? '' : 'none';
    cellsG.setAttribute('opacity', (L.opacity / 100).toFixed(2));
    for (const id in LY) $('#' + id).checked = !!L[LY[id]];
    $('#lyBorders').value = L.borders;
    $('#lyOpacity').value = L.opacity;
    updateEdges();
    updateLabelVis();
  }
  for (const id in LY) $('#' + id).addEventListener('change', (e) => { S.layers[LY[id]] = e.target.checked; applyLayers(); scheduleSave(); });
  $('#lyBorders').addEventListener('change', (e) => { S.layers.borders = e.target.value; applyLayers(); scheduleSave(); });
  $('#lyOpacity').addEventListener('input', (e) => { S.layers.opacity = +e.target.value; applyLayers(); scheduleSave(); });

  // ---------------------------------------------------------------- title
  const titleEl = $('#mapTitle');
  function setTitle(t) { S.title = t; titleEl.value = t; scheduleSave(); }
  titleEl.addEventListener('input', () => { S.title = titleEl.value; scheduleSave(); });
  titleEl.addEventListener('keydown', (e) => { if (e.key === 'Enter') titleEl.blur(); });

  // ---------------------------------------------------------------- search
  const searchEl = $('#search'), resultsEl = $('#results');
  const index = [];
  D.realms.forEach((r, i) => index.push({ n: r.n, lv: 'realm', u: i, kind: 'Realm' }));
  D.provinces.forEach((p, i) => index.push({ n: p.n, lv: 'province', u: i, kind: 'Province' }));
  D.districts.forEach((d, i) => index.push({ n: d.n, lv: 'district', u: i, kind: 'District' }));
  const seenPlace = new Set(index.map((x) => norm(x.n)));
  for (const [t, d] of D.places) {
    const n = t.replace(/\s+/g, ' ').replace(/^\(|\)$/g, '').trim();
    if (n.length < 3 || seenPlace.has(norm(n))) continue;
    seenPlace.add(norm(n));
    index.push({ n, lv: 'district', u: d, kind: 'Place' });
  }
  for (const x of index) x.k = norm(x.n);
  let selIdx = -1, shown = [];
  function runSearch() {
    const q = norm(searchEl.value.trim());
    resultsEl.textContent = '';
    selIdx = -1;
    if (!q) { resultsEl.hidden = true; return; }
    const scored = [];
    for (const x of index) {
      let s = -1;
      if (x.k === q) s = 0;
      else if (x.k.startsWith(q)) s = 1;
      else if (x.k.split(/[\s\-–(]+/).some((w) => w.startsWith(q))) s = 2;
      else if (x.k.includes(q)) s = 3;
      if (s >= 0) scored.push([s, LEVELS.indexOf(x.lv), x.n.length, x]);
    }
    scored.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
    shown = scored.slice(0, 12).map((s) => s[3]);
    shown.forEach((x, i) => {
      const chain = x.kind === 'Place' ? [D.districts[x.u].n].concat(unitChain('district', x.u)) : unitChain(x.lv, x.u);
      const li = h('li', { role: 'option', 'aria-selected': 'false' },
        h('span', { class: 'nm' }, x.n, h('small', null, chain.join(' · '))),
        h('span', { class: 'kind' }, x.kind),
        h('button', { class: 'paint-it', title: `Paint ${x.kind === 'Place' ? 'its district' : 'it'} with the current colour`, onclick: (e) => { e.stopPropagation(); paintUnit(x.lv, x.u); } }, 'Paint'));
      li.addEventListener('click', () => goTo(x));
      li.addEventListener('mouseenter', () => flash(x.lv, x.u, false));
      resultsEl.append(li);
    });
    if (!shown.length) resultsEl.append(h('li', { 'aria-disabled': 'true' }, h('span', { class: 'nm' }, 'No match on this map')));
    resultsEl.hidden = false;
  }
  function paintUnit(lv, u) {
    const cs = membersOf(lv, u);
    if (change(cs, swatchIdx(S.active), unitTitle(lv, u))) note(`Painted <b>${esc(unitTitle(lv, u))}</b>`);
  }
  function unitBox(lv, u) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const c of membersOf(lv, u)) {
      const b = cellEls[c].getBBox();
      x0 = Math.min(x0, b.x); y0 = Math.min(y0, b.y); x1 = Math.max(x1, b.x + b.width); y1 = Math.max(y1, b.y + b.height);
    }
    return { x: x0, y: y0, width: x1 - x0, height: y1 - y0 };
  }
  let flashTimer = 0;
  function flash(lv, u, long) {
    hoverPath.setAttribute('d', unitPath(lv, u));
    hoverPath.setAttribute('fill', '#ffd34d');
    hoverPath.setAttribute('fill-opacity', '0.7');
    hoverKey = 'flash';
    clearTimeout(flashTimer);
    flashTimer = setTimeout(() => { if (hoverKey === 'flash') { hoverPath.setAttribute('d', ''); hoverKey = null; } }, long ? 1600 : 900);
  }
  function goTo(x) {
    zoomTo(unitBox(x.lv, x.u));
    flash(x.lv, x.u, true);
    if (x.lv !== 'district' || x.kind !== 'Place') { /* keep mode */ }
    resultsEl.hidden = true;
    const chain = unitChain(x.lv, x.u);
    note(`<b>${esc(x.n)}</b>${chain.length ? ' · ' + esc(chain.join(' · ')) : ''}`);
  }
  searchEl.addEventListener('input', runSearch);
  searchEl.addEventListener('focus', () => { if (searchEl.value) runSearch(); });
  searchEl.addEventListener('keydown', (e) => {
    const items = [...resultsEl.querySelectorAll('li[role=option]')];
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!items.length) return;
      selIdx = (selIdx + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      items.forEach((li, i) => li.setAttribute('aria-selected', String(i === selIdx)));
      flash(shown[selIdx].lv, shown[selIdx].u, false);
    } else if (e.key === 'Enter') {
      const x = shown[selIdx >= 0 ? selIdx : 0];
      if (x) goTo(x);
    } else if (e.key === 'Escape') {
      resultsEl.hidden = true; searchEl.blur();
    }
  });
  document.addEventListener('pointerdown', (e) => { if (!e.target.closest('.search')) resultsEl.hidden = true; });

  // ---------------------------------------------------------------- keyboard
  document.addEventListener('keydown', (e) => {
    const typing = e.target.closest('input, textarea, select, [contenteditable]');
    const mod = e.ctrlKey || e.metaKey;
    if (mod && e.key.toLowerCase() === 'z') { if (typing && e.target.type === 'text') return; e.preventDefault(); e.shiftKey ? redo() : undo(); return; }
    if (mod && e.key.toLowerCase() === 'y') { e.preventDefault(); redo(); return; }
    if (typing || mod || e.altKey) return;
    const k = e.key;
    if (k >= '1' && k <= '4') setMode(LEVELS[+k - 1]);
    else if (k === 'p') setTool('paint');
    else if (k === 'e') setTool('erase');
    else if (k === 'i') setTool('pick');
    else if (k === 'b') setBrush(!S.brush);
    else if (k === '+' || k === '=') zoomCenter(1.5);
    else if (k === '-' || k === '_') zoomCenter(1 / 1.5);
    else if (k === '0') fitView();
    else if (k === '/') { e.preventDefault(); searchEl.focus(); }
    else if (k === 'Escape') closeModal();
  });
  $('#undo').onclick = undo;
  $('#redo').onclick = redo;

  // ---------------------------------------------------------------- phone sheet
  const panel = $('#panel'), sheetBtn = $('#sheetBtn');
  sheetBtn.onclick = () => {
    const open = !panel.classList.contains('open');
    panel.classList.toggle('open', open);
    sheetBtn.setAttribute('aria-expanded', String(open));
    sheetBtn.textContent = open ? 'Close' : 'More';
  };

  // ---------------------------------------------------------------- save / load
  function serialize() {
    const used = new Map();
    const swatches = [];
    const runs = [];
    let prev = 0, start = 0;
    for (let i = 0; i <= N; i++) {
      const v = i < N ? S.cells[i] : -1;
      if (v !== prev) {
        if (prev > 0) {
          if (!used.has(prev)) { used.set(prev, swatches.length + 1); swatches.push(S.swatches[prev - 1]); }
          runs.push(start, i - start, used.get(prev));
        }
        prev = v; start = i;
      }
    }
    const labels = {};
    for (const c of swatches) if (S.labels[c]) labels[c] = S.labels[c];
    return { app: 'middle-earth-map-painter', v: 1, cells: N, title: S.title, mode: S.mode, active: S.active, swatches, labels, runs, layers: S.layers };
  }
  function load(o, opts) {
    if (!o || o.app !== 'middle-earth-map-painter' || !Array.isArray(o.runs) || !Array.isArray(o.swatches)) throw new Error('This is not a Middle-earth Map Painter file.');
    if (o.cells !== N) throw new Error('This map file was made for a different version of the regions.');
    const vals = new Uint16Array(N);
    const idxs = o.swatches.map((c) => swatchIdx(String(c)));
    for (let k = 0; k + 2 < o.runs.length; k += 3) {
      const s = o.runs[k], n = o.runs[k + 1], v = idxs[o.runs[k + 2] - 1];
      if (!(s >= 0 && n > 0 && s + n <= N && v)) continue;
      vals.fill(v, s, s + n);
    }
    if (o.labels && typeof o.labels === 'object') for (const c in o.labels) S.labels[c.toLowerCase()] = String(o.labels[c]).slice(0, 60);
    if (typeof o.title === 'string') setTitle(o.title.slice(0, 120));
    if (o.layers && typeof o.layers === 'object') Object.assign(S.layers, o.layers);
    if (typeof o.active === 'string' && /^#[0-9a-f]{6}$/i.test(o.active)) S.active = o.active.toLowerCase();
    applyLayers();
    if (opts && opts.history) fillAll(vals, opts.history);
    else {
      const idx = new Int32Array(N);
      for (let i = 0; i < N; i++) idx[i] = i;
      setCells(idx, vals);
      changed();
    }
    if (LEVELS.includes(o.mode)) setMode(o.mode);
    renderPalette();
  }
  let saveTimer = 0;
  function scheduleSave() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      try { localStorage.setItem(STORE, JSON.stringify(serialize())); } catch (e) { /* storage may be off */ }
    }, 500);
  }
  const hot = window.claude && window.claude.hot;
  if (hot && typeof hot.snapshot === 'function') hot.snapshot(() => serialize());

  async function toCode() {
    const json = JSON.stringify(serialize());
    let bytes = new TextEncoder().encode(json), tag = 'ME0.';
    if (window.CompressionStream) {
      const cs = new Blob([bytes]).stream().pipeThrough(new CompressionStream('deflate-raw'));
      bytes = new Uint8Array(await new Response(cs).arrayBuffer());
      tag = 'ME1.';
    }
    let bin = '';
    for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return tag + btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  async function fromCode(code) {
    code = code.trim().replace(/\s+/g, '');
    const m = /^ME([01])\.([A-Za-z0-9_-]+)$/.exec(code);
    if (!m) throw new Error('That does not look like a map code. Codes start with ME1.');
    const bin = atob(m[2].replace(/-/g, '+').replace(/_/g, '/'));
    let bytes = Uint8Array.from(bin, (ch) => ch.charCodeAt(0));
    if (m[1] === '1') {
      if (!window.DecompressionStream) throw new Error('This browser cannot unpack map codes. Use a map file instead.');
      const ds = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
      bytes = new Uint8Array(await new Response(ds).arrayBuffer());
    }
    return JSON.parse(new TextDecoder().decode(bytes));
  }

  // ---------------------------------------------------------------- files out
  let dlPromise = null;
  function downloadsCap() {
    if (!dlPromise) dlPromise = (window.claude && typeof window.claude.use === 'function') ? window.claude.use('downloads').catch(() => null) : Promise.resolve(null);
    return dlPromise;
  }
  async function offerFile(filename, blob, fallback) {
    const dl = await downloadsCap();
    if (dl) {
      try {
        const r = await dl.save({ filename, data: blob });
        toast(r && r.status === 'delivered' ? 'Sent' : `Saved ${filename}`);
        return;
      } catch (err) {
        const code = err && err.code;
        if (code === 'declined') { toast('Save cancelled'); return; }
        if (code === 'rate_limited') { toast('Another save is still waiting for an answer'); return; }
      }
    }
    let framed = true;
    try { framed = window.top !== window.self; } catch (e) { framed = true; }
    if (!framed) {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      document.body.append(a);
      a.click();
      setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 4000);
      toast(`Saved ${filename}`);
      return;
    }
    fallback();
  }
  const slug = () => (S.title || 'middle-earth').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60) || 'middle-earth';

  $('#saveBtn').onclick = () => {
    const text = JSON.stringify(serialize());
    offerFile(`${slug()}.json`, new Blob([text], { type: 'application/json' }), () => showText('Your map file', 'Copy this text and keep it somewhere safe. Paste it back with "Paste map code".', text));
  };
  const fileIn = $('#fileIn');
  $('#openBtn').onclick = () => fileIn.click();
  fileIn.addEventListener('change', async () => {
    const f = fileIn.files && fileIn.files[0];
    fileIn.value = '';
    if (!f) return;
    try { load(JSON.parse(await f.text()), { history: 'opening the file' }); toast(`Opened ${f.name}`); }
    catch (err) { toast(err.message || 'That file could not be read'); }
  });
  $('#codeBtn').onclick = async () => {
    const code = await toCode();
    try { await navigator.clipboard.writeText(code); toast(`Copied a ${fmtInt(code.length)}-character map code`); }
    catch (e) { showText('Map code', 'Select all of this code and copy it. Anyone can load it with "Paste map code".', code); }
  };
  $('#pasteBtn').onclick = () => {
    const ta = h('textarea', { id: 'codeIn', placeholder: 'ME1.…', 'aria-label': 'Map code' });
    const err = h('p', { class: 'hint', style: 'color:var(--accent)' });
    openModal(h('h3', null, 'Paste a map code'), h('p', { class: 'hint' }, 'A map code (or the text of a map file) replaces the current colouring. Undo brings yours back.'), ta, err,
      h('div', { class: 'btn-row' },
        h('button', { class: 'btn primary', onclick: async () => {
          const v = ta.value.trim();
          try {
            const o = v.startsWith('{') ? JSON.parse(v) : await fromCode(v);
            load(o, { history: 'loading the map code' });
            closeModal(); toast('Map loaded');
          } catch (e) { err.textContent = e.message || 'That code could not be read.'; }
        } }, 'Load map'),
        h('button', { class: 'btn', onclick: closeModal }, 'Cancel')));
    setTimeout(() => ta.focus(), 30);
  };

  // ---------------------------------------------------------------- modal
  const modal = $('#modal'), dialog = $('#dialog');
  function openModal(...kids) { dialog.textContent = ''; dialog.append(...kids); modal.hidden = false; }
  function closeModal() { modal.hidden = true; dialog.textContent = ''; }
  modal.addEventListener('pointerdown', (e) => { if (e.target === modal) closeModal(); });
  function showText(title, hint, text) {
    const ta = h('textarea', { readonly: '', 'aria-label': title }, text);
    openModal(h('h3', null, title), h('p', { class: 'hint' }, hint), ta,
      h('div', { class: 'btn-row' },
        h('button', { class: 'btn primary', onclick: async () => { ta.select(); try { await navigator.clipboard.writeText(text); toast('Copied'); } catch (e) { document.execCommand && document.execCommand('copy'); } } }, 'Copy'),
        h('button', { class: 'btn', onclick: closeModal }, 'Close')));
    setTimeout(() => ta.select(), 30);
  }

  // ---------------------------------------------------------------- image export
  const p2d = new Map();
  function path2d(key, d) { let p = p2d.get(key); if (!p) { p = new Path2D(d); p2d.set(key, p); } return p; }
  function matrixOf(t) {
    const m = /matrix\(([^)]+)\)/.exec(t || '');
    return m ? new DOMMatrix(m[1].split(/[\s,]+/).map(Number)) : new DOMMatrix();
  }
  function drawGroups(ctx, base, name) {
    (D.base[name] || []).forEach((g, i) => {
      ctx.setTransform(base.multiply(matrixOf(g.t)));
      const a = g.a, p = path2d(name + i, g.d);
      if (a.fill !== 'none') { ctx.fillStyle = a.fill || '#000'; ctx.fill(p, a['fill-rule'] === 'evenodd' ? 'evenodd' : 'nonzero'); }
      if (a.stroke && a.stroke !== 'none') {
        ctx.strokeStyle = a.stroke;
        ctx.lineWidth = +a['stroke-width'] || 1;
        ctx.lineCap = a['stroke-linecap'] || 'butt';
        ctx.lineJoin = a['stroke-linejoin'] || 'miter';
        ctx.setLineDash(a['stroke-dasharray'] ? a['stroke-dasharray'].split(/[\s,]+/).map(Number) : []);
        ctx.stroke(p);
        ctx.setLineDash([]);
      }
    });
  }
  function drawGlyphs(ctx, base, kind) {
    for (const L of D.labels[kind] || []) {
      ctx.fillStyle = L.f;
      for (const u of L.u) {
        ctx.setTransform(base.multiply(new DOMMatrix(u.slice(1))));
        ctx.fill(path2d('g' + u[0], D.glyphs[u[0]]));
      }
    }
  }
  const EXPORT_W = { realm: 1.25, province: 0.75, district: 0.45, cell: 0.28 };
  async function renderImage(scale, withLegend) {
    try { await Promise.race([document.fonts.ready, new Promise((r) => setTimeout(r, 2500))]); } catch (e) { /* fonts optional */ }
    const cw = Math.round(FW * scale), mh = Math.round(FH * scale);
    const legend = withLegend ? legendData() : [];
    const lay = withLegend ? legendLayout(legend, cw, scale) : null;
    const cv = document.createElement('canvas');
    cv.width = cw; cv.height = mh + (lay ? lay.height : 0);
    const ctx = cv.getContext('2d');
    const base = new DOMMatrix([scale, 0, 0, scale, -FX0 * scale, -FY0 * scale]);
    const L = S.layers;
    ctx.setTransform(base);
    ctx.fillStyle = PAPER;
    ctx.fillRect(FX0, FY0, FW, FH);
    drawGroups(ctx, base, 'water');
    drawGroups(ctx, base, 'island');
    // colours (as one layer, so partial strength does not show seams)
    const op = L.opacity / 100;
    let tctx = ctx, off = null;
    if (op < 1) { off = document.createElement('canvas'); off.width = cw; off.height = mh; tctx = off.getContext('2d'); }
    tctx.setTransform(base);
    tctx.lineJoin = 'round';
    tctx.lineWidth = 0.6;
    for (let i = 0; i < N; i++) {
      const col = colorOf(S.cells[i]);
      if (!col) continue;
      const p = path2d('c' + i, D.cells.path[i]);
      tctx.fillStyle = col; tctx.strokeStyle = col;
      tctx.fill(p); tctx.stroke(p);
    }
    if (off) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = op; ctx.drawImage(off, 0, 0); ctx.globalAlpha = 1; }
    drawGroups(ctx, base, 'coast');
    if (L.rivers) drawGroups(ctx, base, 'river');
    ctx.globalCompositeOperation = 'multiply';
    if (L.terrain) { drawGroups(ctx, base, 'mountain'); drawGroups(ctx, base, 'forest'); drawGroups(ctx, base, 'marsh'); }
    if (L.roads) drawGroups(ctx, base, 'road');
    drawGroups(ctx, base, 'symbol');
    ctx.globalCompositeOperation = 'source-over';
    // borders
    ctx.setTransform(base);
    ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    for (const key of ['cell_w', 'district_w', 'province_w', 'realm_w', 'cell_l', 'district_l', 'province_l', 'realm_l']) {
      const e = edgeEls[key];
      if (!e || e.style.display === 'none') continue;
      const st = EDGE[key], lv = key.split('_')[0];
      ctx.strokeStyle = st.c; ctx.globalAlpha = st.o;
      ctx.lineWidth = EXPORT_W[lv] * (key.endsWith('_w') ? 0.8 : 1);
      ctx.setLineDash(st.dash ? st.dash.split(' ').map((v) => v * EXPORT_W[lv]) : []);
      ctx.stroke(path2d('e' + key, D.edges[key]));
    }
    ctx.globalAlpha = 1; ctx.setLineDash([]);
    if (L.places) drawGlyphs(ctx, base, 'place');
    if (L.political) { drawGlyphs(ctx, base, 'region'); drawGlyphs(ctx, base, 'political'); }
    if (L.labels && S.mode !== 'cell') drawRegionLabels(ctx, base, scale);
    drawGroups(ctx, base, 'decor');
    drawGlyphs(ctx, base, 'decor');
    drawGroups(ctx, base, 'frame');
    if (lay) drawLegend(ctx, lay, legend, mh, cw, scale);
    return cv;
  }
  function drawRegionLabels(ctx, base, scale) {
    const lv = S.mode, f = LABEL_FONT[lv];
    ctx.setTransform(base);
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    UNITS[lv].forEach((unit, i) => {
      const name = f.upper ? unit.n.toUpperCase() : unit.n;
      const fs = labelSize(lv, name, unit.l);
      if (fs * scale < 7) return;
      if (lv === 'realm' && isWaterUnit(lv, i) && S.layers.places) return;
      ctx.font = f.font.replace('100px', fs.toFixed(2) + 'px');
      if ('letterSpacing' in ctx) ctx.letterSpacing = (f.track * fs).toFixed(2) + 'px';
      const water = isWaterUnit(lv, i);
      ctx.lineWidth = fs * 0.2;
      ctx.strokeStyle = water ? 'rgba(223,241,251,.8)' : 'rgba(255,249,234,.8)';
      ctx.strokeText(name, unit.l[0], unit.l[1]);
      ctx.fillStyle = water ? '#1f4f73' : '#2b2420';
      ctx.fillText(name, unit.l[0], unit.l[1]);
    });
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
  }
  function legendLayout(rows, cw, scale) {
    const u = Math.max(1, scale) * 14; // one text line
    const pad = u * 1.4;
    const colW = u * 16;
    const cols = Math.max(1, Math.floor((cw - pad * 2) / colW));
    const lines = Math.ceil(rows.length / cols);
    return { u, pad, colW, cols, height: Math.round(pad * 2 + u * 2.2 + (rows.length ? lines * u * 1.7 : 0)) };
  }
  function drawLegend(ctx, lay, rows, top, cw, scale) {
    const { u, pad, colW, cols } = lay;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.fillStyle = PAPER;
    ctx.fillRect(0, top, cw, lay.height);
    ctx.fillStyle = '#231f20';
    ctx.fillRect(0, top, cw, Math.max(1, scale));
    ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
    ctx.font = `700 ${u * 1.35}px "Alegreya SC", Georgia, serif`;
    ctx.fillText(S.title || 'Middle-earth', pad, top + pad + u * 0.6);
    ctx.font = `${u * 0.8}px "Alegreya Sans", sans-serif`;
    ctx.fillStyle = '#5a5248';
    ctx.textAlign = 'right';
    ctx.fillText('Middle-earth in the Third Age · base map by Chris Taylor and Chris Guerette', cw - pad, top + pad + u * 0.6);
    ctx.textAlign = 'left';
    rows.forEach((r, i) => {
      const cx = pad + (i % cols) * colW, cy = top + pad + u * 2.2 + Math.floor(i / cols) * u * 1.7;
      ctx.fillStyle = r.hex;
      ctx.fillRect(cx, cy - u * 0.5, u * 1.6, u);
      ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = Math.max(1, scale * 0.5);
      ctx.strokeRect(cx, cy - u * 0.5, u * 1.6, u);
      ctx.fillStyle = '#231f20';
      ctx.font = `${u}px "Alegreya", Georgia, serif`;
      let name = S.labels[r.hex] || r.hex;
      while (ctx.measureText(name).width > colW - u * 2.6 && name.length > 4) name = name.slice(0, -2) + '…';
      ctx.fillText(name, cx + u * 2.1, cy);
    });
  }
  function exportDialog() {
    const sizes = [
      { s: 1, t: 'Standard', d: `${fmtInt(FW)} × ${fmtInt(FH)} px` },
      { s: 2, t: 'Large', d: `${fmtInt(FW * 2)} × ${fmtInt(FH * 2)} px` },
      { s: 3, t: 'Poster', d: `${fmtInt(FW * 3)} × ${fmtInt(FH * 3)} px` },
    ];
    let pick = 2;
    const withLegend = h('input', { type: 'checkbox', id: 'expLegend', checked: '' });
    const choices = h('div', { class: 'choices' });
    const draw = () => {
      choices.textContent = '';
      for (const z of sizes) {
        choices.append(h('button', { class: 'choice', 'aria-pressed': String(z.s === pick), style: z.s === pick ? 'border-color:var(--accent);box-shadow:inset 0 0 0 1px var(--accent)' : '', onclick: () => { pick = z.s; draw(); } },
          h('b', null, z.t), h('small', null, z.d)));
      }
    };
    draw();
    const status = h('p', { class: 'hint' });
    openModal(h('h3', null, 'Export image'),
      h('p', { class: 'hint' }, 'A PNG of the whole map with your colours, borders and names as they are set now.'),
      choices,
      h('label', { class: 'tg' }, 'Add the title and legend underneath', withLegend),
      status,
      h('div', { class: 'btn-row' },
        h('button', { class: 'btn primary', onclick: async (e) => {
          e.target.disabled = true; status.textContent = 'Drawing the map…';
          await new Promise((r) => setTimeout(r, 30));
          try {
            const cv = await renderImage(pick, withLegend.checked);
            const blob = await new Promise((r) => cv.toBlob(r, 'image/png'));
            const url = URL.createObjectURL(blob);
            closeModal();
            await offerFile(`${slug()}.png`, blob, () => {
              openModal(h('h3', null, 'Your map'), h('p', { class: 'hint' }, 'Right-click the image (or press and hold on a phone) and choose Save image.'),
                h('img', { src: url, alt: S.title }), h('div', { class: 'btn-row' }, h('button', { class: 'btn', onclick: closeModal }, 'Close')));
            });
          } catch (err) { status.textContent = 'The image could not be drawn: ' + (err.message || err); e.target.disabled = false; }
        } }, 'Export PNG'),
        h('button', { class: 'btn', onclick: exportSVG }, 'Export SVG'),
        h('button', { class: 'btn', onclick: closeModal }, 'Cancel')));
  }
  function exportSVG() {
    const clone = svg.cloneNode(true);
    clone.setAttribute('viewBox', `${FX0} ${FY0} ${FW} ${FH}`);
    clone.setAttribute('width', Math.round(FW));
    clone.setAttribute('height', Math.round(FH));
    clone.removeAttribute('style');
    const style = document.createElementNS(NS, 'style');
    style.textContent = '.rlab{font-family:"Alegreya SC",Georgia,serif;font-weight:700;fill:#2b2420;paint-order:stroke;stroke:#fff9ea;stroke-opacity:.8;stroke-linejoin:round}' +
      '.rlab.realm{letter-spacing:.14em}.rlab.province{font-weight:500;letter-spacing:.06em}.rlab.district{font-family:Alegreya,Georgia,serif;font-style:italic;font-weight:500}.rlab.water{fill:#1f4f73;stroke:#dff1fb}';
    clone.insertBefore(style, clone.firstChild);
    const hov = clone.querySelector('#world > path[fill-opacity]');
    if (hov) hov.setAttribute('d', '');
    for (const t of clone.querySelectorAll('[style*="display: none"], [style*="display:none"]')) t.remove();
    const text = '<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(clone);
    closeModal();
    offerFile(`${slug()}.svg`, new Blob([text], { type: 'image/svg+xml' }), () => showText('SVG', 'Copy this into a file ending in .svg.', text));
  }
  $('#exportBtn').onclick = exportDialog;
  $('#pngBtn').onclick = exportDialog;

  // ---------------------------------------------------------------- boot
  function start(snapshot) {
    measureStage();
    fitView();
    buildLabels(S.mode);
    let saved = snapshot && snapshot.app ? snapshot : null;
    if (!saved) {
      try { const raw = localStorage.getItem(STORE); if (raw) saved = JSON.parse(raw); } catch (e) { saved = null; }
    }
    let loaded = false;
    if (saved) { try { load(saved); loaded = true; } catch (e) { loaded = false; } }
    if (!loaded) {
      // first visit: show what the tool does with a filled example
      const vals = warVals();
      const idx = new Int32Array(N);
      for (let i = 0; i < N; i++) idx[i] = i;
      setCells(idx, vals);
      setTitle('War of the Ring, T.A. 3019 (example)');
      changed();
      setMode('realm');
      note('An example to start from: the realms by side in the War of the Ring. <b>Clear map</b> starts fresh.');
    } else {
      setMode(S.mode);
    }
    applyLayers();
    renderPalette();
    renderLegend();
    setTool('paint');
    if (document.fonts && document.fonts.load) {
      Promise.all([
        document.fonts.load('700 20px "Alegreya SC"'), document.fonts.load('500 20px "Alegreya SC"'),
        document.fonts.load('italic 500 20px "Alegreya"'),
      ]).then(() => { for (const lv in labelGroups) { const vis = lv === S.mode; buildLabels(lv); if (!vis) labelGroups[lv].style.display = 'none'; } updateLabelVis(); }).catch(() => {});
    }
  }
  if (hot && typeof hot.ready === 'function') hot.ready(start);
  else start((hot && hot.data) || null);
})();
