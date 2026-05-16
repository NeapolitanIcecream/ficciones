from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping

import typer
from rich.console import Console

from .schemas import write_json


app = typer.Typer(add_completion=False, help="Build and validate the EHA Step 2 target venue/budget context.")
console = Console()


REQUIRED_NONBLANK_FIELDS = ["target_venue", "target_deadline", "submission_track", "decision_owner"]
REQUIRED_TRUE_FIELDS = ["budget_confirmed", "human_review_budget_confirmed", "approval_required_before_model_calls"]
REQUIRED_POSITIVE_BUDGET_FIELDS = ["max_step2_api_budget_usd", "human_review_budget_usd"]


def build_default_target_context() -> Dict[str, Any]:
    return {
        "date": "2026-05-16",
        "status": "incomplete",
        "target_venue": "",
        "target_deadline": "",
        "submission_track": "",
        "decision_owner": "",
        "budget_confirmed": False,
        "max_step2_api_budget_usd": 0.0,
        "human_review_budget_confirmed": False,
        "human_review_budget_usd": 0.0,
        "approval_required_before_model_calls": True,
        "candidate_paths": [
            {
                "path_id": "workshop_arxiv_v1_first",
                "description": "Release Step 1 as a controlled diagnostic benchmark only after the independent human audit is complete.",
                "api_boundary": "No new model calls required.",
            },
            {
                "path_id": "main_conference_step2_after_gates",
                "description": "Prepare a larger benchmark/evaluation submission only after Step 1 human audit, surface-cue design review, schema repair, target venue, and budget gates clear.",
                "api_boundary": "Requires explicit approval and budget before fixed-slice or larger API runs.",
            },
        ],
        "notes": "Fill this file before any new Step 2 model/API pilot. Do not mark budgets confirmed unless the human-review and API spend caps are approved.",
    }


def _as_positive_float(context: Mapping[str, Any], key: str) -> bool:
    try:
        return float(context.get(key, 0.0)) > 0.0
    except (TypeError, ValueError):
        return False


def validate_target_context(context: Mapping[str, Any]) -> Dict[str, Any]:
    context_with_defaults = build_default_target_context()
    context_with_defaults.update(dict(context))
    missing_fields = []
    for field in REQUIRED_NONBLANK_FIELDS:
        if not str(context_with_defaults.get(field, "")).strip():
            missing_fields.append(field)
    for field in REQUIRED_TRUE_FIELDS:
        if context_with_defaults.get(field) is not True:
            missing_fields.append(field)
    for field in REQUIRED_POSITIVE_BUDGET_FIELDS:
        if not _as_positive_float(context_with_defaults, field):
            missing_fields.append(field)

    ready = not missing_fields
    return {
        "date": "2026-05-16",
        "status": "ready" if ready else "incomplete",
        "ready": ready,
        "target_venue": str(context_with_defaults.get("target_venue", "")).strip(),
        "target_deadline": str(context_with_defaults.get("target_deadline", "")).strip(),
        "submission_track": str(context_with_defaults.get("submission_track", "")).strip(),
        "decision_owner": str(context_with_defaults.get("decision_owner", "")).strip(),
        "budget_confirmed": bool(context_with_defaults.get("budget_confirmed", False)),
        "max_step2_api_budget_usd": float(context_with_defaults.get("max_step2_api_budget_usd", 0.0) or 0.0),
        "human_review_budget_confirmed": bool(context_with_defaults.get("human_review_budget_confirmed", False)),
        "human_review_budget_usd": float(context_with_defaults.get("human_review_budget_usd", 0.0) or 0.0),
        "approval_required_before_model_calls": bool(context_with_defaults.get("approval_required_before_model_calls", False)),
        "missing_fields": missing_fields,
        "candidate_paths": context_with_defaults.get("candidate_paths", []),
        "non_claims": [
            "not model evidence",
            "not permission to run model/API calls",
            "not a substitute for Step 1 human audit or surface-cue design review",
            "not a budget approval unless budget_confirmed and human_review_budget_confirmed are true",
        ],
    }


def render_target_context_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# EHA Step 2 Target Context",
        "",
        "Date: 2026-05-16",
        "",
        f"- Status: `{summary['status']}`",
        f"- Ready: `{str(summary['ready']).lower()}`",
        f"- Target venue: `{summary['target_venue'] or 'TBD'}`",
        f"- Target deadline: `{summary['target_deadline'] or 'TBD'}`",
        f"- Submission track: `{summary['submission_track'] or 'TBD'}`",
        f"- Decision owner: `{summary['decision_owner'] or 'TBD'}`",
        f"- API budget confirmed: `{str(summary['budget_confirmed']).lower()}`",
        f"- Max Step 2 API budget USD: `{float(summary['max_step2_api_budget_usd']):.2f}`",
        f"- Human-review budget confirmed: `{str(summary['human_review_budget_confirmed']).lower()}`",
        f"- Human-review budget USD: `{float(summary['human_review_budget_usd']):.2f}`",
        f"- Explicit approval required before model calls: `{str(summary['approval_required_before_model_calls']).lower()}`",
        "",
        "This is a no-API decision context for the Step 2 launch gate. It records whether the project has an explicit target venue, deadline, and approved budget before any further model spend.",
        "",
        "## Missing Fields",
        "",
    ]
    if summary["missing_fields"]:
        lines.extend(f"- `{field}`" for field in summary["missing_fields"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Candidate Paths", ""])
    for path in summary.get("candidate_paths", []):
        lines.extend(
            [
                f"### {path.get('path_id', 'unnamed_path')}",
                "",
                f"- Description: {path.get('description', '')}",
                f"- API boundary: {path.get('api_boundary', '')}",
                "",
            ]
        )
    lines.extend(["## Non-Claims", ""])
    lines.extend(f"- {claim}" for claim in summary["non_claims"])
    lines.append("")
    return "\n".join(lines)


def load_target_context(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return build_default_target_context()
    return json.loads(path.read_text(encoding="utf-8"))


def write_target_context_artifacts(out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    context_path = out_dir / "eha_step2_target_context.json"
    if context_path.exists():
        context = load_target_context(context_path)
    else:
        context = build_default_target_context()
        write_json(context_path, context)
    summary = validate_target_context(context)
    write_json(out_dir / "eha_step2_target_context_validation.json", summary)
    (out_dir / "eha-step2-target-context-2026-05-16.md").write_text(
        render_target_context_markdown(summary),
        encoding="utf-8",
    )
    return summary


@app.command()
def main(out_dir: Path = typer.Option(Path("../reports"), help="Output report directory.")) -> None:
    summary = write_target_context_artifacts(out_dir)
    console.print(f"[green]Wrote[/green] Step 2 target context: status={summary['status']}; ready={summary['ready']}")


if __name__ == "__main__":
    app()
