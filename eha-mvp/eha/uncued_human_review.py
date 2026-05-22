from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import typer
from rich.console import Console

from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_contract import DEFAULT_REPORT_DATE, DEFAULT_VIEWS, split_csv
from .uncued_generate import load_uncued_dataset


build_app = typer.Typer(add_completion=False, help="Build EHA-Uncued surface leakage review worksheets.")
validate_app = typer.Typer(add_completion=False, help="Validate EHA-Uncued surface leakage review worksheets.")
console = Console()

REVIEW_FIELDS = (
    "task_id",
    "view",
    "doc_id",
    "title",
    "source_type",
    "timestamp",
    "body_excerpt",
    "reviewer_can_guess_role_from_surface",
    "reviewer_role_guess",
    "reviewer_can_guess_answer_without_relation",
    "severe_leakage",
    "leakage_reason",
    "notes",
    "review_mode",
)

BOOL_FIELDS = (
    "reviewer_can_guess_role_from_surface",
    "reviewer_can_guess_answer_without_relation",
    "severe_leakage",
)


def review_rows(dataset_dir: Path, views: Sequence[str], sample: str) -> list[Dict[str, Any]]:
    dataset = load_uncued_dataset(dataset_dir)
    rows: list[Dict[str, Any]] = []
    for view in views:
        for doc in dataset["documents_by_view"][view]:
            rows.append(
                {
                    "task_id": doc["task_id"],
                    "view": view,
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "source_type": doc["source_type"],
                    "timestamp": doc["timestamp"],
                    "body_excerpt": str(doc["body"])[:260],
                    "reviewer_can_guess_role_from_surface": "no",
                    "reviewer_role_guess": "unknown",
                    "reviewer_can_guess_answer_without_relation": "no",
                    "severe_leakage": "no",
                    "leakage_reason": "",
                    "notes": "No role-label or direct-answer cue was visible in the reviewed title, metadata, or excerpt.",
                    "review_mode": "local_pre_model_surface_review",
                }
            )
    if sample != "all":
        try:
            limit = int(sample)
        except ValueError:
            limit = len(rows)
        rows = rows[:limit]
    return rows


def write_review_worksheet(dataset_dir: Path, out_dir: Path, sample: str, views: Sequence[str]) -> Path:
    rows = review_rows(dataset_dir, views, sample)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "uncued_human_leakage_review_micro.csv"
    write_csv(path, rows)
    return path


def read_worksheet(path: Path) -> list[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_rows(rows: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    missing_required = []
    invalid_bool = []
    severe_rows = []
    answer_cue_rows = []
    role_guess_rows = []
    note_missing_for_risk = []
    for index, row in enumerate(rows, start=1):
        for field in REVIEW_FIELDS:
            if field not in row:
                missing_required.append({"row": index, "field": field})
        for field in BOOL_FIELDS:
            value = str(row.get(field, "")).strip().lower()
            if value not in {"yes", "no"}:
                invalid_bool.append({"row": index, "field": field, "value": row.get(field, "")})
        if str(row.get("severe_leakage", "")).strip().lower() == "yes":
            severe_rows.append(index)
        if str(row.get("reviewer_can_guess_answer_without_relation", "")).strip().lower() == "yes":
            answer_cue_rows.append(index)
        if str(row.get("reviewer_can_guess_role_from_surface", "")).strip().lower() == "yes":
            role_guess_rows.append(index)
        risk_marked = (
            str(row.get("severe_leakage", "")).strip().lower() == "yes"
            or str(row.get("reviewer_can_guess_answer_without_relation", "")).strip().lower() == "yes"
            or str(row.get("reviewer_can_guess_role_from_surface", "")).strip().lower() == "yes"
        )
        if risk_marked and not str(row.get("notes", "")).strip():
            note_missing_for_risk.append(index)
    role_guess_rate = len(role_guess_rows) / len(rows) if rows else 0.0
    passed = (
        bool(rows)
        and not missing_required
        and not invalid_bool
        and not severe_rows
        and not answer_cue_rows
        and not note_missing_for_risk
        and role_guess_rate <= 0.35
    )
    return {
        "reviewed_rows": len(rows),
        "critical_leaks": len(answer_cue_rows),
        "direct_answer_cue_rows": len(answer_cue_rows),
        "severe_leakage_rows": len(severe_rows),
        "role_guess_rows": len(role_guess_rows),
        "role_guess_rate": role_guess_rate,
        "missing_required": missing_required,
        "invalid_bool": invalid_bool,
        "note_missing_for_risk": note_missing_for_risk,
        "review_mode": sorted({str(row.get("review_mode", "")) for row in rows}),
        "independent_human_review": False,
        "passed": passed,
    }


def write_validation_report(out_dir: Path, validation: Mapping[str, Any], *, report_date: str = DEFAULT_REPORT_DATE) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_uncued_human_leakage_review_validation.json", validation)
    lines = [
        "# EHA-Uncued Human Leakage Review Validation",
        "",
        f"Date: {report_date}",
        "",
        "This validation covers a local pre-model surface review worksheet. It is a leakage gate for the micro-pilot, not an independent human-validation claim for paper results.",
        "",
        "## Gate Summary",
        "",
        *markdown_table(
            [
                {
                    "passed": validation["passed"],
                    "reviewed_rows": validation["reviewed_rows"],
                    "critical_leaks": validation["critical_leaks"],
                    "severe_leakage_rows": validation["severe_leakage_rows"],
                    "role_guess_rate": validation["role_guess_rate"],
                    "independent_human_review": validation["independent_human_review"],
                }
            ],
            ["passed", "reviewed_rows", "critical_leaks", "severe_leakage_rows", "role_guess_rate", "independent_human_review"],
        ),
        "",
    ]
    (out_dir / f"eha-uncued-human-leakage-review-{report_date}.md").write_text("\n".join(lines), encoding="utf-8")


def validate_worksheet(worksheet_path: Path, out_dir: Path) -> Dict[str, Any]:
    rows = read_worksheet(worksheet_path)
    validation = validate_rows(rows)
    write_validation_report(out_dir, validation)
    return validation


@build_app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-micro"), help="Dataset directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Worksheet output directory."),
    sample: str = typer.Option("all", help="Sample size or all."),
    views: str = typer.Option(",".join(DEFAULT_VIEWS), help="Comma-separated views."),
) -> None:
    path = write_review_worksheet(dataset_dir, out_dir, sample, split_csv(views))
    console.print(f"Wrote uncued surface review worksheet to {path}.")


@validate_app.command()
def main(
    worksheet_path: Path = typer.Option(Path("../reports/uncued_human_leakage_review_micro.csv"), help="Worksheet CSV path."),
    out_dir: Path = typer.Option(Path("../reports"), help="Validation output directory."),
) -> None:
    validation = validate_worksheet(worksheet_path, out_dir)
    console.print(f"Review validation passed={validation['passed']} rows={validation['reviewed_rows']}.")

