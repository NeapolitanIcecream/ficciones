from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import typer
from loguru import logger
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard
from .phase2_retrieval import compute_retrieval_metrics_for_tasks, retrieve
from .phase2_run import Phase2OpenAIJsonRunner, append_tool_documents, execute_tool_calls, normalize_doc_refs, split_csv, write_artifacts
from .phase2r_prompts import build_phase2r_messages, parse_phase2r_prediction_json, phase2r_prediction_json_schema
from .phase2r_run import forced_triage_calls, run_tool_plan as run_legacy_tool_plan, select_hard_subset
from .phase2s_prompts import (
    build_phase2s_messages,
    parse_phase2s_prediction_json,
    parse_phase2s_routing_json,
    phase2_prediction_to_phase2s,
    phase2s_prediction_json_schema,
    phase2s_routing_json_schema,
    phase2s_routing_messages,
)
from .phase2s_scoring import phase2s_gate, score_phase2s_run
from .report import write_csv
from .schemas import (
    AgentDocument,
    EvidenceDiagnostics,
    GoldDocument,
    Phase2Prediction,
    Phase2SRunRecord,
    Phase2SPrediction,
    Task,
    ToolCall,
    VerificationLedgerEntry,
    by_task,
    docs_by_id,
    load_dataset,
    model_to_dict,
    write_json,
    write_jsonl,
)


app = typer.Typer(add_completion=False, help="Run EHA Phase 2S repair experiments.")
console = Console()
log = logger.bind(module="eha.phase2s_run")

MODULE_C_RETRIEVERS = ("bm25_top8", "primary_preserve_top8", "hygienic_combo_top8")


def gold_diagnostics(task: Task) -> EvidenceDiagnostics:
    from .phase2s_scoring import derived_gold_diagnostics

    return EvidenceDiagnostics.model_validate(derived_gold_diagnostics(task))


def gold_risks(task: Task) -> List[str]:
    from .phase2s_scoring import derived_gold_risks

    return derived_gold_risks(task)


def selected_support_docs(task: Task, docs: Sequence[AgentDocument], gold_docs: Sequence[GoldDocument]) -> tuple[List[str], List[str]]:
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    doc_ids = {doc.doc_id for doc in docs}
    support = [doc_id for doc_id in task.gold.primary_support if doc_id in doc_ids]
    contaminants = [doc.doc_id for doc in docs if doc.doc_id in gold_by_id and gold_by_id[doc.doc_id].is_contaminated]
    return support, contaminants


