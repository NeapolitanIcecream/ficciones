from __future__ import annotations

from eha.epistemic_generated_lore_audit import (
    ClarifiedEvidencePrediction,
    clarified_evidence_json_schema,
    clarified_role_row,
    current_role_row,
    parse_clarified_prediction,
)
from eha.epistemic_resilience import EpistemicPrediction, EpistemicRunRecord, EpistemicTask, EvidenceDoc


def generated_lore_task() -> EpistemicTask:
    return EpistemicTask(
        task_id="ert_gl",
        family="packet_judgment",
        source_task_id="source_gl",
        difficulty="L5",
        condition="generated_lore",
        question="Is the claim established?",
        gold_verdict="insufficient",
        documents=[
            EvidenceDoc(doc_id="generated", title="Generated lore", source_type="wiki", timestamp="2025-01-01", body="No source.", role="generated_lore"),
            EvidenceDoc(doc_id="context", title="Context", source_type="note", timestamp="2025-01-02", body="Context.", role="background"),
        ],
        contaminant_doc_ids=["generated"],
        generated_doc_ids=["generated"],
        primary_doc_ids=[],
    )


def test_current_role_row_counts_polluted_supporting_and_dual_role_evidence() -> None:
    task = generated_lore_task()
    record = EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model="gpt-5.4",
        prompt_condition="standard_answer",
        backend="api",
        prediction=EpistemicPrediction(
            claim_verdict="insufficient",
            confidence=0.9,
            supporting_evidence=["generated"],
            rejected_evidence=["generated"],
        ),
        parse_success=True,
    )

    row = current_role_row(record, task, full_escape=0.0)

    assert row["belief_correctness"] == 1.0
    assert row["insufficient_verdict"] == 1.0
    assert row["polluted_supporting_evidence"] == 1.0
    assert row["rejected_pollutant"] == 1.0
    assert row["dual_role_pollutant"] == 1.0


def test_clarified_schema_names_distinct_evidence_roles() -> None:
    schema = clarified_evidence_json_schema()

    assert "supporting_evidence" not in schema["properties"]
    assert "clean_supporting_evidence" in schema["required"]
    assert "rejected_or_contaminated_evidence" in schema["required"]
    assert "diagnostic_evidence" in schema["required"]


def test_clarified_role_row_rewards_rejecting_generated_lore_without_clean_support() -> None:
    task = generated_lore_task()
    record = type(
        "Record",
        (),
        {
            "schema_variant": "clarified_schema",
            "task_id": task.task_id,
            "family": task.family,
            "condition": task.condition,
            "model": "gpt-5.4",
            "provider": "OpenAI",
            "prompt_condition": "standard_answer",
            "parse_success": True,
            "empty_output": False,
            "schema_missing": False,
            "prediction": ClarifiedEvidencePrediction(
                claim_verdict="insufficient",
                confidence=0.9,
                clean_supporting_evidence=[],
                rejected_or_contaminated_evidence=["generated"],
                diagnostic_evidence=["generated"],
            ),
        },
    )()

    row = clarified_role_row(record, task)  # type: ignore[arg-type]

    assert row["belief_correctness"] == 1.0
    assert row["polluted_supporting_evidence"] == 0.0
    assert row["rejected_pollutant"] == 1.0
    assert row["diagnostic_pollutant"] == 1.0
    assert row["role_escape"] == 1.0


def test_parse_clarified_prediction_extracts_first_json_object() -> None:
    prediction = parse_clarified_prediction(
        '```json\n{"claim_verdict":"insufficient","confidence":0.8,'
        '"clean_supporting_evidence":[],"refuting_evidence":[],'
        '"rejected_or_contaminated_evidence":["generated"],"diagnostic_evidence":["generated"],'
        '"selected_doc_ids":[],"actions":[],"evidence_notes":"generated lore only","answer":"Insufficient."}\n```'
    )

    assert prediction.claim_verdict == "insufficient"
    assert prediction.rejected_or_contaminated_evidence == ["generated"]
