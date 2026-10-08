// Realistic model of the enlarged House chamber, built from the layout that
// chamber.py computes (window.LAYOUT) and shot from window.VIEW.
// Layout coordinates: x east, y north (away from the rostrum wall), z up, metres.

window.addEventListener('error', e => { window.FAILED = String(e.message); });

THREE.ColorManagement.legacyMode = false;
const L = window.LAYOUT, VIEW = window.VIEW;
const W = L.hall.w, D = L.hall.d, H = L.hall.h, HW = W / 2;
const [SX, SY] = L.speaker;
const DEG = Math.PI / 180;
const PARTY = VIEW.colors === 'party';

const canvas = document.getElementById('c');
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, preserveDrawingBuffer: true});
renderer.setPixelRatio(1);
renderer.setSize(canvas.width, canvas.height, false);
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = VIEW.exposure || 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color('#14161a');
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new THREE.RoomEnvironment(), 0.04).texture;

const V = (x, y, z) => new THREE.Vector3(x, z, -y);   // layout -> three.js
const groups = {};
for (const name of ['ceiling', 'north', 'south', 'east', 'west']) { groups[name] = new THREE.Group(); scene.add(groups[name]); }

// ------------------------------------------------------------------ textures

let seed = 11;
const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

function canvasTexture(w, h, draw, repeat) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.encoding = THREE.sRGBEncoding;
  t.anisotropy = 8;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  if (repeat) t.repeat.set(repeat[0], repeat[1]);
  return t;
}
function noise(g, w, h, amount, alpha) {
  for (let i = 0; i < amount; i++) {
    g.fillStyle = `rgba(${rand() < 0.5 ? '0,0,0' : '255,255,255'},${alpha * rand()})`;
    g.fillRect(rand() * w, rand() * h, 1 + rand() * 2, 1 + rand() * 2);
  }
}
function star(g, cx, cy, r, points = 5, inner = 0.42) {
  g.beginPath();
  for (let i = 0; i < points * 2; i++) {
    const a = -Math.PI / 2 + i * Math.PI / points, rr = i % 2 ? r * inner : r;
    g.lineTo(cx + rr * Math.cos(a), cy + rr * Math.sin(a));
  }
  g.closePath(); g.fill();
}

// Wood grain, near white so each material tints it (1 texture = 1 m).
const grainTex = canvasTexture(1024, 1024, (g, w, h) => {
  g.fillStyle = '#f3e7da'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 60; i++) {
    const y = rand() * h, hh = 6 + rand() * 50;
    g.fillStyle = rand() < 0.5 ? `rgba(95,52,24,${0.04 + rand() * 0.08})` : `rgba(255,246,232,${0.05 + rand() * 0.09})`;
    g.fillRect(0, y, w, hh);
  }
  for (let i = 0; i < 340; i++) {
    const y0 = rand() * h, amp = 1 + rand() * 6, f = (1 + Math.floor(rand() * 4)) * 2 * Math.PI / w, ph = rand() * 6;
    g.strokeStyle = `rgba(58,28,10,${0.05 + rand() * 0.17})`; g.lineWidth = 0.5 + rand() * 2.2;
    g.beginPath();
    for (let x = 0; x <= w; x += 8) g.lineTo(x, y0 + amp * Math.sin(x * f + ph));
    g.stroke();
  }
  noise(g, w, h, 14000, 0.04);
});

// A raised panel on wood, for bench backs and walnut wainscot (tinted by the material).
function panelTexture(w, h, insets) {
  return canvasTexture(w, h, (g) => {
    g.drawImage(grainTex.image, 0, 0, w, h);
    for (const [x0, y0, x1, y1] of insets) {
      g.fillStyle = 'rgba(45,20,6,0.30)'; g.fillRect(x0, y0, x1 - x0, y1 - y0);
      const b = Math.min(18, (x1 - x0) * 0.08);
      g.fillStyle = 'rgba(255,238,215,0.14)'; g.fillRect(x0 + b, y0 + b, x1 - x0 - 2 * b, y1 - y0 - 2 * b);
      g.lineWidth = 3;
      g.strokeStyle = 'rgba(20,8,2,0.6)';
      g.beginPath(); g.moveTo(x0, y1); g.lineTo(x0, y0); g.lineTo(x1, y0); g.stroke();
      g.strokeStyle = 'rgba(255,232,200,0.45)';
      g.beginPath(); g.moveTo(x1, y0); g.lineTo(x1, y1); g.lineTo(x0, y1); g.stroke();
      g.strokeStyle = 'rgba(20,8,2,0.35)'; g.lineWidth = 2;
      g.beginPath(); g.moveTo(x0 + b, y1 - b); g.lineTo(x1 - b, y1 - b); g.lineTo(x1 - b, y0 + b); g.stroke();
    }
  });
}
const benchPanelTex = panelTexture(512, 512, [[40, 60, 472, 360]]);           // one place, 1 m high
const wallPanelTex = panelTexture(512, 1024, [[48, 70, 464, 790], [48, 850, 464, 990]]);   // one wall bay

// Royal blue carpet with gold rosettes and small gold stars (one tile = 2.4 m).
function rosette(g, cx, cy, R, big) {
  g.save(); g.translate(cx, cy);
  g.fillStyle = '#c99a3c';
  g.beginPath(); g.arc(0, 0, R, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#1f3790'; g.beginPath(); g.arc(0, 0, R * 0.9, 0, Math.PI * 2); g.fill();
  const petals = big ? 24 : 18;
  for (let i = 0; i < petals; i++) {
    g.save(); g.rotate(i * Math.PI * 2 / petals);
    g.fillStyle = i % 2 ? '#d9ae4c' : '#c48f34';
    g.beginPath(); g.ellipse(R * 0.66, 0, R * 0.2, R * 0.075, 0, 0, Math.PI * 2); g.fill();
    g.restore();
  }
  g.fillStyle = '#b1362c'; g.beginPath(); g.arc(0, 0, R * 0.45, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#dcb455'; star(g, 0, 0, R * 0.42, 8, 0.55);
  g.fillStyle = '#9e2a24'; g.beginPath(); g.arc(0, 0, R * 0.12, 0, Math.PI * 2); g.fill();
  g.restore();
}
const carpetTex = canvasTexture(1024, 1024, (g, w, h) => {
  g.fillStyle = '#1f3790'; g.fillRect(0, 0, w, h);
  noise(g, w, h, 60000, 0.06);
  rosette(g, w / 4, h / 4, 128); rosette(g, 3 * w / 4, 3 * h / 4, 128);
  g.fillStyle = '#d4a845';
  for (const [x, y] of [[3 * w / 4, h / 4], [w / 4, 3 * h / 4]]) star(g, x, y, 22, 4, 0.3);
  for (const [x, y] of [[0, 0], [w / 2, 0], [0, h / 2], [w / 2, h / 2], [w, 0], [0, h], [w, h], [w / 2, h], [w, h / 2]]) star(g, x, y, 12, 4, 0.35);
}, [1 / 1.8, 1 / 1.8]);

// Centre-aisle runner: big rosettes down the middle, red and gold border (1.25 x 1.25 m).
const runnerTex = canvasTexture(512, 512, (g, w, h) => {
  g.fillStyle = '#1c338a'; g.fillRect(0, 0, w, h);
  noise(g, w, h, 30000, 0.06);
  for (const x of [0, w]) {
    const s = x ? -1 : 1;
    g.fillStyle = '#c99a3c'; g.fillRect(x + s * 14 - (s < 0 ? 8 : 0), 0, 8, h);
    g.fillStyle = '#a3302a'; g.fillRect(x + s * 26 - (s < 0 ? 10 : 0), 0, 10, h);
    g.fillStyle = '#c99a3c'; g.fillRect(x + s * 40 - (s < 0 ? 4 : 0), 0, 4, h);
  }
  rosette(g, w / 2, h / 2, 125, true);
  g.fillStyle = '#d4a845'; star(g, w / 2, 0, 18, 4, 0.3); star(g, w / 2, h, 18, 4, 0.3);
});
const riserTex = canvasTexture(256, 64, (g, w, h) => {
  g.fillStyle = '#182d78'; g.fillRect(0, 0, w, h); noise(g, w, h, 3000, 0.07);
  g.fillStyle = '#b38c3c'; g.fillRect(0, 0, w, 5);
});

const leatherTex = canvasTexture(256, 256, (g, w, h) => {
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
  for (let i = 0; i < 400; i++) { g.fillStyle = `rgba(80,40,10,${rand() * 0.05})`; g.beginPath(); g.arc(rand() * w, rand() * h, 2 + rand() * 12, 0, Math.PI * 2); g.fill(); }
  noise(g, w, h, 9000, 0.07);
}, [3, 3]);
const fabricTex = canvasTexture(128, 128, (g, w, h) => {
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, w, h);
  g.strokeStyle = 'rgba(0,0,0,0.13)';
  for (let i = 0; i < w; i += 3) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, h); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(w, i); g.stroke(); }
}, [6, 6]);

function marbleTexture(base, vein, alpha, n = 26) {
  return canvasTexture(1024, 1024, (g, w, h) => {
    g.fillStyle = base; g.fillRect(0, 0, w, h);
    for (let i = 0; i < 30; i++) { g.fillStyle = `rgba(${rand() < 0.5 ? '0,0,0' : '255,255,255'},${rand() * 0.04})`; g.beginPath(); g.arc(rand() * w, rand() * h, 40 + rand() * 160, 0, Math.PI * 2); g.fill(); }
    noise(g, w, h, 30000, 0.04);
    for (let i = 0; i < n; i++) {
      g.strokeStyle = vein; g.globalAlpha = alpha * (0.3 + rand()); g.lineWidth = 0.6 + rand() * 2.2;
      g.beginPath(); let x = rand() * w, y = rand() * h; g.moveTo(x, y);
      for (let k = 0; k < 7; k++) { x += (rand() - 0.3) * 220; y += (rand() - 0.5) * 160; g.lineTo(x, y); }
      g.stroke();
    }
    g.globalAlpha = 1;
  });
}
const creamTex = marbleTexture('#ddd0b2', '#a08e6c', 0.22);
const blackTex = marbleTexture('#141716', '#c9d0c6', 0.32, 40);
const whiteTex = marbleTexture('#e8e2d4', '#ada493', 0.15);
// Ceiling coffer: cream field, stepped gilt mouldings, bead border and a centre rosette.
const cofferTex = canvasTexture(512, 512, (g, w, h) => {
  g.fillStyle = '#efe7d6'; g.fillRect(0, 0, w, h);
  noise(g, w, h, 5000, 0.03);
  const ring = (i, col, lw) => { g.strokeStyle = col; g.lineWidth = lw; g.strokeRect(i, i, w - 2 * i, h - 2 * i); };
  ring(8, '#d9c9a6', 14); ring(22, '#c79d45', 6); ring(34, '#e6dbc4', 12); ring(46, 'rgba(110,90,50,0.35)', 3); ring(78, '#c79d45', 3);
  g.fillStyle = '#c79d45';
  for (let k = 0; k < 26; k++) {
    const t = 62 + k * (w - 124) / 25;
    for (const [x, y] of [[t, 62], [t, h - 62], [62, t], [w - 62, t]]) { g.beginPath(); g.ellipse(x, y, 5, 5, 0, 0, Math.PI * 2); g.fill(); }
  }
  g.save(); g.translate(w / 2, h / 2);
  for (let i = 0; i < 16; i++) { g.rotate(Math.PI / 8); g.fillStyle = i % 2 ? '#d6ad54' : '#bc903a'; g.beginPath(); g.ellipse(44, 0, 36, 11, 0, 0, Math.PI * 2); g.fill(); }
  g.fillStyle = '#e9dcc0'; g.beginPath(); g.arc(0, 0, 30, 0, Math.PI * 2); g.fill();
  g.fillStyle = '#c79d45'; g.beginPath(); g.arc(0, 0, 18, 0, Math.PI * 2); g.fill();
  g.restore();
  for (const [x, y] of [[96, 96], [w - 96, 96], [96, h - 96], [w - 96, h - 96]]) {
    g.fillStyle = '#c79d45'; star(g, x, y, 16, 4, 0.4);
  }
});
const plasterTex = canvasTexture(256, 256, (g, w, h) => { g.fillStyle = '#e4d9bf'; g.fillRect(0, 0, w, h); noise(g, w, h, 6000, 0.035); });