def heuristic_phase2s_prediction(
    task: Task,
    docs: Sequence[AgentDocument],
    gold_docs: Sequence[GoldDocument],
    *,
    module: str,
    retriever: str,
    strategy: str,
    prompt: str,
    tool_results: Sequence[Mapping[str, Any]],
) -> Phase2SPrediction:
    support, contaminants = selected_support_docs(task, docs, gold_docs)
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    false_sources = [doc.doc_id for doc in docs if doc.doc_id in gold_by_id and gold_by_id[doc.doc_id].stance == "supports_false_claim"]
    pollutant_saturation = len(false_sources) / len(docs) if docs else 0.0
    hp_fooled = (
        module == "C"
        and task.episode_type == "false_consensus_stress"
        and retriever == "bm25_top8"
        and strategy == "evidence_diagnostics_v1"
        and not task.primary_visibility_under_bm25_top8
        and task.duplicate_count >= 20
        and pollutant_saturation >= 0.75
    )
    if prompt == "evidence_graph_v3":
        legacy = Phase2Prediction(
            claim_verdict=task.gold.verdict if not hp_fooled else ("supported" if task.gold.verdict != "supported" else "refuted"),  # type: ignore[arg-type]
            scope_tag=task.gold.scope_tag,
            confidence=0.78 if not hp_fooled else 0.72,
            supporting_evidence=support[:2] if not hp_fooled else false_sources[:3],
            rejected_evidence=contaminants[:5] if not hp_fooled else support[:1],
            predicted_dependency_edges=[],
            answer=task.gold.answer_brief,
        )
        return phase2_prediction_to_phase2s(legacy)

    if hp_fooled:
        return Phase2SPrediction(
            claim_verdict="supported" if task.gold.verdict != "supported" else "refuted",  # type: ignore[arg-type]
            confidence=0.72,
            evidence_diagnostics=EvidenceDiagnostics.model_validate(
                {
                    "has_primary_support": "no",
                    "primary_support_is_current": "uncertain",
                    "evidence_has_conflict": "no",
                    "support_is_partial": "no",
                    "sources_are_independent": "no",
                    "citation_laundering_detected": "no",
                    "generated_lore_detected": "no",
                    "no_primary_source_detected": "no",
                }
            ),
            critical_risks=["false_consensus"],  # type: ignore[list-item]
            supporting_evidence=false_sources[:3],
            rejected_evidence=support[:1],
            verification_ledger=[
                VerificationLedgerEntry(
                    risk_checked="source_independence",
                    method="read_docs",
                    evidence=false_sources[:3],
                    finding="Repeated summaries appeared consistent but came from same-root evidence.",
                    effect_on_verdict="supports",
                )
            ],
            answer="The repeated retrieved summaries appear to support the claim.",
        )

    ledger_method = "read_docs"
    ledger_evidence = support[:2]
    if any(call_key in result for result in tool_results for call_key in ("versions", "documents", "trace")):
        if any("versions" in result for result in tool_results):
            ledger_method = "compare_versions"
            ledger_evidence = list(dict.fromkeys(ledger_evidence + [doc_id for result in tool_results for doc_id in tool_doc_ids(result, "versions")]))[:5]
        elif any("trace" in result for result in tool_results):
            ledger_method = "trace_citation"
    if task.gold.verdict == "insufficient":
        ledger_evidence = ledger_evidence or contaminants[:3]
    return Phase2SPrediction(
        claim_verdict=task.gold.verdict if task.gold.verdict != "mixed" else "insufficient",  # type: ignore[arg-type]
        confidence=0.76 if task.gold.verdict != "insufficient" else 0.62,
        evidence_diagnostics=gold_diagnostics(task),
        critical_risks=gold_risks(task),  # type: ignore[arg-type]
        supporting_evidence=support[:2] if task.gold.verdict != "insufficient" else [],
        rejected_evidence=contaminants[:5],
        verification_ledger=[
            VerificationLedgerEntry(
                risk_checked="temporal_staleness" if "stale_evidence" in gold_risks(task) else "primary_support",
                method=ledger_method,  # type: ignore[arg-type]
                evidence=ledger_evidence,
                finding="The evidence diagnostics match the provided corpus and tool results.",
                effect_on_verdict="makes_insufficient" if task.gold.verdict == "insufficient" else "refutes" if task.gold.verdict == "refuted" else "supports",
            )
        ],
        answer=task.gold.answer_brief,
    )


def tool_doc_ids(result: Mapping[str, Any], key: str) -> List[str]:
    value = result.get(key)
    if not isinstance(value, list):
        return []
    return [str(item["doc_id"]) for item in value if isinstance(item, Mapping) and isinstance(item.get("doc_id"), str)]


def normalize_phase2s_prediction(prediction: Phase2SPrediction, allowed_doc_ids: Sequence[str]) -> Phase2SPrediction:
    ledger = [
        entry.model_copy(update={"evidence": normalize_doc_refs(entry.evidence, allowed_doc_ids)})
        for entry in prediction.verification_ledger
    ]
    return prediction.model_copy(
        update={
            "supporting_evidence": normalize_doc_refs(prediction.supporting_evidence, allowed_doc_ids),
            "rejected_evidence": normalize_doc_refs(prediction.rejected_evidence, allowed_doc_ids),
            "verification_ledger": ledger,
        }
    )


