from __future__ import annotations

from eha.uncued_statistics import (
    bootstrap_statistics,
    group_rows_by_latent_task,
    paired_delta_map,
    paired_delta_values,
    resample_rows_by_latent_task,
)


def scored_row(
    *,
    task: str,
    model: str,
    view: str,
    condition: str,
    operational: float,
    belief: float,
    evidence_precision: float,
) -> dict[str, str]:
    suffix = "visible" if view == "neutral_metadata_visible" else "hidden"
    return {
        "task_id": f"{task}_{suffix}",
        "base_task_id": task,
        "model": model,
        "view": view,
        "condition": condition,
        "operational_epistemic_escape": str(operational),
        "belief_correctness": str(belief),
        "evidence_precision": str(evidence_precision),
    }


def test_resample_rows_by_latent_task_keeps_paired_views_together() -> None:
    rows = [
        scored_row(
            task="t1",
            model="m1",
            view="neutral_metadata_visible",
            condition="clean",
            operational=1.0,
            belief=1.0,
            evidence_precision=1.0,
        ),
        scored_row(
            task="t1",
            model="m1",
            view="neutral_metadata_hidden",
            condition="clean",
            operational=0.0,
            belief=1.0,
            evidence_precision=1.0,
        ),
    ]

    grouped = group_rows_by_latent_task(rows)
    sampled = resample_rows_by_latent_task(grouped, ["t1", "t1"])

    assert len(sampled) == 4
    assert {row["view"] for row in sampled} == {"neutral_metadata_visible", "neutral_metadata_hidden"}


def test_bootstrap_statistics_reports_model_condition_and_paired_delta() -> None:
    rows = [
        scored_row(
            task="t1",
            model="m1",
            view="neutral_metadata_visible",
            condition="generated_lore",
            operational=0.0,
            belief=1.0,
            evidence_precision=0.0,
        ),
        scored_row(
            task="t1",
            model="m1",
            view="neutral_metadata_hidden",
            condition="generated_lore",
            operational=0.0,
            belief=1.0,
            evidence_precision=0.0,
        ),
        scored_row(
            task="t2",
            model="m1",
            view="neutral_metadata_visible",
            condition="clean",
            operational=1.0,
            belief=1.0,
            evidence_precision=1.0,
        ),
        scored_row(
            task="t2",
            model="m1",
            view="neutral_metadata_hidden",
            condition="clean",
            operational=0.0,
            belief=1.0,
            evidence_precision=1.0,
        ),
    ]

    stats = bootstrap_statistics(rows, iterations=25, seed=7)

    assert stats["method"]["resample_unit"] == "latent_task"
    assert stats["method"]["latent_task_count"] == 2
    assert stats["model_metrics"][0]["operational_epistemic_escape"]["mean"] == 0.25
    assert stats["generated_lore_belief_operational_gap"]["mean"] == 1.0

    deltas = {row["model"]: row for row in stats["visible_hidden_paired_deltas"]}
    assert deltas["m1"]["visible_minus_hidden_operational_epistemic_escape"]["mean"] == 0.5


def test_paired_delta_values_use_latent_task_duplicates() -> None:
    rows = [
        scored_row(
            task="t1",
            model="m1",
            view="neutral_metadata_visible",
            condition="clean",
            operational=1.0,
            belief=1.0,
            evidence_precision=1.0,
        ),
        scored_row(
            task="t1",
            model="m1",
            view="neutral_metadata_hidden",
            condition="clean",
            operational=0.0,
            belief=1.0,
            evidence_precision=1.0,
        ),
    ]

    deltas = paired_delta_map(rows, "operational_epistemic_escape")
    values = paired_delta_values(deltas, ["t1", "t1"], ["m1"], model="m1")

    assert values == [1.0, 1.0]
