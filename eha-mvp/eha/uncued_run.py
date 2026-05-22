from __future__ import annotations

import json
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import typer
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard
from .epistemic_frontier_main import (
    FrontierModelProfile,
    completed_job_keys,
    load_run_records,
    profile_groups,
    run_plan_payload,
    run_profile_group_stream,
)
from .epistemic_model_preflight import load_preflight_tasks, provider_for_model
from .epistemic_resilience import EpistemicRunRecord, EpistemicTask
from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_contract import DEFAULT_VIEWS, split_csv


app = typer.Typer(add_completion=False, help="Run EHA-Uncued pilot model calls after pre-model gates pass.")
console = Console()

PROMPT_CONDITIONS = {"standard_answer", "epistemic_hygiene_instruction"}
HIDDEN_PROMPT_MARKERS = (
    '"gold_verdict"',
    '"hidden_role"',
    '"internal_doc_id"',
    '"supports_gold_verdict"',
    '"known_polluted',
    "false_consensus",
    "buried_primary",
    "generated_lore",
    "conflicting_evidence",
)


def uncued_view(task: EpistemicTask) -> str:
    return task.source_task_id.rsplit(":", 1)[1] if ":" in task.source_task_id else ""


def base_uncued_task_id(task: EpistemicTask) -> str:
    return task.source_task_id.split(":", 1)[0] if ":" in task.source_task_id else task.task_id.rsplit("_", 1)[0]


def selected_uncued_tasks(dataset_dir: Path, views: Sequence[str]) -> List[EpistemicTask]:
    selected_views = set(views)
    tasks = [task for task in load_preflight_tasks(dataset_dir) if uncued_view(task) in selected_views]
    if not tasks:
        raise typer.BadParameter(f"no uncued tasks found for views: {', '.join(sorted(selected_views))}")
    return tasks


def uncued_model_profiles(
    models: str,
    *,
    deepseek_response_format: str = "json_object",
    max_output_tokens: int = 4096,
    timeout_s: float = 240.0,
) -> List[FrontierModelProfile]:
    selected_models = split_csv(models)
    if not selected_models:
        raise typer.BadParameter("at least one model is required")
    profiles: List[FrontierModelProfile] = []
    for model in selected_models:
        provider = provider_for_model(model)
        response_format = deepseek_response_format if provider == "DeepSeek" else "json_schema"
        profiles.append(
            FrontierModelProfile(
                provider=provider,
                model=model,
                budget_setting="operational",
                temperature=None,
                max_output_tokens=max_output_tokens,
                response_format=response_format,
                timeout_s=timeout_s,
                cost_estimate_output_tokens=max_output_tokens,
            )
        )
    return profiles


def invocation_profiles_payload(
    profiles: Sequence[FrontierModelProfile],
    *,
    schema: str,
    prompt: str,
    views: Sequence[str],
    max_attempts: int,
    parallel_models: int,
) -> Dict[str, Any]:
    profile_rows = []
    for profile in profiles:
        profile_rows.append(
            {
                "model": profile.model,
                "provider": profile.provider,
                "budget_setting": profile.budget_setting,
                "timeout_s": profile.timeout_s,
                "cost_estimate_output_tokens": profile.cost_estimate_output_tokens,
                "invocation_profile": profile.invocation(),
                "retry_profile": {
                    "max_attempts": max_attempts,
                    "llm_repair": "disabled",
                    "json_extractor": profile.json_extractor,
                    "response_format": profile.response_format,
                    "temperature_policy": "omitted" if profile.temperature is None else f"explicit:{profile.temperature}",
                    "max_completion_tokens_policy": "omitted" if not profile.max_output_tokens else f"explicit:{profile.max_output_tokens}",
                },
            }
        )
    deepseek_rows = [row for row in profile_rows if row["provider"] == "DeepSeek"]
    return {
        "schema_variant": schema,
        "prompt_condition": prompt,
        "views": list(views),
        "parallel_strategy": {
            "parallel_model_streams": min(parallel_models, len(profiles)),
            "per_model_concurrency": 1,
        },
        "profiles": profile_rows,
        "deepseek_profiles": deepseek_rows,
    }


