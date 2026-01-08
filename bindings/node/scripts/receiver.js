const { ResilientDataBridge } = require('../dist/index.js');

async function main() {
  const port = process.argv[2];

  // We don't strictly need item count here for logic, but helpful for knowing when to stop logging?
  // The python runner kills us, so we just log what we get.

  if (!port) {
    console.error("Usage: node receiver.js <port>");
    process.exit(1);
  }

  console.log(`[RECEIVER] Connecting to ${port}...`);
  const bridge = await ResilientDataBridge.open(port, {
    baudRate: 115200,
    reconnect: true
  });

  let receivedCount = 0;

  bridge.on('data', (data) => {
    const str = data.toString();
    receivedCount++;
    console.log(`[RECEIVER] Got: ${str} (Total: ${receivedCount})`);
  });

  console.log("[RECEIVER] Listening...");

  // Keep alive until killed
  await new Promise(() => { });
}

main().catch(err => {
  console.error("[RECEIVER] Fatal:", err);
  process.exit(1);
});
