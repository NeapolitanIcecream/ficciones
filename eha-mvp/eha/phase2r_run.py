from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import typer
from loguru import logger
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard
from .phase2_retrieval import RETRIEVERS, compute_retrieval_metrics_for_tasks, retrieve
from .phase2_run import (
    Phase2OpenAIJsonRunner,
    append_tool_documents,
    execute_tool_calls,
    normalize_phase2_prediction,
    split_csv,
    visible_edges,
    write_artifacts,
)
from .phase2_tools import Phase2Toolbox
from .phase2r_prompts import (
    build_phase2r_messages,
    parse_phase2r_prediction_json,
    parse_tool_plan_json,
    phase2r_prediction_json_schema,
    tool_plan_messages,
)
from .phase2r_scoring import phase2r_gate, score_phase2r_run
from .report import write_csv
from .schemas import AgentDocument, GoldDocument, Phase2Prediction, Phase2RunRecord, Task, ToolCall, by_task, docs_by_id, load_dataset, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Run EHA Phase 2R stress-calibrated pilots.")
console = Console()
log = logger.bind(module="eha.phase2r_run")

STATIC_RETRIEVERS = (
    "bm25_top8",
    "bm25_top12",
    "primary_preserve_top8",
    "heuristic_root_dedup_top8",
    "hygienic_combo_top8",
)
RETRIEVAL_METRIC_RETRIEVERS = (*STATIC_RETRIEVERS, "oracle_root_dedup_top8")


def heuristic_phase2r_prediction(
    task: Task,
    docs: Sequence[AgentDocument],
    gold_docs: Sequence[GoldDocument],
    *,
    retriever: str,
    strategy: str,
) -> Phase2Prediction:
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    doc_ids = [doc.doc_id for doc in docs]
    primary = [doc_id for doc_id in task.gold.primary_support if doc_id in doc_ids]
    false_sources = [doc.doc_id for doc in docs if doc.doc_id in gold_by_id and gold_by_id[doc.doc_id].stance == "supports_false_claim"]
    contaminants = [doc.doc_id for doc in docs if doc.doc_id in gold_by_id and gold_by_id[doc.doc_id].is_contaminated]
    pollutant_saturation = len(false_sources) / len(docs) if docs else 0.0
    is_hp_false = (
        task.episode_type == "false_consensus_stress"
        and not task.primary_visibility_under_bm25_top8
        and task.duplicate_count >= 20
    )
    fooled = False
    if strategy == "evidence_graph_v3" and retriever == "bm25_top8" and is_hp_false and pollutant_saturation >= 0.75:
        fooled = True
    elif strategy == "evidence_graph_v3" and retriever == "bm25_top12" and is_hp_false and pollutant_saturation >= 0.85:
        fooled = True
    elif task.episode_type == "halupedia_or_generated_lore" and not primary and strategy == "evidence_graph_v3" and retriever == "bm25_top8":
        fooled = True

    if fooled:
        verdict = "supported" if task.gold.verdict != "supported" else "refuted"
        support = false_sources[:3]
        rejected = primary[:1]
        confidence = 0.82
        scope_tag = "full"
        answer = "The repeated retrieved summaries appear to support the claim."
    else:
        verdict = task.gold.verdict if task.gold.verdict != "mixed" else "refuted"
        support = primary[:2] if verdict != "insufficient" else []
        rejected = contaminants[:5]
        confidence = 0.73 if support or verdict == "insufficient" else 0.60
        scope_tag = task.gold.scope_tag
        answer = task.gold.answer_brief
    if task.episode_type in {"halupedia_or_generated_lore", "insufficient_or_no_primary"} and not fooled:
        verdict = "insufficient"
        support = []
        confidence = 0.58

    return Phase2Prediction(
        claim_verdict=verdict,  # type: ignore[arg-type]
        scope_tag=scope_tag,  # type: ignore[arg-type]
        confidence=confidence,
        supporting_evidence=support,
        rejected_evidence=rejected,
        predicted_dependency_edges=visible_edges(docs),
        source_independence="Repeated visible citation chains count as one source; primary records are preferred.",
        contamination_notes="Flags generated lore, stale records, laundering chains, and same-root repetition.",
        remaining_uncertainties="Synthetic corpus only; no live web was used.",
        answer=answer,
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
    retriever: str,
    strategy: str,
    out_dir: Path,
    max_output_tokens: int,
    temperature: float,
) -> Tuple[Phase2Prediction, bool, Optional[str], Dict[str, Any], float, Optional[str], Optional[str]]:
    if backend == "heuristic":
        return (
            heuristic_phase2r_prediction(task, final_docs, gold_docs, retriever=retriever, strategy=strategy),
            True,
            None,
            {},
            0.0,
            None,
            None,
        )
    assert runner is not None
    messages = build_phase2r_messages(task.question, final_docs, tool_results)
    cost_guard.before_call(model, json.dumps(messages, ensure_ascii=False), max_output_tokens)
    response_text, usage, used_format = runner.complete(
        model=model,
        messages=messages,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        schema_name="eha_phase2r_prediction",
        schema=phase2r_prediction_json_schema(),
    )
    prompt_path, response_path = write_artifacts(
        out_dir,
        task_id=task.task_id,
        model=model,
        retriever=retriever,
        strategy=strategy,
        suffix="final",
        messages=messages,
        response_text=response_text,
        usage=usage,
        response_format=used_format,
    )
    try:
        prediction = normalize_phase2_prediction(parse_phase2r_prediction_json(response_text), [doc.doc_id for doc in final_docs])
        return prediction, True, None, usage, cost_guard.after_call(model, usage), prompt_path, response_path
    except Exception as exc:  # noqa: BLE001
        prediction = Phase2Prediction(
            claim_verdict="insufficient",
            scope_tag="uncertain",
            confidence=0.0,
            supporting_evidence=[],
            rejected_evidence=[],
            predicted_dependency_edges=[],
            source_independence="Parse failure.",
            contamination_notes="Parse failure.",
            remaining_uncertainties=response_text[:500],
            answer="The model response could not be parsed as the required Phase 2R JSON object.",
        )
        return prediction, False, str(exc), usage, cost_guard.after_call(model, usage), prompt_path, response_path


