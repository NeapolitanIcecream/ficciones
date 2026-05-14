from __future__ import annotations

import json
import os
import re
import shlex
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from urllib.parse import urlparse

import openai
import typer
from loguru import logger
from openai import OpenAI
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard, estimate_tokens, usage_value
from .prompts import build_messages, parse_prediction_json, prediction_json_schema
from .retrieval import search_episode, selected_docs
from .schemas import (
    AgentDocument,
    DependencyEdge,
    GoldDocument,
    Prediction,
    RunRecord,
    STRATEGIES,
    Task,
    by_task,
    load_dataset,
    model_to_dict,
    write_json,
    write_jsonl,
)
from .scoring import pilot_gate, score_run, wrong_verdict_for


app = typer.Typer(add_completion=False, help="Run EHA evaluations.")
console = Console()
log = logger.bind(module="eha.run_eval")


def load_zshrc_env(names: Iterable[str], zshrc_path: Optional[Path] = None) -> Dict[str, str]:
    wanted = set(names)
    path = zshrc_path or (Path.home() / ".zshrc")
    found: Dict[str, str] = {}
    if not path.exists():
        return found
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line.startswith("export "):
            continue
        try:
            parts = shlex.split(line[len("export ") :], posix=True)
        except ValueError:
            continue
        for part in parts:
            if "=" not in part:
                continue
            name, value = part.split("=", 1)
            if name in wanted and name not in found:
                found[name] = value
    return found


def openai_config(zshrc_path: Optional[Path] = None) -> Tuple[str, str]:
    api_key = os.environ.get("LLM_API_KEY")
    base_url = os.environ.get("LLM_BASE_URL")
    if api_key and base_url:
        return api_key, normalize_openai_base_url(base_url)

    zshrc = load_zshrc_env(("LLM_API_KEY", "LLM_BASE_URL"), zshrc_path)
    api_key = api_key or zshrc.get("LLM_API_KEY")
    base_url = base_url or zshrc.get("LLM_BASE_URL")
    missing = [name for name, value in (("LLM_API_KEY", api_key), ("LLM_BASE_URL", base_url)) if not value]
    if missing:
        raise RuntimeError(f"Missing {', '.join(missing)} in environment or ~/.zshrc.")
    return api_key, normalize_openai_base_url(base_url)


def normalize_openai_base_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    path = parsed.path.rstrip("/")
    if not path:
        return base_url.rstrip("/") + "/v1"
    return base_url.rstrip("/")


