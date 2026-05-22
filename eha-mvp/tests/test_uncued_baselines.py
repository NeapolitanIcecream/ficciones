from __future__ import annotations

from eha.uncued_baselines import UNCUED_BASELINES, run_baselines
from eha.uncued_generate import build_uncued_dataset, write_uncued_dataset


def test_uncued_shortcut_baselines_report_all_gate_metrics(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    reports_dir = tmp_path / "reports"
    dataset = build_uncued_dataset(
        phase="micro",
        task_count=10,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=9417,
    )
    write_uncued_dataset(dataset_dir, dataset)

    payload = run_baselines(dataset_dir, reports_dir, ["neutral_metadata_visible", "neutral_metadata_hidden"])

    assert payload["passed"] is True
    assert set(payload["baselines"]) == set(UNCUED_BASELINES)
    assert {row["baseline"] for row in payload["aggregate"]} == set(UNCUED_BASELINES)
    assert all(row["passed"] for row in payload["gate_results"])
    assert (reports_dir / "eha_uncued_baselines_micro.json").exists()
    assert (reports_dir / "uncued_baseline_rows_micro.csv").exists()


def test_uncued_pilot_baselines_write_pilot_specific_reports(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    reports_dir = tmp_path / "reports"
    dataset = build_uncued_dataset(
        phase="pilot",
        task_count=60,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=20260522,
    )
    write_uncued_dataset(dataset_dir, dataset)

    payload = run_baselines(dataset_dir, reports_dir, ["neutral_metadata_visible", "neutral_metadata_hidden"])

    assert payload["dataset_label"] == "pilot"
    assert payload["passed"] is True
    assert (reports_dir / "eha_uncued_baselines_pilot.json").exists()
    assert (reports_dir / "uncued_baseline_rows_pilot.csv").exists()
    assert (reports_dir / "eha-uncued-baselines-pilot-2026-05-22.md").exists()
