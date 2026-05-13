from __future__ import annotations

from collections import Counter
from pathlib import Path
from random import Random
from typing import Dict, List, Tuple

import typer
from rich.console import Console

from .generate_corpus import _body, _doc
from .generate_world import COMPANY, fact_for
from .phase2_retrieval import rank_episode
from .schemas import AgentDocument, DependencyEdge, GoldDocument, Manifest, Task, TaskGold, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Generate EHA Phase 2R stress-calibrated corpora.")
console = Console()


PHASE2R_COUNTS: Dict[str, int] = {
    "clean_control": 8,
    "false_consensus_stress": 32,
    "citation_laundering_trace": 12,
    "temporal_pollution_compare": 8,
    "halupedia_or_generated_lore": 10,
    "insufficient_or_no_primary": 6,
    "mixed_source_corruption_v2": 4,
}

FALSE_CONSENSUS_LEVELS = (5, 20, 50, 100)
AUTHORITY_SOURCE_TYPES = ("press_release", "executive_memo", "industry_digest", "supplier_whitepaper", "wiki_style_summary")


def base_episode_type(episode_type: str) -> str:
    return {
        "false_consensus_stress": "false_consensus",
        "citation_laundering_trace": "citation_laundering",
        "temporal_pollution_compare": "temporal_pollution",
        "halupedia_or_generated_lore": "halupedia_trap",
    }.get(episode_type, episode_type)


def phase2r_scope_tag(episode_type: str) -> str:
    return {
        "clean_control": "full",
        "false_consensus_stress": "conflicting",
        "citation_laundering_trace": "conflicting",
        "temporal_pollution_compare": "stale",
        "halupedia_or_generated_lore": "generated_lore",
        "insufficient_or_no_primary": "no_primary_source",
        "mixed_source_corruption_v2": "partial",
    }[episode_type]


def phase2r_plan() -> List[tuple[str, Dict[str, object]]]:
    plan: List[tuple[str, Dict[str, object]]] = []
    for episode_type in ("clean_control",):
        plan.extend((episode_type, {}) for _ in range(PHASE2R_COUNTS[episode_type]))
    for duplicate_count in FALSE_CONSENSUS_LEVELS:
        for primary_visible in (True, False):
            for repeat in range(4):
                plan.append(
                    (
                        "false_consensus_stress",
                        {
                            "duplicate_count": duplicate_count,
                            "primary_visibility_under_bm25_top8": primary_visible,
                            "repeat": repeat,
                        },
                    )
                )
    for episode_type in (
        "citation_laundering_trace",
        "temporal_pollution_compare",
        "halupedia_or_generated_lore",
        "insufficient_or_no_primary",
        "mixed_source_corruption_v2",
    ):
        plan.extend((episode_type, {}) for _ in range(PHASE2R_COUNTS[episode_type]))
    return plan


def duplicate_docs_for(duplicate_count: int) -> int:
    return {5: 7, 20: 10, 50: 13, 100: 14}.get(duplicate_count, 8)


def primary_types_for(episode_type: str) -> tuple[str, str]:
    if episode_type == "temporal_pollution_compare":
        return "certification_record", "version_history"
    if episode_type == "citation_laundering_trace":
        return "incident_log", "audit_report"
    if episode_type == "mixed_source_corruption_v2":
        return "database_export", "audit_report"
    return "audit_report", "regulator_filing"


def add_primary_docs(
    *,
    task_id: str,
    claim_id: str,
    episode_type: str,
    target_time: str,
    primary_phrase: str,
    primary_visible: bool,
    documents: List[AgentDocument],
    gold_docs: List[GoldDocument],
    edges: List[DependencyEdge],
) -> List[str]:
    primary_a = f"{task_id}_primary_a"
    primary_b = f"{task_id}_primary_b"
    source_a, source_b = primary_types_for(episode_type)
    boost = 5.0 if primary_visible else -0.4
    body_phrases = [
        f"The signed record states that {primary_phrase}.",
        "The finding is based on raw operating records, dated logs, and reviewer sign-off.",
    ]
    if not primary_visible:
        body_phrases = [
            "The signed record reports the audited exception rate as 3.8 percent for the relevant operating year.",
            "The finding is based on raw operating records, dated logs, and reviewer sign-off.",
        ]
    for doc_id, source_type, title, citations, rank_boost in (
        (primary_a, source_a, f"{COMPANY} primary record for {target_time}", [], boost),
        (primary_b, source_b, f"Independent primary corroboration for {target_time}", [primary_a], boost * 0.8),
    ):
        doc, gold = _doc(
            task_id=task_id,
            claim_id=claim_id,
            doc_id=doc_id,
            title=title,
            source_type=source_type,
            timestamp="2025-01-15" if source_type != "version_history" else "2025-02-02",
            body=_body("Primary record", body_phrases),
            visible_citations=citations,
            stance="supports_gold",
            supports_gold_verdict=True,
            contamination=[],
            upstream_root=doc_id,
            valid_time=target_time,
            evidence_quality="primary_record",
            rank_boost=rank_boost,
        )
        documents.append(doc)
        gold_docs.append(gold)
    edges.append(DependencyEdge(from_doc=primary_b, to_doc=primary_a, relation="cites"))
    return [primary_a, primary_b]


