from __future__ import annotations

from collections import Counter
from pathlib import Path
from random import Random
from typing import Dict, List, Tuple

import typer
from rich.console import Console

from .generate_world import COMPANY, duplicate_count_for, episode_plan, fact_for
from .schemas import AgentDocument, DependencyEdge, GoldDocument, Manifest, Task, TaskGold, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Generate deterministic EHA synthetic corpora.")
console = Console()


def _body(title: str, sentences: List[str]) -> str:
    return title + "\n\n" + " ".join(sentences)


def _doc(
    *,
    task_id: str,
    claim_id: str,
    doc_id: str,
    title: str,
    source_type: str,
    timestamp: str,
    body: str,
    visible_citations: List[str] | None,
    stance: str,
    supports_gold_verdict: bool,
    contamination: List[str] | None,
    upstream_root: str,
    generated: bool = False,
    stale: bool = False,
    valid_time: str,
    evidence_quality: str,
    rank_boost: float = 0.0,
) -> Tuple[AgentDocument, GoldDocument]:
    visible = AgentDocument(
        doc_id=doc_id,
        task_id=task_id,
        title=title,
        source_type=source_type,
        timestamp=timestamp,
        body=body,
        visible_citations=visible_citations or [],
    )
    gold = GoldDocument(
        doc_id=doc_id,
        task_id=task_id,
        target_claim_id=claim_id,
        stance=stance,
        supports_gold_verdict=supports_gold_verdict,
        contamination=contamination or [],
        upstream_root=upstream_root,
        generated=generated,
        stale=stale,
        valid_time=valid_time,
        evidence_quality=evidence_quality,
        rank_boost=rank_boost,
    )
    return visible, gold


