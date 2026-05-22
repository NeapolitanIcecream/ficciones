from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from random import Random
from typing import Any, Dict, Iterable, Mapping, Sequence

import typer
from rich.console import Console

from .schemas import write_json, write_jsonl
from .uncued_contract import DEFAULT_REPORT_DATE, DEFAULT_VIEWS, split_csv, write_contract_report


app = typer.Typer(add_completion=False, help="Generate role-uncued EHA micro and pilot datasets.")
console = Console()

CONDITIONS = ("clean", "conflicting_evidence", "false_consensus", "buried_primary", "generated_lore")
FAMILIES = ("packet_judgment", "evidence_selection", "active_verification")
GOLD_VERDICTS = ("supported", "refuted", "insufficient")

MICRO_CONDITION_COUNTS = {
    "clean": 2,
    "conflicting_evidence": 2,
    "false_consensus": 2,
    "buried_primary": 2,
    "generated_lore": 2,
}

MICRO_FAMILY_SEQUENCE = (
    "packet_judgment",
    "packet_judgment",
    "packet_judgment",
    "packet_judgment",
    "evidence_selection",
    "evidence_selection",
    "evidence_selection",
    "evidence_selection",
    "active_verification",
    "active_verification",
)

PILOT_CONDITION_COUNTS = {condition: 12 for condition in CONDITIONS}
PILOT_FAMILY_COUNTS = {
    "packet_judgment": 24,
    "evidence_selection": 24,
    "active_verification": 12,
}

PILOT_FAMILY_BY_CONDITION = {
    "clean": ("packet_judgment",) * 5 + ("evidence_selection",) * 5 + ("active_verification",) * 2,
    "conflicting_evidence": ("packet_judgment",) * 5 + ("evidence_selection",) * 5 + ("active_verification",) * 2,
    "false_consensus": ("packet_judgment",) * 5 + ("evidence_selection",) * 5 + ("active_verification",) * 2,
    "buried_primary": ("packet_judgment",) * 5 + ("evidence_selection",) * 5 + ("active_verification",) * 2,
    "generated_lore": ("packet_judgment",) * 4 + ("evidence_selection",) * 4 + ("active_verification",) * 4,
}

SOURCE_TYPES = ("field note", "registry entry", "operations memo", "timeline note")
VISIBLE_TITLES = (
    "Service Ledger Extract",
    "Operations Timeline Note",
    "Program Registry Entry",
    "Field Summary Memo",
)

THEMES = (
    {
        "subject": "Atlas valve checks",
        "metric": "completed checks",
        "true_value": "184",
        "false_value": "211",
        "period": "March 2025",
        "program": "HelioSplice partner repair program",
        "place": "Northline service bay",
    },
    {
        "subject": "Orion battery swaps",
        "metric": "verified swaps",
        "true_value": "63",
        "false_value": "88",
        "period": "April 2025",
        "program": "AuroraDock field upgrade toolkit",
        "place": "East Yard depot",
    },
    {
        "subject": "Mira sensor recalibrations",
        "metric": "closed tickets",
        "true_value": "97",
        "false_value": "124",
        "period": "May 2025",
        "program": "Meridian Shield recall board",
        "place": "Westhaven lab",
    },
    {
        "subject": "Vega rail inspections",
        "metric": "accepted inspections",
        "true_value": "42",
        "false_value": "57",
        "period": "June 2025",
        "program": "Cobalt Loop service exchange",
        "place": "South Gate workshop",
    },
    {
        "subject": "Nova pump refurbishments",
        "metric": "completed refurbishments",
        "true_value": "118",
        "false_value": "139",
        "period": "July 2025",
        "program": "LumenBridge partner desk",
        "place": "Harbor Annex",
    },
    {
        "subject": "Kestrel firmware checks",
        "metric": "approved checks",
        "true_value": "76",
        "false_value": "101",
        "period": "August 2025",
        "program": "SolaceGrid repair exchange",
        "place": "Ridgeway bench",
    },
)


def stable_hash_text(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path.name).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def view_suffix(view: str) -> str:
    return "hidden" if "hidden" in view else "visible"


def visible_doc_ids(task_id: str, count: int, rng: Random) -> list[str]:
    ids = [f"{task_id}_d{index:02d}" for index in range(1, count + 1)]
    rng.shuffle(ids)
    return ids


