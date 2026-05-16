from __future__ import annotations

import csv
import json

from eha.phase2s_critical_risk_audit import (
    build_critical_risk_audit_report,
    render_critical_risk_audit_markdown,
    repair_focus,
    risk_errors,
    write_critical_risk_audit_report,
)
from eha.phase2s_scoring import CRITICAL_RISK_FLAGS


def scored_row(**overrides):
    row = {
        "task_id": "task_001",
        "episode_type": "clean_control",
        "model": "unit-test",
        "retriever": "bm25_top8",
        "strategy": "evidence_diagnostics_v11_role_disciplined_contract",
        "gold_claim_verdict": "supported",
        "predicted_claim_verdict": "supported",
        "gold_critical_risks": "",
        "predicted_critical_risks": "",
        "claim_accuracy": 1.0,
        "contaminated_citation_rate": 0.0,
    }
    for risk in CRITICAL_RISK_FLAGS:
        row[f"critical_{risk}_tp"] = 0.0
        row[f"critical_{risk}_fp"] = 0.0
        row[f"critical_{risk}_fn"] = 0.0
    row.update(overrides)
    return row


def risk_updates(*, missing=(), spurious=(), matched=()):
    updates = {}
    for risk in matched:
        updates[f"critical_{risk}_tp"] = 1.0
    for risk in missing:
        updates[f"critical_{risk}_fn"] = 1.0
    for risk in spurious:
        updates[f"critical_{risk}_fp"] = 1.0
    return updates


def write_scored_predictions(path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_critical_risk_audit_extracts_missing_and_spurious_labels() -> None:
    row = scored_row(**risk_updates(missing=("partial_support",), spurious=("false_consensus",), matched=("conflicting_evidence",)))

    errors = risk_errors(row)

    assert errors["missing"] == ["partial_support"]
    assert errors["spurious"] == ["false_consensus"]
    assert errors["matched"] == ["conflicting_evidence"]
    assert repair_focus(errors["missing"], errors["spurious"]).startswith("mark partial support")


def test_critical_risk_audit_report_blocks_negative_structural_slice(tmp_path) -> None:
    report_dir = tmp_path / "eha-mvp" / "results" / "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini"
    write_scored_predictions(
        report_dir / "scored_predictions.csv",
        [
            scored_row(task_id="task_001", **risk_updates(missing=("stale_evidence", "citation_laundering"))),
            scored_row(task_id="task_002", **risk_updates(missing=("false_consensus",), spurious=("no_primary_source",))),
            scored_row(task_id="task_003", **risk_updates(missing=("partial_support",), spurious=("conflicting_evidence",))),
            scored_row(task_id="task_004", **risk_updates(spurious=("citation_laundering", "false_consensus"))),
        ],
    )

    report = build_critical_risk_audit_report(tmp_path / "eha-mvp")
    markdown = render_critical_risk_audit_markdown(report)

    assert report["status"] == "blocked"
    assert report["critical_risk_repair_ready"] is False
    assert report["runs"][0]["repair_ready"] is False
    assert report["runs"][0]["critical_risk_exact_row_rate"] == 0.0
    assert report["runs"][0]["false_negative_counts"]["partial_support"] == 1
    assert "not a passing structural repair" in markdown


def test_critical_risk_audit_report_can_mark_slice_ready_when_contract_is_exact_enough(tmp_path) -> None:
    report_dir = tmp_path / "eha-mvp" / "results" / "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini"
    write_scored_predictions(
        report_dir / "scored_predictions.csv",
        [
            scored_row(task_id="task_001"),
            scored_row(task_id="task_002"),
            scored_row(task_id="task_003"),
            scored_row(task_id="task_004", **risk_updates(missing=("generated_lore",), spurious=("false_consensus",))),
        ],
    )

    report = build_critical_risk_audit_report(tmp_path / "eha-mvp")

    assert report["status"] == "ready"
    assert report["critical_risk_repair_ready"] is True
    assert report["runs"][0]["critical_risk_exact_row_rate"] == 0.75
    assert report["runs"][0]["critical_risk_macro_f1"] >= 0.60


def test_critical_risk_audit_writes_json_markdown_and_csv(tmp_path) -> None:
    report_dir = tmp_path / "eha-mvp" / "results" / "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini"
    write_scored_predictions(report_dir / "scored_predictions.csv", [scored_row(), scored_row(), scored_row(), scored_row()])

    report = write_critical_risk_audit_report(tmp_path / "eha-mvp", tmp_path / "reports")

    assert report["status"] == "ready"
    assert (tmp_path / "reports" / "phase2s_critical_risk_audit_rows.csv").exists()
    assert (tmp_path / "reports" / "phase2s_critical_risk_audit_runs.csv").exists()
    json_report = json.loads((tmp_path / "reports" / "eha_step2_phase2s_critical_risk_audit.json").read_text(encoding="utf-8"))
    assert json_report["critical_risk_repair_ready"] is True
    assert "audit_rows" not in json_report
    assert (tmp_path / "reports" / "eha-step2-phase2s-critical-risk-audit-2026-05-16.md").exists()
