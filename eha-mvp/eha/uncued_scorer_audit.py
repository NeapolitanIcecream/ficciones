from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .epistemic_frontier_main import load_run_records
from .epistemic_resilience import EpistemicTask
from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_report import read_action_gold
from .uncued_run import base_uncued_task_id, selected_uncued_tasks


app = typer.Typer(add_completion=False, help="Generate a balanced manual scorer-audit sample for EHA-Uncued.")
console = Console()

AUDIT_METRICS = [
    "belief_correctness",
    "evidence_precision",
    "clean_support_recall",
    "polluted_support_rate",
    "uncertainty_discipline",
    "required_action_recall",
    "operational_epistemic_escape",
]


def load_scored_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _row_sort_key(row: Mapping[str, str]) -> tuple[str, str, str, str, str]:
    return (
        str(row["model"]),
        str(row["view"]),
        str(row["condition"]),
        str(row["family"]),
        str(row["task_id"]),
    )


def _target_quota(values: Sequence[str], sample_size: int) -> Dict[str, int]:
    unique = sorted(set(values))
    base = sample_size // len(unique)
    remainder = sample_size % len(unique)
    return {value: base + (1 if index < remainder else 0) for index, value in enumerate(unique)}


def _under_quota(value: str, counts: Counter[str], quotas: Mapping[str, int]) -> bool:
    return counts[value] < quotas.get(value, 0)