// Blue damask of the upper walls (one repeat = 0.6 m).
const damaskTex = canvasTexture(512, 512, (g, w, h) => {
  g.fillStyle = '#3c5878'; g.fillRect(0, 0, w, h);
  noise(g, w, h, 20000, 0.05);
  const motif = (cx, cy, s) => {
    g.save(); g.translate(cx, cy); g.scale(s, s);
    g.fillStyle = 'rgba(140,166,194,0.6)';
    g.beginPath(); g.moveTo(0, -70); g.bezierCurveTo(40, -35, 36, 35, 0, 70); g.bezierCurveTo(-36, 35, -40, -35, 0, -70); g.fill();
    g.fillStyle = 'rgba(44,68,96,0.95)'; g.beginPath(); g.ellipse(0, 0, 13, 32, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = 'rgba(140,166,194,0.5)';
    for (const sx of [-1, 1]) {
      g.beginPath(); g.ellipse(sx * 48, -16, 11, 32, sx * 0.6, 0, Math.PI * 2); g.fill();
      g.beginPath(); g.ellipse(sx * 40, 42, 9, 22, -sx * 0.7, 0, Math.PI * 2); g.fill();
      g.beginPath(); g.arc(sx * 20, -82, 7, 0, Math.PI * 2); g.fill();
    }
    g.restore();
  };
  for (let i = -1; i <= 2; i++) for (let j = -1; j <= 2; j++) { motif(i * 256 + 128, j * 256 + 128, 1); motif(i * 256, j * 256, 0.55); }
  g.strokeStyle = 'rgba(140,166,194,0.25)'; g.lineWidth = 3;
  for (let k = -2; k <= 2; k++) {
    g.beginPath(); g.moveTo(k * 256, 0); g.lineTo(k * 256 + 512, 512); g.stroke();
    g.beginPath(); g.moveTo(k * 256 + 512, 0); g.lineTo(k * 256, 512); g.stroke();
  }
});

// Gilt Greek key on a dark ground (one repeat = 0.6 x 0.3 m).
const greekTex = canvasTexture(256, 128, (g, w, h) => {
  g.fillStyle = '#3b2414'; g.fillRect(0, 0, w, h);
  g.fillStyle = '#c99a3e'; g.fillRect(0, 6, w, 7); g.fillRect(0, h - 13, w, 7);
  g.strokeStyle = '#d2a548'; g.lineWidth = 9; g.lineCap = 'square';
  for (let x = 0; x < w; x += 128) {
    g.beginPath(); g.moveTo(x, 100); g.lineTo(x + 128, 100); g.stroke();
    g.beginPath(); g.moveTo(x + 108, 100); g.lineTo(x + 108, 28); g.lineTo(x + 22, 28); g.lineTo(x + 22, 78); g.lineTo(x + 84, 78); g.lineTo(x + 84, 50); g.lineTo(x + 52, 50); g.stroke();
  }
});

function doorTexture(leaded) {
  return canvasTexture(256, 512, (g, w, h) => {
    g.drawImage(grainTex.image, 0, 0, w, h);
    g.fillStyle = 'rgba(92,48,20,0.78)'; g.fillRect(0, 0, w, h);
    for (const lx of [0, w / 2]) {
      const raised = (x0, y0, x1, y1) => {
        g.fillStyle = 'rgba(30,12,3,0.35)'; g.fillRect(x0, y0, x1 - x0, y1 - y0);
        g.fillStyle = 'rgba(255,220,180,0.10)'; g.fillRect(x0 + 6, y0 + 6, x1 - x0 - 12, y1 - y0 - 12);
        g.strokeStyle = 'rgba(255,220,170,0.35)'; g.lineWidth = 2; g.strokeRect(x0 + 1, y0 + 1, x1 - x0 - 2, y1 - y0 - 2);
      };
      if (leaded) {
        const gx = lx + 20, gy = 34, gw = w / 2 - 40, gh = 300;
        const grad = g.createLinearGradient(gx, gy, gx + gw, gy + gh);
        grad.addColorStop(0, '#c2bea2'); grad.addColorStop(0.5, '#8e8d76'); grad.addColorStop(1, '#5d5d4f');
        g.fillStyle = grad; g.fillRect(gx, gy, gw, gh);
        g.save(); g.beginPath(); g.rect(gx, gy, gw, gh); g.clip();
        g.strokeStyle = '#2b251c'; g.lineWidth = 2.5;
        for (let k = -12; k < 24; k++) {
          g.beginPath(); g.moveTo(gx + k * 22, gy); g.lineTo(gx + k * 22 + gh * 0.55, gy + gh); g.stroke();
          g.beginPath(); g.moveTo(gx + k * 22, gy); g.lineTo(gx + k * 22 - gh * 0.55, gy + gh); g.stroke();
        }
        g.restore();
        g.strokeStyle = '#c9a24a'; g.lineWidth = 4; g.strokeRect(gx - 3, gy - 3, gw + 6, gh + 6);
        raised(lx + 20, 370, lx + w / 2 - 20, 488);
      } else {
        raised(lx + 20, 26, lx + w / 2 - 20, 150); raised(lx + 20, 170, lx + w / 2 - 20, 340); raised(lx + 20, 360, lx + w / 2 - 20, 488);
      }
    }
    g.fillStyle = 'rgba(15,6,2,0.8)'; g.fillRect(w / 2 - 2, 0, 4, h);
    g.fillStyle = '#d6b25a'; for (const x of [w / 2 - 14, w / 2 + 8]) g.fillRect(x, h * 0.55, 6, 22);
  });
}
const leadedDoorTex = doorTexture(true), panelDoorTex = doorTexture(false);

function portraitTexture(dark) {
  return canvasTexture(512, 680, (g, w, h) => {
    const bg = g.createRadialGradient(w * 0.45, h * 0.3, 20, w * 0.5, h * 0.5, w * 0.95);
    bg.addColorStop(0, '#7a6744'); bg.addColorStop(0.6, '#3d3322'); bg.addColorStop(1, '#17130c');
    g.fillStyle = bg; g.fillRect(0, 0, w, h);
    g.fillStyle = 'rgba(160,140,100,0.35)'; g.fillRect(0, h * 0.62, w, h * 0.38);
    g.fillStyle = dark; g.beginPath();
    g.moveTo(w * 0.3, h); g.lineTo(w * 0.34, h * 0.46); g.quadraticCurveTo(w * 0.5, h * 0.36, w * 0.66, h * 0.46); g.lineTo(w * 0.72, h); g.fill();
    g.fillStyle = '#efe7d8'; g.fillRect(w * 0.465, h * 0.37, w * 0.07, h * 0.06);
    g.fillStyle = '#d8b18b'; g.beginPath(); g.ellipse(w * 0.5, h * 0.31, w * 0.065, h * 0.06, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#e6e1d6'; g.beginPath(); g.ellipse(w * 0.5, h * 0.28, w * 0.075, h * 0.05, 0, Math.PI, Math.PI * 2); g.fill();
    g.fillStyle = '#d8b18b'; g.beginPath(); g.arc(w * 0.66, h * 0.66, w * 0.025, 0, Math.PI * 2); g.fill();
    noise(g, w, h, 20000, 0.05);
  });
}

// ------------------------------------------------------------------ materials

const std = o => new THREE.MeshStandardMaterial(o);
const M = {
  carpet: std({map: carpetTex, roughness: 0.96, envMapIntensity: 0.2}),
  carpetSide: std({color: '#1a2f7a', roughness: 0.96, envMapIntensity: 0.2}),
  riser: std({map: riserTex, roughness: 0.96, envMapIntensity: 0.2}),
  runner: std({map: runnerTex, roughness: 0.96, envMapIntensity: 0.2, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2}),
  bench: std({map: grainTex, color: '#6b3418', roughness: 0.38, envMapIntensity: 0.55}),
  benchPanel: std({map: benchPanelTex, color: '#6b3418', roughness: 0.38, envMapIntensity: 0.55}),
  honey: std({map: grainTex, color: '#a2683a', roughness: 0.35, envMapIntensity: 0.55}),
  honeyPanel: std({map: benchPanelTex, color: '#a2683a', roughness: 0.35, envMapIntensity: 0.55}),
  carved: std({map: grainTex, color: '#6e4222', roughness: 0.45, envMapIntensity: 0.5}),
  walnut: std({map: grainTex, color: '#4f2c16', roughness: 0.42, envMapIntensity: 0.5}),
  walnutPanel: std({map: wallPanelTex, color: '#4f2c16', roughness: 0.42, envMapIntensity: 0.5}),
  parapet: std({map: benchPanelTex, color: '#4f2c16', roughness: 0.42, envMapIntensity: 0.5}),
  leather: std({map: leatherTex, roughness: 0.48, envMapIntensity: 0.55}),
  chairLeather: std({map: leatherTex, color: '#8a4a26', roughness: 0.48, envMapIntensity: 0.55}),
  fabric: std({map: fabricTex, roughness: 0.95, envMapIntensity: 0.2}),
  cream: std({map: creamTex, color: '#e4d9c6', roughness: 0.32, envMapIntensity: 0.55}),
  black: std({map: blackTex, roughness: 0.14, envMapIntensity: 1.0}),
  white: std({map: whiteTex, roughness: 0.3, envMapIntensity: 0.7}),
  greenMarble: std({map: blackTex, color: '#6f8f78', roughness: 0.18, envMapIntensity: 0.9}),
  plaster: std({map: plasterTex, roughness: 0.9, envMapIntensity: 0.35}),
  coffer: std({map: cofferTex, roughness: 0.75, envMapIntensity: 0.35}),
  damask: std({map: damaskTex, roughness: 0.85, envMapIntensity: 0.3}),
  greek: std({map: greekTex, roughness: 0.38, metalness: 0.35, envMapIntensity: 0.9}),
  gold: std({color: '#c99a3e', roughness: 0.3, metalness: 1.0, envMapIntensity: 1.15}),
  brass: std({color: '#c39a48', roughness: 0.22, metalness: 1.0, envMapIntensity: 1.2}),
  silver: std({color: '#d6d6d6', roughness: 0.2, metalness: 1.0}),
  bronze: std({color: '#7a5a2c', roughness: 0.35, metalness: 1.0, envMapIntensity: 1.0}),
  dark: std({color: '#151515', roughness: 0.5}),
  chrome: std({color: '#9a9a9a', roughness: 0.15, metalness: 1.0}),
  leadedDoor: std({map: leadedDoorTex, roughness: 0.35, envMapIntensity: 0.6}),
  panelDoor: std({map: panelDoorTex, roughness: 0.4, envMapIntensity: 0.5}),
  bulb: new THREE.MeshBasicMaterial({color: '#fff3d6'}),
  glass: std({color: '#d6e6e8', transparent: true, opacity: 0.16, roughness: 0.04, metalness: 0.1, envMapIntensity: 1.6, depthWrite: false, side: THREE.DoubleSide}),
};
const NO_AO = [];   // see-through things the ambient occlusion pass should ignore

// ------------------------------------------------------------------ geometry helpers

const nV = n => new THREE.Vector3(n[0], n[2], -n[1]);

// Collects quads given in layout coordinates into one mesh.
class Builder {
  constructor() { this.p = []; this.n = []; this.uv = []; }
  quad(ps, ns, uvs) {
    const P = ps.map(p => V(p[0], p[1], p[2]));
    const N = (Array.isArray(ns[0]) ? ns : [ns, ns, ns, ns]).map(nV);
    let f = P[1].clone().sub(P[0]).cross(P[2].clone().sub(P[0]));
    if (f.lengthSq() < 1e-14) f = P[2].clone().sub(P[0]).cross(P[3].clone().sub(P[0]));
    const order = f.dot(N[0].clone().add(N[2])) >= 0 ? [0, 1, 2, 0, 2, 3] : [0, 2, 1, 0, 3, 2];
    for (const i of order) { this.p.push(P[i].x, P[i].y, P[i].z); this.n.push(N[i].x, N[i].y, N[i].z); this.uv.push(uvs[i][0], uvs[i][1]); }
  }
  mesh(material, {cast = true, parent = scene} = {}) {
    if (!this.p.length) return null;
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    const m = new THREE.Mesh(g, material); m.castShadow = cast; m.receiveShadow = true; parent.add(m);
    return m;
  }
}

// A curved box: the part of a ring r0..r1 between angles a0..a1 (radians), z0..z1.
function arcBox(o) {
  const cx = o.cx ?? SX, cy = o.cy ?? SY, {r0, r1, a0, a1, z0, z1} = o;
  const seg = o.seg || Math.max(1, Math.ceil((a1 - a0) / (1.5 * DEG)));
  const P = (r, a, z) => [cx + r * Math.cos(a), cy + r * Math.sin(a), z];
  const R = (a, s) => [s * Math.cos(a), s * Math.sin(a), 0];
  const wood = (r, a, z) => [r * (a - a0), z];
  const woodTop = (r, a) => [r * (a - a0), r];
  const flat = (r, a) => { const p = P(r, a, 0); return [p[0], p[1]]; };
  for (let k = 0; k < seg; k++) {
    const t0 = a0 + (a1 - a0) * k / seg, t1 = a0 + (a1 - a0) * (k + 1) / seg;
    for (const [b, r, s, uvf] of [[o.outer, r1, 1, o.outerUV || wood], [o.inner, r0, -1, o.innerUV || wood]]) {
      if (!b) continue;
      b.quad([P(r, t0, z0), P(r, t1, z0), P(r, t1, z1), P(r, t0, z1)], [R(t0, s), R(t1, s), R(t1, s), R(t0, s)],
             [uvf(r, t0, z0), uvf(r, t1, z0), uvf(r, t1, z1), uvf(r, t0, z1)]);
    }
    for (const [b, z, s] of [[o.top, z1, 1], [o.bottom, z0, -1]]) {
      if (!b) continue;
      const uvf = o.topUV === 'flat' ? flat : woodTop;
      b.quad([P(r0, t0, z), P(r1, t0, z), P(r1, t1, z), P(r0, t1, z)], [0, 0, s], [uvf(r0, t0), uvf(r1, t0), uvf(r1, t1), uvf(r0, t1)]);
    }
  }
  if (o.ends) for (const [a, s] of [[a0, -1], [a1, 1]]) {
    o.ends.quad([P(r0, a, z0), P(r1, a, z0), P(r1, a, z1), P(r0, a, z1)], [-s * Math.sin(a), s * Math.cos(a), 0],
                [[r0, z0], [r1, z0], [r1, z1], [r0, z1]]);
  }
}

function boxUV(g, w, h, d, scale) {
  const uv = g.attributes.uv, dims = [[d, h], [d, h], [w, d], [w, d], [w, h], [w, h]];
  for (let f = 0; f < 6; f++) for (let i = 0; i < 4; i++) {
    const k = f * 4 + i; uv.setXY(k, uv.getX(k) * dims[f][0] / scale, uv.getY(k) * dims[f][1] / scale);
  }
}
function add(mesh, parent = scene, cast = true) { mesh.castShadow = cast; mesh.receiveShadow = true; parent.add(mesh); return mesh; }
// box centred on (x, y), from z up, rotated so its width runs along angle rot
function box(x, y, z, w, d, h, mat, rot = 0, parent = scene, uvScale = 1) {
  const g = new THREE.BoxGeometry(w, h, d); boxUV(g, w, h, d, uvScale);
  const m = new THREE.Mesh(g, mat); m.position.copy(V(x, y, z + h / 2)); m.rotation.y = rot;
  return add(m, parent);
}
function cylinder(x, y, z, r, h, mat, seg = 24, r2 = r, parent = scene) {
  const m = new THREE.Mesh(new THREE.CylinderGeometry(r2, r, h, seg), mat);
  m.position.copy(V(x, y, z + h / 2));
  return add(m, parent);
}
function shapeFrom(outer, holes = []) {
  const s = new THREE.Shape(outer.map(([x, y]) => new THREE.Vector2(x, y)));
  for (const h of holes) s.holes.push(new THREE.Path(h.map(([x, y]) => new THREE.Vector2(x, y))));
  return s;
}
function extrude(outer, z0, z1, materials, holes = [], parent = scene) {
  if (z1 - z0 < 0.005) z1 = z0 + 0.005;
  const g = new THREE.ExtrudeGeometry(shapeFrom(outer, holes), {depth: z1 - z0, bevelEnabled: false, curveSegments: 1});
  g.rotateX(-Math.PI / 2); g.translate(0, z0, 0);
  return add(new THREE.Mesh(g, materials), parent);
}
function merge(geos) {
  const parts = geos.map(g => g.index ? g.toNonIndexed() : g);
  const out = new THREE.BufferGeometry();
  for (const name of ['position', 'normal', 'uv']) {
    const arrays = parts.map(p => p.attributes[name].array);
    const merged = new Float32Array(arrays.reduce((n, a) => n + a.length, 0));
    let o = 0; for (const a of arrays) { merged.set(a, o); o += a.length; }
    out.setAttribute(name, new THREE.BufferAttribute(merged, parts[0].attributes[name].itemSize));
  }
  return out;
}
const RB = (x, y, z, r, seg = 2) => new THREE.RoundedBoxGeometry(x, y, z, seg, r);
// rotation that turns an object's local +z (and x along the face) to face layout direction (nx, ny)
const facing = (nx, ny) => Math.atan2(nx, -ny);
function pip(poly, x, y) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}
function floorAt(x, y) {
  let z = 0;
  for (const b of L.bands) for (const p of b.polys) if (b.z > z && pip(p.outer, x, y)) z = b.z;
  return z;
}
const [AMIN, AMAX] = L.angles, [CLX, CLY] = L.clearance;
// angle ranges (radians) where a ring of radius r is inside the tiered area
function arcRanges(r) {
  const out = []; let start = null, prev = null;
  for (let a = AMIN; a <= AMAX + 1e-9; a += 0.1) {
    const x = SX + r * Math.cos(a * DEG), y = SY + r * Math.sin(a * DEG);
    const ok = Math.abs(x) <= HW - 0.01 && y <= D - 0.01 && !(Math.abs(x) < CLX && y < CLY);
    if (ok && start === null) start = a;
    if (!ok && start !== null) { out.push([start * DEG, prev * DEG]); start = null; }
    prev = a;
  }
  if (start !== null) out.push([start * DEG, AMAX * DEG]);
  return out;
}

// ------------------------------------------------------------------ floor and tiers

const floorGeo = new THREE.PlaneGeometry(W, D + 4);
floorGeo.attributes.uv.array.forEach((v, i, a) => { a[i] = v * (i % 2 ? D + 4 : W); });
const floorMesh = new THREE.Mesh(floorGeo, M.carpet);
floorMesh.rotation.x = -Math.PI / 2; floorMesh.position.copy(V(0, D / 2 - 2, 0)); floorMesh.receiveShadow = true;
scene.add(floorMesh);

for (const b of L.bands) for (const p of b.polys) extrude(p.outer, 0, b.z, [M.carpet, M.carpetSide], p.holes);

// risers with a gold nosing, and the half steps in the steeper aisles
const B = {riser: new Builder(), carpet: new Builder(), carpetSide: new Builder()};
const riserUV = (z0, z1) => (r, a, z) => [r * a, (z - z0) / (z1 - z0)];
L.rows.forEach((row, i) => {
  const prev = L.rows[i - 1];
  if (prev && prev.kind !== row.kind) return;          // behind the rail
  const z0 = prev ? prev.z : 0, r = row.r - row.depth / 2 - 0.003;
  for (const [a0, a1] of arcRanges(r)) arcBox({r0: r, r1: r, a0, a1, z0, z1: row.z, inner: B.riser, innerUV: riserUV(z0, row.z)});
});
const AISLE_ANGLES = [...L.aisles, 90];
const stepped = [];   // rows whose aisles get a half step
L.rows.forEach((row, i) => {
  const nxt = L.rows[i + 1];
  if (!nxt || nxt.kind !== row.kind || nxt.z - row.z <= 0.26) return;
  const rOut = nxt.r - nxt.depth / 2, rIn = rOut - 0.42, zs = row.z + (nxt.z - row.z) / 2;
  stepped.push({row: i, y: rIn, z: zs});
  for (const a of AISLE_ANGLES) {
    const hw = ((a === 90 ? L.centre_aisle : L.aisle_width) / 2 - 0.03) / rOut;
    arcBox({r0: rIn, r1: rOut, a0: a * DEG - hw, a1: a * DEG + hw, z0: row.z, z1: zs, top: B.carpet, topUV: 'flat',
            inner: B.riser, innerUV: riserUV(row.z, zs), ends: B.carpetSide, seg: 2});
  }
});
B.riser.mesh(M.riser, {cast: false}); B.carpet.mesh(M.carpet); B.carpetSide.mesh(M.carpetSide);

// the centre-aisle runner, from the well over every tier and step to the top
{
  const members = L.rows.filter(r => r.kind === 'member');
  const pts = [[CLY, 0]];
  let z = 0;
  members.forEach((row, i) => {
    const y0 = SY + row.r - row.depth / 2;
    pts.push([y0, z], [y0, row.z]); z = row.z;
    const st = stepped.find(s => s.row === L.rows.indexOf(row));
    if (st) { pts.push([SY + st.y, z], [SY + st.y, st.z]); z = st.z; }
  });
  pts.push([SY + L.aisle.r_out, z]);
  const b = new Builder(), RW = 1.25, RL = 1.25;
  for (let i = 0; i + 1 < pts.length; i++) {
    const [y0, z0] = pts[i], [y1, z1] = pts[i + 1], len = Math.hypot(y1 - y0, z1 - z0);
    if (len < 1e-4) continue;
    if (z1 === z0) b.quad([[-RW / 2, y0, z0 + 0.004], [RW / 2, y0, z0 + 0.004], [RW / 2, y1, z0 + 0.004], [-RW / 2, y1, z0 + 0.004]], [0, 0, 1], [[0, y0 / RL], [1, y0 / RL], [1, y1 / RL], [0, y1 / RL]]);
    else b.quad([[-RW / 2, y0 - 0.005, z0], [RW / 2, y0 - 0.005, z0], [RW / 2, y0 - 0.005, z1], [-RW / 2, y0 - 0.005, z1]], [0, -1, 0], [[0, 0.1], [1, 0.1], [1, 0.1], [0, 0.1]]);
  }
  b.mesh(M.runner, {cast: false});
}

// walnut screens stepping up both open ends of the bowl
{
  for (const sc of L.screens) for (const p of sc.polys) {
    extrude(p.outer, 0, sc.z + 0.95, [M.walnut, M.walnut]);
    extrude(p.outer, sc.z + 0.95, sc.z + 1.0, [M.brass, M.brass]);
  }
}

// the rail between the members' bowl and the public rows
{
  const rail = new Builder(), wood = new Builder(), cap = new Builder();
  const pub = L.rows.find(r => r.kind === 'public');
  const r = pub.r - pub.depth / 2, z0 = L.aisle.z, z1 = L.aisle.z + 0.95;
  for (const [a0, a1] of arcRanges(r - 0.07)) {
    arcBox({r0: r - 0.14, r1: r, a0, a1, z0, z1, inner: rail, innerUV: (rr, a, z) => [rr * a / 1.4, (z - z0) / (z1 - z0)], outer: wood, ends: wood});
    arcBox({r0: r - 0.17, r1: r + 0.02, a0, a1, z0: z1, z1: z1 + 0.06, inner: cap, outer: cap, top: cap, ends: cap});
  }
  rail.mesh(M.parapet); wood.mesh(M.walnut); cap.mesh(M.brass);
  // a security screen of laminated glass in a bronze frame, 1.7 m above the rail
  const glass = new Builder(), frame = new Builder(), g0 = z1 + 0.06, g1 = g0 + 1.7, rg = r - 0.07;
  for (const [a0, a1] of arcRanges(rg)) {
    arcBox({r0: rg - 0.01, r1: rg + 0.01, a0, a1, z0: g0, z1: g1, inner: glass, outer: glass});
    arcBox({r0: rg - 0.04, r1: rg + 0.04, a0, a1, z0: g1, z1: g1 + 0.06, inner: frame, outer: frame, top: frame, ends: frame});
    const n = Math.max(1, Math.round((a1 - a0) * rg / 1.8));
    for (let k = 0; k <= n; k++) {
      const a = a0 + (a1 - a0) * k / n, da = 0.025 / rg;
      arcBox({r0: rg - 0.04, r1: rg + 0.04, a0: a - da, a1: a + da, z0: g0, z1: g1, inner: frame, outer: frame, ends: frame, seg: 1});
    }
  }
  NO_AO.push(glass.mesh(M.glass, {cast: false}));
  frame.mesh(M.bronze);
}

// brass handrails down the steeper side aisles
{
  const mat = M.brass, rows = L.rows;
  const tube = (p, q, rad) => {
    const a = V(...p), b = V(...q), len = a.distanceTo(b);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, len, 8), mat);
    m.position.copy(a).add(b).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), b.clone().sub(a).normalize());
    add(m, scene, false);
  };
  for (const kind of ['member', 'public']) {
    const list = rows.filter(r => r.kind === kind && (kind === 'public' || r.z >= 3.2));
    for (const a of L.aisles) {
      const pts = list.map(r => { const rr = r.r; return [SX + rr * Math.cos(a * DEG), SY + rr * Math.sin(a * DEG), r.z]; });
      for (let i = 0; i < pts.length; i++) {
        const [x, y, z] = pts[i];
        tube([x, y, z], [x, y, z + 0.9], 0.018);
        if (i + 1 < pts.length) tube([x, y, z + 0.9], [pts[i + 1][0], pts[i + 1][1], pts[i + 1][2] + 0.9], 0.024);
      }
    }
  }
}

