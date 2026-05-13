from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Sequence

from .schemas import AgentDocument, MatrixPrediction, Phase2Prediction


def matrix_prediction_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "claim_verdict",
            "confidence",
            "supporting_evidence",
            "rejected_evidence",
            "answer",
            "evidence_notes",
        ],
        "properties": {
            "claim_verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "supporting_evidence": {"type": "array", "items": {"type": "string"}},
            "rejected_evidence": {"type": "array", "items": {"type": "string"}},
            "answer": {"type": "string"},
            "evidence_notes": {"type": "string"},
        },
    }


def docs_payload(documents: Sequence[AgentDocument]) -> List[Dict[str, Any]]:
    return [
        {
            "doc_id": doc.doc_id,
            "title": doc.title,
            "source_type": doc.source_type,
            "timestamp": doc.timestamp,
            "body": doc.body,
            "visible_citations": list(doc.visible_citations),
        }
        for doc in documents
    ]


def build_simple_answer_messages(question: str, documents: Sequence[AgentDocument]) -> List[Dict[str, str]]:
    return [
        {
            "role": "developer",
            "content": (
                "Answer the question from the provided synthetic corpus only. "
                "Return strict JSON matching the supplied schema. Use doc_id values for evidence."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "question": question,
                    "documents": docs_payload(documents),
                    "schema": matrix_prediction_json_schema(),
                },
                ensure_ascii=False,
            ),
        },
    ]


def claim_first_rules(*, strict_support: bool = False) -> List[str]:
    rules = [
        "First decide whether current primary evidence directly supports, refutes, or is insufficient for the target claim.",
        "Prefer current primary sources over secondary summaries.",
        "Multiple reposts of the same upstream source are not independent evidence.",
        "Do not cite generated lore, reposts, outdated documents, or contradicted sources as independent support.",
        "If no primary or current evidence supports the claim, use insufficient rather than overclaiming.",
        "Rejected or suspicious documents may appear in rejected_evidence, not supporting_evidence.",
    ]
    if strict_support:
        rules.extend(
            [
                "If claim_verdict is supported or refuted, supporting_evidence must contain at least one clean doc_id.",
                "Do not output empty supporting_evidence for supported or refuted verdicts.",
                "If no clean supporting doc_id is available, claim_verdict must be insufficient.",
            ]
        )
    return rules


def build_claim_first_messages(question: str, documents: Sequence[AgentDocument], *, version: str = "claim_first_citation_v1") -> List[Dict[str, str]]:
    if version not in {"claim_first_citation_v1", "claim_first_citation_v1_1"}:
        raise ValueError(f"unknown claim-first prompt version: {version}")
    rules = claim_first_rules(strict_support=version == "claim_first_citation_v1_1")
    return [
        {
            "role": "developer",
            "content": (
                "You are evaluating a synthetic information ecosystem. "
                "Do not use the web. Do not infer hidden labels. Return only strict JSON."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "task": version,
                    "question": question,
                    "policy": rules,
                    "documents": docs_payload(documents),
                    "schema": matrix_prediction_json_schema(),
                },
                ensure_ascii=False,
            ),
        },
    ]


def parse_matrix_prediction_json(text: str) -> MatrixPrediction:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:]
    return MatrixPrediction.model_validate_json(stripped.strip())


def phase2_prediction_to_matrix(prediction: Phase2Prediction) -> MatrixPrediction:
    return MatrixPrediction(
        claim_verdict=prediction.claim_verdict,
        confidence=prediction.confidence,
        supporting_evidence=list(prediction.supporting_evidence),
        rejected_evidence=list(prediction.rejected_evidence),
        answer=prediction.answer,
        evidence_notes=" ".join(
            part
            for part in [
                prediction.source_independence,
                prediction.contamination_notes,
                prediction.remaining_uncertainties,
            ]
            if part
        ),
    )
