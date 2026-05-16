from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

import typer
from rich.console import Console

from .phase2s_scoring import (
    aggregate_phase2s,
    derived_gold_diagnostics,
    derived_gold_risks,
    score_phase2s_run,
)
from .report import markdown_table, write_csv
from .schemas import (
    AgentDocument,
    EvidenceDiagnostics,
    GoldDocument,
    Phase2SPrediction,
    Phase2SRunRecord,
    Task,
    ToolCall,
    VerificationLedgerEntry,
    by_task,
    write_json,
)
from .surface_cue_report import load_surface_cue_dataset, parse_surface_claim_id


app = typer.Typer(add_completion=False, help="Score no-API EHA Step 2 surface-cue baselines.")
console = Console()

SURFACE_CUE_BASELINES = ("oracle_gold_contract", "always_insufficient", "source_type_prior")
AUTHORITY_SOURCE_TYPES = {"audit_report", "database_export", "regulator_filing", "certification_record"}


def gold_environment_observations(task: Task, final_doc_ids: Sequence[str], gold_documents: Sequence[GoldDocument]) -> Dict[str, str]:
    gold_by_id = {gold.doc_id: gold for gold in gold_documents}
    visible_gold = [gold_by_id[doc_id] for doc_id in dict.fromkeys(final_doc_ids) if doc_id in gold_by_id]
    upstream_roots = Counter(gold.upstream_root for gold in visible_gold if gold.upstream_root)
    contamination = {kind for gold in visible_gold for kind in gold.contamination}
    stances = {gold.stance for gold in visible_gold}
    qualities = {gold.evidence_quality for gold in visible_gold}
    conflicting = any(
        stance in {"supports_false_claim", "irrelevant_citation_target"} for stance in stances
    ) or any(task.gold.verdict == "refuted" and gold.supports_gold_verdict for gold in visible_gold)
    partial = "mixed_source_corruption" in contamination or "corrupted_table" in qualities or task.gold.scope_tag == "partial"
    return {
        "visible_stale_or_superseded_material": "yes"
        if any(gold.stale or "temporal_pollution" in gold.contamination for gold in visible_gold)
        else "no",
        "visible_conflicting_material": "yes" if conflicting else "no",
        "visible_generated_or_synthetic_lore": "yes" if any(gold.generated for gold in visible_gold) else "no",
        "visible_reposts_or_same_root_repetition": "yes"
        if any(count >= 2 for count in upstream_roots.values()) or bool({"consensus_fabrication", "secondary_pollution", "surface_cue_repetition"} & contamination)
        else "no",
        "visible_citation_chain_problem": "yes" if "citation_laundering" in contamination else "no",
        "visible_partial_or_scope_limited_support": "yes" if partial else "no",
    }


def no_primary_diagnostics() -> EvidenceDiagnostics:
    return EvidenceDiagnostics.model_validate(
        {
            "has_primary_support": "no",
            "primary_support_is_current": "not_applicable",
            "evidence_has_conflict": "no",
            "support_is_partial": "no",
            "sources_are_independent": "uncertain",
            "citation_laundering_detected": "no",
            "generated_lore_detected": "no",
            "no_primary_source_detected": "yes",
        }
    )


def conflict_diagnostics() -> EvidenceDiagnostics:
    return EvidenceDiagnostics.model_validate(
        {
            "has_primary_support": "yes",
            "primary_support_is_current": "yes",
            "evidence_has_conflict": "yes",
            "support_is_partial": "no",
            "sources_are_independent": "uncertain",
            "citation_laundering_detected": "no",
            "generated_lore_detected": "no",
            "no_primary_source_detected": "no",
        }
    )


def oracle_prediction(task: Task, docs: Sequence[AgentDocument], gold_docs: Sequence[GoldDocument]) -> Tuple[Phase2SPrediction, List[ToolCall], List[Dict[str, Any]]]:
    doc_ids = [doc.doc_id for doc in docs]
    contaminants = [gold.doc_id for gold in gold_docs if gold.is_contaminated]
    ledger_evidence = list(task.gold.primary_support)
    tool_calls: List[ToolCall] = []
    tool_results: List[Dict[str, Any]] = []
    if task.target_claim_id.startswith("c_surface_active_verification_") and task.primary_refutation_docs and task.pollutant_root_id:
        compare_target = task.primary_refutation_docs[0]
        tool_calls = [
            ToolCall(tool="compare_versions", args={"doc_ids": [compare_target, task.pollutant_root_id]}),
            ToolCall(tool="trace_citation", args={"doc_id": task.pollutant_root_id}),
        ]
        tool_results = [
            {"versions": [{"doc_id": compare_target}, {"doc_id": task.pollutant_root_id}]},
            {"trace": [{"doc_id": task.pollutant_root_id}]},
        ]
        ledger_evidence = [compare_target, task.pollutant_root_id]
    elif task.gold.verdict == "insufficient":
        ledger_evidence = contaminants[:2]

    prediction = Phase2SPrediction(
        claim_verdict=task.gold.verdict,  # type: ignore[arg-type]
        confidence=0.82 if task.gold.verdict != "insufficient" else 0.68,
        environment_observations=gold_environment_observations(task, doc_ids, gold_docs),
        evidence_diagnostics=EvidenceDiagnostics.model_validate(derived_gold_diagnostics(task)),
        critical_risks=derived_gold_risks(task),  # type: ignore[arg-type]
        supporting_evidence=list(task.gold.primary_support) if task.gold.verdict != "insufficient" else [],
        rejected_evidence=contaminants,
        verification_ledger=[
            VerificationLedgerEntry(
                risk_checked="temporal_staleness" if "stale_evidence" in derived_gold_risks(task) else "generated_lore" if "generated_lore" in derived_gold_risks(task) else "primary_support",
                method="compare_versions" if tool_calls else "read_docs",
                evidence=ledger_evidence,
                finding="Gold-contract baseline uses known labels to validate the surface-cue scoring path.",
                effect_on_verdict="makes_insufficient" if task.gold.verdict == "insufficient" else "refutes" if task.gold.verdict == "refuted" else "supports",
            )
        ],
        answer=task.gold.answer_brief,
    )
    return prediction, tool_calls, tool_results


