const os = require('os');
const EventEmitter = require('events');
// Load the compiled binary
const native = require('../build/Release/serial_native.node');

class BaseDriver extends EventEmitter {
    constructor() {
        super();
        this.instance = new native.SerialNative(); // The C++ instance
    }

    send(data) {
        // data: string or buffer
        return this.instance.write(data);
    }

    // A loop to poll the serial port and emit events
    startListening() {
        setInterval(() => {
            const buffer = this.instance.read();
            if (buffer && buffer.length > 0) {
                this.emit('data', buffer);
            }
        }, 10);
    }
}

// Architecture-specific exports
if (os.platform() === 'win32') {
    exports.WindowsDriver = class extends BaseDriver {};
} else if (os.platform() === 'linux') {
    exports.LinuxDriver = class extends BaseDriver {};
} else {
    throw new Error("Unsupported Platform");
}
