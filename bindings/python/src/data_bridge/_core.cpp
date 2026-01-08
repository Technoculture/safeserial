#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <data_bridge/protocol/packet.hpp>
#include <data_bridge/protocol/reassembler.hpp>
#include <data_bridge/transport/serial_port.hpp>

namespace py = pybind11;

// Helper to convert vector<uint8_t> to py::bytes
py::bytes vec_to_bytes(const std::vector<uint8_t>& vec) {
    return py::bytes(reinterpret_cast<const char*>(vec.data()), vec.size());
}

// Helper to convert py::bytes to vector<uint8_t>
std::vector<uint8_t> bytes_to_vec(py::bytes b) {
    std::string s = b; // Implicit conversion or cast
    const uint8_t* data = reinterpret_cast<const uint8_t*>(s.data());
    return std::vector<uint8_t>(data, data + s.size());
}

PYBIND11_MODULE(_core, m) {
    m.doc() = "Python bindings for Data Bridge SDK";

    // Packet Class
    py::class_<Packet> packet(m, "Packet");
    
    // Packet Constants
    packet.attr("TYPE_DATA") = Packet::TYPE_DATA;
    packet.attr("TYPE_ACK") = Packet::TYPE_ACK;
    packet.attr("TYPE_NACK") = Packet::TYPE_NACK;
    packet.attr("TYPE_SYN") = Packet::TYPE_SYN;

    // Header Struct
    py::class_<Packet::Header>(packet, "Header")
        .def_readonly("type", &Packet::Header::type)
        .def_readonly("seq_id", &Packet::Header::seq_id)
        .def_readonly("fragment_id", &Packet::Header::fragment_id)
        .def_readonly("total_frags", &Packet::Header::total_frags)
        .def_readonly("payload_len", &Packet::Header::payload_len)
        .def_readonly("crc32", &Packet::Header::crc32);

    // Frame Struct
    py::class_<Packet::Frame>(packet, "Frame")
        .def_readonly("header", &Packet::Frame::header)
        .def_property_readonly("payload", [](const Packet::Frame& f) {
            return vec_to_bytes(f.payload);
        })
        .def_readonly("valid", &Packet::Frame::valid);

    // Packet Static Methods
    packet.def_static("serialize", [](uint8_t type, uint8_t seq, py::bytes payload, uint16_t frag_id, uint16_t total_frags) {
        std::string s = payload;
        return vec_to_bytes(Packet::serialize(type, seq, s, frag_id, total_frags));
    }, py::arg("type"), py::arg("seq"), py::arg("payload"), py::arg("frag_id") = 0, py::arg("total_frags") = 1);

    packet.def_static("deserialize", [](py::object buffer_obj) {
        // We have to be careful with buffer modification. 
        // Packet::deserialize takes std::vector<uint8_t>& and MODIFIES it (removes processed bytes).
        // This is hard to map directly to immutable python bytes.
        // We probably need a stateful buffer class or just pass a bytearray and copy back?
        // OR: Require the user to pass a bytearray, convert to vector, process, update bytearray?
        // Pythonic way: Pass bytes, return (Frame, remaining_bytes).
        
        // Let's implement input as bytes, return (Frame, remaining_bytes)
        py::bytes b = buffer_obj; // or cast
        std::vector<uint8_t> vec = bytes_to_vec(b);
        auto frame = Packet::deserialize(vec);
        
        return py::make_tuple(frame, vec_to_bytes(vec));
    }, "Deserialize a packet from bytes. Returns (Frame, remaining_bytes).");
    
    // Cobs wrappers if needed, but serialize/deserialize handles it usually.
    packet.def_static("cobs_encode", [](py::bytes data) {
         return vec_to_bytes(Packet::cobs_encode(bytes_to_vec(data)));
    });
    
    packet.def_static("cobs_decode", [](py::bytes data) {
         return vec_to_bytes(Packet::cobs_decode(bytes_to_vec(data)));
    });

    // Reassembler Class
    py::class_<Reassembler>(m, "Reassembler")
        .def(py::init<>())
        .def("process_fragment", &Reassembler::process_fragment)
        .def("is_complete", &Reassembler::is_complete)
        .def("is_duplicate", &Reassembler::is_duplicate)
        .def("get_data", [](const Reassembler& r) {
            return vec_to_bytes(r.get_data());
        })
        .def("get_buffered_size", &Reassembler::get_buffered_size)
        .def("get_current_seq", &Reassembler::get_current_seq);

    // SerialPort Class
    // ISerialPort is abstract, SerialPort is concrete.
    py::class_<ISerialPort>(m, "ISerialPort"); // interface binding if needed
    
    py::class_<SerialPort, ISerialPort>(m, "SerialPort")
        .def(py::init<>())
        .def("open", &SerialPort::open)
        .def("close", &SerialPort::close)
        .def("write", [](SerialPort& self, py::bytes data) {
            std::vector<uint8_t> vec = bytes_to_vec(data);
            return self.write(vec);
        })
        .def("read", [](SerialPort& self, size_t size) {
            std::vector<uint8_t> buf(size);
            int n = self.read(buf.data(), size);
            if (n < 0) n = 0;
            buf.resize(n);
            return vec_to_bytes(buf);
        });
}
