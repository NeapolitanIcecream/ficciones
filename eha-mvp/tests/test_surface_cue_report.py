from __future__ import annotations

from eha.surface_cue_generate import generate_surface_cue_dataset, write_surface_cue_dataset
from eha.surface_cue_report import (
    build_surface_cue_balance_summary,
    parse_surface_claim_id,
    render_surface_cue_balance_markdown,
    write_surface_cue_balance_report,
)


def test_surface_cue_balance_summary_reports_multitemplate_contracts(tmp_path) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=9417)
    write_surface_cue_dataset(tmp_path, manifest, tasks, documents, gold_documents, edges)

    summary = build_surface_cue_balance_summary(tmp_path)

    assert summary["tasks"] == 180
    assert summary["documents"] == 900
    assert summary["gold_documents"] == 900
    assert summary["action_gold_rows"] == 30
    assert set(summary["family_counts"].values()) == {30}
    assert set(summary["axis_counts"].values()) == {36}
    assert set(summary["template_counts"].values()) == {10}
    assert summary["verdict_counts"] == {"insufficient": 90, "refuted": 90}
    assert summary["pair_contract_violations"] == []
    assert summary["visible_leakage_count"] == 0
    assert summary["action_target_violations"] == []
    assert summary["retrieval_observability"] == {
        "clean_support_required_rows": 120,
        "clean_support_observable_rows": 120,
        "contaminated_observable_rows": 180,
    }


def test_surface_cue_balance_report_writes_json_and_markdown(tmp_path) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=9417)
    dataset_dir = tmp_path / "dataset"
    out_dir = tmp_path / "reports"
    write_surface_cue_dataset(dataset_dir, manifest, tasks, documents, gold_documents, edges)

    summary = write_surface_cue_balance_report(dataset_dir, out_dir)
    markdown = render_surface_cue_balance_markdown(summary)

    assert (out_dir / "eha_step2_surface_cue_balance_summary.json").exists()
    assert (out_dir / "eha-step2-surface-cue-balance-2026-05-16.md").read_text(encoding="utf-8") == markdown
    assert "- Tasks: 180" in markdown
    assert "- Active-verification action-gold rows: 30" in markdown
    assert "- Pair contract violations: 0" in markdown


def test_parse_surface_claim_id_handles_family_names_with_underscores() -> None:
    assert parse_surface_claim_id("c_surface_active_verification_service_lane_content_only") == (
        "active_verification",
        "service_lane",
        "content_only",
    )
