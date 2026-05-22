from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import typer
from rich.console import Console

from .schemas import write_json


app = typer.Typer(add_completion=False, help="Write and inspect the EHA-Uncued data contract.")
console = Console()

DEFAULT_REPORT_DATE = "2026-05-22"
DEFAULT_VIEWS = ("neutral_metadata_visible", "neutral_metadata_hidden")

HIDDEN_FIELD_NAMES = {
    "role",
    "hidden_role",
    "gold_role",
    "gold_verdict",
    "condition",
    "known_contaminants",
    "contamination",
    "supports_gold_verdict",
    "semantic_id",
    "internal_doc_id",
    "upstream_root",
}

SEMANTIC_ID_TERMS = {
    "primary",
    "secondary",
    "contaminant",
    "pollutant",
    "generated",
    "lore",
    "stale",
    "repost",
    "root",
    "gold",
    "support",
    "refute",
    "clean",
}

FORBIDDEN_ROLE_PHRASES = (
    "primary",
    "secondary",
    "contaminant",
    "pollutant",
    "generated lore",
    "wiki-style",
    "authoritative-looking",
    "copied from the same upstream story",
    "raw records",
    "signed record",
    "reviewer sign-off",
    "does not settle",
    "no primary evidence",
    "not independent",
    "repeats the same claim",
    "background material",
    "orientation material",
    "insufficient evidence",
)

DIRECT_ANSWER_CUE_PATTERNS = (
    r"\bthe answer is\b",
    r"\bcorrect answer\b",
    r"\bgold verdict\b",
    r"\bverdict\s*:",
    r"\bshould answer\b",
    r"\bmust answer\b",
    r"\btherefore\s+(supported|refuted|insufficient)\b",
    r"\bclaim\s+is\s+(supported|refuted|insufficient|true|false)\b",
)

ALLOWED_RELATIONAL_EVIDENCE = (
    "timestamps",
    "citations among visible documents",
    "numeric disagreements",
    "named-entity disagreements",
    "version references that do not label document roles",
    "same-source repetition that is observable from citations rather than role words",
)

ALLOWED_METADATA_BY_VIEW: Dict[str, Sequence[str]] = {
    "neutral_metadata_visible": ("doc_id", "title", "source_type", "timestamp", "visible_citations"),
    "neutral_metadata_hidden": ("doc_id", "title", "source_type", "timestamp", "visible_citations"),
}

BASELINE_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "id_only": {"operational_epistemic_escape_max": 0.10, "verdict_accuracy_max": 0.40},
    "document_order_only": {"operational_epistemic_escape_max": 0.15, "verdict_accuracy_max": 0.45},
    "title_only": {"operational_epistemic_escape_max": 0.25, "role_reconstruction_accuracy_max": 0.45},
    "source_type_only:hidden": {"operational_epistemic_escape_max": 0.10},
    "source_type_only:visible": {"operational_epistemic_escape_max": 0.25},
    "metadata_only:hidden": {"operational_epistemic_escape_max": 0.20},
    "metadata_only:visible": {"operational_epistemic_escape_max": 0.35},
    "timestamp_only": {"verdict_accuracy_max": 0.55},
    "citation_graph_only": {"operational_epistemic_escape_max": 0.35, "verdict_accuracy_max": 0.60},
    "claim_overlap_only": {"operational_epistemic_escape_max": 0.35, "polluted_support_rate_max": 0.60},
    "cue_phrase_only": {"operational_epistemic_escape_max": 0.10},
    "always_insufficient": {"operational_epistemic_escape_max": 0.30},
}


def split_csv(value: str | Sequence[str]) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def normalized_view_kind(view: str) -> str:
    return "hidden" if "hidden" in view else "visible"


