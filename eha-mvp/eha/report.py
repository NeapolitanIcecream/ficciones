from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import typer
from rich.console import Console

from .schemas import RunRecord, load_dataset, read_json, read_jsonl, run_record_from_dict, write_json
from .scoring import aggregate, score_run


app = typer.Typer(add_completion=False, help="Build EHA reports from predictions.")
console = Console()


def load_records(run_dir: Path) -> List[RunRecord]:
    return [run_record_from_dict(row) for row in read_jsonl(run_dir / "predictions.jsonl")]


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def markdown_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> List[str]:
    if not rows:
        return ["_No rows._"]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        values = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, float):
                values.append(f"{value:.3f}")
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return lines


def false_consensus_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    filtered = [row for row in rows if row["episode_type"] == "false_consensus"]
    grouped: Dict[tuple[Any, ...], List[Mapping[str, Any]]] = {}
    for row in filtered:
        key = (row["model"], row["strategy"], row["duplicate_count"])
        grouped.setdefault(key, []).append(row)
    output: List[Dict[str, Any]] = []
    for (model, strategy, duplicate_count), group in sorted(grouped.items()):
        wrong = [row for row in group if float(row["verdict_accuracy"]) == 0.0]
        output.append(
            {
                "model": model,
                "strategy": strategy,
                "duplicate_count": duplicate_count,
                "n": len(group),
                "wrong_answer_rate": len(wrong) / len(group),
                "mean_wrong_confidence": (sum(float(row["confidence"]) for row in wrong) / len(wrong)) if wrong else 0.0,
                "polluted_mistake_rate": sum(float(row["polluted_mistake"]) for row in group) / len(group),
            }
        )
    return output


def write_failure_cases(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    cases = [
        (
            "Correct verdict but contaminated citation",
            lambda row: float(row["verdict_accuracy"]) == 1.0 and float(row["contaminated_citation_rate"]) > 0,
        ),
        (
            "Wrong and high confidence",
            lambda row: float(row["verdict_accuracy"]) == 0.0 and float(row["confidence"]) >= 0.7,
        ),
        (
            "Same-upstream repetition treated as evidence",
            lambda row: row["episode_type"] == "false_consensus" and float(row["polluted_mistake"]) > 0,
        ),
        (
            "Stale document confusion",
            lambda row: row["episode_type"] == "temporal_pollution" and float(row["polluted_mistake"]) > 0,
        ),
        (
            "Correct generated-lore rejection",
            lambda row: row["episode_type"] == "halupedia_trap"
            and row["predicted_verdict"] == "insufficient"
            and float(row["verdict_accuracy"]) == 1.0,
        ),
    ]
    lines = ["# Failure Cases", ""]
    for label, predicate in cases:
        row = next((item for item in rows if predicate(item)), None)
        if row is None:
            lines.extend([f"## {label}", "", "_No matching case in this run._", ""])
            continue
        lines.extend(
            [
                f"## {label}",
                "",
                f"- Task: `{row['task_id']}`",
                f"- Model / strategy: `{row['model']}` / `{row['strategy']}`",
                f"- Episode type: `{row['episode_type']}`",
                f"- Gold verdict: `{row['gold_verdict']}`",
                f"- Predicted verdict: `{row['predicted_verdict']}`",
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
    by_strategy: Sequence[Mapping[str, Any]],
    by_model: Sequence[Mapping[str, Any]],
    false_consensus: Sequence[Mapping[str, Any]],
    halupedia: Sequence[Mapping[str, Any]],
    cost_report: Mapping[str, Any],
) -> None:
    lines = ["# EHA MVP Summary", ""]
    lines.append("## Overall metrics by model and strategy")
    lines.extend(markdown_table(by_strategy, ["model", "strategy", "n", "verdict_accuracy", "evidence_validity", "contaminated_citation_rate", "independent_evidence_score", "provenance_recovery_f1", "ece"]))
    lines.extend(["", "## Metrics by model", ""])
    lines.extend(markdown_table(by_model, ["model", "n", "verdict_accuracy", "contaminated_citation_rate", "provenance_recovery_f1", "ece", "cost_usd"]))
    lines.extend(["", "## Citation prompt ablation", ""])
    lines.extend(markdown_table(by_strategy, ["strategy", "verdict_accuracy", "evidence_validity", "contaminated_citation_rate", "provenance_recovery_f1"]))
    lines.extend(["", "## False consensus by duplicate count", ""])
    lines.extend(markdown_table(false_consensus, ["model", "strategy", "duplicate_count", "n", "wrong_answer_rate", "mean_wrong_confidence", "polluted_mistake_rate"]))
    lines.extend(["", "## Halupedia trap", ""])
    lines.extend(markdown_table(halupedia, ["model", "strategy", "n", "verdict_accuracy", "qips", "contaminated_citation_rate"]))
    lines.extend(["", "## Cost and token usage", ""])
    lines.append("```json")
    import json

    lines.append(json.dumps(cost_report, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    data_dir: Path = typer.Option(Path("data/generated"), help="Generated dataset directory."),
    run_dir: Path = typer.Option(Path("results/runs/pilot"), help="Run directory containing predictions.jsonl."),
    out_dir: Path = typer.Option(Path("results/reports"), help="Report output directory."),
) -> None:
    dataset = load_dataset(data_dir)
    records = load_records(run_dir)
    rows = score_run(records, dataset["tasks"], dataset["gold_documents"], dataset["edges"])
    by_strategy = aggregate(rows, ["model", "strategy"])
    by_model = aggregate(rows, ["model"])
    false_consensus = false_consensus_rows(rows)
    halupedia_rows = aggregate([row for row in rows if row["episode_type"] == "halupedia_trap"], ["model", "strategy"])
    cost_report = read_json(run_dir / "cost_report.json") if (run_dir / "cost_report.json").exists() else {}

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "metrics_by_strategy.csv", by_strategy)
    write_csv(out_dir / "metrics_by_model.csv", by_model)
    write_csv(out_dir / "false_consensus.csv", false_consensus)
    write_csv(out_dir / "scored_predictions.csv", rows)
    write_json(out_dir / "cost_report.json", cost_report)
    write_failure_cases(out_dir / "failure_cases.md", rows)
    write_summary(
        out_dir / "summary.md",
        by_strategy=by_strategy,
        by_model=by_model,
        false_consensus=false_consensus,
        halupedia=halupedia_rows,
        cost_report=cost_report,
    )
    console.print(f"[green]Wrote reports[/green] to {out_dir}")


if __name__ == "__main__":
    app()
