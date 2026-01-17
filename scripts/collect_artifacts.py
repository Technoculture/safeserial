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
import hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "traceability" / "artifacts" / "latest"

ARTIFACTS = [
    ROOT / "docs" / "test_report.md",
    ROOT / "docs" / "test_timeline.png",
    ROOT / "docs" / "reliability_plot.png",
    ROOT / "docs" / "latency_histogram.png",
    ROOT / "docs" / "traceability" / "requirements.md",
    ROOT / "docs" / "traceability" / "risk_controls.md",
    ROOT / "docs" / "traceability" / "traceability_matrix.csv",
    ROOT / "docs" / "traceability" / "verification_plan.md",
    ROOT / "docs" / "traceability" / "soup_inventory.md",
    ROOT / "docs" / "traceability" / "iec62304_traceability_table.md",
    ROOT / "docs" / "traceability" / "traceability_report.md",
    ROOT / "docs" / "traceability" / "traceability_report.json",
]


def safe_run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, cwd=ROOT, text=True).strip()
    except Exception:
        return ""

def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    checksums = {}
    for path in ARTIFACTS:
        if path.exists():
            shutil.copy2(path, OUT_DIR / path.name)
            checksums[path.name] = sha256_file(path)

    manifest = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "git_commit": safe_run(["git", "rev-parse", "HEAD"]),
        "git_status": safe_run(["git", "status", "--porcelain"]),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "sanitizers": os.environ.get("DATA_BRIDGE_SANITIZERS", ""),
        "coverage": os.environ.get("DATA_BRIDGE_COVERAGE", ""),
        "fuzzing": os.environ.get("DATA_BRIDGE_ENABLE_FUZZING", ""),
        "checksums_sha256": checksums,
    }

    with (OUT_DIR / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
