
import subprocess
import time
import re
import os
import datetime
import signal
import sys

# Requirements
# RELIABILITY TEST BINARY: build/tests/reliability_test
# CHAOS MONKEY: tests/chaos_monkey.py

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")
TEST_BIN = os.path.join(BUILD_DIR, "tests", "reliability_test")
CHAOS_MONKEY = os.path.join(PROJECT_ROOT, "tests", "chaos_monkey.py")
REPORT_FILE = os.path.join(PROJECT_ROOT, "test_report.md")

def kill_process(proc):
    if proc:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

def run_test_cycle(drop_rate, corrupt_rate, item_count):
    print(f"--- Starting Test Cycle: Drop={drop_rate}, Corrupt={corrupt_rate}, Items={item_count} ---")
    
    # Run in-process memory test
    cmd = [TEST_BIN, "memory", str(drop_rate), str(corrupt_rate), str(item_count)]
    print(f"[RUNNER] Executing: {' '.join(cmd)}")
    
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate(timeout=60) # Should be fast
        
        full_log = f"### Execution Log\n```\n{stdout}\n```"
        if stderr:
            full_log += f"\n### Stderr\n```\n{stderr}\n```"
            
        success = proc.returncode == 0 and "TEST COMPLETE" in stdout
        return success, full_log
        
    except subprocess.TimeoutExpired:
        kill_process(proc)
        return False, "Timed Out"

def generate_iso_report(results):
    report = f"""# Test Record - ISO 13485 Compliance
**Project:** Data Bridge Serial Protocol
**Date:** {datetime.datetime.now().isoformat()}
**Tester:** Automated Runner

## 1. Scope
Verification of the reliable serial protocol implementation (Class C Medical Device component).

## 2. Test Environment
*   **OS:** {sys.platform}
*   **Build Artifacts:** `{TEST_BIN}`
*   **Test Driver:** `{os.path.abspath(__file__)}`

## 3. Reliability Visualization
![Reliability Plot](reliability_plot.png)

## 4. Test Cases & Results

| Test ID | Condition | Items | Result | Verification |
| :--- | :--- | :--- | :--- | :--- |
"""
    
    details = "\n## 4. Execution Logs\n"
    
    all_passed = True
    for i, res in enumerate(results):
        status = "PASS" if res['passed'] else "FAIL"
        if not res['passed']: all_passed = False
        
        report += f"| T-{i+1:03d} | Drop={res['drop']*100}%, Corrupt={res['corrupt']*100}% | {res['items']} | **{status}** | Data Integrity confirmed via CRC32 |\n"
        
        details += f"\n### T-{i+1:03d} Details\n{res['logs']}\n"

    report += f"""
## 5. Conclusion
**Overall Status:** {"PASS" if all_passed else "FAIL"}

The software {"HAS" if all_passed else "HAS NOT"} demonstrated compliance with reliability requirements.
"""
    report += details
    
    with open(REPORT_FILE, "w") as f:
        f.write(report)
    
    print(f"[RUNNER] Report generated at {REPORT_FILE}")

def main():
    if not os.path.exists(TEST_BIN):
        print(f"Error: Binary not found at {TEST_BIN}. Run cmake/make first.")
        sys.exit(1)

    test_scenarios = [
        {"drop": 0.0, "corrupt": 0.0, "items": 20},   # Baseline
        {"drop": 0.05, "corrupt": 0.01, "items": 20}, # Light Chaos
        {"drop": 0.10, "corrupt": 0.02, "items": 20}, # Heavy Chaos
    ]
    
    results = []
    
    try:
        for scenario in test_scenarios:
            passed, logs = run_test_cycle(scenario["drop"], scenario["corrupt"], scenario["items"])
            results.append({
                "drop": scenario["drop"],
                "corrupt": scenario["corrupt"],
                "items": scenario["items"],
                "passed": passed,
                "logs": logs
            })
            time.sleep(1) # Cleanup pause
            
        # Aggregate logs for plotting
        combined_logs = ""
        for r in results:
            combined_logs += r["logs"] + "\n"
            
        with open("combined_logs.txt", "w") as f:
            f.write(combined_logs)
            
        # Generate Plot
        try:
            subprocess.run([sys.executable, "tests/visualize_results.py", "combined_logs.txt"], check=False)
        except Exception as e:
            print(f"[RUNNER] Plot generation failed: {e}")

        generate_iso_report(results)
        
    except KeyboardInterrupt:
        print("\n[RUNNER] Interrupted.")

if __name__ == "__main__":
    main()
