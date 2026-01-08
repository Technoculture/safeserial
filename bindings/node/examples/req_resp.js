const { DataBridge } = require('../dist/index.js');

const portPath = process.argv[2] || '/dev/ttyUSB0';
const bridge = new DataBridge();

async function main() {
  await bridge.open(portPath, 115200, async (dataBuf) => {
    try {
      const str = dataBuf.toString();
      console.log(`[RX RAW] ${str}`);
      const msg = JSON.parse(str);

      if (msg.type === 'ping') {
        console.log(`Received PING (ID: ${msg.id}). Sending PONG...`);
        await bridge.send(JSON.stringify({ type: 'pong', id: msg.id }));
      } else if (msg.type === 'pong') {
        console.log(`Received PONG (ID: ${msg.id}). RTT complete.`);
      }
    } catch (e) {
      console.log('Received non-JSON or partial data:', dataBuf.toString());
    }
  });

  console.log(`Examples running on ${portPath}`);
  console.log('Sending PING every 2 seconds...');

  let reqId = 0;
  setInterval(async () => {
    const id = ++reqId;
    const req = { type: 'ping', id };
    console.log(`[TX] Sending PING ID ${id}`);
    await bridge.send(JSON.stringify(req));
  }, 2000);
}

main();
