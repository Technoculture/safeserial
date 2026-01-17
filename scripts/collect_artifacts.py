#!/usr/bin/env python3
"""
Collect deterministic verification artifacts for traceability.
"""

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "traceability" / "artifacts" / "latest"

ARTIFACTS = [
    ROOT / "docs" / "test_report.md",
    ROOT / "docs" / "test_timeline.png",
    ROOT / "docs" / "reliability_plot.png",
    ROOT / "docs" / "latency_histogram.png",
]


def safe_run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, cwd=ROOT, text=True).strip()
    except Exception:
        return ""


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in ARTIFACTS:
        if path.exists():
            shutil.copy2(path, OUT_DIR / path.name)

    manifest = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "git_commit": safe_run(["git", "rev-parse", "HEAD"]),
        "git_status": safe_run(["git", "status", "--porcelain"]),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "sanitizers": os.environ.get("DATA_BRIDGE_SANITIZERS", ""),
        "coverage": os.environ.get("DATA_BRIDGE_COVERAGE", ""),
        "fuzzing": os.environ.get("DATA_BRIDGE_ENABLE_FUZZING", ""),
    }

    with (OUT_DIR / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
