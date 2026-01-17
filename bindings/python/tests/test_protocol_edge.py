import safeserial
from safeserial import _core


def test_deserialize_multiple_frames_returns_remaining():
    pkt1 = _core.Packet.serialize(_core.Packet.TYPE_DATA, 1, b"ONE")
    pkt2 = _core.Packet.serialize(_core.Packet.TYPE_DATA, 2, b"TWO")
    combined = pkt1 + pkt2

    frame, remaining = _core.Packet.deserialize(combined)
    assert frame.valid
    assert frame.payload == b"ONE"
    assert remaining == pkt2


def test_deserialize_without_delimiter_is_incomplete():
    garbage = b"\x01\x02\x03\x04\x05"
    frame, remaining = _core.Packet.deserialize(garbage)
    assert not frame.valid
    assert remaining == garbage
