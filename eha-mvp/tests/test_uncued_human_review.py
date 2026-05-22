from __future__ import annotations

from eha.uncued_generate import build_uncued_dataset, write_uncued_dataset
from eha.uncued_human_review import validate_worksheet, write_review_worksheet


def test_uncued_human_review_validation_accepts_complete_surface_review(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    reports_dir = tmp_path / "reports"
    dataset = build_uncued_dataset(
        phase="micro",
        task_count=10,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=9417,
    )
    write_uncued_dataset(dataset_dir, dataset)

    worksheet = write_review_worksheet(dataset_dir, reports_dir, "all", ["neutral_metadata_visible", "neutral_metadata_hidden"])
    validation = validate_worksheet(worksheet, reports_dir)

    assert validation["passed"] is True
    assert validation["reviewed_rows"] == 80
    assert validation["critical_leaks"] == 0
    assert validation["independent_human_review"] is False
    assert (reports_dir / "eha_uncued_human_leakage_review_validation.json").exists()

