from __future__ import annotations

from collections import Counter
from pathlib import Path
from random import Random
from typing import Dict, List, Tuple

import typer
from rich.console import Console

from .generate_corpus import _body, _doc
from .generate_world import COMPANY, fact_for
from .schemas import AgentDocument, DependencyEdge, GoldDocument, Manifest, Task, TaskGold, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Generate EHA Phase 2S repair datasets.")
console = Console()


SCOPE_COUNTS: Dict[str, int] = {
    "full_current_primary_support": 20,
    "stale_evidence": 20,
    "conflicting_evidence": 20,
    "generated_lore_with_no_primary": 20,
    "partial_support": 20,
    "citation_laundering": 20,
}

TEMPORAL_COUNTS: Dict[str, int] = {
    "current_policy_overrides_old": 15,
    "old_report_retracted_by_new_audit": 15,
    "certification_expired_or_renewed": 10,
    "version_history_changes_claim": 10,
    "non_temporal_control": 10,
}


def clean_diagnostics() -> Dict[str, str]:
    return {
        "has_primary_support": "yes",
        "primary_support_is_current": "yes",
        "evidence_has_conflict": "no",
        "support_is_partial": "no",
        "sources_are_independent": "yes",
        "citation_laundering_detected": "no",
        "generated_lore_detected": "no",
        "no_primary_source_detected": "no",
    }


def diagnostics_for_scope_type(episode_type: str) -> tuple[str, str, Dict[str, str], List[str]]:
    diagnostics = clean_diagnostics()
    verdict = "supported"
    scope_tag = "full"
    risks: List[str] = []
    if episode_type == "stale_evidence":
        verdict = "refuted"
        scope_tag = "stale"
        diagnostics["primary_support_is_current"] = "no"
        risks = ["stale_evidence"]
    elif episode_type == "conflicting_evidence":
        verdict = "refuted"
        scope_tag = "conflicting"
        diagnostics["evidence_has_conflict"] = "yes"
        risks = ["conflicting_evidence"]
    elif episode_type == "generated_lore_with_no_primary":
        verdict = "insufficient"
        scope_tag = "generated_lore"
        diagnostics["has_primary_support"] = "no"
        diagnostics["primary_support_is_current"] = "not_applicable"
        diagnostics["generated_lore_detected"] = "yes"
        diagnostics["no_primary_source_detected"] = "yes"
        risks = ["generated_lore", "no_primary_source"]
    elif episode_type == "partial_support":
        verdict = "insufficient"
        scope_tag = "partial"
        diagnostics["support_is_partial"] = "yes"
        risks = ["partial_support"]
    elif episode_type == "citation_laundering":
        verdict = "refuted"
        scope_tag = "conflicting"
        diagnostics["sources_are_independent"] = "no"
        diagnostics["citation_laundering_detected"] = "yes"
        risks = ["citation_laundering", "conflicting_evidence"]
    return verdict, scope_tag, diagnostics, risks


def diagnostics_for_temporal_type(episode_type: str) -> tuple[str, str, Dict[str, str], List[str]]:
    diagnostics = clean_diagnostics()
    if episode_type == "non_temporal_control":
        return "supported", "full", diagnostics, []
    diagnostics["primary_support_is_current"] = "no"
    return "refuted", "stale", diagnostics, ["stale_evidence"]


def add_doc(
    documents: List[AgentDocument],
    gold_documents: List[GoldDocument],
    *,
    task_id: str,
    claim_id: str,
    doc_id: str,
    title: str,
    source_type: str,
    timestamp: str,
    sentences: List[str],
    visible_citations: List[str] | None = None,
    stance: str,
    supports_gold_verdict: bool,
    contamination: List[str] | None = None,
    upstream_root: str | None = None,
    generated: bool = False,
    stale: bool = False,
    valid_time: str,
    evidence_quality: str,
    rank_boost: float = 0.0,
) -> None:
    doc, gold = _doc(
        task_id=task_id,
        claim_id=claim_id,
        doc_id=doc_id,
        title=title,
        source_type=source_type,
        timestamp=timestamp,
        body=_body(title, sentences),
        visible_citations=visible_citations or [],
        stance=stance,
        supports_gold_verdict=supports_gold_verdict,
        contamination=contamination or [],
        upstream_root=upstream_root or doc_id,
        generated=generated,
        stale=stale,
        valid_time=valid_time,
        evidence_quality=evidence_quality,
        rank_boost=rank_boost,
    )
    documents.append(doc)
    gold_documents.append(gold)