def _make_episode(index: int, episode_type: str, duplicate_ordinal: int, rng: Random) -> Tuple[Task, List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    task_id = f"novalis_{index:03d}"
    fact = fact_for(episode_type, index)
    duplicate_count = duplicate_count_for(episode_type, duplicate_ordinal)
    primary_a = f"{task_id}_audit"
    primary_b = f"{task_id}_filing"
    pollutant_root = f"{task_id}_pollutant_root"
    documents: List[AgentDocument] = []
    gold_docs: List[GoldDocument] = []
    edges: List[DependencyEdge] = []

    def add_pair(pair: Tuple[AgentDocument, GoldDocument]) -> None:
        documents.append(pair[0])
        gold_docs.append(pair[1])

    add_pair(
        _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=primary_a,
            title=f"{COMPANY} audit record for {fact.target_time}",
            source_type="audit_report",
            timestamp="2025-01-08",
            body=_body(
                f"{COMPANY} audit record",
                [
                    f"The quality office states that {fact.primary_phrase}.",
                    "The audit links the conclusion to raw operating records and a signed review log.",
                    "The record is scoped to the investigation question and target time.",
                ],
            ),
            visible_citations=[],
            stance="supports_gold",
            supports_gold_verdict=True,
            contamination=[],
            upstream_root=primary_a,
            valid_time=fact.target_time,
            evidence_quality="primary_record",
        )
    )
    add_pair(
        _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=primary_b,
            title=f"Regulatory or board filing for {fact.target_time}",
            source_type="primary_record",
            timestamp="2025-01-15",
            body=_body(
                "Filing excerpt",
                [
                    f"The filing repeats the primary finding: {fact.primary_phrase}.",
                    "It does not rely on press summaries or customer forum posts.",
                ],
            ),
            visible_citations=[primary_a],
            stance="supports_gold",
            supports_gold_verdict=True,
            contamination=[],
            upstream_root=primary_b,
            valid_time=fact.target_time,
            evidence_quality="primary_record",
        )
    )
    edges.append(DependencyEdge(from_doc=primary_b, to_doc=primary_a, relation="cites"))

    if episode_type == "clean_control":
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=pollutant_root,
                title="Planning note copied from the pre-audit calendar",
                source_type="internal_planning_note",
                timestamp="2024-10-03",
                body=_body(
                    "Planning note",
                    [
                        fact.pollutant_phrase.capitalize() + ".",
                        "The note predates the final audit and warns that status may change.",
                    ],
                ),
                visible_citations=[],
                stance="stale_context",
                supports_gold_verdict=False,
                contamination=["temporal_pollution"],
                upstream_root=pollutant_root,
                stale=True,
                valid_time="2024-Q3",
                evidence_quality="stale_plan",
                rank_boost=0.05,
            )
        )
    else:
        contamination = {
            "false_consensus": ["consensus_fabrication"],
            "citation_laundering": ["citation_laundering"],
            "temporal_pollution": ["temporal_pollution"],
            "mixed_source_corruption": ["mixed_source_corruption"],
            "halupedia_trap": ["query_induced_pollution"],
        }[episode_type]
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=pollutant_root,
                title=f"Popular summary claiming {fact.false_value}",
                source_type="press_release" if episode_type != "halupedia_trap" else "generated_encyclopedia",
                timestamp="2024-11-03",
                body=_body(
                    "Popular summary",
                    [
                        fact.pollutant_phrase.capitalize() + ".",
                        "The summary uses an executive-metrics style and presents the figure as a settled operating result.",
                    ],
                ),
                visible_citations=[],
                stance="supports_false_claim",
                supports_gold_verdict=False,
                contamination=contamination,
                upstream_root=pollutant_root,
                generated=episode_type == "halupedia_trap",
                stale=episode_type == "temporal_pollution",
                valid_time="2023-Q4" if episode_type == "temporal_pollution" else fact.target_time,
                evidence_quality="polluted_root",
                rank_boost=5.50 if episode_type == "false_consensus" else 0.24 if episode_type == "citation_laundering" else 0.16,
            )
        )

    if episode_type == "false_consensus":
        duplicate_docs = 1 if duplicate_count == 1 else min(max(duplicate_count, 8), 10)
    else:
        duplicate_docs = rng.randint(2, 4)
    for offset in range(duplicate_docs):
        doc_id = f"{task_id}_repost_{offset:02d}"
        source_type = rng.choice(["blog_repost", "trade_news", "vendor_brief", "forum_digest"])
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=doc_id,
                title=f"Secondary coverage {offset + 1}: {fact.false_value}",
                source_type=source_type,
                timestamp=f"2024-11-{4 + offset:02d}",
                body=_body(
                    "Secondary coverage",
                    [
                        f"This item repeats the claim that {fact.false_value}.",
                        f"It cites {pollutant_root} and a metrics dashboard mirror.",
                        "The wording differs from other summaries and uses a separate publication channel.",
                    ],
                ),
                visible_citations=[pollutant_root],
                stance="supports_false_claim",
                supports_gold_verdict=False,
                contamination=["consensus_fabrication" if episode_type == "false_consensus" else "secondary_pollution"],
                upstream_root=pollutant_root,
                generated=episode_type == "halupedia_trap" and offset == 0,
                stale=episode_type == "temporal_pollution",
                valid_time="2023-Q4" if episode_type == "temporal_pollution" else fact.target_time,
                evidence_quality="unsupported_repost",
                rank_boost=6.00 if episode_type == "false_consensus" else 0.20 if episode_type == "temporal_pollution" else 0.10,
            )
        )
        edges.append(DependencyEdge(from_doc=doc_id, to_doc=pollutant_root, relation="repost"))

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
                rank_boost=0.10,
            )
        )
        edges.append(DependencyEdge(from_doc=pollutant_root, to_doc=whitepaper, relation="misleading_citation"))

    if episode_type == "mixed_source_corruption":
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=f"{task_id}_appendix",
                title="Polished appendix with a corrupted complaint attribution table",
                source_type="official_appendix",
                timestamp="2025-01-04",
                body=_body(
                    "Appendix table",
                    [
                        fact.pollutant_phrase.capitalize() + ".",
                        "The surrounding report is mostly reliable, but this table uses an obsolete export.",
                    ],
                ),
                visible_citations=[primary_a],
                stance="supports_false_claim",
                supports_gold_verdict=False,
                contamination=["mixed_source_corruption"],
                upstream_root=f"{task_id}_appendix",
                valid_time=fact.target_time,
                evidence_quality="corrupted_table",
                rank_boost=0.18,
            )
        )
        edges.append(DependencyEdge(from_doc=f"{task_id}_appendix", to_doc=primary_a, relation="misreads"))

    for offset in range(3):
        doc_id = f"{task_id}_background_{offset:02d}"
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=doc_id,
                title=f"Background memo {offset + 1}",
                source_type=rng.choice(["meeting_minutes", "support_digest", "procurement_memo"]),
                timestamp=f"2024-12-{10 + offset:02d}",
                body=_body(
                    "Background memo",
                    [
                        f"The memo discusses {COMPANY}, HelioPart, Arcadia, and routine operating context.",
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
    while len(documents) < 12:
        doc_id = f"{task_id}_context_{filler_offset:02d}"
        add_pair(
            _doc(
                task_id=task_id,
                claim_id=fact.claim_id,
                doc_id=doc_id,
                title=f"Context note {filler_offset + 1}",
                source_type=rng.choice(["customer_note", "quality_digest", "legal_calendar", "release_note"]),
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
        difficulty="L3" if episode_type == "halupedia_trap" else "L2" if episode_type == "false_consensus" else "L1",
        episode_type=episode_type,
        pollution_types=sorted({kind for gold in gold_docs for kind in gold.contamination}),
        duplicate_count=duplicate_count,
        gold=TaskGold(
            verdict=fact.gold_verdict,  # type: ignore[arg-type]
            answer_brief=fact.answer_brief,
            primary_support=primary_support,
            known_contaminants=known_contaminants,
        ),
    )
    return task, documents, gold_docs, edges


def generate_dataset(episodes: int, seed: int) -> Tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    rng = Random(seed)
    tasks: List[Task] = []
    documents: List[AgentDocument] = []
    gold_documents: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    seen_type_counts: Counter[str] = Counter()
    plan = episode_plan(episodes)
    for index, episode_type in enumerate(plan):
        duplicate_ordinal = seen_type_counts[episode_type]
        seen_type_counts[episode_type] += 1
        task, task_docs, task_gold, task_edges = _make_episode(index, episode_type, duplicate_ordinal, rng)
        tasks.append(task)
        documents.extend(task_docs)
        gold_documents.extend(task_gold)
        edges.extend(task_edges)

    manifest = Manifest(
        name="eha-mvp",
        seed=seed,
        episodes=episodes,
        created_by="eha.generate_corpus",
        notes="Synthetic fictional company corpus. Gold labels are scorer-only and must not be shown to agents.",
        episode_type_counts=dict(Counter(plan)),
    )
    return manifest, tasks, documents, gold_documents, edges


def write_dataset(out_dir: Path, manifest: Manifest, tasks: List[Task], documents: List[AgentDocument], gold_documents: List[GoldDocument], edges: List[DependencyEdge]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "manifest.json", model_to_dict(manifest))
    write_jsonl(out_dir / "tasks.jsonl", [model_to_dict(task) for task in tasks])
    write_jsonl(out_dir / "documents.jsonl", [model_to_dict(doc) for doc in documents])
    write_jsonl(out_dir / "gold_documents.jsonl", [model_to_dict(doc) for doc in gold_documents])
    write_jsonl(out_dir / "gold_graph.jsonl", [model_to_dict(edge) for edge in edges])


@app.command()
def main(
    episodes: int = typer.Option(60, help="Number of episodes to generate."),
    seed: int = typer.Option(4242, help="Deterministic corpus seed."),
    out_dir: Path = typer.Option(Path("data/generated"), help="Output directory."),
) -> None:
    if episodes < 1:
        raise typer.BadParameter("episodes must be positive")
    manifest, tasks, documents, gold_documents, edges = generate_dataset(episodes=episodes, seed=seed)
    write_dataset(out_dir, manifest, tasks, documents, gold_documents, edges)
    console.print(f"[green]Generated[/green] {len(tasks)} tasks and {len(documents)} documents in {out_dir}")


if __name__ == "__main__":
    app()
