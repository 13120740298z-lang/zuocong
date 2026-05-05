const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const http = require('http');
const https = require('https');

const OPENAI_BASE_URL = process.env.DUMPLING_OPENAI_BASE_URL || 'http://127.0.0.1:8000/v1';
const OPENAI_API_KEY = process.env.DUMPLING_OPENAI_API_KEY || '';
const OPENAI_MODEL = process.env.DUMPLING_OPENAI_MODEL || 'deepseek-chat';

let win;

function requestJson(url, { method, headers, body }) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const isHttps = u.protocol === 'https:';
    const lib = isHttps ? https : http;

    const req = lib.request(
      {
        protocol: u.protocol,
        hostname: u.hostname,
        port: u.port || (isHttps ? 443 : 80),
        path: `${u.pathname}${u.search}`,
        method,
        headers
      },
      (res) => {
        const chunks = [];
        res.on('data', (d) => chunks.push(d));
        res.on('end', () => {
          const text = Buffer.concat(chunks).toString('utf8');
          if (res.statusCode < 200 || res.statusCode >= 300) {
            reject(new Error(`HTTP ${res.statusCode} ${res.statusMessage}${text ? ` - ${text}` : ''}`));
            return;
          }
          try {
            resolve(JSON.parse(text));
          } catch {
            reject(new Error('Invalid JSON response'));
          }
        });
      }
    );

    req.on('error', reject);
    req.setTimeout(15000, () => {
      req.destroy(new Error('Request timeout'));
    });

    if (body) req.write(body);
    req.end();
  });
}

async function openAIChatComplete(userText) {
  const url = new URL('/chat/completions', OPENAI_BASE_URL).toString();
  const payload = {
    model: OPENAI_MODEL,
    messages: [{ role: 'user', content: userText }],
    temperature: 0.7
  };

  const headers = { 'Content-Type': 'application/json' };
  if (OPENAI_API_KEY) headers.Authorization = `Bearer ${OPENAI_API_KEY}`;

  const data = await requestJson(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload)
  });

  const content = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
  if (!content) throw new Error('Chat response missing message content');
  return content;
}

function createWindow() {
  win = new BrowserWindow({
    width: 300,
    height: 300,
    frame: false,
    transparent: true,
    alwaysOnTop: true,
    resizable: false,
    hasShadow: false,
    backgroundColor: '#00000000',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  win.setMenu(null);
  win.setAlwaysOnTop(true, 'screen-saver');

  const { width, height } = screen.getPrimaryDisplay().workAreaSize;
  win.setPosition(Math.max(0, width - 300), Math.max(0, height - 300), false);

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

ipcMain.handle('chat:complete', async (evt, userText) => {
  const text = String(userText || '').slice(0, 4000);
  return await openAIChatComplete(text);
});

