from __future__ import annotations

from eha.generate_corpus import generate_dataset
from eha.retrieval import search_episode


def test_search_is_deterministic_for_same_inputs() -> None:
    _, tasks, documents, gold_documents, _ = generate_dataset(12, 4242)
    task = tasks[1]
    docs = [doc for doc in documents if doc.task_id == task.task_id]
    gold = [doc for doc in gold_documents if doc.task_id == task.task_id]

    first = search_episode(task.question, docs, gold, top_k=8)
    second = search_episode(task.question, docs, gold, top_k=8)

    assert [hit.doc.doc_id for hit in first] == [hit.doc.doc_id for hit in second]


def test_polluted_rank_boost_can_surface_false_consensus_sources() -> None:
    _, tasks, documents, gold_documents, _ = generate_dataset(12, 4242)
    task = next(task for task in tasks if task.episode_type == "false_consensus")
    docs = [doc for doc in documents if doc.task_id == task.task_id]
    gold = [doc for doc in gold_documents if doc.task_id == task.task_id]
    gold_by_id = {doc.doc_id: doc for doc in gold}

    hits = search_episode(task.question, docs, gold, top_k=8)

    assert any(gold_by_id[hit.doc.doc_id].is_contaminated for hit in hits[:3])
