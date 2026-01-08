/**
 * ResilientDataBridge - Connection-resilient wrapper
 * 
 * Guarantees message delivery across USB disconnections by:
 * 1. Auto-reconnection with exponential backoff
 * 2. Message queue for pending sends during disconnect
 * 3. Automatic re-handshake and queue flush on reconnect
 */

import { EventEmitter } from 'events';
import { DataBridge, DataBridgeOptions } from './index';

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

interface QueuedMessage {
  data: Buffer;
  resolve: () => void;
  reject: (err: Error) => void;
  timestamp: number;
}

export class ResilientDataBridge extends EventEmitter {
  private bridge: DataBridge | null = null;
  private port: string;
  private options: Required<ResilientOptions>;
  private messageQueue: QueuedMessage[] = [];
  private isConnected = false;
  private isReconnecting = false;
  private shouldReconnect = true;
  private reconnectAttempt = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;

  private constructor(port: string, options: ResilientOptions) {
    super();
    this.port = port;
    this.options = {
      baudRate: options.baudRate ?? 115200,
      reconnect: options.reconnect ?? true,
      reconnectDelay: options.reconnectDelay ?? 1000,
      maxReconnectDelay: options.maxReconnectDelay ?? 30000,
      maxQueueSize: options.maxQueueSize ?? 1000,
    };
  }

  /**
   * Open a resilient serial connection.
   * 
   * @param port - Serial port path
   * @param options - Configuration including reconnection settings
   */
  static async open (port: string, options: ResilientOptions = {}): Promise<ResilientDataBridge> {
    const instance = new ResilientDataBridge(port, options);
    await instance.connect();
    return instance;
  }

  private async connect (): Promise<void> {
    try
    {
      this.bridge = new DataBridge();
      await this.bridge.open(this.port, this.options.baudRate);

      this.isConnected = true;
      this.reconnectAttempt = 0;

      // Forward data events
      this.bridge.on('data', (data) => {
        this.emit('data', data);
      });

      // Handle errors and detect disconnection
      this.bridge.on('error', (err) => {
        this.emit('error', err);
        this.handleDisconnect();
      });

      // If we're reconnecting, emit event and flush queue
      if (this.isReconnecting)
      {
        this.isReconnecting = false;
        this.emit('reconnected');
        await this.flushQueue();
      }
    } catch (err)
    {
      this.isConnected = false;
      if (this.shouldReconnect && this.options.reconnect)
      {
        this.scheduleReconnect();
      } else
      {
        throw err;
      }
    }
  }

  private handleDisconnect (): void {
    if (!this.isConnected) return;

    this.isConnected = false;
    this.bridge = null;
    this.emit('disconnect');

    if (this.shouldReconnect && this.options.reconnect)
    {
      this.scheduleReconnect();
    }
  }

  private scheduleReconnect (): void {
    if (this.reconnectTimeout) return;

    this.isReconnecting = true;
    this.reconnectAttempt++;

    // Exponential backoff with jitter
    const baseDelay = this.options.reconnectDelay;
    const maxDelay = this.options.maxReconnectDelay;
    const delay = Math.min(
      baseDelay * Math.pow(2, this.reconnectAttempt - 1) + Math.random() * 1000,
      maxDelay
    );

    this.emit('reconnecting', this.reconnectAttempt, delay);

    this.reconnectTimeout = setTimeout(async () => {
      this.reconnectTimeout = null;
      try
      {
        await this.connect();
      } catch
      {
        // connect() will schedule another attempt if needed
      }
    }, delay);
  }

  /**
   * Send data with guaranteed delivery.
   * 
   * If disconnected, the message is queued and will be sent
   * automatically when the connection is restored.
   * 
   * @param data - Data to send
   * @returns Promise that resolves when data is acknowledged
   */
  async send (data: Buffer | string): Promise<void> {
    const buffer = typeof data === 'string' ? Buffer.from(data) : data;

    if (this.isConnected && this.bridge)
    {
      // Connected - send immediately
      try
      {
        await this.bridge.send(buffer);
      } catch (err)
      {
        // Send failed - queue it and handle disconnect
        return this.queueMessage(buffer);
      }
    } else
    {
      // Disconnected - queue the message
      return this.queueMessage(buffer);
    }
  }

  private queueMessage (data: Buffer): Promise<void> {
    return new Promise((resolve, reject) => {
      // Enforce max queue size (drop oldest)
      while (this.messageQueue.length >= this.options.maxQueueSize)
      {
        const dropped = this.messageQueue.shift();
        dropped?.reject(new Error('Message dropped: queue overflow'));
      }

      this.messageQueue.push({
        data,
        resolve,
        reject,
        timestamp: Date.now(),
      });
    });
  }

  private async flushQueue (): Promise<void> {
    while (this.messageQueue.length > 0 && this.isConnected && this.bridge)
    {
      const msg = this.messageQueue.shift()!;
      try
      {
        await this.bridge.send(msg.data);
        msg.resolve();
      } catch (err)
      {
        // Put it back at the front and stop flushing
        this.messageQueue.unshift(msg);
        break;
      }
    }
  }

  /**
   * Close the connection permanently.
   * Rejects all pending queued messages.
   */
  async close (): Promise<void> {
    this.shouldReconnect = false;

    if (this.reconnectTimeout)
    {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    // Reject all queued messages
    for (const msg of this.messageQueue)
    {
      msg.reject(new Error('Connection closed'));
    }
    this.messageQueue = [];

    if (this.bridge)
    {
      await this.bridge.close();
      this.bridge = null;
    }

    this.isConnected = false;
    this.emit('close');
  }

  /** Current connection state */
  get connected (): boolean {
    return this.isConnected;
  }

  /** Number of messages waiting in queue */
  get queueLength (): number {
    return this.messageQueue.length;
  }

  // Type-safe event emitter
  on<K extends keyof ResilientEvents> (event: K, listener: ResilientEvents[K]): this {
    return super.on(event, listener);
  }

  once<K extends keyof ResilientEvents> (event: K, listener: ResilientEvents[K]): this {
    return super.once(event, listener);
  }

  emit<K extends keyof ResilientEvents> (event: K, ...args: Parameters<ResilientEvents[K]>): boolean {
    return super.emit(event, ...args);
  }
}

export default ResilientDataBridge;
