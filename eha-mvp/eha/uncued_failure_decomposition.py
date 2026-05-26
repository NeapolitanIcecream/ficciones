from __future__ import annotations

from collections import Counter, defaultdict
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
    DEFAULT_ROBUSTNESS_RUN_DIR,
    base_task_id_for_row,
    doc_roots,
    doc_sets,
    load_model_rows,
    load_tasks_by_id,
    metric_is_true,
    parse_actions,
    selected_ids_for_row,
    source_file_hashes,
    split_doc_ids,
    support_ids_for_row,
    task_for_row,
    to_float,
)


app = typer.Typer(add_completion=False, help="Decompose EHA-Uncued operational failures into concrete components.")
console = Console()

PRIMARY_COMPONENTS = (
    "dirty_support",
    "missing_clean_support",
    "empty_support",
    "evidence_value_below_threshold",
    "duplicate_or_same_root_failure",
    "generated_lore_selected",
    "required_action_missing",
    "action_target_mismatch",
    "action_not_executable",
    "uncertainty_discipline_failure",
    "belief_incorrect",
    "parse_or_schema_failure",
    "other_unclassified",
)

EXECUTABLE_ACTIONS = {
    "open",
    "trace_source",
    "search_primary",
    "search_contradiction",
    "compare_versions",
    "abstain",
    "open_best_visible_record",
    "trace_visible_citation",
    "compare_visible_counts",
}


def numeric_metric(row: Mapping[str, Any], name: str, default: float = 0.0) -> float:
    value = to_float(row.get(name), default)
    return default if value is None else value


def classify_primary_component(row: Mapping[str, Any], task_sets: Mapping[str, set[str]], support_ids: Sequence[str], selected_ids: Sequence[str], actions: Sequence[Mapping[str, Any]], roots: Sequence[str]) -> str:
    if numeric_metric(row, "parse_success") < 1.0 or numeric_metric(row, "schema_missing") > 0.0 or numeric_metric(row, "empty_output") > 0.0:
        return "parse_or_schema_failure"
    if numeric_metric(row, "belief_correctness") < 1.0:
        return "belief_incorrect"

    polluted_support = set(support_ids) & task_sets["polluted"]
    generated_selected = bool((set(selected_ids) | set(support_ids)) & task_sets["generated"])
    if generated_selected and str(row.get("condition")) == "generated_lore":
        return "generated_lore_selected"
    if polluted_support:
        return "dirty_support"

    gold_verdict = str(row.get("gold_verdict", ""))
    if not support_ids and gold_verdict != "insufficient":
        return "empty_support"
    if gold_verdict != "insufficient" and numeric_metric(row, "clean_support_recall", 1.0) <= 0.0:
        return "missing_clean_support"

    family = str(row.get("family", ""))
    if family == "evidence_selection":
        if numeric_metric(row, "duplicate_avoidance_rate", 1.0) < 1.0 or len(roots) != len(set(roots)):
            return "duplicate_or_same_root_failure"
        if numeric_metric(row, "evidence_value_score", 1.0) < 0.50:
            return "evidence_value_below_threshold"

    if family == "active_verification":
        executable = [action for action in actions if str(action.get("action", "")).strip().lower() in EXECUTABLE_ACTIONS]
        if not executable or numeric_metric(row, "required_action_recall", 1.0) <= 0.0:
            return "required_action_missing"
        exact_target = to_float(row.get("exact_target_rate"), None)
        if exact_target is not None and exact_target <= 0.0:
            return "action_target_mismatch"
        if len(executable) != len(actions):
            return "action_not_executable"

    if numeric_metric(row, "uncertainty_discipline", 1.0) < 1.0:
        return "uncertainty_discipline_failure"
    if numeric_metric(row, "evidence_value_score", 1.0) < 0.50:
        return "evidence_value_below_threshold"
    return "other_unclassified"


