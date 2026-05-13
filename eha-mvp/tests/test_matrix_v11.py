from __future__ import annotations

from collections import Counter
from pathlib import Path

from eha.cost_guard import CostGuard
from eha.matrix_generate import generate_matrix_dataset, write_matrix_dataset
from eha.matrix_prompts import build_claim_first_messages
from eha.matrix_run import run_matrix_records
from eha.matrix_v11 import (
    aggregate_decomposition,
    apply_metadata_noise,
    filter_dataset,
    row_level_escape_decomposition,
    select_tasks_by_difficulty_limit,
)
from eha.schemas import by_task, model_to_dict, write_json, write_jsonl


def test_claim_first_v1_1_prompt_requires_supporting_evidence_for_decisive_verdicts() -> None:
    _, tasks, documents, _, _ = generate_matrix_dataset(seed=9133, preflight=True)
    messages = build_claim_first_messages(tasks[0].question, documents[:3], version="claim_first_citation_v1_1")

    assert "claim_first_citation_v1_1" in messages[1]["content"]
    assert "supporting_evidence must contain at least one clean doc_id" in messages[1]["content"]
    assert "Do not output empty supporting_evidence for supported or refuted verdicts" in messages[1]["content"]


def test_prompt_preflight_subset_selects_twelve_from_required_difficulties() -> None:
    _, tasks, _, _, _ = generate_matrix_dataset(seed=9133)
    selected = select_tasks_by_difficulty_limit(tasks, ("L0", "L3", "L4", "L5"), 12)

    assert len(selected) == 48
    assert Counter(task.difficulty for task in selected) == {"L0": 12, "L3": 12, "L4": 12, "L5": 12}


def test_noisy_metadata_changes_visible_documents_without_changing_gold() -> None:
    manifest, tasks, documents, gold_documents, edges = generate_matrix_dataset(seed=9133)
    selected_tasks = select_tasks_by_difficulty_limit(tasks, ("L3", "L4", "L5"))
    _, _, selected_docs, selected_gold, _ = filter_dataset(
        manifest=model_to_dict(manifest),
        tasks=tasks,
        documents=documents,
        gold_documents=gold_documents,
        edges=edges,
        selected_tasks=selected_tasks,
        name="test",
        notes="test",
    )

    gold_snapshot = [model_to_dict(gold) for gold in selected_gold]
    noisy_docs = apply_metadata_noise(selected_docs, selected_gold, noise_level=50, seed=4401)

    assert [doc.doc_id for doc in noisy_docs] == [doc.doc_id for doc in selected_docs]
    assert [model_to_dict(gold) for gold in selected_gold] == gold_snapshot
    assert any(
        before.source_type != after.source_type
        or before.title != after.title
        or before.visible_citations != after.visible_citations
        for before, after in zip(selected_docs, noisy_docs)
    )


def test_escape_decomposition_splits_claim_support_and_full_escape(tmp_path: Path) -> None:
    dataset = generate_matrix_dataset(seed=9133, preflight=True)
    manifest, tasks, documents, gold_documents, edges = dataset
    data_dir = tmp_path / "data"
    run_dir = tmp_path / "run"
    write_matrix_dataset(data_dir, manifest, tasks, documents, gold_documents, edges)
    records = run_matrix_records(
        tasks=tasks[:6],
        docs_by_task_map=by_task(documents),
        gold_by_task=by_task(gold_documents),
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=run_dir,
        preflight=False,
        max_output_tokens=2500,
        temperature=0.0,
        timeout_s=1.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
        strategy_names=["naive_bm25", "hygienic_combo"],
    )
    write_jsonl(run_dir / "predictions.jsonl", [model_to_dict(record) for record in records])
    write_json(run_dir / "cost_report.json", {"aborted": False, "spent_usd": 0.0, "record_cost_usd": 0.0})

    rows = row_level_escape_decomposition(data_dir, run_dir)
    aggregate = aggregate_decomposition(rows)

    assert len(rows) == 12
    assert {"claim_correct", "clean_supporting_evidence", "has_required_supporting_evidence", "full_escape"} <= set(rows[0])
    assert aggregate
    assert {"full_escape", "full_escape_ci_low", "full_escape_ci_high"} <= set(aggregate[0])