def forced_primary_results(task: Task, episode_docs: Sequence[AgentDocument]) -> tuple[List[ToolCall], List[Dict[str, Any]]]:
    call = ToolCall(
        tool="request_primary_record",
        args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3},
    )
    return [call], execute_tool_calls([call], episode_docs)


def forced_triage_calls(task: Task, initial_docs: Sequence[AgentDocument]) -> List[ToolCall]:
    cited_doc = next((doc for doc in initial_docs if doc.visible_citations), initial_docs[0] if initial_docs else None)
    calls: List[ToolCall] = []
    if task.episode_type == "false_consensus_stress":
        calls = [
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3}),
            ToolCall(tool="search_contradictions", args={"claim_text": task.question, "top_n": 5}),
        ]
    elif task.episode_type == "citation_laundering_trace":
        calls = [
            ToolCall(tool="trace_citation", args={"doc_id": cited_doc.doc_id if cited_doc else "", "depth": 2}),
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3}),
        ]
    elif task.episode_type == "temporal_pollution_compare":
        calls = [
            ToolCall(tool="compare_versions", args={"entity": "Novalis Robotics", "topic": task.question, "top_n": 5}),
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3}),
        ]
    elif task.episode_type == "halupedia_or_generated_lore":
        calls = [
            ToolCall(tool="trace_citation", args={"doc_id": cited_doc.doc_id if cited_doc else "", "depth": 2}),
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3}),
        ]
    elif task.episode_type == "insufficient_or_no_primary":
        calls = [
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3}),
            ToolCall(tool="search_contradictions", args={"claim_text": task.question, "top_n": 5}),
        ]
    else:
        calls = [ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3})]
    return calls[:3]


def heuristic_tool_policy_calls(task: Task, initial_docs: Sequence[AgentDocument]) -> List[ToolCall]:
    cited_doc = next((doc for doc in initial_docs if doc.visible_citations), initial_docs[0] if initial_docs else None)
    if task.episode_type == "citation_laundering_trace":
        return [
            ToolCall(tool="trace_citation", args={"doc_id": cited_doc.doc_id if cited_doc else "", "depth": 2, "_intent": "trace_source"}),
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3, "_intent": "check_primary_support"}),
        ]
    if task.episode_type == "temporal_pollution_compare":
        return [
            ToolCall(tool="compare_versions", args={"entity": "Novalis Robotics", "topic": task.question, "top_n": 5, "_intent": "compare_versions"}),
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3, "_intent": "check_primary_support"}),
        ]
    if task.episode_type == "false_consensus_stress":
        return [
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3, "_intent": "check_primary_support"}),
            ToolCall(tool="search_contradictions", args={"claim_text": task.question, "top_n": 5, "_intent": "find_contradiction"}),
            ToolCall(tool="trace_citation", args={"doc_id": cited_doc.doc_id if cited_doc else "", "depth": 2, "_intent": "trace_source"}),
        ]
    if task.episode_type == "halupedia_or_generated_lore":
        return [
            ToolCall(tool="trace_citation", args={"doc_id": cited_doc.doc_id if cited_doc else "", "depth": 2, "_intent": "test_generated_lore"}),
            ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3, "_intent": "check_primary_support"}),
            ToolCall(tool="search_contradictions", args={"claim_text": task.question, "top_n": 5, "_intent": "find_contradiction"}),
        ]
    return forced_triage_calls(task, initial_docs)


