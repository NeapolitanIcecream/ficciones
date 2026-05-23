from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from eha.epistemic_resilience import epistemic_prediction_json_schema
from eha.uncued_schema_ablation import (
    SCHEMA_VARIANTS,
    build_schema_prompt_payload,
    invocation_profiles_payload,
    latest_records_by_key,
    parse_schema_prediction,
    plan_schema_ablation,
    schema_json_schema,
    schema_profiles,
    score_schema_ablation_rows,
    verify_schema_ablation,
)


DATASET_DIR = Path("data/uncued-pilot-v1")


def test_schema_variants_are_closed_and_current_matches_phase1_contract() -> None:
    current = schema_json_schema("current")

    assert set(SCHEMA_VARIANTS) == {"current", "clarified", "minimal", "diagnostic_no_hygiene"}
    assert current == epistemic_prediction_json_schema()
    for variant in SCHEMA_VARIANTS:
        schema = schema_json_schema(variant)
        assert schema["additionalProperties"] is False
        assert schema["required"]


@pytest.mark.parametrize("variant", SCHEMA_VARIANTS)
def test_schema_parser_rejects_missing_required_fields(variant: str) -> None:
    payload = {"claim_verdict": "supported", "confidence": 0.5}

    with pytest.raises(ValueError, match="missing required"):
        parse_schema_prediction(variant, json.dumps(payload))


def test_plan_selects_stratified_role_uncued_task_slice(tmp_path: Path) -> None:
    manifest = plan_schema_ablation(
        DATASET_DIR,
        tmp_path,
        conditions=["generated_lore", "buried_primary"],
        tasks_per_condition=8,
        view="neutral_metadata_visible",
        seed=20260523,
    )

    selected = manifest["selected_tasks"]
    assert len(selected) == 16
    assert {row["condition"] for row in selected} == {"generated_lore", "buried_primary"}
    assert manifest["family_counts_by_condition"]["generated_lore"] == {
        "active_verification": 2,
        "evidence_selection": 3,
        "packet_judgment": 3,
    }
    assert (tmp_path / "selection_manifest.json").exists()
    assert "eha-mvp/data/uncued-pilot-v1" not in json.dumps(manifest)


def test_prompt_payload_keeps_evidence_fixed_and_hides_labels(tmp_path: Path) -> None:
    manifest = plan_schema_ablation(
        DATASET_DIR,
        tmp_path,
        conditions=["generated_lore", "buried_primary"],
        tasks_per_condition=8,
        view="neutral_metadata_visible",
        seed=20260523,
    )
    task_id = manifest["selected_tasks"][0]["view_task_id"]
    payloads = {
        variant: build_schema_prompt_payload(DATASET_DIR, task_id, variant, prompt_condition="standard_answer")
        for variant in SCHEMA_VARIANTS
    }
    reference = payloads["current"]

    for variant, payload in payloads.items():
        assert payload["question"] == reference["question"]
        assert payload["documents"] == reference["documents"]
        assert payload["base_policy"] == reference["base_policy"]
        assert payload["schema"] == schema_json_schema(variant)
        visible_text = json.dumps(payload, ensure_ascii=False)
        for forbidden in ("generated_lore", "buried_primary", "packet_judgment", "evidence_selection", "active_verification", "gold_verdict", "hidden_role"):
            assert forbidden not in visible_text


def test_score_marks_minimal_rejection_metrics_not_applicable(tmp_path: Path) -> None:
    rows = [
        {
            "task_id": "uncued_048_visible",
            "base_task_id": "uncued_048",
            "view": "neutral_metadata_visible",
            "condition": "generated_lore",
            "family": "packet_judgment",
            "model": "fixture-model",
            "schema_variant": "minimal",
            "prompt_condition": "standard_answer",
            "parse_success": True,
            "prediction": {
                "claim_verdict": "supported",
                "confidence": 0.8,
                "evidence_doc_ids": ["uncued_048_d02"],
                "selected_doc_ids": ["uncued_048_d02"],
                "evidence_notes": "Uses the apparent support.",
            },
        }
    ]

    scored = score_schema_ablation_rows(rows, DATASET_DIR)

    assert scored[0]["polluted_rejected"] == "not_applicable"
    assert scored[0]["polluted_diagnostic"] == "not_applicable"


