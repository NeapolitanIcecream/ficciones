from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import typer
from rich.console import Console

from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_core_claim_common import (
    DEFAULT_DATASET_DIR,
    DEFAULT_OUT_DIR,
    DEFAULT_PILOT_RUN_DIR,
    TEXT_REJECTION_CUES,
    PRIMARY_ACTION_CUES,
    combined_prediction_text,
    doc_sets,
    has_any_cue,
    load_model_rows,
    load_tasks_by_id,
    merged_prediction_indexes,
    metric_is_true,
    parse_actions,
    prediction_for_row,
    read_csv_rows,
    rejected_ids_for_row,
    selected_ids_for_row,
    split_doc_ids,
    support_ids_for_row,
    task_for_row,
    to_float,
)


app = typer.Typer(add_completion=False, help="Run support-field ambiguity sensitivity analysis for EHA-Uncued rows.")
console = Console()


def status_from_score(score: float) -> str:
    if score >= 0.999:
        return "pass"
    if score > 0.0:
        return "partial"
    return "fail"


def row_action_primary_credit(prediction: Mapping[str, Any]) -> bool:
    text = combined_prediction_text(prediction)
    if has_any_cue(text, PRIMARY_ACTION_CUES):
        return True
    for action in parse_actions(prediction.get("actions", [])):
        action_name = str(action.get("action", "")).lower()
        if action_name in {"search_primary", "trace_source"}:
            return True
    return False


def support_ambiguity_rows(*, pilot_run_dir: Path, dataset_dir: Path) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
    rows = [row for row in load_model_rows(pilot_run_dir, None) if row.get("source_run") == "pilot"]
    tasks_by_id = load_tasks_by_id(dataset_dir)
    predictions = merged_prediction_indexes(pilot_run_dir)
    candidate_rows: list[Dict[str, Any]] = []
    sensitivity_rows: list[Dict[str, Any]] = []
    for row in rows:
        task = task_for_row(row, tasks_by_id)
        sets = doc_sets(task)
        support_ids = support_ids_for_row(row)
        polluted_support = sorted(set(support_ids) & sets["polluted"])
        if not polluted_support:
            continue
        prediction = prediction_for_row(row, predictions)
        rejected_ids = rejected_ids_for_row(row, prediction)
        text = combined_prediction_text(prediction)
        rejection_cue = has_any_cue(text, TEXT_REJECTION_CUES)
        explicit_rejected_pollution = bool(set(rejected_ids) & set(polluted_support))
        primary_action_credit = row_action_primary_credit(prediction)
        is_target_candidate = (
            str(row.get("condition")) == "generated_lore"
            and str(row.get("gold_verdict")) == "insufficient"
            and metric_is_true(row.get("belief_correctness"))
            and to_float(row.get("operational_epistemic_escape"), 0.0) == 0.0
        )
        candidate = {
            "task_id": row.get("task_id", ""),
            "base_task_id": row.get("base_task_id", ""),
            "view": row.get("view", ""),
            "model": row.get("model", ""),
            "family": row.get("family", ""),
            "condition": row.get("condition", ""),
            "gold_verdict": row.get("gold_verdict", ""),
            "predicted_verdict": row.get("predicted_verdict", ""),
            "belief_correctness": row.get("belief_correctness", ""),
            "operational_epistemic_escape": row.get("operational_epistemic_escape", ""),
            "support_doc_ids": ",".join(support_ids),
            "polluted_support_doc_ids": ",".join(polluted_support),
            "selected_doc_ids": ",".join(selected_ids_for_row(row)),
            "rejected_doc_ids": ",".join(rejected_ids),
            "rejection_cue_present": int(rejection_cue),
            "explicit_polluted_rejection": int(explicit_rejected_pollution),
            "primary_source_action_or_cue": int(primary_action_credit),
            "target_candidate": int(is_target_candidate),
        }
        if is_target_candidate:
            candidate_rows.append(candidate)

        strict_score = to_float(row.get("operational_epistemic_escape"), 0.0) or 0.0
        prose_score = 1.0 if metric_is_true(row.get("belief_correctness")) and (rejection_cue or explicit_rejected_pollution) else strict_score
        action_score = prose_score
        if prose_score >= 1.0:
            action_score = 1.0
        elif metric_is_true(row.get("belief_correctness")) and primary_action_credit and (rejection_cue or explicit_rejected_pollution):
            action_score = 0.5
        sensitivity_rows.append(
            {
                **candidate,
                "strict_current_score": strict_score,
                "strict_current_status": status_from_score(strict_score),
                "prose_aware_rejected_score": prose_score,
                "prose_aware_rejected_status": status_from_score(prose_score),
                "action_aware_partial_score": action_score,
                "action_aware_partial_status": status_from_score(action_score),
                "classification": (
                    "likely_schema_allocation_artifact"
                    if prose_score >= 1.0
                    else "borderline"
                    if action_score > 0.0
                    else "strict_true_failure"
                ),
            }
        )
    return candidate_rows, sensitivity_rows


