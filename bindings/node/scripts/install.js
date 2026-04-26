const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const pkgRoot = path.resolve(__dirname, "..");
const platform = process.env.npm_config_platform || process.platform;
const arch = process.env.npm_config_arch || process.arch;
const localPrebuild = path.join(
  pkgRoot,
  "prebuilds",
  `${platform}-${arch}`,
  "safeserial_node.node",
);

function runNodeScript(scriptPath, args = []) {
  const result = spawnSync(process.execPath, [scriptPath, ...args], {
    cwd: pkgRoot,
    env: process.env,
    stdio: "inherit",
  });
  return result.status === 0;
}

function runCopyDeps() {
  const scriptPath = path.join(__dirname, "copy_deps.js");
  if (!runNodeScript(scriptPath)) {
    process.exit(1);
  }
}

function runPrebuildInstall() {
  const scriptPath = require.resolve("prebuild-install/bin.js");
  return runNodeScript(scriptPath);
}

function runCmakeCompile() {
  const scriptPath = path.join(pkgRoot, "node_modules", "cmake-js", "bin", "cmake-js");
  return runNodeScript(scriptPath, ["compile"]);
}

runCopyDeps();

if (fs.existsSync(localPrebuild)) {
  console.log(`[safeserial] Using bundled prebuild: ${localPrebuild}`);
  process.exit(0);
}

if (runPrebuildInstall()) {
  process.exit(0);
}

console.warn("[safeserial] No prebuilt addon found; falling back to local CMake build.");
if (!runCmakeCompile()) {
  process.exit(1);
}
