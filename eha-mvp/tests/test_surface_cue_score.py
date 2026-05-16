from __future__ import annotations

from eha.surface_cue_generate import generate_surface_cue_dataset, write_surface_cue_dataset
from eha.surface_cue_score import (
    SURFACE_CUE_BASELINES,
    build_surface_cue_baseline_records,
    score_surface_cue_baselines,
    write_surface_cue_score_report,
)


def test_surface_cue_baseline_records_are_phase2s_scorable() -> None:
    _, tasks, documents, gold_documents, _ = generate_surface_cue_dataset(seed=9417)

    records = build_surface_cue_baseline_records(tasks, documents, gold_documents)
    rows, metrics, axis_metrics = score_surface_cue_baselines(tasks, documents, gold_documents)

    assert len(records) == len(tasks) * len(SURFACE_CUE_BASELINES)
    assert len(rows) == len(records)
    assert {record.strategy for record in records} == set(SURFACE_CUE_BASELINES)
    assert all(row["family"] and row["template_id"] and row["surface_axis"] for row in rows)
    assert {row["strategy"] for row in metrics} == set(SURFACE_CUE_BASELINES)
    assert axis_metrics


def test_surface_cue_gold_contract_and_conservative_baseline_have_expected_bounds() -> None:
    _, tasks, documents, gold_documents, _ = generate_surface_cue_dataset(seed=9417)

    _, metrics, _ = score_surface_cue_baselines(tasks, documents, gold_documents)
    by_strategy = {row["strategy"]: row for row in metrics}

    oracle = by_strategy["oracle_gold_contract"]
    assert oracle["claim_accuracy"] == 1.0
    assert oracle["escape_rate"] == 1.0
    assert oracle["support_role_valid_rate"] == 1.0
    assert oracle["contaminated_citation_rate"] == 0.0
    assert oracle["useful_compare_versions_rate"] == 1 / 6
    assert oracle["trace_rate"] == 1 / 6

    conservative = by_strategy["always_insufficient"]
    assert conservative["claim_accuracy"] == 0.5
    assert conservative["escape_rate"] == 0.5
    assert conservative["support_role_valid_rate"] == 0.5
    assert conservative["contaminated_citation_rate"] == 0.0


def test_surface_cue_source_type_prior_exposes_metadata_spoofing_risk() -> None:
    _, tasks, documents, gold_documents, _ = generate_surface_cue_dataset(seed=9417)

    _, metrics, axis_metrics = score_surface_cue_baselines(tasks, documents, gold_documents)
    by_strategy = {row["strategy"]: row for row in metrics}
    source_type = by_strategy["source_type_prior"]
    source_axis = {
        row["surface_axis"]: row
        for row in axis_metrics
        if row["strategy"] == "source_type_prior"
    }

    assert source_type["claim_accuracy"] == 0.5
    assert source_type["contaminated_citation_rate"] > 0.0
    assert source_type["support_role_valid_rate"] < 0.5
    assert source_axis["metadata_perturbation"]["contaminated_citation_rate"] > source_axis["content_only"]["contaminated_citation_rate"]
    assert source_axis["adversarial_spoofing"]["contaminated_citation_rate"] > source_axis["content_only"]["contaminated_citation_rate"]


def test_surface_cue_score_report_writes_pipeline_artifacts(tmp_path) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=9417)
    dataset_dir = tmp_path / "dataset"
    out_dir = tmp_path / "reports"
    write_surface_cue_dataset(dataset_dir, manifest, tasks, documents, gold_documents, edges)

    summary = write_surface_cue_score_report(dataset_dir, out_dir)

    assert summary["tasks"] == 180
    assert summary["baselines"] == list(SURFACE_CUE_BASELINES)
    assert (out_dir / "surface_cue_scored_baselines.csv").exists()
    assert (out_dir / "surface_cue_baseline_metrics.csv").exists()
    assert (out_dir / "surface_cue_axis_metrics.csv").exists()
    assert (out_dir / "eha-step2-surface-cue-scoring-pipeline-2026-05-16.md").exists()
