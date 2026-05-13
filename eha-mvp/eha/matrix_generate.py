from __future__ import annotations

from collections import Counter
from pathlib import Path
from random import Random
from typing import Dict, List, Tuple

import typer
from rich.console import Console

from .phase2r_generate import make_phase2r_episode
from .schemas import AgentDocument, DependencyEdge, GoldDocument, Manifest, Task, TaskGold, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Generate EHA Matrix Escape Table v1 corpora.")
console = Console()

MATRIX_LEVEL_COUNTS: Dict[str, int] = {
    "L0_clean_web": 24,
    "L1_mild_pollution": 24,
    "L2_temporal_drift": 24,
    "L3_false_consensus": 24,
    "L4_hidden_primary": 24,
    "L5_halluweb_generated_lore": 24,
}

PREFLIGHT_LEVEL_COUNTS: Dict[str, int] = {level: 6 for level in MATRIX_LEVEL_COUNTS}

LEVEL_TO_DIFFICULTY = {
    "L0_clean_web": "L0",
    "L1_mild_pollution": "L1",
    "L2_temporal_drift": "L2",
    "L3_false_consensus": "L3",
    "L4_hidden_primary": "L4",
    "L5_halluweb_generated_lore": "L5",
}


def matrix_plan(*, preflight: bool = False) -> List[tuple[str, Dict[str, object]]]:
    counts = PREFLIGHT_LEVEL_COUNTS if preflight else MATRIX_LEVEL_COUNTS
    plan: List[tuple[str, Dict[str, object]]] = []
    plan.extend(("L0_clean_web", {"episode_type": "clean_control"}) for _ in range(counts["L0_clean_web"]))
    plan.extend(
        (
            "L1_mild_pollution",
            {
                "episode_type": "false_consensus_stress",
                "duplicate_count": 5,
                "primary_visibility_under_bm25_top8": True,
            },
        )
        for _ in range(counts["L1_mild_pollution"])
    )
    plan.extend(("L2_temporal_drift", {"episode_type": "temporal_pollution_compare"}) for _ in range(counts["L2_temporal_drift"]))
    for index in range(counts["L3_false_consensus"]):
        plan.append(
            (
                "L3_false_consensus",
                {
                    "episode_type": "false_consensus_stress",
                    "duplicate_count": (20, 50, 100)[index % 3],
                    "primary_visibility_under_bm25_top8": True,
                },
            )
        )
    for index in range(counts["L4_hidden_primary"]):
        plan.append(
            (
                "L4_hidden_primary",
                {
                    "episode_type": "false_consensus_stress",
                    "duplicate_count": (20, 50, 100)[index % 3],
                    "primary_visibility_under_bm25_top8": False,
                },
            )
        )
    for index in range(counts["L5_halluweb_generated_lore"]):
        plan.append(
            (
                "L5_halluweb_generated_lore",
                {
                    "episode_type": "halupedia_or_generated_lore" if index % 2 == 0 else "insufficient_or_no_primary",
                },
            )
        )
    return plan


def _replace_id(value: str, old_task_id: str, new_task_id: str) -> str:
    return value.replace(old_task_id, new_task_id)