def select_scorer_audit_sample(rows: Sequence[Mapping[str, str]], sample_size: int = 40) -> List[Dict[str, str]]:
    if sample_size < 30:
        # Tests may ask for smaller samples; production Phase 14 uses the runbook minimum.
        sample_size = int(sample_size)
    if len(rows) < sample_size:
        raise ValueError(f"not enough rows for scorer audit: need {sample_size}, found {len(rows)}")

    models = sorted(set(str(row["model"]) for row in rows))
    conditions = sorted(set(str(row["condition"]) for row in rows))
    views = sorted(set(str(row["view"]) for row in rows))
    if sample_size == len(models) * len(conditions) * len(views):
        return _select_model_condition_view_grid(rows, models=models, conditions=conditions, views=views, sample_size=sample_size)
    model_quota = _target_quota([str(row["model"]) for row in rows], sample_size)
    view_quota = _target_quota([str(row["view"]) for row in rows], sample_size)
    condition_quota = _target_quota([str(row["condition"]) for row in rows], sample_size)
    family_quota = _target_quota([str(row["family"]) for row in rows], sample_size)
    escape_quota = {"0.0": sample_size // 2, "1.0": sample_size - sample_size // 2}
    selected: List[Dict[str, str]] = []
    counts = {name: Counter() for name in ("model", "view", "condition", "family", "escape")}

    def add(row: Mapping[str, str]) -> None:
        item = dict(row)
        selected.append(item)
        counts["model"][str(row["model"])] += 1
        counts["view"][str(row["view"])] += 1
        counts["condition"][str(row["condition"])] += 1
        counts["family"][str(row["family"])] += 1
        counts["escape"][str(float(row["operational_epistemic_escape"]))] += 1

    candidates = sorted(rows, key=_row_sort_key)
    for row in candidates:
        if len(selected) >= sample_size:
            break
        escape_key = str(float(row["operational_epistemic_escape"]))
        if (
            _under_quota(str(row["model"]), counts["model"], model_quota)
            and _under_quota(str(row["view"]), counts["view"], view_quota)
            and _under_quota(str(row["condition"]), counts["condition"], condition_quota)
            and _under_quota(str(row["family"]), counts["family"], family_quota)
            and _under_quota(escape_key, counts["escape"], escape_quota)
        ):
            add(row)

    for row in candidates:
        if len(selected) >= sample_size:
            break
        key = (row["model"], row["task_id"], row["view"])
        if any((item["model"], item["task_id"], item["view"]) == key for item in selected):
            continue
        add(row)
    return selected


def _proportional_quota(values: Sequence[str], sample_size: int) -> Dict[str, int]:
    counts = Counter(values)
    total = sum(counts.values())
    raw = {value: sample_size * count / total for value, count in counts.items()}
    quotas = {value: int(raw[value]) for value in counts}
    remainder = sample_size - sum(quotas.values())
    for value, _fraction in sorted(((value, raw[value] - quotas[value]) for value in counts), key=lambda item: (-item[1], item[0]))[:remainder]:
        quotas[value] += 1
    return dict(sorted(quotas.items()))


def _select_model_condition_view_grid(
    rows: Sequence[Mapping[str, str]],
    *,
    models: Sequence[str],
    conditions: Sequence[str],
    views: Sequence[str],
    sample_size: int,
) -> List[Dict[str, str]]:
    family_quota = _proportional_quota([str(row["family"]) for row in rows], sample_size)
    escape_quota = {"0.0": sample_size // 2, "1.0": sample_size - sample_size // 2}
    family_counts: Counter[str] = Counter()
    escape_counts: Counter[str] = Counter()
    selected: List[Dict[str, str]] = []
    used_keys: set[tuple[str, str, str]] = set()
    rows_by_cell: Dict[tuple[str, str, str], List[Mapping[str, str]]] = {}
    for row in rows:
        rows_by_cell.setdefault((str(row["model"]), str(row["condition"]), str(row["view"])), []).append(row)

    for model in models:
        for condition in conditions:
            for view in views:
                cell = sorted(rows_by_cell.get((model, condition, view), []), key=_row_sort_key)
                if not cell:
                    raise ValueError(f"missing scorer-audit cell: model={model} condition={condition} view={view}")

                def score(row: Mapping[str, str]) -> tuple[int, int, str]:
                    family = str(row["family"])
                    escape_key = str(float(row["operational_epistemic_escape"]))
                    family_deficit = family_quota.get(family, 0) - family_counts[family]
                    escape_deficit = escape_quota.get(escape_key, 0) - escape_counts[escape_key]
                    return (family_deficit, escape_deficit, str(row["task_id"]))

                candidate = max(
                    (
                        row
                        for row in cell
                        if (str(row["model"]), str(row["task_id"]), str(row["view"])) not in used_keys
                    ),
                    key=score,
                )
                selected.append(dict(candidate))
                used_keys.add((str(candidate["model"]), str(candidate["task_id"]), str(candidate["view"])))
                family_counts[str(candidate["family"])] += 1
                escape_counts[str(float(candidate["operational_epistemic_escape"]))] += 1
    return selected


def _float_or_blank(value: Any) -> float | str:
    if value == "" or value is None:
        return ""
    return float(value)


def _near_equal(left: float | str, right: float | str) -> bool:
    if left == "" or right == "":
        return left == right
    return abs(float(left) - float(right)) < 1e-9


def _parse_actions(row: Mapping[str, str]) -> List[Mapping[str, Any]]:
    try:
        payload = json.loads(str(row.get("actions", "[]") or "[]"))
    except json.JSONDecodeError:
        return []
    return [action for action in payload if isinstance(action, Mapping)]


def _secondary_manual_scores(row: Mapping[str, str], task: EpistemicTask, action_gold: Mapping[str, Mapping[str, Any]]) -> Dict[str, float | str]:
    supporting = [item for item in str(row.get("supporting_evidence", "")).split(",") if item]
    selected = [item for item in str(row.get("selected_doc_ids", "")).split(",") if item]
    pollutant_doc_ids = set(task.contaminant_doc_ids + task.generated_doc_ids + task.stale_doc_ids)
    clean_supporting = [doc_id for doc_id in supporting if doc_id in task.primary_doc_ids and doc_id not in pollutant_doc_ids]
    support_dirty = bool(set(supporting) & pollutant_doc_ids)
    belief_correctness = 1.0 if row["predicted_verdict"] == row["gold_verdict"] else 0.0
    evidence_cleanliness = 0.0 if support_dirty else 1.0
    evidence_precision = len(clean_supporting) / len(supporting) if supporting else ""
    clean_support_recall = len(set(clean_supporting)) / len(task.primary_doc_ids) if task.primary_doc_ids else ""
    polluted_support_rate = 1.0 - evidence_cleanliness
    uncertainty_discipline = (
        row["predicted_verdict"] == "insufficient"
        if row["gold_verdict"] == "insufficient"
        else row["predicted_verdict"] != "insufficient"
    )

    primary_selected = bool(set(selected) & set(task.primary_doc_ids))
    generated_selected = bool(set(selected) & set(task.generated_doc_ids))
    selected_docs = {doc.doc_id: doc for doc in task.documents}
    value_score = sum(selected_docs[doc_id].value_score for doc_id in selected if doc_id in selected_docs) / max(1, task.max_selected_docs)
    duplicate_ok = 1.0 if len(selected) == len(set(selected)) else 0.0

    actions = _parse_actions(row)
    primary_action = any(action.get("action") == "search_primary" or str(action.get("target", "")) in task.primary_doc_ids for action in actions)
    contradiction_action = any(action.get("action") in {"search_contradiction", "compare_versions"} or str(action.get("target", "")) in task.contradiction_doc_ids for action in actions)
    generated_trace_action = any(action.get("action") == "trace_source" and (not action.get("target") or str(action.get("target", "")) in task.generated_doc_ids) for action in actions)
    required_actions: List[bool] = []
    if task.family == "active_verification":
        if task.primary_doc_ids:
            required_actions.append(primary_action)
        if task.condition in {"false_consensus", "buried_primary", "conflicting_evidence"}:
            required_actions.append(contradiction_action)
        if task.condition == "generated_lore":
            required_actions.append(generated_trace_action)
    required_action_recall: float | str = sum(1.0 if item else 0.0 for item in required_actions) / len(required_actions) if required_actions else ""

    if task.family == "evidence_selection":
        epistemic_escape = value_score >= 0.50 and duplicate_ok == 1.0 and not generated_selected
    elif task.family == "active_verification":
        wants_primary = bool(task.primary_doc_ids)
        action_ok = (
            (primary_action or not wants_primary)
            and (contradiction_action or task.condition not in {"false_consensus", "buried_primary", "conflicting_evidence"})
            and (generated_trace_action or task.condition != "generated_lore")
        )
        epistemic_escape = belief_correctness == 1.0 and evidence_cleanliness == 1.0 and bool(uncertainty_discipline) and action_ok
    else:
        epistemic_escape = belief_correctness == 1.0 and evidence_cleanliness == 1.0 and bool(uncertainty_discipline)

    # The action_gold lookup keeps the manual audit tied to exact target data even
    # when a row's automatic metric is blank outside active-verification tasks.
    exact_target_rate = ""
    if task.family == "active_verification":
        gold = action_gold.get(base_uncued_task_id(task), {})
        required = set(gold.get("required_target_doc_ids_by_view", {}).get(str(row["view"]), []))
        action_targets = {str(action.get("target", "")) for action in actions}
        exact_target_rate = 1.0 if required and (action_targets | set(selected)) & required else 0.0

    return {
        "belief_correctness": belief_correctness,
        "evidence_precision": evidence_precision,
        "clean_support_recall": clean_support_recall,
        "polluted_support_rate": polluted_support_rate,
        "uncertainty_discipline": 1.0 if uncertainty_discipline else 0.0,
        "required_action_recall": required_action_recall,
        "operational_epistemic_escape": 1.0 if float(row.get("parse_success", 0.0) or 0.0) == 1.0 and epistemic_escape else 0.0,
        "exact_target_rate": exact_target_rate,
    }


def scorer_audit(
    sample: Sequence[Mapping[str, str]],
    *,
    dataset_dir: Path,
    rejected_evidence_by_key: Mapping[tuple[str, str], Sequence[str]] | None = None,
) -> List[Dict[str, Any]]:
    tasks = selected_uncued_tasks(dataset_dir, ["neutral_metadata_visible", "neutral_metadata_hidden"])
    tasks_by_id = {task.task_id: task for task in tasks}
    action_gold = read_action_gold(dataset_dir)
    audited: List[Dict[str, Any]] = []
    for index, row in enumerate(sample, start=1):
        task = tasks_by_id[str(row["task_id"])]
        manual = _secondary_manual_scores(row, task, action_gold)
        metric_agreements = {}
        disagreement_reasons = []
        for metric in AUDIT_METRICS:
            automatic = _float_or_blank(row.get(metric, ""))
            agrees = _near_equal(automatic, manual.get(metric, ""))
            metric_agreements[metric] = "yes" if agrees else "no"
            if not agrees:
                disagreement_reasons.append(f"{metric}: automatic={automatic} manual={manual.get(metric, '')}")
        fix_needed = "yes" if disagreement_reasons else "no"
        audited.append(
            {
                "row_id": f"scorer_audit_{index:03d}",
                "task_id": row["task_id"],
                "base_task_id": row.get("base_task_id", ""),
                "model": row["model"],
                "view": row["view"],
                "condition": row["condition"],
                "family": row["family"],
                "gold_verdict": row["gold_verdict"],
                "predicted_verdict": row["predicted_verdict"],
                "selected_evidence": row.get("selected_doc_ids", ""),
                "supporting_evidence": row.get("supporting_evidence", ""),
                "rejected_evidence": ",".join(
                    rejected_evidence_by_key.get((str(row["model"]), str(row["task_id"])), [])
                    if rejected_evidence_by_key is not None
                    else str(row.get("rejected_evidence", "")).split(",")
                ),
                "actions": row.get("actions", "[]"),
                "automatic_scores": json.dumps({metric: row.get(metric, "") for metric in AUDIT_METRICS}, ensure_ascii=False, sort_keys=True),
                "human_belief_correctness_agrees": metric_agreements["belief_correctness"],
                "human_evidence_precision_agrees": metric_agreements["evidence_precision"],
                "human_clean_support_recall_agrees": metric_agreements["clean_support_recall"],
                "human_polluted_support_rate_agrees": metric_agreements["polluted_support_rate"],
                "human_uncertainty_discipline_agrees": metric_agreements["uncertainty_discipline"],
                "human_required_action_recall_agrees": metric_agreements["required_action_recall"],
                "human_operational_escape_agrees": metric_agreements["operational_epistemic_escape"],
                "disagreement_reason": "; ".join(disagreement_reasons),
                "scorer_fix_needed": fix_needed,
            }
        )
    return audited


def scorer_audit_summary(audited: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    disagreement_rows = [row for row in audited if row.get("scorer_fix_needed") == "yes"]
    by_model = Counter(str(row["model"]) for row in audited)
    by_view = Counter(str(row["view"]) for row in audited)
    by_condition = Counter(str(row["condition"]) for row in audited)
    by_family = Counter(str(row["family"]) for row in audited)
    by_escape = Counter(json.loads(str(row["automatic_scores"])).get("operational_epistemic_escape", "") for row in audited)
    return {
        "review_mode": "local_codex_assisted_manual_scorer_audit",
        "independent_human_review": False,
        "reviewed_rows": len(audited),
        "scorer_disagreement_count": len(disagreement_rows),
        "scorer_disagreement_rate": len(disagreement_rows) / len(audited) if audited else 0.0,
        "systematic_scorer_bug_found": bool(disagreement_rows),
        "rescoring_required": bool(disagreement_rows),
        "by_model": dict(sorted(by_model.items())),
        "by_view": dict(sorted(by_view.items())),
        "by_condition": dict(sorted(by_condition.items())),
        "by_family": dict(sorted(by_family.items())),
        "by_operational_escape": dict(sorted(by_escape.items())),
        "caveat": "This is a local Codex-assisted scorer audit, not an independent human-subject review.",
    }


def write_scorer_audit_report(path: Path, *, summary: Mapping[str, Any]) -> None:
    lines = [
        "# EHA-Uncued Phase 14 Scorer Audit",
        "",
        "Date: 2026-05-22",
        "",
        f"Reviewed rows: {summary['reviewed_rows']}",
        f"Scorer disagreement rate: {summary['scorer_disagreement_rate']:.3f}",
        f"Systematic scorer bug found: {str(summary['systematic_scorer_bug_found']).lower()}",
        "",
        "This audit uses a balanced 40-row sample from the Phase 13 scored predictions. It independently recomputes the audited metrics from scorer-visible gold fields and model outputs. The audit is local and Codex-assisted; it is not an independent human-subject review.",
        "",
        "## Balance",
        "",
    ]
    balance_rows = [
        {"axis": "model", "counts": json.dumps(summary["by_model"], sort_keys=True)},
        {"axis": "view", "counts": json.dumps(summary["by_view"], sort_keys=True)},
        {"axis": "condition", "counts": json.dumps(summary["by_condition"], sort_keys=True)},
        {"axis": "family", "counts": json.dumps(summary["by_family"], sort_keys=True)},
        {"axis": "operational_escape", "counts": json.dumps(summary["by_operational_escape"], sort_keys=True)},
    ]
    lines.extend(markdown_table(balance_rows, ["axis", "counts"]))
    lines.extend(["", "## Summary JSON", "", "```json", json.dumps(summary, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Pilot dataset directory."),
    run_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Pilot report/run directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Reports output directory."),
    sample_size: int = typer.Option(40, help="Scorer-audit sample size; Phase 14 requires 30-50 rows."),
) -> None:
    if not 30 <= sample_size <= 50:
        raise typer.BadParameter("sample_size must be between 30 and 50 for Phase 14")
    scored_path = run_dir / "uncued_pilot_scored_predictions.csv"
    rows = load_scored_rows(scored_path)
    sample = select_scorer_audit_sample(rows, sample_size=sample_size)
    records = load_run_records(run_dir / "predictions.jsonl")
    rejected_evidence_by_key = {
        (record.model, record.task_id): record.prediction.rejected_evidence
        for record in records
    }
    audited = scorer_audit(sample, dataset_dir=dataset_dir, rejected_evidence_by_key=rejected_evidence_by_key)
    summary = scorer_audit_summary(audited)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "uncued_scorer_audit_rows.csv", audited)
    write_json(out_dir / "eha_uncued_scorer_audit.json", summary)
    write_scorer_audit_report(out_dir / "eha-uncued-scorer-audit-2026-05-22.md", summary=summary)
    write_csv(run_dir / "uncued_scorer_audit_rows.csv", audited)
    write_json(run_dir / "uncued_scorer_audit_summary.json", summary)
    console.print(f"[green]Wrote EHA-Uncued scorer audit[/green] with {len(audited)} rows to {out_dir}")
