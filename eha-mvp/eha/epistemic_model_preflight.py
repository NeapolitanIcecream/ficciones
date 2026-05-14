from __future__ import annotations

import json
import multiprocessing
import signal
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path
from queue import Empty
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence

import typer
from loguru import logger
from pydantic import Field, ValidationError
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard
from .epistemic_resilience import (
    CONDITION_BY_DIFFICULTY,
    FAMILIES,
    EpistemicPrediction,
    EpistemicRunRecord,
    EpistemicTask,
    build_messages,
    epistemic_prediction_json_schema,
    invocation_profile,
    portable_chat_messages,
    read_tasks,
    score_records,
)
from .phase2_run import Phase2OpenAIJsonRunner, split_csv
from .report import markdown_table, write_csv
from .schemas import EhaModel, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Run structured-output model preflight for EHA cohorts.")
console = Console()
log = logger.bind(module="eha.epistemic_model_preflight")

DEFAULT_MAIN_CANDIDATES = (
    "gpt-5.4",
    "claude-opus-4-7",
    "gemini-3.1-pro-preview",
    "deepseek-v4-pro",
    "kimi-k2.6",
)
DEFAULT_FALLBACK_CANDIDATES = ("gemini-2.5-pro",)
GOOGLE_PRIMARY = "gemini-3.1-pro-preview"
GOOGLE_FALLBACK = "gemini-2.5-pro"

PRELIGHT_TASK_PLAN_20: Sequence[tuple[str, Mapping[str, int]]] = (
    ("clean", {"packet_judgment": 2, "evidence_selection": 1, "active_verification": 1}),
    ("conflicting_evidence", {"packet_judgment": 1, "evidence_selection": 2, "active_verification": 1}),
    ("false_consensus", {"packet_judgment": 2, "evidence_selection": 2, "active_verification": 0}),
    ("buried_primary", {"packet_judgment": 1, "evidence_selection": 2, "active_verification": 1}),
    ("generated_lore", {"packet_judgment": 2, "evidence_selection": 1, "active_verification": 1}),
)


class PredictionParseResult(EhaModel):
    parse_success: bool
    prediction: Optional[EpistemicPrediction] = None
    parse_error: str = ""
    schema_missing: bool = False
    json_extractor_used: str = "first_json_object"


class PreflightRecord(EhaModel):
    task_id: str
    family: str
    condition: str
    model: str
    prompt_condition: str
    parse_success: bool
    empty_output: bool
    schema_missing: bool
    parse_error: str = ""
    raw_content_preview: str = ""
    response_format_used: str = ""
    json_extractor_used: str = ""
    invocation_profile: Dict[str, Any] = Field(default_factory=dict)
    usage: Dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    prediction: Optional[EpistemicPrediction] = None


def extract_first_json_object(text: str) -> str:
    """Return the first syntactically valid JSON object embedded in text."""
    for start, character in enumerate(text):
        if character != "{":
            continue
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : index + 1]
                    try:
                        json.loads(candidate)
                    except json.JSONDecodeError:
                        break
                    return candidate
    raise ValueError("no JSON object found")


def schema_missing_from_validation_error(exc: ValidationError) -> bool:
    return any(error.get("type") == "missing" for error in exc.errors())


def parse_prediction_with_diagnostics(text: str) -> PredictionParseResult:
    if not text.strip():
        return PredictionParseResult(parse_success=False, parse_error="empty output")
    try:
        payload = extract_first_json_object(text)
        data = json.loads(payload)
        required_fields = epistemic_prediction_json_schema().get("required", [])
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return PredictionParseResult(
                parse_success=False,
                parse_error=f"Field required: {', '.join(missing_fields)}",
                schema_missing=True,
            )
        prediction = EpistemicPrediction.model_validate(data)
    except ValidationError as exc:
        return PredictionParseResult(
            parse_success=False,
            parse_error=str(exc),
            schema_missing=schema_missing_from_validation_error(exc),
        )
    except Exception as exc:  # noqa: BLE001
        return PredictionParseResult(parse_success=False, parse_error=str(exc))
    return PredictionParseResult(parse_success=True, prediction=prediction)


