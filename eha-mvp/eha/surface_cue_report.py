from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

import typer
from rich.console import Console

from .phase2_retrieval import retrieve
from .schemas import (
    AgentDocument,
    GoldDocument,
    Task,
    by_task,
    document_from_dict,
    gold_document_from_dict,
    read_jsonl,
    task_from_dict,
    write_json,
)
from .surface_cue_generate import SURFACE_CUE_AXES, SURFACE_CUE_FAMILIES


app = typer.Typer(add_completion=False, help="Build no-API EHA Step 2 surface-cue balance reports.")
console = Console()


FORBIDDEN_VISIBLE_TERMS = {
    "supports_gold",
    "supports_false_claim",
    "contamination",
    "known_contaminants",
    "gold verdict",
    "pollutant",
    "primary_a",
    "primary_b",
}


def parse_surface_claim_id(target_claim_id: str) -> Tuple[str, str, str]:
    if not target_claim_id.startswith("c_surface_"):
        raise ValueError(f"not a surface-cue claim id: {target_claim_id}")
    suffix = target_claim_id.removeprefix("c_surface_")
    for family in sorted(SURFACE_CUE_FAMILIES, key=len, reverse=True):
        prefix = f"{family}_"
        if not suffix.startswith(prefix):
            continue
        rest = suffix.removeprefix(prefix)
        for axis in SURFACE_CUE_AXES:
            axis_suffix = f"_{axis}"
            if rest.endswith(axis_suffix):
                template_id = rest[: -len(axis_suffix)]
                if not template_id:
                    raise ValueError(f"missing template id in claim id: {target_claim_id}")
                return family, template_id, axis
    raise ValueError(f"unrecognized surface-cue claim id: {target_claim_id}")


def load_surface_cue_dataset(dataset_dir: Path) -> Tuple[List[Task], List[AgentDocument], List[GoldDocument], List[Dict[str, Any]]]:
    tasks = [task_from_dict(row) for row in read_jsonl(dataset_dir / "tasks.jsonl")]
    documents = [document_from_dict(row) for row in read_jsonl(dataset_dir / "documents.jsonl")]
    gold_documents = [gold_document_from_dict(row) for row in read_jsonl(dataset_dir / "gold_documents.jsonl")]
    action_rows = list(read_jsonl(dataset_dir / "action_gold.jsonl"))
    return tasks, documents, gold_documents, action_rows


def visible_leakage_count(tasks: List[Task], documents: List[AgentDocument]) -> int:
    count = 0
    for task in tasks:
        visible = f"{task.task_id} {task.question}".lower()
        if any(term in visible for term in FORBIDDEN_VISIBLE_TERMS):
            count += 1
    for doc in documents:
        visible = f"{doc.doc_id} {doc.title} {doc.source_type} {doc.body}".lower()
        if any(term in visible for term in FORBIDDEN_VISIBLE_TERMS):
            count += 1
    return count


def pair_contract_violations(tasks: List[Task]) -> List[Dict[str, Any]]:
    by_claim: Dict[str, List[Task]] = defaultdict(list)
    for task in tasks:
        by_claim[task.target_claim_id].append(task)

    violations: List[Dict[str, Any]] = []
    for claim_id, pair in sorted(by_claim.items()):
        verdicts = {task.gold.verdict for task in pair}
        answers = {task.gold.answer_brief for task in pair}
        risks = {tuple(task.gold.critical_risks) for task in pair}
        axes = {parse_surface_claim_id(task.target_claim_id)[2] for task in pair}
        if len(pair) != 2 or len(verdicts) != 1 or len(answers) != 1 or len(risks) != 1 or len(axes) != 1:
            violations.append(
                {
                    "target_claim_id": claim_id,
                    "rows": len(pair),
                    "verdicts": sorted(verdicts),
                    "answer_count": len(answers),
                    "critical_risk_sets": [list(item) for item in sorted(risks)],
                    "axes": sorted(axes),
                }
            )
    return violations


def retrieval_observability(tasks: List[Task], documents: List[AgentDocument], gold_documents: List[GoldDocument]) -> Dict[str, int]:
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    clean_support_required = 0
    clean_support_observable = 0
    contaminated_observable = 0

    for task in tasks:
        hits = retrieve(task.question, docs_by_task[task.task_id], gold_by_task[task.task_id], "bm25_top8")
        hit_ids = {hit.doc.doc_id for hit in hits}
        gold_by_id = {gold.doc_id: gold for gold in gold_by_task[task.task_id]}
        if task.gold.primary_support:
            clean_support_required += 1
            if set(task.gold.primary_support) & hit_ids:
                clean_support_observable += 1
        if any(gold_by_id[doc_id].is_contaminated for doc_id in hit_ids):
            contaminated_observable += 1

    return {
        "clean_support_required_rows": clean_support_required,
        "clean_support_observable_rows": clean_support_observable,
        "contaminated_observable_rows": contaminated_observable,
    }