// ------------------------------------------------------------------ benches

const UP = new THREE.Vector3(0, 1, 0), ONE = new THREE.Vector3(1, 1, 1);
function seatMatrix(s, lx, lz, sz = 1) {
  const q = new THREE.Quaternion().setFromAxisAngle(UP, s.face);
  return new THREE.Matrix4().compose(V(s.x, s.y, s.z), q, ONE).multiply(new THREE.Matrix4().makeTranslation(lx, 0, lz))
    .multiply(new THREE.Matrix4().makeScale(1, 1, sz));
}
function instanced(geo, mat, matrices, colors) {
  if (!matrices.length) return;
  const mesh = new THREE.InstancedMesh(geo, mat, matrices.length);
  matrices.forEach((m, i) => mesh.setMatrixAt(i, m));
  if (colors) colors.forEach((c, i) => mesh.setColorAt(i, c));
  mesh.castShadow = mesh.receiveShadow = true; scene.add(mesh);
}

// one place on a bench: local x forward (towards the Speaker), y up, z to the occupant's right
const cushionGeo = RB(0.46, 0.085, 0.53, 0.035).translate(-0.10, 0.415, 0);
const backGeo = RB(0.07, 0.46, 0.5, 0.03).rotateZ(0.12).translate(-0.315, 0.73, 0);
const armGeo = merge([RB(0.40, 0.25, 0.04, 0.012, 1).translate(-0.15, 0.585, 0),
                      RB(0.50, 0.05, 0.075, 0.022, 1).translate(-0.11, 0.725, 0),
                      RB(0.075, 0.1, 0.08, 0.03, 1).translate(0.12, 0.71, 0)]);
