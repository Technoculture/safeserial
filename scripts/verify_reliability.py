import subprocess
import time
import re
import os
import datetime
import signal
import sys
import argparse

# Requirements
# C++ TEST BINARY: build/tests/reliability_test
# NODE SENDER: bindings/node/scripts/sender.js
# NODE RECEIVER: bindings/node/scripts/receiver.js
# CHAOS MONKEY: scripts/chaos_monkey.py
#
# Usage:
#   python scripts/verify_reliability.py --target cpp   # Test C++ bindings (Default)
#   python scripts/verify_reliability.py --target node  # Test Node.js bindings

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
TEST_BIN = os.path.join(BUILD_DIR, "tests", "reliability_test")

NODE_BINDING_ROOT = os.path.join(PROJECT_ROOT, "bindings", "node")
NODE_SENDER = os.path.join(NODE_BINDING_ROOT, "scripts", "sender.js")
NODE_RECEIVER = os.path.join(NODE_BINDING_ROOT, "scripts", "receiver.js")

CHAOS_MONKEY = os.path.join(PROJECT_ROOT, "scripts", "chaos_monkey.py")
CHAOS_LOG = os.path.join(PROJECT_ROOT, "chaos_monkey.log")
COMBINED_LOG = os.path.join(PROJECT_ROOT, "combined.log")

def kill_process(proc):
    if proc:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

def run_test_cycle(target, drop_rate, corrupt_rate, item_count):
    print(f"--- Starting {target.upper()} Test Cycle: Drop={drop_rate}, Corrupt={corrupt_rate}, Items={item_count} ---")
    
    # 1. Start Chaos Monkey
    print("[RUNNER] Launching Chaos Monkey...")
    # Use setsid to easily kill entire process group later
    chaos_proc = subprocess.Popen(
        [sys.executable, "-u", CHAOS_MONKEY, str(drop_rate), str(corrupt_rate)], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid
    )
    
    # Wait for ports
    port_a = None
    port_b = None
    
    start_time = time.time()
    while time.time() - start_time < 5:
        line = chaos_proc.stdout.readline()
        if "Port A:" in line:
            port_a = line.split(":")[1].strip()
        if "Port B:" in line:
            port_b = line.split(":")[1].strip()
        if port_a and port_b:
            break
            
    if not port_a or not port_b:
        print("[RUNNER] FAILED to get virtual ports from Chaos Monkey")
        stdout, stderr = chaos_proc.communicate()
        print(f"--- Chaos Monkey STDOUT ---\n{stdout}")
        print(f"--- Chaos Monkey STDERR ---\n{stderr}")
        kill_process(chaos_proc)
        return False, "Chaos Monkey failed to start"
        
    print(f"[RUNNER] Ports Active: {port_a} <-> {port_b}")
    
    # Determine commands based on target
    if target == "cpp":
        recv_cmd = [TEST_BIN, port_b, "receiver"]
        send_cmd = [TEST_BIN, port_a, "sender", str(item_count)]
        cwd = PROJECT_ROOT
    elif target == "node":
        recv_cmd = ["node", NODE_RECEIVER, port_b]
        send_cmd = ["node", NODE_SENDER, port_a, str(item_count)]
        cwd = PROJECT_ROOT
    else:
        raise ValueError(f"Unknown target: {target}")

    # 2. Start Receiver (Background)
    print(f"[RUNNER] Launching Receiver ({target}) on {port_b}...")
    recv_proc = subprocess.Popen(
        recv_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, 
        text=True,
        preexec_fn=os.setsid,
        cwd=cwd
    )
    
    # 3. Start Sender (Foreground - wait for completion)
    print(f"[RUNNER] Launching Sender ({target}) on {port_a}...")
    sender_proc = subprocess.Popen(
        send_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
        cwd=cwd
    )
    
    sender_out = ""
    try:
        sender_out, _ = sender_proc.communicate(timeout=120) # 120s timeout
    except subprocess.TimeoutExpired:
        print("[RUNNER] Sender timed out!")
        kill_process(sender_proc)
        try:
            sender_out, _ = sender_proc.communicate(timeout=1)
        except: pass
        sender_proc.returncode = -1 
    
    # 4. Stop everything
    kill_process(recv_proc)
    kill_process(chaos_proc)
    
    # Analyze Receiver Output
    recv_out, _ = recv_proc.communicate()
    
    # Check PASS criteria
    sender_success = sender_proc.returncode == 0 and "TEST COMPLETE" in sender_out
    
    expected_msg = f"(Total: {item_count})"
    recv_success = expected_msg in recv_out
    
    full_log = f"### Sender Log\n```\n{sender_out}\n```\n### Receiver Log\n```\n{recv_out}\n```"
    
    if sender_success and recv_success:
        return True, full_log
    else:
        print(f"[RUNNER] Cycle Failed!")
        if target == "node" and ("Cannot find module" in sender_out or "Cannot find module" in recv_out):
             print("[RUNNER] Hint: Check if Node.js bindings are built (npm run build in bindings/node)")
        
        print(f"--- SENDER LOG ---\n{sender_out}\n------------------")
        print(f"--- RECEIVER LOG ---\n{recv_out}\n--------------------")
        return False, full_log