def split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def task_index(task: Task) -> int:
    try:
        return int(task.task_id.rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return 0


def edge_predictions_from_visible_docs(docs: Sequence[AgentDocument]) -> List[DependencyEdge]:
    doc_ids = {doc.doc_id for doc in docs}
    edges: List[DependencyEdge] = []
    for doc in docs:
        for citation in doc.visible_citations:
            if citation in doc_ids:
                relation = "repost" if doc.source_type in {"blog_repost", "trade_news", "vendor_brief", "forum_digest"} else "cites"
                edges.append(DependencyEdge(from_doc=doc.doc_id, to_doc=citation, relation=relation))
    return edges


def make_prediction(
    *,
    verdict: str,
    confidence: float,
    support: Sequence[str],
    rejected: Sequence[str],
    docs: Sequence[AgentDocument],
    answer: str,
    source_independence: str,
    contamination_notes: str,
    remaining_uncertainties: str,
    include_edges: bool,
) -> Prediction:
    edges = edge_predictions_from_visible_docs(docs) if include_edges else []
    return Prediction(
        verdict=verdict,  # type: ignore[arg-type]
        confidence=max(0.0, min(1.0, confidence)),
        supporting_evidence=list(support),
        rejected_evidence=list(rejected),
        predicted_dependency_edges=edges,
        source_independence=source_independence,
        contamination_notes=contamination_notes,
        remaining_uncertainties=remaining_uncertainties,
        answer=answer,
    )


def heuristic_prediction(task: Task, strategy: str, docs: Sequence[AgentDocument], gold_docs: Sequence[GoldDocument]) -> Prediction:
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    retrieved_ids = [doc.doc_id for doc in docs]
    primary = [doc_id for doc_id in task.gold.primary_support if doc_id in retrieved_ids] or task.gold.primary_support[:1]
    false_sources = [doc.doc_id for doc in docs if gold_by_id[doc.doc_id].stance == "supports_false_claim"]
    contaminants = [doc.doc_id for doc in docs if gold_by_id[doc.doc_id].is_contaminated]
    index = task_index(task)

    if strategy in {"topk_rag", "citation_prompt"}:
        fooled = task.episode_type != "clean_control" and len(false_sources) >= max(1, len(primary))
        verdict = wrong_verdict_for(task.gold.verdict) if fooled else task.gold.verdict
        if strategy == "citation_prompt" and task.episode_type == "clean_control" and contaminants:
            support = primary[:2] + contaminants[:1]
            rejected = [doc_id for doc_id in contaminants if doc_id not in set(support)][:3]
        else:
            support = false_sources[:4] if fooled else primary[:2]
            rejected = primary[:2] if fooled else contaminants[:3]
        confidence = min(0.92, 0.66 + 0.035 * len(support)) if fooled else 0.72
        return make_prediction(
            verdict=verdict,
            confidence=confidence,
            support=support,
            rejected=rejected,
            docs=docs,
            answer=("The retrieved summaries appear to support the claim." if fooled else task.gold.answer_brief),
            source_independence="Not analyzed." if strategy == "topk_rag" else "Citations listed without upstream independence analysis.",
            contamination_notes="Polluted summaries were treated as evidence." if fooled else "No major contamination used.",
            remaining_uncertainties="Limited to top-k retrieved documents.",
            include_edges=False,
        )

    if strategy == "source_independence_prompt":
        fooled = task.episode_type == "mixed_source_corruption" and index % 2 == 0
        verdict = wrong_verdict_for(task.gold.verdict) if fooled else task.gold.verdict
        support = false_sources[:2] if fooled else primary[:2]
        rejected = primary[:1] if fooled else contaminants[:4]
        return make_prediction(
            verdict=verdict,
            confidence=0.64 if fooled else 0.68,
            support=support,
            rejected=rejected,
            docs=docs,
            answer=("The official-looking appendix is treated as decisive." if fooled else task.gold.answer_brief),
            source_independence="Repeated summaries share upstream roots; primary records are preferred.",
            contamination_notes="Flags reposts, stale documents, and missing primary support.",
            remaining_uncertainties="Some secondary records are plausible but non-independent.",
            include_edges=True,
        )

    fooled = task.episode_type == "citation_laundering" and index % 12 == 2
    verdict = "insufficient" if fooled else task.gold.verdict
    support = false_sources[:1] if fooled else primary[:2]
    rejected = primary[:1] if fooled else contaminants[:5]
    return make_prediction(
        verdict=verdict,
        confidence=0.58 if fooled else 0.71,
        support=support,
        rejected=rejected,
        docs=docs,
        answer=("The citation chain is ambiguous enough to abstain." if fooled else task.gold.answer_brief),
        source_independence="Evidence graph separates roots from reposts and treats shared upstream as one source.",
        contamination_notes="Rejected non-primary reposts, stale records, and generated lore where present.",
        remaining_uncertainties="Remaining uncertainty is limited to unobserved records outside the synthetic corpus.",
        include_edges=True,
    )


def usage_to_dict(usage: object) -> Dict[str, Any]:
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    if isinstance(usage, Mapping):
        return dict(usage)
    return {
        "prompt_tokens": usage_value(usage, "prompt_tokens"),
        "completion_tokens": usage_value(usage, "completion_tokens"),
        "total_tokens": usage_value(usage, "total_tokens"),
    }


def normalize_doc_ref(value: str, allowed_doc_ids: Sequence[str]) -> Optional[str]:
    if value in allowed_doc_ids:
        return value
    for doc_id in allowed_doc_ids:
        if re.search(rf"(?<![A-Za-z0-9_]){re.escape(doc_id)}(?![A-Za-z0-9_])", value):
            return doc_id
    return None


def normalize_prediction_doc_refs(prediction: Prediction, allowed_doc_ids: Sequence[str]) -> Prediction:
    support = [doc_id for item in prediction.supporting_evidence if (doc_id := normalize_doc_ref(item, allowed_doc_ids))]
    rejected = [doc_id for item in prediction.rejected_evidence if (doc_id := normalize_doc_ref(item, allowed_doc_ids))]
    allowed = set(allowed_doc_ids)
    edges = [
        edge
        for edge in prediction.predicted_dependency_edges
        if edge.from_doc in allowed and edge.to_doc in allowed
    ]
    return prediction.model_copy(
        update={
            "supporting_evidence": support,
            "rejected_evidence": rejected,
            "predicted_dependency_edges": edges,
        }
    )


class OpenAIJsonRunner:
    def __init__(self, timeout_s: float, response_format: str) -> None:
        api_key, base_url = openai_config()
        kwargs: Dict[str, Any] = {"api_key": api_key, "base_url": base_url, "timeout": timeout_s}
        self.client = OpenAI(**kwargs)
        self.response_format = response_format

    def _response_format_payload(self, mode: str) -> Optional[Dict[str, Any]]:
        if mode == "none":
            return None
        if mode == "json_object":
            return {"type": "json_object"}
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "eha_prediction",
                "strict": True,
                "schema": prediction_json_schema(),
            },
        }

    def complete(
        self,
        *,
        model: str,
        messages: Sequence[Dict[str, str]],
        max_output_tokens: int,
        temperature: float,
    ) -> Tuple[str, Dict[str, Any], str]:
        mode = self.response_format
        kwargs: Dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "temperature": temperature,
            "max_completion_tokens": max_output_tokens,
        }
        payload = self._response_format_payload(mode)
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
                if exc.status_code == 400 and mode == "json_schema":
                    kwargs["response_format"] = {"type": "json_object"}
                    completion = self.client.chat.completions.create(**kwargs)
                    mode = "json_object"
                    break
                raise
        content = completion.choices[0].message.content or ""
        return content, usage_to_dict(completion.usage), mode


