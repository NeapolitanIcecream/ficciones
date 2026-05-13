from __future__ import annotations

from pathlib import Path

from eha.cost_guard import CostGuard
from eha.phase2_generate import generate_phase2_dataset
from eha.phase2_retrieval import compute_retrieval_metrics_for_tasks, retrieve
from eha.phase2_run import run_phase2_records
from eha.phase2_scoring import hidden_labels_leaked, phase2_pilot_gate, score_phase2_run
from eha.phase2_tools import Phase2Toolbox
from eha.schemas import by_task


def test_phase2_dataset_matches_requested_distribution_and_schema_v2() -> None:
    manifest, tasks, documents, gold_documents, _ = generate_phase2_dataset(episodes=120, seed=5252)

    assert manifest.name == "eha-v2"
    assert manifest.episode_type_counts == {
        "clean_control": 15,
        "false_consensus": 30,
        "citation_laundering": 20,
        "temporal_pollution": 15,
        "mixed_source_corruption_v2": 20,
        "halupedia_trap": 10,
        "insufficient_or_no_primary": 10,
    }
    assert len(tasks) == 120
    assert len(documents) == len(gold_documents)
    assert all(task.phase == "phase2" for task in tasks)
    assert all(task.gold.verdict in {"supported", "refuted", "insufficient"} for task in tasks)
    assert any(task.gold.scope_tag == "mixed_evidence" for task in tasks)


def test_phase2_documents_stay_within_bounds_and_labels_are_hidden() -> None:
    _, tasks, documents, gold_documents, _ = generate_phase2_dataset(episodes=120, seed=5252)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)

    for task in tasks:
        assert 14 <= len(docs_by_task[task.task_id]) <= 22
        assert any(gold.evidence_quality == "primary_record" for gold in gold_by_task[task.task_id])
        assert any(gold.is_contaminated for gold in gold_by_task[task.task_id])
        for doc in docs_by_task[task.task_id]:
            visible = doc.model_dump()
            assert "contamination" not in visible
            assert "upstream_root" not in visible
            assert "rank_boost" not in visible


def test_phase2_retrievers_improve_false_consensus_hygiene() -> None:
    _, tasks, documents, gold_documents, _ = generate_phase2_dataset(episodes=120, seed=5252)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    target = next(task for task in tasks if task.episode_type == "false_consensus" and not task.primary_visibility_under_bm25_top8)

    bm25 = retrieve(target.question, docs_by_task[target.task_id], gold_by_task[target.task_id], "bm25_top8")
    primary = retrieve(target.question, docs_by_task[target.task_id], gold_by_task[target.task_id], "primary_preserve_top8")
    oracle = retrieve(target.question, docs_by_task[target.task_id], gold_by_task[target.task_id], "oracle_root_dedup_top8")
    target_primary = set(target.gold.primary_support)
    gold_by_id = {gold.doc_id: gold for gold in gold_by_task[target.task_id]}

    assert not (target_primary & {hit.doc.doc_id for hit in bm25})
    assert target_primary & {hit.doc.doc_id for hit in primary}
    assert len({gold_by_id[hit.doc.doc_id].upstream_root for hit in oracle}) == len(oracle)
    assert len({hit.doc.doc_id for hit in oracle}) == len(oracle)


def test_phase2_tools_do_not_return_hidden_labels() -> None:
    _, tasks, documents, _, _ = generate_phase2_dataset(episodes=24, seed=5252, pilot=True)
    docs_by_task = by_task(documents)
    task = next(task for task in tasks if task.episode_type == "false_consensus")
    toolbox = Phase2Toolbox(docs_by_task[task.task_id])

    results = [
        toolbox.trace_citation(f"{task.task_id}_repost_00"),
        toolbox.request_primary_record(task.question, entity="Novalis Robotics", date_range="2024", top_n=3),
        toolbox.compare_versions("Novalis Robotics", task.question, top_n=3),
        toolbox.search_contradictions(task.question, top_n=3),
    ]

    assert not hidden_labels_leaked(results)


def test_phase2_heuristic_pilot_gate_passes() -> None:
    _, tasks, documents, gold_documents, edges = generate_phase2_dataset(episodes=24, seed=5252, pilot=True)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    retrieval_rows = compute_retrieval_metrics_for_tasks(tasks, docs_by_task, gold_by_task)
    records = run_phase2_records(
        tasks=tasks,
        docs_by_task_map=docs_by_task,
        gold_by_task=gold_by_task,
        backend="heuristic",
        models=["heuristic-sim"],
        retrievers=["bm25_top8", "bm25_top12", "primary_preserve_top8", "heuristic_root_dedup_top8", "oracle_root_dedup_top8"],
        out_dir=Path("/tmp/eha-phase2-test"),
        active=True,
        max_output_tokens=4000,
        temperature=0.0,
        timeout_s=120.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
    )
    rows = score_phase2_run(records, tasks, gold_documents, edges)
    gate = phase2_pilot_gate(rows, retrieval_rows, records)

    assert gate.passed