def retarget_episode(
    *,
    index: int,
    level: str,
    task: Task,
    documents: List[AgentDocument],
    gold_documents: List[GoldDocument],
    edges: List[DependencyEdge],
) -> None:
    old_task_id = task.task_id
    new_task_id = f"eham_{index:03d}"

    for doc in documents:
        doc.task_id = new_task_id
        doc.doc_id = _replace_id(doc.doc_id, old_task_id, new_task_id)
        doc.visible_citations = [_replace_id(doc_id, old_task_id, new_task_id) for doc_id in doc.visible_citations]
    for gold in gold_documents:
        gold.task_id = new_task_id
        gold.doc_id = _replace_id(gold.doc_id, old_task_id, new_task_id)
        gold.upstream_root = _replace_id(gold.upstream_root, old_task_id, new_task_id)
    for edge in edges:
        edge.from_doc = _replace_id(edge.from_doc, old_task_id, new_task_id)
        edge.to_doc = _replace_id(edge.to_doc, old_task_id, new_task_id)

    task.task_id = new_task_id
    task.phase = "matrix_v1"
    task.difficulty = LEVEL_TO_DIFFICULTY[level]
    task.episode_type = level
    task.pollutant_root_id = _replace_id(task.pollutant_root_id, old_task_id, new_task_id) if task.pollutant_root_id else None
    task.primary_refutation_docs = [_replace_id(doc_id, old_task_id, new_task_id) for doc_id in task.primary_refutation_docs]
    task.gold.primary_support = [_replace_id(doc_id, old_task_id, new_task_id) for doc_id in task.gold.primary_support]
    task.gold.known_contaminants = [_replace_id(doc_id, old_task_id, new_task_id) for doc_id in task.gold.known_contaminants]
    if level == "L5_halluweb_generated_lore":
        task.gold = TaskGold(
            verdict="insufficient",
            scope_tag="no_primary_source",
            answer_brief="The provided corpus does not contain current primary evidence sufficient to decide the claim.",
            primary_support=[],
            known_contaminants=task.gold.known_contaminants,
        )


def generate_matrix_dataset(
    *,
    seed: int = 9133,
    preflight: bool = False,
) -> Tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    rng = Random(seed)
    tasks: List[Task] = []
    documents: List[AgentDocument] = []
    gold_documents: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    for index, (level, params) in enumerate(matrix_plan(preflight=preflight)):
        phase2r_episode_type = str(params["episode_type"])
        task, task_docs, task_gold, task_edges = make_phase2r_episode(index, phase2r_episode_type, params, rng)
        retarget_episode(index=index, level=level, task=task, documents=task_docs, gold_documents=task_gold, edges=task_edges)
        tasks.append(task)
        documents.extend(task_docs)
        gold_documents.extend(task_gold)
        edges.extend(task_edges)
    manifest = Manifest(
        name="EHA-Matrix-v1-preflight" if preflight else "EHA-Matrix-v1",
        seed=seed,
        episodes=len(tasks),
        created_by="eha.matrix_generate",
        notes="Matrix Escape Table v1. Hidden gold labels, contamination labels, and upstream roots are scorer-only.",
        episode_type_counts=dict(Counter(task.episode_type for task in tasks)),
    )
    return manifest, tasks, documents, gold_documents, edges


def write_matrix_dataset(
    out_dir: Path,
    manifest: Manifest,
    tasks: List[Task],
    documents: List[AgentDocument],
    gold_documents: List[GoldDocument],
    edges: List[DependencyEdge],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "manifest.json", model_to_dict(manifest))
    write_jsonl(out_dir / "tasks.jsonl", [model_to_dict(task) for task in tasks])
    write_jsonl(out_dir / "documents.jsonl", [model_to_dict(doc) for doc in documents])
    write_jsonl(out_dir / "gold_documents.jsonl", [model_to_dict(doc) for doc in gold_documents])
    write_jsonl(out_dir / "gold_graph.jsonl", [model_to_dict(edge) for edge in edges])


@app.command()
def main(
    seed: int = typer.Option(9133, help="Deterministic Matrix v1 seed."),
    out_dir: Path = typer.Option(Path("data/matrix-v1"), help="Output directory."),
    preflight: bool = typer.Option(False, help="Generate the 36-episode Matrix v1 preflight set."),
) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_matrix_dataset(seed=seed, preflight=preflight)
    write_matrix_dataset(out_dir, manifest, tasks, documents, gold_documents, edges)
    console.print(f"[green]Generated[/green] {len(tasks)} Matrix v1 tasks and {len(documents)} documents in {out_dir}")


if __name__ == "__main__":
    app()
