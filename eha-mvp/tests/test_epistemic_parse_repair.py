from __future__ import annotations

from pathlib import Path

from eha.epistemic_parse_repair import comparison_rows, repair_messages
from eha.epistemic_resilience import read_tasks


def test_repair_messages_include_schema_previous_response_and_evidence() -> None:
    task = read_tasks(Path("data/epistemic-resilience-v1/tasks.jsonl"))[0]

    messages = repair_messages(task, previous_response='{"claim_verdict":"supported"', parse_error="unterminated json")

    assert messages[0]["role"] == "developer"
    assert "JSON" in messages[0]["content"]
    payload = messages[1]["content"]
    assert "epistemic_resilience_v1_json_repair" in payload
    assert task.task_id not in payload
    assert task.question in payload
    assert "unterminated json" in payload
    assert "claim_verdict" in payload
    assert task.documents[0].doc_id in payload


def test_comparison_rows_report_original_vs_repaired_metric_deltas() -> None:
    original_rows = [
        {
            "task_id": "ert_000",
            "model": "openai/gpt-5-mini",
            "prompt_condition": "standard_answer",
            "family": "packet_judgment",
            "condition": "clean",
            "parse_success": 0.0,
            "epistemic_escape": 0.0,
            "belief_correctness": 0.0,
            "evidence_cleanliness": 1.0,
        }
    ]
    repaired_rows = [
        {
            "task_id": "ert_000",
            "model": "openai/gpt-5-mini",
            "prompt_condition": "standard_answer",
            "family": "packet_judgment",
            "condition": "clean",
            "parse_success": 1.0,
            "epistemic_escape": 1.0,
            "belief_correctness": 1.0,
            "evidence_cleanliness": 1.0,
        }
    ]

    rows = comparison_rows(
        original_rows,
        repaired_rows,
        {("ert_000", "openai/gpt-5-mini", "standard_answer")},
    )
    all_row = next(row for row in rows if row["scope"] == "all")

    assert all_row["repair_attempted_count"] == 1
    assert all_row["delta_parse_success"] == 1.0
    assert all_row["delta_epistemic_escape"] == 1.0
