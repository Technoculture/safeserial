const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const platform = process.env.npm_config_platform || process.platform;
const arch = process.env.npm_config_arch || process.arch;
const outputDir = path.resolve(__dirname, "..", "prebuilds", `${platform}-${arch}`);

fs.mkdirSync(outputDir, { recursive: true });

const bin = path.resolve(
  __dirname,
  "..",
  "node_modules",
  "cmake-js",
  "bin",
  "cmake-js",
);
const args = ["compile", "-O", outputDir];
const result = spawnSync(
  process.execPath,
  [bin, ...args],
  {
    cwd: path.resolve(__dirname, ".."),
    env: {
      ...process.env,
      npm_config_platform: platform,
      npm_config_arch: arch,
    },
    stdio: "inherit",
  },
);

if (result.error) {
  console.error(result.error);
  process.exit(1);
}

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

const builtAddon = path.join(outputDir, "Release", "safeserial_node.node");
const finalAddon = path.join(outputDir, "safeserial_node.node");

if (fs.existsSync(builtAddon)) {
  fs.copyFileSync(builtAddon, finalAddon);
  fs.rmSync(path.dirname(builtAddon), { recursive: true, force: true });
} else if (!fs.existsSync(finalAddon)) {
  console.error(`[prebuild] Could not find built addon at ${builtAddon}`);
  process.exit(1);
}

console.log(`[prebuild] Wrote ${finalAddon}`);
