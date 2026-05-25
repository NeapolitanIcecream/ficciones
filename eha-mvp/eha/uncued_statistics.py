from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from random import Random
from statistics import pstdev
from typing import Any, Dict, Iterable, Mapping, Sequence

import typer
from rich.console import Console

from .report import markdown_table
from .schemas import write_json


app = typer.Typer(add_completion=False, help="Bootstrap uncertainty summaries for EHA-Uncued pilot results.")
console = Console()

MODEL_METRICS = ("operational_epistemic_escape", "belief_correctness", "evidence_precision")
CONDITION_ORDER = ("clean", "conflicting_evidence", "false_consensus", "buried_primary", "generated_lore")
VIEW_HIDDEN = "neutral_metadata_hidden"
VIEW_VISIBLE = "neutral_metadata_visible"


def load_scored_rows(results_dir: Path) -> list[Dict[str, str]]:
    path = results_dir / "uncued_pilot_scored_predictions.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def latent_task_id(row: Mapping[str, Any]) -> str:
    if row.get("base_task_id"):
        return str(row["base_task_id"])
    task_id = str(row.get("task_id", ""))
    for suffix in ("_visible", "_hidden"):
        if task_id.endswith(suffix):
            return task_id[: -len(suffix)]
    return task_id


def parse_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def mean_metric(rows: Sequence[Mapping[str, Any]], metric: str) -> float:
    values = [value for row in rows if (value := parse_float(row.get(metric))) is not None]
    return sum(values) / len(values) if values else 0.0


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def metric_summary(observed: float, distribution: Sequence[float]) -> Dict[str, Any]:
    return {
        "mean": observed,
        "ci95": {
            "low": percentile(distribution, 0.025),
            "high": percentile(distribution, 0.975),
        },
        "bootstrap_std": pstdev(distribution) if len(distribution) > 1 else 0.0,
    }


def group_rows_by_latent_task(rows: Sequence[Mapping[str, Any]]) -> Dict[str, list[Mapping[str, Any]]]:
    grouped: Dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[latent_task_id(row)].append(row)
    return dict(grouped)


def resample_rows_by_latent_task(
    rows_by_task: Mapping[str, Sequence[Mapping[str, Any]]],
    sampled_task_ids: Sequence[str],
) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    for task_id in sampled_task_ids:
        rows.extend(rows_by_task[task_id])
    return rows


