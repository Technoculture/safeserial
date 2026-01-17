# Traceability Scaffold

This folder provides scaffolding for requirements, risk controls, and verification traceability.

Contents:
- `requirements.md`: functional and safety-related requirements with stable IDs.
- `risk_controls.md`: risk control measures and the evidence expected.
- `traceability_matrix.csv`: mapping of requirements to tests and evidence.
- `verification_plan.md`: outline of verification activities and artifacts.
- `soup_inventory.md`: SOUP inventory template.
- `iec62304_traceability_table.md`: IEC 62304 traceability template.
- `artifacts/`: deterministic outputs from verification runs (see `artifacts/README.md`).

Validation:
- `scripts/validate_traceability.py` checks ID consistency, missing coverage, and test file existence.
- `traceability_report.md` and `traceability_report.json` summarize validation results.
- `scripts/link_test_ids.py` links TestIDs to concrete test definitions (GTest/pytest).
- `testid_links.md` and `testid_links.json` capture linkage results.
