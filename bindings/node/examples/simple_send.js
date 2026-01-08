const { DataBridge } = require('../dist/index.js');

const portPath = process.argv[2] || '/dev/ttyUSB0';
const bridge = new DataBridge();

console.log(`Openning port: ${portPath}`);

async function main() {
  try {
    const isOpen = await bridge.open(portPath, 115200, (data) => {
      console.log(`[RX] ${data.toString()}`);
    });

    if (isOpen) {
      console.log('Port opened successfully');

      const msg = `Hello using DataBridge`;
      console.log(`[TX] ${msg}`);
      await bridge.send(msg);
    }
  } catch (err) {
    console.error("Error:", err);
  }
}

main();
