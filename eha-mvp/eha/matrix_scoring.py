from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .scoring import expected_calibration_error, unique
from .schemas import GoldDocument, MatrixRunRecord, Task, gold_by_doc


DIFFICULTY_ORDER = ("L0", "L1", "L2", "L3", "L4", "L5")
MAIN_STRATEGIES = ("naive_bm25", "careful_bm25", "primary_preserve", "hygienic_combo")


def is_l5(task: Task) -> bool:
    return task.difficulty == "L5" or task.episode_type == "L5_halluweb_generated_lore"


def score_matrix_record(record: MatrixRunRecord, task: Task, gold_docs: Mapping[str, GoldDocument]) -> Dict[str, Any]:
    prediction = record.prediction
    supporting = unique(prediction.supporting_evidence)
    supporting_gold = [gold_docs[doc_id] for doc_id in supporting if doc_id in gold_docs]
    claim_correct = prediction.claim_verdict == task.gold.verdict
    contaminated_citation_rate = (sum(1 for gold in supporting_gold if gold.is_contaminated) / len(supporting)) if supporting else 0.0
    overconfident_wrong = (not claim_correct) and prediction.confidence >= 0.70
    l5 = is_l5(task)
    overclaim = l5 and prediction.claim_verdict in {"supported", "refuted"}
    abstention_quality = 1.0 if (l5 and prediction.claim_verdict == "insufficient") else 0.0 if l5 else ""
    clean_or_insufficient = bool(supporting and contaminated_citation_rate == 0.0) or prediction.claim_verdict == "insufficient"
    escape = claim_correct and contaminated_citation_rate == 0.0 and clean_or_insufficient and not overclaim

    false_consensus_susceptibility = (
        1.0
        if task.difficulty in {"L3", "L4"}
        and not claim_correct
        and any(gold.is_contaminated for gold in supporting_gold)
        else 0.0
    )
    return {
        "task_id": task.task_id,
        "difficulty": task.difficulty,
        "episode_type": task.episode_type,
        "model": record.model,
        "retriever": record.retriever,
        "strategy": record.strategy,
        "prompt": record.prompt,
        "backend": record.backend,
        "parse_success": 1.0 if record.parse_success else 0.0,
        "claim_accuracy": 1.0 if claim_correct else 0.0,
        "escape_rate": 1.0 if escape else 0.0,
        "contaminated_citation_rate": contaminated_citation_rate,
        "abstention_quality": abstention_quality,
        "overconfident_wrong_rate": 1.0 if overconfident_wrong else 0.0,
        "over_abstention_rate": 1.0 if task.difficulty == "L0" and prediction.claim_verdict == "insufficient" else 0.0,
        "generated_lore_overclaim_rate": 1.0 if overclaim else 0.0,
        "false_consensus_susceptibility": false_consensus_susceptibility,
        "primary_recovery_rate": 1.0 if set(record.final_doc_ids) & set(task.gold.primary_support) else 0.0,
        "confidence": prediction.confidence,
        "cost_usd": record.cost_usd,
        "supporting_evidence": ",".join(supporting),
        "rejected_evidence": ",".join(prediction.rejected_evidence),
        "gold_claim_verdict": task.gold.verdict,
        "predicted_claim_verdict": prediction.claim_verdict,
    }


def score_matrix_run(records: Sequence[MatrixRunRecord], tasks: Sequence[Task], gold_documents: Sequence[GoldDocument]) -> List[Dict[str, Any]]:
    task_by_id = {task.task_id: task for task in tasks}
    gold_by_id = gold_by_doc(gold_documents)
    return [score_matrix_record(record, task_by_id[record.task_id], gold_by_id) for record in records]


def mean_metric(rows: Sequence[Mapping[str, Any]], metric: str) -> float:
    values = [float(row[metric]) for row in rows if row.get(metric) != ""]
    return sum(values) / len(values) if values else 0.0


