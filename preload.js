const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electron', {
    // Expose any Electron or Node.js functionalities needed in the renderer process
});