def call_artifact_paths(out_dir: Path, *, task_id: str, model: str, strategy: str) -> Tuple[Path, Path]:
    safe_model = model.replace("/", "_")
    base = out_dir / "artifacts" / safe_model / strategy
    return base / f"{task_id}.prompt.json", base / f"{task_id}.response.json"


def write_call_artifacts(
    out_dir: Path,
    *,
    task_id: str,
    model: str,
    strategy: str,
    messages: Sequence[Dict[str, str]],
    response_text: str,
    usage: Mapping[str, Any],
    response_format: str,
) -> Tuple[str, str]:
    prompt_path, response_path = call_artifact_paths(out_dir, task_id=task_id, model=model, strategy=strategy)
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        prompt_path,
        {
            "task_id": task_id,
            "model": model,
            "strategy": strategy,
            "messages": list(messages),
            "response_format": response_format,
        },
    )
    write_json(
        response_path,
        {
            "task_id": task_id,
            "model": model,
            "strategy": strategy,
            "response_text": response_text,
            "usage": dict(usage),
        },
    )
    return str(prompt_path), str(response_path)


def record_from_artifact(
    *,
    out_dir: Path,
    task: Task,
    model: str,
    strategy: str,
    retrieved_doc_ids: Sequence[str],
) -> Optional[RunRecord]:
    prompt_path, response_path = call_artifact_paths(out_dir, task_id=task.task_id, model=model, strategy=strategy)
    if not response_path.exists():
        return None
    payload = json.loads(response_path.read_text(encoding="utf-8"))
    response_text = str(payload.get("response_text", ""))
    usage = dict(payload.get("usage") or {})
    try:
        prediction = normalize_prediction_doc_refs(parse_prediction_json(response_text), retrieved_doc_ids)
        parse_success = True
        parse_error = None
    except Exception as exc:  # noqa: BLE001 - recovered parse diagnostic
        prediction = Prediction(
            verdict="insufficient",
            confidence=0.0,
            supporting_evidence=[],
            rejected_evidence=[],
            predicted_dependency_edges=[],
            source_independence="Parse failure.",
            contamination_notes="Parse failure.",
            remaining_uncertainties=response_text[:500],
            answer="The stored model response could not be parsed as the required JSON object.",
        )
        parse_success = False
        parse_error = str(exc)
    cost_usd = float(usage.get("cost", 0.0)) if isinstance(usage.get("cost"), (int, float)) else 0.0
    return RunRecord(
        task_id=task.task_id,
        model=model,
        strategy=strategy,  # type: ignore[arg-type]
        backend="api",
        retrieved_doc_ids=list(retrieved_doc_ids),
        prediction=prediction,
        parse_success=parse_success,
        parse_error=parse_error,
        usage=usage,
        cost_usd=cost_usd,
        prompt_path=str(prompt_path) if prompt_path.exists() else None,
        response_path=str(response_path),
    )


