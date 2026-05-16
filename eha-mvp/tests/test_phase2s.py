from __future__ import annotations

from collections import Counter

import pytest
from loguru import logger

from eha.cost_guard import CostGuard
from eha.phase2_retrieval import retrieve
from eha.phase2s_generate import (
    SCOPE_COUNTS,
    TEMPORAL_COUNTS,
    generate_scope_diagnostic_dataset,
    generate_temporal_routing_dataset,
)
from eha.phase2r_generate import generate_phase2r_dataset
from eha.phase2s_run import run_phase2s_records
from eha.phase2s_prompts import build_phase2s_messages, phase2s_system_prompt
from eha.phase2s_prompts import phase2s_routing_messages
from eha.phase2s_prompts import parse_phase2s_prediction_json, phase2s_prediction_json_schema
from eha.phase2s_scoring import critical_risk_confusion_by_flag, critical_risk_macro_f1, phase2s_gate, phase2s_module_a_gate, score_phase2s_record, score_phase2s_run, selected_module_c_prompt
from eha.schemas import EvidenceDiagnostics, Phase2SPrediction, Phase2SRunRecord, gold_by_doc


logger.disable("eha.phase2s_run")


def test_phase2s_scope_dataset_matches_diagnostic_isolation_spec() -> None:
    manifest, tasks, documents, gold_documents, _ = generate_scope_diagnostic_dataset(seed=7319)
    docs_by_task = Counter(doc.task_id for doc in documents)

    assert manifest.name == "EHA-v2S-scope-diagnostic"
    assert manifest.seed == 7319
    assert manifest.episodes == 120
    assert manifest.episode_type_counts == SCOPE_COUNTS
    assert Counter(task.episode_type for task in tasks) == SCOPE_COUNTS
    assert all(task.phase == "phase2s_scope" for task in tasks)
    assert all(4 <= docs_by_task[task.task_id] <= 8 for task in tasks)
    assert all(task.gold.diagnostics for task in tasks)
    assert len(documents) == len(gold_documents)


def test_phase2s_scope_dataset_makes_verdict_observable_in_document_text() -> None:
    """Regression: Module A claim verdicts must be inferable from visible document text."""
    _, tasks, documents, _, _ = generate_scope_diagnostic_dataset(seed=7319)
    docs_by_task = {}
    for doc in documents:
        docs_by_task.setdefault(doc.task_id, {})[doc.doc_id] = doc

    for task in tasks:
        task_docs = docs_by_task[task.task_id]
        current = task_docs.get(f"{task.task_id}_current_primary")
        if task.episode_type == "generated_lore_with_no_primary":
            assert current is None
            continue

        assert current is not None
        body = current.body.lower()
        if task.episode_type == "full_current_primary_support":
            assert "explicitly supports the target claim" in body
        elif task.episode_type in {"stale_evidence", "conflicting_evidence", "citation_laundering"}:
            assert "target claim is not supported" in body or "contradicts the target claim" in body
        elif task.episode_type == "partial_support":
            assert "does not establish the broader target claim" in body


def test_phase2s_temporal_dataset_matches_routing_repair_spec() -> None:
    manifest, tasks, documents, gold_documents, _ = generate_temporal_routing_dataset(seed=8144)
    temporal_tasks = [task for task in tasks if task.episode_type != "non_temporal_control"]
    docs_by_task = {}
    for doc in documents:
        docs_by_task.setdefault(doc.task_id, set()).add(doc.doc_id)

    assert manifest.name == "EHA-v2S-temporal-routing"
    assert manifest.seed == 8144
    assert manifest.episodes == 60
    assert manifest.episode_type_counts == TEMPORAL_COUNTS
    assert Counter(task.episode_type for task in tasks) == TEMPORAL_COUNTS
    assert all(task.phase == "phase2s_temporal" for task in tasks)
    assert all(task.gold.critical_risks == ["stale_evidence"] for task in temporal_tasks)
    assert all(any(doc_id.endswith("_old_version") for doc_id in docs_by_task[task.task_id]) for task in temporal_tasks)
    assert all(any(doc_id.endswith("_current_record") for doc_id in docs_by_task[task.task_id]) for task in temporal_tasks)
    assert len(documents) == len(gold_documents)


