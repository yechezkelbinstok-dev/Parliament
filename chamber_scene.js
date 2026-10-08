// Realistic model of the enlarged House chamber, built from the layout that
// chamber.py computes (window.LAYOUT) and shot from window.VIEW.
// Coordinates in the layout: x east, y north (away from the rostrum), z up, metres.

THREE.ColorManagement.legacyMode = false;
const L = window.LAYOUT, VIEW = window.VIEW;
const W = L.room.w, D = L.room.d, H = L.room.h, HW = W / 2;

const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(1);
renderer.setSize(canvas.width, canvas.height, false);
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = VIEW.exposure || 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.physicallyCorrectLights = false;

const scene = new THREE.Scene();
scene.background = new THREE.Color('#14161a');
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new THREE.RoomEnvironment(), 0.04).texture;

const V = (x, y, z) => new THREE.Vector3(x, z, -y);   // layout -> three.js

// ------------------------------------------------------------------ textures

let seed = 7;
const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

function canvasTexture(w, h, draw, repeat) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.encoding = THREE.sRGBEncoding;
  t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(repeat[0], repeat[1]); }
  return t;
}
function noise(g, w, h, amount, alpha) {
  for (let i = 0; i < amount; i++) {
    g.fillStyle = `rgba(${rand() < 0.5 ? '0,0,0' : '255,255,255'},${alpha * rand()})`;
    g.fillRect(rand() * w, rand() * h, 1 + rand() * 2, 1 + rand() * 2);
  }
}
function star(g, cx, cy, r) {
  g.beginPath();
  for (let i = 0; i < 10; i++) {
    const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.4 : r;
    g.lineTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a));
  }
  g.closePath(); g.fill();
}

// Royal blue carpet with gold wreaths and red/gold accents (one tile = 2.4 m).
const carpetTex = canvasTexture(512, 512, (g, w, h) => {
  g.fillStyle = '#1b2f78'; g.fillRect(0, 0, w, h);
  noise(g, w, h, 30000, 0.07);
  const wreath = (cx, cy, r) => {
    for (let i = 0; i < 22; i++) {
      const a = (i / 22) * Math.PI * 2;
      g.save(); g.translate(cx + r * Math.cos(a), cy + r * Math.sin(a)); g.rotate(a + 0.6);
      g.fillStyle = i % 2 ? 'rgba(196,158,72,0.75)' : 'rgba(170,134,58,0.75)';
      g.beginPath(); g.ellipse(0, 0, 7, 2.8, 0, 0, Math.PI * 2); g.fill(); g.restore();
    }
    g.fillStyle = 'rgba(196,158,72,0.8)'; star(g, cx, cy, 7);
  };
  wreath(w / 4, h / 4, 34); wreath(3 * w / 4, 3 * h / 4, 34);
  g.fillStyle = 'rgba(150,34,44,0.8)';
  for (const [x, y] of [[3 * w / 4, h / 4], [w / 4, 3 * h / 4]]) { g.beginPath(); g.arc(x, y, 5, 0, Math.PI * 2); g.fill(); }
  g.strokeStyle = 'rgba(201,164,76,0.18)'; g.lineWidth = 2;
  g.strokeRect(1, 1, w - 2, h - 2);
}, [1 / 1.6, 1 / 1.6]);
const riserTex = canvasTexture(256, 64, (g, w, h) => {
  g.fillStyle = '#16296a'; g.fillRect(0, 0, w, h); noise(g, w, h, 3000, 0.08);
  g.fillStyle = '#b8933f'; g.fillRect(0, 0, w, 4);
}, [1 / 2, 1]);

function woodTexture(base, dark, light) {
  return canvasTexture(512, 512, (g, w, h) => {
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 160; i++) {
      const y0 = rand() * h, amp = 2 + rand() * 6, freq = 0.005 + rand() * 0.02, ph = rand() * 6;
      g.strokeStyle = rand() < 0.6 ? dark : light; g.globalAlpha = 0.08 + rand() * 0.18; g.lineWidth = 1 + rand() * 2.5;
      g.beginPath();
      for (let x = 0; x <= w; x += 8) g.lineTo(x, y0 + amp * Math.sin(x * freq + ph));
      g.stroke();
    }
    g.globalAlpha = 1; noise(g, w, h, 8000, 0.05);
  }, [0.6, 0.6]);
}
const walnutTex = woodTexture('#5a3720', '#2e1a0e', '#7a4e2e');

