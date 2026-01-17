import path from "path";

// Load native addon
function loadAddon(): any {
  const possiblePaths = [
    `../prebuilds/${process.platform}-${process.arch}/safeserial_node.node`,
    "../build/Release/safeserial_node.node",
  ];

  for (const p of possiblePaths) {
    try {
      return require(path.join(__dirname, p));
    } catch {
      continue;
    }
  }
  throw new Error("Failed to load native addon. Run `npm run build` first.");
}

const addon = loadAddon();

export interface SerialPort {
  open(port: string, baud: number, callback: (data: Buffer) => void): boolean;
  write(data: Buffer): number;
  close(): boolean;
  isOpen(): boolean;
}

export const SerialPort: {
  new (): SerialPort;
} = addon.SerialPort;

export interface NativeDataBridge {
  open(port: string, baud?: number): boolean;
  close(): boolean;
  send(
    data: Buffer | string,
    ackTimeoutMs?: number,
    maxRetries?: number,
    fragmentSize?: number,
  ): number;
  isOpen(): boolean;
  onData(callback: (data: Buffer) => void): void;
}

export const NativeDataBridge: {
  new (): NativeDataBridge;
} = addon.DataBridge;

export interface NativeResilientDataBridge {
  open(port: string): boolean;
  close(): boolean;
  send(data: Buffer | string): number;
  isConnected(): boolean;
  queueLength(): number;
  onData(callback: (data: Buffer) => void): void;
  onError(callback: (message: string) => void): void;
  onDisconnect(callback: () => void): void;
  onReconnecting(callback: (attempt: number, delay: number) => void): void;
  onReconnected(callback: () => void): void;
  onClose(callback: () => void): void;
}

export const NativeResilientDataBridge: {
  new (options?: any): NativeResilientDataBridge;
} = addon.ResilientDataBridge;

export interface Frame {
  valid: boolean;
  header: {
    type: number;
    seq_id: number;
    fragment_id: number;
    total_frags: number;
    payload_len: number;
    crc32: number;
  };
  payload: Buffer;
}

export interface PacketHelper {
  serialize(
    type: number,
    seq: number,
    payload: string | Buffer,
    frag_id?: number,
    total_frags?: number,
  ): Buffer;
  deserialize(buffer: Buffer): { frame: Frame; remaining: Buffer };
  TYPE_DATA: number;
  TYPE_ACK: number;
  TYPE_NACK: number;
  TYPE_SYN: number;
}

export const Packet: PacketHelper = addon.Packet;

export interface Reassembler {
  processFragment(frame: Frame): boolean;
  isComplete(frame: Frame): boolean;
  getData(): Buffer;
  isDuplicate(frame: Frame): boolean;
  getBufferedSize(): number;
}

export const Reassembler: {
  new (): Reassembler;
} = addon.Reassembler;
