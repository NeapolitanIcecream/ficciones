from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import openai
import typer
from loguru import logger
from openai import OpenAI
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard, estimate_tokens
from .phase2_prompts import (
    build_phase2_messages,
    parse_phase2_prediction_json,
    parse_tool_decision_json,
    phase2_prediction_json_schema,
    tool_decision_messages,
)
from .phase2_retrieval import RETRIEVERS, compute_retrieval_metrics_for_tasks, retrieve
from .phase2_scoring import phase2_pilot_gate, score_phase2_run
from .phase2_tools import Phase2Toolbox
from .report import write_csv
from .run_eval import openai_config, usage_to_dict
from .schemas import (
    AgentDocument,
    DependencyEdge,
    GoldDocument,
    Phase2Prediction,
    Phase2RunRecord,
    Task,
    ToolCall,
    by_task,
    docs_by_id,
    load_dataset,
    model_to_dict,
    write_json,
    write_jsonl,
)


app = typer.Typer(add_completion=False, help="Run EHA Phase 2 pilot experiments.")
console = Console()
log = logger.bind(module="eha.phase2_run")


def split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Phase2OpenAIJsonRunner:
    def __init__(self, timeout_s: float, response_format: str) -> None:
        api_key, base_url = openai_config()
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_s)
        self.response_format = response_format

    def _response_format_payload(self, *, schema_name: str, schema: Mapping[str, Any], mode: Optional[str] = None) -> Optional[Dict[str, Any]]:
        selected = mode or self.response_format
        if selected == "none":
            return None
        if selected == "json_object":
            return {"type": "json_object"}
        return {"type": "json_schema", "json_schema": {"name": schema_name, "strict": True, "schema": dict(schema)}}

    def complete(
        self,
        *,
        model: str,
        messages: Sequence[Dict[str, str]],
        max_output_tokens: int,
        temperature: float,
        schema_name: str,
        schema: Mapping[str, Any],
        mode: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any], str]:
        selected_mode = mode or self.response_format
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "temperature": temperature,
            "max_completion_tokens": max_output_tokens,
        }
        payload = self._response_format_payload(schema_name=schema_name, schema=schema, mode=selected_mode)
        if payload is not None:
            kwargs["response_format"] = payload
        for attempt in range(1, 5):
            try:
                completion = self.client.chat.completions.create(**kwargs)
                break
            except openai.APIConnectionError:
                if attempt >= 4:
                    raise
                time.sleep(2 * attempt)
            except openai.APIStatusError as exc:
                detail = str(exc)
                if exc.status_code == 400 and "max_completion_tokens" in detail:
                    kwargs["max_tokens"] = kwargs.pop("max_completion_tokens")
                    completion = self.client.chat.completions.create(**kwargs)
                    break
                if exc.status_code == 400 and selected_mode == "json_schema":
                    kwargs["response_format"] = {"type": "json_object"}
                    selected_mode = "json_object"
                    completion = self.client.chat.completions.create(**kwargs)
                    break
                raise
        content = completion.choices[0].message.content or ""
        return content, usage_to_dict(completion.usage), selected_mode


def visible_edges(docs: Sequence[AgentDocument]) -> List[DependencyEdge]:
    doc_ids = {doc.doc_id for doc in docs}
    edges: List[DependencyEdge] = []
    for doc in docs:
        for citation in doc.visible_citations:
            if citation in doc_ids:
                relation = "reposts" if doc.source_type in {"blog_repost", "trade_news", "vendor_brief", "forum_digest"} else "cites"
                edges.append(DependencyEdge(from_doc=doc.doc_id, to_doc=citation, relation=relation))
    return edges