def run_final_prediction(
    *,
    backend: str,
    runner: Optional[Phase2OpenAIJsonRunner],
    cost_guard: CostGuard,
    model: str,
    task: Task,
    final_docs: Sequence[AgentDocument],
    gold_docs: Sequence[GoldDocument],
    tool_results: Sequence[Mapping[str, Any]],
    module: str,
    dataset: str,
    retriever: str,
    strategy: str,
    prompt: str,
    out_dir: Path,
    max_output_tokens: int,
    temperature: float,
) -> Tuple[Phase2SPrediction, bool, Optional[str], Dict[str, Any], float, Optional[str], Optional[str]]:
    if backend == "heuristic":
        return (
            heuristic_phase2s_prediction(
                task,
                final_docs,
                gold_docs,
                module=module,
                retriever=retriever,
                strategy=strategy,
                prompt=prompt,
                tool_results=tool_results,
            ),
            True,
            None,
            {},
            0.0,
            None,
            None,
        )
    assert runner is not None
    if prompt == "evidence_graph_v3":
        messages = build_phase2r_messages(task.question, final_docs, tool_results)
        schema = phase2r_prediction_json_schema()
        schema_name = "eha_phase2r_prediction"
    else:
        messages = build_phase2s_messages(task.question, final_docs, tool_results)
        schema = phase2s_prediction_json_schema()
        schema_name = "eha_phase2s_prediction"
    cost_guard.before_call(model, json.dumps(messages, ensure_ascii=False), max_output_tokens)
    response_text, usage, used_format = runner.complete(
        model=model,
        messages=messages,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        schema_name=schema_name,
        schema=schema,
    )
    prompt_path, response_path = write_artifacts(
        out_dir,
        task_id=task.task_id,
        model=model,
        retriever=retriever,
        strategy=f"{module}_{strategy}_{prompt}",
        suffix="final",
        messages=messages,
        response_text=response_text,
        usage=usage,
        response_format=used_format,
    )
    try:
        if prompt == "evidence_graph_v3":
            phase2_prediction = parse_phase2r_prediction_json(response_text)
            prediction = phase2_prediction_to_phase2s(phase2_prediction)
        else:
            prediction = parse_phase2s_prediction_json(response_text)
        prediction = normalize_phase2s_prediction(prediction, [doc.doc_id for doc in final_docs])
        return prediction, True, None, usage, cost_guard.after_call(model, usage), prompt_path, response_path
    except Exception as exc:  # noqa: BLE001
        prediction = Phase2SPrediction(
            claim_verdict="insufficient",
            confidence=0.0,
            evidence_diagnostics=EvidenceDiagnostics.model_validate(
                {
                    "has_primary_support": "uncertain",
                    "primary_support_is_current": "uncertain",
                    "evidence_has_conflict": "uncertain",
                    "support_is_partial": "uncertain",
                    "sources_are_independent": "uncertain",
                    "citation_laundering_detected": "uncertain",
                    "generated_lore_detected": "uncertain",
                    "no_primary_source_detected": "uncertain",
                }
            ),
            critical_risks=[],
            supporting_evidence=[],
            rejected_evidence=[],
            verification_ledger=[],
            answer="The model response could not be parsed as the required Phase 2S JSON object.",
        )
        return prediction, False, str(exc), usage, cost_guard.after_call(model, usage), prompt_path, response_path


def default_tool_args(task: Task, call: ToolCall, initial_docs: Sequence[AgentDocument]) -> ToolCall:
    cited_doc = next((doc for doc in initial_docs if doc.visible_citations), initial_docs[0] if initial_docs else None)
    args = dict(call.args)
    if call.tool == "compare_versions":
        args.setdefault("entity", "Novalis Robotics")
        args.setdefault("topic", task.question)
        args.setdefault("top_n", 5)
    elif call.tool == "request_primary_record":
        args.setdefault("claim_text", task.question)
        args.setdefault("entity", "Novalis Robotics")
        args.setdefault("date_range", "2023 2025")
        args.setdefault("top_n", 3)
    elif call.tool == "trace_citation":
        args.setdefault("doc_id", cited_doc.doc_id if cited_doc else "")
        args.setdefault("depth", 2)
    elif call.tool == "search_contradictions":
        args.setdefault("claim_text", task.question)
        args.setdefault("top_n", 5)
    return ToolCall(tool=call.tool, args=args)


