#!/usr/bin/env python3
"""
Validate traceability scaffolding consistency.

Checks:
- Requirement and risk control IDs exist and are referenced
- Traceability matrix references known IDs
- Test locations exist
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = ROOT / "docs" / "traceability"
REQ_FILE = TRACE_DIR / "requirements.md"
RISK_FILE = TRACE_DIR / "risk_controls.md"
MATRIX_FILE = TRACE_DIR / "traceability_matrix.csv"
REPORT_MD = TRACE_DIR / "traceability_report.md"
REPORT_JSON = TRACE_DIR / "traceability_report.json"


REQ_RE = re.compile(r"^(REQ-[A-Z0-9-]+):")
RC_RE = re.compile(r"^(RC-[A-Z0-9-]+):")
REQUIRED_COVERAGE = float(os.environ.get("DATA_BRIDGE_REQ_COVERAGE", "1.0"))


def load_ids(path: Path, pattern: re.Pattern[str]) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if match:
            ids.add(match.group(1))
    return ids


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    requirements = load_ids(REQ_FILE, REQ_RE)
    risk_controls = load_ids(RISK_FILE, RC_RE)

    if not requirements:
        errors.append("No requirements found in docs/traceability/requirements.md")
    if not risk_controls:
        errors.append("No risk controls found in docs/traceability/risk_controls.md")

    matrix_rows: list[dict[str, str]] = []
    if MATRIX_FILE.exists():
        with MATRIX_FILE.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                matrix_rows.append({k: (v or "").strip() for k, v in row.items()})
    else:
        errors.append("Missing docs/traceability/traceability_matrix.csv")

    if not matrix_rows:
        errors.append("Traceability matrix is empty")

    referenced_reqs: set[str] = set()
    referenced_controls: set[str] = set()

    for idx, row in enumerate(matrix_rows, start=1):
        req_id = row.get("RequirementID", "")
        rc_id = row.get("RiskControlID", "")
        test_location = row.get("TestLocation", "")

        if not req_id:
            errors.append(f"Row {idx}: RequirementID is empty")
        elif req_id not in requirements:
            errors.append(f"Row {idx}: RequirementID {req_id} not in requirements.md")
        else:
            referenced_reqs.add(req_id)

        if rc_id:
            if rc_id not in risk_controls:
                errors.append(f"Row {idx}: RiskControlID {rc_id} not in risk_controls.md")
            else:
                referenced_controls.add(rc_id)
        else:
            warnings.append(f"Row {idx}: RiskControlID is empty")

        if test_location:
            test_path = ROOT / test_location
            if not test_path.exists():
                errors.append(f"Row {idx}: TestLocation not found: {test_location}")
        else:
            warnings.append(f"Row {idx}: TestLocation is empty")

    missing_reqs = sorted(requirements - referenced_reqs)
    if missing_reqs:
        errors.append(
            "Requirements missing from matrix: " + ", ".join(missing_reqs)
        )

    coverage_ratio = (
        len(referenced_reqs) / len(requirements) if requirements else 0.0
    )
    if coverage_ratio < REQUIRED_COVERAGE:
        errors.append(
            f"Requirements coverage {coverage_ratio:.2%} below threshold "
            f"{REQUIRED_COVERAGE:.2%}"
        )

    report = {
        "timestamp_utc": datetime.utcnow().isoformat() + "Z",
        "requirements_total": len(requirements),
        "risk_controls_total": len(risk_controls),
        "matrix_rows": len(matrix_rows),
        "requirements_covered": len(referenced_reqs),
        "coverage_ratio": coverage_ratio,
        "coverage_threshold": REQUIRED_COVERAGE,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_MD.write_text(
        "\n".join(
            [
                "# Traceability Validation Report",
                f"**Timestamp (UTC):** {report['timestamp_utc']}",
                "",
                "## Summary",
                f"- Requirements: {report['requirements_total']}",
                f"- Risk controls: {report['risk_controls_total']}",
                f"- Matrix rows: {report['matrix_rows']}",
                f"- Requirements covered: {report['requirements_covered']}",
                f"- Coverage ratio: {coverage_ratio:.2%}",
                f"- Coverage threshold: {REQUIRED_COVERAGE:.2%}",
                "",
                "## Errors",
                "\n".join(f"- {err}" for err in errors) if errors else "- None",
                "",
                "## Warnings",
                "\n".join(f"- {warn}" for warn in warnings) if warnings else "- None",
                "",
            ]
        ),
        encoding="utf-8",
    )

    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if errors:
        print("Traceability validation failed.")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Traceability validation passed.")
    if warnings:
        for warn in warnings:
            print(f"- {warn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