def add_context_doc(
    *,
    task_id: str,
    claim_id: str,
    index: int,
    rng: Random,
    target_time: str,
    documents: List[AgentDocument],
    gold_docs: List[GoldDocument],
) -> None:
    doc_id = f"{task_id}_context_{index:02d}"
    doc, gold = _doc(
        task_id=task_id,
        claim_id=claim_id,
        doc_id=doc_id,
        title=f"Context note {index + 1}",
        source_type=rng.choice(["customer_note", "quality_digest", "release_note", "meeting_minutes"]),
        timestamp=f"2024-12-{10 + index:02d}",
        body=_body(
            "Context note",
            [
                f"This note mentions {COMPANY}, suppliers, customers, and the same operating period.",
                "It is orientation material and does not settle the target claim.",
            ],
        ),
        visible_citations=[],
        stance="background",
        supports_gold_verdict=False,
        contamination=[],
        upstream_root=doc_id,
        valid_time=target_time,
        evidence_quality="background",
    )
    documents.append(doc)
    gold_docs.append(gold)


def make_phase2r_episode(index: int, episode_type: str, params: Dict[str, object], rng: Random) -> Tuple[Task, List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    task_id = f"eha2r_{index:03d}"
    fact = fact_for(base_episode_type(episode_type), index)
    documents: List[AgentDocument] = []
    gold_docs: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    duplicate_count = int(params.get("duplicate_count", 1))
    primary_visibility_target = params.get("primary_visibility_under_bm25_top8")
    primary_visible = bool(primary_visibility_target) if primary_visibility_target is not None else True
    pollutant_root = f"{task_id}_pollutant_root"
    primary_support: List[str] = []

    no_primary_episode = episode_type in {"halupedia_or_generated_lore", "insufficient_or_no_primary"}
    if not no_primary_episode:
        primary_support = add_primary_docs(
            task_id=task_id,
            claim_id=fact.claim_id,
            episode_type=episode_type,
            target_time=fact.target_time,
            primary_phrase=fact.primary_phrase,
            primary_visible=primary_visible,
            documents=documents,
            gold_docs=gold_docs,
            edges=edges,
        )

    if episode_type == "clean_control":
        contamination = ["temporal_pollution"]
        source_type = "old_planning_note"
        stance = "stale_context"
        rank_boost = 0.05
    elif episode_type == "false_consensus_stress":
        contamination = ["consensus_fabrication"]
        source_type = AUTHORITY_SOURCE_TYPES[index % len(AUTHORITY_SOURCE_TYPES)]
        stance = "supports_false_claim"
        rank_boost = 8.5 if not primary_visible else 3.0
    elif episode_type == "citation_laundering_trace":
        contamination = ["citation_laundering"]
        source_type = "supplier_whitepaper"
        stance = "supports_false_claim"
        rank_boost = 1.2
    elif episode_type == "temporal_pollution_compare":
        contamination = ["temporal_pollution"]
        source_type = "old_certificate_notice"
        stance = "supports_false_claim"
        rank_boost = 1.0
    elif episode_type == "mixed_source_corruption_v2":
        contamination = ["mixed_source_corruption"]
        source_type = "official_appendix"
        stance = "supports_false_claim"
        rank_boost = 0.7
    else:
        contamination = ["query_induced_pollution"]
        source_type = "wiki_style_summary"
        stance = "supports_false_claim"
        rank_boost = 2.0

    pollutant_body = [
        fact.pollutant_phrase.capitalize() + ".",
        f"This source repeats the wording of the question: {fact.question}",
        "It presents the result as settled and cites secondary summaries rather than raw records.",
    ]
    if episode_type == "false_consensus_stress":
        pollutant_body.append("Executive and industry summaries describe the repeated figure as a confirmed operating result.")
    doc, gold = _doc(
        task_id=task_id,
        claim_id=fact.claim_id,
        doc_id=pollutant_root,
        title=f"Authoritative-looking summary claiming {fact.false_value}",
        source_type=source_type,
        timestamp="2024-11-03",
        body=_body("Authoritative-looking summary", pollutant_body),
        visible_citations=[],
        stance=stance,
        supports_gold_verdict=False,
        contamination=contamination,
        upstream_root=pollutant_root,
        generated=episode_type in {"halupedia_or_generated_lore", "insufficient_or_no_primary"},
        stale=episode_type == "temporal_pollution_compare",
        valid_time="2023-Q4" if episode_type == "temporal_pollution_compare" else fact.target_time,
        evidence_quality="polluted_root",
        rank_boost=rank_boost,
    )
    documents.append(doc)
    gold_docs.append(gold)

    duplicate_docs = duplicate_docs_for(duplicate_count) if episode_type == "false_consensus_stress" else rng.randint(3, 5)
    for offset in range(duplicate_docs):
        doc_id = f"{task_id}_repost_{offset:02d}"
        doc, gold = _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=doc_id,
            title=f"Secondary coverage {offset + 1}: {fact.false_value}",
            source_type=AUTHORITY_SOURCE_TYPES[(index + offset) % len(AUTHORITY_SOURCE_TYPES)],
            timestamp=f"2024-11-{4 + offset:02d}",
            body=_body(
                "Secondary coverage",
                [
                    f"This item repeats that {fact.false_value}.",
                    f"It cites {pollutant_root} and another summary using the same claim phrasing.",
                    "The channel looks independent, but the claim text is copied from the same upstream story.",
                ],
            ),
            visible_citations=[pollutant_root],
            stance="supports_false_claim",
            supports_gold_verdict=False,
            contamination=["consensus_fabrication" if episode_type == "false_consensus_stress" else "secondary_pollution"],
            upstream_root=pollutant_root,
            generated=episode_type in {"halupedia_or_generated_lore", "insufficient_or_no_primary"} and offset == 0,
            stale=episode_type == "temporal_pollution_compare",
            valid_time="2023-Q4" if episode_type == "temporal_pollution_compare" else fact.target_time,
            evidence_quality="unsupported_repost",
            rank_boost=9.0 if episode_type == "false_consensus_stress" and not primary_visible else 3.2 if episode_type == "false_consensus_stress" else 0.35,
        )
        documents.append(doc)
        gold_docs.append(gold)
        edges.append(DependencyEdge(from_doc=doc_id, to_doc=pollutant_root, relation="reposts"))

    if episode_type == "citation_laundering_trace":
        target = f"{task_id}_citation_target"
        doc, gold = _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=target,
            title="Whitepaper cited as SLA proof",
            source_type="supplier_whitepaper",
            timestamp="2024-10-20",
            body=_body("Supplier whitepaper", ["The whitepaper discusses packaging changes but does not contain the Q3 SLA table."]),
            visible_citations=[],
            stance="irrelevant_citation_target",
            supports_gold_verdict=False,
            contamination=["citation_laundering"],
            upstream_root=target,
            valid_time=fact.target_time,
            evidence_quality="does_not_support_claim",
            rank_boost=0.4,
        )
        documents.append(doc)
        gold_docs.append(gold)
        edges.append(DependencyEdge(from_doc=pollutant_root, to_doc=target, relation="cites"))
    elif episode_type == "temporal_pollution_compare":
        older = f"{task_id}_old_version"
        doc, gold = _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=older,
            title="Prior version certificate notice",
            source_type="version_history",
            timestamp="2023-12-12",
            body=_body("Old version", [fact.pollutant_phrase.capitalize() + ".", "This was true when issued but not current for January 2025."]),
            visible_citations=[],
            stance="stale_context",
            supports_gold_verdict=False,
            contamination=["temporal_pollution"],
            upstream_root=older,
            stale=True,
            valid_time="2023-Q4",
            evidence_quality="stale_version",
            rank_boost=1.5,
        )
        documents.append(doc)
        gold_docs.append(gold)
    elif episode_type == "mixed_source_corruption_v2":
        appendix = f"{task_id}_corrupted_appendix"
        doc, gold = _doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            doc_id=appendix,
            title="Official appendix with corrupted attribution row",
            source_type="official_appendix",
            timestamp="2025-01-04",
            body=_body("Appendix row", [fact.pollutant_phrase.capitalize() + ".", "Other rows are reliable, but this row uses an obsolete export."]),
            visible_citations=primary_support[:1],
            stance="supports_false_claim",
            supports_gold_verdict=False,
            contamination=["mixed_source_corruption"],
            upstream_root=appendix,
            valid_time=fact.target_time,
            evidence_quality="corrupted_table",
            rank_boost=0.7,
        )
        documents.append(doc)
        gold_docs.append(gold)
        if primary_support:
            edges.append(DependencyEdge(from_doc=appendix, to_doc=primary_support[0], relation="misreads"))

    while len(documents) < 14:
        add_context_doc(
            task_id=task_id,
            claim_id=fact.claim_id,
            index=len(documents),
            rng=rng,
            target_time=fact.target_time,
            documents=documents,
            gold_docs=gold_docs,
        )

    known_contaminants = [gold.doc_id for gold in gold_docs if gold.is_contaminated]
    task = Task(
        task_id=task_id,
        question=fact.question,
        target_claim_id=fact.claim_id,
        difficulty="L3" if episode_type in {"false_consensus_stress", "halupedia_or_generated_lore"} else "L2",
        episode_type=episode_type,
        pollution_types=sorted({kind for gold in gold_docs for kind in gold.contamination}),
        duplicate_count=duplicate_count,
        phase="phase2r",
        primary_visibility_under_bm25_top8=None,
        pollutant_root_id=pollutant_root,
        pollutant_saturation_at_8_target=0.75 if episode_type == "false_consensus_stress" and duplicate_count >= 20 and not primary_visible else None,
        primary_refutation_docs=primary_support if fact.gold_verdict == "refuted" else [],
        gold=TaskGold(
            verdict=fact.gold_verdict if fact.gold_verdict != "mixed" else "refuted",  # type: ignore[arg-type]
            scope_tag=phase2r_scope_tag(episode_type),  # type: ignore[arg-type]
            answer_brief=fact.answer_brief,
            primary_support=primary_support,
            known_contaminants=known_contaminants,
        ),
    )
    apply_stress_metadata(task, documents, gold_docs)
    return task, documents, gold_docs, edges