def condition_plan(phase: str, task_count: int) -> list[str]:
    if phase == "micro":
        counts = MICRO_CONDITION_COUNTS
    elif phase == "pilot":
        counts = PILOT_CONDITION_COUNTS
    else:
        raise ValueError(f"unknown uncued dataset phase: {phase}")
    planned = [condition for condition in CONDITIONS for _ in range(counts[condition])]
    if len(planned) != task_count:
        raise ValueError(f"{phase} requires task_count={len(planned)}, got {task_count}")
    return planned


def family_plan(phase: str, task_count: int, conditions: Sequence[str] | None = None) -> list[str]:
    if phase == "micro":
        planned = list(MICRO_FAMILY_SEQUENCE)
    elif phase == "pilot":
        if conditions is None:
            raise ValueError("pilot family plan requires conditions")
        remaining_by_condition = {condition: list(PILOT_FAMILY_BY_CONDITION[condition]) for condition in CONDITIONS}
        planned = []
        for condition in conditions:
            try:
                planned.append(remaining_by_condition[condition].pop(0))
            except IndexError as exc:
                raise ValueError(f"too many pilot tasks for condition: {condition}") from exc
        leftovers = {condition: families for condition, families in remaining_by_condition.items() if families}
        if leftovers:
            raise ValueError(f"pilot family plan left unused family slots: {leftovers}")
    else:
        raise ValueError(f"unknown uncued dataset phase: {phase}")
    if len(planned) != task_count:
        raise ValueError(f"{phase} requires task_count={len(planned)}, got {task_count}")
    return planned


def selected_theme(index: int) -> Mapping[str, str]:
    return THEMES[index % len(THEMES)]


def claim_question(theme: Mapping[str, str], condition: str, index: int) -> tuple[str, str, str]:
    if condition == "clean":
        verdict = "supported" if index % 2 == 0 else "refuted"
        value = theme["true_value"] if verdict == "supported" else theme["false_value"]
        question = f"Did Novalis Robotics log {value} {theme['metric']} for {theme['subject']} in {theme['period']}?"
    elif condition in {"conflicting_evidence", "false_consensus"}:
        verdict = "refuted"
        question = f"Did Novalis Robotics log {theme['false_value']} {theme['metric']} for {theme['subject']} in {theme['period']}?"
    elif condition == "buried_primary":
        verdict = "supported"
        question = f"Did Novalis Robotics log {theme['true_value']} {theme['metric']} for {theme['subject']} in {theme['period']}?"
    elif condition == "generated_lore":
        verdict = "insufficient"
        question = f"Did Novalis Robotics launch the {theme['program']} in {theme['period']}?"
    else:
        raise ValueError(f"unknown condition: {condition}")
    target_claim = f"novalis_{theme['subject'].lower().replace(' ', '_')}_{theme['period'].lower().replace(' ', '_')}"
    return question, verdict, target_claim


def padded_body(*sentences: str) -> str:
    body = " ".join(sentence.strip() for sentence in sentences if sentence.strip())
    if len(body.split()) < 45:
        body += " The note uses the same site code, workstream name, and monthly close date as the surrounding packet so that relation checks depend on the stated values rather than labels."
    return body