def summarize_sensitivity(rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("condition", "")), str(row.get("family", "")), str(row.get("model", "")))].append(row)
    output: list[Dict[str, Any]] = []
    for (condition, family, model), group in sorted(grouped.items()):
        target = [row for row in group if str(row.get("target_candidate")) == "1" or row.get("target_candidate") == 1]
        for source_group, label in ((group, "all_polluted_support"), (target, "target_generated_lore_gap")):
            if not source_group:
                continue
            item: Dict[str, Any] = {"condition": condition, "family": family, "model": model, "row_class": label, "n": len(source_group)}
            for metric in ("strict_current_score", "prose_aware_rejected_score", "action_aware_partial_score"):
                item[metric] = sum(float(row.get(metric, 0.0) or 0.0) for row in source_group) / len(source_group)
            item["strict_to_prose_pass_count"] = sum(
                1
                for row in source_group
                if str(row.get("strict_current_status")) != "pass" and str(row.get("prose_aware_rejected_status")) == "pass"
            )
            item["strict_to_action_partial_or_pass_count"] = sum(
                1
                for row in source_group
                if str(row.get("strict_current_status")) != "pass" and str(row.get("action_aware_partial_status")) in {"partial", "pass"}
            )
            output.append(item)
    return output


def example_lines(rows: Sequence[Mapping[str, Any]], *, pilot_run_dir: Path) -> list[str]:
    predictions = merged_prediction_indexes(pilot_run_dir)
    by_class: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_class[str(row.get("classification", ""))].append(row)
    lines = [
        "# Qualitative Failure Examples",
        "",
        "These are deterministic local audit examples for scorer/schema interpretation. They are not independent human validation.",
        "",
    ]
    labels = (
        ("strict_true_failure", "Strict True Failures"),
        ("likely_schema_allocation_artifact", "Likely Schema-Allocation Artifacts"),
        ("borderline", "Borderline Rows"),
    )
    for class_name, heading in labels:
        lines.extend([f"## {heading}", ""])
        selected = by_class.get(class_name, [])[:4]
        if not selected:
            lines.extend(["_No matching rows._", ""])
            continue
        for row in selected:
            prediction = prediction_for_row(row, predictions)
            text = " ".join(str(prediction.get(field, "")) for field in ("answer", "evidence_environment_assessment", "evidence_notes")).strip()
            if len(text) > 360:
                text = text[:357].rstrip() + "..."
            lines.extend(
                [
                    f"### {row.get('task_id')} / {row.get('model')}",
                    "",
                    f"- Condition/family: `{row.get('condition')}` / `{row.get('family')}`",
                    f"- Polluted support: `{row.get('polluted_support_doc_ids')}`",
                    f"- Rejected docs: `{row.get('rejected_doc_ids') or '-'}`",
                    f"- Sensitivity: strict=`{row.get('strict_current_status')}`, prose=`{row.get('prose_aware_rejected_status')}`, action=`{row.get('action_aware_partial_status')}`",
                    f"- Local audit note: {text or 'No prose available in prediction payload.'}",
                    "",
                ]
            )
    return lines


def run_support_ambiguity(*, pilot_run_dir: Path, dataset_dir: Path, decomposition_dir: Path, out_dir: Path) -> Dict[str, Any]:
    if not (decomposition_dir / "failure_decomposition_rows.csv").exists():
        raise FileNotFoundError(f"missing failure decomposition rows: {decomposition_dir / 'failure_decomposition_rows.csv'}")
    candidate_rows, sensitivity_rows = support_ambiguity_rows(pilot_run_dir=pilot_run_dir, dataset_dir=dataset_dir)
    summary = summarize_sensitivity(sensitivity_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "support_ambiguity_candidate_rows.csv", candidate_rows)
    write_csv(out_dir / "support_ambiguity_sensitivity_rows.csv", sensitivity_rows)
    write_csv(out_dir / "support_ambiguity_sensitivity_summary.csv", summary)
    (out_dir / "qualitative_failure_examples.md").write_text("\n".join(example_lines(sensitivity_rows, pilot_run_dir=pilot_run_dir)), encoding="utf-8")
    target = [row for row in sensitivity_rows if str(row.get("target_candidate")) == "1" or row.get("target_candidate") == 1]
    strict_failures = [row for row in target if str(row.get("strict_current_status")) == "fail"]
    prose_pass = [row for row in strict_failures if str(row.get("prose_aware_rejected_status")) == "pass"]
    payload = {
        "polluted_support_row_count": len(sensitivity_rows),
        "target_candidate_count": len(candidate_rows),
        "target_strict_failure_count": len(strict_failures),
        "target_strict_failures_becoming_prose_pass_count": len(prose_pass),
        "target_gap_closed_share": len(prose_pass) / len(strict_failures) if strict_failures else 0.0,
        "interpretation": (
            "gap_mostly_support_field_artifact"
            if strict_failures and len(prose_pass) / len(strict_failures) > 0.5
            else "gap_survives_ambiguity_rescoring"
            if strict_failures
            else "no_target_strict_gap_rows"
        ),
        "subjectivity_note": "prose_aware_rejected is deterministic keyword-based sensitivity, not a new main scorer.",
    }
    write_json(out_dir / "support_ambiguity_summary.json", payload)
    return payload


@app.command()
def main(
    pilot_run_dir: Path = typer.Option(DEFAULT_PILOT_RUN_DIR, help="Phase 1 pilot result directory."),
    dataset_dir: Path = typer.Option(DEFAULT_DATASET_DIR, help="Role-uncued dataset directory."),
    decomposition_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Directory containing failure decomposition outputs."),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Immutable output directory."),
) -> None:
    payload = run_support_ambiguity(
        pilot_run_dir=pilot_run_dir,
        dataset_dir=dataset_dir,
        decomposition_dir=decomposition_dir,
        out_dir=out_dir,
    )
    console.print(
        "Support ambiguity complete: "
        f"target_candidates={payload['target_candidate_count']} "
        f"gap_closed_share={payload['target_gap_closed_share']:.3f}."
    )
