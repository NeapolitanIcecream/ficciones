from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .phase2r_scoring import (
    aggregate_phase2r,
    false_consensus_stress_rows,
    halupedia_abstention_rows,
    phase2r_gate,
    scope_confusion_matrix,
    score_phase2r_run,
)
from .report import markdown_table, write_csv
from .schemas import Phase2RunRecord, load_dataset, read_json, read_jsonl, write_json


app = typer.Typer(add_completion=False, help="Build EHA Phase 2R reports.")
console = Console()


def load_phase2r_records(run_dir: Path) -> List[Phase2RunRecord]:
    return [Phase2RunRecord.model_validate(row) for row in read_jsonl(run_dir / "predictions.jsonl")]


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def retrieval_aggregate(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["retriever"]), []).append(row)
    metrics = [
        "primary_recall_at_k",
        "gold_evidence_recall_at_k",
        "contradiction_candidate_recall_at_k",
        "contaminant_fraction_at_k",
        "unique_upstream_roots_at_k",
        "source_type_entropy_at_k",
        "pollutant_saturation_at_k",
    ]
    output: List[Dict[str, Any]] = []
    for retriever, group in sorted(grouped.items()):
        record: Dict[str, Any] = {"retriever": retriever, "n": len(group)}
        for metric in metrics:
            record[metric] = sum(float(row[metric]) for row in group) / len(group)
        output.append(record)
    return output


def active_tool_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return aggregate_phase2r(
        [row for row in rows if row["strategy"] in {"static_hygienic_combo", "forced_primary_append", "forced_triage_tools", "tool_agent_3call_policy"}],
        ["strategy"],
    )


