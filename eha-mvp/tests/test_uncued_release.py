from __future__ import annotations

import json

from eha.uncued_baselines import run_baselines
from eha.uncued_generate import build_uncued_dataset, write_uncued_dataset
from eha.uncued_human_review import validate_worksheet, write_review_worksheet
from eha.uncued_leakage import run_leakage_audit
from eha.uncued_release import freeze_micro_gate, refuses_cued_artifact_as_uncued_evidence


def test_uncued_release_refuses_quarantined_cued_artifact(tmp_path) -> None:
    artifact_dir = tmp_path / "artifact"
    artifact_dir.mkdir()
    (artifact_dir / "manifest.json").write_text(
        json.dumps({"scientific_status": "quarantined_cued_internal"}),
        encoding="utf-8",
    )
    (artifact_dir / "CUED_INTERNAL_ONLY.md").write_text("internal only\n", encoding="utf-8")

    assert refuses_cued_artifact_as_uncued_evidence(artifact_dir) is True


def test_uncued_micro_gate_records_hashes_and_go_decision(tmp_path) -> None:
    dataset_dir = tmp_path / "dataset"
    reports_dir = tmp_path / "reports"
    dataset = build_uncued_dataset(
        phase="micro",
        task_count=10,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=9417,
    )
    write_uncued_dataset(dataset_dir, dataset)
    run_leakage_audit(dataset_dir, reports_dir, ["neutral_metadata_visible", "neutral_metadata_hidden"])
    run_baselines(dataset_dir, reports_dir, ["neutral_metadata_visible", "neutral_metadata_hidden"])
    worksheet = write_review_worksheet(dataset_dir, reports_dir, "all", ["neutral_metadata_visible", "neutral_metadata_hidden"])
    validate_worksheet(worksheet, reports_dir)

    gate = freeze_micro_gate(dataset_dir, reports_dir, reports_dir)

    assert gate["decision"] == "go"
    assert "micro_generation_manifest" in gate["hashes"]
    assert "leakage_report" in gate["hashes"]
    assert "baseline_report" in gate["hashes"]
    assert "human_review_validation" in gate["hashes"]
    assert (reports_dir / "eha_uncued_micro_gate.json").exists()

