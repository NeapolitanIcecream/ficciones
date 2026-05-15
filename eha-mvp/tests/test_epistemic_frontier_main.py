from __future__ import annotations

import json
from pathlib import Path

from eha.epistemic_frontier_main import (
    BUDGET_AUDIT_MODEL_PROFILES,
    FRONTIER_MODEL_PROFILES,
    PROMPT_CONDITIONS,
    budget_setting_decisions,
    completed_job_keys,
    frontier_jobs,
    output_budget_diagnostics,
    write_frontier_reports,
)
from eha.epistemic_model_preflight import select_preflight_tasks
from eha.epistemic_resilience import EpistemicAction, EpistemicPrediction, EpistemicRunRecord, build_epistemic_tasks, epistemic_prediction_json_schema
from eha.schemas import model_to_dict, write_jsonl


def test_frontier_plan_has_expected_jobs_and_frozen_profiles() -> None:
    tasks = build_epistemic_tasks(Path("data/matrix-v1"))

    jobs = frontier_jobs(tasks, FRONTIER_MODEL_PROFILES, PROMPT_CONDITIONS)

    assert len(jobs) == 100 * 5 * 2
    profiles = {profile.model: profile for profile in FRONTIER_MODEL_PROFILES}
    assert profiles["gpt-5.4"].max_output_tokens == 4096
    assert profiles["claude-opus-4-7"].max_output_tokens == 4096
    assert profiles["gemini-3.1-pro-preview"].max_output_tokens == 4096
    assert profiles["deepseek-v4-pro"].max_output_tokens is None
    assert profiles["deepseek-v4-pro"].response_format == "json_object"
    assert profiles["kimi-k2.6"].max_output_tokens is None
    assert profiles["kimi-k2.6"].response_format == "json_schema"


def test_completed_job_keys_reads_existing_predictions_for_resume(tmp_path: Path) -> None:
    record = EpistemicRunRecord(
        task_id="ert_000",
        family="packet_judgment",
        condition="clean",
        model="gpt-5.4",
        prompt_condition="standard_answer",
        backend="api",
        prediction=EpistemicPrediction(claim_verdict="supported", confidence=0.8),
        parse_success=True,
    )
    path = tmp_path / "predictions.jsonl"
    write_jsonl(path, [model_to_dict(record)])

    assert completed_job_keys(path) == {("gpt-5.4", "ert_000", "standard_answer", "operational")}


def test_budget_audit_plan_covers_no_cap_and_cap_sensitivity_settings() -> None:
    tasks = select_preflight_tasks(build_epistemic_tasks(Path("data/matrix-v1")), sample_size=20)

    jobs = frontier_jobs(tasks, BUDGET_AUDIT_MODEL_PROFILES, ["epistemic_hygiene_instruction"])

    assert len(jobs) == 20 * 2 * 3
    settings = {(profile.model, profile.budget_setting, profile.max_output_tokens) for profile in BUDGET_AUDIT_MODEL_PROFILES}
    assert ("deepseek-v4-pro", "no_cap", None) in settings
    assert ("deepseek-v4-pro", "cap_8192", 8192) in settings
    assert ("deepseek-v4-pro", "cap_4096_diagnostic", 4096) in settings
    assert ("kimi-k2.6", "no_cap", None) in settings
    assert ("kimi-k2.6", "cap_8192", 8192) in settings
    assert ("kimi-k2.6", "cap_4096_diagnostic", 4096) in settings


def test_output_budget_diagnostics_records_visible_tokens_and_overlength() -> None:
    prediction = EpistemicPrediction(
        claim_verdict="supported",
        confidence=0.8,
        supporting_evidence=["doc"] * 6,
        rejected_evidence=[],
        selected_doc_ids=["doc"],
        actions=[EpistemicAction(action="open", target="doc", rationale="short")],
        evidence_environment_assessment="brief",
        answer=" ".join(["word"] * 121),
    )

    visible_tokens, field_lengths, overlength = output_budget_diagnostics(prediction, '{"answer":"x"}')

    assert visible_tokens > 0
    assert field_lengths["answer_words"] == 121
    assert field_lengths["supporting_evidence_count"] == 6
    assert overlength


def test_epistemic_schema_limits_visible_output_budget() -> None:
    schema = epistemic_prediction_json_schema()

    assert schema["properties"]["supporting_evidence"]["maxItems"] == 5
    assert schema["properties"]["rejected_evidence"]["maxItems"] == 5
    assert schema["properties"]["selected_doc_ids"]["maxItems"] == 3
    assert schema["properties"]["actions"]["maxItems"] == 2


def test_budget_setting_decision_prefers_8192_only_when_gate_passes() -> None:
    rows = [
        {"model": "deepseek-v4-pro", "budget_setting": "no_cap", "gate_pass": True},
        {"model": "deepseek-v4-pro", "budget_setting": "cap_8192", "gate_pass": False},
        {"model": "deepseek-v4-pro", "budget_setting": "cap_4096_diagnostic", "parse_success": 1.0, "empty_output_rate": 0.0},
        {"model": "kimi-k2.6", "budget_setting": "no_cap", "gate_pass": True},
        {"model": "kimi-k2.6", "budget_setting": "cap_8192", "gate_pass": True},
    ]

    decisions = {row["model"]: row for row in budget_setting_decisions(rows)}

    assert decisions["deepseek-v4-pro"]["selected_budget_setting"] == "no_cap"
    assert decisions["kimi-k2.6"]["selected_budget_setting"] == "cap_8192"


def test_frontier_reports_write_required_artifacts(tmp_path: Path) -> None:
    task = build_epistemic_tasks(Path("data/matrix-v1"))[0]
    record = EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model="gpt-5.4",
        prompt_condition="epistemic_hygiene_instruction",
        backend="api",
        prediction=EpistemicPrediction(
            claim_verdict=task.gold_verdict,
            confidence=0.8,
            supporting_evidence=task.primary_doc_ids[:1],
            selected_doc_ids=task.primary_doc_ids[:1],
        ),
        parse_success=True,
        invocation_profile={"temperature_policy": "omitted"},
    )

    write_frontier_reports(tmp_path, records=[record], tasks=[task], cost_report={"spent_usd": 0.0})

    required = [
        "summary.md",
        "frontier_main_metrics_by_model.csv",
        "frontier_main_metrics_by_family.csv",
        "frontier_main_metrics_by_condition.csv",
        "frontier_main_metrics_by_prompt.csv",
        "operational_vs_conditional_escape.csv",
        "failure_cases_frontier.jsonl",
        "cost_report.json",
    ]
    for name in required:
        assert (tmp_path / name).exists(), name
    header = (tmp_path / "frontier_main_metrics_by_model.csv").read_text(encoding="utf-8").splitlines()[0]
    assert "verification_action_score" in header
    manifest = json.loads((tmp_path / "report_manifest.json").read_text(encoding="utf-8"))
    assert manifest["record_count"] == 1
