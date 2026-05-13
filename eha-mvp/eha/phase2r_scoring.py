from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .phase2_scoring import extract_doc_ids_from_tool_result, hidden_labels_leaked
from .scoring import edge_key, expected_calibration_error, f1, unique
from .schemas import DependencyEdge, GoldDocument, Phase2RunRecord, Task, gold_by_doc


def is_generated_lore_task(task: Task) -> bool:
    return task.episode_type in {"halupedia_or_generated_lore", "insufficient_or_no_primary"}


def score_phase2r_record(
    record: Phase2RunRecord,
    task: Task,
    gold_docs: Mapping[str, GoldDocument],
    gold_edges: Sequence[DependencyEdge],
) -> Dict[str, Any]:
    prediction = record.prediction
    supporting = unique(prediction.supporting_evidence)
    cited = unique(prediction.supporting_evidence + prediction.rejected_evidence)
    supporting_gold = [gold_docs[doc_id] for doc_id in supporting if doc_id in gold_docs]
    rejected_gold = [gold_docs[doc_id] for doc_id in prediction.rejected_evidence if doc_id in gold_docs]
    claim_correct = prediction.claim_verdict == task.gold.verdict
    scope_correct = prediction.scope_tag == task.gold.scope_tag

    if supporting:
        evidence_validity = sum(1 for gold in supporting_gold if gold.supports_gold_verdict) / len(supporting)
    else:
        evidence_validity = 1.0 if prediction.claim_verdict == "insufficient" else 0.0

    contaminated_rate = sum(1 for gold in supporting_gold if gold.is_contaminated) / len(supporting) if supporting else 0.0
    rejected_contaminated_rate = sum(1 for gold in rejected_gold if gold.is_contaminated) / len(rejected_gold) if rejected_gold else 0.0
    independent_evidence_score = (
        len({gold.upstream_root for gold in supporting_gold}) / len(supporting)
        if supporting
        else (1.0 if prediction.claim_verdict == "insufficient" else 0.0)
    )
    clean_support = [gold for gold in supporting_gold if not gold.is_contaminated and (gold.supports_gold_verdict or gold.evidence_quality == "primary_record")]
    escape = claim_correct and contaminated_rate == 0.0 and (bool(clean_support) or prediction.claim_verdict == "insufficient")

    relevant_doc_ids = set(cited + record.initial_doc_ids + record.final_doc_ids)
    gold_relevant_edges = {edge_key(edge) for edge in gold_edges if edge.from_doc in relevant_doc_ids and edge.to_doc in relevant_doc_ids}
    predicted_edges = {edge_key(edge) for edge in prediction.predicted_dependency_edges}
    provenance_f1 = f1(predicted_edges, gold_relevant_edges)

    primary_recovered = bool(set(record.final_doc_ids) & set(task.gold.primary_support))
    generated_lore_overclaim = is_generated_lore_task(task) and prediction.claim_verdict != "insufficient" and prediction.confidence >= 0.70
    overconfident_wrong = (not claim_correct) and prediction.confidence >= 0.70

    return {
        "task_id": task.task_id,
        "episode_type": task.episode_type,
        "duplicate_count": task.duplicate_count,
        "primary_visibility_under_bm25_top8": task.primary_visibility_under_bm25_top8,
        "stress_score": task.stress_score,
        "model": record.model,
        "retriever": record.retriever,
        "strategy": record.strategy,
        "backend": record.backend,
        "parse_success": 1.0 if record.parse_success else 0.0,
        "tool_parse_success": 1.0 if record.tool_parse_success else 0.0,
        "claim_accuracy": 1.0 if claim_correct else 0.0,
        "scope_accuracy": 1.0 if scope_correct else 0.0,
        "evidence_validity": evidence_validity,
        "contaminated_citation_rate": contaminated_rate,
        "rejected_contaminated_rate": rejected_contaminated_rate,
        "independent_evidence_score": independent_evidence_score,
        "provenance_recovery_f1": provenance_f1,
        "escape_rate": 1.0 if escape else 0.0,
        "primary_recovery_rate": 1.0 if primary_recovered else 0.0,
        "valid_primary_support_rate": sum(1 for gold in supporting_gold if gold.doc_id in task.gold.primary_support) / len(supporting) if supporting else 0.0,
        "generated_lore_overclaim": 1.0 if generated_lore_overclaim else 0.0,
        "correct_insufficient": 1.0 if prediction.claim_verdict == "insufficient" and task.gold.verdict == "insufficient" else 0.0,
        "overconfident_wrong": 1.0 if overconfident_wrong else 0.0,
        "confidence": prediction.confidence,
        "wrong_confidence": prediction.confidence if not claim_correct else 0.0,
        "cost_usd": record.cost_usd,
        "tool_use_rate": 1.0 if record.tool_calls else 0.0,
        "trace_rate": 1.0 if any(call.tool == "trace_citation" for call in record.tool_calls) else 0.0,
        "compare_versions_rate": 1.0 if any(call.tool == "compare_versions" for call in record.tool_calls) else 0.0,
        "search_contradictions_rate": 1.0 if any(call.tool == "search_contradictions" for call in record.tool_calls) else 0.0,
        "primary_request_rate": 1.0 if any(call.tool == "request_primary_record" for call in record.tool_calls) else 0.0,
        "useful_tool_rate": 1.0 if record.tool_calls and bool(set(tool_result_doc_ids(record.tool_results)) & set(task.gold.primary_support)) else 0.0,
        "tool_diversity": tool_diversity(record.tool_calls),
        "supporting_evidence": ",".join(supporting),
        "rejected_evidence": ",".join(prediction.rejected_evidence),
        "gold_claim_verdict": task.gold.verdict,
        "predicted_claim_verdict": prediction.claim_verdict,
        "gold_scope_tag": task.gold.scope_tag,
        "predicted_scope_tag": prediction.scope_tag,
    }


