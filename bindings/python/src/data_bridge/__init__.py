import threading
import time
from typing import Callable, Optional, Union
from . import _core

# Re-export key classes for low-level access if needed
Packet = _core.Packet
SerialPort = _core.SerialPort
Reassembler = _core.Reassembler

class DataBridge:
    """
    High-level DataBridge client mirroring the Node.js API.
    Provides async-like serial communication via background threading.
    """
    
    def __init__(self):
        self._serial = _core.SerialPort()
        self._is_open = False
        self._bg_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._on_data_callback: Optional[Callable[[bytes], None]] = None
        self._seq_id = 0
        self._lock = threading.Lock()

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
        if self._bg_thread and self._bg_thread.is_alive():
            self._bg_thread.join(timeout=1.0)
        
        self._serial.close()
        self._is_open = False

    def is_open(self) -> bool:
        """Check if port is open."""
        return self._is_open

    def send(self, data: Union[str, bytes]) -> int:
        """
        Send data.
        :param data: String or bytes to send
        :return: Number of bytes written
        """
        if not self._is_open:
            raise RuntimeError("Port not open")
            
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        with self._lock:
            seq = self._seq_id
            self._seq_id = (self._seq_id + 1) % 256
        
        # Serialize with next sequence ID
        packet = _core.Packet.serialize(_core.Packet.TYPE_DATA, seq, data)
        return self._serial.write(packet)

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
        """Background thread for reading and reassembly."""
        reassembler = _core.Reassembler()
        rx_pool = bytearray()
        
        while not self._stop_event.is_set():
            # Read chunk
            chunk = self._serial.read(1024)
            if chunk:
                rx_pool.extend(chunk)
                
                # Deserialization loop
                while True:
                    # Packet.deserialize expects bytes, we pass our buffer
                    # Returns (frame, remaining_bytes)
                    # We convert bytearray to bytes for binding, then update pool
                    frame, remaining = _core.Packet.deserialize(bytes(rx_pool))
                    
                    if not frame.valid:
                        break
                    
                    # Update pool with remaining data (effectively consumes frame)
                    rx_pool = bytearray(remaining)
                    
                    if frame.header.type == _core.Packet.TYPE_DATA:
                        if reassembler.process_fragment(frame):
                            if reassembler.is_complete(frame):
                                data = reassembler.get_data()
                                if self._on_data_callback:
                                    try:
                                        self._on_data_callback(data)
                                    except Exception as e:
                                        print(f"Error in data callback: {e}")
                        
                        # Send ACK
                        ack_pkt = _core.Packet.serialize(_core.Packet.TYPE_ACK, frame.header.seq_id, b"")
                        self._serial.write(ack_pkt)
            
            time.sleep(0.001) 