const endShape = new THREE.Shape();
endShape.moveTo(-0.455, 0); endShape.lineTo(0.15, 0); endShape.lineTo(0.15, 0.64);
endShape.quadraticCurveTo(0.17, 0.77, 0.04, 0.775);
endShape.lineTo(-0.2, 0.78);
endShape.quadraticCurveTo(-0.33, 0.8, -0.37, 0.98);
endShape.quadraticCurveTo(-0.39, 1.09, -0.455, 1.09);
endShape.lineTo(-0.455, 0);
const endGeo = new THREE.ExtrudeGeometry(endShape, {depth: 0.05, bevelEnabled: true, bevelThickness: 0.006, bevelSize: 0.006, bevelSegments: 1, curveSegments: 6}).translate(0, 0, -0.025);
const voteGeo = new THREE.BoxGeometry(0.03, 0.075, 0.14).translate(0, 0.82, 0);

function benchesOf(seats, cx, cy) {
  const out = []; let cur = null;
  for (const s of seats) {
    if (!cur || s.end_lo) { cur = {seats: [], z: s.z, cx, cy}; out.push(cur); }
    cur.seats.push(s);
  }
  for (const b of out) {
    const f = b.seats[0], l = b.seats[b.seats.length - 1];
    b.r = Math.hypot(f.x - cx, f.y - cy);
    const af = Math.atan2(f.y - cy, f.x - cx), al = Math.atan2(l.y - cy, l.x - cx);
    b.step = b.seats.length > 1 ? (al - af) / (b.seats.length - 1) : 0.58 / b.r;
    b.a0 = af - b.step / 2; b.a1 = al + b.step / 2;
  }
  return out;
}

const caramel = new THREE.Color('#9c5426'), blue = new THREE.Color('#2c3f72');
function buildBenches(benches, {depth, upholstery, colorOf, votes}) {
  const shift = 0.46 - depth / 2;                // local x shift so the back sits at the tier's edge
  const wood = new Builder(), panel = new Builder();
  const parts = {cushion: [], back: [], arm: [], end: [], vote: []}, colors = [];
  for (const b of benches) {
    const back1 = b.r + depth / 2 - 0.02, back0 = back1 - 0.08, z = b.z;
    const common = {cx: b.cx, cy: b.cy, a0: b.a0, a1: b.a1, seg: Math.max(1, b.seats.length * 2)};
    arcBox({...common, r0: back0, r1: back1, z0: z, z1: z + 1.0, outer: panel, outerUV: (r, a, zz) => [(a - b.a0) / b.step, zz - z], inner: wood});
    arcBox({...common, r0: back0 - 0.03, r1: back1 + 0.025, z0: z + 1.0, z1: z + 1.05, outer: wood, inner: wood, top: wood});
    arcBox({...common, r0: b.r - 0.11 - shift, r1: back0, z0: z, z1: z + 0.37, inner: wood, top: wood});
    b.seats.forEach((s, i) => {
      const w = b.step * b.r;
      const sz = (w - 0.06) / 0.53;      // cushions fill the place between the arms
      parts.cushion.push(seatMatrix(s, shift, 0, sz)); parts.back.push(seatMatrix(s, shift, 0, sz));
      colors.push(colorOf(s));
      if (!s.end_lo) parts.arm.push(seatMatrix(s, shift, -w / 2));
      if (s.end_lo) parts.end.push(seatMatrix(s, shift, -w / 2 - 0.028));
      if (s.end_hi) parts.end.push(seatMatrix(s, shift, w / 2 + 0.028));
      if (votes && (s.end_lo || s.end_hi || i % 8 === 4)) parts.vote.push(seatMatrix(s, shift - 0.455, 0));
    });
  }
  panel.mesh(M.benchPanel); wood.mesh(M.bench);
  instanced(cushionGeo, upholstery, parts.cushion, colors);
  instanced(backGeo, upholstery, parts.back, colors);
  instanced(armGeo, M.bench, parts.arm);
  instanced(endGeo, M.bench, parts.end);
  instanced(voteGeo, M.dark, parts.vote);
}
const jitter = c => c.clone().offsetHSL((rand() - 0.5) * 0.01, (rand() - 0.5) * 0.06, (rand() - 0.5) * 0.04);
const partyColor = s => new THREE.Color(s.party == null ? '#8c7f73' : L.parties[s.party].color);
buildBenches(benchesOf(L.members, SX, SY), {depth: L.rows[0].depth, upholstery: M.leather, votes: true,
             colorOf: PARTY ? partyColor : () => jitter(caramel)});
const pubDepth = L.rows.find(r => r.kind === 'public').depth;
buildBenches(benchesOf(L.public, SX, SY), {depth: pubDepth, upholstery: M.fabric, colorOf: () => jitter(blue)});

// ------------------------------------------------------------------ chairs, lecterns, tables

function chair(x, y, z, face, {backH = 0.62, scale = 1, swivel = true} = {}) {
  const g = new THREE.Group();
  const leather = [RB(0.5, 0.12, 0.52, 0.05).translate(0.02, 0.5, 0), RB(0.12, backH, 0.54, 0.05).rotateZ(0.1).translate(-0.24, 0.56 + backH / 2, 0)];
  const arms = [RB(0.42, 0.07, 0.08, 0.03).translate(0.0, 0.7, 0.29), RB(0.42, 0.07, 0.08, 0.03).translate(0.0, 0.7, -0.29),
                RB(0.06, 0.22, 0.06, 0.02).translate(0.16, 0.6, 0.29), RB(0.06, 0.22, 0.06, 0.02).translate(0.16, 0.6, -0.29)];
  g.add(add(new THREE.Mesh(merge(leather), M.chairLeather), g));
  g.add(add(new THREE.Mesh(merge(arms), M.honey), g));
  if (swivel) {
    g.add(add(new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.4, 10).translate(0, 0.24, 0), M.chrome), g));
    for (let k = 0; k < 5; k++) {
      const leg = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.035, 0.04).translate(0.15, 0.05, 0), M.chrome);
      leg.rotation.y = k * Math.PI * 2 / 5; g.add(add(leg, g));
    }
  } else g.add(add(new THREE.Mesh(RB(0.48, 0.42, 0.5, 0.03, 1).translate(0, 0.22, 0), M.honey), g));
  g.position.copy(V(x, y, z)); g.rotation.y = face; g.scale.setScalar(scale);
  scene.add(g); return g;
}
function gooseneck(x, y, z, face, len = 0.42) {
  const d = [Math.cos(face), Math.sin(face)];
  const pts = [[0, 0, 0], [0, 0, len * 0.55], [len * 0.25, 0, len * 0.85], [len * 0.5, 0, len * 0.9]]
    .map(([f, , h]) => V(x + d[0] * f, y + d[1] * f, z + h));
  const m = new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 16, 0.0045, 6), M.dark);
  add(m, scene, false);
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.016, 10, 8), M.dark); head.scale.set(1, 1.6, 1);
  head.position.copy(pts[3]); add(head, scene, false);
}
// a lectern whose reader faces `face`; the sloped top tilts towards the reader
function lectern(x, y, z, face, {w = 0.62, d = 0.48, pedestal = 0}) {
  const g = new THREE.Group();
  if (pedestal) {
    g.add(add(new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.06, 0.5).translate(0, 0.03, 0), M.honey), g));
    g.add(add(new THREE.Mesh(new THREE.BoxGeometry(0.16, pedestal, 0.16).translate(0, pedestal / 2, 0), M.honey), g));
  }
  const top = new THREE.Mesh(new THREE.BoxGeometry(d, 0.05, w), M.honey);
  top.position.set(0, pedestal + 0.12, 0); top.rotation.z = -0.32; g.add(add(top, g));
  const body = new THREE.Mesh(new THREE.BoxGeometry(d * 0.9, 0.12, w * 0.96).translate(0, pedestal + 0.05, 0), M.honey); g.add(add(body, g));
  g.position.copy(V(x, y, z)); g.rotation.y = face + Math.PI; scene.add(g);
  gooseneck(x + Math.cos(face) * 0.2, y + Math.sin(face) * 0.2, z + pedestal + 0.15, face + Math.PI, 0.38);
}

// leadership tables at the front of each side
for (const t of L.tables) {
  const r = t.r, a0 = t.a0 * DEG, a1 = t.a1 * DEG, z = t.z;
  const wood = new Builder(), panel = new Builder(), top = new Builder();
  arcBox({r0: r - 0.34, r1: r + 0.3, a0: a0 + 0.004, a1: a1 - 0.004, z0: z, z1: z + 0.72, inner: panel, innerUV: (rr, a, zz) => [rr * (a - a0) / 1.2, (zz - z) / 0.72 * 0.75], outer: wood, ends: wood});
  arcBox({r0: r - 0.44, r1: r + 0.42, a0, a1, z0: z + 0.72, z1: z + 0.77, inner: top, outer: top, top, ends: top});
  panel.mesh(M.honeyPanel); wood.mesh(M.honey); top.mesh(M.honey);
  const mid = (a0 + a1) / 2, reader = mid;   // the reader stands behind the table, facing the Speaker
  const lx = SX + (r + 0.12) * Math.cos(mid), ly = SY + (r + 0.12) * Math.sin(mid);
  lectern(lx, ly, z + 0.77, reader + Math.PI, {w: 0.6, d: 0.42});
  for (const da of [-0.35, 0.35]) {
    const a = mid + da * (a1 - a0);
    gooseneck(SX + (r - 0.25) * Math.cos(a), SY + (r - 0.25) * Math.sin(a), z + 0.77, a);
  }
}

// the well: two lecterns and the small round table
for (const s of [-1, 1]) lectern(s * 2.35, 6.55, 0, Math.PI / 2, {w: 0.62, d: 0.45, pedestal: 1.0});
cylinder(0, 6.85, 0, 0.09, 0.72, M.honey, 16);
cylinder(0, 6.85, 0, 0.35, 0.05, M.honey, 24);
cylinder(0, 6.85, 0.72, 0.52, 0.04, M.honey, 40);
for (const s of [-1, 1]) chair(s * 0.85, 6.85, 0, s > 0 ? Math.PI : 0, {backH: 0.55});

// ------------------------------------------------------------------ rostrum

