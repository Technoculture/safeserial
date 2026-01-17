import threading

import safeserial
from safeserial import _core


class RetrySerial:
    def __init__(self, drop_count: int = 1):
        self._buffer = bytearray()
        self._write_log = []
        self._lock = threading.Lock()
        self._drop_remaining = drop_count

    def open(self, port, baud):
        return True

    def close(self):
        pass

    def write(self, data):
        with self._lock:
            self._write_log.append(bytes(data))
            if self._drop_remaining > 0:
                self._drop_remaining -= 1
                return len(data)

            frame, _ = _core.Packet.deserialize(data)
            if frame.valid and frame.header.type == _core.Packet.TYPE_DATA:
                ack_pkt = _core.Packet.serialize(
                    _core.Packet.TYPE_ACK,
                    frame.header.seq_id,
                    b"",
                    frame.header.fragment_id,
                    frame.header.total_frags,
                )
                self._buffer.extend(ack_pkt)
        return len(data)

    def read(self, size):
        with self._lock:
            if not self._buffer:
                return b""
            chunk = self._buffer[:size]
            self._buffer = self._buffer[size:]
            return bytes(chunk)


def test_databridge_retries_until_ack():
    serial = RetrySerial(drop_count=1)
    bridge = safeserial.DataBridge(serial=serial)
    assert bridge.open("/dev/test")

    bridge.send("Retry", ack_timeout_ms=50, max_retries=3, fragment_size=64)

    assert len(serial._write_log) >= 2
    bridge.close()