def heuristic_phase2_prediction(
    task: Task,
    docs: Sequence[AgentDocument],
    gold_docs: Sequence[GoldDocument],
    *,
    strategy: str,
) -> Phase2Prediction:
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    doc_ids = [doc.doc_id for doc in docs]
    primary = [doc_id for doc_id in task.gold.primary_support if doc_id in doc_ids]
    contaminants = [doc.doc_id for doc in docs if gold_by_id[doc.doc_id].is_contaminated]
    false_sources = [doc.doc_id for doc in docs if gold_by_id[doc.doc_id].stance == "supports_false_claim"]
    primary_visible = bool(primary)
    false_saturation = len(false_sources) / len(docs) if docs else 0.0

    fooled = False
    if task.episode_type == "false_consensus":
        fooled = false_saturation >= 0.75 or (false_saturation >= 0.50 and not primary_visible)
    elif task.episode_type in {"citation_laundering", "halupedia_trap", "insufficient_or_no_primary"}:
        fooled = bool(false_sources) and not primary_visible and strategy == "evidence_graph_v2"
    elif task.episode_type == "temporal_pollution":
        fooled = bool(false_sources) and not primary_visible
    elif task.episode_type == "mixed_source_corruption_v2":
        fooled = bool(false_sources) and not primary_visible

    if fooled:
        verdict = "supported" if task.gold.verdict != "supported" else "refuted"
        support = false_sources[:3]
        rejected = primary[:1]
        confidence = 0.86
        answer = "The visible summaries appear to support the claim, but the supporting set is not independently verified."
    else:
        verdict = task.gold.verdict if task.gold.verdict != "mixed" else "insufficient"
        support = primary[:2] if verdict != "insufficient" else primary[:1]
        rejected = contaminants[:5]
        confidence = 0.73 if primary_visible else 0.61
        answer = task.gold.answer_brief

    if task.episode_type in {"halupedia_trap", "insufficient_or_no_primary"} and primary_visible and not fooled:
        verdict = "insufficient"
        support = primary[:2]
        confidence = 0.64

    return Phase2Prediction(
        claim_verdict=verdict,  # type: ignore[arg-type]
        scope_tag=task.gold.scope_tag,
        confidence=confidence,
        supporting_evidence=support,
        rejected_evidence=rejected,
        predicted_dependency_edges=visible_edges(docs),
        source_independence="Primary records are preferred; repeated visible citations count as one upstream source.",
        contamination_notes="Rejected stale, generated, unsupported, or repeated sources when visible.",
        remaining_uncertainties="Synthetic corpus only; no live web was used.",
        answer=answer,
    )


def normalize_doc_refs(values: Iterable[str], allowed_doc_ids: Sequence[str]) -> List[str]:
    allowed = set(allowed_doc_ids)
    output: List[str] = []
    for value in values:
        if value in allowed and value not in output:
            output.append(value)
            continue
        for doc_id in allowed_doc_ids:
            if doc_id in value and doc_id not in output:
                output.append(doc_id)
                break
    return output


def normalize_phase2_prediction(prediction: Phase2Prediction, allowed_doc_ids: Sequence[str]) -> Phase2Prediction:
    allowed = set(allowed_doc_ids)
    edges = [
        edge
        for edge in prediction.predicted_dependency_edges
        if edge.from_doc in allowed and edge.to_doc in allowed
    ]
    return prediction.model_copy(
        update={
            "supporting_evidence": normalize_doc_refs(prediction.supporting_evidence, allowed_doc_ids),
            "rejected_evidence": normalize_doc_refs(prediction.rejected_evidence, allowed_doc_ids),
            "predicted_dependency_edges": edges,
        }
    )


def append_tool_documents(base_docs: Sequence[AgentDocument], all_docs_by_id: Mapping[str, AgentDocument], tool_results: Sequence[Mapping[str, Any]]) -> List[AgentDocument]:
    output = list(base_docs)
    seen = {doc.doc_id for doc in output}
    for result in tool_results:
        for key in ("documents", "versions"):
            value = result.get(key)
            if not isinstance(value, list):
                continue
            for item in value:
                if not isinstance(item, Mapping):
                    continue
                doc_id = item.get("doc_id")
                if isinstance(doc_id, str) and doc_id in all_docs_by_id and doc_id not in seen:
                    output.append(all_docs_by_id[doc_id])
                    seen.add(doc_id)
    return output


def forced_primary_tool_results(task: Task, episode_docs: Sequence[AgentDocument]) -> List[Dict[str, Any]]:
    toolbox = Phase2Toolbox(episode_docs)
    return [toolbox.request_primary_record(task.question, entity="Novalis Robotics", date_range="2024 2025", top_n=3)]


