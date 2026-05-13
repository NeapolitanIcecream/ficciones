from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from random import Random
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import typer
from rich.console import Console

from .matrix_scoring import score_matrix_run
from .matrix_v11 import (
    DEFAULT_V11_SEEDS,
    bootstrap_ci,
    combine_cost_reports,
    collect_multiseed_rows,
    load_matrix_records,
    mean,
    summarize_with_ci,
)
from .report import markdown_table, write_csv
from .scoring import unique
from .schemas import GoldDocument, MatrixRunRecord, Task, gold_by_doc, load_dataset, write_json


app = typer.Typer(add_completion=False, help="Build Matrix paper-consolidation robustness reports.")
console = Console()

PROMPT_HYGIENE_STRATEGIES = {"primary_preserve", "hygienic_combo"}
PROMPT_HYGIENE_MODEL = "openai/gpt-4o-mini"
PROMPT_HYGIENE_BASELINE_PROMPT = "claim_first_citation_v1"
PROMPT_HYGIENE_V11_PROMPT = "claim_first_citation_v1_1"
PAPER_METRICS = ["escape_rate", "claim_accuracy", "contaminated_citation_rate", "generated_lore_overclaim_rate"]
MECHANISM_METRICS = [
    "has_required_supporting_evidence",
    "clean_supporting_evidence",
    "primary_in_context",
    "primary_cited",
    "primary_rejected",
    "primary_ignored",
]


def cluster_bootstrap_ci(
    rows: Sequence[Mapping[str, Any]],
    *,
    metric: str,
    cluster_key: str,
    seed: int = 13901,
    samples: int = 1000,
) -> tuple[float, float]:
    clusters: Dict[Any, List[float]] = defaultdict(list)
    for row in rows:
        if row.get(metric) != "":
            clusters[row[cluster_key]].append(float(row[metric]))
    if not clusters:
        return 0.0, 0.0
    cluster_names = sorted(clusters)
    if len(cluster_names) == 1:
        value = mean(clusters[cluster_names[0]])
        return value, value
    rng = Random(seed)
    estimates: List[float] = []
    for _ in range(samples):
        values: List[float] = []
        for _cluster in cluster_names:
            values.extend(clusters[rng.choice(cluster_names)])
        estimates.append(mean(values))
    estimates.sort()
    lower = estimates[int(0.025 * (len(estimates) - 1))]
    upper = estimates[int(0.975 * (len(estimates) - 1))]
    return lower, upper


def summarize_with_cluster_ci(
    rows: Sequence[Mapping[str, Any]],
    group_keys: Sequence[str],
    metrics: Sequence[str],
    *,
    cluster_key: str,
) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {name: value for name, value in zip(group_keys, key)}
        item["n"] = len(group)
        item["cluster_count"] = len({row[cluster_key] for row in group})
        for metric in metrics:
            values = [float(row[metric]) for row in group if row.get(metric) != ""]
            row_low, row_high = bootstrap_ci(values)
            cluster_low, cluster_high = cluster_bootstrap_ci(group, metric=metric, cluster_key=cluster_key)
            item[metric] = mean(values)
            item[f"{metric}_row_ci_low"] = row_low
            item[f"{metric}_row_ci_high"] = row_high
            item[f"{metric}_cluster_ci_low"] = cluster_low
            item[f"{metric}_cluster_ci_high"] = cluster_high
        output.append(item)
    return output