def select_preflight_tasks(tasks: Sequence[EpistemicTask], sample_size: int = 20) -> List[EpistemicTask]:
    if sample_size != 20:
        return list(tasks[:sample_size])
    by_condition_family: Dict[tuple[str, str], List[EpistemicTask]] = defaultdict(list)
    for task in tasks:
        by_condition_family[(task.condition, task.family)].append(task)
    selected: List[EpistemicTask] = []
    for condition, family_counts in PRELIGHT_TASK_PLAN_20:
        for family, count in family_counts.items():
            candidates = by_condition_family[(condition, family)]
            if len(candidates) < count:
                raise ValueError(f"not enough preflight tasks for {condition}/{family}: need {count}, found {len(candidates)}")
            selected.extend(candidates[:count])
    return selected


def preflight_row(record: PreflightRecord) -> Dict[str, Any]:
    return {
        "task_id": record.task_id,
        "family": record.family,
        "condition": record.condition,
        "model": record.model,
        "prompt_condition": record.prompt_condition,
        "parse_success": 1.0 if record.parse_success else 0.0,
        "empty_output": 1.0 if record.empty_output else 0.0,
        "schema_missing": 1.0 if record.schema_missing else 0.0,
        "parse_error": record.parse_error,
        "response_format_used": record.response_format_used,
        "json_extractor_used": record.json_extractor_used,
        "cost_usd": record.cost_usd,
    }


def model_preflight_summary(records: Sequence[PreflightRecord], *, schema: Mapping[str, Any]) -> List[Dict[str, Any]]:
    required = schema.get("required", [])
    grouped: Dict[str, List[PreflightRecord]] = defaultdict(list)
    for record in records:
        grouped[record.model].append(record)
    output: List[Dict[str, Any]] = []
    for model, group in sorted(grouped.items()):
        n = len(group)
        parse_success_count = sum(1 for record in group if record.parse_success)
        empty_output_count = sum(1 for record in group if record.empty_output)
        schema_missing_count = sum(1 for record in group if record.schema_missing)
        parse_success_rate = parse_success_count / n if n else 0.0
        schema_missing_rate = schema_missing_count / n if n else 0.0
        structured_pass = parse_success_rate >= 0.95 and empty_output_count == 0 and schema_missing_rate <= 0.05
        response_formats = Counter(record.response_format_used for record in group if record.response_format_used)
        extractors = Counter(record.json_extractor_used for record in group if record.json_extractor_used)
        profiles = [record.invocation_profile for record in group if record.invocation_profile]
        output.append(
            {
                "model": model,
                "n": n,
                "parse_success_count": parse_success_count,
                "parse_success_rate": parse_success_rate,
                "empty_output_count": empty_output_count,
                "schema_missing_count": schema_missing_count,
                "schema_missing_rate": schema_missing_rate,
                "structured_preflight_pass": structured_pass,
                "response_format_used": json.dumps(dict(response_formats), ensure_ascii=False, sort_keys=True),
                "json_extractor_used": json.dumps(dict(extractors), ensure_ascii=False, sort_keys=True),
                "temperature_policy": profiles[0].get("temperature_policy", "") if profiles else "",
                "max_completion_tokens_policy": profiles[0].get("max_completion_tokens_policy", "") if profiles else "",
                "required_schema_fields": ",".join(str(item) for item in required),
            }
        )
    return output


def safe_model_dir(model: str) -> str:
    return model.replace("/", "_").replace(":", "_")


@contextmanager
def wall_clock_timeout(timeout_s: float) -> Iterator[None]:
    if timeout_s <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def raise_timeout(_signum: int, _frame: object) -> None:
        raise TimeoutError(f"API call exceeded {timeout_s:.1f}s wall-clock timeout")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, raise_timeout)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, timeout_s)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, previous_timer[0], previous_timer[1])


def write_preflight_artifacts(
    out_dir: Path,
    *,
    model: str,
    task: EpistemicTask,
    messages: Sequence[Mapping[str, str]],
    response_payload: Mapping[str, Any],
) -> None:
    base = out_dir / "artifacts" / safe_model_dir(model)
    write_json(base / f"{task.task_id}.prompt.json", {"model": model, "task_id": task.task_id, "messages": list(messages)})
    write_json(base / f"{task.task_id}.response.json", response_payload)


