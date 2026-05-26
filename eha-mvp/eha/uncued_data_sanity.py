from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import typer
from rich.console import Console

from .report import write_csv
from .schemas import write_json
from .uncued_core_claim_common import (
    DEFAULT_DATASET_DIR,
    DEFAULT_OUT_DIR,
    DEFAULT_PILOT_RUN_DIR,
    base_task_id_for_row,
    load_model_rows,
    read_jsonl,
    selected_ids_for_row,
    split_doc_ids,
    support_ids_for_row,
)


app = typer.Typer(add_completion=False, help="Audit EHA-Uncued data sanity and label consistency.")
console = Console()

DOC_ID_RE = re.compile(r"\buncued_\d{3}_d\d+\b")
MONTH_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b",
    re.IGNORECASE,
)
MONTH_TO_NUMBER = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def issue(check: str, severity: str, task_id: str, view: str, subject: str, detail: str) -> Dict[str, str]:
    return {"check": check, "severity": severity, "task_id": task_id, "view": view, "subject": subject, "detail": detail}


def by_task_view(rows: Sequence[Mapping[str, Any]]) -> dict[tuple[str, str], list[Mapping[str, Any]]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row.get("task_id")), str(row.get("view", "")))].append(row)
    return grouped


def doc_ids_by_task_view(docs_by_view: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[tuple[str, str], set[str]]:
    output: dict[tuple[str, str], set[str]] = defaultdict(set)
    for view, docs in docs_by_view.items():
        for doc in docs:
            output[(str(doc["task_id"]), view)].add(str(doc["doc_id"]))
    return output


def parse_claim_month(question: str) -> tuple[int, int] | None:
    match = MONTH_RE.search(question)
    if not match:
        return None
    return int(match.group(2)), MONTH_TO_NUMBER[match.group(1).lower()]


def parse_timestamp_month(timestamp: str) -> tuple[int, int] | None:
    parts = timestamp.split("-")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def audit_doc_id_consistency(*, dataset_dir: Path, pilot_run_dir: Path, docs_by_key: Mapping[tuple[str, str], set[str]]) -> list[Dict[str, str]]:
    rows = load_model_rows(pilot_run_dir, None)
    output: list[Dict[str, str]] = []
    for row in rows:
        task_id = base_task_id_for_row(row)
        view = str(row.get("view", ""))
        known = docs_by_key.get((task_id, view), set())
        refs = set(support_ids_for_row(row)) | set(selected_ids_for_row(row)) | set(split_doc_ids(row.get("rejected_evidence") or row.get("rejected_doc_ids")))
        for ref in refs:
            if ref not in known:
                output.append(issue("doc_id_consistency", "P0", task_id, view, ref, "scored row references a missing document id"))
        for ref in DOC_ID_RE.findall(str(row.get("actions", ""))):
            if ref not in known:
                output.append(issue("doc_id_consistency", "P1", task_id, view, ref, "action text references a doc id outside the task/view document set"))
    return output


def audit_dependency_edges(edges: Sequence[Mapping[str, Any]], docs_by_key: Mapping[tuple[str, str], set[str]]) -> list[Dict[str, str]]:
    output: list[Dict[str, str]] = []
    graph: dict[tuple[str, str], dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for edge in edges:
        task_id = str(edge.get("task_id", ""))
        view = str(edge.get("view", ""))
        source = str(edge.get("from", ""))
        target = str(edge.get("to", ""))
        known = docs_by_key.get((task_id, view), set())
        if source not in known:
            output.append(issue("dependency_edge_consistency", "P0", task_id, view, source, "dependency edge source is missing"))
        if target not in known:
            output.append(issue("dependency_edge_consistency", "P0", task_id, view, target, "dependency edge target is missing"))
        graph[(task_id, view)][source].add(target)
    for (task_id, view), edges_by_source in graph.items():
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            for target in edges_by_source.get(node, set()):
                if visit(target):
                    return True
            visiting.remove(node)
            visited.add(node)
            return False

        for node in list(edges_by_source):
            if visit(node):
                output.append(issue("dependency_edge_consistency", "P1", task_id, view, node, "visible citation graph contains a cycle"))
                break
    return output


def audit_gold_and_pollutants(latent_tasks: Sequence[Mapping[str, Any]], gold_documents: Sequence[Mapping[str, Any]]) -> list[Dict[str, str]]:
    output: list[Dict[str, str]] = []
    gold_by_key = by_task_view(gold_documents)
    for latent in latent_tasks:
        task_id = str(latent["task_id"])
        for view in ("neutral_metadata_visible", "neutral_metadata_hidden"):
            rows = gold_by_key.get((task_id, view), [])
            support_docs = {str(row["doc_id"]) for row in rows if bool(row.get("supports_gold_verdict"))}
            polluted_docs = {str(row["doc_id"]) for row in rows if row.get("contamination")}
            expected_polluted = set(str(item) for item in latent.get("known_polluted_doc_ids_by_view", {}).get(view, []))
            expected_support = set(str(item) for item in latent.get("gold_support_doc_ids_by_view", {}).get(view, []))
            if support_docs != expected_support:
                output.append(issue("gold_verdict_consistency", "P0", task_id, view, ",".join(sorted(support_docs ^ expected_support)), "gold support docs differ between latent task and gold_documents"))
            if polluted_docs != expected_polluted:
                output.append(issue("pollutant_label_consistency", "P0", task_id, view, ",".join(sorted(polluted_docs ^ expected_polluted)), "known polluted docs differ between latent task and gold_documents"))
            if str(latent.get("gold_verdict")) in {"supported", "refuted"} and not support_docs:
                output.append(issue("gold_verdict_consistency", "P0", task_id, view, "gold_support_doc_ids", "supported/refuted task has no clean support doc"))
    return output


def audit_views(docs_by_view: Mapping[str, Sequence[Mapping[str, Any]]], gold_documents: Sequence[Mapping[str, Any]]) -> list[Dict[str, str]]:
    output: list[Dict[str, str]] = []
    visible = by_task_view(docs_by_view["neutral_metadata_visible"])
    hidden = by_task_view(docs_by_view["neutral_metadata_hidden"])
    task_ids = {task_id for task_id, _ in visible} | {task_id for task_id, _ in hidden}
    for task_id in sorted(task_ids):
        visible_docs = visible.get((task_id, "neutral_metadata_visible"), [])
        hidden_docs = hidden.get((task_id, "neutral_metadata_hidden"), [])
        if len(visible_docs) != len(hidden_docs):
            output.append(issue("view_consistency", "P0", task_id, "both", "document_count", "visible and hidden views have different document counts"))
            continue
        visible_bodies = sorted((str(doc.get("title", "")), str(doc.get("body", ""))) for doc in visible_docs)
        hidden_bodies = sorted((str(doc.get("title", "")), str(doc.get("body", ""))) for doc in hidden_docs)
        if visible_bodies != hidden_bodies:
            output.append(issue("view_consistency", "P1", task_id, "both", "title_body_multiset", "visible and hidden views differ beyond intended metadata/doc-id remapping"))
    gold_by_key = by_task_view(gold_documents)
    for task_id in sorted(task_ids):
        if len(gold_by_key.get((task_id, "neutral_metadata_visible"), [])) != len(gold_by_key.get((task_id, "neutral_metadata_hidden"), [])):
            output.append(issue("view_consistency", "P0", task_id, "both", "gold_document_count", "visible and hidden gold views have different row counts"))
    return output


def audit_action_gold(action_gold: Sequence[Mapping[str, Any]], docs_by_key: Mapping[tuple[str, str], set[str]]) -> list[Dict[str, str]]:
    output: list[Dict[str, str]] = []
    for row in action_gold:
        task_id = str(row.get("task_id", ""))
        required_types = set(str(item) for item in row.get("required_action_types", []))
        if bool(row.get("machine_executable_target_required")) and not required_types:
            output.append(issue("action_gold_consistency", "P0", task_id, "", "required_action_types", "machine-executable action target is required but no action type is listed"))
        for view, targets in row.get("required_target_doc_ids_by_view", {}).items():
            known = docs_by_key.get((task_id, str(view)), set())
            for target in targets:
                if str(target) not in known:
                    output.append(issue("action_gold_consistency", "P0", task_id, str(view), str(target), "required action target doc id is missing from view documents"))
    return output


def audit_chronology(tasks: Sequence[Mapping[str, Any]], docs_by_view: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[Dict[str, str]]:
    output: list[Dict[str, str]] = []
    task_by_id = {str(task["task_id"]): task for task in tasks}
    mismatch_count = 0
    examples: list[str] = []
    for view, docs in docs_by_view.items():
        for doc in docs:
            task = task_by_id.get(str(doc.get("task_id", "")))
            if not task:
                continue
            claim_month = parse_claim_month(str(task.get("question", "")))
            timestamp_month = parse_timestamp_month(str(doc.get("timestamp", "")))
            if claim_month and timestamp_month and timestamp_month < claim_month:
                mismatch_count += 1
                if len(examples) < 5:
                    examples.append(f"{doc.get('doc_id')} timestamp={doc.get('timestamp')} claim_month={claim_month[0]}-{claim_month[1]:02d}")
    if mismatch_count:
        output.append(
            issue(
                "chronology_consistency",
                "P1",
                "multiple",
                "both",
                "synthetic_timestamps",
                f"{mismatch_count} document timestamps precede the claim month; examples: {'; '.join(examples)}. Treat timestamps as synthetic/non-evidential unless dataset documentation says otherwise.",
            )
        )
    return output


def audit_missing_inputs(dataset_dir: Path) -> list[Dict[str, str]]:
    output: list[Dict[str, str]] = []
    if not (dataset_dir / "gold_labels.jsonl").exists():
        output.append(issue("gold_verdict_consistency", "P1", "", "", "gold_labels.jsonl", "runbook listed gold_labels.jsonl, but this dataset version stores verdicts in latent_tasks.jsonl"))
    return output


def run_data_sanity(*, dataset_dir: Path, pilot_run_dir: Path, out_dir: Path) -> Dict[str, Any]:
    tasks = read_jsonl(dataset_dir / "tasks.jsonl")
    latent_tasks = read_jsonl(dataset_dir / "latent_tasks.jsonl")
    gold_documents = read_jsonl(dataset_dir / "gold_documents.jsonl")
    action_gold = read_jsonl(dataset_dir / "action_gold.jsonl")
    dependency_edges = read_jsonl(dataset_dir / "dependency_edges.jsonl")
    docs_by_view = {
        "neutral_metadata_visible": read_jsonl(dataset_dir / "documents_neutral_metadata_visible.jsonl"),
        "neutral_metadata_hidden": read_jsonl(dataset_dir / "documents_neutral_metadata_hidden.jsonl"),
    }
    docs_by_key = doc_ids_by_task_view(docs_by_view)
    rows: list[Dict[str, str]] = []
    rows.extend(audit_missing_inputs(dataset_dir))
    rows.extend(audit_doc_id_consistency(dataset_dir=dataset_dir, pilot_run_dir=pilot_run_dir, docs_by_key=docs_by_key))
    rows.extend(audit_dependency_edges(dependency_edges, docs_by_key))
    rows.extend(audit_gold_and_pollutants(latent_tasks, gold_documents))
    rows.extend(audit_views(docs_by_view, gold_documents))
    rows.extend(audit_action_gold(action_gold, docs_by_key))
    rows.extend(audit_chronology(tasks, docs_by_view))
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "data_sanity_audit_rows.csv", rows)
    counts = Counter(row["severity"] for row in rows)
    summary = {
        "issue_count": len(rows),
        "severity_counts": dict(sorted(counts.items())),
        "p0_count": counts.get("P0", 0),
        "p1_count": counts.get("P1", 0),
        "p2_count": counts.get("P2", 0),
        "decision": "block_paper_claims" if counts.get("P0", 0) else "pass_with_qualifications" if rows else "pass",
        "heuristic_false_positive_categories": [
            "synthetic timestamp chronology warnings",
            "missing gold_labels.jsonl when latent_tasks.jsonl is the authoritative local contract",
        ],
    }
    write_json(out_dir / "data_sanity_audit_summary.json", summary)
    return summary


@app.command()
def main(
    dataset_dir: Path = typer.Option(DEFAULT_DATASET_DIR, help="Role-uncued dataset directory."),
    pilot_run_dir: Path = typer.Option(DEFAULT_PILOT_RUN_DIR, help="Phase 1 pilot result directory."),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Immutable output directory."),
) -> None:
    summary = run_data_sanity(dataset_dir=dataset_dir, pilot_run_dir=pilot_run_dir, out_dir=out_dir)
    console.print(f"Data sanity audit complete: decision={summary['decision']} issues={summary['issue_count']}.")
