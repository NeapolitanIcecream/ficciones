from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .phase2_scoring import extract_doc_ids_from_tool_result, hidden_labels_leaked
from .phase2r_scoring import high_pressure_task_ids
from .scoring import expected_calibration_error, unique
from .schemas import GoldDocument, Phase2SRunRecord, Task, gold_by_doc


DIAGNOSTIC_FLAGS = [
    "stale",
    "conflict",
    "generated_lore",
    "no_primary",
    "citation_laundering",
    "false_consensus",
    "partial_support",
]
UNSAFE_FLAGS = ["stale", "conflict", "generated_lore", "no_primary"]


def default_diagnostics() -> Dict[str, str]:
    return {
        "has_primary_support": "yes",
        "primary_support_is_current": "yes",
        "evidence_has_conflict": "no",
        "support_is_partial": "no",
        "sources_are_independent": "yes",
        "citation_laundering_detected": "no",
        "generated_lore_detected": "no",
        "no_primary_source_detected": "no",
    }


def derived_gold_diagnostics(task: Task) -> Dict[str, str]:
    diagnostics = default_diagnostics()
    if task.gold.diagnostics:
        diagnostics.update(task.gold.diagnostics)
        return diagnostics
    if task.gold.scope_tag == "stale" or task.episode_type in {"temporal_pollution_compare"}:
        diagnostics["primary_support_is_current"] = "no"
    if task.gold.scope_tag == "conflicting" or task.episode_type in {"false_consensus_stress", "citation_laundering_trace"}:
        diagnostics["evidence_has_conflict"] = "yes"
    if task.gold.scope_tag == "partial" or task.episode_type == "mixed_source_corruption_v2":
        diagnostics["support_is_partial"] = "yes"
    if task.gold.scope_tag == "generated_lore" or task.episode_type == "halupedia_or_generated_lore":
        diagnostics["has_primary_support"] = "no"
        diagnostics["primary_support_is_current"] = "not_applicable"
        diagnostics["generated_lore_detected"] = "yes"
        diagnostics["no_primary_source_detected"] = "yes"
    if task.gold.scope_tag == "no_primary_source" or task.episode_type == "insufficient_or_no_primary":
        diagnostics["has_primary_support"] = "no"
        diagnostics["primary_support_is_current"] = "not_applicable"
        diagnostics["no_primary_source_detected"] = "yes"
    if task.episode_type in {"citation_laundering_trace", "citation_laundering"}:
        diagnostics["citation_laundering_detected"] = "yes"
        diagnostics["sources_are_independent"] = "no"
    return diagnostics


def derived_gold_risks(task: Task) -> List[str]:
    if task.gold.critical_risks:
        return list(task.gold.critical_risks)
    risks: List[str] = []
    if task.episode_type in {"temporal_pollution_compare"} or task.gold.scope_tag == "stale":
        risks.append("stale_evidence")
    if task.episode_type in {"false_consensus_stress"}:
        risks.extend(["false_consensus", "conflicting_evidence"])
    if task.episode_type in {"citation_laundering_trace", "citation_laundering"}:
        risks.extend(["citation_laundering", "conflicting_evidence"])
    if task.episode_type in {"halupedia_or_generated_lore"} or task.gold.scope_tag == "generated_lore":
        risks.extend(["generated_lore", "no_primary_source"])
    if task.episode_type in {"insufficient_or_no_primary"} or task.gold.scope_tag == "no_primary_source":
        risks.append("no_primary_source")
    if task.episode_type in {"mixed_source_corruption_v2"} or task.gold.scope_tag == "partial":
        risks.append("partial_support")
    return sorted(set(risks))


def flags_from_diagnostics(diagnostics: Mapping[str, str], risks: Sequence[str]) -> Dict[str, bool]:
    risk_set = set(risks)
    return {
        "stale": diagnostics.get("primary_support_is_current") == "no" or "stale_evidence" in risk_set,
        "conflict": diagnostics.get("evidence_has_conflict") == "yes" or "conflicting_evidence" in risk_set,
        "generated_lore": diagnostics.get("generated_lore_detected") == "yes" or "generated_lore" in risk_set,
        "no_primary": diagnostics.get("no_primary_source_detected") == "yes" or "no_primary_source" in risk_set,
        "citation_laundering": diagnostics.get("citation_laundering_detected") == "yes" or "citation_laundering" in risk_set,
        "false_consensus": "false_consensus" in risk_set,
        "partial_support": diagnostics.get("support_is_partial") == "yes" or "partial_support" in risk_set,
    }


