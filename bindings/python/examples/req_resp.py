import sys
import time
import json
import safeserial

port = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyUSB1"
bridge = safeserial.DataBridge()

def on_data(data):
    try:
        msg_str = data.decode('utf-8')
        print(f"[RX RAW] {msg_str}")
        msg = json.loads(msg_str)
        
        if msg.get('type') == 'ping':
            print(f"Received PING (ID: {msg.get('id')}). Sending PONG...")
            resp = json.dumps({'type': 'pong', 'id': msg.get('id')})
            bridge.send(resp)
        elif msg.get('type') == 'pong':
            print(f"Received PONG (ID: {msg.get('id')}). RTT complete.")
            
    except Exception as e:
        print(f"Error parsing RX: {e}")

if bridge.open(port, 115200, on_data):
    print(f"Examples running on {port}")
    print("Sending PING every 2 seconds...")
    
    req_id = 0
    try:
        while True:
            req_id += 1
            req = json.dumps({'type': 'ping', 'id': req_id})
            print(f"[TX] Sending PING ID {req_id}")
            bridge.send(req)
            time.sleep(2)
            
    except KeyboardInterrupt:
        bridge.close()
else:
    print("Failed to open port")
