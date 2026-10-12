const fs = require('node:fs');
const path = require('node:path');

const nodeModulesPath = path.resolve(__dirname, '..', 'node_modules');
fs.rmSync(nodeModulesPath, { recursive: true, force: true });