function offsetLine(pts, d) {   // offset an open polyline by d to its left
  const segs = [];
  for (let i = 0; i + 1 < pts.length; i++) {
    const [x0, y0] = pts[i], [x1, y1] = pts[i + 1], len = Math.hypot(x1 - x0, y1 - y0);
    const nx = -(y1 - y0) / len, ny = (x1 - x0) / len;
    segs.push([[x0 + nx * d, y0 + ny * d], [x1 + nx * d, y1 + ny * d]]);
  }
  const hit = ([[x1, y1], [x2, y2]], [[x3, y3], [x4, y4]]) => {
    const den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
    if (Math.abs(den) < 1e-9) return [x2, y2];
    const t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den;
    return [x1 + t * (x2 - x1), y1 + t * (y2 - y1)];
  };
  const out = [segs[0][0]];
  for (let i = 0; i + 1 < segs.length; i++) out.push(hit(segs[i], segs[i + 1]));
  out.push(segs[segs.length - 1][1]);
  return out;
}
// the three tiers, lowest first; each front runs east -> west with the inside on its left
const TIERS = [
  {hw: 6.25, front: [[6.25, 3.4], [4.3, 5.2], [-4.3, 5.2], [-6.25, 3.4]], floor: 0.3, desk: 1.12, depth: 0.55, medallions: true},
  {hw: 4.6, front: [[4.6, 2.75], [3.5, 3.85], [-3.5, 3.85], [-4.6, 2.75]], floor: 0.72, desk: 1.72, depth: 0.45, medallions: true},
  {hw: 2.4, front: [[2.4, 2.0], [1.8, 2.6], [-1.8, 2.6], [-2.4, 2.0]], floor: 1.25, desk: 2.32, depth: 0.45, medallions: false},
];
for (const t of TIERS) {
  const outline = [[t.hw, 0], ...t.front, [-t.hw, 0]];
  extrude(outline, 0, t.floor, [M.carpet, M.honey]);
  const inner = offsetLine(t.front, t.depth);
  extrude([...t.front, ...inner.slice().reverse()], 0, t.desk, [M.honey, M.honey]);
  const capOut = offsetLine(t.front, -0.05), capIn = offsetLine(t.front, t.depth + 0.02);
  extrude([...capOut, ...capIn.slice().reverse()], t.desk, t.desk + 0.06, [M.cream, M.cream]);
  // carved front: plinth, rails, panels with round medallions
  for (let i = 0; i + 1 < t.front.length; i++) {
    const [x0, y0] = t.front[i], [x1, y1] = t.front[i + 1], len = Math.hypot(x1 - x0, y1 - y0);
    const nx = (y1 - y0) / len, ny = -(x1 - x0) / len, rot = facing(nx, ny);
    const at = (f, off) => [x0 + (x1 - x0) * f + nx * off, y0 + (y1 - y0) * f + ny * off];
    const [mx, my] = at(0.5, 0.025);
    box(mx, my, 0, len, 0.05, 0.14, M.carved, rot);
    box(mx, my, 0.24, len, 0.03, 0.04, M.carved, rot);
    box(mx, my, t.desk - 0.16, len, 0.03, 0.04, M.carved, rot);
    const bays = Math.max(1, Math.round(len / 1.35));
    for (let k = 0; k <= bays; k++) { const [sx, sy] = at(k / bays, 0.02); box(sx, sy, 0.14, 0.06, 0.04, t.desk - 0.3, M.carved, rot); }
    if (!t.medallions) continue;
    for (let k = 0; k < bays; k++) {
      const [cx, cy] = at((k + 0.5) / bays, 0.03), zc = (0.28 + t.desk - 0.16) / 2;
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.17, 0.04, 10, 28), M.carved);
      ring.position.copy(V(cx, cy, zc)); ring.rotation.y = rot; add(ring);
      const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.03, 24).rotateX(Math.PI / 2), M.carved);
      disc.position.copy(V(cx, cy, zc)); disc.rotation.y = rot; add(disc);
      for (let p = 0; p < 8; p++) {
        const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.035, 8, 6), M.honey);
        const a = p * Math.PI / 4; leaf.position.copy(V(cx + nx * 0.03 + Math.cos(a) * 0.08 * -ny, cy + ny * 0.03 + Math.cos(a) * 0.08 * nx, zc + Math.sin(a) * 0.08));
        add(leaf, scene, false);
      }
    }
  }
}

// chairs on the rostrum
// the Speaker's chair; at a joint session the Vice President sits beside the Speaker
// it stands on a dais behind the Speaker's desk
const DAIS = 1.25 + 0.38;
extrude([[1.6, 0.35], [1.6, 1.75], [-1.6, 1.75], [-1.6, 0.35]], 1.25, DAIS, [M.carpet, M.honey]);
if (VIEW.sotu) for (const x of [-0.62, 0.62]) chair(x, 1.1, DAIS, Math.PI / 2, {backH: 1.25, scale: 1.08});
else chair(0, 1.1, DAIS, Math.PI / 2, {backH: 1.25, scale: 1.08});
for (const x of [-3.15, -0.9, 0.9, 3.15]) chair(x, Math.abs(x) > 3 ? 2.75 : 3.05, 0.72, Math.PI / 2);
for (const x of [-5.0, -2.6, -1.0, 1.0, 2.6, 5.0]) chair(x, Math.abs(x) > 4 ? 3.3 : 4.25, 0.3, Math.PI / 2);
// the Mace on its marble pedestal, at the Speaker's right
cylinder(3.35, 1.55, 0.72, 0.2, 0.95, M.greenMarble, 24);
cylinder(3.35, 1.55, 1.67, 0.24, 0.05, M.white, 24);
cylinder(3.35, 1.55, 1.72, 0.05, 1.05, M.silver, 12);
{ const globe = new THREE.Mesh(new THREE.SphereGeometry(0.12, 20, 16), M.silver); globe.position.copy(V(3.35, 1.55, 2.86)); add(globe);
  const eagle = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.16, 8), M.silver); eagle.position.copy(V(3.35, 1.55, 3.04)); add(eagle); }

const PRESS_SEATS = [];

// ------------------------------------------------------------------ frontispiece

