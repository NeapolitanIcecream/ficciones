from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from random import Random
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import typer
from rich.console import Console

from .matrix_generate import generate_matrix_dataset, write_matrix_dataset
from .matrix_scoring import is_l5, score_matrix_run
from .phase2_run import split_csv
from .report import markdown_table, write_csv
from .scoring import unique
from .schemas import (
    AgentDocument,
    DependencyEdge,
    GoldDocument,
    Manifest,
    MatrixRunRecord,
    Task,
    gold_by_doc,
    load_dataset,
    model_to_dict,
    read_json,
    read_jsonl,
    write_json,
)


app = typer.Typer(add_completion=False, help="Prepare and report Matrix v1.1 robustness-pack experiments.")
console = Console()

DEFAULT_V11_SEEDS = (9201, 9202, 9203)
DEFAULT_NOISE_LEVELS = (0, 10, 25, 50)
CRITICAL_DIFFICULTIES = ("L3", "L4", "L5")
PROMPT_PREFLIGHT_DIFFICULTIES = ("L0", "L3", "L4", "L5")
REPOST_SOURCE_TYPES = {"blog_repost", "trade_news", "vendor_brief", "forum_digest"}
SECONDARY_SOURCE_TYPES = ("trade_news", "industry_blog", "blog_repost")
AUTHORITY_SOURCE_TYPES = ("official_report", "regulatory_filing", "audit_report", "press_release")


def parse_int_csv(value: str, default: Sequence[int]) -> List[int]:
    if not value:
        return list(default)
    return [int(item) for item in split_csv(value)]


def select_tasks_by_difficulty_limit(tasks: Sequence[Task], difficulties: Sequence[str], per_difficulty: int | None = None) -> List[Task]:
    wanted = set(difficulties)
    counts: Counter[str] = Counter()
    selected: List[Task] = []
    for task in tasks:
        if task.difficulty not in wanted:
            continue
        if per_difficulty is not None and counts[task.difficulty] >= per_difficulty:
            continue
        selected.append(task)
        counts[task.difficulty] += 1
    missing = {difficulty for difficulty in difficulties if counts[difficulty] == 0}
    if missing:
        raise ValueError(f"missing requested difficulties: {', '.join(sorted(missing))}")
    return selected


def filter_dataset(
    *,
    manifest: Manifest,
    tasks: Sequence[Task],
    documents: Sequence[AgentDocument],
    gold_documents: Sequence[GoldDocument],
    edges: Sequence[DependencyEdge],
    selected_tasks: Sequence[Task],
    name: str,
    notes: str,
) -> tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    task_ids = {task.task_id for task in selected_tasks}
    selected_docs = [doc for doc in documents if doc.task_id in task_ids]
    selected_doc_ids = {doc.doc_id for doc in selected_docs}
    selected_gold = [doc for doc in gold_documents if doc.task_id in task_ids]
    selected_edges = [edge for edge in edges if edge.from_doc in selected_doc_ids and edge.to_doc in selected_doc_ids]
    manifest_payload = model_to_dict(manifest) if isinstance(manifest, Manifest) else dict(manifest)
    manifest_payload.update(
        {
            "name": name,
            "episodes": len(selected_tasks),
            "created_by": "eha.matrix_v11",
            "notes": notes,
            "episode_type_counts": dict(Counter(task.episode_type for task in selected_tasks)),
        }
    )
    filtered_manifest = Manifest.model_validate(manifest_payload)
    return filtered_manifest, list(selected_tasks), selected_docs, selected_gold, selected_edges


def _sample_doc_ids(rng: Random, candidates: Sequence[str], fraction: float) -> set[str]:
    if fraction <= 0 or not candidates:
        return set()
    count = max(1, round(len(candidates) * fraction))
    return set(rng.sample(list(candidates), min(len(candidates), count)))


