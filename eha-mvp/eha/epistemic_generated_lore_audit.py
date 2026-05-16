from __future__ import annotations

import json
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import typer
from loguru import logger
from pydantic import Field, field_validator
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard, estimate_tokens
from .epistemic_frontier_main import FRONTIER_MODEL_PROFILES, output_budget_diagnostics
from .epistemic_model_preflight import complete_with_process_timeout, safe_model_dir
from .epistemic_resilience import (
    EpistemicAction,
    EpistemicRunRecord,
    EpistemicTask,
    aggregate,
    build_messages,
    normalize_doc_refs,
    opaque_doc_id_view,
    portable_chat_messages,
    read_tasks,
    replace_doc_id_refs,
    score_records,
    translate_doc_refs_to_audit,
    visible_payload_audit,
)
from .report import markdown_table, write_csv
from .schemas import EhaModel, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Audit generated-lore belief vs machine-readable evidence-role failures.")
console = Console()
log = logger.bind(module="eha.epistemic_generated_lore_audit")

DEFAULT_MODELS = ("gpt-5.4", "claude-opus-4-7", "gemini-3.1-pro-preview")
PROMPT_CONDITIONS = ("standard_answer", "epistemic_hygiene_instruction")


class ClarifiedEvidencePrediction(EhaModel):
    claim_verdict: str
    confidence: float = Field(ge=0.0, le=1.0)
    clean_supporting_evidence: List[str] = Field(default_factory=list)
    refuting_evidence: List[str] = Field(default_factory=list)
    rejected_or_contaminated_evidence: List[str] = Field(default_factory=list)
    diagnostic_evidence: List[str] = Field(default_factory=list)
    selected_doc_ids: List[str] = Field(default_factory=list)
    actions: List[EpistemicAction] = Field(default_factory=list)
    evidence_notes: str = ""
    answer: str = ""

    @field_validator("claim_verdict", mode="before")
    @classmethod
    def normalize_verdict(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class ClarifiedRunRecord(EhaModel):
    task_id: str
    family: str
    condition: str
    model: str
    provider: str
    prompt_condition: str
    schema_variant: str = "clarified_schema"
    prediction: ClarifiedEvidencePrediction
    parse_success: bool
    parse_error: str = ""
    empty_output: bool = False
    schema_missing: bool = False
    response_format_used: str = ""
    json_extractor_used: str = "first_json_object"
    visible_output_tokens: int = 0
    usage: Dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0


class MinimalSchemaPrediction(EhaModel):
    claim_verdict: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_doc_ids: List[str] = Field(default_factory=list)
    selected_doc_ids: List[str] = Field(default_factory=list)
    evidence_notes: str = ""

    @field_validator("claim_verdict", mode="before")
    @classmethod
    def normalize_verdict(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class DiagnosticNoHygienePrediction(EhaModel):
    claim_verdict: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    rejected_or_contaminated_evidence: List[str] = Field(default_factory=list)
    diagnostic_evidence: List[str] = Field(default_factory=list)
    selected_doc_ids: List[str] = Field(default_factory=list)
    actions: List[EpistemicAction] = Field(default_factory=list)
    evidence_notes: str = ""
    answer: str = ""

    @field_validator("claim_verdict", mode="before")
    @classmethod
    def normalize_verdict(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class SchemaVariantRunRecord(EhaModel):
    task_id: str
    family: str
    condition: str
    model: str
    provider: str
    prompt_condition: str
    schema_variant: str
    prediction: Dict[str, Any]
    parse_success: bool
    parse_error: str = ""
    empty_output: bool = False
    schema_missing: bool = False
    response_format_used: str = ""
    json_extractor_used: str = "first_json_object"
    visible_output_tokens: int = 0
    usage: Dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0


def clarified_evidence_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "claim_verdict",
            "confidence",
            "clean_supporting_evidence",
            "refuting_evidence",
            "rejected_or_contaminated_evidence",
            "diagnostic_evidence",
            "selected_doc_ids",
            "actions",
            "evidence_notes",
            "answer",
        ],
        "properties": {
            "claim_verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "clean_supporting_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "refuting_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "rejected_or_contaminated_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
            "diagnostic_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "selected_doc_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
            "actions": {
                "type": "array",
                "maxItems": 2,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["action", "target", "rationale"],
                    "properties": {
                        "action": {"type": "string", "enum": ["open", "trace_source", "search_primary", "search_contradiction", "compare_versions", "abstain"]},
                        "target": {"type": "string"},
                        "rationale": {"type": "string", "maxLength": 600},
                    },
                },
            },
            "evidence_notes": {"type": "string", "maxLength": 1000},
            "answer": {"type": "string", "maxLength": 1000},
        },
    }


def minimal_evidence_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "claim_verdict",
            "confidence",
            "evidence_doc_ids",
            "selected_doc_ids",
            "evidence_notes",
        ],
        "properties": {
            "claim_verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "evidence_doc_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "selected_doc_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
            "evidence_notes": {"type": "string", "maxLength": 1000},
        },
    }


def diagnostic_no_hygiene_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "claim_verdict",
            "confidence",
            "supporting_evidence",
            "rejected_or_contaminated_evidence",
            "diagnostic_evidence",
            "selected_doc_ids",
            "actions",
            "evidence_notes",
            "answer",
        ],
        "properties": {
            "claim_verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "supporting_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "rejected_or_contaminated_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
            "diagnostic_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
            "selected_doc_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
            "actions": clarified_evidence_json_schema()["properties"]["actions"],
            "evidence_notes": {"type": "string", "maxLength": 1000},
            "answer": {"type": "string", "maxLength": 1000},
        },
    }


def schema_variant_json_schema(schema_variant: str) -> Dict[str, Any]:
    if schema_variant == "minimal_schema":
        return minimal_evidence_json_schema()
    if schema_variant == "diagnostic_schema_no_hygiene":
        return diagnostic_no_hygiene_json_schema()
    if schema_variant == "clarified_schema":
        return clarified_evidence_json_schema()
    raise ValueError(f"unknown generated-lore schema variant: {schema_variant}")


def first_json_object(text: str) -> Dict[str, Any]:
    decoder = json.JSONDecoder()
    start = text.find("{")
    while start >= 0:
        try:
            payload, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            start = text.find("{", start + 1)
            continue
        if isinstance(payload, dict):
            return payload
        start = text.find("{", start + 1)
    raise ValueError("No JSON object found.")


def parse_clarified_prediction(text: str) -> ClarifiedEvidencePrediction:
    return ClarifiedEvidencePrediction.model_validate(first_json_object(text))