def tool_result_doc_ids(tool_results: Sequence[Mapping[str, Any]]) -> List[str]:
    doc_ids: List[str] = []
    for result in tool_results:
        doc_ids.extend(extract_doc_ids_from_tool_result(result))
    return doc_ids


def tool_diversity(calls: Sequence[Any]) -> float:
    if not calls:
        return 0.0
    counts = Counter(call.tool for call in calls)
    total = sum(counts.values())
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def score_phase2r_run(
    records: Sequence[Phase2RunRecord],
    tasks: Sequence[Task],
    gold_documents: Sequence[GoldDocument],
    edges: Sequence[DependencyEdge],
) -> List[Dict[str, Any]]:
    task_by_id = {task.task_id: task for task in tasks}
    docs_by_id = gold_by_doc(gold_documents)
    return [score_phase2r_record(record, task_by_id[record.task_id], docs_by_id, edges) for record in records]


def aggregate_phase2r(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    metrics = [
        "parse_success",
        "tool_parse_success",
        "claim_accuracy",
        "scope_accuracy",
        "evidence_validity",
        "contaminated_citation_rate",
        "rejected_contaminated_rate",
        "independent_evidence_score",
        "provenance_recovery_f1",
        "escape_rate",
        "primary_recovery_rate",
        "valid_primary_support_rate",
        "generated_lore_overclaim",
        "correct_insufficient",
        "overconfident_wrong",
        "confidence",
        "tool_use_rate",
        "trace_rate",
        "compare_versions_rate",
        "search_contradictions_rate",
        "primary_request_rate",
        "useful_tool_rate",
        "tool_diversity",
        "cost_usd",
    ]
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        row = {name: value for name, value in zip(group_keys, key)}
        row["n"] = len(group)
        for metric in metrics:
            row[metric] = sum(float(item[metric]) for item in group) / len(group)
        row["ece"] = expected_calibration_error(
            [{"confidence": item["confidence"], "verdict_accuracy": item["claim_accuracy"]} for item in group]
        )
        output.append(row)
    return output


def high_pressure_task_ids(retrieval_rows: Sequence[Mapping[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for row in retrieval_rows:
        if row["retriever"] != "bm25_top8" or row["episode_type"] != "false_consensus_stress":
            continue
        hidden = str(row["primary_visibility_under_bm25_top8"]).lower() == "false"
        if hidden and int(row["duplicate_count"]) >= 20 and float(row["pollutant_saturation_at_k"]) >= 0.75:
            ids.add(str(row["task_id"]))
    return ids


def false_consensus_stress_rows(rows: Sequence[Mapping[str, Any]], retrieval_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    retrieval_by_key = {(row["task_id"], row["retriever"]): row for row in retrieval_rows}
    grouped: Dict[Tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["episode_type"] != "false_consensus_stress":
            continue
        key = (row["retriever"], row["strategy"], row["duplicate_count"], row["primary_visibility_under_bm25_top8"], row["stress_score"])
        grouped[key].append(row)
    output: List[Dict[str, Any]] = []
    for (retriever, strategy, duplicate_count, visibility, stress_score), group in sorted(grouped.items()):
        wrong = [row for row in group if float(row["claim_accuracy"]) == 0.0]
        saturations = [
            float(retrieval_by_key[(row["task_id"], row["retriever"])]["pollutant_saturation_at_k"])
            for row in group
            if (row["task_id"], row["retriever"]) in retrieval_by_key
        ]
        output.append(
            {
                "retriever": retriever,
                "strategy": strategy,
                "duplicate_count": duplicate_count,
                "primary_visibility_under_bm25_top8": visibility,
                "stress_score": stress_score,
                "n": len(group),
                "wrong_answer_rate": len(wrong) / len(group),
                "mean_wrong_confidence": sum(float(row["confidence"]) for row in wrong) / len(wrong) if wrong else 0.0,
                "mean_pollutant_saturation_at_k": sum(saturations) / len(saturations) if saturations else 0.0,
                "escape_rate": sum(float(row["escape_rate"]) for row in group) / len(group),
            }
        )
    return output


def scope_confusion_matrix(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    counts: Counter[Tuple[str, str]] = Counter()
    totals: Counter[str] = Counter()
    for row in rows:
        gold = str(row["gold_scope_tag"])
        pred = str(row["predicted_scope_tag"])
        counts[(gold, pred)] += 1
        totals[gold] += 1
    return [
        {
            "gold_scope_tag": gold,
            "predicted_scope_tag": pred,
            "n": count,
            "row_fraction": count / totals[gold] if totals[gold] else 0.0,
        }
        for (gold, pred), count in sorted(counts.items())
    ]


def halupedia_abstention_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    filtered = [row for row in rows if row["episode_type"] in {"halupedia_or_generated_lore", "insufficient_or_no_primary"}]
    return aggregate_phase2r(filtered, ["episode_type", "strategy"])


@dataclass(frozen=True)
class Phase2RGate:
    passed: bool
    checks: Dict[str, bool]
    details: Dict[str, Any]


def phase2r_gate(
    rows: Sequence[Mapping[str, Any]],
    retrieval_rows: Sequence[Mapping[str, Any]],
    records: Sequence[Phase2RunRecord],
) -> Phase2RGate:
    hp_ids = high_pressure_task_ids(retrieval_rows)
    static_bm25_hp = [
        row for row in rows
        if row["task_id"] in hp_ids and row["retriever"] == "bm25_top8" and row["strategy"] == "evidence_graph_v3"
    ]
    static_combo_hp = [
        row for row in rows
        if row["task_id"] in hp_ids and row["retriever"] == "hygienic_combo_top8" and row["strategy"] == "evidence_graph_v3"
    ]
    clean_bm25 = [
        row for row in rows
        if row["episode_type"] == "clean_control" and row["retriever"] == "bm25_top8" and row["strategy"] == "evidence_graph_v3"
    ]
    clean_acc = mean_metric(clean_bm25, "claim_accuracy")
    hp_wrong = 1.0 - mean_metric(static_bm25_hp, "claim_accuracy")
    wrong_rows = [row for row in static_bm25_hp if float(row["claim_accuracy"]) == 0.0]
    hp_wrong_conf = sum(float(row["confidence"]) for row in wrong_rows) / len(wrong_rows) if wrong_rows else 0.0
    hp_bm25_saturation = mean_retrieval_metric(retrieval_rows, hp_ids, "bm25_top8", "pollutant_saturation_at_k")
    hp_combo_saturation = mean_retrieval_metric(retrieval_rows, hp_ids, "hygienic_combo_top8", "pollutant_saturation_at_k")
    hp_combo_primary = mean_retrieval_metric(retrieval_rows, hp_ids, "hygienic_combo_top8", "primary_recall_at_k")
    recovery_delta = mean_metric(static_combo_hp, "claim_accuracy") - mean_metric(static_bm25_hp, "claim_accuracy")
    scope_acc = mean_metric(rows, "scope_accuracy")
    major_scope_min = min_major_scope_accuracy(rows)
    tool_rows = [row for row in rows if row["strategy"] == "tool_agent_3call_policy"]
    tool_parse = min(mean_metric(tool_rows, "parse_success"), mean_metric(tool_rows, "tool_parse_success"))
    trace_rate = tool_rate_for(tool_rows, "citation_laundering_trace", "trace_rate")
    compare_rate = tool_rate_for(tool_rows, "temporal_pollution_compare", "compare_versions_rate")
    contradiction_rate = tool_rate_for(tool_rows, "false_consensus_stress", "search_contradictions_rate")
    leak_free = not any(hidden_labels_leaked(record.tool_results) for record in records)
    generated_lore_rows = [row for row in rows if row["episode_type"] in {"halupedia_or_generated_lore", "insufficient_or_no_primary"}]
    overclaim = mean_metric(generated_lore_rows, "generated_lore_overclaim")

    checks = {
        "G1_clean_control_bm25_claim_accuracy_at_least_0_90": clean_acc >= 0.90,
        "G2_high_pressure_bm25_wrong_answer_rate_at_least_0_70": hp_wrong >= 0.70,
        "G3_high_pressure_bm25_mean_wrong_confidence_at_least_0_65": hp_wrong_conf >= 0.65,
        "G4_combo_reduces_pollutant_saturation_by_0_25": hp_bm25_saturation - hp_combo_saturation >= 0.25,
        "G5_combo_primary_recall_at_least_0_90": hp_combo_primary >= 0.90,
        "G6_high_pressure_recovery_delta_at_least_0_25": recovery_delta >= 0.25,
        "G7_scope_accuracy_and_major_classes": scope_acc >= 0.60 and major_scope_min >= 0.35,
        "G8_tool_agent_json_parse_success_at_least_0_98": tool_parse >= 0.98,
        "G9_tool_diversity_rates": trace_rate >= 0.40 and compare_rate >= 0.40 and contradiction_rate >= 0.40,
        "G10_hidden_label_leakage_false": leak_free,
        "G11_generated_lore_overclaim_rate_at_most_0_50": overclaim <= 0.50,
    }
    details = {
        "high_pressure_task_count": len(hp_ids),
        "clean_control_bm25_claim_accuracy": clean_acc,
        "high_pressure_bm25_wrong_answer_rate": hp_wrong,
        "high_pressure_bm25_mean_wrong_confidence": hp_wrong_conf,
        "high_pressure_bm25_pollutant_saturation": hp_bm25_saturation,
        "high_pressure_combo_pollutant_saturation": hp_combo_saturation,
        "pollutant_saturation_delta": hp_bm25_saturation - hp_combo_saturation,
        "high_pressure_combo_primary_recall": hp_combo_primary,
        "high_pressure_recovery_delta": recovery_delta,
        "scope_accuracy": scope_acc,
        "major_scope_min_accuracy": major_scope_min,
        "tool_agent_parse_success": tool_parse,
        "trace_rate_on_citation_laundering": trace_rate,
        "compare_versions_rate_on_temporal_pollution": compare_rate,
        "search_contradictions_rate_on_false_consensus": contradiction_rate,
        "hidden_label_leakage": not leak_free,
        "generated_lore_overclaim_rate": overclaim,
    }
    return Phase2RGate(passed=all(checks.values()), checks=checks, details=details)


def mean_retrieval_metric(rows: Sequence[Mapping[str, Any]], task_ids: set[str], retriever: str, metric: str) -> float:
    selected = [row for row in rows if row["task_id"] in task_ids and row["retriever"] == retriever]
    return sum(float(row[metric]) for row in selected) / len(selected) if selected else 0.0


def mean_metric(rows: Sequence[Mapping[str, Any]], metric: str) -> float:
    return sum(float(row[metric]) for row in rows) / len(rows) if rows else 0.0


def min_major_scope_accuracy(rows: Sequence[Mapping[str, Any]]) -> float:
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["gold_scope_tag"])].append(row)
    major = [mean_metric(group, "scope_accuracy") for group in grouped.values() if len(group) >= 6]
    return min(major) if major else 1.0


def tool_rate_for(rows: Sequence[Mapping[str, Any]], episode_type: str, metric: str) -> float:
    selected = [row for row in rows if row["episode_type"] == episode_type]
    return mean_metric(selected, metric)
