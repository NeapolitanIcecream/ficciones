from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from random import Random
from typing import Any, Dict, Mapping, Sequence

import typer
from rich.console import Console

from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_contract import BASELINE_THRESHOLDS, DEFAULT_REPORT_DATE, DEFAULT_VIEWS, normalized_view_kind, split_csv
from .uncued_generate import load_uncued_dataset


app = typer.Typer(add_completion=False, help="Score no-API shortcut baselines for EHA-Uncued datasets.")
console = Console()

UNCUED_BASELINES = (
    "id_only",
    "document_order_only",
    "title_only",
    "source_type_only",
    "metadata_only",
    "timestamp_only",
    "citation_graph_only",
    "claim_overlap_only",
    "cue_phrase_only",
    "random_valid_schema",
    "always_insufficient",
    "simple_heuristic",
)


def docs_by_task(docs: Sequence[Mapping[str, Any]]) -> Dict[str, list[Mapping[str, Any]]]:
    grouped: Dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for doc in docs:
        grouped[str(doc["task_id"])].append(doc)
    return grouped


def gold_by_view_task(gold_docs: Sequence[Mapping[str, Any]]) -> Dict[tuple[str, str], list[Mapping[str, Any]]]:
    grouped: Dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for gold in gold_docs:
        grouped[(str(gold["view"]), str(gold["task_id"]))].append(gold)
    return grouped


