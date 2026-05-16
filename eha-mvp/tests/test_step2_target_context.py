from __future__ import annotations

import json

from eha.step2_target_context import (
    build_default_target_context,
    render_target_context_markdown,
    validate_target_context,
    write_target_context_artifacts,
)


def test_default_target_context_is_incomplete_until_venue_deadline_and_budgets_are_filled() -> None:
    context = build_default_target_context()

    summary = validate_target_context(context)

    assert summary["status"] == "incomplete"
    assert summary["ready"] is False
    assert "target_venue" in summary["missing_fields"]
    assert "target_deadline" in summary["missing_fields"]
    assert "max_step2_api_budget_usd" in summary["missing_fields"]
    assert "human_review_budget_usd" in summary["missing_fields"]
    assert summary["approval_required_before_model_calls"] is True


def test_target_context_ready_requires_human_review_budget_not_only_api_budget() -> None:
    context = build_default_target_context()
    context.update(
        {
            "target_venue": "Workshop or main-conference track TBD by PI",
            "target_deadline": "2026-09-01",
            "submission_track": "benchmark/evaluation",
            "decision_owner": "PI",
            "budget_confirmed": True,
            "max_step2_api_budget_usd": 250.0,
            "human_review_budget_confirmed": False,
            "human_review_budget_usd": 0.0,
            "approval_required_before_model_calls": True,
        }
    )

    summary = validate_target_context(context)

    assert summary["status"] == "incomplete"
    assert summary["ready"] is False
    assert "human_review_budget_confirmed" in summary["missing_fields"]
    assert "human_review_budget_usd" in summary["missing_fields"]


def test_target_context_can_be_marked_ready_after_all_launch_decisions_are_explicit() -> None:
    context = build_default_target_context()
    context.update(
        {
            "target_venue": "ACL Rolling Review",
            "target_deadline": "2026-10-01",
            "submission_track": "benchmark/evaluation",
            "decision_owner": "PI",
            "budget_confirmed": True,
            "max_step2_api_budget_usd": 500.0,
            "human_review_budget_confirmed": True,
            "human_review_budget_usd": 1200.0,
            "approval_required_before_model_calls": True,
        }
    )

    summary = validate_target_context(context)

    assert summary["status"] == "ready"
    assert summary["ready"] is True
    assert summary["missing_fields"] == []


def test_target_context_markdown_preserves_no_api_boundary() -> None:
    summary = validate_target_context(build_default_target_context())
    markdown = render_target_context_markdown(summary)

    assert "# EHA Step 2 Target Context" in markdown
    assert "Status: `incomplete`" in markdown
    assert "not permission to run model/API calls" in markdown
    assert "target_venue" in markdown
    assert "human_review_budget_usd" in markdown


def test_target_context_writer_creates_template_validation_and_markdown(tmp_path) -> None:
    summary = write_target_context_artifacts(tmp_path)

    assert summary["status"] == "incomplete"
    context_path = tmp_path / "eha_step2_target_context.json"
    validation_path = tmp_path / "eha_step2_target_context_validation.json"
    report_path = tmp_path / "eha-step2-target-context-2026-05-16.md"
    assert context_path.exists()
    assert validation_path.exists()
    assert report_path.exists()
    assert json.loads(validation_path.read_text(encoding="utf-8"))["ready"] is False
    assert report_path.read_text(encoding="utf-8") == render_target_context_markdown(summary)