def sorted_conditions(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    observed = {str(row["condition"]) for row in rows}
    ordered = [condition for condition in CONDITION_ORDER if condition in observed]
    ordered.extend(sorted(observed - set(ordered)))
    return ordered


def paired_delta_map(rows: Sequence[Mapping[str, Any]], metric: str) -> Dict[tuple[str, str], float]:
    grouped: Dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        value = parse_float(row.get(metric))
        if value is None:
            continue
        grouped[(latent_task_id(row), str(row["model"]), str(row["view"]))].append(value)

    output: Dict[tuple[str, str], float] = {}
    task_models = {(task_id, model) for task_id, model, _view in grouped}
    for task_id, model in task_models:
        hidden_values = grouped.get((task_id, model, VIEW_HIDDEN), [])
        visible_values = grouped.get((task_id, model, VIEW_VISIBLE), [])
        if hidden_values and visible_values:
            output[(task_id, model)] = mean(visible_values) - mean(hidden_values)
    return output


def paired_delta_values(
    deltas: Mapping[tuple[str, str], float],
    sampled_task_ids: Sequence[str],
    models: Sequence[str],
    *,
    model: str | None = None,
) -> list[float]:
    selected_models = [model] if model is not None else list(models)
    values: list[float] = []
    for task_id in sampled_task_ids:
        for selected_model in selected_models:
            value = deltas.get((task_id, selected_model))
            if value is not None:
                values.append(value)
    return values


def initialize_distributions(
    models: Sequence[str],
    conditions: Sequence[str],
) -> Dict[str, Dict[Any, list[float]]]:
    return {
        "model_metrics": {(model, metric): [] for model in models for metric in MODEL_METRICS},
        "condition_operational_epistemic_escape": {condition: [] for condition in conditions},
        "generated_lore_belief_operational_gap": {"generated_lore": []},
        "visible_hidden_paired_deltas": {model: [] for model in ["overall", *models]},
    }


def bootstrap_statistics(
    rows: Sequence[Mapping[str, Any]],
    *,
    iterations: int,
    seed: int,
) -> Dict[str, Any]:
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    rows_by_task = group_rows_by_latent_task(rows)
    task_ids = sorted(rows_by_task)
    if not task_ids:
        raise ValueError("at least one scored row is required")

    models = sorted({str(row["model"]) for row in rows})
    conditions = sorted_conditions(rows)
    distributions = initialize_distributions(models, conditions)
    rng = Random(seed)
    delta_map = paired_delta_map(rows, "operational_epistemic_escape")

    for _ in range(iterations):
        sampled_task_ids = [rng.choice(task_ids) for _ in task_ids]
        sample_rows = resample_rows_by_latent_task(rows_by_task, sampled_task_ids)

        for model in models:
            model_rows = [row for row in sample_rows if row["model"] == model]
            for metric in MODEL_METRICS:
                distributions["model_metrics"][(model, metric)].append(mean_metric(model_rows, metric))

        for condition in conditions:
            condition_rows = [row for row in sample_rows if row["condition"] == condition]
            if condition_rows:
                distributions["condition_operational_epistemic_escape"][condition].append(
                    mean_metric(condition_rows, "operational_epistemic_escape")
                )

        generated_rows = [row for row in sample_rows if row["condition"] == "generated_lore"]
        if generated_rows:
            gap = mean_metric(generated_rows, "belief_correctness") - mean_metric(
                generated_rows, "operational_epistemic_escape"
            )
            distributions["generated_lore_belief_operational_gap"]["generated_lore"].append(gap)

        overall_deltas = paired_delta_values(delta_map, sampled_task_ids, models)
        if overall_deltas:
            distributions["visible_hidden_paired_deltas"]["overall"].append(mean(overall_deltas))
        for model in models:
            model_deltas = paired_delta_values(delta_map, sampled_task_ids, models, model=model)
            if model_deltas:
                distributions["visible_hidden_paired_deltas"][model].append(mean(model_deltas))

    model_metrics: list[Dict[str, Any]] = []
    for model in models:
        model_rows = [row for row in rows if row["model"] == model]
        item: Dict[str, Any] = {"model": model, "n": len(model_rows)}
        for metric in MODEL_METRICS:
            item[metric] = metric_summary(
                mean_metric(model_rows, metric),
                distributions["model_metrics"][(model, metric)],
            )
        model_metrics.append(item)

    condition_metrics: list[Dict[str, Any]] = []
    for condition in conditions:
        condition_rows = [row for row in rows if row["condition"] == condition]
        condition_metrics.append(
            {
                "condition": condition,
                "n": len(condition_rows),
                "operational_epistemic_escape": metric_summary(
                    mean_metric(condition_rows, "operational_epistemic_escape"),
                    distributions["condition_operational_epistemic_escape"][condition],
                ),
            }
        )

    generated_rows = [row for row in rows if row["condition"] == "generated_lore"]
    generated_gap = mean_metric(generated_rows, "belief_correctness") - mean_metric(
        generated_rows, "operational_epistemic_escape"
    )
    visible_hidden_deltas: list[Dict[str, Any]] = []
    for model in ["overall", *models]:
        values = paired_delta_values(delta_map, task_ids, models, model=None if model == "overall" else model)
        visible_hidden_deltas.append(
            {
                "model": model,
                "n_pairs": len(values),
                "visible_minus_hidden_operational_epistemic_escape": metric_summary(
                    mean(values),
                    distributions["visible_hidden_paired_deltas"][model],
                ),
            }
        )

    return {
        "method": {
            "resample_unit": "latent_task",
            "paired_views_kept_together": True,
            "iterations": iterations,
            "seed": seed,
            "latent_task_count": len(task_ids),
            "scored_row_count": len(rows),
        },
        "model_metrics": model_metrics,
        "condition_operational_epistemic_escape": condition_metrics,
        "generated_lore_belief_operational_gap": metric_summary(
            generated_gap,
            distributions["generated_lore_belief_operational_gap"]["generated_lore"],
        ),
        "visible_hidden_paired_deltas": visible_hidden_deltas,
    }


def format_ci(entry: Mapping[str, Any]) -> str:
    ci = entry["ci95"]
    return f"{float(entry['mean']):.3f} [{float(ci['low']):.3f}, {float(ci['high']):.3f}]"


def latex_escape(value: Any) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def latex_code(value: Any) -> str:
    text = str(value)
    return text.replace("\\", r"\textbackslash{}").replace("{", r"\{").replace("}", r"\}")


def write_model_ci_table(path: Path, stats: Mapping[str, Any]) -> None:
    lines = [
        r"\begin{table}[t]",
        r"    \centering",
        r"    \small",
        r"    \caption{Model metrics with 95\% bootstrap intervals from latent-task resampling. Each bootstrap draw resamples the 60 latent tasks and keeps both metadata views paired.}",
        r"    \label{tab:model-metrics-with-ci}",
        r"    \begin{tabular}{lrrrr}",
        r"        \toprule",
        r"        Model & $n$ & Operational escape & Belief correct & Evidence precision \\",
        r"        \midrule",
    ]
    for row in stats["model_metrics"]:
        lines.append(
            "        "
            + " & ".join(
                [
                    rf"\code{{{latex_code(row['model'])}}}",
                    str(row["n"]),
                    format_ci(row["operational_epistemic_escape"]),
                    format_ci(row["belief_correctness"]),
                    format_ci(row["evidence_precision"]),
                ]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"        \bottomrule",
            r"    \end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_condition_ci_table(path: Path, stats: Mapping[str, Any]) -> None:
    lines = [
        r"\begin{table}[t]",
        r"    \centering",
        r"    \small",
        r"    \caption{Condition-level operational epistemic escape with 95\% bootstrap intervals from latent-task resampling. Values aggregate across models and both neutral metadata views.}",
        r"    \label{tab:condition-metrics-with-ci}",
        r"    \begin{tabular}{lrr}",
        r"        \toprule",
        r"        Condition & $n$ & Operational escape \\",
        r"        \midrule",
    ]
    for row in stats["condition_operational_epistemic_escape"]:
        lines.append(
            "        "
            + " & ".join(
                [
                    rf"\code{{{latex_code(row['condition'])}}}",
                    str(row["n"]),
                    format_ci(row["operational_epistemic_escape"]),
                ]
            )
            + r" \\"
        )
    lines.extend(
        [
            r"        \bottomrule",
            r"    \end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def markdown_metric_rows(rows: Sequence[Mapping[str, Any]], key: str, metrics: Sequence[str]) -> list[Dict[str, Any]]:
    output: list[Dict[str, Any]] = []
    for row in rows:
        item: Dict[str, Any] = {key: row[key], "n": row.get("n", row.get("n_pairs", ""))}
        for metric in metrics:
            item[metric] = format_ci(row[metric])
        output.append(item)
    return output


def write_markdown_report(path: Path, stats: Mapping[str, Any]) -> None:
    model_rows = markdown_metric_rows(
        stats["model_metrics"],
        "model",
        MODEL_METRICS,
    )
    condition_rows = markdown_metric_rows(
        stats["condition_operational_epistemic_escape"],
        "condition",
        ("operational_epistemic_escape",),
    )
    delta_rows = markdown_metric_rows(
        stats["visible_hidden_paired_deltas"],
        "model",
        ("visible_minus_hidden_operational_epistemic_escape",),
    )
    gap = stats["generated_lore_belief_operational_gap"]
    method = stats["method"]
    lines = [
        "# EHA-Uncued Bootstrap Uncertainty",
        "",
        "Date: 2026-05-25",
        "",
        "## Method",
        "",
        f"- Resample unit: `{method['resample_unit']}`.",
        f"- Latent tasks: `{method['latent_task_count']}`.",
        f"- Scored rows: `{method['scored_row_count']}`.",
        f"- Bootstrap iterations: `{method['iterations']}`.",
        f"- Seed: `{method['seed']}`.",
        "- Each draw keeps the hidden and visible metadata views together inside the sampled latent task.",
        "",
        "## Model Metrics",
        "",
        *markdown_table(model_rows, ["model", "n", *MODEL_METRICS]),
        "",
        "## Condition-Level Operational Escape",
        "",
        *markdown_table(condition_rows, ["condition", "n", "operational_epistemic_escape"]),
        "",
        "## Generated-Lore Belief-To-Operational Gap",
        "",
        f"- Gap: `{format_ci(gap)}`.",
        "",
        "## Visible-Hidden Paired Deltas",
        "",
        *markdown_table(delta_rows, ["model", "n", "visible_minus_hidden_operational_epistemic_escape"]),
        "",
        "## Interpretation Boundary",
        "",
        "The intervals are task-level pilot uncertainty summaries, not population estimates for a full benchmark. Model ordering should remain descriptive unless a later, larger design supports stronger comparisons.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(
    *,
    stats: Mapping[str, Any],
    out_dir: Path,
    reports_dir: Path,
    paper_dir: Path,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_uncued_bootstrap_uncertainty.json", stats)
    write_markdown_report(out_dir / "bootstrap_uncertainty.md", stats)
    write_json(reports_dir / "eha_uncued_bootstrap_uncertainty.json", stats)
    write_markdown_report(reports_dir / "eha-uncued-bootstrap-uncertainty-2026-05-25.md", stats)
    write_model_ci_table(paper_dir / "tables/model_metrics_with_ci.tex", stats)
    write_condition_ci_table(paper_dir / "tables/condition_metrics_with_ci.tex", stats)


@app.command()
def main(
    results_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Directory containing scored pilot CSVs."),
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Dataset directory, recorded for provenance."),
    out_dir: Path = typer.Option(Path("results/reports-eha-uncued-statistics-2026-05-25"), help="Statistics output directory."),
    resample_unit: str = typer.Option("latent_task", help="Bootstrap resampling unit. Only latent_task is supported."),
    iterations: int = typer.Option(10000, help="Bootstrap iterations."),
    seed: int = typer.Option(20260525, help="Bootstrap random seed."),
    reports_dir: Path = typer.Option(Path("../reports"), help="Top-level report output directory."),
    paper_dir: Path = typer.Option(Path("../paper"), help="Paper directory for generated tables."),
) -> None:
    if resample_unit != "latent_task":
        raise typer.BadParameter("only --resample-unit latent_task is supported")
    if not dataset_dir.exists():
        raise typer.BadParameter(f"dataset directory does not exist: {dataset_dir}")
    rows = load_scored_rows(results_dir)
    stats = bootstrap_statistics(rows, iterations=iterations, seed=seed)
    stats["method"]["dataset_dir"] = str(dataset_dir)
    stats["method"]["results_dir"] = str(results_dir)
    write_outputs(stats=stats, out_dir=out_dir, reports_dir=reports_dir, paper_dir=paper_dir)
    console.print(
        f"[green]Wrote EHA-Uncued bootstrap uncertainty[/green] "
        f"for {stats['method']['latent_task_count']} latent tasks to {out_dir}"
    )


if __name__ == "__main__":
    app()
