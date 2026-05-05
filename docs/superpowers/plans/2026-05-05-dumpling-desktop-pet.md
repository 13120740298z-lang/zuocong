# Dumpling Desktop Pet (Electron + Canvas) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows desktop pet app “Dumpling” with a transparent, always-on-top, frameless Electron window and a Canvas-drawn character with animations, drag, right-click menu, and OpenAI-compatible chat bubble.

**Architecture:** Use Electron main process for window management and network calls; renderer draws the pet on a single Canvas and runs the animation state machine. Use IPC for commands (quit, move window, chat request/response).

**Tech Stack:** Electron, plain HTML/CSS/JavaScript (no external assets), electron-builder (Windows .exe).

---

## File Structure

- Create: `/workspace/index.html`
  - Renderer UI: Canvas drawing, animation loop, state machine, drag handling, custom context menu, chat input overlay, chat bubble rendering.
- Create: `/workspace/main.js`
  - Electron app entry: transparent always-on-top window, initial position (bottom-right), IPC handlers (window move, quit, chat request).
- Create: `/workspace/preload.js`
  - `contextBridge` API to expose a minimal safe IPC surface to the renderer.
- Create: `/workspace/package.json`
  - `npm start` runs Electron; `npm run dist` builds Windows `.exe` via electron-builder.
- Create: `/workspace/.gitignore`
  - Ignore `node_modules/`, `dist/`, build artifacts.

---

### Task 1: Initialize Electron project scaffold

**Files:**
- Create: `/workspace/package.json`
- Create: `/workspace/main.js`
- Create: `/workspace/preload.js`
- Create: `/workspace/index.html`
- Create: `/workspace/.gitignore`

- [ ] **Step 1: Create `package.json` with Electron + builder**

```json
{
  "name": "dumpling-desktop-pet",
  "version": "1.0.0",
  "private": true,
  "main": "main.js",
  "scripts": {
    "start": "electron .",
    "dist": "electron-builder --win nsis portable"
  },
  "devDependencies": {
    "electron": "^31.0.0",
    "electron-builder": "^24.13.3"
  },
  "build": {
    "appId": "com.dumpling.desktoppet",
    "productName": "Dumpling",
    "files": [
      "main.js",
      "preload.js",
      "index.html"
    ],
    "asar": true,
    "win": {
      "target": [
        "nsis",
        "portable"
      ]
    },
    "nsis": {
      "oneClick": true,
      "perMachine": false,
      "createDesktopShortcut": true,
      "createStartMenuShortcut": true
    }
  }
}
```

- [ ] **Step 2: Create `.gitignore`**

```gitignore
node_modules/
dist/
*.log
```

- [ ] **Step 3: Implement `main.js` window + IPC skeleton**

Key requirements:
- 300x300, `transparent: true`, `frame: false`, `alwaysOnTop: true`
- initial bottom-right positioning based on work area
- IPC:
  - `window:moveBy(dx, dy)` to move window during dragging
  - `app:quit()` to exit
  - `chat:complete(prompt)` to call OpenAI-compatible API and return text

```js
const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');

const OPENAI_BASE_URL = process.env.DUMPLING_OPENAI_BASE_URL || 'http://127.0.0.1:8000/v1';
const OPENAI_API_KEY = process.env.DUMPLING_OPENAI_API_KEY || '';
const OPENAI_MODEL = process.env.DUMPLING_OPENAI_MODEL || 'deepseek-chat';

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 300,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    hasShadow: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  win.setMenu(null);

  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  win.setPosition(Math.max(0, width - 300), Math.max(0, height - 300));

  win.loadFile(path.join(__dirname, 'index.html'));
}

app.whenReady().then(() => {
  createWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

ipcMain.handle('app:quit', () => {
  app.quit();
});

ipcMain.handle('window:moveBy', (evt, dx, dy) => {
  if (!win) return;
  const [x, y] = win.getPosition();
  win.setPosition(x + Math.round(dx), y + Math.round(dy), false);
});

async function openAIChatComplete(userText) {
  const url = new URL('/chat/completions', OPENAI_BASE_URL).toString();
  const body = {
    model: OPENAI_MODEL,
    messages: [{ role: 'user', content: userText }],
    temperature: 0.7
  };

  const headers = { 'Content-Type': 'application/json' };
  if (OPENAI_API_KEY) headers.Authorization = `Bearer ${OPENAI_API_KEY}`;

  const res = await fetch(url, { method: 'POST', headers, body: JSON.stringify(body) });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Chat request failed: ${res.status} ${res.statusText}${text ? ` - ${text}` : ''}`);
  }
  const data = await res.json();
  const content = data?.choices?.[0]?.message?.content;
  if (!content) throw new Error('Chat response missing message content');
  return content;
}

