from __future__ import annotations

import csv
import json

from eha.phase2s_support_role_guard import (
    build_support_role_guard_report,
    render_support_role_guard_markdown,
    support_role_guard_decision,
    write_support_role_guard_report,
)


def scored_row(**overrides):
    row = {
        "task_id": "task_001",
        "module": "C",
        "dataset": "EHA-v2R-stress-pilot",
        "episode_type": "clean_control",
        "model": "unit-test",
        "retriever": "bm25_top8",
        "strategy": "evidence_diagnostics_v11_role_disciplined_contract",
        "prompt": "evidence_diagnostics_v11_role_disciplined_contract",
        "gold_claim_verdict": "supported",
        "predicted_claim_verdict": "supported",
        "supporting_evidence": "doc_001",
        "support_role_valid": 1.0,
        "support_role_clean_only": 1.0,
        "support_role_verdict_direct": 1.0,
        "support_role_has_contaminated_doc": 0.0,
        "support_role_has_unknown_doc": 0.0,
        "support_role_has_extraneous_clean_doc": 0.0,
        "support_role_nonempty_for_insufficient": 0.0,
    }
    row.update(overrides)
    return row


def write_scored_predictions(path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_support_role_guard_blocks_non_consumable_support_rows() -> None:
    decision = support_role_guard_decision(
        scored_row(
            support_role_valid=0.0,
            support_role_clean_only=0.0,
            support_role_verdict_direct=0.0,
            support_role_has_contaminated_doc=1.0,
            supporting_evidence="doc_polluted",
        )
    )

    assert decision["guard_decision"] == "block"
    assert decision["guard_invalid_accepted"] == 0.0
    assert "contaminated_support" in decision["guard_reasons"]
    assert "not_verdict_direct" in decision["guard_reasons"]


def test_support_role_guard_report_is_ready_when_invalid_rows_are_blocked(tmp_path) -> None:
    report_dir = tmp_path / "eha-mvp" / "results" / "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini"
    write_scored_predictions(
        report_dir / "scored_predictions.csv",
        [
            scored_row(task_id="task_001"),
            scored_row(task_id="task_002"),
            scored_row(task_id="task_003"),
            scored_row(
                task_id="task_004",
                support_role_valid=0.0,
                support_role_clean_only=1.0,
                support_role_verdict_direct=0.0,
                supporting_evidence="",
                gold_claim_verdict="refuted",
                predicted_claim_verdict="insufficient",
            ),
        ],
    )

    report = build_support_role_guard_report(tmp_path / "eha-mvp")

    assert report["status"] == "ready"
    assert report["guard_ready"] is True
    run = report["runs"][0]
    assert run["guard_ready"] is True
    assert run["allow_rate"] == 0.75
    assert run["invalid_accepted_rate"] == 0.0
    assert run["valid_blocked_rate"] == 0.0
    assert run["reason_counts"] == {"not_verdict_direct": 1}
    assert "not a repair for missing critical-risk labels" in render_support_role_guard_markdown(report)


def test_support_role_guard_report_blocks_when_scored_columns_are_missing(tmp_path) -> None:
    report_dir = tmp_path / "eha-mvp" / "results" / "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini"
    row = scored_row()
    row.pop("support_role_verdict_direct")
    write_scored_predictions(report_dir / "scored_predictions.csv", [row, row, row, row])

    report = build_support_role_guard_report(tmp_path / "eha-mvp")

    assert report["status"] == "blocked"
    assert report["runs"][0]["guard_ready"] is False
    assert report["runs"][0]["missing_fields"] == ["support_role_verdict_direct"]


def test_support_role_guard_writes_json_markdown_and_csv(tmp_path) -> None:
    report_dir = tmp_path / "eha-mvp" / "results" / "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini"
    write_scored_predictions(report_dir / "scored_predictions.csv", [scored_row(), scored_row(), scored_row(), scored_row()])

    report = write_support_role_guard_report(tmp_path / "eha-mvp", tmp_path / "reports")

    assert report["status"] == "ready"
    assert (tmp_path / "reports" / "phase2s_support_role_guard_rows.csv").exists()
    assert (tmp_path / "reports" / "phase2s_support_role_guard_runs.csv").exists()
    json_report = json.loads((tmp_path / "reports" / "eha_step2_phase2s_support_role_guard.json").read_text(encoding="utf-8"))
    assert json_report["guard_ready"] is True
    assert "guard_rows" not in json_report
    assert (tmp_path / "reports" / "eha-step2-phase2s-support-role-guard-2026-05-16.md").exists()
