from __future__ import annotations

from pathlib import Path

from eha.matrix_generate import generate_matrix_dataset, write_matrix_dataset
from eha.matrix_paper_pack import (
    aggregate_prompt_hygiene,
    aggregate_l4_primary_recovery,
    prompt_hygiene_preflight_rows,
    score_records_with_mechanisms,
    summarize_with_cluster_ci,
)
from eha.matrix_v11 import filter_dataset, select_tasks_by_difficulty_limit
from eha.schemas import MatrixPrediction, MatrixRunRecord, model_to_dict, write_jsonl


def test_seed_cluster_ci_groups_rows_by_seed_before_resampling() -> None:
    rows = [
        {"model": "m", "strategy": "s", "difficulty": "L4", "seed": 1, "escape_rate": 1.0},
        {"model": "m", "strategy": "s", "difficulty": "L4", "seed": 1, "escape_rate": 1.0},
        {"model": "m", "strategy": "s", "difficulty": "L4", "seed": 2, "escape_rate": 0.0},
        {"model": "m", "strategy": "s", "difficulty": "L4", "seed": 2, "escape_rate": 0.0},
    ]

    summary = summarize_with_cluster_ci(rows, ["model", "strategy", "difficulty"], ["escape_rate"], cluster_key="seed")

    assert len(summary) == 1
    assert summary[0]["cluster_count"] == 2
    assert summary[0]["escape_rate"] == 0.5
    assert {"escape_rate_cluster_ci_low", "escape_rate_cluster_ci_high", "escape_rate_row_ci_low", "escape_rate_row_ci_high"} <= set(summary[0])


def test_mechanism_scoring_records_primary_context_citation_and_required_support() -> None:
    _, tasks, _, gold_documents, _ = generate_matrix_dataset(seed=9133)
    task = next(item for item in tasks if item.difficulty == "L4" and item.gold.primary_support)
    primary_doc = task.gold.primary_support[0]
    record = MatrixRunRecord(
        task_id=task.task_id,
        model="heuristic-sim",
        retriever="primary_preserve_top8",
        strategy="primary_preserve",
        prompt="claim_first_citation_v1",
        backend="heuristic",
        initial_doc_ids=[primary_doc],
        final_doc_ids=[primary_doc],
        prediction=MatrixPrediction(claim_verdict=task.gold.verdict, confidence=0.9, supporting_evidence=[primary_doc]),
        parse_success=True,
    )

    rows = score_records_with_mechanisms([record], tasks, gold_documents)

    assert rows[0]["has_required_supporting_evidence"] == 1.0
    assert rows[0]["clean_supporting_evidence"] == 1.0
    assert rows[0]["primary_in_context"] == 1.0
    assert rows[0]["primary_cited"] == 1.0
    assert rows[0]["best_primary_context_rank"] == 1


def test_prompt_hygiene_rows_compare_baseline_and_v1_1_on_same_subset(tmp_path: Path) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_matrix_dataset(seed=9133)
    selected_tasks = select_tasks_by_difficulty_limit(tasks, ("L0", "L3", "L4", "L5"), 1)
    prompt_data_dir = tmp_path / "prompt-data"
    baseline_data_dir = tmp_path / "baseline-data"
    v11_run_dir = tmp_path / "v11-run"
    baseline_run_dir = tmp_path / "baseline-run"
    filtered = filter_dataset(
        manifest=manifest,
        tasks=tasks,
        documents=documents,
        gold_documents=gold_documents,
        edges=edges,
        selected_tasks=selected_tasks,
        name="prompt-test",
        notes="prompt-test",
    )
    write_matrix_dataset(prompt_data_dir, *filtered)
    write_matrix_dataset(baseline_data_dir, manifest, tasks, documents, gold_documents, edges)
    task = selected_tasks[0]
    primary_doc = task.gold.primary_support[0]

    baseline_record = MatrixRunRecord(
        task_id=task.task_id,
        model="openai/gpt-4o-mini",
        retriever="primary_preserve_top8",
        strategy="primary_preserve",
        prompt="claim_first_citation_v1",
        backend="api",
        initial_doc_ids=[primary_doc],
        final_doc_ids=[primary_doc],
        prediction=MatrixPrediction(claim_verdict=task.gold.verdict, confidence=0.9, supporting_evidence=[]),
        parse_success=True,
    )
    v11_record = baseline_record.model_copy(
        update={
            "prompt": "claim_first_citation_v1_1",
            "prediction": MatrixPrediction(claim_verdict=task.gold.verdict, confidence=0.9, supporting_evidence=[primary_doc]),
        }
    )
    v11_run_dir.mkdir(parents=True)
    baseline_run_dir.mkdir(parents=True)
    write_jsonl(v11_run_dir / "predictions.jsonl", [model_to_dict(v11_record)])
    write_jsonl(baseline_run_dir / "predictions.jsonl", [model_to_dict(baseline_record)])

    rows = prompt_hygiene_preflight_rows(
        data_dir=prompt_data_dir,
        run_dir=v11_run_dir,
        baseline_data_dir=baseline_data_dir,
        baseline_run_dir=baseline_run_dir,
    )

    assert {row["prompt_version"] for row in rows} == {"claim_first_citation_v1", "claim_first_citation_v1_1"}
    assert {row["strategy"] for row in rows} == {"primary_preserve"}
    assert any(row["prompt_version"] == "claim_first_citation_v1_1" and row["has_required_supporting_evidence"] == 1.0 for row in rows)
    assert any(row["prompt_version"] == "claim_first_citation_v1" and row["has_required_supporting_evidence"] == 0.0 for row in rows)
    assert "over_abstention_rate" in aggregate_prompt_hygiene(rows)[0]


def test_l4_primary_recovery_aggregate_reports_rank_and_ignored_rate() -> None:
    rows = [
        {
            "model": "m",
            "strategy": "s",
            "prompt": "p",
            "retriever": "r",
            "claim_accuracy": 1.0,
            "escape_rate": 1.0,
            "contaminated_citation_rate": 0.0,
            "has_required_supporting_evidence": 1.0,
            "clean_supporting_evidence": 1.0,
            "primary_in_context": 1.0,
            "primary_cited": 0.0,
            "primary_rejected": 0.0,
            "primary_ignored": 1.0,
            "best_primary_context_rank": 3,
        },
        {
            "model": "m",
            "strategy": "s",
            "prompt": "p",
            "retriever": "r",
            "claim_accuracy": 0.0,
            "escape_rate": 0.0,
            "contaminated_citation_rate": 1.0,
            "has_required_supporting_evidence": 1.0,
            "clean_supporting_evidence": 0.0,
            "primary_in_context": 0.0,
            "primary_cited": 0.0,
            "primary_rejected": 0.0,
            "primary_ignored": 0.0,
            "best_primary_context_rank": "",
        },
    ]

    aggregate = aggregate_l4_primary_recovery(rows)

    assert aggregate[0]["n"] == 2
    assert aggregate[0]["primary_in_context"] == 0.5
    assert aggregate[0]["primary_ignored"] == 0.5
    assert aggregate[0]["primary_rank_n"] == 1
    assert aggregate[0]["mean_best_primary_context_rank"] == 3.0