ipcMain.handle('chat:complete', async (evt, userText) => {
  return await openAIChatComplete(String(userText || '').slice(0, 4000));
});
```

- [ ] **Step 4: Implement `preload.js` with minimal API surface**

```js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('dumpling', {
  quit: () => ipcRenderer.invoke('app:quit'),
  moveBy: (dx, dy) => ipcRenderer.invoke('window:moveBy', dx, dy),
  chatComplete: (text) => ipcRenderer.invoke('chat:complete', text)
});
```

- [ ] **Step 5: Create minimal `index.html` that loads renderer code**

Implementation note: keep everything in a single HTML file; inline the JS in a `<script>` tag to avoid extra renderer files.

```html
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Dumpling</title>
    <style>
      html, body { width: 100%; height: 100%; margin: 0; background: transparent; overflow: hidden; }
      canvas { display: block; width: 300px; height: 300px; }
    </style>
  </head>
  <body>
    <canvas id="c" width="300" height="300"></canvas>
    <script>
      // renderer implementation added in later tasks
    </script>
  </body>
</html>
```

- [ ] **Step 6: Install + run smoke test**

Run:

```bash
npm install
npm start
```

Expected:
- A 300x300 transparent frameless window appears (black/opaque indicates transparency isn’t enabled in OS compositor).

- [ ] **Step 7: Commit**

```bash
git add package.json main.js preload.js index.html .gitignore
git commit -m "chore: scaffold electron dumpling app"
```

---

### Task 2: Canvas renderer foundation (drawing + timing)

**Files:**
- Modify: `/workspace/index.html`

- [ ] **Step 1: Implement renderer time loop + shared state**

Add inside `<script>`:

```js
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

const DPR = Math.max(1, Math.floor(window.devicePixelRatio || 1));
canvas.width = 300 * DPR;
canvas.height = 300 * DPR;
canvas.style.width = '300px';
canvas.style.height = '300px';
ctx.setTransform(DPR, 0, 0, DPR, 0, 0);

const state = {
  t0: performance.now(),
  now: performance.now(),
  mode: 'idle', // idle | blink | bounce | think | sleep
  modeSince: performance.now(),
  bubble: null, // { text, until }
  pendingTimers: {
    blinkAt: 0,
    bounceAt: 0
  }
};