def prompt_audit_summary(records: Sequence[EpistemicRunRecord]) -> Dict[str, Any]:
    totals = Counter()
    hidden_field_values: Counter[str] = Counter()
    for record in records:
        audit = record.invocation_profile.get("visible_prompt_audit", {})
        totals["records"] += 1
        totals["semantic_doc_id_hits"] += int(audit.get("semantic_doc_id_hits", 0) or 0)
        totals["semantic_visible_citation_hits"] += int(audit.get("semantic_visible_citation_hits", 0) or 0)
        totals["audit_id_hits_in_title_or_body"] += int(audit.get("audit_id_hits_in_title_or_body", 0) or 0)
        hidden_hits = audit.get("hidden_field_hits", [])
        if isinstance(hidden_hits, list):
            totals["hidden_field_hit_count"] += len(hidden_hits)
            hidden_field_values.update(str(item) for item in hidden_hits)
    passed = all(
        totals[key] == 0
        for key in (
            "semantic_doc_id_hits",
            "semantic_visible_citation_hits",
            "audit_id_hits_in_title_or_body",
            "hidden_field_hit_count",
        )
    )
    return {
        "records": totals["records"],
        "semantic_doc_id_hits": totals["semantic_doc_id_hits"],
        "semantic_visible_citation_hits": totals["semantic_visible_citation_hits"],
        "audit_id_hits_in_title_or_body": totals["audit_id_hits_in_title_or_body"],
        "hidden_field_hit_count": totals["hidden_field_hit_count"],
        "hidden_field_hits": dict(sorted(hidden_field_values.items())),
        "passed": passed,
    }


def stored_hidden_label_audit(out_dir: Path) -> Dict[str, Any]:
    prompt_hits: List[Dict[str, str]] = []
    output_hits: List[Dict[str, str]] = []
    for path in sorted((out_dir / "artifacts").glob("**/*.prompt.json")):
        text = path.read_text(encoding="utf-8")
        for marker in HIDDEN_PROMPT_MARKERS:
            if marker in text:
                prompt_hits.append({"path": str(path.relative_to(out_dir)), "marker": marker})
    for path in sorted((out_dir / "artifacts").glob("**/*.response.json")):
        text = path.read_text(encoding="utf-8")
        for marker in HIDDEN_PROMPT_MARKERS:
            if marker in text:
                output_hits.append({"path": str(path.relative_to(out_dir)), "marker": marker})
    return {
        "prompt_hit_count": len(prompt_hits),
        "output_hit_count": len(output_hits),
        "prompt_hits": prompt_hits[:50],
        "output_hits": output_hits[:50],
        "passed": not prompt_hits and not output_hits,
    }


def model_run_summary(records: Sequence[EpistemicRunRecord]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str], List[EpistemicRunRecord]] = {}
    for record in records:
        grouped.setdefault((record.model, record.provider), []).append(record)
    rows: List[Dict[str, Any]] = []
    for (model, provider), group in sorted(grouped.items()):
        n = len(group)
        parse_success = sum(1 for record in group if record.parse_success)
        empty_outputs = sum(1 for record in group if record.empty_output)
        schema_missing = sum(1 for record in group if record.schema_missing)
        timeout_count = sum(1 for record in group if "timeout" in record.parse_error.lower())
        rows.append(
            {
                "model": model,
                "provider": provider,
                "n": n,
                "parse_success_count": parse_success,
                "parse_success_rate": parse_success / n if n else 0.0,
                "empty_output_count": empty_outputs,
                "schema_missing_count": schema_missing,
                "timeout_count": timeout_count,
                "cost_usd": round(sum(record.cost_usd for record in group), 6),
            }
        )
    return rows


