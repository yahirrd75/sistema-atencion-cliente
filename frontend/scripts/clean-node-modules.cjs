const fs = require('node:fs');
const path = require('node:path');

const frontendPath = path.resolve(__dirname, '..');
for (const directory of ['node_modules', '.angular']) {
  fs.rmSync(path.join(frontendPath, directory), { recursive: true, force: true });
}

console.log('Removed Angular build-only dependencies and cache.');