def run_records(
    *,
    tasks: Sequence[Task],
    docs_by_task: Mapping[str, List[AgentDocument]],
    gold_by_task: Mapping[str, List[GoldDocument]],
    backend: str,
    models: Sequence[str],
    strategies: Sequence[str],
    out_dir: Path,
    top_k: int,
    max_output_tokens: int,
    temperature: float,
    timeout_s: float,
    response_format: str,
    cost_guard: CostGuard,
    resume: bool,
) -> List[RunRecord]:
    runner = OpenAIJsonRunner(timeout_s=timeout_s, response_format=response_format) if backend == "api" else None
    records: List[RunRecord] = []
    for model in models:
        for task in tasks:
            hits = search_episode(task.question, docs_by_task[task.task_id], gold_by_task[task.task_id], top_k=top_k)
            retrieved_docs = selected_docs(hits)
            retrieved_doc_ids = [doc.doc_id for doc in retrieved_docs]
            for strategy in strategies:
                if backend == "api" and resume:
                    recovered = record_from_artifact(
                        out_dir=out_dir,
                        task=task,
                        model=model,
                        strategy=strategy,
                        retrieved_doc_ids=retrieved_doc_ids,
                    )
                    if recovered is not None:
                        records.append(recovered)
                        log.info(
                            "recovered task={task_id} model={model} strategy={strategy} backend=api",
                            task_id=task.task_id,
                            model=model,
                            strategy=strategy,
                        )
                        continue
                parse_success = True
                parse_error = None
                usage: Dict[str, Any] = {}
                cost_usd = 0.0
                prompt_path = None
                response_path = None
                if backend == "heuristic":
                    prediction = heuristic_prediction(task, strategy, retrieved_docs, gold_by_task[task.task_id])
                else:
                    assert runner is not None
                    messages = build_messages(strategy, task.question, retrieved_docs)
                    prompt_text = json.dumps(messages, ensure_ascii=False)
                    cost_guard.before_call(model, prompt_text, max_output_tokens)
                    response_text, usage, used_format = runner.complete(
                        model=model,
                        messages=messages,
                        max_output_tokens=max_output_tokens,
                        temperature=temperature,
                    )
                    prompt_path, response_path = write_call_artifacts(
                        out_dir,
                        task_id=task.task_id,
                        model=model,
                        strategy=strategy,
                        messages=messages,
                        response_text=response_text,
                        usage=usage,
                        response_format=used_format,
                    )
                    try:
                        prediction = normalize_prediction_doc_refs(parse_prediction_json(response_text), retrieved_doc_ids)
                    except Exception as exc:  # noqa: BLE001 - stored as machine-readable parse diagnostic
                        parse_success = False
                        parse_error = str(exc)
                        prediction = Prediction(
                            verdict="insufficient",
                            confidence=0.0,
                            supporting_evidence=[],
                            rejected_evidence=[],
                            predicted_dependency_edges=[],
                            source_independence="Parse failure.",
                            contamination_notes="Parse failure.",
                            remaining_uncertainties=response_text[:500],
                            answer="The model response could not be parsed as the required JSON object.",
                        )
                    cost_usd = cost_guard.after_call(model, usage)
                record = RunRecord(
                    task_id=task.task_id,
                    model=model,
                    strategy=strategy,  # type: ignore[arg-type]
                    backend=backend,
                    retrieved_doc_ids=retrieved_doc_ids,
                    prediction=prediction,
                    parse_success=parse_success,
                    parse_error=parse_error,
                    usage=usage,
                    cost_usd=cost_usd,
                    prompt_path=prompt_path,
                    response_path=response_path,
                )
                records.append(record)
                log.info(
                    "evaluated task={task_id} model={model} strategy={strategy} backend={backend} prompt_tokens_est={prompt_tokens}",
                    task_id=task.task_id,
                    model=model,
                    strategy=strategy,
                    backend=backend,
                    prompt_tokens=estimate_tokens(json.dumps(retrieved_doc_ids)),
                )
    return records


