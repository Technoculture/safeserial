#!/usr/bin/env python3
"""
Cross-link TestID strings to actual test names (GTest/pytest).
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = ROOT / "docs" / "traceability"
MATRIX_FILE = TRACE_DIR / "traceability_matrix.csv"
REPORT_MD = TRACE_DIR / "testid_links.md"
REPORT_JSON = TRACE_DIR / "testid_links.json"

GTEST_RE = re.compile(r"TEST(?:_F)?\s*\(\s*([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+)\s*\)")
PYTEST_RE = re.compile(r"^\s*def\s+(test_[A-Za-z0-9_]+)\s*\(")


def index_gtest_tests() -> dict[str, tuple[str, int]]:
    index: dict[str, tuple[str, int]] = {}
    for path in (ROOT / "tests").glob("*.cpp"):
        for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = GTEST_RE.search(line)
            if match:
                name = f"{match.group(1)}.{match.group(2)}"
                index.setdefault(name, (str(path.relative_to(ROOT)), idx))
    return index


def index_pytest_tests() -> dict[str, tuple[str, int]]:
    index: dict[str, tuple[str, int]] = {}
    for path in (ROOT / "bindings" / "python" / "tests").glob("*.py"):
        for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = PYTEST_RE.match(line)
            if match:
                name = match.group(1)
                index.setdefault(name, (str(path.relative_to(ROOT)), idx))
    return index


def main() -> int:
    if not MATRIX_FILE.exists():
        REPORT_MD.write_text(
            "# TestID Link Report\n\nTraceability matrix not found.\n",
            encoding="utf-8",
        )
        REPORT_JSON.write_text(
            json.dumps(
                {"error": "traceability_matrix.csv not found"}, indent=2
            ),
            encoding="utf-8",
        )
        return 1

    gtest_index = index_gtest_tests()
    pytest_index = index_pytest_tests()

    rows = []
    with MATRIX_FILE.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (v or "").strip() for k, v in row.items()})

    links = []
    unresolved = 0
    for row in rows:
        test_id = row.get("TestID", "")
        location = row.get("TestLocation", "")
        link = {
            "test_id": test_id,
            "matrix_location": location,
            "resolved": False,
            "resolved_location": "",
            "resolved_line": 0,
        }

        if test_id in gtest_index:
            resolved_path, line = gtest_index[test_id]
            link.update(
                {
                    "resolved": True,
                    "resolved_location": resolved_path,
                    "resolved_line": line,
                }
            )
        elif test_id in pytest_index:
            resolved_path, line = pytest_index[test_id]
            link.update(
                {
                    "resolved": True,
                    "resolved_location": resolved_path,
                    "resolved_line": line,
                }
            )

        if not link["resolved"]:
            unresolved += 1

        links.append(link)

    report = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "total": len(links),
        "resolved": len(links) - unresolved,
        "unresolved": unresolved,
        "links": links,
    }

    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# TestID Link Report",
        f"**Timestamp (UTC):** {report['timestamp_utc']}",
        "",
        "## Summary",
        f"- Total TestIDs: {report['total']}",
        f"- Resolved: {report['resolved']}",
        f"- Unresolved: {report['unresolved']}",
        "",
        "## Links",
        "| TestID | Matrix Location | Resolved Location | Line | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

    for link in links:
        status = "RESOLVED" if link["resolved"] else "UNRESOLVED"
        resolved_loc = link["resolved_location"] or "-"
        resolved_line = str(link["resolved_line"]) if link["resolved_line"] else "-"
        lines.append(
            f"| {link['test_id']} | {link['matrix_location'] or '-'} | "
            f"{resolved_loc} | {resolved_line} | {status} |"
        )

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
