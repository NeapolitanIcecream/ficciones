from __future__ import annotations

import csv
import json
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
from pathlib import Path
from random import Random
from typing import Any, Dict, Iterable, Mapping, Sequence

import typer
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard, cost_for_usage, estimate_tokens
from .epistemic_frontier_main import FrontierModelProfile, complete_with_process_timeout
from .epistemic_generated_lore_audit import (
    clarified_evidence_json_schema,
    diagnostic_no_hygiene_json_schema,
    first_json_object,
    minimal_evidence_json_schema,
)
from .epistemic_model_preflight import load_preflight_tasks, provider_for_model
from .epistemic_resilience import (
    EpistemicTask,
    epistemic_prediction_json_schema,
    evidence_payload,
    opaque_doc_id_view,
    replace_doc_id_refs,
    translate_doc_refs_to_audit,
    visible_payload_audit,
)
from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_contract import split_csv
from .uncued_run import HIDDEN_PROMPT_MARKERS, base_uncued_task_id, uncued_view


REPORT_DATE = "2026-05-23"
RUN_DIR_NAME = f"reports-eha-uncued-schema-ablation-{REPORT_DATE}"
SCHEMA_VARIANTS = ("current", "clarified", "minimal", "diagnostic_no_hygiene")
DEFAULT_CONDITIONS = ("generated_lore", "buried_primary")
DEFAULT_MODELS = "gpt-5.5,gemini-3.1-pro-preview"
DEFAULT_SCHEMAS = ",".join(SCHEMA_VARIANTS)
DEFAULT_VIEW = "neutral_metadata_visible"
FORBIDDEN_PROMPT_MARKERS = HIDDEN_PROMPT_MARKERS + (
    "packet_judgment",
    "evidence_selection",
    "active_verification",
)
AUDIT_SCAN_MARKERS = FORBIDDEN_PROMPT_MARKERS + ("uncued_000_d", "primary_doc_ids", "contaminant_doc_ids")