def latent_documents_for_condition(theme: Mapping[str, str], condition: str, verdict: str, index: int) -> list[Dict[str, Any]]:
    period = theme["period"]
    subject = theme["subject"]
    metric = theme["metric"]
    true_value = theme["true_value"]
    false_value = theme["false_value"]
    place = theme["place"]
    program = theme["program"]

    if condition == "clean":
        if verdict == "supported":
            docs = [
                ("clean_anchor", True, [], padded_body(f"The monthly ledger for {place} lists {true_value} {metric} for {subject} in {period}.", "The entry is dated after the close of the month and uses the same work order code as the question.")),
                ("context", False, [], padded_body(f"A planning note for {subject} describes the inspection route at {place} during {period}.", "It gives staffing context and does not include a final monthly count.")),
                ("context", False, [], padded_body(f"A shift memo mentions that {subject} work was concentrated in the final week of {period}.", "It tracks handoff timing but not the final tally.")),
                ("context", False, [], padded_body(f"A routing note lists {place} as the site for the {subject} workstream.", "The note does not provide a closing count.")),
            ]
        else:
            docs = [
                ("clean_anchor", True, [], padded_body(f"The monthly ledger for {place} lists {true_value} {metric} for {subject} in {period}.", f"No line in the packet lists {false_value} for this workstream.")),
                ("context", False, [], padded_body(f"A staffing note for {subject} names the same site and month.", "It does not report the closing count.")),
                ("context", False, [], padded_body(f"A routing note gives the work order code for {subject}.", "It omits the final count.")),
                ("context", False, [], padded_body(f"A brief memo says the closeout was filed after the last weekend of {period}.", "It does not state a number.")),
            ]
    elif condition == "conflicting_evidence":
        docs = [
            ("clean_anchor", True, [], padded_body(f"The month-close ledger for {place} lists {true_value} {metric} for {subject} in {period}.", f"The row uses the same workstream name as the claim but a different count from {false_value}.")),
            ("conflict_leaf", False, ["false_value"], padded_body(f"A short operations digest says the {subject} count reached {false_value} in {period}.", "The digest cites no visible row beyond the packet references.")),
            ("context", False, [], padded_body(f"A routing note for {place} records when the {subject} packet was assembled.", "It gives chronology but not the final count.")),
            ("context", False, [], padded_body(f"A scheduling memo says the {subject} closeout was delayed by one day.", "It contains no total.")),
        ]
    elif condition == "false_consensus":
        docs = [
            ("clean_anchor", True, [], padded_body(f"The closing ledger for {place} gives {true_value} {metric} for {subject} in {period}.", f"The ledger row is the only visible row with a final count different from {false_value}.")),
            ("same_root_echo", False, ["false_value"], padded_body(f"A weekly digest repeats that {subject} reached {false_value} {metric} in {period}.", "The digest points to the same earlier bulletin used by another note in the packet.")),
            ("same_root_echo", False, ["false_value"], padded_body(f"A partner summary also gives {false_value} for {subject} in {period}.", "Its visible citation points back to the weekly digest rather than to a separate count sheet.")),
            ("context", False, [], padded_body(f"A site memo for {place} lists the workstream and month.", "It does not contain a final count.")),
        ]
    elif condition == "buried_primary":
        docs = [
            ("context", False, [], padded_body(f"A planning memo for {subject} describes the expected workload at {place}.", "It was prepared before the monthly close and has no final number.")),
            ("same_root_echo", False, ["false_value"], padded_body(f"A digest estimates {false_value} {metric} for {subject} in {period}.", "The note is framed as a running estimate and points to the planning memo.")),
            ("context", False, [], padded_body(f"A handoff note names the workstream and site for {period}.", "It contains no closing count.")),
            ("clean_anchor", True, [], padded_body(f"The closeout ledger lists {true_value} {metric} for {subject} in {period}.", "The row appears after the planning notes and uses the final close date.")),
        ]
    elif condition == "generated_lore":
        docs = [
            ("unsupported_story", False, ["unsupported"], padded_body(f"A community roundup says the {program} appeared during {period}.", "The item gives a program name and month but no linked operational record.")),
            ("same_root_echo", False, ["unsupported"], padded_body(f"A partner recap repeats the {program} launch wording from the roundup.", "Its visible citation points to the roundup item.")),
            ("context", False, [], padded_body(f"A service planning memo for {place} lists routine {subject} work in {period}.", f"It does not mention the {program}.")),
            ("context", False, [], padded_body(f"A monthly index names the {subject} workstream and site.", "It lists regular service categories but no program launch entry.")),
        ]
    else:
        raise ValueError(f"unknown condition: {condition}")

    rows: list[Dict[str, Any]] = []
    for doc_index, (role, supports_gold, contamination, body) in enumerate(docs, start=1):
        rows.append(
            {
                "internal_doc_id": f"latent_{index:03d}_{role}_{doc_index:02d}",
                "hidden_role": role,
                "supports_gold_verdict": supports_gold,
                "contamination": contamination,
                "timestamp": f"2025-{(index % 9) + 1:02d}-{12 + doc_index:02d}",
                "body": body,
                "source_type_index": doc_index - 1,
            }
        )
    return rows


