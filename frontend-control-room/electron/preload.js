const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('controlRoom', {
  platform: process.platform,
  electronVersion: process.versions.electron,
});
