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
from .epistemic_frontier_main import FrontierModelProfile, fallback_prediction, output_budget_diagnostics
from .epistemic_model_preflight import complete_with_process_timeout, load_preflight_tasks, parse_prediction_with_diagnostics, provider_for_model
from .epistemic_resilience import (
    EpistemicPrediction,
    EpistemicRunRecord,
    EpistemicTask,
    evidence_payload,
    epistemic_prediction_json_schema,
    normalize_prediction,
    opaque_doc_id_view,
    score_record,
    translate_prediction_to_audit_ids,
    visible_payload_audit,
)
from .report import markdown_table, write_csv
from .schemas import model_to_dict, write_json
from .uncued_contract import split_csv
from .uncued_report import action_exact_target_rate, read_action_gold
from .uncued_run import HIDDEN_PROMPT_MARKERS, base_uncued_task_id, uncued_view


REPORT_DATE = "2026-05-25"
RUN_DIR_NAME = f"reports-eha-uncued-robustness-{REPORT_DATE}"
DEFAULT_CONDITIONS = ("generated_lore", "buried_primary", "conflicting_evidence", "false_consensus")
DEFAULT_MODELS = "gpt-5.5,gemini-3.1-pro-preview"
DEFAULT_VIEW = "neutral_metadata_visible"
DEFAULT_SCHEMA = "current_phase1_interface"
DEFAULT_PROMPT = "standard_answer"
ROBUSTNESS_VARIANTS = (
    "baseline_original",
    "order_randomized",
    "source_type_masked",
    "prompt_paraphrase",
    "citation_masked",
)
BASELINE_VARIANT = "baseline_original"
FORBIDDEN_PROMPT_MARKERS = HIDDEN_PROMPT_MARKERS + (
    "packet_judgment",
    "evidence_selection",
    "active_verification",
)
AUDIT_SCAN_MARKERS = FORBIDDEN_PROMPT_MARKERS + (
    "primary_doc_ids",
    "contaminant_doc_ids",
    "generated_doc_ids",
    "stale_doc_ids",
    "gold_verdict",
    "hidden_role",
)


plan_app = typer.Typer(add_completion=False, help="Plan the EHA-Uncued Phase 1.3 robustness mini-suite.")
run_app = typer.Typer(add_completion=False, help="Run the EHA-Uncued Phase 1.3 robustness mini-suite.")
report_app = typer.Typer(add_completion=False, help="Report EHA-Uncued Phase 1.3 robustness results.")
verify_app = typer.Typer(add_completion=False, help="Verify EHA-Uncued Phase 1.3 robustness artifacts.")
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