function rand(min, max) { return min + Math.random() * (max - min); }
function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function easeOutCubic(x) { return 1 - Math.pow(1 - clamp(x, 0, 1), 3); }
```

- [ ] **Step 2: Add a single `drawDumpling()` that renders the character**

Key visuals:
- body: soft white, semi-transparent, warm glow edge
- hair: 2 strands, time-based swing
- face: dot eyes + blush

```js
function drawDumpling(x, y, p) {
  const r = 62;

  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(p.tilt || 0);

  const glow = ctx.createRadialGradient(0, 0, r * 0.4, 0, 0, r * 1.25);
  glow.addColorStop(0, 'rgba(255,255,255,0.20)');
  glow.addColorStop(0.65, 'rgba(255,255,255,0.08)');
  glow.addColorStop(1, 'rgba(255,210,150,0.00)');
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(0, 0, r * 1.25, 0, Math.PI * 2);
  ctx.fill();

  const body = ctx.createRadialGradient(-r * 0.25, -r * 0.35, r * 0.25, 0, 0, r);
  body.addColorStop(0, 'rgba(255,255,255,0.90)');
  body.addColorStop(1, 'rgba(255,255,255,0.55)');
  ctx.fillStyle = body;
  ctx.beginPath();
  ctx.arc(0, 0, r, 0, Math.PI * 2);
  ctx.fill();

  ctx.strokeStyle = 'rgba(255,230,200,0.25)';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.arc(0, 0, r - 1, 0, Math.PI * 2);
  ctx.stroke();

  const hs = p.hairSwing || 0;
  ctx.strokeStyle = 'rgba(255,255,255,0.80)';
  ctx.lineCap = 'round';
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.moveTo(-12, -r + 6);
  ctx.quadraticCurveTo(-18 - hs * 8, -r - 18, -10 - hs * 2, -r - 30);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(12, -r + 6);
  ctx.quadraticCurveTo(18 + hs * 8, -r - 18, 10 + hs * 2, -r - 30);
  ctx.stroke();

  const eyeY = -8;
  ctx.fillStyle = 'rgba(30,30,30,0.85)';
  if (p.blink) {
    ctx.strokeStyle = 'rgba(30,30,30,0.70)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(-18, eyeY);
    ctx.lineTo(-6, eyeY);
    ctx.moveTo(6, eyeY);
    ctx.lineTo(18, eyeY);
    ctx.stroke();
  } else if (p.sleep) {
    ctx.strokeStyle = 'rgba(30,30,30,0.50)';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(-12, eyeY, 7, 0.1 * Math.PI, 0.9 * Math.PI);
    ctx.arc(12, eyeY, 7, 0.1 * Math.PI, 0.9 * Math.PI);
    ctx.stroke();
  } else {
    ctx.beginPath();
    ctx.arc(-12, eyeY, 4, 0, Math.PI * 2);
    ctx.arc(12, eyeY, 4, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = 'rgba(255,140,170,0.25)';
  ctx.beginPath();
  ctx.arc(-26, 6, 9, 0, Math.PI * 2);
  ctx.arc(26, 6, 9, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}
```

- [ ] **Step 3: Implement `drawBubble()` (chat + think + sleep Zzz)**

```js
function wrapText(text, maxCharsPerLine) {
  const words = String(text || '').split(/\s+/);
  const lines = [];
  let line = '';
  for (const w of words) {
    const next = line ? `${line} ${w}` : w;
    if (next.length > maxCharsPerLine && line) {
      lines.push(line);
      line = w;
    } else {
      line = next;
    }
  }
  if (line) lines.push(line);
  return lines.slice(0, 5);
}

function drawBubble(x, y, text) {
  const lines = wrapText(text, 18);
  ctx.save();
  ctx.translate(x, y);
  ctx.font = '12px system-ui, -apple-system, Segoe UI, sans-serif';
  const padX = 10, padY = 8, lineH = 16;
  const w = Math.max(120, ...lines.map(l => ctx.measureText(l).width)) + padX * 2;
  const h = lines.length * lineH + padY * 2;

  ctx.fillStyle = 'rgba(255,255,255,0.82)';
  ctx.strokeStyle = 'rgba(255,220,190,0.35)';
  ctx.lineWidth = 2;

  const r = 12;
  ctx.beginPath();
  ctx.moveTo(r, 0);
  ctx.arcTo(w, 0, w, h, r);
  ctx.arcTo(w, h, 0, h, r);
  ctx.arcTo(0, h, 0, 0, r);
  ctx.arcTo(0, 0, w, 0, r);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = 'rgba(60,60,60,0.90)';
  lines.forEach((l, i) => ctx.fillText(l, padX, padY + lineH * (i + 1) - 4));
  ctx.restore();
}
```

- [ ] **Step 4: Implement the render loop drawing to center**

```js
function scheduleNext() {
  state.pendingTimers.blinkAt = state.now + rand(5000, 10000);
  state.pendingTimers.bounceAt = state.now + rand(20000, 40000);
}
scheduleNext();

function setMode(mode) {
  state.mode = mode;
  state.modeSince = state.now;
}

function tick() {
  state.now = performance.now();
  ctx.clearRect(0, 0, 300, 300);

  const t = (state.now - state.t0) / 1000;
  const hover = Math.sin(t * Math.PI * 2 * 0.4) * 6;
  const hairSwing = Math.sin(t * Math.PI * 2 * 1.0) * 0.35;

  let yOffset = hover;
  let tilt = 0;
  let blink = false;
  let sleep = state.mode === 'sleep';

  if (state.mode === 'blink') {
    const dt = (state.now - state.modeSince) / 200;
    blink = dt >= 0 && dt <= 1;
    if (dt > 1) setMode('idle');
  }

  if (state.mode === 'bounce') {
    const dur = 1200;
    const p = clamp((state.now - state.modeSince) / dur, 0, 1);
    const two = p * 2;
    const phase = two < 1 ? two : two - 1;
    const amp = two < 1 ? 26 : 16;
    const e = easeOutCubic(phase);
    yOffset += (1 - Math.abs(2 * e - 1)) * (-amp);
    if (p >= 1) setMode('idle');
  }

  if (state.mode === 'think') {
    tilt = Math.sin(t * 2.2) * 0.10;
  }

  if (state.mode === 'sleep') {
    yOffset *= 0.35;
    tilt = 0;
  }

  if (state.mode === 'idle') {
    if (state.now >= state.pendingTimers.blinkAt) { setMode('blink'); scheduleNext(); }
    else if (state.now >= state.pendingTimers.bounceAt) { setMode('bounce'); scheduleNext(); }
  }

  const cx = 150;
  const cy = 160 + yOffset;
  drawDumpling(cx, cy, { hairSwing, tilt, blink, sleep });

  if (state.mode === 'think') {
    drawBubble(cx + 50, cy - 130, '…');
  }
  if (state.bubble && state.now < state.bubble.until) {
    drawBubble(cx + 40, cy - 150, state.bubble.text);
  }
  if (state.mode === 'sleep') {
    drawBubble(cx + 58, cy - 140, 'Zzz');
  }

  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
```

- [ ] **Step 5: Verify render visuals**

Run:

```bash
npm start
```

Expected:
- Dumpling appears (white translucent ball), subtle glow edge, hair wiggle, idle hover.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat: draw dumpling canvas renderer"
```

---

### Task 3: Drag-to-move window (mouse)

**Files:**
- Modify: `/workspace/index.html`

- [ ] **Step 1: Implement pointer drag capturing and send `moveBy`**

Requirements:
- Click-drag anywhere on canvas moves the window.
- Do not start dragging when interacting with menu/input elements.

```js
let dragging = false;
let last = null;

function isUIEventTarget(el) {
  return el && (el.closest?.('#menu') || el.closest?.('#chat'));
}

window.addEventListener('pointerdown', (e) => {
  if (e.button !== 0) return;
  if (isUIEventTarget(e.target)) return;
  dragging = true;
  last = { x: e.screenX, y: e.screenY };
});

window.addEventListener('pointermove', (e) => {
  if (!dragging || !last) return;
  const dx = e.screenX - last.x;
  const dy = e.screenY - last.y;
  last = { x: e.screenX, y: e.screenY };
  window.dumpling?.moveBy(dx, dy);
});

window.addEventListener('pointerup', () => {
  dragging = false;
  last = null;
});
```

- [ ] **Step 2: Verify dragging**

Expected:
- Left mouse drag moves the frameless window smoothly.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: drag moves window via ipc"
```

---

### Task 4: Custom right-click menu (chat / walk / sleep / quit)

**Files:**
- Modify: `/workspace/index.html`

- [ ] **Step 1: Add menu HTML + CSS overlay**

Add to `<body>` after canvas:

```html
<div id="menu" hidden>
  <button data-act="chat">聊天</button>
  <button data-act="walk">散步</button>
  <button data-act="sleep">睡觉</button>
  <button data-act="quit">退出</button>
</div>
```

CSS (in `<style>`):

```css
#menu {
  position: fixed;
  min-width: 120px;
  padding: 6px;
  border-radius: 10px;
  background: rgba(255,255,255,0.86);
  border: 1px solid rgba(255,210,180,0.45);
  backdrop-filter: blur(6px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.18);
}
#menu button {
  display: block;
  width: 100%;
  border: 0;
  background: transparent;
  padding: 8px 10px;
  text-align: left;
  font: 12px system-ui, -apple-system, Segoe UI, sans-serif;
  color: rgba(50,50,50,0.92);
}
#menu button:hover {
  background: rgba(255,220,190,0.35);
  border-radius: 8px;
}
```

- [ ] **Step 2: Implement menu show/hide + actions**

```js
const menu = document.getElementById('menu');

function hideMenu() { menu.hidden = true; }
function showMenu(x, y) {
  menu.hidden = false;
  const mw = 140, mh = 150;
  const px = clamp(x, 6, window.innerWidth - mw - 6);
  const py = clamp(y, 6, window.innerHeight - mh - 6);
  menu.style.left = `${px}px`;
  menu.style.top = `${py}px`;
}

window.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  showMenu(e.clientX, e.clientY);
});
window.addEventListener('pointerdown', (e) => {
  if (!menu.hidden && !menu.contains(e.target)) hideMenu();
});