def test_phase2s_heuristic_gate_passes_full_repair_pipeline(tmp_path) -> None:
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
    )
    all_tasks = scope["tasks"] + temporal["tasks"] + phase2r["tasks"]
    all_gold = scope["gold_documents"] + temporal["gold_documents"] + phase2r["gold_documents"]
    rows = score_phase2s_run(records, all_tasks, all_gold)
    gate = phase2s_gate(rows, retrieval_rows, records)

    assert len(records) == 1224
    assert any(record.module == "A" and record.prompt == "evidence_diagnostics_v4" for record in records)
    assert gate.passed
    assert gate.details["module_a_prompt"] == "evidence_diagnostics_v4"
    assert gate.details["module_b_temporal_route"]["compare_versions_rate"] == 1.0
    assert gate.details["module_b_temporal_route"]["useful_compare_versions_rate"] == 1.0


def test_phase2s_module_a_only_runs_calibration_arm_without_full_pipeline(tmp_path) -> None:
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
        modules=("A",),
    )
    rows = score_phase2s_run(records, scope["tasks"], scope["gold_documents"])
    gate = phase2s_module_a_gate(rows)

    assert len(records) == 600
    assert retrieval_rows == []
    assert {record.module for record in records} == {"A"}
    assert Counter(record.prompt for record in records) == {
        "evidence_graph_v3": 120,
        "evidence_diagnostics_v1": 120,
        "evidence_diagnostics_v2": 120,
        "evidence_diagnostics_v3": 120,
        "evidence_diagnostics_v4": 120,
    }
    assert gate.passed
    assert gate.details["module_a_prompt"] == "evidence_diagnostics_v4"


def test_phase2s_module_a_only_can_run_single_diagnostic_prompt(tmp_path) -> None:
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
        modules=("A",),
        module_a_prompts=("evidence_diagnostics_v3",),
    )
    rows = score_phase2s_run(records, scope["tasks"], scope["gold_documents"])
    gate = phase2s_module_a_gate(rows)

    assert len(records) == 120
    assert retrieval_rows == []
    assert {record.prompt for record in records} == {"evidence_diagnostics_v3"}
    assert gate.passed
    assert gate.details["module_a_prompt"] == "evidence_diagnostics_v3"


def test_phase2s_modules_b_and_c_use_configured_final_diagnostic_prompt(tmp_path) -> None:
    """Regression: Module C repair experiments must not be stuck on the v1 final prompt."""
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
        modules=("B", "C"),
        final_diagnostic_prompt="evidence_diagnostics_v5",
    )

    assert len(records) == 624
    assert retrieval_rows
    assert {record.module for record in records} == {"B", "C"}
    assert {record.prompt for record in records} == {"evidence_diagnostics_v5"}
    assert any(record.module == "C" and record.strategy == "evidence_diagnostics_v5" for record in records)


def test_phase2s_module_c_calibration_slice_runs_only_listed_static_rows(tmp_path) -> None:
    """Phase 2S v8 calibration must be able to run a small fixed C-only slice before full API spend."""
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    slice_path = tmp_path / "calibration_slice.csv"
    slice_path.write_text(
        "\n".join(
            [
                "row_id,episode_type,task_id,retriever",
                "cal_001,clean_control,eha2r_000,bm25_top8",
                "cal_002,halupedia_or_generated_lore,eha2r_060,hygienic_combo_top8",
            ]
        )
        + "\n"
    )

    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
        modules=("C",),
        final_diagnostic_prompt="evidence_diagnostics_v7",
        calibration_slice=slice_path,
    )

    selected_pairs = {("eha2r_000", "bm25_top8"), ("eha2r_060", "hygienic_combo_top8")}
    assert len(records) == 2
    assert {(record.task_id, record.retriever) for record in records} == selected_pairs
    assert {record.strategy for record in records} == {"evidence_diagnostics_v7"}
    assert {record.prompt for record in records} == {"evidence_diagnostics_v7"}
    assert {(row["task_id"], row["retriever"]) for row in retrieval_rows} == selected_pairs


