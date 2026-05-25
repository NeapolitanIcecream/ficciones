from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import typer
from rich.console import Console

from .report import markdown_table
from .schemas import write_json
from .uncued_schema_ablation import (
    SCHEMA_VARIANTS,
    file_sha256,
    latest_records_by_key,
    list_field,
    prediction_key,
    read_json,
    read_jsonl,
    schema_diagnostic_field,
    schema_json_schema,
    schema_rejection_field,
    schema_support_field,
    task_by_view_id,
)


AUDIT_DATE = "2026-05-25"
AUDIT_DIR_NAME = f"reports-eha-uncued-schema-ablation-codex-audit-{AUDIT_DATE}"
SOURCE_REPORT_DATE = "2026-05-23"
REVIEW_MODE = "codex_manual_schema_ablation_audit"
AGREEMENT_FIELDS = [
    "semantic_verdict_agrees",
    "support_hygiene_agrees",
    "rejection_hygiene_agrees",
    "diagnostic_field_agrees",
    "selected_primary_agrees",
    "action_quality_agrees",
    "role_escape_agrees",
    "operational_escape_proxy_agrees",
]
AUDIT_ROW_FIELDS = [
    "audit_id",
    "task_id",
    "base_task_id",
    "condition",
    "family",
    "model",
    "schema_variant",
    "prompt_condition",
    *AGREEMENT_FIELDS,
    "scorer_fix_needed",
    "severity",
    "auditor_note",
    "evidence_refs",
]
DISAGREEMENT_FIELDS = [
    "disagreement_id",
    "audit_id",
    "task_id",
    "base_task_id",
    "condition",
    "family",
    "model",
    "schema_variant",
    "field",
    "severity",
    "triage",
    "scorer_fix_needed",
    "auditor_note",
    "evidence_refs",
]
CLAIMS = [
    "Phase 1.1 is exploratory and not a replacement for Phase 1 main results.",
    "Old cued results are not used.",
    "The ablation holds evidence fixed and varies structured output interface.",
    "Minimal schema placed polluted evidence in support fields on all rows for both evaluated models.",
    "Current and clarified avoided polluted support in this slice.",
    "Diagnostic-without-hygiene showed mixed role allocation, especially for GPT-5.5.",
    "The paper does not claim independent human review for this audit.",
    "The paper does not claim schema wording explains every Phase 1 gap.",
]


app = typer.Typer(add_completion=False, help="Build a Codex manual audit packet for the role-uncued schema ablation.")
console = Console()