def apply_metadata_noise(
    documents: Sequence[AgentDocument],
    gold_documents: Sequence[GoldDocument],
    *,
    noise_level: int,
    seed: int,
) -> List[AgentDocument]:
    fraction = noise_level / 100.0
    rng = Random(seed + noise_level * 17)
    gold_by_id = gold_by_doc(gold_documents)
    docs = [doc.model_copy(deep=True) for doc in documents]
    doc_by_id = {doc.doc_id: doc for doc in docs}

    primary_ids = [
        gold.doc_id
        for gold in gold_documents
        if gold.supports_gold_verdict and not gold.is_contaminated and gold.doc_id in doc_by_id
    ]
    pollutant_ids = [
        gold.doc_id
        for gold in gold_documents
        if (gold.is_contaminated or gold.stance == "supports_false_claim") and gold.doc_id in doc_by_id
    ]
    generated_ids = [gold.doc_id for gold in gold_documents if gold.generated and gold.doc_id in doc_by_id]
    citation_ids = [doc.doc_id for doc in docs if doc.visible_citations]
    repost_ids = [doc.doc_id for doc in docs if doc.source_type in REPOST_SOURCE_TYPES]

    for doc_id in _sample_doc_ids(rng, primary_ids, fraction):
        doc = doc_by_id[doc_id]
        doc.source_type = rng.choice(SECONDARY_SOURCE_TYPES)
        doc.title = f"Secondary digest: {doc.title}"

    for doc_id in _sample_doc_ids(rng, pollutant_ids, fraction):
        doc = doc_by_id[doc_id]
        doc.source_type = rng.choice(AUTHORITY_SOURCE_TYPES)
        doc.title = f"Authority-style release: {doc.title}"

    for doc_id in _sample_doc_ids(rng, citation_ids, fraction):
        doc_by_id[doc_id].visible_citations = []

    for doc_id in _sample_doc_ids(rng, repost_ids, fraction):
        doc = doc_by_id[doc_id]
        doc.source_type = "independent_report"
        doc.visible_citations = []
        doc.title = f"Independent analysis: {doc.title}"

    for doc_id in _sample_doc_ids(rng, generated_ids, fraction):
        doc = doc_by_id[doc_id]
        doc.source_type = "audit_report"
        doc.title = f"External assurance memo: {doc.title}"

    return docs


def write_dataset_tuple(out_dir: Path, dataset: tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]) -> None:
    manifest, tasks, documents, gold_documents, edges = dataset
    write_matrix_dataset(out_dir, manifest, tasks, documents, gold_documents, edges)


@app.command("prepare-multiseed")
def prepare_multiseed(
    seeds: str = typer.Option("9201,9202,9203", help="Comma-separated new seeds."),
    out_root: Path = typer.Option(Path("data/matrix-v1.1/multiseed"), help="Output root for per-seed datasets."),
) -> None:
    selected_seeds = parse_int_csv(seeds, DEFAULT_V11_SEEDS)
    for seed in selected_seeds:
        dataset = generate_matrix_dataset(seed=seed)
        write_dataset_tuple(out_root / f"seed-{seed}", dataset)
    console.print(f"[green]Prepared[/green] {len(selected_seeds)} Matrix v1.1 multiseed datasets in {out_root}")


@app.command("prepare-noisy")
def prepare_noisy(
    data_dir: Path = typer.Option(Path("data/matrix-v1"), help="Base Matrix v1 dataset."),
    noise_levels: str = typer.Option("0,10,25,50", help="Comma-separated metadata-noise percentages."),
    out_root: Path = typer.Option(Path("data/matrix-v1.1/noisy"), help="Output root for noisy datasets."),
    seed: int = typer.Option(4401, help="Metadata-noise RNG seed."),
) -> None:
    dataset = load_dataset(data_dir)
    selected_tasks = select_tasks_by_difficulty_limit(dataset["tasks"], CRITICAL_DIFFICULTIES)
    base = filter_dataset(
        manifest=dataset["manifest"],
        tasks=dataset["tasks"],
        documents=dataset["documents"],
        gold_documents=dataset["gold_documents"],
        edges=dataset["edges"],
        selected_tasks=selected_tasks,
        name="EHA-Matrix-v1.1-noisy-base",
        notes="Matrix v1.1 noisy metadata stress subset: L3-L5 only.",
    )
    manifest, tasks, documents, gold_documents, edges = base
    for level in parse_int_csv(noise_levels, DEFAULT_NOISE_LEVELS):
        noisy_docs = apply_metadata_noise(documents, gold_documents, noise_level=level, seed=seed)
        noisy_manifest = manifest.model_copy(
            update={
                "name": f"EHA-Matrix-v1.1-noisy-{level:02d}",
                "notes": f"Matrix v1.1 noisy metadata stress subset with metadata_noise={level}%. Gold labels unchanged.",
            }
        )
        write_dataset_tuple(out_root / f"noise-{level:02d}", (noisy_manifest, tasks, noisy_docs, gold_documents, edges))
    console.print(f"[green]Prepared[/green] noisy metadata datasets in {out_root}")


