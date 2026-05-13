from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .schemas import DependencyEdge, GoldDocument, RunRecord, Task, gold_by_doc


def unique(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def wrong_verdict_for(verdict: str) -> str:
    return {
        "supported": "refuted",
        "refuted": "supported",
        "insufficient": "supported",
        "mixed": "supported",
    }.get(verdict, "supported")


def edge_key(edge: DependencyEdge) -> Tuple[str, str]:
    return (edge.from_doc, edge.to_doc)


def f1(predicted: set[Tuple[str, str]], gold: set[Tuple[str, str]]) -> float:
    if not predicted and not gold:
        return 1.0
    if not predicted or not gold:
        return 0.0
    tp = len(predicted & gold)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(gold) if gold else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score_record(record: RunRecord, task: Task, gold_docs: Mapping[str, GoldDocument], gold_edges: Sequence[DependencyEdge]) -> Dict[str, Any]:
    prediction = record.prediction
    supporting = unique(prediction.supporting_evidence)
    cited = unique(prediction.supporting_evidence + prediction.rejected_evidence)
    supporting_gold = [gold_docs[doc_id] for doc_id in supporting if doc_id in gold_docs]
    rejected_gold = [gold_docs[doc_id] for doc_id in prediction.rejected_evidence if doc_id in gold_docs]
    verdict_correct = prediction.verdict == task.gold.verdict

    if supporting:
        valid_support = sum(1 for gold in supporting_gold if gold.supports_gold_verdict)
        evidence_validity = valid_support / len(supporting)
    else:
        evidence_validity = 1.0 if prediction.verdict == "insufficient" else 0.0

    contaminated_rate = (sum(1 for gold in supporting_gold if gold.is_contaminated) / len(supporting)) if supporting else 0.0
    rejected_contaminated_rate = (
        sum(1 for gold in rejected_gold if gold.is_contaminated) / len(rejected_gold)
        if rejected_gold
        else 0.0
    )
    independent_evidence_score = (
        len({gold.upstream_root for gold in supporting_gold}) / len(supporting)
        if supporting
        else (1.0 if prediction.verdict == "insufficient" else 0.0)
    )

    relevant_doc_ids = set(cited + record.retrieved_doc_ids)
    gold_relevant_edges = {edge_key(edge) for edge in gold_edges if edge.from_doc in relevant_doc_ids and edge.to_doc in relevant_doc_ids}
    predicted_edges = {edge_key(edge) for edge in prediction.predicted_dependency_edges}
    provenance_f1 = f1(predicted_edges, gold_relevant_edges)

    generated_exposed = [gold_docs[doc_id] for doc_id in record.retrieved_doc_ids if doc_id in gold_docs and gold_docs[doc_id].generated]
    generated_cited = [gold for gold in supporting_gold if gold.generated]
    qips = (len(generated_cited) / len(generated_exposed)) if generated_exposed else 0.0

    polluted_mistake = (not verdict_correct) and any(gold.is_contaminated for gold in supporting_gold)

    return {
        "task_id": task.task_id,
        "episode_type": task.episode_type,
        "duplicate_count": task.duplicate_count,
        "model": record.model,
        "strategy": record.strategy,
        "backend": record.backend,
        "parse_success": 1.0 if record.parse_success else 0.0,
        "verdict_accuracy": 1.0 if verdict_correct else 0.0,
        "evidence_validity": evidence_validity,
        "contaminated_citation_rate": contaminated_rate,
        "rejected_contaminated_rate": rejected_contaminated_rate,
        "independent_evidence_score": independent_evidence_score,
        "provenance_recovery_f1": provenance_f1,
        "qips": qips,
        "confidence": prediction.confidence,
        "wrong_confidence": prediction.confidence if not verdict_correct else 0.0,
        "polluted_mistake": 1.0 if polluted_mistake else 0.0,
        "cost_usd": record.cost_usd,
        "supporting_evidence": ",".join(supporting),
        "rejected_evidence": ",".join(prediction.rejected_evidence),
        "gold_verdict": task.gold.verdict,
        "predicted_verdict": prediction.verdict,
    }


def expected_calibration_error(rows: Sequence[Mapping[str, Any]], bins: int = 5) -> float:
    if not rows:
        return 0.0
    bucket_rows: List[List[Mapping[str, Any]]] = [[] for _ in range(bins)]
    for row in rows:
        confidence = max(0.0, min(0.999999, float(row["confidence"])))
        bucket_rows[int(confidence * bins)].append(row)
    total = len(rows)
    ece = 0.0
    for bucket in bucket_rows:
        if not bucket:
            continue
        accuracy = sum(float(row["verdict_accuracy"]) for row in bucket) / len(bucket)
        confidence = sum(float(row["confidence"]) for row in bucket) / len(bucket)
        ece += (len(bucket) / total) * abs(confidence - accuracy)
    return ece


def aggregate(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)

    output: List[Dict[str, Any]] = []
    metric_names = [
        "parse_success",
        "verdict_accuracy",
        "evidence_validity",
        "contaminated_citation_rate",
        "rejected_contaminated_rate",
        "independent_evidence_score",
        "provenance_recovery_f1",
        "qips",
        "confidence",
        "polluted_mistake",
        "cost_usd",
    ]
    for key, group in sorted(grouped.items()):
        row = {name: value for name, value in zip(group_keys, key)}
        row["n"] = len(group)
        for metric in metric_names:
            row[metric] = sum(float(item[metric]) for item in group) / len(group)
        row["ece"] = expected_calibration_error(group)
        output.append(row)
    return output


def score_run(records: Sequence[RunRecord], tasks: Sequence[Task], gold_documents: Sequence[GoldDocument], edges: Sequence[DependencyEdge]) -> List[Dict[str, Any]]:
    task_by_id = {task.task_id: task for task in tasks}
    docs_by_id = gold_by_doc(gold_documents)
    rows = []
    for record in records:
        rows.append(score_record(record, task_by_id[record.task_id], docs_by_id, edges))
    return rows


@dataclass(frozen=True)
class PilotGate:
    passed: bool
    checks: Dict[str, bool]
    details: Dict[str, Any]


def check_primary_and_pollutant(tasks: Sequence[Task], gold_documents: Sequence[GoldDocument]) -> bool:
    docs_by_task: Dict[str, List[GoldDocument]] = defaultdict(list)
    for gold in gold_documents:
        docs_by_task[gold.task_id].append(gold)
    for task in tasks:
        docs = docs_by_task[task.task_id]
        has_primary = any(gold.evidence_quality == "primary_record" for gold in docs)
        has_pollutant = any(gold.is_contaminated for gold in docs)
        if not has_primary or not has_pollutant:
            return False
    return True


def pilot_gate(rows: Sequence[Mapping[str, Any]], tasks: Sequence[Task], gold_documents: Sequence[GoldDocument]) -> PilotGate:
    clean_topk = [row for row in rows if row["episode_type"] == "clean_control" and row["strategy"] == "topk_rag"]
    clean_accuracy = sum(float(row["verdict_accuracy"]) for row in clean_topk) / len(clean_topk) if clean_topk else 0.0

    false_consensus_bad = [
        row
        for row in rows
        if row["episode_type"] == "false_consensus"
        and row["strategy"] in {"topk_rag", "citation_prompt"}
        and float(row["polluted_mistake"]) > 0
    ]

    robust_rows = [row for row in rows if row["strategy"] in {"source_independence_prompt", "evidence_graph_prompt"}]
    robust_accuracy = sum(float(row["verdict_accuracy"]) for row in robust_rows) / len(robust_rows) if robust_rows else 0.0
    parse_success = sum(float(row["parse_success"]) for row in rows) / len(rows) if rows else 0.0
    every_episode_has_required_docs = check_primary_and_pollutant(tasks, gold_documents)

    checks = {
        "clean_topk_accuracy_at_least_0_65": clean_accuracy >= 0.65,
        "false_consensus_has_at_least_3_polluted_mistakes": len(false_consensus_bad) >= 3,
        "a2_a3_not_trivially_perfect": robust_accuracy <= 0.95,
        "json_parse_success_at_least_0_95": parse_success >= 0.95,
        "every_episode_has_primary_and_pollutant": every_episode_has_required_docs,
    }
    details = {
        "clean_topk_accuracy": clean_accuracy,
        "false_consensus_polluted_mistakes": len(false_consensus_bad),
        "a2_a3_accuracy": robust_accuracy,
        "parse_success": parse_success,
    }
    return PilotGate(passed=all(checks.values()), checks=checks, details=details)
