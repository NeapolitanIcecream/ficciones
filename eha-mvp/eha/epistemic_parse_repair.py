from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard
from .epistemic_resilience import (
    EpistemicPrediction,
    EpistemicRunRecord,
    EpistemicTask,
    build_messages,
    epistemic_prediction_json_schema,
    markdown_table,
    normalize_prediction,
    parse_prediction,
    read_tasks,
    score_records,
)
from .phase2_run import Phase2OpenAIJsonRunner
from .report import write_csv
from .schemas import model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Run a raw-response-preserving parse repair audit for ERT v1.")
console = Console()

REPAIR_METRICS = ("parse_success", "epistemic_escape", "belief_correctness", "evidence_cleanliness")


def read_records(path: Path) -> List[EpistemicRunRecord]:
    return [EpistemicRunRecord.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def safe_name(value: str) -> str:
    return value.replace("/", "_").replace(":", "_")


def record_key(record: EpistemicRunRecord) -> tuple[str, str, str]:
    return (record.task_id, record.model, record.prompt_condition)


def row_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (str(row["task_id"]), str(row["model"]), str(row["prompt_condition"]))


def mean(rows: Sequence[Mapping[str, Any]], metric: str) -> float:
    values = [float(row[metric]) for row in rows if row.get(metric) not in {None, ""}]
    return sum(values) / len(values) if values else 0.0


def usage_sum(usages: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cost"):
        values = [usage.get(key) for usage in usages if isinstance(usage.get(key), (int, float))]
        if values:
            output[key] = sum(values)
    reasoning_values = []
    for usage in usages:
        details = usage.get("completion_tokens_details") if isinstance(usage, Mapping) else None
        if isinstance(details, Mapping) and isinstance(details.get("reasoning_tokens"), (int, float)):
            reasoning_values.append(details["reasoning_tokens"])
    if reasoning_values:
        output["completion_tokens_details"] = {"reasoning_tokens": sum(reasoning_values)}
    return output


def repair_messages(task: EpistemicTask, *, previous_response: str, parse_error: str) -> List[Dict[str, str]]:
    payload = {
        "task": "epistemic_resilience_v1_json_repair",
        "instruction": (
            "Repair the previous answer into exactly one JSON object matching the schema. "
            "Use only the provided evidence environment and doc_id strings. If the previous "
            "answer is empty or unusable, answer the original task from the provided evidence."
        ),
        "family": task.family,
        "condition": task.condition,
        "question": task.question,
        "documents": [
            {
                "doc_id": doc.doc_id,
                "title": doc.title,
                "source_type": doc.source_type,
                "timestamp": doc.timestamp,
                "body": doc.body,
                "visible_citations": doc.visible_citations,
            }
            for doc in task.documents
        ],
        "schema": epistemic_prediction_json_schema(),
        "previous_response": previous_response[:8000],
        "parse_error": parse_error[:1000],
    }
    return [
        {"role": "developer", "content": "You repair malformed model output into valid, schema-compliant JSON only."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def artifact_paths(out_dir: Path, *, model: str, prompt_condition: str, task_id: str, attempt: str) -> tuple[Path, Path]:
    base = out_dir / "artifacts" / safe_name(model) / prompt_condition
    return base / f"{task_id}.{attempt}.prompt.json", base / f"{task_id}.{attempt}.response.json"


def write_attempt_artifacts(
    out_dir: Path,
    *,
    model: str,
    prompt_condition: str,
    task_id: str,
    attempt: str,
    messages: Sequence[Mapping[str, str]],
    response_text: str,
    usage: Mapping[str, Any],
    response_format: str,
    parse_success: bool,
    parse_error: str,
) -> tuple[str, str]:
    prompt_path, response_path = artifact_paths(out_dir, model=model, prompt_condition=prompt_condition, task_id=task_id, attempt=attempt)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        prompt_path,
        {
            "task_id": task_id,
            "model": model,
            "prompt_condition": prompt_condition,
            "attempt": attempt,
            "messages": list(messages),
            "response_format": response_format,
        },
    )
    write_json(
        response_path,
        {
            "task_id": task_id,
            "model": model,
            "prompt_condition": prompt_condition,
            "attempt": attempt,
            "response_text": response_text,
            "usage": dict(usage),
            "parse_success": parse_success,
            "parse_error": parse_error,
        },
    )
    return str(prompt_path), str(response_path)


def parse_or_failure(response_text: str, task: EpistemicTask) -> tuple[EpistemicPrediction, bool, str]:
    try:
        return normalize_prediction(parse_prediction(response_text), task), True, ""
    except Exception as exc:  # noqa: BLE001
        return (
            EpistemicPrediction(
                claim_verdict="insufficient",
                confidence=0.0,
                evidence_environment_assessment="Response failed to parse during parse-repair audit.",
                answer="Parse repair failure.",
            ),
            False,
            str(exc),
        )


def api_complete(
    runner: Phase2OpenAIJsonRunner,
    cost_guard: CostGuard,
    *,
    model: str,
    messages: Sequence[Dict[str, str]],
    max_output_tokens: int,
    temperature: float,
) -> tuple[str, Dict[str, Any], str, float]:
    cost_guard.before_call(model, json.dumps(messages, ensure_ascii=False), max_output_tokens)
    response_text, usage, used_format = runner.complete(
        model=model,
        messages=messages,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        schema_name="eha_epistemic_prediction",
        schema=epistemic_prediction_json_schema(),
    )
    return response_text, usage, used_format, cost_guard.after_call(model, usage)


def repair_one_record(
    *,
    runner: Phase2OpenAIJsonRunner,
    cost_guard: CostGuard,
    original: EpistemicRunRecord,
    task: EpistemicTask,
    out_dir: Path,
    max_output_tokens: int,
    repair_max_output_tokens: int,
    temperature: float,
) -> tuple[EpistemicRunRecord, Dict[str, Any]]:
    total_cost = 0.0
    usages: List[Mapping[str, Any]] = []
    artifacts: Dict[str, str] = {}

    direct_messages = build_messages(task, original.prompt_condition)
    try:
        direct_response, direct_usage, direct_format, direct_cost = api_complete(
            runner,
            cost_guard,
            model=original.model,
            messages=direct_messages,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
        )
        total_cost += direct_cost
        usages.append(direct_usage)
        direct_prediction, direct_success, direct_error = parse_or_failure(direct_response, task)
    except Exception as exc:  # noqa: BLE001
        direct_response = ""
        direct_usage = {}
        direct_format = "api_error"
        direct_prediction = EpistemicPrediction(
            claim_verdict="insufficient",
            confidence=0.0,
            evidence_environment_assessment="Direct rerun API call failed.",
            answer="API failure.",
        )
        direct_success = False
        direct_error = str(exc)

    prompt_path, response_path = write_attempt_artifacts(
        out_dir,
        model=original.model,
        prompt_condition=original.prompt_condition,
        task_id=original.task_id,
        attempt="direct",
        messages=direct_messages,
        response_text=direct_response,
        usage=direct_usage,
        response_format=direct_format,
        parse_success=direct_success,
        parse_error=direct_error,
    )
    artifacts["direct_prompt_path"] = prompt_path
    artifacts["direct_response_path"] = response_path

    final_prediction = direct_prediction
    final_success = direct_success
    final_error = direct_error
    repair_success = False
    repair_error = ""
    repair_format = ""
    repair_response = ""

    if not direct_success:
        retry_messages = repair_messages(task, previous_response=direct_response, parse_error=direct_error)
        try:
            repair_response, repair_usage, repair_format, repair_cost = api_complete(
                runner,
                cost_guard,
                model=original.model,
                messages=retry_messages,
                max_output_tokens=repair_max_output_tokens,
                temperature=temperature,
            )
            total_cost += repair_cost
            usages.append(repair_usage)
            final_prediction, repair_success, repair_error = parse_or_failure(repair_response, task)
            final_success = repair_success
            final_error = repair_error
        except Exception as exc:  # noqa: BLE001
            repair_usage = {}
            repair_format = "api_error"
            repair_success = False
            repair_error = str(exc)
            final_prediction = EpistemicPrediction(
                claim_verdict="insufficient",
                confidence=0.0,
                evidence_environment_assessment="Repair retry API call failed.",
                answer="API repair failure.",
            )
            final_success = False
            final_error = repair_error

        prompt_path, response_path = write_attempt_artifacts(
            out_dir,
            model=original.model,
            prompt_condition=original.prompt_condition,
            task_id=original.task_id,
            attempt="repair",
            messages=retry_messages,
            response_text=repair_response,
            usage=repair_usage,
            response_format=repair_format,
            parse_success=repair_success,
            parse_error=repair_error,
        )
        artifacts["repair_prompt_path"] = prompt_path
        artifacts["repair_response_path"] = response_path

    repaired_record = EpistemicRunRecord(
        task_id=original.task_id,
        family=original.family,
        condition=original.condition,
        model=original.model,
        prompt_condition=original.prompt_condition,
        backend="api_parse_repair",
        prediction=final_prediction,
        parse_success=final_success,
        parse_error=final_error,
        usage=usage_sum(usages),
        cost_usd=total_cost,
    )
    attempt_row: Dict[str, Any] = {
        "task_id": original.task_id,
        "family": original.family,
        "condition": original.condition,
        "model": original.model,
        "prompt_condition": original.prompt_condition,
        "original_parse_success": 1.0 if original.parse_success else 0.0,
        "original_parse_error": original.parse_error,
        "direct_parse_success": 1.0 if direct_success else 0.0,
        "direct_parse_error": direct_error,
        "repair_attempted": 0.0 if direct_success else 1.0,
        "repair_parse_success": "" if direct_success else (1.0 if repair_success else 0.0),
        "repair_parse_error": "" if direct_success else repair_error,
        "final_parse_success": 1.0 if final_success else 0.0,
        "final_parse_error": final_error,
        "cost_usd": total_cost,
        **artifacts,
    }
    return repaired_record, attempt_row


def comparison_rows(original_rows: Sequence[Mapping[str, Any]], repaired_rows: Sequence[Mapping[str, Any]], attempted_keys: set[tuple[str, str, str]]) -> List[Dict[str, Any]]:
    original_by_key = {row_key(row): row for row in original_rows}
    repaired_by_key = {row_key(row): row for row in repaired_rows}
    keys = sorted(set(original_by_key) & set(repaired_by_key))
    groups: Dict[tuple[str, str, str], List[tuple[Mapping[str, Any], Mapping[str, Any]]]] = defaultdict(list)
    for key in keys:
        original = original_by_key[key]
        repaired = repaired_by_key[key]
        groups[("all", "all", "all")].append((original, repaired))
        groups[("prompt_condition", str(original["prompt_condition"]), "all")].append((original, repaired))
        groups[("family", str(original["family"]), "all")].append((original, repaired))
        groups[("condition", str(original["condition"]), "all")].append((original, repaired))
        groups[("prompt_family", str(original["prompt_condition"]), str(original["family"]))].append((original, repaired))
    output: List[Dict[str, Any]] = []
    for (scope, value, subvalue), pairs in sorted(groups.items()):
        original_group = [pair[0] for pair in pairs]
        repaired_group = [pair[1] for pair in pairs]
        item: Dict[str, Any] = {
            "scope": scope,
            "value": value,
            "subvalue": subvalue,
            "n": len(pairs),
            "repair_attempted_count": sum(1 for row, _ in pairs if row_key(row) in attempted_keys),
        }
        for metric in REPAIR_METRICS:
            original_value = mean(original_group, metric)
            repaired_value = mean(repaired_group, metric)
            item[f"original_{metric}"] = original_value
            item[f"repaired_{metric}"] = repaired_value
            item[f"delta_{metric}"] = repaired_value - original_value
        output.append(item)
    return output


def write_summary(
    path: Path,
    *,
    target_model: str,
    attempt_rows: Sequence[Mapping[str, Any]],
    comparison: Sequence[Mapping[str, Any]],
    cost_report: Mapping[str, Any],
) -> None:
    direct_success = sum(1 for row in attempt_rows if float(row["direct_parse_success"]) == 1.0)
    repair_attempted = sum(1 for row in attempt_rows if float(row["repair_attempted"]) == 1.0)
    repair_success = sum(1 for row in attempt_rows if row["repair_parse_success"] != "" and float(row["repair_parse_success"]) == 1.0)
    final_success = sum(1 for row in attempt_rows if float(row["final_parse_success"]) == 1.0)
    top_rows = [row for row in comparison if row["scope"] in {"all", "prompt_condition", "family"}]
    lines = [
        f"# EHA Parse Repair Audit: {target_model}",
        "",
        "This report is separate from the main Epistemic Resilience Table. It reruns only original parse-failed rows, preserves raw prompt/response artifacts, and does not merge repaired metrics into the main table.",
        "",
        "## Repair Outcomes",
        "",
        f"- Attempted original parse-failed rows: {len(attempt_rows)}.",
        f"- Direct rerun parse successes: {direct_success}.",
        f"- JSON repair retries attempted: {repair_attempted}.",
        f"- JSON repair retry successes: {repair_success}.",
        f"- Final repaired parse successes: {final_success}.",
        "",
        "## Original vs Repaired",
        "",
    ]
    lines.extend(markdown_table(top_rows, ["scope", "value", "subvalue", "n", "repair_attempted_count", "original_parse_success", "repaired_parse_success", "original_epistemic_escape", "repaired_epistemic_escape", "original_belief_correctness", "repaired_belief_correctness", "original_evidence_cleanliness", "repaired_evidence_cleanliness"]))
    lines.extend(["", "## Cost Report", "", "```json", json.dumps(cost_report, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run_parse_repair(
    *,
    task_dir: Path,
    original_run_dir: Path,
    original_report_dir: Path,
    out_dir: Path,
    target_model: str,
    max_output_tokens: int,
    repair_max_output_tokens: int,
    temperature: float,
    response_format: str,
    soft_cap_usd: float,
    hard_cap_usd: float,
    abort_cap_usd: float,
) -> Dict[str, Any]:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    tasks_by_id = {task.task_id: task for task in tasks}
    original_records = read_records(original_run_dir / "predictions.jsonl")
    original_scored_rows = []
    original_scored_path = original_report_dir / "scored_predictions.csv"
    if original_scored_path.exists():
        import csv

        with original_scored_path.open(encoding="utf-8", newline="") as handle:
            original_scored_rows = [row for row in csv.DictReader(handle) if row["model"] == target_model]

    failed = [record for record in original_records if record.model == target_model and not record.parse_success]
    runner = Phase2OpenAIJsonRunner(timeout_s=240.0, response_format=response_format)
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    out_dir.mkdir(parents=True, exist_ok=True)

    repaired_records: List[EpistemicRunRecord] = []
    attempt_rows: List[Dict[str, Any]] = []
    try:
        for original in failed:
            repaired, attempt = repair_one_record(
                runner=runner,
                cost_guard=cost_guard,
                original=original,
                task=tasks_by_id[original.task_id],
                out_dir=out_dir,
                max_output_tokens=max_output_tokens,
                repair_max_output_tokens=repair_max_output_tokens,
                temperature=temperature,
            )
            repaired_records.append(repaired)
            attempt_rows.append(attempt)
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise

    repairs_by_key = {record_key(record): record for record in repaired_records}
    combined_records = [
        repairs_by_key.get(record_key(record), record)
        for record in original_records
        if record.model == target_model
    ]
    repaired_failed_rows = score_records(repaired_records, tasks)
    combined_scored_rows = score_records(combined_records, tasks)
    comparison = comparison_rows(original_scored_rows, combined_scored_rows, set(repairs_by_key))
    cost_report = {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in repaired_records), 6), **cost_guard.report()}

    write_jsonl(out_dir / "parse_repair_predictions.jsonl", [model_to_dict(record) for record in repaired_records])
    write_jsonl(out_dir / "parse_repair_combined_predictions.jsonl", [model_to_dict(record) for record in combined_records])
    write_csv(out_dir / "parse_repair_attempts.csv", attempt_rows)
    write_csv(out_dir / "parse_repair_failed_rows_scored.csv", repaired_failed_rows)
    write_csv(out_dir / "parse_repair_combined_scored_predictions.csv", combined_scored_rows)
    write_csv(out_dir / "parse_repair_comparison.csv", comparison)
    write_json(out_dir / "cost_report.json", cost_report)
    manifest = {
        "name": "EHA gpt-5-mini parse repair audit",
        "target_model": target_model,
        "task_content_changed": False,
        "gold_labels_changed": False,
        "main_table_changed": False,
        "original_failed_count": len(failed),
        "repair_prediction_count": len(repaired_records),
        "combined_prediction_count": len(combined_records),
        "response_format": response_format,
        "max_output_tokens": max_output_tokens,
        "repair_max_output_tokens": repair_max_output_tokens,
        "attempt_rows": len(attempt_rows),
        "final_parse_success_count": sum(1 for row in attempt_rows if float(row["final_parse_success"]) == 1.0),
        "cost_report": cost_report,
    }
    write_json(out_dir / "audit_manifest.json", manifest)
    write_summary(out_dir / "summary.md", target_model=target_model, attempt_rows=attempt_rows, comparison=comparison, cost_report=cost_report)
    return manifest


@app.command("run")
def run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT v1 task directory."),
    original_run_dir: Path = typer.Option(Path("results/runs/epistemic-resilience-v1-api-final"), help="Original final API run directory."),
    original_report_dir: Path = typer.Option(Path("results/reports-epistemic-resilience-v1"), help="Original final report directory."),
    out_dir: Path = typer.Option(Path("results/reports-epistemic-parse-repair-gpt5mini"), help="Parse-repair output directory."),
    target_model: str = typer.Option("openai/gpt-5-mini", help="Model whose original parse-failed rows should be rerun."),
    max_output_tokens: int = typer.Option(4096, help="Direct rerun output token cap."),
    repair_max_output_tokens: int = typer.Option(2048, help="JSON repair retry output token cap."),
    temperature: float = typer.Option(0.0, help="Model temperature."),
    response_format: str = typer.Option("json_schema", help="json_schema, json_object, or none."),
    soft_cap_usd: float = typer.Option(5.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(15.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(25.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    try:
        manifest = run_parse_repair(
            task_dir=task_dir,
            original_run_dir=original_run_dir,
            original_report_dir=original_report_dir,
            out_dir=out_dir,
            target_model=target_model,
            max_output_tokens=max_output_tokens,
            repair_max_output_tokens=repair_max_output_tokens,
            temperature=temperature,
            response_format=response_format,
            soft_cap_usd=soft_cap_usd,
            hard_cap_usd=hard_cap_usd,
            abort_cap_usd=abort_cap_usd,
        )
    except BudgetExceeded as exc:
        console.print(f"[red]Budget exceeded[/red]: {exc}")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]Wrote parse-repair audit[/green] to {out_dir}")
    console.print_json(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    app()
