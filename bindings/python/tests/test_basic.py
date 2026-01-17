import threading
import time

import pytest

import safeserial
from safeserial import _core

# --- Low-Level Binding Tests (Regression) ---


def test_packet_constants():
    assert _core.Packet.TYPE_DATA == 0x10
    assert _core.Packet.TYPE_ACK == 0x20


def test_packet_serialization():
    payload = b"Hello World"
    seq = 1
    packet_bytes = _core.Packet.serialize(_core.Packet.TYPE_DATA, seq, payload)
    assert len(packet_bytes) > 0

    frame, remaining = _core.Packet.deserialize(packet_bytes)
    assert frame.valid
    assert frame.header.type == _core.Packet.TYPE_DATA
    assert frame.header.seq_id == seq
    assert frame.payload == payload


# --- High-Level API Tests ---


class MockSerial:
    """Mock for SerialPort to intercept write/read calls."""

    def __init__(self):
        self._buffer = bytearray()
        self._write_log = []
        self._lock = threading.Lock()

    def open(self, port, baud):
        return True

    def close(self):
        pass

    def write(self, data):
        with self._lock:
            self._write_log.append(bytes(data))

            # Auto-ACK logic for testing
            try:
                # 1. Deserialize the packet we just "sent"
                frame, _ = _core.Packet.deserialize(data)
                if frame.valid and frame.header.type == _core.Packet.TYPE_DATA:
                    # 2. Construct ACK
                    ack_pkt = _core.Packet.serialize(
                        _core.Packet.TYPE_ACK, frame.header.seq_id, b""
                    )
                    # 3. Queue ACK to be "read" back by the bridge
                    self._buffer.extend(ack_pkt)
            except Exception:
                pass  # Ignore invalid packets

        return len(data)

    def read(self, size):
        with self._lock:
            if not self._buffer:
                return b""
            chunk = self._buffer[:size]
            self._buffer = self._buffer[size:]
            return bytes(chunk)

    def queue_read(self, data):
        with self._lock:
            self._buffer.extend(data)


@pytest.fixture
def mock_bridge():
    """Fixture to provide a DataBridge instance with a mocked SerialPort."""
    mock_serial = MockSerial()

    bridge = safeserial.DataBridge(serial=mock_serial)
    try:
        yield bridge, mock_serial
    finally:
        try:
            bridge.close()
        except Exception:
            pass


def test_databridge_open_send(mock_bridge):
    bridge, mock_serial = mock_bridge
    assert bridge.open("/dev/test")
    assert bridge.is_open()

    bridge.send("Test Payload")

    # Verify write was called
    assert len(mock_serial._write_log) >= 1
    sent_pkt = mock_serial._write_log[-1]

    # Verify packet content
    frame, _ = _core.Packet.deserialize(sent_pkt)
    assert frame.valid
    assert frame.payload == b"Test Payload"

    bridge.close()
    assert not bridge.is_open()


def test_databridge_receive(mock_bridge):
    bridge, mock_serial = mock_bridge
    received_data = []

    def on_data(data):
        received_data.append(data)

    bridge.open("/dev/test")
    bridge.on("data", on_data)

    # Simulate incoming packet
    payload = b"Incoming"
    pkt = _core.Packet.serialize(_core.Packet.TYPE_DATA, 5, payload)

    # Queue it into the mock serial buffer
    mock_serial.queue_read(pkt)

    # Wait for processing (thread sleep)
    time.sleep(0.1)

    assert len(received_data) == 1
    assert received_data[0] == payload

    # Verify ACK was sent
    assert len(mock_serial._write_log) == 1
    ack_frame, _ = _core.Packet.deserialize(mock_serial._write_log[0])
    assert ack_frame.header.type == _core.Packet.TYPE_ACK
    assert ack_frame.header.seq_id == 5

    bridge.close()