def test_phase2s_module_c_calibration_slice_accepts_v12_critical_risk_contract(tmp_path) -> None:
    """Phase 2S v12 must be runnable on the fixed C-only calibration path before any API spend."""
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    slice_path = tmp_path / "calibration_slice.csv"
    slice_path.write_text(
        "\n".join(
            [
                "row_id,episode_type,task_id,retriever",
                "cal_001,clean_control,eha2r_000,bm25_top8",
                "cal_002,citation_laundering_trace,eha2r_040,hygienic_combo_top8",
            ]
        )
        + "\n"
    )

    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
        modules=("C",),
        final_diagnostic_prompt="evidence_diagnostics_v12_critical_risk_contract",
        calibration_slice=slice_path,
    )
    rows = score_phase2s_run(records, phase2r["tasks"], phase2r["gold_documents"])

    assert len(records) == 2
    assert {record.strategy for record in records} == {"evidence_diagnostics_v12_critical_risk_contract"}
    assert {record.prompt for record in records} == {"evidence_diagnostics_v12_critical_risk_contract"}
    assert all("environment_observations" in record.prediction.model_dump() for record in records)
    assert {(row["task_id"], row["retriever"]) for row in retrieval_rows} == {
        ("eha2r_000", "bm25_top8"),
        ("eha2r_040", "hygienic_combo_top8"),
    }
    assert len(rows) == 2
    assert all("critical_risk_exact" not in row for row in rows)


def test_phase2s_module_c_calibration_slice_rejects_unknown_pairs(tmp_path) -> None:
    """Regression: a stale slice row should fail before running a misleading calibration job."""
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    slice_path = tmp_path / "bad_slice.csv"
    slice_path.write_text(
        "\n".join(
            [
                "row_id,episode_type,task_id,retriever",
                "cal_bad,clean_control,eha2r_missing,bm25_top8",
            ]
        )
        + "\n"
    )

    with pytest.raises(ValueError, match="unknown calibration slice task/retriever pairs"):
        run_phase2s_records(
            scope_dataset=scope,
            temporal_dataset=temporal,
            phase2r_dataset=phase2r,
            backend="heuristic",
            models=["heuristic-sim"],
            out_dir=tmp_path,
            max_output_tokens=3500,
            temperature=0.0,
            timeout_s=180.0,
            response_format="json_schema",
            cost_guard=CostGuard(),
            modules=("C",),
            calibration_slice=slice_path,
        )


def test_phase2s_gate_fails_when_route_then_answer_omits_compare_versions(tmp_path) -> None:
    """Regression: temporal repair must fail loudly if route_then_answer stops comparing versions."""
    scope = dataset_dict(generate_scope_diagnostic_dataset(seed=7319))
    temporal = dataset_dict(generate_temporal_routing_dataset(seed=8144))
    phase2r = dataset_dict(generate_phase2r_dataset(seed=6271))
    records, retrieval_rows = run_phase2s_records(
        scope_dataset=scope,
        temporal_dataset=temporal,
        phase2r_dataset=phase2r,
        backend="heuristic",
        models=["heuristic-sim"],
        out_dir=tmp_path,
        max_output_tokens=3500,
        temperature=0.0,
        timeout_s=180.0,
        response_format="json_schema",
        cost_guard=CostGuard(),
    )
    broken_records = [
        record.model_copy(update={"tool_calls": [], "tool_results": []})
        if record.module == "B" and record.strategy == "route_then_answer_v1"
        else record
        for record in records
    ]
    all_tasks = scope["tasks"] + temporal["tasks"] + phase2r["tasks"]
    all_gold = scope["gold_documents"] + temporal["gold_documents"] + phase2r["gold_documents"]
    rows = score_phase2s_run(broken_records, all_tasks, all_gold)
    gate = phase2s_gate(rows, retrieval_rows, broken_records)

    assert not gate.passed
    assert not gate.checks["B1_compare_versions_rate_on_temporal_at_least_0_75"]
    assert not gate.checks["B2_useful_compare_versions_rate_at_least_0_60"]