def test_deepseek_invocation_profile_is_recorded_separately() -> None:
    profiles = schema_profiles(
        "deepseek-v4-pro",
        max_output_tokens=4096,
        timeout_s=240.0,
        cost_estimate_output_tokens=900,
    )

    payload = invocation_profiles_payload(
        profiles,
        schemas=["current", "clarified"],
        prompt="standard_answer",
        view="neutral_metadata_visible",
        max_attempts=2,
        parallel_models=1,
    )

    assert [row["model"] for row in payload["deepseek_profiles"]] == ["deepseek-v4-pro"]
    profile = payload["deepseek_profiles"][0]
    assert profile["invocation_profile"]["response_format"] == "json_object"
    assert profile["invocation_profile"]["max_completion_tokens_policy"] == "explicit:4096"
    assert profile["retry_profile"]["llm_repair"] == "disabled"
    assert profile["retry_profile"]["max_attempts"] == 2


def test_latest_records_by_key_prefers_retry_row() -> None:
    records = [
        {
            "schema_variant": "current",
            "model": "fixture-model",
            "task_id": "uncued_048_visible",
            "prompt_condition": "standard_answer",
            "parse_success": False,
        },
        {
            "schema_variant": "current",
            "model": "fixture-model",
            "task_id": "uncued_048_visible",
            "prompt_condition": "standard_answer",
            "parse_success": True,
        },
    ]

    latest = latest_records_by_key(records)

    assert len(latest) == 1
    assert latest[0]["parse_success"] is True


def test_verifier_rejects_missing_current_anchor(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    reports_dir = tmp_path / "reports"
    run_dir.mkdir()
    reports_dir.mkdir()
    (run_dir / "selection_manifest.json").write_text(
        json.dumps(
            {
                "dataset_dir": "data/uncued-pilot-v1",
                "selected_tasks": [{"task_id": "uncued_048", "view_task_id": "uncued_048_visible", "condition": "generated_lore", "family": "packet_judgment"}],
                "view": "neutral_metadata_visible",
                "seed": 20260523,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "models": ["fixture-model"],
                "schemas": ["clarified", "minimal"],
                "selected_view": "neutral_metadata_visible",
                "prompt_condition": "standard_answer",
                "planned_calls": 2,
                "actual_records": 2,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "prompt_audit_summary.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (run_dir / "stored_hidden_label_audit.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (run_dir / "cost_report.json").write_text(json.dumps({"spent_usd": 0.0, "hard_cap_usd": 5.0, "aborted": False}), encoding="utf-8")
    with (run_dir / "schema_ablation_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_id", "model", "schema_variant", "parse_success"])
        writer.writeheader()
        writer.writerow({"task_id": "uncued_048_visible", "model": "fixture-model", "schema_variant": "clarified", "parse_success": "1"})
        writer.writerow({"task_id": "uncued_048_visible", "model": "fixture-model", "schema_variant": "minimal", "parse_success": "1"})

    result = verify_schema_ablation(run_dir, reports_dir)

    assert result["decision"] == "fail"
    assert result["gates"]["current_anchor_complete"] is False


def test_verifier_rejects_latest_parse_failures(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    reports_dir = tmp_path / "reports"
    run_dir.mkdir()
    reports_dir.mkdir()
    (run_dir / "selection_manifest.json").write_text(
        json.dumps(
            {
                "dataset_dir": "data/uncued-pilot-v1",
                "selected_tasks": [{"task_id": "uncued_048", "view_task_id": "uncued_048_visible", "condition": "generated_lore", "family": "packet_judgment"}],
                "view": "neutral_metadata_visible",
                "seed": 20260523,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "run_manifest.json").write_text(
        json.dumps(
            {
                "models": ["fixture-model"],
                "schemas": list(SCHEMA_VARIANTS),
                "selected_view": "neutral_metadata_visible",
                "prompt_condition": "standard_answer",
                "planned_calls": 4,
                "actual_records": 4,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "prompt_audit_summary.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (run_dir / "stored_hidden_label_audit.json").write_text(json.dumps({"passed": True}), encoding="utf-8")
    (run_dir / "cost_report.json").write_text(json.dumps({"spent_usd": 0.0, "hard_cap_usd": 5.0, "aborted": False}), encoding="utf-8")
    with (run_dir / "schema_ablation_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["task_id", "model", "schema_variant", "parse_success"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for variant in SCHEMA_VARIANTS:
            writer.writerow({"task_id": "uncued_048_visible", "model": "fixture-model", "schema_variant": variant, "parse_success": "0" if variant == "current" else "1"})
    (reports_dir / "eha-uncued-schema-ablation-results-2026-05-23.md").write_text(
        "exploratory Phase 1.1; does not revise the Phase 1 main table; old cued model outputs; does not use old cued",
        encoding="utf-8",
    )

    result = verify_schema_ablation(run_dir, reports_dir)

    assert result["decision"] == "fail"
    assert result["gates"]["all_latest_rows_parse_success"] is False
