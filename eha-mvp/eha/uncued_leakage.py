from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import typer
from rich.console import Console

from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_contract import (
    DEFAULT_REPORT_DATE,
    DEFAULT_VIEWS,
    HIDDEN_FIELD_NAMES,
    direct_answer_regexes,
    forbidden_role_regexes,
    semantic_id_regex,
    split_csv,
)
from .uncued_generate import load_uncued_dataset


app = typer.Typer(add_completion=False, help="Audit role-uncued datasets for visible leakage.")
console = Console()

VISIBLE_TASK_KEYS = ("task_id", "question")
VISIBLE_DOC_KEYS = ("task_id", "doc_id", "title", "source_type", "timestamp", "body", "visible_citations")


def excerpt(text: str, pattern: str) -> str:
    lowered = text.lower()
    idx = lowered.find(pattern.lower().strip("\\b"))
    if idx < 0:
        return text[:120]
    start = max(0, idx - 45)
    end = min(len(text), idx + len(pattern) + 75)
    return text[start:end].replace("\n", " ")


def row_text(row: Mapping[str, Any], keys: Iterable[str]) -> str:
    parts: list[str] = []
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    return "\n".join(parts)


def visible_hidden_field_hits(row: Mapping[str, Any]) -> list[str]:
    return sorted(key for key in row if key in HIDDEN_FIELD_NAMES)


def severity_for_forbidden_phrase(phrase: str) -> str:
    if phrase in {"primary", "secondary", "contaminant", "pollutant", "generated lore", "no primary evidence", "insufficient evidence"}:
        return "high"
    return "medium"


def audit_visible_rows(dataset: Mapping[str, Any], views: Sequence[str]) -> list[Dict[str, Any]]:
    hits: list[Dict[str, Any]] = []
    semantic_re = semantic_id_regex()
    forbidden_regexes = forbidden_role_regexes()
    direct_regexes = direct_answer_regexes()

    for task in dataset["tasks"]:
        task_text = row_text(task, VISIBLE_TASK_KEYS)
        hidden = visible_hidden_field_hits(task)
        for key in hidden:
            hits.append({"view": "tasks", "task_id": task.get("task_id", ""), "doc_id": "", "surface": key, "severity": "critical", "category": "hidden_field", "pattern": key, "excerpt": key})
        for pattern, regex in direct_regexes:
            if regex.search(task_text):
                hits.append({"view": "tasks", "task_id": task.get("task_id", ""), "doc_id": "", "surface": "question", "severity": "critical", "category": "direct_answer_cue", "pattern": pattern, "excerpt": excerpt(task_text, pattern)})
    for view in views:
        for doc in dataset["documents_by_view"].get(view, []):
            task_id = str(doc.get("task_id", ""))
            doc_id = str(doc.get("doc_id", ""))
            hidden = visible_hidden_field_hits(doc)
            for key in hidden:
                hits.append({"view": view, "task_id": task_id, "doc_id": doc_id, "surface": key, "severity": "critical", "category": "hidden_field", "pattern": key, "excerpt": key})
            for identifier in [doc_id, *[str(item) for item in doc.get("visible_citations", [])]]:
                if semantic_re.search(identifier):
                    hits.append({"view": view, "task_id": task_id, "doc_id": doc_id, "surface": "doc_id_or_citation", "severity": "critical", "category": "semantic_id", "pattern": semantic_re.search(identifier).group(0), "excerpt": identifier})
            text = row_text(doc, VISIBLE_DOC_KEYS)
            for phrase, regex in forbidden_regexes:
                if regex.search(text):
                    hits.append({"view": view, "task_id": task_id, "doc_id": doc_id, "surface": "visible_document", "severity": severity_for_forbidden_phrase(phrase), "category": "material_role_phrase", "pattern": phrase, "excerpt": excerpt(text, phrase)})
            for pattern, regex in direct_regexes:
                if regex.search(text):
                    hits.append({"view": view, "task_id": task_id, "doc_id": doc_id, "surface": "visible_document", "severity": "critical", "category": "direct_answer_cue", "pattern": pattern, "excerpt": excerpt(text, pattern)})
    return hits


def leakage_summary(hits: Sequence[Mapping[str, Any]], *, dataset_dir: Path, views: Sequence[str]) -> Dict[str, Any]:
    by_severity = Counter(str(hit["severity"]) for hit in hits)
    by_category = Counter(str(hit["category"]) for hit in hits)
    hidden_label_hits = by_category.get("hidden_field", 0)
    semantic_id_hits = by_category.get("semantic_id", 0)
    direct_answer_cue_hits = by_category.get("direct_answer_cue", 0)
    critical_hits = by_severity.get("critical", 0)
    high_hits = by_severity.get("high", 0)
    passed = critical_hits == 0 and high_hits == 0 and hidden_label_hits == 0 and semantic_id_hits == 0 and direct_answer_cue_hits == 0
    return {
        "dataset_dir": str(dataset_dir),
        "views": list(views),
        "total_hits": len(hits),
        "critical_hits": critical_hits,
        "high_hits": high_hits,
        "medium_hits": by_severity.get("medium", 0),
        "low_hits": by_severity.get("low", 0),
        "hidden_label_hits": hidden_label_hits,
        "semantic_id_hits": semantic_id_hits,
        "direct_answer_cue_hits": direct_answer_cue_hits,
        "hits_by_category": dict(sorted(by_category.items())),
        "hits_by_severity": dict(sorted(by_severity.items())),
        "passed": passed,
    }


def write_leakage_report(out_dir: Path, summary: Mapping[str, Any], hits: Sequence[Mapping[str, Any]], *, report_date: str = DEFAULT_REPORT_DATE) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_uncued_leakage_micro.json", {**summary, "hits": list(hits)})
    write_csv(out_dir / "uncued_leakage_micro_rows.csv", hits)
    lines = [
        "# EHA-Uncued Micro Leakage Audit",
        "",
        f"Date: {report_date}",
        "",
        "## Gate Summary",
        "",
        *markdown_table(
            [
                {
                    "passed": summary["passed"],
                    "critical_hits": summary["critical_hits"],
                    "high_hits": summary["high_hits"],
                    "hidden_label_hits": summary["hidden_label_hits"],
                    "semantic_id_hits": summary["semantic_id_hits"],
                    "direct_answer_cue_hits": summary["direct_answer_cue_hits"],
                }
            ],
            ["passed", "critical_hits", "high_hits", "hidden_label_hits", "semantic_id_hits", "direct_answer_cue_hits"],
        ),
        "",
        "## Hit Rows",
        "",
    ]
    lines.extend(markdown_table(hits[:20], ["view", "task_id", "doc_id", "severity", "category", "pattern"]))
    lines.append("")
    (out_dir / f"eha-uncued-leakage-micro-{report_date}.md").write_text("\n".join(lines), encoding="utf-8")


def run_leakage_audit(dataset_dir: Path, out_dir: Path, views: Sequence[str]) -> Dict[str, Any]:
    dataset = load_uncued_dataset(dataset_dir)
    hits = audit_visible_rows(dataset, views)
    summary = leakage_summary(hits, dataset_dir=dataset_dir, views=views)
    write_leakage_report(out_dir, summary, hits)
    return {**summary, "hits": hits}


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-micro"), help="Dataset directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Report output directory."),
    views: str = typer.Option(",".join(DEFAULT_VIEWS), help="Comma-separated views."),
) -> None:
    selected_views = split_csv(views)
    summary = run_leakage_audit(dataset_dir, out_dir, selected_views)
    console.print(f"Leakage audit passed={summary['passed']} critical={summary['critical_hits']} high={summary['high_hits']}.")