def test_phase2s_v2_prompt_makes_claim_first_calibration_explicit() -> None:
    """Phase 2S repair spec: v2 must constrain no-primary and partial-support false alarms."""
    system = phase2s_system_prompt("evidence_diagnostics_v2")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v2")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "evidence-diagnostics-v2" in system
    assert "First decide whether a current primary record directly supports or refutes the target claim" in system
    assert "Do not let generic risk labels reverse a supported claim" in system
    assert "No-primary is a last-resort diagnostic" in combined
    assert "Partial support requires a named missing claim component" in combined


def test_phase2s_v3_prompt_adds_risk_to_verdict_overrides() -> None:
    """Phase 2S repair spec: v3 must keep claim-first calibration without suppressing critical risks."""
    system = phase2s_system_prompt("evidence_diagnostics_v3")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v3")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "evidence-diagnostics-v3" in system
    assert "Risk-to-verdict override rules" in system
    assert "stale_evidence" in system and "must not be supported" in system
    assert "conflicting_evidence" in system and "refuted" in system
    assert "citation_laundering" in system and "insufficient" in system
    assert "partial_support" in system and "insufficient" in system
    assert "Generated lore or no primary source" in combined


def test_phase2s_v4_prompt_tightens_no_primary_diagnostic() -> None:
    """Phase 2S repair spec: v4 must not call refuting primary evidence no-primary."""
    system = phase2s_system_prompt("evidence_diagnostics_v4")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v4")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "evidence-diagnostics-v4" in system
    assert "Strict no-primary rule" in system
    assert "primary record can refute" in system
    assert "do not mark no_primary_source" in combined
    assert "no current primary record, audit report, signed record, database export, or direct primary document" in combined


def test_phase2s_v5_prompt_reports_visible_pollution_without_reversing_verdict() -> None:
    """Phase 2S repair spec: v5 must preserve supply-chain risk labels after claim-first calibration."""
    system = phase2s_system_prompt("evidence_diagnostics_v5")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v5")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "evidence-diagnostics-v5" in system
    assert "Polluted-environment risk reporting" in system
    assert "visible claim-bearing pollution" in system
    assert "include false_consensus" in system
    assert "include citation_laundering" in system
    assert "include stale_evidence" in system
    assert "Verdict discipline remains" in combined


def test_phase2s_v6_prompt_tightens_no_primary_and_risk_precision() -> None:
    """Phase 2S repair spec: v6 must not turn no-primary generated/repost evidence into refutation."""
    system = phase2s_system_prompt("evidence_diagnostics_v6")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v6")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "evidence-diagnostics-v6" in system
    assert "Precision and verdict-boundary repair" in system
    assert "supporting_evidence must include clean primary or direct refuting evidence" in system
    assert "verdict should be insufficient rather than refuted" in system
    assert "Generated lore precision" in combined
    assert "Partial-support precision" in combined
    assert "not every rejected background document needs every critical_risks label" in combined


def test_phase2s_v7_prompt_calibrates_specific_diagnostic_labels() -> None:
    """Phase 2S repair spec: v7 must separate same-root, stale, generated-lore, and partial risks."""
    system = phase2s_system_prompt("evidence_diagnostics_v7")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v7")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "evidence-diagnostics-v7" in system
    assert "Fine-grained diagnostic label calibration" in system
    assert "Do not mark stale_evidence for an ordinary pre-event planning note" in system
    assert "same-root repetition alone is false_consensus, not citation_laundering" in combined
    assert "Generated-lore recall" in combined
    assert "Partial-support recall" in combined
    assert "target quantifier, scope, or causal strength" in combined


