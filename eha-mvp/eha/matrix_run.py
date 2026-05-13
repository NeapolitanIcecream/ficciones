from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import typer
from loguru import logger
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard
from .matrix_prompts import (
    build_claim_first_messages,
    build_simple_answer_messages,
    matrix_prediction_json_schema,
    parse_matrix_prediction_json,
    phase2_prediction_to_matrix,
)
from .matrix_scoring import matrix_preflight_gate, score_matrix_run
from .phase2_retrieval import compute_retrieval_metrics_for_tasks, retrieve
from .phase2_run import Phase2OpenAIJsonRunner, normalize_doc_refs, split_csv, write_artifacts
from .phase2r_prompts import build_phase2r_messages, parse_phase2r_prediction_json, phase2r_prediction_json_schema
from .report import write_csv
from .schemas import (
    AgentDocument,
    GoldDocument,
    MatrixPrediction,
    MatrixRunRecord,
    Task,
    by_task,
    load_dataset,
    model_to_dict,
    write_json,
    write_jsonl,
)


app = typer.Typer(add_completion=False, help="Run EHA Matrix Escape Table v1 experiments.")
console = Console()
log = logger.bind(module="eha.matrix_run")

MAIN_STRATEGIES: tuple[tuple[str, str, str], ...] = (
    ("naive_bm25", "bm25_top8", "simple_answer_v1"),
    ("careful_bm25", "bm25_top8", "claim_first_citation_v1"),
    ("primary_preserve", "primary_preserve_top8", "claim_first_citation_v1"),
    ("hygienic_combo", "hygienic_combo_top8", "claim_first_citation_v1"),
)

PREFLIGHT_SPECS: tuple[tuple[str, str, str], ...] = (
    ("evidence_graph_v3_bm25", "bm25_top8", "evidence_graph_v3"),
    ("evidence_graph_v3_hygienic", "hygienic_combo_top8", "evidence_graph_v3"),
    ("claim_first_bm25", "bm25_top8", "claim_first_citation_v1"),
    ("claim_first_hygienic", "hygienic_combo_top8", "claim_first_citation_v1"),
)

RETRIEVAL_METRIC_RETRIEVERS = ("bm25_top8", "primary_preserve_top8", "hygienic_combo_top8")
CLAIM_FIRST_PROMPTS = {"claim_first_citation_v1", "claim_first_citation_v1_1"}


def select_matrix_specs(*, preflight: bool, strategy_names: Sequence[str] | None = None) -> tuple[tuple[str, str, str], ...]:
    specs = PREFLIGHT_SPECS if preflight else MAIN_STRATEGIES
    if not strategy_names:
        return specs
    wanted = set(strategy_names)
    selected = tuple(spec for spec in specs if spec[0] in wanted)
    unknown = sorted(wanted - {spec[0] for spec in specs})
    if unknown:
        available = ", ".join(spec[0] for spec in specs)
        raise ValueError(f"unknown Matrix strategy for this mode: {', '.join(unknown)}; available: {available}")
    return selected


def apply_claim_first_prompt(
    specs: Sequence[tuple[str, str, str]],
    claim_first_prompt: str,
) -> tuple[tuple[str, str, str], ...]:
    if claim_first_prompt not in CLAIM_FIRST_PROMPTS:
        raise ValueError(f"unknown claim-first prompt: {claim_first_prompt}")
    return tuple((strategy, retriever, claim_first_prompt if prompt == "claim_first_citation_v1" else prompt) for strategy, retriever, prompt in specs)


def filter_tasks_by_difficulties(tasks: Sequence[Task], difficulties: Sequence[str] | None = None) -> List[Task]:
    if not difficulties:
        return list(tasks)
    wanted = set(difficulties)
    known = {task.difficulty for task in tasks}
    unknown = sorted(wanted - known)
    if unknown:
        raise ValueError(f"unknown Matrix difficulty: {', '.join(unknown)}; available: {', '.join(sorted(known))}")
    return [task for task in tasks if task.difficulty in wanted]


