from __future__ import annotations

import json

from eha.uncued_baselines import run_baselines
from eha.uncued_generate import build_uncued_dataset, write_uncued_dataset
from eha.uncued_human_review import validate_worksheet, write_review_worksheet
from eha.uncued_leakage import run_leakage_audit
from eha.uncued_release import (
    freeze_micro_gate,
    package_uncued_phase1,
    refuses_cued_artifact_as_uncued_evidence,
    verify_uncued_phase1,
)


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


def write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def minimal_phase1_inputs(tmp_path):
    dataset_dir = tmp_path / "dataset"
    run_dir = tmp_path / "run"
    reports_dir = tmp_path / "reports"

    write_json(dataset_dir / "manifest.json", {"name": "fixture", "task_count": 1, "views": ["neutral_metadata_visible", "neutral_metadata_hidden"]})
    write_jsonl(dataset_dir / "tasks.jsonl", [{"task_id": "uncued_000", "condition": "clean", "family": "packet_judgment"}])
    visible_doc = {"doc_id": "d0", "task_id": "uncued_000", "title": "Neutral note", "body": "The claim is tested without role labels."}
    write_jsonl(dataset_dir / "documents_neutral_metadata_visible.jsonl", [visible_doc])
    write_jsonl(dataset_dir / "documents_neutral_metadata_hidden.jsonl", [{**visible_doc, "hidden_role": "primary"}])
    write_jsonl(dataset_dir / "gold_documents.jsonl", [{"doc_id": "d0", "task_id": "uncued_000", "supports_gold_verdict": True}])
    write_jsonl(dataset_dir / "dependency_edges.jsonl", [{"from": "d0", "to": "d0", "relation": "self"}])
    write_jsonl(dataset_dir / "action_gold.jsonl", [{"task_id": "uncued_000", "required_action": "read_docs", "target": "d0"}])

    write_jsonl(run_dir / "predictions.jsonl", [{"task_id": "uncued_000_visible", "model": "fixture-model", "parse_success": True}])
    write_json(run_dir / "run_manifest.json", {"expected_records": 1, "actual_records": 1})
    write_json(run_dir / "invocation_profiles.json", {"profiles": [{"model": "fixture-model"}], "deepseek_profiles": []})
    (run_dir / "run_summary_by_model.csv").write_text("model,parse_success_rate\nfixture-model,1.0\n", encoding="utf-8")
    write_json(run_dir / "prompt_audit_summary.json", {"passed": True, "hidden_field_hit_count": 0})
    write_json(run_dir / "stored_hidden_label_audit.json", {"passed": True, "prompt_hit_count": 0, "output_hit_count": 0})
    write_json(run_dir / "cost_report.json", {"spent_usd": 0.01})
    write_json(
        run_dir / "artifacts" / "fixture-model" / "operational" / "standard_answer" / "uncued_000_visible.prompt.json",
        {"messages": [{"role": "user", "content": "Use the neutral note."}]},
    )

    write_json(reports_dir / "eha_uncued_leakage_pilot.json", {"passed": True, "critical_hits": 0, "high_hits": 0, "hidden_label_hits": 0})
    write_json(reports_dir / "eha_uncued_baselines_pilot.json", {"passed": True, "baseline_count": 1})
    write_json(reports_dir / "eha_uncued_human_leakage_review_pilot_validation.json", {"passed": True, "critical_leaks": 0})
    write_json(
        reports_dir / "eha_uncued_pilot_run.json",
        {
            "expected_records": 1,
            "actual_records": 1,
            "prompt_audit": {"passed": True},
            "stored_hidden_label_audit": {"passed": True},
        },
    )
    write_json(reports_dir / "eha_uncued_pilot_results.json", {"phase13_acceptance_passed": True, "scored_rows": 1})
    write_json(reports_dir / "eha_uncued_scorer_audit.json", {"reviewed_rows": 40, "systematic_scorer_bug_found": False, "rescoring_required": False})
    write_json(reports_dir / "eha_uncued_schema_ablation_plan.json", {"status": "skipped_under_runbook_rule", "model_calls_made": 0})
    (reports_dir / "uncued_baseline_rows_pilot.csv").write_text("baseline,score\nsimple,0.0\n", encoding="utf-8")
    (reports_dir / "uncued_baseline_aggregate_pilot.csv").write_text("baseline,score\nsimple,0.0\n", encoding="utf-8")
    (reports_dir / "uncued_leakage_pilot_rows.csv").write_text("row,severity\n", encoding="utf-8")
    (reports_dir / "uncued_scorer_audit_rows.csv").write_text("row,agree\n0,true\n", encoding="utf-8")
    return dataset_dir, run_dir, reports_dir


def test_uncued_phase1_package_writes_required_layout_and_verifies(tmp_path) -> None:
    dataset_dir, run_dir, reports_dir = minimal_phase1_inputs(tmp_path)
    artifact_dir = tmp_path / "artifact_uncued_phase1"

    manifest = package_uncued_phase1(dataset_dir, run_dir, artifact_dir, reports_dir=reports_dir, repo_root=tmp_path)
    verification = verify_uncued_phase1(artifact_dir, reports_dir=reports_dir, out_dir=reports_dir)

    assert manifest["scientific_status"] == "role_uncued_phase1_pilot_artifact"
    assert (artifact_dir / "README.md").exists()
    assert (artifact_dir / "data" / "gold_labels.jsonl").exists()
    assert (artifact_dir / "prompts" / "prompt_manifest.json").exists()
    assert (artifact_dir / "schemas" / "epistemic_prediction_schema.json").exists()
    assert (artifact_dir / "scorer" / "scoring_contract.md").exists()
    assert (artifact_dir / "reproduce_minimal.sh").stat().st_mode & 0o111
    assert "data/documents_neutral_metadata_visible.jsonl" in manifest["hashes"]
    assert verification["decision"] == "pass"
    assert verification["gates"]["model_visible_files_exclude_hidden_labels"] is True
    assert (reports_dir / "eha_uncued_phase1_readiness.json").exists()


def test_uncued_phase1_verifier_rejects_hidden_label_in_visible_package(tmp_path) -> None:
    dataset_dir, run_dir, reports_dir = minimal_phase1_inputs(tmp_path)
    artifact_dir = tmp_path / "artifact_uncued_phase1"
    package_uncued_phase1(dataset_dir, run_dir, artifact_dir, reports_dir=reports_dir, repo_root=tmp_path)
    (artifact_dir / "data" / "documents_neutral_metadata_visible.jsonl").write_text(
        '{"doc_id":"d0","hidden_role":"primary"}\n',
        encoding="utf-8",
    )

    verification = verify_uncued_phase1(artifact_dir, reports_dir=reports_dir, out_dir=reports_dir)

    assert verification["decision"] == "fail"
    assert verification["gates"]["model_visible_files_exclude_hidden_labels"] is False
    assert verification["visible_hidden_label_hits"]