def test_phase2s_v8_structural_schema_separates_observations_from_critical_risks() -> None:
    """Phase 2S v8 repair spec: visible pollution observations must not inflate critical risks."""
    schema = phase2s_prediction_json_schema("evidence_diagnostics_v8_structural")
    system = phase2s_system_prompt("evidence_diagnostics_v8_structural")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v8_structural")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "environment_observations" in schema["required"]
    assert "environment_observations" in schema["properties"]
    assert "visible_reposts_or_same_root_repetition" in schema["properties"]["environment_observations"]["properties"]
    assert "evidence-diagnostics-v8-structural" in system
    assert "environment_observations may acknowledge all visible pollution" in system
    assert "critical_risks must stay sparse" in system
    assert "Observation is not the same as verdict-critical risk" in combined
    assert "Clean controls with clean primary support should keep critical_risks empty" in combined


def test_phase2s_v8_parser_accepts_environment_observations_and_preserves_legacy_outputs() -> None:
    """Regression: v8 structural outputs add observations without breaking old Phase 2S JSON."""
    legacy = """
    {
      "claim_verdict": "supported",
      "confidence": 0.9,
      "evidence_diagnostics": {
        "has_primary_support": "yes",
        "primary_support_is_current": "yes",
        "evidence_has_conflict": "no",
        "support_is_partial": "no",
        "sources_are_independent": "yes",
        "citation_laundering_detected": "no",
        "generated_lore_detected": "no",
        "no_primary_source_detected": "no"
      },
      "critical_risks": [],
      "supporting_evidence": ["doc_001"],
      "rejected_evidence": ["doc_002"],
      "verification_ledger": [],
      "answer": "Supported by the primary record."
    }
    """
    structural = """
    {
      "claim_verdict": "supported",
      "confidence": 0.9,
      "environment_observations": {
        "visible_stale_or_superseded_material": "no",
        "visible_conflicting_material": "no",
        "visible_generated_or_synthetic_lore": "no",
        "visible_reposts_or_same_root_repetition": "yes",
        "visible_citation_chain_problem": "no",
        "visible_partial_or_scope_limited_support": "no"
      },
      "evidence_diagnostics": {
        "has_primary_support": "yes",
        "primary_support_is_current": "yes",
        "evidence_has_conflict": "no",
        "support_is_partial": "no",
        "sources_are_independent": "yes",
        "citation_laundering_detected": "no",
        "generated_lore_detected": "no",
        "no_primary_source_detected": "no"
      },
      "critical_risks": [],
      "supporting_evidence": ["doc_001"],
      "rejected_evidence": ["doc_002"],
      "verification_ledger": [],
      "answer": "Supported by the primary record."
    }
    """

    assert parse_phase2s_prediction_json(legacy).environment_observations == {}
    prediction = parse_phase2s_prediction_json(structural)
    assert prediction.environment_observations["visible_reposts_or_same_root_repetition"] == "yes"
    assert prediction.critical_risks == []


def test_phase2s_v9_structural_prompt_keeps_true_blockers_in_critical_risks() -> None:
    """Phase 2S v9 repair spec: structural observations must not hide true critical risks."""
    schema = phase2s_prediction_json_schema("evidence_diagnostics_v9_structural_recall")
    system = phase2s_system_prompt("evidence_diagnostics_v9_structural_recall")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v9_structural_recall")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "environment_observations" in schema["required"]
    assert "evidence-diagnostics-v9-structural-recall" in system
    assert "Structural recall repair" in system
    assert "include false_consensus in critical_risks" in system
    assert "include citation_laundering in critical_risks" in system
    assert "include partial_support rather than conflicting_evidence" in system
    assert "do not hide true verdict blockers in environment_observations" in combined