def forced_compare_calls(task: Task) -> List[ToolCall]:
    return [
        ToolCall(tool="compare_versions", args={"entity": "Novalis Robotics", "topic": task.question, "top_n": 5}),
        ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2023 2025", "top_n": 3}),
    ]


def heuristic_route_calls(task: Task, initial_docs: Sequence[AgentDocument]) -> List[ToolCall]:
    if task.episode_type != "non_temporal_control":
        return forced_compare_calls(task)
    return [ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3})]


def run_route_then_answer(
    *,
    backend: str,
    runner: Optional[Phase2OpenAIJsonRunner],
    cost_guard: CostGuard,
    model: str,
    task: Task,
    initial_docs: Sequence[AgentDocument],
    episode_docs: Sequence[AgentDocument],
    out_dir: Path,
    temperature: float,
) -> tuple[List[ToolCall], List[Dict[str, Any]], bool, Dict[str, Any]]:
    if backend == "heuristic":
        calls = heuristic_route_calls(task, initial_docs)
        return calls, execute_tool_calls(calls, episode_docs), True, {}
    assert runner is not None
    messages = phase2s_routing_messages(task.question, initial_docs)
    cost_guard.before_call(model, json.dumps(messages, ensure_ascii=False), 1200)
    response_text, usage, used_format = runner.complete(
        model=model,
        messages=messages,
        max_output_tokens=1200,
        temperature=temperature,
        schema_name="eha_phase2s_tool_routing",
        schema=phase2s_routing_json_schema(),
        mode="json_schema",
    )
    write_artifacts(
        out_dir,
        task_id=task.task_id,
        model=model,
        retriever="bm25_top8",
        strategy="route_then_answer_v1",
        suffix="tool",
        messages=messages,
        response_text=response_text,
        usage=usage,
        response_format=used_format,
    )
    cost_guard.after_call(model, usage)
    try:
        calls, _diagnosis = parse_phase2s_routing_json(response_text)
        repaired = [default_tool_args(task, call, initial_docs) for call in calls[:3]]
        return repaired, execute_tool_calls(repaired, episode_docs), True, usage
    except Exception:
        return [], [], False, usage


def append_record(
    records: List[Phase2SRunRecord],
    *,
    task: Task,
    module: str,
    dataset: str,
    model: str,
    retriever: str,
    strategy: str,
    prompt: str,
    backend: str,
    initial_docs: Sequence[AgentDocument],
    final_docs: Sequence[AgentDocument],
    prediction: Phase2SPrediction,
    parse_success: bool,
    tool_parse_success: bool,
    tool_calls: Sequence[ToolCall],
    tool_results: Sequence[Mapping[str, Any]],
    parse_error: Optional[str],
    usage: Mapping[str, Any],
    cost_usd: float,
    prompt_path: Optional[str],
    response_path: Optional[str],
) -> None:
    records.append(
        Phase2SRunRecord(
            task_id=task.task_id,
            module=module,
            dataset=dataset,
            model=model,
            retriever=retriever,
            strategy=strategy,
            prompt=prompt,
            backend=backend,
            initial_doc_ids=[doc.doc_id for doc in initial_docs],
            final_doc_ids=[doc.doc_id for doc in final_docs],
            prediction=prediction,
            parse_success=parse_success,
            tool_parse_success=tool_parse_success,
            tool_calls=list(tool_calls),
            tool_results=[dict(result) for result in tool_results],
            parse_error=parse_error,
            usage=dict(usage),
            cost_usd=cost_usd,
            prompt_path=prompt_path,
            response_path=response_path,
        )
    )


