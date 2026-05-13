from __future__ import annotations

from collections import Counter

from loguru import logger

from eha.cost_guard import CostGuard
from eha.phase2s_generate import (
    SCOPE_COUNTS,
    TEMPORAL_COUNTS,
    generate_scope_diagnostic_dataset,
    generate_temporal_routing_dataset,
)
from eha.phase2r_generate import generate_phase2r_dataset
from eha.phase2s_run import run_phase2s_records
from eha.phase2s_scoring import phase2s_gate, score_phase2s_run


logger.disable("eha.phase2s_run")


def test_phase2s_scope_dataset_matches_diagnostic_isolation_spec() -> None:
    manifest, tasks, documents, gold_documents, _ = generate_scope_diagnostic_dataset(seed=7319)
    docs_by_task = Counter(doc.task_id for doc in documents)

    assert manifest.name == "EHA-v2S-scope-diagnostic"
    assert manifest.seed == 7319
    assert manifest.episodes == 120
    assert manifest.episode_type_counts == SCOPE_COUNTS
    assert Counter(task.episode_type for task in tasks) == SCOPE_COUNTS
    assert all(task.phase == "phase2s_scope" for task in tasks)
    assert all(4 <= docs_by_task[task.task_id] <= 8 for task in tasks)
    assert all(task.gold.diagnostics for task in tasks)
    assert len(documents) == len(gold_documents)


def test_phase2s_temporal_dataset_matches_routing_repair_spec() -> None:
    manifest, tasks, documents, gold_documents, _ = generate_temporal_routing_dataset(seed=8144)
    temporal_tasks = [task for task in tasks if task.episode_type != "non_temporal_control"]
    docs_by_task = {}
    for doc in documents:
        docs_by_task.setdefault(doc.task_id, set()).add(doc.doc_id)

    assert manifest.name == "EHA-v2S-temporal-routing"
    assert manifest.seed == 8144
    assert manifest.episodes == 60
    assert manifest.episode_type_counts == TEMPORAL_COUNTS
    assert Counter(task.episode_type for task in tasks) == TEMPORAL_COUNTS
    assert all(task.phase == "phase2s_temporal" for task in tasks)
    assert all(task.gold.critical_risks == ["stale_evidence"] for task in temporal_tasks)
    assert all(any(doc_id.endswith("_old_version") for doc_id in docs_by_task[task.task_id]) for task in temporal_tasks)
    assert all(any(doc_id.endswith("_current_record") for doc_id in docs_by_task[task.task_id]) for task in temporal_tasks)
    assert len(documents) == len(gold_documents)


def test_phase2s_heuristic_gate_passes_full_repair_pipeline(tmp_path) -> None:
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
    )
    all_tasks = scope["tasks"] + temporal["tasks"] + phase2r["tasks"]
    all_gold = scope["gold_documents"] + temporal["gold_documents"] + phase2r["gold_documents"]
    rows = score_phase2s_run(records, all_tasks, all_gold)
    gate = phase2s_gate(rows, retrieval_rows, records)

    assert len(records) == 864
    assert gate.passed
    assert gate.details["module_b_temporal_route"]["compare_versions_rate"] == 1.0
    assert gate.details["module_b_temporal_route"]["useful_compare_versions_rate"] == 1.0


def test_phase2s_gate_fails_when_route_then_answer_omits_compare_versions(tmp_path) -> None:
    """Regression: temporal repair must fail loudly if route_then_answer stops comparing versions."""
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
    )
    broken_records = [
        record.model_copy(update={"tool_calls": [], "tool_results": []})
        if record.module == "B" and record.strategy == "route_then_answer_v1"
        else record
        for record in records
    ]
    all_tasks = scope["tasks"] + temporal["tasks"] + phase2r["tasks"]
    all_gold = scope["gold_documents"] + temporal["gold_documents"] + phase2r["gold_documents"]
    rows = score_phase2s_run(broken_records, all_tasks, all_gold)
    gate = phase2s_gate(rows, retrieval_rows, broken_records)

    assert not gate.passed
    assert not gate.checks["B1_compare_versions_rate_on_temporal_at_least_0_75"]
    assert not gate.checks["B2_useful_compare_versions_rate_at_least_0_60"]


def dataset_dict(dataset_tuple):
    manifest, tasks, documents, gold_documents, edges = dataset_tuple
    return {
        "manifest": manifest,
        "tasks": tasks,
        "documents": documents,
        "gold_documents": gold_documents,
        "edges": edges,
    }
