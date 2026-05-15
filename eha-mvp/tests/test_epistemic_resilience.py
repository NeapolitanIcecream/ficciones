from __future__ import annotations

import json
from pathlib import Path

from eha.epistemic_resilience import (
    EpistemicAction,
    EpistemicPrediction,
    EpistemicRunRecord,
    build_epistemic_tasks,
    build_messages,
    opaque_doc_id_view,
    score_record,
    selected_model_tasks,
    translate_prediction_to_audit_ids,
    visible_payload_audit,
)


def test_epistemic_resilience_dataset_has_planned_family_and_condition_counts() -> None:
    tasks = build_epistemic_tasks(Path("data/matrix-v1"))

    assert len(tasks) == 100
    assert {family: sum(1 for task in tasks if task.family == family) for family in {task.family for task in tasks}} == {
        "packet_judgment": 40,
        "evidence_selection": 40,
        "active_verification": 20,
    }
    assert {condition: sum(1 for task in tasks if task.condition == condition) for condition in {task.condition for task in tasks}} == {
        "clean": 20,
        "conflicting_evidence": 20,
        "false_consensus": 20,
        "buried_primary": 20,
        "generated_lore": 20,
    }


def test_sample_model_uses_small_stratified_task_subset() -> None:
    tasks = build_epistemic_tasks(Path("data/matrix-v1"))

    selected = selected_model_tasks(tasks, "openai/gpt-5.5", "openai/gpt-5.5", 12)

    assert len(selected) == 12
    assert {family: sum(1 for task in selected if task.family == family) for family in {task.family for task in selected}} == {
        "packet_judgment": 4,
        "evidence_selection": 4,
        "active_verification": 4,
    }
    assert {condition: sum(1 for task in selected if task.condition == condition) for condition in {task.condition for task in selected}} == {
        "clean": 3,
        "conflicting_evidence": 3,
        "false_consensus": 2,
        "buried_primary": 2,
        "generated_lore": 2,
    }


def test_packet_escape_requires_correct_belief_and_clean_support() -> None:
    task = next(task for task in build_epistemic_tasks(Path("data/matrix-v1")) if task.family == "packet_judgment" and task.condition == "false_consensus")
    dirty_doc = task.contaminant_doc_ids[0]
    record = EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model="heuristic",
        prompt_condition="standard_answer",
        backend="heuristic",
        prediction=EpistemicPrediction(claim_verdict=task.gold_verdict, confidence=0.8, supporting_evidence=[dirty_doc]),
        parse_success=True,
    )

    row = score_record(record, task)

    assert row["belief_correctness"] == 1.0
    assert row["evidence_cleanliness"] == 0.0
    assert row["epistemic_escape"] == 0.0


def test_selection_rewards_primary_seeking_and_duplicate_avoidance() -> None:
    task = next(task for task in build_epistemic_tasks(Path("data/matrix-v1")) if task.family == "evidence_selection" and task.primary_doc_ids)
    primary = task.primary_doc_ids[0]
    backgrounds = [doc.doc_id for doc in task.documents if doc.role == "background"][:2]
    record = EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model="heuristic",
        prompt_condition="epistemic_hygiene_instruction",
        backend="heuristic",
        prediction=EpistemicPrediction(
            claim_verdict="insufficient",
            confidence=0.6,
            selected_doc_ids=[primary, *backgrounds],
        ),
        parse_success=True,
    )

    row = score_record(record, task)

    assert row["primary_seeking_rate"] == 1.0
    assert row["duplicate_avoidance_rate"] == 1.0
    assert row["generated_lore_avoidance_rate"] == 1.0
    assert row["epistemic_escape"] == 1.0


def test_active_verification_scores_primary_and_contradiction_actions() -> None:
    task = next(task for task in build_epistemic_tasks(Path("data/matrix-v1")) if task.family == "active_verification" and task.condition == "buried_primary")
    record = EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model="heuristic",
        prompt_condition="epistemic_hygiene_instruction",
        backend="heuristic",
        prediction=EpistemicPrediction(
            claim_verdict=task.gold_verdict,
            confidence=0.7,
            supporting_evidence=[],
            actions=[
                EpistemicAction(action="search_primary", target=task.question, rationale="Need primary record."),
                EpistemicAction(action="search_contradiction", target=task.question, rationale="Check disconfirmation."),
            ],
        ),
        parse_success=True,
    )

    row = score_record(record, task)

    assert row["primary_action_rate"] == 1.0
    assert row["contradiction_action_rate"] == 1.0
    assert row["epistemic_escape"] == 1.0


def test_parse_failure_counts_as_operational_failure_even_when_fallback_verdict_matches() -> None:
    task = next(task for task in build_epistemic_tasks(Path("data/matrix-v1")) if task.family == "packet_judgment" and task.condition == "generated_lore")
    record = EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model="api-model",
        prompt_condition="standard_answer",
        backend="api",
        prediction=EpistemicPrediction(
            claim_verdict=task.gold_verdict,
            confidence=0.0,
            evidence_environment_assessment="Response failed to parse.",
            answer="Parse failure.",
        ),
        parse_success=False,
        parse_error="Expecting value",
    )

    row = score_record(record, task)

    assert row["parse_success"] == 0.0
    assert row["epistemic_escape"] == 0.0
    assert row["operational_epistemic_escape"] == 0.0
    assert row["conditional_epistemic_escape"] == ""


def test_opaque_prompt_view_hides_semantic_doc_ids_and_hidden_fields() -> None:
    task = build_epistemic_tasks(Path("data/matrix-v1"))[0]

    messages = build_messages(task, "standard_answer", opaque_doc_ids=True, scrub_audit_labels=True)
    payload = json.loads(messages[-1]["content"])
    audit = visible_payload_audit(payload["documents"])

    assert audit["semantic_doc_id_hits"] == 0
    assert audit["semantic_visible_citation_hits"] == 0
    assert audit["audit_id_hits_in_title_or_body"] == 0
    assert audit["hidden_field_hits"] == []
    assert {doc["doc_id"] for doc in payload["documents"]} == {f"doc_{i:03d}" for i in range(1, len(task.documents) + 1)}
    assert not any("primary" in doc["doc_id"].lower() or "pollutant" in doc["doc_id"].lower() for doc in payload["documents"])


def test_opaque_prediction_refs_translate_back_to_audit_ids_before_scoring() -> None:
    task = build_epistemic_tasks(Path("data/matrix-v1"))[0]
    view = opaque_doc_id_view(task)
    primary = task.primary_doc_ids[0]
    visible_primary = view.audit_to_visible[primary]
    prediction = EpistemicPrediction(
        claim_verdict=task.gold_verdict,
        confidence=0.8,
        supporting_evidence=[visible_primary],
        selected_doc_ids=[visible_primary],
        actions=[EpistemicAction(action="open", target=visible_primary, rationale=f"Inspect {visible_primary}.")],
        evidence_environment_assessment=f"{visible_primary} is the strongest record.",
        answer=f"Use {visible_primary}.",
    )

    translated = translate_prediction_to_audit_ids(prediction, view.visible_to_audit)

    assert translated.supporting_evidence == [primary]
    assert translated.selected_doc_ids == [primary]
    assert translated.actions[0].target == primary
    assert translated.actions[0].rationale == f"Inspect {primary}."
    assert translated.evidence_environment_assessment == f"{primary} is the strongest record."
    assert translated.answer == f"Use {primary}."
