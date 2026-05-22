from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .epistemic_frontier_main import load_run_records
from .epistemic_resilience import EpistemicRunRecord, EpistemicTask, aggregate, score_records
from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_run import base_uncued_task_id, selected_uncued_tasks, uncued_view


app = typer.Typer(add_completion=False, help="Report EHA-Uncued pilot model results.")
console = Console()

REPORT_METRICS = [
    "operational_epistemic_escape",
    "conditional_epistemic_escape",
    "parse_success",
    "belief_correctness",
    "evidence_precision",
    "clean_support_recall",
    "polluted_support_rate",
    "rejected_pollutant_rate",
    "dual_role_rate",
    "support_empty_rate",
    "uncertainty_discipline",
    "verification_action_score",
    "exact_target_rate",
    "required_action_recall",
    "cost_usd",
]

REQUIRED_TABLES = [
    "uncued_pilot_metrics_by_model.csv",
    "uncued_pilot_metrics_by_view.csv",
    "uncued_pilot_metrics_by_condition.csv",
    "uncued_pilot_metrics_by_family.csv",
    "uncued_pilot_metrics_by_model_view.csv",
    "uncued_pilot_metrics_by_model_condition.csv",
    "uncued_pilot_baselines_vs_models.csv",
    "uncued_pilot_active_verification_action_metrics.csv",
]


def read_action_gold(dataset_dir: Path) -> Dict[str, Mapping[str, Any]]:
    path = dataset_dir / "action_gold.jsonl"
    if not path.exists():
        return {}
    return {
        str(row["task_id"]): row
        for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    }


def read_baseline_aggregate() -> List[Dict[str, Any]]:
    path = Path("../reports/uncued_baseline_aggregate_pilot.csv")
    if not path.exists():
        path = Path("reports/uncued_baseline_aggregate_pilot.csv")
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def row_view(task: EpistemicTask) -> str:
    return uncued_view(task)


def action_exact_target_rate(row: Mapping[str, Any], *, action_gold: Mapping[str, Mapping[str, Any]]) -> float | str:
    if row["family"] != "active_verification":
        return ""
    base_task_id = str(row["base_task_id"])
    gold = action_gold.get(base_task_id)
    if not gold:
        return ""
    required = set(str(item) for item in gold.get("required_target_doc_ids_by_view", {}).get(str(row["view"]), []))
    if not required:
        return ""
    try:
        actions = json.loads(str(row.get("actions", "[]")))
    except json.JSONDecodeError:
        actions = []
    targets = {str(action.get("target", "")) for action in actions if isinstance(action, Mapping)}
    selected = {str(item) for item in str(row.get("selected_doc_ids", "")).split(",") if item}
    return 1.0 if (targets | selected) & required else 0.0


def enriched_score_rows(records: Sequence[EpistemicRunRecord], tasks: Sequence[EpistemicTask], *, action_gold: Mapping[str, Mapping[str, Any]]) -> List[Dict[str, Any]]:
    tasks_by_id = {task.task_id: task for task in tasks}
    rows = score_records(records, tasks)
    enriched: List[Dict[str, Any]] = []
    for row in rows:
        task = tasks_by_id[str(row["task_id"])]
        item = dict(row)
        item["base_task_id"] = base_uncued_task_id(task)
        item["view"] = row_view(task)
        item["polluted_support_rate"] = 1.0 - float(item["evidence_cleanliness"])
        item["verification_action_score"] = item["required_action_recall"] if item["required_action_recall"] != "" else ""
        item["exact_target_rate"] = action_exact_target_rate(item, action_gold=action_gold)
        enriched.append(item)
    return enriched


