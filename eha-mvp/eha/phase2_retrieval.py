from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

from rank_bm25 import BM25Okapi

from .retrieval import SearchHit, document_text, tokenize
from .schemas import AgentDocument, GoldDocument, Task


RETRIEVERS = (
    "bm25_top8",
    "bm25_top12",
    "primary_preserve_top8",
    "heuristic_root_dedup_top8",
    "hygienic_combo_top8",
    "oracle_root_dedup_top8",
)

PRIMARY_SOURCE_TYPES = {
    "audit_report",
    "regulator_filing",
    "contract",
    "incident_log",
    "version_history",
    "certification_record",
    "database_export",
}


def rank_episode(query: str, documents: Sequence[AgentDocument], gold_documents: Sequence[GoldDocument]) -> List[SearchHit]:
    if not documents:
        return []
    corpus = [tokenize(document_text(doc)) for doc in documents]
    bm25 = BM25Okapi(corpus)
    scores = list(bm25.get_scores(tokenize(query)))
    gold_by_id = {gold.doc_id: gold for gold in gold_documents}
    scored: List[tuple[float, AgentDocument]] = []
    for score, doc in zip(scores, documents):
        rank_boost = gold_by_id.get(doc.doc_id).rank_boost if doc.doc_id in gold_by_id else 0.0
        scored.append((float(score) + rank_boost, doc))
    scored.sort(key=lambda item: (-item[0], item[1].doc_id))
    return [SearchHit(doc=doc, score=score) for score, doc in scored]


def normalize_group_text(value: str) -> str:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return " ".join(tokens[:12])


def visible_group_key(doc: AgentDocument) -> str:
    if doc.visible_citations:
        return f"citation:{doc.visible_citations[0]}"
    first_line = doc.body.splitlines()[0] if doc.body else ""
    return "meta:" + normalize_group_text(f"{doc.source_type} {doc.title} {first_line}")


def jaccard_similarity(left: AgentDocument, right: AgentDocument) -> float:
    left_tokens = set(tokenize(left.title + " " + left.body))
    right_tokens = set(tokenize(right.title + " " + right.body))
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def contradiction_score(doc: AgentDocument, query: str) -> float:
    text = f"{doc.title} {doc.body}".lower()
    signals = (
        "not",
        "no ",
        "missed",
        "lapsed",
        "expired",
        "refuted",
        "correction",
        "revised",
        "audit",
        "regulator",
        "incident",
        "configuration",
        "no primary",
    )
    signal_score = sum(1 for signal in signals if signal in text)
    query_overlap = len(set(tokenize(query)) & set(tokenize(text)))
    primary_bonus = 3 if doc.source_type in PRIMARY_SOURCE_TYPES else 0
    return float(signal_score + primary_bonus) + query_overlap / 20.0


def _dedupe_hits_by_doc(hits: Iterable[SearchHit]) -> List[SearchHit]:
    seen: set[str] = set()
    output: List[SearchHit] = []
    for hit in hits:
        if hit.doc.doc_id in seen:
            continue
        output.append(hit)
        seen.add(hit.doc.doc_id)
    return output


def retrieve(
    query: str,
    documents: Sequence[AgentDocument],
    gold_documents: Sequence[GoldDocument],
    retriever: str,
) -> List[SearchHit]:
    ranked = rank_episode(query, documents, gold_documents)
    gold_by_id = {gold.doc_id: gold for gold in gold_documents}

    if retriever == "bm25_top8":
        return ranked[:8]
    if retriever == "bm25_top12":
        return ranked[:12]
    if retriever == "primary_preserve_top8":
        pool = ranked[:20]
        primaries = [hit for hit in pool if hit.doc.source_type in PRIMARY_SOURCE_TYPES][:2]
        return _dedupe_hits_by_doc([*primaries, *ranked])[:8]
    if retriever == "heuristic_root_dedup_top8":
        selected: List[SearchHit] = []
        group_counts: Counter[str] = Counter()
        for hit in ranked:
            key = visible_group_key(hit.doc)
            if group_counts[key] >= 1:
                continue
            if any(jaccard_similarity(hit.doc, kept.doc) > 0.82 for kept in selected):
                continue
            selected.append(hit)
            group_counts[key] += 1
            if len(selected) == 8:
                break
        return _dedupe_hits_by_doc([*selected, *ranked])[:8]
    if retriever == "hygienic_combo_top8":
        pool = ranked[:40]
        selected: List[SearchHit] = []
        group_counts: Counter[str] = Counter()
        source_type_counts: Counter[str] = Counter()
        selected_ids: set[str] = set()

        def can_add(hit: SearchHit) -> bool:
            if hit.doc.doc_id in selected_ids:
                return False
            if group_counts[visible_group_key(hit.doc)] >= 2:
                return False
            if source_type_counts[hit.doc.source_type] >= 3:
                return False
            return True

        def add(hit: SearchHit) -> None:
            selected.append(hit)
            selected_ids.add(hit.doc.doc_id)
            group_counts[visible_group_key(hit.doc)] += 1
            source_type_counts[hit.doc.source_type] += 1

        for hit in [item for item in pool if item.doc.source_type in PRIMARY_SOURCE_TYPES][:2]:
            if can_add(hit):
                add(hit)

        contradiction_candidates = sorted(pool, key=lambda hit: (-contradiction_score(hit.doc, query), hit.doc.doc_id))
        for hit in contradiction_candidates[:4]:
            if contradiction_score(hit.doc, query) > 2.0 and can_add(hit):
                add(hit)
                break

        current_status = any(word in query.lower() for word in ("still", "current", "january 2025", "valid", "2025"))
        fill_pool = sorted(pool, key=lambda hit: (-hit.score, hit.doc.doc_id))
        if current_status:
            fill_pool = sorted(pool, key=lambda hit: (-hit.score, hit.doc.timestamp, hit.doc.doc_id), reverse=False)
            fill_pool.sort(key=lambda hit: (-hit.score, -int("".join(ch for ch in hit.doc.timestamp if ch.isdigit()) or "0"), hit.doc.doc_id))
        for hit in fill_pool:
            if can_add(hit):
                add(hit)
            if len(selected) == 8:
                break
        return _dedupe_hits_by_doc([*selected, *ranked])[:8]
    if retriever == "oracle_root_dedup_top8":
        selected = []
        seen_roots: set[str] = set()
        for hit in ranked:
            root = gold_by_id[hit.doc.doc_id].upstream_root
            if root in seen_roots:
                continue
            selected.append(hit)
            seen_roots.add(root)
            if len(selected) == 8:
                break
        return _dedupe_hits_by_doc([*selected, *ranked])[:8]
    raise ValueError(f"unknown retriever: {retriever}")