const south = groups.south;
box(0, 0.16, 0, 11.0, 0.32, 6.0, M.cream, 0, south, 2);
for (const [x, w] of [[-3.0, 2.5], [3.0, 2.5], [0, 2.6]]) {     // recessed panels on the marble
  for (const [z, h] of [[0.4, 1.4], [2.0, 2.6]]) {
    for (const [dx, dz, bw, bh] of [[0, 0, w, 0.05], [0, h, w, 0.05], [-w / 2, 0, 0.05, h], [w / 2, 0, 0.05, h]])
      box(x + dx, 0.33, z + dz, bw, 0.03, bh + 0.05, M.white, 0, south);
  }
}
for (const [x, base] of [[-4.5, 0.72], [-1.55, 1.25], [1.55, 1.25], [4.5, 0.72]]) {
  const y = 0.62;
  box(x, y, base, 0.62, 0.62, 0.22, M.white, 0, south);
  const torus = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.05, 10, 32), M.white);
  torus.rotation.x = Math.PI / 2; torus.position.copy(V(x, y, base + 0.27)); add(torus, south);
  cylinder(x, y, base + 0.22, 0.27, 4.65 - base - 0.22, M.black, 40, 0.24, south);
  cylinder(x, y, 4.58, 0.25, 0.1, M.white, 32, 0.3, south);
  box(x, y, 4.68, 0.78, 0.66, 0.2, M.white, 0, south);
  for (const s of [-1, 1]) {
    const vol = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.62, 20), M.white);
    vol.rotation.x = Math.PI / 2; vol.position.copy(V(x + s * 0.34, y, 4.72)); add(vol, south);
    const eye = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.018, 6, 16), M.gold);
    eye.position.copy(V(x + s * 0.34, y + 0.32, 4.72)); add(eye, south);
  }
}
box(0, 0.55, 4.88, 11.4, 1.1, 0.62, M.cream, 0, south, 2);           // entablature
box(0, 1.1, 4.95, 11.4, 0.02, 0.03, M.gold, 0, south);
box(0, 0.6, 5.5, 11.7, 1.2, 0.18, M.white, 0, south, 2);            // cornice
box(0, 1.2, 5.5, 11.7, 0.02, 0.04, M.gold, 0, south);
box(0, 0.3, 5.68, 11.0, 0.6, 0.32, M.cream, 0, south, 2);           // attic
{
  const mottoTex = canvasTexture(2048, 160, (g, w, h) => {
    g.drawImage(creamTex.image, 0, 0, w, h);
    g.fillStyle = '#b48b35'; g.font = 'bold 104px Georgia, "DejaVu Serif", serif'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText('IN GOD WE TRUST', w / 2, h / 2 + 6);
  });
  const motto = new THREE.Mesh(new THREE.PlaneGeometry(6.0, 0.42), std({map: mottoTex, roughness: 0.35, metalness: 0.2}));
  motto.position.copy(V(0, 1.106, 5.25)); motto.rotation.y = Math.PI; add(motto, south, false);
}
// the flag, gathered in folds between the inner columns
{
  const flagTex = canvasTexture(1900, 1000, (g, w, h) => {
    for (let i = 0; i < 13; i++) { g.fillStyle = i % 2 ? '#ece8df' : '#9c1b29'; g.fillRect(0, i * h / 13, w, h / 13 + 1); }
    g.fillStyle = '#26295c'; g.fillRect(0, 0, w * 0.4, h * 7 / 13);
    g.fillStyle = '#f4f1ea';
    for (let r = 0; r < 9; r++) for (let c = 0; c < (r % 2 ? 5 : 6); c++) star(g, (c + (r % 2 ? 1 : 0.5)) * w * 0.4 / 6, (r + 1) * h * 7 / 13 / 10, 18);
  });
  const unfolded = 4.2, width = 2.45, height = 2.2, folds = 8;
  const geo = new THREE.PlaneGeometry(unfolded, height, 280, 2);
  const p = geo.attributes.position, amp = 0.11;
  for (let i = 0; i < p.count; i++) {
    const u = (p.getX(i) + unfolded / 2) / unfolded;
    p.setX(i, -width / 2 + u * width);
    p.setZ(i, amp * Math.sin(u * folds * 2 * Math.PI) * (0.7 + 0.3 * Math.sin(u * 3.1)));
  }
  geo.computeVertexNormals();
  const flag = new THREE.Mesh(geo, std({map: flagTex, roughness: 0.8, side: THREE.DoubleSide}));
  flag.position.copy(V(0, 0.48, 4.55 - height / 2)); flag.rotation.y = Math.PI; add(flag, south);
  box(0, 0.42, 4.5, 2.7, 0.06, 0.06, M.gold, 0, south);
}
// gilt fasces between the columns
for (const x of [-3.02, 3.02]) {
  const y = 0.48;
  for (let k = 0; k < 9; k++) {
    const a = (k / 9) * Math.PI * 2;
    cylinder(x + 0.12 * Math.cos(a), y + 0.07 * Math.sin(a), 1.75, 0.032, 2.75, M.gold, 8, 0.03, south);
  }
  for (const z of [2.1, 3.1, 4.1]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.15, 0.03, 8, 20), M.gold); ring.scale.set(1, 0.6, 1);
    ring.rotation.x = Math.PI / 2; ring.position.copy(V(x, y, z)); add(ring, south);
  }
  const blade = new THREE.Shape([[0, 0], [0.3, 0.06], [0.36, 0.3], [0.32, 0.5], [0, 0.42]].map(([a, b]) => new THREE.Vector2(a, b)));
  const bg = new THREE.ExtrudeGeometry(blade, {depth: 0.03, bevelEnabled: false});
  const bm = new THREE.Mesh(bg, M.gold); bm.position.copy(V(x + (x < 0 ? 0.08 : -0.08), y, 4.15));
  bm.rotation.y = x < 0 ? 0 : Math.PI; add(bm, south);
  cylinder(x, y, 4.5, 0.05, 0.12, M.gold, 12, 0.02, south);
}
// the clock above the frontispiece
{
  const faceTex = canvasTexture(256, 256, (g, w, h) => {
    g.fillStyle = '#f2ead6'; g.beginPath(); g.arc(128, 128, 126, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#222';
    for (let i = 0; i < 12; i++) { g.save(); g.translate(128, 128); g.rotate(i * Math.PI / 6); g.fillRect(-3, -112, 6, 20); g.restore(); }
    g.strokeStyle = '#222'; g.lineCap = 'round';
    g.lineWidth = 7; g.beginPath(); g.moveTo(128, 128); g.lineTo(128 + 50, 128 - 30); g.stroke();
    g.lineWidth = 4; g.beginPath(); g.moveTo(128, 128); g.lineTo(128 - 20, 128 - 92); g.stroke();
  });
  box(0, 0.33, 6.0, 1.4, 0.66, 0.9, M.cream, 0, south);
  const face = new THREE.Mesh(new THREE.CircleGeometry(0.34, 40), std({map: faceTex, roughness: 0.4}));
  face.position.copy(V(0, 0.72, 6.42)); face.rotation.y = Math.PI; add(face, south, false);
  const rim = new THREE.Mesh(new THREE.TorusGeometry(0.37, 0.05, 10, 40), M.gold); rim.position.copy(V(0, 0.7, 6.42)); add(rim, south);
  const orn = new THREE.Shape();
  orn.moveTo(-1.1, 0); orn.quadraticCurveTo(-0.9, 0.35, -0.42, 0.42); orn.quadraticCurveTo(-0.2, 0.95, 0, 0.98);
  orn.quadraticCurveTo(0.2, 0.95, 0.42, 0.42); orn.quadraticCurveTo(0.9, 0.35, 1.1, 0); orn.lineTo(-1.1, 0);
  const og = new THREE.ExtrudeGeometry(orn, {depth: 0.06, bevelEnabled: true, bevelThickness: 0.02, bevelSize: 0.02, bevelSegments: 2});
  const om = new THREE.Mesh(og, M.gold); om.position.copy(V(0, 0.68, 6.0)); add(om, south);
}

// ------------------------------------------------------------------ walls

const WALLS = {};
for (const [name, o, t, len] of [['south', [HW, 0], [-1, 0], W], ['east', [HW, D], [0, -1], D],
                                 ['north', [-HW, D], [1, 0], W], ['west', [-HW, 0], [0, 1], D]]) {
  WALLS[name] = {name, o, t, n: [t[1], -t[0]], len, rot: Math.atan2(t[1], t[0]), group: groups[name]};
}
const wpt = (w, s, off) => [w.o[0] + s * w.t[0] + off * w.n[0], w.o[1] + s * w.t[1] + off * w.n[1]];
function wmesh(w, geo, mat, s, off, z, cast = false) {
  const m = new THREE.Mesh(geo, mat); const [x, y] = wpt(w, s, off);
  m.position.copy(V(x, y, z)); m.rotation.y = w.rot; m.receiveShadow = true; m.castShadow = cast; w.group.add(m); return m;
}
function wbox(w, s, off, z, bw, bd, bh, mat, uvScale = 1) {
  const g = new THREE.BoxGeometry(bw, bh, bd); boxUV(g, bw, bh, bd, uvScale);
  return wmesh(w, g, mat, s, off + bd / 2, z + bh / 2);
}
function wplane(w, s, off, z, pw, ph, mat, uv) {   // uv = [u0, v0, u1, v1], default metres
  const g = new THREE.PlaneGeometry(pw, ph);
  const [u0, v0, u1, v1] = uv || [0, z, pw, z + ph];
  const a = g.attributes.uv;
  for (let i = 0; i < a.count; i++) a.setXY(i, u0 + a.getX(i) * (u1 - u0), v0 + a.getY(i) * (v1 - v0));
  return wmesh(w, g, mat, s, off, z + ph / 2);
}
function wdisc(w, s, off, z, r, mat, seg = 32) {
  const g = new THREE.CylinderGeometry(r, r, 0.05, seg).rotateX(Math.PI / 2);
  return wmesh(w, g, mat, s, off + 0.025, z);
}
function wring(w, s, off, z, r, tube, mat, seg = 32) {
  return wmesh(w, new THREE.TorusGeometry(r, tube, 8, seg), mat, s, off, z);
}
const Z_LOW = 5.5, Z_FRIEZE = 5.8, Z_LEDGE = 5.95, Z_UP = 7.0, Z_CORNICE = 10.2;

function pilaster(w, s, z0, z1, width = 0.5) {
  wbox(w, s, 0, z0, width + 0.12, 0.2, 0.32, M.cream);
  wbox(w, s, 0, z0, width, 0.13, z1 - z0, M.cream, 2);
  wbox(w, s, 0, z1 - 0.24, width + 0.14, 0.2, 0.24, M.cream);
  wbox(w, s, 0, z1 - 0.3, width + 0.06, 0.16, 0.04, M.gold);
}
function door(w, s, z, kind) {
  const leaded = kind === 'leaded', dw = leaded ? 1.6 : 1.5, dh = leaded ? 3.0 : 2.2;
  wbox(w, s, 0, z, dw + 0.5, 0.06, dh + 0.3, M.cream);
  wbox(w, s, 0.06, z + dh + 0.12, dw + 0.36, 0.04, 0.06, M.gold);
  const leaf = wbox(w, s, 0.06, z, dw, 0.03, dh, leaded ? M.leadedDoor : M.panelDoor);
  const uv = leaf.geometry.attributes.uv;
  for (let i = 16; i < 20; i++) uv.setXY(i, uv.getX(i) / dw, uv.getY(i) / dh);   // front face shows the whole texture
  if (leaded) {
    const g = new THREE.CylinderGeometry(0.3, 0.3, 0.05, 8).rotateX(Math.PI / 2).rotateZ(Math.PI / 8);
    wmesh(w, g, M.carved, s, 0.05, z + dh + 0.75);
    wring(w, s, 0.08, z + dh + 0.75, 0.3, 0.025, M.gold, 8);
  }
}
function portrait(w, s, z, dark) {
  const pw = 1.9, ph = 2.5;
  wplane(w, s, 0.1, z, pw, ph, std({map: portraitTexture(dark), roughness: 0.55}), [0, 0, 1, 1]);
  for (const [ds, dz, bw, bh] of [[0, -0.12, pw + 0.3, 0.15], [0, ph - 0.03, pw + 0.3, 0.15], [-pw / 2 - 0.08, -0.12, 0.15, ph + 0.27], [pw / 2 + 0.08, -0.12, 0.15, ph + 0.27]])
    wbox(w, s + ds, 0.02, z + dz, bw, 0.14, bh, M.gold);
  wbox(w, s, 0, z - 0.75, 2.4, 0.12, 0.06, M.brass);
}

// floor level: walnut bays between cream pilasters, with doors and portraits
function lowerWall(w, pilasters, bays) {
  for (const s of pilasters) pilaster(w, s, 0, Z_LOW);
  for (const [s0, s1, what] of bays) {
    const s = (s0 + s1) / 2, bw = s1 - s0;
    wplane(w, s, 0, 0, bw, Z_LOW, M.walnutPanel, [0, 0, 1, 1]);
    if (what === 'door') door(w, s, 0, 'leaded');
    else if (what && what.portrait) portrait(w, s, 1.7, what.portrait);
  }
}
// frieze, ledge and the walnut band up to the upper level
function band(w, s0, s1) {
  const s = (s0 + s1) / 2, len = s1 - s0;
  wplane(w, s, 0.004, Z_LOW, len, Z_FRIEZE - Z_LOW, M.greek, [s0 / 0.6, 0, s1 / 0.6, 1]);
  wbox(w, s, 0, Z_LOW - 0.04, len, 0.06, 0.04, M.gold);
  wbox(w, s, 0, Z_FRIEZE, len, 0.3, Z_LEDGE - Z_FRIEZE, M.walnut);
  wbox(w, s, 0, Z_FRIEZE - 0.02, len, 0.32, 0.03, M.gold);
  wplane(w, s, 0, Z_LEDGE, len, Z_UP - Z_LEDGE, M.parapet, [s0 / 1.5, 0, s1 / 1.5, 1]);
  wbox(w, s, 0, Z_UP - 0.04, len, 0.14, 0.07, M.brass);
}
// the upper level: walnut wainscot, blue damask panels in cream frames, doors at the walkway
function upperWall(w, s0, s1, floorZ) {
  const len = s1 - s0, s = (s0 + s1) / 2;
  wplane(w, s, 0, Z_UP, len, Z_CORNICE - Z_UP, M.plaster);
  const widths = [], unit = [3.4, 2.0];
  const n = Math.max(1, Math.round((len - 0.5) / 5.4 * 2));
  for (let i = 0; i < n; i++) widths.push(unit[i % 2]);
  if (widths.length % 2 === 0 && widths.length > 1) widths.push(3.4);
  const scale = (len - 0.5 * (widths.length + 1)) / widths.reduce((a, b) => a + b, 0);
  let pos = s0;
  const pil = [];
  pil.push(pos + 0.25); pos += 0.5;
  widths.forEach((bw0, i) => {
    const bw = bw0 * scale, c = pos + bw / 2;
    const fz = floorZ(c);
    const wainTop = Math.max(Z_UP, fz) + 0.65;
    wplane(w, c, 0.01, Math.max(Z_UP, fz) - 0.02, bw, wainTop - Math.max(Z_UP, fz) + 0.02, M.parapet, [0, 0, bw / 1.2, 1]);
    wbox(w, c, 0, wainTop, bw, 0.08, 0.05, M.walnut);
    if (i % 2 === 0) {            // damask panel in a cream frame
      const z0 = wainTop + 0.25, z1 = Z_CORNICE - 0.4, pw = bw - 0.5;
      wplane(w, c, 0.012, z0, pw, z1 - z0, M.damask, [c / 0.6, z0 / 0.6, (c + pw) / 0.6, z1 / 0.6]);
      for (const [ds, dz, fw, fh] of [[0, -0.1, pw + 0.2, 0.1], [0, z1 - z0, pw + 0.2, 0.1], [-pw / 2 - 0.05, -0.1, 0.1, z1 - z0 + 0.2], [pw / 2 + 0.05, -0.1, 0.1, z1 - z0 + 0.2]])
        wbox(w, c + ds, 0, z0 + dz, fw, 0.07, fh, M.cream);
      for (const [ds, dz, fw, fh] of [[0, 0, pw, 0.02], [0, z1 - z0 - 0.02, pw, 0.02], [-pw / 2, 0, 0.02, z1 - z0], [pw / 2 - 0.02 + 0.01, 0, 0.02, z1 - z0]])
        wbox(w, c + ds, 0.012, z0 + dz, fw, 0.03, fh, M.gold);
    } else {
      if (fz > 4.5) door(w, c, fz, 'panel');
      else wplane(w, c, 0.012, wainTop + 0.25, bw - 0.4, Z_CORNICE - 0.4 - wainTop - 0.25, M.damask);
      wdisc(w, c, 0, Z_CORNICE - 0.42, 0.27, M.white);
      wring(w, c, 0.06, Z_CORNICE - 0.42, 0.28, 0.03, M.gold);
    }
    pos += bw; pil.push(pos + 0.25); pos += 0.5;
  });
  for (const p of pil) {
    pilaster(w, p, Z_UP, Z_CORNICE, 0.4);
    wbox(w, p, 0.13, Z_CORNICE - 1.55, 0.08, 0.2, 0.06, M.bronze);   // sconce
    const bulb = wmesh(w, new THREE.SphereGeometry(0.07, 12, 8), M.bulb, p, 0.33, Z_CORNICE - 1.42);
    bulb.castShadow = false;
  }
}
function cornice(w, s0, s1) {
  const s = (s0 + s1) / 2, len = s1 - s0;
  wbox(w, s, 0, Z_CORNICE, len, 0.22, 0.28, M.cream, 2);
  wbox(w, s, 0, Z_CORNICE + 0.28, len, 0.16, 0.24, M.plaster);
  wbox(w, s, 0, Z_CORNICE + 0.3, len, 0.17, 0.03, M.gold);
  wbox(w, s, 0, Z_CORNICE + 0.52, len, 0.5, H - Z_CORNICE - 0.52, M.cream, 2);
  wbox(w, s, 0, Z_CORNICE + 0.5, len, 0.52, 0.04, M.gold);
}
const wallFloor = w => s => { const [x, y] = wpt(w, s, 0.7); return floorAt(x, y); };

{ // south wall: rostrum in the middle, portraits of Lafayette and Washington, doors
  const w = WALLS.south, S = x => HW - x;
  const pil = [5.9, 8.5, 11.8, 14.4];
  while (pil[pil.length - 1] + 3.25 < HW - 1.0) pil.push(+(pil[pil.length - 1] + 3.25).toFixed(2));
  const contents = {7.2: 'door', 10.15: 'portrait', 13.1: 'door'};
  for (let i = 4; i + 1 < pil.length; i += 2) contents[((pil[i] + pil[i + 1]) / 2).toFixed(3)] = 'door';
  const bays = [];
  for (const side of [-1, 1]) {
    const edges = [5.5, ...pil, HW];
    for (let i = 0; i + 1 < edges.length; i++) {
      const c = (edges[i] + edges[i + 1]) / 2;
      let what = null;
      for (const [k, v] of Object.entries(contents)) if (Math.abs(+k - c) < 0.3) what = v;
      if (what === 'portrait') what = {portrait: side < 0 ? '#1b1712' : '#262838'};
      const a = S(side * edges[i]), b = S(side * edges[i + 1]), dir = Math.sign(b - a);
      const a2 = a + (i > 0 ? 0.25 * dir : 0), b2 = b - (i + 2 < edges.length ? 0.25 * dir : 0);
      bays.push([Math.min(a2, b2), Math.max(a2, b2), what]);
    }
  }
  lowerWall(w, [...pil.map(x => S(x)), ...pil.map(x => S(-x))], bays);
  band(w, 0, W);
  const PG = 18;   // press gallery opening
  upperWall(w, 0, S(PG), () => Z_UP); upperWall(w, S(-PG), W, () => Z_UP);
  cornice(w, 0, S(PG)); cornice(w, S(-PG), W);
}
for (const name of ['east', 'west']) {     // side walls: floor-level doors in the passage, galleries above
  const w = WALLS[name], Y = y => name === 'east' ? D - y : y;
  const pil = [1.8, 5.4, 9.0].map(Y);
  lowerWall(w, pil, [[Math.min(Y(0), Y(1.8)) + (name === 'east' ? 0.25 : 0), Math.max(Y(0), Y(1.8)) - (name === 'west' ? 0.25 : 0), null],
                     [Math.min(Y(1.8), Y(5.4)) + 0.25, Math.max(Y(1.8), Y(5.4)) - 0.25, 'door'],
                     [Math.min(Y(5.4), Y(9.0)) + 0.25, Math.max(Y(5.4), Y(9.0)) - 0.25, null]]);
  band(w, 0, D);
  upperWall(w, 0, D, wallFloor(w));
  cornice(w, 0, D);
}
{ // north wall: only the upper level shows, above the top walkway
  const w = WALLS.north;
  band(w, 0, W);
  upperWall(w, 0, W, wallFloor(w));
  cornice(w, 0, W);
}

// the press gallery, recessed above the rostrum as today
{
  const PG = 18, back = -3.6, g = south;
  const tiers = [[-0.975, 0, 6.0], [-1.825, -0.975, 6.42], [back, -1.825, 6.84]];
  for (const [y0, y1, z] of tiers) {
    const m = box(0, (y0 + y1) / 2, Z_LEDGE, 2 * PG, y1 - y0, z - Z_LEDGE, M.carpetSide, 0, g);
    m.material = [M.carpetSide, M.carpetSide, M.carpet, M.carpetSide, M.carpetSide, M.carpetSide];
  }
  box(0, -0.08, Z_LEDGE, 2 * PG, 0.16, Z_UP - Z_LEDGE, M.walnut, 0, g);
  box(0, -0.08, Z_UP - 0.04, 2 * PG, 0.3, 0.07, M.brass, 0, g);
  const seats = PRESS_SEATS;
  [-0.55, -1.4, -2.25].forEach((y, k) => {
    const z = tiers[k][2];
    for (let x = -PG + 0.6; x <= PG - 0.6; x += 0.55) {
      if ([-9, 0, 9].some(a => Math.abs(x - a) < 0.6)) continue;
      seats.push({x, y, z, face: Math.PI / 2});
    }
  });
  seats.forEach((s, i) => { const p = seats[i - 1], n = seats[i + 1];
    s.end_lo = !p || p.y !== s.y || s.x - p.x > 0.6; s.end_hi = !n || n.y !== s.y || n.x - s.x > 0.6; });
  // straight benches: an arc around a far-away centre to the north
  const byRow = {};
  for (const s of seats) (byRow[s.y] = byRow[s.y] || []).push(s);
  const benches = [];
  for (const [y, list] of Object.entries(byRow)) benches.push(...benchesOf(list, 0, +y + 1e5));
  buildBenches(benches, {depth: 0.85, upholstery: M.fabric, colorOf: () => jitter(blue)});
  // back and side walls of the recess
  const pb = {o: [PG, back], t: [-1, 0], n: [0, 1], len: 2 * PG, rot: Math.PI, group: g};
  upperWall(pb, 0, 2 * PG, () => 6.84);
  cornice(pb, 0, 2 * PG);
  for (const [o, t] of [[[PG, 0], [0, -1]], [[-PG, back], [0, 1]]]) {
    const w = {o, t, n: [t[1], -t[0]], len: -back, rot: Math.atan2(t[1], t[0]), group: g};
    wplane(w, -back / 2, 0, Z_LEDGE, -back, H - Z_LEDGE, M.plaster);
    wplane(w, -back / 2, 0.01, 7.6, -back - 1.0, 2.1, M.damask);
    wplane(w, -back / 2, 0.01, 6.0, -back, 1.4, M.parapet, [0, 0, 2.4, 1]);
    cornice(w, 0, -back);
  }
}

// ------------------------------------------------------------------ ceiling

{
  const c = groups.ceiling, y0 = -3.6, depth = D - y0;
  const ceil = new THREE.Mesh(new THREE.PlaneGeometry(W, depth), M.plaster);
  ceil.rotation.x = Math.PI / 2; ceil.position.copy(V(0, y0 + depth / 2, H)); c.add(ceil);
  const LAY = {x: 12.5, y0: 9.5, y1: 24.5};   // laylight half width and extent
  const nx = 12, ny = 8, cw = W / nx, cd = depth / ny;
  for (let i = 0; i <= nx; i++) {
    const x = -HW + i * cw;
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.5, depth), M.cream); b.position.copy(V(x, y0 + depth / 2, H - 0.25)); c.add(b);
    const t = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.03, depth), M.gold); t.position.copy(V(x, y0 + depth / 2, H - 0.5)); c.add(t);
  }
  for (let j = 0; j <= ny; j++) {
    const y = y0 + j * cd;
    const b = new THREE.Mesh(new THREE.BoxGeometry(W, 0.5, 0.4), M.cream); b.position.copy(V(0, y, H - 0.25)); c.add(b);
    const t = new THREE.Mesh(new THREE.BoxGeometry(W, 0.03, 0.2), M.gold); t.position.copy(V(0, y, H - 0.5)); c.add(t);
  }
  for (let i = 0; i < nx; i++) for (let j = 0; j < ny; j++) {
    const x = -HW + (i + 0.5) * cw, y = y0 + (j + 0.5) * cd;
    if (Math.abs(x) < LAY.x && y > LAY.y0 && y < LAY.y1) continue;
    const panel = new THREE.Mesh(new THREE.PlaneGeometry(cw - 1.4, cd - 1.4), M.coffer);
    panel.rotation.x = Math.PI / 2; panel.position.copy(V(x, y, H - 0.02)); c.add(panel);
    const rim = new THREE.Mesh(new THREE.BoxGeometry(cw - 1.3, 0.04, cd - 1.3), M.gold); rim.position.copy(V(x, y, H - 0.06)); c.add(rim);
    const inner = new THREE.Mesh(new THREE.PlaneGeometry(cw - 1.45, cd - 1.45), M.coffer);
    inner.rotation.x = Math.PI / 2; inner.position.copy(V(x, y, H - 0.085)); c.add(inner);
    for (const [dx, dy] of [[-0.3, -0.3], [0.3, 0.3], [-0.3, 0.3], [0.3, -0.3]].map(([a, b]) => [a * (cw - 1.45), b * (cd - 1.45)])) {
      const disc = new THREE.Mesh(new THREE.CircleGeometry(0.16, 20), M.bulb);
      disc.rotation.x = Math.PI / 2; disc.position.copy(V(x + dx, y + dy, H - 0.09)); c.add(disc);
    }
  }
  // stained-glass laylight: the eagle in the centre, ringed by the state seals
  const laylightTex = canvasTexture(2048, 1280, (g, w, h) => {
    g.fillStyle = '#efe0b0'; g.fillRect(0, 0, w, h);
    const cols = 18, rows = 11;
    for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) {
      const x = i * w / cols, y = j * h / rows;
      const grad = g.createLinearGradient(x, y, x + w / cols, y + h / rows);
      grad.addColorStop(0, '#fbf1cf'); grad.addColorStop(1, (i + j) % 2 ? '#ead79b' : '#f3e5b6');
      g.fillStyle = grad; g.fillRect(x + 5, y + 5, w / cols - 10, h / rows - 10);
    }
    g.strokeStyle = '#9b7a35'; g.lineWidth = 12; g.strokeRect(6, 6, w - 12, h - 12);
    for (let k = 0; k < 50; k++) {
      const a = (k / 50) * Math.PI * 2, cx = w / 2 + 780 * Math.cos(a), cy = h / 2 + 480 * Math.sin(a);
      g.fillStyle = ['#8a7a5a', '#7c7258', '#93805e', '#776d58'][k % 4];
      g.beginPath(); g.arc(cx, cy, 26, 0, Math.PI * 2); g.fill();
      g.strokeStyle = '#b8964e'; g.lineWidth = 4; g.stroke();
      g.fillStyle = '#e8d9ae'; g.beginPath(); g.arc(cx, cy, 11, 0, Math.PI * 2); g.fill();
    }
    g.fillStyle = '#20356f'; g.beginPath(); g.ellipse(w / 2, h / 2, 330, 300, 0, 0, Math.PI * 2); g.fill();
    g.strokeStyle = '#d9b75a'; g.lineWidth = 18; g.stroke();
    g.fillStyle = '#f2e7c4'; for (let k = 0; k < 13; k++) star(g, w / 2 - 150 + (k % 7) * 50, h / 2 - 230 + Math.floor(k / 7) * 46, 16);
    g.fillStyle = '#e6c25c';
    g.beginPath();
    g.moveTo(w / 2, h / 2 - 40);
    g.bezierCurveTo(w / 2 - 120, h / 2 - 170, w / 2 - 260, h / 2 - 120, w / 2 - 290, h / 2 + 10);
    g.bezierCurveTo(w / 2 - 210, h / 2 - 20, w / 2 - 120, h / 2 + 10, w / 2 - 60, h / 2 + 40);
    g.lineTo(w / 2 + 60, h / 2 + 40);
    g.bezierCurveTo(w / 2 + 120, h / 2 + 10, w / 2 + 210, h / 2 - 20, w / 2 + 290, h / 2 + 10);
    g.bezierCurveTo(w / 2 + 260, h / 2 - 120, w / 2 + 120, h / 2 - 170, w / 2, h / 2 - 40);
    g.fill();
    g.beginPath(); g.ellipse(w / 2, h / 2 - 70, 34, 40, 0, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#ffffff'; g.fillRect(w / 2 - 55, h / 2 - 20, 110, 130);
    g.fillStyle = '#b22234'; for (let k = 0; k < 6; k++) g.fillRect(w / 2 - 55 + k * 20, h / 2 + 10, 10, 100);
    g.fillStyle = '#20356f'; g.fillRect(w / 2 - 55, h / 2 - 20, 110, 32);
    g.fillStyle = '#e6c25c'; g.fillRect(w / 2 - 110, h / 2 + 120, 220, 18);
  });
  const lw = 2 * LAY.x - 0.6, ld = LAY.y1 - LAY.y0 - 0.6;
  const laylight = new THREE.Mesh(new THREE.PlaneGeometry(lw, ld), std({map: laylightTex, emissive: '#fff1cf', emissiveMap: laylightTex, emissiveIntensity: 0.6, roughness: 0.6}));
  laylight.rotation.x = Math.PI / 2; laylight.position.copy(V(0, (LAY.y0 + LAY.y1) / 2, H - 0.6)); c.add(laylight);
  for (const [w, d, dx, dy] of [[lw + 0.8, 0.4, 0, ld / 2 + 0.2], [lw + 0.8, 0.4, 0, -ld / 2 - 0.2], [0.4, ld + 0.8, lw / 2 + 0.2, 0], [0.4, ld + 0.8, -lw / 2 - 0.2, 0]]) {
    const f = new THREE.Mesh(new THREE.BoxGeometry(w, 0.3, d), M.gold);
    f.position.copy(V(dx, (LAY.y0 + LAY.y1) / 2 + dy, H - 0.45)); c.add(f);
  }
}

