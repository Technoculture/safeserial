
import { EventEmitter } from 'events';
import { SerialPort, Packet, Reassembler, Frame } from './native';

export interface DataBridgeOptions {
  baudRate?: number;
  maxRetries?: number;
  ackTimeoutMs?: number;
  fragmentSize?: number;
}

/**
 * ReliableDataBridge
 * 
 * Implements Stop-and-Wait ARQ with fragmentation/reassembly.
 * Mirrors the Python bindings.wrapper.DataBridge logic.
 */
export class ReliableDataBridge extends EventEmitter {
  private serial: SerialPort;
  private reassembler: Reassembler;
  private isOpen_ = false;

  // Config
  private options: Required<DataBridgeOptions>;

  // State
  private seqId = 0;
  private rxBuffer = Buffer.alloc(0);

  // ARQ State
  // We only process one send at a time (Stop-and-Wait)
  // Map of seqId -> { resolve, reject } (though we only have one really)
  private pendingAcks = new Map<number, (fragId: number) => void>();

  constructor(options: DataBridgeOptions = {}) {
    super();
    this.serial = new SerialPort();
    this.reassembler = new Reassembler();

    this.options = {
      baudRate: options.baudRate ?? 115200,
      maxRetries: options.maxRetries ?? 10,
      ackTimeoutMs: options.ackTimeoutMs ?? 500,
      fragmentSize: options.fragmentSize ?? 200
    };
  }

  static async open (port: string, baudOrOptions?: number | DataBridgeOptions, cb?: (data: Buffer) => void): Promise<ReliableDataBridge> {
    let opts: DataBridgeOptions = {};
    if (typeof baudOrOptions === 'number')
    {
      opts.baudRate = baudOrOptions;
    } else if (baudOrOptions)
    {
      opts = baudOrOptions;
    }

    const bridge = new ReliableDataBridge(opts);
    if (cb) bridge.on('data', cb);

    await bridge.open(port);
    return bridge;
  }

  async open (port: string, baud?: number): Promise<boolean> {
    if (this.isOpen_) return true;

    // Backward compatibility: override baud from options if provided
    const baudRate = baud ?? this.options.baudRate;

    const success = this.serial.open(port, baudRate, (data) => {
      this.onData(data);
    });

    if (success)
    {
      this.isOpen_ = true;
      return true;
    }
    throw new Error(`Failed to open ${port}`);
  }

  async close (): Promise<void> {
    if (this.isOpen_)
    {
      this.serial.close();
      this.isOpen_ = false;
      this.emit('close');
    }
  }

  get isOpen (): boolean {
    return this.isOpen_;
  }

  async send (data: string | Buffer): Promise<void> {
    if (!this.isOpen_) throw new Error("Port not open");

    const buf = Buffer.isBuffer(data) ? data : Buffer.from(data);

    // Fragment
    const fragments: Buffer[] = [];
    for (let i = 0; i < buf.length; i += this.options.fragmentSize)
    {
      fragments.push(buf.subarray(i, i + this.options.fragmentSize));
    }

    const totalFrags = fragments.length;
    const seq = this.seqId;
    this.seqId = (this.seqId + 1) % 256;

    for (let fragId = 0; fragId < totalFrags; fragId++)
    {
      const payload = fragments[fragId];

      const packet = Packet.serialize(
        Packet.TYPE_DATA,
        seq,
        payload,
        fragId,
        totalFrags
      );

      await this.sendWithRetry(packet, seq, fragId);
    }
  }

  private async sendWithRetry (packet: Buffer, seq: number, fragId: number): Promise<void> {
    let retries = 0;

    while (retries <= this.options.maxRetries)
    {
      // Prepare waiter
      const ackPromise = new Promise<void>((resolve, reject) => {
        const handler = (ackedFragId: number) => {
          if (ackedFragId === fragId) resolve();
        };
        this.pendingAcks.set(seq, handler);

        // Timeout
        setTimeout(() => {
          if (this.pendingAcks.has(seq))
          {
            this.pendingAcks.delete(seq);
            reject(new Error("Timeout"));
          }
        }, this.options.ackTimeoutMs);
      });

      // Send
      this.serial.write(packet);

      try
      {
        await ackPromise;
        return; // Success
      } catch (e)
      {
        retries++;
        // console.log(`[Reliable] Retry ${retries} for seq=${seq} frag=${fragId}`);
      }
    }

    throw new Error(`Send failed after ${this.options.maxRetries} retries`);
  }

  private onData (chunk: Buffer) {
    this.rxBuffer = Buffer.concat([this.rxBuffer, chunk]);

    while (true)
    {
      const { frame, remaining } = Packet.deserialize(this.rxBuffer);

      if (!frame.valid)
      {
        if (remaining.length === this.rxBuffer.length)
        {
          break;
        }
        // Else we consumed some garbage, continue loop with remaining
        this.rxBuffer = Buffer.from(remaining);
        continue;
      }

      // Valid frame
      this.rxBuffer = Buffer.from(remaining);

      if (frame.header.type === Packet.TYPE_ACK)
      {
        const seq = frame.header.seq_id;
        const frag = frame.header.fragment_id;

        if (this.pendingAcks.has(seq))
        {
          this.pendingAcks.get(seq)!(frag);
        }
      } else if (frame.header.type === Packet.TYPE_DATA)
      {
        let shouldAck = false;

        if (this.reassembler.processFragment(frame))
        {
          shouldAck = true;
          if (this.reassembler.isComplete(frame))
          {
            try
            {
              const data = this.reassembler.getData();
              this.emit('data', data);
            } catch (e)
            {
              console.error("Error in data emission:", e);
            }
          }
        } else if (this.reassembler.isDuplicate(frame))
        {
          shouldAck = true;
        }

        if (shouldAck)
        {
          const ackParams = Packet.serialize(
            Packet.TYPE_ACK,
            frame.header.seq_id,
            Buffer.alloc(0),
            frame.header.fragment_id,
            frame.header.total_frags
          );
          this.serial.write(ackParams);
        }
      }
    }
  }
}