function marbleTexture(base, vein, veinAlpha) {
  return canvasTexture(512, 512, (g, w, h) => {
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    noise(g, w, h, 20000, 0.05);
    for (let i = 0; i < 26; i++) {
      g.strokeStyle = vein; g.globalAlpha = veinAlpha * (0.3 + rand()); g.lineWidth = 0.6 + rand() * 1.8;
      g.beginPath(); let x = rand() * w, y = rand() * h; g.moveTo(x, y);
      for (let k = 0; k < 6; k++) { x += (rand() - 0.3) * 140; y += (rand() - 0.5) * 120; g.lineTo(x, y); }
      g.stroke();
    }
    g.globalAlpha = 1;
  }, [0.5, 0.5]);
}
const greyMarbleTex = marbleTexture('#c9c6bf', '#7d7a74', 0.35);
const blackMarbleTex = marbleTexture('#151517', '#d8d6d0', 0.25);
const whiteMarbleTex = marbleTexture('#efece4', '#a9a49a', 0.2);
const plasterTex = canvasTexture(256, 256, (g, w, h) => { g.fillStyle = '#e7dfcc'; g.fillRect(0, 0, w, h); noise(g, w, h, 6000, 0.04); }, [0.25, 0.25]);
const leatherTex = canvasTexture(256, 256, (g, w, h) => { g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h); noise(g, w, h, 12000, 0.10); }, [2, 2]);
const fabricTex = canvasTexture(128, 128, (g, w, h) => {
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
  g.strokeStyle = 'rgba(0,0,0,0.12)';
  for (let i = 0; i < w; i += 3) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, h); g.stroke(); }
}, [4, 4]);

// ------------------------------------------------------------------ materials

const M = {
  carpet: new THREE.MeshStandardMaterial({map: carpetTex, roughness: 0.97, envMapIntensity: 0.3}),
  riser: new THREE.MeshStandardMaterial({map: riserTex, roughness: 0.9, envMapIntensity: 0.3}),
  walnut: new THREE.MeshStandardMaterial({map: walnutTex, color: '#b9a597', roughness: 0.5, envMapIntensity: 0.45}),
  greyMarble: new THREE.MeshStandardMaterial({map: greyMarbleTex, roughness: 0.25, envMapIntensity: 0.9}),
  blackMarble: new THREE.MeshStandardMaterial({map: blackMarbleTex, roughness: 0.18, envMapIntensity: 1.0}),
  whiteMarble: new THREE.MeshStandardMaterial({map: whiteMarbleTex, roughness: 0.3, envMapIntensity: 0.8}),
  plaster: new THREE.MeshStandardMaterial({map: plasterTex, roughness: 0.92, envMapIntensity: 0.4}),
  gold: new THREE.MeshStandardMaterial({color: '#c9a043', roughness: 0.3, metalness: 1.0, envMapIntensity: 1.2}),
  bronze: new THREE.MeshStandardMaterial({color: '#7a5a2c', roughness: 0.35, metalness: 1.0, envMapIntensity: 1.1}),
  silver: new THREE.MeshStandardMaterial({color: '#d8d8d8', roughness: 0.2, metalness: 1.0}),
  leather: new THREE.MeshStandardMaterial({map: leatherTex, color: VIEW.colors === 'party' ? '#ffffff' : '#4a1d14', roughness: 0.45, envMapIntensity: 0.55}),
  chairWood: new THREE.MeshStandardMaterial({map: walnutTex, color: '#8a7466', roughness: 0.4, envMapIntensity: 0.5}),
  fabric: new THREE.MeshStandardMaterial({map: fabricTex, color: '#24345f', roughness: 0.95, envMapIntensity: 0.3}),
  door: new THREE.MeshStandardMaterial({map: walnutTex, color: '#b8a08a', roughness: 0.4}),
  black: new THREE.MeshStandardMaterial({color: '#111', roughness: 0.6}),
};

// ------------------------------------------------------------------ helpers

