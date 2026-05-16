from __future__ import annotations

from eha.step2_statistics import (
    paired_metric_differences,
    paired_permutation_test,
    summarize_task_cluster_ci,
    task_cluster_bootstrap_ci,
)


def test_task_cluster_bootstrap_ci_resamples_whole_tasks_not_rows() -> None:
    rows = [
        {"task_id": "t1", "model": "m1", "operational_escape": 1.0},
        {"task_id": "t1", "model": "m2", "operational_escape": 1.0},
        {"task_id": "t2", "model": "m1", "operational_escape": 0.0},
        {"task_id": "t2", "model": "m2", "operational_escape": 0.0},
    ]

    low, high = task_cluster_bootstrap_ci(rows, metric="operational_escape", samples=500, seed=7)

    assert 0.0 <= low <= 0.5
    assert 0.5 <= high <= 1.0


def test_summarize_task_cluster_ci_reports_grouped_means_and_cluster_counts() -> None:
    rows = [
        {"task_id": "t1", "model": "a", "operational_escape": 1.0},
        {"task_id": "t2", "model": "a", "operational_escape": 0.0},
        {"task_id": "t1", "model": "b", "operational_escape": 1.0},
        {"task_id": "t2", "model": "b", "operational_escape": 1.0},
    ]

    summary = summarize_task_cluster_ci(
        rows,
        group_keys=["model"],
        metrics=["operational_escape"],
        samples=500,
        seed=11,
    )

    by_model = {row["model"]: row for row in summary}
    assert by_model["a"]["n"] == 2
    assert by_model["a"]["cluster_count"] == 2
    assert by_model["a"]["operational_escape"] == 0.5
    assert by_model["b"]["operational_escape"] == 1.0
    assert by_model["b"]["operational_escape_ci_low"] == 1.0
    assert by_model["b"]["operational_escape_ci_high"] == 1.0


def test_paired_metric_differences_average_duplicate_rows_within_pair_condition() -> None:
    rows = [
        {"pair_id": "p1", "condition": "visible", "model": "m", "escape": 0.0},
        {"pair_id": "p1", "condition": "hidden", "model": "m", "escape": 1.0},
        {"pair_id": "p2", "condition": "visible", "model": "m", "escape": 0.0},
        {"pair_id": "p2", "condition": "hidden", "model": "m", "escape": 0.0},
        {"pair_id": "p2", "condition": "hidden", "model": "m", "escape": 1.0},
    ]

    diffs = paired_metric_differences(
        rows,
        metric="escape",
        condition_key="condition",
        baseline_condition="visible",
        treatment_condition="hidden",
        pair_keys=["pair_id", "model"],
    )

    assert diffs == [1.0, 0.5]


def test_paired_permutation_test_reports_two_sided_exact_p_value_for_small_samples() -> None:
    rows = [
        {"pair_id": "p1", "condition": "standard", "model": "m", "escape": 0.0},
        {"pair_id": "p1", "condition": "hygiene", "model": "m", "escape": 1.0},
        {"pair_id": "p2", "condition": "standard", "model": "m", "escape": 0.0},
        {"pair_id": "p2", "condition": "hygiene", "model": "m", "escape": 1.0},
        {"pair_id": "p3", "condition": "standard", "model": "m", "escape": 1.0},
        {"pair_id": "p3", "condition": "hygiene", "model": "m", "escape": 1.0},
        {"pair_id": "p4", "condition": "standard", "model": "m", "escape": 0.0},
        {"pair_id": "p4", "condition": "hygiene", "model": "m", "escape": 0.0},
    ]

    result = paired_permutation_test(
        rows,
        metric="escape",
        condition_key="condition",
        baseline_condition="standard",
        treatment_condition="hygiene",
        pair_keys=["pair_id", "model"],
    )

    assert result["n_pairs"] == 4
    assert result["mean_difference"] == 0.5
    assert result["p_value"] == 0.5