def run_tool_plan(
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
        calls = heuristic_tool_policy_calls(task, initial_docs)
        return calls, execute_tool_calls(calls, episode_docs), True, {}
    assert runner is not None
    messages = tool_plan_messages(task.question, initial_docs)
    cost_guard.before_call(model, json.dumps(messages, ensure_ascii=False), 1200)
    response_text, usage, used_format = runner.complete(
        model=model,
        messages=messages,
        max_output_tokens=1200,
        temperature=temperature,
        schema_name="eha_phase2r_tool_plan",
        schema={"type": "object"},
        mode="json_object",
    )
    write_artifacts(
        out_dir,
        task_id=task.task_id,
        model=model,
        retriever="bm25_top8",
        strategy="tool_agent_3call_policy",
        suffix="tool",
        messages=messages,
        response_text=response_text,
        usage=usage,
        response_format=used_format,
    )
    cost_guard.after_call(model, usage)
    try:
        calls, _reason = parse_tool_plan_json(response_text)
        return calls[:3], execute_tool_calls(calls[:3], episode_docs), True, usage
    except Exception:
        return [], [], False, usage


def select_hard_subset(tasks: Sequence[Task]) -> List[Task]:
    false_tasks = [task for task in tasks if task.episode_type == "false_consensus_stress"]
    high_pressure = [task for task in false_tasks if not task.primary_visibility_under_bm25_top8 and task.duplicate_count >= 20]
    extra_false = [task for task in false_tasks if task not in high_pressure]
    selected = high_pressure[:20]
    selected.extend(extra_false[: max(0, 20 - len(selected))])
    selected.extend([task for task in tasks if task.episode_type == "citation_laundering_trace"][:8])
    selected.extend([task for task in tasks if task.episode_type == "temporal_pollution_compare"][:6])
    selected.extend([task for task in tasks if task.episode_type == "halupedia_or_generated_lore"][:8])
    selected.extend([task for task in tasks if task.episode_type == "insufficient_or_no_primary"][:4])
    selected.extend([task for task in tasks if task.episode_type == "mixed_source_corruption_v2"][:2])
    return selected[:48]


def run_phase2r_records(
    *,
    tasks: Sequence[Task],
    docs_by_task_map: Mapping[str, List[AgentDocument]],
    gold_by_task: Mapping[str, List[GoldDocument]],
    backend: str,
    models: Sequence[str],
    out_dir: Path,
    run_active: bool,
    max_output_tokens: int,
    temperature: float,
    timeout_s: float,
    response_format: str,
    cost_guard: CostGuard,
) -> List[Phase2RunRecord]:
    runner = Phase2OpenAIJsonRunner(timeout_s=timeout_s, response_format=response_format) if backend == "api" else None
    records: List[Phase2RunRecord] = []
    for model in models:
        for task in tasks:
            episode_docs = docs_by_task_map[task.task_id]
            episode_gold = gold_by_task[task.task_id]
            for retriever in STATIC_RETRIEVERS:
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
                    retriever=retriever,
                    strategy="evidence_graph_v3",
                    out_dir=out_dir,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                records.append(
                    Phase2RunRecord(
                        task_id=task.task_id,
                        model=model,
                        retriever=retriever,
                        strategy="evidence_graph_v3",
                        backend=backend,
                        initial_doc_ids=[doc.doc_id for doc in retrieved_docs],
                        final_doc_ids=[doc.doc_id for doc in retrieved_docs],
                        prediction=prediction,
                        parse_success=parse_success,
                        parse_error=parse_error,
                        usage=usage,
                        cost_usd=cost_usd,
                        prompt_path=prompt_path,
                        response_path=response_path,
                    )
                )
                log.info("phase2r static task={task_id} model={model} retriever={retriever}", task_id=task.task_id, model=model, retriever=retriever)

        if not run_active:
            continue
        hard_tasks = select_hard_subset(tasks)
        for task in hard_tasks:
            episode_docs = docs_by_task_map[task.task_id]
            episode_gold = gold_by_task[task.task_id]
            episode_docs_by_id = docs_by_id(episode_docs)
            bm25_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, "bm25_top8")]
            combo_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, "hygienic_combo_top8")]

            active_specs: List[tuple[str, str, List[AgentDocument], List[ToolCall], List[Dict[str, Any]], bool]] = []
            active_specs.append(("hygienic_combo_top8", "static_hygienic_combo", combo_docs, [], [], True))
            calls, results = forced_primary_results(task, episode_docs)
            active_specs.append(("bm25_top8", "forced_primary_append", append_tool_documents(bm25_docs, episode_docs_by_id, results), calls, results, True))
            calls = forced_triage_calls(task, bm25_docs)
            results = execute_tool_calls(calls, episode_docs)
            active_specs.append(("bm25_top8", "forced_triage_tools", append_tool_documents(bm25_docs, episode_docs_by_id, results), calls, results, True))
            calls, results, tool_parse_success, _tool_usage = run_tool_plan(
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
            active_specs.append(("bm25_top8", "tool_agent_3call_policy", append_tool_documents(bm25_docs, episode_docs_by_id, results), calls, results, tool_parse_success))

            for retriever, strategy, final_docs, calls, results, tool_parse_success in active_specs:
                prediction, parse_success, parse_error, usage, cost_usd, prompt_path, response_path = run_final_prediction(
                    backend=backend,
                    runner=runner,
                    cost_guard=cost_guard,
                    model=model,
                    task=task,
                    final_docs=final_docs,
                    gold_docs=episode_gold,
                    tool_results=results,
                    retriever=retriever,
                    strategy=strategy,
                    out_dir=out_dir,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                records.append(
                    Phase2RunRecord(
                        task_id=task.task_id,
                        model=model,
                        retriever=retriever,
                        strategy=strategy,
                        backend=backend,
                        initial_doc_ids=[doc.doc_id for doc in bm25_docs if retriever == "bm25_top8"] or [doc.doc_id for doc in combo_docs],
                        final_doc_ids=[doc.doc_id for doc in final_docs],
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
                )
    return records


@app.command()
def main(
    data_dir: Path = typer.Option(Path("data/phase2r-stress-pilot"), help="Generated Phase 2R dataset directory."),
    backend: str = typer.Option("heuristic", help="heuristic or api."),
    models: str = typer.Option("heuristic-sim", help="Comma-separated model names."),
    out_dir: Path = typer.Option(Path("results/runs/phase2r-stress-pilot"), help="Run output directory."),
    run_active: bool = typer.Option(True, help="Run active verification hard subset."),
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

    dataset = load_dataset(data_dir)
    tasks: List[Task] = dataset["tasks"]
    docs_by_task_map = by_task(dataset["documents"])
    gold_by_task = by_task(dataset["gold_documents"])
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    out_dir.mkdir(parents=True, exist_ok=True)

    retrieval_rows = compute_retrieval_metrics_for_tasks(tasks, docs_by_task_map, gold_by_task, RETRIEVAL_METRIC_RETRIEVERS)
    write_csv(out_dir / "retrieval_metrics.csv", retrieval_rows)
    try:
        records = run_phase2r_records(
            tasks=tasks,
            docs_by_task_map=docs_by_task_map,
            gold_by_task=gold_by_task,
            backend=backend,
            models=selected_models,
            out_dir=out_dir,
            run_active=run_active,
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
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in records), 6), **cost_guard.report()})
    rows = score_phase2r_run(records, tasks, dataset["gold_documents"], dataset["edges"])
    write_csv(out_dir / "scored_predictions.csv", rows)
    gate = phase2r_gate(rows, retrieval_rows, records)
    write_json(out_dir / "phase2r_gate.json", {"passed": gate.passed, "checks": gate.checks, "details": gate.details})
    status = "[green]passed[/green]" if gate.passed else "[red]failed[/red]"
    console.print(f"Phase 2R gate {status}: {gate.details}")
    console.print(f"[green]Wrote[/green] {len(records)} Phase 2R predictions to {out_dir / 'predictions.jsonl'}")


if __name__ == "__main__":
    app()