def write_phase12_summary(path: Path, *, manifest: Mapping[str, Any], model_summary: Sequence[Mapping[str, Any]], prompt_audit: Mapping[str, Any], hidden_label_audit: Mapping[str, Any], cost_report: Mapping[str, Any]) -> None:
    lines = [
        "# EHA-Uncued Phase 12 Pilot Run",
        "",
        "## Run Plan",
        "",
        "```json",
        json.dumps(manifest, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Model Summary",
        "",
    ]
    lines.extend(markdown_table(model_summary, ["model", "provider", "n", "parse_success_rate", "empty_output_count", "schema_missing_count", "timeout_count", "cost_usd"]))
    lines.extend(
        [
            "",
            "## Prompt Audit",
            "",
            "```json",
            json.dumps(prompt_audit, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Stored Hidden Label Audit",
            "",
            "```json",
            json.dumps(hidden_label_audit, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Cost Report",
            "",
            "```json",
            json.dumps(cost_report, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Pilot dataset directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Run output directory."),
    models: str = typer.Option("", help="Comma-separated model list."),
    views: str = typer.Option(",".join(DEFAULT_VIEWS), help="Comma-separated views."),
    schema: str = typer.Option("clarified", help="Schema variant."),
    prompt: str = typer.Option("standard_answer", help="Prompt condition."),
    hard_cap_usd: float = typer.Option(15.0, help="Hard cost cap."),
    soft_cap_usd: float = typer.Option(10.0, help="Soft cost cap."),
    abort_cap_usd: float = typer.Option(20.0, help="Abort cost cap."),
    max_output_tokens: int = typer.Option(4096, help="Model output token cap."),
    timeout_s: float = typer.Option(240.0, help="Per-call process timeout."),
    parallel_models: int = typer.Option(4, help="Number of model streams to run concurrently."),
    max_attempts: int = typer.Option(2, help="Attempts per call for transient failures."),
    resume: bool = typer.Option(True, help="Skip completed rows already in predictions.jsonl."),
    deepseek_response_format: str = typer.Option("json_object", help="DeepSeek response format from Phase 11 retry."),
) -> None:
    if schema != "clarified":
        raise typer.BadParameter("schema must be clarified")
    if prompt not in PROMPT_CONDITIONS:
        raise typer.BadParameter("prompt must be standard_answer or epistemic_hygiene_instruction")
    selected_views = split_csv(views)
    tasks = selected_uncued_tasks(dataset_dir, selected_views)
    profiles = uncued_model_profiles(
        models,
        deepseek_response_format=deepseek_response_format,
        max_output_tokens=max_output_tokens,
        timeout_s=timeout_s,
    )
    prompts = [prompt]
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "predictions.jsonl"
    completed = completed_job_keys(predictions_path) if resume else set()
    plan_payload = run_plan_payload(tasks, profiles, prompts, parallel_models=parallel_models, max_attempts=max_attempts)
    manifest = {
        **plan_payload,
        "name": "EHA-Uncued Phase 12 Pilot Run",
        "dataset_dir": str(dataset_dir),
        "views": selected_views,
        "schema_variant": schema,
        "prompt_condition": prompt,
        "resume_completed_count": len(completed),
    }
    write_json(out_dir / "run_manifest.json", manifest)
    write_json(
        out_dir / "invocation_profiles.json",
        invocation_profiles_payload(
            profiles,
            schema=schema,
            prompt=prompt,
            views=selected_views,
            max_attempts=max_attempts,
            parallel_models=parallel_models,
        ),
    )

    write_lock = threading.Lock()
    cost_lock = threading.Lock()
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    try:
        groups = profile_groups(profiles)
        with ThreadPoolExecutor(max_workers=max(1, min(parallel_models, len(groups)))) as executor:
            futures = [
                executor.submit(
                    run_profile_group_stream,
                    profiles=group,
                    tasks=tasks,
                    prompt_conditions=prompts,
                    out_dir=out_dir,
                    predictions_path=predictions_path,
                    completed=completed,
                    write_lock=write_lock,
                    cost_guard=cost_guard,
                    cost_lock=cost_lock,
                    max_attempts=max_attempts,
                )
                for group in groups
            ]
            for future in as_completed(futures):
                future.result()
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise typer.Exit(code=2) from exc

    records = load_run_records(predictions_path)
    cost_report = {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in records), 6), **cost_guard.report()}
    prompt_audit = prompt_audit_summary(records)
    hidden_label_audit = stored_hidden_label_audit(out_dir)
    summary_rows = model_run_summary(records)
    write_json(out_dir / "cost_report.json", cost_report)
    write_json(out_dir / "prompt_audit_summary.json", prompt_audit)
    write_json(out_dir / "stored_hidden_label_audit.json", hidden_label_audit)
    write_csv(out_dir / "run_summary_by_model.csv", summary_rows)
    write_phase12_summary(out_dir / "phase12_run_summary.md", manifest=manifest, model_summary=summary_rows, prompt_audit=prompt_audit, hidden_label_audit=hidden_label_audit, cost_report=cost_report)
    console.print(f"[green]Wrote EHA-Uncued Phase 12 pilot run[/green] to {out_dir}")