def test_phase2s_v10_structural_contract_defines_risk_decision_table() -> None:
    """Phase 2S v10 repair spec: critical risks follow a narrow decision table."""
    schema = phase2s_prediction_json_schema("evidence_diagnostics_v10_structural_contract")
    system = phase2s_system_prompt("evidence_diagnostics_v10_structural_contract")
    messages = build_phase2s_messages("Is the target claim currently supported?", [], prompt="evidence_diagnostics_v10_structural_contract")
    combined = "\n\n".join(message["content"] for message in messages)

    assert "environment_observations" in schema["required"]
    assert "evidence-diagnostics-v10-structural-contract" in system
    assert "Structural critical-risk contract" in system
    assert "false_consensus: include only when repeated same-root summaries dominate apparent support" in system
    assert "citation_laundering: include only when a visible cited target" in system
    assert "partial_support: include when clean evidence supports a weaker component" in system
    assert "do not replace it with conflicting_evidence or citation_laundering" in system
    assert "do not use false_consensus for citation-chain failures" in combined
    assert "reserve for clean primary or direct evidence that contradicts the target claim" in combined


def test_phase2s_v11_role_disciplined_contract_hard_gates_supporting_evidence() -> None:
    """Phase 2S v11 repair spec: supporting evidence must stay clean and verdict-direct."""
    schema = phase2s_prediction_json_schema("evidence_diagnostics_v11_role_disciplined_contract")
    system = phase2s_system_prompt("evidence_diagnostics_v11_role_disciplined_contract")
    messages = build_phase2s_messages(
        "Is the target claim currently supported?",
        [],
        prompt="evidence_diagnostics_v11_role_disciplined_contract",
    )
    combined = "\n\n".join(message["content"] for message in messages)

    assert "environment_observations" in schema["required"]
    assert "evidence-diagnostics-v11-role-disciplined-contract" in system
    assert "Structural evidence-role discipline contract" in system
    assert "supporting_evidence hard gate" in system
    assert "Never put pollutant roots, reposts, generated/wiki-like pages" in system
    assert "leave supporting_evidence empty" in system
    assert "include both false_consensus and conflicting_evidence" in system
    assert "include both citation_laundering and conflicting_evidence" in system
    assert "use stale_evidence rather than conflicting_evidence" in combined
    assert "use partial_support rather than conflicting_evidence or citation_laundering" in combined


def test_phase2s_v12_critical_risk_contract_targets_exact_label_boundaries() -> None:
    """Phase 2S v12 repair spec: critical-risk labels need positive and negative boundaries."""
    schema = phase2s_prediction_json_schema("evidence_diagnostics_v12_critical_risk_contract")
    system = phase2s_system_prompt("evidence_diagnostics_v12_critical_risk_contract")
    messages = build_phase2s_messages(
        "Is the target claim currently supported?",
        [],
        prompt="evidence_diagnostics_v12_critical_risk_contract",
    )
    combined = "\n\n".join(message["content"] for message in messages)

    assert "environment_observations" in schema["required"]
    assert "evidence-diagnostics-v12-critical-risk-contract" in system
    assert "Critical-risk repair audit contract" in system
    assert "positive rule and a negative rule" in system
    assert "false_consensus positive" in system
    assert "citation_laundering positive" in system
    assert "partial_support positive" in system
    assert "remove any critical_risks label whose only basis is a visible rejected pollutant" in system
    assert "Optimize for exact critical-risk rows" in combined


def test_phase2s_prompt_selection_prefers_v12_when_present() -> None:
    rows = [
        {"module": "C", "strategy": "evidence_diagnostics_v11_role_disciplined_contract"},
        {"module": "C", "strategy": "evidence_diagnostics_v12_critical_risk_contract"},
    ]

    assert selected_module_c_prompt(rows) == "evidence_diagnostics_v12_critical_risk_contract"


