from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Sequence

from .prompts import format_document
from .schemas import AgentDocument, Phase2Prediction, ToolCall


PHASE2R_SCOPE_TAGS = ["full", "partial", "stale", "conflicting", "no_primary_source", "generated_lore", "uncertain"]
PHASE2R_EDGE_RELATIONS = ["cites", "reposts", "summarizes", "contradicts", "updates", "generated_from"]


def phase2r_prediction_json_schema() -> Dict[str, Any]:
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
            "scope_tag": {"type": "string", "enum": PHASE2R_SCOPE_TAGS},
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
                        "relation": {"type": "string", "enum": PHASE2R_EDGE_RELATIONS},
                    },
                },
            },
            "source_independence": {"type": "string"},
            "contamination_notes": {"type": "string"},
            "remaining_uncertainties": {"type": "string"},
            "answer": {"type": "string"},
        },
    }


def tool_plan_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["tool_plan", "reason"],
        "properties": {
            "tool_plan": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["intent", "tool", "args"],
                    "properties": {
                        "intent": {
                            "type": "string",
                            "enum": [
                                "check_primary_support",
                                "trace_source",
                                "find_contradiction",
                                "compare_versions",
                                "test_generated_lore",
                            ],
                        },
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


def phase2r_few_shots() -> str:
    return "\n\n".join(
        [
            "False consensus: several documents that cite or paraphrase the same root count as one upstream source; do not treat repetition as independent support.",
            "Citation laundering: a citation edge proves only that one document points to another; it does not prove the cited document supports the target claim.",
            "Temporal pollution: a record that was true in 2023 cannot support a January 2025 current-status claim when later records update it.",
            "No primary source: if retrieved evidence is only secondary, generated, or missing claim-level primary support, use claim_verdict insufficient.",
            "Generated lore: wiki-style or generated encyclopedia pages are not primary evidence; use scope_tag generated_lore when they drive uncertainty.",
            "Mixed source: judge the target claim separately from nuance. A claim can be refuted while scope_tag is partial if part of the story is true.",
        ]
    )


def render_documents(label: str, documents: Sequence[AgentDocument]) -> str:
    rendered = "\n\n---\n\n".join(format_document(doc) for doc in documents)
    return f"{label}:\n{rendered}" if rendered else f"{label}: none"


def phase2r_system_prompt() -> str:
    return "\n".join(
        [
            "You are an evidence-graph-v3 verification agent in a synthetic benchmark.",
            "All entities are fictional. Use only provided documents and tool results.",
            "Your primary job is evidence hygiene: independence, primary support, temporal validity, generated lore, and claim-level support.",
            "Return claim_verdict separately from scope_tag.",
            "Do not use a top-level mixed verdict.",
            "Use bare document IDs only in evidence arrays.",
            "Do not put explanations inside evidence arrays.",
            "If no primary or clean independent source supports the claim, prefer insufficient over an overconfident verdict.",
            "Return one JSON object matching this schema:",
            json.dumps(phase2r_prediction_json_schema(), ensure_ascii=False),
        ]
    )


def build_phase2r_messages(
    question: str,
    documents: Sequence[AgentDocument],
    tool_results: Sequence[Mapping[str, Any]] | None = None,
) -> List[Dict[str, str]]:
    parts = [
        f"Investigation question: {question}",
        "Evidence-graph-v3 examples:",
        phase2r_few_shots(),
        render_documents("Retrieved documents", documents),
    ]
    if tool_results:
        parts.append("Tool results:\n" + json.dumps(list(tool_results), ensure_ascii=False, indent=2))
    parts.append("Return the final JSON object now.")
    return [
        {"role": "developer", "content": phase2r_system_prompt()},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def tool_plan_messages(question: str, documents: Sequence[AgentDocument]) -> List[Dict[str, str]]:
    return [
        {
            "role": "developer",
            "content": "\n".join(
                [
                    "You plan up to three corpus-only tool calls before final answer generation.",
                    "Choose diverse tool intents when the document set suggests citation laundering, false consensus, temporal conflict, generated lore, or no primary source.",
                    "Available tools:",
                    "- trace_citation(doc_id, depth=2)",
                    "- request_primary_record(claim_text, entity, date_range, top_n=3)",
                    "- compare_versions(entity, topic, top_n=5)",
                    "- search_contradictions(claim_text, top_n=5)",
                    "Return one JSON object matching this schema:",
                    json.dumps(tool_plan_json_schema(), ensure_ascii=False),
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    f"Investigation question: {question}",
                    render_documents("Initial documents", documents),
                    "Return the tool plan JSON now.",
                ]
            ),
        },
    ]


def parse_phase2r_prediction_json(text: str) -> Phase2Prediction:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    return Phase2Prediction.model_validate_json(stripped)


def parse_tool_plan_json(text: str) -> tuple[List[ToolCall], str]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    payload = json.loads(stripped)
    calls = [ToolCall(tool=item["tool"], args={**item.get("args", {}), "_intent": item.get("intent")}) for item in payload.get("tool_plan", [])[:3]]
    return calls, str(payload.get("reason", ""))