menu.addEventListener('click', async (e) => {
  const btn = e.target.closest('button[data-act]');
  if (!btn) return;
  hideMenu();
  const act = btn.dataset.act;
  if (act === 'quit') window.dumpling?.quit();
  if (act === 'walk') setMode('bounce');
  if (act === 'sleep') setMode(state.mode === 'sleep' ? 'idle' : 'sleep');
  if (act === 'chat') openChat();
});
```

- [ ] **Step 3: Verify menu behavior**

Expected:
- Right-click shows menu.
- Click outside closes it.
- “散步” triggers bounce.
- “睡觉” toggles sleep mode.
- “退出” closes app.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: custom context menu actions"
```

---

### Task 5: Chat input overlay + think state + bubble display

**Files:**
- Modify: `/workspace/index.html`
- Modify: `/workspace/main.js` (optional: improve error extraction)

- [ ] **Step 1: Add chat overlay HTML + CSS**

Add to `<body>`:

```html
<div id="chat" hidden>
  <input id="chatInput" placeholder="跟小团子说点什么…" />
  <button id="chatSend">发送</button>
</div>
```

CSS:

```css
#chat {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: 12px;
  display: flex;
  gap: 8px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(255,255,255,0.86);
  border: 1px solid rgba(255,210,180,0.45);
  backdrop-filter: blur(6px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.18);
}
#chat input {
  flex: 1;
  border: 1px solid rgba(0,0,0,0.10);
  border-radius: 10px;
  padding: 8px 10px;
  font: 12px system-ui, -apple-system, Segoe UI, sans-serif;
  outline: none;
  background: rgba(255,255,255,0.90);
}
#chat button {
  border: 0;
  border-radius: 10px;
  padding: 8px 12px;
  font: 12px system-ui, -apple-system, Segoe UI, sans-serif;
  background: rgba(255,200,170,0.75);
  color: rgba(60,60,60,0.92);
}
#chat button:hover { background: rgba(255,200,170,0.95); }
```