def load_csv_rows(path: Path) -> list[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def robustness_schema(schema_variant: str) -> Dict[str, Any]:
    if schema_variant != DEFAULT_SCHEMA:
        raise ValueError(f"unknown robustness schema variant: {schema_variant}")
    return epistemic_prediction_json_schema()


def standard_policy(prompt_condition: str) -> list[str]:
    if prompt_condition != DEFAULT_PROMPT:
        raise ValueError("Phase 1.3 robustness supports standard_answer only")
    return [
        "Return only JSON matching the schema.",
        "Base your answer only on the provided evidence environment.",
        "Do not output chain-of-thought or hidden reasoning.",
        "Use doc_id strings exactly as given.",
        "Place document IDs that support your verdict in supporting_evidence.",
        "Place document IDs you do not rely on in rejected_evidence.",
        "For selected_doc_ids choose at most three document IDs that are most valuable for judging the claim.",
        "For actions choose at most two actions from open, trace_source, search_primary, search_contradiction, compare_versions, abstain.",
    ]


def paraphrased_policy(prompt_condition: str) -> list[str]:
    if prompt_condition != DEFAULT_PROMPT:
        raise ValueError("Phase 1.3 robustness supports standard_answer only")
    return [
        "Output a single JSON object that conforms to the schema.",
        "Use only the supplied evidence environment when deciding.",
        "Do not include chain-of-thought or private reasoning.",
        "Copy doc_id values exactly as shown.",
        "List IDs that support your verdict in supporting_evidence.",
        "List IDs you set aside in rejected_evidence.",
        "In selected_doc_ids, include no more than three IDs most useful for judging the claim.",
        "In actions, include no more than two items chosen from open, trace_source, search_primary, search_contradiction, compare_versions, abstain.",
    ]


def task_by_view_id(dataset_dir: Path) -> Dict[str, EpistemicTask]:
    return {task.task_id: task for task in load_preflight_tasks(dataset_dir)}


def latent_rows_by_task(dataset_dir: Path) -> Dict[str, Dict[str, Any]]:
    return {str(row["task_id"]): row for row in read_jsonl(dataset_dir / "latent_tasks.jsonl")}


def family_targets(tasks_per_condition: int) -> Dict[str, int]:
    if tasks_per_condition == 5:
        return {"packet_judgment": 2, "evidence_selection": 2, "active_verification": 1}
    if tasks_per_condition == 8:
        return {"packet_judgment": 3, "evidence_selection": 3, "active_verification": 2}
    base = tasks_per_condition // 3
    remainder = tasks_per_condition % 3
    families = ["packet_judgment", "evidence_selection", "active_verification"]
    return {family: base + (1 if index < remainder else 0) for index, family in enumerate(families)}


def view_task_id(base_task_id: str, view: str) -> str:
    suffix = "hidden" if "hidden" in view else "visible"
    return f"{base_task_id}_{suffix}"


def stable_variant_seed(seed: int, task_id: str, variant: str) -> int:
    digest = sha256(f"{seed}:{task_id}:{variant}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def reordered_documents(documents: Sequence[Mapping[str, Any]], *, seed: int, task_id: str, variant: str) -> list[Dict[str, Any]]:
    output = [dict(doc) for doc in documents]
    if len(output) <= 1:
        return output
    original_ids = [str(doc["doc_id"]) for doc in output]
    Random(stable_variant_seed(seed, task_id, variant)).shuffle(output)
    if [str(doc["doc_id"]) for doc in output] == original_ids:
        output = output[1:] + output[:1]
    return output


def build_robustness_prompt_payload(
    dataset_dir: Path,
    view_task_id_value: str,
    variant: str,
    *,
    prompt_condition: str,
    seed: int,
    schema_variant: str = DEFAULT_SCHEMA,
) -> Dict[str, Any]:
    if variant not in ROBUSTNESS_VARIANTS:
        raise ValueError(f"unknown robustness variant: {variant}")
    task = task_by_view_id(dataset_dir)[view_task_id_value]
    doc_view = opaque_doc_id_view(task)
    documents = evidence_payload(task, doc_id_view=doc_view, scrub_audit_labels=True)
    documents = [dict(doc) for doc in documents]
    policy = standard_policy(prompt_condition)

    if variant == "order_randomized":
        documents = reordered_documents(documents, seed=seed, task_id=view_task_id_value, variant=variant)
    elif variant == "source_type_masked":
        for doc in documents:
            doc["source_type"] = "document"
    elif variant == "prompt_paraphrase":
        policy = paraphrased_policy(prompt_condition)
    elif variant == "citation_masked":
        for doc in documents:
            doc["visible_citations"] = []

    return {
        "task": "eha_uncued_robustness_v1",
        "question": task.question,
        "policy": policy,
        "documents": documents,
        "schema": robustness_schema(schema_variant),
    }


def build_robustness_messages(
    dataset_dir: Path,
    view_task_id_value: str,
    variant: str,
    *,
    prompt_condition: str,
    seed: int,
    schema_variant: str = DEFAULT_SCHEMA,
) -> tuple[list[Dict[str, str]], Dict[str, Any], Dict[str, str]]:
    task = task_by_view_id(dataset_dir)[view_task_id_value]
    doc_view = opaque_doc_id_view(task)
    payload = build_robustness_prompt_payload(
        dataset_dir,
        view_task_id_value,
        variant,
        prompt_condition=prompt_condition,
        seed=seed,
        schema_variant=schema_variant,
    )
    messages = [
        {"role": "developer", "content": "You evaluate evidence quality in polluted information environments."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    return messages, payload, doc_view.visible_to_audit


def portable_messages(messages: Sequence[Mapping[str, str]]) -> list[Dict[str, str]]:
    developer_text = "\n".join(str(message.get("content", "")) for message in messages if message.get("role") in {"developer", "system"})
    users = [
        {"role": str(message.get("role", "user")), "content": str(message.get("content", ""))}
        for message in messages
        if message.get("role") not in {"developer", "system"}
    ]
    if not users:
        return [{"role": "user", "content": developer_text}]
    users[0]["content"] = f"Instructions:\n{developer_text}\n\nUser task:\n{users[0]['content']}"
    return users


def prompt_audit_for_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    audit = visible_payload_audit(payload.get("documents", []))
    text = json.dumps(payload, ensure_ascii=False)
    label_hits = [marker for marker in FORBIDDEN_PROMPT_MARKERS if marker in text]
    passed = (
        not label_hits
        and not audit["hidden_field_hits"]
        and audit["semantic_doc_id_hits"] == 0
        and audit["semantic_visible_citation_hits"] == 0
        and audit["audit_id_hits_in_title_or_body"] == 0
    )
    return {**audit, "condition_or_family_label_hits": label_hits, "passed": passed}


def prompt_audit_summary_for_rows(rows: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    totals = Counter()
    label_hits = Counter()
    hidden_hits = Counter()
    for row in rows:
        totals["records"] += 1
        for key in ("semantic_doc_id_hits", "semantic_visible_citation_hits", "audit_id_hits_in_title_or_body"):
            totals[key] += int(row.get(key, 0) or 0)
        for value in row.get("hidden_field_hits", []) if isinstance(row.get("hidden_field_hits"), list) else []:
            hidden_hits[str(value)] += 1
        for value in row.get("condition_or_family_label_hits", []) if isinstance(row.get("condition_or_family_label_hits"), list) else []:
            label_hits[str(value)] += 1
    passed = all(
        totals[key] == 0
        for key in ("semantic_doc_id_hits", "semantic_visible_citation_hits", "audit_id_hits_in_title_or_body")
    ) and not hidden_hits and not label_hits
    return {
        "records": totals["records"],
        "semantic_doc_id_hits": totals["semantic_doc_id_hits"],
        "semantic_visible_citation_hits": totals["semantic_visible_citation_hits"],
        "audit_id_hits_in_title_or_body": totals["audit_id_hits_in_title_or_body"],
        "hidden_field_hits": dict(sorted(hidden_hits.items())),
        "condition_or_family_label_hits": dict(sorted(label_hits.items())),
        "passed": passed,
    }


def without_key(document: Mapping[str, Any], key: str) -> Dict[str, Any]:
    return {name: value for name, value in document.items() if name != key}


def sorted_docs(documents: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    return sorted([dict(doc) for doc in documents], key=lambda doc: str(doc.get("doc_id", "")))


def write_prompt_parity_audit(
    dataset_dir: Path,
    out_dir: Path,
    view_task_ids: Sequence[str],
    variants: Sequence[str],
    *,
    prompt_condition: str = DEFAULT_PROMPT,
    seed: int = 20260525,
) -> Dict[str, Any]:
    failures: list[Dict[str, str]] = []
    audit_rows: list[Dict[str, Any]] = []
    for task_id in view_task_ids:
        payloads = {
            variant: build_robustness_prompt_payload(
                dataset_dir,
                task_id,
                variant,
                prompt_condition=prompt_condition,
                seed=seed,
            )
            for variant in variants
        }
        baseline = payloads[BASELINE_VARIANT]
        for variant, payload in payloads.items():
            audit_rows.append({"task_id": task_id, "variant": variant, **prompt_audit_for_payload(payload)})
        if "order_randomized" in payloads:
            ordered = payloads["order_randomized"]
            if sorted_docs(ordered["documents"]) != sorted_docs(baseline["documents"]):
                failures.append({"task_id": task_id, "variant": "order_randomized", "reason": "document_set_changed"})
            if len(baseline["documents"]) > 1 and [doc["doc_id"] for doc in ordered["documents"]] == [doc["doc_id"] for doc in baseline["documents"]]:
                failures.append({"task_id": task_id, "variant": "order_randomized", "reason": "document_order_unchanged"})
        if "source_type_masked" in payloads:
            masked = payloads["source_type_masked"]
            if [without_key(doc, "source_type") for doc in masked["documents"]] != [without_key(doc, "source_type") for doc in baseline["documents"]]:
                failures.append({"task_id": task_id, "variant": "source_type_masked", "reason": "non_source_type_field_changed"})
            if {str(doc.get("source_type")) for doc in masked["documents"]} != {"document"}:
                failures.append({"task_id": task_id, "variant": "source_type_masked", "reason": "source_type_not_fully_masked"})
        if "prompt_paraphrase" in payloads:
            paraphrase = payloads["prompt_paraphrase"]
            for key in ("question", "documents", "schema"):
                if paraphrase[key] != baseline[key]:
                    failures.append({"task_id": task_id, "variant": "prompt_paraphrase", "reason": f"{key}_changed"})
            if paraphrase["policy"] == baseline["policy"]:
                failures.append({"task_id": task_id, "variant": "prompt_paraphrase", "reason": "policy_unchanged"})
        if "citation_masked" in payloads:
            citation_masked = payloads["citation_masked"]
            if [without_key(doc, "visible_citations") for doc in citation_masked["documents"]] != [without_key(doc, "visible_citations") for doc in baseline["documents"]]:
                failures.append({"task_id": task_id, "variant": "citation_masked", "reason": "non_citation_field_changed"})
            if any(doc.get("visible_citations") for doc in citation_masked["documents"]):
                failures.append({"task_id": task_id, "variant": "citation_masked", "reason": "citations_not_masked"})
    prompt_summary = prompt_audit_summary_for_rows(audit_rows)
    summary = {
        "task_count": len(view_task_ids),
        "variants": list(variants),
        "prompt_count": len(audit_rows),
        "parity_failure_count": len(failures),
        "prompt_audit_failure_count": sum(1 for row in audit_rows if not row["passed"]),
        "prompt_audit_summary": prompt_summary,
        "failures": failures[:50],
        "passed": not failures and prompt_summary["passed"],
    }
    write_json(out_dir / "prompt_parity_audit.json", summary)
    write_json(out_dir / "prompt_audit_summary.json", prompt_summary)
    return summary


def perturbation_manifest_payload() -> Dict[str, Any]:
    return {
        "date": REPORT_DATE,
        "phase": "1.3_uncued_robustness_perturbations",
        "variants": [
            {
                "variant": "baseline_original",
                "changed_factor": "none",
                "rule": "Rebuild the normal role-uncued prompt from the frozen source task.",
            },
            {
                "variant": "order_randomized",
                "changed_factor": "document_order",
                "rule": "Shuffle model-visible document order using seed and task ID; preserve document fields.",
            },
            {
                "variant": "source_type_masked",
                "changed_factor": "source_type_metadata",
                "rule": "Replace every model-visible source_type with document; preserve all other document fields.",
            },
            {
                "variant": "prompt_paraphrase",
                "changed_factor": "policy_wording",
                "rule": "Use semantically equivalent base policy wording while keeping documents and schema fixed.",
            },
            {
                "variant": "citation_masked",
                "changed_factor": "visible_citations",
                "rule": "Remove model-visible citation lists; preserve document body text and all non-citation fields.",
            },
        ],
        "baseline_required": True,
        "schema_variant": DEFAULT_SCHEMA,
        "prompt_condition": DEFAULT_PROMPT,
    }


def write_perturbation_manifest(out_dir: Path) -> Dict[str, Any]:
    payload = perturbation_manifest_payload()
    write_json(out_dir / "perturbation_manifest.json", payload)
    return payload


def write_prompt_artifacts(
    dataset_dir: Path,
    out_dir: Path,
    view_task_ids: Sequence[str],
    variants: Sequence[str],
    *,
    prompt_condition: str,
    seed: int,
) -> None:
    for task_id in view_task_ids:
        for variant in variants:
            messages, payload, visible_to_audit = build_robustness_messages(
                dataset_dir,
                task_id,
                variant,
                prompt_condition=prompt_condition,
                seed=seed,
            )
            artifact_path = out_dir / "prompt_artifacts" / variant / f"{task_id}.prompt.json"
            write_json(
                artifact_path,
                {
                    "task_id": task_id,
                    "variant": variant,
                    "prompt_condition": prompt_condition,
                    "messages": portable_messages(messages),
                    "schema_name": "eha_uncued_robustness_current_phase1_interface",
                    "model_visible_doc_id_policy": "opaque_per_task",
                    "scorer_visible_to_audit_doc_id_map": visible_to_audit,
                    "visible_prompt_audit": prompt_audit_for_payload(payload),
                },
            )


def plan_robustness(
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
                condition_selected.append(
                    {
                        "task_id": str(row["task_id"]),
                        "view_task_id": view_task_id(str(row["task_id"]), view),
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
        "dependency_edges": dataset_dir / "dependency_edges.jsonl",
    }
    manifest = {
        "date": REPORT_DATE,
        "phase": "1.3_uncued_robustness_selection",
        "dataset_dir": str(dataset_dir),
        "source_dataset": str(dataset_dir),
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
    write_perturbation_manifest(out_dir)
    selected_view_ids = [str(row["view_task_id"]) for row in selected]
    write_prompt_artifacts(
        dataset_dir,
        out_dir,
        selected_view_ids,
        ROBUSTNESS_VARIANTS,
        prompt_condition=DEFAULT_PROMPT,
        seed=seed,
    )
    write_prompt_parity_audit(
        dataset_dir,
        out_dir,
        selected_view_ids,
        ROBUSTNESS_VARIANTS,
        prompt_condition=DEFAULT_PROMPT,
        seed=seed,
    )
    write_json(out_dir / "stored_hidden_label_audit.json", stored_hidden_label_audit(out_dir))
    return manifest


def robustness_profiles(
    models: str,
    *,
    max_output_tokens: int,
    timeout_s: float,
    cost_estimate_output_tokens: int,
) -> list[FrontierModelProfile]:
    profiles: list[FrontierModelProfile] = []
    for model in split_csv(models):
        provider = provider_for_model(model)
        response_format = "json_object" if provider == "DeepSeek" else "json_schema"
        profiles.append(
            FrontierModelProfile(
                provider=provider,
                model=model,
                budget_setting="robustness",
                temperature=None,
                max_output_tokens=max_output_tokens,
                response_format=response_format,
                timeout_s=timeout_s,
                cost_estimate_output_tokens=cost_estimate_output_tokens,
            )
        )
    return profiles


def invocation_profiles_payload(
    profiles: Sequence[FrontierModelProfile],
    *,
    variants: Sequence[str],
    prompt: str,
    view: str,
    max_attempts: int,
    parallel_models: int,
) -> Dict[str, Any]:
    profile_rows: list[Dict[str, Any]] = []
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
    return {
        "phase": "1.3_uncued_robustness_run",
        "schema_variant": DEFAULT_SCHEMA,
        "variants": list(variants),
        "prompt_condition": prompt,
        "selected_view": view,
        "parallel_strategy": {
            "parallel_model_streams": parallel_models,
            "per_job_concurrency": 1,
        },
        "profiles": profile_rows,
        "deepseek_profiles": [row for row in profile_rows if row["provider"] == "DeepSeek"],
    }


def safe_name(value: str) -> str:
    return value.replace("/", "_").replace(":", "_")


def prediction_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (str(row.get("variant")), str(row.get("model")), str(row.get("task_id")), str(row.get("prompt_condition")))


def completed_keys(predictions_path: Path, *, successful_only: bool = False) -> set[tuple[str, str, str, str]]:
    keys: set[tuple[str, str, str, str]] = set()
    for row in read_jsonl(predictions_path):
        if successful_only and not bool(row.get("parse_success")):
            continue
        keys.add(prediction_key(row))
    return keys


def latest_records_by_key(records: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    latest: dict[tuple[str, str, str, str], Dict[str, Any]] = {}
    for row in records:
        latest[prediction_key(row)] = dict(row)
    return list(latest.values())


def estimate_plan_cost(
    dataset_dir: Path,
    task_ids: Sequence[str],
    models: str,
    variants: Sequence[str],
    *,
    prompt_condition: str,
    seed: int,
    max_output_tokens: int,
    cost_estimate_output_tokens: int,
    timeout_s: float,
) -> Dict[str, Any]:
    profiles = robustness_profiles(
        models,
        max_output_tokens=max_output_tokens,
        timeout_s=timeout_s,
        cost_estimate_output_tokens=cost_estimate_output_tokens,
    )
    rows = []
    total = 0.0
    for task_id in task_ids:
        for variant in variants:
            messages, _, _ = build_robustness_messages(
                dataset_dir,
                task_id,
                variant,
                prompt_condition=prompt_condition,
                seed=seed,
            )
            prompt_text = json.dumps(portable_messages(messages), ensure_ascii=False)
            prompt_tokens = estimate_tokens(prompt_text)
            for profile in profiles:
                estimated = cost_for_usage(profile.model, prompt_tokens, cost_estimate_output_tokens)
                total += estimated
                rows.append(
                    {
                        "task_id": task_id,
                        "variant": variant,
                        "model": profile.model,
                        "prompt_tokens_estimate": prompt_tokens,
                        "output_tokens_estimate": cost_estimate_output_tokens,
                        "estimated_cost_usd": estimated,
                    }
                )
    return {
        "planned_calls": len(rows),
        "projected_cost_usd": round(total, 6),
        "max_output_tokens": max_output_tokens,
        "cost_estimate_output_tokens": cost_estimate_output_tokens,
        "rows": rows,
    }


def run_robustness_job(
    *,
    dataset_dir: Path,
    task: EpistemicTask,
    variant: str,
    profile: FrontierModelProfile,
    prompt_condition: str,
    seed: int,
    out_dir: Path,
    max_attempts: int,
    cost_guard: CostGuard,
    cost_lock: threading.Lock,
) -> Dict[str, Any]:
    base_messages, prompt_payload, visible_to_audit = build_robustness_messages(
        dataset_dir,
        task.task_id,
        variant,
        prompt_condition=prompt_condition,
        seed=seed,
    )
    messages = portable_messages(base_messages)
    prompt_audit = prompt_audit_for_payload(prompt_payload)
    artifact_dir = out_dir / "artifacts" / safe_name(profile.model) / prompt_condition / variant
    prompt_path = artifact_dir / f"{task.task_id}.prompt.json"
    response_path = artifact_dir / f"{task.task_id}.response.json"
    write_json(
        prompt_path,
        {
            "model": profile.model,
            "provider": profile.provider,
            "task_id": task.task_id,
            "variant": variant,
            "prompt_condition": prompt_condition,
            "messages": messages,
            "schema_name": "eha_uncued_robustness_current_phase1_interface",
            "model_visible_doc_id_policy": "opaque_per_task",
            "scorer_visible_to_audit_doc_id_map": visible_to_audit,
            "visible_prompt_audit": prompt_audit,
        },
    )
    prompt_text = json.dumps(messages, ensure_ascii=False)
    final_prediction: EpistemicPrediction | None = None
    final_response = ""
    final_usage: Dict[str, Any] = {}
    final_used_format = profile.response_format
    final_error = ""
    final_empty = False
    final_schema_missing = False
    final_success = False
    final_extractor = "not_attempted"
    final_cost = 0.0
    final_visible_tokens = 0
    final_field_lengths: Dict[str, Any] = {}
    final_overlength = False
    attempts: list[Dict[str, Any]] = []
    attempts_used = 0

    for attempt in range(1, max_attempts + 1):
        attempts_used = attempt
        started = time.time()
        with cost_lock:
            cost_guard.before_call(profile.model, prompt_text, profile.cost_estimate_output_tokens or 1000)
        response = ""
        usage: Dict[str, Any] = {}
        used_format = profile.response_format
        parse_error = ""
        parse_success = False
        schema_missing = False
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
                schema_name="eha_uncued_robustness_current_phase1_interface",
                schema=robustness_schema(DEFAULT_SCHEMA),
            )
            with cost_lock:
                cost_usd = cost_guard.after_call(profile.model, usage)
            parsed = parse_prediction_with_diagnostics(response)
            parse_success = parsed.parse_success
            parse_error = parsed.parse_error
            schema_missing = parsed.schema_missing
            extractor = parsed.json_extractor_used
            if parsed.prediction is not None:
                translated = translate_prediction_to_audit_ids(parsed.prediction, visible_to_audit)
                final_prediction = normalize_prediction(translated, task)
                final_visible_tokens, final_field_lengths, final_overlength = output_budget_diagnostics(final_prediction, response)
        except BudgetExceeded:
            raise
        except Exception as exc:  # noqa: BLE001
            parse_error = str(exc)
        empty_output = not response.strip()
        elapsed_s = round(time.time() - started, 3)
        attempts.append(
            {
                "attempt": attempt,
                "model": profile.model,
                "provider": profile.provider,
                "task_id": task.task_id,
                "variant": variant,
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

    write_json(response_path, {"attempts": attempts, "final_attempt": attempts[-1] if attempts else {}})
    prediction = final_prediction if final_success and final_prediction is not None else fallback_prediction(final_error)
    return {
        "task_id": task.task_id,
        "base_task_id": base_uncued_task_id(task),
        "view": uncued_view(task),
        "family": task.family,
        "condition": task.condition,
        "model": profile.model,
        "provider": profile.provider,
        "budget_setting": profile.budget_setting,
        "variant": variant,
        "prompt_condition": prompt_condition,
        "backend": "api",
        "prediction": model_to_dict(prediction),
        "parse_success": final_success,
        "parse_error": final_error,
        "empty_output": final_empty,
        "schema_missing": final_schema_missing,
        "attempt_count": attempts_used,
        "response_format_used": final_used_format,
        "json_extractor_used": final_extractor,
        "visible_output_tokens": final_visible_tokens if final_visible_tokens else estimate_tokens(final_response),
        "json_field_lengths": final_field_lengths,
        "overlength": final_overlength,
        "usage": final_usage,
        "cost_usd": final_cost,
        "prompt_path": str(prompt_path.relative_to(out_dir)),
        "response_path": str(response_path.relative_to(out_dir)),
        "invocation_profile": {
            **profile.invocation(),
            "attempts": attempts_used,
            "max_attempts": max_attempts,
            "doc_id_policy": "opaque_per_task",
            "visible_prompt_audit": prompt_audit,
        },
    }


def run_robustness(
    dataset_dir: Path,
    out_dir: Path,
    *,
    models: str,
    variants: Sequence[str],
    schema: str,
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
    retry_failed: bool,
) -> Dict[str, Any]:
    if schema != DEFAULT_SCHEMA:
        raise typer.BadParameter(f"schema must be {DEFAULT_SCHEMA}")
    if prompt != DEFAULT_PROMPT:
        raise typer.BadParameter(f"prompt must be {DEFAULT_PROMPT}")
    invalid = [variant for variant in variants if variant not in ROBUSTNESS_VARIANTS]
    if invalid:
        raise typer.BadParameter(f"unknown robustness variant(s): {', '.join(invalid)}")
    if BASELINE_VARIANT not in variants:
        raise typer.BadParameter("baseline_original is required")
    selection_path = out_dir / "selection_manifest.json"
    if not selection_path.exists():
        raise FileNotFoundError(f"missing selection manifest: {selection_path}")
    selection = read_json(selection_path)
    seed = int(selection.get("seed", 20260525))
    task_ids = [str(row["view_task_id"]) for row in selection["selected_tasks"]]
    tasks_by_id = task_by_view_id(dataset_dir)
    tasks = [tasks_by_id[task_id] for task_id in task_ids]
    profiles = robustness_profiles(
        models,
        max_output_tokens=max_output_tokens,
        timeout_s=timeout_s,
        cost_estimate_output_tokens=cost_estimate_output_tokens,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_prompt_artifacts(dataset_dir, out_dir, task_ids, variants, prompt_condition=prompt, seed=seed)
    parity = write_prompt_parity_audit(dataset_dir, out_dir, task_ids, variants, prompt_condition=prompt, seed=seed)
    cost_projection = estimate_plan_cost(
        dataset_dir,
        task_ids,
        models,
        variants,
        prompt_condition=prompt,
        seed=seed,
        max_output_tokens=max_output_tokens,
        cost_estimate_output_tokens=cost_estimate_output_tokens,
        timeout_s=timeout_s,
    )
    manifest = {
        "date": REPORT_DATE,
        "phase": "1.3_uncued_robustness_run",
        "dataset_dir": str(dataset_dir),
        "selection_manifest": str(selection_path),
        "selected_tasks": selection["selected_tasks"],
        "models": [profile.model for profile in profiles],
        "variants": list(variants),
        "schema_variant": schema,
        "selected_view": view,
        "prompt_condition": prompt,
        "planned_calls": len(tasks) * len(profiles) * len(variants),
        "max_attempts": max_attempts,
        "max_output_tokens": max_output_tokens,
        "cost_estimate_output_tokens": cost_estimate_output_tokens,
        "provider_response_formats": {profile.model: profile.response_format for profile in profiles},
        "budget": {"soft_cap_usd": soft_cap_usd, "hard_cap_usd": hard_cap_usd, "abort_cap_usd": abort_cap_usd},
        "dry_run": dry_run,
        "retry_failed": retry_failed,
        "projected_cost_usd": cost_projection["projected_cost_usd"],
        "prompt_parity_passed": parity["passed"],
    }
    write_json(out_dir / "run_manifest.json", manifest)
    write_json(out_dir / "dry_run_cost_projection.json", cost_projection)
    write_json(
        out_dir / "invocation_profiles.json",
        invocation_profiles_payload(
            profiles,
            variants=variants,
            prompt=prompt,
            view=view,
            max_attempts=max_attempts,
            parallel_models=parallel_models,
        ),
    )
    write_json(out_dir / "stored_hidden_label_audit.json", stored_hidden_label_audit(out_dir))
    if cost_projection["projected_cost_usd"] > hard_cap_usd:
        write_json(
            out_dir / "cost_report.json",
            {
                "aborted": True,
                "reason": "projected cost exceeds hard cap",
                **manifest["budget"],
                "projected_cost_usd": cost_projection["projected_cost_usd"],
            },
        )
        raise BudgetExceeded(f"Projected cost ${cost_projection['projected_cost_usd']:.2f} exceeds hard cap ${hard_cap_usd:.2f}.")
    if dry_run:
        write_json(
            out_dir / "cost_report.json",
            {"aborted": False, "dry_run": True, **manifest["budget"], "projected_cost_usd": cost_projection["projected_cost_usd"]},
        )
        return manifest

    predictions_path = out_dir / "predictions.jsonl"
    done = completed_keys(predictions_path, successful_only=retry_failed) if resume else set()
    jobs = [
        (task, variant, profile)
        for task in tasks
        for variant in variants
        for profile in profiles
        if (variant, profile.model, task.task_id, prompt) not in done
    ]
    manifest["resume_completed_count"] = len(done)
    manifest["retry_job_count"] = len(jobs)
    write_json(out_dir / "run_manifest.json", manifest)
    write_lock = threading.Lock()
    cost_lock = threading.Lock()
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)

    def execute(job: tuple[EpistemicTask, str, FrontierModelProfile]) -> Dict[str, Any]:
        task, variant, profile = job
        return run_robustness_job(
            dataset_dir=dataset_dir,
            task=task,
            variant=variant,
            profile=profile,
            prompt_condition=prompt,
            seed=seed,
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
        write_json(
            out_dir / "cost_report.json",
            {"aborted": True, "reason": str(exc), **cost_guard.report(), "projected_cost_usd": cost_projection["projected_cost_usd"]},
        )
        raise

    records = read_jsonl(predictions_path)
    latest_records = latest_records_by_key(records)
    manifest["actual_records"] = len(records)
    manifest["actual_unique_records"] = len(latest_records)
    manifest["latest_parse_success_records"] = sum(1 for row in latest_records if bool(row.get("parse_success")))
    manifest["latest_parse_failure_records"] = sum(1 for row in latest_records if not bool(row.get("parse_success")))
    write_json(out_dir / "run_manifest.json", manifest)
    write_json(out_dir / "prompt_audit_summary.json", prompt_audit_summary_from_records(records, out_dir))
    write_json(out_dir / "stored_hidden_label_audit.json", stored_hidden_label_audit(out_dir))
    guard_report = cost_guard.report()
    record_cost_usd = round(sum(float(row.get("cost_usd", 0.0) or 0.0) for row in records), 6)
    write_json(
        out_dir / "cost_report.json",
        {
            "aborted": False,
            "record_cost_usd": record_cost_usd,
            "projected_cost_usd": cost_projection["projected_cost_usd"],
            **guard_report,
            "retry_spent_usd": guard_report["spent_usd"],
            "spent_usd": record_cost_usd,
        },
    )
    return manifest


def prompt_audit_summary_from_records(records: Sequence[Mapping[str, Any]], out_dir: Path) -> Dict[str, Any]:
    audit_rows: list[Dict[str, Any]] = []
    for record in records:
        audit = record.get("invocation_profile", {}).get("visible_prompt_audit", {})
        if isinstance(audit, Mapping):
            audit_rows.append(dict(audit))
    if not audit_rows and (out_dir / "prompt_parity_audit.json").exists():
        parity = read_json(out_dir / "prompt_parity_audit.json")
        return dict(parity.get("prompt_audit_summary", {"records": 0, "passed": False}))
    return prompt_audit_summary_for_rows(audit_rows)


def stored_hidden_label_audit(out_dir: Path) -> Dict[str, Any]:
    prompt_hits: list[Dict[str, str]] = []
    output_hits: list[Dict[str, str]] = []
    prompt_paths = list((out_dir / "prompt_artifacts").glob("**/*.prompt.json")) + list((out_dir / "artifacts").glob("**/*.prompt.json"))
    for path in sorted(prompt_paths):
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


def record_for_scoring(record: Mapping[str, Any]) -> EpistemicRunRecord:
    allowed_fields = set(EpistemicRunRecord.model_fields.keys())
    payload = {key: value for key, value in record.items() if key in allowed_fields}
    return EpistemicRunRecord.model_validate(payload)


def score_robustness_rows(records: Sequence[Mapping[str, Any]], dataset_dir: Path) -> list[Dict[str, Any]]:
    tasks = task_by_view_id(dataset_dir)
    action_gold = read_action_gold(dataset_dir)
    rows: list[Dict[str, Any]] = []
    for record in records:
        task = tasks[str(record["task_id"])]
        run_record = record_for_scoring(record)
        scored = score_record(run_record, task)
        prediction = run_record.prediction
        item = dict(scored)
        item["base_task_id"] = record.get("base_task_id", base_uncued_task_id(task))
        item["view"] = record.get("view", uncued_view(task))
        item["variant"] = record.get("variant", "")
        item["polluted_support_rate"] = 1.0 - float(item["evidence_cleanliness"])
        item["verification_action_score"] = item["required_action_recall"] if item["required_action_recall"] != "" else ""
        item["exact_target_rate"] = action_exact_target_rate(item, action_gold=action_gold)
        item["support_doc_ids"] = item.get("supporting_evidence", "")
        item["rejected_doc_ids"] = ",".join(prediction.rejected_evidence)
        item["prompt_path"] = record.get("prompt_path", "")
        item["response_path"] = record.get("response_path", "")
        rows.append(item)
    return rows


ROBUSTNESS_METRICS = [
    "parse_success",
    "belief_correctness",
    "operational_epistemic_escape",
    "conditional_epistemic_escape",
    "evidence_precision",
    "polluted_support_rate",
    "rejected_pollutant_rate",
    "clean_support_recall",
    "verification_action_score",
    "exact_target_rate",
    "required_action_recall",
    "cost_usd",
]


def numeric_value(value: Any) -> float | None:
    if value in {"", "not_applicable", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def average_metric(group: Sequence[Mapping[str, Any]], metric: str) -> float | str:
    values = [numeric for row in group if (numeric := numeric_value(row.get(metric))) is not None]
    if not values:
        return ""
    return sum(values) / len(values)


def aggregate_robustness_rows(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> list[Dict[str, Any]]:
    grouped: Dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(key, "")) for key in group_keys)].append(row)
    output: list[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item = {group_key: key[index] for index, group_key in enumerate(group_keys)}
        item["n"] = len(group)
        for metric in ROBUSTNESS_METRICS:
            item[metric] = average_metric(group, metric)
        output.append(item)
    return output


def support_set(value: Any) -> set[str]:
    return {part for part in str(value or "").split(",") if part}


def metric_delta(perturbation: Mapping[str, Any], baseline: Mapping[str, Any], metric: str) -> float | str:
    current = numeric_value(perturbation.get(metric))
    anchor = numeric_value(baseline.get(metric))
    if current is None or anchor is None:
        return ""
    return current - anchor


def compute_paired_delta_rows(rows: Sequence[Mapping[str, Any]], *, variants: Sequence[str]) -> list[Dict[str, Any]]:
    grouped: Dict[tuple[str, str], Dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[(str(row.get("task_id", "")), str(row.get("model", "")))][str(row.get("variant", ""))] = row
    output: list[Dict[str, Any]] = []
    for (task_id, model), by_variant in sorted(grouped.items()):
        baseline = by_variant.get(BASELINE_VARIANT)
        if baseline is None:
            continue
        for variant in variants:
            if variant == BASELINE_VARIANT or variant not in by_variant:
                continue
            row = by_variant[variant]
            base_operational = numeric_value(baseline.get("operational_epistemic_escape"))
            variant_operational = numeric_value(row.get("operational_epistemic_escape"))
            base_belief = numeric_value(baseline.get("belief_correctness"))
            variant_belief = numeric_value(row.get("belief_correctness"))
            base_action = numeric_value(baseline.get("verification_action_score"))
            variant_action = numeric_value(row.get("verification_action_score"))
            output.append(
                {
                    "task_id": task_id,
                    "base_task_id": row.get("base_task_id", baseline.get("base_task_id", "")),
                    "condition": row.get("condition", baseline.get("condition", "")),
                    "family": row.get("family", baseline.get("family", "")),
                    "model": model,
                    "variant": variant,
                    "baseline_variant": BASELINE_VARIANT,
                    "delta_operational_escape": metric_delta(row, baseline, "operational_epistemic_escape"),
                    "delta_belief_correctness": metric_delta(row, baseline, "belief_correctness"),
                    "delta_evidence_precision": metric_delta(row, baseline, "evidence_precision"),
                    "delta_polluted_support_rate": metric_delta(row, baseline, "polluted_support_rate"),
                    "delta_action_score": metric_delta(row, baseline, "verification_action_score"),
                    "pass_to_fail_operational": 1 if base_operational == 1.0 and variant_operational == 0.0 else 0,
                    "fail_to_pass_operational": 1 if base_operational == 0.0 and variant_operational == 1.0 else 0,
                    "pass_to_fail_belief": 1 if base_belief == 1.0 and variant_belief == 0.0 else 0,
                    "fail_to_pass_belief": 1 if base_belief == 0.0 and variant_belief == 1.0 else 0,
                    "support_set_changed": 1 if support_set(row.get("support_doc_ids")) != support_set(baseline.get("support_doc_ids")) else 0,
                    "verdict_changed": 1 if str(row.get("predicted_verdict", "")) != str(baseline.get("predicted_verdict", "")) else 0,
                    "action_score_changed": 1 if base_action is not None and variant_action is not None and base_action != variant_action else 0,
                    "baseline_operational_epistemic_escape": baseline.get("operational_epistemic_escape", ""),
                    "variant_operational_epistemic_escape": row.get("operational_epistemic_escape", ""),
                    "baseline_belief_correctness": baseline.get("belief_correctness", ""),
                    "variant_belief_correctness": row.get("belief_correctness", ""),
                    "baseline_evidence_precision": baseline.get("evidence_precision", ""),
                    "variant_evidence_precision": row.get("evidence_precision", ""),
                    "baseline_polluted_support_rate": baseline.get("polluted_support_rate", ""),
                    "variant_polluted_support_rate": row.get("polluted_support_rate", ""),
                    "baseline_action_score": baseline.get("verification_action_score", ""),
                    "variant_action_score": row.get("verification_action_score", ""),
                    "baseline_support_doc_ids": baseline.get("support_doc_ids", ""),
                    "variant_support_doc_ids": row.get("support_doc_ids", ""),
                    "baseline_selected_doc_ids": baseline.get("selected_doc_ids", ""),
                    "variant_selected_doc_ids": row.get("selected_doc_ids", ""),
                    "baseline_verdict": baseline.get("predicted_verdict", ""),
                    "variant_verdict": row.get("predicted_verdict", ""),
                }
            )
    return output


PAIRED_DELTA_METRICS = [
    "delta_operational_escape",
    "delta_belief_correctness",
    "delta_evidence_precision",
    "delta_polluted_support_rate",
    "delta_action_score",
    "pass_to_fail_operational",
    "fail_to_pass_operational",
    "support_set_changed",
    "verdict_changed",
    "action_score_changed",
]


def aggregate_paired_deltas(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> list[Dict[str, Any]]:
    grouped: Dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(key, "")) for key in group_keys)].append(row)
    output: list[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item = {group_key: key[index] for index, group_key in enumerate(group_keys)}
        item["n"] = len(group)
        for metric in PAIRED_DELTA_METRICS:
            item[metric] = average_metric(group, metric)
        output.append(item)
    return output


def paired_flip_rows(delta_rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    output: list[Dict[str, Any]] = []
    for row in delta_rows:
        action_delta = numeric_value(row.get("delta_action_score"))
        if (
            int(row.get("pass_to_fail_operational", 0) or 0)
            or int(row.get("fail_to_pass_operational", 0) or 0)
            or int(row.get("support_set_changed", 0) or 0)
            or int(row.get("verdict_changed", 0) or 0)
            or (action_delta is not None and action_delta != 0.0)
        ):
            output.append(dict(row))
    return output


def review_cause_for_variant(variant: str) -> str:
    return {
        "order_randomized": "Document order sensitivity or positional attention.",
        "source_type_masked": "Dependence on visible source-type metadata.",
        "prompt_paraphrase": "Prompt wording sensitivity.",
        "citation_masked": "Dependence on visible citation/dependency structure.",
    }.get(variant, "No perturbation-specific cause assigned.")


def build_flip_review_rows(flip_rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    for index, row in enumerate(flip_rows, start=1):
        flip_types = []
        if int(row.get("pass_to_fail_operational", 0) or 0) or int(row.get("fail_to_pass_operational", 0) or 0):
            flip_types.append("operational_escape")
        if int(row.get("verdict_changed", 0) or 0):
            flip_types.append("verdict")
        if int(row.get("support_set_changed", 0) or 0):
            flip_types.append("support_set")
        action_delta = numeric_value(row.get("delta_action_score"))
        if action_delta is not None and action_delta != 0.0:
            flip_types.append("action_score")
        baseline_summary = (
            f"operational={row.get('baseline_operational_epistemic_escape', '')}; "
            f"verdict={row.get('baseline_verdict', '')}; support={row.get('baseline_support_doc_ids', '')}"
        )
        perturbation_summary = (
            f"operational={row.get('variant_operational_epistemic_escape', '')}; "
            f"verdict={row.get('variant_verdict', '')}; support={row.get('variant_support_doc_ids', '')}"
        )
        rows.append(
            {
                "review_id": f"robustness_flip_{index:03d}",
                "task_id": row.get("task_id", ""),
                "model": row.get("model", ""),
                "variant": row.get("variant", ""),
                "flip_type": ",".join(flip_types),
                "baseline_summary": baseline_summary,
                "perturbation_summary": perturbation_summary,
                "likely_cause": review_cause_for_variant(str(row.get("variant", ""))),
                "claim_impact": "inspect before making a robustness claim for this variant",
                "review_note": "Automated local review from paired scorer fields; response artifacts remain available for manual adjudication.",
            }
        )
    return rows


def complete_paired_groups(rows: Sequence[Mapping[str, Any]], variants: Sequence[str]) -> Dict[str, Any]:
    expected = set(variants)
    grouped: Dict[tuple[str, str], set[str]] = defaultdict(set)
    for row in rows:
        grouped[(str(row.get("task_id", "")), str(row.get("model", "")))].add(str(row.get("variant", "")))
    complete = {f"{task_id}:{model}": sorted(values) for (task_id, model), values in grouped.items() if values >= expected}
    incomplete = {f"{task_id}:{model}": sorted(values) for (task_id, model), values in grouped.items() if values < expected}
    return {"complete_count": len(complete), "incomplete_count": len(incomplete), "incomplete_groups": incomplete}


def generated_lore_gap_rows(rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    generated_rows = [row for row in rows if row.get("condition") == "generated_lore"]
    grouped: Dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in generated_rows:
        grouped[str(row.get("variant", ""))].append(row)
    output: list[Dict[str, Any]] = []
    for variant, group in sorted(grouped.items()):
        belief = average_metric(group, "belief_correctness")
        operational = average_metric(group, "operational_epistemic_escape")
        gap = ""
        if belief != "" and operational != "":
            gap = float(belief) - float(operational)
        output.append(
            {
                "variant": variant,
                "n": len(group),
                "belief_correctness": belief,
                "operational_epistemic_escape": operational,
                "belief_operation_gap": gap,
            }
        )
    return output


def variant_claim_rows(delta_by_variant: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    rows: list[Dict[str, Any]] = []
    for row in delta_by_variant:
        delta = numeric_value(row.get("delta_operational_escape"))
        if delta is None:
            status = "incomplete"
        elif delta <= -0.25:
            status = "weakens"
        elif delta >= 0.25:
            status = "strengthens"
        else:
            status = "preserves"
        rows.append(
            {
                "variant": row.get("variant", ""),
                "paired_n": row.get("n", 0),
                "mean_delta_operational_escape": row.get("delta_operational_escape", ""),
                "mean_delta_belief_correctness": row.get("delta_belief_correctness", ""),
                "status": status,
            }
        )
    return rows


def run_robustness_report(run_dir: Path, reports_dir: Path, *, dataset_dir: Path = Path("data/uncued-pilot-v1")) -> Dict[str, Any]:
    raw_records = read_jsonl(run_dir / "predictions.jsonl")
    records = latest_records_by_key(raw_records)
    scored_rows = score_robustness_rows(records, dataset_dir) if records else []
    run_manifest = read_json(run_dir / "run_manifest.json")
    variants = [str(item) for item in run_manifest.get("variants", ROBUSTNESS_VARIANTS)]
    by_variant_model = aggregate_robustness_rows(scored_rows, ["variant", "model"])
    by_variant_condition = aggregate_robustness_rows(scored_rows, ["variant", "condition"])
    by_variant_family = aggregate_robustness_rows(scored_rows, ["variant", "family"])
    paired_rows = compute_paired_delta_rows(scored_rows, variants=variants)
    paired_by_variant = aggregate_paired_deltas(paired_rows, ["variant"])
    paired_by_variant_model = aggregate_paired_deltas(paired_rows, ["variant", "model"])
    paired_by_variant_condition = aggregate_paired_deltas(paired_rows, ["variant", "condition"])
    flips = paired_flip_rows(paired_rows)
    review_rows = build_flip_review_rows(flips)
    gap_rows = generated_lore_gap_rows(scored_rows)
    claim_rows = variant_claim_rows(paired_by_variant)

    write_csv(run_dir / "robustness_rows.csv", scored_rows)
    write_csv(run_dir / "robustness_by_variant_model.csv", by_variant_model)
    write_csv(run_dir / "robustness_by_variant_condition.csv", by_variant_condition)
    write_csv(run_dir / "robustness_by_variant_family.csv", by_variant_family)
    write_csv(run_dir / "paired_deltas_by_variant.csv", paired_by_variant)
    write_csv(run_dir / "paired_deltas_by_variant_model.csv", paired_by_variant_model)
    write_csv(run_dir / "paired_deltas_by_variant_condition.csv", paired_by_variant_condition)
    write_csv(run_dir / "paired_flip_rows.csv", flips)
    write_csv(run_dir / "robustness_flip_review.csv", review_rows)
    write_csv(run_dir / "generated_lore_gap_by_variant.csv", gap_rows)

    cost_report = read_json(run_dir / "cost_report.json") if (run_dir / "cost_report.json").exists() else {"aborted": False}
    prompt_audit = read_json(run_dir / "prompt_audit_summary.json") if (run_dir / "prompt_audit_summary.json").exists() else {"passed": False}
    parity = read_json(run_dir / "prompt_parity_audit.json") if (run_dir / "prompt_parity_audit.json").exists() else {"passed": False}
    hidden_audit = read_json(run_dir / "stored_hidden_label_audit.json") if (run_dir / "stored_hidden_label_audit.json").exists() else {"passed": False}
    complete = complete_paired_groups(scored_rows, variants)
    payload = {
        "date": REPORT_DATE,
        "phase": "1.3_uncued_robustness_results",
        "run_dir": str(run_dir),
        "selected_task_count": len({row["base_task_id"] for row in scored_rows}),
        "raw_record_count": len(raw_records),
        "row_count": len(scored_rows),
        "models": run_manifest.get("models", []),
        "variants": variants,
        "view": run_manifest.get("selected_view"),
        "prompt_condition": run_manifest.get("prompt_condition"),
        "cost": cost_report,
        "prompt_audit": prompt_audit,
        "prompt_parity_audit": parity,
        "stored_hidden_label_audit": hidden_audit,
        "complete_paired_groups": complete,
        "paired_delta_rows": len(paired_rows),
        "flip_review": {
            "review_mode": "local_codex_assisted_paired_flip_review",
            "reviewed_rows": len(review_rows),
            "independent_human_review": False,
        },
        "by_variant_model": by_variant_model,
        "by_variant_condition": by_variant_condition,
        "paired_deltas_by_variant": paired_by_variant,
        "generated_lore_gap_by_variant": gap_rows,
        "variant_claims": claim_rows,
        "claim_boundary": "Phase 1.3 robustness mini-suite only; not production robustness, not open-web validity, and not a replacement for Phase 1 main tables.",
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "eha_uncued_robustness_results.json", payload)
    lines = [
        "# EHA-Uncued Phase 1.3 Robustness Mini-Suite Results",
        "",
        f"Date: {REPORT_DATE}",
        "",
        "This paired mini-suite checks whether the role-uncued evidence-hygiene result persists under small presentation perturbations. It is not a full robustness proof and does not claim open-web validity.",
        "",
        "## Scope And Task Selection",
        "",
        f"- Run directory: `{run_dir}`",
        f"- Selected source tasks: {payload['selected_task_count']}",
        f"- Rows: {payload['row_count']} latest records ({payload['raw_record_count']} raw records)",
        f"- Models: {', '.join(payload['models'])}",
        f"- Variants: {', '.join(payload['variants'])}",
        f"- View: `{payload['view']}`",
        f"- Prompt condition: `{payload['prompt_condition']}`",
        "",
        "## Perturbation Definitions",
        "",
        "- `baseline_original`: normal role-uncued prompt rebuilt from the frozen slice.",
        "- `order_randomized`: same documents, shuffled order.",
        "- `source_type_masked`: source_type replaced with `document`.",
        "- `prompt_paraphrase`: policy wording paraphrased, schema and evidence fixed.",
        "- `citation_masked`: visible citations removed while document body text is preserved.",
        "",
        "## Prompt Audit",
        "",
        f"- Prompt parity audit passed: {parity.get('passed')}",
        f"- Prompt hidden-label audit passed: {prompt_audit.get('passed')}",
        f"- Stored hidden-label audit passed: {hidden_audit.get('passed')}",
        "",
        "## Cost And Invocation Profile",
        "",
        f"- Projected cost: USD {cost_report.get('projected_cost_usd', '')}",
        f"- Spent cost: USD {cost_report.get('spent_usd', cost_report.get('record_cost_usd', 0.0))}",
        f"- Hard cap: USD {cost_report.get('hard_cap_usd', '')}",
        "",
        "## Aggregate Metrics By Variant And Model",
        "",
        *markdown_table(by_variant_model, ["variant", "model", "n", "parse_success", "belief_correctness", "operational_epistemic_escape", "evidence_precision", "polluted_support_rate", "required_action_recall"]),
        "",
        "## Paired Deltas",
        "",
        *markdown_table(paired_by_variant, ["variant", "n", "delta_operational_escape", "delta_belief_correctness", "delta_evidence_precision", "delta_polluted_support_rate", "pass_to_fail_operational", "fail_to_pass_operational"]),
        "",
        "## Generated-Lore Belief/Operation Gap",
        "",
        *markdown_table(gap_rows, ["variant", "n", "belief_correctness", "operational_epistemic_escape", "belief_operation_gap"]),
        "",
        "## Flip Review Summary",
        "",
        f"- Paired flip rows: {len(flips)}",
        f"- Reviewed rows: {len(review_rows)}",
        "",
        "## Claim Boundary",
        "",
        "Allowed claim: this paired role-uncued Phase 1.3 mini-suite supports only named perturbation-sensitivity or mini-suite robustness statements. It does not replace Phase 1 main tables and does not establish production or open-web validity.",
        "",
        "## Variant Claim Status",
        "",
        *markdown_table(claim_rows, ["variant", "paired_n", "mean_delta_operational_escape", "mean_delta_belief_correctness", "status"]),
        "",
    ]
    (run_dir / "robustness_report.md").write_text("\n".join(lines), encoding="utf-8")
    (reports_dir / f"eha-uncued-robustness-results-{REPORT_DATE}.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def verify_robustness(run_dir: Path, reports_dir: Path, *, dataset_dir: Path = Path("data/uncued-pilot-v1")) -> Dict[str, Any]:
    selection = read_json(run_dir / "selection_manifest.json") if (run_dir / "selection_manifest.json").exists() else {}
    run_manifest = read_json(run_dir / "run_manifest.json") if (run_dir / "run_manifest.json").exists() else {}
    parity = read_json(run_dir / "prompt_parity_audit.json") if (run_dir / "prompt_parity_audit.json").exists() else {}
    prompt_audit = read_json(run_dir / "prompt_audit_summary.json") if (run_dir / "prompt_audit_summary.json").exists() else {}
    hidden_audit = read_json(run_dir / "stored_hidden_label_audit.json") if (run_dir / "stored_hidden_label_audit.json").exists() else {}
    cost_projection = read_json(run_dir / "dry_run_cost_projection.json") if (run_dir / "dry_run_cost_projection.json").exists() else {}
    cost_report = read_json(run_dir / "cost_report.json") if (run_dir / "cost_report.json").exists() else {}
    rows = load_csv_rows(run_dir / "robustness_rows.csv")
    variants = [str(item) for item in run_manifest.get("variants", ROBUSTNESS_VARIANTS)]
    complete = complete_paired_groups(rows, variants)
    report_path = reports_dir / f"eha-uncued-robustness-results-{REPORT_DATE}.md"
    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    selected_tasks = selection.get("selected_tasks", [])
    selected_conditions = {str(row.get("condition")) for row in selected_tasks}
    hard_cap = float(cost_report.get("hard_cap_usd", run_manifest.get("budget", {}).get("hard_cap_usd", 7.0)) or 7.0)
    projected = float(cost_projection.get("projected_cost_usd", run_manifest.get("projected_cost_usd", 0.0)) or 0.0)
    spent = float(cost_report.get("spent_usd", cost_report.get("record_cost_usd", 0.0)) or 0.0)
    planned_calls = int(run_manifest.get("planned_calls", 0) or 0)
    all_rows_parse_success = all(str(row.get("parse_success")) in {"1", "1.0", "True", "true"} for row in rows) and bool(rows)
    gates = {
        "data_source_role_uncued": "uncued-pilot-v1" in str(selection.get("dataset_dir", selection.get("source_dataset", ""))) and "epistemic-resilience-v1" not in str(selection),
        "frozen_selection_recorded": bool(selected_tasks)
        and all(row.get("task_id") and row.get("view_task_id") and row.get("condition") and row.get("family") for row in selected_tasks)
        and "seed" in selection,
        "selected_conditions_polluted_only": selected_conditions <= set(DEFAULT_CONDITIONS) and bool(selected_conditions),
        "perturbation_isolation_passed": bool(parity.get("passed")),
        "prompt_audit_passed": bool(prompt_audit.get("passed")),
        "stored_hidden_label_audit_passed": bool(hidden_audit.get("passed")),
        "cost_preflight_under_hard_cap": projected <= hard_cap and projected > 0.0,
        "cost_under_hard_cap": not bool(cost_report.get("aborted")) and spent <= hard_cap,
        "baseline_anchor_complete": bool(rows) and complete["complete_count"] > 0 and complete["incomplete_count"] == 0 and BASELINE_VARIANT in set(variants),
        "planned_rows_complete": bool(rows) and len(rows) == planned_calls,
        "all_latest_rows_parse_success": all_rows_parse_success,
        "results_separate_from_phase1_artifact": "artifact_uncued_phase1" not in str(run_dir),
        "report_boundary_present": "mini-suite" in report_text and "open-web validity" in report_text and "does not replace Phase 1 main tables" in report_text,
        "no_old_cued_evidence_claim": "old cued" not in report_text.lower(),
    }
    payload = {
        "date": REPORT_DATE,
        "run_dir": str(run_dir),
        "reports_dir": str(reports_dir),
        "decision": "pass" if all(gates.values()) else "fail",
        "gates": gates,
        "complete_paired_groups": complete,
        "row_count": len(rows),
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    write_json(reports_dir / "eha_uncued_robustness_verification.json", payload)
    return payload


@plan_app.command()
def plan_main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
    out_dir: Path = typer.Option(Path(f"results/{RUN_DIR_NAME}")),
    conditions: str = typer.Option(",".join(DEFAULT_CONDITIONS)),
    tasks_per_condition: int = typer.Option(5),
    view: str = typer.Option(DEFAULT_VIEW),
    seed: int = typer.Option(20260525),
) -> None:
    manifest = plan_robustness(
        dataset_dir,
        out_dir,
        conditions=split_csv(conditions),
        tasks_per_condition=tasks_per_condition,
        view=view,
        seed=seed,
    )
    console.print(f"Wrote robustness selection manifest with {manifest['source_task_count']} tasks to {out_dir}.")


@run_app.command()
def run_main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
    out_dir: Path = typer.Option(Path(f"results/{RUN_DIR_NAME}")),
    models: str = typer.Option(DEFAULT_MODELS),
    variants: str = typer.Option(",".join(ROBUSTNESS_VARIANTS)),
    schema: str = typer.Option(DEFAULT_SCHEMA),
    prompt: str = typer.Option(DEFAULT_PROMPT),
    view: str = typer.Option(DEFAULT_VIEW),
    dry_run: bool = typer.Option(False),
    hard_cap_usd: float = typer.Option(7.0),
    soft_cap_usd: float = typer.Option(5.0),
    abort_cap_usd: float = typer.Option(8.0),
    max_output_tokens: int = typer.Option(4096),
    cost_estimate_output_tokens: int = typer.Option(900),
    timeout_s: float = typer.Option(240.0),
    parallel_models: int = typer.Option(2),
    max_attempts: int = typer.Option(2),
    resume: bool = typer.Option(True),
    retry_failed: bool = typer.Option(False, help="When resuming, rerun failed rows while skipping successful rows."),
) -> None:
    try:
        manifest = run_robustness(
            dataset_dir,
            out_dir,
            models=models,
            variants=split_csv(variants),
            schema=schema,
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
            retry_failed=retry_failed,
        )
    except BudgetExceeded as exc:
        console.print(str(exc))
        raise typer.Exit(code=2) from exc
    console.print(f"Wrote robustness {'dry run' if dry_run else 'run'} manifest with {manifest['planned_calls']} planned calls to {out_dir}.")


@report_app.command()
def report_main(
    run_dir: Path = typer.Option(Path(f"results/{RUN_DIR_NAME}")),
    reports_dir: Path = typer.Option(Path("../reports")),
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
) -> None:
    payload = run_robustness_report(run_dir, reports_dir, dataset_dir=dataset_dir)
    console.print(f"Wrote robustness report with {payload['row_count']} rows.")


@verify_app.command()
def verify_main(
    run_dir: Path = typer.Option(Path(f"results/{RUN_DIR_NAME}")),
    reports_dir: Path = typer.Option(Path("../reports")),
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
) -> None:
    payload = verify_robustness(run_dir, reports_dir, dataset_dir=dataset_dir)
    console.print(f"Robustness verification decision={payload['decision']}.")
    if payload["decision"] != "pass":
        raise typer.Exit(code=1)