@app.command("prepare-prompt-preflight")
def prepare_prompt_preflight(
    data_dir: Path = typer.Option(Path("data/matrix-v1"), help="Base Matrix v1 dataset."),
    out_dir: Path = typer.Option(Path("data/matrix-v1.1/prompt-v1_1-preflight"), help="Output dataset directory."),
    per_difficulty: int = typer.Option(12, help="Episodes per selected difficulty."),
) -> None:
    dataset = load_dataset(data_dir)
    selected_tasks = select_tasks_by_difficulty_limit(dataset["tasks"], PROMPT_PREFLIGHT_DIFFICULTIES, per_difficulty)
    filtered = filter_dataset(
        manifest=dataset["manifest"],
        tasks=dataset["tasks"],
        documents=dataset["documents"],
        gold_documents=dataset["gold_documents"],
        edges=dataset["edges"],
        selected_tasks=selected_tasks,
        name="EHA-Matrix-v1.1-prompt-preflight",
        notes="Matrix v1.1 prompt-only preflight subset: L0/L3/L4/L5, 12 episodes each.",
    )
    write_dataset_tuple(out_dir, filtered)
    console.print(f"[green]Prepared[/green] prompt v1.1 preflight dataset in {out_dir}")


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def bootstrap_ci(values: Sequence[float], *, seed: int = 9311, samples: int = 500) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    rng = Random(seed)
    estimates: List[float] = []
    for _ in range(samples):
        estimates.append(mean([values[rng.randrange(len(values))] for _ in values]))
    estimates.sort()
    lower = estimates[int(0.025 * (len(estimates) - 1))]
    upper = estimates[int(0.975 * (len(estimates) - 1))]
    return lower, upper


def summarize_with_ci(
    rows: Sequence[Mapping[str, Any]],
    group_keys: Sequence[str],
    metrics: Sequence[str],
) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {name: value for name, value in zip(group_keys, key)}
        item["n"] = len(group)
        if "seed" in group[0]:
            item["seed_count"] = len({row["seed"] for row in group})
        for metric in metrics:
            values = [float(row[metric]) for row in group if row.get(metric) != ""]
            low, high = bootstrap_ci(values)
            item[metric] = mean(values)
            item[f"{metric}_ci_low"] = low
            item[f"{metric}_ci_high"] = high
        output.append(item)
    return output


def load_matrix_records(run_dir: Path) -> List[MatrixRunRecord]:
    return [MatrixRunRecord.model_validate(row) for row in read_jsonl(run_dir / "predictions.jsonl")]


def score_run_with_dataset(data_dir: Path, run_dir: Path) -> List[Dict[str, Any]]:
    dataset = load_dataset(data_dir)
    return score_matrix_run(load_matrix_records(run_dir), dataset["tasks"], dataset["gold_documents"])


def row_level_escape_decomposition(data_dir: Path, run_dir: Path) -> List[Dict[str, Any]]:
    dataset = load_dataset(data_dir)
    records = load_matrix_records(run_dir)
    task_by_id = {task.task_id: task for task in dataset["tasks"]}
    gold_by_id = gold_by_doc(dataset["gold_documents"])
    scored = {
        (row["task_id"], row["model"], row["strategy"], row["prompt"]): row
        for row in score_matrix_run(records, dataset["tasks"], dataset["gold_documents"])
    }
    rows: List[Dict[str, Any]] = []
    for record in records:
        task = task_by_id[record.task_id]
        prediction = record.prediction
        supporting = unique(prediction.supporting_evidence)
        supporting_gold = [gold_by_id[doc_id] for doc_id in supporting if doc_id in gold_by_id]
        clean_support = all(not gold.is_contaminated for gold in supporting_gold)
        has_required_support = prediction.claim_verdict == "insufficient" or bool(supporting)
        generated_lore_abstention_ok = not is_l5(task) or prediction.claim_verdict == "insufficient"
        score = scored[(record.task_id, record.model, record.strategy, record.prompt)]
        rows.append(
            {
                "task_id": record.task_id,
                "difficulty": task.difficulty,
                "model": record.model,
                "strategy": record.strategy,
                "prompt": record.prompt,
                "claim_correct": score["claim_accuracy"],
                "clean_supporting_evidence": 1.0 if clean_support else 0.0,
                "has_required_supporting_evidence": 1.0 if has_required_support else 0.0,
                "generated_lore_abstention_ok": 1.0 if generated_lore_abstention_ok else 0.0,
                "full_escape": score["escape_rate"],
            }
        )
    return rows