def prediction_diagnostics(record: Phase2SRunRecord) -> Dict[str, str]:
    return record.prediction.evidence_diagnostics.model_dump()


def prediction_ledger_doc_ids(record: Phase2SRunRecord) -> List[str]:
    ids: List[str] = []
    for entry in record.prediction.verification_ledger:
        ids.extend(entry.evidence)
    return unique(ids)


def tool_result_doc_ids(tool_results: Sequence[Mapping[str, Any]], *, key: str | None = None) -> List[str]:
    ids: List[str] = []
    for result in tool_results:
        if key is not None:
            value = result.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, Mapping) and isinstance(item.get("doc_id"), str):
                        ids.append(str(item["doc_id"]))
            continue
        ids.extend(extract_doc_ids_from_tool_result(result))
    return unique(ids)


def useful_compare_versions(record: Phase2SRunRecord, task: Task, gold_docs: Mapping[str, GoldDocument]) -> bool:
    if not any(call.tool == "compare_versions" for call in record.tool_calls):
        return False
    compare_ids = set(tool_result_doc_ids(record.tool_results, key="versions"))
    ledger_ids = set(prediction_ledger_doc_ids(record))
    stale_ids = {gold.doc_id for gold in gold_docs.values() if gold.task_id == task.task_id and gold.stale}
    relevant = set(task.gold.primary_support) | stale_ids
    return bool(compare_ids & ledger_ids & relevant)


def score_phase2s_record(record: Phase2SRunRecord, task: Task, gold_docs: Mapping[str, GoldDocument]) -> Dict[str, Any]:
    prediction = record.prediction
    pred_diags = prediction_diagnostics(record)
    gold_diags = derived_gold_diagnostics(task)
    pred_risks = [str(risk) for risk in prediction.critical_risks]
    gold_risks = derived_gold_risks(task)
    pred_flags = flags_from_diagnostics(pred_diags, pred_risks)
    gold_flags = flags_from_diagnostics(gold_diags, gold_risks)
    supporting = unique(prediction.supporting_evidence)
    supporting_gold = [gold_docs[doc_id] for doc_id in supporting if doc_id in gold_docs]
    claim_correct = prediction.claim_verdict == task.gold.verdict
    contaminated_rate = sum(1 for gold in supporting_gold if gold.is_contaminated) / len(supporting) if supporting else 0.0
    clean_support = [gold for gold in supporting_gold if not gold.is_contaminated and gold.supports_gold_verdict]
    escape = claim_correct and contaminated_rate == 0.0 and (bool(clean_support) or prediction.claim_verdict == "insufficient")
    unsafe_gold = any(gold_flags[name] for name in UNSAFE_FLAGS)
    unsafe_pred = any(pred_flags[name] for name in UNSAFE_FLAGS)
    unsafe_miss = unsafe_gold and not unsafe_pred and prediction.confidence >= 0.70
    field_matches = [
        1.0 if str(pred_diags.get(field, "")) == str(gold_diags.get(field, "")) else 0.0
        for field in gold_diags
        if field in pred_diags
    ]
    result: Dict[str, Any] = {
        "task_id": task.task_id,
        "module": record.module,
        "dataset": record.dataset,
        "episode_type": task.episode_type,
        "model": record.model,
        "retriever": record.retriever,
        "strategy": record.strategy,
        "prompt": record.prompt,
        "backend": record.backend,
        "parse_success": 1.0 if record.parse_success else 0.0,
        "tool_parse_success": 1.0 if record.tool_parse_success else 0.0,
        "claim_accuracy": 1.0 if claim_correct else 0.0,
        "diagnostic_field_accuracy": sum(field_matches) / len(field_matches) if field_matches else 0.0,
        "source_independence_accuracy": 1.0 if pred_diags.get("sources_are_independent") == gold_diags.get("sources_are_independent") else 0.0,
        "contaminated_citation_rate": contaminated_rate,
        "escape_rate": 1.0 if escape else 0.0,
        "unsafe_scope_miss": 1.0 if unsafe_miss else 0.0,
        "overconfident_wrong": 1.0 if (not claim_correct and prediction.confidence >= 0.70) else 0.0,
        "confidence": prediction.confidence,
        "cost_usd": record.cost_usd,
        "tool_use_rate": 1.0 if record.tool_calls else 0.0,
        "trace_rate": 1.0 if any(call.tool == "trace_citation" for call in record.tool_calls) else 0.0,
        "compare_versions_rate": 1.0 if any(call.tool == "compare_versions" for call in record.tool_calls) else 0.0,
        "search_contradictions_rate": 1.0 if any(call.tool == "search_contradictions" for call in record.tool_calls) else 0.0,
        "primary_request_rate": 1.0 if any(call.tool == "request_primary_record" for call in record.tool_calls) else 0.0,
        "useful_compare_versions_rate": 1.0 if useful_compare_versions(record, task, gold_docs) else 0.0,
        "hidden_label_leakage": 1.0 if hidden_labels_leaked(record.tool_results) else 0.0,
        "supporting_evidence": ",".join(supporting),
        "rejected_evidence": ",".join(prediction.rejected_evidence),
        "ledger_evidence": ",".join(prediction_ledger_doc_ids(record)),
        "gold_claim_verdict": task.gold.verdict,
        "predicted_claim_verdict": prediction.claim_verdict,
        "gold_critical_risks": ",".join(gold_risks),
        "predicted_critical_risks": ",".join(pred_risks),
    }
    for flag in DIAGNOSTIC_FLAGS:
        result[f"gold_{flag}"] = 1.0 if gold_flags[flag] else 0.0
        result[f"pred_{flag}"] = 1.0 if pred_flags[flag] else 0.0
        result[f"{flag}_tp"] = 1.0 if gold_flags[flag] and pred_flags[flag] else 0.0
        result[f"{flag}_fp"] = 1.0 if (not gold_flags[flag]) and pred_flags[flag] else 0.0
        result[f"{flag}_fn"] = 1.0 if gold_flags[flag] and (not pred_flags[flag]) else 0.0
    return result


