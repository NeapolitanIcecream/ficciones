from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Sequence

from .prompts import format_document
from .schemas import AgentDocument, Phase2Prediction, ToolCall


def phase2_prediction_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "claim_verdict",
            "scope_tag",
            "confidence",
            "supporting_evidence",
            "rejected_evidence",
            "predicted_dependency_edges",
            "source_independence",
            "contamination_notes",
            "remaining_uncertainties",
            "answer",
        ],
        "properties": {
            "claim_verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient"]},
            "scope_tag": {"type": "string", "enum": ["full", "partial", "stale", "conflicting", "mixed_evidence", "no_primary_source"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "supporting_evidence": {"type": "array", "items": {"type": "string"}},
            "rejected_evidence": {"type": "array", "items": {"type": "string"}},
            "predicted_dependency_edges": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["from", "to", "relation"],
                    "properties": {
                        "from": {"type": "string"},
                        "to": {"type": "string"},
                        "relation": {"type": "string", "enum": ["cites", "reposts", "summarizes", "contradicts", "updates", "misreads"]},
                    },
                },
            },
            "source_independence": {"type": "string"},
            "contamination_notes": {"type": "string"},
            "remaining_uncertainties": {"type": "string"},
            "answer": {"type": "string"},
        },
    }


def tool_decision_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["need_tools", "tool_calls", "reason"],
        "properties": {
            "need_tools": {"type": "boolean"},
            "tool_calls": {
                "type": "array",
                "maxItems": 2,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["tool", "args"],
                    "properties": {
                        "tool": {
                            "type": "string",
                            "enum": ["trace_citation", "request_primary_record", "compare_versions", "search_contradictions"],
                        },
                        "args": {"type": "object"},
                    },
                },
            },
            "reason": {"type": "string"},
        },
    }


def phase2_system_prompt() -> str:
    return "\n".join(
        [
            "You are an evidence-graph retrieval agent in a synthetic benchmark.",
            "All organizations, documents, and claims are fictional. Use only the provided documents and tool results.",
            "Return claim_verdict separately from scope_tag. Do not use a top-level mixed verdict.",
            "Repeated sources with the same visible citation chain are not independent evidence.",
            "Old documents do not support current claims unless the question asks about that old date.",
            "A locally corrupted or partially correct source can be useful context but should not support an overbroad claim.",
            "Prefer primary records such as audit_report, regulator_filing, contract, incident_log, version_history, certification_record, and database_export.",
            "Use bare document IDs only in supporting_evidence and rejected_evidence.",
            "Do not put explanations inside evidence arrays. Put explanations in text fields.",
            "When predicted_dependency_edges is non-empty, from and to must be document IDs from the provided documents or tool-returned documents.",
            "Return one JSON object. Do not include markdown.",
            "The JSON object must match this schema:",
            json.dumps(phase2_prediction_json_schema(), ensure_ascii=False),
        ]
    )


def few_shot_notes() -> str:
    return "\n\n".join(
        [
            "Example rule: if five blogs repeat one press release, cite at most one as context and do not treat them as independent support.",
            "Example rule: if a 2023 certificate was valid when issued but the question asks about January 2025, mark the scope as stale and use the later version record.",
            "Example rule: if a document says version 4.2 contributed to some incidents but configuration caused most incidents, claim_verdict can be refuted while scope_tag is mixed_evidence.",
        ]
    )


def render_documents(label: str, documents: Sequence[AgentDocument]) -> str:
    rendered = "\n\n---\n\n".join(format_document(doc) for doc in documents)
    return f"{label}:\n{rendered}" if rendered else f"{label}: none"


def phase2_user_prompt(question: str, documents: Sequence[AgentDocument], tool_results: Sequence[Mapping[str, Any]] | None = None) -> str:
    parts = [
        f"Investigation question: {question}",
        few_shot_notes(),
        render_documents("Retrieved documents", documents),
    ]
    if tool_results:
        parts.append("Tool results:\n" + json.dumps(list(tool_results), ensure_ascii=False, indent=2))
    parts.append("Return the final JSON object now.")
    return "\n\n".join(parts)


def build_phase2_messages(
    question: str,
    documents: Sequence[AgentDocument],
    tool_results: Sequence[Mapping[str, Any]] | None = None,
) -> List[Dict[str, str]]:
    return [
        {"role": "developer", "content": phase2_system_prompt()},
        {"role": "user", "content": phase2_user_prompt(question, documents, tool_results)},
    ]


def tool_decision_messages(question: str, documents: Sequence[AgentDocument]) -> List[Dict[str, str]]:
    return [
        {
            "role": "developer",
            "content": "\n".join(
                [
                    "You decide whether a synthetic retrieval agent should call corpus-only verification tools before answering.",
                    "Available tools:",
                    "- trace_citation(doc_id, depth=2): follows visible citations.",
                    "- request_primary_record(claim_text, entity, date_range, top_n=3): searches primary-source documents only.",
                    "- compare_versions(entity, topic, top_n=5): retrieves dated versions for temporal checks.",
                    "- search_contradictions(claim_text, top_n=5): searches for corrections, audits, revised records, and contradictions.",
                    "Use at most two tool calls. Prefer request_primary_record when no primary source is visible.",
                    "Return one JSON object matching this schema:",
                    json.dumps(tool_decision_json_schema(), ensure_ascii=False),
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    f"Investigation question: {question}",
                    render_documents("Initial retrieved documents", documents),
                    "Return the tool decision JSON now.",
                ]
            ),
        },
    ]


def parse_phase2_prediction_json(text: str) -> Phase2Prediction:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    return Phase2Prediction.model_validate_json(stripped)


def parse_tool_decision_json(text: str) -> tuple[bool, List[ToolCall], str]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    payload = json.loads(stripped)
    calls = [ToolCall.model_validate(item) for item in payload.get("tool_calls", [])[:2]]
    return bool(payload.get("need_tools", False)), calls, str(payload.get("reason", ""))