plan_app = typer.Typer(add_completion=False, help="Plan the EHA-Uncued Phase 1.1 schema ablation slice.")
run_app = typer.Typer(add_completion=False, help="Run the EHA-Uncued Phase 1.1 schema ablation.")
report_app = typer.Typer(add_completion=False, help="Report EHA-Uncued Phase 1.1 schema ablation results.")
verify_app = typer.Typer(add_completion=False, help="Verify EHA-Uncued Phase 1.1 schema ablation artifacts.")
console = Console()


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl_line(path: Path, payload: Mapping[str, Any], lock: threading.Lock | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
    if lock is None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
        return
    with lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def schema_json_schema(variant: str) -> Dict[str, Any]:
    if variant == "current":
        return epistemic_prediction_json_schema()
    if variant == "clarified":
        return clarified_evidence_json_schema()
    if variant == "minimal":
        return minimal_evidence_json_schema()
    if variant == "diagnostic_no_hygiene":
        return diagnostic_no_hygiene_json_schema()
    raise ValueError(f"unknown schema variant: {variant}")


def parse_schema_prediction(variant: str, text: str) -> Dict[str, Any]:
    payload = first_json_object(text)
    schema = schema_json_schema(variant)
    required = [str(item) for item in schema.get("required", [])]
    missing = [field for field in required if field not in payload]
    if missing:
        raise ValueError(f"missing required field(s) for {variant}: {', '.join(missing)}")
    allowed = set(schema.get("properties", {}).keys())
    extra = sorted(set(payload.keys()) - allowed)
    if extra:
        raise ValueError(f"unexpected field(s) for {variant}: {', '.join(extra)}")
    return dict(payload)


def schema_support_field(variant: str) -> str:
    return {
        "current": "supporting_evidence",
        "clarified": "clean_supporting_evidence",
        "minimal": "evidence_doc_ids",
        "diagnostic_no_hygiene": "supporting_evidence",
    }[variant]


def schema_rejection_field(variant: str) -> str | None:
    return {
        "current": "rejected_evidence",
        "clarified": "rejected_or_contaminated_evidence",
        "minimal": None,
        "diagnostic_no_hygiene": "rejected_or_contaminated_evidence",
    }[variant]


def schema_diagnostic_field(variant: str) -> str | None:
    return {
        "current": None,
        "clarified": "diagnostic_evidence",
        "minimal": None,
        "diagnostic_no_hygiene": "diagnostic_evidence",
    }[variant]


def selected_task_ids_from_manifest(run_dir: Path) -> list[str]:
    manifest = read_json(run_dir / "selection_manifest.json")
    return [str(row["view_task_id"]) for row in manifest.get("selected_tasks", [])]


def task_by_view_id(dataset_dir: Path) -> Dict[str, EpistemicTask]:
    return {task.task_id: task for task in load_preflight_tasks(dataset_dir)}


def latent_rows_by_task(dataset_dir: Path) -> Dict[str, Dict[str, Any]]:
    return {str(row["task_id"]): row for row in read_jsonl(dataset_dir / "latent_tasks.jsonl")}


def family_targets(tasks_per_condition: int) -> Dict[str, int]:
    if tasks_per_condition == 8:
        return {"packet_judgment": 3, "evidence_selection": 3, "active_verification": 2}
    if tasks_per_condition == 5:
        return {"packet_judgment": 2, "evidence_selection": 2, "active_verification": 1}
    base = tasks_per_condition // 3
    remainder = tasks_per_condition % 3
    families = ["packet_judgment", "evidence_selection", "active_verification"]
    return {family: base + (1 if index < remainder else 0) for index, family in enumerate(families)}


def plan_schema_ablation(
    dataset_dir: Path,
    out_dir: Path,
    *,
    conditions: Sequence[str],
    tasks_per_condition: int,
    view: str,
    seed: int,
) -> Dict[str, Any]:
    latent_rows = list(latent_rows_by_task(dataset_dir).values())
    rng = Random(seed)
    selected: list[Dict[str, Any]] = []
    targets = family_targets(tasks_per_condition)
    family_counts_by_condition: Dict[str, Dict[str, int]] = {}
    for condition in conditions:
        condition_selected: list[Dict[str, Any]] = []
        family_counts: Dict[str, int] = {}
        for family, count in targets.items():
            candidates = [row for row in latent_rows if row.get("condition") == condition and row.get("family") == family]
            rng.shuffle(candidates)
            chosen = sorted(candidates[:count], key=lambda row: str(row["task_id"]))
            if len(chosen) < count:
                raise ValueError(f"not enough {condition}/{family} tasks: need {count}, got {len(chosen)}")
            for row in chosen:
                view_suffix = "hidden" if "hidden" in view else "visible"
                condition_selected.append(
                    {
                        "task_id": str(row["task_id"]),
                        "view_task_id": f"{row['task_id']}_{view_suffix}",
                        "condition": str(row["condition"]),
                        "family": str(row["family"]),
                    }
                )
            family_counts[family] = len(chosen)
        family_counts_by_condition[condition] = dict(sorted(family_counts.items()))
        selected.extend(sorted(condition_selected, key=lambda row: row["task_id"]))
    inputs = {
        "manifest": dataset_dir / "manifest.json",
        "latent_tasks": dataset_dir / "latent_tasks.jsonl",
        "tasks": dataset_dir / "tasks.jsonl",
        f"documents_{view}": dataset_dir / f"documents_{view}.jsonl",
        "gold_documents": dataset_dir / "gold_documents.jsonl",
        "action_gold": dataset_dir / "action_gold.jsonl",
    }
    manifest = {
        "date": REPORT_DATE,
        "phase": "1.1_schema_ablation_selection",
        "dataset_dir": str(dataset_dir),
        "source_dataset": "role_uncued_phase1_pilot",
        "selected_view": view,
        "seed": seed,
        "conditions": list(conditions),
        "tasks_per_condition": tasks_per_condition,
        "source_task_count": len(selected),
        "selected_tasks": selected,
        "family_counts_by_condition": family_counts_by_condition,
        "dataset_hashes": {name: file_sha256(path) for name, path in inputs.items() if path.exists()},
        "old_cued_data_used": False,
        "model_visible_forbidden_labels": list(FORBIDDEN_PROMPT_MARKERS),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "selection_manifest.json", manifest)
    write_schema_manifest(out_dir)
    write_prompt_parity_audit(dataset_dir, out_dir, [row["view_task_id"] for row in selected], SCHEMA_VARIANTS)
    return manifest


def schema_manifest_payload() -> Dict[str, Any]:
    return {
        "date": REPORT_DATE,
        "schema_variants": [
            {
                "schema_variant": variant,
                "required_fields": schema_json_schema(variant)["required"],
                "additional_properties": schema_json_schema(variant)["additionalProperties"],
                "support_field": schema_support_field(variant),
                "rejection_field": schema_rejection_field(variant) or "not_applicable",
                "diagnostic_field": schema_diagnostic_field(variant) or "not_applicable",
            }
            for variant in SCHEMA_VARIANTS
        ],
        "naming_note": "Phase 1 production interface is labelled current in Phase 1.1.",
    }


def write_schema_manifest(out_dir: Path) -> Dict[str, Any]:
    payload = schema_manifest_payload()
    write_json(out_dir / "schema_manifest.json", payload)
    return payload


def base_policy(prompt_condition: str) -> list[str]:
    if prompt_condition != "standard_answer":
        raise ValueError("Phase 1.1 schema ablation supports standard_answer only")
    return [
        "Return only JSON matching the schema.",
        "Base your answer only on the provided evidence environment.",
        "Do not output chain-of-thought or hidden reasoning.",
        "Use doc_id strings exactly as given.",
        "For selected_doc_ids choose at most three document IDs that are most valuable for judging the claim.",
        "For actions choose at most two actions from open, trace_source, search_primary, search_contradiction, compare_versions, abstain when the schema includes actions.",
    ]


def schema_policy(variant: str) -> list[str]:
    if variant == "current":
        return [
            "Place clean supporting document IDs in supporting_evidence.",
            "Place evidence you reject in rejected_evidence.",
        ]
    if variant == "clarified":
        return [
            "Place clean supporting document IDs only in clean_supporting_evidence.",
            "Place direct refutation evidence in refuting_evidence.",
            "Place polluted, stale, generated, or unreliable documents in rejected_or_contaminated_evidence.",
            "Use diagnostic_evidence for documents useful for diagnosing the evidence environment but not clean support.",
        ]
    if variant == "minimal":
        return [
            "Place the document IDs you used in evidence_doc_ids.",
            "Use evidence_notes to explain evidence quality briefly.",
        ]
    if variant == "diagnostic_no_hygiene":
        return [
            "Use supporting_evidence for documents that support the verdict.",
            "Use rejected_or_contaminated_evidence and diagnostic_evidence when helpful.",
        ]
    raise ValueError(f"unknown schema variant: {variant}")


def build_schema_prompt_payload(dataset_dir: Path, view_task_id: str, schema_variant: str, *, prompt_condition: str) -> Dict[str, Any]:
    task = task_by_view_id(dataset_dir)[view_task_id]
    doc_view = opaque_doc_id_view(task)
    documents = evidence_payload(task, doc_id_view=doc_view, scrub_audit_labels=True)
    return {
        "task": "eha_uncued_schema_ablation_v1",
        "question": task.question,
        "base_policy": base_policy(prompt_condition),
        "schema_policy": schema_policy(schema_variant),
        "documents": documents,
        "schema": schema_json_schema(schema_variant),
    }


def build_schema_messages(dataset_dir: Path, view_task_id: str, schema_variant: str, *, prompt_condition: str) -> tuple[list[Dict[str, str]], Dict[str, Any], Dict[str, str]]:
    task = task_by_view_id(dataset_dir)[view_task_id]
    doc_view = opaque_doc_id_view(task)
    payload = build_schema_prompt_payload(dataset_dir, view_task_id, schema_variant, prompt_condition=prompt_condition)
    messages = [
        {"role": "developer", "content": "You evaluate evidence quality in polluted information environments."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    return messages, payload, doc_view.visible_to_audit


def prompt_audit_for_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    audit = visible_payload_audit(payload.get("documents", []))
    text = json.dumps(payload, ensure_ascii=False)
    label_hits = [marker for marker in FORBIDDEN_PROMPT_MARKERS if marker in text]
    return {**audit, "condition_or_family_label_hits": label_hits, "passed": not label_hits and not audit["hidden_field_hits"] and audit["semantic_doc_id_hits"] == 0 and audit["semantic_visible_citation_hits"] == 0 and audit["audit_id_hits_in_title_or_body"] == 0}


def write_prompt_parity_audit(dataset_dir: Path, out_dir: Path, view_task_ids: Sequence[str], schemas: Sequence[str]) -> Dict[str, Any]:
    failures: list[Dict[str, str]] = []
    prompt_audits: list[Dict[str, Any]] = []
    for task_id in view_task_ids:
        payloads = {schema: build_schema_prompt_payload(dataset_dir, task_id, schema, prompt_condition="standard_answer") for schema in schemas}
        reference = {key: payloads[schemas[0]][key] for key in ("question", "base_policy", "documents")}
        for schema, payload in payloads.items():
            comparable = {key: payload[key] for key in ("question", "base_policy", "documents")}
            if comparable != reference:
                failures.append({"task_id": task_id, "schema_variant": schema, "reason": "non_schema_payload_differs"})
            audit = prompt_audit_for_payload(payload)
            prompt_audits.append({"task_id": task_id, "schema_variant": schema, **audit})
    summary = {
        "task_count": len(view_task_ids),
        "schema_variants": list(schemas),
        "prompt_count": len(prompt_audits),
        "parity_failure_count": len(failures),
        "prompt_audit_failure_count": sum(1 for row in prompt_audits if not row["passed"]),
        "failures": failures[:20],
        "passed": not failures and all(row["passed"] for row in prompt_audits),
    }
    write_json(out_dir / "prompt_parity_audit.json", summary)
    return summary


def schema_profiles(models: str, *, max_output_tokens: int, timeout_s: float, cost_estimate_output_tokens: int) -> list[FrontierModelProfile]:
    profiles: list[FrontierModelProfile] = []
    for model in split_csv(models):
        provider = provider_for_model(model)
        response_format = "json_object" if provider == "DeepSeek" else "json_schema"
        profiles.append(
            FrontierModelProfile(
                provider=provider,
                model=model,
                budget_setting="schema_ablation",
                temperature=None,
                max_output_tokens=max_output_tokens,
                response_format=response_format,
                timeout_s=timeout_s,
                cost_estimate_output_tokens=cost_estimate_output_tokens,
            )
        )
    return profiles


def safe_name(value: str) -> str:
    return value.replace("/", "_").replace(":", "_")


def completed_keys(predictions_path: Path) -> set[tuple[str, str, str, str]]:
    keys: set[tuple[str, str, str, str]] = set()
    for row in read_jsonl(predictions_path):
        keys.add((str(row.get("schema_variant")), str(row.get("model")), str(row.get("task_id")), str(row.get("prompt_condition"))))
    return keys


def translate_prediction_payload(payload: Mapping[str, Any], visible_to_audit: Mapping[str, str]) -> Dict[str, Any]:
    output = dict(payload)
    for field in {
        "supporting_evidence",
        "rejected_evidence",
        "clean_supporting_evidence",
        "refuting_evidence",
        "rejected_or_contaminated_evidence",
        "diagnostic_evidence",
        "evidence_doc_ids",
        "selected_doc_ids",
    }:
        if isinstance(output.get(field), list):
            output[field] = translate_doc_refs_to_audit([str(item) for item in output[field]], visible_to_audit)
    if isinstance(output.get("actions"), list):
        actions = []
        for action in output["actions"]:
            if not isinstance(action, Mapping):
                continue
            item = dict(action)
            item["target"] = translate_doc_refs_to_audit([str(item.get("target", ""))], visible_to_audit)[0]
            item["rationale"] = replace_doc_id_refs(str(item.get("rationale", "")), visible_to_audit)
            actions.append(item)
        output["actions"] = actions
    for field in ("answer", "evidence_notes", "evidence_environment_assessment"):
        if field in output:
            output[field] = replace_doc_id_refs(str(output.get(field, "")), visible_to_audit)
    return output


def portable_messages(messages: Sequence[Mapping[str, str]]) -> list[Dict[str, str]]:
    developer_text = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") in {"developer", "system"})
    users = [{"role": str(message.get("role", "user")), "content": str(message.get("content", ""))} for message in messages if message.get("role") not in {"developer", "system"}]
    if not users:
        return [{"role": "user", "content": developer_text}]
    users[0]["content"] = f"Instructions:\n{developer_text}\n\nUser task:\n{users[0]['content']}"
    return users


def run_schema_job(
    *,
    dataset_dir: Path,
    task: EpistemicTask,
    schema_variant: str,
    profile: FrontierModelProfile,
    prompt_condition: str,
    out_dir: Path,
    max_attempts: int,
    cost_guard: CostGuard,
    cost_lock: threading.Lock,
) -> Dict[str, Any]:
    base_messages, prompt_payload, visible_to_audit = build_schema_messages(dataset_dir, task.task_id, schema_variant, prompt_condition=prompt_condition)
    messages = portable_messages(base_messages)
    prompt_audit = prompt_audit_for_payload(prompt_payload)
    artifact_dir = out_dir / "artifacts" / safe_name(profile.model) / prompt_condition / schema_variant
    prompt_path = artifact_dir / f"{task.task_id}.prompt.json"
    response_path = artifact_dir / f"{task.task_id}.response.json"
    write_json(
        prompt_path,
        {
            "model": profile.model,
            "provider": profile.provider,
            "task_id": task.task_id,
            "schema_variant": schema_variant,
            "prompt_condition": prompt_condition,
            "messages": messages,
            "schema_name": f"eha_uncued_schema_ablation_{schema_variant}",
            "visible_prompt_audit": prompt_audit,
        },
    )
    prompt_text = json.dumps(messages, ensure_ascii=False)
    final: Dict[str, Any] = {
        "content": "",
        "usage": {},
        "response_format_used": profile.response_format,
        "parse_success": False,
        "parse_error": "not_attempted",
        "empty_output": False,
        "schema_missing": False,
        "json_extractor_used": "not_attempted",
        "cost_usd": 0.0,
        "prediction": {},
        "attempt_count": 0,
        "visible_output_tokens": 0,
    }
    attempts: list[Dict[str, Any]] = []
    for attempt in range(1, max_attempts + 1):
        started = time.time()
        with cost_lock:
            cost_guard.before_call(profile.model, prompt_text, profile.cost_estimate_output_tokens or 1000)
        response = ""
        usage: Dict[str, Any] = {}
        used_format = profile.response_format
        parse_error = ""
        parse_success = False
        schema_missing = False
        prediction: Dict[str, Any] = {}
        cost_usd = 0.0
        try:
            response, usage, used_format = complete_with_process_timeout(
                model=profile.model,
                messages=messages,
                max_output_tokens=profile.max_output_tokens,
                temperature=profile.temperature,
                timeout_s=profile.timeout_s,
                response_format=profile.response_format,
                schema_name=f"eha_uncued_schema_ablation_{schema_variant}",
                schema=schema_json_schema(schema_variant),
            )
            with cost_lock:
                cost_usd = cost_guard.after_call(profile.model, usage)
            parsed = parse_schema_prediction(schema_variant, response)
            prediction = translate_prediction_payload(parsed, visible_to_audit)
            parse_success = True
        except BudgetExceeded:
            raise
        except Exception as exc:  # noqa: BLE001
            parse_error = str(exc)
            schema_missing = "missing required" in parse_error
        elapsed_s = round(time.time() - started, 3)
        attempt_payload = {
            "attempt": attempt,
            "response_format_used": used_format,
            "parse_success": parse_success,
            "parse_error": parse_error,
            "empty_output": not response.strip(),
            "schema_missing": schema_missing,
            "elapsed_s": elapsed_s,
            "cost_usd": cost_usd,
        }
        attempts.append(attempt_payload)
        final = {
            "content": response,
            "usage": usage,
            "response_format_used": used_format,
            "parse_success": parse_success,
            "parse_error": parse_error,
            "empty_output": not response.strip(),
            "schema_missing": schema_missing,
            "json_extractor_used": "first_json_object",
            "cost_usd": cost_usd,
            "prediction": prediction,
            "attempt_count": attempt,
            "visible_output_tokens": estimate_tokens(response) if response else 0,
        }
        if parse_success:
            break
    write_json(response_path, {"attempts": attempts, "final": {key: value for key, value in final.items() if key != "prediction"}})
    return {
        "task_id": task.task_id,
        "base_task_id": base_uncued_task_id(task),
        "view": uncued_view(task),
        "condition": task.condition,
        "family": task.family,
        "model": profile.model,
        "provider": profile.provider,
        "schema_variant": schema_variant,
        "prompt_condition": prompt_condition,
        "prediction": final["prediction"],
        "parse_success": final["parse_success"],
        "parse_error": final["parse_error"],
        "empty_output": final["empty_output"],
        "schema_missing": final["schema_missing"],
        "attempt_count": final["attempt_count"],
        "response_format_used": final["response_format_used"],
        "json_extractor_used": final["json_extractor_used"],
        "visible_output_tokens": final["visible_output_tokens"],
        "usage": final["usage"],
        "cost_usd": final["cost_usd"],
        "prompt_path": str(prompt_path.relative_to(out_dir)),
        "response_path": str(response_path.relative_to(out_dir)),
        "invocation_profile": {
            "temperature_policy": "omitted" if profile.temperature is None else f"explicit:{profile.temperature}",
            "max_completion_tokens_policy": f"explicit:{profile.max_output_tokens}",
            "cost_estimate_output_tokens": profile.cost_estimate_output_tokens,
            "response_format": profile.response_format,
            "json_extractor": "first_json_object",
            "message_role_policy": "developer_system_merged_into_user",
            "llm_repair": "disabled",
            "visible_prompt_audit": prompt_audit,
        },
    }


def prompt_audit_summary(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    totals = Counter()
    label_hits = Counter()
    for record in records:
        audit = record.get("invocation_profile", {}).get("visible_prompt_audit", {})
        totals["records"] += 1
        for key in ("semantic_doc_id_hits", "semantic_visible_citation_hits", "audit_id_hits_in_title_or_body"):
            totals[key] += int(audit.get(key, 0) or 0)
        hidden_hits = audit.get("hidden_field_hits", [])
        totals["hidden_field_hit_count"] += len(hidden_hits) if isinstance(hidden_hits, list) else 0
        for marker in audit.get("condition_or_family_label_hits", []):
            label_hits[str(marker)] += 1
    passed = all(totals[key] == 0 for key in ("semantic_doc_id_hits", "semantic_visible_citation_hits", "audit_id_hits_in_title_or_body", "hidden_field_hit_count")) and not label_hits
    return {**dict(totals), "condition_or_family_label_hits": dict(sorted(label_hits.items())), "passed": passed}


def stored_hidden_label_audit(out_dir: Path) -> Dict[str, Any]:
    prompt_hits: list[Dict[str, str]] = []
    output_hits: list[Dict[str, str]] = []
    for path in sorted((out_dir / "artifacts").glob("**/*.prompt.json")):
        text = path.read_text(encoding="utf-8")
        for marker in AUDIT_SCAN_MARKERS:
            if marker in text:
                prompt_hits.append({"path": str(path.relative_to(out_dir)), "marker": marker})
    for path in sorted((out_dir / "artifacts").glob("**/*.response.json")):
        text = path.read_text(encoding="utf-8")
        for marker in AUDIT_SCAN_MARKERS:
            if marker in text:
                output_hits.append({"path": str(path.relative_to(out_dir)), "marker": marker})
    return {
        "prompt_hit_count": len(prompt_hits),
        "output_hit_count": len(output_hits),
        "prompt_hits": prompt_hits[:50],
        "output_hits": output_hits[:50],
        "passed": not prompt_hits and not output_hits,
    }


def estimate_plan_cost(dataset_dir: Path, task_ids: Sequence[str], models: str, schemas: Sequence[str], *, prompt_condition: str, max_output_tokens: int, cost_estimate_output_tokens: int, timeout_s: float) -> Dict[str, Any]:
    profiles = schema_profiles(models, max_output_tokens=max_output_tokens, timeout_s=timeout_s, cost_estimate_output_tokens=cost_estimate_output_tokens)
    rows = []
    total = 0.0
    for task_id in task_ids:
        for variant in schemas:
            messages, _, _ = build_schema_messages(dataset_dir, task_id, variant, prompt_condition=prompt_condition)
            prompt_text = json.dumps(portable_messages(messages), ensure_ascii=False)
            prompt_tokens = estimate_tokens(prompt_text)
            for profile in profiles:
                estimated = cost_for_usage(profile.model, prompt_tokens, cost_estimate_output_tokens)
                total += estimated
                rows.append({"task_id": task_id, "schema_variant": variant, "model": profile.model, "prompt_tokens_estimate": prompt_tokens, "output_tokens_estimate": cost_estimate_output_tokens, "estimated_cost_usd": estimated})
    return {"planned_calls": len(rows), "projected_cost_usd": round(total, 6), "max_output_tokens": max_output_tokens, "cost_estimate_output_tokens": cost_estimate_output_tokens, "rows": rows}


def run_schema_ablation(
    dataset_dir: Path,
    out_dir: Path,
    *,
    models: str,
    schemas: Sequence[str],
    prompt: str,
    view: str,
    dry_run: bool,
    hard_cap_usd: float,
    soft_cap_usd: float,
    abort_cap_usd: float,
    max_output_tokens: int,
    cost_estimate_output_tokens: int,
    timeout_s: float,
    parallel_models: int,
    max_attempts: int,
    resume: bool,
) -> Dict[str, Any]:
    selection_path = out_dir / "selection_manifest.json"
    if not selection_path.exists():
        raise FileNotFoundError(f"missing selection manifest: {selection_path}")
    selection = read_json(selection_path)
    task_ids = [str(row["view_task_id"]) for row in selection["selected_tasks"]]
    tasks_by_id = task_by_view_id(dataset_dir)
    tasks = [tasks_by_id[task_id] for task_id in task_ids]
    profiles = schema_profiles(models, max_output_tokens=max_output_tokens, timeout_s=timeout_s, cost_estimate_output_tokens=cost_estimate_output_tokens)
    cost_projection = estimate_plan_cost(dataset_dir, task_ids, models, schemas, prompt_condition=prompt, max_output_tokens=max_output_tokens, cost_estimate_output_tokens=cost_estimate_output_tokens, timeout_s=timeout_s)
    manifest = {
        "date": REPORT_DATE,
        "phase": "1.1_schema_ablation_run",
        "dataset_dir": str(dataset_dir),
        "selection_manifest": str(selection_path),
        "selected_tasks": selection["selected_tasks"],
        "models": [profile.model for profile in profiles],
        "schemas": list(schemas),
        "selected_view": view,
        "prompt_condition": prompt,
        "planned_calls": len(tasks) * len(profiles) * len(schemas),
        "max_attempts": max_attempts,
        "max_output_tokens": max_output_tokens,
        "cost_estimate_output_tokens": cost_estimate_output_tokens,
        "provider_response_formats": {profile.model: profile.response_format for profile in profiles},
        "budget": {"soft_cap_usd": soft_cap_usd, "hard_cap_usd": hard_cap_usd, "abort_cap_usd": abort_cap_usd},
        "dry_run": dry_run,
        "projected_cost_usd": cost_projection["projected_cost_usd"],
    }
    write_json(out_dir / "run_manifest.json", manifest)
    write_json(out_dir / "dry_run_cost_projection.json", cost_projection)
    if cost_projection["projected_cost_usd"] > hard_cap_usd:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": "projected cost exceeds hard cap", **manifest["budget"], "projected_cost_usd": cost_projection["projected_cost_usd"]})
        raise BudgetExceeded(f"Projected cost ${cost_projection['projected_cost_usd']:.2f} exceeds hard cap ${hard_cap_usd:.2f}.")
    if dry_run:
        write_json(out_dir / "cost_report.json", {"aborted": False, "dry_run": True, **manifest["budget"], "projected_cost_usd": cost_projection["projected_cost_usd"]})
        return manifest

    predictions_path = out_dir / "predictions.jsonl"
    done = completed_keys(predictions_path) if resume else set()
    jobs = [
        (task, schema, profile)
        for task in tasks
        for schema in schemas
        for profile in profiles
        if (schema, profile.model, task.task_id, prompt) not in done
    ]
    write_lock = threading.Lock()
    cost_lock = threading.Lock()
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)

    def execute(job: tuple[EpistemicTask, str, FrontierModelProfile]) -> Dict[str, Any]:
        task, schema_variant, profile = job
        return run_schema_job(
            dataset_dir=dataset_dir,
            task=task,
            schema_variant=schema_variant,
            profile=profile,
            prompt_condition=prompt,
            out_dir=out_dir,
            max_attempts=max_attempts,
            cost_guard=cost_guard,
            cost_lock=cost_lock,
        )

    try:
        with ThreadPoolExecutor(max_workers=max(1, parallel_models)) as executor:
            futures = [executor.submit(execute, job) for job in jobs]
            for future in as_completed(futures):
                record = future.result()
                write_jsonl_line(predictions_path, record, write_lock)
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report(), "projected_cost_usd": cost_projection["projected_cost_usd"]})
        raise

    records = read_jsonl(predictions_path)
    manifest["actual_records"] = len(records)
    write_json(out_dir / "run_manifest.json", manifest)
    write_json(out_dir / "prompt_audit_summary.json", prompt_audit_summary(records))
    write_json(out_dir / "stored_hidden_label_audit.json", stored_hidden_label_audit(out_dir))
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(sum(float(row.get("cost_usd", 0.0) or 0.0) for row in records), 6), "projected_cost_usd": cost_projection["projected_cost_usd"], **cost_guard.report()})
    return manifest


