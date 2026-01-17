# Verification Artifacts

`latest/` is overwritten on each verification run and contains:
- `manifest.json` with run metadata.
- `test_report.md`, `test_timeline.png`, `reliability_plot.png`, `latency_histogram.png` when available.

Generate with:
```
python scripts/collect_artifacts.py
```