def aggregate_rows(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> List[Dict[str, Any]]:
    return aggregate(rows, group_keys, REPORT_METRICS)


def active_verification_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    active = [row for row in rows if row["family"] == "active_verification"]
    return aggregate(active, ["model", "view", "condition"], ["verification_action_score", "exact_target_rate", "required_action_recall", "operational_epistemic_escape", "parse_success"])


def baselines_vs_models(model_rows: Sequence[Mapping[str, Any]], baseline_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    simple = [row for row in baseline_rows if row.get("baseline") == "simple_heuristic"]
    simple_by_view = {str(row["view"]): row for row in simple}
    output: List[Dict[str, Any]] = []
    for row in model_rows:
        baseline = simple_by_view.get(str(row.get("view", "")), {})
        output.append(
            {
                "comparison": "model_vs_simple_heuristic",
                "model": row.get("model", ""),
                "view": row.get("view", ""),
                "model_n": row.get("n", ""),
                "model_operational_epistemic_escape": row.get("operational_epistemic_escape", ""),
                "simple_heuristic_operational_epistemic_escape": baseline.get("operational_epistemic_escape", ""),
                "model_evidence_precision": row.get("evidence_precision", ""),
                "simple_heuristic_evidence_precision": baseline.get("evidence_precision", ""),
                "operational_margin": float(row.get("operational_epistemic_escape", 0.0) or 0.0) - float(baseline.get("operational_epistemic_escape", 0.0) or 0.0),
                "evidence_precision_margin": float(row.get("evidence_precision", 0.0) or 0.0) - float(baseline.get("evidence_precision", 0.0) or 0.0),
            }
        )
    return output


def acceptance_diagnostics(rows: Sequence[Mapping[str, Any]], by_model_condition: Sequence[Mapping[str, Any]], baselines_vs: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    clean_rows = [row for row in by_model_condition if row["condition"] == "clean"]
    clean_pass = any(float(row["operational_epistemic_escape"]) >= 0.75 for row in clean_rows)
    polluted_by_model: Dict[str, List[Mapping[str, Any]]] = {}
    for row in by_model_condition:
        if row["condition"] != "clean":
            polluted_by_model.setdefault(str(row["model"]), []).append(row)
    polluted_perfect = [
        model
        for model, group in polluted_by_model.items()
        if group and all(float(row["operational_epistemic_escape"]) >= 1.0 for row in group)
    ]
    condition_rows = aggregate_rows(rows, ["condition"])
    by_condition = {str(row["condition"]): row for row in condition_rows}
    separation = {}
    for condition in ("generated_lore", "buried_primary"):
        row = by_condition.get(condition, {})
        separation[condition] = {
            "belief_correctness": row.get("belief_correctness", ""),
            "operational_epistemic_escape": row.get("operational_epistemic_escape", ""),
            "gap": float(row.get("belief_correctness", 0.0) or 0.0) - float(row.get("operational_epistemic_escape", 0.0) or 0.0),
        }
    positive_baseline_margins = [
        row
        for row in baselines_vs
        if float(row.get("operational_margin", 0.0) or 0.0) > 0.0
        and float(row.get("evidence_precision_margin", 0.0) or 0.0) > 0.0
    ]
    nonpositive_baseline_margins = [
        row
        for row in baselines_vs
        if not (
            float(row.get("operational_margin", 0.0) or 0.0) > 0.0
            and float(row.get("evidence_precision_margin", 0.0) or 0.0) > 0.0
        )
    ]
    baseline_margin_pass = bool(positive_baseline_margins)
    best_operational_margin = max(
        (float(row.get("operational_margin", 0.0) or 0.0) for row in baselines_vs),
        default=0.0,
    )
    best_evidence_precision_margin = max(
        (float(row.get("evidence_precision_margin", 0.0) or 0.0) for row in baselines_vs),
        default=0.0,
    )
    baseline_margin_detail = {
        "positive_model_view_count": len(positive_baseline_margins),
        "nonpositive_model_view_count": len(nonpositive_baseline_margins),
        "positive_model_views": [
            {"model": row.get("model", ""), "view": row.get("view", "")}
            for row in positive_baseline_margins
        ],
        "nonpositive_model_views": [
            {"model": row.get("model", ""), "view": row.get("view", "")}
            for row in nonpositive_baseline_margins
        ],
        "best_operational_margin": best_operational_margin,
        "best_evidence_precision_margin": best_evidence_precision_margin,
    }
    baseline_all_models_pass = all(
        float(row.get("operational_margin", 0.0) or 0.0) > 0.0 and float(row.get("evidence_precision_margin", 0.0) or 0.0) > 0.0
        for row in baselines_vs
    ) if baselines_vs else False
    return {
        "clean_operational_escape_at_least_075_for_one_model": clean_pass,
        "models_with_perfect_polluted_operational_escape": polluted_perfect,
        "no_model_perfect_across_polluted_conditions": not polluted_perfect,
        "generated_lore_buried_primary_belief_vs_hygiene_separation": separation,
        "metadata_hidden_reported_separately": True,
        "simple_heuristic_below_frontier_on_operational_and_evidence_metric": baseline_margin_pass,
        "simple_heuristic_below_all_model_views_on_operational_and_evidence_metric": baseline_all_models_pass,
        "simple_heuristic_margin_detail": baseline_margin_detail,
        "phase13_acceptance_passed": clean_pass and not polluted_perfect and baseline_margin_pass,
    }


def write_summary(path: Path, *, by_model: Sequence[Mapping[str, Any]], by_view: Sequence[Mapping[str, Any]], by_model_condition: Sequence[Mapping[str, Any]], diagnostics: Mapping[str, Any], cost_report: Mapping[str, Any]) -> None:
    lines = ["# EHA-Uncued Pilot Results", "", "## By Model", ""]
    lines.extend(markdown_table(by_model, ["model", "n", "operational_epistemic_escape", "parse_success", "belief_correctness", "evidence_precision", "clean_support_recall", "polluted_support_rate", "required_action_recall", "cost_usd"]))
    lines.extend(["", "## By View", ""])
    lines.extend(markdown_table(by_view, ["view", "n", "operational_epistemic_escape", "parse_success", "belief_correctness", "evidence_precision", "polluted_support_rate"]))
    lines.extend(["", "## By Model x Condition", ""])
    lines.extend(markdown_table(by_model_condition, ["model", "condition", "n", "operational_epistemic_escape", "parse_success", "belief_correctness", "evidence_precision", "polluted_support_rate", "required_action_recall"]))
    lines.extend(["", "## Acceptance Diagnostics", "", "```json", json.dumps(diagnostics, ensure_ascii=False, indent=2), "```"])
    lines.extend(["", "## Cost Report", "", "```json", json.dumps(cost_report, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_uncued_pilot_report(*, dataset_dir: Path, run_dir: Path, out_dir: Path) -> Dict[str, Any]:
    predictions_path = run_dir / "predictions.jsonl"
    if not predictions_path.exists():
        raise typer.BadParameter("No EHA-Uncued pilot run exists yet; reporting starts after Phase 12.")
    tasks = selected_uncued_tasks(dataset_dir, ["neutral_metadata_visible", "neutral_metadata_hidden"])
    records = load_run_records(predictions_path)
    action_gold = read_action_gold(dataset_dir)
    rows = enriched_score_rows(records, tasks, action_gold=action_gold)
    by_model = aggregate_rows(rows, ["model"])
    by_view = aggregate_rows(rows, ["view"])
    by_condition = aggregate_rows(rows, ["condition"])
    by_family = aggregate_rows(rows, ["family"])
    by_model_view = aggregate_rows(rows, ["model", "view"])
    by_model_condition = aggregate_rows(rows, ["model", "condition"])
    active_metrics = active_verification_rows(rows)
    baseline_rows = read_baseline_aggregate()
    baseline_comparison = baselines_vs_models(by_model_view, baseline_rows)
    cost_report = json.loads((run_dir / "cost_report.json").read_text(encoding="utf-8")) if (run_dir / "cost_report.json").exists() else {"aborted": False}
    diagnostics = acceptance_diagnostics(rows, by_model_condition, baseline_comparison)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "uncued_pilot_scored_predictions.csv", rows)
    write_csv(out_dir / "uncued_pilot_metrics_by_model.csv", by_model)
    write_csv(out_dir / "uncued_pilot_metrics_by_view.csv", by_view)
    write_csv(out_dir / "uncued_pilot_metrics_by_condition.csv", by_condition)
    write_csv(out_dir / "uncued_pilot_metrics_by_family.csv", by_family)
    write_csv(out_dir / "uncued_pilot_metrics_by_model_view.csv", by_model_view)
    write_csv(out_dir / "uncued_pilot_metrics_by_model_condition.csv", by_model_condition)
    write_csv(out_dir / "uncued_pilot_baselines_vs_models.csv", baseline_comparison)
    write_csv(out_dir / "uncued_pilot_active_verification_action_metrics.csv", active_metrics)
    write_json(out_dir / "uncued_pilot_acceptance_diagnostics.json", diagnostics)
    manifest = {
        "dataset_dir": str(dataset_dir),
        "run_dir": str(run_dir),
        "prediction_count": len(records),
        "scored_rows": len(rows),
        "required_tables_present": all((out_dir / table).exists() for table in REQUIRED_TABLES),
        "metrics": REPORT_METRICS,
        "acceptance": diagnostics,
    }
    write_json(out_dir / "report_manifest.json", manifest)
    write_summary(out_dir / "summary.md", by_model=by_model, by_view=by_view, by_model_condition=by_model_condition, diagnostics=diagnostics, cost_report=cost_report)
    return manifest


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Pilot dataset directory."),
    run_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Pilot run directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Report output directory."),
) -> None:
    manifest = write_uncued_pilot_report(dataset_dir=dataset_dir, run_dir=run_dir, out_dir=out_dir)
    console.print(f"[green]Wrote EHA-Uncued pilot report[/green] with {manifest['scored_rows']} scored rows to {out_dir}")