def scope_current_primary_sentences(episode_type: str) -> List[str]:
    if episode_type == "full_current_primary_support":
        return [
            "The signed current record explicitly supports the target claim for this case.",
            "It states that the claim is current, complete, and reviewer-signed.",
        ]
    if episode_type == "stale_evidence":
        return [
            "The signed current record says the target claim is not supported under the current status.",
            "It supersedes the older record that appeared to support the claim.",
        ]
    if episode_type == "conflicting_evidence":
        return [
            "The signed current record directly contradicts the target claim for this case.",
            "It is the current claim-level primary record and carries reviewer sign-off.",
        ]
    if episode_type == "partial_support":
        return [
            "The signed current record says the available primary evidence does not establish the broader target claim.",
            "Only a narrower operational detail is documented, leaving a material component unresolved.",
        ]
    if episode_type == "citation_laundering":
        return [
            "The signed current record says the target claim is not supported by the cited chain.",
            "It rejects the laundered summary as claim-level evidence for this case.",
        ]
    return [
        "The signed current record gives the claim-level status for this case.",
        "It is scoped to the target question and contains reviewer sign-off.",
    ]


def make_scope_episode(index: int, episode_type: str, rng: Random) -> Tuple[Task, List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    task_id = f"eha2s_a_{index:03d}"
    claim_id = f"c_scope_{episode_type}_{index:03d}"
    verdict, scope_tag, diagnostics, risks = diagnostics_for_scope_type(episode_type)
    question = f"What is the evidence status for {COMPANY} scope diagnostic case {index}?"
    answer = "The provided evidence is sufficient and current." if verdict == "supported" else "The provided evidence does not safely support the target claim."
    docs: List[AgentDocument] = []
    gold_docs: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    current_id = f"{task_id}_current_primary"

    if episode_type != "generated_lore_with_no_primary":
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=current_id,
            title=f"{COMPANY} current primary record",
            source_type="audit_report",
            timestamp="2025-01-20",
            sentences=scope_current_primary_sentences(episode_type),
            stance="supports_gold",
            supports_gold_verdict=verdict == "supported",
            valid_time="2025-Q1",
            evidence_quality="primary_record",
            rank_boost=2.0,
        )

    old_id = f"{task_id}_old_record"
    if episode_type in {"stale_evidence", "conflicting_evidence", "citation_laundering"}:
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=old_id,
            title=f"{COMPANY} outdated or conflicting record",
            source_type="version_history",
            timestamp="2023-11-15",
            sentences=[
                "This older record appears to support the target claim if read alone.",
                "Later records supersede or contradict this earlier status.",
            ],
            stance="supports_false_claim",
            supports_gold_verdict=False,
            contamination=["temporal_pollution" if episode_type == "stale_evidence" else "conflict"],
            stale=episode_type == "stale_evidence",
            valid_time="2023-Q4",
            evidence_quality="stale_version",
            rank_boost=1.5,
        )
        edges.append(DependencyEdge(from_doc=current_id, to_doc=old_id, relation="updates"))

    if episode_type == "generated_lore_with_no_primary":
        lore_root = f"{task_id}_generated_lore"
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=lore_root,
            title="Generated lore encyclopedia page",
            source_type="wiki_style_summary",
            timestamp="2025-01-05",
            sentences=[
                "This generated page narrates a fictional internal initiative as if it were settled history.",
                "It cites no contract, audit, or board record.",
            ],
            stance="supports_false_claim",
            supports_gold_verdict=False,
            contamination=["generated_lore"],
            upstream_root=lore_root,
            generated=True,
            valid_time="2025-Q1",
            evidence_quality="generated_summary",
            rank_boost=2.0,
        )
        for offset in range(2):
            add_doc(
                docs,
                gold_docs,
                task_id=task_id,
                claim_id=claim_id,
                doc_id=f"{task_id}_lore_repost_{offset}",
                title=f"Lore repost {offset + 1}",
                source_type="forum_digest",
                timestamp=f"2025-01-{6 + offset:02d}",
                sentences=["This digest repeats the generated encyclopedia page without primary records."],
                visible_citations=[lore_root],
                stance="supports_false_claim",
                supports_gold_verdict=False,
                contamination=["generated_lore"],
                upstream_root=lore_root,
                generated=True,
                valid_time="2025-Q1",
                evidence_quality="unsupported_repost",
            )
            edges.append(DependencyEdge(from_doc=f"{task_id}_lore_repost_{offset}", to_doc=lore_root, relation="generated_from"))

    if episode_type == "partial_support":
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=f"{task_id}_partial_primary",
            title="Primary record for a narrower claim",
            source_type="database_export",
            timestamp="2025-01-18",
            sentences=[
                "This record supports a narrower operational detail but not the broader target claim.",
                "The missing portion is material to the answer.",
            ],
            stance="partial_support",
            supports_gold_verdict=False,
            contamination=[],
            valid_time="2025-Q1",
            evidence_quality="partial_primary",
            rank_boost=2.0,
        )

    if episode_type == "citation_laundering":
        target = f"{task_id}_irrelevant_target"
        launderer = f"{task_id}_laundered_summary"
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=target,
            title="Cited technical note that does not support the claim",
            source_type="supplier_whitepaper",
            timestamp="2024-10-01",
            sentences=["The technical note discusses background procedures but does not contain the target result."],
            stance="irrelevant_citation_target",
            supports_gold_verdict=False,
            contamination=["citation_laundering"],
            valid_time="2024-Q4",
            evidence_quality="does_not_support_claim",
        )
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=launderer,
            title="Summary laundering an unsupported citation",
            source_type="industry_digest",
            timestamp="2024-11-02",
            sentences=["The summary claims the target result and points to a technical note that does not say it."],
            visible_citations=[target],
            stance="supports_false_claim",
            supports_gold_verdict=False,
            contamination=["citation_laundering"],
            upstream_root=launderer,
            valid_time="2024-Q4",
            evidence_quality="unsupported_summary",
            rank_boost=1.2,
        )
        edges.append(DependencyEdge(from_doc=launderer, to_doc=target, relation="cites"))

    while len(docs) < rng.randint(4, 8):
        offset = len(docs)
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=f"{task_id}_context_{offset}",
            title=f"Context note {offset}",
            source_type="meeting_minutes",
            timestamp=f"2025-01-{1 + offset:02d}",
            sentences=["This context note mentions the case but does not settle the target claim."],
            stance="background",
            supports_gold_verdict=False,
            valid_time="2025-Q1",
            evidence_quality="background",
        )

    primary_support = [gold.doc_id for gold in gold_docs if gold.supports_gold_verdict]
    contaminants = [gold.doc_id for gold in gold_docs if gold.is_contaminated]
    task = Task(
        task_id=task_id,
        question=question,
        target_claim_id=claim_id,
        difficulty="L2",
        episode_type=episode_type,
        pollution_types=sorted({kind for gold in gold_docs for kind in gold.contamination}),
        duplicate_count=1,
        phase="phase2s_scope",
        gold=TaskGold(
            verdict=verdict,  # type: ignore[arg-type]
            scope_tag=scope_tag,  # type: ignore[arg-type]
            answer_brief=answer,
            primary_support=primary_support,
            known_contaminants=contaminants,
            diagnostics=diagnostics,
            critical_risks=risks,
        ),
    )
    return task, docs, gold_docs, edges


