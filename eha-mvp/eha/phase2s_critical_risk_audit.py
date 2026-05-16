from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .phase2s_scoring import CRITICAL_RISK_FLAGS, critical_risk_macro_f1
from .report import markdown_table, write_csv
from .schemas import write_json


app = typer.Typer(add_completion=False, help="Audit Phase 2S critical-risk schema failures without API calls.")
console = Console()

STRUCTURAL_REPORT_DIRS = [
    "reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini",
    "reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini",
    "reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini",
    "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini",
]
MIN_CRITICAL_RISK_MACRO_F1 = 0.60
MIN_EXACT_ROW_RATE = 0.60
MAX_CONTAMINATED_SUPPORT = 0.08
MIN_CLAIM_ACCURACY = 0.85

REQUIRED_FIELDS = [
    "task_id",
    "episode_type",
    "model",
    "retriever",
    "strategy",
    "gold_claim_verdict",
    "predicted_claim_verdict",
    "gold_critical_risks",
    "predicted_critical_risks",
    "claim_accuracy",
    "contaminated_citation_rate",
]

RISK_REPAIR_HINTS = {
    "stale_evidence": "define stale as verdict-critical only when the accepted support is superseded or no current primary support is used",
    "conflicting_evidence": "reserve conflict for clean contradiction or direct refutation, not every rejected pollutant",
    "generated_lore": "separate generated/wiki-like visible pollutants from no-primary abstention and verdict-critical generated lore",
    "no_primary_source": "use no-primary only when no current primary, audit, signed record, export, or direct source is visible",
    "citation_laundering": "require a visible source-chain problem, not same-root repetition or generic reposting",
    "false_consensus": "require repeated same-root apparent support that could dominate the verdict, not ordinary visible repetition",
    "partial_support": "mark partial support when clean evidence supports a weaker scope, quantifier, or causal claim",
}


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def as_float(row: Mapping[str, Any], key: str) -> float:
    value = row.get(key, "")
    if value in {"", None}:
        return 0.0
    return float(value)


def risk_errors(row: Mapping[str, Any]) -> Dict[str, List[str]]:
    missing = [risk for risk in CRITICAL_RISK_FLAGS if as_float(row, f"critical_{risk}_fn") > 0.0]
    spurious = [risk for risk in CRITICAL_RISK_FLAGS if as_float(row, f"critical_{risk}_fp") > 0.0]
    matched = [risk for risk in CRITICAL_RISK_FLAGS if as_float(row, f"critical_{risk}_tp") > 0.0]
    return {"missing": missing, "spurious": spurious, "matched": matched}


def row_error_type(missing: Sequence[str], spurious: Sequence[str]) -> str:
    if not missing and not spurious:
        return "exact"
    if missing and spurious:
        return "mixed_error"
    if missing:
        return "false_negative_only"
    return "false_positive_only"


def repair_focus(missing: Sequence[str], spurious: Sequence[str]) -> str:
    risks = list(missing) + list(spurious)
    if not risks:
        return "preserve_current_boundary"
    for priority in ("partial_support", "citation_laundering", "false_consensus", "conflicting_evidence", "stale_evidence", "generated_lore", "no_primary_source"):
        if priority in risks:
            return RISK_REPAIR_HINTS[priority]
    return RISK_REPAIR_HINTS[risks[0]]


def annotate_critical_risk_rows(rows: Sequence[Mapping[str, Any]], report_dir_name: str) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for row in rows:
        errors = risk_errors(row)
        missing = errors["missing"]
        spurious = errors["spurious"]
        error_type = row_error_type(missing, spurious)
        output.append(
            {
                "report_dir": report_dir_name,
                "task_id": row.get("task_id", ""),
                "episode_type": row.get("episode_type", ""),
                "model": row.get("model", ""),
                "retriever": row.get("retriever", ""),
                "strategy": row.get("strategy", ""),
                "gold_claim_verdict": row.get("gold_claim_verdict", ""),
                "predicted_claim_verdict": row.get("predicted_claim_verdict", ""),
                "claim_accuracy": as_float(row, "claim_accuracy"),
                "contaminated_citation_rate": as_float(row, "contaminated_citation_rate"),
                "gold_critical_risks": row.get("gold_critical_risks", ""),
                "predicted_critical_risks": row.get("predicted_critical_risks", ""),
                "matched_critical_risks": ",".join(errors["matched"]),
                "missing_critical_risks": ",".join(missing),
                "spurious_critical_risks": ",".join(spurious),
                "critical_risk_error_type": error_type,
                "critical_risk_exact": 1.0 if error_type == "exact" else 0.0,
                "critical_risk_has_false_negative": 1.0 if missing else 0.0,
                "critical_risk_has_false_positive": 1.0 if spurious else 0.0,
                "critical_risk_mixed_error": 1.0 if error_type == "mixed_error" else 0.0,
                "repair_focus": repair_focus(missing, spurious),
            }
        )
    return output