def normalize_matrix_prediction(prediction: MatrixPrediction, allowed_doc_ids: Sequence[str]) -> MatrixPrediction:
    return prediction.model_copy(
        update={
            "supporting_evidence": normalize_doc_refs(prediction.supporting_evidence, allowed_doc_ids),
            "rejected_evidence": normalize_doc_refs(prediction.rejected_evidence, allowed_doc_ids),
        }
    )


def heuristic_matrix_prediction(
    task: Task,
    docs: Sequence[AgentDocument],
    gold_docs: Sequence[GoldDocument],
    *,
    retriever: str,
    strategy: str,
    prompt: str,
) -> MatrixPrediction:
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    doc_ids = [doc.doc_id for doc in docs]
    primary = [doc_id for doc_id in task.gold.primary_support if doc_id in doc_ids]
    false_sources = [doc.doc_id for doc in docs if gold_by_id[doc.doc_id].stance == "supports_false_claim"]
    contaminants = [doc.doc_id for doc in docs if gold_by_id[doc.doc_id].is_contaminated]
    false_saturation = len(false_sources) / len(docs) if docs else 0.0
    primary_visible = bool(primary)

    fooled = False
    if task.difficulty == "L4" and retriever == "bm25_top8":
        fooled = strategy in {"naive_bm25", "evidence_graph_v3_bm25"} or (prompt in CLAIM_FIRST_PROMPTS and false_saturation >= 0.75)
    elif task.difficulty == "L3" and retriever == "bm25_top8":
        fooled = strategy in {"naive_bm25", "evidence_graph_v3_bm25"} and false_saturation >= 0.75
    elif task.difficulty == "L2" and strategy == "naive_bm25":
        fooled = bool(false_sources) and not primary_visible
    elif task.difficulty == "L5":
        fooled = prompt in {"simple_answer_v1", "evidence_graph_v3"} and bool(false_sources)

    if fooled:
        verdict = "supported" if task.gold.verdict != "supported" else "refuted"
        support = false_sources[:3]
        rejected = primary[:1]
        confidence = 0.82 if task.difficulty in {"L3", "L4"} else 0.72
        answer = "The retrieved summaries appear to support the claim."
        notes = "Naive reading treated repeated or generated sources as evidence."
    else:
        verdict = task.gold.verdict
        if verdict == "insufficient":
            support = []
            rejected = contaminants[:5]
            confidence = 0.55
        else:
            support = primary[:2] if primary else []
            rejected = contaminants[:5]
            confidence = 0.74 if support else 0.62
        answer = task.gold.answer_brief
        notes = "Current primary evidence was preferred; suspicious sources were rejected."

    return MatrixPrediction(
        claim_verdict=verdict,  # type: ignore[arg-type]
        confidence=confidence,
        supporting_evidence=support,
        rejected_evidence=rejected,
        answer=answer,
        evidence_notes=notes,
    )


def build_messages(prompt: str, question: str, documents: Sequence[AgentDocument], tool_results: Sequence[Mapping[str, Any]]) -> tuple[List[Dict[str, str]], Mapping[str, Any], str]:
    if prompt == "simple_answer_v1":
        return build_simple_answer_messages(question, documents), matrix_prediction_json_schema(), "eha_matrix_prediction"
    if prompt in CLAIM_FIRST_PROMPTS:
        return build_claim_first_messages(question, documents, version=prompt), matrix_prediction_json_schema(), "eha_matrix_prediction"
    if prompt == "evidence_graph_v3":
        return build_phase2r_messages(question, documents, tool_results), phase2r_prediction_json_schema(), "eha_phase2r_prediction"
    raise ValueError(f"unknown Matrix prompt: {prompt}")


