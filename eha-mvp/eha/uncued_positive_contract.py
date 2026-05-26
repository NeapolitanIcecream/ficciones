from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import typer
from rich.console import Console

from .report import write_csv
from .schemas import write_json
from .uncued_core_claim_common import (
    DEFAULT_DATASET_DIR,
    DEFAULT_OUT_DIR,
    DEFAULT_PILOT_RUN_DIR,
    EXECUTABLE_ACTIONS,
    PRIMARY_ACTION_CUES,
    TEXT_REJECTION_CUES,
    combined_prediction_text,
    doc_roots,
    doc_sets,
    has_any_cue,
    load_model_rows,
    load_tasks_by_id,
    merged_prediction_indexes,
    metric_is_true,
    parse_actions,
    prediction_for_row,
    rejected_ids_for_row,
    selected_ids_for_row,
    support_ids_for_row,
    task_for_row,
    to_float,
)


app = typer.Typer(add_completion=False, help="Compute positive evidence-contract metrics for EHA-Uncued rows.")
console = Console()


def bool_int(value: bool) -> int:
    return 1 if value else 0


def action_executable(actions: Sequence[Mapping[str, Any]]) -> bool:
    return all(str(action.get("action", "")).strip().lower() in EXECUTABLE_ACTIONS for action in actions) if actions else False


def evidence_selection_contract(row: Mapping[str, Any], selected_ids: Sequence[str], task_sets: Mapping[str, set[str]], roots: Sequence[str]) -> bool:
    generated_selected = bool(set(selected_ids) & task_sets["generated"])
    duplicate_ok = len(roots) == len(set(roots)) and (to_float(row.get("duplicate_avoidance_rate"), 1.0) or 0.0) >= 1.0
    value_ok = (to_float(row.get("evidence_value_score"), 0.0) or 0.0) >= 0.50
    return value_ok and duplicate_ok and not generated_selected


def contract_rows(*, pilot_run_dir: Path, dataset_dir: Path) -> list[Dict[str, Any]]:
    rows = [row for row in load_model_rows(pilot_run_dir, None) if row.get("source_run") == "pilot"]
    tasks_by_id = load_tasks_by_id(dataset_dir)
    predictions = merged_prediction_indexes(pilot_run_dir)
    output: list[Dict[str, Any]] = []
    for row in rows:
        task = task_for_row(row, tasks_by_id)
        sets = doc_sets(task)
        prediction = prediction_for_row(row, predictions)
        support_ids = support_ids_for_row(row)
        selected_ids = selected_ids_for_row(row)
        rejected_ids = rejected_ids_for_row(row, prediction)
        actions = parse_actions(prediction.get("actions") or row.get("actions"))
        text = combined_prediction_text(prediction)
        polluted_support = set(support_ids) & sets["polluted"]
        clean_support = set(support_ids) & sets["clean"]
        rejected_polluted = set(rejected_ids) & sets["polluted"]
        primary_action_or_cue = has_any_cue(text, PRIMARY_ACTION_CUES) or any(str(action.get("action", "")).lower() in {"search_primary", "trace_source"} for action in actions)
        pollution_reason = has_any_cue(text, TEXT_REJECTION_CUES) or bool(rejected_polluted)
        clean_support_contract = (
            str(row.get("gold_verdict")) in {"supported", "refuted"}
            and bool(clean_support)
            and not polluted_support
            and metric_is_true(row.get("belief_correctness"))
        )
        pollutant_rejection_contract = (
            str(row.get("gold_verdict")) == "insufficient"
            and not polluted_support
            and (pollution_reason or primary_action_or_cue)
            and metric_is_true(row.get("belief_correctness"))
        )
        selection_contract = evidence_selection_contract(row, selected_ids, sets, doc_roots(task, selected_ids))
        exact_target = to_float(row.get("exact_target_rate"), None)
        required_action_recall = to_float(row.get("required_action_recall"), None)
        verification_contract = (
            action_executable(actions)
            and (
                (exact_target is not None and exact_target >= 1.0)
                or (required_action_recall is not None and required_action_recall >= 1.0)
                or (task.family != "active_verification" and primary_action_or_cue)
            )
        )
        if task.family == "packet_judgment":
            relevant = clean_support_contract if str(row.get("gold_verdict")) != "insufficient" else pollutant_rejection_contract
        elif task.family == "evidence_selection":
            relevant = selection_contract and (not polluted_support)
        else:
            relevant = verification_contract and not polluted_support and metric_is_true(row.get("belief_correctness"))
        output.append(
            {
                "task_id": row.get("task_id", ""),
                "base_task_id": row.get("base_task_id", ""),
                "view": row.get("view", ""),
                "model": row.get("model", ""),
                "family": row.get("family", task.family),
                "condition": row.get("condition", task.condition),
                "gold_verdict": row.get("gold_verdict", task.gold_verdict),
                "predicted_verdict": row.get("predicted_verdict", ""),
                "belief_correctness": row.get("belief_correctness", ""),
                "operational_epistemic_escape": row.get("operational_epistemic_escape", ""),
                "clean_support_contract": bool_int(clean_support_contract),
                "pollutant_rejection_contract": bool_int(pollutant_rejection_contract),
                "evidence_selection_contract": bool_int(selection_contract),
                "verification_contract": bool_int(verification_contract),
                "composite_evidence_hygiene_contract": bool_int(relevant),
                "final_verdict_correct": bool_int(metric_is_true(row.get("belief_correctness"))),
                "no_dirty_support": bool_int(not polluted_support),
                "clean_support_recovered": bool_int(bool(clean_support)),
                "pollutant_rejected_or_diagnosed": bool_int(pollution_reason),
                "verification_path_executable": bool_int(action_executable(actions)),
                "primary_source_action_or_cue": bool_int(primary_action_or_cue),
                "support_doc_ids": ",".join(support_ids),
                "selected_doc_ids": ",".join(selected_ids),
                "rejected_doc_ids": ",".join(rejected_ids),
                "polluted_support_doc_ids": ",".join(sorted(polluted_support)),
                "clean_support_doc_ids": ",".join(sorted(clean_support)),
            }
        )
    return output


