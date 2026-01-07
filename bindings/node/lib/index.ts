/**
 * Data Bridge - Guaranteed Reliable Serial Communication
 * 
 * TypeScript wrapper for the native Node-API addon.
 * Provides a clean, async-friendly API for Electron applications.
 */

import { EventEmitter } from 'events';
import path from 'path';

// Load native addon - works in both ESM and CJS
let addon: NativeAddon;

function loadAddon (): NativeAddon {
  const possiblePaths = [
    // Prebuilt binaries
    `../prebuilds/${process.platform}-${process.arch}/data_bridge_node.node`,
    // Local build
    '../build/Release/data_bridge_node.node',
  ];

  for (const p of possiblePaths)
  {
    try
    {
      // Use require for native addons (works in both ESM and CJS)
      return require(path.join(__dirname, p));
    } catch
    {
      continue;
    }
  }

  throw new Error('Failed to load native addon. Run `npm run build` first.');
}

addon = loadAddon();

interface NativeAddon {
  DataBridge: new () => NativeDataBridge;
}

interface NativeDataBridge {
  open (port: string, baud: number, callback?: (data: Buffer) => void): Promise<boolean>;
  send (data: Buffer | string): Promise<number>;
  close (): boolean;
  isOpen (): boolean;
}

export interface DataBridgeOptions {
  baudRate?: number;
}

export interface DataBridgeEvents {
  data: (data: Buffer) => void;
  error: (error: Error) => void;
  close: () => void;
}

/**
 * DataBridge provides guaranteed reliable serial communication.
 * 
 * Features:
 * - Automatic retransmission on packet loss
 * - CRC32 integrity checking
 * - COBS framing for robust delimitation
 * - Fragmentation for large messages
 * 
 * @example
 * ```typescript
 * const bridge = await DataBridge.open('/dev/ttyUSB0');
 * 
 * bridge.on('data', (data) => {
 *   console.log('Received:', data.toString());
 * });
 * 
 * await bridge.send('Hello, World!');
 * await bridge.close();
 * ```
 */
export class DataBridge extends EventEmitter {
  private native: NativeDataBridge;
  private _isOpen = false;

  private constructor() {
    super();
    this.native = new addon.DataBridge();
  }

  /**
   * Open a serial port with guaranteed reliable communication.
   * 
   * @param port - Serial port path (e.g., '/dev/ttyUSB0' or 'COM3')
   * @param options - Configuration options
   * @returns Promise resolving to a DataBridge instance
   */
  static async open (port: string, options: DataBridgeOptions = {}): Promise<DataBridge> {
    const instance = new DataBridge();
    const baud = options.baudRate ?? 115200;

    const onData = (data: Buffer) => {
      instance.emit('data', data);
    };

    try
    {
      await instance.native.open(port, baud, onData);
      instance._isOpen = true;
      return instance;
    } catch (err)
    {
      throw new Error(`Failed to open ${port}: ${err instanceof Error ? err.message : err}`);
    }
  }

  /**
   * Send data with guaranteed delivery.
   * 
   * The data will be fragmented if necessary, checksummed, and
   * retransmitted until acknowledged by the receiver.
   * 
   * @param data - Data to send (Buffer or string)
   * @returns Promise resolving when data is acknowledged
   */
  async send (data: Buffer | string): Promise<void> {
    if (!this._isOpen)
    {
      throw new Error('Port not open');
    }

    const buffer = typeof data === 'string' ? Buffer.from(data) : data;
    await this.native.send(buffer);
  }

  /**
   * Close the serial port.
   */
  async close (): Promise<void> {
    if (this._isOpen)
    {
      this.native.close();
      this._isOpen = false;
      this.emit('close');
    }
  }

  /**
   * Check if the port is currently open.
   */
  get isOpen (): boolean {
    return this._isOpen && this.native.isOpen();
  }

  // Type-safe event emitter methods
  on<K extends keyof DataBridgeEvents> (event: K, listener: DataBridgeEvents[K]): this {
    return super.on(event, listener);
  }

  once<K extends keyof DataBridgeEvents> (event: K, listener: DataBridgeEvents[K]): this {
    return super.once(event, listener);
  }

  emit<K extends keyof DataBridgeEvents> (event: K, ...args: Parameters<DataBridgeEvents[K]>): boolean {
    return super.emit(event, ...args);
  }
}

export default DataBridge;