def make_temporal_episode(index: int, episode_type: str, rng: Random) -> Tuple[Task, List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    task_id = f"eha2s_b_{index:03d}"
    base_fact = fact_for("temporal_pollution" if episode_type != "non_temporal_control" else "clean_control", index)
    verdict, scope_tag, diagnostics, risks = diagnostics_for_temporal_type(episode_type)
    claim_id = f"c_temporal_{episode_type}_{index:03d}"
    question_templates = {
        "current_policy_overrides_old": "Does the current Novalis field-service policy still allow the old waiver?",
        "old_report_retracted_by_new_audit": "Does the old HelioPart audit conclusion remain valid after the new audit?",
        "certification_expired_or_renewed": "Is Novalis Robotics' EU safety certification still valid in January 2025?",
        "version_history_changes_claim": "Does version history still support the original accident attribution?",
        "non_temporal_control": "Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?",
    }
    question = question_templates[episode_type]
    docs: List[AgentDocument] = []
    gold_docs: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    old_id = f"{task_id}_old_version"
    new_id = f"{task_id}_current_record"

    if episode_type == "non_temporal_control":
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=new_id,
            title=f"{COMPANY} current audit record",
            source_type="audit_report",
            timestamp="2025-01-16",
            sentences=[base_fact.primary_phrase.capitalize() + ".", "This record is current and directly answers the question."],
            stance="supports_gold",
            supports_gold_verdict=True,
            valid_time="2025-Q1",
            evidence_quality="primary_record",
            rank_boost=3.0,
        )
    else:
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=old_id,
            title="Older version that supports the outdated conclusion",
            source_type="version_history",
            timestamp="2023-12-10",
            sentences=[
                "The older version appears to support the claim if read without later records.",
                "It was true only for the prior reporting period.",
            ],
            stance="supports_false_claim",
            supports_gold_verdict=False,
            contamination=["temporal_pollution"],
            stale=True,
            valid_time="2023-Q4",
            evidence_quality="stale_version",
            rank_boost=4.0,
        )
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=new_id,
            title="Current record that updates the old conclusion",
            source_type="certification_record" if "certification" in episode_type else "audit_report",
            timestamp="2025-01-18",
            sentences=[
                "The current record supersedes the older version and changes the answer to the target claim.",
                "It is the controlling record for the current-status question.",
            ],
            stance="supports_gold",
            supports_gold_verdict=True,
            contamination=[],
            valid_time="2025-Q1",
            evidence_quality="primary_record",
            rank_boost=0.5,
        )
        edges.append(DependencyEdge(from_doc=new_id, to_doc=old_id, relation="updates"))

    add_doc(
        docs,
        gold_docs,
        task_id=task_id,
        claim_id=claim_id,
        doc_id=f"{task_id}_version_index",
        title="Version index listing old and current records",
        source_type="version_history",
        timestamp="2025-01-19",
        sentences=[
            f"The version index lists {old_id} as older and {new_id} as current.",
            "For current-status claims, compare_versions should inspect both records.",
        ],
        visible_citations=[doc_id for doc_id in [old_id, new_id] if doc_id],
        stance="version_index",
        supports_gold_verdict=episode_type != "non_temporal_control",
        contamination=[],
        valid_time="2025-Q1",
        evidence_quality="version_index",
        rank_boost=1.0,
    )

    for offset in range(3):
        add_doc(
            docs,
            gold_docs,
            task_id=task_id,
            claim_id=claim_id,
            doc_id=f"{task_id}_summary_{offset}",
            title=f"Secondary temporal summary {offset + 1}",
            source_type="trade_news",
            timestamp=f"2024-02-{10 + offset:02d}",
            sentences=["This secondary summary repeats the older status and may rank before the current record."],
            visible_citations=[old_id] if episode_type != "non_temporal_control" else [new_id],
            stance="supports_false_claim" if episode_type != "non_temporal_control" else "background",
            supports_gold_verdict=False,
            contamination=["temporal_pollution"] if episode_type != "non_temporal_control" else [],
            upstream_root=old_id if episode_type != "non_temporal_control" else f"{task_id}_summary_{offset}",
            stale=episode_type != "non_temporal_control",
            valid_time="2023-Q4" if episode_type != "non_temporal_control" else "2025-Q1",
            evidence_quality="secondary_summary",
            rank_boost=2.0 if episode_type != "non_temporal_control" else 0.2,
        )

    primary_support = [gold.doc_id for gold in gold_docs if gold.supports_gold_verdict and gold.doc_id != f"{task_id}_version_index"]
    contaminants = [gold.doc_id for gold in gold_docs if gold.is_contaminated]
    task = Task(
        task_id=task_id,
        question=question,
        target_claim_id=claim_id,
        difficulty="L2",
        episode_type=episode_type,
        pollution_types=sorted({kind for gold in gold_docs for kind in gold.contamination}),
        duplicate_count=1,
        phase="phase2s_temporal",
        gold=TaskGold(
            verdict=verdict,  # type: ignore[arg-type]
            scope_tag=scope_tag,  # type: ignore[arg-type]
            answer_brief="The current record controls; older evidence is stale." if verdict == "refuted" else base_fact.answer_brief,
            primary_support=primary_support,
            known_contaminants=contaminants,
            diagnostics=diagnostics,
            critical_risks=risks,
        ),
    )
    return task, docs, gold_docs, edges


