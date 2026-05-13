from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .phase2_scoring import aggregate_phase2, false_consensus_v2_rows, score_phase2_run
from .report import markdown_table, write_csv, write_failure_cases
from .schemas import Phase2RunRecord, load_dataset, read_json, read_jsonl, write_json


app = typer.Typer(add_completion=False, help="Build EHA Phase 2 reports.")
console = Console()


def load_phase2_records(run_dir: Path) -> List[Phase2RunRecord]:
    return [Phase2RunRecord.model_validate(row) for row in read_jsonl(run_dir / "predictions.jsonl")]


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def retrieval_aggregate(rows: Sequence[Mapping[str, Any]], group_key: str = "retriever") -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Mapping[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row[group_key]), []).append(row)
    metrics = [
        "primary_recall_at_k",
        "gold_evidence_recall_at_k",
        "contaminant_fraction_at_k",
        "unique_upstream_roots_at_k",
        "source_type_entropy_at_k",
        "pollutant_saturation_at_k",
    ]
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        record: Dict[str, Any] = {group_key: key, "n": len(group)}
        for metric in metrics:
            record[metric] = sum(float(row[metric]) for row in group) / len(group)
        output.append(record)
    return output


def primary_visibility_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str], List[Mapping[str, Any]]] = {}
    for row in rows:
        if row["episode_type"] != "false_consensus":
            continue
        key = (str(row["retriever"]), str(row["primary_visibility_under_bm25_top8"]))
        grouped.setdefault(key, []).append(row)
    output: List[Dict[str, Any]] = []
    for (retriever, visibility), group in sorted(grouped.items()):
        output.append(
            {
                "retriever": retriever,
                "primary_visibility_under_bm25_top8": visibility,
                "n": len(group),
                "claim_accuracy": sum(float(row["claim_accuracy"]) for row in group) / len(group),
                "escape_rate": sum(float(row["escape_rate"]) for row in group) / len(group),
                "mean_confidence": sum(float(row["confidence"]) for row in group) / len(group),
            }
        )
    return output