function add(mesh, shadows = true) {
  mesh.castShadow = shadows; mesh.receiveShadow = true;
  scene.add(mesh); return mesh;
}
function box(x, y, z, w, d, h, material, rotY = 0, rounded = 0) {
  const geo = rounded ? new THREE.RoundedBoxGeometry(w, h, d, 2, rounded) : new THREE.BoxGeometry(w, h, d);
  const m = new THREE.Mesh(geo, material);
  m.position.copy(V(x, y, z + h / 2)); m.rotation.y = rotY;
  return add(m);
}
function cylinder(x, y, z, r, h, material, seg = 24) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), material);
  m.position.copy(V(x, y, z + h / 2));
  return add(m);
}
function shapeFrom(poly) {
  const s = new THREE.Shape(poly.outer.map(([x, y]) => new THREE.Vector2(x, y)));
  for (const h of poly.holes) s.holes.push(new THREE.Path(h.map(([x, y]) => new THREE.Vector2(x, y))));
  return s;
}
function extrude(polys, z0, z1, materials) {
  if (z1 - z0 < 0.005) z1 = z0 + 0.005;
  for (const poly of polys) {
    const g = new THREE.ExtrudeGeometry(shapeFrom(poly), {depth: z1 - z0, bevelEnabled: false, curveSegments: 1});
    g.rotateX(-Math.PI / 2); g.translate(0, z0, 0);
    add(new THREE.Mesh(g, materials));
  }
}
function flatPolys(polys, z, material, facingDown) {
  for (const poly of polys) {
    const g = new THREE.ShapeGeometry(shapeFrom(poly));
    g.rotateX(-Math.PI / 2);
    g.translate(0, z, 0);
    const mat = material.clone(); mat.side = THREE.DoubleSide;
    const m = new THREE.Mesh(g, mat); m.receiveShadow = true; scene.add(m);
  }
}
function merge(geos) {
  const parts = geos.map(g => g.index ? g.toNonIndexed() : g);
  const out = new THREE.BufferGeometry();
  for (const name of ['position', 'normal', 'uv']) {
    const arrays = parts.map(p => p.attributes[name].array);
    const total = arrays.reduce((n, a) => n + a.length, 0);
    const merged = new Float32Array(total);
    let o = 0; for (const a of arrays) { merged.set(a, o); o += a.length; }
    out.setAttribute(name, new THREE.BufferAttribute(merged, parts[0].attributes[name].itemSize));
  }
  return out;
}

// ------------------------------------------------------------------ room shell

// floor (well and walkways)
const floorMesh = new THREE.Mesh(new THREE.PlaneGeometry(W, D), M.carpet);
floorMesh.geometry.attributes.uv.array.forEach((v, i, a) => { a[i] = v * (i % 2 ? D : W); });
floorMesh.rotation.x = -Math.PI / 2; floorMesh.position.copy(V(0, D / 2, 0)); floorMesh.receiveShadow = true;
scene.add(floorMesh);

const balconyFloor = L.balcony_rows[0].z;
const walls = {};
function wall(name, cx, cy, length, rotY, opts) {
  const g = new THREE.Group();
  const lowerH = opts.lowerH, upperH = H - lowerH;
  // walnut panelled lower wall
  const lower = new THREE.Mesh(new THREE.PlaneGeometry(length, lowerH), M.walnut);
  lower.position.set(0, lowerH / 2, 0); lower.receiveShadow = true; g.add(lower);
  // plaster upper wall
  const upper = new THREE.Mesh(new THREE.PlaneGeometry(length, upperH), M.plaster);
  upper.position.set(0, lowerH + upperH / 2, 0); upper.receiveShadow = true; g.add(upper);
  // panel mouldings on the walnut
  const bays = Math.max(2, Math.round(length / 3.2));
  for (let i = 0; i < bays; i++) {
    const px = -length / 2 + (i + 0.5) * (length / bays);
    for (const [py, ph] of [[0.55, 0.9], [lowerH * 0.55, lowerH * 0.55]]) {
      if (py + ph / 2 > lowerH - 0.2) continue;
      const frame = new THREE.Mesh(new THREE.BoxGeometry(length / bays - 0.9, ph, 0.03), M.walnut);
      frame.position.set(px, py, 0.02); frame.receiveShadow = true; g.add(frame);
    }
  }
  // grey marble pilasters, full height, with gilt capitals
  for (let i = 0; i <= bays; i += 1) {
    const px = -length / 2 + i * (length / bays);
    const pil = new THREE.Mesh(new THREE.BoxGeometry(0.62, H - 0.6, 0.22), M.greyMarble);
    pil.position.set(px, (H - 0.6) / 2, 0.11); pil.castShadow = pil.receiveShadow = true; g.add(pil);
    const cap = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.28, 0.3), M.gold);
    cap.position.set(px, H - 0.75, 0.15); g.add(cap);
  }
  // relief portrait medallions on the upper wall (between pilasters)
  if (opts.reliefs) for (let i = 0; i < bays; i++) {
    if (i % 2) continue;
    const px = -length / 2 + (i + 0.5) * (length / bays);
    const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.62, 0.08, 40), M.whiteMarble);
    disc.rotation.x = Math.PI / 2; disc.position.set(px, H - 1.75, 0.05); g.add(disc);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.64, 0.05, 8, 40), M.gold);
    rim.position.set(px, H - 1.75, 0.09); g.add(rim);
    const head = new THREE.Mesh(new THREE.SphereGeometry(0.3, 20, 16), M.whiteMarble);
    head.scale.set(0.8, 1, 0.35); head.position.set(px, H - 1.72, 0.1); g.add(head);
  }
  // cornice and frieze
  const cornice = new THREE.Mesh(new THREE.BoxGeometry(length, 0.5, 0.5), M.whiteMarble);
  cornice.position.set(0, H - 0.25, 0.25); g.add(cornice);
  const frieze = new THREE.Mesh(new THREE.BoxGeometry(length, 0.1, 0.52), M.gold);
  frieze.position.set(0, H - 0.55, 0.26); g.add(frieze);
  const chair_rail = new THREE.Mesh(new THREE.BoxGeometry(length, 0.12, 0.08), M.walnut);
  chair_rail.position.set(0, lowerH, 0.04); g.add(chair_rail);
  g.position.copy(V(cx, cy, 0)); g.rotation.y = rotY;
  scene.add(g); walls[name] = g;
}
wall('south', 0, 0, W, Math.PI, {lowerH: 5.2, reliefs: false});
wall('north', 0, D, W, 0, {lowerH: balconyFloor - 0.4, reliefs: true});
wall('west', -HW, D / 2, D, Math.PI / 2, {lowerH: balconyFloor - 0.4, reliefs: true});
wall('east', HW, D / 2, D, -Math.PI / 2, {lowerH: balconyFloor - 0.4, reliefs: true});