def score_phase2s_run(records: Sequence[Phase2SRunRecord], tasks: Sequence[Task], gold_documents: Sequence[GoldDocument]) -> List[Dict[str, Any]]:
    task_by_id = {task.task_id: task for task in tasks}
    docs_by_id = gold_by_doc(gold_documents)
    return [score_phase2s_record(record, task_by_id[record.task_id], docs_by_id) for record in records]


def mean_metric(rows: Sequence[Mapping[str, Any]], metric: str) -> float:
    return sum(float(row[metric]) for row in rows) / len(rows) if rows else 0.0


def precision(rows: Sequence[Mapping[str, Any]], flag: str) -> float:
    tp = sum(float(row[f"{flag}_tp"]) for row in rows)
    fp = sum(float(row[f"{flag}_fp"]) for row in rows)
    return tp / (tp + fp) if tp + fp else 1.0


def recall(rows: Sequence[Mapping[str, Any]], flag: str) -> float:
    tp = sum(float(row[f"{flag}_tp"]) for row in rows)
    fn = sum(float(row[f"{flag}_fn"]) for row in rows)
    return tp / (tp + fn) if tp + fn else 1.0


def flag_f1(rows: Sequence[Mapping[str, Any]], flag: str) -> float:
    p = precision(rows, flag)
    r = recall(rows, flag)
    return 2 * p * r / (p + r) if p + r else 0.0


def diagnostic_macro_f1(rows: Sequence[Mapping[str, Any]]) -> float:
    return sum(flag_f1(rows, flag) for flag in DIAGNOSTIC_FLAGS) / len(DIAGNOSTIC_FLAGS) if rows else 0.0


