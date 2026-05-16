from __future__ import annotations

import json
import csv
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from html import escape
from pathlib import Path
from random import Random
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import typer
from rich.console import Console

from .epistemic_resilience import (
    PROMPTS,
    EpistemicAction,
    EpistemicPrediction,
    EpistemicRunRecord,
    aggregate,
    build_messages,
    normalize_prediction,
    opaque_doc_id_view,
    read_tasks,
    score_record,
    score_records,
    stable_task_seed,
)
from .report import write_csv
from .schemas import model_to_dict, read_jsonl, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Build EHA Step 1 baselines and release artifacts.")
console = Console()

BASELINE_NAMES = (
    "id_only",
    "metadata_only",
    "simple_heuristic",
    "random_valid_schema",
    "always_insufficient",
)

BASELINE_DISPLAY_NAMES = {
    "id_only": "ID-only",
    "metadata_only": "Metadata-only",
    "simple_heuristic": "Simple heuristic",
    "random_valid_schema": "Random valid schema",
    "always_insufficient": "Always insufficient",
}

BASELINE_TABLE_METRICS = (
    "operational_epistemic_escape",
    "belief_correctness",
    "evidence_cleanliness",
    "uncertainty_discipline",
    "verification_action_score",
    "support_empty_rate",
)

ACTION_AUDIT_TABLE_METRICS = (
    "n",
    "action_gate_pass",
    "missing_primary_action",
    "missing_contradiction_action",
    "missing_trace_source_action",
)

FRONTIER_TABLE_MODELS = (
    "gpt-5.4",
    "claude-opus-4-7",
    "gemini-3.1-pro-preview",
    "deepseek-v4-pro",
    "kimi-k2.6",
)

FRONTIER_TABLE_FAMILIES = (
    "packet_judgment",
    "evidence_selection",
    "active_verification",
)

FRONTIER_TABLE_CONDITIONS = (
    "clean",
    "conflicting_evidence",
    "false_consensus",
    "buried_primary",
    "generated_lore",
)

STEP1_REQUIRED_ARTIFACT_FILES = (
    "README.md",
    "manifest.json",
    "file_manifest.json",
    "data/tasks_opaque.jsonl",
    "data/documents_opaque.jsonl",
    "data/gold_labels.jsonl",
    "prompts/standard_answer.txt",
    "prompts/epistemic_hygiene_instruction.txt",
    "scorer/scoring_contract.py",
    "scorer/README.md",
    "outputs/frontier_main_opaque_predictions.jsonl",
    "outputs/frontier_main_opaque_scored.csv",
    "outputs/frontier_main_opaque_run_manifest.json",
    "outputs/frontier_main_opaque_report_manifest.json",
    "audits/opaque_prompt_audit_summary.json",
    "audits/generated_lore_schema_ablation.csv",
    "audits/generated_lore_schema_ablation_rows.csv",
    "audits/active_verification_human_audit.csv",
    "audits/active_verification_human_audit_manifest.json",
    "audits/active_verification_human_audit_readme.md",
    "audits/active_verification_human_audit_reviewer_brief.md",
    "audits/active_verification_human_audit_protocol.md",
    "audits/active_verification_human_audit_attestation.md",
    "audits/active_verification_human_audit_review.html",
    "audits/active_verification_pilot_human_audit_packet_50.md",
    "audits/active_verification_pilot_human_audit_model_blinded_packet_50.md",
    "audits/active_verification_pilot_human_audit_worksheet_50.csv",
    "audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv",
    "audits/active_verification_pilot_human_audit_validation.json",
    "audits/active_verification_pilot_human_audit_paper_update.md",
    "examples/minimal_task.json",
    "examples/minimal_model_output.json",
    "examples/minimal_score.json",
    "reproduce_minimal.sh",
    "serve_human_audit_review.sh",
    "finalize_human_audit.sh",
    "verify_step1_release.sh",
)

STEP1_REQUIRED_SCHEMA_VARIANTS = {
    "current_schema",
    "minimal_schema",
    "diagnostic_schema_no_hygiene",
    "clarified_schema",
}

STEP1_REQUIRED_HUMAN_AUDIT_CONDITIONS = {
    "clean",
    "generated_lore",
    "false_consensus",
    "buried_primary",
    "conflicting_evidence",
}

STEP1_SEMANTIC_ID_PATTERNS = {
    "eham_": re.compile(r"eham_"),
    "pollutant_root": re.compile(r"pollutant_root"),
    "primary_[ab]": re.compile(r"\bprimary_[ab]\b"),
    "repost_00_to_03": re.compile(r"\brepost_0[0-3]\b"),
}

STEP1_REQUIRED_PAPER_FILES = (
    "main.tex",
    "main.pdf",
    "sections/00_abstract.tex",
    "sections/01_intro.tex",
    "sections/02_benchmark_design.tex",
    "sections/05_generated_lore_case.tex",
    "sections/06_active_verification_case.tex",
    "sections/08_discussion.tex",
    "sections/09_limitations.tex",
    "appendix/d_extra_tables.tex",
    "appendix/e_artifacts.tex",
    "tables/main_model_decomposition.tex",
    "tables/task_family_breakdown.tex",
    "tables/evidence_condition_breakdown.tex",
    "tables/prompt_hygiene.tex",
    "tables/opaque_baselines.tex",
)

STEP1_PAPER_REQUIRED_PHRASES = {
    "controlled diagnostic benchmark": "controlled diagnostic benchmark",
    "not a universal provider leaderboard": "not as a universal provider leaderboard",
    "not human validation": "not counted as human validation",
    "deployment safety scope limit": "not to certify deployment safety",
}

STEP1_PAPER_STEP_BOUNDARY_REQUIRED_PHRASES = {
    "diagnostic release": "diagnostic release",
    "not completed scalable benchmark": "not a completed scalable benchmark",
    "larger benchmark claim": "larger benchmark claim would require",
    "larger task scale": "substantially more tasks",
    "surface-cue stress tests": "surface-cue stress tests",
    "broader schema ablations": "broader schema ablations",
    "independent human audit": "independent human audit",
}

STEP1_PAPER_ARTIFACT_APPENDIX_REQUIRED_PHRASES = {
    "review launcher": "artifact/serve_human_audit_review.sh",
    "finalization shortcut": "artifact/finalize_human_audit.sh",
    "worksheet finalization option": "--from-worksheet",
    "release verifier": "artifact/verify_step1_release.sh",
    "model-blinded audit packet": "model-blinded",
    "model-blinded worksheet": "model-blinded worksheet",
    "human-audit reviewer brief": "reviewer brief",
    "human-audit attestation": "human-audit attestation",
    "paper-update memo": "paper-update memo",
    "paper-aware readiness check": "paper-aware readiness check",
    "not human validation": "not counted as human validation",
}

STEP1_ARTIFACT_README_REQUIRED_PHRASES = {
    "controlled diagnostic package": "controlled diagnostic",
    "readiness command": "step1-readiness-check",
    "paper-aware readiness command": "--paper-dir ../paper",
    "not human validation": "not human validation",
    "human audit status label": "audit_status = human_labeled",
    "human audit row count": "n_labeled = 50",
    "auditor notes required": "auditor_notes",
    "deployment safety scope limit": "legal, medical, financial",
}

STEP1_HUMAN_AUDIT_PROTOCOL_REQUIRED_PHRASES = {
    "single-auditor pilot": "single-auditor pilot audit",
    "sample stratification": "stratified across five evidence conditions with 10 rows per condition",
    "eight binary labels": "all eight binary label fields",
    "human label status": "audit_status` to `human_labeled",
    "codex triage boundary": "Codex-assisted labels are triage evidence only",
    "not human validation by itself": "does not create human-validation evidence by itself",
    "model-blinded packet": "Model identities, prompt conditions, and automatic scorer outcomes are intentionally omitted",
    "attestation file": "active_verification_human_audit_attestation.md",
    "finalization row count": "n_complete_rows = 50",
    "auditor notes required": "no blank `auditor_notes` rows",
    "manifest completion gate": "n_labeled = 50",
}

STEP1_HUMAN_AUDIT_MODEL_BLINDED_PACKET_REQUIRED_PHRASES = {
    "model identity omitted": "Model identities and prompt conditions are intentionally omitted",
    "auto scorer omitted": "Auto scorer outcomes are intentionally omitted",
    "row-order transfer": "Use row order to transfer labels",
    "strict CSV target": "active_verification_human_audit.csv",
}

STEP1_HUMAN_AUDIT_MODEL_BLINDED_PACKET_FORBIDDEN_PHRASES = (
    "gpt-5.4",
    "claude-opus-4-7",
    "gemini-3.1-pro-preview",
    "deepseek-v4-pro",
    "kimi-k2.6",
    "standard_answer",
    "epistemic_hygiene_instruction",
    "action_gate_pass",
    "missing_primary_action",
    "missing_contradiction_action",
    "missing_trace_source_action",
)

STEP1_HUMAN_AUDIT_ATTESTATION_REQUIRED_PHRASES = {
    "auditor identifier": "auditor_identifier:",
    "date completed": "date_completed:",
    "audit surface": "audit_surface_used:",
    "independent review": "independent_human_review_completed:",
    "codex not copied": "codex_triage_not_copied_as_human_labels:",
    "all rows reviewed": "all_50_rows_reviewed:",
    "all fields and notes completed": "all_eight_binary_fields_and_auditor_notes_completed:",
    "all 50 rows statement": "The independent human review covered all 50 rows.",
    "codex boundary statement": "Codex-assisted audit was not copied as human labels.",
    "label completion statement": "All eight binary label fields and auditor_notes were completed.",
}

STEP1_HUMAN_AUDIT_ATTESTATION_SURFACES = {
    "strict_csv",
    "wide_worksheet",
    "model_blinded_worksheet",
    "html_review",
}

STEP1_HUMAN_AUDIT_ATTESTATION_PLACEHOLDER = "[TO BE COMPLETED"

STEP1_HUMAN_AUDIT_REVIEW_HTML_REQUIRED_PHRASES = {
    "download strict CSV": "Download strict CSV",
    "import strict CSV draft": "Import strict CSV draft",
    "condition filter": "condition-filter",
    "next incomplete row": "Next incomplete row",
    "completion download guard": "download.disabled",
    "strict CSV import validator": "validateImportedRows",
    "condition filter function": "applyConditionFilter",
    "strict CSV target": "active_verification_human_audit.csv",
}

STEP1_HUMAN_AUDIT_REVIEW_LAUNCHER_REQUIRED_PHRASES = {
    "localhost bind": "--bind 127.0.0.1",
    "review HTML target": "active_verification_human_audit_review.html",
    "python http server": "python3 -m http.server",
    "artifact directory cwd": 'cd "$(dirname "$0")"',
}

STEP1_HUMAN_AUDIT_FINALIZE_SCRIPT_REQUIRED_PHRASES = {
    "finalize command": "finalize-active-verification-human-audit",
    "worksheet import option": "--from-worksheet",
    "worksheet import command": "import-active-verification-human-audit-worksheet",
    "model-blinded worksheet import option": "--from-model-blinded-worksheet",
    "model-blinded worksheet import command": "import-active-verification-model-blinded-human-audit-worksheet",
    "attestation file": "active_verification_human_audit_attestation.md",
    "attestation sync": "cp \"$attestation_md\"",
    "artifact rebuild command": "artifact-package",
    "readiness command": "step1-readiness-check",
    "readiness status summary": "Step 1 readiness status:",
    "failing gates summary": "Failing gates:",
    "artifact directory cwd": 'cd "$(dirname "$0")"',
}

STEP1_RELEASE_VERIFY_SCRIPT_REQUIRED_PHRASES = {
    "minimal example command": "./reproduce_minimal.sh",
    "pytest command": "uv run pytest",
    "paper build command": "make",
    "readiness command": "step1-readiness-check",
    "readiness status check": "eha_step1_readiness_check.json",
    "git diff check": "git diff --check",
    "allow blocked option": "--allow-blocked",
    "artifact directory cwd": 'cd "$(dirname "$0")"',
}

SUMMARY_METRICS = [
    "operational_epistemic_escape",
    "conditional_epistemic_escape",
    "parse_success",
    "belief_correctness",
    "evidence_cleanliness",
    "uncertainty_discipline",
    "support_empty_rate",
    "evidence_precision",
    "clean_support_recall",
    "rejected_pollutant_rate",
    "dual_role_rate",
    "required_action_recall",
    "verification_action_score",
    "visible_output_tokens",
    "answer_word_count",
    "evidence_assessment_word_count",
    "max_action_rationale_word_count",
    "overlength_rate",
    "cost_usd",
]


def split_csv(value: str) -> List[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def pollutant_ids(task) -> set[str]:
    return set(task.contaminant_doc_ids) | set(task.generated_doc_ids) | set(task.stale_doc_ids)


def baseline_record(task, prompt_condition: str, baseline_name: str, prediction: EpistemicPrediction) -> EpistemicRunRecord:
    return EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model=f"{baseline_name}_baseline",
        provider="baseline",
        budget_setting="opaque_no_api",
        prompt_condition=prompt_condition,
        backend="baseline",
        prediction=normalize_prediction(prediction, task),
        parse_success=True,
        invocation_profile={"api_calls_made": False, "doc_id_policy": "opaque_per_task"},
    )


def id_only_prediction(task, prompt_condition: str) -> EpistemicPrediction:
    return EpistemicPrediction(
        claim_verdict="insufficient",
        confidence=0.34,
        supporting_evidence=[],
        rejected_evidence=[],
        selected_doc_ids=[],
        actions=[],
        evidence_environment_assessment="ID-only baseline sees opaque document IDs only.",
        answer="Insufficient information from IDs alone.",
    )


def metadata_only_prediction(task, prompt_condition: str) -> EpistemicPrediction:
    source_priority = {"audit_report", "regulator_filing", "certification_record", "official_statement", "technical_changelog"}
    weak_markers = ("summary", "secondary", "coverage", "wiki", "digest", "planning", "repost")
    support = [
        doc.doc_id
        for doc in task.documents
        if doc.source_type in source_priority and not any(marker in (doc.title + " " + doc.source_type).lower() for marker in weak_markers)
    ][:2]
    rejected = [
        doc.doc_id
        for doc in task.documents
        if any(marker in (doc.title + " " + doc.source_type).lower() for marker in weak_markers)
    ][:3]
    verdict = "insufficient" if task.condition in {"generated_lore", "buried_primary"} and not support else ("supported" if support else "insufficient")
    actions: List[EpistemicAction] = []
    if task.family == "active_verification":
        if not support:
            actions.append(EpistemicAction(action="search_primary", target=task.question, rationale="Metadata does not expose a strong primary-looking source."))
        if task.condition in {"false_consensus", "buried_primary", "conflicting_evidence"}:
            actions.append(EpistemicAction(action="search_contradiction", target=task.question, rationale="Metadata suggests checking for a contrary source."))
    return EpistemicPrediction(
        claim_verdict=verdict,
        confidence=0.55,
        supporting_evidence=support,
        rejected_evidence=rejected,
        selected_doc_ids=support[: task.max_selected_docs],
        actions=actions[: task.max_actions],
        evidence_environment_assessment="Metadata-only baseline uses visible source type, title, and timestamp cues, not body text.",
        answer="Verdict follows visible metadata heuristic.",
    )


def simple_heuristic_prediction(task, prompt_condition: str) -> EpistemicPrediction:
    primary_markers = ("primary record", "independent primary", "signed record")
    refute_markers = ("lapsed", "unresolved", "failed", "did not", "not completed", "above two percent", "no signed")
    weak_markers = ("authoritative-looking summary", "secondary coverage", "wiki-style", "repeats", "generated-lore")
    primary_like = [
        doc.doc_id
        for doc in task.documents
        if any(marker in (doc.title + " " + doc.body[:220]).lower() for marker in primary_markers)
    ]
    weak_like = [
        doc.doc_id
        for doc in task.documents
        if any(marker in (doc.title + " " + doc.body[:220]).lower() for marker in weak_markers)
    ]
    if not primary_like:
        verdict = "insufficient"
        support: List[str] = []
    else:
        primary_text = " ".join(doc.body[:260].lower() for doc in task.documents if doc.doc_id in primary_like)
        verdict = "refuted" if any(marker in primary_text for marker in refute_markers) else "supported"
        support = primary_like[:2]
    return EpistemicPrediction(
        claim_verdict=verdict,
        confidence=0.62,
        supporting_evidence=support,
        rejected_evidence=weak_like[:5],
        selected_doc_ids=(primary_like + [doc.doc_id for doc in task.documents if doc.doc_id not in primary_like and doc.doc_id not in weak_like])[: task.max_selected_docs],
        actions=[],
        evidence_environment_assessment="Simple heuristic uses visible body/source cues for direct records and weak repeated summaries; it emits no active tool actions.",
        answer="Heuristic baseline result.",
    )


def random_valid_schema_prediction(task, prompt_condition: str) -> EpistemicPrediction:
    rng = Random(stable_task_seed(task.task_id, salt=f"random-valid-schema:{prompt_condition}"))
    doc_ids = [doc.doc_id for doc in task.documents]
    shuffled = list(doc_ids)
    rng.shuffle(shuffled)
    verdict = rng.choice(["supported", "refuted", "insufficient"])
    action_names = ["open", "trace_source", "search_primary", "search_contradiction", "compare_versions", "abstain"]
    actions = [
        EpistemicAction(action=rng.choice(action_names), target=shuffled[index % len(shuffled)] if shuffled else "", rationale="Random valid-schema action.")
        for index in range(min(task.max_actions, 2))
    ]
    return EpistemicPrediction(
        claim_verdict=verdict,
        confidence=round(rng.uniform(0.34, 0.66), 3),
        supporting_evidence=shuffled[: rng.randint(0, min(2, len(shuffled)))],
        rejected_evidence=shuffled[2 : 2 + rng.randint(0, min(3, max(0, len(shuffled) - 2)))],
        selected_doc_ids=shuffled[: task.max_selected_docs],
        actions=actions,
        evidence_environment_assessment="Random valid-schema baseline emits structurally valid fields without evidence understanding.",
        answer="Random valid-schema baseline result.",
    )


def always_insufficient_prediction(task, prompt_condition: str) -> EpistemicPrediction:
    return EpistemicPrediction(
        claim_verdict="insufficient",
        confidence=0.50,
        supporting_evidence=[],
        rejected_evidence=[],
        selected_doc_ids=[],
        actions=[],
        evidence_environment_assessment="Always-insufficient baseline abstains regardless of visible evidence.",
        answer="Insufficient evidence.",
    )


PREDICTORS = {
    "id_only": id_only_prediction,
    "metadata_only": metadata_only_prediction,
    "simple_heuristic": simple_heuristic_prediction,
    "random_valid_schema": random_valid_schema_prediction,
    "always_insufficient": always_insufficient_prediction,
}