def test_phase2s_structural_observation_scoring_uses_visible_gold_documents() -> None:
    """Phase 2S structural scoring must separate observed pollution from critical risks."""
    _, tasks, documents, gold_documents, _ = generate_phase2r_dataset(seed=6271)
    task = next(task for task in tasks if task.episode_type == "clean_control")
    episode_docs = [doc for doc in documents if doc.task_id == task.task_id]
    episode_gold = [gold for gold in gold_documents if gold.task_id == task.task_id]
    retrieved_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, "bm25_top8")]
    final_doc_ids = [doc.doc_id for doc in retrieved_docs]

    prediction = Phase2SPrediction(
        claim_verdict="supported",
        confidence=0.95,
        environment_observations={
            "visible_stale_or_superseded_material": "yes",
            "visible_conflicting_material": "no",
            "visible_generated_or_synthetic_lore": "no",
            "visible_reposts_or_same_root_repetition": "yes",
            "visible_citation_chain_problem": "no",
            "visible_partial_or_scope_limited_support": "no",
        },
        evidence_diagnostics=EvidenceDiagnostics(
            has_primary_support="yes",
            primary_support_is_current="yes",
            evidence_has_conflict="no",
            support_is_partial="no",
            sources_are_independent="yes",
            citation_laundering_detected="no",
            generated_lore_detected="no",
            no_primary_source_detected="no",
        ),
        critical_risks=[],
        supporting_evidence=[f"{task.task_id}_primary_a", f"{task.task_id}_primary_b"],
        rejected_evidence=[f"{task.task_id}_pollutant_root", f"{task.task_id}_repost_00"],
        verification_ledger=[],
        answer="Supported by clean primary records; visible old/reposted pollutants are rejected.",
    )
    record = Phase2SRunRecord(
        task_id=task.task_id,
        module="C",
        dataset="EHA-v2R-stress-pilot",
        model="unit-test",
        retriever="bm25_top8",
        strategy="evidence_diagnostics_v8_structural",
        prompt="evidence_diagnostics_v8_structural",
        backend="heuristic",
        initial_doc_ids=final_doc_ids,
        final_doc_ids=final_doc_ids,
        prediction=prediction,
        parse_success=True,
    )

    row = score_phase2s_record(record, task, gold_by_doc(episode_gold))

    assert row["predicted_critical_risks"] == ""
    assert row["gold_visible_stale_or_superseded_material"] == 1.0
    assert row["pred_visible_stale_or_superseded_material"] == 1.0
    assert row["visible_stale_or_superseded_material_tp"] == 1.0
    assert row["gold_visible_reposts_or_same_root_repetition"] == 1.0
    assert row["pred_visible_reposts_or_same_root_repetition"] == 1.0
    assert row["visible_reposts_or_same_root_repetition_tp"] == 1.0
    assert row["gold_critical_stale_evidence"] == 0.0
    assert row["pred_critical_stale_evidence"] == 0.0
    assert row["critical_stale_evidence_fp"] == 0.0
    critical_rows = critical_risk_confusion_by_flag([row])
    stale_row = next(item for item in critical_rows if item["risk"] == "stale_evidence")
    assert stale_row["tp"] == 0
    assert stale_row["fp"] == 0
    assert critical_risk_macro_f1([row]) == 1.0


def test_phase2s_support_role_flags_contaminated_support_without_changing_risk_score() -> None:
    """Support-role scoring is separate from direct critical-risk label scoring."""
    _, tasks, _, gold_documents, _ = generate_phase2r_dataset(seed=6271)
    task = next(task for task in tasks if task.episode_type == "clean_control")
    episode_gold = [gold for gold in gold_documents if gold.task_id == task.task_id]
    final_doc_ids = [gold.doc_id for gold in episode_gold]
    polluted_doc_id = f"{task.task_id}_pollutant_root"

    prediction = Phase2SPrediction(
        claim_verdict="supported",
        confidence=0.95,
        environment_observations={},
        evidence_diagnostics=EvidenceDiagnostics(
            has_primary_support="yes",
            primary_support_is_current="yes",
            evidence_has_conflict="no",
            support_is_partial="no",
            sources_are_independent="yes",
            citation_laundering_detected="no",
            generated_lore_detected="no",
            no_primary_source_detected="no",
        ),
        critical_risks=[],
        supporting_evidence=[f"{task.task_id}_primary_a", polluted_doc_id],
        rejected_evidence=[],
        verification_ledger=[],
        answer="Correct claim verdict, but one polluted source is incorrectly listed as support.",
    )
    record = Phase2SRunRecord(
        task_id=task.task_id,
        module="C",
        dataset="EHA-v2R-stress-pilot",
        model="unit-test",
        retriever="bm25_top8",
        strategy="evidence_diagnostics_v11_role_disciplined_contract",
        prompt="evidence_diagnostics_v11_role_disciplined_contract",
        backend="heuristic",
        initial_doc_ids=final_doc_ids,
        final_doc_ids=final_doc_ids,
        prediction=prediction,
        parse_success=True,
    )

    row = score_phase2s_record(record, task, gold_by_doc(episode_gold))

    assert row["claim_accuracy"] == 1.0
    assert row["support_role_valid"] == 0.0
    assert row["support_role_clean_only"] == 0.0
    assert row["support_role_verdict_direct"] == 1.0
    assert row["support_role_has_contaminated_doc"] == 1.0
    assert row["support_role_contaminated_doc_ids"] == polluted_doc_id
    assert critical_risk_macro_f1([row]) == 1.0


