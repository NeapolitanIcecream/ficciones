from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping

import typer
from rich.console import Console

from .schemas import write_json
from .surface_cue_design_review import DESIGN_REVIEW_FIELDNAMES, DESIGN_REVIEW_LABEL_FIELDS, validate_surface_cue_design_review_rows


app = typer.Typer(add_completion=False, help="Validate completed EHA Step 2 surface-cue design-review worksheets.")
console = Console()


PILOT_READY_EXPECTED_LABELS = {
    "intended_cue_changed_only": "yes",
    "verdict_and_evidence_contract_preserved": "yes",
    "hidden_label_leakage_found": "no",
    "retrieval_observability_ok": "yes",
    "action_target_contract_ok": "yes",
    "suitable_for_small_api_pilot": "yes",
}


def read_design_review_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def label_value_counts(rows: List[Mapping[str, str]]) -> Dict[str, Dict[str, int]]:
    output: Dict[str, Dict[str, int]] = {}
    for field in DESIGN_REVIEW_LABEL_FIELDS:
        counts = Counter(str(row.get(field, "")).strip().lower() or "<blank>" for row in rows)
        output[field] = dict(sorted(counts.items()))
    return output


def design_review_pilot_blockers(rows: List[Mapping[str, str]], summary: Mapping[str, Any]) -> List[str]:
    blockers: List[str] = []
    if summary["status"] != "complete":
        blockers.append("review_status_incomplete")
    if summary["missing_label_cells"]:
        blockers.append("missing_label_cells")
    if summary["invalid_label_cells"]:
        blockers.append("invalid_label_cells")
    if summary["missing_notes"]:
        blockers.append("missing_notes")
    if summary.get("missing_columns"):
        blockers.append("missing_columns")
    if summary.get("duplicate_target_claim_ids"):
        blockers.append("duplicate_target_claim_ids")
    if summary.get("n_pairs") != 90:
        blockers.append("unexpected_pair_count")
    if summary.get("auto_pair_contract_failures"):
        blockers.append("auto_pair_contract_failures")
    if summary.get("auto_retrieval_observability_failures"):
        blockers.append("auto_retrieval_observability_failures")
    if summary.get("auto_action_target_contract_failures"):
        blockers.append("auto_action_target_contract_failures")
    if summary.get("auto_visible_leakage_rows"):
        blockers.append("auto_visible_leakage_rows")

    for field, expected in PILOT_READY_EXPECTED_LABELS.items():
        for row in rows:
            value = str(row.get(field, "")).strip().lower()
            if value and value != expected:
                blockers.append(f"{field}_{value}")
                break
    return sorted(set(blockers))


def validate_surface_cue_design_review_csv(worksheet_path: Path, out_dir: Path) -> Dict[str, Any]:
    rows = read_design_review_csv(worksheet_path)
    base_summary = validate_surface_cue_design_review_rows(rows)
    target_claim_ids = [str(row.get("target_claim_id", "")).strip() for row in rows]
    target_claim_counts = Counter(target_claim_ids)
    missing_columns = [field for field in DESIGN_REVIEW_FIELDNAMES if rows and field not in rows[0]]
    summary: Dict[str, Any] = {
        **base_summary,
        "worksheet_path": str(worksheet_path),
        "missing_columns": missing_columns,
        "duplicate_target_claim_ids": sorted(claim_id for claim_id, count in target_claim_counts.items() if claim_id and count > 1),
        "auto_pair_contract_failures": sum(1 for row in rows if str(row.get("auto_pair_contract_ok", "")).strip().lower() != "yes"),
        "auto_retrieval_observability_failures": sum(1 for row in rows if str(row.get("auto_retrieval_observability_ok", "")).strip().lower() != "yes"),
        "auto_action_target_contract_failures": sum(1 for row in rows if str(row.get("auto_action_target_contract_ok", "")).strip().lower() != "yes"),
        "auto_visible_leakage_rows": sum(1 for row in rows if str(row.get("auto_visible_leakage_count", "")).strip() not in {"", "0"}),
        "label_value_counts": label_value_counts(rows),
    }
    blockers = design_review_pilot_blockers(rows, summary)
    summary["pilot_blockers"] = blockers
    summary["pilot_ready"] = not blockers

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_step2_surface_cue_design_review_validation.json", summary)
    (out_dir / "eha-step2-surface-cue-design-review-validation-2026-05-16.md").write_text(
        render_surface_cue_design_review_validation_markdown(summary),
        encoding="utf-8",
    )
    return summary


def render_surface_cue_design_review_validation_markdown(summary: Mapping[str, Any]) -> str:
    blockers = summary.get("pilot_blockers", [])
    lines = [
        "# EHA Step 2 Surface-Cue Design Review Validation",
        "",
        "Date: 2026-05-16",
        "",
        f"- Worksheet: `{summary['worksheet_path']}`",
        f"- Status: `{summary['status']}`",
        f"- Pair rows: {summary['n_pairs']}",
        f"- Reviewed pairs: {summary['n_reviewed']}",
        f"- Missing label cells: {summary['missing_label_cells']}",
        f"- Invalid label cells: {summary['invalid_label_cells']}",
        f"- Missing notes: {summary['missing_notes']}",
        f"- Pilot ready: `{str(summary['pilot_ready']).lower()}`",
        "",
        "## Pilot Blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- None")
    lines.extend(["", "## Label Counts", ""])
    for field, counts in summary["label_value_counts"].items():
        lines.append(f"- `{field}`: {counts}")
    lines.append("")
    return "\n".join(lines)


@app.command()
def main(
    worksheet_path: Path = typer.Option(Path("../reports/surface_cue_design_review_worksheet.csv"), help="Completed design-review worksheet CSV."),
    out_dir: Path = typer.Option(Path("../reports"), help="Output report directory."),
) -> None:
    summary = validate_surface_cue_design_review_csv(worksheet_path, out_dir)
    console.print(
        f"[green]Validated[/green] surface-cue design review: status={summary['status']}; pilot_ready={summary['pilot_ready']}"
    )


if __name__ == "__main__":
    app()