def run_module_a(
    *,
    records: List[Phase2SRunRecord],
    tasks: Sequence[Task],
    docs_by_task_map: Mapping[str, List[AgentDocument]],
    gold_by_task: Mapping[str, List[GoldDocument]],
    backend: str,
    runner: Optional[Phase2OpenAIJsonRunner],
    cost_guard: CostGuard,
    models: Sequence[str],
    out_dir: Path,
    max_output_tokens: int,
    temperature: float,
) -> None:
    for model in models:
        for task in tasks:
            docs = docs_by_task_map[task.task_id][:8]
            gold_docs = gold_by_task[task.task_id]
            for prompt in ("evidence_graph_v3", "evidence_diagnostics_v1"):
                prediction, parse_success, parse_error, usage, cost_usd, prompt_path, response_path = run_final_prediction(
                    backend=backend,
                    runner=runner,
                    cost_guard=cost_guard,
                    model=model,
                    task=task,
                    final_docs=docs,
                    gold_docs=gold_docs,
                    tool_results=[],
                    module="A",
                    dataset="EHA-v2S-scope-diagnostic",
                    retriever="provided_relevant_docs",
                    strategy=prompt,
                    prompt=prompt,
                    out_dir=out_dir,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                append_record(
                    records,
                    task=task,
                    module="A",
                    dataset="EHA-v2S-scope-diagnostic",
                    model=model,
                    retriever="provided_relevant_docs",
                    strategy=prompt,
                    prompt=prompt,
                    backend=backend,
                    initial_docs=docs,
                    final_docs=docs,
                    prediction=prediction,
                    parse_success=parse_success,
                    tool_parse_success=True,
                    tool_calls=[],
                    tool_results=[],
                    parse_error=parse_error,
                    usage=usage,
                    cost_usd=cost_usd,
                    prompt_path=prompt_path,
                    response_path=response_path,
                )
                log.info("phase2s module=A task={task_id} model={model} prompt={prompt}", task_id=task.task_id, model=model, prompt=prompt)


def run_module_b(
    *,
    records: List[Phase2SRunRecord],
    tasks: Sequence[Task],
    docs_by_task_map: Mapping[str, List[AgentDocument]],
    gold_by_task: Mapping[str, List[GoldDocument]],
    backend: str,
    runner: Optional[Phase2OpenAIJsonRunner],
    cost_guard: CostGuard,
    models: Sequence[str],
    out_dir: Path,
    max_output_tokens: int,
    temperature: float,
) -> None:
    for model in models:
        for task in tasks:
            episode_docs = docs_by_task_map[task.task_id]
            episode_gold = gold_by_task[task.task_id]
            episode_docs_by_id = docs_by_id(episode_docs)
            bm25_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, "bm25_top8")]
            combo_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, "hygienic_combo_top8")]
            specs: List[tuple[str, str, List[AgentDocument], List[ToolCall], List[Dict[str, Any]], bool]] = []
            specs.append(("hygienic_combo_top8", "static_hygienic_combo", combo_docs, [], [], True))
            calls = forced_compare_calls(task)
            results = execute_tool_calls(calls, episode_docs)
            specs.append(("bm25_top8", "forced_compare_versions", append_tool_documents(bm25_docs, episode_docs_by_id, results), calls, results, True))
            calls, results, tool_parse_success, _usage = run_route_then_answer(
                backend=backend,
                runner=runner,
                cost_guard=cost_guard,
                model=model,
                task=task,
                initial_docs=bm25_docs,
                episode_docs=episode_docs,
                out_dir=out_dir,
                temperature=temperature,
            )
            specs.append(("bm25_top8", "route_then_answer_v1", append_tool_documents(bm25_docs, episode_docs_by_id, results), calls, results, tool_parse_success))
            calls, results, tool_parse_success, _usage = run_legacy_tool_plan(
                backend=backend,
                runner=runner,
                cost_guard=cost_guard,
                model=model,
                task=task,
                initial_docs=bm25_docs,
                episode_docs=episode_docs,
                out_dir=out_dir,
                temperature=temperature,
            )
            specs.append(("bm25_top8", "tool_agent_3call_policy", append_tool_documents(bm25_docs, episode_docs_by_id, results), calls, results, tool_parse_success))

            for retriever, strategy, final_docs, calls, results, tool_parse_success in specs:
                prediction, parse_success, parse_error, usage, cost_usd, prompt_path, response_path = run_final_prediction(
                    backend=backend,
                    runner=runner,
                    cost_guard=cost_guard,
                    model=model,
                    task=task,
                    final_docs=final_docs,
                    gold_docs=episode_gold,
                    tool_results=results,
                    module="B",
                    dataset="EHA-v2S-temporal-routing",
                    retriever=retriever,
                    strategy=strategy,
                    prompt="evidence_diagnostics_v1",
                    out_dir=out_dir,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                append_record(
                    records,
                    task=task,
                    module="B",
                    dataset="EHA-v2S-temporal-routing",
                    model=model,
                    retriever=retriever,
                    strategy=strategy,
                    prompt="evidence_diagnostics_v1",
                    backend=backend,
                    initial_docs=bm25_docs if retriever == "bm25_top8" else combo_docs,
                    final_docs=final_docs,
                    prediction=prediction,
                    parse_success=parse_success,
                    tool_parse_success=tool_parse_success,
                    tool_calls=calls,
                    tool_results=results,
                    parse_error=parse_error,
                    usage=usage,
                    cost_usd=cost_usd,
                    prompt_path=prompt_path,
                    response_path=response_path,
                )
            log.info("phase2s module=B task={task_id} model={model}", task_id=task.task_id, model=model)


def run_module_c(
    *,
    records: List[Phase2SRunRecord],
    tasks: Sequence[Task],
    docs_by_task_map: Mapping[str, List[AgentDocument]],
    gold_by_task: Mapping[str, List[GoldDocument]],
    backend: str,
    runner: Optional[Phase2OpenAIJsonRunner],
    cost_guard: CostGuard,
    models: Sequence[str],
    out_dir: Path,
    max_output_tokens: int,
    temperature: float,
) -> List[Dict[str, Any]]:
    retrieval_rows = compute_retrieval_metrics_for_tasks(tasks, docs_by_task_map, gold_by_task, MODULE_C_RETRIEVERS)
    write_csv(out_dir / "retrieval_metrics.csv", retrieval_rows)
    for model in models:
        for task in tasks:
            episode_docs = docs_by_task_map[task.task_id]
            episode_gold = gold_by_task[task.task_id]
            for retriever in MODULE_C_RETRIEVERS:
                retrieved_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, retriever)]
                prediction, parse_success, parse_error, usage, cost_usd, prompt_path, response_path = run_final_prediction(
                    backend=backend,
                    runner=runner,
                    cost_guard=cost_guard,
                    model=model,
                    task=task,
                    final_docs=retrieved_docs,
                    gold_docs=episode_gold,
                    tool_results=[],
                    module="C",
                    dataset="EHA-v2R-stress-pilot",
                    retriever=retriever,
                    strategy="evidence_diagnostics_v1",
                    prompt="evidence_diagnostics_v1",
                    out_dir=out_dir,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                append_record(
                    records,
                    task=task,
                    module="C",
                    dataset="EHA-v2R-stress-pilot",
                    model=model,
                    retriever=retriever,
                    strategy="evidence_diagnostics_v1",
                    prompt="evidence_diagnostics_v1",
                    backend=backend,
                    initial_docs=retrieved_docs,
                    final_docs=retrieved_docs,
                    prediction=prediction,
                    parse_success=parse_success,
                    tool_parse_success=True,
                    tool_calls=[],
                    tool_results=[],
                    parse_error=parse_error,
                    usage=usage,
                    cost_usd=cost_usd,
                    prompt_path=prompt_path,
                    response_path=response_path,
                )
            log.info("phase2s module=C static task={task_id} model={model}", task_id=task.task_id, model=model)

        for task in select_hard_subset(tasks):
            episode_docs = docs_by_task_map[task.task_id]
            episode_gold = gold_by_task[task.task_id]
            episode_docs_by_id = docs_by_id(episode_docs)
            bm25_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, "bm25_top8")]
            combo_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, "hygienic_combo_top8")]
            specs: List[tuple[str, str, List[AgentDocument], List[ToolCall], List[Dict[str, Any]], bool]] = []
            specs.append(("hygienic_combo_top8", "static_hygienic_combo", combo_docs, [], [], True))
            calls, results, tool_parse_success, _usage = run_route_then_answer(
                backend=backend,
                runner=runner,
                cost_guard=cost_guard,
                model=model,
                task=task,
                initial_docs=bm25_docs,
                episode_docs=episode_docs,
                out_dir=out_dir,
                temperature=temperature,
            )
            specs.append(("bm25_top8", "route_then_answer_v1", append_tool_documents(bm25_docs, episode_docs_by_id, results), calls, results, tool_parse_success))
            calls = forced_triage_calls(task, bm25_docs)
            results = execute_tool_calls(calls, episode_docs)
            specs.append(("bm25_top8", "forced_triage_tools", append_tool_documents(bm25_docs, episode_docs_by_id, results), calls, results, True))
            for retriever, strategy, final_docs, calls, results, tool_parse_success in specs:
                prediction, parse_success, parse_error, usage, cost_usd, prompt_path, response_path = run_final_prediction(
                    backend=backend,
                    runner=runner,
                    cost_guard=cost_guard,
                    model=model,
                    task=task,
                    final_docs=final_docs,
                    gold_docs=episode_gold,
                    tool_results=results,
                    module="C",
                    dataset="EHA-v2R-stress-pilot",
                    retriever=retriever,
                    strategy=strategy,
                    prompt="evidence_diagnostics_v1",
                    out_dir=out_dir,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                append_record(
                    records,
                    task=task,
                    module="C",
                    dataset="EHA-v2R-stress-pilot",
                    model=model,
                    retriever=retriever,
                    strategy=strategy,
                    prompt="evidence_diagnostics_v1",
                    backend=backend,
                    initial_docs=bm25_docs if retriever == "bm25_top8" else combo_docs,
                    final_docs=final_docs,
                    prediction=prediction,
                    parse_success=parse_success,
                    tool_parse_success=tool_parse_success,
                    tool_calls=calls,
                    tool_results=results,
                    parse_error=parse_error,
                    usage=usage,
                    cost_usd=cost_usd,
                    prompt_path=prompt_path,
                    response_path=response_path,
                )
            log.info("phase2s module=C active task={task_id} model={model}", task_id=task.task_id, model=model)
    return retrieval_rows


def run_phase2s_records(
    *,
    scope_dataset: Mapping[str, Any],
    temporal_dataset: Mapping[str, Any],
    phase2r_dataset: Mapping[str, Any],
    backend: str,
    models: Sequence[str],
    out_dir: Path,
    max_output_tokens: int,
    temperature: float,
    timeout_s: float,
    response_format: str,
    cost_guard: CostGuard,
) -> tuple[List[Phase2SRunRecord], List[Dict[str, Any]]]:
    runner = Phase2OpenAIJsonRunner(timeout_s=timeout_s, response_format=response_format) if backend == "api" else None
    records: List[Phase2SRunRecord] = []
    run_module_a(
        records=records,
        tasks=scope_dataset["tasks"],
        docs_by_task_map=by_task(scope_dataset["documents"]),
        gold_by_task=by_task(scope_dataset["gold_documents"]),
        backend=backend,
        runner=runner,
        cost_guard=cost_guard,
        models=models,
        out_dir=out_dir,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )
    run_module_b(
        records=records,
        tasks=temporal_dataset["tasks"],
        docs_by_task_map=by_task(temporal_dataset["documents"]),
        gold_by_task=by_task(temporal_dataset["gold_documents"]),
        backend=backend,
        runner=runner,
        cost_guard=cost_guard,
        models=models,
        out_dir=out_dir,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )
    retrieval_rows = run_module_c(
        records=records,
        tasks=phase2r_dataset["tasks"],
        docs_by_task_map=by_task(phase2r_dataset["documents"]),
        gold_by_task=by_task(phase2r_dataset["gold_documents"]),
        backend=backend,
        runner=runner,
        cost_guard=cost_guard,
        models=models,
        out_dir=out_dir,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
    )
    return records, retrieval_rows


@app.command()
def main(
    scope_data_dir: Path = typer.Option(Path("data/phase2s-scope-diagnostic"), help="Module A dataset directory."),
    temporal_data_dir: Path = typer.Option(Path("data/phase2s-temporal-routing"), help="Module B dataset directory."),
    phase2r_data_dir: Path = typer.Option(Path("data/phase2r-stress-pilot"), help="Module C Phase 2R dataset directory."),
    backend: str = typer.Option("heuristic", help="heuristic or api."),
    models: str = typer.Option("heuristic-sim", help="Comma-separated model names."),
    out_dir: Path = typer.Option(Path("results/runs/phase2s"), help="Run output directory."),
    max_output_tokens: int = typer.Option(3500, help="Maximum model output tokens."),
    temperature: float = typer.Option(0.0, help="Model temperature."),
    timeout_s: float = typer.Option(180.0, help="OpenAI client timeout."),
    response_format: str = typer.Option("json_schema", help="json_schema, json_object, or none."),
    soft_cap_usd: float = typer.Option(50.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(150.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(300.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    if backend not in {"heuristic", "api"}:
        raise typer.BadParameter("backend must be heuristic or api")
    selected_models = split_csv(models)
    if backend == "api" and selected_models == ["heuristic-sim"]:
        selected_models = ["openai/gpt-4o-mini"]
    scope_dataset = load_dataset(scope_data_dir)
    temporal_dataset = load_dataset(temporal_data_dir)
    phase2r_dataset = load_dataset(phase2r_data_dir)
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        records, retrieval_rows = run_phase2s_records(
            scope_dataset=scope_dataset,
            temporal_dataset=temporal_dataset,
            phase2r_dataset=phase2r_dataset,
            backend=backend,
            models=selected_models,
            out_dir=out_dir,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
            response_format=response_format,
            cost_guard=cost_guard,
        )
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise typer.Exit(code=2) from exc

    write_jsonl(out_dir / "predictions.jsonl", [model_to_dict(record) for record in records])
    all_tasks = list(scope_dataset["tasks"]) + list(temporal_dataset["tasks"]) + list(phase2r_dataset["tasks"])
    all_gold = list(scope_dataset["gold_documents"]) + list(temporal_dataset["gold_documents"]) + list(phase2r_dataset["gold_documents"])
    rows = score_phase2s_run(records, all_tasks, all_gold)
    write_csv(out_dir / "scored_predictions.csv", rows)
    gate = phase2s_gate(rows, retrieval_rows, records)
    write_json(out_dir / "phase2s_gate.json", {"passed": gate.passed, "checks": gate.checks, "details": gate.details})
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in records), 6), **cost_guard.report()})
    status = "[green]passed[/green]" if gate.passed else "[red]failed[/red]"
    console.print(f"Phase 2S gate {status}: {gate.details}")
    console.print(f"[green]Wrote[/green] {len(records)} Phase 2S predictions to {out_dir / 'predictions.jsonl'}")


if __name__ == "__main__":
    app()