// doors: members' entrances on the floor, gallery doors on the upper level
const doorsByWall = {north: [], south: [], east: [], west: []};
function door(x, y, z, rotY, w = 1.9, h = 3.0, wallName) {
  const g = new THREE.Group();
  const surround = new THREE.Mesh(new THREE.BoxGeometry(w + 0.5, h + 0.35, 0.12), M.greyMarble); surround.position.set(0, h / 2 + 0.17, 0.06); g.add(surround);
  const leaf = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.14), M.door); leaf.position.set(0, h / 2, 0.08); g.add(leaf);
  const split = new THREE.Mesh(new THREE.BoxGeometry(0.03, h, 0.16), M.black); split.position.set(0, h / 2, 0.08); g.add(split);
  for (const s of [-1, 1]) { const k = new THREE.Mesh(new THREE.SphereGeometry(0.04, 10, 8), M.gold); k.position.set(s * 0.12, h * 0.45, 0.18); g.add(k); }
  g.position.copy(V(x, y, z)); g.rotation.y = rotY; scene.add(g);
  if (wallName) doorsByWall[wallName].push(g);
}
for (const x of [-12, 0, 12]) door(x, D - 0.02, 0, 0, 1.9, 3.0, 'north');
for (const s of [-1, 1]) { door(s * (HW - 0.02), 4.0, 0, -s * Math.PI / 2, 1.9, 3.0, s > 0 ? 'east' : 'west'); door(s * 13.2, 0.02, 0, Math.PI, 1.9, 3.0, 'south'); }
for (const x of [-15, -5, 5, 15]) door(x, D - 0.02, balconyFloor + 2.0, 0, 1.4, 2.4, 'north');

// ------------------------------------------------------------------ ceiling