def complete_in_child(
    queue: multiprocessing.Queue,
    *,
    model: str,
    messages: Sequence[Dict[str, str]],
    max_output_tokens: Optional[int],
    temperature: Optional[float],
    timeout_s: float,
    response_format: str,
    schema_name: str,
    schema: Mapping[str, Any],
) -> None:
    try:
        runner = Phase2OpenAIJsonRunner(timeout_s=timeout_s, response_format=response_format)
        response, usage, used_format = runner.complete(
            model=model,
            messages=messages,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            schema_name=schema_name,
            schema=schema,
        )
        queue.put({"ok": True, "response": response, "usage": usage, "used_format": used_format})
    except Exception as exc:  # noqa: BLE001
        queue.put({"ok": False, "error_type": type(exc).__name__, "error": str(exc)})


def complete_with_process_timeout(
    *,
    model: str,
    messages: Sequence[Dict[str, str]],
    max_output_tokens: Optional[int],
    temperature: Optional[float],
    timeout_s: float,
    response_format: str,
    schema_name: str,
    schema: Mapping[str, Any],
) -> tuple[str, Dict[str, Any], str]:
    context_name = "fork" if "fork" in multiprocessing.get_all_start_methods() else "spawn"
    context = multiprocessing.get_context(context_name)
    queue: multiprocessing.Queue = context.Queue()
    process = context.Process(
        target=complete_in_child,
        kwargs={
            "queue": queue,
            "model": model,
            "messages": list(messages),
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
            "timeout_s": timeout_s,
            "response_format": response_format,
            "schema_name": schema_name,
            "schema": dict(schema),
        },
    )
    process.start()
    process.join(timeout_s)
    if process.is_alive():
        process.terminate()
        process.join(5)
        raise TimeoutError(f"API call exceeded {timeout_s:.1f}s process timeout")
    try:
        result = queue.get_nowait()
    except Empty as exc:
        raise RuntimeError(f"API worker exited without a result, exitcode={process.exitcode}") from exc
    if not result.get("ok"):
        raise RuntimeError(f"{result.get('error_type')}: {result.get('error')}")
    return str(result["response"]), dict(result.get("usage", {})), str(result["used_format"])


def run_preflight_records(
    *,
    tasks: Sequence[EpistemicTask],
    models: Sequence[str],
    prompt_condition: str,
    out_dir: Path,
    max_output_tokens: Optional[int],
    temperature: Optional[float],
    timeout_s: float,
    response_format: str,
    cost_guard: CostGuard,
) -> List[PreflightRecord]:
    profile = invocation_profile(
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        response_format=response_format,
        json_extractor="first_json_object",
    )
    records: List[PreflightRecord] = []
    for model in models:
        for task in tasks:
            messages = portable_chat_messages(build_messages(task, prompt_condition))
            prompt_text = json.dumps(messages, ensure_ascii=False)
            cost_guard.before_call(model, prompt_text, max_output_tokens or 4096)
            response = ""
            usage: Dict[str, Any] = {}
            cost_usd = 0.0
            used_format = response_format
            try:
                response, usage, used_format = complete_with_process_timeout(
                    model=model,
                    messages=messages,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                    timeout_s=timeout_s,
                    response_format=response_format,
                    schema_name="eha_epistemic_prediction",
                    schema=epistemic_prediction_json_schema(),
                )
                cost_usd = cost_guard.after_call(model, usage)
                parsed = parse_prediction_with_diagnostics(response)
                empty_output = not response.strip()
            except Exception as exc:  # noqa: BLE001
                parsed = PredictionParseResult(parse_success=False, parse_error=str(exc), json_extractor_used="not_attempted")
                empty_output = False
            record = PreflightRecord(
                task_id=task.task_id,
                family=task.family,
                condition=task.condition,
                model=model,
                prompt_condition=prompt_condition,
                parse_success=parsed.parse_success,
                empty_output=empty_output,
                schema_missing=parsed.schema_missing,
                parse_error=parsed.parse_error,
                raw_content_preview=response[:1200],
                response_format_used=used_format,
                json_extractor_used=parsed.json_extractor_used,
                invocation_profile=profile,
                usage=usage,
                cost_usd=cost_usd,
                prediction=parsed.prediction,
            )
            write_preflight_artifacts(
                out_dir,
                model=model,
                task=task,
                messages=messages,
                response_payload={
                    "model": model,
                    "task_id": task.task_id,
                    "content": response,
                    "usage": usage,
                    "response_format_used": used_format,
                    "parse_success": parsed.parse_success,
                    "parse_error": parsed.parse_error,
                    "schema_missing": parsed.schema_missing,
                    "empty_output": empty_output,
                    "invocation_profile": profile,
                },
            )
            records.append(record)
            log.info(
                "preflight model={model} task={task_id} parse_success={parse_success} empty={empty}",
                model=model,
                task_id=task.task_id,
                parse_success=parsed.parse_success,
                empty=empty_output,
            )
    return records