def aggregate_matrix(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    metrics = [
        "parse_success",
        "claim_accuracy",
        "escape_rate",
        "contaminated_citation_rate",
        "overconfident_wrong_rate",
        "over_abstention_rate",
        "generated_lore_overclaim_rate",
        "false_consensus_susceptibility",
        "primary_recovery_rate",
        "confidence",
        "cost_usd",
    ]
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        row = {name: value for name, value in zip(group_keys, key)}
        row["n"] = len(group)
        for metric in metrics:
            row[metric] = mean_metric(group, metric)
        row["abstention_quality"] = mean_metric(group, "abstention_quality")
        row["ece"] = expected_calibration_error(
            [{"confidence": item["confidence"], "verdict_accuracy": item["claim_accuracy"]} for item in group]
        )
        output.append(row)
    return output


def matrix_by_difficulty(rows: Sequence[Mapping[str, Any]], metric: str) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["strategy"] not in MAIN_STRATEGIES:
            continue
        grouped[(row["model"], row["strategy"])].append(row)
    output: List[Dict[str, Any]] = []
    for (model, strategy), group in sorted(grouped.items()):
        row: Dict[str, Any] = {"model": model, "strategy": strategy}
        vals: List[float] = []
        for difficulty in DIFFICULTY_ORDER:
            diff_rows = [item for item in group if item["difficulty"] == difficulty]
            if diff_rows:
                value = mean_metric(diff_rows, metric)
                row[difficulty] = value
                vals.append(value)
            else:
                row[difficulty] = ""
        row["avg"] = sum(vals) / len(vals) if vals else 0.0
        output.append(row)
    return output


@dataclass(frozen=True)
class MatrixPreflightGate:
    passed: bool
    checks: Dict[str, bool]
    details: Dict[str, Any]


def matrix_preflight_gate(rows: Sequence[Mapping[str, Any]]) -> MatrixPreflightGate:
    p1 = [row for row in rows if row["prompt"] == "claim_first_citation_v1"]
    p0 = [row for row in rows if row["prompt"] == "evidence_graph_v3"]
    l0_p1 = [row for row in p1 if row["difficulty"] == "L0"]
    l34_p1 = [row for row in p1 if row["difficulty"] in {"L3", "L4"}]
    bm25_l34 = [row for row in l34_p1 if row["retriever"] == "bm25_top8"]
    combo_l34 = [row for row in l34_p1 if row["retriever"] == "hygienic_combo_top8"]
    l5_p1 = [row for row in p1 if row["difficulty"] == "L5"]
    l5_p0 = [row for row in p0 if row["difficulty"] == "L5"]
    details = {
        "l0_claim_accuracy": mean_metric(l0_p1, "claim_accuracy"),
        "l0_over_abstention_rate": mean_metric(l0_p1, "over_abstention_rate"),
        "l34_bm25_escape_rate": mean_metric(bm25_l34, "escape_rate"),
        "l34_hygienic_combo_escape_rate": mean_metric(combo_l34, "escape_rate"),
        "p1_contaminated_citation_rate": mean_metric(p1, "contaminated_citation_rate"),
        "p0_contaminated_citation_rate": mean_metric(p0, "contaminated_citation_rate"),
        "l5_p1_overclaim_rate": mean_metric(l5_p1, "generated_lore_overclaim_rate"),
        "l5_p0_overclaim_rate": mean_metric(l5_p0, "generated_lore_overclaim_rate"),
    }
    checks = {
        "L0_claim_accuracy_at_least_0_90": details["l0_claim_accuracy"] >= 0.90,
        "L0_over_abstention_rate_at_most_0_10": details["l0_over_abstention_rate"] <= 0.10,
        "L3_L4_bm25_escape_below_hygienic_combo": details["l34_bm25_escape_rate"] < details["l34_hygienic_combo_escape_rate"],
        "claim_first_ccr_not_above_evidence_graph_v3": details["p1_contaminated_citation_rate"] <= details["p0_contaminated_citation_rate"],
        "L5_overclaim_not_worse_than_evidence_graph_v3": details["l5_p1_overclaim_rate"] <= details["l5_p0_overclaim_rate"],
    }
    return MatrixPreflightGate(passed=all(checks.values()), checks=checks, details=details)
