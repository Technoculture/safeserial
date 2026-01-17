const fs = require('fs');
const path = require('path');

const PROJECT_ROOT = path.resolve(__dirname, '../../..');
const PKG_ROOT = path.resolve(__dirname, '..');
const CORE_DIR = path.join(PKG_ROOT, 'core');

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

const srcDir = path.join(PROJECT_ROOT, 'src');
const incDir = path.join(PROJECT_ROOT, 'include');

if (!fs.existsSync(srcDir) || !fs.existsSync(incDir)) {
  console.error('[prepare_core] Missing repo src/include');
  process.exit(1);
}

if (fs.existsSync(CORE_DIR)) {
  fs.rmSync(CORE_DIR, { recursive: true, force: true });
}

console.log('[prepare_core] Staging core sources for npm package...');
copyDir(srcDir, path.join(CORE_DIR, 'src'));
copyDir(incDir, path.join(CORE_DIR, 'include'));
console.log('[prepare_core] Done.');
