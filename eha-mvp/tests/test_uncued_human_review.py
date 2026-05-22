from __future__ import annotations

import csv

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


def test_uncued_pilot_review_sample_covers_50_tasks_and_all_active_tasks(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    reports_dir = tmp_path / "reports"
    dataset = build_uncued_dataset(
        phase="pilot",
        task_count=60,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=20260522,
    )
    write_uncued_dataset(dataset_dir, dataset)

    worksheet = write_review_worksheet(
        dataset_dir,
        reports_dir,
        "50-tasks-200-docs",
        ["neutral_metadata_visible", "neutral_metadata_hidden"],
    )
    validation = validate_worksheet(worksheet, reports_dir, max_severe_leakage_rate=0.01)
    rows = list(csv.DictReader(worksheet.open()))
    reviewed_task_ids = {row["task_id"] for row in rows}
    active_task_ids = {task["task_id"] for task in dataset["latent_tasks"] if task["family"] == "active_verification"}

    assert worksheet.name == "uncued_human_leakage_review_pilot.csv"
    assert validation["passed"] is True
    assert validation["unique_tasks"] == 50
    assert validation["reviewed_rows"] == 400
    assert active_task_ids <= reviewed_task_ids
    assert (reports_dir / "eha_uncued_human_leakage_review_pilot_validation.json").exists()
    assert (reports_dir / "eha-uncued-human-leakage-review-pilot-2026-05-22.md").exists()