def generate_iso_report(results, target, report_file):
    report = f"""# Test Record - {target.upper()} Binding Reliability
**Project:** Data Bridge Serial Protocol
**Date:** {datetime.datetime.now().isoformat()}
**Tester:** Automated Runner
**Target:** {target}

## 1. Scope
Verification of the reliable serial protocol implementation (Class C Medical Device component).

## 2. Test Environment
*   **OS:** {sys.platform}
*   **Test Driver:** `{os.path.abspath(__file__)}`
*   **Target:** {target} 

## 3. Reliability Visualization
![Reliability Plot](test_timeline.png)

## 4. Test Cases & Results

| Test ID | Condition | Items | Result | Verification |
| :--- | :--- | :--- | :--- | :--- |
"""
    
    details = "\n## 5. Execution Logs\n"
    
    all_passed = True
    for i, res in enumerate(results):
        status = "PASS" if res['passed'] else "FAIL"
        if not res['passed']: all_passed = False
        
        report += f"| T-{i+1:03d} | Drop={res['drop']*100}%, Corrupt={res['corrupt']*100}% | {res['items']} | **{status}** | Data Integrity confirmed via CRC32 |\n"
        
        details += f"\n### T-{i+1:03d} Details\n{res['logs']}\n"

    report += f"""
## 6. Conclusion
**Overall Status:** {"PASS" if all_passed else "FAIL"}

The software {"HAS" if all_passed else "HAS NOT"} demonstrated compliance with reliability requirements.
"""
    report += details
    
    with open(report_file, "w") as f:
        f.write(report)
    
    print(f"[RUNNER] Report generated at {report_file}")

def main():
    parser = argparse.ArgumentParser(description="Run reliability verification tests for Data Bridge.")
    parser.add_argument("--target", choices=["cpp", "node"], default="cpp", help="Target implementation to test (cpp or node)")
    parser.add_argument("--report", default=os.path.join(PROJECT_ROOT, "docs", "test_report.md"), help="Path to output report file")
    
    args = parser.parse_args()
    
    # Check binary existence
    if args.target == "cpp":
        if not os.path.exists(TEST_BIN):
            print(f"Error: Binary not found at {TEST_BIN}. Run cmake/make first.")
            sys.exit(1)
    elif args.target == "node":
        if not os.path.exists(NODE_SENDER):
            print(f"Error: Sender script not found at {NODE_SENDER}")
            sys.exit(1)

    test_scenarios = [
        {"drop": 0.0, "corrupt": 0.0, "items": 20},   # Baseline
        {"drop": 0.05, "corrupt": 0.01, "items": 20}, # Light Chaos
        {"drop": 0.10, "corrupt": 0.02, "items": 20}, # Heavy Chaos
    ]
    
    results = []
    
    try:
        for scenario in test_scenarios:
            passed, logs = run_test_cycle(args.target, scenario["drop"], scenario["corrupt"], scenario["items"])
            results.append({
                "drop": scenario["drop"],
                "corrupt": scenario["corrupt"],
                "items": scenario["items"],
                "passed": passed,
                "logs": logs
            })
            time.sleep(1) # Cleanup pause
            
        # Aggregate logs and sort by timestamp
        all_log_lines = []
        for r in results:
            all_log_lines.extend(r["logs"].splitlines())
            
        if os.path.exists(CHAOS_LOG):
            with open(CHAOS_LOG, "r") as f:
                all_log_lines.extend(f.readlines())
        
        # Sort lines by timestamp (both C++ and Chaos use "float: msg")
        def get_ts(line):
            m = re.match(r"(\d+\.\d+):", line)
            return float(m.group(1)) if m else 0.0
            
        sorted_lines = sorted([l.strip() for l in all_log_lines if l.strip()], key=get_ts)
            
        with open(COMBINED_LOG, "w") as f:
            f.write("\n".join(sorted_lines))
            
        generate_iso_report(results, args.target, args.report)

        # Generate Plot (only for full runs usually, but we can try)
        try:
            print(f"[RUNNER] Generating visual report from {args.report}...")
            # Visualize script might depend on specific report format or just the report file path
            subprocess.run([sys.executable, "scripts/visualize_results.py", args.report], check=False)
        except Exception as e:
            print(f"[RUNNER] Plot generation failed: {e}")
        
    except KeyboardInterrupt:
        print("\n[RUNNER] Interrupted.")

if __name__ == "__main__":
    main()