def always_insufficient_prediction(task: Task, docs: Sequence[AgentDocument], gold_docs: Sequence[GoldDocument]) -> Tuple[Phase2SPrediction, List[ToolCall], List[Dict[str, Any]]]:
    _ = (docs, gold_docs)
    prediction = Phase2SPrediction(
        claim_verdict="insufficient",
        confidence=0.60,
        environment_observations={},
        evidence_diagnostics=no_primary_diagnostics(),
        critical_risks=["no_primary_source"],
        supporting_evidence=[],
        rejected_evidence=[],
        verification_ledger=[
            VerificationLedgerEntry(
                risk_checked="primary_support",
                method="read_docs",
                evidence=[],
                finding="Conservative baseline abstains instead of assigning support.",
                effect_on_verdict="makes_insufficient",
            )
        ],
        answer="Insufficient evidence.",
    )
    return prediction, [], []


def source_type_prior_prediction(task: Task, docs: Sequence[AgentDocument], gold_docs: Sequence[GoldDocument]) -> Tuple[Phase2SPrediction, List[ToolCall], List[Dict[str, Any]]]:
    _ = gold_docs
    support = [doc.doc_id for doc in docs if doc.source_type in AUTHORITY_SOURCE_TYPES]
    if support:
        prediction = Phase2SPrediction(
            claim_verdict="refuted",
            confidence=0.66,
            environment_observations={},
            evidence_diagnostics=conflict_diagnostics(),
            critical_risks=["conflicting_evidence"],
            supporting_evidence=support,
            rejected_evidence=[],
            verification_ledger=[
                VerificationLedgerEntry(
                    risk_checked="source_independence",
                    method="read_docs",
                    evidence=support,
                    finding="Source-type prior trusts high-authority metadata without reading the evidence role.",
                    effect_on_verdict="refutes",
                )
            ],
            answer="The high-authority source types appear decisive.",
        )
    else:
        prediction = Phase2SPrediction(
            claim_verdict="insufficient",
            confidence=0.56,
            environment_observations={},
            evidence_diagnostics=no_primary_diagnostics(),
            critical_risks=["no_primary_source"],
            supporting_evidence=[],
            rejected_evidence=[],
            verification_ledger=[
                VerificationLedgerEntry(
                    risk_checked="primary_support",
                    method="read_docs",
                    evidence=[],
                    finding="Source-type prior found no high-authority metadata.",
                    effect_on_verdict="makes_insufficient",
                )
            ],
            answer="Insufficient authority cues.",
        )
    return prediction, [], []


def baseline_prediction(
    strategy: str,
    task: Task,
    docs: Sequence[AgentDocument],
    gold_docs: Sequence[GoldDocument],
) -> Tuple[Phase2SPrediction, List[ToolCall], List[Dict[str, Any]]]:
    if strategy == "oracle_gold_contract":
        return oracle_prediction(task, docs, gold_docs)
    if strategy == "always_insufficient":
        return always_insufficient_prediction(task, docs, gold_docs)
    if strategy == "source_type_prior":
        return source_type_prior_prediction(task, docs, gold_docs)
    raise ValueError(f"unknown surface-cue baseline strategy: {strategy}")


def build_surface_cue_baseline_records(
    tasks: Sequence[Task],
    documents: Sequence[AgentDocument],
    gold_documents: Sequence[GoldDocument],
) -> List[Phase2SRunRecord]:
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    records: List[Phase2SRunRecord] = []
    for task in tasks:
        final_doc_ids = [doc.doc_id for doc in docs_by_task[task.task_id]]
        for strategy in SURFACE_CUE_BASELINES:
            prediction, tool_calls, tool_results = baseline_prediction(strategy, task, docs_by_task[task.task_id], gold_by_task[task.task_id])
            records.append(
                Phase2SRunRecord(
                    task_id=task.task_id,
                    module="surface_cue",
                    dataset="phase2_surface_cue_smoke",
                    model=strategy,
                    retriever="full_context_no_api",
                    strategy=strategy,
                    prompt="surface_cue_no_api_baseline",
                    backend="no_api",
                    initial_doc_ids=final_doc_ids,
                    final_doc_ids=final_doc_ids,
                    prediction=prediction,
                    parse_success=True,
                    tool_parse_success=True,
                    tool_calls=tool_calls,
                    tool_results=tool_results,
                    usage={},
                    cost_usd=0.0,
                )
            )
    return records