def matrix_record_mechanism_fields(record: MatrixRunRecord, task: Task, gold_by_id: Mapping[str, GoldDocument]) -> Dict[str, Any]:
    supporting = unique(record.prediction.supporting_evidence)
    supporting_gold = [gold_by_id[doc_id] for doc_id in supporting if doc_id in gold_by_id]
    clean_support = all(not gold.is_contaminated for gold in supporting_gold)
    has_required_support = record.prediction.claim_verdict == "insufficient" or bool(supporting)
    primary_ids = set(task.gold.primary_support)
    final_doc_ids = list(record.final_doc_ids)
    primary_ranks = [idx + 1 for idx, doc_id in enumerate(final_doc_ids) if doc_id in primary_ids]
    primary_in_context = bool(primary_ranks)
    primary_cited = bool(set(supporting) & primary_ids)
    primary_rejected = bool(set(record.prediction.rejected_evidence) & primary_ids)
    primary_ignored = primary_in_context and not primary_cited and not primary_rejected
    return {
        "has_required_supporting_evidence": 1.0 if has_required_support else 0.0,
        "clean_supporting_evidence": 1.0 if clean_support else 0.0,
        "primary_in_context": 1.0 if primary_in_context else 0.0,
        "primary_cited": 1.0 if primary_cited else 0.0,
        "primary_rejected": 1.0 if primary_rejected else 0.0,
        "primary_ignored": 1.0 if primary_ignored else 0.0,
        "best_primary_context_rank": min(primary_ranks) if primary_ranks else "",
        "primary_support": ",".join(task.gold.primary_support),
        "final_doc_ids": ",".join(final_doc_ids),
    }


def score_records_with_mechanisms(
    records: Sequence[MatrixRunRecord],
    tasks: Sequence[Task],
    gold_documents: Sequence[GoldDocument],
) -> List[Dict[str, Any]]:
    task_by_id = {task.task_id: task for task in tasks}
    gold_by_id = gold_by_doc(gold_documents)
    scored = {
        (row["task_id"], row["model"], row["strategy"], row["prompt"]): row
        for row in score_matrix_run(records, tasks, gold_documents)
    }
    rows: List[Dict[str, Any]] = []
    for record in records:
        task = task_by_id[record.task_id]
        row = dict(scored[(record.task_id, record.model, record.strategy, record.prompt)])
        row.update(matrix_record_mechanism_fields(record, task, gold_by_id))
        rows.append(row)
    return rows


def prompt_hygiene_preflight_rows(
    *,
    data_dir: Path,
    run_dir: Path,
    baseline_data_dir: Path,
    baseline_run_dir: Path,
) -> List[Dict[str, Any]]:
    prompt_dataset = load_dataset(data_dir)
    task_ids = {task.task_id for task in prompt_dataset["tasks"]}
    rows: List[Dict[str, Any]] = []

    v11_records = load_matrix_records(run_dir)
    for row in score_records_with_mechanisms(v11_records, prompt_dataset["tasks"], prompt_dataset["gold_documents"]):
        item = dict(row)
        item["prompt_version"] = PROMPT_HYGIENE_V11_PROMPT
        rows.append(item)

    baseline_dataset = load_dataset(baseline_data_dir)
    baseline_records = [
        record
        for record in load_matrix_records(baseline_run_dir)
        if record.task_id in task_ids
        and record.model == PROMPT_HYGIENE_MODEL
        and record.strategy in PROMPT_HYGIENE_STRATEGIES
        and record.prompt == PROMPT_HYGIENE_BASELINE_PROMPT
    ]
    for row in score_records_with_mechanisms(baseline_records, baseline_dataset["tasks"], baseline_dataset["gold_documents"]):
        item = dict(row)
        item["prompt_version"] = PROMPT_HYGIENE_BASELINE_PROMPT
        rows.append(item)
    return rows