def run_record_from_preflight(record: PreflightRecord) -> EpistemicRunRecord:
    prediction = record.prediction or EpistemicPrediction(
        claim_verdict="insufficient",
        confidence=0.0,
        evidence_environment_assessment="Response failed structured-output preflight.",
        answer="Preflight parse failure.",
    )
    return EpistemicRunRecord(
        task_id=record.task_id,
        family=record.family,
        condition=record.condition,
        model=record.model,
        prompt_condition=record.prompt_condition,
        backend="api",
        prediction=prediction,
        parse_success=record.parse_success,
        parse_error=record.parse_error,
        response_format_used=record.response_format_used,
        json_extractor_used=record.json_extractor_used,
        invocation_profile=record.invocation_profile,
        usage=record.usage,
        cost_usd=record.cost_usd,
    )


def collect_artifact_records(source_dirs: Sequence[Path], tasks: Sequence[EpistemicTask]) -> List[PreflightRecord]:
    tasks_by_id = {task.task_id: task for task in tasks}
    records: Dict[tuple[str, str], PreflightRecord] = {}
    for source_dir in source_dirs:
        artifact_dir = source_dir / "artifacts"
        if not artifact_dir.exists():
            continue
        for response_path in sorted(artifact_dir.glob("*/*.response.json")):
            payload = json.loads(response_path.read_text(encoding="utf-8"))
            model = str(payload.get("model", ""))
            task_id = str(payload.get("task_id", ""))
            task = tasks_by_id.get(task_id)
            if not model or task is None:
                continue
            content = str(payload.get("content", ""))
            if content.strip():
                parsed = parse_prediction_with_diagnostics(content)
            else:
                parsed = PredictionParseResult(
                    parse_success=False,
                    parse_error=str(payload.get("parse_error") or "empty output"),
                    schema_missing=bool(payload.get("schema_missing", False)),
                    json_extractor_used=str(payload.get("json_extractor_used") or "not_attempted"),
                )
            record = PreflightRecord(
                task_id=task.task_id,
                family=task.family,
                condition=task.condition,
                model=model,
                prompt_condition=str(payload.get("prompt_condition") or "epistemic_hygiene_instruction"),
                parse_success=parsed.parse_success,
                empty_output=bool(payload.get("empty_output", not content.strip() and not payload.get("parse_error"))),
                schema_missing=parsed.schema_missing,
                parse_error="" if parsed.parse_success else (parsed.parse_error or str(payload.get("parse_error", ""))),
                raw_content_preview=content[:1200],
                response_format_used=str(payload.get("response_format_used", "")),
                json_extractor_used=parsed.json_extractor_used,
                invocation_profile=dict(payload.get("invocation_profile") or {}),
                usage=dict(payload.get("usage") or {}),
                cost_usd=float(payload.get("cost_usd", 0.0) or 0.0),
                prediction=parsed.prediction,
            )
            records[(model, task.task_id)] = record
    return [records[key] for key in sorted(records)]


