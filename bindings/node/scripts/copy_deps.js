const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '../../..');
const PKG_ROOT = path.resolve(__dirname, '..');
const DEPS_DIR = path.join(PKG_ROOT, 'deps');

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  let entries = fs.readdirSync(src, { withFileTypes: true });

  for (let entry of entries) {
    let srcPath = path.join(src, entry.name);
    let destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

console.log('[copy_deps] Bundling C++ core files...');

// Clean deps
if (fs.existsSync(DEPS_DIR)) {
  fs.rmSync(DEPS_DIR, { recursive: true, force: true });
}
fs.mkdirSync(DEPS_DIR);

// Copy src
const srcDir = path.join(PROJECT_ROOT, 'src');
const destSrc = path.join(DEPS_DIR, 'src');
console.log(`Copying ${srcDir} -> ${destSrc}`);
copyDir(srcDir, destSrc);

// Copy include
const incDir = path.join(PROJECT_ROOT, 'include');
const destInc = path.join(DEPS_DIR, 'include');
console.log(`Copying ${incDir} -> ${destInc}`);
copyDir(incDir, destInc);

console.log('[copy_deps] Done.');