def apply_stress_metadata(task: Task, documents: List[AgentDocument], gold_docs: List[GoldDocument]) -> None:
    hits = rank_episode(task.question, documents, gold_docs)[:8]
    selected_ids = [hit.doc.doc_id for hit in hits]
    primary_ids = set(task.gold.primary_support)
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    primary_visible = bool(primary_ids & set(selected_ids))
    pollutant_roots = Counter(gold_by_id[doc_id].upstream_root for doc_id in selected_ids if gold_by_id[doc_id].is_contaminated)
    saturation = max(pollutant_roots.values()) / len(hits) if hits and pollutant_roots else 0.0
    task.primary_visibility_under_bm25_top8 = primary_visible
    no_clean_primary = not any(doc_id in primary_ids and not gold_by_id[doc_id].is_contaminated for doc_id in selected_ids)
    task.stress_score = int(not primary_visible) + int(saturation >= 0.75) + int(task.duplicate_count >= 20) + int(no_clean_primary)
    if (
        task.episode_type == "false_consensus_stress"
        and task.duplicate_count >= 20
        and task.pollutant_saturation_at_8_target is not None
        and (primary_visible or saturation < 0.75)
    ):
        raise RuntimeError(
            f"{task.task_id} failed high-pressure constraints: primary_visible={primary_visible} saturation={saturation:.3f}"
        )