const ceiling = new THREE.Group();
const ceil = new THREE.Mesh(new THREE.PlaneGeometry(W, D), M.plaster);
ceil.rotation.x = Math.PI / 2; ceil.position.copy(V(0, D / 2, H)); ceiling.add(ceil);
// coffer grid with gilt edges
const beamMat = M.whiteMarble;
for (let i = 0; i <= 10; i++) {
  const b = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.45, D), beamMat); b.position.copy(V(-HW + i * W / 10, D / 2, H - 0.22)); ceiling.add(b);
  const t = new THREE.Mesh(new THREE.BoxGeometry(0.32, 0.02, D), M.gold); t.position.copy(V(-HW + i * W / 10, D / 2, H - 0.46)); ceiling.add(t);
}
for (let j = 0; j <= 7; j++) {
  const b = new THREE.Mesh(new THREE.BoxGeometry(W, 0.45, 0.3), beamMat); b.position.copy(V(0, j * D / 7, H - 0.22)); ceiling.add(b);
  const t = new THREE.Mesh(new THREE.BoxGeometry(W, 0.02, 0.32), M.gold); t.position.copy(V(0, j * D / 7, H - 0.46)); ceiling.add(t);
}
// recessed downlights
for (let i = 0; i < 10; i++) for (let j = 0; j < 7; j++) {
  const x = -HW + (i + 0.5) * W / 10, y = (j + 0.5) * D / 7;
  if (Math.abs(x) < 9 && y > 7 && y < 23) continue;
  const disc = new THREE.Mesh(new THREE.CircleGeometry(0.22, 20), new THREE.MeshBasicMaterial({color: '#fff4dc'}));
  disc.rotation.x = Math.PI / 2; disc.position.copy(V(x, y, H - 0.01)); ceiling.add(disc);
}
// stained-glass laylight with the eagle, ringed by state seals
const laylightTex = canvasTexture(2048, 1280, (g, w, h) => {
  g.fillStyle = '#efe0b0'; g.fillRect(0, 0, w, h);
  const cols = 16, rows = 10;
  for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
    const x = i * w / cols, y = j * h / rows;
    const grad = g.createLinearGradient(x, y, x + w / cols, y + h / rows);
    grad.addColorStop(0, '#fbf1cf'); grad.addColorStop(1, (i + j) % 2 ? '#ead79b' : '#f3e5b6');
    g.fillStyle = grad; g.fillRect(x + 5, y + 5, w / cols - 10, h / rows - 10);
  }
  g.strokeStyle = '#9b7a35'; g.lineWidth = 10; g.strokeRect(5, 5, w - 10, h - 10);
  // state seals around an oval band
  for (let k = 0; k < 50; k++) {
    const a = (k / 50) * Math.PI * 2, cx = w / 2 + 760 * Math.cos(a), cy = h / 2 + 470 * Math.sin(a);
    g.fillStyle = ['#56638a', '#5f7358', '#86504a', '#a48a52'][k % 4];
    g.beginPath(); g.arc(cx, cy, 34, 0, Math.PI * 2); g.fill();
    g.strokeStyle = '#c9a85a'; g.lineWidth = 5; g.stroke();
    g.fillStyle = '#efe2bb'; g.beginPath(); g.arc(cx, cy, 16, 0, Math.PI * 2); g.fill();
  }
  // central medallion with the eagle
  g.fillStyle = '#20356f'; g.beginPath(); g.ellipse(w / 2, h / 2, 330, 300, 0, 0, Math.PI * 2); g.fill();
  g.strokeStyle = '#d9b75a'; g.lineWidth = 18; g.stroke();
  g.fillStyle = '#f2e7c4'; for (let k = 0; k < 13; k++) star(g, w / 2 - 150 + (k % 7) * 50, h / 2 - 230 + Math.floor(k / 7) * 46, 16);
  g.fillStyle = '#e6c25c';
  g.beginPath(); // wings
  g.moveTo(w / 2, h / 2 - 40);
  g.bezierCurveTo(w / 2 - 120, h / 2 - 170, w / 2 - 260, h / 2 - 120, w / 2 - 290, h / 2 + 10);
  g.bezierCurveTo(w / 2 - 210, h / 2 - 20, w / 2 - 120, h / 2 + 10, w / 2 - 60, h / 2 + 40);
  g.lineTo(w / 2 + 60, h / 2 + 40);
  g.bezierCurveTo(w / 2 + 120, h / 2 + 10, w / 2 + 210, h / 2 - 20, w / 2 + 290, h / 2 + 10);
  g.bezierCurveTo(w / 2 + 260, h / 2 - 120, w / 2 + 120, h / 2 - 170, w / 2, h / 2 - 40);
  g.fill();
  g.beginPath(); g.ellipse(w / 2, h / 2 - 70, 34, 40, 0, 0, Math.PI * 2); g.fill();  // head
  // shield
  g.fillStyle = '#ffffff'; g.fillRect(w / 2 - 55, h / 2 - 20, 110, 130);
  g.fillStyle = '#b22234'; for (let k = 0; k < 6; k++) g.fillRect(w / 2 - 55 + k * 20, h / 2 + 10, 10, 100);
  g.fillStyle = '#20356f'; g.fillRect(w / 2 - 55, h / 2 - 20, 110, 32);
  g.fillStyle = '#e6c25c'; g.fillRect(w / 2 - 110, h / 2 + 120, 220, 18);  // tail
});
const laylight = new THREE.Mesh(new THREE.PlaneGeometry(20, 12.5), new THREE.MeshStandardMaterial({map: laylightTex, emissive: '#fff1cf', emissiveMap: laylightTex, emissiveIntensity: 0.85, roughness: 0.6}));
laylight.rotation.x = Math.PI / 2; laylight.position.copy(V(0, D * 0.55, H - 0.48)); ceiling.add(laylight);
for (const [w, d, dx, dy] of [[20.8, 0.4, 0, 6.45], [20.8, 0.4, 0, -6.45], [0.4, 13.3, 10.2, 0], [0.4, 13.3, -10.2, 0]]) {
  const f = new THREE.Mesh(new THREE.BoxGeometry(w, 0.5, d), M.gold);
  f.position.copy(V(dx, D * 0.55 + dy, H - 0.25)); ceiling.add(f);
}
scene.add(ceiling);