def write_phase2_failure_cases(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    cases = [
        row
        for row in rows
        if float(row["claim_accuracy"]) == 0.0
        or float(row["contaminated_citation_rate"]) > 0.0
        or float(row["escape_rate"]) == 0.0
    ][:8]
    lines = ["# EHA Phase 2 Failure Cases", ""]
    if not cases:
        lines.extend(["_No failure cases matched the report filters._", ""])
    for row in cases:
        lines.extend(
            [
                f"## `{row['task_id']}`",
                "",
                f"- Model / strategy / retriever: `{row['model']}` / `{row['strategy']}` / `{row['retriever']}`",
                f"- Episode type: `{row['episode_type']}`",
                f"- Gold claim verdict: `{row['gold_claim_verdict']}`",
                f"- Predicted claim verdict: `{row['predicted_claim_verdict']}`",
                f"- Gold scope tag: `{row['gold_scope_tag']}`",
                f"- Predicted scope tag: `{row['predicted_scope_tag']}`",
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
    retrieval_by_retriever: Sequence[Mapping[str, Any]],
    by_retriever: Sequence[Mapping[str, Any]],
    by_model: Sequence[Mapping[str, Any]],
    by_episode_type: Sequence[Mapping[str, Any]],
    false_consensus: Sequence[Mapping[str, Any]],
    primary_visibility: Sequence[Mapping[str, Any]],
    tool_agent: Sequence[Mapping[str, Any]],
    mixed_rows: Sequence[Mapping[str, Any]],
    cost_report: Mapping[str, Any],
    pilot_gate: Mapping[str, Any],
) -> None:
    lines = ["# EHA Phase 2 Pilot Summary", ""]
    lines.extend(["## Pilot Gate", ""])
    lines.append("```json")
    lines.append(json.dumps(pilot_gate, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.extend(["", "## Retrieval Stage", ""])
    lines.extend(markdown_table(retrieval_by_retriever, ["retriever", "n", "primary_recall_at_k", "gold_evidence_recall_at_k", "contaminant_fraction_at_k", "unique_upstream_roots_at_k", "pollutant_saturation_at_k"]))
    lines.extend(["", "## Final Answer By Retriever", ""])
    lines.extend(markdown_table(by_retriever, ["retriever", "n", "claim_accuracy", "scope_accuracy", "escape_rate", "primary_recovery_rate", "contaminated_citation_rate", "ece"]))
    lines.extend(["", "## Final Answer By Model", ""])
    lines.extend(markdown_table(by_model, ["model", "n", "claim_accuracy", "scope_accuracy", "escape_rate", "primary_recovery_rate", "cost_usd", "ece"]))
    lines.extend(["", "## Episode Type", ""])
    lines.extend(markdown_table(by_episode_type, ["episode_type", "n", "claim_accuracy", "scope_accuracy", "escape_rate", "contaminated_citation_rate", "laundered_support_rate"]))
    lines.extend(["", "## False Consensus V2", ""])
    lines.extend(markdown_table(false_consensus, ["retriever", "strategy", "duplicate_count", "primary_visibility_under_bm25_top8", "n", "wrong_answer_rate", "mean_wrong_confidence", "mean_pollutant_saturation_at_k"]))
    lines.extend(["", "## Primary Visibility Stratification", ""])
    lines.extend(markdown_table(primary_visibility, ["retriever", "primary_visibility_under_bm25_top8", "n", "claim_accuracy", "escape_rate", "mean_confidence"]))
    lines.extend(["", "## Oracle Vs Non-Oracle Note", ""])
    lines.append("`oracle_root_dedup_top8` is a diagnostic upper bound, not a deployable baseline; it uses scorer-only upstream roots.")
    lines.extend(["", "## Tool-Agent Comparison", ""])
    lines.extend(markdown_table(tool_agent, ["strategy", "n", "claim_accuracy", "escape_rate", "tool_parse_success", "primary_request_rate", "useful_tool_rate"]))
    lines.extend(["", "## Mixed-Source Schema V2", ""])
    lines.extend(markdown_table(mixed_rows, ["retriever", "strategy", "n", "claim_accuracy", "scope_accuracy", "escape_rate"]))
    lines.extend(["", "## Cost", ""])
    lines.append("```json")
    lines.append(json.dumps(cost_report, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    data_dir: Path = typer.Option(Path("data/phase2-pilot"), help="Generated Phase 2 dataset directory."),
    run_dir: Path = typer.Option(Path("results/runs/phase2-pilot"), help="Run directory containing Phase 2 predictions."),
    out_dir: Path = typer.Option(Path("results/reports-phase2"), help="Report output directory."),
) -> None:
    dataset = load_dataset(data_dir)
    records = load_phase2_records(run_dir)
    rows = score_phase2_run(records, dataset["tasks"], dataset["gold_documents"], dataset["edges"])
    retrieval_rows = read_csv_rows(run_dir / "retrieval_metrics.csv")
    by_retriever = aggregate_phase2(rows, ["retriever"])
    by_model = aggregate_phase2(rows, ["model"])
    by_episode_type = aggregate_phase2(rows, ["episode_type"])
    false_consensus = false_consensus_v2_rows(rows, retrieval_rows)
    retrieval_by_retriever = retrieval_aggregate(retrieval_rows)
    primary_visibility = primary_visibility_rows(rows)
    tool_agent = aggregate_phase2([row for row in rows if row["strategy"] in {"forced_primary_append", "tool_agent_2call"}], ["strategy"])
    mixed_rows = aggregate_phase2([row for row in rows if row["episode_type"] == "mixed_source_corruption_v2"], ["retriever", "strategy"])
    cost_report = read_json(run_dir / "cost_report.json") if (run_dir / "cost_report.json").exists() else {}
    pilot_gate = read_json(run_dir / "pilot_gate.json") if (run_dir / "pilot_gate.json").exists() else {}

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "metrics_by_retriever.csv", by_retriever)
    write_csv(out_dir / "metrics_by_model.csv", by_model)
    write_csv(out_dir / "metrics_by_episode_type.csv", by_episode_type)
    write_csv(out_dir / "retrieval_metrics.csv", retrieval_rows)
    write_csv(out_dir / "false_consensus_v2.csv", false_consensus)
    write_csv(out_dir / "tool_agent_metrics.csv", tool_agent)
    write_csv(out_dir / "scored_predictions.csv", rows)
    write_json(out_dir / "cost_report.json", cost_report)
    write_phase2_failure_cases(out_dir / "failure_cases_phase2.md", rows)
    write_summary(
        out_dir / "summary.md",
        retrieval_by_retriever=retrieval_by_retriever,
        by_retriever=by_retriever,
        by_model=by_model,
        by_episode_type=by_episode_type,
        false_consensus=false_consensus,
        primary_visibility=primary_visibility,
        tool_agent=tool_agent,
        mixed_rows=mixed_rows,
        cost_report=cost_report,
        pilot_gate=pilot_gate,
    )
    console.print(f"[green]Wrote Phase 2 reports[/green] to {out_dir}")


if __name__ == "__main__":
    app()
