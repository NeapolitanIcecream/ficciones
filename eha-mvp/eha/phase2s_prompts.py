from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Sequence

from .phase2r_prompts import PHASE2R_SCOPE_TAGS
from .prompts import format_document
from .schemas import AgentDocument, EvidenceDiagnostics, Phase2Prediction, Phase2SPrediction, ToolCall, VerificationLedgerEntry


DIAGNOSTIC_FIELDS = [
    "has_primary_support",
    "primary_support_is_current",
    "evidence_has_conflict",
    "support_is_partial",
    "sources_are_independent",
    "citation_laundering_detected",
    "generated_lore_detected",
    "no_primary_source_detected",
]
CRITICAL_RISKS = [
    "stale_evidence",
    "conflicting_evidence",
    "generated_lore",
    "no_primary_source",
    "false_consensus",
    "citation_laundering",
    "partial_support",
]
LEDGER_RISKS = ["temporal_staleness", "source_independence", "citation_chain", "generated_lore", "primary_support"]
LEDGER_METHODS = ["read_docs", "trace_citation", "compare_versions", "request_primary_record", "search_contradictions"]
LEDGER_EFFECTS = ["supports", "weakens", "refutes", "makes_insufficient"]
ROUTING_TOOLS = ["trace_citation", "request_primary_record", "compare_versions", "search_contradictions"]


def phase2s_prediction_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "claim_verdict",
            "confidence",
            "evidence_diagnostics",
            "critical_risks",
            "supporting_evidence",
            "rejected_evidence",
            "verification_ledger",
            "answer",
        ],
        "properties": {
            "claim_verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "evidence_diagnostics": {
                "type": "object",
                "additionalProperties": False,
                "required": DIAGNOSTIC_FIELDS,
                "properties": {
                    "has_primary_support": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                    "primary_support_is_current": {"type": "string", "enum": ["yes", "no", "not_applicable", "uncertain"]},
                    "evidence_has_conflict": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                    "support_is_partial": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                    "sources_are_independent": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                    "citation_laundering_detected": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                    "generated_lore_detected": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                    "no_primary_source_detected": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                },
            },
            "critical_risks": {"type": "array", "items": {"type": "string", "enum": CRITICAL_RISKS}},
            "supporting_evidence": {"type": "array", "items": {"type": "string"}},
            "rejected_evidence": {"type": "array", "items": {"type": "string"}},
            "verification_ledger": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["risk_checked", "method", "evidence", "finding", "effect_on_verdict"],
                    "properties": {
                        "risk_checked": {"type": "string", "enum": LEDGER_RISKS},
                        "method": {"type": "string", "enum": LEDGER_METHODS},
                        "evidence": {"type": "array", "items": {"type": "string"}},
                        "finding": {"type": "string"},
                        "effect_on_verdict": {"type": "string", "enum": LEDGER_EFFECTS},
                    },
                },
            },
            "answer": {"type": "string"},
        },
    }


def phase2s_routing_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["tool_routing_diagnosis", "chosen_tools"],
        "properties": {
            "tool_routing_diagnosis": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "is_current_status_question",
                    "does_evidence_contain_dates_or_versions",
                    "is_temporal_comparison_required",
                    "reason",
                ],
                "properties": {
                    "is_current_status_question": {"type": "boolean"},
                    "does_evidence_contain_dates_or_versions": {"type": "boolean"},
                    "is_temporal_comparison_required": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
            },
            "chosen_tools": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["tool", "why", "args"],
                    "properties": {
                        "tool": {"type": "string", "enum": ROUTING_TOOLS},
                        "why": {"type": "string"},
                        "args": {"type": "object"},
                    },
                },
            },
        },
    }


def render_documents(label: str, documents: Sequence[AgentDocument]) -> str:
    rendered = "\n\n---\n\n".join(format_document(doc) for doc in documents)
    return f"{label}:\n{rendered}" if rendered else f"{label}: none"


def phase2s_system_prompt() -> str:
    return "\n".join(
        [
            "You are an evidence-diagnostics-v1 verification agent in a synthetic benchmark.",
            "All entities are fictional. Use only provided documents and tool results.",
            "Separate claim correctness from evidence-risk diagnosis.",
            "Use evidence_diagnostics as multi-label evidence state, not as one exclusive scope tag.",
            "Mark every critical risk that is visible or unresolved: stale_evidence, conflicting_evidence, generated_lore, no_primary_source, false_consensus, citation_laundering, partial_support.",
            "Use verification_ledger to tie risks, methods, evidence IDs, and verdict effects together.",
            "Use bare document IDs only in evidence arrays and ledger evidence.",
            "If no primary source supports the target claim, prefer insufficient over overclaiming.",
            "Return one JSON object matching this schema:",
            json.dumps(phase2s_prediction_json_schema(), ensure_ascii=False),
        ]
    )