// ------------------------------------------------------------------ rostrum and frontispiece

const rw = L.rostrum.w, rd = L.rostrum.d;
// three tiers of walnut with marble fronts and gilt trim
const tiers = [[rw, rd, 0, 0.8], [rw * 0.72, rd - 1.15, 0.8, 0.8], [rw * 0.36, rd - 2.4, 1.6, 0.85]];
for (const [tw, td, tz, th] of tiers) {
  box(0, td / 2, tz, tw, td, th, M.walnut);
  const front = box(0, td + 0.02, tz + 0.08, tw - 0.4, 0.05, th - 0.16, M.greyMarble);
  box(0, td + 0.05, tz + th - 0.06, tw, 0.08, 0.06, M.gold);
  // fluted panels on the front
  for (let k = -3; k <= 3; k++) box(k * (tw / 8), td + 0.05, tz + 0.15, 0.06, 0.03, th - 0.3, M.walnut);
}
// Speaker's desk and chair
box(0, rd - 2.4 - 0.3, 2.45, 2.6, 0.7, 0.75, M.walnut);
box(0, 0.75, 2.45, 0.9, 0.75, 0.5, M.leather, 0, 0.06);
box(0, 0.45, 2.45, 0.95, 0.18, 1.7, M.leather, 0, 0.06);
// clerks' chairs on the lower tiers
for (const x of [-3.5, -1.2, 1.2, 3.5]) { box(x, rd - 1.6, 0.8, 0.6, 0.55, 0.5, M.leather, 0, 0.05); box(x, rd - 1.95, 0.8, 0.6, 0.12, 1.0, M.leather, 0, 0.04); }