- [ ] **Step 2: Implement `openChat()` and send flow**

```js
const chat = document.getElementById('chat');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');

function openChat() {
  chat.hidden = false;
  chatInput.value = '';
  chatInput.focus();
  setMode('think');
}
function closeChat() {
  chat.hidden = true;
}

async function sendChat() {
  const text = String(chatInput.value || '').trim();
  if (!text) return;
  chatSend.disabled = true;
  setMode('think');
  try {
    const reply = await window.dumpling.chatComplete(text);
    state.bubble = { text: reply, until: performance.now() + 10000 };
    setMode('idle');
    closeChat();
  } catch (err) {
    state.bubble = { text: `（请求失败）${String(err?.message || err)}`, until: performance.now() + 10000 };
    setMode('idle');
    closeChat();
  } finally {
    chatSend.disabled = false;
  }
}

chatSend.addEventListener('click', sendChat);
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendChat();
  if (e.key === 'Escape') { setMode('idle'); closeChat(); }
});
```

- [ ] **Step 3: Verify think + bubble**

Expected:
- Opening chat shows input overlay and sets think state (… bubble).
- Sending message triggers IPC request; reply appears in bubble for 10 seconds.

- [ ] **Step 4: Add documentation for env vars**

In `README.md` (optional) describe:
- `DUMPLING_OPENAI_BASE_URL`
- `DUMPLING_OPENAI_API_KEY`
- `DUMPLING_OPENAI_MODEL`

- [ ] **Step 5: Commit**

```bash
git add index.html main.js README.md
git commit -m "feat: chat overlay and ai bubble"
```

---

### Task 6: Packaging for Windows `.exe` + validation

**Files:**
- Modify: `/workspace/package.json`

- [ ] **Step 1: Ensure builder config includes required files**

Confirm `build.files` includes `index.html`, `main.js`, `preload.js`.

- [ ] **Step 2: Build**

Run:

```bash
npm run dist
```

Expected:
- `dist/` contains:
  - `Dumpling Setup *.exe` (NSIS installer)
  - `Dumpling *.exe` (portable)

- [ ] **Step 3: Quick runtime validation**

On a Windows machine:
- Launch portable `.exe`
- Verify: transparent window, drag works, menu works
- Set env vars (or adapt to config file later) and verify chat.

- [ ] **Step 4: Commit**

```bash
git add package.json
git commit -m "chore: add electron-builder windows exe targets"
```

---

## Self-Review Checklist (run before implementation handoff)

- No external images/assets; all visuals drawn on Canvas.
- Renderer contains 4 required animation states: idle, blink, bounce, think (sleep is extra but optional).
- Right-click menu includes: 聊天/散步/睡觉/退出.
- Chat calls OpenAI-compatible endpoint; model defaults to `deepseek-chat`.
- API key not logged anywhere; prefer environment variables over hardcoding.
- Windows packaging produces `.exe` via electron-builder.

