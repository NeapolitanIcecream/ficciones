from __future__ import annotations

import json
from typing import Dict, List, Sequence

from .schemas import AgentDocument, Prediction


STRATEGY_INSTRUCTIONS: Dict[str, str] = {
    "topk_rag": (
        "Answer the investigation question using the retrieved documents. "
        "Return the best verdict and concise evidence."
    ),
    "citation_prompt": (
        "Answer the investigation question and cite document IDs that support your answer. "
        "Only cite documents you actually use."
    ),
    "source_independence_prompt": (
        "Answer the investigation question, but first reason about whether sources are independent, "
        "current, primary, and claim-level supportive. Repeated documents with the same upstream source "
        "must not count as independent evidence."
    ),
    "evidence_graph_prompt": (
        "Build a small evidence graph before answering. Track citation, repost, summary, stale-version, "
        "and misread relations when visible from the retrieved documents. Prefer primary records, reject "
        "unsupported reposts, and abstain when the evidence is insufficient."
    ),
}


def prediction_json_schema() -> Dict[str, object]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "verdict",
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
            "verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient", "mixed"]},
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
                        "relation": {"type": "string"},
                    },
                },
            },
            "source_independence": {"type": "string"},
            "contamination_notes": {"type": "string"},
            "remaining_uncertainties": {"type": "string"},
            "answer": {"type": "string"},
        },
    }


def system_prompt(strategy: str) -> str:
    if strategy in {"topk_rag", "citation_prompt"}:
        role = "You are a standard retrieval-augmented QA assistant in a synthetic benchmark."
        edge_rule = "Set predicted_dependency_edges to an empty array."
        rejection_rule = "Use rejected_evidence only for documents that directly conflict with your answer; otherwise use an empty array."
    elif strategy == "source_independence_prompt":
        role = "You are a source-independence auditing agent in a synthetic benchmark."
        edge_rule = "Include dependency edges when a visible citation or repost relationship is explicit."
        rejection_rule = "Reject stale, non-independent, non-primary, or claim-unsupported documents."
    else:
        role = "You are an evidence-graph auditing agent in a synthetic benchmark."
        edge_rule = "Include all visible citation, repost, stale-version, and misread relations that use provided document IDs."
        rejection_rule = "Reject stale, non-independent, non-primary, generated-lore, or claim-unsupported documents."
    return "\n".join(
        [
            role,
            "All entities are fictional. Use only the provided documents.",
            STRATEGY_INSTRUCTIONS[strategy],
            "Keep the JSON concise. Use bare document IDs only in supporting_evidence and rejected_evidence.",
            "Do not put explanations inside evidence arrays. Put explanations in the text fields.",
            rejection_rule,
            edge_rule,
            "When predicted_dependency_edges is non-empty, from and to must be document IDs from the provided documents.",
            "Do not include placeholder nodes such as raw records that are not provided as documents.",
            "Return one JSON object. Do not include markdown.",
            "The JSON object must match this schema:",
            json.dumps(prediction_json_schema(), ensure_ascii=False),
        ]
    )


def format_document(doc: AgentDocument) -> str:
    return "\n".join(
        [
            f"doc_id: {doc.doc_id}",
            f"title: {doc.title}",
            f"source_type: {doc.source_type}",
            f"timestamp: {doc.timestamp}",
            "visible_citations: " + (", ".join(doc.visible_citations) if doc.visible_citations else "none"),
            "body:",
            doc.body,
        ]
    )


def user_prompt(question: str, documents: Sequence[AgentDocument]) -> str:
    rendered_docs = "\n\n---\n\n".join(format_document(doc) for doc in documents)
    return "\n\n".join(
        [
            f"Investigation question: {question}",
            "Retrieved documents:",
            rendered_docs,
            "Return the JSON object now.",
        ]
    )


def build_messages(strategy: str, question: str, documents: Sequence[AgentDocument]) -> List[Dict[str, str]]:
    return [
        {"role": "developer", "content": system_prompt(strategy)},
        {"role": "user", "content": user_prompt(question, documents)},
    ]


def parse_prediction_json(text: str) -> Prediction:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    return Prediction.model_validate_json(stripped)
