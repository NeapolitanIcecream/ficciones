from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .scoring import edge_key, expected_calibration_error, f1, unique
from .schemas import DependencyEdge, GoldDocument, Phase2RunRecord, Task, gold_by_doc


def score_phase2_record(
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
        valid_support = sum(1 for gold in supporting_gold if gold.supports_gold_verdict)
        evidence_validity = valid_support / len(supporting)
    else:
        evidence_validity = 1.0 if prediction.claim_verdict == "insufficient" else 0.0

    contaminated_rate = (sum(1 for gold in supporting_gold if gold.is_contaminated) / len(supporting)) if supporting else 0.0
    rejected_contaminated_rate = (
        sum(1 for gold in rejected_gold if gold.is_contaminated) / len(rejected_gold)
        if rejected_gold
        else 0.0
    )
    independent_evidence_score = (
        len({gold.upstream_root for gold in supporting_gold}) / len(supporting)
        if supporting
        else (1.0 if prediction.claim_verdict == "insufficient" else 0.0)
    )

    relevant_doc_ids = set(cited + record.final_doc_ids + record.initial_doc_ids)
    gold_relevant_edges = {edge_key(edge) for edge in gold_edges if edge.from_doc in relevant_doc_ids and edge.to_doc in relevant_doc_ids}
    predicted_edges = {edge_key(edge) for edge in prediction.predicted_dependency_edges}
    provenance_f1 = f1(predicted_edges, gold_relevant_edges)

    primary_supporting = [gold for gold in supporting_gold if gold.doc_id in task.gold.primary_support]
    clean_independent_support = [
        gold
        for gold in supporting_gold
        if (not gold.is_contaminated) and (gold.evidence_quality == "primary_record" or gold.supports_gold_verdict)
    ]
    overconfident_insufficient = prediction.claim_verdict == "insufficient" and prediction.confidence > 0.75
    escape = (
        claim_correct
        and bool(clean_independent_support or prediction.claim_verdict == "insufficient")
        and contaminated_rate == 0.0
        and not overconfident_insufficient
    )

    laundered_support = [
        gold
        for gold in supporting_gold
        if any(kind in {"citation_laundering", "secondary_pollution", "consensus_fabrication"} for kind in gold.contamination)
    ]
    generated_exposed = [gold_docs[doc_id] for doc_id in record.initial_doc_ids if doc_id in gold_docs and gold_docs[doc_id].generated]
    generated_cited = [gold for gold in supporting_gold if gold.generated]
    qips = (len(generated_cited) / len(generated_exposed)) if generated_exposed else 0.0
    polluted_mistake = (not claim_correct) and any(gold.is_contaminated for gold in supporting_gold)

    return {
        "task_id": task.task_id,
        "episode_type": task.episode_type,
        "duplicate_count": task.duplicate_count,
        "primary_visibility_under_bm25_top8": task.primary_visibility_under_bm25_top8,
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
        "qips": qips,
        "confidence": prediction.confidence,
        "wrong_confidence": prediction.confidence if not claim_correct else 0.0,
        "polluted_mistake": 1.0 if polluted_mistake else 0.0,
        "escape_rate": 1.0 if escape else 0.0,
        "primary_recovery_rate": 1.0 if set(record.final_doc_ids) & set(task.gold.primary_support) else 0.0,
        "valid_primary_support_rate": len(primary_supporting) / len(supporting) if supporting else 0.0,
        "laundered_support_rate": len(laundered_support) / len(supporting) if supporting else 0.0,
        "tool_use_rate": 1.0 if record.tool_calls else 0.0,
        "primary_request_rate": 1.0 if any(call.tool == "request_primary_record" for call in record.tool_calls) else 0.0,
        "trace_rate": 1.0 if any(call.tool == "trace_citation" for call in record.tool_calls) else 0.0,
        "useful_tool_rate": 1.0 if record.tool_calls and set(record.final_doc_ids) & set(task.gold.primary_support) else 0.0,
        "time_to_primary": time_to_primary(record.tool_results, task.gold.primary_support),
        "cost_usd": record.cost_usd,
        "supporting_evidence": ",".join(supporting),
        "rejected_evidence": ",".join(prediction.rejected_evidence),
        "gold_claim_verdict": task.gold.verdict,
        "predicted_claim_verdict": prediction.claim_verdict,
        "gold_scope_tag": task.gold.scope_tag,
        "predicted_scope_tag": prediction.scope_tag,
    }


def time_to_primary(tool_results: Sequence[Mapping[str, Any]], primary_support: Sequence[str]) -> Any:
    primary_ids = set(primary_support)
    for index, result in enumerate(tool_results, start=1):
        if primary_ids & set(extract_doc_ids_from_tool_result(result)):
            return index
    return ""


def extract_doc_ids_from_tool_result(result: Mapping[str, Any]) -> List[str]:
    doc_ids: List[str] = []
    for key in ("documents", "versions"):
        value = result.get(key)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping) and isinstance(item.get("doc_id"), str):
                    doc_ids.append(item["doc_id"])
    trace = result.get("trace")
    if isinstance(trace, list):
        for item in trace:
            if isinstance(item, Mapping) and isinstance(item.get("doc_id"), str):
                doc_ids.append(item["doc_id"])
    return doc_ids