def heuristic_tool_calls(task: Task, initial_docs: Sequence[AgentDocument], gold_docs: Sequence[GoldDocument]) -> List[ToolCall]:
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    primary_visible = any(doc.doc_id in task.gold.primary_support for doc in initial_docs)
    calls: List[ToolCall] = []
    cited_doc = next((doc for doc in initial_docs if doc.visible_citations), None)
    if cited_doc is not None and task.episode_type in {"false_consensus", "citation_laundering", "halupedia_trap"}:
        calls.append(ToolCall(tool="trace_citation", args={"doc_id": cited_doc.doc_id, "depth": 2}))
    if not primary_visible:
        calls.append(
            ToolCall(
                tool="request_primary_record",
                args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3},
            )
        )
    elif task.episode_type == "temporal_pollution":
        calls.append(ToolCall(tool="compare_versions", args={"entity": "Novalis Robotics", "topic": task.question, "top_n": 5}))
    elif any(gold_by_id[doc.doc_id].is_contaminated for doc in initial_docs):
        calls.append(ToolCall(tool="search_contradictions", args={"claim_text": task.question, "top_n": 4}))
    return calls[:2]


def execute_tool_calls(calls: Sequence[ToolCall], episode_docs: Sequence[AgentDocument]) -> List[Dict[str, Any]]:
    toolbox = Phase2Toolbox(episode_docs)
    results: List[Dict[str, Any]] = []
    for call in calls[:2]:
        result = toolbox.execute(call.tool, call.args)
        result["tool"] = call.tool
        results.append(result)
    return results


def artifact_paths(out_dir: Path, *, task_id: str, model: str, retriever: str, strategy: str, suffix: str = "final") -> Tuple[Path, Path]:
    safe_model = model.replace("/", "_")
    base = out_dir / "artifacts" / safe_model / retriever / strategy
    return base / f"{task_id}.{suffix}.prompt.json", base / f"{task_id}.{suffix}.response.json"


