from __future__ import annotations

import json
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import typer
from loguru import logger
from pydantic import Field
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard
from .cost_guard import estimate_tokens
from .epistemic_model_preflight import complete_with_process_timeout, parse_prediction_with_diagnostics, safe_model_dir, select_preflight_tasks
from .epistemic_resilience import (
    EpistemicPrediction,
    EpistemicRunRecord,
    EpistemicTask,
    aggregate,
    build_messages,
    epistemic_prediction_json_schema,
    invocation_profile,
    normalize_prediction,
    opaque_doc_id_view,
    portable_chat_messages,
    read_tasks,
    score_records,
    split_csv,
    translate_prediction_to_audit_ids,
    visible_payload_audit,
)
from .report import markdown_table, write_csv
from .schemas import EhaModel, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Run the frozen EHA frontier cohort main experiment.")
console = Console()
log = logger.bind(module="eha.epistemic_frontier_main")

PROMPT_CONDITIONS = ("standard_answer", "epistemic_hygiene_instruction")


class FrontierModelProfile(EhaModel):
    provider: str
    model: str
    budget_setting: str = "operational"
    temperature: Optional[float] = None
    max_output_tokens: Optional[int] = None
    response_format: str = "json_schema"
    timeout_s: float = 240.0
    cost_estimate_output_tokens: int = 4096
    message_role_policy: str = "developer_system_merged_into_user"
    json_extractor: str = "first_json_object"

    def invocation(self) -> Dict[str, Any]:
        profile = invocation_profile(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            response_format=self.response_format,
            json_extractor=self.json_extractor,
            message_role_policy=self.message_role_policy,
        )
        profile["provider"] = self.provider
        profile["budget_setting"] = self.budget_setting
        return profile


class FrontierJob(EhaModel):
    task_id: str
    family: str
    condition: str
    model: str
    provider: str
    budget_setting: str = "operational"
    prompt_condition: str


FRONTIER_MODEL_PROFILES = (
    FrontierModelProfile(provider="OpenAI", model="gpt-5.4", max_output_tokens=4096, response_format="json_schema", timeout_s=180.0),
    FrontierModelProfile(provider="Anthropic", model="claude-opus-4-7", max_output_tokens=4096, response_format="json_schema", timeout_s=180.0),
    FrontierModelProfile(provider="Google", model="gemini-3.1-pro-preview", max_output_tokens=4096, response_format="json_schema", timeout_s=180.0),
    FrontierModelProfile(provider="DeepSeek", model="deepseek-v4-pro", max_output_tokens=None, response_format="json_object", timeout_s=240.0),
    FrontierModelProfile(provider="Kimi", model="kimi-k2.6", max_output_tokens=None, response_format="json_schema", timeout_s=300.0),
)


BUDGET_AUDIT_MODEL_PROFILES = (
    FrontierModelProfile(provider="DeepSeek", model="deepseek-v4-pro", budget_setting="no_cap", max_output_tokens=None, response_format="json_object", timeout_s=240.0),
    FrontierModelProfile(provider="DeepSeek", model="deepseek-v4-pro", budget_setting="cap_8192", max_output_tokens=8192, response_format="json_object", timeout_s=240.0, cost_estimate_output_tokens=8192),
    FrontierModelProfile(provider="DeepSeek", model="deepseek-v4-pro", budget_setting="cap_4096_diagnostic", max_output_tokens=4096, response_format="json_object", timeout_s=240.0),
    FrontierModelProfile(provider="Kimi", model="kimi-k2.6", budget_setting="no_cap", max_output_tokens=None, response_format="json_schema", timeout_s=300.0),
    FrontierModelProfile(provider="Kimi", model="kimi-k2.6", budget_setting="cap_8192", max_output_tokens=8192, response_format="json_schema", timeout_s=300.0, cost_estimate_output_tokens=8192),
    FrontierModelProfile(provider="Kimi", model="kimi-k2.6", budget_setting="cap_4096_diagnostic", max_output_tokens=4096, response_format="json_schema", timeout_s=300.0),
)


def selected_profiles(models: str = "") -> List[FrontierModelProfile]:
    requested = set(split_csv(models)) if models else set()
    profiles = [profile for profile in FRONTIER_MODEL_PROFILES if not requested or profile.model in requested]
    missing = sorted(requested - {profile.model for profile in profiles})
    if missing:
        raise typer.BadParameter(f"unknown frontier model(s): {', '.join(missing)}")
    return profiles