def latent_by_task(latent_tasks: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    return {str(task["task_id"]): task for task in latent_tasks}


def overlap_score(question: str, body: str) -> int:
    q_words = {word.strip(".,?:;()").lower() for word in question.split() if len(word.strip(".,?:;()")) >= 4}
    b_words = {word.strip(".,?:;()").lower() for word in body.split() if len(word.strip(".,?:;()")) >= 4}
    return len(q_words & b_words)


def baseline_prediction(
    baseline: str,
    *,
    task: Mapping[str, Any],
    latent_task: Mapping[str, Any],
    docs: Sequence[Mapping[str, Any]],
    view: str,
) -> Dict[str, Any]:
    doc_ids = [str(doc["doc_id"]) for doc in docs]
    verdict = "supported"
    supporting: list[str] = []
    rejected: list[str] = []
    selected: list[str] = []
    actions: list[Dict[str, str]] = []
    role_guesses = {doc_id: "unknown" for doc_id in doc_ids}

    if baseline == "id_only":
        selected = sorted(doc_ids)[:1]
    elif baseline == "document_order_only":
        selected = doc_ids[:1]
        supporting = doc_ids[:1]
    elif baseline == "title_only":
        verdict = "insufficient"
        selected = [doc["doc_id"] for doc in docs if "Ledger" in str(doc.get("title", ""))][:1]
    elif baseline == "source_type_only":
        selected = [doc["doc_id"] for doc in docs if str(doc.get("source_type")) != "document"][:1]
        verdict = "supported" if selected else "supported"
    elif baseline == "metadata_only":
        selected = sorted(doc_ids)[-1:]
        verdict = "supported"
    elif baseline == "timestamp_only":
        newest = sorted(docs, key=lambda doc: str(doc.get("timestamp", "")), reverse=True)[:1]
        selected = [str(doc["doc_id"]) for doc in newest]
        verdict = "supported"
    elif baseline == "citation_graph_only":
        selected = sorted(doc_ids, key=lambda doc_id: sum(1 for doc in docs if doc_id in doc.get("visible_citations", [])), reverse=True)[:2]
        verdict = "insufficient"
    elif baseline == "claim_overlap_only":
        ranked = sorted(docs, key=lambda doc: overlap_score(str(task["question"]), str(doc.get("body", ""))), reverse=True)
        selected = [str(doc["doc_id"]) for doc in ranked[:2]]
        verdict = "insufficient"
    elif baseline == "cue_phrase_only":
        verdict = "supported"
    elif baseline == "random_valid_schema":
        rng = Random(f"{task['task_id']}:{view}:{baseline}")
        verdict = rng.choice(["supported", "refuted", "insufficient"])
        selected = rng.sample(doc_ids, k=min(1, len(doc_ids))) if doc_ids else []
    elif baseline == "always_insufficient":
        verdict = "insufficient"
    elif baseline == "simple_heuristic":
        question = str(task["question"])
        ranked = sorted(docs, key=lambda doc: overlap_score(question, str(doc.get("body", ""))), reverse=True)
        selected = [str(doc["doc_id"]) for doc in ranked[:3]]
        query_numbers = [token.strip(".,?:;()") for token in question.split() if any(ch.isdigit() for ch in token)]
        bodies = "\n".join(str(doc.get("body", "")) for doc in docs)
        if "launch the" in question and "does not mention" in bodies:
            verdict = "insufficient"
        elif any(number and number in bodies for number in query_numbers):
            verdict = "supported"
            supporting = selected[:1]
        else:
            verdict = "insufficient"
        target = selected[:1]
        if target:
            actions = [{"action": "open_best_visible_record", "target": target[0]}]
            if "launch the" in question:
                actions.append({"action": "trace_visible_citation", "target": target[0]})
    else:
        raise ValueError(f"unknown uncued baseline: {baseline}")

    return {
        "claim_verdict": verdict,
        "supporting_evidence": supporting,
        "rejected_evidence": rejected,
        "selected_doc_ids": selected[:3],
        "actions": actions[:2],
        "role_guesses": role_guesses,
    }


def score_prediction(
    *,
    baseline: str,
    task: Mapping[str, Any],
    latent_task: Mapping[str, Any],
    gold_docs: Sequence[Mapping[str, Any]],
    prediction: Mapping[str, Any],
    view: str,
) -> Dict[str, Any]:
    gold_by_doc = {str(gold["doc_id"]): gold for gold in gold_docs}
    clean_support = {str(gold["doc_id"]) for gold in gold_docs if gold.get("supports_gold_verdict")}
    polluted = {str(gold["doc_id"]) for gold in gold_docs if gold.get("contamination")}
    supporting = [str(doc_id) for doc_id in prediction.get("supporting_evidence", []) if str(doc_id) in gold_by_doc]
    selected = [str(doc_id) for doc_id in prediction.get("selected_doc_ids", []) if str(doc_id) in gold_by_doc]
    actions = prediction.get("actions", [])
    verdict_correct = prediction["claim_verdict"] == latent_task["gold_verdict"]
    support_clean = [doc_id for doc_id in supporting if doc_id in clean_support]
    support_polluted = [doc_id for doc_id in supporting if doc_id in polluted]
    evidence_precision = len(support_clean) / len(supporting) if supporting else 0.0
    clean_support_recall = len(set(support_clean)) / len(clean_support) if clean_support else 1.0 if latent_task["gold_verdict"] == "insufficient" else 0.0
    polluted_support_rate = len(support_polluted) / len(supporting) if supporting else 0.0
    role_guesses = prediction.get("role_guesses", {})
    role_reconstruction_accuracy = (
        sum(1 for doc_id, gold in gold_by_doc.items() if role_guesses.get(doc_id) == gold.get("hidden_role")) / len(gold_by_doc)
        if gold_by_doc
        else 0.0
    )
    if latent_task.get("action_gold_required"):
        required = set()
        if latent_task["gold_verdict"] != "insufficient":
            required.add("open_best_visible_record")
        if latent_task["condition"] in {"conflicting_evidence", "false_consensus", "buried_primary"}:
            required.add("compare_visible_counts")
        if latent_task["condition"] == "generated_lore":
            required.add("trace_visible_citation")
        predicted_actions = {str(action.get("action", "")) for action in actions}
        action_target_score = len(required & predicted_actions) / len(required) if required else 1.0
    else:
        action_target_score = 0.0

    if latent_task["gold_verdict"] == "insufficient":
        evidence_ok = len(supporting) == 0
    else:
        evidence_ok = clean_support_recall > 0.0 and polluted_support_rate == 0.0
    action_ok = action_target_score >= 1.0 if latent_task.get("action_gold_required") else True
    operational_escape = 1.0 if verdict_correct and evidence_ok and action_ok else 0.0

    return {
        "baseline": baseline,
        "view": view,
        "task_id": task["task_id"],
        "family": latent_task["family"],
        "condition": latent_task["condition"],
        "gold_verdict": latent_task["gold_verdict"],
        "predicted_verdict": prediction["claim_verdict"],
        "verdict_accuracy": 1.0 if verdict_correct else 0.0,
        "evidence_precision": evidence_precision,
        "clean_support_recall": clean_support_recall,
        "polluted_support_rate": polluted_support_rate,
        "role_reconstruction_accuracy": role_reconstruction_accuracy,
        "action_target_score": action_target_score,
        "operational_epistemic_escape": operational_escape,
        "supporting_evidence": ",".join(supporting),
        "selected_doc_ids": ",".join(selected),
    }


def aggregate_rows(rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    grouped: Dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["baseline"]), str(row["view"]))].append(row)
    metrics = (
        "verdict_accuracy",
        "evidence_precision",
        "clean_support_recall",
        "polluted_support_rate",
        "role_reconstruction_accuracy",
        "action_target_score",
        "operational_epistemic_escape",
    )
    output: list[Dict[str, Any]] = []
    for (baseline, view), group in sorted(grouped.items()):
        item: Dict[str, Any] = {"baseline": baseline, "view": view, "n": len(group)}
        for metric in metrics:
            item[metric] = sum(float(row[metric]) for row in group) / len(group)
        output.append(item)
    return output