def scope_plan() -> List[str]:
    return [episode_type for episode_type, count in SCOPE_COUNTS.items() for _ in range(count)]


def temporal_plan() -> List[str]:
    return [episode_type for episode_type, count in TEMPORAL_COUNTS.items() for _ in range(count)]


def generate_scope_diagnostic_dataset(seed: int = 7319) -> Tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    rng = Random(seed)
    tasks: List[Task] = []
    documents: List[AgentDocument] = []
    gold_documents: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    for index, episode_type in enumerate(scope_plan()):
        task, docs, gold_docs, task_edges = make_scope_episode(index, episode_type, rng)
        tasks.append(task)
        documents.extend(docs)
        gold_documents.extend(gold_docs)
        edges.extend(task_edges)
    manifest = Manifest(
        name="EHA-v2S-scope-diagnostic",
        seed=seed,
        episodes=len(tasks),
        created_by="eha.phase2s_generate",
        notes="Phase 2S module A. Relevant documents are provided directly; no retrieval is used.",
        episode_type_counts=dict(Counter(task.episode_type for task in tasks)),
    )
    return manifest, tasks, documents, gold_documents, edges


def generate_temporal_routing_dataset(seed: int = 8144) -> Tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    rng = Random(seed)
    tasks: List[Task] = []
    documents: List[AgentDocument] = []
    gold_documents: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    for index, episode_type in enumerate(temporal_plan()):
        task, docs, gold_docs, task_edges = make_temporal_episode(index, episode_type, rng)
        tasks.append(task)
        documents.extend(docs)
        gold_documents.extend(gold_docs)
        edges.extend(task_edges)
    manifest = Manifest(
        name="EHA-v2S-temporal-routing",
        seed=seed,
        episodes=len(tasks),
        created_by="eha.phase2s_generate",
        notes="Phase 2S module B. Temporal episodes require version comparison to avoid stale evidence.",
        episode_type_counts=dict(Counter(task.episode_type for task in tasks)),
    )
    return manifest, tasks, documents, gold_documents, edges


