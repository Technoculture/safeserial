#!/usr/bin/env python3
"""
Comprehensive Reliability Verification Matrix
Runs `chaos_visual.py` across multiple language pairs and failure scenarios.
"""

import subprocess
import sys
import os
import time
from datetime import datetime

# --- Configuration ---

LANGUAGES = ["python", "node"] # "cpp" requires build
SCENARIOS = [
    {"name": "Baseline", "args": []},
    {"name": "Light Chaos", "args": ["--drop", "0.05", "--corrupt", "0.01"]},
    {"name": "Heavy Chaos", "args": ["--drop", "0.1", "--corrupt", "0.05"]},
    {"name": "Burst", "args": ["--burst", "0.02"]},
    {"name": "Latency", "args": ["--latency", "0.02"]},
]

# --- Helper ---

def run_test(sender, receiver, scenario):
    print(f"\n>>> TESTING: {sender.upper()} -> {receiver.upper()} | {scenario['name']}")
    
    cmd = [
        "uv", "run", "--project", "bindings/python", "python", "scripts/chaos_visual.py",
        "--sender", sender,
        "--receiver", receiver,
        "--items", "50",
        "--baud", "0"
    ] + scenario["args"]
    
    start = time.time()
    try:
        # We capture output but print it if it fails
        # Using check=True to raise CalledProcessError on non-zero exit
        proc = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = time.time() - start
        
        if proc.returncode == 0:
            print(f"✅ PASS ({duration:.1f}s)")
            return True, duration, ""
        else:
            print(f"❌ FAIL ({duration:.1f}s)")
            return False, duration, proc.stdout + "\n" + proc.stderr
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, 0, str(e)

def main():
    results = []
    
    print("========================================")
    print("   DataBridge Reliability Matrix     ")
    print("========================================")
    
    # 1. Generate Matrix
    pairs = []
    # Intra-language
    for l in LANGUAGES:
        pairs.append((l, l))
    # Inter-language
    pairs.append(("node", "python"))
    pairs.append(("python", "node"))
    
    # 2. Run Tests
    for sender, receiver in pairs:
        for scenario in SCENARIOS:
            passed, duration, logs = run_test(sender, receiver, scenario)
            results.append({
                "sender": sender,
                "receiver": receiver,
                "scenario": scenario["name"],
                "passed": passed,
                "duration": duration,
                "logs": logs
            })
            
    # 3. Generate Report
    report_file = "docs/matrix_report.md"
    os.makedirs("docs", exist_ok=True)
    
    with open(report_file, "w") as f:
        f.write(f"# Reliability Matrix Report\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Sender | Receiver | Scenario | Result | Time |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        
        all_pass = True
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            if not r["passed"]: all_pass = False
            f.write(f"| {r['sender'].upper()} | {r['receiver'].upper()} | {r['scenario']} | {status} | {r['duration']:.1f}s |\n")
            
        f.write("\n\n## Failure Logs\n")
        for r in results:
            if not r["passed"]:
                f.write(f"### {r['sender']}->{r['receiver']} ({r['scenario']})\n")
                f.write("```\n")
                f.write(r["logs"][-2000:]) # Last 2000 chars
                f.write("\n```\n")
                
    print(f"\nReport written to {report_file}")
    
    if all_pass:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
