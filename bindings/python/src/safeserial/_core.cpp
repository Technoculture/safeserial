#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <algorithm>
#include <cstring>
#include <safeserial/safeserial.hpp>
#include <safeserial/resilient_bridge.hpp>
#include <safeserial/protocol/packet.hpp>
#include <safeserial/protocol/reassembler.hpp>
#include <safeserial/transport/serial_port.hpp>

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

class PySerialPortAdapter : public ISerialPort {
public:
    explicit PySerialPortAdapter(py::object obj) : obj_(std::move(obj)) {}

    bool open(const std::string& port_name, int baud_rate) override {
        py::gil_scoped_acquire gil;
        return obj_.attr("open")(port_name, baud_rate).cast<bool>();
    }

    void close() override {
        py::gil_scoped_acquire gil;
        obj_.attr("close")();
    }

    int write(const std::vector<uint8_t>& data) override {
        py::gil_scoped_acquire gil;
        py::bytes payload(reinterpret_cast<const char*>(data.data()), data.size());
        return obj_.attr("write")(payload).cast<int>();
    }

    int read(uint8_t* buffer, size_t size) override {
        py::gil_scoped_acquire gil;
        py::object res = obj_.attr("read")(size);
        py::bytes payload = res;
        std::string s = payload;
        size_t n = std::min(size, s.size());
        if (n > 0) {
            std::memcpy(buffer, s.data(), n);
        }
        return static_cast<int>(n);
    }

private:
    py::object obj_;
};

