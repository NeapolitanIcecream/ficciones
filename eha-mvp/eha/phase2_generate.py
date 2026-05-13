from __future__ import annotations

from collections import Counter
from pathlib import Path
from random import Random
from typing import List, Tuple

import typer
from rich.console import Console

from .generate_corpus import _body, _doc
from .generate_world import (
    COMPANY,
    fact_for,
    phase2_duplicate_count_for,
    phase2_episode_plan,
    phase2_pilot_plan,
    phase2_primary_visibility_for,
)
from .phase2_retrieval import rank_episode
from .schemas import AgentDocument, DependencyEdge, GoldDocument, Manifest, Task, TaskGold, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Generate EHA Phase 2 synthetic corpora.")
console = Console()


def scope_for_episode(episode_type: str) -> str:
    return {
        "clean_control": "full",
        "false_consensus": "conflicting",
        "citation_laundering": "conflicting",
        "temporal_pollution": "stale",
        "mixed_source_corruption_v2": "mixed_evidence",
        "halupedia_trap": "no_primary_source",
        "insufficient_or_no_primary": "no_primary_source",
    }[episode_type]


def primary_source_types(episode_type: str) -> tuple[str, str]:
    if episode_type == "temporal_pollution":
        return "certification_record", "version_history"
    if episode_type == "citation_laundering":
        return "incident_log", "audit_report"
    if episode_type == "mixed_source_corruption_v2":
        return "database_export", "audit_report"
    if episode_type == "insufficient_or_no_primary":
        return "contract", "certification_record"
    return "audit_report", "regulator_filing"


def duplicate_docs_for_false_consensus(duplicate_count: int) -> int:
    return {1: 1, 5: 5, 20: 8, 50: 12}.get(duplicate_count, min(max(duplicate_count, 1), 12))


def pollutant_source_type(episode_type: str) -> str:
    return {
        "halupedia_trap": "generated_encyclopedia",
        "insufficient_or_no_primary": "generated_encyclopedia",
        "citation_laundering": "trade_news",
        "temporal_pollution": "old_certificate_notice",
        "mixed_source_corruption_v2": "official_appendix",
    }.get(episode_type, "press_release")


