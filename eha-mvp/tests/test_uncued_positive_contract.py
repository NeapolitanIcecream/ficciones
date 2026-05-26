from __future__ import annotations

from pathlib import Path

from eha.uncued_failure_decomposition import run_failure_decomposition
from eha.uncued_positive_contract import run_positive_contract
from eha.uncued_support_ambiguity import run_support_ambiguity


DATASET_DIR = Path("data/uncued-pilot-v1")
PILOT_RUN_DIR = Path("results/reports-eha-uncued-pilot-2026-05-22")
ROBUSTNESS_RUN_DIR = Path("results/reports-eha-uncued-robustness-2026-05-25")


def test_positive_contract_separates_composite_from_operational_escape(tmp_path: Path) -> None:
    run_failure_decomposition(
        pilot_run_dir=PILOT_RUN_DIR,
        robustness_run_dir=ROBUSTNESS_RUN_DIR,
        dataset_dir=DATASET_DIR,
        out_dir=tmp_path,
    )
    run_support_ambiguity(
        pilot_run_dir=PILOT_RUN_DIR,
        dataset_dir=DATASET_DIR,
        decomposition_dir=tmp_path,
        out_dir=tmp_path,
    )

    summary = run_positive_contract(
        pilot_run_dir=PILOT_RUN_DIR,
        dataset_dir=DATASET_DIR,
        support_ambiguity_dir=tmp_path,
        out_dir=tmp_path,
    )

    assert summary["row_count"] > 0
    assert 0.0 <= summary["mean_composite_contract"] <= 1.0
    assert 0.0 <= summary["mean_operational_escape"] <= 1.0
    assert (tmp_path / "positive_evidence_contract_rows.csv").exists()
    assert (tmp_path / "positive_evidence_contract_summary.csv").exists()