def generate_phase2r_dataset(seed: int = 6271) -> Tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    rng = Random(seed)
    tasks: List[Task] = []
    documents: List[AgentDocument] = []
    gold_documents: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    plan = phase2r_plan()
    for index, (episode_type, params) in enumerate(plan):
        task, task_docs, task_gold, task_edges = make_phase2r_episode(index, episode_type, params, rng)
        tasks.append(task)
        documents.extend(task_docs)
        gold_documents.extend(task_gold)
        edges.extend(task_edges)
    manifest = Manifest(
        name="EHA-v2R-stress-pilot",
        seed=seed,
        episodes=len(tasks),
        created_by="eha.phase2r_generate",
        notes="Stress-calibrated Phase 2R pilot. Scorer-only fields must not be shown to agents or tools.",
        episode_type_counts=dict(Counter(task.episode_type for task in tasks)),
    )
    return manifest, tasks, documents, gold_documents, edges


def write_phase2r_dataset(
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
    seed: int = typer.Option(6271, help="Deterministic stress-pilot seed."),
    out_dir: Path = typer.Option(Path("data/phase2r-stress-pilot"), help="Output directory."),
) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_phase2r_dataset(seed=seed)
    write_phase2r_dataset(out_dir, manifest, tasks, documents, gold_documents, edges)
    console.print(f"[green]Generated[/green] {len(tasks)} Phase 2R tasks and {len(documents)} documents in {out_dir}")


if __name__ == "__main__":
    app()
