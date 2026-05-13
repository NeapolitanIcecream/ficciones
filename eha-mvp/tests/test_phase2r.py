from __future__ import annotations

from collections import Counter
from pathlib import Path

from eha.cost_guard import CostGuard
from eha.phase2_retrieval import compute_retrieval_metrics_for_tasks, retrieve
from eha.phase2_scoring import hidden_labels_leaked
from eha.phase2r_generate import generate_phase2r_dataset
from eha.phase2r_run import run_phase2r_records
from eha.phase2r_scoring import high_pressure_task_ids, phase2r_gate, score_phase2r_run
from eha.schemas import by_task


def test_phase2r_dataset_matches_stress_pilot_distribution() -> None:
    manifest, tasks, documents, gold_documents, _ = generate_phase2r_dataset(seed=6271)

    assert manifest.name == "EHA-v2R-stress-pilot"
    assert manifest.episodes == 80
    assert manifest.episode_type_counts == {
        "clean_control": 8,
        "false_consensus_stress": 32,
        "citation_laundering_trace": 12,
        "temporal_pollution_compare": 8,
        "halupedia_or_generated_lore": 10,
        "insufficient_or_no_primary": 6,
        "mixed_source_corruption_v2": 4,
    }
    assert len(documents) == len(gold_documents)
    assert all(task.phase == "phase2r" for task in tasks)
    assert all(task.gold.verdict in {"supported", "refuted", "insufficient"} for task in tasks)


def test_phase2r_false_consensus_grid_and_high_pressure_constraints_hold() -> None:
    _, tasks, documents, gold_documents, _ = generate_phase2r_dataset(seed=6271)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    false_tasks = [task for task in tasks if task.episode_type == "false_consensus_stress"]
    grid = Counter((task.duplicate_count, task.primary_visibility_under_bm25_top8) for task in false_tasks)

    for duplicate_count in (5, 20, 50, 100):
        assert grid[(duplicate_count, True)] == 4
        assert grid[(duplicate_count, False)] == 4

    for task in false_tasks:
        if task.duplicate_count < 20 or task.primary_visibility_under_bm25_top8:
            continue
        hits = retrieve(task.question, docs_by_task[task.task_id], gold_by_task[task.task_id], "bm25_top8")
        gold_by_id = {gold.doc_id: gold for gold in gold_by_task[task.task_id]}
        pollutant_hits = [hit for hit in hits if gold_by_id[hit.doc.doc_id].upstream_root == task.pollutant_root_id]
        assert len(pollutant_hits) / len(hits) >= 0.75
        assert not (set(task.gold.primary_support) & {hit.doc.doc_id for hit in hits})


def test_hygienic_combo_improves_high_pressure_retrieval_metrics() -> None:
    _, tasks, documents, gold_documents, _ = generate_phase2r_dataset(seed=6271)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    retrieval_rows = compute_retrieval_metrics_for_tasks(
        tasks,
        docs_by_task,
        gold_by_task,
        ["bm25_top8", "hygienic_combo_top8"],
    )
    hp_ids = high_pressure_task_ids(retrieval_rows)
    bm25 = [row for row in retrieval_rows if row["task_id"] in hp_ids and row["retriever"] == "bm25_top8"]
    combo = [row for row in retrieval_rows if row["task_id"] in hp_ids and row["retriever"] == "hygienic_combo_top8"]

    bm25_saturation = sum(float(row["pollutant_saturation_at_k"]) for row in bm25) / len(bm25)
    combo_saturation = sum(float(row["pollutant_saturation_at_k"]) for row in combo) / len(combo)
    combo_primary = sum(float(row["primary_recall_at_k"]) for row in combo) / len(combo)

    assert len(hp_ids) == 12
    assert bm25_saturation - combo_saturation >= 0.25
    assert combo_primary >= 0.90


def test_phase2r_tool_outputs_do_not_leak_hidden_labels_in_heuristic_run() -> None:
    _, tasks, documents, gold_documents, _ = generate_phase2r_dataset(seed=6271)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    records = run_phase2r_records(
        tasks=tasks[:4],
        docs_by_task_map=docs_by_task,
        gold_by_task=gold_by_task,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=Path("/tmp/eha-phase2r-test"),
        run_active=True,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
    )

    assert not any(hidden_labels_leaked(record.tool_results) for record in records)


def test_phase2r_heuristic_gate_passes() -> None:
    _, tasks, documents, gold_documents, edges = generate_phase2r_dataset(seed=6271)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    retrieval_rows = compute_retrieval_metrics_for_tasks(
        tasks,
        docs_by_task,
        gold_by_task,
        ["bm25_top8", "bm25_top12", "primary_preserve_top8", "heuristic_root_dedup_top8", "hygienic_combo_top8", "oracle_root_dedup_top8"],
    )
    records = run_phase2r_records(
        tasks=tasks,
        docs_by_task_map=docs_by_task,
        gold_by_task=gold_by_task,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=Path("/tmp/eha-phase2r-test"),
        run_active=True,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
    )
    rows = score_phase2r_run(records, tasks, gold_documents, edges)
    gate = phase2r_gate(rows, retrieval_rows, records)

    assert gate.passed
