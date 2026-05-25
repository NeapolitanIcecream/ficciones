from __future__ import annotations

import csv
import json
from pathlib import Path

from eha.epistemic_resilience import epistemic_prediction_json_schema
from eha.uncued_robustness import (
    ROBUSTNESS_VARIANTS,
    build_robustness_prompt_payload,
    complete_paired_groups,
    compute_paired_delta_rows,
    latest_records_by_key,
    plan_robustness,
    robustness_schema,
    verify_robustness,
)


DATASET_DIR = Path("data/uncued-pilot-v1")


def test_robustness_schema_uses_current_phase1_interface() -> None:
    assert robustness_schema("current_phase1_interface") == epistemic_prediction_json_schema()


def test_plan_freezes_stratified_role_uncued_slice(tmp_path: Path) -> None:
    manifest = plan_robustness(
        DATASET_DIR,
        tmp_path,
        conditions=["generated_lore", "buried_primary"],
        tasks_per_condition=5,
        view="neutral_metadata_visible",
        seed=20260525,
    )

    selected = manifest["selected_tasks"]
    assert len(selected) == 10
    assert {row["condition"] for row in selected} == {"generated_lore", "buried_primary"}
    assert manifest["family_counts_by_condition"]["generated_lore"] == {
        "active_verification": 1,
        "evidence_selection": 2,
        "packet_judgment": 2,
    }
    assert manifest["old_cued_data_used"] is False
    assert (tmp_path / "selection_manifest.json").exists()
    assert (tmp_path / "perturbation_manifest.json").exists()


def test_perturbations_change_only_intended_prompt_fields(tmp_path: Path) -> None:
    manifest = plan_robustness(
        DATASET_DIR,
        tmp_path,
        conditions=["generated_lore"],
        tasks_per_condition=5,
        view="neutral_metadata_visible",
        seed=20260525,
    )
    task_id = manifest["selected_tasks"][0]["view_task_id"]
    baseline = build_robustness_prompt_payload(
        DATASET_DIR,
        task_id,
        "baseline_original",
        prompt_condition="standard_answer",
        seed=20260525,
    )
    ordered = build_robustness_prompt_payload(
        DATASET_DIR,
        task_id,
        "order_randomized",
        prompt_condition="standard_answer",
        seed=20260525,
    )
    source_masked = build_robustness_prompt_payload(
        DATASET_DIR,
        task_id,
        "source_type_masked",
        prompt_condition="standard_answer",
        seed=20260525,
    )
    paraphrase = build_robustness_prompt_payload(
        DATASET_DIR,
        task_id,
        "prompt_paraphrase",
        prompt_condition="standard_answer",
        seed=20260525,
    )
    citation_masked = build_robustness_prompt_payload(
        DATASET_DIR,
        task_id,
        "citation_masked",
        prompt_condition="standard_answer",
        seed=20260525,
    )

    assert set(ROBUSTNESS_VARIANTS) == {
        "baseline_original",
        "order_randomized",
        "source_type_masked",
        "prompt_paraphrase",
        "citation_masked",
    }
    assert sorted(doc["doc_id"] for doc in ordered["documents"]) == sorted(doc["doc_id"] for doc in baseline["documents"])
    assert [doc["doc_id"] for doc in ordered["documents"]] != [doc["doc_id"] for doc in baseline["documents"]]
    assert [
        {key: value for key, value in doc.items() if key != "source_type"}
        for doc in source_masked["documents"]
    ] == [
        {key: value for key, value in doc.items() if key != "source_type"}
        for doc in baseline["documents"]
    ]
    assert {doc["source_type"] for doc in source_masked["documents"]} == {"document"}
    assert paraphrase["documents"] == baseline["documents"]
    assert paraphrase["schema"] == baseline["schema"]
    assert paraphrase["policy"] != baseline["policy"]
    assert [doc["body"] for doc in citation_masked["documents"]] == [doc["body"] for doc in baseline["documents"]]
    assert all(doc["visible_citations"] == [] for doc in citation_masked["documents"])


