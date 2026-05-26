from __future__ import annotations

from pathlib import Path

from eha.uncued_failure_decomposition import run_failure_decomposition
from eha.uncued_support_ambiguity import run_support_ambiguity, status_from_score


DATASET_DIR = Path("data/uncued-pilot-v1")
PILOT_RUN_DIR = Path("results/reports-eha-uncued-pilot-2026-05-22")
ROBUSTNESS_RUN_DIR = Path("results/reports-eha-uncued-robustness-2026-05-25")


def test_status_from_score_distinguishes_partial_credit() -> None:
    assert status_from_score(1.0) == "pass"
    assert status_from_score(0.5) == "partial"
    assert status_from_score(0.0) == "fail"


def test_support_ambiguity_writes_candidate_sensitivity_and_examples(tmp_path: Path) -> None:
    run_failure_decomposition(
        pilot_run_dir=PILOT_RUN_DIR,
        robustness_run_dir=ROBUSTNESS_RUN_DIR,
        dataset_dir=DATASET_DIR,
        out_dir=tmp_path,
    )

    summary = run_support_ambiguity(
        pilot_run_dir=PILOT_RUN_DIR,
        dataset_dir=DATASET_DIR,
        decomposition_dir=tmp_path,
        out_dir=tmp_path,
    )

    assert summary["polluted_support_row_count"] > 0
    assert summary["target_candidate_count"] > 0
    assert summary["interpretation"] in {
        "gap_mostly_support_field_artifact",
        "gap_survives_ambiguity_rescoring",
        "no_target_strict_gap_rows",
    }
    assert (tmp_path / "support_ambiguity_candidate_rows.csv").exists()
    assert (tmp_path / "qualitative_failure_examples.md").exists()
