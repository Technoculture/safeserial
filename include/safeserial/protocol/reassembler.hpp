#pragma once
#include <safeserial/protocol/packet.hpp>
#include <vector>
#include <iostream>

class Reassembler {
public:
    struct Result {
        bool complete;
        std::vector<uint8_t> payload;
    };

    Reassembler() : current_seq_id_(255), expected_frag_(0), active_(false) {}

    // Returns true if fragment was accepted (in sequence).
    // Caller should send ACK if this returns true.
    // If returns false, caller might ignore or send NACK/ACK-of-last-good.
    bool process_fragment(const Packet::Frame& frame) {
        if (!frame.valid) return false;
        
        uint8_t seq = frame.header.seq_id;
        uint16_t frag = frame.header.fragment_id;
        
        // New Sequence ?
        if (seq != current_seq_id_) {
             // Accept if it's a new message (logic can be more complex for strict strictness, 
             // e.g. only seq+1, but for now accept any new seq as new message start)
             if (frag == 0) {
                 reset(seq);
             } else {
                 return false; // Received middle of new message without start?
             }
        }

        if (frag != expected_frag_) {
            // Out of order fragment
            return false;
        }

        // Valid fragment
        buffer_.insert(buffer_.end(), frame.payload.begin(), frame.payload.end());
        expected_frag_++;
        return true;
    }

    bool is_complete(const Packet::Frame& last_frame) const {
         if (!active_) return false;
         return expected_frag_ == last_frame.header.total_frags;
    }

    bool is_duplicate(const Packet::Frame& frame) const {
         if (!active_) return false;
         uint8_t seq = frame.header.seq_id;
         uint16_t frag = frame.header.fragment_id;
         return (seq == current_seq_id_ && frag < expected_frag_);
    }

    std::vector<uint8_t> get_data() const {
        return buffer_;
    }

    size_t get_buffered_size() const {
        return buffer_.size();
    }

    uint8_t get_current_seq() const { return current_seq_id_; }

private:
    void reset(uint8_t seq) {
        buffer_.clear();
        current_seq_id_ = seq;
        expected_frag_ = 0;
        active_ = true;
    }

    uint8_t current_seq_id_;
    uint16_t expected_frag_;
    std::vector<uint8_t> buffer_;
    bool active_;
};
