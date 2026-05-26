from __future__ import annotations

from pathlib import Path

from eha.uncued_data_sanity import run_data_sanity


DATASET_DIR = Path("data/uncued-pilot-v1")
PILOT_RUN_DIR = Path("results/reports-eha-uncued-pilot-2026-05-22")


def test_data_sanity_reports_no_p0_for_current_uncued_dataset(tmp_path: Path) -> None:
    summary = run_data_sanity(dataset_dir=DATASET_DIR, pilot_run_dir=PILOT_RUN_DIR, out_dir=tmp_path)

    assert summary["p0_count"] == 0
    assert summary["decision"] in {"pass", "pass_with_qualifications"}
    assert (tmp_path / "data_sanity_audit_rows.csv").exists()
    assert (tmp_path / "data_sanity_audit_summary.json").exists()