def mean_metric(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    return sum(float(row.get(key, 0.0)) for row in rows) / len(rows) if rows else 0.0


def summarize_critical_risk_run(
    scored_rows: Sequence[Mapping[str, Any]],
    audit_rows: Sequence[Mapping[str, Any]],
    report_dir_name: str,
    *,
    missing_fields: Sequence[str],
) -> Dict[str, Any]:
    fn_counts = Counter()
    fp_counts = Counter()
    error_counts = Counter(str(row["critical_risk_error_type"]) for row in audit_rows)
    focus_counts = Counter(str(row["repair_focus"]) for row in audit_rows if row["critical_risk_error_type"] != "exact")
    for row in audit_rows:
        fn_counts.update([risk for risk in str(row["missing_critical_risks"]).split(",") if risk])
        fp_counts.update([risk for risk in str(row["spurious_critical_risks"]).split(",") if risk])

    macro_f1 = critical_risk_macro_f1(scored_rows)
    claim_accuracy = mean_metric(scored_rows, "claim_accuracy")
    contaminated_support = mean_metric(scored_rows, "contaminated_citation_rate")
    exact_rate = mean_metric(audit_rows, "critical_risk_exact")
    repair_ready = (
        bool(scored_rows)
        and not missing_fields
        and claim_accuracy >= MIN_CLAIM_ACCURACY
        and contaminated_support <= MAX_CONTAMINATED_SUPPORT
        and macro_f1 >= MIN_CRITICAL_RISK_MACRO_F1
        and exact_rate >= MIN_EXACT_ROW_RATE
    )
    return {
        "report_dir": report_dir_name,
        "n": len(scored_rows),
        "repair_ready": repair_ready,
        "claim_accuracy": claim_accuracy,
        "contaminated_citation_rate": contaminated_support,
        "critical_risk_macro_f1": macro_f1,
        "critical_risk_exact_row_rate": exact_rate,
        "false_negative_row_rate": mean_metric(audit_rows, "critical_risk_has_false_negative"),
        "false_positive_row_rate": mean_metric(audit_rows, "critical_risk_has_false_positive"),
        "mixed_error_row_rate": mean_metric(audit_rows, "critical_risk_mixed_error"),
        "error_counts": dict(error_counts),
        "false_negative_counts": dict(fn_counts),
        "false_positive_counts": dict(fp_counts),
        "top_repair_focus": focus_counts.most_common(1)[0][0] if focus_counts else "preserve_current_boundary",
        "missing_fields": list(missing_fields),
    }


def build_critical_risk_audit_report(eha_mvp_dir: Path) -> Dict[str, Any]:
    runs: List[Dict[str, Any]] = []
    audit_rows: List[Dict[str, Any]] = []
    base = eha_mvp_dir / "results"
    for report_dir_name in STRUCTURAL_REPORT_DIRS:
        scored_rows = read_csv_rows(base / report_dir_name / "scored_predictions.csv")
        if not scored_rows:
            continue
        risk_fields = [
            f"critical_{risk}_{suffix}"
            for risk in CRITICAL_RISK_FLAGS
            for suffix in ("tp", "fp", "fn")
        ]
        missing_fields = [field for field in REQUIRED_FIELDS + risk_fields if field not in scored_rows[0]]
        annotated = annotate_critical_risk_rows(scored_rows, report_dir_name)
        audit_rows.extend(annotated)
        runs.append(summarize_critical_risk_run(scored_rows, annotated, report_dir_name, missing_fields=missing_fields))

    ready_runs = [run for run in runs if run["repair_ready"]]
    best_run = max(runs, key=lambda run: (run["critical_risk_macro_f1"], run["critical_risk_exact_row_rate"]), default=None)
    return {
        "date": "2026-05-16",
        "status": "ready" if ready_runs else "blocked",
        "critical_risk_repair_ready": bool(ready_runs),
        "thresholds": {
            "min_claim_accuracy": MIN_CLAIM_ACCURACY,
            "max_contaminated_support": MAX_CONTAMINATED_SUPPORT,
            "min_critical_risk_macro_f1": MIN_CRITICAL_RISK_MACRO_F1,
            "min_exact_row_rate": MIN_EXACT_ROW_RATE,
        },
        "runs": runs,
        "ready_runs": ready_runs,
        "best_run": best_run,
        "audit_rows": audit_rows,
        "recommended_next_contract": [
            "keep support-role guard as a separate deterministic consumer-safety check",
            "use evidence_diagnostics_v12_critical_risk_contract to add explicit positive and negative examples for false_consensus, citation_laundering, and partial_support",
            "separate visible rejected pollution from verdict-critical risks in every label definition",
            "require exact critical-risk rows on a fixed no-API audit before any full C-only API spend",
        ],
        "non_claims": [
            "not new model evidence",
            "not a passing structural repair",
            "not permission to run a full C-only or 500-1000 task expansion",
        ],
    }


def render_critical_risk_audit_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# EHA Step 2 Phase 2S Critical-Risk Repair Audit",
        "",
        "Date: 2026-05-16",
        "",
        f"- Status: `{report['status']}`",
        f"- Critical-risk repair ready: `{str(report['critical_risk_repair_ready']).lower()}`",
        "",
        "This is a no-API audit over already scored v8-v11 structural calibration rows. It decomposes critical-risk failures into exact rows, false negatives, false positives, and mixed errors so the next schema change has a concrete target.",
        "",
        "## Run Summary",
        "",
    ]
    table_rows = []
    for run in report["runs"]:
        table_rows.append(
            {
                "run": Path(str(run["report_dir"])).name,
                "n": run["n"],
                "ready": str(run["repair_ready"]).lower(),
                "claim": run["claim_accuracy"],
                "contam": run["contaminated_citation_rate"],
                "macro_f1": run["critical_risk_macro_f1"],
                "exact_rows": run["critical_risk_exact_row_rate"],
                "fn_rows": run["false_negative_row_rate"],
                "fp_rows": run["false_positive_row_rate"],
                "mixed_rows": run["mixed_error_row_rate"],
            }
        )
    lines.extend(
        markdown_table(
            table_rows,
            ["run", "n", "ready", "claim", "contam", "macro_f1", "exact_rows", "fn_rows", "fp_rows", "mixed_rows"],
        )
    )
    lines.extend(["", "## Top Repair Focus", ""])
    focus_rows = [
        {
            "run": Path(str(run["report_dir"])).name,
            "top_repair_focus": run["top_repair_focus"],
            "fn_counts": ", ".join(f"{risk}:{count}" for risk, count in sorted(run["false_negative_counts"].items())),
            "fp_counts": ", ".join(f"{risk}:{count}" for risk, count in sorted(run["false_positive_counts"].items())),
        }
        for run in report["runs"]
    ]
    lines.extend(markdown_table(focus_rows, ["run", "top_repair_focus", "fn_counts", "fp_counts"]))
    lines.extend(["", "## Recommended Next Contract", ""])
    for item in report["recommended_next_contract"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Non-Claims", ""])
    for item in report["non_claims"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def write_critical_risk_audit_report(eha_mvp_dir: Path, out_dir: Path) -> Dict[str, Any]:
    report = build_critical_risk_audit_report(eha_mvp_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "phase2s_critical_risk_audit_rows.csv", report["audit_rows"])
    write_csv(out_dir / "phase2s_critical_risk_audit_runs.csv", report["runs"])
    json_report = dict(report)
    json_report.pop("audit_rows", None)
    write_json(out_dir / "eha_step2_phase2s_critical_risk_audit.json", json_report)
    (out_dir / "eha-step2-phase2s-critical-risk-audit-2026-05-16.md").write_text(
        render_critical_risk_audit_markdown(report),
        encoding="utf-8",
    )
    return report


@app.command()
def main(
    eha_mvp_dir: Path = typer.Option(Path("."), help="eha-mvp project directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Output report directory."),
) -> None:
    report = write_critical_risk_audit_report(eha_mvp_dir, out_dir)
    console.print(f"[green]Wrote[/green] Phase 2S critical-risk audit: status={report['status']}")


if __name__ == "__main__":
    app()
