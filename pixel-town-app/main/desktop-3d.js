'use strict';
// Packaged entry: Electron and all application assets ship together. No external Node or shell.
const {app}=require('electron');
require('../shared/desktop-data').prepare3DData({support:app.getPath('appData')});
process.env.PIXEL_TOWN_3D='1';
require('./main');
