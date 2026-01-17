import { EventEmitter } from "events";
import { NativeDataBridge } from "./native";

export interface DataBridgeOptions {
  baudRate?: number;
  maxRetries?: number;
  ackTimeoutMs?: number;
  fragmentSize?: number;
}

/**
 * ReliableDataBridge
 *
 * Thin wrapper around the native C++ DataBridge implementation.
 */
export class ReliableDataBridge extends EventEmitter {
  private bridge: NativeDataBridge;
  private isOpen_ = false;

  // Config
  private options: Required<DataBridgeOptions>;

  constructor(options: DataBridgeOptions = {}) {
    super();
    this.bridge = new NativeDataBridge();

    this.options = {
      baudRate: options.baudRate ?? 115200,
      maxRetries: options.maxRetries ?? 10,
      ackTimeoutMs: options.ackTimeoutMs ?? 500,
      fragmentSize: options.fragmentSize ?? 200,
    };

    this.bridge.onData((data) => {
      this.emit("data", data);
    });
  }

  static async open(
    port: string,
    baudOrOptions?: number | DataBridgeOptions,
    cb?: (data: Buffer) => void,
  ): Promise<ReliableDataBridge> {
    let opts: DataBridgeOptions = {};
    if (typeof baudOrOptions === "number") {
      opts.baudRate = baudOrOptions;
    } else if (baudOrOptions) {
      opts = baudOrOptions;
    }

    const bridge = new ReliableDataBridge(opts);
    if (cb) bridge.on("data", cb);

    await bridge.open(port);
    return bridge;
  }

  async open(port: string, baud?: number): Promise<boolean> {
    if (this.isOpen_) return true;

    // Backward compatibility: override baud from options if provided
    const baudRate = baud ?? this.options.baudRate;

    const success = this.bridge.open(port, baudRate);
    if (!success) {
      throw new Error(`Failed to open ${port}`);
    }
    this.isOpen_ = true;
    return true;
  }

  async close(): Promise<void> {
    if (this.isOpen_) {
      this.bridge.close();
      this.isOpen_ = false;
      this.emit("close");
    }
  }

  get isOpen(): boolean {
    return this.isOpen_;
  }

  async send(data: string | Buffer): Promise<void> {
    if (!this.isOpen_) throw new Error("Port not open");
    const buf = Buffer.isBuffer(data) ? data : Buffer.from(data);
    this.bridge.send(
      buf,
      this.options.ackTimeoutMs,
      this.options.maxRetries,
      this.options.fragmentSize,
    );
  }
}
