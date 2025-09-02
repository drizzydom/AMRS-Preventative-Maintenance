const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  onSplashStatus: (callback) => ipcRenderer.on('splash-status', callback),
  send: (channel, ...args) => ipcRenderer.send(channel, ...args)
});