def run_final_prediction(
    *,
    backend: str,
    runner: Optional[Phase2OpenAIJsonRunner],
    cost_guard: CostGuard,
    model: str,
    task: Task,
    final_docs: Sequence[AgentDocument],
    gold_docs: Sequence[GoldDocument],
    retriever: str,
    strategy: str,
    prompt: str,
    out_dir: Path,
    max_output_tokens: int,
    temperature: float,
) -> Tuple[MatrixPrediction, bool, Optional[str], Dict[str, Any], float, Optional[str], Optional[str]]:
    if backend == "heuristic":
        prediction = heuristic_matrix_prediction(task, final_docs, gold_docs, retriever=retriever, strategy=strategy, prompt=prompt)
        return normalize_matrix_prediction(prediction, [doc.doc_id for doc in final_docs]), True, None, {}, 0.0, None, None

    assert runner is not None
    messages, schema, schema_name = build_messages(prompt, task.question, final_docs, [])
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
        strategy=strategy,
        suffix=prompt,
        messages=messages,
        response_text=response_text,
        usage=usage,
        response_format=used_format,
    )
    try:
        if prompt == "evidence_graph_v3":
            prediction = phase2_prediction_to_matrix(parse_phase2r_prediction_json(response_text))
        else:
            prediction = parse_matrix_prediction_json(response_text)
        prediction = normalize_matrix_prediction(prediction, [doc.doc_id for doc in final_docs])
        return prediction, True, None, usage, cost_guard.after_call(model, usage), prompt_path, response_path
    except Exception as exc:  # noqa: BLE001
        prediction = MatrixPrediction(
            claim_verdict="insufficient",
            confidence=0.0,
            supporting_evidence=[],
            rejected_evidence=[],
            answer="The model response could not be parsed as the required Matrix v1 JSON object.",
            evidence_notes=response_text[:500],
        )
        return prediction, False, str(exc), usage, cost_guard.after_call(model, usage), prompt_path, response_path


def run_matrix_records(
    *,
    tasks: Sequence[Task],
    docs_by_task_map: Mapping[str, List[AgentDocument]],
    gold_by_task: Mapping[str, List[GoldDocument]],
    backend: str,
    models: Sequence[str],
    out_dir: Path,
    preflight: bool,
    max_output_tokens: int,
    temperature: float,
    timeout_s: float,
    response_format: str,
    cost_guard: CostGuard,
    strategy_names: Sequence[str] | None = None,
    claim_first_prompt: str = "claim_first_citation_v1",
) -> List[MatrixRunRecord]:
    runner = Phase2OpenAIJsonRunner(timeout_s=timeout_s, response_format=response_format) if backend == "api" else None
    specs = apply_claim_first_prompt(select_matrix_specs(preflight=preflight, strategy_names=strategy_names), claim_first_prompt)
    records: List[MatrixRunRecord] = []
    for model in models:
        for task in tasks:
            episode_docs = docs_by_task_map[task.task_id]
            episode_gold = gold_by_task[task.task_id]
            for strategy, retriever, prompt in specs:
                docs = [hit.doc for hit in retrieve(task.question, episode_docs, episode_gold, retriever)]
                prediction, parse_success, parse_error, usage, cost_usd, prompt_path, response_path = run_final_prediction(
                    backend=backend,
                    runner=runner,
                    cost_guard=cost_guard,
                    model=model,
                    task=task,
                    final_docs=docs,
                    gold_docs=episode_gold,
                    retriever=retriever,
                    strategy=strategy,
                    prompt=prompt,
                    out_dir=out_dir,
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                )
                records.append(
                    MatrixRunRecord(
                        task_id=task.task_id,
                        model=model,
                        retriever=retriever,
                        strategy=strategy,
                        prompt=prompt,
                        backend=backend,
                        initial_doc_ids=[doc.doc_id for doc in docs],
                        final_doc_ids=[doc.doc_id for doc in docs],
                        prediction=prediction,
                        parse_success=parse_success,
                        parse_error=parse_error,
                        usage=usage,
                        cost_usd=cost_usd,
                        prompt_path=prompt_path,
                        response_path=response_path,
                    )
                )
                log.info("matrix task={task_id} model={model} strategy={strategy}", task_id=task.task_id, model=model, strategy=strategy)
    return records


