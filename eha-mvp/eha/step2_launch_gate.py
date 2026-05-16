from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .phase2s_scoring import critical_risk_macro_f1
from .schemas import write_json


app = typer.Typer(add_completion=False, help="Build the EHA Step 2 launch go/no-go gate.")
console = Console()


STRUCTURAL_REPORT_DIRS = [
    "reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini",
    "reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini",
    "reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini",
    "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini",
]
V12_CRITICAL_RISK_SMOKE_RUN_DIR = "runs/phase2s-v12-critical-risk-contract-calibration-slice-heuristic"
V12_CRITICAL_RISK_SMOKE_REPORT_DIR = "reports-phase2s-v12-critical-risk-contract-calibration-slice-heuristic"


def read_json_or_empty(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def count_jsonl_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def mean_metric(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    values = [float(row.get(key, 0.0)) for row in rows]
    return sum(values) / len(values) if values else 0.0


def structural_schema_summaries(eha_mvp_dir: Path) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    base = eha_mvp_dir / "results"
    for report_dir_name in STRUCTURAL_REPORT_DIRS:
        rows = read_csv_rows(base / report_dir_name / "scored_predictions.csv")
        if not rows:
            continue
        metrics = {
            "report_dir": str(base / report_dir_name),
            "n": len(rows),
            "claim_accuracy": mean_metric(rows, "claim_accuracy"),
            "contaminated_citation_rate": mean_metric(rows, "contaminated_citation_rate"),
            "support_role_valid_rate": mean_metric(rows, "support_role_valid"),
            "critical_risk_macro_f1": critical_risk_macro_f1(rows),
        }
        metrics["passed"] = (
            metrics["claim_accuracy"] >= 0.85
            and metrics["critical_risk_macro_f1"] >= 0.60
            and metrics["contaminated_citation_rate"] <= 0.08
            and metrics["support_role_valid_rate"] >= 0.95
        )
        summaries.append(metrics)
    return summaries


def target_context(reports_dir: Path) -> Dict[str, Any]:
    context = read_json_or_empty(reports_dir / "eha_step2_target_context.json")
    return {
        "target_venue": context.get("target_venue", ""),
        "budget_confirmed": bool(context.get("budget_confirmed", False)),
    }


def support_role_guard_context(reports_dir: Path) -> Dict[str, Any]:
    context = read_json_or_empty(reports_dir / "eha_step2_phase2s_support_role_guard.json")
    return {
        "status": context.get("status", "missing"),
        "guard_ready": bool(context.get("guard_ready", False)),
        "recommended_run": context.get("recommended_run"),
        "ready_runs": context.get("ready_runs", []),
        "non_claims": context.get("non_claims", []),
    }


def critical_risk_audit_context(reports_dir: Path) -> Dict[str, Any]:
    context = read_json_or_empty(reports_dir / "eha_step2_phase2s_critical_risk_audit.json")
    return {
        "status": context.get("status", "missing"),
        "critical_risk_repair_ready": bool(context.get("critical_risk_repair_ready", False)),
        "best_run": context.get("best_run"),
        "ready_runs": context.get("ready_runs", []),
        "recommended_next_contract": context.get("recommended_next_contract", []),
    }


def v12_critical_risk_smoke_context(eha_mvp_dir: Path) -> Dict[str, Any]:
    results_dir = eha_mvp_dir / "results"
    run_dir = results_dir / V12_CRITICAL_RISK_SMOKE_RUN_DIR
    report_dir = results_dir / V12_CRITICAL_RISK_SMOKE_REPORT_DIR
    cost_report = read_json_or_empty(run_dir / "cost_report.json")
    gate = read_json_or_empty(report_dir / "phase2s_gate.json") or read_json_or_empty(run_dir / "phase2s_gate.json")
    support_rows = read_csv_rows(report_dir / "support_role_metrics.csv")
    support_role_valid_rates = [float(row.get("support_role_valid_rate", 0.0)) for row in support_rows]
    prediction_count = count_jsonl_rows(run_dir / "predictions.jsonl")
    report_completed = (report_dir / "summary.md").exists()
    status = "no_api_smoke_complete" if prediction_count > 0 and report_completed else "missing"
    return {
        "status": status,
        "prompt": "evidence_diagnostics_v12_critical_risk_contract",
        "backend": "heuristic",
        "model_label": "heuristic-sim",
        "model_evidence": False,
        "api_calls": 0,
        "predictions": prediction_count,
        "report_completed": report_completed,
        "cost_usd": float(cost_report.get("spent_usd", 0.0)),
        "gate_scope": gate.get("scope", ""),
        "gate_passed": bool(gate.get("passed", False)),
        "support_role_valid_rate_min": min(support_role_valid_rates) if support_role_valid_rates else 0.0,
        "run_dir": str(run_dir),
        "report_dir": str(report_dir),
        "non_claims": [
            "not a model run",
            "not model evidence",
            "not launch approval",
        ],
    }


def build_step2_launch_gate(reports_dir: Path, eha_mvp_dir: Path) -> Dict[str, Any]:
    step1 = read_json_or_empty(reports_dir / "eha_step1_readiness_check.json")
    surface = read_json_or_empty(reports_dir / "eha_step2_surface_cue_design_review_validation.json")
    external = read_json_or_empty(reports_dir / "eha_step2_external_validity_design.json")
    schema_runs = structural_schema_summaries(eha_mvp_dir)
    target = target_context(reports_dir)
    support_guard = support_role_guard_context(reports_dir)
    critical_risk_audit = critical_risk_audit_context(reports_dir)
    v12_smoke = v12_critical_risk_smoke_context(eha_mvp_dir)

    structural_passed = any(bool(run.get("passed")) for run in schema_runs)
    checks = {
        "step1_release_ready": step1.get("status") == "ready",
        "surface_cue_design_review_complete": surface.get("status") == "complete",
        "surface_cue_pilot_ready": surface.get("pilot_ready") is True,
        "external_validity_api_ready": external.get("api_ready") is True,
        "deterministic_support_role_validation_ready": support_guard["guard_ready"] or structural_passed,
        "structural_schema_repair_passed": structural_passed,
        "target_venue_and_budget_defined": bool(target["target_venue"]) and target["budget_confirmed"],
    }
    required_next_actions: List[str] = []
    if not checks["step1_release_ready"]:
        required_next_actions.append("complete Step 1 independent human audit")
    if not checks["surface_cue_pilot_ready"]:
        required_next_actions.append("complete 90-pair surface-cue human design review")
    if not checks["deterministic_support_role_validation_ready"] and not checks["structural_schema_repair_passed"]:
        required_next_actions.append("repair structural schema or add deterministic support-role validation before full C-only API spend")
    elif not checks["structural_schema_repair_passed"]:
        required_next_actions.append("repair critical-risk structural schema; support-role guard is ready but not a substitute")
    if not checks["external_validity_api_ready"]:
        required_next_actions.append("keep external-validity work design-only until prerequisite gates clear")
    if not checks["target_venue_and_budget_defined"]:
        required_next_actions.append("define target venue and budget before model calls")

    launch_ready = all(checks.values())
    return {
        "date": "2026-05-16",
        "status": "ready" if launch_ready else "blocked",
        "launch_ready": launch_ready,
        "decision": "Step 2 API pilot may proceed only with explicit human approval." if launch_ready else "do not launch a Step 2 API pilot or 500-1000 task expansion",
        "checks": checks,
        "required_next_actions": required_next_actions,
        "step1_readiness": {"status": step1.get("status", "missing"), "errors": step1.get("errors", [])},
        "surface_cue_design_review": {
            "status": surface.get("status", "missing"),
            "n_pairs": surface.get("n_pairs", 0),
            "n_reviewed": surface.get("n_reviewed", 0),
            "pilot_ready": surface.get("pilot_ready", False),
            "pilot_blockers": surface.get("pilot_blockers", []),
        },
        "external_validity": {
            "status": external.get("status", "missing"),
            "api_ready": external.get("api_ready", False),
            "recommended_first_slice": external.get("recommended_first_slice", ""),
        },
        "structural_schema_calibration": {
            "runs": schema_runs,
            "passed_runs": [run for run in schema_runs if run.get("passed")],
        },
        "support_role_guard": support_guard,
        "critical_risk_audit": critical_risk_audit,
        "v12_critical_risk_contract_smoke": v12_smoke,
        "target_context": target,
        "non_claims": [
            "not model evidence",
            "not a substitute for Step 1 human validation",
            "not permission to run a 500-1000 task expansion",
        ],
    }


def render_step2_launch_gate_markdown(gate: Mapping[str, Any]) -> str:
    lines = [
        "# EHA Step 2 Launch Gate",
        "",
        "Date: 2026-05-16",
        "",
        f"- Status: `{gate['status']}`",
        f"- Launch ready: `{str(gate['launch_ready']).lower()}`",
        f"- Decision: {gate['decision']}",
        "",
        "This is a no-API launch gate. It is not model evidence and does not substitute for independent human validation.",
        "",
        "## Checks",
        "",
    ]
    for key, value in gate["checks"].items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines.extend(["", "## Required Next Actions", ""])
    for action in gate["required_next_actions"]:
        lines.append(f"- {action}")
    lines.extend(["", "## Step 1 Readiness", ""])
    lines.append(f"- Status: `{gate['step1_readiness']['status']}`")
    for error in gate["step1_readiness"].get("errors", []):
        lines.append(f"- Error: {error}")
    lines.extend(["", "## Surface-Cue Design Review", ""])
    surface = gate["surface_cue_design_review"]
    lines.extend(
        [
            f"- Status: `{surface['status']}`",
            f"- Reviewed pairs: {surface['n_reviewed']} / {surface['n_pairs']}",
            f"- Pilot ready: `{str(surface['pilot_ready']).lower()}`",
        ]
    )
    for blocker in surface.get("pilot_blockers", []):
        lines.append(f"- Blocker: `{blocker}`")
    lines.extend(["", "## External Validity", ""])
    external = gate["external_validity"]
    lines.extend(
        [
            f"- Status: `{external['status']}`",
            f"- API ready: `{str(external['api_ready']).lower()}`",
            f"- Recommended first slice: `{external['recommended_first_slice']}`",
        ]
    )
    lines.extend(["", "## Structural Schema Calibration", ""])
    if not gate["structural_schema_calibration"]["runs"]:
        lines.append("- No calibration runs found.")
    else:
        lines.append("| run | n | claim | critical-risk F1 | contaminated support | support-role valid | passed |")
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")
        for run in gate["structural_schema_calibration"]["runs"]:
            run_name = Path(str(run["report_dir"])).name
            lines.append(
                f"| `{run_name}` | {run['n']} | {run['claim_accuracy']:.3f} | {run['critical_risk_macro_f1']:.3f} | {run['contaminated_citation_rate']:.3f} | {run['support_role_valid_rate']:.3f} | `{str(run['passed']).lower()}` |"
            )
    lines.extend(["", "## Deterministic Support-Role Guard", ""])
    support_guard = gate["support_role_guard"]
    lines.extend(
        [
            f"- Status: `{support_guard['status']}`",
            f"- Guard ready: `{str(support_guard['guard_ready']).lower()}`",
        ]
    )
    recommended = support_guard.get("recommended_run")
    if recommended:
        lines.append(f"- Recommended run: `{Path(str(recommended['report_dir'])).name}`")
        lines.append(f"- Allow rate: `{float(recommended['allow_rate']):.3f}`")
        lines.append(f"- Invalid accepted rate: `{float(recommended['invalid_accepted_rate']):.3f}`")
    lines.extend(["", "## Critical-Risk Repair Audit", ""])
    critical_audit = gate["critical_risk_audit"]
    lines.extend(
        [
            f"- Status: `{critical_audit['status']}`",
            f"- Repair ready: `{str(critical_audit['critical_risk_repair_ready']).lower()}`",
        ]
    )
    best_run = critical_audit.get("best_run")
    if best_run:
        lines.append(f"- Best current run: `{Path(str(best_run['report_dir'])).name}`")
        lines.append(f"- Critical-risk macro-F1: `{float(best_run['critical_risk_macro_f1']):.3f}`")
        lines.append(f"- Exact-row rate: `{float(best_run['critical_risk_exact_row_rate']):.3f}`")
    lines.extend(["", "## v12 Critical-Risk Contract Smoke", ""])
    v12_smoke = gate["v12_critical_risk_contract_smoke"]
    lines.extend(
        [
            f"- Status: `{v12_smoke['status']}`",
            f"- Prompt: `{v12_smoke['prompt']}`",
            f"- Backend: `{v12_smoke['backend']}`",
            f"- Predictions: `{v12_smoke['predictions']}`",
            f"- Report completed: `{str(v12_smoke['report_completed']).lower()}`",
            f"- Model evidence: `{str(v12_smoke['model_evidence']).lower()}`",
            f"- API calls: `{v12_smoke['api_calls']}`",
            f"- Gate scope: `{v12_smoke['gate_scope']}`",
            f"- Gate passed: `{str(v12_smoke['gate_passed']).lower()}`",
        ]
    )
    lines.extend(["", "## Non-Claims", ""])
    for claim in gate["non_claims"]:
        lines.append(f"- {claim}")
    lines.append("")
    return "\n".join(lines)


def write_step2_launch_gate(reports_dir: Path, eha_mvp_dir: Path, out_dir: Path) -> Dict[str, Any]:
    gate = build_step2_launch_gate(reports_dir, eha_mvp_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_step2_launch_gate.json", gate)
    (out_dir / "eha-step2-launch-gate-2026-05-16.md").write_text(
        render_step2_launch_gate_markdown(gate),
        encoding="utf-8",
    )
    return gate


@app.command()
def main(
    reports_dir: Path = typer.Option(Path("../reports"), help="Report directory containing Step 1/Step 2 gate inputs."),
    eha_mvp_dir: Path = typer.Option(Path("."), help="eha-mvp project directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Output report directory."),
) -> None:
    gate = write_step2_launch_gate(reports_dir, eha_mvp_dir, out_dir)
    console.print(f"[green]Wrote[/green] Step 2 launch gate: status={gate['status']}; launch_ready={gate['launch_ready']}")


if __name__ == "__main__":
    app()
