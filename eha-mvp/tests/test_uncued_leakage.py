from __future__ import annotations

import json

from eha.uncued_generate import build_uncued_dataset, write_uncued_dataset
from eha.uncued_leakage import run_leakage_audit


def test_uncued_leakage_audit_writes_pass_signal_for_clean_micro_dataset(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    reports_dir = tmp_path / "reports"
    dataset = build_uncued_dataset(
        phase="micro",
        task_count=10,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=9417,
    )
    write_uncued_dataset(dataset_dir, dataset)

    result = run_leakage_audit(dataset_dir, reports_dir, ["neutral_metadata_visible", "neutral_metadata_hidden"])

    assert result["passed"] is True
    assert result["critical_hits"] == 0
    assert (reports_dir / "eha_uncued_leakage_micro.json").exists()
    assert (reports_dir / "uncued_leakage_micro_rows.csv").exists()


def test_uncued_leakage_audit_emits_failure_artifact_for_role_phrase(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    reports_dir = tmp_path / "reports"
    dataset = build_uncued_dataset(
        phase="micro",
        task_count=10,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=9417,
    )
    write_uncued_dataset(dataset_dir, dataset)
    doc_path = dataset_dir / "documents_neutral_metadata_visible.jsonl"
    rows = [json.loads(line) for line in doc_path.read_text(encoding="utf-8").splitlines()]
    rows[0]["title"] = "Primary record extract"
    doc_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")

    result = run_leakage_audit(dataset_dir, reports_dir, ["neutral_metadata_visible"])

    assert result["passed"] is False
    assert result["high_hits"] >= 1
    payload = json.loads((reports_dir / "eha_uncued_leakage_micro.json").read_text(encoding="utf-8"))
    assert payload["hits"][0]["category"] == "material_role_phrase"


def test_uncued_pilot_leakage_audit_writes_pilot_specific_reports(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    reports_dir = tmp_path / "reports"
    dataset = build_uncued_dataset(
        phase="pilot",
        task_count=60,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=20260522,
    )
    write_uncued_dataset(dataset_dir, dataset)

    result = run_leakage_audit(dataset_dir, reports_dir, ["neutral_metadata_visible", "neutral_metadata_hidden"])

    assert result["dataset_label"] == "pilot"
    assert result["passed"] is True
    assert (reports_dir / "eha_uncued_leakage_pilot.json").exists()
    assert (reports_dir / "uncued_leakage_pilot_rows.csv").exists()
    assert (reports_dir / "eha-uncued-leakage-pilot-2026-05-22.md").exists()