def test_phase2s_support_role_can_pass_when_critical_risks_are_missing() -> None:
    """Clean verdict-direct support must not mask omitted direct critical-risk labels."""
    _, tasks, _, gold_documents, _ = generate_phase2r_dataset(seed=6271)
    task = next(task for task in tasks if task.episode_type == "false_consensus_stress")
    episode_gold = [gold for gold in gold_documents if gold.task_id == task.task_id]
    final_doc_ids = [gold.doc_id for gold in episode_gold]

    prediction = Phase2SPrediction(
        claim_verdict="refuted",
        confidence=0.95,
        environment_observations={},
        evidence_diagnostics=EvidenceDiagnostics(
            has_primary_support="yes",
            primary_support_is_current="yes",
            evidence_has_conflict="yes",
            support_is_partial="no",
            sources_are_independent="no",
            citation_laundering_detected="no",
            generated_lore_detected="no",
            no_primary_source_detected="no",
        ),
        critical_risks=[],
        supporting_evidence=[f"{task.task_id}_primary_a", f"{task.task_id}_primary_b"],
        rejected_evidence=[f"{task.task_id}_pollutant_root"],
        verification_ledger=[],
        answer="The support list is clean, but the false-consensus and conflict risk labels are missing.",
    )
    record = Phase2SRunRecord(
        task_id=task.task_id,
        module="C",
        dataset="EHA-v2R-stress-pilot",
        model="unit-test",
        retriever="bm25_top8",
        strategy="evidence_diagnostics_v11_role_disciplined_contract",
        prompt="evidence_diagnostics_v11_role_disciplined_contract",
        backend="heuristic",
        initial_doc_ids=final_doc_ids,
        final_doc_ids=final_doc_ids,
        prediction=prediction,
        parse_success=True,
    )

    row = score_phase2s_record(record, task, gold_by_doc(episode_gold))

    assert row["claim_accuracy"] == 1.0
    assert row["support_role_valid"] == 1.0
    assert row["support_role_clean_only"] == 1.0
    assert row["support_role_verdict_direct"] == 1.0
    assert row["critical_conflicting_evidence_fn"] == 1.0
    assert row["critical_false_consensus_fn"] == 1.0
    assert critical_risk_macro_f1([row]) < 1.0


def test_phase2s_routing_prompt_forces_tools_on_same_root_repetition() -> None:
    """Regression: saturated same-root evidence should not let route_then_answer skip tools."""
    messages = phase2s_routing_messages("Did the repeated claim hold?", [])
    combined = "\n\n".join(message["content"] for message in messages)

    assert "repeat the same claim wording" in combined
    assert "do not return an empty tool list" in combined
    assert "request_primary_record and search_contradictions" in combined
    assert "trace_citation on the root" in combined
    assert "primary search returns no documents" in combined


def dataset_dict(dataset_tuple):
    manifest, tasks, documents, gold_documents, edges = dataset_tuple
    return {
        "manifest": manifest,
        "tasks": tasks,
        "documents": documents,
        "gold_documents": gold_documents,
        "edges": edges,
    }