def remap_documents(
    *,
    task_id: str,
    latent_docs: Sequence[Mapping[str, Any]],
    view: str,
    rng: Random,
) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]], Dict[str, str]]:
    visible_ids = visible_doc_ids(task_id, len(latent_docs), rng)
    internal_to_visible = {str(doc["internal_doc_id"]): visible_id for doc, visible_id in zip(latent_docs, visible_ids)}
    order = list(latent_docs)
    rng.shuffle(order)
    docs: list[Dict[str, Any]] = []
    gold_docs: list[Dict[str, Any]] = []
    for position, doc in enumerate(order, start=1):
        visible_id = internal_to_visible[str(doc["internal_doc_id"])]
        citations: list[str] = []
        role = str(doc["hidden_role"])
        if role == "same_root_echo":
            target = next((item for item in latent_docs if item["hidden_role"] in {"same_root_echo", "unsupported_story", "context"} and item["internal_doc_id"] != doc["internal_doc_id"]), None)
            if target is not None:
                citations.append(internal_to_visible[str(target["internal_doc_id"])])
        elif role == "conflict_leaf":
            target = next((item for item in latent_docs if item["hidden_role"] == "context"), None)
            if target is not None:
                citations.append(internal_to_visible[str(target["internal_doc_id"])])

        if "hidden" in view:
            title = f"Document {position}"
            source_type = "document"
        else:
            title = VISIBLE_TITLES[(position - 1) % len(VISIBLE_TITLES)]
            source_type = SOURCE_TYPES[int(doc["source_type_index"]) % len(SOURCE_TYPES)]

        docs.append(
            {
                "task_id": task_id,
                "doc_id": visible_id,
                "title": title,
                "source_type": source_type,
                "timestamp": str(doc["timestamp"]),
                "body": str(doc["body"]),
                "visible_citations": citations,
            }
        )
        gold_docs.append(
            {
                "task_id": task_id,
                "doc_id": visible_id,
                "internal_doc_id": doc["internal_doc_id"],
                "hidden_role": doc["hidden_role"],
                "supports_gold_verdict": bool(doc["supports_gold_verdict"]),
                "contamination": list(doc["contamination"]),
                "timestamp": str(doc["timestamp"]),
                "view": view,
            }
        )
    return docs, gold_docs, internal_to_visible


def build_uncued_dataset(
    *,
    phase: str,
    task_count: int,
    views: Sequence[str],
    seed: int,
) -> Dict[str, Any]:
    conditions = condition_plan(phase, task_count)
    families = family_plan(phase, task_count, conditions)
    rng = Random(seed)

    tasks: list[Dict[str, Any]] = []
    latent_tasks: list[Dict[str, Any]] = []
    all_gold_docs: list[Dict[str, Any]] = []
    edges: list[Dict[str, Any]] = []
    action_gold: list[Dict[str, Any]] = []
    docs_by_view: Dict[str, list[Dict[str, Any]]] = {view: [] for view in views}

    for index, (condition, family) in enumerate(zip(conditions, families)):
        theme = selected_theme(index)
        task_id = f"uncued_{index:03d}"
        question, verdict, target_claim_id = claim_question(theme, condition, index)
        latent_docs = latent_documents_for_condition(theme, condition, verdict, index)
        task = {
            "task_id": task_id,
            "question": question,
            "max_selected_docs": 3,
            "max_actions": 2,
        }
        tasks.append(task)

        per_view_gold: Dict[str, list[Dict[str, Any]]] = {}
        for view_index, view in enumerate(views):
            view_rng = Random(rng.randrange(1_000_000_000) + view_index)
            docs, gold_docs, _mapping = remap_documents(task_id=task_id, latent_docs=latent_docs, view=view, rng=view_rng)
            docs_by_view[view].extend(docs)
            all_gold_docs.extend(gold_docs)
            per_view_gold[view] = gold_docs
            for doc in docs:
                for citation in doc["visible_citations"]:
                    edges.append({"task_id": task_id, "view": view, "from": doc["doc_id"], "to": citation, "relation": "visible_citation"})

        primary_by_view = {
            view: [gold["doc_id"] for gold in rows if gold["supports_gold_verdict"]]
            for view, rows in per_view_gold.items()
        }
        polluted_by_view = {
            view: [gold["doc_id"] for gold in rows if gold["contamination"]]
            for view, rows in per_view_gold.items()
        }
        required_actions = []
        if family == "active_verification":
            if verdict != "insufficient":
                required_actions.append("open_best_visible_record")
            if condition in {"conflicting_evidence", "false_consensus", "buried_primary"}:
                required_actions.append("compare_visible_counts")
            if condition == "generated_lore":
                required_actions.append("trace_visible_citation")
            action_gold.append(
                {
                    "task_id": task_id,
                    "required_action_types": required_actions,
                    "required_target_doc_ids_by_view": {
                        view: (primary_by_view[view] or polluted_by_view[view])[:2] for view in views
                    },
                    "machine_executable_target_required": True,
                }
            )

        latent_tasks.append(
            {
                "task_id": task_id,
                "family": family,
                "condition": condition,
                "target_claim_id": target_claim_id,
                "question": question,
                "gold_verdict": verdict,
                "gold_support_doc_ids_by_view": primary_by_view,
                "known_polluted_doc_ids_by_view": polluted_by_view,
                "action_gold_required": family == "active_verification",
            }
        )

    manifest = {
        "name": f"EHA-Uncued {phase}",
        "phase": phase,
        "seed": seed,
        "task_count": task_count,
        "views": list(views),
        "condition_counts": dict(Counter(item["condition"] for item in latent_tasks)),
        "family_counts": dict(Counter(item["family"] for item in latent_tasks)),
        "role_uncued": True,
        "model_visible_files": ["tasks.jsonl", *[f"documents_{view}.jsonl" for view in views]],
        "gold_files": ["latent_tasks.jsonl", "gold_documents.jsonl", "dependency_edges.jsonl", "action_gold.jsonl"],
    }
    return {
        "manifest": manifest,
        "tasks": tasks,
        "latent_tasks": latent_tasks,
        "documents_by_view": docs_by_view,
        "gold_documents": all_gold_docs,
        "dependency_edges": edges,
        "action_gold": action_gold,
    }