def build_phase2s_messages(
    question: str,
    documents: Sequence[AgentDocument],
    tool_results: Sequence[Mapping[str, Any]] | None = None,
) -> List[Dict[str, str]]:
    parts = [
        f"Investigation question: {question}",
        "Diagnostic rules:",
        "\n".join(
            [
                "- Stale: old records or superseded versions are not current support.",
                "- Conflict: clean evidence refutes or contradicts the apparent support.",
                "- Generated lore: wiki-style/generated pages cannot substitute for primary evidence.",
                "- No primary: secondary summaries alone are insufficient for claim-level support.",
                "- Citation laundering: a citation chain can point to irrelevant or unsupported sources.",
                "- False consensus: repeated same-root summaries are not independent support.",
                "- Partial support: a document may support a weaker claim while not supporting the target claim.",
            ]
        ),
        render_documents("Retrieved documents", documents),
    ]
    if tool_results:
        parts.append("Tool results:\n" + json.dumps(list(tool_results), ensure_ascii=False, indent=2))
    parts.append("Return the final JSON object now.")
    return [
        {"role": "developer", "content": phase2s_system_prompt()},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def phase2s_routing_messages(question: str, documents: Sequence[AgentDocument]) -> List[Dict[str, str]]:
    return [
        {
            "role": "developer",
            "content": "\n".join(
                [
                    "You choose up to three corpus-only tool calls before final answer generation.",
                    "You must explicitly decide whether temporal comparison is required.",
                    "Rule: if the question asks about current status, active certification, updated policy, version history, yearly audit, or whether an old claim remains true, and multiple dates or versions appear, call compare_versions.",
                    "Available tools:",
                    "- trace_citation(doc_id, depth=2)",
                    "- request_primary_record(claim_text, entity, date_range, top_n=3)",
                    "- compare_versions(entity, topic, top_n=5)",
                    "- search_contradictions(claim_text, top_n=5)",
                    "Return one JSON object matching this schema:",
                    json.dumps(phase2s_routing_json_schema(), ensure_ascii=False),
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    f"Investigation question: {question}",
                    render_documents("Initial documents", documents),
                    "Return the routing JSON now.",
                ]
            ),
        },
    ]


def parse_phase2s_prediction_json(text: str) -> Phase2SPrediction:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    return Phase2SPrediction.model_validate_json(stripped)


def parse_phase2s_routing_json(text: str) -> tuple[List[ToolCall], Dict[str, Any]]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    payload = json.loads(stripped)
    calls = [
        ToolCall(tool=str(item["tool"]), args={**item.get("args", {}), "_why": item.get("why", "")})
        for item in payload.get("chosen_tools", [])[:3]
    ]
    return calls, dict(payload.get("tool_routing_diagnosis", {}))


def diagnostics_from_scope_tag(scope_tag: str) -> EvidenceDiagnostics:
    fields: Dict[str, str] = {
        "has_primary_support": "yes",
        "primary_support_is_current": "yes",
        "evidence_has_conflict": "no",
        "support_is_partial": "no",
        "sources_are_independent": "yes",
        "citation_laundering_detected": "no",
        "generated_lore_detected": "no",
        "no_primary_source_detected": "no",
    }
    if scope_tag == "stale":
        fields["primary_support_is_current"] = "no"
    elif scope_tag == "conflicting":
        fields["evidence_has_conflict"] = "yes"
    elif scope_tag == "partial":
        fields["support_is_partial"] = "yes"
    elif scope_tag == "no_primary_source":
        fields["has_primary_support"] = "no"
        fields["primary_support_is_current"] = "not_applicable"
        fields["no_primary_source_detected"] = "yes"
    elif scope_tag == "generated_lore":
        fields["has_primary_support"] = "no"
        fields["primary_support_is_current"] = "not_applicable"
        fields["generated_lore_detected"] = "yes"
        fields["no_primary_source_detected"] = "yes"
    elif scope_tag == "uncertain":
        fields = {key: "uncertain" for key in DIAGNOSTIC_FIELDS}
        fields["primary_support_is_current"] = "uncertain"
    return EvidenceDiagnostics.model_validate(fields)


def risks_from_scope_tag(scope_tag: str) -> List[str]:
    return {
        "stale": ["stale_evidence"],
        "conflicting": ["conflicting_evidence"],
        "partial": ["partial_support"],
        "no_primary_source": ["no_primary_source"],
        "generated_lore": ["generated_lore", "no_primary_source"],
    }.get(scope_tag, [])


def phase2_prediction_to_phase2s(prediction: Phase2Prediction) -> Phase2SPrediction:
    scope_tag = prediction.scope_tag if prediction.scope_tag in PHASE2R_SCOPE_TAGS else "uncertain"
    diagnostics = diagnostics_from_scope_tag(scope_tag)
    risks = risks_from_scope_tag(scope_tag)
    method = "read_docs"
    ledger = [
        VerificationLedgerEntry(
            risk_checked="primary_support",
            method=method,
            evidence=list(dict.fromkeys(prediction.supporting_evidence + prediction.rejected_evidence)),
            finding=f"Legacy evidence_graph_v3 emitted scope_tag={scope_tag}.",
            effect_on_verdict="supports" if prediction.claim_verdict == "supported" else "refutes" if prediction.claim_verdict == "refuted" else "makes_insufficient",
        )
    ]
    return Phase2SPrediction(
        claim_verdict=prediction.claim_verdict,
        confidence=prediction.confidence,
        evidence_diagnostics=diagnostics,
        critical_risks=risks,  # type: ignore[arg-type]
        supporting_evidence=prediction.supporting_evidence,
        rejected_evidence=prediction.rejected_evidence,
        verification_ledger=ledger,
        answer=prediction.answer,
    )
