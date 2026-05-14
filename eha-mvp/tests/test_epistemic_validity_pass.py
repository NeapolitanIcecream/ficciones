from __future__ import annotations

import csv
import json
from pathlib import Path

from eha.epistemic_validity_pass import build_validity_pass, parse_error_category


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_parse_error_category_describes_common_json_failures() -> None:
    assert parse_error_category("Expecting value: line 1 column 1 (char 0)") == "empty_or_non_json_response"
    assert parse_error_category("Unterminated string starting at: line 5 column 20") == "truncated_or_unterminated_json"
    assert parse_error_category("Expecting ',' delimiter: line 12 column 6") == "malformed_or_truncated_json"


def test_validity_pass_writes_artifacts_without_claiming_repair(tmp_path: Path) -> None:
    manifest = build_validity_pass(
        task_dir=Path("data/epistemic-resilience-v1"),
        run_dir=Path("results/runs/epistemic-resilience-v1-api-final"),
        report_dir=Path("results/reports-epistemic-resilience-v1"),
        heuristic_report_dir=Path("results/reports-epistemic-resilience-v1-heuristic"),
        out_dir=tmp_path,
        human_sample_per_bucket=20,
    )

    assert manifest["task_content_changed"] is False
    assert manifest["gold_labels_changed"] is False
    assert manifest["api_calls_made"] is False
    assert manifest["outputs"]["human_audit_sample_rows"] == 80
    assert manifest["human_audit_bucket_counts"] == {
        "generated_lore": 20,
        "false_consensus": 20,
        "buried_primary": 20,
        "active_verification": 20,
    }

    parse_rows = read_csv(tmp_path / "parse_repair_audit.csv")
    gpt5_rows = [row for row in parse_rows if row["model"] == "openai/gpt-5-mini"]
    assert gpt5_rows
    assert sum(int(row["parse_failure_count"]) for row in gpt5_rows) == 124
    assert {row["repair_attempted"] for row in gpt5_rows} == {"0"}
    assert {row["raw_response_available"] for row in gpt5_rows} == {"0"}

    with (tmp_path / "audit_manifest.json").open(encoding="utf-8") as handle:
        written_manifest = json.load(handle)
    assert written_manifest["repair_attempted"] is False
    assert written_manifest["raw_response_available"] is False


def test_evidence_cleanliness_taxonomy_flags_dirty_support_types(tmp_path: Path) -> None:
    build_validity_pass(
        task_dir=Path("data/epistemic-resilience-v1"),
        run_dir=Path("results/runs/epistemic-resilience-v1-api-final"),
        report_dir=Path("results/reports-epistemic-resilience-v1"),
        heuristic_report_dir=Path("results/reports-epistemic-resilience-v1-heuristic"),
        out_dir=tmp_path,
        human_sample_per_bucket=5,
    )

    rows = read_csv(tmp_path / "evidence_cleanliness_failure_taxonomy.csv")
    labels = {label for row in rows for label in row["taxonomy_labels"].split(",")}

    assert "contaminated_support" in labels
    assert "generated_lore_cited" in labels
    assert "stale_evidence_cited" in labels
    assert any(row["model"] == "openai/gpt-5.4-mini" for row in rows)
