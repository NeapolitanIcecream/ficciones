from __future__ import annotations

from collections import Counter
from pathlib import Path

from eha.uncued_scorer_audit import (
    load_scored_rows,
    scorer_audit,
    scorer_audit_summary,
    select_scorer_audit_sample,
)


def test_scorer_audit_sample_is_balanced_and_includes_successes_and_failures() -> None:
    rows = load_scored_rows(Path("results/reports-eha-uncued-pilot-2026-05-22/uncued_pilot_scored_predictions.csv"))

    sample = select_scorer_audit_sample(rows, sample_size=40)

    assert len(sample) == 40
    assert {row["model"] for row in sample} == {
        "claude-opus-4-7",
        "deepseek-v4-pro",
        "gemini-3.1-pro-preview",
        "gpt-5.5",
    }
    assert {row["view"] for row in sample} == {
        "neutral_metadata_hidden",
        "neutral_metadata_visible",
    }
    assert {row["condition"] for row in sample} == {
        "buried_primary",
        "clean",
        "conflicting_evidence",
        "false_consensus",
        "generated_lore",
    }
    assert {row["family"] for row in sample} == {
        "active_verification",
        "evidence_selection",
        "packet_judgment",
    }
    assert Counter(row["model"] for row in sample) == {
        "claude-opus-4-7": 10,
        "deepseek-v4-pro": 10,
        "gemini-3.1-pro-preview": 10,
        "gpt-5.5": 10,
    }
    assert Counter(row["view"] for row in sample) == {
        "neutral_metadata_hidden": 20,
        "neutral_metadata_visible": 20,
    }
    assert Counter(row["condition"] for row in sample) == {
        "buried_primary": 8,
        "clean": 8,
        "conflicting_evidence": 8,
        "false_consensus": 8,
        "generated_lore": 8,
    }
    assert any(float(row["operational_epistemic_escape"]) == 1.0 for row in sample)
    assert any(float(row["operational_epistemic_escape"]) == 0.0 for row in sample)


def test_scorer_audit_reports_reviewed_rows_and_disagreement_rate() -> None:
    rows = load_scored_rows(Path("results/reports-eha-uncued-pilot-2026-05-22/uncued_pilot_scored_predictions.csv"))
    sample = select_scorer_audit_sample(rows, sample_size=12)

    audited = scorer_audit(sample, dataset_dir=Path("data/uncued-pilot-v1"))
    summary = scorer_audit_summary(audited)

    assert len(audited) == 12
    assert summary["reviewed_rows"] == 12
    assert 0.0 <= summary["scorer_disagreement_rate"] <= 1.0
    assert "systematic_scorer_bug_found" in summary
    assert {"yes", "no"} >= {row["scorer_fix_needed"] for row in audited}
