from __future__ import annotations

from pathlib import Path

from eha.uncued_schema_codex_audit import (
    audit_sample_rows,
    build_sample_rows,
    run_codex_schema_audit,
)


DATASET_DIR = Path("data/uncued-pilot-v1")
RUN_DIR = Path("results/reports-eha-uncued-schema-ablation-2026-05-23")
REPORTS_DIR = Path("../reports")


def test_codex_audit_packet_joins_latest_rows_with_gold_and_artifacts(tmp_path: Path) -> None:
    sample = build_sample_rows(RUN_DIR, DATASET_DIR, scope="full")

    assert len(sample) == 128
    assert {row["schema_variant"] for row in sample} == {"current", "clarified", "minimal", "diagnostic_no_hygiene"}
    assert all(row["prompt_path"] for row in sample)
    assert all(row["response_path"] for row in sample)
    assert all(row["gold_doc_roles_json"] != "[]" for row in sample)


def test_codex_audit_rows_have_notes_and_schema_specific_not_applicable_values() -> None:
    sample = build_sample_rows(RUN_DIR, DATASET_DIR, scope="full")
    audited, disagreements = audit_sample_rows(sample)

    assert len(audited) == 128
    assert disagreements == []
    assert all(row["auditor_note"].strip() for row in audited)
    minimal_rows = [row for row in audited if row["schema_variant"] == "minimal"]
    assert minimal_rows
    assert {row["rejection_hygiene_agrees"] for row in minimal_rows} == {"not_applicable"}
    assert {row["diagnostic_field_agrees"] for row in minimal_rows} == {"not_applicable"}
    active_minimal_rows = [row for row in minimal_rows if row["family"] == "active_verification"]
    assert {row["action_quality_agrees"] for row in active_minimal_rows} == {"not_applicable"}


def test_codex_audit_writes_full_summary_and_empty_disagreement_table(tmp_path: Path) -> None:
    summary = run_codex_schema_audit(
        RUN_DIR,
        DATASET_DIR,
        tmp_path / "audit",
        tmp_path / "reports",
        scope="full",
    )

    assert summary["rows_audited"] == 128
    assert summary["rows_with_scorer_fix_needed"] == 0
    assert summary["material_disagreements"] == 0
    assert (tmp_path / "audit/codex_schema_audit_disagreements.csv").read_text(encoding="utf-8").startswith("disagreement_id,")