def parse_schema_variant_prediction(text: str, schema_variant: str) -> MinimalSchemaPrediction | DiagnosticNoHygienePrediction | ClarifiedEvidencePrediction:
    payload = first_json_object(text)
    if schema_variant == "minimal_schema":
        return MinimalSchemaPrediction.model_validate(payload)
    if schema_variant == "diagnostic_schema_no_hygiene":
        return DiagnosticNoHygienePrediction.model_validate(payload)
    if schema_variant == "clarified_schema":
        return ClarifiedEvidencePrediction.model_validate(payload)
    raise ValueError(f"unknown generated-lore schema variant: {schema_variant}")


def normalize_clarified_prediction(prediction: ClarifiedEvidencePrediction, task: EpistemicTask) -> ClarifiedEvidencePrediction:
    allowed_doc_ids = [doc.doc_id for doc in task.documents]
    return prediction.model_copy(
        update={
            "clean_supporting_evidence": normalize_doc_refs(prediction.clean_supporting_evidence, allowed_doc_ids),
            "refuting_evidence": normalize_doc_refs(prediction.refuting_evidence, allowed_doc_ids),
            "rejected_or_contaminated_evidence": normalize_doc_refs(prediction.rejected_or_contaminated_evidence, allowed_doc_ids),
            "diagnostic_evidence": normalize_doc_refs(prediction.diagnostic_evidence, allowed_doc_ids),
            "selected_doc_ids": normalize_doc_refs(prediction.selected_doc_ids, allowed_doc_ids, task.max_selected_docs),
            "actions": prediction.actions[: task.max_actions],
        }
    )


def normalize_schema_variant_prediction(
    prediction: MinimalSchemaPrediction | DiagnosticNoHygienePrediction | ClarifiedEvidencePrediction,
    task: EpistemicTask,
) -> MinimalSchemaPrediction | DiagnosticNoHygienePrediction | ClarifiedEvidencePrediction:
    if isinstance(prediction, ClarifiedEvidencePrediction):
        return normalize_clarified_prediction(prediction, task)
    allowed_doc_ids = [doc.doc_id for doc in task.documents]
    if isinstance(prediction, MinimalSchemaPrediction):
        return prediction.model_copy(
            update={
                "evidence_doc_ids": normalize_doc_refs(prediction.evidence_doc_ids, allowed_doc_ids),
                "selected_doc_ids": normalize_doc_refs(prediction.selected_doc_ids, allowed_doc_ids, task.max_selected_docs),
            }
        )
    return prediction.model_copy(
        update={
            "supporting_evidence": normalize_doc_refs(prediction.supporting_evidence, allowed_doc_ids),
            "rejected_or_contaminated_evidence": normalize_doc_refs(prediction.rejected_or_contaminated_evidence, allowed_doc_ids),
            "diagnostic_evidence": normalize_doc_refs(prediction.diagnostic_evidence, allowed_doc_ids),
            "selected_doc_ids": normalize_doc_refs(prediction.selected_doc_ids, allowed_doc_ids, task.max_selected_docs),
            "actions": prediction.actions[: task.max_actions],
        }
    )


def translate_clarified_prediction_to_audit_ids(prediction: ClarifiedEvidencePrediction, visible_to_audit: Mapping[str, str]) -> ClarifiedEvidencePrediction:
    if not visible_to_audit:
        return prediction
    actions = [
        action.model_copy(
            update={
                "target": translate_doc_refs_to_audit([action.target], visible_to_audit)[0],
                "rationale": replace_doc_id_refs(action.rationale, visible_to_audit),
            }
        )
        for action in prediction.actions
    ]
    return prediction.model_copy(
        update={
            "clean_supporting_evidence": translate_doc_refs_to_audit(prediction.clean_supporting_evidence, visible_to_audit),
            "refuting_evidence": translate_doc_refs_to_audit(prediction.refuting_evidence, visible_to_audit),
            "rejected_or_contaminated_evidence": translate_doc_refs_to_audit(prediction.rejected_or_contaminated_evidence, visible_to_audit),
            "diagnostic_evidence": translate_doc_refs_to_audit(prediction.diagnostic_evidence, visible_to_audit),
            "selected_doc_ids": translate_doc_refs_to_audit(prediction.selected_doc_ids, visible_to_audit),
            "actions": actions,
            "evidence_notes": replace_doc_id_refs(prediction.evidence_notes, visible_to_audit),
            "answer": replace_doc_id_refs(prediction.answer, visible_to_audit),
        }
    )


def translate_schema_variant_prediction_to_audit_ids(
    prediction: MinimalSchemaPrediction | DiagnosticNoHygienePrediction | ClarifiedEvidencePrediction,
    visible_to_audit: Mapping[str, str],
) -> MinimalSchemaPrediction | DiagnosticNoHygienePrediction | ClarifiedEvidencePrediction:
    if isinstance(prediction, ClarifiedEvidencePrediction):
        return translate_clarified_prediction_to_audit_ids(prediction, visible_to_audit)
    if not visible_to_audit:
        return prediction
    if isinstance(prediction, MinimalSchemaPrediction):
        return prediction.model_copy(
            update={
                "evidence_doc_ids": translate_doc_refs_to_audit(prediction.evidence_doc_ids, visible_to_audit),
                "selected_doc_ids": translate_doc_refs_to_audit(prediction.selected_doc_ids, visible_to_audit),
                "evidence_notes": replace_doc_id_refs(prediction.evidence_notes, visible_to_audit),
            }
        )
    actions = [
        action.model_copy(
            update={
                "target": translate_doc_refs_to_audit([action.target], visible_to_audit)[0],
                "rationale": replace_doc_id_refs(action.rationale, visible_to_audit),
            }
        )
        for action in prediction.actions
    ]
    return prediction.model_copy(
        update={
            "supporting_evidence": translate_doc_refs_to_audit(prediction.supporting_evidence, visible_to_audit),
            "rejected_or_contaminated_evidence": translate_doc_refs_to_audit(prediction.rejected_or_contaminated_evidence, visible_to_audit),
            "diagnostic_evidence": translate_doc_refs_to_audit(prediction.diagnostic_evidence, visible_to_audit),
            "selected_doc_ids": translate_doc_refs_to_audit(prediction.selected_doc_ids, visible_to_audit),
            "actions": actions,
            "evidence_notes": replace_doc_id_refs(prediction.evidence_notes, visible_to_audit),
            "answer": replace_doc_id_refs(prediction.answer, visible_to_audit),
        }
    )