def selected_prompts(prompt_conditions: str = "") -> List[str]:
    prompts = split_csv(prompt_conditions) if prompt_conditions else list(PROMPT_CONDITIONS)
    invalid = [prompt for prompt in prompts if prompt not in PROMPT_CONDITIONS]
    if invalid:
        raise typer.BadParameter(f"unknown prompt condition(s): {', '.join(invalid)}")
    return prompts


def profile_groups(profiles: Sequence[FrontierModelProfile]) -> List[List[FrontierModelProfile]]:
    groups: Dict[str, List[FrontierModelProfile]] = {}
    for profile in profiles:
        groups.setdefault(profile.model, []).append(profile)
    return [groups[model] for model in sorted(groups)]


def frontier_jobs(tasks: Sequence[EpistemicTask], profiles: Sequence[FrontierModelProfile], prompt_conditions: Sequence[str]) -> List[FrontierJob]:
    return [
        FrontierJob(
            task_id=task.task_id,
            family=task.family,
            condition=task.condition,
            model=profile.model,
            provider=profile.provider,
            budget_setting=profile.budget_setting,
            prompt_condition=prompt,
        )
        for profile in profiles
        for task in tasks
        for prompt in prompt_conditions
    ]


def completed_job_keys(path: Path) -> set[Tuple[str, str, str, str]]:
    if not path.exists():
        return set()
    keys: set[Tuple[str, str, str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        model = item.get("model")
        task_id = item.get("task_id")
        prompt = item.get("prompt_condition")
        budget_setting = item.get("budget_setting") or "operational"
        if isinstance(model, str) and isinstance(task_id, str) and isinstance(prompt, str):
            keys.add((model, task_id, prompt, str(budget_setting)))
    return keys


def load_run_records(path: Path) -> List[EpistemicRunRecord]:
    if not path.exists():
        return []
    return [EpistemicRunRecord.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl_line(path: Path, payload: Mapping[str, Any], lock: threading.Lock) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def call_artifact_base(out_dir: Path, *, model: str, budget_setting: str, prompt_condition: str, task_id: str) -> Path:
    return out_dir / "artifacts" / safe_model_dir(model) / budget_setting / prompt_condition / task_id


def write_call_artifacts(
    out_dir: Path,
    *,
    profile: FrontierModelProfile,
    task: EpistemicTask,
    prompt_condition: str,
    messages: Sequence[Mapping[str, str]],
    attempt_payloads: Sequence[Mapping[str, Any]],
    doc_id_map: Mapping[str, str] | None = None,
    visible_prompt_audit: Mapping[str, Any] | None = None,
) -> None:
    base = call_artifact_base(out_dir, model=profile.model, budget_setting=profile.budget_setting, prompt_condition=prompt_condition, task_id=task.task_id)
    write_json(
        base.with_suffix(".prompt.json"),
        {
            "model": profile.model,
            "provider": profile.provider,
            "task_id": task.task_id,
            "prompt_condition": prompt_condition,
            "messages": list(messages),
            "invocation_profile": profile.invocation(),
            "model_visible_doc_id_policy": "opaque_per_task",
            "scorer_visible_to_audit_doc_id_map": dict(doc_id_map or {}),
            "visible_prompt_audit": dict(visible_prompt_audit or {}),
        },
    )
    write_json(base.with_suffix(".response.json"), {"attempts": list(attempt_payloads), "final_attempt": attempt_payloads[-1] if attempt_payloads else {}})


def fallback_prediction(parse_error: str) -> EpistemicPrediction:
    return EpistemicPrediction(
        claim_verdict="insufficient",
        confidence=0.0,
        evidence_environment_assessment="Response failed before a parseable structured output was available.",
        answer=parse_error or "Call failed.",
    )


def word_count(text: str) -> int:
    return len([part for part in text.replace("\n", " ").split(" ") if part.strip()])


def output_budget_diagnostics(prediction: Optional[EpistemicPrediction], raw_response: str) -> tuple[int, Dict[str, Any], bool]:
    visible_tokens = estimate_tokens(raw_response) if raw_response else 0
    if prediction is None:
        return visible_tokens, {}, False
    action_words = [word_count(action.rationale) for action in prediction.actions]
    field_lengths: Dict[str, Any] = {
        "answer_words": word_count(prediction.answer),
        "evidence_environment_assessment_words": word_count(prediction.evidence_environment_assessment),
        "max_action_rationale_words": max(action_words) if action_words else 0,
        "supporting_evidence_count": len(prediction.supporting_evidence),
        "rejected_evidence_count": len(prediction.rejected_evidence),
        "selected_doc_ids_count": len(prediction.selected_doc_ids),
        "actions_count": len(prediction.actions),
    }
    overlength = (
        field_lengths["answer_words"] > 120
        or field_lengths["evidence_environment_assessment_words"] > 120
        or field_lengths["max_action_rationale_words"] > 80
        or field_lengths["supporting_evidence_count"] > 5
        or field_lengths["rejected_evidence_count"] > 5
        or field_lengths["selected_doc_ids_count"] > 3
        or field_lengths["actions_count"] > 2
    )
    return visible_tokens, field_lengths, bool(overlength)


def run_single_job(
    *,
    profile: FrontierModelProfile,
    task: EpistemicTask,
    prompt_condition: str,
    out_dir: Path,
    max_attempts: int,
    cost_guard: CostGuard,
    cost_lock: threading.Lock,
) -> EpistemicRunRecord:
    doc_id_view = opaque_doc_id_view(task)
    base_messages = build_messages(task, prompt_condition, opaque_doc_ids=True, scrub_audit_labels=True)
    messages = portable_chat_messages(base_messages)
    prompt_payload = json.loads(base_messages[-1]["content"])
    prompt_audit = visible_payload_audit(prompt_payload.get("documents", []))
    prompt_text = json.dumps(messages, ensure_ascii=False)
    attempt_payloads: List[Dict[str, Any]] = []
    final_response = ""
    final_usage: Dict[str, Any] = {}
    final_used_format = profile.response_format
    final_error = ""
    final_empty = False
    final_schema_missing = False
    final_prediction: Optional[EpistemicPrediction] = None
    final_success = False
    final_extractor = "not_attempted"
    final_cost = 0.0
    final_visible_tokens = 0
    final_field_lengths: Dict[str, Any] = {}
    final_overlength = False
    attempts_used = 0

    for attempt in range(1, max_attempts + 1):
        attempts_used = attempt
        with cost_lock:
            cost_guard.before_call(profile.model, prompt_text, profile.max_output_tokens or profile.cost_estimate_output_tokens)
        started = time.time()
        response = ""
        usage: Dict[str, Any] = {}
        used_format = profile.response_format
        parse_error = ""
        empty_output = False
        schema_missing = False
        parse_success = False
        extractor = "not_attempted"
        cost_usd = 0.0
        try:
            response, usage, used_format = complete_with_process_timeout(
                model=profile.model,
                messages=messages,
                max_output_tokens=profile.max_output_tokens,
                temperature=profile.temperature,
                timeout_s=profile.timeout_s,
                response_format=profile.response_format,
                schema_name="eha_epistemic_prediction",
                schema=epistemic_prediction_json_schema(),
            )
            with cost_lock:
                cost_usd = cost_guard.after_call(profile.model, usage)
            parsed = parse_prediction_with_diagnostics(response)
            parse_success = parsed.parse_success
            parse_error = parsed.parse_error
            schema_missing = parsed.schema_missing
            extractor = parsed.json_extractor_used
            empty_output = not response.strip()
            if parsed.prediction is not None:
                translated_prediction = translate_prediction_to_audit_ids(parsed.prediction, doc_id_view.visible_to_audit)
                final_prediction = normalize_prediction(translated_prediction, task)
                final_visible_tokens, final_field_lengths, final_overlength = output_budget_diagnostics(final_prediction, response)
        except BudgetExceeded:
            raise
        except Exception as exc:  # noqa: BLE001
            parse_error = str(exc)
            empty_output = False
        elapsed_s = round(time.time() - started, 3)
        attempt_payloads.append(
            {
                "attempt": attempt,
                "model": profile.model,
        "provider": profile.provider,
        "budget_setting": profile.budget_setting,
                "task_id": task.task_id,
                "prompt_condition": prompt_condition,
                "content": response,
                "usage": usage,
                "response_format_used": used_format,
                "parse_success": parse_success,
                "parse_error": parse_error,
                "empty_output": empty_output,
                "schema_missing": schema_missing,
                "json_extractor_used": extractor,
                "elapsed_s": elapsed_s,
                "cost_usd": cost_usd,
            }
        )
        final_response = response
        final_usage = usage
        final_used_format = used_format
        final_error = parse_error
        final_empty = empty_output
        final_schema_missing = schema_missing
        final_success = parse_success
        final_extractor = extractor
        final_cost = cost_usd
        if parse_success:
            break
        if attempt < max_attempts and (empty_output or "timeout" in parse_error.lower() or "api" in parse_error.lower() or "worker exited" in parse_error.lower()):
            time.sleep(min(10.0, 2.0 * attempt))
            continue
        break

    write_call_artifacts(
        out_dir,
        profile=profile,
        task=task,
        prompt_condition=prompt_condition,
        messages=messages,
        attempt_payloads=attempt_payloads,
        doc_id_map=doc_id_view.visible_to_audit,
        visible_prompt_audit=prompt_audit,
    )
    prediction = final_prediction if final_success and final_prediction is not None else fallback_prediction(final_error)
    profile_payload = profile.invocation()
    profile_payload.update({"attempts": attempts_used, "max_attempts": max_attempts, "doc_id_policy": "opaque_per_task", "visible_prompt_audit": prompt_audit})
    return EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model=profile.model,
        provider=profile.provider,
        budget_setting=profile.budget_setting,
        prompt_condition=prompt_condition,
        backend="api",
        prediction=prediction,
        parse_success=final_success,
        parse_error=final_error,
        empty_output=final_empty,
        schema_missing=final_schema_missing,
        attempt_count=attempts_used,
        response_format_used=final_used_format,
        json_extractor_used=final_extractor,
        invocation_profile=profile_payload,
        visible_output_tokens=final_visible_tokens if final_visible_tokens else estimate_tokens(final_response),
        json_field_lengths=final_field_lengths,
        overlength=final_overlength,
        usage=final_usage,
        cost_usd=final_cost,
    )


def run_profile_stream(
    *,
    profile: FrontierModelProfile,
    tasks: Sequence[EpistemicTask],
    prompt_conditions: Sequence[str],
    out_dir: Path,
    predictions_path: Path,
    completed: set[Tuple[str, str, str, str]],
    write_lock: threading.Lock,
    cost_guard: CostGuard,
    cost_lock: threading.Lock,
    max_attempts: int,
) -> int:
    written = 0
    for task in tasks:
        for prompt_condition in prompt_conditions:
            key = (profile.model, task.task_id, prompt_condition, profile.budget_setting)
            if key in completed:
                continue
            record = run_single_job(
                profile=profile,
                task=task,
                prompt_condition=prompt_condition,
                out_dir=out_dir,
                max_attempts=max_attempts,
                cost_guard=cost_guard,
                cost_lock=cost_lock,
            )
            write_jsonl_line(predictions_path, model_to_dict(record), write_lock)
            written += 1
            log.info("frontier model={model} task={task_id} prompt={prompt} parse_success={parse_success}", model=profile.model, task_id=task.task_id, prompt=prompt_condition, parse_success=record.parse_success)
    return written


def run_profile_group_stream(
    *,
    profiles: Sequence[FrontierModelProfile],
    tasks: Sequence[EpistemicTask],
    prompt_conditions: Sequence[str],
    out_dir: Path,
    predictions_path: Path,
    completed: set[Tuple[str, str, str, str]],
    write_lock: threading.Lock,
    cost_guard: CostGuard,
    cost_lock: threading.Lock,
    max_attempts: int,
) -> int:
    written = 0
    for profile in profiles:
        written += run_profile_stream(
            profile=profile,
            tasks=tasks,
            prompt_conditions=prompt_conditions,
            out_dir=out_dir,
            predictions_path=predictions_path,
            completed=completed,
            write_lock=write_lock,
            cost_guard=cost_guard,
            cost_lock=cost_lock,
            max_attempts=max_attempts,
        )
    return written


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def add_frontier_metrics(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        if item["family"] == "active_verification":
            item["verification_action_score"] = mean(
                [
                    float(item["primary_action_rate"]),
                    float(item["contradiction_action_rate"]),
                    float(item["generated_lore_trace_rate"]),
                ]
            )
        else:
            item["verification_action_score"] = ""
        output.append(item)
    return output


def aggregate_frontier(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> List[Dict[str, Any]]:
    metrics = [
        "operational_epistemic_escape",
        "conditional_epistemic_escape",
        "parse_success",
        "belief_correctness",
        "evidence_cleanliness",
        "uncertainty_discipline",
        "verification_action_score",
        "visible_output_tokens",
        "answer_word_count",
        "evidence_assessment_word_count",
        "max_action_rationale_word_count",
        "overlength_rate",
        "cost_usd",
    ]
    return aggregate(rows, group_keys, metrics)


def failure_case_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    failures: List[Dict[str, Any]] = []
    for row in rows:
        if float(row["parse_success"]) == 0.0 or float(row["operational_epistemic_escape"]) == 0.0:
            failures.append(
                {
                    "model": row["model"],
                    "provider": row.get("provider", ""),
                    "budget_setting": row.get("budget_setting", ""),
                    "task_id": row["task_id"],
                    "family": row["family"],
                    "condition": row["condition"],
                    "prompt_condition": row["prompt_condition"],
                    "parse_success": row["parse_success"],
                    "empty_output": row.get("empty_output", ""),
                    "schema_missing": row.get("schema_missing", ""),
                    "operational_epistemic_escape": row["operational_epistemic_escape"],
                    "gold_verdict": row["gold_verdict"],
                    "predicted_verdict": row["predicted_verdict"],
                    "confidence": row["confidence"],
                    "supporting_evidence": row["supporting_evidence"],
                    "selected_doc_ids": row["selected_doc_ids"],
                    "actions": row["actions"],
                }
            )
    return failures


def percentile(values: Sequence[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * p))))
    return ordered[index]


def budget_sensitivity_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[str, str], List[Mapping[str, Any]]] = {}
    for row in rows:
        setting = str(row.get("budget_setting", "operational"))
        if setting == "operational":
            continue
        grouped.setdefault((str(row["model"]), setting), []).append(row)
    output: List[Dict[str, Any]] = []
    for (model, setting), group in sorted(grouped.items()):
        visible_tokens = [float(row["visible_output_tokens"]) for row in group if row.get("visible_output_tokens") != ""]
        parse_success = mean([float(row["parse_success"]) for row in group])
        empty_output_rate = mean([float(row.get("empty_output", 0.0)) for row in group])
        schema_missing_rate = mean([float(row.get("schema_missing", 0.0)) for row in group])
        gate_pass = parse_success >= 0.95 and empty_output_rate == 0.0 and schema_missing_rate <= 0.05
        output.append(
            {
                "model": model,
                "budget_setting": setting,
                "n": len(group),
                "parse_success": parse_success,
                "empty_output_rate": empty_output_rate,
                "schema_missing_rate": schema_missing_rate,
                "visible_output_tokens_mean": mean(visible_tokens),
                "visible_output_tokens_median": percentile(visible_tokens, 0.5),
                "visible_output_tokens_p95": percentile(visible_tokens, 0.95),
                "overlength_rate": mean([float(row.get("overlength_rate", 0.0)) for row in group]),
                "operational_epistemic_escape": mean([float(row["operational_epistemic_escape"]) for row in group]),
                "conditional_epistemic_escape": mean([float(row["conditional_epistemic_escape"]) for row in group if row["conditional_epistemic_escape"] != ""]),
                "evidence_cleanliness": mean([float(row["evidence_cleanliness"]) for row in group]),
                "verification_action_score": mean([float(row["verification_action_score"]) for row in group if row["verification_action_score"] != ""]),
                "gate_pass": gate_pass,
            }
        )
    return output


def budget_setting_decisions(sensitivity_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    by_model: Dict[str, Dict[str, Mapping[str, Any]]] = {}
    for row in sensitivity_rows:
        by_model.setdefault(str(row["model"]), {})[str(row["budget_setting"])] = row
    decisions: List[Dict[str, Any]] = []
    for model, settings in sorted(by_model.items()):
        cap_8192 = settings.get("cap_8192")
        no_cap = settings.get("no_cap")
        if cap_8192 and cap_8192.get("gate_pass") is True:
            selected = "cap_8192"
            reason = "8192 cap passed parse/empty/schema gate; use capped setting for better token-budget comparability."
        elif no_cap and no_cap.get("gate_pass") is True:
            selected = "no_cap"
            reason = "8192 cap failed or was unavailable; no-cap passed gate, so keep provider-compatible operational setting."
        else:
            selected = "blocked"
            reason = "Neither 8192 cap nor no-cap passed the structured-output gate."
        diagnostic = settings.get("cap_4096_diagnostic", {})
        decisions.append(
            {
                "model": model,
                "selected_budget_setting": selected,
                "reason": reason,
                "no_cap_gate_pass": bool(no_cap and no_cap.get("gate_pass") is True),
                "cap_8192_gate_pass": bool(cap_8192 and cap_8192.get("gate_pass") is True),
                "cap_4096_parse_success": diagnostic.get("parse_success", ""),
                "cap_4096_empty_output_rate": diagnostic.get("empty_output_rate", ""),
            }
        )
    return decisions


def write_budget_decision_markdown(path: Path, *, sensitivity_rows: Sequence[Mapping[str, Any]], decisions: Sequence[Mapping[str, Any]]) -> None:
    lines = [
        "# Token-Budget Fairness Audit Decision",
        "",
        "Gate: `parse_success >= 0.95`, `empty_output_rate = 0`, `schema_missing_rate <= 0.05`.",
        "",
        "## Decision",
        "",
    ]
    lines.extend(markdown_table(decisions, ["model", "selected_budget_setting", "reason", "no_cap_gate_pass", "cap_8192_gate_pass", "cap_4096_parse_success", "cap_4096_empty_output_rate"]))
    lines.extend(["", "## Sensitivity Table", ""])
    lines.extend(markdown_table(sensitivity_rows, ["model", "budget_setting", "n", "parse_success", "empty_output_rate", "schema_missing_rate", "visible_output_tokens_mean", "visible_output_tokens_median", "visible_output_tokens_p95", "overlength_rate", "operational_epistemic_escape", "conditional_epistemic_escape", "evidence_cleanliness", "verification_action_score", "gate_pass"]))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(path: Path, *, by_model: Sequence[Mapping[str, Any]], by_prompt: Sequence[Mapping[str, Any]], cost_report: Mapping[str, Any]) -> None:
    lines = [
        "# EHA Frontier Cohort Main Run",
        "",
        "## By Model",
        "",
    ]
    lines.extend(markdown_table(by_model, ["model", "budget_setting", "n", "operational_epistemic_escape", "conditional_epistemic_escape", "parse_success", "belief_correctness", "evidence_cleanliness", "uncertainty_discipline", "verification_action_score", "visible_output_tokens", "overlength_rate"]))
    lines.extend(["", "## By Prompt", ""])
    lines.extend(markdown_table(by_prompt, ["model", "budget_setting", "prompt_condition", "n", "operational_epistemic_escape", "conditional_epistemic_escape", "parse_success", "belief_correctness", "evidence_cleanliness", "uncertainty_discipline", "verification_action_score", "visible_output_tokens", "overlength_rate"]))
    lines.extend(["", "## Cost Report", "", "```json", json.dumps(cost_report, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_frontier_reports(out_dir: Path, *, records: Sequence[EpistemicRunRecord], tasks: Sequence[EpistemicTask], cost_report: Mapping[str, Any]) -> None:
    rows = add_frontier_metrics(score_records(records, tasks))
    by_model = aggregate_frontier(rows, ["model", "budget_setting"])
    by_family = aggregate_frontier(rows, ["model", "budget_setting", "family"])
    by_condition = aggregate_frontier(rows, ["model", "budget_setting", "condition"])
    by_prompt = aggregate_frontier(rows, ["model", "budget_setting", "prompt_condition"])
    operational_vs_conditional = aggregate_frontier(rows, ["model", "budget_setting", "prompt_condition"])
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "frontier_main_scored_predictions.csv", rows)
    write_csv(out_dir / "frontier_main_metrics_by_model.csv", by_model)
    write_csv(out_dir / "frontier_main_metrics_by_family.csv", by_family)
    write_csv(out_dir / "frontier_main_metrics_by_condition.csv", by_condition)
    write_csv(out_dir / "frontier_main_metrics_by_prompt.csv", by_prompt)
    write_csv(out_dir / "operational_vs_conditional_escape.csv", operational_vs_conditional)
    write_jsonl(out_dir / "failure_cases_frontier.jsonl", failure_case_rows(rows))
    sensitivity_rows = budget_sensitivity_rows(rows)
    if sensitivity_rows:
        decisions = budget_setting_decisions(sensitivity_rows)
        write_csv(out_dir / "budget_sensitivity_table.csv", sensitivity_rows)
        write_csv(out_dir / "budget_setting_decision.csv", decisions)
        write_json(out_dir / "budget_setting_decision.json", {"decisions": decisions, "sensitivity": sensitivity_rows})
        write_budget_decision_markdown(out_dir / "budget_setting_decision.md", sensitivity_rows=sensitivity_rows, decisions=decisions)
    write_json(out_dir / "cost_report.json", cost_report)
    write_json(
        out_dir / "report_manifest.json",
        {
            "record_count": len(records),
            "task_count": len(tasks),
            "model_count": len({record.model for record in records}),
            "prompt_conditions": sorted({record.prompt_condition for record in records}),
            "metrics": [
                "operational_epistemic_escape",
                "conditional_epistemic_escape",
                "parse_success",
                "belief_correctness",
                "evidence_cleanliness",
                "uncertainty_discipline",
                "verification_action_score",
                "visible_output_tokens",
                "answer_word_count",
                "evidence_assessment_word_count",
                "max_action_rationale_word_count",
                "overlength_rate",
            ],
        },
    )
    write_summary(out_dir / "summary.md", by_model=by_model, by_prompt=by_prompt, cost_report=cost_report)


def run_plan_payload(tasks: Sequence[EpistemicTask], profiles: Sequence[FrontierModelProfile], prompts: Sequence[str], parallel_models: int, max_attempts: int) -> Dict[str, Any]:
    jobs = frontier_jobs(tasks, profiles, prompts)
    return {
        "name": "EHA Frontier Cohort Main Run",
        "task_count": len(tasks),
        "model_count": len(profiles),
        "prompt_conditions": list(prompts),
        "job_count": len(jobs),
        "parallel_strategy": {
            "parallel_model_streams": min(parallel_models, len(profiles)),
            "per_model_concurrency": 1,
            "reason": "Run one sequential stream per model to preserve call success while parallelizing across providers.",
        },
        "max_attempts": max_attempts,
        "model_visible_doc_id_policy": "opaque_per_task",
        "visible_prompt_sanitization": [
            "semantic doc_id tokens are replaced with opaque per-task IDs",
            "visible_citations are remapped into the same opaque namespace",
            "audit-only source IDs in title/body text are scrubbed before model calls",
        ],
        "models": [model_to_dict(profile) for profile in profiles],
        "family_counts": dict(Counter(task.family for task in tasks)),
        "condition_counts": dict(Counter(task.condition for task in tasks)),
        "outputs": [
            "summary.md",
            "frontier_main_metrics_by_model.csv",
            "frontier_main_metrics_by_family.csv",
            "frontier_main_metrics_by_condition.csv",
            "frontier_main_metrics_by_prompt.csv",
            "operational_vs_conditional_escape.csv",
            "failure_cases_frontier.jsonl",
            "cost_report.json",
        ],
    }


def write_plan_markdown(path: Path, plan: Mapping[str, Any]) -> None:
    lines = [
        "# EHA Frontier Main Run Plan",
        "",
        f"- Tasks: `{plan['task_count']}`",
        f"- Models: `{plan['model_count']}`",
        f"- Prompt conditions: `{', '.join(plan['prompt_conditions'])}`",
        f"- Total calls: `{plan['job_count']}`",
        f"- Parallel model streams: `{plan['parallel_strategy']['parallel_model_streams']}`",
        f"- Per-model concurrency: `{plan['parallel_strategy']['per_model_concurrency']}`",
        f"- Max attempts per call: `{plan['max_attempts']}`",
        f"- Model-visible document IDs: `{plan.get('model_visible_doc_id_policy', 'legacy')}`",
        "",
        "## Models",
        "",
    ]
    lines.extend(markdown_table(plan["models"], ["provider", "model", "budget_setting", "temperature", "max_output_tokens", "response_format", "timeout_s"]))
    lines.extend(["", "## Outputs", ""])
    lines.extend([f"- `{name}`" for name in plan["outputs"]])
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command("plan")
def plan(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-frontier-main"), help="Output directory."),
    models: str = typer.Option("", help="Optional comma-separated subset of frozen frontier models."),
    prompt_conditions: str = typer.Option(",".join(PROMPT_CONDITIONS), help="Comma-separated prompt conditions."),
    limit_tasks: int = typer.Option(0, help="Limit tasks for smoke planning; 0 means all tasks."),
    parallel_models: int = typer.Option(5, help="Number of provider/model streams to run concurrently."),
    max_attempts: int = typer.Option(2, help="Attempts per call for transient API/empty-output failures."),
) -> None:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    if limit_tasks > 0:
        tasks = tasks[:limit_tasks]
    profiles = selected_profiles(models)
    prompts = selected_prompts(prompt_conditions)
    payload = run_plan_payload(tasks, profiles, prompts, parallel_models=parallel_models, max_attempts=max_attempts)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "frontier_main_run_plan.json", payload)
    write_plan_markdown(out_dir / "frontier_main_run_plan.md", payload)
    console.print(f"[green]Wrote frontier main run plan[/green] to {out_dir}")


@app.command("budget-plan")
def budget_plan(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-frontier-budget-audit"), help="Budget audit output directory."),
    prompt_condition: str = typer.Option("epistemic_hygiene_instruction", help="Prompt condition for the 20-task audit."),
    parallel_models: int = typer.Option(2, help="Run DeepSeek and Kimi audit streams concurrently."),
    max_attempts: int = typer.Option(1, help="Attempts per call; default 1 so cap compatibility failures are not masked."),
) -> None:
    tasks = select_preflight_tasks(read_tasks(task_dir / "tasks.jsonl"), sample_size=20)
    prompts = selected_prompts(prompt_condition)
    payload = run_plan_payload(tasks, BUDGET_AUDIT_MODEL_PROFILES, prompts, parallel_models=parallel_models, max_attempts=max_attempts)
    payload["decision_rule"] = {
        "cap_8192_pass": "If parse_success >= 0.95, empty_output=0, and schema_missing_rate <= 0.05, use cap_8192 in the main run for that model.",
        "no_cap_fallback": "If cap_8192 fails but no_cap passes, keep no_cap and mark provider-compatible operational setting.",
        "cap_4096": "Diagnostic only for DeepSeek/Kimi if it causes empty outputs.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "budget_fairness_audit_plan.json", payload)
    write_plan_markdown(out_dir / "budget_fairness_audit_plan.md", payload)
    console.print(f"[green]Wrote budget fairness audit plan[/green] to {out_dir}")


@app.command("budget-run")
def budget_run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-frontier-budget-audit"), help="Budget audit output directory."),
    prompt_condition: str = typer.Option("epistemic_hygiene_instruction", help="Prompt condition for the 20-task audit."),
    parallel_models: int = typer.Option(2, help="Run DeepSeek and Kimi audit streams concurrently."),
    max_attempts: int = typer.Option(1, help="Attempts per call; default 1 so cap compatibility failures are not masked."),
    resume: bool = typer.Option(True, help="Skip completed rows already in predictions.jsonl."),
    soft_cap_usd: float = typer.Option(120.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(400.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(600.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    tasks = select_preflight_tasks(read_tasks(task_dir / "tasks.jsonl"), sample_size=20)
    prompts = selected_prompts(prompt_condition)
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "predictions.jsonl"
    completed = completed_job_keys(predictions_path) if resume else set()
    plan_payload = run_plan_payload(tasks, BUDGET_AUDIT_MODEL_PROFILES, prompts, parallel_models=parallel_models, max_attempts=max_attempts)
    plan_payload["resume_completed_count"] = len(completed)
    write_json(out_dir / "run_manifest.json", plan_payload)

    write_lock = threading.Lock()
    cost_lock = threading.Lock()
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    try:
        groups = profile_groups(BUDGET_AUDIT_MODEL_PROFILES)
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
    write_frontier_reports(out_dir, records=records, tasks=tasks, cost_report=cost_report)
    console.print(f"[green]Wrote budget fairness audit outputs[/green] to {out_dir}")


@app.command("run")
def run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-frontier-main"), help="Output directory."),
    models: str = typer.Option("", help="Optional comma-separated subset of frozen frontier models."),
    prompt_conditions: str = typer.Option(",".join(PROMPT_CONDITIONS), help="Comma-separated prompt conditions."),
    limit_tasks: int = typer.Option(0, help="Limit tasks for smoke run; 0 means all tasks."),
    parallel_models: int = typer.Option(5, help="Number of provider/model streams to run concurrently."),
    max_attempts: int = typer.Option(2, help="Attempts per call for transient API/empty-output failures."),
    resume: bool = typer.Option(True, help="Skip completed model/task/prompt rows already in predictions.jsonl."),
    soft_cap_usd: float = typer.Option(250.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(800.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(1000.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    if limit_tasks > 0:
        tasks = tasks[:limit_tasks]
    profiles = selected_profiles(models)
    prompts = selected_prompts(prompt_conditions)
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "predictions.jsonl"
    completed = completed_job_keys(predictions_path) if resume else set()
    plan_payload = run_plan_payload(tasks, profiles, prompts, parallel_models=parallel_models, max_attempts=max_attempts)
    plan_payload["resume_completed_count"] = len(completed)
    write_json(out_dir / "run_manifest.json", plan_payload)

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
    write_frontier_reports(out_dir, records=records, tasks=tasks, cost_report=cost_report)
    console.print(f"[green]Wrote frontier main outputs[/green] to {out_dir}")


@app.command("report")
def report(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    run_dir: Path = typer.Option(Path("results/reports-eha-frontier-main"), help="Run directory containing predictions.jsonl."),
) -> None:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    records = load_run_records(run_dir / "predictions.jsonl")
    cost_report = json.loads((run_dir / "cost_report.json").read_text(encoding="utf-8")) if (run_dir / "cost_report.json").exists() else {"aborted": False}
    write_frontier_reports(run_dir, records=records, tasks=tasks, cost_report=cost_report)
    console.print(f"[green]Wrote frontier main reports[/green] to {run_dir}")


if __name__ == "__main__":
    app()