def write_failure_cases(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    candidates = [
        row
        for row in rows
        if float(row["claim_accuracy"]) == 0.0
        or float(row["scope_accuracy"]) == 0.0
        or float(row["generated_lore_overclaim"]) > 0.0
        or float(row["contaminated_citation_rate"]) > 0.0
    ][:8]
    lines = ["# EHA Phase 2R Failure Cases", ""]
    if not candidates:
        lines.extend(["_No matching failure cases._", ""])
    for row in candidates:
        lines.extend(
            [
                f"## `{row['task_id']}`",
                "",
                f"- Model / strategy / retriever: `{row['model']}` / `{row['strategy']}` / `{row['retriever']}`",
                f"- Episode type: `{row['episode_type']}`",
                f"- Duplicate count: `{row['duplicate_count']}`",
                f"- Stress score: `{row['stress_score']}`",
                f"- Gold claim / predicted claim: `{row['gold_claim_verdict']}` / `{row['predicted_claim_verdict']}`",
                f"- Gold scope / predicted scope: `{row['gold_scope_tag']}` / `{row['predicted_scope_tag']}`",
                f"- Confidence: `{float(row['confidence']):.3f}`",
                f"- Supporting evidence: `{row['supporting_evidence'] or '-'}`",
                f"- Rejected evidence: `{row['rejected_evidence'] or '-'}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(
    path: Path,
    *,
    gate: Mapping[str, Any],
    false_consensus: Sequence[Mapping[str, Any]],
    retrieval_by_retriever: Sequence[Mapping[str, Any]],
    static_by_retriever: Sequence[Mapping[str, Any]],
    active_tools: Sequence[Mapping[str, Any]],
    scope_confusion: Sequence[Mapping[str, Any]],
    halupedia: Sequence[Mapping[str, Any]],
    cost_report: Mapping[str, Any],
) -> None:
    lines = ["# EHA Phase 2R Stress-Calibrated Pilot Summary", ""]
    lines.extend(["## Gate Table", ""])
    lines.append("```json")
    lines.append(json.dumps(gate, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.extend(["", "## False-Consensus Stress", ""])
    lines.extend(markdown_table(false_consensus, ["retriever", "strategy", "duplicate_count", "primary_visibility_under_bm25_top8", "stress_score", "n", "wrong_answer_rate", "mean_wrong_confidence", "mean_pollutant_saturation_at_k", "escape_rate"]))
    lines.extend(["", "## Retrieval Stage", ""])
    lines.extend(markdown_table(retrieval_by_retriever, ["retriever", "n", "primary_recall_at_k", "gold_evidence_recall_at_k", "contradiction_candidate_recall_at_k", "contaminant_fraction_at_k", "pollutant_saturation_at_k"]))
    lines.extend(["", "## Static Answer", ""])
    lines.extend(markdown_table(static_by_retriever, ["retriever", "n", "claim_accuracy", "scope_accuracy", "escape_rate", "contaminated_citation_rate", "generated_lore_overclaim", "ece"]))
    lines.extend(["", "## Active Verification", ""])
    lines.extend(markdown_table(active_tools, ["strategy", "n", "claim_accuracy", "scope_accuracy", "escape_rate", "tool_parse_success", "trace_rate", "compare_versions_rate", "search_contradictions_rate", "primary_request_rate", "tool_diversity"]))
    lines.extend(["", "## Scope Confusion Matrix", ""])
    lines.extend(markdown_table(scope_confusion, ["gold_scope_tag", "predicted_scope_tag", "n", "row_fraction"]))
    lines.extend(["", "## Tool Diversity", ""])
    lines.extend(markdown_table(active_tools, ["strategy", "trace_rate", "compare_versions_rate", "search_contradictions_rate", "primary_request_rate", "tool_diversity"]))
    lines.extend(["", "## Halupedia And No-Primary Abstention", ""])
    lines.extend(markdown_table(halupedia, ["episode_type", "strategy", "n", "claim_accuracy", "generated_lore_overclaim", "correct_insufficient", "overconfident_wrong", "confidence"]))
    lines.extend(["", "## Oracle Note", ""])
    lines.append("`oracle_root_dedup_top8` uses scorer-only upstream roots and is not deployable. It is included only in retrieval-stage diagnostics.")
    lines.extend(["", "## Cost Report", ""])
    lines.append("```json")
    lines.append(json.dumps(cost_report, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    data_dir: Path = typer.Option(Path("data/phase2r-stress-pilot"), help="Generated Phase 2R dataset directory."),
    run_dir: Path = typer.Option(Path("results/runs/phase2r-stress-pilot"), help="Run directory containing predictions."),
    out_dir: Path = typer.Option(Path("results/reports-phase2r"), help="Report output directory."),
) -> None:
    dataset = load_dataset(data_dir)
    records = load_phase2r_records(run_dir)
    rows = score_phase2r_run(records, dataset["tasks"], dataset["gold_documents"], dataset["edges"])
    retrieval_rows = read_csv_rows(run_dir / "retrieval_metrics.csv")
    gate_obj = phase2r_gate(rows, retrieval_rows, records)
    gate = {"passed": gate_obj.passed, "checks": gate_obj.checks, "details": gate_obj.details}
    retrieval_by_retriever = retrieval_aggregate(retrieval_rows)
    static_rows = [row for row in rows if row["strategy"] == "evidence_graph_v3"]
    static_by_retriever = aggregate_phase2r(static_rows, ["retriever"])
    active_tools = active_tool_rows(rows)
    false_consensus = false_consensus_stress_rows(rows, retrieval_rows)
    scope_confusion = scope_confusion_matrix(rows)
    halupedia = halupedia_abstention_rows(rows)
    cost_report = read_json(run_dir / "cost_report.json") if (run_dir / "cost_report.json").exists() else {}

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "retrieval_metrics.csv", retrieval_rows)
    write_csv(out_dir / "static_metrics_by_retriever.csv", static_by_retriever)
    write_csv(out_dir / "active_tool_metrics.csv", active_tools)
    write_csv(out_dir / "false_consensus_stress.csv", false_consensus)
    write_csv(out_dir / "scope_confusion_matrix.csv", scope_confusion)
    write_csv(out_dir / "halupedia_abstention.csv", halupedia)
    write_csv(out_dir / "scored_predictions.csv", rows)
    write_json(out_dir / "cost_report.json", cost_report)
    write_json(out_dir / "phase2r_gate.json", gate)
    write_failure_cases(out_dir / "failure_cases_phase2r.md", rows)
    write_summary(
        out_dir / "summary.md",
        gate=gate,
        false_consensus=false_consensus,
        retrieval_by_retriever=retrieval_by_retriever,
        static_by_retriever=static_by_retriever,
        active_tools=active_tools,
        scope_confusion=scope_confusion,
        halupedia=halupedia,
        cost_report=cost_report,
    )
    console.print(f"[green]Wrote Phase 2R reports[/green] to {out_dir}")


if __name__ == "__main__":
    app()
