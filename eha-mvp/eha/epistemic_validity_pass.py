from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .epistemic_resilience import EpistemicRunRecord, EpistemicTask, markdown_table, read_tasks
from .report import write_csv
from .schemas import model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Build offline validity-pass artifacts for Epistemic Resilience Table v1.")
console = Console()

TARGET_AUDIT_BUCKETS = ("generated_lore", "false_consensus", "buried_primary", "active_verification")
VALIDITY_METRICS = (
    "parse_success",
    "epistemic_escape",
    "belief_correctness",
    "evidence_cleanliness",
    "uncertainty_discipline",
    "primary_seeking_rate",
    "duplicate_avoidance_rate",
    "generated_lore_avoidance_rate",
    "contradiction_seeking_rate",
    "evidence_value_score",
    "primary_action_rate",
    "contradiction_action_rate",
    "generated_lore_trace_rate",
)


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_records(path: Path) -> List[EpistemicRunRecord]:
    return [EpistemicRunRecord.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def row_key(row: Mapping[str, Any]) -> tuple[str, str, str]:
    return (str(row["task_id"]), str(row["model"]), str(row["prompt_condition"]))


def record_key(record: EpistemicRunRecord) -> tuple[str, str, str]:
    return (record.task_id, record.model, record.prompt_condition)


def mean_float(rows: Sequence[Mapping[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows if row.get(key) not in {None, ""}]
    return sum(values) / len(values) if values else 0.0


def usage_number(record: EpistemicRunRecord, key: str) -> float:
    usage = record.usage or {}
    if key == "reasoning_tokens":
        details = usage.get("completion_tokens_details") or {}
        value = details.get("reasoning_tokens")
    else:
        value = usage.get(key)
    return float(value) if isinstance(value, (int, float)) else 0.0


def parse_error_category(parse_error: str) -> str:
    error = parse_error.lower()
    if not error:
        return "none"
    if "expecting value: line 1 column 1" in error:
        return "empty_or_non_json_response"
    if "unterminated string" in error:
        return "truncated_or_unterminated_json"
    if "expecting ',' delimiter" in error:
        return "malformed_or_truncated_json"
    if "validation" in error or "field required" in error:
        return "schema_validation_error"
    return "other_json_parse_error"


def task_doc_map(task: EpistemicTask) -> Dict[str, Dict[str, Any]]:
    return {doc.doc_id: model_to_dict(doc) for doc in task.documents}


def split_doc_ids(value: str) -> List[str]:
    return [item for item in value.split(",") if item]


def top_counter_value(counter: Counter[str]) -> str:
    if not counter:
        return ""
    value, count = counter.most_common(1)[0]
    return f"{value} ({count})"


def aggregate_parse_repair_audit(scored_rows: Sequence[Mapping[str, str]], records: Sequence[EpistemicRunRecord]) -> List[Dict[str, Any]]:
    records_by_key = {record_key(record): record for record in records}
    grouped: Dict[tuple[str, str, str, str], List[Mapping[str, str]]] = defaultdict(list)
    for row in scored_rows:
        grouped[(row["model"], row["prompt_condition"], row["family"], row["condition"])].append(row)

    output: List[Dict[str, Any]] = []
    for (model, prompt, family, condition), rows in sorted(grouped.items()):
        group_records = [records_by_key[row_key(row)] for row in rows if row_key(row) in records_by_key]
        failed_records = [record for record in group_records if not record.parse_success]
        categories = Counter(parse_error_category(record.parse_error or "") for record in failed_records)
        item: Dict[str, Any] = {
            "model": model,
            "prompt_condition": prompt,
            "family": family,
            "condition": condition,
            "n": len(rows),
            "original_parse_success": mean_float(rows, "parse_success"),
            "parse_failure_count": len(failed_records),
            "original_epistemic_escape": mean_float(rows, "epistemic_escape"),
            "original_belief_correctness": mean_float(rows, "belief_correctness"),
            "original_evidence_cleanliness": mean_float(rows, "evidence_cleanliness"),
            "mean_completion_tokens": mean([usage_number(record, "completion_tokens") for record in group_records]),
            "mean_reasoning_tokens": mean([usage_number(record, "reasoning_tokens") for record in group_records]),
            "mean_prompt_tokens": mean([usage_number(record, "prompt_tokens") for record in group_records]),
            "top_parse_error_category": top_counter_value(categories),
            "raw_response_available": 0,
            "repair_attempted": 0,
            "repaired_parse_success": "",
            "repaired_epistemic_escape": "",
            "interpretation": parse_repair_interpretation(len(failed_records)),
        }
        output.append(item)
    return output


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def parse_repair_interpretation(parse_failures: int) -> str:
    if parse_failures == 0:
        return "No offline repair needed for this slice."
    return "Repair not run: final run did not persist raw responses; rerun with response artifacts before claiming repaired metrics."


def taxonomy_labels(row: Mapping[str, str], task: EpistemicTask) -> List[str]:
    supporting = split_doc_ids(row.get("supporting_evidence", ""))
    docs_by_id = {doc.doc_id: doc for doc in task.documents}
    labels: List[str] = []
    support_set = set(supporting)
    if support_set & set(task.contaminant_doc_ids):
        labels.append("contaminated_support")
    if support_set & set(task.generated_doc_ids):
        labels.append("generated_lore_cited")
    if support_set & set(task.stale_doc_ids):
        labels.append("stale_evidence_cited")
    roots = [docs_by_id[doc_id].upstream_root or doc_id for doc_id in supporting if doc_id in docs_by_id]
    if len(roots) != len(set(roots)):
        labels.append("duplicate_upstream_treated_as_independent")
    if not labels:
        labels.append("scorer_edge_case_candidate")
    return labels


def evidence_cleanliness_failure_rows(scored_rows: Sequence[Mapping[str, str]], tasks_by_id: Mapping[str, EpistemicTask]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for row in scored_rows:
        if float(row["evidence_cleanliness"]) != 0.0:
            continue
        task = tasks_by_id[row["task_id"]]
        supporting = split_doc_ids(row.get("supporting_evidence", ""))
        docs_by_id = {doc.doc_id: doc for doc in task.documents}
        roles = [docs_by_id[doc_id].role for doc_id in supporting if doc_id in docs_by_id]
        labels = taxonomy_labels(row, task)
        dirty = sorted(set(supporting) & set(task.contaminant_doc_ids + task.generated_doc_ids + task.stale_doc_ids))
        output.append(
            {
                "model": row["model"],
                "prompt_condition": row["prompt_condition"],
                "family": row["family"],
                "condition": row["condition"],
                "task_id": row["task_id"],
                "gold_verdict": row["gold_verdict"],
                "predicted_verdict": row["predicted_verdict"],
                "epistemic_escape": row["epistemic_escape"],
                "belief_correctness": row["belief_correctness"],
                "supporting_evidence": ",".join(supporting),
                "supporting_roles": ",".join(roles),
                "dirty_support_doc_ids": ",".join(dirty),
                "taxonomy_labels": ",".join(labels),
                "scorer_edge_case_candidate": 1 if labels == ["scorer_edge_case_candidate"] else 0,
                "question": task.question,
            }
        )
    return output


def audit_bucket(row: Mapping[str, str]) -> str | None:
    if row["condition"] in {"generated_lore", "false_consensus", "buried_primary"}:
        return row["condition"]
    if row["family"] == "active_verification":
        return "active_verification"
    return None


def sample_priority(row: Mapping[str, str]) -> tuple[int, int, int, str, str, str]:
    parse_failure = 1 if float(row["parse_success"]) == 0.0 else 0
    evidence_failure = 1 if float(row["evidence_cleanliness"]) == 0.0 else 0
    escape_failure = 1 if float(row["epistemic_escape"]) == 0.0 else 0
    return (-evidence_failure, -escape_failure, -parse_failure, row["model"], row["prompt_condition"], row["task_id"])


def compact_doc(doc: Mapping[str, Any]) -> Dict[str, Any]:
    body = str(doc.get("body", ""))
    return {
        "doc_id": doc.get("doc_id", ""),
        "title": doc.get("title", ""),
        "source_type": doc.get("source_type", ""),
        "timestamp": doc.get("timestamp", ""),
        "role": doc.get("role", ""),
        "value_score": doc.get("value_score", ""),
        "upstream_root": doc.get("upstream_root", ""),
        "visible_citations": doc.get("visible_citations", []),
        "body_excerpt": body[:650],
    }


def human_audit_sample(
    scored_rows: Sequence[Mapping[str, str]],
    records: Sequence[EpistemicRunRecord],
    tasks_by_id: Mapping[str, EpistemicTask],
    per_bucket: int,
) -> List[Dict[str, Any]]:
    records_by_key = {record_key(record): record for record in records}
    selected: List[Dict[str, Any]] = []
    used_keys: set[tuple[str, str, str]] = set()
    for bucket in TARGET_AUDIT_BUCKETS:
        candidates = [row for row in scored_rows if audit_bucket(row) == bucket and row_key(row) not in used_keys]
        candidates = sorted(candidates, key=sample_priority)
        for row in candidates[:per_bucket]:
            key = row_key(row)
            record = records_by_key[key]
            task = tasks_by_id[row["task_id"]]
            doc_lookup = task_doc_map(task)
            cited_doc_ids = sorted(
                set(split_doc_ids(row.get("supporting_evidence", "")))
                | set(split_doc_ids(row.get("selected_doc_ids", "")))
                | set(record.prediction.rejected_evidence)
            )
            selected.append(
                {
                    "audit_bucket": bucket,
                    "task_id": task.task_id,
                    "family": task.family,
                    "condition": task.condition,
                    "model": record.model,
                    "prompt_condition": record.prompt_condition,
                    "question": task.question,
                    "gold": {
                        "verdict": task.gold_verdict,
                        "primary_doc_ids": task.primary_doc_ids,
                        "contaminant_doc_ids": task.contaminant_doc_ids,
                        "generated_doc_ids": task.generated_doc_ids,
                        "stale_doc_ids": task.stale_doc_ids,
                        "contradiction_doc_ids": task.contradiction_doc_ids,
                    },
                    "scorer_decision": {
                        metric: float(row[metric]) for metric in VALIDITY_METRICS if metric in row and row[metric] != ""
                    },
                    "prediction": model_to_dict(record.prediction),
                    "cited_documents": [compact_doc(doc_lookup[doc_id]) for doc_id in cited_doc_ids if doc_id in doc_lookup],
                    "visible_documents": [compact_doc(doc) for doc in doc_lookup.values()],
                    "audit_form": {
                        "verdict_reasonable": "",
                        "supporting_evidence_actually_supports_verdict": "",
                        "contamination_label_reasonable": "",
                        "rejected_evidence_misclassified_as_support": "",
                        "generated_lore_label_too_strict": "",
                        "scorer_agreement": "",
                        "notes": "",
                    },
                }
            )
            used_keys.add(key)
    return selected


def filtered_slice(rows: Sequence[Mapping[str, str]], slice_name: str) -> List[Mapping[str, str]]:
    if slice_name == "all":
        return list(rows)
    if slice_name == "evidence_selection":
        return [row for row in rows if row["family"] == "evidence_selection"]
    if slice_name == "generated_lore":
        return [row for row in rows if row["condition"] == "generated_lore"]
    if slice_name == "buried_primary":
        return [row for row in rows if row["condition"] == "buried_primary"]
    if slice_name == "false_consensus":
        return [row for row in rows if row["condition"] == "false_consensus"]
    if slice_name == "active_verification":
        return [row for row in rows if row["family"] == "active_verification"]
    raise ValueError(f"unknown slice: {slice_name}")


def heuristic_appendix_rows(
    scored_rows: Sequence[Mapping[str, str]],
    heuristic_rows: Sequence[Mapping[str, str]],
) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    slices = ("all", "evidence_selection", "generated_lore", "buried_primary", "false_consensus", "active_verification")
    combined = [(scored_rows, 0, 1), (heuristic_rows, 1, 0)]
    for rows, uses_gold_metadata, is_model_comparable in combined:
        groups: Dict[tuple[str, str], List[Mapping[str, str]]] = defaultdict(list)
        for row in rows:
            groups[(row["model"], row["prompt_condition"])].append(row)
        for (model, prompt), group_rows in sorted(groups.items()):
            for slice_name in slices:
                subset = filtered_slice(group_rows, slice_name)
                if not subset:
                    continue
                output.append(
                    {
                        "model_or_baseline": model,
                        "prompt_condition": prompt,
                        "slice": slice_name,
                        "n": len(subset),
                        "epistemic_escape": mean_float(subset, "epistemic_escape"),
                        "evidence_cleanliness": mean_float(subset, "evidence_cleanliness"),
                        "primary_seeking_rate": mean_float(subset, "primary_seeking_rate"),
                        "duplicate_avoidance_rate": mean_float(subset, "duplicate_avoidance_rate"),
                        "generated_lore_avoidance_rate": mean_float(subset, "generated_lore_avoidance_rate"),
                        "evidence_value_score": mean_float(subset, "evidence_value_score"),
                        "active_primary_action_rate": mean_float(subset, "primary_action_rate"),
                        "parse_success": mean_float(subset, "parse_success"),
                        "uses_gold_metadata": uses_gold_metadata,
                        "is_model_comparable": is_model_comparable,
                        "interpretation": (
                            "Gold-metadata heuristic for plumbing and upper-bound checks; not a fair agent-visible model baseline."
                            if uses_gold_metadata
                            else "Model run scored from visible prompt output."
                        ),
                    }
                )
    return output


def write_figures_manifest(path: Path) -> None:
    lines = [
        "# Paper Figures Manifest",
        "",
        "| Figure/Table | Source artifact | Use | Caveat |",
        "| --- | --- | --- | --- |",
        "| Main epistemic resilience table | `../reports-epistemic-resilience-v1/main_table.csv` | Primary model x prompt family-average escape table. | Do not interpret as absolute model ranking because parse and schema compliance differ by model. |",
        "| Parse failure caveat table | `parse_repair_audit.csv` | Shows where parse failures concentrate and why repaired metrics are not yet available. | Raw responses were not persisted in the final run; repair requires rerun. |",
        "| Evidence cleanliness failure mechanism table | `evidence_cleanliness_failure_taxonomy.csv` | Audits dirty support citations by condition/family/model. | Automatic taxonomy should be validated against the human sample. |",
        "| Human audit pack | `human_audit_sample.jsonl` | 80-case manual review pack for generated lore, false consensus, buried primary, and active verification. | Requires human completion before being used as validation evidence. |",
        "| Heuristic baseline appendix | `heuristic_baseline_appendix.csv` | Compares existing heuristic smoke-test slices with LLM slices. | The heuristic uses gold metadata and is not a fair model baseline. |",
        "| Generated lore profile | `../reports-epistemic-resilience-v1/by_condition.csv`, `heuristic_baseline_appendix.csv` | Isolates generated-lore avoidance and escape. | Generated-lore labels are synthetic and need manual audit. |",
        "| Active verification profile | `../reports-epistemic-resilience-v1/by_family.csv`, `heuristic_baseline_appendix.csv` | Shows action-selection failures separate from answer correctness. | Active-verification scorer should be checked for prompt/tool affordance artifacts. |",
        "| Matrix L4 evidence-environment case study | `../reports-matrix-v1.3/l4_primary_recovery_audit.csv` | Connects earlier RAG retrieval results to evidence environment construction. | Use as mechanism case study, not as the main ERT v1 result. |",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_prompt_to_artifact_checklist(path: Path, audit_manifest: Mapping[str, Any]) -> None:
    lines = [
        "# Validity Pass Prompt-to-Artifact Checklist",
        "",
        "| Requirement | Evidence | Status |",
        "| --- | --- | --- |",
        "| Understand the current stage report. | Input report `../../../reports/eha-epistemic-resilience-v1-stage-report-2026-05-14.md` was used to identify the ERT v1 results and caveats. | Done |",
        "| Continue from the user-provided research memo without expanding the benchmark. | This pass creates validation artifacts only; `task_content_changed=false` and `gold_labels_changed=false` in `audit_manifest.json`. | Done |",
        "| Audit `gpt-5-mini` parse failures. | `parse_repair_audit.csv` groups parse success, parse errors, and token usage by model/prompt/family/condition. | Done, offline only |",
        "| Do not claim repaired `gpt-5-mini` metrics without raw responses. | `parse_repair_audit.csv` sets `repair_attempted=0` and `raw_response_available=0`; summary states rerun is required for repair. | Done |",
        "| Export manual audit pack. | `human_audit_sample.jsonl` contains 80 cases across generated_lore, false_consensus, buried_primary, and active_verification. | Done |",
        "| Analyze evidence cleanliness failures. | `evidence_cleanliness_failure_taxonomy.csv` contains row-level dirty-support taxonomy. | Done |",
        "| Promote heuristic smoke test into appendix-quality comparison. | `heuristic_baseline_appendix.csv` reports comparable slices and flags heuristic gold-metadata use. | Done |",
        "| Prepare paper figure/table manifest. | `paper_figures_manifest.md` maps figures to source artifacts and caveats. | Done |",
        "| Preserve machine-readable diagnostics. | `audit_manifest.json` records input paths, row counts, sample counts, and non-mutation flags. | Done |",
    ]
    lines.extend(["", "## Audit Snapshot", "", "```json", json.dumps(audit_manifest, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(
    path: Path,
    *,
    parse_rows: Sequence[Mapping[str, Any]],
    taxonomy_rows: Sequence[Mapping[str, Any]],
    human_rows: Sequence[Mapping[str, Any]],
    heuristic_rows: Sequence[Mapping[str, Any]],
    audit_manifest: Mapping[str, Any],
) -> None:
    gpt5_parse = [row for row in parse_rows if row["model"] == "openai/gpt-5-mini"]
    parse_failures = sum(int(row["parse_failure_count"]) for row in gpt5_parse)
    gpt54_taxonomy = [row for row in taxonomy_rows if row["model"] == "openai/gpt-5.4-mini"]
    taxonomy_counts = Counter(label for row in taxonomy_rows for label in str(row["taxonomy_labels"]).split(",") if label)
    bucket_counts = Counter(row["audit_bucket"] for row in human_rows)
    heuristic_all = [row for row in heuristic_rows if row["model_or_baseline"] == "heuristic-sim" and row["slice"] == "all"]

    lines = [
        "# EHA Validity Pass",
        "",
        "This is an offline validity pass for Epistemic Resilience Table v1. It does not add tasks, alter gold labels, or make new API calls.",
        "",
        "## Outputs",
        "",
        "| Artifact | Purpose |",
        "| --- | --- |",
        "| `parse_repair_audit.csv` | Groups original parse failures and token patterns; records that repair was not attempted because raw responses are unavailable. |",
        "| `human_audit_sample.jsonl` | 80-case manual audit pack with task, prediction, scorer metrics, visible evidence, and blank audit form. |",
        "| `evidence_cleanliness_failure_taxonomy.csv` | Row-level taxonomy for dirty supporting evidence. |",
        "| `heuristic_baseline_appendix.csv` | Appendix-ready heuristic-vs-model slice comparison with explicit gold-metadata caveat. |",
        "| `paper_figures_manifest.md` | Figure/table source map and caveats. |",
        "| `prompt_to_artifact_checklist.md` | Requirement-to-artifact checklist for this pass. |",
        "| `audit_manifest.json` | Machine-readable diagnostics for this pass. |",
        "",
        "## Key Findings",
        "",
        f"- `openai/gpt-5-mini` has {parse_failures} parse failures in the final 200-record run. The failures are concentrated near the output cap, so low escape should remain a parse/schema caveat until a raw-response-preserving rerun is complete.",
        f"- Evidence-cleanliness failures are common enough to justify manual review: {len(taxonomy_rows)} total dirty-support rows, including {len(gpt54_taxonomy)} for `openai/gpt-5.4-mini`.",
        f"- Dirty-support taxonomy counts: {dict(taxonomy_counts)}.",
        f"- Human audit pack counts: {dict(bucket_counts)}.",
        "- The heuristic comparison is useful as a plumbing and upper-bound appendix, but it is not a fair model baseline because the heuristic uses gold metadata hidden from the model prompt.",
        "",
        "## Heuristic All-Slice Snapshot",
        "",
    ]
    lines.extend(markdown_table(heuristic_all, ["model_or_baseline", "prompt_condition", "n", "epistemic_escape", "evidence_cleanliness", "primary_seeking_rate", "generated_lore_avoidance_rate", "uses_gold_metadata", "is_model_comparable"]))
    lines.extend(
        [
            "",
            "## Completion Boundary",
            "",
            "This pass prepares validation artifacts. It does not complete the human audit, does not repair `gpt-5-mini` outputs, and does not make repaired numbers eligible for the main table.",
            "",
            "```json",
            json.dumps(audit_manifest, ensure_ascii=False, indent=2),
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_validity_pass(
    *,
    task_dir: Path,
    run_dir: Path,
    report_dir: Path,
    heuristic_report_dir: Path,
    out_dir: Path,
    human_sample_per_bucket: int,
) -> Dict[str, Any]:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    tasks_by_id = {task.task_id: task for task in tasks}
    records = read_records(run_dir / "predictions.jsonl")
    scored_rows = read_csv_rows(report_dir / "scored_predictions.csv")
    heuristic_rows = read_csv_rows(heuristic_report_dir / "scored_predictions.csv")

    parse_rows = aggregate_parse_repair_audit(scored_rows, records)
    taxonomy_rows = evidence_cleanliness_failure_rows(scored_rows, tasks_by_id)
    human_rows = human_audit_sample(scored_rows, records, tasks_by_id, human_sample_per_bucket)
    heuristic_appendix = heuristic_appendix_rows(scored_rows, heuristic_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "parse_repair_audit.csv", parse_rows)
    write_jsonl(out_dir / "human_audit_sample.jsonl", human_rows)
    write_csv(out_dir / "evidence_cleanliness_failure_taxonomy.csv", taxonomy_rows)
    write_csv(out_dir / "heuristic_baseline_appendix.csv", heuristic_appendix)
    write_figures_manifest(out_dir / "paper_figures_manifest.md")

    audit_manifest: Dict[str, Any] = {
        "name": "EHA Validity Pass",
        "task_content_changed": False,
        "gold_labels_changed": False,
        "api_calls_made": False,
        "inputs": {
            "task_dir": str(task_dir),
            "run_dir": str(run_dir),
            "report_dir": str(report_dir),
            "heuristic_report_dir": str(heuristic_report_dir),
        },
        "outputs": {
            "parse_repair_audit_rows": len(parse_rows),
            "human_audit_sample_rows": len(human_rows),
            "evidence_cleanliness_failure_rows": len(taxonomy_rows),
            "heuristic_baseline_appendix_rows": len(heuristic_appendix),
        },
        "human_audit_bucket_counts": dict(Counter(row["audit_bucket"] for row in human_rows)),
        "parse_failure_counts_by_model": dict(Counter(record.model for record in records if not record.parse_success)),
        "taxonomy_label_counts": dict(Counter(label for row in taxonomy_rows for label in str(row["taxonomy_labels"]).split(",") if label)),
        "raw_response_available": False,
        "repair_attempted": False,
        "repair_blocker": "Final run persisted predictions and parse errors, but not raw unparsed response text.",
    }
    write_json(out_dir / "audit_manifest.json", audit_manifest)
    write_prompt_to_artifact_checklist(out_dir / "prompt_to_artifact_checklist.md", audit_manifest)
    write_summary(
        out_dir / "summary.md",
        parse_rows=parse_rows,
        taxonomy_rows=taxonomy_rows,
        human_rows=human_rows,
        heuristic_rows=heuristic_appendix,
        audit_manifest=audit_manifest,
    )
    return audit_manifest


@app.command("run")
def run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared Epistemic Resilience task directory."),
    run_dir: Path = typer.Option(Path("results/runs/epistemic-resilience-v1-api-final"), help="Final API run directory."),
    report_dir: Path = typer.Option(Path("results/reports-epistemic-resilience-v1"), help="Final API report directory."),
    heuristic_report_dir: Path = typer.Option(Path("results/reports-epistemic-resilience-v1-heuristic"), help="Heuristic report directory."),
    out_dir: Path = typer.Option(Path("results/reports-epistemic-validity-pass"), help="Validity-pass report directory."),
    human_sample_per_bucket: int = typer.Option(20, min=1, help="Manual-audit cases to export per target bucket."),
) -> None:
    audit_manifest = build_validity_pass(
        task_dir=task_dir,
        run_dir=run_dir,
        report_dir=report_dir,
        heuristic_report_dir=heuristic_report_dir,
        out_dir=out_dir,
        human_sample_per_bucket=human_sample_per_bucket,
    )
    console.print(f"[green]Wrote EHA validity-pass artifacts[/green] to {out_dir}")
    console.print_json(json.dumps(audit_manifest, ensure_ascii=False))


if __name__ == "__main__":
    app()
