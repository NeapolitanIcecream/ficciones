from __future__ import annotations

import time
from pathlib import Path

import pytest

from eha.epistemic_model_preflight import (
    DEFAULT_MAIN_CANDIDATES,
    PreflightRecord,
    collect_artifact_records,
    cohort_decisions,
    extract_first_json_object,
    load_preflight_tasks,
    model_preflight_summary,
    model_visible_task,
    parse_prediction_with_diagnostics,
    portable_chat_messages,
    select_preflight_tasks,
    wall_clock_timeout,
)
from eha.epistemic_resilience import build_epistemic_tasks, build_messages, epistemic_prediction_json_schema


VALID_JSON = """
```json
{
  "claim_verdict": "insufficient",
  "confidence": 0.2,
  "supporting_evidence": [],
  "rejected_evidence": [],
  "selected_doc_ids": [],
  "actions": [],
  "evidence_environment_assessment": "No reliable primary evidence.",
  "answer": "Insufficient evidence."
}
```
"""


def test_universal_json_extractor_accepts_fenced_json_with_surrounding_text() -> None:
    assert extract_first_json_object(f"Here is the result:\n{VALID_JSON}\nDone.").startswith("{")

    parsed = parse_prediction_with_diagnostics(VALID_JSON)

    assert parsed.parse_success
    assert parsed.prediction is not None
    assert parsed.schema_missing is False
    assert parsed.json_extractor_used == "first_json_object"


def test_parse_diagnostics_marks_missing_required_schema_fields() -> None:
    missing_field_json = '{"claim_verdict":"supported","confidence":0.7}'

    parsed = parse_prediction_with_diagnostics(missing_field_json)

    assert not parsed.parse_success
    assert parsed.schema_missing
    assert "Field required" in parsed.parse_error


def test_portable_chat_messages_merge_developer_role_into_user_message() -> None:
    messages = [
        {"role": "developer", "content": "Return JSON only."},
        {"role": "user", "content": '{"task":"preflight"}'},
    ]

    adapted = portable_chat_messages(messages)

    assert [message["role"] for message in adapted] == ["user"]
    assert "Return JSON only." in adapted[0]["content"]
    assert '{"task":"preflight"}' in adapted[0]["content"]


def test_wall_clock_timeout_raises_for_hanging_call() -> None:
    with pytest.raises(TimeoutError, match="wall-clock timeout"):
        with wall_clock_timeout(0.05):
            time.sleep(0.2)


def test_collect_artifact_records_uses_later_dirs_to_override(tmp_path: Path) -> None:
    tasks = build_epistemic_tasks(Path("data/matrix-v1"))
    first = tmp_path / "first" / "artifacts" / "candidate"
    second = tmp_path / "second" / "artifacts" / "candidate"
    first.mkdir(parents=True)
    second.mkdir(parents=True)
    base_payload = {
        "model": "candidate",
        "task_id": "ert_000",
        "usage": {},
        "response_format_used": "json_schema",
        "schema_missing": False,
        "invocation_profile": {"max_completion_tokens_policy": "explicit:4096"},
    }
    (first / "ert_000.response.json").write_text(
        json_payload({**base_payload, "content": "", "parse_success": False, "parse_error": "empty output", "empty_output": True}),
        encoding="utf-8",
    )
    (second / "ert_000.response.json").write_text(
        json_payload({**base_payload, "content": VALID_JSON, "parse_success": True, "parse_error": "", "empty_output": False, "invocation_profile": {"max_completion_tokens_policy": "omitted"}}),
        encoding="utf-8",
    )

    records = collect_artifact_records([tmp_path / "first", tmp_path / "second"], tasks)

    assert len(records) == 1
    assert records[0].parse_success
    assert not records[0].empty_output
    assert records[0].invocation_profile["max_completion_tokens_policy"] == "omitted"


def json_payload(payload: dict) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2)