def threshold_key_for_row(row: Mapping[str, Any]) -> str:
    baseline = str(row["baseline"])
    if baseline in {"source_type_only", "metadata_only"}:
        return f"{baseline}:{normalized_view_kind(str(row['view']))}"
    return baseline


def gate_results(aggregate: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    results: list[Dict[str, Any]] = []
    metric_map = {
        "operational_epistemic_escape_max": "operational_epistemic_escape",
        "verdict_accuracy_max": "verdict_accuracy",
        "role_reconstruction_accuracy_max": "role_reconstruction_accuracy",
        "polluted_support_rate_max": "polluted_support_rate",
    }
    for row in aggregate:
        key = threshold_key_for_row(row)
        thresholds = BASELINE_THRESHOLDS.get(key) or BASELINE_THRESHOLDS.get(str(row["baseline"]), {})
        for threshold_name, limit in thresholds.items():
            metric = metric_map[threshold_name]
            value = float(row[metric])
            results.append(
                {
                    "baseline": row["baseline"],
                    "view": row["view"],
                    "metric": metric,
                    "value": value,
                    "limit": limit,
                    "passed": value <= limit,
                }
            )
    return results


def run_baselines(dataset_dir: Path, out_dir: Path, views: Sequence[str]) -> Dict[str, Any]:
    dataset = load_uncued_dataset(dataset_dir)
    task_by_id = {str(task["task_id"]): task for task in dataset["tasks"]}
    latent = latent_by_task(dataset["latent_tasks"])
    gold_grouped = gold_by_view_task(dataset["gold_documents"])
    rows: list[Dict[str, Any]] = []
    for view in views:
        docs_grouped = docs_by_task(dataset["documents_by_view"][view])
        for task_id, task in task_by_id.items():
            for baseline in UNCUED_BASELINES:
                prediction = baseline_prediction(baseline, task=task, latent_task=latent[task_id], docs=docs_grouped[task_id], view=view)
                rows.append(
                    score_prediction(
                        baseline=baseline,
                        task=task,
                        latent_task=latent[task_id],
                        gold_docs=gold_grouped[(view, task_id)],
                        prediction=prediction,
                        view=view,
                    )
                )
    aggregate = aggregate_rows(rows)
    gates = gate_results(aggregate)
    passed = all(bool(row["passed"]) for row in gates)
    payload = {
        "dataset_dir": str(dataset_dir),
        "views": list(views),
        "baselines": list(UNCUED_BASELINES),
        "rows": rows,
        "aggregate": aggregate,
        "gate_results": gates,
        "passed": passed,
    }
    write_baseline_report(out_dir, payload)
    return payload


def write_baseline_report(out_dir: Path, payload: Mapping[str, Any], *, report_date: str = DEFAULT_REPORT_DATE) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_uncued_baselines_micro.json", payload)
    write_csv(out_dir / "uncued_baseline_rows_micro.csv", payload["rows"])
    write_csv(out_dir / "uncued_baseline_aggregate_micro.csv", payload["aggregate"])
    lines = [
        "# EHA-Uncued Micro Shortcut Baselines",
        "",
        f"Date: {report_date}",
        "",
        "## Gate Summary",
        "",
        *markdown_table([{"passed": payload["passed"], "baseline_count": len(payload["baselines"]), "gate_count": len(payload["gate_results"])}], ["passed", "baseline_count", "gate_count"]),
        "",
        "## Aggregate Metrics",
        "",
        *markdown_table(
            payload["aggregate"],
            ["baseline", "view", "n", "verdict_accuracy", "operational_epistemic_escape", "role_reconstruction_accuracy", "polluted_support_rate"],
        ),
        "",
        "## Gate Rows",
        "",
        *markdown_table(payload["gate_results"], ["baseline", "view", "metric", "value", "limit", "passed"]),
        "",
    ]
    (out_dir / f"eha-uncued-baselines-micro-{report_date}.md").write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-micro"), help="Dataset directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Report output directory."),
    views: str = typer.Option(",".join(DEFAULT_VIEWS), help="Comma-separated views."),
) -> None:
    selected_views = split_csv(views)
    payload = run_baselines(dataset_dir, out_dir, selected_views)
    console.print(f"Shortcut baselines passed={payload['passed']} gates={len(payload['gate_results'])}.")