def test_paired_delta_rows_use_complete_baseline_groups_only() -> None:
    rows = [
        {
            "task_id": "task_a",
            "model": "fixture-model",
            "variant": "baseline_original",
            "operational_epistemic_escape": 1.0,
            "belief_correctness": 1.0,
            "evidence_precision": 1.0,
            "polluted_support_rate": 0.0,
            "verification_action_score": "",
            "support_doc_ids": "d1",
            "predicted_verdict": "supported",
        },
        {
            "task_id": "task_a",
            "model": "fixture-model",
            "variant": "prompt_paraphrase",
            "operational_epistemic_escape": 0.0,
            "belief_correctness": 1.0,
            "evidence_precision": 0.0,
            "polluted_support_rate": 1.0,
            "verification_action_score": "",
            "support_doc_ids": "d2",
            "predicted_verdict": "supported",
        },
        {
            "task_id": "task_b",
            "model": "fixture-model",
            "variant": "prompt_paraphrase",
            "operational_epistemic_escape": 1.0,
            "belief_correctness": 1.0,
            "evidence_precision": 1.0,
            "polluted_support_rate": 0.0,
            "verification_action_score": "",
            "support_doc_ids": "d3",
            "predicted_verdict": "supported",
        },
    ]

    deltas = compute_paired_delta_rows(rows, variants=["baseline_original", "prompt_paraphrase"])

    assert len(deltas) == 1
    assert deltas[0]["task_id"] == "task_a"
    assert deltas[0]["delta_operational_escape"] == -1.0
    assert deltas[0]["pass_to_fail_operational"] == 1
    assert deltas[0]["support_set_changed"] == 1


def test_latest_records_by_key_prefers_retry_row() -> None:
    records = [
        {
            "variant": "baseline_original",
            "model": "fixture-model",
            "task_id": "uncued_048_visible",
            "prompt_condition": "standard_answer",
            "parse_success": False,
        },
        {
            "variant": "baseline_original",
            "model": "fixture-model",
            "task_id": "uncued_048_visible",
            "prompt_condition": "standard_answer",
            "parse_success": True,
        },
    ]

    latest = latest_records_by_key(records)

    assert len(latest) == 1
    assert latest[0]["parse_success"] is True


def test_verifier_rejects_missing_baseline_pair(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    reports_dir = tmp_path / "reports"
    run_dir.mkdir()
    reports_dir.mkdir()
    (run_dir / "selection_manifest.json").write_text(
        json.dumps(
            {
                "dataset_dir": "data/uncued-pilot-v1",
                "selected_tasks": [
                    {
                        "task_id": "uncued_048",
                        "view_task_id": "uncued_048_visible",
                        "condition": "generated_lore",
                        "family": "packet_judgment",
                    }
                ],
                "selected_view": "neutral_metadata_visible",
                "seed": 20260525,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "models": ["fixture-model"],
                "variants": ["baseline_original", "prompt_paraphrase"],
                "selected_view": "neutral_metadata_visible",
                "prompt_condition": "standard_answer",
                "planned_calls": 2,
                "actual_unique_records": 1,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "prompt_parity_audit.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (run_dir / "prompt_audit_summary.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (run_dir / "stored_hidden_label_audit.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (run_dir / "dry_run_cost_projection.json").write_text(json.dumps({"projected_cost_usd": 0.1, "planned_calls": 2}), encoding="utf-8")
    (run_dir / "cost_report.json").write_text(json.dumps({"spent_usd": 0.0, "hard_cap_usd": 5.0, "aborted": False}), encoding="utf-8")
    with (run_dir / "robustness_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_id", "model", "variant", "parse_success"])
        writer.writeheader()
        writer.writerow({"task_id": "uncued_048_visible", "model": "fixture-model", "variant": "prompt_paraphrase", "parse_success": "1"})

    result = verify_robustness(run_dir, reports_dir)

    assert result["decision"] == "fail"
    assert result["gates"]["baseline_anchor_complete"] is False
    assert complete_paired_groups(
        [{"task_id": "uncued_048_visible", "model": "fixture-model", "variant": "prompt_paraphrase"}],
        ["baseline_original", "prompt_paraphrase"],
    )["complete_count"] == 0