def write_artifacts(
    out_dir: Path,
    *,
    task_id: str,
    model: str,
    retriever: str,
    strategy: str,
    suffix: str,
    messages: Sequence[Dict[str, str]],
    response_text: str,
    usage: Mapping[str, Any],
    response_format: str,
) -> Tuple[str, str]:
    prompt_path, response_path = artifact_paths(out_dir, task_id=task_id, model=model, retriever=retriever, strategy=strategy, suffix=suffix)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(prompt_path, {"task_id": task_id, "model": model, "retriever": retriever, "strategy": strategy, "messages": list(messages), "response_format": response_format})
    write_json(response_path, {"task_id": task_id, "model": model, "retriever": retriever, "strategy": strategy, "response_text": response_text, "usage": dict(usage)})
    return str(prompt_path), str(response_path)


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
        return heuristic_phase2_prediction(task, final_docs, gold_docs, strategy=strategy), True, None, {}, 0.0, None, None
    assert runner is not None
    messages = build_phase2_messages(task.question, final_docs, tool_results)
    prompt_text = json.dumps(messages, ensure_ascii=False)
    cost_guard.before_call(model, prompt_text, max_output_tokens)
    response_text, usage, used_format = runner.complete(
        model=model,
        messages=messages,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        schema_name="eha_phase2_prediction",
        schema=phase2_prediction_json_schema(),
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
        prediction = normalize_phase2_prediction(parse_phase2_prediction_json(response_text), [doc.doc_id for doc in final_docs])
        parse_success = True
        parse_error = None
    except Exception as exc:  # noqa: BLE001
        prediction = Phase2Prediction(
            claim_verdict="insufficient",
            scope_tag="no_primary_source",
            confidence=0.0,
            supporting_evidence=[],
            rejected_evidence=[],
            predicted_dependency_edges=[],
            source_independence="Parse failure.",
            contamination_notes="Parse failure.",
            remaining_uncertainties=response_text[:500],
            answer="The model response could not be parsed as the required Phase 2 JSON object.",
        )
        parse_success = False
        parse_error = str(exc)
    return prediction, parse_success, parse_error, usage, cost_guard.after_call(model, usage), prompt_path, response_path


def run_phase2_records(
    *,
    tasks: Sequence[Task],
    docs_by_task_map: Mapping[str, List[AgentDocument]],
    gold_by_task: Mapping[str, List[GoldDocument]],
    backend: str,
    models: Sequence[str],
    retrievers: Sequence[str],
    out_dir: Path,
    active: bool,
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
            episode_docs_by_id = docs_by_id(episode_docs)
            for retriever in retrievers:
                hits = retrieve(task.question, episode_docs, episode_gold, retriever)
                retrieved_docs = [hit.doc for hit in hits]
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
                    strategy="evidence_graph_v2",
                    out_dir=out_dir,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                records.append(
                    Phase2RunRecord(
                        task_id=task.task_id,
                        model=model,
                        retriever=retriever,
                        strategy="evidence_graph_v2",
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
                log.info("phase2 static task={task_id} model={model} retriever={retriever}", task_id=task.task_id, model=model, retriever=retriever)

            if not active:
                continue

            bm25_docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, "bm25_top8")]
            forced_results = forced_primary_tool_results(task, episode_docs)
            forced_docs = append_tool_documents(bm25_docs, episode_docs_by_id, forced_results)
            prediction, parse_success, parse_error, usage, cost_usd, prompt_path, response_path = run_final_prediction(
                backend=backend,
                runner=runner,
                cost_guard=cost_guard,
                model=model,
                task=task,
                final_docs=forced_docs,
                gold_docs=episode_gold,
                tool_results=forced_results,
                retriever="bm25_top8",
                strategy="forced_primary_append",
                out_dir=out_dir,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
            records.append(
                Phase2RunRecord(
                    task_id=task.task_id,
                    model=model,
                    retriever="bm25_top8",
                    strategy="forced_primary_append",
                    backend=backend,
                    initial_doc_ids=[doc.doc_id for doc in bm25_docs],
                    final_doc_ids=[doc.doc_id for doc in forced_docs],
                    prediction=prediction,
                    parse_success=parse_success,
                    tool_calls=[ToolCall(tool="request_primary_record", args={"claim_text": task.question, "entity": "Novalis Robotics", "date_range": "2024 2025", "top_n": 3})],
                    tool_results=forced_results,
                    parse_error=parse_error,
                    usage=usage,
                    cost_usd=cost_usd,
                    prompt_path=prompt_path,
                    response_path=response_path,
                )
            )

            tool_parse_success = True
            calls: List[ToolCall]
            if backend == "heuristic":
                calls = heuristic_tool_calls(task, bm25_docs, episode_gold)
                tool_usage: Dict[str, Any] = {}
            else:
                assert runner is not None
                messages = tool_decision_messages(task.question, bm25_docs)
                prompt_text = json.dumps(messages, ensure_ascii=False)
                cost_guard.before_call(model, prompt_text, 1000)
                response_text, tool_usage, used_format = runner.complete(
                    model=model,
                    messages=messages,
                    max_output_tokens=1000,
                    temperature=temperature,
                    schema_name="eha_phase2_tool_decision",
                    schema={"type": "object"},
                    mode="json_object",
                )
                write_artifacts(
                    out_dir,
                    task_id=task.task_id,
                    model=model,
                    retriever="bm25_top8",
                    strategy="tool_agent_2call",
                    suffix="tool",
                    messages=messages,
                    response_text=response_text,
                    usage=tool_usage,
                    response_format=used_format,
                )
                cost_guard.after_call(model, tool_usage)
                try:
                    need_tools, calls, _reason = parse_tool_decision_json(response_text)
                    if not need_tools:
                        calls = []
                except Exception:
                    calls = []
                    tool_parse_success = False
            tool_results = execute_tool_calls(calls, episode_docs)
            final_docs = append_tool_documents(bm25_docs, episode_docs_by_id, tool_results)
            prediction, parse_success, parse_error, usage, cost_usd, prompt_path, response_path = run_final_prediction(
                backend=backend,
                runner=runner,
                cost_guard=cost_guard,
                model=model,
                task=task,
                final_docs=final_docs,
                gold_docs=episode_gold,
                tool_results=tool_results,
                retriever="bm25_top8",
                strategy="tool_agent_2call",
                out_dir=out_dir,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
            )
            records.append(
                Phase2RunRecord(
                    task_id=task.task_id,
                    model=model,
                    retriever="bm25_top8",
                    strategy="tool_agent_2call",
                    backend=backend,
                    initial_doc_ids=[doc.doc_id for doc in bm25_docs],
                    final_doc_ids=[doc.doc_id for doc in final_docs],
                    prediction=prediction,
                    parse_success=parse_success,
                    tool_parse_success=tool_parse_success,
                    tool_calls=calls,
                    tool_results=tool_results,
                    parse_error=parse_error,
                    usage=usage,
                    cost_usd=cost_usd,
                    prompt_path=prompt_path,
                    response_path=response_path,
                )
            )
    return records


@app.command()
def pilot(
    data_dir: Path = typer.Option(Path("data/phase2-pilot"), help="Generated Phase 2 pilot dataset directory."),
    backend: str = typer.Option("heuristic", help="heuristic or api."),
    models: str = typer.Option("heuristic-sim", help="Comma-separated model names."),
    retrievers: str = typer.Option(",".join(RETRIEVERS), help="Comma-separated retriever names."),
    out_dir: Path = typer.Option(Path("results/runs/phase2-pilot"), help="Run output directory."),
    active: bool = typer.Option(True, help="Run forced-primary and tool-agent active strategies."),
    max_output_tokens: int = typer.Option(4000, help="Maximum model output tokens."),
    temperature: float = typer.Option(0.0, help="Model temperature."),
    timeout_s: float = typer.Option(120.0, help="OpenAI client timeout."),
    response_format: str = typer.Option("json_schema", help="json_schema, json_object, or none."),
    soft_cap_usd: float = typer.Option(100.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(250.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(300.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    if backend not in {"heuristic", "api"}:
        raise typer.BadParameter("backend must be heuristic or api")
    selected_retrievers = split_csv(retrievers)
    unknown = sorted(set(selected_retrievers) - set(RETRIEVERS))
    if unknown:
        raise typer.BadParameter(f"unknown retrievers: {', '.join(unknown)}")
    selected_models = split_csv(models)
    if backend == "api" and selected_models == ["heuristic-sim"]:
        selected_models = ["openai/gpt-4o-mini"]

    dataset = load_dataset(data_dir)
    tasks: List[Task] = dataset["tasks"]
    docs_by_task_map = by_task(dataset["documents"])
    gold_by_task = by_task(dataset["gold_documents"])
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    out_dir.mkdir(parents=True, exist_ok=True)

    retrieval_rows = compute_retrieval_metrics_for_tasks(tasks, docs_by_task_map, gold_by_task, selected_retrievers)
    write_csv(out_dir / "retrieval_metrics.csv", retrieval_rows)
    try:
        records = run_phase2_records(
            tasks=tasks,
            docs_by_task_map=docs_by_task_map,
            gold_by_task=gold_by_task,
            backend=backend,
            models=selected_models,
            retrievers=selected_retrievers,
            out_dir=out_dir,
            active=active,
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
    total_record_cost = sum(record.cost_usd for record in records)
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(total_record_cost, 6), **cost_guard.report()})
    rows = score_phase2_run(records, tasks, dataset["gold_documents"], dataset["edges"])
    write_csv(out_dir / "scored_predictions.csv", rows)
    gate = phase2_pilot_gate(rows, retrieval_rows, records)
    write_json(out_dir / "pilot_gate.json", {"passed": gate.passed, "checks": gate.checks, "details": gate.details})
    status = "[green]passed[/green]" if gate.passed else "[red]failed[/red]"
    console.print(f"Phase 2 pilot gate {status}: {gate.details}")
    console.print(f"[green]Wrote[/green] {len(records)} Phase 2 predictions to {out_dir / 'predictions.jsonl'}")


if __name__ == "__main__":
    app()