def score_phase2_run(
    records: Sequence[Phase2RunRecord],
    tasks: Sequence[Task],
    gold_documents: Sequence[GoldDocument],
    edges: Sequence[DependencyEdge],
) -> List[Dict[str, Any]]:
    task_by_id = {task.task_id: task for task in tasks}
    docs_by_id = gold_by_doc(gold_documents)
    return [score_phase2_record(record, task_by_id[record.task_id], docs_by_id, edges) for record in records]


def aggregate_phase2(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> List[Dict[str, Any]]:
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
        "qips",
        "confidence",
        "polluted_mistake",
        "escape_rate",
        "primary_recovery_rate",
        "valid_primary_support_rate",
        "laundered_support_rate",
        "tool_use_rate",
        "primary_request_rate",
        "trace_rate",
        "useful_tool_rate",
        "cost_usd",
    ]
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        row = {name: value for name, value in zip(group_keys, key)}
        row["n"] = len(group)
        for metric in metrics:
            row[metric] = sum(float(item[metric]) for item in group) / len(group)
        row["ece"] = expected_calibration_error(
            [
                {"confidence": item["confidence"], "verdict_accuracy": item["claim_accuracy"]}
                for item in group
            ]
        )
        output.append(row)
    return output


def false_consensus_v2_rows(rows: Sequence[Mapping[str, Any]], retrieval_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    retrieval_by_key = {
        (row["task_id"], row["retriever"]): row
        for row in retrieval_rows
        if row["episode_type"] == "false_consensus"
    }
    grouped: Dict[Tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["episode_type"] != "false_consensus":
            continue
        key = (row["model"], row["retriever"], row["strategy"], row["duplicate_count"], row["primary_visibility_under_bm25_top8"])
        grouped[key].append(row)
    output: List[Dict[str, Any]] = []
    for (model, retriever, strategy, duplicate_count, primary_visibility), group in sorted(grouped.items()):
        wrong = [row for row in group if float(row["claim_accuracy"]) == 0.0]
        saturations = [
            float(retrieval_by_key[(row["task_id"], row["retriever"])]["pollutant_saturation_at_k"])
            for row in group
            if (row["task_id"], row["retriever"]) in retrieval_by_key
        ]
        output.append(
            {
                "model": model,
                "retriever": retriever,
                "strategy": strategy,
                "duplicate_count": duplicate_count,
                "primary_visibility_under_bm25_top8": primary_visibility,
                "n": len(group),
                "wrong_answer_rate": len(wrong) / len(group),
                "mean_wrong_confidence": (sum(float(row["confidence"]) for row in wrong) / len(wrong)) if wrong else 0.0,
                "polluted_mistake_rate": sum(float(row["polluted_mistake"]) for row in group) / len(group),
                "mean_pollutant_saturation_at_k": sum(saturations) / len(saturations) if saturations else 0.0,
            }
        )
    return output


@dataclass(frozen=True)
class Phase2PilotGate:
    passed: bool
    checks: Dict[str, bool]
    details: Dict[str, Any]


def hidden_labels_leaked(tool_results: Sequence[Mapping[str, Any]]) -> bool:
    text = json.dumps(list(tool_results), ensure_ascii=False).lower()
    forbidden = ["contamination", "upstream_root", "supports_gold", "gold_verdict", "rank_boost", "truth"]
    return any(label in text for label in forbidden)


def phase2_pilot_gate(
    rows: Sequence[Mapping[str, Any]],
    retrieval_rows: Sequence[Mapping[str, Any]],
    records: Sequence[Phase2RunRecord],
) -> Phase2PilotGate:
    clean_bm25 = [
        row for row in rows
        if row["episode_type"] == "clean_control" and row["retriever"] == "bm25_top8" and row["strategy"] == "evidence_graph_v2"
    ]
    clean_accuracy = sum(float(row["claim_accuracy"]) for row in clean_bm25) / len(clean_bm25) if clean_bm25 else 0.0

    false_bm25 = [
        row for row in rows
        if row["episode_type"] == "false_consensus" and row["retriever"] == "bm25_top8" and row["strategy"] == "evidence_graph_v2"
    ]
    false_wrong = sum(1.0 - float(row["claim_accuracy"]) for row in false_bm25) / len(false_bm25) if false_bm25 else 0.0

    retrieval_grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in retrieval_rows:
        retrieval_grouped[str(row["retriever"])].append(row)
    bm25_primary = mean_metric(
        [row for row in retrieval_grouped["bm25_top8"] if row["episode_type"] == "false_consensus"],
        "primary_recall_at_k",
    )
    preserve_primary = mean_metric(
        [row for row in retrieval_grouped["primary_preserve_top8"] if row["episode_type"] == "false_consensus"],
        "primary_recall_at_k",
    )
    bm25_saturation = mean_metric(
        [row for row in retrieval_grouped["bm25_top8"] if row["episode_type"] == "false_consensus"],
        "pollutant_saturation_at_k",
    )
    oracle_saturation = mean_metric(
        [row for row in retrieval_grouped["oracle_root_dedup_top8"] if row["episode_type"] == "false_consensus"],
        "pollutant_saturation_at_k",
    )

    mixed_rows = [row for row in rows if row["episode_type"] == "mixed_source_corruption_v2"]
    mixed_accuracy = sum(float(row["claim_accuracy"]) for row in mixed_rows) / len(mixed_rows) if mixed_rows else 0.0
    tool_rows = [row for row in rows if row["strategy"] == "tool_agent_2call"]
    tool_parse = sum(float(row["tool_parse_success"]) for row in tool_rows) / len(tool_rows) if tool_rows else 1.0
    leak_free = not any(hidden_labels_leaked(record.tool_results) for record in records)

    checks = {
        "clean_control_bm25_evidence_graph_v2_accuracy_at_least_0_90": clean_accuracy >= 0.90,
        "false_consensus_bm25_wrong_answer_rate_at_least_0_60": false_wrong >= 0.60,
        "primary_preserve_improves_primary_recall_by_0_25": preserve_primary - bm25_primary >= 0.25,
        "oracle_root_dedup_lowers_pollutant_saturation": bm25_saturation - oracle_saturation >= 0.20,
        "mixed_source_v2_not_all_zero_accuracy": mixed_accuracy > 0.0,
        "tool_agent_json_parse_success_at_least_0_95": tool_parse >= 0.95,
        "tool_outputs_do_not_leak_hidden_labels": leak_free,
    }
    details = {
        "clean_control_bm25_accuracy": clean_accuracy,
        "false_consensus_bm25_wrong_answer_rate": false_wrong,
        "bm25_primary_recall": bm25_primary,
        "primary_preserve_primary_recall": preserve_primary,
        "primary_recall_delta": preserve_primary - bm25_primary,
        "bm25_false_consensus_pollutant_saturation": bm25_saturation,
        "oracle_false_consensus_pollutant_saturation": oracle_saturation,
        "pollutant_saturation_delta": bm25_saturation - oracle_saturation,
        "mixed_source_v2_accuracy": mixed_accuracy,
        "tool_agent_json_parse_success": tool_parse,
        "tool_outputs_leak_hidden_labels": not leak_free,
    }
    return Phase2PilotGate(passed=all(checks.values()), checks=checks, details=details)


def mean_metric(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows) if rows else 0.0
