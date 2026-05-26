from __future__ import annotations

from pathlib import Path

from eha.uncued_failure_decomposition import run_failure_decomposition


DATASET_DIR = Path("data/uncued-pilot-v1")
PILOT_RUN_DIR = Path("results/reports-eha-uncued-pilot-2026-05-22")
ROBUSTNESS_RUN_DIR = Path("results/reports-eha-uncued-robustness-2026-05-25")


def test_failure_decomposition_assigns_one_primary_component(tmp_path: Path) -> None:
    summary = run_failure_decomposition(
        pilot_run_dir=PILOT_RUN_DIR,
        robustness_run_dir=ROBUSTNESS_RUN_DIR,
        dataset_dir=DATASET_DIR,
        out_dir=tmp_path,
    )

    assert summary["operational_failure_count"] > 0
    assert summary["belief_correct_operational_failure_count"] > 0
    assert summary["one_primary_component_per_operational_failure"] is True
    assert (tmp_path / "failure_decomposition_rows.csv").exists()
    assert (tmp_path / "belief_correct_operational_failure_rows.csv").exists()
    assert (tmp_path / "source_file_hashes.json").exists()
