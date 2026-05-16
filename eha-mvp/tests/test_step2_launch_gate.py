from __future__ import annotations

import csv
import json

from eha.step2_launch_gate import build_step2_launch_gate, render_step2_launch_gate_markdown, write_step2_launch_gate


def write_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_scored_predictions(path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def scored_row(**overrides):
    row = {
        "claim_accuracy": 1.0,
        "contaminated_citation_rate": 0.0,
        "support_role_valid": 1.0,
        "gold_critical_stale_evidence": 0.0,
        "pred_critical_stale_evidence": 0.0,
        "critical_stale_evidence_tp": 0.0,
        "critical_stale_evidence_fp": 0.0,
        "critical_stale_evidence_fn": 0.0,
        "gold_critical_conflicting_evidence": 0.0,
        "pred_critical_conflicting_evidence": 0.0,
        "critical_conflicting_evidence_tp": 0.0,
        "critical_conflicting_evidence_fp": 0.0,
        "critical_conflicting_evidence_fn": 0.0,
        "gold_critical_generated_lore": 0.0,
        "pred_critical_generated_lore": 0.0,
        "critical_generated_lore_tp": 0.0,
        "critical_generated_lore_fp": 0.0,
        "critical_generated_lore_fn": 0.0,
        "gold_critical_no_primary_source": 0.0,
        "pred_critical_no_primary_source": 0.0,
        "critical_no_primary_source_tp": 0.0,
        "critical_no_primary_source_fp": 0.0,
        "critical_no_primary_source_fn": 0.0,
        "gold_critical_citation_laundering": 0.0,
        "pred_critical_citation_laundering": 0.0,
        "critical_citation_laundering_tp": 0.0,
        "critical_citation_laundering_fp": 0.0,
        "critical_citation_laundering_fn": 0.0,
        "gold_critical_false_consensus": 0.0,
        "pred_critical_false_consensus": 0.0,
        "critical_false_consensus_tp": 0.0,
        "critical_false_consensus_fp": 0.0,
        "critical_false_consensus_fn": 0.0,
        "gold_critical_partial_support": 0.0,
        "pred_critical_partial_support": 0.0,
        "critical_partial_support_tp": 0.0,
        "critical_partial_support_fp": 0.0,
        "critical_partial_support_fn": 0.0,
    }
    row.update(overrides)
    return row


def seed_gate_inputs(base):
    reports = base / "reports"
    eha_mvp = base / "eha-mvp"
    write_json(reports / "eha_step1_readiness_check.json", {"status": "blocked", "errors": ["human audit missing"]})
    write_json(
        reports / "eha_step2_surface_cue_design_review_validation.json",
        {
            "status": "incomplete",
            "n_pairs": 90,
            "n_reviewed": 0,
            "pilot_ready": False,
            "pilot_blockers": ["missing_label_cells"],
        },
    )
    write_json(
        reports / "eha_step2_external_validity_design.json",
        {"status": "design_only", "api_ready": False, "recommended_first_slice": "semi_real_enterprise_wiki"},
    )
    report_dir = eha_mvp / "results" / "reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini"
    write_scored_predictions(
        report_dir / "scored_predictions.csv",
        [
            scored_row(gold_critical_stale_evidence=1.0, critical_stale_evidence_fn=1.0),
            scored_row(gold_critical_conflicting_evidence=1.0, critical_conflicting_evidence_fn=1.0, support_role_valid=0.0),
        ],
    )
    return reports, eha_mvp


def test_step2_launch_gate_blocks_when_required_human_reviews_are_incomplete(tmp_path) -> None:
    reports, eha_mvp = seed_gate_inputs(tmp_path)

    gate = build_step2_launch_gate(reports, eha_mvp)

    assert gate["status"] == "blocked"
    assert gate["launch_ready"] is False
    assert gate["checks"]["step1_release_ready"] is False
    assert gate["checks"]["surface_cue_pilot_ready"] is False
    assert gate["checks"]["external_validity_api_ready"] is False
    assert gate["checks"]["structural_schema_repair_passed"] is False
    assert "complete Step 1 independent human audit" in gate["required_next_actions"]
    assert "complete 90-pair surface-cue human design review" in gate["required_next_actions"]
    assert "do not launch a Step 2 API pilot" in gate["decision"]


def test_step2_launch_gate_markdown_preserves_claim_boundary(tmp_path) -> None:
    reports, eha_mvp = seed_gate_inputs(tmp_path)
    gate = build_step2_launch_gate(reports, eha_mvp)
    markdown = render_step2_launch_gate_markdown(gate)

    assert "# EHA Step 2 Launch Gate" in markdown
    assert "Status: `blocked`" in markdown
    assert "not model evidence" in markdown
    assert "do not launch a Step 2 API pilot" in markdown
    assert "human audit missing" in markdown
    assert "missing_label_cells" in markdown


def test_step2_launch_gate_writes_json_and_markdown(tmp_path) -> None:
    reports, eha_mvp = seed_gate_inputs(tmp_path)

    gate = write_step2_launch_gate(reports, eha_mvp, reports)

    assert gate["status"] == "blocked"
    assert (reports / "eha_step2_launch_gate.json").exists()
    report_path = reports / "eha-step2-launch-gate-2026-05-16.md"
    assert report_path.exists()
    assert report_path.read_text(encoding="utf-8") == render_step2_launch_gate_markdown(gate)


def test_step2_launch_gate_separates_support_role_guard_from_critical_risk_repair(tmp_path) -> None:
    reports, eha_mvp = seed_gate_inputs(tmp_path)
    write_json(
        reports / "eha_step2_phase2s_support_role_guard.json",
        {
            "status": "ready",
            "guard_ready": True,
            "recommended_run": {
                "report_dir": "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini",
                "allow_rate": 0.857,
                "invalid_accepted_rate": 0.0,
            },
            "ready_runs": [{"report_dir": "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini"}],
            "non_claims": ["not a repair for missing critical-risk labels"],
        },
    )

    gate = build_step2_launch_gate(reports, eha_mvp)
    markdown = render_step2_launch_gate_markdown(gate)

    assert gate["status"] == "blocked"
    assert gate["checks"]["deterministic_support_role_validation_ready"] is True
    assert gate["checks"]["structural_schema_repair_passed"] is False
    assert "repair critical-risk structural schema; support-role guard is ready but not a substitute" in gate["required_next_actions"]
    assert "repair structural schema or add deterministic support-role validation before full C-only API spend" not in gate["required_next_actions"]
    assert "## Deterministic Support-Role Guard" in markdown
    assert "Guard ready: `true`" in markdown


def test_step2_launch_gate_surfaces_critical_risk_audit_without_unblocking_launch(tmp_path) -> None:
    reports, eha_mvp = seed_gate_inputs(tmp_path)
    write_json(
        reports / "eha_step2_phase2s_critical_risk_audit.json",
        {
            "status": "blocked",
            "critical_risk_repair_ready": False,
            "best_run": {
                "report_dir": "reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini",
                "critical_risk_macro_f1": 0.404,
                "critical_risk_exact_row_rate": 0.286,
            },
            "recommended_next_contract": ["separate visible rejected pollution from verdict-critical risks"],
        },
    )

    gate = build_step2_launch_gate(reports, eha_mvp)
    markdown = render_step2_launch_gate_markdown(gate)

    assert gate["status"] == "blocked"
    assert gate["critical_risk_audit"]["status"] == "blocked"
    assert gate["critical_risk_audit"]["critical_risk_repair_ready"] is False
    assert "## Critical-Risk Repair Audit" in markdown
    assert "Critical-risk macro-F1: `0.404`" in markdown


def test_step2_launch_gate_records_v12_no_api_smoke_without_model_evidence(tmp_path) -> None:
    reports, eha_mvp = seed_gate_inputs(tmp_path)
    run_dir = eha_mvp / "results" / "runs" / "phase2s-v12-critical-risk-contract-calibration-slice-heuristic"
    report_dir = eha_mvp / "results" / "reports-phase2s-v12-critical-risk-contract-calibration-slice-heuristic"
    run_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "predictions.jsonl").write_text('{"row": 1}\n{"row": 2}\n', encoding="utf-8")
    write_json(run_dir / "cost_report.json", {"spent_usd": 0.0})
    write_json(report_dir / "phase2s_gate.json", {"scope": "partial", "passed": False})
    write_scored_predictions(
        report_dir / "support_role_metrics.csv",
        [{"support_role_valid_rate": 0.812}, {"support_role_valid_rate": 1.0}],
    )
    (report_dir / "summary.md").write_text("# Summary\n", encoding="utf-8")

    gate = build_step2_launch_gate(reports, eha_mvp)
    markdown = render_step2_launch_gate_markdown(gate)

    smoke = gate["v12_critical_risk_contract_smoke"]
    assert smoke["status"] == "no_api_smoke_complete"
    assert smoke["predictions"] == 2
    assert smoke["model_evidence"] is False
    assert smoke["api_calls"] == 0
    assert smoke["gate_scope"] == "partial"
    assert smoke["support_role_valid_rate_min"] == 0.812
    assert "## v12 Critical-Risk Contract Smoke" in markdown
    assert "Model evidence: `false`" in markdown
