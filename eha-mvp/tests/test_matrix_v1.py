from __future__ import annotations

from collections import Counter
from pathlib import Path

from eha.cost_guard import CostGuard
from eha.matrix_generate import generate_matrix_dataset
from eha.matrix_run import filter_tasks_by_difficulties, run_matrix_records, select_matrix_specs
from eha.matrix_scoring import matrix_by_difficulty, matrix_preflight_gate, score_matrix_run
from eha.phase2_retrieval import compute_retrieval_metrics_for_tasks
from eha.schemas import by_task


def dataset_dict(dataset):
    manifest, tasks, documents, gold_documents, edges = dataset
    return {
        "manifest": manifest,
        "tasks": tasks,
        "documents": documents,
        "gold_documents": gold_documents,
        "edges": edges,
    }


def test_matrix_dataset_matches_escape_table_spec() -> None:
    manifest, tasks, documents, gold_documents, _ = generate_matrix_dataset(seed=9133)

    assert manifest.name == "EHA-Matrix-v1"
    assert manifest.episodes == 144
    assert Counter(task.difficulty for task in tasks) == {"L0": 24, "L1": 24, "L2": 24, "L3": 24, "L4": 24, "L5": 24}
    assert Counter(task.episode_type for task in tasks) == {
        "L0_clean_web": 24,
        "L1_mild_pollution": 24,
        "L2_temporal_drift": 24,
        "L3_false_consensus": 24,
        "L4_hidden_primary": 24,
        "L5_halluweb_generated_lore": 24,
    }
    assert all(task.phase == "matrix_v1" for task in tasks)
    assert all(task.gold.verdict == "insufficient" and not task.gold.primary_support for task in tasks if task.difficulty == "L5")
    assert not any(hasattr(doc, "contamination") for doc in documents)
    assert any(gold.generated for gold in gold_documents)


def test_matrix_preflight_dataset_has_six_per_difficulty() -> None:
    manifest, tasks, _, _, _ = generate_matrix_dataset(seed=9133, preflight=True)

    assert manifest.name == "EHA-Matrix-v1-preflight"
    assert manifest.episodes == 36
    assert Counter(task.difficulty for task in tasks) == {"L0": 6, "L1": 6, "L2": 6, "L3": 6, "L4": 6, "L5": 6}


def test_matrix_retrieval_metrics_exclude_oracle_retriever() -> None:
    _, tasks, documents, gold_documents, _ = generate_matrix_dataset(seed=9133, preflight=True)
    rows = compute_retrieval_metrics_for_tasks(
        tasks,
        by_task(documents),
        by_task(gold_documents),
        ("bm25_top8", "primary_preserve_top8", "hygienic_combo_top8"),
    )

    assert {row["retriever"] for row in rows} == {"bm25_top8", "primary_preserve_top8", "hygienic_combo_top8"}
    assert len(rows) == 36 * 3


def test_matrix_heuristic_preflight_gate_passes(tmp_path: Path) -> None:
    dataset = dataset_dict(generate_matrix_dataset(seed=9133, preflight=True))
    records = run_matrix_records(
        tasks=dataset["tasks"],
        docs_by_task_map=by_task(dataset["documents"]),
        gold_by_task=by_task(dataset["gold_documents"]),
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        preflight=True,
        max_output_tokens=2500,
        temperature=0.0,
        timeout_s=1.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
    )
    rows = score_matrix_run(records, dataset["tasks"], dataset["gold_documents"])
    gate = matrix_preflight_gate(rows)

    assert len(records) == 36 * 4
    assert gate.passed
    assert gate.details["l34_bm25_escape_rate"] < gate.details["l34_hygienic_combo_escape_rate"]


def test_matrix_sanity_subset_can_select_l3_l5_and_s0_s2_s3(tmp_path: Path) -> None:
    dataset = dataset_dict(generate_matrix_dataset(seed=9133, preflight=True))
    tasks = filter_tasks_by_difficulties(dataset["tasks"], ["L3", "L4", "L5"])
    strategies = ["naive_bm25", "primary_preserve", "hygienic_combo"]
    specs = select_matrix_specs(preflight=False, strategy_names=strategies)

    records = run_matrix_records(
        tasks=tasks,
        docs_by_task_map=by_task(dataset["documents"]),
        gold_by_task=by_task(dataset["gold_documents"]),
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        preflight=False,
        max_output_tokens=2500,
        temperature=0.0,
        timeout_s=1.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
        strategy_names=strategies,
    )
    rows = score_matrix_run(records, dataset["tasks"], dataset["gold_documents"])
    curve = matrix_by_difficulty(rows, "escape_rate")

    assert {task.difficulty for task in tasks} == {"L3", "L4", "L5"}
    assert [spec[0] for spec in specs] == strategies
    assert len(records) == 18 * 3
    assert {record.strategy for record in records} == set(strategies)
    assert curve[0]["L0"] == ""
    assert curve[0]["L3"] != ""