def enrich_surface_cue_score_rows(rows: Sequence[Mapping[str, Any]], tasks: Sequence[Task]) -> List[Dict[str, Any]]:
    task_by_id = {task.task_id: task for task in tasks}
    output: List[Dict[str, Any]] = []
    for row in rows:
        task = task_by_id[str(row["task_id"])]
        family, template_id, axis = parse_surface_claim_id(task.target_claim_id)
        enriched = dict(row)
        enriched.update(
            {
                "family": family,
                "template_id": template_id,
                "surface_axis": axis,
                "target_claim_id": task.target_claim_id,
            }
        )
        output.append(enriched)
    return output


def score_surface_cue_baselines(
    tasks: Sequence[Task],
    documents: Sequence[AgentDocument],
    gold_documents: Sequence[GoldDocument],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    records = build_surface_cue_baseline_records(tasks, documents, gold_documents)
    rows = enrich_surface_cue_score_rows(score_phase2s_run(records, tasks, gold_documents), tasks)
    metrics = aggregate_phase2s(rows, ["strategy"])
    axis_metrics = aggregate_phase2s(rows, ["strategy", "surface_axis"])
    return rows, metrics, axis_metrics


def render_surface_cue_score_markdown(summary: Mapping[str, Any], metrics: Sequence[Mapping[str, Any]], axis_metrics: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "# EHA Step 2 Surface-Cue Scoring Pipeline",
        "",
        "Date: 2026-05-16",
        "",
        "This no-API report verifies that the surface-cue smoke dataset can be consumed by the Phase 2S scoring contract. The baseline rows are scaffolding and sanity checks, not model evidence.",
        "",
        "## Inputs",
        "",
        f"- Dataset directory: `{summary['dataset_dir']}`",
        f"- Tasks: {summary['tasks']}",
        f"- Documents: {summary['documents']}",
        f"- Baseline records: {summary['records']}",
        f"- Baselines: {', '.join(summary['baselines'])}",
        "",
        "## Baseline Metrics",
        "",
    ]
    lines.extend(
        markdown_table(
            metrics,
            [
                "strategy",
                "n",
                "claim_accuracy",
                "escape_rate",
                "support_role_valid_rate",
                "support_role_clean_only_rate",
                "contaminated_citation_rate",
                "useful_compare_versions_rate",
                "trace_rate",
            ],
        )
    )
    lines.extend(["", "## Source-Type Prior By Axis", ""])
    lines.extend(
        markdown_table(
            [row for row in axis_metrics if row["strategy"] == "source_type_prior"],
            [
                "surface_axis",
                "n",
                "claim_accuracy",
                "support_role_valid_rate",
                "support_role_clean_only_rate",
                "contaminated_citation_rate",
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The oracle baseline validates the scorer path. The always-insufficient baseline defines the conservative-abstention floor. The source-type prior is intentionally brittle: it reaches only the abstention-level claim accuracy while adding contaminated support under metadata perturbation and adversarial spoofing. That gives the future API pilot a concrete surface-cue sanity check.",
            "",
        ]
    )
    return "\n".join(lines)


def write_surface_cue_score_report(dataset_dir: Path, out_dir: Path) -> Dict[str, Any]:
    tasks, documents, gold_documents, _ = load_surface_cue_dataset(dataset_dir)
    rows, metrics, axis_metrics = score_surface_cue_baselines(tasks, documents, gold_documents)
    summary: Dict[str, Any] = {
        "dataset_dir": str(dataset_dir),
        "tasks": len(tasks),
        "documents": len(documents),
        "gold_documents": len(gold_documents),
        "records": len(rows),
        "baselines": list(SURFACE_CUE_BASELINES),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "surface_cue_scored_baselines.csv", rows)
    write_csv(out_dir / "surface_cue_baseline_metrics.csv", metrics)
    write_csv(out_dir / "surface_cue_axis_metrics.csv", axis_metrics)
    write_json(out_dir / "eha_step2_surface_cue_scoring_summary.json", summary)
    (out_dir / "eha-step2-surface-cue-scoring-pipeline-2026-05-16.md").write_text(
        render_surface_cue_score_markdown(summary, metrics, axis_metrics),
        encoding="utf-8",
    )
    return summary


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/phase2-surface-cue-smoke"), help="Surface-cue dataset directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Output report directory."),
) -> None:
    summary = write_surface_cue_score_report(dataset_dir, out_dir)
    console.print(
        f"[green]Wrote[/green] surface-cue scoring report for {summary['records']} no-API baseline records to {out_dir}"
    )


if __name__ == "__main__":
    app()
