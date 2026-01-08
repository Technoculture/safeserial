const { ResilientDataBridge } = require('../dist/index.js');

async function main() {
  const port = process.argv[2];
  const itemCount = parseInt(process.argv[3] || '20', 10);
  const baudRate = 115200; // Match Chaos Monkey defaults

  if (!port) {
    console.error("Usage: node sender.js <port> [item_count]");
    process.exit(1);
  }

  console.log(`[SENDER] Connecting to ${port}...`);
  const bridge = await ResilientDataBridge.open(port, {
    baudRate,
    reconnect: true
  });

  console.log(`[SENDER] Starting transmission of ${itemCount} items...`);

  for (let i = 0; i < itemCount; i++) {
    const msg = `Packet-${i}`;
    try {
      await bridge.send(msg);
      console.log(`[SENDER] Sent: ${msg}`);
    } catch (err) {
      console.error(`[SENDER] Error sending ${msg}:`, err);
    }

    // Small delay to prevent overwhelming the chaos monkey's internal buffer too fast 
    // if we want to simulate realistic traffic, though the bridge handles backpressure.
    await new Promise(r => setTimeout(r, 50));
  }

  // Give time for final ACKs
  await new Promise(r => setTimeout(r, 2000));

  console.log("[SENDER] TEST COMPLETE");

  // Clean exit
  await bridge.close();
  process.exit(0);
}

main().catch(err => {
  console.error("[SENDER] Fatal:", err);
  process.exit(1);
});