def write_dataset(
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


@app.command("scope")
def scope_main(
    seed: int = typer.Option(7319, help="Deterministic Module A seed."),
    out_dir: Path = typer.Option(Path("data/phase2s-scope-diagnostic"), help="Scope diagnostic output directory."),
) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_scope_diagnostic_dataset(seed=seed)
    write_dataset(out_dir, manifest, tasks, documents, gold_documents, edges)
    console.print(f"[green]Generated[/green] {len(tasks)} Phase 2S scope tasks and {len(documents)} documents in {out_dir}")


@app.command("temporal")
def temporal_main(
    seed: int = typer.Option(8144, help="Deterministic Module B seed."),
    out_dir: Path = typer.Option(Path("data/phase2s-temporal-routing"), help="Temporal routing output directory."),
) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_temporal_routing_dataset(seed=seed)
    write_dataset(out_dir, manifest, tasks, documents, gold_documents, edges)
    console.print(f"[green]Generated[/green] {len(tasks)} Phase 2S temporal tasks and {len(documents)} documents in {out_dir}")


@app.command("all")
def all_main(
    scope_out_dir: Path = typer.Option(Path("data/phase2s-scope-diagnostic"), help="Scope diagnostic output directory."),
    temporal_out_dir: Path = typer.Option(Path("data/phase2s-temporal-routing"), help="Temporal routing output directory."),
    scope_seed: int = typer.Option(7319, help="Deterministic Module A seed."),
    temporal_seed: int = typer.Option(8144, help="Deterministic Module B seed."),
) -> None:
    scope_manifest, scope_tasks, scope_docs, scope_gold, scope_edges = generate_scope_diagnostic_dataset(seed=scope_seed)
    temporal_manifest, temporal_tasks, temporal_docs, temporal_gold, temporal_edges = generate_temporal_routing_dataset(seed=temporal_seed)
    write_dataset(scope_out_dir, scope_manifest, scope_tasks, scope_docs, scope_gold, scope_edges)
    write_dataset(temporal_out_dir, temporal_manifest, temporal_tasks, temporal_docs, temporal_gold, temporal_edges)
    console.print(f"[green]Generated[/green] Phase 2S scope dataset in {scope_out_dir}")
    console.print(f"[green]Generated[/green] Phase 2S temporal dataset in {temporal_out_dir}")


if __name__ == "__main__":
    app()