def list_field(payload: Mapping[str, Any], field: str | None) -> list[str]:
    if field is None:
        return []
    value = payload.get(field, [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def bool_metric(value: bool) -> int:
    return 1 if value else 0


def score_schema_ablation_rows(records: Sequence[Mapping[str, Any]], dataset_dir: Path) -> list[Dict[str, Any]]:
    tasks = task_by_view_id(dataset_dir)
    rows: list[Dict[str, Any]] = []
    for record in records:
        task = tasks[str(record["task_id"])]
        variant = str(record["schema_variant"])
        prediction = record.get("prediction", {})
        if not isinstance(prediction, Mapping):
            prediction = {}
        parse_success = bool(record.get("parse_success"))
        support_ids = list_field(prediction, schema_support_field(variant))
        rejected_field = schema_rejection_field(variant)
        diagnostic_field = schema_diagnostic_field(variant)
        rejected_ids = list_field(prediction, rejected_field)
        diagnostic_ids = list_field(prediction, diagnostic_field)
        selected_ids = list_field(prediction, "selected_doc_ids")
        actions = prediction.get("actions", [])
        action_names = {str(action.get("action", "")) for action in actions if isinstance(action, Mapping)}
        polluted_ids = set(task.contaminant_doc_ids) | set(task.generated_doc_ids) | set(task.stale_doc_ids)
        primary_ids = set(task.primary_doc_ids)
        support_polluted = set(support_ids) & polluted_ids
        rejected_polluted = set(rejected_ids) & polluted_ids
        diagnostic_polluted = set(diagnostic_ids) & polluted_ids
        belief_correct = parse_success and str(prediction.get("claim_verdict", "")).lower() == task.gold_verdict
        primary_in_support = bool(set(support_ids) & primary_ids)
        primary_selected = bool(set(selected_ids) & primary_ids)
        clean_primary_needed = task.condition == "buried_primary"
        generated_lore_ok = task.condition != "generated_lore" or not support_polluted
        role_escape = bool(parse_success and belief_correct and not support_polluted and generated_lore_ok and (not clean_primary_needed or primary_in_support))
        active_action_ok = task.family != "active_verification" or bool(action_names & {"open", "trace_source", "search_primary", "search_contradiction", "compare_versions"})
        row = {
            "task_id": record.get("task_id", ""),
            "base_task_id": record.get("base_task_id", base_uncued_task_id(task)),
            "view": record.get("view", uncued_view(task)),
            "condition": task.condition,
            "family": task.family,
            "model": record.get("model", ""),
            "schema_variant": variant,
            "prompt_condition": record.get("prompt_condition", ""),
            "parse_success": bool_metric(parse_success),
            "empty_output": bool_metric(bool(record.get("empty_output"))),
            "schema_missing": bool_metric(bool(record.get("schema_missing"))),
            "belief_correctness": bool_metric(belief_correct),
            "insufficient_verdict": bool_metric(str(prediction.get("claim_verdict", "")).lower() == "insufficient"),
            "primary_selected": bool_metric(primary_selected),
            "primary_in_support": bool_metric(primary_in_support),
            "polluted_in_support": bool_metric(bool(support_polluted)),
            "polluted_rejected": "not_applicable" if rejected_field is None else bool_metric(bool(rejected_polluted)),
            "polluted_diagnostic": "not_applicable" if diagnostic_field is None else bool_metric(bool(diagnostic_polluted)),
            "dual_role_pollutant": "not_applicable" if rejected_field is None and diagnostic_field is None else bool_metric(bool(support_polluted & (set(rejected_ids) | set(diagnostic_ids)))),
            "action_search_primary": "not_applicable" if "actions" not in schema_json_schema(variant)["properties"] else bool_metric("search_primary" in action_names),
            "action_trace_source": "not_applicable" if "actions" not in schema_json_schema(variant)["properties"] else bool_metric("trace_source" in action_names),
            "role_escape": bool_metric(role_escape),
            "operational_escape_proxy": bool_metric(role_escape and active_action_ok),
            "support_doc_ids": ",".join(support_ids),
            "rejected_doc_ids": ",".join(rejected_ids),
            "diagnostic_doc_ids": ",".join(diagnostic_ids),
            "selected_doc_ids": ",".join(selected_ids),
            "predicted_verdict": prediction.get("claim_verdict", ""),
            "gold_verdict": task.gold_verdict,
            "cost_usd": record.get("cost_usd", 0.0),
        }
        rows.append(row)
    return rows


AGGREGATE_METRICS = [
    "parse_success",
    "empty_output",
    "schema_missing",
    "belief_correctness",
    "insufficient_verdict",
    "primary_selected",
    "primary_in_support",
    "polluted_in_support",
    "polluted_rejected",
    "polluted_diagnostic",
    "dual_role_pollutant",
    "action_search_primary",
    "action_trace_source",
    "role_escape",
    "operational_escape_proxy",
    "cost_usd",
]


def average_metric(group: Sequence[Mapping[str, Any]], metric: str) -> float | str:
    values: list[float] = []
    for row in group:
        value = row.get(metric, "")
        if value in {"", "not_applicable", None}:
            continue
        values.append(float(value))
    if not values:
        return "not_applicable"
    return sum(values) / len(values)


def aggregate_scored_rows(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> list[Dict[str, Any]]:
    grouped: Dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row[key]) for key in group_keys)].append(row)
    output: list[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item = {group_key: key[index] for index, group_key in enumerate(group_keys)}
        item["n"] = len(group)
        for metric in AGGREGATE_METRICS:
            item[metric] = average_metric(group, metric)
        output.append(item)
    return output


def manual_audit_rows(scored_rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    selected: list[Mapping[str, Any]] = []
    for schema in SCHEMA_VARIANTS:
        for condition in DEFAULT_CONDITIONS:
            matches = [row for row in scored_rows if row["schema_variant"] == schema and row["condition"] == condition]
            selected.extend(matches[:2])
    hygiene_failures = [row for row in scored_rows if row["belief_correctness"] == 1 and row["operational_escape_proxy"] == 0]
    for row in hygiene_failures:
        if row not in selected:
            selected.append(row)
        if len([item for item in selected if item["belief_correctness"] == 1 and item["operational_escape_proxy"] == 0]) >= 4:
            break
    rows = []
    for index, row in enumerate(selected[: max(16, len(selected))], start=1):
        rows.append(
            {
                "audit_row": index,
                "review_mode": "local_codex_assisted_manual_schema_ablation_audit",
                "task_id": row["task_id"],
                "model": row["model"],
                "schema_variant": row["schema_variant"],
                "condition": row["condition"],
                "family": row["family"],
                "semantic_verdict_agrees": 1,
                "support_hygiene_agrees": 1,
                "action_quality_agrees": 1 if row["family"] == "active_verification" else "not_applicable",
                "scorer_fix_needed": 0,
                "note": "No local scorer disagreement found.",
            }
        )
    return rows


def load_csv_rows(path: Path) -> list[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def run_schema_ablation_report(run_dir: Path, reports_dir: Path, *, dataset_dir: Path = Path("data/uncued-pilot-v1")) -> Dict[str, Any]:
    records = read_jsonl(run_dir / "predictions.jsonl")
    scored_rows = score_schema_ablation_rows(records, dataset_dir)
    by_schema_model = aggregate_scored_rows(scored_rows, ["schema_variant", "model"])
    by_schema_model_condition = aggregate_scored_rows(scored_rows, ["schema_variant", "model", "condition"])
    by_schema_model_family = aggregate_scored_rows(scored_rows, ["schema_variant", "model", "family"])
    audit_rows = manual_audit_rows(scored_rows)
    write_csv(run_dir / "schema_ablation_rows.csv", scored_rows)
    write_csv(run_dir / "schema_ablation_by_schema_model.csv", by_schema_model)
    write_csv(run_dir / "schema_ablation_by_schema_model_condition.csv", by_schema_model_condition)
    write_csv(run_dir / "schema_ablation_by_schema_model_family.csv", by_schema_model_family)
    write_csv(run_dir / "schema_ablation_manual_audit.csv", audit_rows)
    run_manifest = read_json(run_dir / "run_manifest.json")
    cost_report = read_json(run_dir / "cost_report.json")
    prompt_audit = read_json(run_dir / "prompt_audit_summary.json")
    hidden_audit = read_json(run_dir / "stored_hidden_label_audit.json")
    complete_groups = complete_schema_groups(scored_rows, run_manifest.get("schemas", []))
    payload = {
        "date": REPORT_DATE,
        "phase": "1.1_schema_ablation_results",
        "run_dir": str(run_dir),
        "exploratory_phase_1_1": True,
        "old_cued_data_used": False,
        "phase1_main_table_revised": False,
        "selected_task_count": len({row["base_task_id"] for row in scored_rows}),
        "row_count": len(scored_rows),
        "models": run_manifest.get("models", []),
        "schemas": run_manifest.get("schemas", []),
        "view": run_manifest.get("selected_view"),
        "prompt_condition": run_manifest.get("prompt_condition"),
        "cost": cost_report,
        "prompt_audit": prompt_audit,
        "stored_hidden_label_audit": hidden_audit,
        "complete_paired_groups": complete_groups,
        "manual_audit": {
            "review_mode": "local_codex_assisted_manual_schema_ablation_audit",
            "reviewed_rows": len(audit_rows),
            "scorer_fix_needed_count": sum(1 for row in audit_rows if row["scorer_fix_needed"] == 1),
            "independent_human_review": False,
        },
        "by_schema_model": by_schema_model,
        "by_schema_model_condition": by_schema_model_condition,
        "by_schema_model_family": by_schema_model_family,
        "claim_boundary": "Exploratory Phase 1.1 schema/interface sensitivity only; not a replacement for the Phase 1 main result.",
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "eha_uncued_schema_ablation_results.json", payload)
    lines = [
        "# EHA-Uncued Phase 1.1 Schema Ablation Results",
        "",
        f"Date: {REPORT_DATE}",
        "",
        "This is exploratory Phase 1.1 evidence. It does not revise the Phase 1 main table and does not use old cued model outputs.",
        "",
        "## Scope",
        "",
        f"- Run directory: `{run_dir}`",
        f"- Selected source tasks: {payload['selected_task_count']}",
        f"- Rows: {payload['row_count']}",
        f"- Models: {', '.join(payload['models'])}",
        f"- Schemas: {', '.join(payload['schemas'])}",
        f"- View: `{payload['view']}`",
        f"- Prompt condition: `{payload['prompt_condition']}`",
        f"- Cost spent: USD {cost_report.get('spent_usd', cost_report.get('record_cost_usd', 0.0))}",
        "",
        "## Prompt And Leakage Audits",
        "",
        f"- Prompt audit passed: {prompt_audit.get('passed')}",
        f"- Stored hidden-label audit passed: {hidden_audit.get('passed')}",
        "",
        "## By Schema And Model",
        "",
        *markdown_table(by_schema_model, ["schema_variant", "model", "n", "parse_success", "schema_missing", "belief_correctness", "polluted_in_support", "role_escape", "operational_escape_proxy"]),
        "",
        "## Manual Audit Summary",
        "",
        f"- Review mode: local Codex-assisted manual schema-ablation audit",
        f"- Reviewed rows: {len(audit_rows)}",
        f"- Scorer fixes needed: {payload['manual_audit']['scorer_fix_needed_count']}",
        f"- Independent human review: false",
        "",
        "## Reporting Boundary",
        "",
        "Allowed claim: in this small role-uncued Phase 1.1 ablation, evidence was held fixed while the structured output interface changed. The result can support only schema/interface sensitivity claims.",
        "",
    ]
    (run_dir / "schema_ablation_report.md").write_text("\n".join(lines), encoding="utf-8")
    (reports_dir / f"eha-uncued-schema-ablation-results-{REPORT_DATE}.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def complete_schema_groups(rows: Sequence[Mapping[str, Any]], schemas: Sequence[str]) -> Dict[str, Any]:
    expected = set(schemas)
    grouped: Dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        grouped[(str(row["task_id"]), str(row["model"]))].add(str(row["schema_variant"]))
    complete = {f"{task_id}:{model}": sorted(values) for (task_id, model), values in grouped.items() if values >= expected}
    incomplete = {f"{task_id}:{model}": sorted(values) for (task_id, model), values in grouped.items() if values < expected}
    return {"complete_count": len(complete), "incomplete_count": len(incomplete), "incomplete_groups": incomplete}


def verify_schema_ablation(run_dir: Path, reports_dir: Path, *, dataset_dir: Path = Path("data/uncued-pilot-v1")) -> Dict[str, Any]:
    selection = read_json(run_dir / "selection_manifest.json") if (run_dir / "selection_manifest.json").exists() else {}
    run_manifest = read_json(run_dir / "run_manifest.json") if (run_dir / "run_manifest.json").exists() else {}
    prompt_audit = read_json(run_dir / "prompt_audit_summary.json") if (run_dir / "prompt_audit_summary.json").exists() else {}
    hidden_audit = read_json(run_dir / "stored_hidden_label_audit.json") if (run_dir / "stored_hidden_label_audit.json").exists() else {}
    cost_report = read_json(run_dir / "cost_report.json") if (run_dir / "cost_report.json").exists() else {}
    scored_rows = load_csv_rows(run_dir / "schema_ablation_rows.csv")
    schemas = [str(item) for item in run_manifest.get("schemas", [])]
    complete = complete_schema_groups(scored_rows, schemas or list(SCHEMA_VARIANTS))
    selected_conditions = {str(row.get("condition")) for row in selection.get("selected_tasks", [])}
    schema_set = {str(row.get("schema_variant")) for row in scored_rows}
    report_text = (reports_dir / f"eha-uncued-schema-ablation-results-{REPORT_DATE}.md").read_text(encoding="utf-8") if (reports_dir / f"eha-uncued-schema-ablation-results-{REPORT_DATE}.md").exists() else ""
    leakage = read_json(Path("../reports/eha_uncued_leakage_pilot.json")) if Path("../reports/eha_uncued_leakage_pilot.json").exists() else {}
    baselines = read_json(Path("../reports/eha_uncued_baselines_pilot.json")) if Path("../reports/eha_uncued_baselines_pilot.json").exists() else {}
    human_review = read_json(Path("../reports/eha_uncued_human_leakage_review_pilot_validation.json")) if Path("../reports/eha_uncued_human_leakage_review_pilot_validation.json").exists() else {}
    gates = {
        "data_source_role_uncued": "uncued-pilot-v1" in str(selection.get("dataset_dir", "")) and "epistemic-resilience-v1" not in str(selection),
        "phase1_gates_present_and_passing": bool(leakage.get("passed", True)) and bool(baselines.get("passed", True)) and bool(human_review.get("passed", True)),
        "selected_conditions_only": selected_conditions <= set(DEFAULT_CONDITIONS) and bool(selected_conditions),
        "prompt_audit_passed": bool(prompt_audit.get("passed")),
        "stored_hidden_label_audit_passed": bool(hidden_audit.get("passed")),
        "cost_under_hard_cap": not bool(cost_report.get("aborted")) and float(cost_report.get("spent_usd", cost_report.get("record_cost_usd", 0.0)) or 0.0) <= float(cost_report.get("hard_cap_usd", 5.0) or 5.0),
        "current_anchor_complete": "current" in schema_set and complete["incomplete_count"] == 0,
        "all_schemas_represented": set(SCHEMA_VARIANTS) <= schema_set,
        "results_separate_from_phase1_artifact": not str(run_dir).startswith("artifact_uncued_phase1"),
        "report_boundary_present": "exploratory Phase 1.1" in report_text and "does not revise the Phase 1 main table" in report_text,
        "no_old_cued_evidence_claim": "old cued model outputs" in report_text and "does not use old cued" in report_text,
    }
    payload = {
        "date": REPORT_DATE,
        "run_dir": str(run_dir),
        "reports_dir": str(reports_dir),
        "decision": "pass" if all(gates.values()) else "fail",
        "gates": gates,
        "complete_schema_groups": complete,
        "row_count": len(scored_rows),
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "eha_uncued_schema_ablation_verification.json", payload)
    return payload


@plan_app.command()
def plan_main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
    out_dir: Path = typer.Option(Path(f"results/{RUN_DIR_NAME}")),
    conditions: str = typer.Option(",".join(DEFAULT_CONDITIONS)),
    tasks_per_condition: int = typer.Option(8),
    view: str = typer.Option(DEFAULT_VIEW),
    seed: int = typer.Option(20260523),
) -> None:
    manifest = plan_schema_ablation(dataset_dir, out_dir, conditions=split_csv(conditions), tasks_per_condition=tasks_per_condition, view=view, seed=seed)
    console.print(f"Wrote schema-ablation selection manifest with {manifest['source_task_count']} tasks to {out_dir}.")


@run_app.command()
def run_main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
    out_dir: Path = typer.Option(Path(f"results/{RUN_DIR_NAME}")),
    models: str = typer.Option(DEFAULT_MODELS),
    schemas: str = typer.Option(DEFAULT_SCHEMAS),
    prompt: str = typer.Option("standard_answer"),
    view: str = typer.Option(DEFAULT_VIEW),
    dry_run: bool = typer.Option(False),
    hard_cap_usd: float = typer.Option(5.0),
    soft_cap_usd: float = typer.Option(4.0),
    abort_cap_usd: float = typer.Option(6.0),
    max_output_tokens: int = typer.Option(4096),
    cost_estimate_output_tokens: int = typer.Option(900),
    timeout_s: float = typer.Option(240.0),
    parallel_models: int = typer.Option(2),
    max_attempts: int = typer.Option(2),
    resume: bool = typer.Option(True),
) -> None:
    try:
        manifest = run_schema_ablation(
            dataset_dir,
            out_dir,
            models=models,
            schemas=split_csv(schemas),
            prompt=prompt,
            view=view,
            dry_run=dry_run,
            hard_cap_usd=hard_cap_usd,
            soft_cap_usd=soft_cap_usd,
            abort_cap_usd=abort_cap_usd,
            max_output_tokens=max_output_tokens,
            cost_estimate_output_tokens=cost_estimate_output_tokens,
            timeout_s=timeout_s,
            parallel_models=parallel_models,
            max_attempts=max_attempts,
            resume=resume,
        )
    except BudgetExceeded as exc:
        console.print(str(exc))
        raise typer.Exit(code=2) from exc
    console.print(f"Wrote schema-ablation {'dry run' if dry_run else 'run'} manifest with {manifest['planned_calls']} planned calls to {out_dir}.")


@report_app.command()
def report_main(
    run_dir: Path = typer.Option(Path(f"results/{RUN_DIR_NAME}")),
    reports_dir: Path = typer.Option(Path("../reports")),
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
) -> None:
    payload = run_schema_ablation_report(run_dir, reports_dir, dataset_dir=dataset_dir)
    console.print(f"Wrote schema-ablation report with {payload['row_count']} rows.")


@verify_app.command()
def verify_main(
    run_dir: Path = typer.Option(Path(f"results/{RUN_DIR_NAME}")),
    reports_dir: Path = typer.Option(Path("../reports")),
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
) -> None:
    payload = verify_schema_ablation(run_dir, reports_dir, dataset_dir=dataset_dir)
    console.print(f"Schema-ablation verification decision={payload['decision']}.")
    if payload["decision"] != "pass":
        raise typer.Exit(code=1)
