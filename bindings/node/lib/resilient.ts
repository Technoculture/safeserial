/**
 * ResilientDataBridge - Connection-resilient wrapper
 *
 * Thin wrapper around the native C++ ResilientDataBridge implementation.
 */

import { EventEmitter } from "events";
import { DataBridgeOptions } from "./reliable";
import { NativeResilientDataBridge } from "./native";

export interface ResilientOptions extends DataBridgeOptions {
  /** Enable auto-reconnection (default: true) */
  reconnect?: boolean;
  /** Initial reconnect delay in ms (default: 1000) */
  reconnectDelay?: number;
  /** Maximum reconnect delay in ms (default: 30000) */
  maxReconnectDelay?: number;
  /** Maximum queue size before dropping old messages (default: 1000) */
  maxQueueSize?: number;
}

export interface ResilientEvents {
  data: (data: Buffer) => void;
  error: (error: Error) => void;
  close: () => void;
  disconnect: () => void;
  reconnecting: (attempt: number, delay: number) => void;
  reconnected: () => void;
}

export class ResilientDataBridge extends EventEmitter {
  private bridge: NativeResilientDataBridge;
  private port: string;
  private options: ResilientOptions;

  private constructor(port: string, options: ResilientOptions) {
    super();
    this.port = port;
    this.options = options;

    this.bridge = new NativeResilientDataBridge(options);
    this.bridge.onData((data) => this.emit("data", data));
    this.bridge.onError((message) => this.emit("error", new Error(message)));
    this.bridge.onDisconnect(() => this.emit("disconnect"));
    this.bridge.onReconnecting((attempt, delay) =>
      this.emit("reconnecting", attempt, delay),
    );
    this.bridge.onReconnected(() => this.emit("reconnected"));
    this.bridge.onClose(() => this.emit("close"));
  }

  /**
   * Open a resilient serial connection.
   *
   * @param port - Serial port path
   * @param options - Configuration including reconnection settings
   */
  static async open(
    port: string,
    options: ResilientOptions = {},
  ): Promise<ResilientDataBridge> {
    const instance = new ResilientDataBridge(port, options);
    await instance.open();
    return instance;
  }

  async open(): Promise<boolean> {
    return this.bridge.open(this.port);
  }

  /**
   * Send data with guaranteed delivery.
   *
   * @param data - Data to send
   * @returns Promise that resolves when data is acknowledged
   */
  async send(data: Buffer | string): Promise<void> {
    const buffer = typeof data === "string" ? Buffer.from(data) : data;
    this.bridge.send(buffer);
  }

  /**
   * Close the connection permanently.
   */
  async close(): Promise<void> {
    this.bridge.close();
  }

  /** Current connection state */
  get connected(): boolean {
    return this.bridge.isConnected();
  }

  /** Number of messages waiting in queue */
  get queueLength(): number {
    return this.bridge.queueLength();
  }

  // Type-safe event emitter
  on<K extends keyof ResilientEvents>(
    event: K,
    listener: ResilientEvents[K],
  ): this {
    return super.on(event, listener);
  }

  once<K extends keyof ResilientEvents>(
    event: K,
    listener: ResilientEvents[K],
  ): this {
    return super.once(event, listener);
  }

  emit<K extends keyof ResilientEvents>(
    event: K,
    ...args: Parameters<ResilientEvents[K]>
  ): boolean {
    return super.emit(event, ...args);
  }
}

export default ResilientDataBridge;