@app.command()
def main(
    data_dir: Path = typer.Option(Path("data/generated"), help="Generated dataset directory."),
    backend: str = typer.Option("heuristic", help="Evaluation backend: heuristic or api."),
    models: str = typer.Option("heuristic-sim", help="Comma-separated model names."),
    strategies: str = typer.Option(",".join(STRATEGIES), help="Comma-separated strategy names."),
    out_dir: Path = typer.Option(Path("results/runs/pilot"), help="Run output directory."),
    pilot: bool = typer.Option(False, help="Run only the first 12 episodes and write pilot gate diagnostics."),
    top_k: int = typer.Option(8, help="Retrieved documents per episode."),
    max_output_tokens: int = typer.Option(6000, help="Maximum model output tokens, including reasoning tokens on reasoning models."),
    temperature: float = typer.Option(0.0, help="Model temperature."),
    timeout_s: float = typer.Option(120.0, help="OpenAI client timeout."),
    response_format: str = typer.Option("json_schema", help="json_schema, json_object, or none."),
    resume: bool = typer.Option(True, help="Reuse existing prompt/response artifacts and run only missing calls."),
    soft_cap_usd: float = typer.Option(100.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(250.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(300.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    if backend not in {"heuristic", "api"}:
        raise typer.BadParameter("backend must be heuristic or api")
    selected_strategies = split_csv(strategies)
    unknown = sorted(set(selected_strategies) - set(STRATEGIES))
    if unknown:
        raise typer.BadParameter(f"unknown strategies: {', '.join(unknown)}")
    selected_models = split_csv(models)
    if backend == "api" and selected_models == ["heuristic-sim"]:
        selected_models = ["gpt-5-mini", "gpt-5.4-mini"]

    dataset = load_dataset(data_dir)
    tasks: List[Task] = dataset["tasks"]
    if pilot:
        tasks = tasks[:12]
    docs_by_task = by_task(dataset["documents"])
    gold_by_task = by_task(dataset["gold_documents"])
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)

    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        records = run_records(
            tasks=tasks,
            docs_by_task=docs_by_task,
            gold_by_task=gold_by_task,
            backend=backend,
            models=selected_models,
            strategies=selected_strategies,
            out_dir=out_dir,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
            response_format=response_format,
            cost_guard=cost_guard,
            resume=resume,
        )
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise typer.Exit(code=2) from exc

    write_jsonl(out_dir / "predictions.jsonl", [model_to_dict(record) for record in records])
    total_record_cost = sum(record.cost_usd for record in records)
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(total_record_cost, 6), **cost_guard.report()})
    if pilot:
        rows = score_run(records, tasks, dataset["gold_documents"], dataset["edges"])
        gate = pilot_gate(rows, tasks, dataset["gold_documents"])
        write_json(out_dir / "pilot_gate.json", {"passed": gate.passed, "checks": gate.checks, "details": gate.details})
        status = "[green]passed[/green]" if gate.passed else "[red]failed[/red]"
        console.print(f"Pilot gate {status}: {gate.details}")
    console.print(f"[green]Wrote[/green] {len(records)} predictions to {out_dir / 'predictions.jsonl'}")


if __name__ == "__main__":
    app()