// frontispiece: black marble Ionic columns, white capitals, flag between bronze fasces
for (const x of [-4.6, -3.0, 3.0, 4.6]) {
  cylinder(x, 0.45, 0, 0.38, 0.35, M.whiteMarble);
  cylinder(x, 0.45, 0.35, 0.3, 7.0, M.blackMarble, 32);
  const cap = box(x, 0.45, 7.35, 0.95, 0.75, 0.38, M.whiteMarble);
  for (const s of [-1, 1]) {   // volutes
    const vol = new THREE.Mesh(new THREE.TorusGeometry(0.11, 0.05, 8, 16), M.whiteMarble);
    vol.position.copy(V(x + s * 0.42, 0.85, 7.55)); scene.add(vol);
  }
}
box(0, 0.4, 7.73, 10.6, 0.8, 0.7, M.whiteMarble);   // entablature
box(0, 0.82, 7.95, 10.6, 0.04, 0.08, M.gold);
const mottoTex = canvasTexture(2000, 140, (g, w, h) => {
  g.fillStyle = '#e9e5db'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#b08a35'; g.font = 'bold 96px Georgia, "Gelasio", serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('IN GOD WE TRUST', w / 2, h / 2 + 6);
});
const motto = new THREE.Mesh(new THREE.PlaneGeometry(9.6, 0.67), new THREE.MeshStandardMaterial({map: mottoTex, roughness: 0.4}));
motto.position.copy(V(0, 0.81, 8.08)); motto.rotation.y = Math.PI; scene.add(motto);
// the flag, hanging with soft folds
const flagTex = canvasTexture(1900, 1000, (g, w, h) => {
  for (let i = 0; i < 13; i++) { g.fillStyle = i % 2 ? '#f4f1ea' : '#a51f2d'; g.fillRect(0, i * h / 13, w, h / 13 + 1); }
  g.fillStyle = '#25285a'; g.fillRect(0, 0, w * 0.4, h * 7 / 13);
  g.fillStyle = '#f4f1ea';
  for (let r = 0; r < 9; r++) for (let c = 0; c < (r % 2 ? 5 : 6); c++) star(g, (c + (r % 2 ? 1 : 0.5)) * w * 0.4 / 6, (r + 1) * h * 7 / 13 / 10, 17);
});
const flagGeo = new THREE.PlaneGeometry(5.0, 2.65, 120, 2);
const fp = flagGeo.attributes.position;
for (let i = 0; i < fp.count; i++) fp.setZ(i, 0.05 * Math.sin(fp.getX(i) * 7.0) + 0.03 * Math.sin(fp.getX(i) * 2.3));
flagGeo.computeVertexNormals();
const flag = new THREE.Mesh(flagGeo, new THREE.MeshStandardMaterial({map: flagTex, roughness: 0.85, side: THREE.DoubleSide}));
flag.position.copy(V(0, 0.28, 5.0)); flag.rotation.y = Math.PI; flag.castShadow = true; scene.add(flag);
box(0, 0.12, 3.5, 5.4, 0.1, 3.3, M.blackMarble);   // dark marble behind the flag
// bronze fasces either side of the flag
for (const x of [-3.8, 3.8]) {
  for (let k = 0; k < 8; k++) {
    const a = (k / 8) * Math.PI * 2;
    cylinder(x + 0.11 * Math.cos(a), 0.55 + 0.11 * Math.sin(a), 1.9, 0.045, 3.6, M.bronze, 10);
  }
  for (const z of [2.3, 3.7, 5.1]) { const ring = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.035, 8, 20), M.bronze); ring.rotation.x = Math.PI / 2; ring.position.copy(V(x, 0.55, z)); scene.add(ring); }
  box(x + (x < 0 ? 0.22 : -0.22), 0.55, 5.1, 0.28, 0.04, 0.5, M.bronze);  // axe blade
}
// the Mace on its pedestal, to the Speaker's right
cylinder(3.9, 3.6, 0.8, 0.22, 0.9, M.greyMarble);
cylinder(3.9, 3.6, 1.7, 0.05, 1.2, M.silver, 12);
const globe = new THREE.Mesh(new THREE.SphereGeometry(0.13, 20, 16), M.silver); globe.position.copy(V(3.9, 3.6, 3.0)); add(globe);
box(3.9, 3.6, 3.12, 0.22, 0.06, 0.12, M.silver);
// lecterns and leadership tables in the well
for (const x of [-3.4, 3.4]) {
  box(x, 6.0, 0, 0.9, 0.65, 1.12, M.walnut, 0, 0.03);
  box(x, 5.95, 1.12, 0.95, 0.75, 0.05, M.walnut);
  cylinder(x, 5.9, 1.17, 0.012, 0.35, M.black, 6);
  box(x * 1.0, 8.2, 0, 3.4, 1.0, 0.76, M.walnut, 0, 0.03);
}

// ------------------------------------------------------------------ tiers and balcony

const tierMaterials = [M.carpet, M.riser];
for (const b of L.bowl_bands) extrude(b.polys, 0, b.z, tierMaterials);
const nb = L.balcony_bands.length;
L.balcony_bands.forEach((b, i) => extrude(b.polys, b.z0, b.z, i === nb - 1 ? [M.carpet, M.walnut] : tierMaterials));
// walnut and marble balcony front, gilt rail
extrude(L.parapet.polys, L.parapet.z0, L.parapet.z - 0.1, [M.walnut, M.walnut]);
extrude(L.parapet.polys, L.parapet.z - 0.1, L.parapet.z, [M.greyMarble, M.greyMarble]);
extrude(L.parapet.polys, L.parapet.z, L.parapet.z + 0.05, [M.gold, M.gold]);
// plaster soffit under the balcony
flatPolys([{outer: L.balcony.outline, holes: []}], L.balcony_rows[0].z - L.balcony.slab - 0.02, M.plaster, true);
// brass rail between the members' rows and the public gallery
if (L.split_rail) {
  extrude(L.split_rail.polys, L.split_rail.z0, L.split_rail.z - 0.05, [M.walnut, M.walnut]);
  extrude(L.split_rail.polys, L.split_rail.z - 0.05, L.split_rail.z, [M.gold, M.gold]);
}

// ------------------------------------------------------------------ chairs