def contract_payload() -> Dict[str, Any]:
    return {
        "name": "EHA-Uncued data contract",
        "date": DEFAULT_REPORT_DATE,
        "preferred_term": "role_uncued",
        "avoid_as_main_term": "content_neutral",
        "levels": {
            "L0_hidden_label_leakage": "model-visible JSON must not expose hidden role or gold fields",
            "L1_semantic_id_leakage": "visible IDs and citations must not encode evidence roles or gold semantics",
            "L2_material_role_phrase_leakage": "visible title/body/source metadata must not state material evidence roles",
            "L3_conclusion_cue_leakage": "visible task text must not state the target answer or verdict",
            "L4_allowed_relational_evidence": list(ALLOWED_RELATIONAL_EVIDENCE),
        },
        "hidden_field_names": sorted(HIDDEN_FIELD_NAMES),
        "semantic_id_terms": sorted(SEMANTIC_ID_TERMS),
        "forbidden_role_phrases": list(FORBIDDEN_ROLE_PHRASES),
        "direct_answer_cue_patterns": list(DIRECT_ANSWER_CUE_PATTERNS),
        "allowed_metadata_by_view": {key: list(value) for key, value in ALLOWED_METADATA_BY_VIEW.items()},
        "baseline_thresholds": BASELINE_THRESHOLDS,
        "human_review_rubric": {
            "critical": "reviewer can answer the task or identify gold role from wording alone",
            "high": "visible text directly states source independence, insufficiency, or material role",
            "medium": "realistic metadata cue that is strong enough to require balance review",
            "low": "weak cue allowed only if balanced across roles and conditions",
        },
        "model_call_go_no_go_rule": (
            "Do not call frontier models until leakage, shortcut baseline, and surface-review gates pass "
            "with zero critical/high leakage and zero direct-answer cue rows."
        ),
    }


def forbidden_role_regexes() -> list[tuple[str, re.Pattern[str]]]:
    return [
        (phrase, re.compile(r"(?<![a-z0-9])" + re.escape(phrase).replace(r"\ ", r"\s+") + r"(?![a-z0-9])", re.IGNORECASE))
        for phrase in FORBIDDEN_ROLE_PHRASES
    ]


def direct_answer_regexes() -> list[tuple[str, re.Pattern[str]]]:
    return [(pattern, re.compile(pattern, re.IGNORECASE)) for pattern in DIRECT_ANSWER_CUE_PATTERNS]


def semantic_id_regex() -> re.Pattern[str]:
    return re.compile(r"(" + "|".join(re.escape(term) for term in sorted(SEMANTIC_ID_TERMS, key=len, reverse=True)) + r")", re.IGNORECASE)


def visible_text_from_mapping(row: Mapping[str, Any], keys: Iterable[str]) -> str:
    parts: list[str] = []
    for key in keys:
        value = row.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif value is not None:
            parts.append(str(value))
    return "\n".join(parts)


def write_contract_report(out_dir: Path, *, report_date: str = DEFAULT_REPORT_DATE) -> Dict[str, Any]:
    payload = contract_payload()
    payload["date"] = report_date
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_uncued_data_contract.json", payload)

    lines = [
        "# EHA-Uncued Data Contract",
        "",
        f"Date: {report_date}",
        "",
        "This contract makes `role_uncued` executable. The dataset may contain task-relevant content, but model-visible surfaces must not explicitly label evidence roles, hidden verdicts, contamination labels, or semantic document IDs.",
        "",
        "## Leakage Levels",
        "",
        "- L0 hidden-label leakage: hidden role and gold fields are forbidden in model-visible JSON.",
        "- L1 semantic ID leakage: visible IDs and citations must not encode evidence roles.",
        "- L2 material-role phrase leakage: visible text must not state material evidence roles.",
        "- L3 conclusion cue leakage: visible text must not state the answer or verdict.",
        "- L4 allowed relational evidence: timestamps, citations, contradictions, and numeric disagreements are allowed when they do not label roles.",
        "",
        "## Machine-Readable Contract",
        "",
        "```json",
        json.dumps(payload, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Go/No-Go Rule",
        "",
        payload["model_call_go_no_go_rule"],
        "",
    ]
    report_path = out_dir / f"eha-uncued-data-contract-{report_date}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "uncued_data_contract.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


@app.command("write")
def write(
    out_dir: Path = typer.Option(Path("../reports"), help="Directory for the contract report."),
    report_date: str = typer.Option(DEFAULT_REPORT_DATE, help="Report date stamp."),
) -> None:
    payload = write_contract_report(out_dir, report_date=report_date)
    console.print(f"Wrote EHA-Uncued data contract with {len(payload['forbidden_role_phrases'])} forbidden role phrase families.")

