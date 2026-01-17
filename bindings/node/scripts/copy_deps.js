const fs = require("fs");
const path = require("path");

const PROJECT_ROOT = path.resolve(__dirname, "../../..");
const PKG_ROOT = path.resolve(__dirname, "..");
const DEPS_DIR = path.join(PKG_ROOT, "deps");

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

console.log("[copy_deps] Bundling C++ core files...");

const repoSrc = path.join(PROJECT_ROOT, "src");
const repoInc = path.join(PROJECT_ROOT, "include");
const coreSrc = path.join(PKG_ROOT, "core", "src");
const coreInc = path.join(PKG_ROOT, "core", "include");

let srcDir = repoSrc;
let incDir = repoInc;

if (fs.existsSync(repoSrc) && fs.existsSync(repoInc)) {
  console.log("[copy_deps] Using repo core sources");
} else if (fs.existsSync(coreSrc) && fs.existsSync(coreInc)) {
  console.log("[copy_deps] Using packaged core sources");
  srcDir = coreSrc;
  incDir = coreInc;
} else if (fs.existsSync(DEPS_DIR)) {
  console.log("[copy_deps] deps already present, skipping copy");
  process.exit(0);
} else {
  console.error(
    "[copy_deps] No core sources found. Install from repo or publish with packaged core.",
  );
  process.exit(1);
}

// Clean deps
if (fs.existsSync(DEPS_DIR)) {
  fs.rmSync(DEPS_DIR, { recursive: true, force: true });
}
fs.mkdirSync(DEPS_DIR);

// Copy src
const destSrc = path.join(DEPS_DIR, "src");
console.log(`Copying ${srcDir} -> ${destSrc}`);
copyDir(srcDir, destSrc);

// Copy include
const destInc = path.join(DEPS_DIR, "include");
console.log(`Copying ${incDir} -> ${destInc}`);
copyDir(incDir, destInc);

console.log("[copy_deps] Done.");
