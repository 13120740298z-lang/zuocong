const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('dumpling', {
  quit: () => ipcRenderer.invoke('app:quit'),
  moveBy: (dx, dy) => ipcRenderer.invoke('window:moveBy', dx, dy),
  chatComplete: (text) => ipcRenderer.invoke('chat:complete', text)
});