// ------------------------------------------------------------------ people (State of the Union)

// A simple figure, seated or standing: local x forward, y up, z to the right.
function figureParts(pose) {
  const R = (w, h, d, x, y, z, rz = 0, r = 0.03) => RB(w, h, d, r, 1).rotateZ(rz).translate(x, y, z);
  const S = (r, x, y, z, sx = 1, sy = 1, sz = 1) => new THREE.SphereGeometry(r, 14, 10).scale(sx, sy, sz).translate(x, y, z);
  const C = (r, h, x, y, z) => new THREE.CylinderGeometry(r, r, h, 10).translate(x, y, z);
  const P = {};
  if (pose === 'seated') {
    const t = 0.1;   // leaning back a little
    P.suit = [R(0.25, 0.56, 0.42, -0.15, 0.79, 0, t, 0.07),
      ...[-1, 1].flatMap(s => [R(0.46, 0.16, 0.17, 0.02, 0.545, s * 0.1, 0, 0.05), R(0.13, 0.46, 0.14, 0.24, 0.27, s * 0.1, 0, 0.04),
                               R(0.11, 0.33, 0.12, -0.12, 0.88, s * 0.245, 0.38, 0.04), R(0.31, 0.1, 0.11, 0.07, 0.69, s * 0.215, 0, 0.035)])];
    P.shoes = [-1, 1].map(s => R(0.26, 0.09, 0.11, 0.31, 0.045, s * 0.1, 0, 0.03));
    P.skin = [S(0.09, -0.12, 1.25, 0, 1, 1.27, 0.86), C(0.05, 0.12, -0.135, 1.1, 0),
              ...[-1, 1].map(s => S(0.047, 0.24, 0.68, s * 0.19, 1.3, 0.7, 0.9))];
    P.shirt = [R(0.02, 0.24, 0.15, -0.035, 0.94, 0, t, 0.005)];
    P.tie = [R(0.015, 0.32, 0.055, -0.022, 0.88, 0, t, 0.004)];
    P.hairShort = [S(0.095, -0.14, 1.285, 0, 1, 0.92, 0.92)];
    P.hairLong = [S(0.1, -0.145, 1.27, 0, 1.0, 1.15, 0.98), R(0.08, 0.28, 0.2, -0.2, 1.1, 0, t, 0.04)];
  } else {
    P.suit = [R(0.25, 0.58, 0.43, 0, 1.26, 0, 0, 0.07),
      ...[-1, 1].flatMap(s => [R(0.16, 0.48, 0.17, 0, 0.73, s * 0.1, 0, 0.05), R(0.14, 0.46, 0.14, 0, 0.28, s * 0.1, 0, 0.04),
                               R(0.11, 0.33, 0.12, 0.03, 1.35, s * 0.255, 0.25, 0.04), R(0.32, 0.1, 0.11, 0.2, 1.2, s * 0.225, 0, 0.035)])];
    P.shoes = [-1, 1].map(s => R(0.26, 0.09, 0.11, 0.07, 0.045, s * 0.1, 0, 0.03));
    P.skin = [S(0.09, 0.02, 1.73, 0, 1, 1.27, 0.86), C(0.05, 0.12, 0.0, 1.58, 0),
              ...[-1, 1].map(s => S(0.047, 0.37, 1.2, s * 0.2, 1.3, 0.7, 0.9))];
    P.shirt = [R(0.02, 0.24, 0.15, 0.125, 1.42, 0, 0, 0.005)];
    P.tie = [R(0.015, 0.32, 0.055, 0.137, 1.36, 0, 0, 0.004)];
    P.hairShort = [S(0.095, 0.0, 1.765, 0, 1, 0.92, 0.92)];
    P.hairLong = [S(0.1, -0.005, 1.75, 0, 1.0, 1.15, 0.98), R(0.08, 0.28, 0.2, -0.06, 1.58, 0, 0, 0.04)];
  }
  for (const k in P) P[k] = merge(P[k]);
  return P;
}