def test_preflight_task_sample_balances_conditions_and_families() -> None:
    tasks = build_epistemic_tasks(Path("data/matrix-v1"))

    selected = select_preflight_tasks(tasks, sample_size=20)

    assert len(selected) == 20
    assert {family: sum(1 for task in selected if task.family == family) for family in {task.family for task in selected}} == {
        "packet_judgment": 8,
        "evidence_selection": 8,
        "active_verification": 4,
    }
    assert {condition: sum(1 for task in selected if task.condition == condition) for condition in {task.condition for task in selected}} == {
        "clean": 4,
        "conflicting_evidence": 4,
        "false_consensus": 4,
        "buried_primary": 4,
        "generated_lore": 4,
    }


def test_uncued_task_dir_loads_view_specific_preflight_tasks_without_prompt_condition_leakage() -> None:
    tasks = load_preflight_tasks(Path("data/uncued-pilot-v1"))

    assert len(tasks) == 120
    assert {task.source_task_id.rsplit(":", 1)[1] for task in tasks} == {
        "neutral_metadata_visible",
        "neutral_metadata_hidden",
    }
    assert {task.condition for task in select_preflight_tasks(tasks, sample_size=20)} == {
        "clean",
        "conflicting_evidence",
        "false_consensus",
        "buried_primary",
        "generated_lore",
    }

    generated_task = next(task for task in tasks if task.condition == "generated_lore")
    messages = build_messages(model_visible_task(generated_task), "standard_answer", opaque_doc_ids=True, scrub_audit_labels=True)
    payload_text = messages[-1]["content"]

    assert '"condition": "role_uncued"' in payload_text
    assert "generated_lore" not in payload_text
    assert "false_consensus" not in payload_text
    assert "buried_primary" not in payload_text


def test_phase_11_defaults_exclude_kimi_and_use_uncued_openai_candidate() -> None:
    assert DEFAULT_MAIN_CANDIDATES == (
        "gpt-5.5",
        "claude-opus-4-7",
        "gemini-3.1-pro-preview",
        "deepseek-v4-pro",
    )
    assert "kimi-k2.6" not in DEFAULT_MAIN_CANDIDATES


def test_cohort_decisions_only_reports_models_that_were_preflighted() -> None:
    summaries = [
        {"model": "gpt-5.5", "structured_preflight_pass": True},
        {"model": "claude-opus-4-7", "structured_preflight_pass": True},
        {"model": "gemini-3.1-pro-preview", "structured_preflight_pass": True},
        {"model": "deepseek-v4-pro", "structured_preflight_pass": False},
    ]

    decisions = cohort_decisions(summaries)
    by_provider = {decision["provider"]: decision for decision in decisions}

    assert {decision["primary_candidate"] for decision in decisions} == {
        "gpt-5.5",
        "claude-opus-4-7",
        "gemini-3.1-pro-preview",
        "deepseek-v4-pro",
    }
    assert "Kimi" not in by_provider
    assert by_provider["OpenAI"]["selected_model"] == "gpt-5.5"
    assert by_provider["DeepSeek"]["status"] == "blocked"


def test_preflight_gate_requires_parse_empty_and_schema_thresholds() -> None:
    records = [
        PreflightRecord(
            task_id=f"ert_{index:03d}",
            family="packet_judgment",
            condition="clean",
            model="candidate",
            prompt_condition="epistemic_hygiene_instruction",
            parse_success=index != 0,
            empty_output=index == 1,
            schema_missing=index == 2,
            parse_error="" if index not in {0, 1, 2} else "preflight failure",
            raw_content_preview="" if index == 1 else "{}",
            response_format_used="json_schema",
            json_extractor_used="first_json_object",
            invocation_profile={"temperature_policy": "omitted", "max_completion_tokens_policy": "4096"},
        )
        for index in range(20)
    ]

    summary = model_preflight_summary(records, schema=epistemic_prediction_json_schema())[0]

    assert summary["parse_success_rate"] == 0.95
    assert summary["empty_output_count"] == 1
    assert summary["schema_missing_rate"] == 0.05
    assert summary["structured_preflight_pass"] is False