def write_uncued_dataset(out_dir: Path, dataset: Mapping[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "manifest.json", dataset["manifest"])
    write_jsonl(out_dir / "tasks.jsonl", dataset["tasks"])
    write_jsonl(out_dir / "latent_tasks.jsonl", dataset["latent_tasks"])
    write_jsonl(out_dir / "gold_documents.jsonl", dataset["gold_documents"])
    write_jsonl(out_dir / "dependency_edges.jsonl", dataset["dependency_edges"])
    write_jsonl(out_dir / "action_gold.jsonl", dataset["action_gold"])
    for view, docs in dataset["documents_by_view"].items():
        write_jsonl(out_dir / f"documents_{view}.jsonl", docs)


def load_uncued_dataset(dataset_dir: Path) -> Dict[str, Any]:
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    rows = {
        "manifest": manifest,
        "tasks": [json.loads(line) for line in (dataset_dir / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()],
        "latent_tasks": [json.loads(line) for line in (dataset_dir / "latent_tasks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()],
        "gold_documents": [json.loads(line) for line in (dataset_dir / "gold_documents.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()],
        "dependency_edges": [json.loads(line) for line in (dataset_dir / "dependency_edges.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()],
        "action_gold": [json.loads(line) for line in (dataset_dir / "action_gold.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()],
        "documents_by_view": {},
    }
    for view in manifest.get("views", DEFAULT_VIEWS):
        path = dataset_dir / f"documents_{view}.jsonl"
        rows["documents_by_view"][view] = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows


@app.command()
def main(
    phase: str = typer.Argument(..., help="Dataset phase: micro or pilot."),
    out_dir: Path = typer.Option(Path("data/uncued-micro"), help="Output dataset directory."),
    task_count: int = typer.Option(10, help="Number of tasks to generate."),
    views: str = typer.Option(",".join(DEFAULT_VIEWS), help="Comma-separated views."),
    seed: int = typer.Option(9417, help="Deterministic generation seed."),
    reports_dir: Path = typer.Option(Path("../reports"), help="Directory for the data contract report."),
) -> None:
    selected_views = split_csv(views)
    write_contract_report(reports_dir, report_date=DEFAULT_REPORT_DATE)
    dataset = build_uncued_dataset(phase=phase, task_count=task_count, views=selected_views, seed=seed)
    write_uncued_dataset(out_dir, dataset)
    manifest_paths = [out_dir / "manifest.json", out_dir / "tasks.jsonl", out_dir / "latent_tasks.jsonl"]
    console.print(f"Wrote {phase} EHA-Uncued dataset with hash seed {stable_hash_text(manifest_paths)[:12]} to {out_dir}.")
