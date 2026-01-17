import argparse
import datetime
import os
import shutil
import signal
import subprocess
import sys
import time

# Requirements
# C++ TEST BINARY: build/tests/reliability_test
# NODE BINDINGS: bindings/node/scripts/{sender,receiver}.js
# PYTHON BINDINGS: bindings/python/scripts/{sender,receiver}.py
# CHAOS MONKEY: scripts/chaos_monkey.py

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
TEST_BIN = os.path.join(BUILD_DIR, "tests", "reliability_test")
TRACEABILITY_DIR = os.path.join(
    PROJECT_ROOT, "docs", "traceability", "artifacts", "latest"
)
DEFAULT_REPORT = os.path.join(TRACEABILITY_DIR, "verify_reliability_report.md")

NODE_BINDING_ROOT = os.path.join(PROJECT_ROOT, "bindings", "node")
NODE_SENDER = os.path.join(NODE_BINDING_ROOT, "scripts", "sender.js")
NODE_RECEIVER = os.path.join(NODE_BINDING_ROOT, "scripts", "receiver.js")

PYTHON_BINDING_ROOT = os.path.join(PROJECT_ROOT, "bindings", "python")
PYTHON_SENDER = os.path.join(PYTHON_BINDING_ROOT, "scripts", "sender.py")
PYTHON_RECEIVER = os.path.join(PYTHON_BINDING_ROOT, "scripts", "receiver.py")

CHAOS_MONKEY = os.path.join(PROJECT_ROOT, "scripts", "chaos_monkey.py")
CHAOS_LOG = os.path.join(PROJECT_ROOT, "chaos_monkey.log")
COMBINED_LOG = os.path.join(PROJECT_ROOT, "combined.log")


def kill_process(proc):
    if proc:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass


def get_command(lang, role, port, item_count=None):
    """Return [cmd_list, cwd] for the given language and role."""
    if lang == "cpp":
        args = [TEST_BIN, port, role]
        if role == "sender":
            args.append(str(item_count))
        return args, PROJECT_ROOT
    elif lang == "node":
        script = NODE_SENDER if role == "sender" else NODE_RECEIVER
        args = ["node", script, port]
        if role == "sender":
            args.append(str(item_count))
        return args, PROJECT_ROOT
    elif lang == "python":
        script = PYTHON_SENDER if role == "sender" else PYTHON_RECEIVER
        # Must run via uv for environment
        uv = shutil.which("uv")
        if not uv:
            raise RuntimeError("'uv' not found")
        args = [uv, "run", "--project", PYTHON_BINDING_ROOT, "python", script, port]
        if role == "sender":
            args.append(str(item_count))
        return args, PROJECT_ROOT
    else:
        raise ValueError(f"Unknown language: {lang}")