def aggregate_prompt_hygiene(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    base = summarize_with_ci(
        rows,
        ["prompt_version", "model", "strategy", "difficulty"],
        ["escape_rate", "claim_accuracy", "contaminated_citation_rate", "generated_lore_overclaim_rate", "over_abstention_rate"],
    )
    mechanism = {
        tuple(row[key] for key in ["prompt_version", "model", "strategy", "difficulty"]): row
        for row in summarize_plain(
            rows,
            ["prompt_version", "model", "strategy", "difficulty"],
            ["has_required_supporting_evidence", "clean_supporting_evidence", "primary_in_context", "primary_cited", "primary_ignored"],
        )
    }
    output: List[Dict[str, Any]] = []
    for row in base:
        item = dict(row)
        item.update(mechanism[tuple(row[key] for key in ["prompt_version", "model", "strategy", "difficulty"])])
        output.append(item)
    return output


def summarize_plain(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str], metrics: Sequence[str]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {name: value for name, value in zip(group_keys, key)}
        for metric in metrics:
            item[metric] = mean([float(row[metric]) for row in group if row.get(metric) != ""])
        output.append(item)
    return output


def l4_primary_recovery_rows(data_dir: Path, run_dir: Path) -> List[Dict[str, Any]]:
    dataset = load_dataset(data_dir)
    records = [record for record in load_matrix_records(run_dir) if record.task_id in {task.task_id for task in dataset["tasks"]}]
    rows = score_records_with_mechanisms(records, dataset["tasks"], dataset["gold_documents"])
    return [row for row in rows if row["difficulty"] == "L4"]


def aggregate_l4_primary_recovery(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["strategy"], row["prompt"], row["retriever"])].append(row)
    output: List[Dict[str, Any]] = []
    metrics = ["claim_accuracy", "escape_rate", "contaminated_citation_rate", *MECHANISM_METRICS]
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {name: value for name, value in zip(["model", "strategy", "prompt", "retriever"], key)}
        item["n"] = len(group)
        for metric in metrics:
            values = [float(row[metric]) for row in group if row.get(metric) != ""]
            low, high = bootstrap_ci(values)
            item[metric] = mean(values)
            item[f"{metric}_ci_low"] = low
            item[f"{metric}_ci_high"] = high
        ranks = [float(row["best_primary_context_rank"]) for row in group if row.get("best_primary_context_rank") != ""]
        item["primary_rank_n"] = len(ranks)
        item["mean_best_primary_context_rank"] = mean(ranks) if ranks else ""
        output.append(item)
    return output


