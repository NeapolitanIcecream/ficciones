from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .report import markdown_table, write_csv
from .schemas import write_json


app = typer.Typer(add_completion=False, help="Validate Phase 2S supporting-evidence role safety without API calls.")
console = Console()

STRUCTURAL_REPORT_DIRS = [
    "reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini",
    "reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini",
    "reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini",
    "reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini",
]
MIN_ALLOW_RATE = 0.75
REQUIRED_FIELDS = [
    "task_id",
    "module",
    "dataset",
    "episode_type",
    "model",
    "retriever",
    "strategy",
    "prompt",
    "gold_claim_verdict",
    "predicted_claim_verdict",
    "supporting_evidence",
    "support_role_valid",
    "support_role_clean_only",
    "support_role_verdict_direct",
    "support_role_has_contaminated_doc",
    "support_role_has_unknown_doc",
    "support_role_has_extraneous_clean_doc",
    "support_role_nonempty_for_insufficient",
]


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


def support_role_guard_decision(row: Mapping[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    if as_float(row, "support_role_has_contaminated_doc") > 0.0:
        reasons.append("contaminated_support")
    if as_float(row, "support_role_has_unknown_doc") > 0.0:
        reasons.append("unknown_support")
    if as_float(row, "support_role_has_extraneous_clean_doc") > 0.0:
        reasons.append("extraneous_clean_support")
    if as_float(row, "support_role_nonempty_for_insufficient") > 0.0:
        reasons.append("nonempty_support_for_insufficient")
    if as_float(row, "support_role_clean_only") < 1.0 and not reasons:
        reasons.append("support_not_clean_only")
    if as_float(row, "support_role_verdict_direct") < 1.0:
        reasons.append("not_verdict_direct")

    decision = "allow" if not reasons else "block"
    support_role_valid = as_float(row, "support_role_valid") >= 1.0
    return {
        "guard_decision": decision,
        "guard_reasons": ",".join(reasons),
        "guard_allow": 1.0 if decision == "allow" else 0.0,
        "guard_block": 1.0 if decision == "block" else 0.0,
        "guard_invalid_accepted": 1.0 if decision == "allow" and not support_role_valid else 0.0,
        "guard_valid_blocked": 1.0 if decision == "block" and support_role_valid else 0.0,
    }


def annotate_guard_rows(rows: Sequence[Mapping[str, Any]], report_dir_name: str) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for row in rows:
        annotated = {
            "report_dir": report_dir_name,
            "task_id": row.get("task_id", ""),
            "module": row.get("module", ""),
            "dataset": row.get("dataset", ""),
            "episode_type": row.get("episode_type", ""),
            "model": row.get("model", ""),
            "retriever": row.get("retriever", ""),
            "strategy": row.get("strategy", ""),
            "prompt": row.get("prompt", ""),
            "gold_claim_verdict": row.get("gold_claim_verdict", ""),
            "predicted_claim_verdict": row.get("predicted_claim_verdict", ""),
            "supporting_evidence": row.get("supporting_evidence", ""),
            "support_role_valid": as_float(row, "support_role_valid"),
            "support_role_clean_only": as_float(row, "support_role_clean_only"),
            "support_role_verdict_direct": as_float(row, "support_role_verdict_direct"),
            "support_role_has_contaminated_doc": as_float(row, "support_role_has_contaminated_doc"),
            "support_role_has_unknown_doc": as_float(row, "support_role_has_unknown_doc"),
            "support_role_has_extraneous_clean_doc": as_float(row, "support_role_has_extraneous_clean_doc"),
            "support_role_nonempty_for_insufficient": as_float(row, "support_role_nonempty_for_insufficient"),
        }
        annotated.update(support_role_guard_decision(row))
        output.append(annotated)
    return output


def mean_metric(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    return sum(float(row.get(key, 0.0)) for row in rows) / len(rows) if rows else 0.0


def summarize_guard_run(rows: Sequence[Mapping[str, Any]], report_dir_name: str, *, missing_fields: Sequence[str]) -> Dict[str, Any]:
    reason_counts: Dict[str, int] = {}
    for row in rows:
        reasons = str(row.get("guard_reasons", ""))
        for reason in [item for item in reasons.split(",") if item]:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

    allow_rate = mean_metric(rows, "guard_allow")
    invalid_accepted_rate = mean_metric(rows, "guard_invalid_accepted")
    valid_blocked_rate = mean_metric(rows, "guard_valid_blocked")
    guard_ready = (
        bool(rows)
        and not missing_fields
        and allow_rate >= MIN_ALLOW_RATE
        and invalid_accepted_rate == 0.0
        and valid_blocked_rate == 0.0
    )
    return {
        "report_dir": report_dir_name,
        "n": len(rows),
        "guard_ready": guard_ready,
        "allow_rate": allow_rate,
        "block_rate": mean_metric(rows, "guard_block"),
        "support_role_valid_rate": mean_metric(rows, "support_role_valid"),
        "support_role_clean_only_rate": mean_metric(rows, "support_role_clean_only"),
        "support_role_verdict_direct_rate": mean_metric(rows, "support_role_verdict_direct"),
        "contaminated_support_rate": mean_metric(rows, "support_role_has_contaminated_doc"),
        "unknown_support_rate": mean_metric(rows, "support_role_has_unknown_doc"),
        "extraneous_clean_support_rate": mean_metric(rows, "support_role_has_extraneous_clean_doc"),
        "nonempty_support_for_insufficient_rate": mean_metric(rows, "support_role_nonempty_for_insufficient"),
        "invalid_accepted_rate": invalid_accepted_rate,
        "valid_blocked_rate": valid_blocked_rate,
        "reason_counts": reason_counts,
        "missing_fields": list(missing_fields),
    }


def build_support_role_guard_report(eha_mvp_dir: Path) -> Dict[str, Any]:
    runs: List[Dict[str, Any]] = []
    guard_rows: List[Dict[str, Any]] = []
    base = eha_mvp_dir / "results"
    for report_dir_name in STRUCTURAL_REPORT_DIRS:
        scored_path = base / report_dir_name / "scored_predictions.csv"
        rows = read_csv_rows(scored_path)
        if not rows:
            continue
        missing_fields = [field for field in REQUIRED_FIELDS if field not in rows[0]]
        annotated = annotate_guard_rows(rows, report_dir_name)
        guard_rows.extend(annotated)
        runs.append(summarize_guard_run(annotated, report_dir_name, missing_fields=missing_fields))

    ready_runs = [run for run in runs if run["guard_ready"]]
    latest_ready = next((run for run in reversed(runs) if run["guard_ready"]), None)
    return {
        "date": "2026-05-16",
        "status": "ready" if ready_runs else "blocked",
        "guard_ready": bool(ready_runs),
        "min_allow_rate": MIN_ALLOW_RATE,
        "runs": runs,
        "ready_runs": ready_runs,
        "recommended_run": latest_ready,
        "guard_rows": guard_rows,
        "non_claims": [
            "not new model evidence",
            "not a repair for wrong claim verdicts",
            "not a repair for missing critical-risk labels",
            "not a substitute for human audit or surface-cue design review",
        ],
    }


def render_support_role_guard_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# EHA Step 2 Phase 2S Support-Role Guard",
        "",
        "Date: 2026-05-16",
        "",
        f"- Status: `{report['status']}`",
        f"- Guard ready: `{str(report['guard_ready']).lower()}`",
        f"- Minimum allow rate: `{float(report['min_allow_rate']):.2f}`",
        "",
        "This is a no-API deterministic validation pass over already scored Phase 2S calibration rows. "
        "It validates whether supporting-evidence rows can be accepted by a downstream consumer, and blocks rows with contaminated, unknown, extraneous, non-empty insufficient, or non-verdict-direct support.",
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
                "ready": str(run["guard_ready"]).lower(),
                "allow": run["allow_rate"],
                "block": run["block_rate"],
                "valid": run["support_role_valid_rate"],
                "clean": run["support_role_clean_only_rate"],
                "direct": run["support_role_verdict_direct_rate"],
                "invalid_accepted": run["invalid_accepted_rate"],
                "valid_blocked": run["valid_blocked_rate"],
            }
        )
    lines.extend(
        markdown_table(
            table_rows,
            ["run", "n", "ready", "allow", "block", "valid", "clean", "direct", "invalid_accepted", "valid_blocked"],
        )
    )
    lines.extend(["", "## Block Reasons", ""])
    reason_rows = []
    for run in report["runs"]:
        counts = run.get("reason_counts", {})
        reason_rows.append(
            {
                "run": Path(str(run["report_dir"])).name,
                "contaminated": counts.get("contaminated_support", 0),
                "unknown": counts.get("unknown_support", 0),
                "extraneous": counts.get("extraneous_clean_support", 0),
                "nonempty_insufficient": counts.get("nonempty_support_for_insufficient", 0),
                "not_direct": counts.get("not_verdict_direct", 0),
                "missing_fields": ",".join(run.get("missing_fields", [])),
            }
        )
    lines.extend(
        markdown_table(
            reason_rows,
            ["run", "contaminated", "unknown", "extraneous", "nonempty_insufficient", "not_direct", "missing_fields"],
        )
    )
    lines.extend(["", "## Non-Claims", ""])
    for claim in report["non_claims"]:
        lines.append(f"- {claim}")
    lines.append("")
    return "\n".join(lines)


def write_support_role_guard_report(eha_mvp_dir: Path, out_dir: Path) -> Dict[str, Any]:
    report = build_support_role_guard_report(eha_mvp_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "phase2s_support_role_guard_rows.csv", report["guard_rows"])
    write_csv(out_dir / "phase2s_support_role_guard_runs.csv", report["runs"])
    json_report = dict(report)
    json_report.pop("guard_rows", None)
    write_json(out_dir / "eha_step2_phase2s_support_role_guard.json", json_report)
    (out_dir / "eha-step2-phase2s-support-role-guard-2026-05-16.md").write_text(
        render_support_role_guard_markdown(report),
        encoding="utf-8",
    )
    return report


@app.command()
def main(
    eha_mvp_dir: Path = typer.Option(Path("."), help="eha-mvp project directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Output report directory."),
) -> None:
    report = write_support_role_guard_report(eha_mvp_dir, out_dir)
    console.print(f"[green]Wrote[/green] Phase 2S support-role guard: status={report['status']}")


if __name__ == "__main__":
    app()