def decompose_rows(rows: Sequence[Mapping[str, Any]], *, dataset_dir: Path) -> list[Dict[str, Any]]:
    tasks_by_id = load_tasks_by_id(dataset_dir)
    output: list[Dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        task = task_for_row(row, tasks_by_id)
        sets = doc_sets(task)
        support_ids = support_ids_for_row(row)
        selected_ids = selected_ids_for_row(row)
        actions = parse_actions(row.get("actions"))
        selected_roots = doc_roots(task, selected_ids)
        polluted_support = set(support_ids) & sets["polluted"]
        clean_support = set(support_ids) & sets["clean"]
        generated_selected = bool((set(selected_ids) | set(support_ids)) & sets["generated"])
        operational_failed = numeric_metric(row, "operational_epistemic_escape") < 1.0
        primary_component = classify_primary_component(row, sets, support_ids, selected_ids, actions, selected_roots) if operational_failed else "none"
        action_targets = {str(action.get("target", "")) for action in actions}
        action_text = " ".join(str(action.get(key, "")) for action in actions for key in ("action", "target", "rationale")).lower()
        output.append(
            {
                "row_id": index,
                "source_run": row.get("source_run", "pilot"),
                "variant": row.get("variant", ""),
                "task_id": row.get("task_id", ""),
                "base_task_id": base_task_id_for_row(row),
                "view": row.get("view", ""),
                "model": row.get("model", ""),
                "family": row.get("family", task.family),
                "condition": row.get("condition", task.condition),
                "gold_verdict": row.get("gold_verdict", task.gold_verdict),
                "predicted_verdict": row.get("predicted_verdict", ""),
                "parse_success": row.get("parse_success", ""),
                "belief_correctness": row.get("belief_correctness", ""),
                "operational_epistemic_escape": row.get("operational_epistemic_escape", ""),
                "primary_failure_component": primary_component,
                "belief_correct_but_operational_failed": int(metric_is_true(row.get("belief_correctness")) and operational_failed),
                "insufficient_verdict": int(str(row.get("predicted_verdict", "")).lower() == "insufficient"),
                "supported_or_refuted_verdict": int(str(row.get("predicted_verdict", "")).lower() in {"supported", "refuted"}),
                "polluted_support_present": int(bool(polluted_support)),
                "clean_support_present": int(bool(clean_support)),
                "all_support_polluted": int(bool(support_ids) and set(support_ids) <= sets["polluted"]),
                "support_mentions_primary_source": int(bool(clean_support)),
                "verification_action_present": int(bool(actions)),
                "verification_action_targets_primary": int(bool(action_targets & sets["clean"]) or any(cue in action_text for cue in ("primary", "official", "ledger", "source repository", "original notice", "event archive"))),
                "robustness_variant_row": int(row.get("source_run") == "robustness"),
                "generated_lore_selected": int(generated_selected),
                "duplicate_root_count": len(selected_roots) - len(set(selected_roots)),
                "support_doc_ids": ",".join(support_ids),
                "selected_doc_ids": ",".join(selected_ids),
                "polluted_support_doc_ids": ",".join(sorted(polluted_support)),
                "clean_support_doc_ids": ",".join(sorted(clean_support)),
            }
        )
    return output


def summarize_components(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> list[Dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["primary_failure_component"] == "none":
            continue
        grouped[tuple(str(row.get(key, "")) for key in group_keys)].append(row)
    output: list[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        counts = Counter(str(row["primary_failure_component"]) for row in group)
        item: Dict[str, Any] = {group_key: key[index] for index, group_key in enumerate(group_keys)}
        item["n_operational_failures"] = len(group)
        for component in PRIMARY_COMPONENTS:
            item[component] = counts.get(component, 0)
            item[f"{component}_rate"] = counts.get(component, 0) / len(group) if group else 0.0
        output.append(item)
    return output


def run_failure_decomposition(*, pilot_run_dir: Path, robustness_run_dir: Path, dataset_dir: Path, out_dir: Path) -> Dict[str, Any]:
    rows = load_model_rows(pilot_run_dir, robustness_run_dir)
    decomposed = decompose_rows(rows, dataset_dir=dataset_dir)
    failures = [row for row in decomposed if row["primary_failure_component"] != "none"]
    gap_rows = [row for row in decomposed if int(row["belief_correct_but_operational_failed"]) == 1]
    by_model = summarize_components(decomposed, ["source_run", "model"])
    by_condition_family = summarize_components(decomposed, ["source_run", "condition", "family"])
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "failure_decomposition_rows.csv", decomposed)
    write_csv(out_dir / "failure_decomposition_by_model.csv", by_model)
    write_csv(out_dir / "failure_decomposition_by_condition_family.csv", by_condition_family)
    write_csv(out_dir / "belief_correct_operational_failure_rows.csv", gap_rows)
    hashes = source_file_hashes(dataset_dir, pilot_run_dir, robustness_run_dir)
    write_json(out_dir / "source_file_hashes.json", hashes)
    unclassified = sum(1 for row in failures if row["primary_failure_component"] == "other_unclassified")
    payload = {
        "row_count": len(decomposed),
        "operational_failure_count": len(failures),
        "belief_correct_operational_failure_count": len(gap_rows),
        "other_unclassified_count": unclassified,
        "other_unclassified_rate": unclassified / len(failures) if failures else 0.0,
        "one_primary_component_per_operational_failure": all(row["primary_failure_component"] in PRIMARY_COMPONENTS for row in failures),
        "old_cued_data_used": False,
        "source_hash_count": len(hashes),
    }
    write_json(out_dir / "failure_decomposition_summary.json", payload)
    return payload


@app.command()
def main(
    pilot_run_dir: Path = typer.Option(DEFAULT_PILOT_RUN_DIR, help="Phase 1 pilot result directory."),
    robustness_run_dir: Path = typer.Option(DEFAULT_ROBUSTNESS_RUN_DIR, help="Phase 1.x robustness result directory."),
    dataset_dir: Path = typer.Option(DEFAULT_DATASET_DIR, help="Role-uncued dataset directory."),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Immutable output directory."),
) -> None:
    payload = run_failure_decomposition(
        pilot_run_dir=pilot_run_dir,
        robustness_run_dir=robustness_run_dir,
        dataset_dir=dataset_dir,
        out_dir=out_dir,
    )
    console.print(
        "Failure decomposition complete: "
        f"rows={payload['row_count']} failures={payload['operational_failure_count']} "
        f"gap_rows={payload['belief_correct_operational_failure_count']}."
    )