def summary_by_model(summaries: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    return {str(summary["model"]): summary for summary in summaries}


def summary_passes(summary: Mapping[str, Any] | None) -> bool:
    return bool(summary and summary.get("structured_preflight_pass") is True)


def cohort_decisions(summaries: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    by_model = summary_by_model(summaries)
    decisions: List[Dict[str, Any]] = []
    for provider, model in (
        ("OpenAI", "gpt-5.4"),
        ("Anthropic", "claude-opus-4-7"),
        ("DeepSeek", "deepseek-v4-pro"),
        ("Kimi", "kimi-k2.6"),
    ):
        summary = by_model.get(model)
        decisions.append(
            {
                "provider": provider,
                "selected_model": model if summary_passes(summary) else "",
                "primary_candidate": model,
                "fallback_model": "",
                "status": "selected" if summary_passes(summary) else "blocked",
                "note": "Latest routable flagship passed structured-output preflight." if summary_passes(summary) else "Primary candidate did not pass structured-output preflight.",
            }
        )
    google_primary = by_model.get(GOOGLE_PRIMARY)
    google_fallback = by_model.get(GOOGLE_FALLBACK)
    if summary_passes(google_primary):
        decisions.append(
            {
                "provider": "Google",
                "selected_model": GOOGLE_PRIMARY,
                "primary_candidate": GOOGLE_PRIMARY,
                "fallback_model": GOOGLE_FALLBACK,
                "status": "selected",
                "note": "Latest Google candidate passed structured-output preflight.",
            }
        )
    elif summary_passes(google_fallback):
        decisions.append(
            {
                "provider": "Google",
                "selected_model": GOOGLE_FALLBACK,
                "primary_candidate": GOOGLE_PRIMARY,
                "fallback_model": GOOGLE_FALLBACK,
                "status": "fallback_selected",
                "note": "Google latest candidate did not pass; stable fallback passed preflight.",
            }
        )
    else:
        decisions.append(
            {
                "provider": "Google",
                "selected_model": "",
                "primary_candidate": GOOGLE_PRIMARY,
                "fallback_model": GOOGLE_FALLBACK,
                "status": "blocked",
                "note": "Neither Google primary nor fallback passed structured-output preflight.",
            }
        )
    return sorted(decisions, key=lambda row: row["provider"])


def write_decision_markdown(
    path: Path,
    *,
    summaries: Sequence[Mapping[str, Any]],
    decisions: Sequence[Mapping[str, Any]],
    invocation: Mapping[str, Any],
    sample_counts: Mapping[str, Any],
) -> None:
    lines = [
        "# EHA Frontier Cohort Structured-Output Preflight",
        "",
        "## Selection Rule",
        "",
        "Use the newest routable flagship model per mainstream provider. A model can enter the main table only if it passes the 20-task structured-output preflight.",
        "",
        "Gate: `parse_success >= 0.95`, `empty_output = 0`, and `schema_missing_rate <= 0.05`. LLM-based repair is not used in this gate.",
        "",
        "## Invocation Profile",
        "",
        "```json",
        json.dumps(invocation, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sample",
        "",
        "```json",
        json.dumps(sample_counts, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Cohort Decision",
        "",
    ]
    lines.extend(markdown_table(decisions, ["provider", "selected_model", "primary_candidate", "fallback_model", "status", "note"]))
    lines.extend(["", "## Preflight Summary", ""])
    lines.extend(
        markdown_table(
            summaries,
            [
                "model",
                "n",
                "parse_success_rate",
                "empty_output_count",
                "schema_missing_rate",
                "structured_preflight_pass",
                "temperature_policy",
                "max_completion_tokens_policy",
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Reporting Implication",
            "",
            "Main EHA reports should include both `operational_epistemic_escape` and `conditional_epistemic_escape`; parse failures count as failures in the operational metric.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_preflight_outputs(
    *,
    out_dir: Path,
    tasks: Sequence[EpistemicTask],
    records: Sequence[PreflightRecord],
    selected_models: Sequence[str],
    profile: Mapping[str, Any],
    sample_counts: Mapping[str, Any],
    cost_guard: CostGuard,
    collection_sources: Sequence[str] = (),
) -> None:
    rows = [preflight_row(record) for record in records]
    summaries = model_preflight_summary(records, schema=epistemic_prediction_json_schema())
    decisions = cohort_decisions(summaries)
    run_records = [run_record_from_preflight(record) for record in records]
    scored_rows = score_records(run_records, tasks)

    write_jsonl(out_dir / "preflight_predictions.jsonl", [model_to_dict(record) for record in records])
    write_csv(out_dir / "preflight_rows.csv", rows)
    write_csv(out_dir / "preflight_summary.csv", summaries)
    write_csv(out_dir / "cohort_decision.csv", decisions)
    write_csv(out_dir / "scored_preflight_predictions.csv", scored_rows)
    write_json(out_dir / "cohort_decision.json", {"decisions": decisions, "summaries": summaries})
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in records), 6), **cost_guard.report()})
    write_json(
        out_dir / "audit_manifest.json",
        {
            "task_count_per_model": len(tasks),
            "record_count": len(records),
            "models": list(selected_models),
            "invocation_profile": dict(profile),
            "sample_counts": dict(sample_counts),
            "collection_sources": list(collection_sources),
            "gates": {
                "parse_success_min": 0.95,
                "empty_output_required": 0,
                "schema_missing_rate_max": 0.05,
                "llm_repair": "disabled",
            },
            "artifacts": {
                "predictions": "preflight_predictions.jsonl",
                "rows": "preflight_rows.csv",
                "summary": "preflight_summary.csv",
                "cohort_decision": "cohort_decision.md",
                "raw_calls": "artifacts/",
            },
        },
    )
    write_decision_markdown(
        out_dir / "cohort_decision.md",
        summaries=summaries,
        decisions=decisions,
        invocation=profile,
        sample_counts=sample_counts,
    )


@app.command("run")
def run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    out_dir: Path = typer.Option(Path("results/reports-epistemic-model-preflight-frontier-2026-05-14"), help="Preflight output directory."),
    models: str = typer.Option(",".join(DEFAULT_MAIN_CANDIDATES), help="Comma-separated primary candidate models."),
    fallback_models: str = typer.Option(",".join(DEFAULT_FALLBACK_CANDIDATES), help="Comma-separated fallback models to preflight too."),
    sample_size: int = typer.Option(20, help="Number of EHA tasks per model."),
    prompt_condition: str = typer.Option("epistemic_hygiene_instruction", help="ERT prompt condition to use."),
    max_output_tokens: Optional[int] = typer.Option(4096, help="Output token cap; pass 0 to omit the cap."),
    temperature: Optional[float] = typer.Option(None, help="Omit by default; pass only for models that support it."),
    timeout_s: float = typer.Option(240.0, help="OpenAI client timeout."),
    response_format: str = typer.Option("json_schema", help="json_schema, json_object, or none."),
    collect_from: str = typer.Option("", help="Comma-separated existing preflight output dirs to collect instead of calling APIs."),
    soft_cap_usd: float = typer.Option(30.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(80.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(120.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    if prompt_condition not in {"standard_answer", "epistemic_hygiene_instruction"}:
        raise typer.BadParameter("prompt_condition must be standard_answer or epistemic_hygiene_instruction")
    tasks = select_preflight_tasks(read_tasks(task_dir / "tasks.jsonl"), sample_size=sample_size)
    selected_models = split_csv(models)
    for model in split_csv(fallback_models):
        if model not in selected_models:
            selected_models.append(model)
    if not selected_models:
        raise typer.BadParameter("at least one model is required")
    effective_max_output_tokens = None if max_output_tokens is not None and max_output_tokens <= 0 else max_output_tokens
    profile = invocation_profile(
        temperature=temperature,
        max_output_tokens=effective_max_output_tokens,
        response_format=response_format,
        json_extractor="first_json_object",
    )
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    out_dir.mkdir(parents=True, exist_ok=True)
    collection_sources = split_csv(collect_from)
    if collection_sources:
        source_dirs = [Path(source) for source in collection_sources]
        records = collect_artifact_records(source_dirs, tasks)
        selected_models = sorted({record.model for record in records})
        profile = {
            "collection_mode": True,
            "source_dirs": collection_sources,
            "per_record_invocation_profile": "preserved",
            "llm_repair": "disabled",
        }
        sample_counts = {
            "task_count": len(tasks),
            "family_counts": dict(Counter(task.family for task in tasks)),
            "condition_counts": dict(Counter(task.condition for task in tasks)),
            "prompt_condition": prompt_condition,
        }
        write_preflight_outputs(
            out_dir=out_dir,
            tasks=tasks,
            records=records,
            selected_models=selected_models,
            profile=profile,
            sample_counts=sample_counts,
            cost_guard=cost_guard,
            collection_sources=collection_sources,
        )
        console.print(f"[green]Collected structured-output preflight[/green] to {out_dir}")
        return
    try:
        records = run_preflight_records(
            tasks=tasks,
            models=selected_models,
            prompt_condition=prompt_condition,
            out_dir=out_dir,
            max_output_tokens=effective_max_output_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
            response_format=response_format,
            cost_guard=cost_guard,
        )
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise typer.Exit(code=2) from exc

    sample_counts = {
        "task_count": len(tasks),
        "family_counts": dict(Counter(task.family for task in tasks)),
        "condition_counts": dict(Counter(task.condition for task in tasks)),
        "prompt_condition": prompt_condition,
    }
    write_preflight_outputs(
        out_dir=out_dir,
        tasks=tasks,
        records=records,
        selected_models=selected_models,
        profile=profile,
        sample_counts=sample_counts,
        cost_guard=cost_guard,
    )
    console.print(f"[green]Wrote structured-output preflight[/green] to {out_dir}")


if __name__ == "__main__":
    app()
