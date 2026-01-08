import threading
import time
from typing import Callable, Optional, Union, Dict
from . import _core

# Re-export key classes for low-level access if needed
Packet = _core.Packet
SerialPort = _core.SerialPort
Reassembler = _core.Reassembler

# Configuration defaults (match C++ config.hpp)
MAX_RETRIES = 10
ACK_TIMEOUT_MS = 500
RETRY_TIMEOUT_MS = 2000


class DataBridge:
    """
    High-level DataBridge client with reliable ARQ (Automatic Repeat reQuest).
    
    Implements Stop-and-Wait ARQ:
    - Sender waits for ACK after each packet
    - Timeout triggers retransmission (up to MAX_RETRIES)
    - Receiver sends ACK for each valid packet
    """
    
    def __init__(self):
        self._serial = _core.SerialPort()
        self._is_open = False
        self._bg_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._on_data_callback: Optional[Callable[[bytes], None]] = None
        self._seq_id = 0
        self._lock = threading.Lock()
        
        # ACK tracking for reliable send
        # Map seq_id -> (fragment_id, event)
        self._pending_acks: Dict[int, tuple[int, threading.Event]] = {}
        self._ack_lock = threading.Lock()
        
        self._reassembler = _core.Reassembler()

    def get_received_bytes(self) -> int:
        """Return the number of bytes currently buffered in the reassembler."""
        return self._reassembler.get_buffered_size()

    def open(self, port: str, baud_rate: int = 115200, on_data: Optional[Callable[[bytes], None]] = None) -> bool:
        """
        Open the serial port.
        :param port: Device path (e.g. /dev/ttyUSB0 or COM3)
        :param baud_rate: Baud rate (default 115200)
        :param on_data: Optional callback for received data
        :return: True if successful
        """
        if self._is_open:
            return True

        if self._serial.open(port, baud_rate):
            self._is_open = True
            if on_data:
                self.on('data', on_data)
            
            self._stop_event.clear()
            self._bg_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self._bg_thread.start()
            return True
        return False
    
    def is_open(self) -> bool:
        return self._is_open

    def close(self) -> None:
        """Close the serial port and stop background processing."""
        self._stop_event.set()
        
        # Wake up any pending sends
        with self._ack_lock:
            for _, evt in self._pending_acks.values():
                evt.set()
            self._pending_acks.clear()
        
        if self._bg_thread and self._bg_thread.is_alive():
            self._bg_thread.join(timeout=1.0)
        
        self._serial.close()
        self._is_open = False

    def send(self, data: Union[str, bytes], timeout_ms: int = RETRY_TIMEOUT_MS, max_retries: int = MAX_RETRIES, fragment_size: int = 200) -> int:
        """
        Send data with guaranteed delivery (ARQ) and automatic fragmentation.
        """
        if not self._is_open:
            raise RuntimeError("Port not open")
            
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Fragment the data
        fragments = []
        for i in range(0, len(data), fragment_size):
            fragments.append(data[i:i+fragment_size])
        
        total_frags = len(fragments)
        total_bytes_written = 0
        
        # Get sequence ID
        with self._lock:
            seq = self._seq_id
            self._seq_id = (self._seq_id + 1) % 256
        
        # Send each fragment with Stop-and-Wait ARQ
        for frag_id, frag_data in enumerate(fragments):
            # Create fresh ACK event for this fragment
            ack_event = threading.Event()
            with self._ack_lock:
                self._pending_acks[seq] = (frag_id, ack_event)
            
            packet = _core.Packet.serialize(
                _core.Packet.TYPE_DATA, 
                seq, 
                frag_data,
                frag_id,        
                total_frags     
            )
            
            # ARQ: Send and wait for ACK with retry
            retries = 0
            acked = False
            
            try:
                while retries <= max_retries and not acked:
                    # Clear event
                    ack_event.clear()
                    
                    # Send packet
                    bytes_written = self._serial.write(packet)
                    
                    # Wait for ACK
                    ack_received = ack_event.wait(timeout=timeout_ms / 1000.0)
                    
                    if ack_received:
                        total_bytes_written += bytes_written
                        acked = True
                    else:
                        retries += 1
                
                if not acked:
                    raise RuntimeError(f"Send failed after {max_retries} retries (seq={seq}, frag={frag_id}/{total_frags})")
                    
            finally:
                # Remove from pending
                with self._ack_lock:
                    self._pending_acks.pop(seq, None)
        
        return total_bytes_written


    def on(self, event: str, callback: Callable[[bytes], None]):
        if event == 'data':
            self._on_data_callback = callback
        else:
            raise ValueError(f"Unknown event: {event}")

    def _receive_loop(self):
        """Background thread for reading, reassembly, and ACK handling."""
        # reassembler = _core.Reassembler()  <-- Using self._reassembler now
        rx_pool = bytearray()
        
        while not self._stop_event.is_set():
            # Read chunk
            chunk = self._serial.read(1024)
            if chunk:
                rx_pool.extend(chunk)
                
                # Deserialization loop
                while True:
                    frame, remaining = _core.Packet.deserialize(bytes(rx_pool))
                    
                    if not frame.valid:
                        # If bytes were consumed (buffer shrank), it was a corrupted frame.
                        # We must consume the bytes and continue (try next frame).
                        if len(remaining) < len(rx_pool):
                            # print(f"[WARN] Discarding corrupted frame ({len(rx_pool) - len(remaining)} bytes)")
                            rx_pool = bytearray(remaining)
                            continue
                        else:
                            # partial frame, wait for more data
                            break
                    
                    # Consume processed bytes
                    rx_pool = bytearray(remaining)
                    
                    # Handle by packet type
                    if frame.header.type == _core.Packet.TYPE_ACK:
                        seq = frame.header.seq_id
                        frag = frame.header.fragment_id
                        
                        # print(f"[DEBUG] Rx ACK seq={seq} frag={frag}")
                        with self._ack_lock:
                            if seq in self._pending_acks:
                                expected_frag, evt = self._pending_acks[seq]
                                if frag == expected_frag:
                                    evt.set()
                                # else:
                                #    print(f"[DEBUG] Ignored ACK seq={seq} frag={frag} (expected {expected_frag})")
                    
                    elif frame.header.type == _core.Packet.TYPE_DATA:
                        should_ack = False
                        
                        if self._reassembler.process_fragment(frame):
                             should_ack = True
                             if self._reassembler.is_complete(frame):
                                 data = self._reassembler.get_data()
                                 if self._on_data_callback:
                                     try:
                                         self._on_data_callback(data)
                                     except Exception as e:
                                         print(f"Error in data callback: {e}")
                        elif self._reassembler.is_duplicate(frame):
                             should_ack = True
                        
                        # Always send ACK for valid DATA packets (including duplicates)
                        # Include fragment_id in ACK so sender knows which fragment is ACKed
                        if should_ack:
                            ack_pkt = _core.Packet.serialize(
                                _core.Packet.TYPE_ACK, 
                                frame.header.seq_id, 
                                b"", 
                                frame.header.fragment_id, 
                                frame.header.total_frags
                            )
                            self._serial.write(ack_pkt)
                    
                    elif frame.header.type == _core.Packet.TYPE_NACK:
                        pass
            
            time.sleep(0.001) 