def action_target_violations(tasks: List[Task], documents: List[AgentDocument], action_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs_by_task = by_task(documents)
    tasks_by_id = {task.task_id: task for task in tasks}
    violations: List[Dict[str, Any]] = []
    for row in action_rows:
        task = tasks_by_id.get(str(row.get("task_id")))
        if task is None:
            violations.append({"task_id": row.get("task_id"), "reason": "unknown_task"})
            continue
        doc_ids = {doc.doc_id for doc in docs_by_task[task.task_id]}
        required_ids = set(row.get("required_target_doc_ids", []))
        reasons = []
        if row.get("required_action_types") != ["compare_versions", "trace_citation"]:
            reasons.append("unexpected_action_types")
        if not required_ids <= doc_ids:
            reasons.append("target_doc_not_in_task")
        if row.get("compare_versions_target_doc_id") not in task.primary_refutation_docs:
            reasons.append("compare_target_not_primary_refutation")
        if row.get("trace_citation_target_doc_id") != task.pollutant_root_id:
            reasons.append("trace_target_not_pollutant_root")
        if row.get("machine_executable_target_required") is not True:
            reasons.append("machine_executable_target_not_required")
        if reasons:
            violations.append({"task_id": task.task_id, "target_claim_id": task.target_claim_id, "reasons": reasons})
    return violations


def build_surface_cue_balance_summary(dataset_dir: Path) -> Dict[str, Any]:
    tasks, documents, gold_documents, action_rows = load_surface_cue_dataset(dataset_dir)
    family_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()
    axis_counts: Counter[str] = Counter()
    verdict_counts = Counter(task.gold.verdict for task in tasks)
    scope_counts = Counter(task.gold.scope_tag for task in tasks)
    family_axis_counts: Counter[str] = Counter()

    for task in tasks:
        family, template_id, axis = parse_surface_claim_id(task.target_claim_id)
        family_counts[family] += 1
        template_counts[f"{family}:{template_id}"] += 1
        axis_counts[axis] += 1
        family_axis_counts[f"{family}:{axis}"] += 1

    action_violations = action_target_violations(tasks, documents, action_rows)
    active_tasks = [task for task in tasks if parse_surface_claim_id(task.target_claim_id)[0] == "active_verification"]
    return {
        "dataset_dir": str(dataset_dir),
        "tasks": len(tasks),
        "documents": len(documents),
        "gold_documents": len(gold_documents),
        "action_gold_rows": len(action_rows),
        "family_counts": dict(sorted(family_counts.items())),
        "template_counts": dict(sorted(template_counts.items())),
        "axis_counts": dict(sorted(axis_counts.items())),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "scope_counts": dict(sorted(scope_counts.items())),
        "family_axis_counts": dict(sorted(family_axis_counts.items())),
        "pair_contract_violations": pair_contract_violations(tasks),
        "retrieval_observability": retrieval_observability(tasks, documents, gold_documents),
        "active_verification_tasks": len(active_tasks),
        "action_target_violations": action_violations,
        "visible_leakage_count": visible_leakage_count(tasks, documents),
    }


def render_surface_cue_balance_markdown(summary: Dict[str, Any]) -> str:
    retrieval = summary["retrieval_observability"]
    lines = [
        "# EHA Step 2 Surface-Cue Balance Report",
        "",
        "Date: 2026-05-16",
        "",
        "This no-API report checks whether the Step 2 surface-cue smoke dataset is balanced enough to justify design review. It is not model evidence.",
        "",
        "## Counts",
        "",
        f"- Tasks: {summary['tasks']}",
        f"- Documents: {summary['documents']}",
        f"- Gold documents: {summary['gold_documents']}",
        f"- Active-verification action-gold rows: {summary['action_gold_rows']}",
        "",
        "## Balance",
        "",
        f"- Family counts: {summary['family_counts']}",
        f"- Axis counts: {summary['axis_counts']}",
        f"- Verdict counts: {summary['verdict_counts']}",
        f"- Scope counts: {summary['scope_counts']}",
        f"- Template cells: {len(summary['template_counts'])}",
        "",
        "## Contract Checks",
        "",
        f"- Pair contract violations: {len(summary['pair_contract_violations'])}",
        f"- Visible leakage count: {summary['visible_leakage_count']}",
        f"- Action target violations: {len(summary['action_target_violations'])}",
        f"- Clean-support observable rows: {retrieval['clean_support_observable_rows']} / {retrieval['clean_support_required_rows']}",
        f"- Contaminated observable rows: {retrieval['contaminated_observable_rows']} / {summary['tasks']}",
        "",
        "## Decision",
        "",
        "The dataset is ready for human design review and scoring-pipeline integration. It should still not trigger a large API run or 500-1000 task expansion without a separate go/no-go decision.",
        "",
    ]
    return "\n".join(lines)


def write_surface_cue_balance_report(dataset_dir: Path, out_dir: Path) -> Dict[str, Any]:
    summary = build_surface_cue_balance_summary(dataset_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_step2_surface_cue_balance_summary.json", summary)
    (out_dir / "eha-step2-surface-cue-balance-2026-05-16.md").write_text(
        render_surface_cue_balance_markdown(summary),
        encoding="utf-8",
    )
    return summary


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/phase2-surface-cue-smoke"), help="Surface-cue dataset directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Output report directory."),
) -> None:
    summary = write_surface_cue_balance_report(dataset_dir, out_dir)
    console.print(
        f"[green]Wrote[/green] surface-cue balance report for {summary['tasks']} tasks and {summary['action_gold_rows']} action-gold rows to {out_dir}"
    )


if __name__ == "__main__":
    app()