@app.command()
def main(
    data_dir: Path = typer.Option(Path("data/matrix-v1"), help="Generated Matrix v1 dataset directory."),
    backend: str = typer.Option("heuristic", help="heuristic or api."),
    models: str = typer.Option("heuristic-sim", help="Comma-separated model names."),
    out_dir: Path = typer.Option(Path("results/runs/matrix-v1"), help="Run output directory."),
    preflight: bool = typer.Option(False, help="Run preflight prompt comparison instead of the main four-strategy table."),
    max_output_tokens: int = typer.Option(2500, help="Maximum model output tokens."),
    temperature: float = typer.Option(0.0, help="Model temperature."),
    timeout_s: float = typer.Option(180.0, help="OpenAI client timeout."),
    response_format: str = typer.Option("json_schema", help="json_schema, json_object, or none."),
    difficulties: str = typer.Option("", help="Optional comma-separated difficulty subset, for example L3,L4,L5."),
    strategies: str = typer.Option("", help="Optional comma-separated strategy subset, for example naive_bm25,primary_preserve,hygienic_combo."),
    claim_first_prompt: str = typer.Option("claim_first_citation_v1", help="claim_first_citation_v1 or claim_first_citation_v1_1."),
    soft_cap_usd: float = typer.Option(75.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(200.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(300.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    if backend not in {"heuristic", "api"}:
        raise typer.BadParameter("backend must be heuristic or api")
    selected_models = split_csv(models)
    if backend == "api" and selected_models == ["heuristic-sim"]:
        selected_models = ["openai/gpt-4o-mini"]

    dataset = load_dataset(data_dir)
    try:
        tasks = filter_tasks_by_difficulties(dataset["tasks"], split_csv(difficulties))
        selected_strategies = split_csv(strategies)
        selected_specs = apply_claim_first_prompt(select_matrix_specs(preflight=preflight, strategy_names=selected_strategies), claim_first_prompt)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    docs_by_task_map = by_task(dataset["documents"])
    gold_by_task = by_task(dataset["gold_documents"])
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    out_dir.mkdir(parents=True, exist_ok=True)

    metric_retrievers = tuple(retriever for retriever in RETRIEVAL_METRIC_RETRIEVERS if retriever in {spec[1] for spec in selected_specs})
    retrieval_rows = compute_retrieval_metrics_for_tasks(tasks, docs_by_task_map, gold_by_task, metric_retrievers)
    write_csv(out_dir / "retrieval_metrics.csv", retrieval_rows)
    try:
        records = run_matrix_records(
            tasks=tasks,
            docs_by_task_map=docs_by_task_map,
            gold_by_task=gold_by_task,
            backend=backend,
            models=selected_models,
            out_dir=out_dir,
            preflight=preflight,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
            response_format=response_format,
            cost_guard=cost_guard,
            strategy_names=selected_strategies,
            claim_first_prompt=claim_first_prompt,
        )
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise typer.Exit(code=2) from exc

    write_jsonl(out_dir / "predictions.jsonl", [model_to_dict(record) for record in records])
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in records), 6), **cost_guard.report()})
    rows = score_matrix_run(records, tasks, dataset["gold_documents"])
    write_csv(out_dir / "scored_predictions.csv", rows)
    if preflight:
        gate = matrix_preflight_gate(rows)
        write_json(out_dir / "preflight_gate.json", {"passed": gate.passed, "checks": gate.checks, "details": gate.details})
        status = "[green]passed[/green]" if gate.passed else "[red]failed[/red]"
        console.print(f"Matrix v1 preflight gate {status}: {gate.details}")
    console.print(f"[green]Wrote[/green] {len(records)} Matrix v1 predictions to {out_dir / 'predictions.jsonl'}")


if __name__ == "__main__":
    app()