def diagnostic_metrics(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    return {
        "n": len(rows),
        "parse_success": mean_metric(rows, "parse_success"),
        "tool_parse_success": mean_metric(rows, "tool_parse_success"),
        "claim_accuracy": mean_metric(rows, "claim_accuracy"),
        "diagnostic_macro_f1": diagnostic_macro_f1(rows),
        "stale_recall": recall(rows, "stale"),
        "conflict_recall": recall(rows, "conflict"),
        "generated_lore_recall": recall(rows, "generated_lore"),
        "no_primary_precision": precision(rows, "no_primary"),
        "citation_laundering_recall": recall(rows, "citation_laundering"),
        "source_independence_accuracy": mean_metric(rows, "source_independence_accuracy"),
        "unsafe_scope_miss_rate": mean_metric(rows, "unsafe_scope_miss"),
        "escape_rate": mean_metric(rows, "escape_rate"),
        "contaminated_citation_rate": mean_metric(rows, "contaminated_citation_rate"),
        "compare_versions_rate": mean_metric(rows, "compare_versions_rate"),
        "useful_compare_versions_rate": mean_metric(rows, "useful_compare_versions_rate"),
        "trace_rate": mean_metric(rows, "trace_rate"),
        "search_contradictions_rate": mean_metric(rows, "search_contradictions_rate"),
        "primary_request_rate": mean_metric(rows, "primary_request_rate"),
        "hidden_label_leakage": mean_metric(rows, "hidden_label_leakage"),
        "overconfident_wrong_rate": mean_metric(rows, "overconfident_wrong"),
        "confidence": mean_metric(rows, "confidence"),
        "cost_usd": mean_metric(rows, "cost_usd"),
        "ece": expected_calibration_error([{"confidence": row["confidence"], "verdict_accuracy": row["claim_accuracy"]} for row in rows]),
    }


def aggregate_phase2s(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        record = {name: value for name, value in zip(group_keys, key)}
        record.update(diagnostic_metrics(group))
        output.append(record)
    return output


def diagnostic_confusion_by_flag(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for flag in DIAGNOSTIC_FLAGS:
        tp = int(sum(float(row[f"{flag}_tp"]) for row in rows))
        fp = int(sum(float(row[f"{flag}_fp"]) for row in rows))
        fn = int(sum(float(row[f"{flag}_fn"]) for row in rows))
        tn = len(rows) - tp - fp - fn
        output.append(
            {
                "flag": flag,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "tn": tn,
                "precision": precision(rows, flag),
                "recall": recall(rows, flag),
                "f1": flag_f1(rows, flag),
            }
        )
    return output


def unsafe_scope_miss_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "task_id": row["task_id"],
            "module": row["module"],
            "dataset": row["dataset"],
            "episode_type": row["episode_type"],
            "model": row["model"],
            "strategy": row["strategy"],
            "prompt": row["prompt"],
            "confidence": row["confidence"],
            "gold_critical_risks": row["gold_critical_risks"],
            "predicted_critical_risks": row["predicted_critical_risks"],
            "supporting_evidence": row["supporting_evidence"],
        }
        for row in rows
        if float(row["unsafe_scope_miss"]) > 0.0
    ]


@dataclass(frozen=True)
class Phase2SGate:
    passed: bool
    checks: Dict[str, bool]
    details: Dict[str, Any]


def phase2s_gate(
    rows: Sequence[Mapping[str, Any]],
    retrieval_rows: Sequence[Mapping[str, Any]],
    records: Sequence[Phase2SRunRecord],
) -> Phase2SGate:
    module_a_p1 = [row for row in rows if row["module"] == "A" and row["prompt"] == "evidence_diagnostics_v1"]
    module_b_route = [row for row in rows if row["module"] == "B" and row["strategy"] == "route_then_answer_v1"]
    module_b_temporal = [row for row in module_b_route if row["episode_type"] != "non_temporal_control"]
    module_c_static = [row for row in rows if row["module"] == "C" and row["strategy"] == "evidence_diagnostics_v1"]
    c_clean_bm25 = [row for row in module_c_static if row["episode_type"] == "clean_control" and row["retriever"] == "bm25_top8"]
    hp_ids = high_pressure_task_ids(retrieval_rows)
    c_hp_bm25 = [row for row in module_c_static if row["task_id"] in hp_ids and row["retriever"] == "bm25_top8"]
    c_hp_combo = [row for row in module_c_static if row["task_id"] in hp_ids and row["retriever"] == "hygienic_combo_top8"]
    c_combo = [row for row in module_c_static if row["retriever"] == "hygienic_combo_top8"]
    c_active_static = [row for row in rows if row["module"] == "C" and row["strategy"] == "static_hygienic_combo"]
    c_active_tools = [row for row in rows if row["module"] == "C" and row["strategy"] in {"route_then_answer_v1", "forced_triage_tools"}]
    static_escape = mean_metric(c_active_static, "escape_rate")
    min_active_escape = min((mean_metric(group, "escape_rate") for group in group_by(c_active_tools, "strategy").values()), default=1.0)
    a = diagnostic_metrics(module_a_p1)
    b = diagnostic_metrics(module_b_temporal)
    c = diagnostic_metrics(module_c_static)
    hp_wrong = 1.0 - mean_metric(c_hp_bm25, "claim_accuracy")
    hp_recovery = mean_metric(c_hp_combo, "claim_accuracy") - mean_metric(c_hp_bm25, "claim_accuracy")
    leak_free = not any(hidden_labels_leaked(record.tool_results) for record in records)

    checks = {
        "A1_claim_accuracy_at_least_0_90": a["claim_accuracy"] >= 0.90,
        "A2_diagnostic_macro_f1_at_least_0_70": a["diagnostic_macro_f1"] >= 0.70,
        "A3_stale_recall_at_least_0_75": a["stale_recall"] >= 0.75,
        "A4_conflict_recall_at_least_0_65": a["conflict_recall"] >= 0.65,
        "A5_generated_lore_recall_at_least_0_70": a["generated_lore_recall"] >= 0.70,
        "A6_no_primary_precision_at_least_0_90": a["no_primary_precision"] >= 0.90,
        "A7_unsafe_scope_miss_rate_at_most_0_25": a["unsafe_scope_miss_rate"] <= 0.25,
        "B1_compare_versions_rate_on_temporal_at_least_0_75": b["compare_versions_rate"] >= 0.75,
        "B2_useful_compare_versions_rate_at_least_0_60": b["useful_compare_versions_rate"] >= 0.60,
        "B3_temporal_claim_accuracy_at_least_0_85": b["claim_accuracy"] >= 0.85,
        "B4_stale_recall_at_least_0_75": b["stale_recall"] >= 0.75,
        "B5_tool_parse_success_at_least_0_98": b["tool_parse_success"] >= 0.98,
        "B6_hidden_label_leakage_false": leak_free,
        "C1_clean_control_claim_accuracy_at_least_0_90": mean_metric(c_clean_bm25, "claim_accuracy") >= 0.90,
        "C2_high_pressure_bm25_wrong_answer_rate_at_least_0_70": hp_wrong >= 0.70,
        "C3_hygienic_combo_high_pressure_recovery_delta_at_least_0_25": hp_recovery >= 0.25,
        "C4_hygienic_combo_claim_accuracy_at_least_0_95": mean_metric(c_combo, "claim_accuracy") >= 0.95,
        "C5_hygienic_combo_contaminated_citation_rate_at_most_0_08": mean_metric(c_combo, "contaminated_citation_rate") <= 0.08,
        "C6_diagnostic_macro_f1_at_least_0_60": c["diagnostic_macro_f1"] >= 0.60,
        "C7_stale_recall_at_least_0_65": c["stale_recall"] >= 0.65,
        "C8_conflict_recall_at_least_0_60": c["conflict_recall"] >= 0.60,
        "C9_generated_lore_recall_at_least_0_60": c["generated_lore_recall"] >= 0.60,
        "C10_active_tool_escape_not_more_than_0_05_below_static": min_active_escape + 0.05 >= static_escape,
    }
    details = {
        "module_a": a,
        "module_b_temporal_route": b,
        "module_c_static": c,
        "module_c_clean_bm25_claim_accuracy": mean_metric(c_clean_bm25, "claim_accuracy"),
        "module_c_high_pressure_bm25_wrong_answer_rate": hp_wrong,
        "module_c_high_pressure_recovery_delta": hp_recovery,
        "module_c_hygienic_combo_claim_accuracy": mean_metric(c_combo, "claim_accuracy"),
        "module_c_hygienic_combo_contaminated_citation_rate": mean_metric(c_combo, "contaminated_citation_rate"),
        "module_c_static_hygienic_combo_escape_rate": static_escape,
        "module_c_min_active_tool_escape_rate": min_active_escape,
        "hidden_label_leakage": not leak_free,
        "wrong_answer_rate_replaces_g3": hp_wrong,
        "mean_wrong_confidence": mean_wrong_confidence(c_hp_bm25),
        "overconfident_wrong_rate": mean_metric(c_hp_bm25, "overconfident_wrong"),
    }
    return Phase2SGate(passed=all(checks.values()), checks=checks, details=details)


def group_by(rows: Sequence[Mapping[str, Any]], key: str) -> Dict[Any, List[Mapping[str, Any]]]:
    grouped: Dict[Any, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row[key]].append(row)
    return grouped


def mean_wrong_confidence(rows: Sequence[Mapping[str, Any]]) -> float:
    wrong = [row for row in rows if float(row["claim_accuracy"]) == 0.0]
    return sum(float(row["confidence"]) for row in wrong) / len(wrong) if wrong else 0.0