def aggregate_decomposition(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return summarize_with_ci(
        rows,
        ["model", "strategy", "difficulty"],
        [
            "claim_correct",
            "clean_supporting_evidence",
            "has_required_supporting_evidence",
            "generated_lore_abstention_ok",
            "full_escape",
        ],
    )


def collect_multiseed_rows(data_root: Path, run_root: Path, seeds: Sequence[int]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for seed in seeds:
        for row in score_run_with_dataset(data_root / f"seed-{seed}", run_root / f"seed-{seed}"):
            if row["difficulty"] not in CRITICAL_DIFFICULTIES:
                continue
            item = dict(row)
            item["seed"] = seed
            rows.append(item)
    return rows


def collect_noisy_rows(data_root: Path, run_root: Path, noise_levels: Sequence[int]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for noise in noise_levels:
        for row in score_run_with_dataset(data_root / f"noise-{noise:02d}", run_root / f"noise-{noise:02d}"):
            item = dict(row)
            item["metadata_noise"] = noise
            rows.append(item)
    return rows


def prompt_preflight_rows(
    *,
    data_dir: Path,
    run_dir: Path,
    baseline_data_dir: Path,
    baseline_run_dir: Path,
) -> List[Dict[str, Any]]:
    prompt_dataset = load_dataset(data_dir)
    task_ids = {task.task_id for task in prompt_dataset["tasks"]}
    rows: List[Dict[str, Any]] = []
    for row in score_run_with_dataset(data_dir, run_dir):
        item = dict(row)
        item["prompt_version"] = "claim_first_citation_v1_1"
        rows.append(item)

    baseline_dataset = load_dataset(baseline_data_dir)
    baseline_records = [
        record
        for record in load_matrix_records(baseline_run_dir)
        if record.task_id in task_ids
        and record.model == "openai/gpt-4o-mini"
        and record.strategy == "careful_bm25"
        and record.prompt == "claim_first_citation_v1"
    ]
    for row in score_matrix_run(baseline_records, baseline_dataset["tasks"], baseline_dataset["gold_documents"]):
        item = dict(row)
        item["prompt_version"] = "claim_first_citation_v1"
        rows.append(item)
    return rows


def aggregate_prompt_preflight(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return summarize_with_ci(
        rows,
        ["prompt_version", "model", "strategy", "difficulty"],
        ["escape_rate", "claim_accuracy", "contaminated_citation_rate", "generated_lore_overclaim_rate"],
    )


def combine_cost_reports(paths: Iterable[Path]) -> Dict[str, Any]:
    reports = []
    for path in paths:
        if path.exists():
            reports.append(read_json(path))
    return {
        "aborted": any(bool(report.get("aborted")) for report in reports),
        "spent_usd": round(sum(float(report.get("spent_usd", 0.0)) for report in reports), 6),
        "record_cost_usd": round(sum(float(report.get("record_cost_usd", 0.0)) for report in reports), 6),
        "source_reports": reports,
    }


def write_v11_summary(
    path: Path,
    *,
    multiseed: Sequence[Mapping[str, Any]],
    noisy: Sequence[Mapping[str, Any]],
    decomposition: Sequence[Mapping[str, Any]],
    prompt_preflight: Sequence[Mapping[str, Any]],
    cost_report: Mapping[str, Any],
) -> None:
    lines = ["# Matrix v1.1 Robustness Pack", ""]
    lines.extend(["## 1. Multi-Seed Critical Replication", ""])
    lines.extend(markdown_table(multiseed, ["model", "strategy", "difficulty", "n", "seed_count", "escape_rate", "escape_rate_ci_low", "escape_rate_ci_high", "contaminated_citation_rate"]))
    lines.extend(["", "## 2. Noisy Metadata / Source Spoofing", ""])
    lines.extend(markdown_table(noisy, ["metadata_noise", "model", "strategy", "difficulty", "n", "escape_rate", "contaminated_citation_rate", "generated_lore_overclaim_rate"]))
    lines.extend(["", "## 3. Escape Metric Decomposition", ""])
    lines.extend(markdown_table(decomposition, ["model", "strategy", "difficulty", "n", "claim_correct", "clean_supporting_evidence", "has_required_supporting_evidence", "generated_lore_abstention_ok", "full_escape"]))
    lines.extend(["", "## 4. Prompt v1.1 Preflight", ""])
    lines.extend(markdown_table(prompt_preflight, ["prompt_version", "difficulty", "n", "escape_rate", "claim_accuracy", "contaminated_citation_rate"]))
    lines.extend(["", "## 5. Cost Report", "", "```json", json.dumps(cost_report, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command("report")
def report(
    out_dir: Path = typer.Option(Path("results/reports-matrix-v1.1"), help="Report output directory."),
    main_data_dir: Path = typer.Option(Path("data/matrix-v1"), help="Matrix v1 main dataset."),
    main_run_dir: Path = typer.Option(Path("results/runs/matrix-v1-main"), help="Matrix v1 merged main run."),
    multiseed_data_root: Path = typer.Option(Path("data/matrix-v1.1/multiseed"), help="Per-seed dataset root."),
    multiseed_run_root: Path = typer.Option(Path("results/runs/matrix-v1.1/multiseed"), help="Per-seed run root."),
    noisy_data_root: Path = typer.Option(Path("data/matrix-v1.1/noisy"), help="Noisy dataset root."),
    noisy_run_root: Path = typer.Option(Path("results/runs/matrix-v1.1/noisy"), help="Noisy run root."),
    prompt_data_dir: Path = typer.Option(Path("data/matrix-v1.1/prompt-v1_1-preflight"), help="Prompt v1.1 preflight dataset."),
    prompt_run_dir: Path = typer.Option(Path("results/runs/matrix-v1.1/prompt-v1_1-preflight"), help="Prompt v1.1 preflight run."),
    seeds: str = typer.Option("9201,9202,9203", help="Comma-separated seeds used for multiseed runs."),
    noise_levels: str = typer.Option("0,10,25,50", help="Comma-separated metadata-noise percentages."),
) -> None:
    selected_seeds = parse_int_csv(seeds, DEFAULT_V11_SEEDS)
    selected_noise_levels = parse_int_csv(noise_levels, DEFAULT_NOISE_LEVELS)

    multiseed_rows = collect_multiseed_rows(multiseed_data_root, multiseed_run_root, selected_seeds)
    noisy_rows = collect_noisy_rows(noisy_data_root, noisy_run_root, selected_noise_levels)
    decomposition_rows = row_level_escape_decomposition(main_data_dir, main_run_dir)
    prompt_rows = prompt_preflight_rows(
        data_dir=prompt_data_dir,
        run_dir=prompt_run_dir,
        baseline_data_dir=main_data_dir,
        baseline_run_dir=Path("results/runs/matrix-v1-gpt4omini"),
    )

    multiseed = summarize_with_ci(
        multiseed_rows,
        ["model", "strategy", "difficulty"],
        ["escape_rate", "claim_accuracy", "contaminated_citation_rate", "generated_lore_overclaim_rate"],
    )
    noisy = summarize_with_ci(
        noisy_rows,
        ["metadata_noise", "model", "strategy", "difficulty"],
        ["escape_rate", "claim_accuracy", "contaminated_citation_rate", "generated_lore_overclaim_rate"],
    )
    decomposition = aggregate_decomposition(decomposition_rows)
    prompt_preflight = aggregate_prompt_preflight(prompt_rows)
    cost_report = combine_cost_reports(
        [multiseed_run_root / f"seed-{seed}" / "cost_report.json" for seed in selected_seeds]
        + [noisy_run_root / f"noise-{noise:02d}" / "cost_report.json" for noise in selected_noise_levels]
        + [prompt_run_dir / "cost_report.json"]
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "multiseed_replication.csv", multiseed)
    write_csv(out_dir / "noisy_metadata_stress.csv", noisy)
    write_csv(out_dir / "escape_decomposition.csv", decomposition)
    write_csv(out_dir / "prompt_v1_1_preflight.csv", prompt_preflight)
    write_csv(out_dir / "scored_multiseed_predictions.csv", multiseed_rows)
    write_csv(out_dir / "scored_noisy_predictions.csv", noisy_rows)
    write_csv(out_dir / "escape_decomposition_rows.csv", decomposition_rows)
    write_csv(out_dir / "prompt_v1_1_preflight_rows.csv", prompt_rows)
    write_json(out_dir / "cost_report.json", cost_report)
    write_v11_summary(
        out_dir / "summary.md",
        multiseed=multiseed,
        noisy=noisy,
        decomposition=decomposition,
        prompt_preflight=prompt_preflight,
        cost_report=cost_report,
    )
    console.print(f"[green]Wrote Matrix v1.1 reports[/green] to {out_dir}")


if __name__ == "__main__":
    app()