def run_test_cycle(sender_lang, receiver_lang, drop_rate, corrupt_rate, item_count):
    print(
        f"--- Starting Test Cycle: Sender={sender_lang} -> Receiver={receiver_lang} "
        f"(Drop={drop_rate}, Corrupt={corrupt_rate}, Items={item_count}) ---"
    )

    # 1. Start Chaos Monkey
    print("[RUNNER] Launching Chaos Monkey...")
    chaos_proc = subprocess.Popen(
        [sys.executable, "-u", CHAOS_MONKEY, str(drop_rate), str(corrupt_rate)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,
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

    # 2. Start Receiver (Background)
    recv_cmd, recv_cwd = get_command(receiver_lang, "receiver", port_b)
    print(f"[RUNNER] Launching Receiver ({receiver_lang}) on {port_b}...")
    recv_proc = subprocess.Popen(
        recv_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
        cwd=recv_cwd,
    )

    # 3. Start Sender (Foreground)
    send_cmd, send_cwd = get_command(sender_lang, "sender", port_a, item_count)
    print(f"[RUNNER] Launching Sender ({sender_lang}) on {port_a}...")
    sender_proc = subprocess.Popen(
        send_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        preexec_fn=os.setsid,
        cwd=send_cwd,
    )

    sender_out = ""
    try:
        sender_out, _ = sender_proc.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        print("[RUNNER] Sender timed out!")
        kill_process(sender_proc)
        try:
            sender_out, _ = sender_proc.communicate(timeout=1)
        except:
            pass
        sender_proc.returncode = -1

    # 4. Stop everything
    kill_process(recv_proc)
    kill_process(chaos_proc)

    # Analyze
    recv_out, _ = recv_proc.communicate()

    sender_success = sender_proc.returncode == 0 and "TEST COMPLETE" in sender_out
    expected_msg = f"(Total: {item_count})"
    recv_success = expected_msg in recv_out

    full_log = f"### Sender Log\n```\n{sender_out}\n```\n### Receiver Log\n```\n{recv_out}\n```"

    if sender_success and recv_success:
        return True, full_log
    else:
        print(f"[RUNNER] Cycle Failed!")
        if "Cannot find module" in sender_out or "Cannot find module" in recv_out:
            print("[RUNNER] Hint: Check if Node.js bindings are built")
        if "ImportError" in sender_out or "ImportError" in recv_out:
            print("[RUNNER] Hint: Check Python environment")

        print(f"--- SENDER LOG ---\n{sender_out}\n------------------")
        print(f"--- RECEIVER LOG ---\n{recv_out}\n--------------------")
        return False, full_log


def generate_report(results, sender, receiver, report_file):
    report = f"""# Test Record - {sender.upper()}->{receiver.upper()} Reliability
**Project:** Data Bridge Serial Protocol
**Date:** {datetime.datetime.now().isoformat()}
**Tester:** Automated Runner
**Configuration:** Sender={sender}, Receiver={receiver}

## 1. Summary

| Test ID | Condition | Items | Result |
| :--- | :--- | :--- | :--- |
"""

    details = "\n## 2. Execution Logs\n"

    all_passed = True
    for i, res in enumerate(results):
        status = "PASS" if res["passed"] else "FAIL"
        if not res["passed"]:
            all_passed = False

        report += f"| T-{i+1:03d} | Drop={res['drop']*100}%, Corrupt={res['corrupt']*100}% | {res['items']} | **{status}** |\n"
        details += f"\n### T-{i+1:03d} Details\n{res['logs']}\n"

    report += f"""
## 3. Conclusion
**Overall Status:** {"PASS" if all_passed else "FAIL"}
"""
    report += details

    with open(report_file, "w") as f:
        f.write(report)

    print(f"[RUNNER] Report generated at {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run reliability verification tests for Data Bridge."
    )
    parser.add_argument(
        "--sender",
        choices=["cpp", "node", "python"],
        default="cpp",
        help="Sender implementation",
    )
    parser.add_argument(
        "--receiver",
        choices=["cpp", "node", "python"],
        default="cpp",
        help="Receiver implementation",
    )
    parser.add_argument(
        "--target",
        help="Legacy: set both sender and receiver to this value",
        choices=["cpp", "node", "python"],
    )
    parser.add_argument(
        "--report", default=DEFAULT_REPORT, help="Path to output report file"
    )

    args = parser.parse_args()

    sender = args.sender
    receiver = args.receiver

    if args.target:
        sender = args.target
        receiver = args.target

    print(f"Configuration: Sender={sender}, Receiver={receiver}")

    # Check binaries/scripts
    for role, lang in [("Sender", sender), ("Receiver", receiver)]:
        if lang == "cpp" and not os.path.exists(TEST_BIN):
            print(f"Error: C++ Binary not found at {TEST_BIN}. Run cmake/make first.")
            sys.exit(1)
        elif lang == "node":
            script = NODE_SENDER if role == "Sender" else NODE_RECEIVER
            if not os.path.exists(script):
                print(f"Error: Node.js {role} script not found at {script}")
                sys.exit(1)
        elif lang == "python":
            script = PYTHON_SENDER if role == "Sender" else PYTHON_RECEIVER
            if not os.path.exists(script):
                print(f"Error: Python {role} script not found at {script}")
                sys.exit(1)

    os.makedirs(os.path.dirname(args.report), exist_ok=True)

    test_scenarios = [
        {"drop": 0.0, "corrupt": 0.0, "items": 20},  # Baseline
        {"drop": 0.05, "corrupt": 0.01, "items": 20},  # Light Chaos
        {"drop": 0.10, "corrupt": 0.02, "items": 20},  # Heavy Chaos
    ]

    results = []

    try:
        for scenario in test_scenarios:
            passed, logs = run_test_cycle(
                sender,
                receiver,
                scenario["drop"],
                scenario["corrupt"],
                scenario["items"],
            )
            results.append(
                {
                    "drop": scenario["drop"],
                    "corrupt": scenario["corrupt"],
                    "items": scenario["items"],
                    "passed": passed,
                    "logs": logs,
                }
            )
            time.sleep(1)

        generate_report(results, sender, receiver, args.report)

        # Plot only supports standard report structure?
        # visualize_results.py likely parses the MD file.
        try:
            print(f"[RUNNER] Generating visual report from {args.report}...")
            subprocess.run(
                [sys.executable, "scripts/visualize_results.py", args.report],
                check=False,
            )
        except Exception as e:
            print(f"[RUNNER] Plot generation failed: {e}")

    except KeyboardInterrupt:
        print("\n[RUNNER] Interrupted.")


if __name__ == "__main__":
    main()