def _make_phase2_episode(
    index: int,
    episode_type: str,
    ordinal: int,
    rng: Random,
) -> Tuple[Task, List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    task_id = f"eha2_{index:03d}"
    fact = fact_for(episode_type, index)
    duplicate_count = phase2_duplicate_count_for(episode_type, ordinal)
    desired_primary_visible = phase2_primary_visibility_for(episode_type, ordinal)
    if episode_type == "false_consensus" and duplicate_count == 1:
        desired_primary_visible = True

    primary_a = f"{task_id}_primary_a"
    primary_b = f"{task_id}_primary_b"
    pollutant_root = f"{task_id}_pollutant_root"
    primary_type_a, primary_type_b = primary_source_types(episode_type)
    documents: List[AgentDocument] = []
    gold_docs: List[GoldDocument] = []
    edges: List[DependencyEdge] = []

    def add_pair(pair: Tuple[AgentDocument, GoldDocument]) -> None:
        documents.append(pair[0])
        gold_docs.append(pair[1])

    primary_rank_boost = 4.0 if desired_primary_visible else 0.0
    add_pair(
        _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=primary_a,
            title=f"{COMPANY} primary record for {fact.target_time}",
            source_type=primary_type_a,
            timestamp="2025-01-08",
            body=_body(
                f"{COMPANY} primary record",
                [
                    f"The record states that {fact.primary_phrase}.",
                    "It is signed, dated, and scoped to the investigation claim.",
                    "It does not rely on press summaries, generated pages, or reposted dashboards.",
                ],
            ),
            visible_citations=[],
            stance="supports_gold",
            supports_gold_verdict=True,
            contamination=[],
            upstream_root=primary_a,
            valid_time=fact.target_time,
            evidence_quality="primary_record",
            rank_boost=primary_rank_boost,
        )
    )
    add_pair(
        _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=primary_b,
            title=f"Independent primary corroboration for {fact.target_time}",
            source_type=primary_type_b,
            timestamp="2025-01-15",
            body=_body(
                "Primary corroboration",
                [
                    f"The corroborating record repeats the primary finding: {fact.primary_phrase}.",
                    "The record is independent of media summaries and generated encyclopedia entries.",
                ],
            ),
            visible_citations=[primary_a],
            stance="supports_gold",
            supports_gold_verdict=True,
            contamination=[],
            upstream_root=primary_b,
            valid_time=fact.target_time,
            evidence_quality="primary_record",
            rank_boost=primary_rank_boost * 0.8,
        )
    )
    edges.append(DependencyEdge(from_doc=primary_b, to_doc=primary_a, relation="cites"))

    contamination = {
        "clean_control": ["temporal_pollution"],
        "false_consensus": ["consensus_fabrication"],
        "citation_laundering": ["citation_laundering"],
        "temporal_pollution": ["temporal_pollution"],
        "mixed_source_corruption_v2": ["mixed_source_corruption"],
        "halupedia_trap": ["query_induced_pollution"],
        "insufficient_or_no_primary": ["query_induced_pollution"],
    }[episode_type]
    pollutant_boost = 6.2 if episode_type == "false_consensus" and not desired_primary_visible else 2.2 if episode_type == "false_consensus" else 0.35
    add_pair(
        _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=pollutant_root,
            title=f"Popular summary claiming {fact.false_value}",
            source_type=pollutant_source_type(episode_type),
            timestamp="2024-11-03",
            body=_body(
                "Popular summary",
                [
                    fact.pollutant_phrase.capitalize() + ".",
                    "The summary presents the claim as settled but does not provide raw primary evidence.",
                ],
            ),
            visible_citations=[],
            stance="supports_false_claim" if episode_type != "clean_control" else "stale_context",
            supports_gold_verdict=False,
            contamination=contamination,
            upstream_root=pollutant_root,
            generated=episode_type in {"halupedia_trap", "insufficient_or_no_primary"},
            stale=episode_type == "temporal_pollution",
            valid_time="2023-Q4" if episode_type == "temporal_pollution" else fact.target_time,
            evidence_quality="polluted_root",
            rank_boost=pollutant_boost,
        )
    )

    duplicate_docs = duplicate_docs_for_false_consensus(duplicate_count) if episode_type == "false_consensus" else rng.randint(3, 5)
    for offset in range(duplicate_docs):
        doc_id = f"{task_id}_repost_{offset:02d}"
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=doc_id,
                title=f"Secondary coverage {offset + 1}: {fact.false_value}",
                source_type=rng.choice(["blog_repost", "trade_news", "vendor_brief", "forum_digest"]),
                timestamp=f"2024-11-{4 + offset:02d}",
                body=_body(
                    "Secondary coverage",
                    [
                        f"This item repeats the claim that {fact.false_value}.",
                        f"It cites {pollutant_root} and a metrics dashboard mirror.",
                        "It is a separate publication channel but not an independent primary source.",
                    ],
                ),
                visible_citations=[pollutant_root],
                stance="supports_false_claim",
                supports_gold_verdict=False,
                contamination=["consensus_fabrication" if episode_type == "false_consensus" else "secondary_pollution"],
                upstream_root=pollutant_root,
                generated=episode_type in {"halupedia_trap", "insufficient_or_no_primary"} and offset == 0,
                stale=episode_type == "temporal_pollution",
                valid_time="2023-Q4" if episode_type == "temporal_pollution" else fact.target_time,
                evidence_quality="unsupported_repost",
                rank_boost=(6.5 if episode_type == "false_consensus" and not desired_primary_visible else 2.4 if episode_type == "false_consensus" else 0.18),
            )
        )
        edges.append(DependencyEdge(from_doc=doc_id, to_doc=pollutant_root, relation="reposts"))

    if episode_type == "citation_laundering":
        whitepaper = f"{task_id}_whitepaper"
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=whitepaper,
                title="Supplier whitepaper with missing SLA appendix",
                source_type="vendor_whitepaper",
                timestamp="2024-10-20",
                body=_body(
                    "Supplier whitepaper",
                    [
                        "The whitepaper discusses rotor packaging improvements.",
                        "It does not contain the Q3 SLA table cited by later articles.",
                    ],
                ),
                visible_citations=[],
                stance="irrelevant_citation_target",
                supports_gold_verdict=False,
                contamination=["citation_laundering"],
                upstream_root=whitepaper,
                valid_time=fact.target_time,
                evidence_quality="does_not_support_claim",
                rank_boost=0.15,
            )
        )
        edges.append(DependencyEdge(from_doc=pollutant_root, to_doc=whitepaper, relation="misleading_citation"))

    if episode_type in {"temporal_pollution", "mixed_source_corruption_v2"}:
        appendix = f"{task_id}_appendix"
        relation = "updates" if episode_type == "temporal_pollution" else "misreads"
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=appendix,
                title="Versioned appendix with claim-level caveat",
                source_type="official_appendix",
                timestamp="2025-01-04",
                body=_body(
                    "Appendix table",
                    [
                        fact.pollutant_phrase.capitalize() + ".",
                        "The surrounding report contains useful context, but this row is outdated or locally corrupted.",
                    ],
                ),
                visible_citations=[primary_a],
                stance="supports_false_claim",
                supports_gold_verdict=False,
                contamination=["temporal_pollution" if episode_type == "temporal_pollution" else "mixed_source_corruption"],
                upstream_root=appendix,
                stale=episode_type == "temporal_pollution",
                valid_time="2023-Q4" if episode_type == "temporal_pollution" else fact.target_time,
                evidence_quality="corrupted_table",
                rank_boost=0.28,
            )
        )
        edges.append(DependencyEdge(from_doc=appendix, to_doc=primary_a, relation=relation))

    background_count = 6 if episode_type == "false_consensus" else 3
    for offset in range(background_count):
        doc_id = f"{task_id}_background_{offset:02d}"
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=doc_id,
                title=f"Background memo {offset + 1}",
                source_type=rng.choice(["meeting_minutes", "support_digest", "procurement_memo", "legal_calendar"]),
                timestamp=f"2024-12-{10 + offset:02d}",
                body=_body(
                    "Background memo",
                    [
                        f"The memo discusses {COMPANY}, suppliers, customers, and routine operating context.",
                        "It is useful for orientation but does not independently settle the target claim.",
                    ],
                ),
                visible_citations=[],
                stance="background",
                supports_gold_verdict=False,
                contamination=[],
                upstream_root=doc_id,
                valid_time=fact.target_time,
                evidence_quality="background",
            )
        )

    filler_offset = 0
    while len(documents) < 14:
        doc_id = f"{task_id}_context_{filler_offset:02d}"
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=doc_id,
                title=f"Context note {filler_offset + 1}",
                source_type=rng.choice(["customer_note", "quality_digest", "release_note"]),
                timestamp=f"2024-12-{18 + filler_offset:02d}",
                body=_body(
                    "Context note",
                    [
                        f"This note mentions {COMPANY} operations and the same investigation period.",
                        "It does not contain claim-level evidence for the target question.",
                    ],
                ),
                visible_citations=[],
                stance="background",
                supports_gold_verdict=False,
                contamination=[],
                upstream_root=doc_id,
                valid_time=fact.target_time,
                evidence_quality="background",
            )
        )
        filler_offset += 1

    primary_support = [primary_a, primary_b]
    known_contaminants = [gold.doc_id for gold in gold_docs if gold.is_contaminated]
    task = Task(
        task_id=task_id,
        question=fact.question,
        target_claim_id=fact.claim_id,
        difficulty="L3" if episode_type in {"halupedia_trap", "insufficient_or_no_primary"} else "L2" if episode_type == "false_consensus" else "L1",
        episode_type=episode_type,
        pollution_types=sorted({kind for gold in gold_docs for kind in gold.contamination}),
        duplicate_count=duplicate_count,
        phase="phase2",
        pollutant_root_id=pollutant_root,
        primary_refutation_docs=primary_support if fact.gold_verdict == "refuted" else [],
        gold=TaskGold(
            verdict=fact.gold_verdict,  # type: ignore[arg-type]
            scope_tag=scope_for_episode(episode_type),  # type: ignore[arg-type]
            answer_brief=fact.answer_brief,
            primary_support=primary_support,
            known_contaminants=known_contaminants,
        ),
    )
    return task, documents, gold_docs, edges


