from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .phase2s_scoring import (
    aggregate_phase2s,
    diagnostic_confusion_by_flag,
    phase2s_gate,
    score_phase2s_run,
    unsafe_scope_miss_rows,
)
from .report import markdown_table, write_csv
from .schemas import Phase2SRunRecord, load_dataset, read_json, read_jsonl, write_json


app = typer.Typer(add_completion=False, help="Build EHA Phase 2S reports.")
console = Console()


def load_phase2s_records(run_dir: Path) -> List[Phase2SRunRecord]:
    return [Phase2SRunRecord.model_validate(row) for row in read_jsonl(run_dir / "predictions.jsonl")]


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_failure_cases(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    candidates = [
        row
        for row in rows
        if float(row["claim_accuracy"]) == 0.0
        or float(row["unsafe_scope_miss"]) > 0.0
        or float(row["contaminated_citation_rate"]) > 0.0
        or float(row["diagnostic_field_accuracy"]) < 1.0
    ][:10]
    lines = ["# EHA Phase 2S Failure Cases", ""]
    if not candidates:
        lines.extend(["_No matching failure cases._", ""])
    for row in candidates:
        lines.extend(
            [
                f"## `{row['task_id']}`",
                "",
                f"- Module / dataset: `{row['module']}` / `{row['dataset']}`",
                f"- Model / strategy / retriever: `{row['model']}` / `{row['strategy']}` / `{row['retriever']}`",
                f"- Prompt: `{row['prompt']}`",
                f"- Episode type: `{row['episode_type']}`",
                f"- Gold claim / predicted claim: `{row['gold_claim_verdict']}` / `{row['predicted_claim_verdict']}`",
                f"- Gold risks: `{row['gold_critical_risks'] or '-'}`",
                f"- Predicted risks: `{row['predicted_critical_risks'] or '-'}`",
                f"- Confidence: `{float(row['confidence']):.3f}`",
                f"- Supporting evidence: `{row['supporting_evidence'] or '-'}`",
                f"- Rejected evidence: `{row['rejected_evidence'] or '-'}`",
                f"- Ledger evidence: `{row['ledger_evidence'] or '-'}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(
    path: Path,
    *,
    gate: Mapping[str, Any],
    scope_metrics: Sequence[Mapping[str, Any]],
    temporal_metrics: Sequence[Mapping[str, Any]],
    integrated_metrics: Sequence[Mapping[str, Any]],
    diagnostic_confusion: Sequence[Mapping[str, Any]],
    tool_routing: Sequence[Mapping[str, Any]],
    unsafe_misses: Sequence[Mapping[str, Any]],
    failure_cases_path: str,
    cost_report: Mapping[str, Any],
) -> None:
    lines = ["# EHA Phase 2S Scope Diagnosis & Temporal Routing Repair Summary", ""]
    lines.extend(["## 1. Gate Result", ""])
    lines.append("```json")
    lines.append(json.dumps(gate, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.extend(["", "## 2. Module A Prompt Comparison", ""])
    lines.extend(markdown_table(scope_metrics, ["prompt", "n", "claim_accuracy", "diagnostic_macro_f1", "stale_recall", "conflict_recall", "generated_lore_recall", "no_primary_precision", "unsafe_scope_miss_rate"]))
    lines.extend(["", "## 3. Diagnostic Macro-F1 And Per-Risk Recall", ""])
    lines.extend(markdown_table(diagnostic_confusion, ["flag", "tp", "fp", "fn", "tn", "precision", "recall", "f1"]))
    lines.extend(["", "## 4. Temporal Tool Routing", ""])
    lines.extend(markdown_table(temporal_metrics, ["strategy", "n", "claim_accuracy", "stale_recall", "compare_versions_rate", "useful_compare_versions_rate", "tool_parse_success", "unsafe_scope_miss_rate"]))
    lines.extend(["", "## 5. Integrated Regression On Phase 2R", ""])
    lines.extend(markdown_table(integrated_metrics, ["retriever", "strategy", "n", "claim_accuracy", "diagnostic_macro_f1", "escape_rate", "contaminated_citation_rate", "stale_recall", "conflict_recall", "generated_lore_recall"]))
    lines.extend(["", "## 6. False-Consensus Stress Regression Check", ""])
    false_rows = [row for row in integrated_metrics if row.get("retriever") in {"bm25_top8", "hygienic_combo_top8"} and row.get("strategy") == "evidence_diagnostics_v1"]
    lines.extend(markdown_table(false_rows, ["retriever", "strategy", "claim_accuracy", "escape_rate", "contaminated_citation_rate", "diagnostic_macro_f1"]))
    lines.extend(["", "## 7. Generated-Lore Detection Vs No-Primary Abstention", ""])
    lore_rows = [row for row in integrated_metrics if "generated_lore_recall" in row]
    lines.extend(markdown_table(lore_rows, ["retriever", "strategy", "generated_lore_recall", "no_primary_precision", "claim_accuracy", "unsafe_scope_miss_rate"]))
    lines.extend(["", "## 8. Active Tool Helpfulness And Harmfulness", ""])
    lines.extend(markdown_table(tool_routing, ["module", "strategy", "n", "escape_rate", "claim_accuracy", "compare_versions_rate", "useful_compare_versions_rate", "trace_rate", "search_contradictions_rate", "primary_request_rate"]))
    lines.extend(["", "## 9. Qualitative Failure Cases", ""])
    lines.append(f"See `{failure_cases_path}` for at least 10 qualitative cases when available.")
    lines.extend(["", "## 10. Cost Report", ""])
    lines.append("```json")
    lines.append(json.dumps(cost_report, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.extend(["", "## Unsafe Scope Misses", ""])
    lines.extend(markdown_table(unsafe_misses[:20], ["task_id", "module", "episode_type", "strategy", "confidence", "gold_critical_risks", "predicted_critical_risks"]))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    scope_data_dir: Path = typer.Option(Path("data/phase2s-scope-diagnostic"), help="Module A dataset directory."),
    temporal_data_dir: Path = typer.Option(Path("data/phase2s-temporal-routing"), help="Module B dataset directory."),
    phase2r_data_dir: Path = typer.Option(Path("data/phase2r-stress-pilot"), help="Module C Phase 2R dataset directory."),
    run_dir: Path = typer.Option(Path("results/runs/phase2s"), help="Run directory containing Phase 2S predictions."),
    out_dir: Path = typer.Option(Path("results/reports-phase2s"), help="Report output directory."),
) -> None:
    scope_dataset = load_dataset(scope_data_dir)
    temporal_dataset = load_dataset(temporal_data_dir)
    phase2r_dataset = load_dataset(phase2r_data_dir)
    records = load_phase2s_records(run_dir)
    all_tasks = list(scope_dataset["tasks"]) + list(temporal_dataset["tasks"]) + list(phase2r_dataset["tasks"])
    all_gold = list(scope_dataset["gold_documents"]) + list(temporal_dataset["gold_documents"]) + list(phase2r_dataset["gold_documents"])
    rows = score_phase2s_run(records, all_tasks, all_gold)
    retrieval_rows = read_csv_rows(run_dir / "retrieval_metrics.csv")
    gate_obj = phase2s_gate(rows, retrieval_rows, records)
    gate = {"passed": gate_obj.passed, "checks": gate_obj.checks, "details": gate_obj.details}
    scope_metrics = aggregate_phase2s([row for row in rows if row["module"] == "A"], ["prompt"])
    temporal_metrics = aggregate_phase2s([row for row in rows if row["module"] == "B"], ["strategy"])
    integrated_metrics = aggregate_phase2s([row for row in rows if row["module"] == "C"], ["retriever", "strategy"])
    diagnostic_confusion = diagnostic_confusion_by_flag(rows)
    tool_routing = aggregate_phase2s([row for row in rows if row["strategy"] in {"route_then_answer_v1", "forced_compare_versions", "tool_agent_3call_policy", "forced_triage_tools", "static_hygienic_combo"}], ["module", "strategy"])
    unsafe_misses = unsafe_scope_miss_rows(rows)
    cost_report = read_json(run_dir / "cost_report.json") if (run_dir / "cost_report.json").exists() else {}

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "scope_diagnostic_metrics.csv", scope_metrics)
    write_csv(out_dir / "temporal_routing_metrics.csv", temporal_metrics)
    write_csv(out_dir / "integrated_regression_metrics.csv", integrated_metrics)
    write_csv(out_dir / "diagnostic_confusion_by_flag.csv", diagnostic_confusion)
    write_csv(out_dir / "tool_routing_metrics.csv", tool_routing)
    write_csv(out_dir / "unsafe_scope_misses.csv", unsafe_misses)
    write_csv(out_dir / "scored_predictions.csv", rows)
    write_json(out_dir / "phase2s_gate.json", gate)
    write_json(out_dir / "cost_report.json", cost_report)
    write_failure_cases(out_dir / "failure_cases_phase2s.md", rows)
    write_summary(
        out_dir / "summary.md",
        gate=gate,
        scope_metrics=scope_metrics,
        temporal_metrics=temporal_metrics,
        integrated_metrics=integrated_metrics,
        diagnostic_confusion=diagnostic_confusion,
        tool_routing=tool_routing,
        unsafe_misses=unsafe_misses,
        failure_cases_path=str(out_dir / "failure_cases_phase2s.md"),
        cost_report=cost_report,
    )
    console.print(f"[green]Wrote Phase 2S reports[/green] to {out_dir}")


if __name__ == "__main__":
    app()