const pick = list => list[Math.floor(rand() * list.length)];
const PALETTE = {
  suitMen: ['#1c2230', '#24272d', '#16171a', '#33363c', '#22304f', '#2e2f33', '#3a3a3e', '#1f2a3d', '#2a2522'],
  suitWomen: ['#a3242c', '#e9e5dc', '#2a4fa0', '#c76d8e', '#2a6b70', '#5a3d7a', '#cdb79a', '#1c2230', '#16171a', '#8a1c3a', '#d1b44f', '#efefef'],
  skin: ['#f1c9a5', '#e8b996', '#d9a47c', '#c68863', '#a86b47', '#8a5434', '#6b3e26', '#4a2a1a', '#f5d6bc'],
  hair: ['#1b1612', '#1b1612', '#2e2219', '#2e2219', '#4a3626', '#4a3626', '#6b5038', '#a88a5c', '#8e8c88', '#b9b6b0'],
  tie: ['#9c1c26', '#1f3d7a', '#3a6fb0', '#6b1f3a', '#c9a043', '#2b2b2b', '#5d7fa8', '#b8323a', '#7d8fa8'],
  shirt: ['#f2f2f0', '#f2f2f0', '#f2f2f0', '#dfe8f2', '#eef0f5'],
  uniform: ['#3f4430', '#1b2235', '#354a6b', '#2f3640', '#1d2433', '#3b4232'],
};
function randomPerson(extra = {}) {
  const woman = rand() < 0.32, hair = pick(PALETTE.hair);
  const p = {pose: 'seated', woman, skin: pick(PALETTE.skin), hair, hairStyle: woman ? 'long' : (rand() < 0.06 ? 'bald' : 'short'),
             suit: woman ? pick(PALETTE.suitWomen) : pick(PALETTE.suitMen), shirt: pick(PALETTE.shirt), tie: woman ? null : pick(PALETTE.tie)};
  if (woman) p.shirt = rand() < 0.5 ? p.suit : '#f1ede4';
  return Object.assign(p, extra);
}
function addPeople(people) {
  const mats = {suit: std({map: fabricTex, roughness: 0.82, envMapIntensity: 0.3}), shoes: std({color: '#0d0d0d', roughness: 0.35}),
                skin: std({roughness: 0.62, envMapIntensity: 0.4}), shirt: std({roughness: 0.7, envMapIntensity: 0.3}),
                tie: std({roughness: 0.45, envMapIntensity: 0.5}), hairShort: std({roughness: 0.75, envMapIntensity: 0.3}),
                hairLong: std({roughness: 0.75, envMapIntensity: 0.3})};
  for (const pose of ['seated', 'standing']) {
    const geos = figureParts(pose), group = people.filter(p => p.pose === pose);
    const colorOf = {suit: p => p.suit, shoes: () => '#111111', skin: p => p.skin, shirt: p => p.shirt, tie: p => p.tie,
                     hairShort: p => p.hairStyle === 'short' ? p.hair : null, hairLong: p => p.hairStyle === 'long' ? p.hair : null};
    for (const part in geos) {
      const list = group.filter(p => colorOf[part](p));
      instanced(geos[part], mats[part], list.map(p => p.m), list.map(p => new THREE.Color(colorOf[part](p))));
    }
  }
}

if (VIEW.sotu) {
  const people = [];
  const seated = (s, shift, extra) => people.push(randomPerson(Object.assign({m: seatMatrix(s, shift, 0)}, extra)));
  const memberShift = 0.46 - L.rows[0].depth / 2;
  // the front rows near the centre aisle: the justices and the Joint Chiefs on one side, the Cabinet on the other
  const near = (row, east) => L.members.filter(s => s.row === row && (east ? s.angle < 90 : s.angle > 90))
    .sort((a, b) => Math.abs(a.angle - 90) - Math.abs(b.angle - 90));
  const special = new Map();
  near(1, true).slice(0, 9).forEach(s => special.set(s, {suit: '#0e0f11', shirt: '#f4f2ee', tie: null}));
  near(2, true).slice(0, 6).forEach(s => special.set(s, {suit: pick(PALETTE.uniform), shirt: '#d8d2c4', tie: '#1b1b1b', woman: false, hairStyle: 'short'}));
  for (const s of L.members) seated(s, memberShift, special.get(s) || {});
  for (const s of L.public) seated(s, 0.46 - L.rows.find(r => r.kind === 'public').depth / 2, {});
  for (const s of PRESS_SEATS) seated(s, 0.46 - 0.85 / 2, {});
  // the President at the rostrum; the Vice President and the Speaker behind
  const at = (x, y, z, face, dy = 0) => new THREE.Matrix4().compose(V(x, y, z + dy), new THREE.Quaternion().setFromAxisAngle(UP, face), ONE);
  people.push(randomPerson({pose: 'standing', m: at(0, 3.02, 0.72, Math.PI / 2), woman: false, hairStyle: 'short', hair: '#9a968e',
                            suit: '#1b2233', shirt: '#f2f2f0', tie: '#2a4b8d', skin: '#e8b996'}));
  for (const x of [-0.62, 0.62]) people.push(randomPerson({m: at(x, 1.12, DAIS, Math.PI / 2, 0.1)}));
  lectern(0, 3.6, 1.78, Math.PI / 2, {w: 0.85, d: 0.44});
  addPeople(people);
}

// ------------------------------------------------------------------ lighting

scene.add(new THREE.HemisphereLight('#fff3e0', '#4a3a2a', 0.42));
const key = new THREE.DirectionalLight('#ffe9c8', 1.15);
key.position.copy(V(-6, 12, 60)); key.target.position.copy(V(0, 17, 0));
key.castShadow = true; key.shadow.mapSize.set(4096, 4096);
Object.assign(key.shadow.camera, {left: -34, right: 34, top: 26, bottom: -26, near: 20, far: 90});
key.shadow.bias = -0.0002; key.shadow.normalBias = 0.02; key.shadow.radius = 2;
scene.add(key, key.target);
const fill = new THREE.DirectionalLight('#ffe9cc', 0.22);
fill.position.copy(V(0, 45, 10)); fill.target.position.copy(V(0, 0, 3)); scene.add(fill, fill.target);
for (const [x, y, z, power] of [[0, 8, 8.2, 0.55], [-16, 14, 8.2, 0.3], [16, 14, 8.2, 0.3], [0, 24, 8.2, 0.35], [-20, 28, 8.2, 0.25], [20, 28, 8.2, 0.25]]) {
  const p = new THREE.PointLight('#ffdcb0', power, 30, 1.5); p.position.copy(V(x, y, z)); scene.add(p);
}
const rostrumSpot = new THREE.SpotLight('#fff0d8', 0.22, 30, 0.55, 0.6, 1.2);
rostrumSpot.position.copy(V(0, 14, 9.8)); rostrumSpot.target.position.copy(V(0, 1, 3)); scene.add(rostrumSpot, rostrumSpot.target);

// ------------------------------------------------------------------ camera

for (const name of VIEW.hide || []) groups[name].visible = false;
const cam = new THREE.PerspectiveCamera(VIEW.fov, canvas.width / canvas.height, 0.1, 120);
cam.position.copy(V(...VIEW.eye));
cam.lookAt(V(...VIEW.target));

// Render in linear light, darken creases with ambient occlusion (SAO), then
// tone-map and encode for the screen.
const size = [canvas.width, canvas.height];
const target = new THREE.WebGLRenderTarget(...size, {type: THREE.HalfFloatType, samples: 4});
const composer = new THREE.EffectComposer(renderer, target);
composer.addPass(new THREE.RenderPass(scene, cam));
const sao = new THREE.SAOPass(scene, cam, true, false, new THREE.Vector2(...size));
const ao = Object.assign({intensity: 3.0, scale: 80, bias: 0.25, kernel: 0.05, blur: 0.006}, VIEW.ao || {});
Object.assign(sao.params, {saoIntensity: ao.intensity, saoScale: ao.scale, saoBias: ao.bias,
  saoKernelRadius: ao.kernel * canvas.width, saoBlurRadius: Math.max(4, Math.round(ao.blur * canvas.width)),
  saoBlurStdDev: Math.max(2, ao.blur * canvas.width / 2), saoBlurDepthCutoff: 0.001, output: VIEW.aoOnly ? 2 : 0});
sao.saoMaterial.defines.NUM_SAMPLES = 16; sao.saoMaterial.needsUpdate = true;
{ // the depth render inside the pass needs no lighting
  const depthOnly = new THREE.MeshBasicMaterial({colorWrite: false});
  const render = sao.render.bind(sao);
  sao.render = (...args) => {
    scene.overrideMaterial = depthOnly; for (const m of NO_AO) m.visible = false;
    try { render(...args); } finally { scene.overrideMaterial = null; for (const m of NO_AO) m.visible = true; }
  };
}
composer.addPass(sao);
composer.addPass(new THREE.ShaderPass({
  uniforms: {tDiffuse: {value: null}},
  vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }',
  // three.js adds its ACES toneMapping() and sRGB linearToOutputTexel() when drawing to the screen
  fragmentShader: `uniform sampler2D tDiffuse; varying vec2 vUv;
    void main() { vec3 c = texture2D(tDiffuse, vUv).rgb; gl_FragColor = ${VIEW.aoOnly ? 'vec4(c, 1.0)' : 'linearToOutputTexel(vec4(toneMapping(c), 1.0))'}; }`,
}));
composer.setSize(...size);
renderer.shadowMap.autoUpdate = false; renderer.shadowMap.needsUpdate = true;
composer.render();
window.RENDERED = true;