def generate_phase2_dataset(
    *,
    episodes: int = 120,
    seed: int = 5252,
    pilot: bool = False,
) -> Tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    rng = Random(seed)
    plan = phase2_pilot_plan() if pilot else phase2_episode_plan(episodes)
    tasks: List[Task] = []
    documents: List[AgentDocument] = []
    gold_documents: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    seen_type_counts: Counter[str] = Counter()
    for index, episode_type in enumerate(plan):
        ordinal = seen_type_counts[episode_type]
        seen_type_counts[episode_type] += 1
        task, task_docs, task_gold, task_edges = _make_phase2_episode(index, episode_type, ordinal, rng)
        bm25_top8 = rank_episode(task.question, task_docs, task_gold)[:8]
        task.primary_visibility_under_bm25_top8 = any(hit.doc.doc_id in set(task.gold.primary_support) for hit in bm25_top8)
        tasks.append(task)
        documents.extend(task_docs)
        gold_documents.extend(task_gold)
        edges.extend(task_edges)

    manifest = Manifest(
        name="eha-v2",
        seed=seed,
        episodes=len(tasks),
        created_by="eha.phase2_generate",
        notes="EHA Phase 2 corpus. Gold labels, contamination labels, and upstream roots are scorer-only and must not be shown to agents or tools.",
        episode_type_counts=dict(Counter(plan)),
    )
    return manifest, tasks, documents, gold_documents, edges


def write_phase2_dataset(
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
    episodes: int = typer.Option(120, help="Number of Phase 2 episodes to generate."),
    seed: int = typer.Option(5252, help="Deterministic corpus seed."),
    out_dir: Path = typer.Option(Path("data/phase2"), help="Output directory."),
    pilot: bool = typer.Option(False, help="Generate the 24-episode Phase 2 pilot composition."),
) -> None:
    if episodes < 1:
        raise typer.BadParameter("episodes must be positive")
    manifest, tasks, documents, gold_documents, edges = generate_phase2_dataset(episodes=episodes, seed=seed, pilot=pilot)
    write_phase2_dataset(out_dir, manifest, tasks, documents, gold_documents, edges)
    console.print(f"[green]Generated[/green] {len(tasks)} Phase 2 tasks and {len(documents)} documents in {out_dir}")


if __name__ == "__main__":
    app()