def source_type_entropy(docs: Sequence[AgentDocument]) -> float:
    if not docs:
        return 0.0
    counts = Counter(doc.source_type for doc in docs)
    total = sum(counts.values())
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def first_primary_rank(task: Task, ranked_hits: Sequence[SearchHit]) -> Optional[int]:
    primary_ids = set(task.gold.primary_support)
    for index, hit in enumerate(ranked_hits, start=1):
        if hit.doc.doc_id in primary_ids:
            return index
    return None


def retrieval_metrics(
    *,
    task: Task,
    retriever: str,
    hits: Sequence[SearchHit],
    ranked_hits: Sequence[SearchHit],
    gold_documents: Sequence[GoldDocument],
) -> Dict[str, object]:
    gold_by_id = {gold.doc_id: gold for gold in gold_documents}
    selected_ids = [hit.doc.doc_id for hit in hits]
    selected_gold = [gold_by_id[doc_id] for doc_id in selected_ids if doc_id in gold_by_id]
    primary_ids = set(task.gold.primary_support)
    gold_evidence_ids = {gold.doc_id for gold in gold_documents if gold.supports_gold_verdict}
    contradiction_ids = set(task.primary_refutation_docs or task.gold.primary_support)
    contaminated_roots = [gold.upstream_root for gold in selected_gold if gold.is_contaminated]
    root_counts = Counter(contaminated_roots)
    pollutant_saturation = (max(root_counts.values()) / len(hits)) if hits and root_counts else 0.0
    primary_rank = first_primary_rank(task, ranked_hits)
    primary_visibility = any(hit.doc.doc_id in primary_ids for hit in ranked_hits[:8])

    return {
        "task_id": task.task_id,
        "episode_type": task.episode_type,
        "duplicate_count": task.duplicate_count,
        "primary_visibility_under_bm25_top8": primary_visibility,
        "retriever": retriever,
        "k": len(hits),
        "retrieved_doc_ids": ",".join(selected_ids),
        "primary_recall_at_k": len(primary_ids & set(selected_ids)) / len(primary_ids) if primary_ids else 0.0,
        "gold_evidence_recall_at_k": len(gold_evidence_ids & set(selected_ids)) / len(gold_evidence_ids) if gold_evidence_ids else 0.0,
        "contradiction_candidate_recall_at_k": len(contradiction_ids & set(selected_ids)) / len(contradiction_ids) if contradiction_ids else 0.0,
        "contaminant_fraction_at_k": (sum(1 for gold in selected_gold if gold.is_contaminated) / len(hits)) if hits else 0.0,
        "unique_upstream_roots_at_k": len({gold.upstream_root for gold in selected_gold}),
        "source_type_entropy_at_k": source_type_entropy([hit.doc for hit in hits]),
        "primary_rank": primary_rank if primary_rank is not None else "",
        "pollutant_saturation_at_k": pollutant_saturation,
        "stress_score": task.stress_score if task.stress_score is not None else "",
    }


def compute_retrieval_metrics_for_tasks(
    tasks: Sequence[Task],
    docs_by_task: Mapping[str, List[AgentDocument]],
    gold_by_task: Mapping[str, List[GoldDocument]],
    retrievers: Sequence[str] = RETRIEVERS,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for task in tasks:
        ranked = rank_episode(task.question, docs_by_task[task.task_id], gold_by_task[task.task_id])
        for retriever in retrievers:
            hits = retrieve(task.question, docs_by_task[task.task_id], gold_by_task[task.task_id], retriever)
            rows.append(
                retrieval_metrics(
                    task=task,
                    retriever=retriever,
                    hits=hits,
                    ranked_hits=ranked,
                    gold_documents=gold_by_task[task.task_id],
                )
            )
    return rows