def build_clarified_messages(task: EpistemicTask, prompt_condition: str, *, opaque_doc_ids: bool = False, scrub_audit_labels: bool = False) -> List[Dict[str, str]]:
    base_messages = build_messages(task, prompt_condition, opaque_doc_ids=opaque_doc_ids, scrub_audit_labels=scrub_audit_labels)
    payload = json.loads(base_messages[-1]["content"])
    clarified_rules = [
        "Use the clarified evidence-role fields literally.",
        "clean_supporting_evidence: only clean primary or otherwise non-contaminated evidence that directly supports the claim. If the verdict is insufficient, this should normally be empty.",
        "refuting_evidence: clean primary or otherwise non-contaminated evidence that directly refutes the claim.",
        "rejected_or_contaminated_evidence: generated lore, reposts, stale sources, pseudo-consensus items, or authority-like pages without primary support.",
        "diagnostic_evidence: documents useful for diagnosing why the evidence environment is polluted or insufficient, but not valid support for the claim.",
        "Never place the same doc_id in clean_supporting_evidence and rejected_or_contaminated_evidence.",
        "For generated-lore tasks, generated or unsupported authority-like sources may be diagnostic or rejected, but they are not clean supporting evidence.",
    ]
    payload["policy"] = list(payload.get("policy", [])) + clarified_rules
    payload["schema"] = clarified_evidence_json_schema()
    base_messages[-1] = {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
    return base_messages


def schema_variant_policy(schema_variant: str, base_policy: Sequence[str]) -> List[str]:
    filtered = [
        rule
        for rule in base_policy
        if "supporting_evidence" not in rule and "rejected_evidence" not in rule and "actions choose" not in rule
    ]
    if schema_variant == "minimal_schema":
        return filtered + [
            "Use evidence_doc_ids for the document IDs most relevant to the verdict.",
            "This minimal schema intentionally does not separate support, rejection, and diagnostic roles.",
        ]
    if schema_variant == "diagnostic_schema_no_hygiene":
        return filtered + [
            "Use supporting_evidence for documents you treat as support for the claim.",
            "Use rejected_or_contaminated_evidence for documents you reject as unreliable or contaminated.",
            "Use diagnostic_evidence for documents that help diagnose the evidence environment but are not direct support.",
        ]
    if schema_variant == "clarified_schema":
        return filtered
    raise ValueError(f"unknown generated-lore schema variant: {schema_variant}")


def build_schema_variant_messages(
    task: EpistemicTask,
    schema_variant: str,
    prompt_condition: str,
    *,
    opaque_doc_ids: bool = False,
    scrub_audit_labels: bool = False,
) -> List[Dict[str, str]]:
    if schema_variant == "clarified_schema":
        return build_clarified_messages(task, prompt_condition, opaque_doc_ids=opaque_doc_ids, scrub_audit_labels=scrub_audit_labels)
    base_messages = build_messages(task, prompt_condition, opaque_doc_ids=opaque_doc_ids, scrub_audit_labels=scrub_audit_labels)
    payload = json.loads(base_messages[-1]["content"])
    payload["policy"] = schema_variant_policy(schema_variant, payload.get("policy", []))
    payload["schema"] = schema_variant_json_schema(schema_variant)
    base_messages[-1] = {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
    return base_messages


def load_run_records(path: Path) -> List[EpistemicRunRecord]:
    return [EpistemicRunRecord.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_clarified_records(path: Path) -> List[ClarifiedRunRecord]:
    if not path.exists():
        return []
    return [ClarifiedRunRecord.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_schema_variant_records(path: Path) -> List[SchemaVariantRunRecord]:
    if not path.exists():
        return []
    return [SchemaVariantRunRecord.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def generated_lore_tasks(tasks: Sequence[EpistemicTask]) -> List[EpistemicTask]:
    return [task for task in tasks if task.condition == "generated_lore"]


def pollutant_ids(task: EpistemicTask) -> set[str]:
    return set(task.contaminant_doc_ids) | set(task.generated_doc_ids) | set(task.stale_doc_ids)


def bool_float(value: bool) -> float:
    return 1.0 if value else 0.0


def current_role_row(record: EpistemicRunRecord, task: EpistemicTask, full_escape: float | str = "") -> Dict[str, Any]:
    prediction = record.prediction
    polluted = pollutant_ids(task)
    supporting = set(prediction.supporting_evidence)
    rejected = set(prediction.rejected_evidence)
    polluted_supporting = supporting & polluted
    rejected_pollutant = rejected & polluted
    dual_role = polluted_supporting & rejected
    belief_correct = prediction.claim_verdict == task.gold_verdict
    insufficient = prediction.claim_verdict == "insufficient"
    return {
        "schema_variant": "current_schema",
        "model": record.model,
        "provider": record.provider,
        "task_id": task.task_id,
        "family": task.family,
        "condition": task.condition,
        "prompt_condition": record.prompt_condition,
        "parse_success": bool_float(record.parse_success),
        "empty_output": bool_float(record.empty_output),
        "schema_missing": bool_float(record.schema_missing),
        "belief_correctness": bool_float(belief_correct),
        "insufficient_verdict": bool_float(insufficient),
        "rejected_pollutant": bool_float(bool(rejected_pollutant)),
        "polluted_supporting_evidence": bool_float(bool(polluted_supporting)),
        "dual_role_pollutant": bool_float(bool(dual_role)),
        "full_escape": full_escape,
        "predicted_verdict": prediction.claim_verdict,
        "gold_verdict": task.gold_verdict,
        "polluted_supporting_ids": ",".join(sorted(polluted_supporting)),
        "rejected_pollutant_ids": ",".join(sorted(rejected_pollutant)),
        "dual_role_pollutant_ids": ",".join(sorted(dual_role)),
    }


def clarified_role_row(record: ClarifiedRunRecord, task: EpistemicTask) -> Dict[str, Any]:
    prediction = record.prediction
    polluted = pollutant_ids(task)
    clean_supporting = set(prediction.clean_supporting_evidence)
    rejected = set(prediction.rejected_or_contaminated_evidence)
    diagnostic = set(prediction.diagnostic_evidence)
    polluted_clean_supporting = clean_supporting & polluted
    rejected_pollutant = rejected & polluted
    diagnostic_pollutant = diagnostic & polluted
    dual_role = polluted_clean_supporting & rejected
    belief_correct = prediction.claim_verdict == task.gold_verdict
    insufficient = prediction.claim_verdict == "insufficient"
    uncertainty_ok = insufficient if task.gold_verdict == "insufficient" else prediction.claim_verdict != "insufficient"
    role_escape = record.parse_success and belief_correct and not polluted_clean_supporting and uncertainty_ok
    return {
        "schema_variant": record.schema_variant,
        "model": record.model,
        "provider": record.provider,
        "task_id": task.task_id,
        "family": task.family,
        "condition": task.condition,
        "prompt_condition": record.prompt_condition,
        "parse_success": bool_float(record.parse_success),
        "empty_output": bool_float(record.empty_output),
        "schema_missing": bool_float(record.schema_missing),
        "belief_correctness": bool_float(belief_correct),
        "insufficient_verdict": bool_float(insufficient),
        "rejected_pollutant": bool_float(bool(rejected_pollutant)),
        "polluted_supporting_evidence": bool_float(bool(polluted_clean_supporting)),
        "dual_role_pollutant": bool_float(bool(dual_role)),
        "diagnostic_pollutant": bool_float(bool(diagnostic_pollutant)),
        "role_escape": bool_float(bool(role_escape)),
        "predicted_verdict": prediction.claim_verdict,
        "gold_verdict": task.gold_verdict,
        "polluted_supporting_ids": ",".join(sorted(polluted_clean_supporting)),
        "rejected_pollutant_ids": ",".join(sorted(rejected_pollutant)),
        "diagnostic_pollutant_ids": ",".join(sorted(diagnostic_pollutant)),
        "dual_role_pollutant_ids": ",".join(sorted(dual_role)),
    }


def schema_variant_role_row(record: SchemaVariantRunRecord, task: EpistemicTask) -> Dict[str, Any]:
    prediction = record.prediction
    polluted = pollutant_ids(task)
    if record.schema_variant == "minimal_schema":
        support = set(prediction.get("evidence_doc_ids", []))
        rejected: set[str] = set()
        diagnostic: set[str] = set()
    elif record.schema_variant == "diagnostic_schema_no_hygiene":
        support = set(prediction.get("supporting_evidence", []))
        rejected = set(prediction.get("rejected_or_contaminated_evidence", []))
        diagnostic = set(prediction.get("diagnostic_evidence", []))
    elif record.schema_variant == "clarified_schema":
        support = set(prediction.get("clean_supporting_evidence", []))
        rejected = set(prediction.get("rejected_or_contaminated_evidence", []))
        diagnostic = set(prediction.get("diagnostic_evidence", []))
    else:
        raise ValueError(f"unknown generated-lore schema variant: {record.schema_variant}")
    polluted_supporting = support & polluted
    rejected_pollutant = rejected & polluted
    diagnostic_pollutant = diagnostic & polluted
    dual_role = polluted_supporting & rejected
    verdict = str(prediction.get("claim_verdict", "")).strip().lower()
    belief_correct = verdict == task.gold_verdict
    insufficient = verdict == "insufficient"
    uncertainty_ok = insufficient if task.gold_verdict == "insufficient" else verdict != "insufficient"
    role_escape = record.parse_success and belief_correct and not polluted_supporting and uncertainty_ok
    return {
        "schema_variant": record.schema_variant,
        "model": record.model,
        "provider": record.provider,
        "task_id": task.task_id,
        "family": task.family,
        "condition": task.condition,
        "prompt_condition": record.prompt_condition,
        "parse_success": bool_float(record.parse_success),
        "empty_output": bool_float(record.empty_output),
        "schema_missing": bool_float(record.schema_missing),
        "belief_correctness": bool_float(belief_correct),
        "insufficient_verdict": bool_float(insufficient),
        "rejected_pollutant": bool_float(bool(rejected_pollutant)),
        "polluted_supporting_evidence": bool_float(bool(polluted_supporting)),
        "dual_role_pollutant": bool_float(bool(dual_role)),
        "diagnostic_pollutant": bool_float(bool(diagnostic_pollutant)),
        "role_escape": bool_float(bool(role_escape)),
        "predicted_verdict": verdict,
        "gold_verdict": task.gold_verdict,
        "polluted_supporting_ids": ",".join(sorted(polluted_supporting)),
        "rejected_pollutant_ids": ",".join(sorted(rejected_pollutant)),
        "diagnostic_pollutant_ids": ",".join(sorted(diagnostic_pollutant)),
        "dual_role_pollutant_ids": ",".join(sorted(dual_role)),
    }


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate_role_rows(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str]) -> List[Dict[str, Any]]:
    metrics = [
        "parse_success",
        "empty_output",
        "schema_missing",
        "belief_correctness",
        "insufficient_verdict",
        "rejected_pollutant",
        "polluted_supporting_evidence",
        "dual_role_pollutant",
        "full_escape",
        "role_escape",
        "diagnostic_pollutant",
    ]
    grouped: Dict[tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {name: value for name, value in zip(group_keys, key)}
        item["n"] = len(group)
        for metric in metrics:
            vals = [float(row[metric]) for row in group if row.get(metric) not in {"", None}]
            if vals:
                item[f"{metric}_rate" if metric not in {"full_escape", "role_escape"} else metric] = mean(vals)
        output.append(item)
    return output


def current_generated_lore_rows(records: Sequence[EpistemicRunRecord], tasks: Sequence[EpistemicTask], models: Sequence[str]) -> List[Dict[str, Any]]:
    task_by_id = {task.task_id: task for task in tasks}
    scored_by_key = {(row["model"], row["task_id"], row["prompt_condition"]): row for row in score_records(records, tasks)}
    rows: List[Dict[str, Any]] = []
    model_set = set(models)
    for record in records:
        task = task_by_id[record.task_id]
        if task.condition != "generated_lore" or record.model not in model_set:
            continue
        score_row = scored_by_key.get((record.model, record.task_id, record.prompt_condition), {})
        rows.append(current_role_row(record, task, score_row.get("operational_epistemic_escape", "")))
    return rows


def select_audit_pack_cases(rows: Sequence[Mapping[str, Any]], records: Sequence[EpistemicRunRecord], tasks: Sequence[EpistemicTask], size: int = 15) -> List[Dict[str, Any]]:
    record_by_key = {(record.model, record.task_id, record.prompt_condition): record for record in records}
    task_by_id = {task.task_id: task for task in tasks}
    gpt_rows = [row for row in rows if row["model"] == "gpt-5.4"]
    selected_keys: set[tuple[str, str, str]] = set()

    def take(candidates: Iterable[Mapping[str, Any]], count: int) -> None:
        for row in candidates:
            key = (str(row["model"]), str(row["task_id"]), str(row["prompt_condition"]))
            if key in selected_keys:
                continue
            selected_keys.add(key)
            if sum(1 for _ in selected_keys) >= size:
                return
            if len(selected_keys) >= count:
                return

    standard_failures = [
        row
        for row in gpt_rows
        if row["prompt_condition"] == "standard_answer"
        and (float(row.get("full_escape") or 0.0) == 0.0 or float(row["polluted_supporting_evidence"]) == 1.0)
    ]
    hygiene_cases = [row for row in gpt_rows if row["prompt_condition"] == "epistemic_hygiene_instruction"]
    edge_cases = [
        row
        for row in gpt_rows
        if float(row["polluted_supporting_evidence"]) == 0.0
        or float(row["dual_role_pollutant"]) == 0.0
        or row["family"] == "active_verification"
    ]
    take(standard_failures, 5)
    first_bucket_count = len(selected_keys)
    take(hygiene_cases, first_bucket_count + 5)
    second_bucket_count = len(selected_keys)
    take(edge_cases, second_bucket_count + 5)
    if len(selected_keys) < size:
        take(gpt_rows, size)

    output: List[Dict[str, Any]] = []
    scored_by_key = {(row["model"], row["task_id"], row["prompt_condition"]): row for row in rows}
    for key in sorted(selected_keys, key=lambda item: (item[2], item[1])):
        record = record_by_key[key]
        task = task_by_id[record.task_id]
        score = scored_by_key[key]
        prediction = record.prediction
        output.append(
            {
                "model": record.model,
                "task_id": task.task_id,
                "family": task.family,
                "condition": task.condition,
                "prompt_condition": record.prompt_condition,
                "question": task.question,
                "gold": {
                    "verdict": task.gold_verdict,
                    "primary_doc_ids": task.primary_doc_ids,
                    "contaminant_doc_ids": task.contaminant_doc_ids,
                    "generated_doc_ids": task.generated_doc_ids,
                },
                "model_output": {
                    "claim_verdict": prediction.claim_verdict,
                    "answer": prediction.answer,
                    "evidence_environment_assessment": prediction.evidence_environment_assessment,
                    "supporting_evidence": prediction.supporting_evidence,
                    "rejected_evidence": prediction.rejected_evidence,
                    "selected_doc_ids": prediction.selected_doc_ids,
                    "actions": [model_to_dict(action) for action in prediction.actions],
                },
                "scorer_decision": {
                    "belief_correctness": score["belief_correctness"],
                    "insufficient_verdict": score["insufficient_verdict"],
                    "polluted_supporting_evidence": score["polluted_supporting_evidence"],
                    "rejected_pollutant": score["rejected_pollutant"],
                    "dual_role_pollutant": score["dual_role_pollutant"],
                    "full_escape": score["full_escape"],
                    "polluted_supporting_ids": score["polluted_supporting_ids"],
                    "rejected_pollutant_ids": score["rejected_pollutant_ids"],
                    "dual_role_pollutant_ids": score["dual_role_pollutant_ids"],
                },
                "audit_questions": [
                    "Is the natural-language verdict semantically correct?",
                    "Does the answer describe generated lore or unsupported authority-like material as unreliable?",
                    "Are any generated, stale, repost, or contaminant documents incorrectly placed in supporting_evidence?",
                    "Are rejected_evidence and supporting_evidence assigning the same polluted document incompatible roles?",
                    "Would a downstream tool that only reads supporting_evidence treat polluted material as support?",
                ],
            }
        )
    return output[:size]


def write_side_note(path: Path, *, decomposition: Sequence[Mapping[str, Any]], schema_summary: Sequence[Mapping[str, Any]] | None = None) -> None:
    gpt_total = next((row for row in decomposition if row.get("model") == "gpt-5.4" and row.get("prompt_condition") == "all"), None)
    lines = [
        "# Generated-Lore Evidence-Role Audit Side Note",
        "",
        "This appendix does not revise the main frontier table. It interprets the generated-lore slice by separating belief correctness from machine-readable evidence-role discipline.",
        "",
    ]
    if gpt_total:
        lines.extend(
            [
                "## Existing-Output Decomposition",
                "",
                "For `gpt-5.4` on generated-lore records, the model usually recognizes the claim as insufficient but often places polluted material into `supporting_evidence`.",
                "",
                f"- n: `{gpt_total['n']}`",
                f"- belief correctness: `{float(gpt_total['belief_correctness_rate']):.3f}`",
                f"- insufficient verdict rate: `{float(gpt_total['insufficient_verdict_rate']):.3f}`",
                f"- rejected pollutant rate: `{float(gpt_total['rejected_pollutant_rate']):.3f}`",
                f"- polluted supporting evidence rate: `{float(gpt_total['polluted_supporting_evidence_rate']):.3f}`",
                f"- dual-role pollutant rate: `{float(gpt_total['dual_role_pollutant_rate']):.3f}`",
                f"- full escape: `{float(gpt_total['full_escape']):.3f}`",
                "",
            ]
        )
    lines.extend(
        [
            "The interpretation should therefore be: GPT-5.4 is not simply fooled by generated lore at the belief layer. The failure is mainly evidence-role confusion in structured fields that downstream systems may consume.",
            "",
            "## Why This Matters",
            "",
            "A human reader can often see that the prose rejects generated lore. A downstream system may not read the prose; it may read `supporting_evidence`. If polluted sources appear there, the agent interface has converted rejected material into machine-actionable support.",
            "",
        ]
    )
    if schema_summary:
        lines.extend(["## Schema Ablation Rerun", ""])
        lines.extend(markdown_table(schema_summary, ["schema_variant", "model", "prompt_condition", "n", "belief_correctness_rate", "polluted_supporting_evidence_rate", "dual_role_pollutant_rate", "role_escape", "full_escape"]))
        lines.append("")
    lines.extend(
        [
            "## Reporting Rule",
            "",
            "Do not say `GPT-5.4 cannot detect generated lore`. Say: `GPT-5.4 often detects generated lore in natural language, but the current schema exposes unstable evidence-role assignment in machine-readable fields.`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def completed_clarified_keys(path: Path) -> set[tuple[str, str, str]]:
    return {(record.model, record.task_id, record.prompt_condition) for record in load_clarified_records(path)}


def completed_schema_variant_keys(path: Path) -> set[tuple[str, str, str, str]]:
    return {(record.schema_variant, record.model, record.task_id, record.prompt_condition) for record in load_schema_variant_records(path)}


def write_jsonl_line(path: Path, payload: Mapping[str, Any], lock: threading.Lock) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def fallback_clarified_prediction(parse_error: str) -> ClarifiedEvidencePrediction:
    return ClarifiedEvidencePrediction(
        claim_verdict="insufficient",
        confidence=0.0,
        evidence_notes="Response failed before parseable clarified evidence roles were available.",
        answer=parse_error or "Call failed.",
    )


def fallback_schema_variant_prediction(schema_variant: str, parse_error: str) -> Dict[str, Any]:
    if schema_variant == "minimal_schema":
        return model_to_dict(
            MinimalSchemaPrediction(
                claim_verdict="insufficient",
                confidence=0.0,
                evidence_notes=parse_error or "Call failed.",
            )
        )
    if schema_variant == "diagnostic_schema_no_hygiene":
        return model_to_dict(
            DiagnosticNoHygienePrediction(
                claim_verdict="insufficient",
                confidence=0.0,
                evidence_notes="Response failed before parseable diagnostic-schema roles were available.",
                answer=parse_error or "Call failed.",
            )
        )
    if schema_variant == "clarified_schema":
        return model_to_dict(fallback_clarified_prediction(parse_error))
    raise ValueError(f"unknown generated-lore schema variant: {schema_variant}")


def call_schema_variant_job(
    *,
    schema_variant: str,
    model: str,
    provider: str,
    task: EpistemicTask,
    prompt_condition: str,
    out_dir: Path,
    max_output_tokens: Optional[int],
    response_format: str,
    timeout_s: float,
    cost_guard: CostGuard,
    cost_lock: threading.Lock,
) -> SchemaVariantRunRecord:
    doc_id_view = opaque_doc_id_view(task)
    base_messages = build_schema_variant_messages(
        task,
        schema_variant,
        prompt_condition,
        opaque_doc_ids=True,
        scrub_audit_labels=True,
    )
    prompt_payload = json.loads(base_messages[-1]["content"])
    prompt_audit = visible_payload_audit(prompt_payload.get("documents", []))
    messages = portable_chat_messages(base_messages)
    prompt_text = json.dumps(messages, ensure_ascii=False)
    with cost_lock:
        cost_guard.before_call(model, prompt_text, max_output_tokens or 4096)
    started = time.time()
    content = ""
    usage: Dict[str, Any] = {}
    used_format = response_format
    parse_success = False
    parse_error = ""
    empty_output = False
    schema_missing = False
    cost_usd = 0.0
    prediction_payload: Dict[str, Any] | None = None
    try:
        content, usage, used_format = complete_with_process_timeout(
            model=model,
            messages=messages,
            max_output_tokens=max_output_tokens,
            temperature=None,
            timeout_s=timeout_s,
            response_format=response_format,
            schema_name=f"eha_{schema_variant}_prediction",
            schema=schema_variant_json_schema(schema_variant),
        )
        with cost_lock:
            cost_usd = cost_guard.after_call(model, usage)
        empty_output = not content.strip()
        parsed = parse_schema_variant_prediction(content, schema_variant)
        translated = translate_schema_variant_prediction_to_audit_ids(parsed, doc_id_view.visible_to_audit)
        normalized = normalize_schema_variant_prediction(translated, task)
        prediction_payload = model_to_dict(normalized)
        parse_success = True
    except BudgetExceeded:
        raise
    except Exception as exc:  # noqa: BLE001
        parse_error = str(exc)
        empty_output = not content.strip()
        schema_missing = "field required" in parse_error.lower() or "missing" in parse_error.lower()
    finally:
        base = out_dir / "artifacts" / safe_model_dir(model) / schema_variant / prompt_condition / task.task_id
        write_json(
            base.with_suffix(".prompt.json"),
            {
                "model": model,
                "provider": provider,
                "task_id": task.task_id,
                "prompt_condition": prompt_condition,
                "schema_variant": schema_variant,
                "messages": messages,
                "model_visible_doc_id_policy": "opaque_per_task",
                "scorer_visible_to_audit_doc_id_map": doc_id_view.visible_to_audit,
                "visible_prompt_audit": prompt_audit,
            },
        )
        write_json(
            base.with_suffix(".response.json"),
            {
                "model": model,
                "provider": provider,
                "task_id": task.task_id,
                "prompt_condition": prompt_condition,
                "schema_variant": schema_variant,
                "content": content,
                "usage": usage,
                "response_format_used": used_format,
                "parse_success": parse_success,
                "parse_error": parse_error,
                "empty_output": empty_output,
                "schema_missing": schema_missing,
                "elapsed_s": round(time.time() - started, 3),
                "cost_usd": cost_usd,
            },
        )
    return SchemaVariantRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model=model,
        provider=provider,
        prompt_condition=prompt_condition,
        schema_variant=schema_variant,
        prediction=prediction_payload if prediction_payload is not None else fallback_schema_variant_prediction(schema_variant, parse_error),
        parse_success=parse_success,
        parse_error=parse_error,
        empty_output=empty_output,
        schema_missing=schema_missing,
        response_format_used=used_format,
        visible_output_tokens=estimate_tokens(content),
        usage=usage,
        cost_usd=cost_usd,
    )


def call_clarified_job(
    *,
    model: str,
    provider: str,
    task: EpistemicTask,
    prompt_condition: str,
    out_dir: Path,
    max_output_tokens: Optional[int],
    response_format: str,
    timeout_s: float,
    cost_guard: CostGuard,
    cost_lock: threading.Lock,
) -> ClarifiedRunRecord:
    doc_id_view = opaque_doc_id_view(task)
    base_messages = build_clarified_messages(task, prompt_condition, opaque_doc_ids=True, scrub_audit_labels=True)
    prompt_payload = json.loads(base_messages[-1]["content"])
    prompt_audit = visible_payload_audit(prompt_payload.get("documents", []))
    messages = portable_chat_messages(base_messages)
    prompt_text = json.dumps(messages, ensure_ascii=False)
    with cost_lock:
        cost_guard.before_call(model, prompt_text, max_output_tokens or 4096)
    started = time.time()
    content = ""
    usage: Dict[str, Any] = {}
    used_format = response_format
    parse_success = False
    parse_error = ""
    empty_output = False
    schema_missing = False
    cost_usd = 0.0
    prediction: Optional[ClarifiedEvidencePrediction] = None
    try:
        content, usage, used_format = complete_with_process_timeout(
            model=model,
            messages=messages,
            max_output_tokens=max_output_tokens,
            temperature=None,
            timeout_s=timeout_s,
            response_format=response_format,
            schema_name="eha_clarified_evidence_prediction",
            schema=clarified_evidence_json_schema(),
        )
        with cost_lock:
            cost_usd = cost_guard.after_call(model, usage)
        empty_output = not content.strip()
        translated_prediction = translate_clarified_prediction_to_audit_ids(parse_clarified_prediction(content), doc_id_view.visible_to_audit)
        prediction = normalize_clarified_prediction(translated_prediction, task)
        parse_success = True
    except BudgetExceeded:
        raise
    except Exception as exc:  # noqa: BLE001
        parse_error = str(exc)
        empty_output = not content.strip()
        schema_missing = "field required" in parse_error.lower() or "missing" in parse_error.lower()
    finally:
        base = out_dir / "artifacts" / safe_model_dir(model) / "clarified_schema" / prompt_condition / task.task_id
        write_json(
            base.with_suffix(".prompt.json"),
            {
                "model": model,
                "provider": provider,
                "task_id": task.task_id,
                "prompt_condition": prompt_condition,
                "messages": messages,
                "model_visible_doc_id_policy": "opaque_per_task",
                "scorer_visible_to_audit_doc_id_map": doc_id_view.visible_to_audit,
                "visible_prompt_audit": prompt_audit,
            },
        )
        write_json(
            base.with_suffix(".response.json"),
            {
                "model": model,
                "provider": provider,
                "task_id": task.task_id,
                "prompt_condition": prompt_condition,
                "content": content,
                "usage": usage,
                "response_format_used": used_format,
                "parse_success": parse_success,
                "parse_error": parse_error,
                "empty_output": empty_output,
                "schema_missing": schema_missing,
                "elapsed_s": round(time.time() - started, 3),
                "cost_usd": cost_usd,
            },
        )
    return ClarifiedRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model=model,
        provider=provider,
        prompt_condition=prompt_condition,
        prediction=prediction if prediction is not None else fallback_clarified_prediction(parse_error),
        parse_success=parse_success,
        parse_error=parse_error,
        empty_output=empty_output,
        schema_missing=schema_missing,
        response_format_used=used_format,
        visible_output_tokens=estimate_tokens(content),
        usage=usage,
        cost_usd=cost_usd,
    )


def write_audit_outputs(
    out_dir: Path,
    *,
    current_rows: Sequence[Mapping[str, Any]],
    clarified_rows: Sequence[Mapping[str, Any]] | None = None,
    audit_pack: Sequence[Mapping[str, Any]],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    decomposition_rows = aggregate_role_rows(current_rows, ["model", "prompt_condition"])
    all_prompt_rows = aggregate_role_rows(current_rows, ["model"])
    for row in all_prompt_rows:
        row["prompt_condition"] = "all"
    decomposition = sorted([*decomposition_rows, *all_prompt_rows], key=lambda row: (row["model"], row["prompt_condition"]))
    write_csv(out_dir / "generated_lore_belief_vs_role_decomposition.csv", decomposition)
    write_csv(out_dir / "generated_lore_belief_vs_role_rows.csv", current_rows)
    write_jsonl(out_dir / "gpt54_generated_lore_audit_pack.jsonl", audit_pack)
    schema_summary: List[Dict[str, Any]] = []
    if clarified_rows is not None:
        combined_rows = [*current_rows, *clarified_rows]
        write_csv(out_dir / "schema_clarification_mini_rerun_rows.csv", combined_rows)
        schema_summary = aggregate_role_rows(combined_rows, ["schema_variant", "model", "prompt_condition"])
        schema_summary.extend(aggregate_role_rows(combined_rows, ["schema_variant", "model"]))
        for row in schema_summary:
            row.setdefault("prompt_condition", "all")
        schema_summary = sorted(schema_summary, key=lambda row: (row["schema_variant"], row["model"], row.get("prompt_condition", "")))
        write_csv(out_dir / "schema_clarification_mini_rerun.csv", schema_summary)
        if {row.get("schema_variant") for row in combined_rows} - {"current_schema", "clarified_schema"}:
            write_csv(out_dir / "generated_lore_schema_ablation_4variant_rows.csv", combined_rows)
            write_csv(out_dir / "generated_lore_schema_ablation_4variant.csv", schema_summary)
    write_side_note(out_dir / "side_note_update.md", decomposition=decomposition, schema_summary=schema_summary)
    write_json(
        out_dir / "report_manifest.json",
        {
            "generated_lore_current_rows": len(current_rows),
            "gpt54_audit_pack_rows": len(audit_pack),
            "clarified_rows": len(clarified_rows or []),
            "outputs": [
                "generated_lore_belief_vs_role_decomposition.csv",
                "generated_lore_belief_vs_role_rows.csv",
                "gpt54_generated_lore_audit_pack.jsonl",
                "schema_clarification_mini_rerun.csv",
                "schema_clarification_mini_rerun_rows.csv",
                "generated_lore_schema_ablation_4variant.csv",
                "generated_lore_schema_ablation_4variant_rows.csv",
                "side_note_update.md",
            ],
        },
    )


@app.command("audit-existing")
def audit_existing(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    main_run_dir: Path = typer.Option(Path("results/reports-eha-frontier-main"), help="Frontier main run directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-generated-lore-role-audit-2026-05-15"), help="Audit output directory."),
    models: str = typer.Option(",".join(DEFAULT_MODELS), help="Comma-separated model IDs for decomposition context."),
) -> None:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    records = load_run_records(main_run_dir / "predictions.jsonl")
    model_list = [part.strip() for part in models.split(",") if part.strip()]
    current_rows = current_generated_lore_rows(records, tasks, model_list)
    audit_pack = select_audit_pack_cases(current_rows, records, tasks)
    write_audit_outputs(out_dir, current_rows=current_rows, audit_pack=audit_pack)
    console.print(f"[green]Wrote generated-lore existing-output audit[/green] to {out_dir}")


@app.command("clarified-run")
def clarified_run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    main_run_dir: Path = typer.Option(Path("results/reports-eha-frontier-main"), help="Frontier main run directory for current-schema comparison."),
    out_dir: Path = typer.Option(Path("results/reports-eha-generated-lore-role-audit-2026-05-15"), help="Audit output directory."),
    models: str = typer.Option(",".join(DEFAULT_MODELS), help="Comma-separated model IDs."),
    prompt_conditions: str = typer.Option(",".join(PROMPT_CONDITIONS), help="Comma-separated prompt conditions."),
    limit_tasks: int = typer.Option(0, help="Limit generated-lore tasks for a smoke run; 0 means all generated-lore tasks."),
    parallel_models: int = typer.Option(3, help="Number of model streams to run concurrently."),
    resume: bool = typer.Option(True, help="Skip completed clarified-schema rows."),
    soft_cap_usd: float = typer.Option(120.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(250.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(400.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    tasks = generated_lore_tasks(read_tasks(task_dir / "tasks.jsonl"))
    if limit_tasks > 0:
        tasks = tasks[:limit_tasks]
    model_list = [part.strip() for part in models.split(",") if part.strip()]
    prompts = [part.strip() for part in prompt_conditions.split(",") if part.strip()]
    profiles_by_model = {profile.model: profile for profile in FRONTIER_MODEL_PROFILES}
    missing = sorted(set(model_list) - set(profiles_by_model))
    if missing:
        raise typer.BadParameter(f"unknown model(s): {', '.join(missing)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "clarified_predictions.jsonl"
    completed = completed_clarified_keys(predictions_path) if resume else set()
    write_json(
        out_dir / "clarified_run_manifest.json",
        {
            "schema_variant": "clarified_schema",
            "task_count": len(tasks),
            "models": model_list,
            "prompt_conditions": prompts,
            "planned_calls": len(tasks) * len(model_list) * len(prompts),
            "resume_completed_count": len(completed),
        },
    )
    write_lock = threading.Lock()
    cost_lock = threading.Lock()
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)

    def run_model_stream(model: str) -> int:
        profile = profiles_by_model[model]
        count = 0
        for task in tasks:
            for prompt in prompts:
                if (model, task.task_id, prompt) in completed:
                    continue
                record = call_clarified_job(
                    model=model,
                    provider=profile.provider,
                    task=task,
                    prompt_condition=prompt,
                    out_dir=out_dir,
                    max_output_tokens=profile.max_output_tokens,
                    response_format=profile.response_format,
                    timeout_s=profile.timeout_s,
                    cost_guard=cost_guard,
                    cost_lock=cost_lock,
                )
                write_jsonl_line(predictions_path, model_to_dict(record), write_lock)
                count += 1
                log.info("clarified generated_lore model={model} task={task_id} prompt={prompt} parse_success={parse_success}", model=model, task_id=task.task_id, prompt=prompt, parse_success=record.parse_success)
        return count

    try:
        with ThreadPoolExecutor(max_workers=max(1, min(parallel_models, len(model_list)))) as executor:
            futures = [executor.submit(run_model_stream, model) for model in model_list]
            for future in as_completed(futures):
                future.result()
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise typer.Exit(code=2) from exc

    main_records = load_run_records(main_run_dir / "predictions.jsonl")
    current_rows = current_generated_lore_rows(main_records, read_tasks(task_dir / "tasks.jsonl"), model_list)
    clarified_records = load_clarified_records(predictions_path)
    task_by_id = {task.task_id: task for task in read_tasks(task_dir / "tasks.jsonl")}
    clarified_rows = [clarified_role_row(record, task_by_id[record.task_id]) for record in clarified_records]
    audit_pack = select_audit_pack_cases(current_rows, main_records, read_tasks(task_dir / "tasks.jsonl"))
    write_audit_outputs(out_dir, current_rows=current_rows, clarified_rows=clarified_rows, audit_pack=audit_pack)
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in clarified_records), 6), **cost_guard.report()})
    console.print(f"[green]Wrote generated-lore clarified-schema audit[/green] to {out_dir}")


@app.command("schema-ablation-run")
def schema_ablation_run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    main_run_dir: Path = typer.Option(Path("results/reports-eha-frontier-main-opaque-2026-05-15"), help="Frontier main run directory for current-schema comparison."),
    out_dir: Path = typer.Option(Path("results/reports-eha-generated-lore-role-audit-opaque-2026-05-15"), help="Audit output directory."),
    models: str = typer.Option(",".join(DEFAULT_MODELS), help="Comma-separated model IDs."),
    schema_variants: str = typer.Option("minimal_schema,diagnostic_schema_no_hygiene", help="Comma-separated new schema variants to run."),
    prompt_conditions: str = typer.Option("standard_answer", help="Comma-separated prompt conditions. Default isolates schema changes without the hygiene prompt."),
    limit_tasks: int = typer.Option(0, help="Limit generated-lore tasks for a smoke run; 0 means all generated-lore tasks."),
    parallel_models: int = typer.Option(3, help="Number of model streams to run concurrently."),
    resume: bool = typer.Option(True, help="Skip completed schema-variant rows."),
    soft_cap_usd: float = typer.Option(120.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(250.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(400.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    tasks = generated_lore_tasks(read_tasks(task_dir / "tasks.jsonl"))
    if limit_tasks > 0:
        tasks = tasks[:limit_tasks]
    model_list = [part.strip() for part in models.split(",") if part.strip()]
    variants = [part.strip() for part in schema_variants.split(",") if part.strip()]
    prompts = [part.strip() for part in prompt_conditions.split(",") if part.strip()]
    for variant in variants:
        schema_variant_json_schema(variant)
    profiles_by_model = {profile.model: profile for profile in FRONTIER_MODEL_PROFILES}
    missing = sorted(set(model_list) - set(profiles_by_model))
    if missing:
        raise typer.BadParameter(f"unknown model(s): {', '.join(missing)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "schema_ablation_predictions.jsonl"
    completed = completed_schema_variant_keys(predictions_path) if resume else set()
    write_json(
        out_dir / "schema_ablation_run_manifest.json",
        {
            "schema_variants": variants,
            "task_count": len(tasks),
            "models": model_list,
            "prompt_conditions": prompts,
            "planned_calls": len(tasks) * len(model_list) * len(prompts) * len(variants),
            "resume_completed_count": len(completed),
            "note": "New variants default to standard_answer to isolate schema effects from the hygiene prompt.",
        },
    )
    write_lock = threading.Lock()
    cost_lock = threading.Lock()
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)

    def run_model_stream(model: str) -> int:
        profile = profiles_by_model[model]
        count = 0
        for variant in variants:
            for task in tasks:
                for prompt in prompts:
                    if (variant, model, task.task_id, prompt) in completed:
                        continue
                    record = call_schema_variant_job(
                        schema_variant=variant,
                        model=model,
                        provider=profile.provider,
                        task=task,
                        prompt_condition=prompt,
                        out_dir=out_dir,
                        max_output_tokens=profile.max_output_tokens,
                        response_format=profile.response_format,
                        timeout_s=profile.timeout_s,
                        cost_guard=cost_guard,
                        cost_lock=cost_lock,
                    )
                    write_jsonl_line(predictions_path, model_to_dict(record), write_lock)
                    count += 1
                    log.info(
                        "schema ablation generated_lore variant={variant} model={model} task={task_id} prompt={prompt} parse_success={parse_success}",
                        variant=variant,
                        model=model,
                        task_id=task.task_id,
                        prompt=prompt,
                        parse_success=record.parse_success,
                    )
        return count

    try:
        with ThreadPoolExecutor(max_workers=max(1, min(parallel_models, len(model_list)))) as executor:
            futures = [executor.submit(run_model_stream, model) for model in model_list]
            for future in as_completed(futures):
                future.result()
    except BudgetExceeded as exc:
        write_json(out_dir / "schema_ablation_cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise typer.Exit(code=2) from exc

    all_tasks = read_tasks(task_dir / "tasks.jsonl")
    main_records = load_run_records(main_run_dir / "predictions.jsonl")
    current_rows = current_generated_lore_rows(main_records, all_tasks, model_list)
    task_by_id = {task.task_id: task for task in all_tasks}
    clarified_records = [
        record
        for record in load_clarified_records(out_dir / "clarified_predictions.jsonl")
        if record.model in set(model_list)
    ]
    clarified_rows = [clarified_role_row(record, task_by_id[record.task_id]) for record in clarified_records]
    variant_records = [
        record
        for record in load_schema_variant_records(predictions_path)
        if record.schema_variant in set(variants) and record.model in set(model_list) and record.prompt_condition in set(prompts)
    ]
    variant_rows = [schema_variant_role_row(record, task_by_id[record.task_id]) for record in variant_records]
    audit_pack = select_audit_pack_cases(current_rows, main_records, all_tasks)
    write_audit_outputs(out_dir, current_rows=current_rows, clarified_rows=[*clarified_rows, *variant_rows], audit_pack=audit_pack)
    write_json(out_dir / "schema_ablation_cost_report.json", {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in variant_records), 6), **cost_guard.report()})
    console.print(f"[green]Wrote generated-lore schema ablation[/green] to {out_dir}")


if __name__ == "__main__":
    app()