def summarize(rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    metrics = (
        "clean_support_contract",
        "pollutant_rejection_contract",
        "evidence_selection_contract",
        "verification_contract",
        "composite_evidence_hygiene_contract",
        "final_verdict_correct",
        "no_dirty_support",
        "clean_support_recovered",
        "pollutant_rejected_or_diagnosed",
        "verification_path_executable",
    )
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("model", "")), str(row.get("condition", "")), str(row.get("family", "")))].append(row)
    output: list[Dict[str, Any]] = []
    for (model, condition, family), group in sorted(grouped.items()):
        item: Dict[str, Any] = {"model": model, "condition": condition, "family": family, "n": len(group)}
        for metric in metrics:
            item[metric] = sum(float(row.get(metric, 0.0) or 0.0) for row in group) / len(group)
        operational = sum(float(row.get("operational_epistemic_escape", 0.0) or 0.0) for row in group) / len(group)
        composite = float(item["composite_evidence_hygiene_contract"])
        item["operational_epistemic_escape"] = operational
        item["contract_minus_operational"] = composite - operational
        if composite > operational + 0.05:
            item["operational_contract_interpretation"] = "operational_too_strict"
        elif operational > composite + 0.05:
            item["operational_contract_interpretation"] = "operational_too_permissive"
        else:
            item["operational_contract_interpretation"] = "directionally_aligned"
        output.append(item)
    return output


def run_positive_contract(*, pilot_run_dir: Path, dataset_dir: Path, support_ambiguity_dir: Path, out_dir: Path) -> Dict[str, Any]:
    if not (support_ambiguity_dir / "support_ambiguity_sensitivity_rows.csv").exists():
        raise FileNotFoundError(f"missing support ambiguity rows: {support_ambiguity_dir / 'support_ambiguity_sensitivity_rows.csv'}")
    rows = contract_rows(pilot_run_dir=pilot_run_dir, dataset_dir=dataset_dir)
    summary = summarize(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "positive_evidence_contract_rows.csv", rows)
    write_csv(out_dir / "positive_evidence_contract_summary.csv", summary)
    payload = {
        "row_count": len(rows),
        "summary_group_count": len(summary),
        "mean_composite_contract": sum(float(row["composite_evidence_hygiene_contract"]) for row in rows) / len(rows) if rows else 0.0,
        "mean_operational_escape": sum(float(row.get("operational_epistemic_escape", 0.0) or 0.0) for row in rows) / len(rows) if rows else 0.0,
        "old_cued_data_used": False,
    }
    write_json(out_dir / "positive_evidence_contract_summary.json", payload)
    return payload


@app.command()
def main(
    pilot_run_dir: Path = typer.Option(DEFAULT_PILOT_RUN_DIR, help="Phase 1 pilot result directory."),
    dataset_dir: Path = typer.Option(DEFAULT_DATASET_DIR, help="Role-uncued dataset directory."),
    support_ambiguity_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Directory containing support ambiguity outputs."),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Immutable output directory."),
) -> None:
    payload = run_positive_contract(
        pilot_run_dir=pilot_run_dir,
        dataset_dir=dataset_dir,
        support_ambiguity_dir=support_ambiguity_dir,
        out_dir=out_dir,
    )
    console.print(
        "Positive evidence contracts complete: "
        f"rows={payload['row_count']} mean_composite={payload['mean_composite_contract']:.3f}."
    )