PYBIND11_MODULE(_core, m) {
    m.doc() = "Python bindings for SafeSerial SDK";

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

    py::class_<DataBridge>(m, "DataBridge")
        .def(py::init<>())
        .def(py::init([](py::object serial_override,
                         int baud_rate,
                         uint8_t max_retries,
                         uint16_t ack_timeout_ms,
                         uint16_t fragment_size) {
            DataBridge::Options options = DataBridge::Options::Defaults();
            options.baud_rate = baud_rate;
            options.max_retries = max_retries;
            options.ack_timeout_ms = ack_timeout_ms;
            options.fragment_size = fragment_size;

            auto serial = std::make_shared<PySerialPortAdapter>(std::move(serial_override));
            return new DataBridge(std::move(serial), options);
        }),
        py::kw_only(),
        py::arg("serial"),
        py::arg("baud_rate") = DataBridge::Options::Defaults().baud_rate,
        py::arg("max_retries") = DataBridge::Options::Defaults().max_retries,
        py::arg("ack_timeout_ms") = DataBridge::Options::Defaults().ack_timeout_ms,
        py::arg("fragment_size") = DataBridge::Options::Defaults().fragment_size)
        .def("open", [](DataBridge& self,
                        const std::string& port,
                        int baud_rate,
                        py::object on_data) {
            if (!on_data.is_none()) {
                py::function cb = on_data.cast<py::function>();
                self.set_on_data([cb = std::move(cb)](const std::vector<uint8_t>& data) {
                    py::gil_scoped_acquire gil;
                    cb(vec_to_bytes(data));
                });
            }
            return self.open(port, baud_rate);
        }, py::arg("port"), py::arg("baud_rate") = -1, py::arg("on_data") = py::none())
        .def("close", &DataBridge::close)
        .def("is_open", &DataBridge::is_open)
        .def("send", [](DataBridge& self,
                        py::object data,
                        uint16_t ack_timeout_ms,
                        uint8_t max_retries,
                        uint16_t fragment_size) {
            std::vector<uint8_t> vec;
            if (py::isinstance<py::bytes>(data)) {
                vec = bytes_to_vec(data.cast<py::bytes>());
            } else {
                std::string s = data.cast<std::string>();
                vec.assign(s.begin(), s.end());
            }
            py::gil_scoped_release release;
            return self.send(vec, ack_timeout_ms, max_retries, fragment_size);
        }, py::arg("data"),
        py::arg("ack_timeout_ms") = 0,
        py::arg("max_retries") = 0,
        py::arg("fragment_size") = 0)
        .def("on", [](DataBridge& self, const std::string& event, py::function cb) {
            if (event != "data") {
                throw py::value_error("Unsupported event");
            }
            self.set_on_data([cb = std::move(cb)](const std::vector<uint8_t>& data) {
                py::gil_scoped_acquire gil;
                cb(vec_to_bytes(data));
            });
        })
        .def("set_on_data", [](DataBridge& self, py::function cb) {
            self.set_on_data([cb = std::move(cb)](const std::vector<uint8_t>& data) {
                py::gil_scoped_acquire gil;
                cb(vec_to_bytes(data));
            });
        })
        .def("get_buffered_size", &DataBridge::get_buffered_size)
        .def("get_received_bytes", &DataBridge::get_buffered_size);

    py::class_<ResilientDataBridge>(m, "ResilientDataBridge")
        .def(py::init<>())
        .def(py::init([](int baud_rate,
                         uint8_t max_retries,
                         uint16_t ack_timeout_ms,
                         uint16_t fragment_size,
                         bool reconnect,
                         uint32_t reconnect_delay_ms,
                         uint32_t max_reconnect_delay_ms,
                         size_t max_queue_size) {
            ResilientDataBridge::Options options = ResilientDataBridge::Options::Defaults();
            options.bridge.baud_rate = baud_rate;
            options.bridge.max_retries = max_retries;
            options.bridge.ack_timeout_ms = ack_timeout_ms;
            options.bridge.fragment_size = fragment_size;
            options.reconnect = reconnect;
            options.reconnect_delay_ms = reconnect_delay_ms;
            options.max_reconnect_delay_ms = max_reconnect_delay_ms;
            options.max_queue_size = max_queue_size;
            return new ResilientDataBridge(options);
        }),
        py::kw_only(),
        py::arg("baud_rate") = ResilientDataBridge::Options::Defaults().bridge.baud_rate,
        py::arg("max_retries") = ResilientDataBridge::Options::Defaults().bridge.max_retries,
        py::arg("ack_timeout_ms") = ResilientDataBridge::Options::Defaults().bridge.ack_timeout_ms,
        py::arg("fragment_size") = ResilientDataBridge::Options::Defaults().bridge.fragment_size,
        py::arg("reconnect") = ResilientDataBridge::Options::Defaults().reconnect,
        py::arg("reconnect_delay_ms") = ResilientDataBridge::Options::Defaults().reconnect_delay_ms,
        py::arg("max_reconnect_delay_ms") = ResilientDataBridge::Options::Defaults().max_reconnect_delay_ms,
        py::arg("max_queue_size") = ResilientDataBridge::Options::Defaults().max_queue_size)
        .def("open", [](ResilientDataBridge& self,
                        const std::string& port,
                        py::object on_data) {
            if (!on_data.is_none()) {
                py::function cb = on_data.cast<py::function>();
                self.set_on_data([cb = std::move(cb)](const std::vector<uint8_t>& data) {
                    py::gil_scoped_acquire gil;
                    cb(vec_to_bytes(data));
                });
            }
            return self.open(port);
        }, py::arg("port"), py::arg("on_data") = py::none())
        .def("close", &ResilientDataBridge::close)
        .def("send", [](ResilientDataBridge& self, py::object data) {
            std::vector<uint8_t> vec;
            if (py::isinstance<py::bytes>(data)) {
                vec = bytes_to_vec(data.cast<py::bytes>());
            } else {
                std::string s = data.cast<std::string>();
                vec.assign(s.begin(), s.end());
            }
            py::gil_scoped_release release;
            return self.send(vec);
        }, py::arg("data"))
        .def("on", [](ResilientDataBridge& self, const std::string& event, py::function cb) {
            if (event == "data") {
                self.set_on_data([cb = std::move(cb)](const std::vector<uint8_t>& data) {
                    py::gil_scoped_acquire gil;
                    cb(vec_to_bytes(data));
                });
                return;
            }
            if (event == "disconnect") {
                self.set_on_disconnect([cb = std::move(cb)]() {
                    py::gil_scoped_acquire gil;
                    cb();
                });
                return;
            }
            if (event == "reconnecting") {
                self.set_on_reconnecting([cb = std::move(cb)](uint32_t attempt, uint32_t delay) {
                    py::gil_scoped_acquire gil;
                    cb(attempt, delay);
                });
                return;
            }
            if (event == "reconnected") {
                self.set_on_reconnected([cb = std::move(cb)]() {
                    py::gil_scoped_acquire gil;
                    cb();
                });
                return;
            }
            if (event == "error") {
                self.set_on_error([cb = std::move(cb)](const std::string& msg) {
                    py::gil_scoped_acquire gil;
                    cb(msg);
                });
                return;
            }
            if (event == "close") {
                self.set_on_close([cb = std::move(cb)]() {
                    py::gil_scoped_acquire gil;
                    cb();
                });
                return;
            }
            throw py::value_error("Unsupported event");
        })
        .def("set_on_data", [](ResilientDataBridge& self, py::function cb) {
            self.set_on_data([cb = std::move(cb)](const std::vector<uint8_t>& data) {
                py::gil_scoped_acquire gil;
                cb(vec_to_bytes(data));
            });
        })
        .def("set_on_error", [](ResilientDataBridge& self, py::function cb) {
            self.set_on_error([cb = std::move(cb)](const std::string& msg) {
                py::gil_scoped_acquire gil;
                cb(msg);
            });
        })
        .def("set_on_disconnect", [](ResilientDataBridge& self, py::function cb) {
            self.set_on_disconnect([cb = std::move(cb)]() {
                py::gil_scoped_acquire gil;
                cb();
            });
        })
        .def("set_on_reconnecting", [](ResilientDataBridge& self, py::function cb) {
            self.set_on_reconnecting([cb = std::move(cb)](uint32_t attempt, uint32_t delay) {
                py::gil_scoped_acquire gil;
                cb(attempt, delay);
            });
        })
        .def("set_on_reconnected", [](ResilientDataBridge& self, py::function cb) {
            self.set_on_reconnected([cb = std::move(cb)]() {
                py::gil_scoped_acquire gil;
                cb();
            });
        })
        .def("set_on_close", [](ResilientDataBridge& self, py::function cb) {
            self.set_on_close([cb = std::move(cb)]() {
                py::gil_scoped_acquire gil;
                cb();
            });
        })
        .def("is_connected", &ResilientDataBridge::is_connected)
        .def("queue_length", &ResilientDataBridge::queue_length);
}
