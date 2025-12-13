const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('gestura', {
  version: '1.0.0'
});



