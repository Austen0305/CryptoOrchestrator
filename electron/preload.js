const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // App information
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getPlatform: () => ipcRenderer.invoke('get-platform'),

  // Window controls
  minimizeToTray: () => ipcRenderer.invoke('minimize-to-tray'),
  showWindow: () => ipcRenderer.invoke('show-window'),

  // Menu actions (listen for menu events)
  onMenuNewBot: (callback) => ipcRenderer.on('menu-new-bot', callback),
  onMenuStartAllBots: (callback) => ipcRenderer.on('menu-start-all-bots', callback),
  onMenuStopAllBots: (callback) => ipcRenderer.on('menu-stop-all-bots', callback),
  onMenuTogglePaperMode: (callback) => ipcRenderer.on('menu-toggle-paper-mode', callback),

  // Remove listeners
  removeAllListeners: (event) => ipcRenderer.removeAllListeners(event),

  // Notification support
  showNotification: (title, body, icon) => {
    new Notification(title, {
      body: body,
      icon: icon || '../client/public/favicon.png'
    });
  },
  
  // Auto-updater
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates'),
  quitAndInstall: () => ipcRenderer.invoke('quit-and-install'),
  onUpdateAvailable: (callback) => ipcRenderer.on('update-available', (event, ...args) => callback(...args)),
  onUpdateDownloaded: (callback) => ipcRenderer.on('update-downloaded', (event, ...args) => callback(...args)),
  onUpdateProgress: (callback) => ipcRenderer.on('update-progress', (event, ...args) => callback(...args)),
  onUpdateError: (callback) => ipcRenderer.on('update-error', (event, ...args) => callback(...args)),
  onUpdateNotAvailable: (callback) => ipcRenderer.on('update-not-available', (event, ...args) => callback(...args)),
  
  // Auto-start
  setAutoStart: (enabled) => ipcRenderer.invoke('set-auto-start', enabled),
  getAutoStart: () => ipcRenderer.invoke('get-auto-start'),
  
  // Notifications
  setNotificationsEnabled: (enabled) => ipcRenderer.invoke('set-notifications-enabled', enabled),
  getNotificationsEnabled: () => ipcRenderer.invoke('get-notifications-enabled'),
  
  // Server health
  onServerHealth: (callback) => ipcRenderer.on('server-health', (event, ...args) => callback(...args)),
  onServerLog: (callback) => ipcRenderer.on('server-log', (event, ...args) => callback(...args)),
  onServerError: (callback) => ipcRenderer.on('server-error', (event, ...args) => callback(...args))
});

// Set API URL for Electron environment
contextBridge.exposeInMainWorld('VITE_API_URL', 'http://localhost:8000');
// Also expose consistent globals the client can read
contextBridge.exposeInMainWorld('__API_BASE__', 'http://localhost:8000');
contextBridge.exposeInMainWorld('__WS_BASE__', 'ws://localhost:8000');

// Forward FastAPI health events to renderer if needed
const FASTAPI_HEALTH_EVENT = 'fastapi-health';
ipcRenderer.on(FASTAPI_HEALTH_EVENT, (_evt, payload) => {
  window.dispatchEvent(new CustomEvent(FASTAPI_HEALTH_EVENT, { detail: payload }));
});

// Handle menu events in the renderer
window.addEventListener('DOMContentLoaded', () => {
  // Listen for menu events and dispatch custom events
  ipcRenderer.on('menu-new-bot', () => {
    window.dispatchEvent(new CustomEvent('electron-menu-new-bot'));
  });

  ipcRenderer.on('menu-start-all-bots', () => {
    window.dispatchEvent(new CustomEvent('electron-menu-start-all-bots'));
  });

  ipcRenderer.on('menu-stop-all-bots', () => {
    window.dispatchEvent(new CustomEvent('electron-menu-stop-all-bots'));
  });

  ipcRenderer.on('menu-toggle-paper-mode', (event, checked) => {
    window.dispatchEvent(new CustomEvent('electron-menu-toggle-paper-mode', { detail: checked }));
  });
});