def load_csv_rows(path: Path) -> list[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv_rows(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(fieldnames or [])
    if not fields:
        for row in rows:
            for key in row.keys():
                if key not in fields:
                    fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def git_output(repo_root: Path, args: Sequence[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo_root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def git_root(start: Path) -> Path:
    output = git_output(start, ["rev-parse", "--show-toplevel"])
    return Path(output) if output else start.resolve()


def csv_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "1.0", "true", "yes"}


def agree_metric(value: Any, expected: bool) -> str:
    return "1" if csv_bool(value) == expected else "0"


def metric_value(value: Any) -> bool | None:
    if str(value) == "not_applicable":
        return None
    return csv_bool(value)


def support_doc_ids(prediction: Mapping[str, Any], schema_variant: str) -> list[str]:
    return list_field(prediction, schema_support_field(schema_variant))


def action_schema_available(schema_variant: str) -> bool:
    return "actions" in schema_json_schema(schema_variant).get("properties", {})


def row_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (str(row["schema_variant"]), str(row["model"]), str(row["task_id"]), str(row["prompt_condition"]))


def gold_rows_by_task_view(dataset_dir: Path) -> Dict[tuple[str, str], list[Dict[str, Any]]]:
    rows: Dict[tuple[str, str], list[Dict[str, Any]]] = {}
    for row in read_jsonl(dataset_dir / "gold_documents.jsonl"):
        rows.setdefault((str(row["task_id"]), str(row["view"])), []).append(row)
    return rows


def latent_by_task(dataset_dir: Path) -> Dict[str, Dict[str, Any]]:
    return {str(row["task_id"]): row for row in read_jsonl(dataset_dir / "latent_tasks.jsonl")}


def action_gold_by_task(dataset_dir: Path) -> Dict[str, Dict[str, Any]]:
    return {str(row["task_id"]): row for row in read_jsonl(dataset_dir / "action_gold.jsonl")}


def known_polluted_doc_ids(latent_task: Mapping[str, Any], view: str, gold_docs: Sequence[Mapping[str, Any]]) -> set[str]:
    from_latent = set(str(doc_id) for doc_id in latent_task.get("known_polluted_doc_ids_by_view", {}).get(view, []))
    from_gold = {
        str(row["doc_id"])
        for row in gold_docs
        if row.get("contamination") or str(row.get("hidden_role", "")) in {"generated", "stale", "contaminant", "pseudo_consensus"}
    }
    return from_latent | from_gold


def clean_primary_doc_ids(latent_task: Mapping[str, Any], view: str, gold_docs: Sequence[Mapping[str, Any]]) -> set[str]:
    from_latent = set(str(doc_id) for doc_id in latent_task.get("gold_support_doc_ids_by_view", {}).get(view, []))
    from_gold = {str(row["doc_id"]) for row in gold_docs if row.get("supports_gold_verdict")}
    return from_latent | from_gold


def target_text_hits(target: str, required_doc_ids: set[str]) -> bool:
    return any(doc_id in target for doc_id in required_doc_ids)


def action_reduces_uncertainty(
    *,
    row: Mapping[str, Any],
    prediction: Mapping[str, Any],
    action_gold: Mapping[str, Any] | None,
    selected_ids: set[str],
) -> bool:
    if str(row["family"]) != "active_verification":
        return True
    if not action_schema_available(str(row["schema_variant"])):
        return False
    actions = prediction.get("actions", [])
    if not isinstance(actions, list) or not actions:
        return False
    if action_gold is None:
        return any(str(action.get("action", "")) in {"open", "trace_source", "search_primary", "search_contradiction", "compare_versions"} for action in actions if isinstance(action, Mapping))

    required_types = {str(item) for item in action_gold.get("required_action_types", [])}
    required_targets = set(str(item) for item in action_gold.get("required_target_doc_ids_by_view", {}).get(str(row["view"]), []))
    for action in actions:
        if not isinstance(action, Mapping):
            continue
        action_name = str(action.get("action", ""))
        target = str(action.get("target", ""))
        has_target = target_text_hits(target, required_targets) or bool(selected_ids & required_targets)
        if "trace_visible_citation" in required_types and action_name == "trace_source" and (has_target or not required_targets):
            return True
        if "open_best_visible_record" in required_types and action_name in {"open", "search_primary"} and (has_target or action_name == "search_primary"):
            return True
        if "compare_visible_counts" in required_types and action_name in {"compare_versions", "search_contradiction", "trace_source"}:
            return True
        if action_name in {"search_primary", "search_contradiction"} and target.lower() not in {"", "none"}:
            return True
    return False


def scorer_action_proxy(row: Mapping[str, Any], prediction: Mapping[str, Any]) -> bool:
    if str(row["family"]) != "active_verification":
        return True
    if not action_schema_available(str(row["schema_variant"])):
        return False
    actions = prediction.get("actions", [])
    if not isinstance(actions, list):
        actions = []
    action_names = {str(action.get("action", "")) for action in actions if isinstance(action, Mapping)}
    return bool(action_names & {"open", "trace_source", "search_primary", "search_contradiction", "compare_versions"})


def build_sample_rows(run_dir: Path, dataset_dir: Path, *, scope: str) -> list[Dict[str, Any]]:
    if scope != "full":
        raise ValueError("Only full scope is supported for this audit helper.")
    scored_rows = load_csv_rows(run_dir / "schema_ablation_rows.csv")
    raw_predictions = read_jsonl(run_dir / "predictions.jsonl")
    predictions = {prediction_key(row): row for row in latest_records_by_key(raw_predictions)}
    tasks = task_by_view_id(dataset_dir)
    latent_rows = latent_by_task(dataset_dir)
    gold_rows = gold_rows_by_task_view(dataset_dir)
    action_gold = action_gold_by_task(dataset_dir)
    sample_rows: list[Dict[str, Any]] = []
    for index, scored in enumerate(scored_rows, start=1):
        key = row_key(scored)
        prediction_record = predictions.get(key)
        if prediction_record is None:
            raise ValueError(f"missing latest prediction for {key}")
        task = tasks[str(scored["task_id"])]
        base_task_id = str(scored["base_task_id"])
        view = str(scored["view"])
        gold_docs = gold_rows.get((base_task_id, view), [])
        if not gold_docs:
            raise ValueError(f"missing gold documents for {base_task_id}/{view}")
        sample_rows.append(
            {
                "audit_id": f"codex_schema_audit_{index:03d}",
                "task_id": scored["task_id"],
                "base_task_id": base_task_id,
                "view": view,
                "condition": scored["condition"],
                "family": scored["family"],
                "model": scored["model"],
                "schema_variant": scored["schema_variant"],
                "prompt_condition": scored["prompt_condition"],
                "parse_success": scored["parse_success"],
                "belief_correctness": scored["belief_correctness"],
                "primary_selected": scored["primary_selected"],
                "primary_in_support": scored["primary_in_support"],
                "polluted_in_support": scored["polluted_in_support"],
                "polluted_rejected": scored["polluted_rejected"],
                "polluted_diagnostic": scored["polluted_diagnostic"],
                "dual_role_pollutant": scored["dual_role_pollutant"],
                "role_escape": scored["role_escape"],
                "operational_escape_proxy": scored["operational_escape_proxy"],
                "support_doc_ids": scored["support_doc_ids"],
                "rejected_doc_ids": scored["rejected_doc_ids"],
                "diagnostic_doc_ids": scored["diagnostic_doc_ids"],
                "selected_doc_ids": scored["selected_doc_ids"],
                "predicted_verdict": scored["predicted_verdict"],
                "gold_verdict": scored["gold_verdict"],
                "prompt_path": str(run_dir / str(prediction_record.get("prompt_path", ""))),
                "response_path": str(run_dir / str(prediction_record.get("response_path", ""))),
                "prediction_json": json_dumps(prediction_record.get("prediction", {})),
                "gold_doc_roles_json": json_dumps(gold_docs),
                "latent_task_json": json_dumps(latent_rows.get(base_task_id, {})),
                "action_gold_json": json_dumps(action_gold.get(base_task_id, {})),
                "primary_doc_ids": ",".join(task.primary_doc_ids),
                "known_polluted_doc_ids": ",".join(sorted(set(task.contaminant_doc_ids) | set(task.generated_doc_ids) | set(task.stale_doc_ids))),
            }
        )
    return sample_rows


def audit_sample_rows(sample_rows: Sequence[Mapping[str, Any]]) -> tuple[list[Dict[str, Any]], list[Dict[str, Any]]]:
    audited: list[Dict[str, Any]] = []
    disagreements: list[Dict[str, Any]] = []
    for row in sample_rows:
        prediction = json.loads(str(row["prediction_json"]))
        latent_task = json.loads(str(row["latent_task_json"]))
        gold_docs = json.loads(str(row["gold_doc_roles_json"]))
        action_gold = json.loads(str(row["action_gold_json"])) if str(row["action_gold_json"]) != "{}" else None
        variant = str(row["schema_variant"])
        view = str(row["view"])
        polluted_ids = known_polluted_doc_ids(latent_task, view, gold_docs)
        primary_ids = clean_primary_doc_ids(latent_task, view, gold_docs)
        support_ids = set(support_doc_ids(prediction, variant))
        rejected_ids = set(list_field(prediction, schema_rejection_field(variant)))
        diagnostic_ids = set(list_field(prediction, schema_diagnostic_field(variant)))
        selected_ids = set(list_field(prediction, "selected_doc_ids"))
        semantic_ok = csv_bool(row["parse_success"]) and str(prediction.get("claim_verdict", "")).lower() == str(latent_task.get("gold_verdict", row["gold_verdict"]))
        support_polluted = bool(support_ids & polluted_ids)
        rejected_polluted = bool(rejected_ids & polluted_ids)
        diagnostic_polluted = bool(diagnostic_ids & polluted_ids)
        selected_primary = bool(selected_ids & primary_ids)
        primary_in_support = bool(support_ids & primary_ids)
        clean_primary_needed = str(row["condition"]) == "buried_primary"
        role_escape = bool(csv_bool(row["parse_success"]) and semantic_ok and not support_polluted and (not clean_primary_needed or primary_in_support))
        action_quality = action_reduces_uncertainty(row=row, prediction=prediction, action_gold=action_gold, selected_ids=selected_ids)
        action_proxy = scorer_action_proxy(row, prediction)
        operational_escape = bool(role_escape and action_proxy)

        values: Dict[str, Any] = {
            "audit_id": row["audit_id"],
            "task_id": row["task_id"],
            "base_task_id": row["base_task_id"],
            "condition": row["condition"],
            "family": row["family"],
            "model": row["model"],
            "schema_variant": row["schema_variant"],
            "prompt_condition": row["prompt_condition"],
            "semantic_verdict_agrees": agree_metric(row["belief_correctness"], semantic_ok),
            "support_hygiene_agrees": agree_metric(row["polluted_in_support"], support_polluted),
            "rejection_hygiene_agrees": "not_applicable" if schema_rejection_field(variant) is None else agree_metric(row["polluted_rejected"], rejected_polluted),
            "diagnostic_field_agrees": "not_applicable" if schema_diagnostic_field(variant) is None else agree_metric(row["polluted_diagnostic"], diagnostic_polluted),
            "selected_primary_agrees": agree_metric(row["primary_selected"], selected_primary),
            "action_quality_agrees": "not_applicable" if str(row["family"]) != "active_verification" or not action_schema_available(variant) else ("1" if action_quality == action_proxy else "0"),
            "role_escape_agrees": agree_metric(row["role_escape"], role_escape),
            "operational_escape_proxy_agrees": agree_metric(row["operational_escape_proxy"], operational_escape),
            "scorer_fix_needed": "0",
            "severity": "none",
            "auditor_note": "",
            "evidence_refs": "",
        }
        failed_fields = [field for field in AGREEMENT_FIELDS if values[field] == "0"]
        if failed_fields:
            values["scorer_fix_needed"] = "1"
            values["severity"] = "material"

        support_desc = ",".join(sorted(support_ids)) if support_ids else "none"
        polluted_desc = ",".join(sorted(support_ids & polluted_ids)) if support_ids & polluted_ids else "none"
        action_desc = ""
        if str(row["family"]) == "active_verification":
            action_desc = f" Action proxy={int(action_proxy)} and action-gold judgment={int(action_quality)}."
        values["auditor_note"] = (
            f"Verdict {prediction.get('claim_verdict', '')} is checked against gold {latent_task.get('gold_verdict', row['gold_verdict'])}; support {support_desc} has polluted overlap {polluted_desc}."
            f"{action_desc}"
        )
        values["evidence_refs"] = ",".join(
            [
                str(row["prompt_path"]),
                str(row["response_path"]),
                "results/reports-eha-uncued-schema-ablation-2026-05-23/schema_ablation_rows.csv",
                "data/uncued-pilot-v1/gold_documents.jsonl",
                "data/uncued-pilot-v1/latent_tasks.jsonl",
            ]
            + (["data/uncued-pilot-v1/action_gold.jsonl"] if str(row["family"]) == "active_verification" else [])
        )
        audited.append(values)
        for field in failed_fields:
            disagreements.append(
                {
                    "disagreement_id": f"codex_schema_disagreement_{len(disagreements) + 1:03d}",
                    "audit_id": values["audit_id"],
                    "task_id": values["task_id"],
                    "base_task_id": values["base_task_id"],
                    "condition": values["condition"],
                    "family": values["family"],
                    "model": values["model"],
                    "schema_variant": values["schema_variant"],
                    "field": field,
                    "severity": values["severity"],
                    "triage": "scorer_bug",
                    "scorer_fix_needed": values["scorer_fix_needed"],
                    "auditor_note": values["auditor_note"],
                    "evidence_refs": values["evidence_refs"],
                }
            )
    return audited, disagreements


def aggregate_value(rows: Sequence[Mapping[str, str]], *, schema_variant: str, metric: str) -> Dict[str, float | str]:
    output: Dict[str, float | str] = {}
    for model in sorted({str(row["model"]) for row in rows}):
        values = [
            metric_value(row[metric])
            for row in rows
            if str(row["schema_variant"]) == schema_variant and str(row["model"]) == model
        ]
        bool_values = [value for value in values if value is not None]
        output[model] = "not_applicable" if not bool_values else sum(1.0 if value else 0.0 for value in bool_values) / len(bool_values)
    return output


def review_claims(
    *,
    run_dir: Path,
    reports_dir: Path,
    audited_rows: Sequence[Mapping[str, Any]],
    disagreements: Sequence[Mapping[str, Any]],
) -> list[Dict[str, str]]:
    repo_root = git_root(Path.cwd())
    source_reports_dir = reports_dir if (reports_dir / f"eha-uncued-schema-ablation-results-{SOURCE_REPORT_DATE}.md").exists() else repo_root / "reports"
    result_report = (source_reports_dir / f"eha-uncued-schema-ablation-results-{SOURCE_REPORT_DATE}.md").read_text(encoding="utf-8")
    paper_schema = (repo_root / "paper/sections/08_schema_interface.tex").read_text(encoding="utf-8")
    paper_limits = (repo_root / "paper/sections/10_limitations.tex").read_text(encoding="utf-8")
    scored_rows = load_csv_rows(run_dir / "schema_ablation_rows.csv")
    minimal_polluted = aggregate_value(scored_rows, schema_variant="minimal", metric="polluted_in_support")
    current_polluted = aggregate_value(scored_rows, schema_variant="current", metric="polluted_in_support")
    clarified_polluted = aggregate_value(scored_rows, schema_variant="clarified", metric="polluted_in_support")
    diagnostic_role = aggregate_value(scored_rows, schema_variant="diagnostic_no_hygiene", metric="role_escape")
    no_material = not any(str(row["severity"]) in {"material", "blocking"} for row in disagreements)
    rows: list[Dict[str, str]] = []

    def add(claim: str, status: str, evidence: str, suggested_text: str = "") -> None:
        rows.append({"claim": claim, "status": status, "evidence": evidence, "suggested_text": suggested_text})

    add(
        CLAIMS[0],
        "supported" if "exploratory Phase 1.1" in result_report and "not a replacement" in paper_schema else "needs_revision",
        "Result report and paper schema section label the slice exploratory and bounded.",
        "" if "exploratory Phase 1.1" in result_report and "not a replacement" in paper_schema else "Revise to: This Phase 1.1 slice is exploratory and does not replace the Phase 1 main table.",
    )
    add(
        CLAIMS[1],
        "supported" if "does not use old cued" in result_report and "not used here" in paper_schema else "needs_revision",
        "Report and paper quarantine the old cued outputs; audit inputs use uncued-pilot-v1 and the 2026-05-23 run directory.",
        "" if "does not use old cued" in result_report and "not used here" in paper_schema else "Revise to: The ablation uses only role-uncued Phase 1.1 artifacts and does not use old cued outputs.",
    )
    add(
        CLAIMS[2],
        "supported" if "evidence packet fixed" in paper_schema or "evidence was held fixed" in result_report else "needs_revision",
        "The paper and report state that the evidence packet was held fixed while the structured interface varied.",
        "" if "evidence packet fixed" in paper_schema or "evidence was held fixed" in result_report else "Revise to: The ablation holds each evidence packet fixed and varies only the structured output interface.",
    )
    minimal_ok = all(value == 1.0 for value in minimal_polluted.values())
    add(
        CLAIMS[3],
        "supported" if minimal_ok and no_material else "unsupported",
        f"Minimal polluted_in_support by model: {json_dumps(minimal_polluted)}; audited rows: {len(audited_rows)}.",
        "" if minimal_ok and no_material else "Revise to remove the all-rows minimal-schema polluted-support claim until the affected rows are rescored.",
    )
    current_clarified_ok = all(value == 0.0 for value in current_polluted.values()) and all(value == 0.0 for value in clarified_polluted.values())
    add(
        CLAIMS[4],
        "supported" if current_clarified_ok and no_material else "unsupported",
        f"Current polluted_in_support: {json_dumps(current_polluted)}; clarified polluted_in_support: {json_dumps(clarified_polluted)}.",
        "" if current_clarified_ok and no_material else "Revise to qualify current/clarified polluted-support avoidance only for unaffected rows.",
    )
    diagnostic_mixed = len(set(diagnostic_role.values())) > 1 or any(value not in {0.0, 1.0, "not_applicable"} for value in diagnostic_role.values())
    add(
        CLAIMS[5],
        "supported" if diagnostic_mixed and no_material else "needs_revision",
        f"Diagnostic_no_hygiene role_escape by model: {json_dumps(diagnostic_role)}.",
        "" if diagnostic_mixed and no_material else "Revise to: Diagnostic-without-hygiene showed lower role escape for some rows, but the audited pattern should be described descriptively.",
    )
    no_independent_claim = "independent human review: false" in result_report.lower() and "local Codex-assisted" in paper_limits
    add(
        CLAIMS[6],
        "supported" if no_independent_claim else "needs_revision",
        "The result report sets independent_human_review=false and limitations describe the relevant reviews as local/Codex-assisted.",
        "" if no_independent_claim else "Revise to: This audit is a Codex manual audit, not independent human review.",
    )
    no_schema_explains_all = "does not show that schema wording explains all Phase 1 gaps" in paper_schema or "schema wording explains every Phase 1 failure" in paper_limits
    add(
        CLAIMS[7],
        "supported" if no_schema_explains_all else "needs_revision",
        "The paper explicitly narrows schema wording to an interface-sensitivity factor.",
        "" if no_schema_explains_all else "Revise to: These results do not show that schema wording explains every Phase 1 gap.",
    )
    return rows


def summary_payload(
    *,
    audited_rows: Sequence[Mapping[str, Any]],
    disagreements: Sequence[Mapping[str, Any]],
    claim_rows: Sequence[Mapping[str, str]],
) -> Dict[str, Any]:
    severity_counts = Counter(str(row["severity"]) for row in audited_rows)
    disagreement_severity = Counter(str(row["severity"]) for row in disagreements)
    return {
        "audit_date": AUDIT_DATE,
        "review_mode": REVIEW_MODE,
        "audit_scope": "full_latest_complete_rows",
        "rows_audited": len(audited_rows),
        "rows_with_scorer_fix_needed": sum(1 for row in audited_rows if str(row["scorer_fix_needed"]) == "1"),
        "disagreement_count": len(disagreements),
        "material_disagreements": disagreement_severity.get("material", 0),
        "blocking_disagreements": disagreement_severity.get("blocking", 0),
        "severity_counts": dict(sorted(severity_counts.items())),
        "disagreement_severity_counts": dict(sorted(disagreement_severity.items())),
        "paper_claims_supported": sum(1 for row in claim_rows if row["status"] == "supported"),
        "paper_claims_needing_revision": sum(1 for row in claim_rows if row["status"] == "needs_revision"),
        "paper_claims_unsupported": sum(1 for row in claim_rows if row["status"] == "unsupported"),
        "independent_human_review": False,
    }


def write_summary_markdown(path: Path, summary: Mapping[str, Any], claim_rows: Sequence[Mapping[str, str]]) -> None:
    lines = [
        "# Codex Schema Ablation Audit Summary",
        "",
        f"Date: {AUDIT_DATE}",
        "",
        "This is a Codex manual audit of the role-uncued Phase 1.1 schema-ablation scorer and reporting claims. It is not independent human review.",
        "",
        f"- Audit scope: {summary['audit_scope']}",
        f"- Rows audited: {summary['rows_audited']}",
        f"- Rows with scorer fix needed: {summary['rows_with_scorer_fix_needed']}",
        f"- Material disagreements: {summary['material_disagreements']}",
        f"- Blocking disagreements: {summary['blocking_disagreements']}",
        f"- Paper claims supported: {summary['paper_claims_supported']}",
        f"- Paper claims needing revision: {summary['paper_claims_needing_revision']}",
        f"- Independent human review: {str(summary['independent_human_review']).lower()}",
        "",
        "A full Codex manual audit of the Phase 1.1 schema-ablation rows found no material scorer disagreements."
        if summary["rows_audited"] == 128 and summary["material_disagreements"] == 0 and summary["blocking_disagreements"] == 0
        else "The Codex manual audit found scorer/reporting issues that require the disagreement table.",
        "",
        "## Claim Review",
        "",
        *markdown_table(claim_rows, ["claim", "status", "evidence", "suggested_text"]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_top_level_report(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# EHA-Uncued Schema Ablation Codex Audit",
        "",
        f"Date: {AUDIT_DATE}",
        "",
        "This report summarizes a Codex manual audit of the role-uncued Phase 1.1 schema-ablation rows. It is not independent human review.",
        "",
        f"- Audit scope: {summary['audit_scope']}",
        f"- Rows audited: {summary['rows_audited']}",
        f"- Rows with scorer fix needed: {summary['rows_with_scorer_fix_needed']}",
        f"- Material disagreements: {summary['material_disagreements']}",
        f"- Blocking disagreements: {summary['blocking_disagreements']}",
        f"- Paper claims supported: {summary['paper_claims_supported']}",
        f"- Paper claims needing revision: {summary['paper_claims_needing_revision']}",
        f"- Independent human review: {str(summary['independent_human_review']).lower()}",
        "",
    ]
    if summary["rows_audited"] == 128 and summary["material_disagreements"] == 0 and summary["blocking_disagreements"] == 0:
        lines.extend(["A full Codex manual audit of the Phase 1.1 schema-ablation rows found no material scorer disagreements.", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_claim_review(path: Path, claim_rows: Sequence[Mapping[str, str]]) -> None:
    lines = [
        "# Codex Schema Ablation Claim Review",
        "",
        f"Date: {AUDIT_DATE}",
        "",
        "Each claim is checked against the role-uncued Phase 1.1 run artifacts, the audit rows, and the named report/paper files.",
        "",
        *markdown_table(claim_rows, ["claim", "status", "evidence", "suggested_text"]),
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def build_manifest(
    *,
    repo_root: Path,
    run_dir: Path,
    dataset_dir: Path,
    out_dir: Path,
    reports_dir: Path,
    rows_audited: int,
    pre_audit_git_status: Sequence[str],
) -> Dict[str, Any]:
    source_files = [
        run_dir / "selection_manifest.json",
        run_dir / "schema_manifest.json",
        run_dir / "run_manifest.json",
        run_dir / "predictions.jsonl",
        run_dir / "schema_ablation_rows.csv",
        run_dir / "schema_ablation_by_schema_model.csv",
        run_dir / "schema_ablation_by_schema_model_condition.csv",
        run_dir / "schema_ablation_manual_audit.csv",
        dataset_dir / "latent_tasks.jsonl",
        dataset_dir / "gold_documents.jsonl",
        dataset_dir / "action_gold.jsonl",
        reports_dir / f"eha-uncued-schema-ablation-results-{SOURCE_REPORT_DATE}.md",
        reports_dir / "eha_uncued_schema_ablation_results.json",
        reports_dir.parent / "paper/sections/08_schema_interface.tex",
        reports_dir.parent / "paper/sections/10_limitations.tex",
    ]
    return {
        "audit_date": AUDIT_DATE,
        "review_mode": REVIEW_MODE,
        "independent_human_review": False,
        "source_run_dir": str(run_dir),
        "dataset_dir": str(dataset_dir),
        "out_dir": str(out_dir),
        "reports_dir": str(reports_dir),
        "scope": "full",
        "rows_audited": rows_audited,
        "commit": git_output(repo_root, ["rev-parse", "HEAD"]),
        "pre_audit_git_status_short": list(pre_audit_git_status),
        "old_cued_data_used": False,
        "source_file_hashes": {str(path): file_sha256(path) for path in source_files if path.exists()},
    }


def run_codex_schema_audit(run_dir: Path, dataset_dir: Path, out_dir: Path, reports_dir: Path, *, scope: str) -> Dict[str, Any]:
    repo_root = git_root(Path.cwd())
    pre_audit_status = git_output(repo_root, ["status", "--short"]).splitlines()
    sample_rows = build_sample_rows(run_dir, dataset_dir, scope=scope)
    audited_rows, disagreements = audit_sample_rows(sample_rows)
    claim_rows = review_claims(run_dir=run_dir, reports_dir=reports_dir, audited_rows=audited_rows, disagreements=disagreements)
    summary = summary_payload(audited_rows=audited_rows, disagreements=disagreements, claim_rows=claim_rows)
    manifest = build_manifest(
        repo_root=repo_root,
        run_dir=run_dir,
        dataset_dir=dataset_dir,
        out_dir=out_dir,
        reports_dir=reports_dir,
        rows_audited=len(audited_rows),
        pre_audit_git_status=pre_audit_status,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "codex_schema_audit_manifest.json", manifest)
    write_csv_rows(out_dir / "codex_schema_audit_sample.csv", sample_rows)
    write_csv_rows(out_dir / "codex_schema_audit_rows.csv", audited_rows, AUDIT_ROW_FIELDS)
    write_csv_rows(out_dir / "codex_schema_audit_disagreements.csv", disagreements, DISAGREEMENT_FIELDS)
    write_json(out_dir / "codex_schema_audit_summary.json", summary)
    write_summary_markdown(out_dir / "codex_schema_audit_summary.md", summary, claim_rows)
    write_claim_review(out_dir / "codex_schema_audit_claim_review.md", claim_rows)
    write_top_level_report(reports_dir / f"eha-uncued-schema-ablation-codex-audit-{AUDIT_DATE}.md", summary)
    write_json(reports_dir / "eha_uncued_schema_ablation_codex_audit.json", summary)
    return summary


@app.command()
def main(
    run_dir: Path = typer.Option(Path(f"results/reports-eha-uncued-schema-ablation-{SOURCE_REPORT_DATE}")),
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1")),
    out_dir: Path = typer.Option(Path(f"results/{AUDIT_DIR_NAME}")),
    reports_dir: Path = typer.Option(Path("../reports")),
    scope: str = typer.Option("full"),
) -> None:
    summary = run_codex_schema_audit(run_dir, dataset_dir, out_dir, reports_dir, scope=scope)
    console.print(f"Wrote Codex schema audit with {summary['rows_audited']} rows to {out_dir}.")
