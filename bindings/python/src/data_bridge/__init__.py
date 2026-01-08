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
        self._pending_acks: Dict[int, threading.Event] = {}
        self._ack_lock = threading.Lock()

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

    def close(self) -> None:
        """Close the serial port and stop background processing."""
        self._stop_event.set()
        
        # Wake up any pending sends
        with self._ack_lock:
            for evt in self._pending_acks.values():
                evt.set()
            self._pending_acks.clear()
        
        if self._bg_thread and self._bg_thread.is_alive():
            self._bg_thread.join(timeout=1.0)
        
        self._serial.close()
        self._is_open = False

    def is_open(self) -> bool:
        """Check if port is open."""
        return self._is_open

    def send(self, data: Union[str, bytes], timeout_ms: int = RETRY_TIMEOUT_MS, max_retries: int = MAX_RETRIES) -> int:
        """
        Send data with guaranteed delivery (ARQ).
        
        Blocks until ACK received or max retries exceeded.
        
        :param data: String or bytes to send
        :param timeout_ms: Timeout per attempt in milliseconds
        :param max_retries: Maximum retry attempts
        :return: Number of bytes written
        :raises RuntimeError: If port not open or max retries exceeded
        """
        if not self._is_open:
            raise RuntimeError("Port not open")
            
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # Get next sequence ID
        with self._lock:
            seq = self._seq_id
            self._seq_id = (self._seq_id + 1) % 256
        
        # Create ACK event for this sequence
        ack_event = threading.Event()
        with self._ack_lock:
            self._pending_acks[seq] = ack_event
        
        # Serialize packet
        packet = _core.Packet.serialize(_core.Packet.TYPE_DATA, seq, data)
        
        # ARQ: Send and wait for ACK with retry
        retries = 0
        bytes_written = 0
        
        try:
            while retries <= max_retries:
                # Send packet
                bytes_written = self._serial.write(packet)
                
                # Wait for ACK
                ack_received = ack_event.wait(timeout=timeout_ms / 1000.0)
                
                if ack_received:
                    return bytes_written
                
                # Timeout - clear and retry
                ack_event.clear()
                retries += 1
                
                if retries <= max_retries:
                    # Optional: could log retry here
                    pass
            
            # Max retries exceeded
            raise RuntimeError(f"Send failed after {max_retries} retries (seq={seq})")
            
        finally:
            # Cleanup
            with self._ack_lock:
                self._pending_acks.pop(seq, None)

    def on(self, event: str, callback: Callable[[bytes], None]):
        """
        Register event handler.
        :param event: Event name (only 'data' supported currently)
        :param callback: Function taking bytes
        """
        if event == 'data':
            self._on_data_callback = callback
        else:
            raise ValueError(f"Unknown event: {event}")

    def _receive_loop(self):
        """Background thread for reading, reassembly, and ACK handling."""
        reassembler = _core.Reassembler()
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
                        break
                    
                    # Consume processed bytes
                    rx_pool = bytearray(remaining)
                    
                    # Handle by packet type
                    if frame.header.type == _core.Packet.TYPE_ACK:
                        # Signal pending send that ACK received
                        seq = frame.header.seq_id
                        with self._ack_lock:
                            if seq in self._pending_acks:
                                self._pending_acks[seq].set()
                    
                    elif frame.header.type == _core.Packet.TYPE_DATA:
                        # Process incoming data
                        if reassembler.process_fragment(frame):
                            if reassembler.is_complete(frame):
                                data = reassembler.get_data()
                                if self._on_data_callback:
                                    try:
                                        self._on_data_callback(data)
                                    except Exception as e:
                                        print(f"Error in data callback: {e}")
                        
                        # Always send ACK for valid DATA packets
                        ack_pkt = _core.Packet.serialize(_core.Packet.TYPE_ACK, frame.header.seq_id, b"")
                        self._serial.write(ack_pkt)
                    
                    elif frame.header.type == _core.Packet.TYPE_NACK:
                        # Could trigger immediate retry - for now treat like timeout
                        seq = frame.header.seq_id
                        with self._ack_lock:
                            if seq in self._pending_acks:
                                # Don't set - let timeout trigger retry
                                pass
            
            time.sleep(0.001) 