function armchair(scale = 1) {
  const RB = (w, h, d, r) => new THREE.RoundedBoxGeometry(d, h, w, 2, r);
  const leather = [
    RB(0.46, 0.13, 0.47, 0.05).translate(0.03, 0.47, 0),                          // seat cushion
    RB(0.46, 0.6, 0.11, 0.05).rotateZ(0.16).translate(-0.2, 0.82, 0),             // back
  ];
  const wood = [
    RB(0.06, 0.07, 0.5, 0.025).translate(0.02, 0.68, 0.255),                      // arms
    RB(0.06, 0.07, 0.5, 0.025).translate(0.02, 0.68, -0.255),
    RB(0.05, 0.27, 0.05, 0.015).translate(0.22, 0.54, 0.255),                     // arm posts
    RB(0.05, 0.27, 0.05, 0.015).translate(0.22, 0.54, -0.255),
    RB(0.5, 0.40, 0.42, 0.03).translate(0.0, 0.20, 0),                            // base
    RB(0.48, 0.05, 0.13, 0.02).rotateZ(0.16).translate(-0.255, 1.12, 0),          // top rail
  ];
  return {leather: merge(leather).scale(scale, scale, scale), wood: merge(wood).scale(scale, scale, scale)};
}
function theatreSeat() {
  const RB = (w, h, d, r) => new THREE.RoundedBoxGeometry(d, h, w, 2, r);
  return {
    leather: merge([RB(0.46, 0.1, 0.45, 0.04).translate(0.05, 0.45, 0), RB(0.46, 0.52, 0.09, 0.04).rotateZ(0.2).translate(-0.17, 0.78, 0)]),
    wood: merge([RB(0.05, 0.55, 0.45, 0.02).translate(0, 0.37, 0.25), RB(0.05, 0.55, 0.45, 0.02).translate(0, 0.37, -0.25)]),
  };
}
function placeSeats(list, geos, upholstery, colorOf) {
  const up = new THREE.Vector3(0, 1, 0), one = new THREE.Vector3(1, 1, 1);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion();
  for (const [geo, mat, colored] of [[geos.leather, upholstery, true], [geos.wood, M.chairWood, false]]) {
    const mesh = new THREE.InstancedMesh(geo, mat, list.length);
    list.forEach((s, i) => {
      q.setFromAxisAngle(up, s.face);
      m4.compose(V(s.x, s.y, s.z), q, one);
      mesh.setMatrixAt(i, m4);
      if (colored && colorOf) mesh.setColorAt(i, new THREE.Color(colorOf(s)));
    });
    mesh.castShadow = true; mesh.receiveShadow = true;
    scene.add(mesh);
  }
}
const partyColor = s => s.party == null ? '#8a7a6a' : L.parties[s.party].color;
const memberColor = VIEW.colors === 'party' ? partyColor : null;
const chairGeo = armchair();
placeSeats(L.floor_seats, chairGeo, M.leather, memberColor);
placeSeats(L.balcony_members, chairGeo, M.leather, memberColor);
placeSeats(L.public, theatreSeat(), M.fabric, null);

// ------------------------------------------------------------------ lighting

scene.add(new THREE.HemisphereLight('#fff7ea', '#6d5a45', 0.45));
const key = new THREE.DirectionalLight('#fff1d8', 1.35);
key.position.copy(V(-3, D * 0.6, 45)); key.target.position.copy(V(0, D * 0.5, 0));
key.castShadow = true; key.shadow.mapSize.set(4096, 4096);
Object.assign(key.shadow.camera, {left: -28, right: 28, top: 24, bottom: -24, near: 10, far: 70});
key.shadow.bias = -0.0003; key.shadow.normalBias = 0.02; key.shadow.radius = 3;
scene.add(key, key.target);
for (const [x, y, z, power] of [[0, 9, 9, 0.9], [-12, 14, 9.5, 0.45], [12, 14, 9.5, 0.45], [0, 20, 9.5, 0.4]]) {
  const p = new THREE.PointLight('#ffe8c8', power, 26, 1.6); p.position.copy(V(x, y, z)); scene.add(p);
}
const rostrumSpot = new THREE.SpotLight('#fff3df', 0.9, 30, 0.6, 0.6, 1.2);
rostrumSpot.position.copy(V(0, 12, 9.5)); rostrumSpot.target.position.copy(V(0, 1, 3)); scene.add(rostrumSpot, rostrumSpot.target);

// ------------------------------------------------------------------ camera

for (const name of VIEW.hide || []) {
  if (name === 'ceiling') ceiling.visible = false;
  else { walls[name].visible = false; for (const d of doorsByWall[name]) d.visible = false; }
}
const cam = new THREE.PerspectiveCamera(VIEW.fov, canvas.width / canvas.height, 0.1, 250);
cam.position.copy(V(...VIEW.eye));
cam.lookAt(V(...VIEW.target));
renderer.render(scene, cam);
window.RENDERED = true;