def add_verification_action_score(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for row in rows:
        row["verification_action_score"] = (
            (
                float(row["primary_action_rate"])
                + float(row["contradiction_action_rate"])
                + float(row["generated_lore_trace_rate"])
            )
            / 3.0
            if row["family"] == "active_verification"
            else 0.0
        )
    return rows


def run_step1_baselines(*, task_dir: Path, out_dir: Path, baselines: Sequence[str] = BASELINE_NAMES) -> None:
    unknown = sorted(set(baselines) - set(PREDICTORS))
    if unknown:
        raise ValueError(f"unknown baseline(s): {', '.join(unknown)}")
    tasks = read_tasks(task_dir / "tasks.jsonl")
    out_dir.mkdir(parents=True, exist_ok=True)
    all_rows: List[Dict[str, Any]] = []
    all_records: List[EpistemicRunRecord] = []
    for baseline_name in baselines:
        predictor = PREDICTORS[baseline_name]
        records = [
            baseline_record(task, prompt_condition, baseline_name, predictor(task, prompt_condition))
            for task in tasks
            for prompt_condition in PROMPTS
        ]
        rows = add_verification_action_score(score_records(records, tasks))
        write_jsonl(out_dir / f"{baseline_name}_baseline_predictions.jsonl", [model_to_dict(record) for record in records])
        write_csv(out_dir / f"{baseline_name}_baseline.csv", rows)
        write_csv(out_dir / f"{baseline_name}_baseline_summary.csv", aggregate(rows, ["model", "budget_setting"], SUMMARY_METRICS))
        write_csv(out_dir / f"{baseline_name}_baseline_by_family.csv", aggregate(rows, ["model", "budget_setting", "family"], SUMMARY_METRICS))
        write_csv(out_dir / f"{baseline_name}_baseline_by_condition.csv", aggregate(rows, ["model", "budget_setting", "condition"], SUMMARY_METRICS))
        all_rows.extend(rows)
        all_records.extend(records)
    write_jsonl(out_dir / "baseline_predictions.jsonl", [model_to_dict(record) for record in all_records])
    write_csv(out_dir / "baseline_rows.csv", all_rows)
    write_csv(out_dir / "baseline_summary.csv", aggregate(all_rows, ["model", "budget_setting"], SUMMARY_METRICS))
    write_json(
        out_dir / "baseline_manifest.json",
        {
            "task_count": len(tasks),
            "prompt_conditions": list(PROMPTS),
            "baselines": list(baselines),
            "api_calls_made": False,
            "row_count": len(all_rows),
        },
    )


def opaque_task_payload(task) -> Dict[str, Any]:
    messages = build_messages(task, "standard_answer", opaque_doc_ids=True, scrub_audit_labels=True)
    payload = json.loads(messages[-1]["content"])
    return {
        "task_id": task.task_id,
        "family": task.family,
        "condition": task.condition,
        "question": payload["question"],
        "documents": payload["documents"],
        "max_selected_docs": task.max_selected_docs,
        "max_actions": task.max_actions,
    }


def visible_gold_label(task) -> Dict[str, Any]:
    view = opaque_doc_id_view(task)

    def translate(values: Iterable[str]) -> List[str]:
        return [view.audit_to_visible[value] for value in values if value in view.audit_to_visible]

    return {
        "task_id": task.task_id,
        "gold_verdict": task.gold_verdict,
        "primary_doc_ids": translate(task.primary_doc_ids),
        "contaminant_doc_ids": translate(task.contaminant_doc_ids),
        "generated_doc_ids": translate(task.generated_doc_ids),
        "stale_doc_ids": translate(task.stale_doc_ids),
        "contradiction_doc_ids": translate(task.contradiction_doc_ids),
    }


def visible_doc_id_maps(tasks: Sequence[Any]) -> Dict[str, Dict[str, str]]:
    return {task.task_id: dict(opaque_doc_id_view(task).audit_to_visible) for task in tasks}


def translate_doc_ids_in_text(value: str, mapping: Mapping[str, str]) -> str:
    translated = value
    for audit_id, visible_id in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        translated = translated.replace(audit_id, visible_id)
    return translated


def translate_doc_ids_in_value(value: Any, mapping: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return translate_doc_ids_in_text(value, mapping)
    if isinstance(value, list):
        return [translate_doc_ids_in_value(item, mapping) for item in value]
    if isinstance(value, dict):
        return {key: translate_doc_ids_in_value(item, mapping) for key, item in value.items()}
    return value


def sanitize_jsonl_doc_ids(src: Path, dst: Path, maps_by_task: Mapping[str, Mapping[str, str]]) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    rows: List[Any] = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        task_id = payload.get("task_id", "") if isinstance(payload, dict) else ""
        if task_id and task_id not in maps_by_task:
            continue
        rows.append(translate_doc_ids_in_value(payload, maps_by_task.get(task_id, {})))
    write_jsonl(dst, rows)


def sanitize_csv_doc_ids(src: Path, dst: Path, maps_by_task: Mapping[str, Mapping[str, str]]) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = []
        for row in reader:
            task_id = row.get("task_id", "")
            if task_id and task_id not in maps_by_task:
                continue
            rows.append(
                {
                    field: translate_doc_ids_in_text(row.get(field, ""), maps_by_task.get(task_id, {}))
                    for field in fieldnames
                }
            )
    write_csv(dst, rows)


def copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def write_prompt_templates(out_dir: Path, sample_task) -> None:
    for prompt_condition in PROMPTS:
        messages = build_messages(sample_task, prompt_condition, opaque_doc_ids=True, scrub_audit_labels=True)
        payload = json.loads(messages[-1]["content"])
        template = {
            "system_or_developer_instruction": messages[0]["content"] if messages else "",
            "prompt_condition": prompt_condition,
            "policy": payload.get("policy", []),
            "schema": payload.get("schema", {}),
            "note": "The runtime task payload supplies question and opaque documents.",
        }
        write_json(out_dir / "prompts" / f"{prompt_condition}.txt", template)


def write_minimal_scorer(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def score(task, output):
    gold = task["gold"]
    support = set(output.get("supporting_evidence", []))
    pollutants = set(gold.get("contaminant_doc_ids", [])) | set(gold.get("generated_doc_ids", [])) | set(gold.get("stale_doc_ids", []))
    belief = output.get("claim_verdict") == gold.get("gold_verdict")
    evidence_clean = not bool(support & pollutants)
    uncertainty = output.get("claim_verdict") == "insufficient" if gold.get("gold_verdict") == "insufficient" else output.get("claim_verdict") != "insufficient"
    operational_escape = bool(belief and evidence_clean and uncertainty)
    return {
        "belief_correctness": float(belief),
        "evidence_cleanliness": float(evidence_clean),
        "uncertainty_discipline": float(uncertainty),
        "operational_epistemic_escape": float(operational_escape),
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: scoring_contract.py TASK_JSON MODEL_OUTPUT_JSON")
    task = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    print(json.dumps(score(task, output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
""",
        encoding="utf-8",
    )


def write_human_audit_review_server_script(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

port="${1:-8765}"
review_path="audits/active_verification_human_audit_review.html"
url="http://127.0.0.1:${port}/${review_path}"

if [ ! -f "$review_path" ]; then
  echo "Missing ${review_path}. Rebuild the artifact package first." >&2
  exit 1
fi

echo "Serving EHA active-verification human-audit review at:"
echo "  ${url}"
echo
echo "Press Ctrl-C here after the reviewer finishes downloading active_verification_human_audit.csv."

if command -v open >/dev/null 2>&1; then
  open "$url" >/dev/null 2>&1 || true
fi

python3 -m http.server "$port" --bind 127.0.0.1
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def write_human_audit_finalize_script(path: Path) -> None:
    path.write_text(
        """#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
  echo "usage: ./finalize_human_audit.sh [--from-worksheet|--from-model-blinded-worksheet]" >&2
  echo "  --from-worksheet                 import audits/active_verification_pilot_human_audit_worksheet_50.csv before finalization" >&2
  echo "  --from-model-blinded-worksheet   import audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv before finalization" >&2
}

if [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "${1:-}" != "" ] && [ "${1:-}" != "--from-worksheet" ] && [ "${1:-}" != "--from-model-blinded-worksheet" ]; then
  usage
  exit 2
fi

artifact_dir="$(pwd)"
repo_root="$(cd .. && pwd)"
eha_dir="${EHA_MVP_DIR:-${repo_root}/eha-mvp}"
paper_dir="${PAPER_DIR:-${repo_root}/paper}"
reports_dir="${REPORTS_DIR:-${repo_root}/reports}"
readiness_json="${reports_dir}/eha_step1_readiness_check.json"
active_dir="results/reports-eha-active-verification-audit-opaque-2026-05-15"
reference_csv="${eha_dir}/${active_dir}/active_verification_pilot_human_audit_sample_50.csv"
labels_csv="${artifact_dir}/audits/active_verification_human_audit.csv"
worksheet_csv="${artifact_dir}/audits/active_verification_pilot_human_audit_worksheet_50.csv"
model_blinded_worksheet_csv="${artifact_dir}/audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv"
attestation_md="${artifact_dir}/audits/active_verification_human_audit_attestation.md"

if [ ! -d "$eha_dir" ]; then
  echo "Missing eha-mvp directory: ${eha_dir}" >&2
  echo "Set EHA_MVP_DIR if this artifact directory is not next to eha-mvp/." >&2
  exit 1
fi

if [ ! -f "$reference_csv" ]; then
  echo "Missing reference CSV: ${reference_csv}" >&2
  echo "Rebuild the active-verification audit package before finalizing labels." >&2
  exit 1
fi

if [ ! -f "$labels_csv" ]; then
  echo "Missing label CSV: ${labels_csv}" >&2
  exit 1
fi

cd "$eha_dir"

if [ "${1:-}" = "--from-worksheet" ]; then
  if [ ! -f "$worksheet_csv" ]; then
    echo "Missing worksheet CSV: ${worksheet_csv}" >&2
    exit 1
  fi
  uv run eha-step1-release import-active-verification-human-audit-worksheet \\
    --worksheet-csv "$worksheet_csv" \\
    --reference-csv "$reference_csv" \\
    --out-csv "$labels_csv"
fi

if [ "${1:-}" = "--from-model-blinded-worksheet" ]; then
  if [ ! -f "$model_blinded_worksheet_csv" ]; then
    echo "Missing model-blinded worksheet CSV: ${model_blinded_worksheet_csv}" >&2
    exit 1
  fi
  uv run eha-step1-release import-active-verification-model-blinded-human-audit-worksheet \\
    --worksheet-csv "$model_blinded_worksheet_csv" \\
    --reference-csv "$reference_csv" \\
    --out-csv "$labels_csv"
fi

uv run eha-step1-release finalize-active-verification-human-audit \\
  --labels-csv "$labels_csv" \\
  --reference-csv "$reference_csv" \\
  --out-dir "$active_dir"

if [ ! -f "$attestation_md" ]; then
  echo "Missing human-audit attestation: ${attestation_md}" >&2
  exit 1
fi

cp "$attestation_md" "${active_dir}/active_verification_human_audit_attestation.md"

uv run eha-step1-release artifact-package \\
  --task-dir data/epistemic-resilience-v1 \\
  --frontier-main-dir results/reports-eha-frontier-main-opaque-2026-05-15 \\
  --baseline-dir results/reports-eha-step1-baselines-2026-05-15 \\
  --generated-lore-dir results/reports-eha-generated-lore-role-audit-opaque-2026-05-15 \\
  --active-verification-dir "$active_dir" \\
  --out-dir "$artifact_dir"

uv run eha-step1-release step1-readiness-check \\
  --artifact-dir "$artifact_dir" \\
  --paper-dir "$paper_dir" \\
  --out-dir "$reports_dir"

if command -v python3 >/dev/null 2>&1 && [ -f "$readiness_json" ]; then
  python3 - "$readiness_json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
status = payload.get("status", "missing")
failing = [
    gate.get("name", "<unnamed>")
    for gate in payload.get("gates", [])
    if gate.get("status") == "fail"
]
print(f"Step 1 readiness status: {status}")
print("Failing gates: " + (", ".join(failing) if failing else "none"))
PY
else
  echo "Step 1 readiness summary unavailable; inspect ${readiness_json}."
fi

echo
echo "Human-audit finalization commands completed."
echo "Inspect ${readiness_json} before changing paper claims."
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def write_step1_release_verify_script(path: Path) -> None:
    path.write_text(
        r'''#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
  echo "usage: ./verify_step1_release.sh [--allow-blocked]" >&2
  echo "  --allow-blocked  run checks but do not fail solely because readiness remains blocked" >&2
}

if [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "${1:-}" != "" ] && [ "${1:-}" != "--allow-blocked" ]; then
  usage
  exit 2
fi

allow_blocked=false
if [ "${1:-}" = "--allow-blocked" ]; then
  allow_blocked=true
fi

artifact_dir="$(pwd)"
repo_root="$(cd .. && pwd)"
eha_dir="${EHA_MVP_DIR:-${repo_root}/eha-mvp}"
paper_dir="${PAPER_DIR:-${repo_root}/paper}"
reports_dir="${REPORTS_DIR:-${repo_root}/reports}"
readiness_json="${reports_dir}/eha_step1_readiness_check.json"

if [ ! -d "$eha_dir" ]; then
  echo "Missing eha-mvp directory: ${eha_dir}" >&2
  echo "Set EHA_MVP_DIR if this artifact directory is not next to eha-mvp/." >&2
  exit 1
fi

if [ ! -d "$paper_dir" ]; then
  echo "Missing paper directory: ${paper_dir}" >&2
  echo "Set PAPER_DIR if this artifact directory is not next to paper/." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to read ${readiness_json}." >&2
  exit 1
fi

bash -n "${artifact_dir}/serve_human_audit_review.sh"
bash -n "${artifact_dir}/finalize_human_audit.sh"
bash -n "${artifact_dir}/verify_step1_release.sh"

cd "$artifact_dir"
./reproduce_minimal.sh >/tmp/eha_step1_minimal_score.json

cd "$eha_dir"
uv run pytest

cd "$paper_dir"
make

cd "$eha_dir"
uv run eha-step1-release step1-readiness-check \
  --artifact-dir "$artifact_dir" \
  --paper-dir "$paper_dir" \
  --out-dir "$reports_dir"

status="$(python3 - "$readiness_json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("status", "missing"))
PY
)"

if [ "$status" != "ready" ] && [ "$allow_blocked" != "true" ]; then
  echo "Step 1 readiness is ${status}; inspect ${readiness_json}." >&2
  exit 2
fi

if git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  (cd "$repo_root" && git diff --check)
fi

echo
echo "Step 1 release verification completed with readiness status: ${status}"
''',
        encoding="utf-8",
    )
    path.chmod(0o755)


def write_release_readme(out_dir: Path) -> None:
    (out_dir / "README.md").write_text(
        "\n".join(
            [
                "# EHA Step 1 Reproducibility Package",
                "",
                "This package contains the opaque-ID repaired Step 1 artifacts for the controlled diagnostic EHA paper.",
                "`file_manifest.json` lists every packaged file except itself, with byte size and SHA-256 hash.",
                "",
                "Contents:",
                "",
                "- `data/`: opaque task packets, document packets, and visible-ID gold labels.",
                "- `prompts/`: standard and epistemic-hygiene prompt contracts.",
                "- `scorer/`: a minimal scoring contract and notes.",
                "- `outputs/`: opaque frontier predictions, scored rows, and copied run/report manifests.",
                "- `baselines/`: no-API baseline scored rows.",
                "- `audits/`: prompt leakage, generated-lore schema, active-verification action audit, the pilot human-audit sheet/context/worksheet/model-blinded worksheet/HTML review page/Markdown packet/model-blinded packet/reviewer brief/paper-update memo/protocol/manifest/attestation/validation report, and any clearly marked Codex-assisted audit outputs.",
                "- `examples/`: a minimal task, model output, and score.",
                "",
                "Run the minimal example from this directory:",
                "",
                "```bash",
                "./reproduce_minimal.sh",
                "```",
                "",
                "Start the active-verification human-audit browser review page from this directory:",
                "",
                "```bash",
                "./serve_human_audit_review.sh",
                "```",
                "",
                "The script serves only on `127.0.0.1` and opens `audits/active_verification_human_audit_review.html` when the local platform supports `open`.",
                "",
                "After an independent human auditor has completed all 50 rows, finalize the label sheet from this directory:",
                "",
                "```bash",
                "./finalize_human_audit.sh",
                "```",
                "",
                "If the auditor filled the wide worksheet instead of the strict CSV, run:",
                "",
                "```bash",
                "./finalize_human_audit.sh --from-worksheet",
                "```",
                "",
                "If the auditor filled the model-blinded worksheet, run:",
                "",
                "```bash",
                "./finalize_human_audit.sh --from-model-blinded-worksheet",
                "```",
                "",
                "The finalization script validates the labels, imports them into the results directory, rebuilds this artifact package, reruns the paper-aware readiness check, and prints the readiness status plus any failing gates. Complete `audits/active_verification_human_audit_attestation.md` before treating the human audit as release-ready.",
                "",
                "Human-audit gate:",
                "",
                "- Release readiness requires all 50 rows in `audits/active_verification_human_audit.csv` to have `audit_status = human_labeled`, all eight binary labels, and nonblank `auditor_notes`.",
                "- After finalization and artifact rebuild, `artifact/manifest.json` must report `active_verification_human_audit.status = complete` and `n_labeled = 50`.",
                "- The paper must keep human-audit counts separate from Codex-assisted triage counts; if readiness remains `blocked`, do not update paper claims as if human validation is complete.",
                "",
                "Check Step 1 release readiness from `eha-mvp/`:",
                "",
                "```bash",
                "uv run eha-step1-release step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports",
                "```",
                "",
                "After human labels and paper claim updates are complete, run the pre-release verifier from this directory:",
                "",
                "```bash",
                "./verify_step1_release.sh",
                "```",
                "",
                "For an intentionally blocked dry run before human labels are complete, use:",
                "",
                "```bash",
                "./verify_step1_release.sh --allow-blocked",
                "```",
                "",
                "The verifier runs the minimal example, the EHA test suite, the paper build, the paper-aware readiness check, and `git diff --check` when the artifact sits inside a git worktree.",
                "",
                "Current gate status may be `blocked` until `audits/active_verification_human_audit.csv` is independently human-labeled and finalized. The audit manifest records the eight required label fields, including the three needed-action labels. Codex-assisted audit outputs are triage artifacts, not human validation.",
                "",
                "Scope: this package supports a controlled diagnostic benchmark. It is not evidence that any model or agent is certified for legal, medical, financial, or live deployment use.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def active_verification_audit_status(active_verification_dir: Path, summary_name: str) -> Dict[str, Any]:
    summary_path = active_verification_dir / summary_name
    if not summary_path.exists():
        return {"status": "missing", "n_rows": 0, "n_labeled": 0}
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "invalid_summary_json", "n_rows": 0, "n_labeled": 0}
    return {
        "status": summary.get("status", "unknown"),
        "n_rows": summary.get("n_rows", 0),
        "n_labeled": summary.get("n_labeled", 0),
    }


def active_verification_human_audit_status(active_verification_dir: Path) -> Dict[str, Any]:
    return active_verification_audit_status(active_verification_dir, "active_verification_pilot_human_audit_summary.json")


def active_verification_codex_xhigh_audit_status(active_verification_dir: Path) -> Dict[str, Any]:
    return active_verification_audit_status(active_verification_dir, "active_verification_pilot_codex_xhigh_audit_summary.json")


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def artifact_file_records(artifact_dir: Path) -> List[Dict[str, Any]]:
    records = []
    for path in sorted(artifact_dir.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(artifact_dir).as_posix()
        if relative == "file_manifest.json":
            continue
        records.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": file_sha256(path),
            }
        )
    return records


def write_artifact_file_manifest(artifact_dir: Path) -> None:
    records = artifact_file_records(artifact_dir)
    write_json(
        artifact_dir / "file_manifest.json",
        {
            "schema_version": 1,
            "scope": "artifact package files excluding file_manifest.json",
            "file_count": len(records),
            "files": records,
        },
    )


def task_audit_role_by_visible_doc(task) -> Dict[str, str]:
    view = opaque_doc_id_view(task)
    roles: Dict[str, str] = {}
    for doc in task.documents:
        visible = view.audit_to_visible.get(doc.doc_id)
        if visible:
            roles[visible] = doc.role
    return roles


def parse_actions(value: str) -> List[Dict[str, Any]]:
    if not value:
        return []
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return [{"action": "unparsed", "target": "", "rationale": value}]
    return payload if isinstance(payload, list) else []


def active_verification_context_row(row: Mapping[str, str], task_by_id: Mapping[str, Any]) -> Dict[str, Any]:
    task = task_by_id[row["task_id"]]
    opaque_task = opaque_task_payload(task)
    gold = visible_gold_label(task)
    roles = task_audit_role_by_visible_doc(task)
    documents = []
    for doc in opaque_task["documents"]:
        documents.append(
            {
                "doc_id": doc["doc_id"],
                "title": doc.get("title", ""),
                "source_type": doc.get("source_type", ""),
                "timestamp": doc.get("timestamp", ""),
                "visible_citations": doc.get("visible_citations", []),
                "body_excerpt": doc.get("body", "")[:420],
                "audit_role": roles.get(doc["doc_id"], "unknown"),
            }
        )
    return {
        "audit_status": row.get("audit_status", "needs_human_label"),
        "model": row["model"],
        "task_id": row["task_id"],
        "condition": row["condition"],
        "prompt_condition": row["prompt_condition"],
        "question": opaque_task["question"],
        "gold": gold,
        "required_action_needs": {
            "primary_search_needed": row.get("primary_search_needed", ""),
            "contradiction_search_needed": row.get("contradiction_search_needed", ""),
            "trace_source_needed": row.get("trace_source_needed", ""),
        },
        "auto_scorer": {
            "action_gate_pass": row.get("auto_action_gate_pass", ""),
            "missing_primary_action": row.get("auto_missing_primary_action", ""),
            "missing_contradiction_action": row.get("auto_missing_contradiction_action", ""),
            "missing_trace_source_action": row.get("auto_missing_trace_source_action", ""),
        },
        "model_actions": parse_actions(row.get("auto_actions_visible_ids", "")),
        "documents": documents,
        "human_label_fields": {
            "semantically_useful_action": row.get("semantically_useful_action", ""),
            "machine_executable_action": row.get("machine_executable_action", ""),
            "exact_target_present": row.get("exact_target_present", ""),
            "required_action_type_present": row.get("required_action_type_present", ""),
            "contradiction_search_needed": row.get("contradiction_search_needed", ""),
            "primary_search_needed": row.get("primary_search_needed", ""),
            "trace_source_needed": row.get("trace_source_needed", ""),
            "scorer_too_strict": row.get("scorer_too_strict", ""),
            "auditor_notes": row.get("auditor_notes", ""),
        },
    }


def write_active_verification_guidelines(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "# Active-Verification Pilot Human-Audit Guidelines",
                "",
                "This sheet audits whether model actions are useful to a human reader and executable by an agent tool interface.",
                "",
                "Label values should be `1` for yes, `0` for no, and blank only when the row has not been reviewed.",
                "",
                "Do not sort, delete, duplicate, or reorder rows. Do not edit non-label columns; the validator compares them against the original sample sheet.",
                "",
                "The Codex-assisted audit, if consulted, is reference-only triage. Do not copy its labels into this sheet unless an independent human auditor has reviewed the row and agrees with the judgment.",
                "",
                "For the sampling design, evidence conditions, finalization gate, and claim boundary, see `active_verification_human_audit_protocol.md`.",
                "",
                "Fields:",
                "",
                "- `semantically_useful_action`: the proposed action would help a human investigate the evidence state.",
                "- `machine_executable_action`: the action has a clear action type and a target a tool could execute without interpretation.",
                "- `exact_target_present`: the target is a single exact `doc_###` or an explicit schema-level search target.",
                "- `required_action_type_present`: the action type matches the needed primary, contradiction, or trace-source action.",
                "- `contradiction_search_needed`: the task requires seeking or checking contradictory evidence.",
                "- `primary_search_needed`: the task requires seeking, opening, or tracing a primary source.",
                "- `trace_source_needed`: the task requires tracing a claim to its upstream source.",
                "- `scorer_too_strict`: mark `1` only when the automatic scorer rejects an action that is both useful and reasonably executable under the written contract.",
                "",
                "Important distinction: an action can be semantically useful but not machine executable. For example, a bundled target such as `doc_001 and doc_004 -> doc_007` may be understandable to a reader but unsafe for a tool call that expects one exact target.",
                "",
                "The context JSONL uses opaque model-visible document IDs. `audit_role` is shown only for auditor context; it was not visible to the model.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_active_verification_human_audit_protocol(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Active-Verification Pilot Human-Audit Protocol",
                "",
                "Protocol version: 1",
                "",
                "## Purpose",
                "",
                "This protocol defines the Step 1 single-auditor pilot audit for active-verification actions. It distinguishes three questions:",
                "",
                "- whether a proposed action is useful to a human reader;",
                "- whether the same action is machine executable under the written action contract;",
                "- whether the automatic scorer is visibly too strict for that row.",
                "",
                "The protocol is part of the release artifact, but it does not create human-validation evidence by itself. The release gate remains blocked until all 50 rows are independently human-labeled and finalized.",
                "",
                "## Sample",
                "",
                "The audit sample contains 50 active-verification rows from the opaque main run. It is stratified across five evidence conditions with 10 rows per condition:",
                "",
                "- `clean`",
                "- `generated_lore`",
                "- `false_consensus`",
                "- `buried_primary`",
                "- `conflicting_evidence`",
                "",
                "The rows are reviewed in the fixed order supplied in `active_verification_human_audit.csv`, the wide worksheet, the browser review page, or the model-blinded packet. Do not sort, delete, duplicate, or reorder rows.",
                "",
                "## Materials",
                "",
                "- Strict label sheet: `active_verification_human_audit.csv`",
                "- Wide worksheet with context: `active_verification_pilot_human_audit_worksheet_50.csv`",
                "- Model-blinded worksheet with row-order transfer: `active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`",
                "- Browser review page: `active_verification_human_audit_review.html`",
                "- Reviewer brief: `active_verification_human_audit_reviewer_brief.md`",
                "- Row packet: `active_verification_pilot_human_audit_packet_50.md`",
                "- Model-blinded row packet: `active_verification_pilot_human_audit_model_blinded_packet_50.md`",
                "- Paper-update memo: `active_verification_pilot_human_audit_paper_update.md`",
                "- Attestation template: `active_verification_human_audit_attestation.md`",
                "- Guidelines: `active_verification_human_audit_guidelines.md`",
                "- Context JSONL: `active_verification_pilot_human_audit_context_50.jsonl`",
                "- Validation report: `active_verification_pilot_human_audit_validation.json` and `_rows.csv`",
                "- Reference-only Codex triage: `active_verification_pilot_codex_xhigh_audit_50.csv`",
                "",
                "The context uses opaque model-visible `doc_###` IDs. Audit roles are shown only to the human auditor for review; they were not visible to the model.",
                "",
                "## Label Contract",
                "",
                "For each row, set `audit_status` to `human_labeled`, fill all eight binary label fields with `0` or `1`, and add a short `auditor_notes` explanation.",
                "",
                "Required binary fields:",
                "",
                "- `semantically_useful_action`",
                "- `machine_executable_action`",
                "- `exact_target_present`",
                "- `required_action_type_present`",
                "- `contradiction_search_needed`",
                "- `primary_search_needed`",
                "- `trace_source_needed`",
                "- `scorer_too_strict`",
                "",
                "The three `*_needed` fields are prefilled from the task design to reduce annotation friction, but they remain human label fields and should be verified or revised.",
                "",
                "Model identities, prompt conditions, and automatic scorer outcomes are intentionally omitted from the model-blinded packet and model-blinded worksheet so an auditor can make the usefulness/executability judgments without seeing provider identity or the automatic gate decision.",
                "",
                "## Boundary Rules",
                "",
                "- A row can be semantically useful but fail machine executability if the target is bundled, vague, or not a direct tool target.",
                "- Mark `scorer_too_strict = 1` only when the rejected action is both useful and reasonably executable under the written contract.",
                "- Do not edit non-label columns. The validator checks row keys, row order, labels, and metadata against the original sample.",
                "- Codex-assisted labels are triage evidence only. They are not human validation and must not be copied into the human sheet unless an independent human auditor has reviewed the row and agrees.",
                "",
                "## Finalization Gate",
                "",
                "Run `finalize-active-verification-human-audit` after labeling. A valid completed audit requires:",
                "",
                "- `active_verification_pilot_human_audit_validation.json` status is `complete`;",
                "- `n_complete_rows = 50`;",
                "- no blank `auditor_notes` rows;",
                "- `active_verification_human_audit_attestation.md` is completed with auditor identity/role, date, review surface, and independent-review statements;",
                "- all five required evidence conditions are present;",
                "- the current label CSV hash matches the validation report;",
                "- the artifact manifest records `active_verification_human_audit.status = complete` and `n_labeled = 50` after rebuilding the release package.",
                "",
                "Until those conditions hold, the paper may cite the prepared materials and Codex-assisted triage only as pilot infrastructure, not as independent human-validation evidence.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_active_verification_human_audit_readme(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Active-Verification Human-Audit Quickstart",
                "",
                "This directory contains the Step 1 active-verification pilot audit materials. The release gate remains blocked until the 50-row human-audit sheet is independently labeled and finalized.",
                "",
                "## Files",
                "",
                "- Label sheet: `active_verification_human_audit.csv`",
                "- Optional wide worksheet: `active_verification_pilot_human_audit_worksheet_50.csv`",
                "- Optional model-blinded worksheet: `active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`",
                "- Browser review page: `active_verification_human_audit_review.html`",
                "- Reviewer brief: `active_verification_human_audit_reviewer_brief.md`",
                "- Row packet: `active_verification_pilot_human_audit_packet_50.md`",
                "- Model-blinded row packet: `active_verification_pilot_human_audit_model_blinded_packet_50.md`",
                "- Guidelines: `active_verification_human_audit_guidelines.md`",
                "- Protocol: `active_verification_human_audit_protocol.md`",
                "- Attestation template: `active_verification_human_audit_attestation.md`",
                "- Context JSONL: `active_verification_pilot_human_audit_context_50.jsonl`",
                "- Validation report: `active_verification_pilot_human_audit_validation.json` and `_rows.csv`",
                "- Paper-update memo: `active_verification_pilot_human_audit_paper_update.md`",
                "- reference-only triage: `active_verification_pilot_codex_xhigh_audit_50.csv`",
                "",
                "## Labeling Rules",
                "",
                "For every row in `active_verification_human_audit.csv`, set `audit_status` to `human_labeled`, verify or revise all eight binary label columns with `0` or `1`, and add a short `auditor_notes` explanation.",
                "",
                "If the wide worksheet is easier to review, fill the same label columns there first, then import it into the strict label sheet before finalization.",
                "",
                "If the model-blinded worksheet is easier to review, fill the same label columns there first, then import it into the strict label sheet before finalization with `--from-model-blinded-worksheet`. The import relies on `row_index` and row order rather than exposing model identity or prompt condition.",
                "",
                "If the HTML review page is easier, open `active_verification_human_audit_review.html` locally. It shows row-completion status, can import an existing strict CSV draft, and enables `active_verification_human_audit.csv` download only after all rows have the eight binary labels and auditor notes.",
                "",
                "If model identity or automatic scorer output could bias the review, use `active_verification_pilot_human_audit_model_blinded_packet_50.md` as the reading surface and transfer labels by row order into the strict CSV or wide worksheet.",
                "",
                "Do not sort, delete, duplicate, or reorder rows. Do not edit non-label columns. The validator checks row keys, row order, labels, and metadata. The three `*_needed` columns are label columns: they are prefilled for convenience, but the human auditor may change them after review.",
                "",
                "Codex-assisted audit files are triage only. Do not copy their labels into the human sheet unless an independent human auditor has reviewed the row and agrees with the judgment.",
                "",
                "Before final release, complete `active_verification_human_audit_attestation.md` with the auditor identifier or role, completion date, review surface, and yes/no statements confirming independent review, no copied Codex triage labels, all 50 rows reviewed, and all eight binary fields plus `auditor_notes` completed.",
                "",
                "## Finalize After Labeling",
                "",
                "Shortcut from the artifact root:",
                "",
                "```bash",
                "./finalize_human_audit.sh",
                "# or, if the wide worksheet was filled:",
                "./finalize_human_audit.sh --from-worksheet",
                "# or, if the model-blinded worksheet was filled:",
                "./finalize_human_audit.sh --from-model-blinded-worksheet",
                "```",
                "",
                "Run from `eha-mvp/`:",
                "",
                "```bash",
                "# If you filled the wide worksheet, run this import step first.",
                "# Skip it if active_verification_human_audit.csv was filled directly.",
                "uv run eha-step1-release import-active-verification-human-audit-worksheet \\",
                "  --worksheet-csv ../artifact/audits/active_verification_pilot_human_audit_worksheet_50.csv \\",
                "  --reference-csv results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv \\",
                "  --out-csv ../artifact/audits/active_verification_human_audit.csv",
                "",
                "# If you filled the model-blinded worksheet, run this import step instead.",
                "uv run eha-step1-release import-active-verification-model-blinded-human-audit-worksheet \\",
                "  --worksheet-csv ../artifact/audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv \\",
                "  --reference-csv results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv \\",
                "  --out-csv ../artifact/audits/active_verification_human_audit.csv",
                "",
                "uv run eha-step1-release finalize-active-verification-human-audit \\",
                "  --labels-csv ../artifact/audits/active_verification_human_audit.csv \\",
                "  --reference-csv results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv \\",
                "  --out-dir results/reports-eha-active-verification-audit-opaque-2026-05-15",
                "",
                "cp ../artifact/audits/active_verification_human_audit_attestation.md \\",
                "  results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_human_audit_attestation.md",
                "",
                "uv run eha-step1-release artifact-package \\",
                "  --task-dir data/epistemic-resilience-v1 \\",
                "  --frontier-main-dir results/reports-eha-frontier-main-opaque-2026-05-15 \\",
                "  --baseline-dir results/reports-eha-step1-baselines-2026-05-15 \\",
                "  --generated-lore-dir results/reports-eha-generated-lore-role-audit-opaque-2026-05-15 \\",
                "  --active-verification-dir results/reports-eha-active-verification-audit-opaque-2026-05-15 \\",
                "  --out-dir ../artifact",
                "",
                "uv run eha-step1-release step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports",
                "```",
                "",
                "Expected final state: `reports/eha_step1_readiness_check.json` reports `status = ready`. The shortcut prints the readiness status and failing gates; if it remains `blocked`, inspect the failing gate before changing paper claims. When the audit is complete, use `active_verification_pilot_human_audit_paper_update.md` as the paper-update memo for Section 6 and keep the Codex-assisted triage counts separate.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_active_verification_human_audit_reviewer_brief(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Human-Audit Reviewer Brief",
                "",
                "Use this brief when you are the independent reviewer for the 50-row active-verification pilot audit.",
                "",
                "## Choose A Review Surface",
                "",
                "Use one of these paths:",
                "",
                "- Browser page: `active_verification_human_audit_review.html`",
                "- Strict CSV: `active_verification_human_audit.csv`",
                "- Wide worksheet: `active_verification_pilot_human_audit_worksheet_50.csv`",
                "- Model-blinded worksheet: `active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`",
                "- Model-blinded reading packet: `active_verification_pilot_human_audit_model_blinded_packet_50.md`",
                "",
                "Prefer the model-blinded worksheet or packet if model identity, prompt condition, or automatic scorer output could bias the review.",
                "",
                "## Label Each Row",
                "",
                "For all 50 rows, set `audit_status = human_labeled`, fill every binary label with `0` or `1`, and write a short `auditor_notes` explanation.",
                "",
                "The eight binary labels are:",
                "",
                "- `semantically_useful_action`",
                "- `machine_executable_action`",
                "- `exact_target_present`",
                "- `required_action_type_present`",
                "- `contradiction_search_needed`",
                "- `primary_search_needed`",
                "- `trace_source_needed`",
                "- `scorer_too_strict`",
                "",
                "Do not sort, delete, duplicate, or reorder rows. Do not edit non-label columns. Blank `auditor_notes` fails validation.",
                "",
                "## Keep Triage Separate",
                "",
                "`active_verification_pilot_codex_xhigh_audit_50.csv` is reference-only triage. Do not copy those labels into the human sheet unless you independently reviewed the row and agree with the judgment.",
                "",
                "## Finish The Audit",
                "",
                "Complete `active_verification_human_audit_attestation.md` after labeling all rows. Set the auditor identifier or role, completion date, review surface, and the required `yes` confirmations.",
                "",
                "From the artifact root, run the matching finalization command:",
                "",
                "```bash",
                "./finalize_human_audit.sh",
                "./finalize_human_audit.sh --from-worksheet",
                "./finalize_human_audit.sh --from-model-blinded-worksheet",
                "```",
                "",
                "Expected result after a valid audit: `reports/eha_step1_readiness_check.json` reports `status = ready`. If it remains `blocked`, inspect the failing gate before changing paper claims.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def compact_text(value: Any, limit: int = 360) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def label_template() -> List[str]:
    return [
        "- semantically_useful_action: ",
        "- machine_executable_action: ",
        "- exact_target_present: ",
        "- required_action_type_present: ",
        "- contradiction_search_needed: ",
        "- primary_search_needed: ",
        "- trace_source_needed: ",
        "- scorer_too_strict: ",
        "- auditor_notes: ",
    ]


def write_active_verification_human_audit_attestation(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Active-Verification Human-Audit Attestation",
                "",
                "Complete this file only after an independent human auditor has reviewed all 50 rows and the strict label CSV has been finalized.",
                "",
                "auditor_identifier: [TO BE COMPLETED]",
                "date_completed: [TO BE COMPLETED]",
                "audit_surface_used: [TO BE COMPLETED: strict_csv | wide_worksheet | model_blinded_worksheet | html_review]",
                "independent_human_review_completed: [TO BE COMPLETED: yes]",
                "codex_triage_not_copied_as_human_labels: [TO BE COMPLETED: yes]",
                "all_50_rows_reviewed: [TO BE COMPLETED: yes]",
                "all_eight_binary_fields_and_auditor_notes_completed: [TO BE COMPLETED: yes]",
                "",
                "Required completion statements:",
                "",
                "- The independent human review covered all 50 rows.",
                "- Codex-assisted audit was not copied as human labels.",
                "- All eight binary label fields and auditor_notes were completed.",
                "",
                "Allowed `audit_surface_used` values: `strict_csv`, `wide_worksheet`, `model_blinded_worksheet`, `html_review`.",
                "",
                "This attestation records audit provenance. It does not replace the executable CSV validation report.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def write_active_verification_manual_packet(path: Path, context_rows: Sequence[Mapping[str, Any]]) -> None:
    lines = [
        "# Active-Verification Pilot Human-Audit Packet",
        "",
        "Use this packet with `active_verification_pilot_human_audit_sample_50.csv`. Fill labels in the CSV, not in this Markdown file.",
        "",
        "Label values are `1` for yes and `0` for no. Keep blanks only for rows not reviewed.",
        "",
        "A useful action can still be non-executable if the target is bundled, vague, or not a direct tool target.",
        "",
    ]
    for index, row in enumerate(context_rows, start=1):
        lines.extend(
            [
                f"## Row {index:02d}: {row['task_id']} / {row['model']} / {row['condition']} / {row['prompt_condition']}",
                "",
                f"Question: {compact_text(row.get('question', ''), 500)}",
                "",
                "Pre-filled needed-action labels to verify:",
                f"- primary_search_needed: {row.get('required_action_needs', {}).get('primary_search_needed', '')}",
                f"- contradiction_search_needed: {row.get('required_action_needs', {}).get('contradiction_search_needed', '')}",
                f"- trace_source_needed: {row.get('required_action_needs', {}).get('trace_source_needed', '')}",
                "",
                "Auto scorer:",
                f"- action_gate_pass: {row.get('auto_scorer', {}).get('action_gate_pass', '')}",
                f"- missing_primary_action: {row.get('auto_scorer', {}).get('missing_primary_action', '')}",
                f"- missing_contradiction_action: {row.get('auto_scorer', {}).get('missing_contradiction_action', '')}",
                f"- missing_trace_source_action: {row.get('auto_scorer', {}).get('missing_trace_source_action', '')}",
                "",
                "Model actions:",
            ]
        )
        actions = row.get("model_actions", [])
        if actions:
            for action in actions:
                lines.append(f"- `{action.get('action', '')}` target=`{action.get('target', '')}` rationale={compact_text(action.get('rationale', ''), 420)}")
        else:
            lines.append("- (none)")
        lines.extend(["", "Gold context for auditor:", f"- gold_verdict: {row.get('gold', {}).get('gold_verdict', '')}"])
        for field in ["primary_doc_ids", "contradiction_doc_ids", "contaminant_doc_ids", "generated_doc_ids", "stale_doc_ids"]:
            values = row.get("gold", {}).get(field, [])
            lines.append(f"- {field}: {', '.join(values) if values else '(none)'}")
        lines.extend(["", "Documents:"])
        for doc in row.get("documents", []):
            lines.append(
                f"- `{doc.get('doc_id', '')}` audit_role=`{doc.get('audit_role', '')}` source_type=`{doc.get('source_type', '')}` title={compact_text(doc.get('title', ''), 120)}"
            )
            lines.append(f"  Excerpt: {compact_text(doc.get('body_excerpt', ''), 420)}")
        lines.extend(["", "Labels to enter in CSV:", *label_template(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_active_verification_model_blinded_packet(path: Path, context_rows: Sequence[Mapping[str, Any]]) -> None:
    lines = [
        "# Active-Verification Pilot Model-Blinded Human-Audit Packet",
        "",
        "Use this packet when the auditor should avoid model identity, prompt condition, and automatic scorer outcomes while judging action usefulness and executability.",
        "",
        "Model identities and prompt conditions are intentionally omitted.",
        "Auto scorer outcomes are intentionally omitted.",
        "Use row order to transfer labels to `active_verification_human_audit.csv` or the wide worksheet.",
        "",
        "Label values are `1` for yes and `0` for no. Keep blanks only for rows not reviewed.",
        "",
        "A useful action can still be non-executable if the target is bundled, vague, or not a direct tool target.",
        "",
    ]
    for index, row in enumerate(context_rows, start=1):
        lines.extend(
            [
                f"## Row {index:02d}",
                "",
                f"Evidence condition: {row.get('condition', '')}",
                "",
                f"Question: {compact_text(row.get('question', ''), 500)}",
                "",
                "Pre-filled needed-action labels to verify:",
                f"- primary_search_needed: {row.get('required_action_needs', {}).get('primary_search_needed', '')}",
                f"- contradiction_search_needed: {row.get('required_action_needs', {}).get('contradiction_search_needed', '')}",
                f"- trace_source_needed: {row.get('required_action_needs', {}).get('trace_source_needed', '')}",
                "",
                "Proposed actions:",
            ]
        )
        actions = row.get("model_actions", [])
        if actions:
            for action in actions:
                lines.append(f"- `{action.get('action', '')}` target=`{action.get('target', '')}` rationale={compact_text(action.get('rationale', ''), 420)}")
        else:
            lines.append("- (none)")
        lines.extend(["", "Gold context for auditor:", f"- gold_verdict: {row.get('gold', {}).get('gold_verdict', '')}"])
        for field in ["primary_doc_ids", "contradiction_doc_ids", "contaminant_doc_ids", "generated_doc_ids", "stale_doc_ids"]:
            values = row.get("gold", {}).get(field, [])
            lines.append(f"- {field}: {', '.join(values) if values else '(none)'}")
        lines.extend(["", "Documents:"])
        for doc in row.get("documents", []):
            lines.append(
                f"- `{doc.get('doc_id', '')}` audit_role=`{doc.get('audit_role', '')}` source_type=`{doc.get('source_type', '')}` title={compact_text(doc.get('title', ''), 120)}"
            )
            lines.append(f"  Excerpt: {compact_text(doc.get('body_excerpt', ''), 420)}")
        lines.extend(["", "Labels to enter in CSV or worksheet:", *label_template(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize_model_actions(actions: Sequence[Mapping[str, Any]]) -> str:
    if not actions:
        return "(none)"
    return " | ".join(
        f"{action.get('action', '')} target={action.get('target', '')}: {compact_text(action.get('rationale', ''), 220)}"
        for action in actions
    )


def summarize_audit_documents(documents: Sequence[Mapping[str, Any]]) -> str:
    parts = []
    for doc in documents:
        parts.append(
            f"{doc.get('doc_id', '')} [{doc.get('audit_role', '')}; {doc.get('source_type', '')}; {doc.get('timestamp', '')}] "
            f"{compact_text(doc.get('title', ''), 100)} -- {compact_text(doc.get('body_excerpt', ''), 260)}"
        )
    return " || ".join(parts)


def write_active_verification_human_audit_worksheet(path: Path, context_rows: Sequence[Mapping[str, Any]]) -> None:
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(context_rows, start=1):
        labels = row.get("human_label_fields", {})
        gold = row.get("gold", {})
        rows.append(
            {
                "row_index": index,
                "audit_status": row.get("audit_status", "needs_human_label"),
                "model": row.get("model", ""),
                "task_id": row.get("task_id", ""),
                "condition": row.get("condition", ""),
                "prompt_condition": row.get("prompt_condition", ""),
                "semantically_useful_action": labels.get("semantically_useful_action", ""),
                "machine_executable_action": labels.get("machine_executable_action", ""),
                "exact_target_present": labels.get("exact_target_present", ""),
                "required_action_type_present": labels.get("required_action_type_present", ""),
                "contradiction_search_needed": labels.get("contradiction_search_needed", ""),
                "primary_search_needed": labels.get("primary_search_needed", ""),
                "trace_source_needed": labels.get("trace_source_needed", ""),
                "scorer_too_strict": labels.get("scorer_too_strict", ""),
                "auditor_notes": labels.get("auditor_notes", ""),
                "question": row.get("question", ""),
                "model_actions": summarize_model_actions(row.get("model_actions", [])),
                "auto_action_gate_pass": row.get("auto_scorer", {}).get("action_gate_pass", ""),
                "auto_missing_primary_action": row.get("auto_scorer", {}).get("missing_primary_action", ""),
                "auto_missing_contradiction_action": row.get("auto_scorer", {}).get("missing_contradiction_action", ""),
                "auto_missing_trace_source_action": row.get("auto_scorer", {}).get("missing_trace_source_action", ""),
                "gold_verdict": gold.get("gold_verdict", ""),
                "primary_doc_ids": ", ".join(gold.get("primary_doc_ids", [])),
                "contradiction_doc_ids": ", ".join(gold.get("contradiction_doc_ids", [])),
                "contaminant_doc_ids": ", ".join(gold.get("contaminant_doc_ids", [])),
                "generated_doc_ids": ", ".join(gold.get("generated_doc_ids", [])),
                "stale_doc_ids": ", ".join(gold.get("stale_doc_ids", [])),
                "documents": summarize_audit_documents(row.get("documents", [])),
            }
        )
    write_csv(path, rows)


def write_active_verification_model_blinded_worksheet(path: Path, context_rows: Sequence[Mapping[str, Any]]) -> None:
    rows: List[Dict[str, Any]] = []
    for index, row in enumerate(context_rows, start=1):
        labels = row.get("human_label_fields", {})
        gold = row.get("gold", {})
        rows.append(
            {
                "row_index": index,
                "audit_status": row.get("audit_status", "needs_human_label"),
                "evidence_condition": row.get("condition", ""),
                "semantically_useful_action": labels.get("semantically_useful_action", ""),
                "machine_executable_action": labels.get("machine_executable_action", ""),
                "exact_target_present": labels.get("exact_target_present", ""),
                "required_action_type_present": labels.get("required_action_type_present", ""),
                "contradiction_search_needed": labels.get("contradiction_search_needed", ""),
                "primary_search_needed": labels.get("primary_search_needed", ""),
                "trace_source_needed": labels.get("trace_source_needed", ""),
                "scorer_too_strict": labels.get("scorer_too_strict", ""),
                "auditor_notes": labels.get("auditor_notes", ""),
                "question": row.get("question", ""),
                "model_actions": summarize_model_actions(row.get("model_actions", [])),
                "gold_verdict": gold.get("gold_verdict", ""),
                "primary_doc_ids": ", ".join(gold.get("primary_doc_ids", [])),
                "contradiction_doc_ids": ", ".join(gold.get("contradiction_doc_ids", [])),
                "contaminant_doc_ids": ", ".join(gold.get("contaminant_doc_ids", [])),
                "generated_doc_ids": ", ".join(gold.get("generated_doc_ids", [])),
                "stale_doc_ids": ", ".join(gold.get("stale_doc_ids", [])),
                "documents": summarize_audit_documents(row.get("documents", [])),
            }
        )
    write_csv(path, rows)


def json_for_script(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")


def write_active_verification_human_audit_review_html(
    path: Path,
    reference_rows: Sequence[Mapping[str, str]],
    context_rows: Sequence[Mapping[str, Any]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape("EHA Active-Verification Human Audit Review")}</title>
  <style>
    :root {{
      color-scheme: light;
      --border: #c8d1dc;
      --muted: #526273;
      --ink: #17202a;
      --bg: #f6f8fa;
      --panel: #ffffff;
      --accent: #1455a6;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font: 14px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }}
    header {{ position: sticky; top: 0; z-index: 2; padding: 12px 16px; border-bottom: 1px solid var(--border); background: var(--panel); }}
    h1 {{ margin: 0 0 4px; font-size: 18px; }}
    h2 {{ margin: 0 0 10px; font-size: 16px; }}
    h3 {{ margin: 12px 0 6px; font-size: 14px; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 16px; }}
    button {{ min-height: 34px; border: 1px solid var(--border); background: #fff; color: var(--ink); border-radius: 6px; padding: 6px 10px; cursor: pointer; }}
    button.primary {{ border-color: var(--accent); background: var(--accent); color: #fff; }}
    button:disabled {{ cursor: not-allowed; opacity: 0.55; }}
    select {{ min-height: 34px; border: 1px solid var(--border); background: #fff; color: var(--ink); border-radius: 6px; padding: 6px 10px; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    .status {{ color: var(--muted); }}
    .status.warn {{ color: #8a4b00; }}
    .status.ok {{ color: #166534; }}
    .row-card {{ margin: 14px 0; padding: 14px; border: 1px solid var(--border); border-radius: 8px; background: var(--panel); }}
    .row-card.incomplete {{ border-color: #d79b35; }}
    .row-card.complete {{ border-color: #89b48b; }}
    .row-card:target {{ outline: 3px solid #9bc2ff; outline-offset: 2px; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 10px; }}
    .pill {{ border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px; background: #eef3f8; color: #253648; }}
    .grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(320px, 0.9fr); gap: 14px; align-items: start; }}
    .label-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 8px; }}
    .label {{ border: 1px solid var(--border); border-radius: 6px; padding: 8px; min-height: 68px; background: #fbfcfe; }}
    .label span {{ display: block; margin-bottom: 6px; font-weight: 600; }}
    .choice {{ display: inline-flex; gap: 4px; align-items: center; margin-right: 10px; }}
    textarea {{ width: 100%; min-height: 72px; resize: vertical; border: 1px solid var(--border); border-radius: 6px; padding: 8px; font: inherit; }}
    pre {{ white-space: pre-wrap; overflow-wrap: anywhere; margin: 0; padding: 8px; border: 1px solid var(--border); border-radius: 6px; background: #f9fbfd; }}
    .doc {{ margin: 8px 0; padding: 8px; border-left: 3px solid var(--border); background: #fbfcfe; }}
    .muted {{ color: var(--muted); }}
    @media (max-width: 820px) {{ .grid {{ grid-template-columns: 1fr; }} header {{ position: static; }} }}
  </style>
</head>
<body>
  <header>
    <h1>EHA Active-Verification Human Audit Review</h1>
    <div class="toolbar">
      <button class="primary" id="download">Download strict CSV</button>
      <button id="save">Save draft in browser</button>
      <button id="load">Load saved draft</button>
      <button id="import-csv">Import strict CSV draft</button>
      <input id="import-file" type="file" accept=".csv,text/csv" hidden>
      <select id="condition-filter" aria-label="Filter rows by evidence condition">
        <option value="">All conditions</option>
      </select>
      <button id="next-incomplete">Next incomplete row</button>
      <span class="status" id="status">0 / 50 rows have all eight binary labels and auditor notes. Download enables after all rows are complete.</span>
      <span class="status" id="visible-status">50 visible rows.</span>
    </div>
  </header>
  <main>
    <p class="muted">Use this page to review the same 50 rows as <code>active_verification_human_audit.csv</code>. The downloaded CSV preserves row order and non-label columns. You can import an existing strict CSV draft, but imports are rejected if row order or non-label metadata changed. Final validation still requires <code>finalize-active-verification-human-audit</code>.</p>
    <div id="rows"></div>
  </main>
  <script>
const referenceRows = {json_for_script(list(reference_rows))};
const contextRows = {json_for_script(list(context_rows))};
const labelFields = {json_for_script(list(HUMAN_AUDIT_LABEL_FIELDS))};
const mutableFields = [...labelFields, "audit_status", "auditor_notes"];
const conditionOrder = [...new Set(contextRows.map(row => row.condition).filter(Boolean))].sort();
const storageKey = "eha-active-verification-human-audit-v1";

function el(tag, attrs = {{}}, text = "") {{
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {{
    if (key === "class") node.className = value;
    else node.setAttribute(key, value);
  }}
  if (text !== "") node.textContent = text;
  return node;
}}

function labelValue(row, field) {{
  const labels = row.human_label_fields || {{}};
  const needs = row.required_action_needs || {{}};
  return labels[field] ?? needs[field] ?? "";
}}

function normalizeBinaryLabel(value) {{
  const text = String(value ?? "").trim().toLowerCase();
  if (text === "") return "";
  if (["1", "1.0", "true", "yes", "y"].includes(text)) return "1";
  if (["0", "0.0", "false", "no", "n"].includes(text)) return "0";
  return null;
}}

function renderRows() {{
  const root = document.getElementById("rows");
  root.innerHTML = "";
  contextRows.forEach((row, index) => {{
    const card = el("section", {{ class: "row-card", id: `row-${{index + 1}}` }});
    card.dataset.condition = row.condition || "";
    card.appendChild(el("h2", {{}}, `Row ${{String(index + 1).padStart(2, "0")}}: ${{row.task_id}} / ${{row.model}}`));
    const meta = el("div", {{ class: "meta" }});
    [row.condition, row.prompt_condition, `gold=${{row.gold?.gold_verdict || ""}}`, `auto_gate=${{row.auto_scorer?.action_gate_pass || ""}}`].forEach(value => meta.appendChild(el("span", {{ class: "pill" }}, value)));
    card.appendChild(meta);
    const grid = el("div", {{ class: "grid" }});
    const left = el("div");
    left.appendChild(el("h3", {{}}, "Question"));
    left.appendChild(el("pre", {{}}, row.question || ""));
    left.appendChild(el("h3", {{}}, "Model Actions"));
    const actions = row.model_actions || [];
    left.appendChild(el("pre", {{}}, actions.length ? actions.map(action => `${{action.action || ""}} target=${{action.target || ""}}: ${{action.rationale || ""}}`).join("\\n") : "(none)"));
    left.appendChild(el("h3", {{}}, "Gold Context"));
    left.appendChild(el("pre", {{}}, JSON.stringify(row.gold || {{}}, null, 2)));
    const right = el("div");
    right.appendChild(el("h3", {{}}, "Labels"));
    const labelGrid = el("div", {{ class: "label-grid" }});
    labelFields.forEach(field => {{
      const box = el("label", {{ class: "label" }});
      box.appendChild(el("span", {{}}, field));
      ["1", "0"].forEach(value => {{
        const choice = el("label", {{ class: "choice" }});
        const input = el("input", {{ type: "radio", name: `${{index}}-${{field}}`, value, "data-row": index, "data-field": field }});
        if (String(labelValue(row, field)) === value || String(labelValue(row, field)) === `${{value}}.0`) input.checked = true;
        input.addEventListener("change", updateStatus);
        choice.appendChild(input);
        choice.appendChild(document.createTextNode(value));
        box.appendChild(choice);
      }});
      labelGrid.appendChild(box);
    }});
    right.appendChild(labelGrid);
    right.appendChild(el("h3", {{}}, "Auditor Notes"));
    const notes = el("textarea", {{ "data-row": index, "data-field": "auditor_notes", placeholder: "Short reason for the judgment" }});
    notes.value = labelValue(row, "auditor_notes") || "";
    notes.addEventListener("input", updateStatus);
    right.appendChild(notes);
    grid.appendChild(left);
    grid.appendChild(right);
    card.appendChild(grid);
    card.appendChild(el("h3", {{}}, "Documents"));
    (row.documents || []).forEach(doc => {{
      const docBox = el("div", {{ class: "doc" }});
      docBox.appendChild(el("strong", {{}}, `${{doc.doc_id}} [${{doc.audit_role}}; ${{doc.source_type}}; ${{doc.timestamp}}] ${{doc.title}}`));
      docBox.appendChild(el("p", {{}}, doc.body_excerpt || ""));
      card.appendChild(docBox);
    }});
    root.appendChild(card);
  }});
  updateStatus();
}}

function collectRows() {{
  return referenceRows.map((row, index) => {{
    const next = {{ ...row }};
    next.audit_status = "human_labeled";
    labelFields.forEach(field => {{
      const checked = document.querySelector(`input[name="${{index}}-${{field}}"]:checked`);
      next[field] = checked ? checked.value : "";
    }});
    const notes = document.querySelector(`textarea[data-row="${{index}}"][data-field="auditor_notes"]`);
    next.auditor_notes = notes ? notes.value : "";
    return next;
  }});
}}

function rowHasCompleteLabels(row) {{
  return labelFields.every(field => row[field] === "0" || row[field] === "1") && String(row.auditor_notes || "").trim() !== "";
}}

function csvEscape(value) {{
  const text = String(value ?? "");
  if (/[",\\n\\r]/.test(text)) return `"${{text.replaceAll('"', '""')}}"`;
  return text;
}}

function toCsv(rows) {{
  const headers = Object.keys(referenceRows[0] || {{}});
  return [headers.join(","), ...rows.map(row => headers.map(header => csvEscape(row[header])).join(","))].join("\\n") + "\\n";
}}

function updateStatus() {{
  const rows = collectRows();
  const complete = rows.filter(rowHasCompleteLabels).length;
  const download = document.getElementById("download");
  const status = document.getElementById("status");
  download.disabled = complete !== rows.length;
  status.className = complete === rows.length ? "status ok" : "status warn";
  status.textContent = `${{complete}} / ${{rows.length}} rows have all eight binary labels and auditor notes. Download enables after all rows are complete.`;
  document.querySelectorAll(".row-card").forEach((card, index) => {{
    const rowComplete = rowHasCompleteLabels(rows[index]);
    card.classList.toggle("complete", rowComplete);
    card.classList.toggle("incomplete", !rowComplete);
  }});
  applyConditionFilter();
}}

function setupConditionFilter() {{
  const filter = document.getElementById("condition-filter");
  conditionOrder.forEach(condition => {{
    const option = el("option", {{ value: condition }}, condition);
    filter.appendChild(option);
  }});
  filter.addEventListener("change", applyConditionFilter);
}}

function applyConditionFilter() {{
  const filter = document.getElementById("condition-filter");
  const selected = filter ? filter.value : "";
  let visible = 0;
  document.querySelectorAll(".row-card").forEach(card => {{
    const show = !selected || card.dataset.condition === selected;
    card.hidden = !show;
    if (show) visible += 1;
  }});
  const visibleStatus = document.getElementById("visible-status");
  if (visibleStatus) {{
    visibleStatus.textContent = selected ? `${{visible}} visible rows for ${{selected}}.` : `${{visible}} visible rows.`;
  }}
}}

function goToNextIncomplete() {{
  const rows = collectRows();
  const cards = [...document.querySelectorAll(".row-card")];
  const target = cards.find((card, index) => !card.hidden && !rowHasCompleteLabels(rows[index]));
  if (!target) {{
    alert("No incomplete rows in the current filter.");
    return;
  }}
  target.scrollIntoView({{ behavior: "smooth", block: "start" }});
  history.replaceState(null, "", `#${{target.id}}`);
}}

function parseStrictCsv(text) {{
  const rawRows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let index = 0; index < text.length; index += 1) {{
    const char = text[index];
    const next = text[index + 1];
    if (inQuotes) {{
      if (char === '"' && next === '"') {{
        field += '"';
        index += 1;
      }} else if (char === '"') {{
        inQuotes = false;
      }} else {{
        field += char;
      }}
    }} else if (char === '"') {{
      inQuotes = true;
    }} else if (char === ",") {{
      row.push(field);
      field = "";
    }} else if (char === "\\n") {{
      row.push(field);
      rawRows.push(row);
      row = [];
      field = "";
    }} else if (char !== "\\r") {{
      field += char;
    }}
  }}
  if (field !== "" || row.length > 0) {{
    row.push(field);
    rawRows.push(row);
  }}
  const headers = rawRows.shift() || [];
  return rawRows
    .filter(values => values.some(value => value !== ""))
    .map(values => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""])));
}}

function validateImportedRows(rows) {{
  const headers = Object.keys(referenceRows[0] || {{}});
  const first = rows[0] || {{}};
  const missing = headers.filter(header => !(header in first));
  if (missing.length) throw new Error(`imported CSV is missing required columns: ${{missing.join(", ")}}`);
  if (rows.length !== referenceRows.length) throw new Error(`imported row count does not match reference row count: imported=${{rows.length}} reference=${{referenceRows.length}}`);
  const fixedFields = headers.filter(header => !mutableFields.includes(header));
  rows.forEach((row, index) => {{
    const reference = referenceRows[index] || {{}};
    fixedFields.forEach(field => {{
      if (String(row[field] ?? "") !== String(reference[field] ?? "")) {{
        throw new Error(`imported row ${{index + 1}} changed non-label field: ${{field}}`);
      }}
    }});
    labelFields.forEach(field => {{
      if (normalizeBinaryLabel(row[field]) === null) {{
        throw new Error(`imported row ${{index + 1}} has invalid binary label: ${{field}}`);
      }}
    }});
  }});
  return rows;
}}

function applyDraftRows(rows) {{
  rows.forEach((row, index) => {{
    labelFields.forEach(field => {{
      const value = normalizeBinaryLabel(row[field]);
      const input = document.querySelector(`input[name="${{index}}-${{field}}"][value="${{value}}"]`);
      if (input) input.checked = true;
    }});
    const notes = document.querySelector(`textarea[data-row="${{index}}"][data-field="auditor_notes"]`);
    if (notes) notes.value = row.auditor_notes || "";
  }});
  updateStatus();
}}

document.getElementById("download").addEventListener("click", () => {{
  const rows = collectRows();
  if (!rows.every(rowHasCompleteLabels)) {{
    alert("Complete all eight binary labels and auditor notes for all rows before downloading the strict CSV.");
    updateStatus();
    return;
  }}
  const blob = new Blob([toCsv(rows)], {{ type: "text/csv;charset=utf-8" }});
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "active_verification_human_audit.csv";
  link.click();
  URL.revokeObjectURL(link.href);
}});
document.getElementById("save").addEventListener("click", () => {{
  localStorage.setItem(storageKey, JSON.stringify(collectRows().map(row => Object.fromEntries(mutableFields.map(field => [field, row[field] || ""])))));
  updateStatus();
}});
document.getElementById("load").addEventListener("click", () => {{
  const draft = JSON.parse(localStorage.getItem(storageKey) || "[]");
  applyDraftRows(draft);
}});
document.getElementById("import-csv").addEventListener("click", () => {{
  document.getElementById("import-file").click();
}});
document.getElementById("import-file").addEventListener("change", event => {{
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  file.text()
    .then(text => {{
      applyDraftRows(validateImportedRows(parseStrictCsv(text)));
    }})
    .catch(error => {{
      alert(`Could not import strict CSV draft: ${{error.message}}`);
    }})
    .finally(() => {{
      event.target.value = "";
    }});
}});
document.getElementById("next-incomplete").addEventListener("click", goToNextIncomplete);

setupConditionFilter();
renderRows();
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def build_active_verification_audit_package(*, sample_csv: Path, task_dir: Path, out_dir: Path) -> None:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    task_by_id = {task.task_id: task for task in tasks}
    rows = read_csv_rows(sample_csv)
    out_dir.mkdir(parents=True, exist_ok=True)
    context_rows = [active_verification_context_row(row, task_by_id) for row in rows]
    write_jsonl(out_dir / "active_verification_pilot_human_audit_context_50.jsonl", context_rows)
    write_active_verification_guidelines(out_dir / "active_verification_human_audit_guidelines.md")
    write_active_verification_human_audit_protocol(out_dir / "active_verification_human_audit_protocol.md")
    write_active_verification_human_audit_readme(out_dir / "active_verification_human_audit_readme.md")
    write_active_verification_human_audit_reviewer_brief(out_dir / "active_verification_human_audit_reviewer_brief.md")
    write_active_verification_human_audit_attestation(out_dir / "active_verification_human_audit_attestation.md")
    write_active_verification_manual_packet(out_dir / "active_verification_pilot_human_audit_packet_50.md", context_rows)
    write_active_verification_model_blinded_packet(out_dir / "active_verification_pilot_human_audit_model_blinded_packet_50.md", context_rows)
    write_active_verification_human_audit_worksheet(out_dir / "active_verification_pilot_human_audit_worksheet_50.csv", context_rows)
    write_active_verification_model_blinded_worksheet(out_dir / "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv", context_rows)
    write_active_verification_human_audit_review_html(out_dir / "active_verification_human_audit_review.html", rows, context_rows)
    write_json(
        out_dir / "active_verification_human_audit_manifest.json",
        {
            "sample_csv": str(sample_csv),
            "context_rows": len(context_rows),
            "manual_packet": "active_verification_pilot_human_audit_packet_50.md",
            "worksheet": "active_verification_pilot_human_audit_worksheet_50.csv",
            "model_blinded_worksheet": "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv",
            "protocol": "active_verification_human_audit_protocol.md",
            "attestation": "active_verification_human_audit_attestation.md",
            "review_html": "active_verification_human_audit_review.html",
            "label_status": "needs_human_labels",
            "label_fields": [
                "semantically_useful_action",
                "machine_executable_action",
                "exact_target_present",
                "required_action_type_present",
                "contradiction_search_needed",
                "primary_search_needed",
                "trace_source_needed",
                "scorer_too_strict",
            ],
            "model_blinded_packet": "active_verification_pilot_human_audit_model_blinded_packet_50.md",
            "paper_update_md": "active_verification_pilot_human_audit_paper_update.md",
        },
    )


def parse_label(value: str) -> float | None:
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return 1.0
    if normalized in {"0", "false", "no", "n"}:
        return 0.0
    try:
        numeric = float(normalized)
    except ValueError:
        return None
    if numeric == 1.0:
        return 1.0
    if numeric == 0.0:
        return 0.0
    return None


def mean_label(rows: Sequence[Mapping[str, str]], field: str) -> float | str:
    values = [value for row in rows if (value := parse_label(row.get(field, ""))) is not None]
    return sum(values) / len(values) if values else ""


def parse_float(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def mean_numeric(rows: Sequence[Mapping[str, str]], field: str) -> float | None:
    values = [value for row in rows if (value := parse_float(row.get(field, ""))) is not None]
    return sum(values) / len(values) if values else None


def format_metric(value: float | None) -> str:
    return "" if value is None else f"{value:.3f}"


def format_count(value: float | None) -> str:
    return "" if value is None else str(int(value))


def wilson_interval(successes: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return 0.0, 0.0
    phat = successes / n
    denominator = 1.0 + (z * z / n)
    center = phat + (z * z / (2.0 * n))
    margin = z * ((phat * (1.0 - phat) + (z * z / (4.0 * n))) / n) ** 0.5
    return (center - margin) / denominator, (center + margin) / denominator


def summarize_group(rows: Sequence[Mapping[str, str]], grouping: str, group_value: str) -> Dict[str, Any]:
    labeled = [row for row in rows if row.get("audit_status") == "human_labeled" or parse_label(row.get("semantically_useful_action", "")) is not None]
    return {
        "grouping": grouping,
        "group": group_value,
        "n_rows": len(rows),
        "n_labeled": len(labeled),
        "semantically_useful_action_rate": mean_label(labeled, "semantically_useful_action"),
        "machine_executable_action_rate": mean_label(labeled, "machine_executable_action"),
        "exact_target_present_rate": mean_label(labeled, "exact_target_present"),
        "required_action_type_present_rate": mean_label(labeled, "required_action_type_present"),
        "contradiction_search_needed_rate": mean_label(labeled, "contradiction_search_needed"),
        "primary_search_needed_rate": mean_label(labeled, "primary_search_needed"),
        "trace_source_needed_rate": mean_label(labeled, "trace_source_needed"),
        "scorer_too_strict_rate": mean_label(labeled, "scorer_too_strict"),
    }


def write_active_verification_human_audit_paper_update(
    *,
    path: Path,
    labels_csv: Path,
    rows: Sequence[Mapping[str, str]],
    status: str,
    summary_csv: str,
) -> None:
    labeled = [row for row in rows if row.get("audit_status") == "human_labeled" or parse_label(row.get("semantically_useful_action", "")) is not None]
    human_labeled = [row for row in rows if row.get("audit_status") == "human_labeled"]
    denominator = len(rows)
    counts = {
        "semantically_useful_action": sum(1 for row in rows if parse_label(row.get("semantically_useful_action", "")) == 1.0),
        "machine_executable_action": sum(1 for row in rows if parse_label(row.get("machine_executable_action", "")) == 1.0),
        "exact_target_present": sum(1 for row in rows if parse_label(row.get("exact_target_present", "")) == 1.0),
        "required_action_type_present": sum(1 for row in rows if parse_label(row.get("required_action_type_present", "")) == 1.0),
        "scorer_too_strict": sum(1 for row in rows if parse_label(row.get("scorer_too_strict", "")) == 1.0),
    }
    lines = [
        "# Active-Verification Human-Audit Paper Update",
        "",
        "This memo is generated from the human-audit label CSV. It is a writing aid, not a substitute for the validation report.",
        "",
        "## Status",
        "",
        f"- labels_csv: `{labels_csv}`",
        f"- summary_csv: `{summary_csv}`",
        f"- status: `{status}`",
        f"- n_rows: {denominator}",
        f"- n_labeled: {len(labeled)}",
        f"- n_human_labeled: {len(human_labeled)}",
        "",
        "## Counts",
        "",
        f"- semantically_useful_action: {counts['semantically_useful_action']}/{denominator}",
        f"- machine_executable_action: {counts['machine_executable_action']}/{denominator}",
        f"- exact_target_present: {counts['exact_target_present']}/{denominator}",
        f"- required_action_type_present: {counts['required_action_type_present']}/{denominator}",
        f"- scorer_too_strict: {counts['scorer_too_strict']}/{denominator}",
        "",
        "## Claim Boundary",
        "",
    ]
    if status == "complete" and denominator and len(human_labeled) == denominator:
        lines.extend(
            [
                "Paper-ready sentence after the independent human audit is complete:",
                "",
                (
                    "A single-auditor pilot human audit reports the human-labeled active-verification audit separately from "
                    f"Codex-assisted triage: {counts['semantically_useful_action']}/{denominator} as semantically useful, "
                    f"{counts['machine_executable_action']}/{denominator} as machine executable, "
                    f"{counts['required_action_type_present']}/{denominator} as containing the required action type, "
                    f"and {counts['scorer_too_strict']}/{denominator} automatic rejections as plausibly too strict."
                ),
                "",
                "Keep the Codex-assisted triage counts in a separate sentence and do not merge them with the human-labeled counts.",
            ]
        )
    else:
        lines.extend(
            [
                "Do not use this memo to make completed human-audit claims yet.",
                "",
                "The current human audit is incomplete or not fully marked `human_labeled`, and is not human validation. Keep the paper wording that treats the Codex-assisted audit as triage only until validation reports `status = complete` and all 50 rows are human-labeled.",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_active_verification_human_audit(
    *,
    labels_csv: Path,
    out_dir: Path,
    output_stem: str = "active_verification_pilot_human_audit_summary",
) -> None:
    rows = read_csv_rows(labels_csv)
    summaries = [summarize_group(rows, "overall", "all")]
    by_condition: Dict[str, List[Mapping[str, str]]] = defaultdict(list)
    by_model: Dict[str, List[Mapping[str, str]]] = defaultdict(list)
    for row in rows:
        by_condition[row.get("condition", "")].append(row)
        by_model[row.get("model", "")].append(row)
    summaries.extend(summarize_group(group, "condition", condition) for condition, group in sorted(by_condition.items()))
    summaries.extend(summarize_group(group, "model", model) for model, group in sorted(by_model.items()))
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = f"{output_stem}.csv"
    update_stem = output_stem[: -len("_summary")] if output_stem.endswith("_summary") else output_stem
    paper_update_md = f"{update_stem}_paper_update.md"
    status = "complete" if summaries[0]["n_labeled"] == len(rows) and rows else "incomplete"
    write_csv(out_dir / summary_csv, summaries)
    write_json(
        out_dir / f"{output_stem}.json",
        {
            "labels_csv": str(labels_csv),
            "n_rows": len(rows),
            "n_labeled": summaries[0]["n_labeled"],
            "status": status,
            "summary_csv": summary_csv,
            "paper_update_md": paper_update_md,
        },
    )
    write_active_verification_human_audit_paper_update(
        path=out_dir / paper_update_md,
        labels_csv=labels_csv,
        rows=rows,
        status=status,
        summary_csv=summary_csv,
    )


HUMAN_AUDIT_LABEL_FIELDS = [
    "semantically_useful_action",
    "machine_executable_action",
    "exact_target_present",
    "required_action_type_present",
    "contradiction_search_needed",
    "primary_search_needed",
    "trace_source_needed",
    "scorer_too_strict",
]


HUMAN_AUDIT_MUTABLE_FIELDS = set(HUMAN_AUDIT_LABEL_FIELDS) | {"audit_status", "auditor_notes"}


def row_key(row: Mapping[str, str]) -> str:
    return "/".join(row.get(field, "") for field in ["model", "task_id", "condition", "prompt_condition"])


def validate_active_verification_human_audit(
    *,
    labels_csv: Path,
    reference_csv: Path,
    out_dir: Path,
    output_stem: str = "active_verification_pilot_human_audit_validation",
) -> Dict[str, Any]:
    rows = read_csv_rows(labels_csv)
    reference_rows = read_csv_rows(reference_csv)
    errors: List[str] = []
    warnings: List[str] = []
    row_reports: List[Dict[str, Any]] = []
    if len(rows) != len(reference_rows):
        errors.append(f"row count mismatch: labels={len(rows)} reference={len(reference_rows)}")
    label_fields = set(HUMAN_AUDIT_LABEL_FIELDS)
    expected_fields = set(reference_rows[0]) if reference_rows else set()
    actual_fields = set(rows[0]) if rows else set()
    if expected_fields and actual_fields != expected_fields:
        errors.append(f"column mismatch: missing={sorted(expected_fields - actual_fields)} extra={sorted(actual_fields - expected_fields)}")
    for index, row in enumerate(rows, start=1):
        reference = reference_rows[index - 1] if index <= len(reference_rows) else {}
        row_errors: List[str] = []
        row_warnings: List[str] = []
        if reference:
            if row_key(row) != row_key(reference):
                row_errors.append("row key changed or row order mismatch")
            for field, reference_value in reference.items():
                if field in HUMAN_AUDIT_MUTABLE_FIELDS:
                    continue
                if row.get(field, "") != reference_value:
                    row_errors.append(f"non-label field changed: {field}")
        for field in HUMAN_AUDIT_LABEL_FIELDS:
            if field not in row:
                row_errors.append(f"missing label field: {field}")
            elif parse_label(row.get(field, "")) is None:
                row_errors.append(f"unlabeled or invalid label: {field}")
        if row.get("audit_status") != "human_labeled":
            row_errors.append("audit_status is not human_labeled")
        if not row.get("auditor_notes", "").strip():
            row_errors.append("auditor_notes is blank")
        row_reports.append(
            {
                "row_index": index,
                "row_key": row_key(row),
                "complete": not row_errors,
                "errors": "; ".join(row_errors),
                "warnings": "; ".join(row_warnings),
            }
        )
    complete_rows = sum(1 for row in row_reports if row["complete"])
    row_error_count = sum(1 for row in row_reports if row["errors"])
    row_warning_count = sum(1 for row in row_reports if row["warnings"])
    if row_error_count:
        errors.append(f"{row_error_count} row(s) failed validation")
    if row_warning_count:
        warnings.append(f"{row_warning_count} row(s) have warnings")
    status = "complete" if rows and complete_rows == len(rows) and not errors else "incomplete"
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / f"{output_stem}_rows.csv", row_reports)
    report = {
        "labels_csv": str(labels_csv),
        "reference_csv": str(reference_csv),
        "labels_sha256": file_sha256(labels_csv) if labels_csv.exists() else "",
        "reference_sha256": file_sha256(reference_csv) if reference_csv.exists() else "",
        "n_rows": len(rows),
        "reference_rows": len(reference_rows),
        "n_complete_rows": complete_rows,
        "status": status,
        "label_fields": HUMAN_AUDIT_LABEL_FIELDS,
        "errors": errors,
        "warnings": warnings,
        "row_report_csv": f"{output_stem}_rows.csv",
    }
    write_json(out_dir / f"{output_stem}.json", report)
    (out_dir / f"{output_stem}.md").write_text(
        "\n".join(
            [
                "# Active-Verification Human-Audit Validation",
                "",
                f"- status: `{status}`",
                f"- rows: `{len(rows)}`",
                f"- complete rows: `{complete_rows}`",
                f"- errors: `{len(errors)}`",
                f"- warnings: `{len(warnings)}`",
                "",
                "## Errors",
                "",
                *(f"- {error}" for error in errors),
                "" if errors else "- none",
                "",
                "## Warnings",
                "",
                *(f"- {warning}" for warning in warnings),
                "" if warnings else "- none",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return report


def import_active_verification_human_audit_worksheet(
    *,
    worksheet_csv: Path,
    reference_csv: Path,
    out_csv: Path,
) -> Dict[str, Any]:
    worksheet_rows = read_csv_rows(worksheet_csv)
    reference_rows = read_csv_rows(reference_csv)
    errors: List[str] = []
    if len(worksheet_rows) != len(reference_rows):
        errors.append(f"row count mismatch: worksheet={len(worksheet_rows)} reference={len(reference_rows)}")
    imported_rows: List[Dict[str, str]] = []
    for index, reference in enumerate(reference_rows, start=1):
        worksheet = worksheet_rows[index - 1] if index <= len(worksheet_rows) else {}
        if worksheet and row_key(worksheet) != row_key(reference):
            errors.append(f"row {index} key changed or row order mismatch: worksheet={row_key(worksheet)} reference={row_key(reference)}")
        imported = dict(reference)
        for field in HUMAN_AUDIT_MUTABLE_FIELDS:
            if field in imported:
                imported[field] = worksheet.get(field, imported.get(field, ""))
        imported_rows.append(imported)
    if errors:
        raise ValueError("; ".join(errors[:5]))
    write_csv(out_csv, imported_rows)
    return {
        "status": "imported",
        "worksheet_csv": str(worksheet_csv),
        "reference_csv": str(reference_csv),
        "out_csv": str(out_csv),
        "n_rows": len(imported_rows),
    }


def import_active_verification_model_blinded_human_audit_worksheet(
    *,
    worksheet_csv: Path,
    reference_csv: Path,
    out_csv: Path,
) -> Dict[str, Any]:
    worksheet_rows = read_csv_rows(worksheet_csv)
    reference_rows = read_csv_rows(reference_csv)
    errors: List[str] = []
    if len(worksheet_rows) != len(reference_rows):
        errors.append(f"row count mismatch: worksheet={len(worksheet_rows)} reference={len(reference_rows)}")
    required_columns = {"row_index", *HUMAN_AUDIT_MUTABLE_FIELDS}
    worksheet_columns = set(worksheet_rows[0]) if worksheet_rows else set()
    errors.extend(f"model-blinded worksheet missing column: {column}" for column in sorted(required_columns - worksheet_columns))
    forbidden_columns = {
        "model",
        "task_id",
        "prompt_condition",
        "auto_action_gate_pass",
        "auto_missing_primary_action",
        "auto_missing_contradiction_action",
        "auto_missing_trace_source_action",
        "auto_actions_visible_ids",
    }
    errors.extend(f"model-blinded worksheet exposes forbidden column: {column}" for column in sorted(forbidden_columns & worksheet_columns))
    imported_rows: List[Dict[str, str]] = []
    for index, reference in enumerate(reference_rows, start=1):
        worksheet = worksheet_rows[index - 1] if index <= len(worksheet_rows) else {}
        raw_index = str(worksheet.get("row_index", "")).strip() if worksheet else ""
        try:
            worksheet_index = int(float(raw_index))
        except ValueError:
            worksheet_index = -1
        if worksheet and worksheet_index != index:
            errors.append(f"row {index} row_index mismatch: worksheet={raw_index or 'blank'} reference={index}")
        imported = dict(reference)
        for field in HUMAN_AUDIT_MUTABLE_FIELDS:
            if field in imported:
                imported[field] = worksheet.get(field, imported.get(field, ""))
        imported_rows.append(imported)
    if errors:
        raise ValueError("; ".join(errors[:5]))
    write_csv(out_csv, imported_rows)
    return {
        "status": "imported",
        "worksheet_csv": str(worksheet_csv),
        "reference_csv": str(reference_csv),
        "out_csv": str(out_csv),
        "n_rows": len(imported_rows),
    }


def finalize_active_verification_human_audit(
    *,
    labels_csv: Path,
    reference_csv: Path,
    out_dir: Path,
    require_complete: bool = True,
) -> Dict[str, Any]:
    report = validate_active_verification_human_audit(labels_csv=labels_csv, reference_csv=reference_csv, out_dir=out_dir)
    if report["status"] != "complete":
        if require_complete:
            raise ValueError(f"human audit validation is {report['status']}; labels were not imported")
        return {"status": "not_imported", "validation": report}
    imported_csv = out_dir / "active_verification_pilot_human_audit_labeled_50.csv"
    copy_if_exists(labels_csv, imported_csv)
    stable_report = validate_active_verification_human_audit(labels_csv=imported_csv, reference_csv=reference_csv, out_dir=out_dir)
    summarize_active_verification_human_audit(labels_csv=imported_csv, out_dir=out_dir)
    manifest = {
        "status": "complete",
        "source_labels_csv": str(labels_csv),
        "imported_labels_csv": imported_csv.name,
        "reference_csv": str(reference_csv),
        "validation_status": stable_report["status"],
        "n_complete_rows": stable_report["n_complete_rows"],
        "summary_json": "active_verification_pilot_human_audit_summary.json",
        "paper_update_md": "active_verification_pilot_human_audit_paper_update.md",
    }
    write_json(out_dir / "active_verification_pilot_human_audit_finalize_manifest.json", manifest)
    return manifest


def build_artifact_package(
    *,
    task_dir: Path,
    frontier_main_dir: Path,
    baseline_dir: Path,
    generated_lore_dir: Path,
    active_verification_dir: Path,
    out_dir: Path,
) -> None:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    maps_by_task = visible_doc_id_maps(tasks)
    out_dir.mkdir(parents=True, exist_ok=True)
    opaque_tasks = [opaque_task_payload(task) for task in tasks]
    documents = [
        {"task_id": task["task_id"], **doc}
        for task in opaque_tasks
        for doc in task["documents"]
    ]
    gold_labels = [visible_gold_label(task) for task in tasks]
    write_jsonl(out_dir / "data" / "tasks_opaque.jsonl", opaque_tasks)
    write_jsonl(out_dir / "data" / "documents_opaque.jsonl", documents)
    write_jsonl(out_dir / "data" / "gold_labels.jsonl", gold_labels)
    write_prompt_templates(out_dir, tasks[0])
    write_minimal_scorer(out_dir / "scorer" / "scoring_contract.py")
    (out_dir / "scorer" / "README.md").write_text(
        "The minimal scorer documents the operational escape formula for a single opaque task. Full paper scoring is implemented in `eha.epistemic_resilience`.\n",
        encoding="utf-8",
    )
    sanitize_jsonl_doc_ids(frontier_main_dir / "predictions.jsonl", out_dir / "outputs" / "frontier_main_opaque_predictions.jsonl", maps_by_task)
    sanitize_csv_doc_ids(frontier_main_dir / "frontier_main_scored_predictions.csv", out_dir / "outputs" / "frontier_main_opaque_scored.csv", maps_by_task)
    copy_if_exists(frontier_main_dir / "run_manifest.json", out_dir / "outputs" / "frontier_main_opaque_run_manifest.json")
    copy_if_exists(frontier_main_dir / "report_manifest.json", out_dir / "outputs" / "frontier_main_opaque_report_manifest.json")
    for path in sorted(baseline_dir.glob("*_baseline.csv")):
        name = path.name.removesuffix("_baseline.csv")
        sanitize_csv_doc_ids(path, out_dir / "baselines" / f"{name}.csv", maps_by_task)
    copy_if_exists(frontier_main_dir / "opaque_full_prompt_artifact_audit_summary.json", out_dir / "audits" / "opaque_prompt_audit_summary.json")
    generated_lore_schema_summary = generated_lore_dir / "generated_lore_schema_ablation_4variant.csv"
    if not generated_lore_schema_summary.exists():
        generated_lore_schema_summary = generated_lore_dir / "schema_clarification_mini_rerun.csv"
    copy_if_exists(generated_lore_schema_summary, out_dir / "audits" / "generated_lore_schema_ablation.csv")
    generated_lore_schema_rows = generated_lore_dir / "generated_lore_schema_ablation_4variant_rows.csv"
    if not generated_lore_schema_rows.exists():
        generated_lore_schema_rows = generated_lore_dir / "schema_clarification_mini_rerun_rows.csv"
    sanitize_csv_doc_ids(generated_lore_schema_rows, out_dir / "audits" / "generated_lore_schema_ablation_rows.csv", maps_by_task)
    copy_if_exists(active_verification_dir / "active_verification_action_audit_summary.csv", out_dir / "audits" / "active_verification_action_audit_summary.csv")
    human_audit_source = active_verification_dir / "active_verification_pilot_human_audit_labeled_50.csv"
    if not human_audit_source.exists():
        human_audit_source = active_verification_dir / "active_verification_pilot_human_audit_sample_50.csv"
    copy_if_exists(human_audit_source, out_dir / "audits" / "active_verification_human_audit.csv")
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_labeled_50.csv", out_dir / "audits" / "active_verification_pilot_human_audit_labeled_50.csv")
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_sample_50.csv", out_dir / "audits" / "active_verification_pilot_human_audit_sample_50.csv")
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_context_50.jsonl", out_dir / "audits" / "active_verification_pilot_human_audit_context_50.jsonl")
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_packet_50.md", out_dir / "audits" / "active_verification_pilot_human_audit_packet_50.md")
    model_blinded_packet_source = active_verification_dir / "active_verification_pilot_human_audit_model_blinded_packet_50.md"
    if model_blinded_packet_source.exists():
        copy_if_exists(model_blinded_packet_source, out_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_packet_50.md")
    else:
        context_source = active_verification_dir / "active_verification_pilot_human_audit_context_50.jsonl"
        if context_source.exists():
            write_active_verification_model_blinded_packet(
                out_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_packet_50.md",
                list(read_jsonl(context_source)),
            )
    review_source = active_verification_dir / "active_verification_human_audit_review.html"
    context_source = active_verification_dir / "active_verification_pilot_human_audit_context_50.jsonl"
    if human_audit_source.exists() and context_source.exists():
        write_active_verification_human_audit_review_html(
            out_dir / "audits" / "active_verification_human_audit_review.html",
            read_csv_rows(human_audit_source),
            list(read_jsonl(context_source)),
        )
    elif review_source.exists():
        copy_if_exists(review_source, out_dir / "audits" / "active_verification_human_audit_review.html")
    worksheet_source = active_verification_dir / "active_verification_pilot_human_audit_worksheet_50.csv"
    if worksheet_source.exists():
        copy_if_exists(worksheet_source, out_dir / "audits" / "active_verification_pilot_human_audit_worksheet_50.csv")
    else:
        context_source = active_verification_dir / "active_verification_pilot_human_audit_context_50.jsonl"
        if context_source.exists():
            write_active_verification_human_audit_worksheet(
                out_dir / "audits" / "active_verification_pilot_human_audit_worksheet_50.csv",
                list(read_jsonl(context_source)),
            )
    model_blinded_worksheet_source = active_verification_dir / "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv"
    if model_blinded_worksheet_source.exists():
        copy_if_exists(model_blinded_worksheet_source, out_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv")
    else:
        context_source = active_verification_dir / "active_verification_pilot_human_audit_context_50.jsonl"
        if context_source.exists():
            write_active_verification_model_blinded_worksheet(
                out_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv",
                list(read_jsonl(context_source)),
            )
    copy_if_exists(active_verification_dir / "active_verification_human_audit_manifest.json", out_dir / "audits" / "active_verification_human_audit_manifest.json")
    copy_if_exists(active_verification_dir / "active_verification_human_audit_guidelines.md", out_dir / "audits" / "active_verification_human_audit_guidelines.md")
    write_active_verification_guidelines(out_dir / "audits" / "active_verification_human_audit_guidelines.md")
    protocol_source = active_verification_dir / "active_verification_human_audit_protocol.md"
    if protocol_source.exists():
        copy_if_exists(protocol_source, out_dir / "audits" / "active_verification_human_audit_protocol.md")
    else:
        write_active_verification_human_audit_protocol(out_dir / "audits" / "active_verification_human_audit_protocol.md")
    write_active_verification_human_audit_protocol(out_dir / "audits" / "active_verification_human_audit_protocol.md")
    human_audit_readme = active_verification_dir / "active_verification_human_audit_readme.md"
    if human_audit_readme.exists():
        copy_if_exists(human_audit_readme, out_dir / "audits" / "active_verification_human_audit_readme.md")
    else:
        write_active_verification_human_audit_readme(out_dir / "audits" / "active_verification_human_audit_readme.md")
    write_active_verification_human_audit_readme(out_dir / "audits" / "active_verification_human_audit_readme.md")
    write_active_verification_human_audit_reviewer_brief(
        out_dir / "audits" / "active_verification_human_audit_reviewer_brief.md"
    )
    attestation_source = active_verification_dir / "active_verification_human_audit_attestation.md"
    attestation_target = out_dir / "audits" / "active_verification_human_audit_attestation.md"
    if attestation_source.exists():
        preserve_existing_completed_attestation = False
        if attestation_target.exists():
            try:
                source_text = attestation_source.read_text(encoding="utf-8", errors="replace")
                target_text = attestation_target.read_text(encoding="utf-8", errors="replace")
                preserve_existing_completed_attestation = (
                    STEP1_HUMAN_AUDIT_ATTESTATION_PLACEHOLDER in source_text
                    and STEP1_HUMAN_AUDIT_ATTESTATION_PLACEHOLDER not in target_text
                )
            except OSError:
                preserve_existing_completed_attestation = False
        if not preserve_existing_completed_attestation:
            copy_if_exists(attestation_source, attestation_target)
    elif not attestation_target.exists():
        write_active_verification_human_audit_attestation(attestation_target)
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_summary.csv", out_dir / "audits" / "active_verification_pilot_human_audit_summary.csv")
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_summary.json", out_dir / "audits" / "active_verification_pilot_human_audit_summary.json")
    paper_update_source = active_verification_dir / "active_verification_pilot_human_audit_paper_update.md"
    if paper_update_source.exists():
        copy_if_exists(paper_update_source, out_dir / "audits" / "active_verification_pilot_human_audit_paper_update.md")
    elif human_audit_source.exists():
        write_active_verification_human_audit_paper_update(
            path=out_dir / "audits" / "active_verification_pilot_human_audit_paper_update.md",
            labels_csv=human_audit_source,
            rows=read_csv_rows(human_audit_source),
            status=str(active_verification_human_audit_status(active_verification_dir).get("status", "incomplete")),
            summary_csv="active_verification_pilot_human_audit_summary.csv",
        )
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_validation.json", out_dir / "audits" / "active_verification_pilot_human_audit_validation.json")
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_validation.md", out_dir / "audits" / "active_verification_pilot_human_audit_validation.md")
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_validation_rows.csv", out_dir / "audits" / "active_verification_pilot_human_audit_validation_rows.csv")
    copy_if_exists(active_verification_dir / "active_verification_pilot_human_audit_finalize_manifest.json", out_dir / "audits" / "active_verification_pilot_human_audit_finalize_manifest.json")
    copy_if_exists(active_verification_dir / "active_verification_pilot_codex_xhigh_audit_50.csv", out_dir / "audits" / "active_verification_pilot_codex_xhigh_audit_50.csv")
    copy_if_exists(active_verification_dir / "active_verification_pilot_codex_xhigh_audit_notes.md", out_dir / "audits" / "active_verification_pilot_codex_xhigh_audit_notes.md")
    copy_if_exists(active_verification_dir / "active_verification_pilot_codex_xhigh_audit_summary.csv", out_dir / "audits" / "active_verification_pilot_codex_xhigh_audit_summary.csv")
    copy_if_exists(active_verification_dir / "active_verification_pilot_codex_xhigh_audit_summary.json", out_dir / "audits" / "active_verification_pilot_codex_xhigh_audit_summary.json")
    minimal_task = opaque_tasks[0] | {"gold": gold_labels[0]}
    minimal_output = model_to_dict(always_insufficient_prediction(tasks[0], "standard_answer"))
    minimal_score = score_record(baseline_record(tasks[0], "standard_answer", "always_insufficient", always_insufficient_prediction(tasks[0], "standard_answer")), tasks[0])
    write_json(out_dir / "examples" / "minimal_task.json", minimal_task)
    write_json(out_dir / "examples" / "minimal_model_output.json", minimal_output)
    write_json(out_dir / "examples" / "minimal_score.json", minimal_score)
    (out_dir / "reproduce_minimal.sh").write_text(
        "#!/usr/bin/env bash\nset -euo pipefail\npython3 scorer/scoring_contract.py examples/minimal_task.json examples/minimal_model_output.json\n",
        encoding="utf-8",
    )
    (out_dir / "reproduce_minimal.sh").chmod(0o755)
    write_human_audit_review_server_script(out_dir / "serve_human_audit_review.sh")
    write_human_audit_finalize_script(out_dir / "finalize_human_audit.sh")
    write_step1_release_verify_script(out_dir / "verify_step1_release.sh")
    write_release_readme(out_dir)
    run_manifest, _ = load_json_file(frontier_main_dir / "run_manifest.json")
    report_manifest, _ = load_json_file(frontier_main_dir / "report_manifest.json")
    predictions_file = out_dir / "outputs" / "frontier_main_opaque_predictions.jsonl"
    scored_file = out_dir / "outputs" / "frontier_main_opaque_scored.csv"
    copied_run_manifest = out_dir / "outputs" / "frontier_main_opaque_run_manifest.json"
    copied_report_manifest = out_dir / "outputs" / "frontier_main_opaque_report_manifest.json"
    write_json(
        out_dir / "manifest.json",
        {
            "task_count": len(tasks),
            "opaque_task_count": len(opaque_tasks),
            "document_rows": len(documents),
            "baseline_files": sorted(path.name for path in (out_dir / "baselines").glob("*.csv")),
            "audit_files": sorted(path.name for path in (out_dir / "audits").glob("*")),
            "active_verification_human_audit": active_verification_human_audit_status(active_verification_dir),
            "active_verification_codex_xhigh_audit": active_verification_codex_xhigh_audit_status(active_verification_dir),
            "frontier_outputs_present": (out_dir / "outputs" / "frontier_main_opaque_scored.csv").exists(),
            "frontier_main_outputs": {
                "source_kind": "opaque_run" if (run_manifest or {}).get("model_visible_doc_id_policy") == "opaque_per_task" else "unknown",
                "source_dir": str(frontier_main_dir),
                "source_run_manifest": "run_manifest.json" if (frontier_main_dir / "run_manifest.json").exists() else "",
                "source_report_manifest": "report_manifest.json" if (frontier_main_dir / "report_manifest.json").exists() else "",
                "run_manifest_file": "outputs/frontier_main_opaque_run_manifest.json",
                "report_manifest_file": "outputs/frontier_main_opaque_report_manifest.json",
                "model_visible_doc_id_policy": (run_manifest or {}).get("model_visible_doc_id_policy", ""),
                "source_task_count": (report_manifest or run_manifest or {}).get("task_count", 0),
                "source_record_count": (report_manifest or {}).get("record_count", 0),
                "source_model_count": (report_manifest or run_manifest or {}).get("model_count", 0),
                "source_prompt_conditions": (report_manifest or run_manifest or {}).get("prompt_conditions", []),
                "predictions_file": "outputs/frontier_main_opaque_predictions.jsonl",
                "scored_file": "outputs/frontier_main_opaque_scored.csv",
                "predictions_sha256": file_sha256(predictions_file) if predictions_file.exists() else "",
                "scored_sha256": file_sha256(scored_file) if scored_file.exists() else "",
                "run_manifest_sha256": file_sha256(copied_run_manifest) if copied_run_manifest.exists() else "",
                "report_manifest_sha256": file_sha256(copied_report_manifest) if copied_report_manifest.exists() else "",
            },
        },
    )
    write_artifact_file_manifest(out_dir)


def readiness_gate(
    name: str,
    *,
    passed: bool,
    evidence: Sequence[str] | None = None,
    errors: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
) -> Dict[str, Any]:
    return {
        "name": name,
        "status": "pass" if passed else "fail",
        "evidence": list(evidence or []),
        "errors": list(errors or []),
        "warnings": list(warnings or []),
    }


def relative_to_artifact(path: Path, artifact_dir: Path) -> str:
    try:
        return str(path.relative_to(artifact_dir))
    except ValueError:
        return str(path)


def load_json_file(path: Path) -> tuple[Dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"missing JSON file: {path}"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in {path}: {exc}"
    if not isinstance(payload, dict):
        return None, f"JSON file is not an object: {path}"
    return payload, None


def required_file_gate(artifact_dir: Path) -> Dict[str, Any]:
    missing = [relative for relative in STEP1_REQUIRED_ARTIFACT_FILES if not (artifact_dir / relative).exists()]
    evidence = [relative for relative in STEP1_REQUIRED_ARTIFACT_FILES if (artifact_dir / relative).exists()]
    return readiness_gate(
        "required_release_files",
        passed=not missing,
        evidence=evidence,
        errors=[f"missing required artifact file: {relative}" for relative in missing],
    )


def file_manifest_gate(artifact_dir: Path) -> Dict[str, Any]:
    manifest_path = artifact_dir / "file_manifest.json"
    payload, error = load_json_file(manifest_path)
    if error or payload is None:
        return readiness_gate("file_manifest", passed=False, errors=[error or "invalid file manifest"])
    errors: List[str] = []
    evidence: List[str] = []
    files = payload.get("files", [])
    if not isinstance(files, list):
        return readiness_gate("file_manifest", passed=False, errors=["file_manifest files is missing or invalid"])
    manifest_records = {str(row.get("path", "")): row for row in files if isinstance(row, Mapping)}
    current_records = {row["path"]: row for row in artifact_file_records(artifact_dir)}
    missing = sorted(set(current_records) - set(manifest_records))
    extra = sorted(set(manifest_records) - set(current_records))
    errors.extend(f"file_manifest missing path: {path}" for path in missing)
    errors.extend(f"file_manifest has stale path: {path}" for path in extra)
    for path in sorted(set(current_records) & set(manifest_records)):
        expected = manifest_records[path]
        actual = current_records[path]
        if int(expected.get("bytes", -1) or -1) != int(actual["bytes"]):
            errors.append(f"file_manifest byte mismatch for {path}")
        if str(expected.get("sha256", "")) != str(actual["sha256"]):
            errors.append(f"file_manifest sha256 mismatch for {path}")
    if int(payload.get("file_count", -1) or -1) != len(files):
        errors.append(f"file_manifest file_count does not match listed files: file_count={payload.get('file_count')} listed={len(files)}")
    if int(payload.get("schema_version", 0) or 0) != 1:
        errors.append(f"file_manifest schema_version is not 1: {payload.get('schema_version')}")
    evidence.extend(
        [
            f"manifest_files={len(files)}",
            f"current_files={len(current_records)}",
        ]
    )
    return readiness_gate("file_manifest", passed=not errors, evidence=evidence, errors=errors)


def baseline_gate(artifact_dir: Path) -> Dict[str, Any]:
    baseline_dir = artifact_dir / "baselines"
    required = {f"{name}.csv" for name in BASELINE_NAMES}
    present = {path.name for path in baseline_dir.glob("*.csv")} if baseline_dir.exists() else set()
    missing = sorted(required - present)
    return readiness_gate(
        "baseline_files",
        passed=not missing,
        evidence=sorted(present & required),
        errors=[f"missing required baseline CSV: baselines/{name}" for name in missing],
    )


def generated_lore_schema_gate(artifact_dir: Path) -> Dict[str, Any]:
    path = artifact_dir / "audits" / "generated_lore_schema_ablation.csv"
    rows_path = artifact_dir / "audits" / "generated_lore_schema_ablation_rows.csv"
    if not path.exists():
        return readiness_gate(
            "generated_lore_schema_ablation",
            passed=False,
            errors=["missing audits/generated_lore_schema_ablation.csv"],
        )
    try:
        rows = read_csv_rows(path)
    except csv.Error as exc:
        return readiness_gate(
            "generated_lore_schema_ablation",
            passed=False,
            errors=[f"could not parse generated-lore schema ablation CSV: {exc}"],
        )
    variants = {row.get("schema_variant", "") for row in rows}
    missing = sorted(STEP1_REQUIRED_SCHEMA_VARIANTS - variants)
    errors = [f"missing required schema variant: {variant}" for variant in missing]
    required_columns = {"schema_variant", "model", "n", "prompt_condition"}
    actual_columns = set(rows[0]) if rows else set()
    missing_columns = sorted(required_columns - actual_columns)
    errors.extend(f"missing generated-lore schema ablation column: {column}" for column in missing_columns)
    models = {row.get("model", "") for row in rows if row.get("model", "")}
    if len(models) < 3:
        errors.append(f"generated-lore schema ablation covers fewer than 3 models: {len(models)}")
    if not missing_columns:
        for variant in sorted(STEP1_REQUIRED_SCHEMA_VARIANTS & variants):
            variant_rows = [row for row in rows if row.get("schema_variant") == variant]
            variant_models = {row.get("model", "") for row in variant_rows if row.get("model", "")}
            if len(variant_models) < 3:
                errors.append(f"schema ablation {variant} covers fewer than 3 models: {len(variant_models)}")
            for model in sorted(variant_models):
                qualifying_rows = [
                    row
                    for row in variant_rows
                    if row.get("model") == model and row.get("prompt_condition") in {"standard_answer", "all"}
                ]
                if not qualifying_rows:
                    errors.append(f"schema ablation {variant}/{model} has no standard_answer or all row")
                    continue
                n_values: List[int] = []
                for row in qualifying_rows:
                    try:
                        n_values.append(int(float(row.get("n", "0") or 0)))
                    except ValueError:
                        errors.append(f"schema ablation {variant}/{model} has invalid n={row.get('n', '')}")
                if n_values and max(n_values) < 20:
                    errors.append(f"schema ablation {variant}/{model} has n={max(n_values)}; expected at least 20")
    try:
        detail_rows = read_csv_rows(rows_path)
    except FileNotFoundError:
        detail_rows = []
        errors.append("missing audits/generated_lore_schema_ablation_rows.csv")
    except csv.Error as exc:
        detail_rows = []
        errors.append(f"could not parse generated-lore schema ablation rows CSV: {exc}")
    detail_task_ids = {row.get("task_id", "") for row in detail_rows if row.get("task_id", "")}
    detail_models = {row.get("model", "") for row in detail_rows if row.get("model", "")}
    if detail_rows:
        detail_columns = set(detail_rows[0])
        for column in ["schema_variant", "model", "task_id", "prompt_condition"]:
            if column not in detail_columns:
                errors.append(f"missing generated-lore schema ablation rows column: {column}")
        if len(detail_models) < 3:
            errors.append(f"generated-lore schema ablation rows cover fewer than 3 models: {len(detail_models)}")
        if len(detail_task_ids) < 20:
            errors.append(f"generated-lore schema ablation rows cover fewer than 20 tasks: {len(detail_task_ids)}")
        if {"schema_variant", "model", "task_id", "prompt_condition"} <= detail_columns:
            for variant in sorted(STEP1_REQUIRED_SCHEMA_VARIANTS & {row.get("schema_variant", "") for row in detail_rows}):
                variant_detail_rows = [row for row in detail_rows if row.get("schema_variant") == variant]
                variant_detail_models = {row.get("model", "") for row in variant_detail_rows if row.get("model", "")}
                if len(variant_detail_models) < 3:
                    errors.append(f"schema ablation rows {variant} cover fewer than 3 models: {len(variant_detail_models)}")
                for model in sorted(variant_detail_models):
                    standard_task_ids = {
                        row.get("task_id", "")
                        for row in variant_detail_rows
                        if row.get("model") == model and row.get("prompt_condition") == "standard_answer" and row.get("task_id", "")
                    }
                    if len(standard_task_ids) < 20:
                        errors.append(f"schema ablation rows {variant}/{model} cover {len(standard_task_ids)} standard tasks; expected at least 20")
    return readiness_gate(
        "generated_lore_schema_ablation",
        passed=not errors,
        evidence=[
            f"variants={','.join(sorted(variants))}",
            f"models={len(models)}",
            f"row_tasks={len(detail_task_ids)}",
            f"row_models={len(detail_models)}",
        ],
        errors=errors,
    )


def active_verification_human_audit_gate(artifact_dir: Path) -> Dict[str, Any]:
    validation_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_validation.json"
    labels_path = artifact_dir / "audits" / "active_verification_human_audit.csv"
    manifest_path = artifact_dir / "audits" / "active_verification_human_audit_manifest.json"
    payload, error = load_json_file(validation_path)
    if error or payload is None:
        return readiness_gate("active_verification_human_audit", passed=False, errors=[error or "invalid validation file"])
    status = str(payload.get("status", ""))
    n_rows = int(payload.get("n_rows", payload.get("reference_rows", 0)) or 0)
    n_complete = int(payload.get("n_complete_rows", 0) or 0)
    errors: List[str] = []
    evidence = [f"status={status}", f"n_rows={n_rows}", f"n_complete_rows={n_complete}"]
    try:
        label_rows = read_csv_rows(labels_path)
    except FileNotFoundError:
        label_rows = []
        errors.append("missing active-verification human-audit CSV")
    validation_labels_sha = str(payload.get("labels_sha256", ""))
    if labels_path.exists():
        current_labels_sha = file_sha256(labels_path)
        evidence.append(f"labels_sha256={current_labels_sha}")
        if not validation_labels_sha:
            errors.append("human audit validation is missing labels_sha256; rerun validation")
        elif validation_labels_sha != current_labels_sha:
            errors.append("human audit validation is stale: labels_sha256 does not match current CSV")
    manifest, manifest_error = load_json_file(manifest_path)
    if manifest_error or manifest is None:
        errors.append(manifest_error or "invalid human audit manifest")
    else:
        manifest_fields = {str(field) for field in manifest.get("label_fields", [])}
        required_fields = set(HUMAN_AUDIT_LABEL_FIELDS)
        context_rows = int(manifest.get("context_rows", 0) or 0)
        missing_fields = sorted(required_fields - manifest_fields)
        extra_fields = sorted(manifest_fields - required_fields)
        evidence.append(f"audit_manifest_context_rows={context_rows}")
        evidence.append(f"audit_manifest_label_fields={len(manifest_fields)}")
        if context_rows < 50:
            errors.append(f"human audit manifest has fewer than 50 context rows: {context_rows}")
        errors.extend(f"human audit manifest missing label field: {field}" for field in missing_fields)
        errors.extend(f"human audit manifest has unexpected label field: {field}" for field in extra_fields)
    actual_rows = len(label_rows)
    condition_counts: Dict[str, int] = defaultdict(int)
    for row in label_rows:
        condition_counts[row.get("condition", "")] += 1
    missing_conditions = sorted(STEP1_REQUIRED_HUMAN_AUDIT_CONDITIONS - set(condition_counts))
    evidence.append(f"actual_label_rows={actual_rows}")
    evidence.extend(f"{condition}={condition_counts.get(condition, 0)}" for condition in sorted(STEP1_REQUIRED_HUMAN_AUDIT_CONDITIONS))
    if actual_rows < 50:
        errors.append(f"human-audit label sheet has fewer than 50 rows: {actual_rows}")
    errors.extend(f"human-audit label sheet missing required condition: {condition}" for condition in missing_conditions)
    if status != "complete":
        errors.append(f"human audit validation is not complete: {status or 'missing'}")
    if n_rows < 50:
        errors.append(f"human audit has fewer than 50 rows: {n_rows}")
    if n_complete < 50:
        errors.append(f"human audit has fewer than 50 complete rows: {n_complete}")
    return readiness_gate(
        "active_verification_human_audit",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def active_verification_human_audit_worksheet_gate(artifact_dir: Path) -> Dict[str, Any]:
    worksheet_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_worksheet_50.csv"
    labels_path = artifact_dir / "audits" / "active_verification_human_audit.csv"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        worksheet_rows = read_csv_rows(worksheet_path)
    except FileNotFoundError:
        worksheet_rows = []
        errors.append("missing active-verification human-audit worksheet CSV")
    except csv.Error as exc:
        worksheet_rows = []
        errors.append(f"could not parse active-verification human-audit worksheet CSV: {exc}")
    try:
        label_rows = read_csv_rows(labels_path)
    except FileNotFoundError:
        label_rows = []
        errors.append("missing active-verification human-audit CSV")
    except csv.Error as exc:
        label_rows = []
        errors.append(f"could not parse active-verification human-audit CSV: {exc}")
    required_columns = {
        "row_index",
        "audit_status",
        "model",
        "task_id",
        "condition",
        "prompt_condition",
        "question",
        "model_actions",
        "documents",
        *HUMAN_AUDIT_LABEL_FIELDS,
    }
    actual_columns = set(worksheet_rows[0]) if worksheet_rows else set()
    missing_columns = sorted(required_columns - actual_columns)
    errors.extend(f"human-audit worksheet missing column: {column}" for column in missing_columns)
    evidence.append(f"worksheet_rows={len(worksheet_rows)}")
    if len(worksheet_rows) != 50:
        errors.append(f"human-audit worksheet has {len(worksheet_rows)} rows; expected 50")
    if label_rows and worksheet_rows and len(label_rows) != len(worksheet_rows):
        errors.append(f"human-audit worksheet row count does not match strict CSV: worksheet={len(worksheet_rows)} labels={len(label_rows)}")
    if label_rows and worksheet_rows:
        for index, (worksheet, label) in enumerate(zip(worksheet_rows, label_rows), start=1):
            if row_key(worksheet) != row_key(label):
                errors.append(f"worksheet row {index} key mismatch: worksheet={row_key(worksheet)} labels={row_key(label)}")
                break
    if not errors:
        with tempfile.TemporaryDirectory() as tmp_dir:
            imported_path = Path(tmp_dir) / "imported.csv"
            try:
                import_active_verification_human_audit_worksheet(
                    worksheet_csv=worksheet_path,
                    reference_csv=labels_path,
                    out_csv=imported_path,
                )
            except (OSError, ValueError, csv.Error) as exc:
                errors.append(f"worksheet import failed: {exc}")
            else:
                imported_rows = read_csv_rows(imported_path)
                evidence.append("importable_to_strict_csv=True")
                evidence.append(f"imported_rows={len(imported_rows)}")
    elif worksheet_rows and label_rows:
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                import_active_verification_human_audit_worksheet(
                    worksheet_csv=worksheet_path,
                    reference_csv=labels_path,
                    out_csv=Path(tmp_dir) / "imported.csv",
                )
            except (OSError, ValueError, csv.Error) as exc:
                errors.append(f"worksheet import failed: {exc}")
    return readiness_gate(
        "active_verification_human_audit_worksheet",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def active_verification_human_audit_model_blinded_worksheet_gate(artifact_dir: Path) -> Dict[str, Any]:
    worksheet_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv"
    labels_path = artifact_dir / "audits" / "active_verification_human_audit.csv"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        worksheet_rows = read_csv_rows(worksheet_path)
    except FileNotFoundError:
        worksheet_rows = []
        errors.append("missing active-verification model-blinded human-audit worksheet CSV")
    except csv.Error as exc:
        worksheet_rows = []
        errors.append(f"could not parse active-verification model-blinded human-audit worksheet CSV: {exc}")
    try:
        label_rows = read_csv_rows(labels_path)
    except FileNotFoundError:
        label_rows = []
        errors.append("missing active-verification human-audit strict CSV")
    except csv.Error as exc:
        label_rows = []
        errors.append(f"could not parse active-verification human-audit strict CSV: {exc}")
    required_columns = {"row_index", "evidence_condition", *HUMAN_AUDIT_MUTABLE_FIELDS}
    actual_columns = set(worksheet_rows[0]) if worksheet_rows else set()
    missing_columns = sorted(required_columns - actual_columns)
    errors.extend(f"model-blinded human-audit worksheet missing column: {column}" for column in missing_columns)
    forbidden_columns = {
        "model",
        "task_id",
        "prompt_condition",
        "auto_action_gate_pass",
        "auto_missing_primary_action",
        "auto_missing_contradiction_action",
        "auto_missing_trace_source_action",
        "auto_actions_visible_ids",
    }
    errors.extend(f"model-blinded human-audit worksheet exposes forbidden column: {column}" for column in sorted(forbidden_columns & actual_columns))
    evidence.append(f"model_blinded_worksheet_rows={len(worksheet_rows)}")
    if len(worksheet_rows) != 50:
        errors.append(f"model-blinded human-audit worksheet has {len(worksheet_rows)} rows; expected 50")
    for index, row in enumerate(worksheet_rows, start=1):
        raw_index = str(row.get("row_index", "")).strip()
        try:
            row_index = int(float(raw_index))
        except ValueError:
            row_index = -1
        if row_index != index:
            errors.append(f"model-blinded worksheet row {index} row_index mismatch: {raw_index or 'blank'}")
            break
    if label_rows and worksheet_rows and len(label_rows) != len(worksheet_rows):
        errors.append(f"model-blinded human-audit worksheet row count does not match strict CSV: worksheet={len(worksheet_rows)} labels={len(label_rows)}")
    worksheet_text = worksheet_path.read_text(encoding="utf-8", errors="replace") if worksheet_path.exists() else ""
    for phrase in STEP1_HUMAN_AUDIT_MODEL_BLINDED_PACKET_FORBIDDEN_PHRASES:
        if phrase in worksheet_text:
            errors.append(f"model-blinded human-audit worksheet exposes forbidden phrase: {phrase}")
    if "eham_" in worksheet_text:
        errors.append("model-blinded human-audit worksheet contains semantic audit ID marker eham_")
    if not errors and label_rows and worksheet_rows:
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                import_active_verification_model_blinded_human_audit_worksheet(
                    worksheet_csv=worksheet_path,
                    reference_csv=labels_path,
                    out_csv=Path(tmpdir) / "imported.csv",
                )
                evidence.append("importable_to_strict_csv=True")
            except ValueError as exc:
                errors.append(f"model-blinded worksheet import failed: {exc}")
    return readiness_gate(
        "active_verification_human_audit_model_blinded_worksheet",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def active_verification_human_audit_protocol_gate(artifact_dir: Path) -> Dict[str, Any]:
    path = artifact_dir / "audits" / "active_verification_human_audit_protocol.md"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return readiness_gate(
            "active_verification_human_audit_protocol",
            passed=False,
            errors=[f"could not read active-verification human-audit protocol: {exc}"],
        )
    missing = [
        label
        for label, phrase in STEP1_HUMAN_AUDIT_PROTOCOL_REQUIRED_PHRASES.items()
        if phrase not in text
    ]
    return readiness_gate(
        "active_verification_human_audit_protocol",
        passed=not missing,
        evidence=[label for label in STEP1_HUMAN_AUDIT_PROTOCOL_REQUIRED_PHRASES if label not in missing],
        errors=[f"missing human-audit protocol phrase: {label}" for label in missing],
    )


def parse_attestation_fields(text: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    expected = {
        "auditor_identifier",
        "date_completed",
        "audit_surface_used",
        "independent_human_review_completed",
        "codex_triage_not_copied_as_human_labels",
        "all_50_rows_reviewed",
        "all_eight_binary_fields_and_auditor_notes_completed",
    }
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized_key = key.strip().lower()
        if normalized_key in expected:
            fields[normalized_key] = value.strip()
    return fields


def attestation_yes(value: str) -> bool:
    return value.strip().lower() in {"yes", "true", "1", "y"}


def active_verification_human_audit_attestation_gate(artifact_dir: Path) -> Dict[str, Any]:
    path = artifact_dir / "audits" / "active_verification_human_audit_attestation.md"
    validation_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_validation.json"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return readiness_gate(
            "active_verification_human_audit_attestation",
            passed=False,
            errors=[f"could not read active-verification human-audit attestation: {exc}"],
        )
    missing = [
        label
        for label, phrase in STEP1_HUMAN_AUDIT_ATTESTATION_REQUIRED_PHRASES.items()
        if phrase not in text
    ]
    evidence.extend(label for label in STEP1_HUMAN_AUDIT_ATTESTATION_REQUIRED_PHRASES if label not in missing)
    errors.extend(f"missing human-audit attestation phrase: {label}" for label in missing)

    validation, validation_error = load_json_file(validation_path)
    status = str((validation or {}).get("status", "")) if isinstance(validation, Mapping) else ""
    n_complete = int((validation or {}).get("n_complete_rows", 0) or 0) if isinstance(validation, Mapping) else 0
    audit_complete = status == "complete" and n_complete >= 50
    evidence.extend([f"human_audit_status={status or 'missing'}", f"human_audit_complete_rows={n_complete}"])
    if validation_error:
        evidence.append(f"validation_read_error={validation_error}")

    has_placeholder = STEP1_HUMAN_AUDIT_ATTESTATION_PLACEHOLDER in text
    if has_placeholder:
        evidence.append("attestation_template_present=True")
        if audit_complete:
            errors.append("human-audit attestation still contains completion placeholders")
    else:
        evidence.append("attestation_template_present=False")

    if audit_complete:
        fields = parse_attestation_fields(text)
        for field in [
            "auditor_identifier",
            "date_completed",
            "audit_surface_used",
            "independent_human_review_completed",
            "codex_triage_not_copied_as_human_labels",
            "all_50_rows_reviewed",
            "all_eight_binary_fields_and_auditor_notes_completed",
        ]:
            value = fields.get(field, "")
            if not value:
                errors.append(f"human-audit attestation missing completed field: {field}")
            elif STEP1_HUMAN_AUDIT_ATTESTATION_PLACEHOLDER in value:
                errors.append(f"human-audit attestation field still has placeholder: {field}")
        surface = fields.get("audit_surface_used", "").strip().lower()
        if surface and surface not in STEP1_HUMAN_AUDIT_ATTESTATION_SURFACES:
            errors.append(f"human-audit attestation audit_surface_used is invalid: {surface}")
        for field in [
            "independent_human_review_completed",
            "codex_triage_not_copied_as_human_labels",
            "all_50_rows_reviewed",
            "all_eight_binary_fields_and_auditor_notes_completed",
        ]:
            value = fields.get(field, "")
            if value and not attestation_yes(value):
                errors.append(f"human-audit attestation field must be yes: {field}")

    return readiness_gate(
        "active_verification_human_audit_attestation",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def active_verification_human_audit_paper_update_gate(artifact_dir: Path) -> Dict[str, Any]:
    memo_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_paper_update.md"
    summary_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_summary.json"
    validation_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_validation.json"
    labels_path = artifact_dir / "audits" / "active_verification_human_audit.csv"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        memo = memo_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return readiness_gate(
            "active_verification_human_audit_paper_update",
            passed=False,
            errors=[f"could not read active-verification human-audit paper-update memo: {exc}"],
        )
    summary, summary_error = load_json_file(summary_path)
    validation, validation_error = load_json_file(validation_path)
    if summary_error or summary is None:
        errors.append(summary_error or "invalid human-audit summary JSON")
        summary = {}
    if validation_error or validation is None:
        errors.append(validation_error or "invalid human-audit validation JSON")
        validation = {}
    status = str(summary.get("status") or validation.get("status") or "")
    n_labeled = int(summary.get("n_labeled", validation.get("n_complete_rows", 0)) or 0)
    n_rows = int(summary.get("n_rows", validation.get("n_rows", validation.get("reference_rows", 0))) or 0)
    audit_complete = status == "complete" and n_labeled >= 50
    evidence.extend([f"human_audit_status={status or 'missing'}", f"n_labeled={n_labeled}", f"n_rows={n_rows}"])

    paper_ready_marker = "A single-auditor pilot human audit reports the human-labeled active-verification audit"
    if audit_complete:
        try:
            rows = read_csv_rows(labels_path)
        except FileNotFoundError:
            rows = []
            errors.append("missing active-verification human-audit CSV for paper-update memo check")
        except csv.Error as exc:
            rows = []
            errors.append(f"could not parse active-verification human-audit CSV for paper-update memo check: {exc}")
        denominator = len(rows) or n_labeled
        counts = {
            "semantically_useful_action": count_binary_label(rows, "semantically_useful_action"),
            "machine_executable_action": count_binary_label(rows, "machine_executable_action"),
            "required_action_type_present": count_binary_label(rows, "required_action_type_present"),
            "scorer_too_strict": count_binary_label(rows, "scorer_too_strict"),
        }
        evidence.extend(f"{field}={value}/{denominator}" for field, value in counts.items())
        expected_phrases = [
            paper_ready_marker,
            f"{counts['semantically_useful_action']}/{denominator} as semantically useful",
            f"{counts['machine_executable_action']}/{denominator} as machine executable",
            f"{counts['required_action_type_present']}/{denominator} as containing the required action type",
            f"{counts['scorer_too_strict']}/{denominator} automatic rejections as plausibly too strict",
        ]
        for phrase in expected_phrases:
            if phrase not in memo:
                errors.append(f"human-audit paper-update memo missing or stale phrase: {phrase}")
        if "not human validation" in memo and "Do not use this memo to make completed human-audit claims yet" in memo:
            errors.append("human-audit paper-update memo still contains incomplete-audit warning after completion")
    else:
        if paper_ready_marker in memo:
            errors.append("human-audit paper-update memo contains paper-ready sentence before completion")
        required_incomplete_phrases = [
            "Do not use this memo to make completed human-audit claims yet.",
            "not human validation",
        ]
        for phrase in required_incomplete_phrases:
            if phrase not in memo:
                errors.append(f"human-audit paper-update memo missing incomplete-audit warning phrase: {phrase}")
        if not errors:
            evidence.append("incomplete_paper_update_boundary=True")

    return readiness_gate(
        "active_verification_human_audit_paper_update",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def active_verification_human_audit_model_blinded_packet_gate(artifact_dir: Path) -> Dict[str, Any]:
    path = artifact_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_packet_50.md"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return readiness_gate(
            "active_verification_human_audit_model_blinded_packet",
            passed=False,
            errors=[f"could not read active-verification model-blinded human-audit packet: {exc}"],
        )
    errors: List[str] = []
    missing = [
        label
        for label, phrase in STEP1_HUMAN_AUDIT_MODEL_BLINDED_PACKET_REQUIRED_PHRASES.items()
        if phrase not in text
    ]
    errors.extend(f"missing model-blinded packet phrase: {label}" for label in missing)
    for phrase in STEP1_HUMAN_AUDIT_MODEL_BLINDED_PACKET_FORBIDDEN_PHRASES:
        if phrase in text:
            errors.append(f"model-blinded packet exposes forbidden phrase: {phrase}")
    if "eham_" in text:
        errors.append("model-blinded packet contains semantic audit ID marker eham_")
    row_count = len(re.findall(r"^## Row \d{2}$", text, flags=re.MULTILINE))
    evidence = [label for label in STEP1_HUMAN_AUDIT_MODEL_BLINDED_PACKET_REQUIRED_PHRASES if label not in missing]
    evidence.append(f"model_blinded_rows={row_count}")
    if row_count != 50:
        errors.append(f"model-blinded packet has {row_count} rows; expected 50")
    return readiness_gate(
        "active_verification_human_audit_model_blinded_packet",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def active_verification_human_audit_review_gate(artifact_dir: Path) -> Dict[str, Any]:
    html_path = artifact_dir / "audits" / "active_verification_human_audit_review.html"
    launcher_path = artifact_dir / "serve_human_audit_review.sh"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        html = html_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        html = ""
        errors.append(f"could not read human-audit review HTML: {exc}")
    if html:
        missing_html = [label for label, phrase in STEP1_HUMAN_AUDIT_REVIEW_HTML_REQUIRED_PHRASES.items() if phrase not in html]
        evidence.extend(label for label in STEP1_HUMAN_AUDIT_REVIEW_HTML_REQUIRED_PHRASES if label not in missing_html)
        errors.extend(f"missing human-audit review HTML phrase: {label}" for label in missing_html)
        if "eham_" in html:
            errors.append("human-audit review HTML contains semantic audit ID marker eham_")
    try:
        launcher = launcher_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        launcher = ""
        errors.append(f"could not read human-audit review launcher: {exc}")
    if launcher:
        missing_launcher = [label for label, phrase in STEP1_HUMAN_AUDIT_REVIEW_LAUNCHER_REQUIRED_PHRASES.items() if phrase not in launcher]
        evidence.extend(f"launcher:{label}" for label in STEP1_HUMAN_AUDIT_REVIEW_LAUNCHER_REQUIRED_PHRASES if label not in missing_launcher)
        errors.extend(f"missing human-audit review launcher phrase: {label}" for label in missing_launcher)
        syntax = subprocess.run(["bash", "-n", str(launcher_path)], capture_output=True, text=True, check=False)
        if syntax.returncode == 0:
            evidence.append("launcher_bash_n=True")
        else:
            errors.append(f"human-audit review launcher fails bash -n: {syntax.stderr.strip() or syntax.stdout.strip()}")
    return readiness_gate(
        "active_verification_human_audit_review",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def active_verification_human_audit_finalize_script_gate(artifact_dir: Path) -> Dict[str, Any]:
    script_path = artifact_dir / "finalize_human_audit.sh"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        script = script_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        script = ""
        errors.append(f"could not read human-audit finalization script: {exc}")
    if script:
        missing = [label for label, phrase in STEP1_HUMAN_AUDIT_FINALIZE_SCRIPT_REQUIRED_PHRASES.items() if phrase not in script]
        evidence.extend(label for label in STEP1_HUMAN_AUDIT_FINALIZE_SCRIPT_REQUIRED_PHRASES if label not in missing)
        errors.extend(f"missing human-audit finalization script phrase: {label}" for label in missing)
        syntax = subprocess.run(["bash", "-n", str(script_path)], capture_output=True, text=True, check=False)
        if syntax.returncode == 0:
            evidence.append("finalize_script_bash_n=True")
        else:
            errors.append(f"human-audit finalization script fails bash -n: {syntax.stderr.strip() or syntax.stdout.strip()}")
    return readiness_gate(
        "active_verification_human_audit_finalize_script",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def step1_release_verify_script_gate(artifact_dir: Path) -> Dict[str, Any]:
    script_path = artifact_dir / "verify_step1_release.sh"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        script = script_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        script = ""
        errors.append(f"could not read Step 1 release verifier script: {exc}")
    if script:
        missing = [label for label, phrase in STEP1_RELEASE_VERIFY_SCRIPT_REQUIRED_PHRASES.items() if phrase not in script]
        evidence.extend(label for label in STEP1_RELEASE_VERIFY_SCRIPT_REQUIRED_PHRASES if label not in missing)
        errors.extend(f"missing Step 1 release verifier script phrase: {label}" for label in missing)
        syntax = subprocess.run(["bash", "-n", str(script_path)], capture_output=True, text=True, check=False)
        if syntax.returncode == 0:
            evidence.append("release_verify_script_bash_n=True")
        else:
            errors.append(f"Step 1 release verifier script fails bash -n: {syntax.stderr.strip() or syntax.stdout.strip()}")
    return readiness_gate(
        "step1_release_verify_script",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def artifact_manifest_gate(artifact_dir: Path) -> Dict[str, Any]:
    path = artifact_dir / "manifest.json"
    payload, error = load_json_file(path)
    if error or payload is None:
        return readiness_gate("artifact_manifest", passed=False, errors=[error or "invalid manifest"])
    errors: List[str] = []
    warnings: List[str] = []
    if int(payload.get("task_count", 0) or 0) <= 0:
        errors.append("manifest task_count is missing or zero")
    if not payload.get("frontier_outputs_present"):
        errors.append("manifest frontier_outputs_present is not true")
    baseline_files = set(payload.get("baseline_files", []))
    missing_baselines = sorted({f"{name}.csv" for name in BASELINE_NAMES} - baseline_files)
    errors.extend(f"manifest missing baseline file: {name}" for name in missing_baselines)
    human_status = payload.get("active_verification_human_audit", {})
    if isinstance(human_status, Mapping):
        if human_status.get("status") != "complete":
            errors.append(f"manifest active_verification_human_audit status is {human_status.get('status', 'missing')}")
        if int(human_status.get("n_labeled", 0) or 0) < 50:
            errors.append(f"manifest active_verification_human_audit n_labeled is {human_status.get('n_labeled', 0)}")
    else:
        errors.append("manifest active_verification_human_audit is missing or invalid")
    if int(payload.get("task_count", 0) or 0) < 100:
        warnings.append(f"manifest task_count is below Step 1 expected 100 tasks: {payload.get('task_count', 0)}")
    return readiness_gate(
        "artifact_manifest",
        passed=not errors,
        evidence=[
            f"task_count={payload.get('task_count', '')}",
            f"frontier_outputs_present={payload.get('frontier_outputs_present', '')}",
            f"baseline_files={len(baseline_files)}",
            f"active_verification_human_audit={human_status if isinstance(human_status, Mapping) else 'invalid'}",
        ],
        errors=errors,
        warnings=warnings,
    )


def opaque_main_outputs_gate(artifact_dir: Path) -> Dict[str, Any]:
    manifest, error = load_json_file(artifact_dir / "manifest.json")
    if error or manifest is None:
        return readiness_gate("opaque_main_outputs", passed=False, errors=[error or "invalid manifest"])
    errors: List[str] = []
    evidence: List[str] = []
    if int(manifest.get("task_count", 0) or 0) != int(manifest.get("opaque_task_count", -1) or -1):
        errors.append(
            f"manifest task_count and opaque_task_count differ: task_count={manifest.get('task_count', 0)} opaque_task_count={manifest.get('opaque_task_count', 0)}"
        )
    outputs = manifest.get("frontier_main_outputs")
    if not isinstance(outputs, Mapping):
        return readiness_gate(
            "opaque_main_outputs",
            passed=False,
            errors=[*errors, "manifest frontier_main_outputs is missing or invalid"],
        )
    evidence.extend(
        [
            f"source_kind={outputs.get('source_kind', '')}",
            f"model_visible_doc_id_policy={outputs.get('model_visible_doc_id_policy', '')}",
            f"source_task_count={outputs.get('source_task_count', '')}",
            f"source_record_count={outputs.get('source_record_count', '')}",
        ]
    )
    if outputs.get("source_kind") != "opaque_run":
        errors.append(f"frontier main source_kind is not opaque_run: {outputs.get('source_kind', '')}")
    if outputs.get("model_visible_doc_id_policy") != "opaque_per_task":
        errors.append(f"frontier main doc_id policy is not opaque_per_task: {outputs.get('model_visible_doc_id_policy', '')}")
    if int(outputs.get("source_task_count", 0) or 0) != int(manifest.get("task_count", 0) or 0):
        errors.append(
            f"frontier main source_task_count does not match manifest task_count: source={outputs.get('source_task_count', 0)} manifest={manifest.get('task_count', 0)}"
        )
    if int(outputs.get("source_record_count", 0) or 0) <= 0:
        errors.append("frontier main source_record_count is missing or zero")
    expected_files = {
        "predictions_file": "outputs/frontier_main_opaque_predictions.jsonl",
        "scored_file": "outputs/frontier_main_opaque_scored.csv",
        "run_manifest_file": "outputs/frontier_main_opaque_run_manifest.json",
        "report_manifest_file": "outputs/frontier_main_opaque_report_manifest.json",
    }
    for key, expected in expected_files.items():
        actual = str(outputs.get(key, ""))
        if actual != expected:
            errors.append(f"frontier main {key} is not {expected}: {actual}")
        if not (artifact_dir / expected).exists():
            errors.append(f"missing frontier main output file: {expected}")
    copied_run_manifest, run_manifest_error = load_json_file(artifact_dir / expected_files["run_manifest_file"])
    copied_report_manifest, report_manifest_error = load_json_file(artifact_dir / expected_files["report_manifest_file"])
    if run_manifest_error or copied_run_manifest is None:
        errors.append(run_manifest_error or "invalid copied run manifest")
    else:
        evidence.append(f"run_manifest_doc_id_policy={copied_run_manifest.get('model_visible_doc_id_policy', '')}")
        if copied_run_manifest.get("model_visible_doc_id_policy") != "opaque_per_task":
            errors.append(f"copied run manifest doc_id policy is not opaque_per_task: {copied_run_manifest.get('model_visible_doc_id_policy', '')}")
        if int(copied_run_manifest.get("task_count", 0) or 0) != int(outputs.get("source_task_count", 0) or 0):
            errors.append(
                f"copied run manifest task_count does not match source_task_count: run={copied_run_manifest.get('task_count', 0)} source={outputs.get('source_task_count', 0)}"
            )
        if int(copied_run_manifest.get("job_count", 0) or 0) != int(outputs.get("source_record_count", 0) or 0):
            errors.append(
                f"copied run manifest job_count does not match source_record_count: run={copied_run_manifest.get('job_count', 0)} source={outputs.get('source_record_count', 0)}"
            )
        if int(copied_run_manifest.get("model_count", 0) or 0) != int(outputs.get("source_model_count", 0) or 0):
            errors.append(
                f"copied run manifest model_count does not match source_model_count: run={copied_run_manifest.get('model_count', 0)} source={outputs.get('source_model_count', 0)}"
            )
    if report_manifest_error or copied_report_manifest is None:
        errors.append(report_manifest_error or "invalid copied report manifest")
    else:
        evidence.append(f"report_manifest_record_count={copied_report_manifest.get('record_count', '')}")
        if int(copied_report_manifest.get("record_count", 0) or 0) != int(outputs.get("source_record_count", 0) or 0):
            errors.append(
                f"copied report manifest record_count does not match source_record_count: report={copied_report_manifest.get('record_count', 0)} source={outputs.get('source_record_count', 0)}"
            )
        if int(copied_report_manifest.get("task_count", 0) or 0) != int(outputs.get("source_task_count", 0) or 0):
            errors.append(
                f"copied report manifest task_count does not match source_task_count: report={copied_report_manifest.get('task_count', 0)} source={outputs.get('source_task_count', 0)}"
            )
        if int(copied_report_manifest.get("model_count", 0) or 0) != int(outputs.get("source_model_count", 0) or 0):
            errors.append(
                f"copied report manifest model_count does not match source_model_count: report={copied_report_manifest.get('model_count', 0)} source={outputs.get('source_model_count', 0)}"
            )
    for key, hash_key in [
        ("run_manifest_file", "run_manifest_sha256"),
        ("report_manifest_file", "report_manifest_sha256"),
    ]:
        path = artifact_dir / expected_files[key]
        if path.exists():
            actual_hash = file_sha256(path)
            if not outputs.get(hash_key):
                errors.append(f"frontier main {hash_key} is missing")
            elif outputs.get(hash_key) != actual_hash:
                errors.append(f"frontier main {hash_key} does not match copied file")
    predictions_path = artifact_dir / expected_files["predictions_file"]
    if predictions_path.exists():
        prediction_rows = 0
        with predictions_path.open(encoding="utf-8") as handle:
            for index, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                prediction_rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"frontier main predictions row {index} is invalid JSON: {exc}")
                    break
                invocation = row.get("invocation_profile", {}) if isinstance(row, Mapping) else {}
                if not isinstance(invocation, Mapping):
                    errors.append(f"frontier main predictions row {index} lacks invocation_profile")
                    break
                if invocation.get("doc_id_policy") != "opaque_per_task":
                    errors.append(f"frontier main predictions row {index} doc_id_policy is not opaque_per_task")
                    break
                audit = invocation.get("visible_prompt_audit", {})
                if isinstance(audit, Mapping):
                    for key in [
                        "semantic_doc_id_hits",
                        "semantic_visible_citation_hits",
                        "audit_id_hits_in_title_or_body",
                    ]:
                        if int(audit.get(key, 0) or 0) != 0:
                            errors.append(f"frontier main predictions row {index} visible prompt audit has {key}={audit.get(key)}")
                            break
                if errors and "visible prompt audit" in errors[-1]:
                    break
        evidence.append(f"prediction_rows={prediction_rows}")
        if prediction_rows <= 0:
            errors.append("frontier main predictions file has no rows")
        elif int(outputs.get("source_record_count", 0) or 0) and prediction_rows != int(outputs.get("source_record_count", 0) or 0):
            errors.append(
                f"frontier main predictions row count does not match source_record_count: rows={prediction_rows} source_record_count={outputs.get('source_record_count', 0)}"
            )
    scored_path = artifact_dir / expected_files["scored_file"]
    if scored_path.exists():
        try:
            scored_rows = len(read_csv_rows(scored_path))
        except csv.Error as exc:
            errors.append(f"could not parse frontier main scored CSV: {exc}")
            scored_rows = 0
        evidence.append(f"scored_rows={scored_rows}")
        if scored_rows <= 0:
            errors.append("frontier main scored CSV has no rows")
        elif int(outputs.get("source_record_count", 0) or 0) and scored_rows != int(outputs.get("source_record_count", 0) or 0):
            errors.append(
                f"frontier main scored row count does not match source_record_count: rows={scored_rows} source_record_count={outputs.get('source_record_count', 0)}"
            )
    return readiness_gate(
        "opaque_main_outputs",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def artifact_readme_scope_gate(artifact_dir: Path) -> Dict[str, Any]:
    path = artifact_dir / "README.md"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return readiness_gate("artifact_readme_scope", passed=False, errors=[f"could not read README.md: {exc}"])
    missing = [label for label, phrase in STEP1_ARTIFACT_README_REQUIRED_PHRASES.items() if phrase not in text]
    return readiness_gate(
        "artifact_readme_scope",
        passed=not missing,
        evidence=[label for label in STEP1_ARTIFACT_README_REQUIRED_PHRASES if label not in missing],
        errors=[f"missing artifact README scope phrase: {label}" for label in missing],
    )


def minimal_example_gate(artifact_dir: Path) -> Dict[str, Any]:
    required = [
        artifact_dir / "scorer" / "scoring_contract.py",
        artifact_dir / "examples" / "minimal_task.json",
        artifact_dir / "examples" / "minimal_model_output.json",
        artifact_dir / "examples" / "minimal_score.json",
    ]
    missing = [relative_to_artifact(path, artifact_dir) for path in required if not path.exists()]
    if missing:
        return readiness_gate(
            "minimal_example",
            passed=False,
            errors=[f"missing minimal example file: {path}" for path in missing],
        )
    try:
        result = subprocess.run(
            [
                sys.executable,
                "scorer/scoring_contract.py",
                "examples/minimal_task.json",
                "examples/minimal_model_output.json",
            ],
            cwd=artifact_dir,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return readiness_gate("minimal_example", passed=False, errors=[f"minimal example did not run: {exc}"])
    if result.returncode != 0:
        detail = compact_text(result.stderr or result.stdout, 500)
        return readiness_gate(
            "minimal_example",
            passed=False,
            evidence=[f"returncode={result.returncode}"],
            errors=[f"minimal example exited nonzero: {detail}"],
        )
    try:
        actual = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return readiness_gate(
            "minimal_example",
            passed=False,
            evidence=["returncode=0"],
            errors=[f"minimal example did not emit JSON: {exc}"],
        )
    expected, expected_error = load_json_file(artifact_dir / "examples" / "minimal_score.json")
    errors: List[str] = []
    required_keys = {
        "belief_correctness",
        "evidence_cleanliness",
        "uncertainty_discipline",
        "operational_epistemic_escape",
    }
    missing_keys = sorted(required_keys - set(actual)) if isinstance(actual, dict) else sorted(required_keys)
    errors.extend(f"minimal example output missing key: {key}" for key in missing_keys)
    if expected_error or expected is None:
        errors.append(expected_error or "minimal_score.json is invalid")
    elif isinstance(actual, dict):
        for key in sorted(required_keys & set(expected)):
            if actual.get(key) != expected.get(key):
                errors.append(f"minimal example output mismatch for {key}: actual={actual.get(key)} expected={expected.get(key)}")
    return readiness_gate(
        "minimal_example",
        passed=not errors,
        evidence=[f"returncode={result.returncode}", *(f"{key}={actual.get(key)}" for key in sorted(required_keys) if isinstance(actual, dict) and key in actual)],
        errors=errors,
    )


def semantic_id_leakage_gate(artifact_dir: Path) -> Dict[str, Any]:
    errors: List[str] = []
    scanned = 0
    for path in sorted(item for item in artifact_dir.rglob("*") if item.is_file()):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            errors.append(f"could not read {relative_to_artifact(path, artifact_dir)}: {exc}")
            continue
        scanned += 1
        for label, pattern in STEP1_SEMANTIC_ID_PATTERNS.items():
            match = pattern.search(text)
            if match:
                errors.append(f"{relative_to_artifact(path, artifact_dir)} contains semantic ID marker `{label}`")
                break
    return readiness_gate(
        "semantic_id_leakage",
        passed=not errors,
        evidence=[f"scanned_files={scanned}"],
        errors=errors,
    )


def relative_to_root(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def paper_required_files_gate(paper_dir: Path) -> Dict[str, Any]:
    missing = [relative for relative in STEP1_REQUIRED_PAPER_FILES if not (paper_dir / relative).exists()]
    evidence = [relative for relative in STEP1_REQUIRED_PAPER_FILES if (paper_dir / relative).exists()]
    return readiness_gate(
        "paper_required_files",
        passed=not missing,
        evidence=evidence,
        errors=[f"missing required paper file: {relative}" for relative in missing],
    )


def paper_source_files(paper_dir: Path) -> List[Path]:
    return sorted(
        path
        for path in paper_dir.rglob("*")
        if path.is_file() and path.suffix in {".tex", ".bib"}
    )


def read_paper_sources(paper_dir: Path) -> tuple[str, List[str]]:
    chunks: List[str] = []
    errors: List[str] = []
    for path in paper_source_files(paper_dir):
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            errors.append(f"could not read {relative_to_root(path, paper_dir)}: {exc}")
    return "\n".join(chunks), errors


def paper_positioning_gate(paper_dir: Path) -> Dict[str, Any]:
    text, read_errors = read_paper_sources(paper_dir)
    missing = [label for label, phrase in STEP1_PAPER_REQUIRED_PHRASES.items() if phrase not in text]
    errors = list(read_errors)
    errors.extend(f"missing paper positioning phrase: {label}" for label in missing)
    return readiness_gate(
        "paper_positioning",
        passed=not errors,
        evidence=[label for label in STEP1_PAPER_REQUIRED_PHRASES if label not in missing],
        errors=errors,
    )


def paper_artifact_appendix_gate(paper_dir: Path) -> Dict[str, Any]:
    path = paper_dir / "appendix" / "e_artifacts.tex"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return readiness_gate(
            "paper_artifact_appendix",
            passed=False,
            errors=[f"could not read artifact appendix: {exc}"],
        )
    missing = [label for label, phrase in STEP1_PAPER_ARTIFACT_APPENDIX_REQUIRED_PHRASES.items() if phrase not in text]
    return readiness_gate(
        "paper_artifact_appendix",
        passed=not missing,
        evidence=[label for label in STEP1_PAPER_ARTIFACT_APPENDIX_REQUIRED_PHRASES if label not in missing],
        errors=[f"missing artifact appendix phrase: {label}" for label in missing],
    )


def paper_step_boundary_gate(paper_dir: Path) -> Dict[str, Any]:
    paths = [
        paper_dir / "sections" / "08_discussion.tex",
        paper_dir / "sections" / "09_limitations.tex",
    ]
    errors: List[str] = []
    chunks: List[str] = []
    for path in paths:
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            errors.append(f"could not read Step 1/Step 2 boundary source {relative_to_root(path, paper_dir)}: {exc}")
    text = "\n".join(chunks)
    missing = [label for label, phrase in STEP1_PAPER_STEP_BOUNDARY_REQUIRED_PHRASES.items() if phrase not in text]
    errors.extend(f"missing Step 1/Step 2 boundary phrase: {label}" for label in missing)
    return readiness_gate(
        "paper_step_boundary",
        passed=not errors,
        evidence=[label for label in STEP1_PAPER_STEP_BOUNDARY_REQUIRED_PHRASES if label not in missing],
        errors=errors,
    )


def parse_opaque_baseline_table(path: Path) -> Dict[str, List[str]]:
    rows: Dict[str, List[str]] = {}
    line_pattern = re.compile(r"^\s*(?P<label>[^&]+?)\s*&\s*(?P<values>.+?)\\\\")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = line_pattern.match(line)
        if not match:
            continue
        label = match.group("label").strip()
        if label in {"Baseline"}:
            continue
        values = [part.strip() for part in match.group("values").split("&")]
        if len(values) == len(BASELINE_TABLE_METRICS):
            rows[label] = values
    return rows


def parse_latex_code_table(path: Path) -> Dict[str, List[str]]:
    rows: Dict[str, List[str]] = {}
    line_pattern = re.compile(r"^\s*\\code\{(?P<label>[^}]+)\}\s*&\s*(?P<values>.+?)\\\\")
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = line_pattern.match(line)
        if not match:
            continue
        rows[match.group("label").strip()] = [part.strip() for part in match.group("values").split("&")]
    return rows


def prompt_direction(standard: float | None, hygiene: float | None) -> str:
    if standard is None or hygiene is None:
        return ""
    delta = hygiene - standard
    if delta >= 0.03:
        return "Gain"
    if delta > 0.0:
        return "Slight gain"
    if delta <= -0.03:
        return "Decline"
    if delta < 0.0:
        return "Slight decline"
    return "No change"


def rows_for(rows: Sequence[Mapping[str, str]], **criteria: str) -> List[Mapping[str, str]]:
    return [row for row in rows if all(row.get(field, "") == value for field, value in criteria.items())]


def compare_table_rows(
    *,
    table_name: str,
    actual_rows: Mapping[str, List[str]],
    expected_rows: Mapping[str, List[str]],
    errors: List[str],
    evidence: List[str],
) -> None:
    for label, expected in expected_rows.items():
        evidence.append(f"{table_name}:{label}={','.join(expected)}")
        actual = actual_rows.get(label)
        if actual is None:
            errors.append(f"{table_name} missing row: {label}")
        elif actual[: len(expected)] != expected:
            errors.append(f"{table_name} row mismatch for {label}: actual={actual[:len(expected)]} expected={expected}")


def paper_frontier_results_consistency_gate(artifact_dir: Path, paper_dir: Path) -> Dict[str, Any]:
    scored_path = artifact_dir / "outputs" / "frontier_main_opaque_scored.csv"
    try:
        scored_rows = read_csv_rows(scored_path)
    except FileNotFoundError:
        return readiness_gate("paper_frontier_results_consistency", passed=False, errors=["missing frontier scored CSV"])
    except csv.Error as exc:
        return readiness_gate("paper_frontier_results_consistency", passed=False, errors=[f"could not parse frontier scored CSV: {exc}"])
    errors: List[str] = []
    evidence: List[str] = [f"scored_rows={len(scored_rows)}"]
    required_columns = {
        "model",
        "family",
        "condition",
        "prompt_condition",
        "operational_epistemic_escape",
        "belief_correctness",
        "evidence_cleanliness",
        "verification_action_score",
    }
    actual_columns = set(scored_rows[0]) if scored_rows else set()
    missing_columns = sorted(required_columns - actual_columns)
    if missing_columns:
        errors.extend(f"frontier scored CSV missing column: {column}" for column in missing_columns)
        return readiness_gate("paper_frontier_results_consistency", passed=False, evidence=evidence, errors=errors)
    models = [model for model in FRONTIER_TABLE_MODELS if rows_for(scored_rows, model=model)]
    if len(models) < len(FRONTIER_TABLE_MODELS):
        missing = sorted(set(FRONTIER_TABLE_MODELS) - set(models))
        errors.extend(f"frontier scored CSV missing model rows: {model}" for model in missing)
    main_expected: Dict[str, List[str]] = {}
    family_expected: Dict[str, List[str]] = {}
    condition_expected: Dict[str, List[str]] = {}
    prompt_expected: Dict[str, List[str]] = {}
    for model in models:
        model_rows = rows_for(scored_rows, model=model)
        op_values = [value for row in model_rows if (value := parse_float(row.get("operational_epistemic_escape", ""))) is not None]
        n = len(op_values)
        ci_low, ci_high = wilson_interval(sum(op_values), n)
        main_expected[model] = [
            str(n),
            format_metric(mean_numeric(model_rows, "operational_epistemic_escape")),
            f"[{ci_low:.3f}, {ci_high:.3f}]",
            format_metric(mean_numeric(model_rows, "belief_correctness")),
            format_metric(mean_numeric(model_rows, "evidence_cleanliness")),
            format_metric(mean_numeric(model_rows, "verification_action_score")),
        ]
        family_expected[model] = [
            format_metric(mean_numeric(rows_for(model_rows, family=family), "operational_epistemic_escape"))
            for family in FRONTIER_TABLE_FAMILIES
        ]
        condition_expected[model] = [
            format_metric(mean_numeric(rows_for(model_rows, condition=condition), "operational_epistemic_escape"))
            for condition in FRONTIER_TABLE_CONDITIONS
        ]
        standard = mean_numeric(rows_for(model_rows, prompt_condition="standard_answer"), "operational_epistemic_escape")
        hygiene = mean_numeric(rows_for(model_rows, prompt_condition="epistemic_hygiene_instruction"), "operational_epistemic_escape")
        prompt_expected[model] = [format_metric(standard), format_metric(hygiene), prompt_direction(standard, hygiene)]
    table_specs = [
        ("main_model_decomposition", paper_dir / "tables" / "main_model_decomposition.tex", main_expected),
        ("task_family_breakdown", paper_dir / "tables" / "task_family_breakdown.tex", family_expected),
        ("evidence_condition_breakdown", paper_dir / "tables" / "evidence_condition_breakdown.tex", condition_expected),
        ("prompt_hygiene", paper_dir / "tables" / "prompt_hygiene.tex", prompt_expected),
    ]
    for table_name, path, expected_rows in table_specs:
        try:
            actual_rows = parse_latex_code_table(path)
        except OSError as exc:
            errors.append(f"could not read {table_name}: {exc}")
            continue
        compare_table_rows(table_name=table_name, actual_rows=actual_rows, expected_rows=expected_rows, errors=errors, evidence=evidence)
    return readiness_gate(
        "paper_frontier_results_consistency",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def baseline_table_consistency_gate(artifact_dir: Path, paper_dir: Path) -> Dict[str, Any]:
    table_path = paper_dir / "tables" / "opaque_baselines.tex"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        paper_rows = parse_opaque_baseline_table(table_path)
    except OSError as exc:
        return readiness_gate("paper_baseline_table_consistency", passed=False, errors=[f"could not read opaque baseline table: {exc}"])
    for baseline in BASELINE_NAMES:
        display = BASELINE_DISPLAY_NAMES[baseline]
        path = artifact_dir / "baselines" / f"{baseline}.csv"
        try:
            rows = read_csv_rows(path)
        except FileNotFoundError:
            errors.append(f"missing artifact baseline CSV for paper check: baselines/{baseline}.csv")
            continue
        except csv.Error as exc:
            errors.append(f"could not parse artifact baseline CSV baselines/{baseline}.csv: {exc}")
            continue
        expected = [format_metric(mean_numeric(rows, metric)) for metric in BASELINE_TABLE_METRICS]
        actual = paper_rows.get(display)
        evidence.append(f"{display}={','.join(expected)}")
        if actual is None:
            errors.append(f"paper opaque baseline table missing row: {display}")
            continue
        if actual != expected:
            errors.append(f"paper opaque baseline table row mismatch for {display}: actual={actual} expected={expected}")
    limitations_path = paper_dir / "sections" / "09_limitations.tex"
    try:
        limitations = limitations_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        errors.append(f"could not read limitations for baseline prose check: {exc}")
    else:
        metadata_rows = read_csv_rows(artifact_dir / "baselines" / "metadata_only.csv") if (artifact_dir / "baselines" / "metadata_only.csv").exists() else []
        heuristic_rows = read_csv_rows(artifact_dir / "baselines" / "simple_heuristic.csv") if (artifact_dir / "baselines" / "simple_heuristic.csv").exists() else []
        metadata_escape = format_metric(mean_numeric(metadata_rows, "operational_epistemic_escape"))
        heuristic_escape = format_metric(mean_numeric(heuristic_rows, "operational_epistemic_escape"))
        expected_phrase = f"metadata-only and simple heuristic baselines reach {metadata_escape} and {heuristic_escape} operational escape"
        evidence.append(f"baseline_prose={expected_phrase}")
        if expected_phrase not in limitations:
            errors.append("paper limitations baseline prose does not match current artifact baseline escape values")
    return readiness_gate(
        "paper_baseline_table_consistency",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def paper_action_audit_table_consistency_gate(artifact_dir: Path, paper_dir: Path) -> Dict[str, Any]:
    audit_path = artifact_dir / "audits" / "active_verification_action_audit_summary.csv"
    section_path = paper_dir / "sections" / "06_active_verification_case.tex"
    appendix_path = paper_dir / "appendix" / "d_extra_tables.tex"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        rows = read_csv_rows(audit_path)
    except FileNotFoundError:
        return readiness_gate("paper_action_audit_table_consistency", passed=False, errors=["missing active-verification action-audit summary CSV"])
    except csv.Error as exc:
        return readiness_gate("paper_action_audit_table_consistency", passed=False, errors=[f"could not parse action-audit summary CSV: {exc}"])
    model_rows = {row.get("model", ""): row for row in rows if row.get("grouping") == "model" and row.get("model", "")}
    if len(model_rows) < 5:
        errors.append(f"active-verification action-audit summary has fewer than 5 model rows: {len(model_rows)}")
    try:
        section_rows = parse_latex_code_table(section_path)
    except OSError as exc:
        section_rows = {}
        errors.append(f"could not read active-verification section table: {exc}")
    try:
        appendix_rows = parse_latex_code_table(appendix_path)
    except OSError as exc:
        appendix_rows = {}
        errors.append(f"could not read active-verification appendix table: {exc}")
    action_gate_values: List[float] = []
    for model, row in sorted(model_rows.items()):
        expected_full = [
            format_count(parse_float(row.get("n", ""))),
            format_metric(parse_float(row.get("action_gate_pass", ""))),
            format_metric(parse_float(row.get("missing_primary_action", ""))),
            format_metric(parse_float(row.get("missing_contradiction_action", ""))),
            format_metric(parse_float(row.get("missing_trace_source_action", ""))),
        ]
        action_gate = parse_float(row.get("action_gate_pass", ""))
        if action_gate is not None:
            action_gate_values.append(action_gate)
        evidence.append(f"{model}={','.join(expected_full)}")
        section_actual = section_rows.get(model)
        if section_actual is None:
            errors.append(f"active-verification section table missing model row: {model}")
        elif section_actual[:4] != expected_full[:4]:
            errors.append(f"active-verification section table mismatch for {model}: actual={section_actual[:4]} expected={expected_full[:4]}")
        appendix_actual = appendix_rows.get(model)
        if appendix_actual is None:
            errors.append(f"active-verification appendix table missing model row: {model}")
        elif appendix_actual[:5] != expected_full:
            errors.append(f"active-verification appendix table mismatch for {model}: actual={appendix_actual[:5]} expected={expected_full}")
    try:
        section_text = section_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        section_text = ""
    if action_gate_values:
        expected_range = f"Action-gate pass rates range from {min(action_gate_values):.3f} to {max(action_gate_values):.3f} across models"
        evidence.append(f"action_gate_range={min(action_gate_values):.3f}-{max(action_gate_values):.3f}")
        if expected_range not in section_text:
            errors.append(f"active-verification section missing action-gate range phrase: {expected_range}")
    return readiness_gate(
        "paper_action_audit_table_consistency",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def count_binary_label(rows: Sequence[Mapping[str, str]], field: str) -> int:
    return sum(1 for row in rows if parse_label(row.get(field, "")) == 1.0)


def paper_codex_triage_consistency_gate(artifact_dir: Path, paper_dir: Path) -> Dict[str, Any]:
    audit_path = artifact_dir / "audits" / "active_verification_pilot_codex_xhigh_audit_50.csv"
    section_path = paper_dir / "sections" / "06_active_verification_case.tex"
    errors: List[str] = []
    evidence: List[str] = []
    try:
        rows = read_csv_rows(audit_path)
    except FileNotFoundError:
        rows = []
        errors.append("missing Codex-assisted active-verification triage CSV")
    except csv.Error as exc:
        rows = []
        errors.append(f"could not parse Codex-assisted active-verification triage CSV: {exc}")
    try:
        section = section_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        section = ""
        errors.append(f"could not read active-verification section: {exc}")
    counts = {
        "rows": len(rows),
        "semantically_useful_action": count_binary_label(rows, "semantically_useful_action"),
        "machine_executable_action": count_binary_label(rows, "machine_executable_action"),
        "required_action_type_present": count_binary_label(rows, "required_action_type_present"),
        "scorer_too_strict": count_binary_label(rows, "scorer_too_strict"),
    }
    evidence.extend(f"{key}={value}" for key, value in counts.items())
    if rows and len(rows) != 50:
        errors.append(f"Codex-assisted active-verification triage row count is {len(rows)}; expected 50")
    expected_phrases = [
        f"all {counts['rows']} sampled action sets as semantically useful",
        f"{counts['machine_executable_action']}/{counts['rows']} as machine executable",
        f"{counts['required_action_type_present']}/{counts['rows']} as containing the required action type",
        f"{counts['scorer_too_strict']}/{counts['rows']} automatic rejections as plausibly too strict",
        "This audit is not treated as human validation",
    ]
    for phrase in expected_phrases:
        if phrase and phrase not in section:
            errors.append(f"active-verification section missing Codex triage phrase: {phrase}")
    return readiness_gate(
        "paper_codex_triage_consistency",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def paper_human_audit_claim_consistency_gate(artifact_dir: Path, paper_dir: Path) -> Dict[str, Any]:
    summary_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_summary.json"
    validation_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_validation.json"
    labels_path = artifact_dir / "audits" / "active_verification_human_audit.csv"
    section_path = paper_dir / "sections" / "06_active_verification_case.tex"
    limitations_path = paper_dir / "sections" / "09_limitations.tex"
    errors: List[str] = []
    evidence: List[str] = []
    summary, summary_error = load_json_file(summary_path)
    validation, validation_error = load_json_file(validation_path)
    if validation_error or validation is None:
        errors.append(validation_error or "invalid human-audit validation JSON")
        validation = {}
    if summary_error or summary is None:
        if validation.get("status") == "complete":
            errors.append(summary_error or "missing human-audit summary JSON")
        summary = {}
    status = str(summary.get("status") or validation.get("status") or "")
    n_labeled = int(summary.get("n_labeled", validation.get("n_complete_rows", 0)) or 0)
    n_rows = int(summary.get("n_rows", validation.get("n_rows", validation.get("reference_rows", 0))) or 0)
    evidence.extend([f"human_audit_status={status or 'missing'}", f"n_labeled={n_labeled}", f"n_rows={n_rows}"])
    try:
        section = section_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        section = ""
        errors.append(f"could not read active-verification section: {exc}")
    try:
        limitations = limitations_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        limitations = ""
        errors.append(f"could not read limitations section: {exc}")
    claim_boundary_phrases = [
        "This audit is not treated as human validation",
        "we do not treat it as a substitute for independent human annotation",
    ]
    if status == "complete" and n_labeled >= 50:
        try:
            rows = read_csv_rows(labels_path)
        except FileNotFoundError:
            rows = []
            errors.append("missing active-verification human-audit CSV for paper claim check")
        except csv.Error as exc:
            rows = []
            errors.append(f"could not parse active-verification human-audit CSV for paper claim check: {exc}")
        denominator = len(rows) or n_labeled
        counts = {
            "semantically_useful_action": count_binary_label(rows, "semantically_useful_action"),
            "machine_executable_action": count_binary_label(rows, "machine_executable_action"),
            "required_action_type_present": count_binary_label(rows, "required_action_type_present"),
            "scorer_too_strict": count_binary_label(rows, "scorer_too_strict"),
        }
        evidence.extend(f"{field}={value}/{denominator}" for field, value in counts.items())
        expected_phrases = [
            "single-auditor pilot human audit",
            "human-labeled active-verification audit",
            f"{counts['semantically_useful_action']}/{denominator} as semantically useful",
            f"{counts['machine_executable_action']}/{denominator} as machine executable",
            f"{counts['required_action_type_present']}/{denominator} as containing the required action type",
            f"{counts['scorer_too_strict']}/{denominator} automatic rejections as plausibly too strict",
        ]
        for phrase in expected_phrases:
            if phrase not in section:
                errors.append(f"active-verification section missing human-audit phrase: {phrase}")
    else:
        if not any(phrase in section or phrase in limitations for phrase in claim_boundary_phrases):
            errors.append("active-verification section or limitations must state incomplete audit is not human validation")
        else:
            evidence.append("incomplete_audit_claim_boundary=True")
        misleading_complete_phrases = [
            "single-auditor pilot human audit labels",
            "human-labeled active-verification audit labels",
        ]
        for phrase in misleading_complete_phrases:
            if phrase in section:
                errors.append(f"active-verification section makes completed human-audit claim before completion: {phrase}")
    return readiness_gate(
        "paper_human_audit_claim_consistency",
        passed=not errors,
        evidence=evidence,
        errors=errors,
    )


def paper_todo_gate(paper_dir: Path) -> Dict[str, Any]:
    errors: List[str] = []
    patterns = [re.compile(pattern, re.IGNORECASE) for pattern in [r"\bTODO\b", r"\bTBD\b", r"\bFIXME\b", r"\[TODO", r"needs citation"]]
    scanned = 0
    for path in paper_source_files(paper_dir):
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            if pattern.search(text):
                errors.append(f"{relative_to_root(path, paper_dir)} contains unresolved marker `{pattern.pattern}`")
                break
    return readiness_gate(
        "paper_unresolved_markers",
        passed=not errors,
        evidence=[f"scanned_files={scanned}"],
        errors=errors,
    )


def paper_pdf_freshness_gate(paper_dir: Path) -> Dict[str, Any]:
    pdf = paper_dir / "main.pdf"
    if not pdf.exists():
        return readiness_gate("paper_pdf_freshness", passed=False, errors=["missing main.pdf"])
    sources = paper_source_files(paper_dir)
    if not sources:
        return readiness_gate("paper_pdf_freshness", passed=False, errors=["no paper .tex/.bib sources found"])
    latest_source = max(sources, key=lambda path: path.stat().st_mtime)
    pdf_mtime = pdf.stat().st_mtime
    source_mtime = latest_source.stat().st_mtime
    stale = pdf_mtime < source_mtime
    return readiness_gate(
        "paper_pdf_freshness",
        passed=not stale,
        evidence=[
            f"main_pdf_mtime={pdf_mtime:.6f}",
            f"latest_source={relative_to_root(latest_source, paper_dir)}",
            f"latest_source_mtime={source_mtime:.6f}",
        ],
        errors=[f"main.pdf is older than {relative_to_root(latest_source, paper_dir)}; rebuild paper"] if stale else [],
    )


def paper_semantic_id_leakage_gate(paper_dir: Path) -> Dict[str, Any]:
    errors: List[str] = []
    scanned = 0
    for path in paper_source_files(paper_dir):
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in STEP1_SEMANTIC_ID_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{relative_to_root(path, paper_dir)} contains semantic ID marker `{label}`")
                break
    return readiness_gate(
        "paper_semantic_id_leakage",
        passed=not errors,
        evidence=[f"scanned_files={scanned}"],
        errors=errors,
    )


def paper_readiness_gates(paper_dir: Path) -> List[Dict[str, Any]]:
    paper_dir = paper_dir.resolve()
    return [
        paper_required_files_gate(paper_dir),
        paper_positioning_gate(paper_dir),
        paper_artifact_appendix_gate(paper_dir),
        paper_step_boundary_gate(paper_dir),
        paper_todo_gate(paper_dir),
        paper_pdf_freshness_gate(paper_dir),
        paper_semantic_id_leakage_gate(paper_dir),
    ]


def write_step1_readiness_markdown(path: Path, report: Mapping[str, Any]) -> None:
    lines = [
        "# EHA Step 1 Readiness Check",
        "",
        f"- status: `{report['status']}`",
        f"- artifact_dir: `{report['artifact_dir']}`",
        f"- paper_dir: `{report.get('paper_dir', 'not checked')}`",
        "",
        "## Prompt-To-Artifact Checklist",
        "",
        "| Requirement | Gate | Status | Evidence | Errors |",
        "| --- | --- | --- | --- | --- |",
    ]
    for gate in report["gates"]:
        evidence = "<br>".join(str(item) for item in gate.get("evidence", [])) or "-"
        errors = "<br>".join(str(item) for item in gate.get("errors", [])) or "-"
        lines.append(f"| {gate['name']} | `{gate['name']}` | `{gate['status']}` | {evidence} | {errors} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report is a release gate, not a substitute for reading the artifact. A `ready` status means the checked Step 1 release requirements are present and internally consistent. A `blocked` status means at least one release requirement is missing, incomplete, or weakly verified.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def step1_readiness_check(
    *,
    artifact_dir: Path,
    out_dir: Path,
    paper_dir: Path | None = None,
    output_stem: str = "eha_step1_readiness_check",
) -> Dict[str, Any]:
    artifact_dir = artifact_dir.resolve()
    gates = [
        required_file_gate(artifact_dir),
        file_manifest_gate(artifact_dir),
        baseline_gate(artifact_dir),
        generated_lore_schema_gate(artifact_dir),
        active_verification_human_audit_gate(artifact_dir),
        active_verification_human_audit_worksheet_gate(artifact_dir),
        active_verification_human_audit_model_blinded_worksheet_gate(artifact_dir),
        active_verification_human_audit_protocol_gate(artifact_dir),
        active_verification_human_audit_attestation_gate(artifact_dir),
        active_verification_human_audit_paper_update_gate(artifact_dir),
        active_verification_human_audit_model_blinded_packet_gate(artifact_dir),
        active_verification_human_audit_review_gate(artifact_dir),
        active_verification_human_audit_finalize_script_gate(artifact_dir),
        step1_release_verify_script_gate(artifact_dir),
        artifact_manifest_gate(artifact_dir),
        opaque_main_outputs_gate(artifact_dir),
        artifact_readme_scope_gate(artifact_dir),
        minimal_example_gate(artifact_dir),
        semantic_id_leakage_gate(artifact_dir),
    ]
    resolved_paper_dir = paper_dir.resolve() if paper_dir is not None else None
    if resolved_paper_dir is not None:
        gates.extend(paper_readiness_gates(resolved_paper_dir))
        gates.append(paper_frontier_results_consistency_gate(artifact_dir, resolved_paper_dir))
        gates.append(baseline_table_consistency_gate(artifact_dir, resolved_paper_dir))
        gates.append(paper_action_audit_table_consistency_gate(artifact_dir, resolved_paper_dir))
        gates.append(paper_codex_triage_consistency_gate(artifact_dir, resolved_paper_dir))
        gates.append(paper_human_audit_claim_consistency_gate(artifact_dir, resolved_paper_dir))
    status = "ready" if all(gate["status"] == "pass" for gate in gates) else "blocked"
    report = {
        "status": status,
        "artifact_dir": str(artifact_dir),
        "paper_dir": str(resolved_paper_dir) if resolved_paper_dir is not None else None,
        "gates": gates,
        "errors": [error for gate in gates for error in gate.get("errors", [])],
        "warnings": [warning for gate in gates for warning in gate.get("warnings", [])],
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / f"{output_stem}.json", report)
    write_step1_readiness_markdown(out_dir / f"{output_stem}.md", report)
    return report


@app.command("baselines")
def baselines_command(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-step1-baselines-2026-05-15"), help="Baseline report output directory."),
    baselines: str = typer.Option(",".join(BASELINE_NAMES), help="Comma-separated baseline names."),
) -> None:
    run_step1_baselines(task_dir=task_dir, out_dir=out_dir, baselines=split_csv(baselines))
    console.print(f"[green]Wrote Step 1 baselines[/green] to {out_dir}")


@app.command("artifact-package")
def artifact_package_command(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    frontier_main_dir: Path = typer.Option(Path("results/reports-eha-frontier-main-opaque-2026-05-15"), help="Opaque frontier main report directory."),
    baseline_dir: Path = typer.Option(Path("results/reports-eha-step1-baselines-2026-05-15"), help="Step 1 baseline report directory."),
    generated_lore_dir: Path = typer.Option(Path("results/reports-eha-generated-lore-role-audit-opaque-2026-05-15"), help="Generated-lore audit directory."),
    active_verification_dir: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15"), help="Active-verification audit directory."),
    out_dir: Path = typer.Option(Path("../artifact"), help="Release artifact package directory."),
) -> None:
    build_artifact_package(
        task_dir=task_dir,
        frontier_main_dir=frontier_main_dir,
        baseline_dir=baseline_dir,
        generated_lore_dir=generated_lore_dir,
        active_verification_dir=active_verification_dir,
        out_dir=out_dir,
    )
    console.print(f"[green]Wrote Step 1 artifact package[/green] to {out_dir}")


@app.command("step1-readiness-check")
def step1_readiness_check_command(
    artifact_dir: Path = typer.Option(Path("../artifact"), help="Step 1 release artifact package directory."),
    paper_dir: Path = typer.Option(Path("../paper"), help="Paper directory to include in readiness checks."),
    out_dir: Path = typer.Option(Path("../reports"), help="Directory for readiness check outputs."),
    output_stem: str = typer.Option("eha_step1_readiness_check", help="Output filename stem for JSON/Markdown reports."),
) -> None:
    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=out_dir, output_stem=output_stem)
    color = "green" if report["status"] == "ready" else "yellow"
    console.print(f"[{color}]Step 1 readiness: {report['status']}[/{color}]")


@app.command("active-verification-audit-package")
def active_verification_audit_package_command(
    sample_csv: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv"), help="Prepared human-audit label sheet."),
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared ERT task directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15"), help="Directory for audit context and guidelines."),
) -> None:
    build_active_verification_audit_package(sample_csv=sample_csv, task_dir=task_dir, out_dir=out_dir)
    console.print(f"[green]Wrote active-verification audit package[/green] to {out_dir}")


@app.command("summarize-active-verification-human-audit")
def summarize_active_verification_human_audit_command(
    labels_csv: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv"), help="Human-labeled audit CSV."),
    out_dir: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15"), help="Directory for audit summary outputs."),
    output_stem: str = typer.Option("active_verification_pilot_human_audit_summary", help="Output filename stem for CSV/JSON summaries."),
) -> None:
    summarize_active_verification_human_audit(labels_csv=labels_csv, out_dir=out_dir, output_stem=output_stem)
    console.print(f"[green]Wrote active-verification human-audit summary[/green] to {out_dir}")


@app.command("validate-active-verification-human-audit")
def validate_active_verification_human_audit_command(
    labels_csv: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv"), help="Human-labeled audit CSV."),
    reference_csv: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv"), help="Original audit CSV used to check non-label columns."),
    out_dir: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15"), help="Directory for validation outputs."),
    output_stem: str = typer.Option("active_verification_pilot_human_audit_validation", help="Output filename stem for validation JSON/Markdown/CSV."),
) -> None:
    report = validate_active_verification_human_audit(labels_csv=labels_csv, reference_csv=reference_csv, out_dir=out_dir, output_stem=output_stem)
    color = "green" if report["status"] == "complete" else "yellow"
    console.print(f"[{color}]Validated active-verification human audit: {report['status']}[/{color}]")


@app.command("import-active-verification-human-audit-worksheet")
def import_active_verification_human_audit_worksheet_command(
    worksheet_csv: Path = typer.Option(Path("../artifact/audits/active_verification_pilot_human_audit_worksheet_50.csv"), help="Wide human-audit worksheet with labels and context."),
    reference_csv: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv"), help="Original audit CSV used to preserve non-label columns."),
    out_csv: Path = typer.Option(Path("../artifact/audits/active_verification_human_audit.csv"), help="Strict label CSV to write for validation/finalization."),
) -> None:
    try:
        manifest = import_active_verification_human_audit_worksheet(
            worksheet_csv=worksheet_csv,
            reference_csv=reference_csv,
            out_csv=out_csv,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]Imported active-verification worksheet[/green]: {manifest['out_csv']}")


@app.command("import-active-verification-model-blinded-human-audit-worksheet")
def import_active_verification_model_blinded_human_audit_worksheet_command(
    worksheet_csv: Path = typer.Option(Path("../artifact/audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv"), help="Model-blinded human-audit worksheet with labels and context."),
    reference_csv: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv"), help="Original audit CSV used to preserve non-label columns."),
    out_csv: Path = typer.Option(Path("../artifact/audits/active_verification_human_audit.csv"), help="Strict label CSV to write for validation/finalization."),
) -> None:
    try:
        manifest = import_active_verification_model_blinded_human_audit_worksheet(
            worksheet_csv=worksheet_csv,
            reference_csv=reference_csv,
            out_csv=out_csv,
        )
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]Imported model-blinded active-verification worksheet[/green]: {manifest['out_csv']}")


@app.command("finalize-active-verification-human-audit")
def finalize_active_verification_human_audit_command(
    labels_csv: Path = typer.Option(Path("../artifact/audits/active_verification_human_audit.csv"), help="Human-labeled audit CSV to import."),
    reference_csv: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv"), help="Original audit CSV used to check non-label columns."),
    out_dir: Path = typer.Option(Path("results/reports-eha-active-verification-audit-opaque-2026-05-15"), help="Directory for imported labels, validation, and summary outputs."),
) -> None:
    try:
        manifest = finalize_active_verification_human_audit(labels_csv=labels_csv, reference_csv=reference_csv, out_dir=out_dir)
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]Finalized active-verification human audit[/green]: {manifest['imported_labels_csv']}")


if __name__ == "__main__":
    app()
