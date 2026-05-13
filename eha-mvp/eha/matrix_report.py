from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .matrix_scoring import aggregate_matrix, matrix_by_difficulty, score_matrix_run
from .report import markdown_table, write_csv
from .schemas import MatrixRunRecord, load_dataset, read_json, read_jsonl, write_json


app = typer.Typer(add_completion=False, help="Build EHA Matrix Escape Table v1 reports.")
console = Console()


def load_matrix_records(run_dir: Path) -> List[MatrixRunRecord]:
    return [MatrixRunRecord.model_validate(row) for row in read_jsonl(run_dir / "predictions.jsonl")]


def model_vs_hygiene(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    agg = aggregate_matrix(rows, ["model", "strategy"])
    by_key = {(row["model"], row["strategy"]): row for row in agg}
    models = sorted({str(row["model"]) for row in agg})
    output: List[Dict[str, Any]] = []
    for weak in models:
        weak_hygiene = by_key.get((weak, "hygienic_combo"))
        if weak_hygiene is None:
            continue
        for strong in models:
            if strong == weak:
                continue
            strong_naive = by_key.get((strong, "naive_bm25"))
            if strong_naive is None:
                continue
            output.append(
                {
                    "comparison": f"{weak} + hygienic_combo vs {strong} + naive_bm25",
                    "left_escape_rate": weak_hygiene["escape_rate"],
                    "right_escape_rate": strong_naive["escape_rate"],
                    "delta_left_minus_right": float(weak_hygiene["escape_rate"]) - float(strong_naive["escape_rate"]),
                }
            )
    return output


def write_failure_cases(path: Path, rows: Sequence[Mapping[str, Any]], limit: int = 12) -> None:
    candidates = [
        row
        for row in rows
        if float(row["escape_rate"]) == 0.0
        or float(row["claim_accuracy"]) == 0.0
        or float(row["contaminated_citation_rate"]) > 0.0
        or float(row["generated_lore_overclaim_rate"]) > 0.0
    ]
    candidates.sort(
        key=lambda row: (
            -float(row["overconfident_wrong_rate"]),
            -float(row["contaminated_citation_rate"]),
            row["difficulty"],
            row["task_id"],
        )
    )
    if len(candidates) < limit:
        seen = {(row["task_id"], row["model"], row["strategy"]) for row in candidates}
        fallback = [row for row in rows if (row["task_id"], row["model"], row["strategy"]) not in seen]
        fallback.sort(
            key=lambda row: (
                row["difficulty"] not in {"L3", "L4", "L5"},
                -float(row["overconfident_wrong_rate"]),
                -float(row["contaminated_citation_rate"]),
                row["difficulty"],
                row["task_id"],
            )
        )
        candidates.extend(fallback[: limit - len(candidates)])
    lines = ["# Matrix v1 Failure Cases", ""]
    for row in candidates[:limit]:
        lines.extend(
            [
                f"## `{row['task_id']}`",
                "",
                f"- Difficulty: `{row['difficulty']}`",
                f"- Model / strategy: `{row['model']}` / `{row['strategy']}`",
                f"- Retriever / prompt: `{row['retriever']}` / `{row['prompt']}`",
                f"- Gold verdict: `{row['gold_claim_verdict']}`",
                f"- Predicted verdict: `{row['predicted_claim_verdict']}`",
                f"- Confidence: `{float(row['confidence']):.3f}`",
                f"- Escape: `{float(row['escape_rate']):.3f}`",
                f"- Contaminated citation rate: `{float(row['contaminated_citation_rate']):.3f}`",
                f"- Supporting evidence: `{row['supporting_evidence'] or '-'}`",
                f"- Rejected evidence: `{row['rejected_evidence'] or '-'}`",
                "",
            ]
        )
    if len(candidates) < limit:
        lines.extend([f"_Only {len(candidates)} matching failure cases were available._", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(
    path: Path,
    *,
    escape_table: Sequence[Mapping[str, Any]],
    claim_table: Sequence[Mapping[str, Any]],
    ccr_table: Sequence[Mapping[str, Any]],
    abstention_table: Sequence[Mapping[str, Any]],
    difficulty_curves: Sequence[Mapping[str, Any]],
    comparisons: Sequence[Mapping[str, Any]],
    cost_report: Mapping[str, Any],
    preflight_gate: Mapping[str, Any] | None,
) -> None:
    lines = ["# EHA Matrix Escape Table v1", ""]
    if preflight_gate:
        lines.extend(["## Preflight Gate", "", "```json", json.dumps(preflight_gate, ensure_ascii=False, indent=2), "```", ""])
    lines.extend(["## 1. Main Escape-Rate Table", ""])
    lines.extend(markdown_table(escape_table, ["model", "strategy", "L0", "L1", "L2", "L3", "L4", "L5", "avg"]))
    lines.extend(["", "## 2. Claim Accuracy Table", ""])
    lines.extend(markdown_table(claim_table, ["model", "strategy", "L0", "L1", "L2", "L3", "L4", "L5", "avg"]))
    lines.extend(["", "## 3. Contaminated Citation Table", ""])
    lines.extend(markdown_table(ccr_table, ["model", "strategy", "L0", "L1", "L2", "L3", "L4", "L5", "avg"]))
    lines.extend(["", "## 4. Abstention Quality On L5", ""])
    lines.extend(markdown_table(abstention_table, ["model", "strategy", "difficulty", "n", "abstention_quality", "generated_lore_overclaim_rate"]))
    lines.extend(["", "## 5. Difficulty Curves", ""])
    lines.extend(markdown_table(difficulty_curves, ["model", "strategy", "difficulty", "n", "escape_rate", "claim_accuracy", "contaminated_citation_rate"]))
    lines.extend(["", "## 6. Weaker Model Plus Hygiene Vs Stronger Model Plus Naive Retrieval", ""])
    lines.extend(markdown_table(comparisons, ["comparison", "left_escape_rate", "right_escape_rate", "delta_left_minus_right"]))
    lines.extend(["", "## 7. Model Scale Vs Information Hygiene", ""])
    lines.append("Compare `hygienic_combo` rows against `naive_bm25` rows at the same or stronger model. The CSV artifacts keep this analysis machine-readable.")
    lines.extend(["", "## 8. Qualitative Failure Cases", ""])
    lines.append("See `failure_cases_matrix_v1.md` for at least 12 scored cases when available.")
    lines.extend(["", "## 9. Cost Report", "", "```json", json.dumps(cost_report, ensure_ascii=False, indent=2), "```"])
    lines.extend(["", "## 10. Diagnostics Note", ""])
    lines.append("Evidence diagnostics are secondary in Matrix v1 and are not used as a blocking gate. The primary metrics are escape rate, claim accuracy, contaminated citation rate, abstention quality, and overconfident wrong rate.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    data_dir: Path = typer.Option(Path("data/matrix-v1"), help="Generated Matrix v1 dataset directory."),
    run_dir: Path = typer.Option(Path("results/runs/matrix-v1"), help="Run directory containing Matrix v1 predictions."),
    out_dir: Path = typer.Option(Path("results/reports-matrix-v1"), help="Report output directory."),
) -> None:
    dataset = load_dataset(data_dir)
    records = load_matrix_records(run_dir)
    rows = score_matrix_run(records, dataset["tasks"], dataset["gold_documents"])
    cost_report = read_json(run_dir / "cost_report.json") if (run_dir / "cost_report.json").exists() else {}
    preflight_gate = read_json(run_dir / "preflight_gate.json") if (run_dir / "preflight_gate.json").exists() else None

    escape_table = matrix_by_difficulty(rows, "escape_rate")
    claim_table = matrix_by_difficulty(rows, "claim_accuracy")
    ccr_table = matrix_by_difficulty(rows, "contaminated_citation_rate")
    abstention = aggregate_matrix([row for row in rows if row["difficulty"] == "L5"], ["model", "strategy", "difficulty"])
    difficulty_curves = aggregate_matrix(rows, ["model", "strategy", "difficulty"])
    comparisons = model_vs_hygiene(rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "matrix_escape_rate.csv", escape_table)
    write_csv(out_dir / "matrix_claim_accuracy.csv", claim_table)
    write_csv(out_dir / "matrix_contaminated_citation_rate.csv", ccr_table)
    write_csv(out_dir / "matrix_abstention_quality.csv", abstention)
    write_csv(out_dir / "model_vs_hygiene_comparisons.csv", comparisons)
    write_csv(out_dir / "difficulty_curves.csv", difficulty_curves)
    write_csv(out_dir / "scored_predictions.csv", rows)
    write_json(out_dir / "cost_report.json", cost_report)
    if preflight_gate:
        write_json(out_dir / "preflight_gate.json", preflight_gate)
    write_failure_cases(out_dir / "failure_cases_matrix_v1.md", rows)
    write_summary(
        out_dir / "summary.md",
        escape_table=escape_table,
        claim_table=claim_table,
        ccr_table=ccr_table,
        abstention_table=abstention,
        difficulty_curves=difficulty_curves,
        comparisons=comparisons,
        cost_report=cost_report,
        preflight_gate=preflight_gate,
    )
    console.print(f"[green]Wrote Matrix v1 reports[/green] to {out_dir}")


if __name__ == "__main__":
    app()