def write_paper_pack_summary(
    path: Path,
    *,
    cluster_ci: Sequence[Mapping[str, Any]],
    prompt_hygiene: Sequence[Mapping[str, Any]],
    l4_audit: Sequence[Mapping[str, Any]],
    cost_report: Mapping[str, Any],
) -> None:
    lines = ["# Matrix Paper Consolidation Pack", ""]
    lines.extend(["## 1. Seed-Cluster Confidence Intervals", ""])
    lines.extend(
        markdown_table(
            cluster_ci,
            [
                "model",
                "strategy",
                "difficulty",
                "n",
                "cluster_count",
                "escape_rate",
                "escape_rate_cluster_ci_low",
                "escape_rate_cluster_ci_high",
                "claim_accuracy",
                "claim_accuracy_cluster_ci_low",
                "claim_accuracy_cluster_ci_high",
            ],
        )
    )
    lines.extend(["", "## 2. Prompt v1.1 + Hygiene Preflight", ""])
    lines.extend(
        markdown_table(
            prompt_hygiene,
            [
                "prompt_version",
                "strategy",
                "difficulty",
                "n",
                "escape_rate",
                "claim_accuracy",
                "contaminated_citation_rate",
                "generated_lore_overclaim_rate",
                "over_abstention_rate",
                "has_required_supporting_evidence",
                "clean_supporting_evidence",
                "primary_in_context",
                "primary_cited",
            ],
        )
    )
    lines.extend(["", "## 3. L4 Primary Recovery Audit", ""])
    lines.extend(
        markdown_table(
            l4_audit,
            [
                "model",
                "strategy",
                "prompt",
                "retriever",
                "n",
                "primary_in_context",
                "primary_cited",
                "primary_ignored",
                "claim_accuracy",
                "escape_rate",
                "contaminated_citation_rate",
                "mean_best_primary_context_rank",
            ],
        )
    )
    lines.extend(["", "## 4. New API Cost", "", "```json", json.dumps(cost_report, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_audit_manifest(path: Path, *, inputs: Mapping[str, Any], outputs: Mapping[str, Any], cost_report: Mapping[str, Any]) -> None:
    write_json(
        path,
        {
            "pack": "matrix-paper-consolidation-0513-5",
            "inputs": inputs,
            "outputs": outputs,
            "cost_report": cost_report,
        },
    )


@app.command("report")
def report(
    out_dir: Path = typer.Option(Path("results/reports-matrix-v1.2"), help="Report output directory."),
    multiseed_data_root: Path = typer.Option(Path("data/matrix-v1.1/multiseed"), help="Per-seed dataset root."),
    multiseed_run_root: Path = typer.Option(Path("results/runs/matrix-v1.1/multiseed"), help="Per-seed Matrix v1.1 run root."),
    prompt_data_dir: Path = typer.Option(Path("data/matrix-v1.1/prompt-v1_1-preflight"), help="Prompt preflight subset."),
    prompt_run_dir: Path = typer.Option(Path("results/runs/matrix-v1.2/prompt-v1_1-hygiene-preflight"), help="Prompt+hygiene v1.1 run."),
    main_data_dir: Path = typer.Option(Path("data/matrix-v1"), help="Matrix v1 main dataset."),
    main_run_dir: Path = typer.Option(Path("results/runs/matrix-v1-main"), help="Matrix v1 merged main run."),
    seeds: str = typer.Option("9201,9202,9203", help="Comma-separated seeds used for multiseed runs."),
) -> None:
    selected_seeds = [int(seed) for seed in seeds.split(",") if seed.strip()] if seeds else list(DEFAULT_V11_SEEDS)
    multiseed_rows = collect_multiseed_rows(multiseed_data_root, multiseed_run_root, selected_seeds)
    cluster_ci = summarize_with_cluster_ci(
        multiseed_rows,
        ["model", "strategy", "difficulty"],
        PAPER_METRICS,
        cluster_key="seed",
    )
    prompt_rows = prompt_hygiene_preflight_rows(
        data_dir=prompt_data_dir,
        run_dir=prompt_run_dir,
        baseline_data_dir=main_data_dir,
        baseline_run_dir=main_run_dir,
    )
    prompt_hygiene = aggregate_prompt_hygiene(prompt_rows)
    l4_rows = l4_primary_recovery_rows(main_data_dir, main_run_dir)
    l4_audit = aggregate_l4_primary_recovery(l4_rows)
    cost_report = combine_cost_reports([prompt_run_dir / "cost_report.json"])

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "multiseed_cluster_ci.csv", cluster_ci)
    write_csv(out_dir / "prompt_hygiene_preflight.csv", prompt_hygiene)
    write_csv(out_dir / "prompt_hygiene_preflight_rows.csv", prompt_rows)
    write_csv(out_dir / "l4_primary_recovery_audit.csv", l4_audit)
    write_csv(out_dir / "l4_primary_recovery_audit_rows.csv", l4_rows)
    write_json(out_dir / "cost_report.json", cost_report)
    write_paper_pack_summary(out_dir / "summary.md", cluster_ci=cluster_ci, prompt_hygiene=prompt_hygiene, l4_audit=l4_audit, cost_report=cost_report)
    write_audit_manifest(
        out_dir / "audit_manifest.json",
        inputs={
            "multiseed_data_root": str(multiseed_data_root),
            "multiseed_run_root": str(multiseed_run_root),
            "prompt_data_dir": str(prompt_data_dir),
            "prompt_run_dir": str(prompt_run_dir),
            "main_data_dir": str(main_data_dir),
            "main_run_dir": str(main_run_dir),
            "seeds": selected_seeds,
        },
        outputs={
            "multiseed_cluster_ci_rows": len(cluster_ci),
            "prompt_hygiene_preflight_rows": len(prompt_hygiene),
            "prompt_hygiene_raw_rows": len(prompt_rows),
            "l4_primary_recovery_audit_rows": len(l4_audit),
            "l4_primary_recovery_raw_rows": len(l4_rows),
        },
        cost_report=cost_report,
    )
    console.print(f"[green]Wrote Matrix paper-consolidation reports[/green] to {out_dir}")


if __name__ == "__main__":
    app()
