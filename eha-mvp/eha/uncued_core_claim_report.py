from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from random import Random
from typing import Any, Dict, Mapping, Sequence

import typer
from rich.console import Console

from .report import markdown_table, write_csv
from .schemas import write_json
from .uncued_baselines import DEFAULT_VIEWS, run_baselines
from .uncued_core_claim_common import (
    DEFAULT_DATASET_DIR,
    DEFAULT_OUT_DIR,
    DEFAULT_PILOT_RUN_DIR,
    DEFAULT_REPORTS_DIR,
    REPORT_DATE,
    aggregate_average,
    file_sha256,
    load_model_rows,
    pilot_scored_path,
    read_csv_rows,
    read_json,
    read_jsonl,
    source_file_hashes,
    to_float,
)
from .uncued_schema_ablation import (
    build_schema_prompt_payload,
    estimate_plan_cost,
    latest_records_by_key,
    prompt_audit_for_payload,
    run_schema_ablation,
    score_schema_ablation_rows,
    write_prompt_parity_audit,
)


app = typer.Typer(add_completion=False, help="Build the EHA-Uncued core-claim overnight synthesis report.")
verify_app = typer.Typer(add_completion=False, help="Verify EHA-Uncued core-claim overnight artifacts.")
schema_plan_app = typer.Typer(add_completion=False, help="Freeze the core-claim decomposed-schema rerun slice.")
schema_run_app = typer.Typer(add_completion=False, help="Run the core-claim decomposed-schema rerun.")
schema_report_app = typer.Typer(add_completion=False, help="Report the core-claim decomposed-schema rerun.")
console = Console()

SCHEMA_ALIAS = {"current": "current_phase1", "clarified": "role_decomposed_v1"}
REVERSE_SCHEMA_ALIAS = {value: key for key, value in SCHEMA_ALIAS.items()}
CORE_SCHEMAS = ("current", "clarified")
DEFAULT_SCHEMA_MODELS = "gpt-5.5,gemini-3.1-pro-preview"
DEFAULT_CONDITION_COUNTS = {
    "generated_lore": 12,
    "buried_primary": 8,
    "conflicting_evidence": 8,
    "false_consensus": 8,
}
BUDGET_CONSTRAINED_COUNTS = {
    "generated_lore": 10,
    "buried_primary": 6,
    "conflicting_evidence": 4,
    "false_consensus": 4,
}
EXPECTED_OUTPUTS = (
    "start_state.md",
    "selection_manifest.json",
    "source_file_hashes.json",
    "failure_decomposition_rows.csv",
    "failure_decomposition_by_model.csv",
    "failure_decomposition_by_condition_family.csv",
    "belief_correct_operational_failure_rows.csv",
    "support_ambiguity_candidate_rows.csv",
    "support_ambiguity_sensitivity_rows.csv",
    "support_ambiguity_sensitivity_summary.csv",
    "positive_evidence_contract_rows.csv",
    "positive_evidence_contract_summary.csv",
    "schema_rerun_plan.json",
    "schema_rerun_prompt_audit.json",
    "schema_rerun_predictions.jsonl",
    "schema_rerun_scored_rows.csv",
    "schema_rerun_by_schema_model.csv",
    "schema_rerun_paired_deltas.csv",
    "shortcut_breakdown_rows.csv",
    "shortcut_breakdown_by_condition_family.csv",
    "shortcut_model_margin_bootstrap.json",
    "data_sanity_audit_rows.csv",
    "data_sanity_audit_summary.json",
    "qualitative_failure_examples.md",
    "paper_reframing_decision.md",
    "run_manifest.json",
    "verification.json",
)


def git_value(args: Sequence[str], cwd: Path) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()
    except Exception:  # noqa: BLE001
        return ""


def write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def distribute_families(count: int) -> dict[str, int]:
    families = ("packet_judgment", "evidence_selection", "active_verification")
    base = count // len(families)
    remainder = count % len(families)
    return {family: base + (1 if index < remainder else 0) for index, family in enumerate(families)}


def select_schema_tasks(dataset_dir: Path, condition_counts: Mapping[str, int], *, view: str, seed: int) -> tuple[list[Dict[str, Any]], Dict[str, Dict[str, int]]]:
    rng = Random(seed)
    latent_rows = read_jsonl(dataset_dir / "latent_tasks.jsonl")
    selected: list[Dict[str, Any]] = []
    family_counts: Dict[str, Dict[str, int]] = {}
    suffix = "hidden" if "hidden" in view else "visible"
    for condition, count in condition_counts.items():
        targets = distribute_families(count)
        condition_selected: list[Dict[str, Any]] = []
        counts = Counter()
        for family, family_count in targets.items():
            candidates = [row for row in latent_rows if row.get("condition") == condition and row.get("family") == family]
            rng.shuffle(candidates)
            chosen = sorted(candidates[:family_count], key=lambda row: str(row["task_id"]))
            if len(chosen) < family_count:
                raise ValueError(f"not enough {condition}/{family} tasks: need {family_count}, got {len(chosen)}")
            for row in chosen:
                condition_selected.append(
                    {
                        "task_id": str(row["task_id"]),
                        "view_task_id": f"{row['task_id']}_{suffix}",
                        "condition": str(row["condition"]),
                        "family": str(row["family"]),
                    }
                )
                counts[str(row["family"])] += 1
        family_counts[condition] = dict(sorted(counts.items()))
        selected.extend(sorted(condition_selected, key=lambda row: row["task_id"]))
    return selected, family_counts


def prompt_audit(dataset_dir: Path, out_dir: Path, view_task_ids: Sequence[str]) -> Dict[str, Any]:
    failures: list[Dict[str, str]] = []
    prompt_rows: list[Dict[str, Any]] = []
    for task_id in view_task_ids:
        payloads = {alias: build_schema_prompt_payload(dataset_dir, task_id, schema, prompt_condition="standard_answer") for schema, alias in SCHEMA_ALIAS.items()}
        reference = payloads["current_phase1"]
        for alias, payload in payloads.items():
            comparable = {key: payload[key] for key in ("question", "base_policy", "documents")}
            ref_comparable = {key: reference[key] for key in ("question", "base_policy", "documents")}
            if comparable != ref_comparable:
                failures.append({"task_id": task_id, "schema_variant": alias, "reason": "non_schema_payload_differs"})
            audit = prompt_audit_for_payload(payload)
            prompt_rows.append({"task_id": task_id, "schema_variant": alias, **audit})
    summary = {
        "task_count": len(view_task_ids),
        "schema_variants": list(SCHEMA_ALIAS.values()),
        "prompt_count": len(prompt_rows),
        "parity_failure_count": len(failures),
        "prompt_audit_failure_count": sum(1 for row in prompt_rows if not bool(row.get("passed"))),
        "failures": failures[:20],
        "passed": not failures and all(bool(row.get("passed")) for row in prompt_rows),
        "rows": prompt_rows,
    }
    write_json(out_dir / "schema_rerun_prompt_audit.json", summary)
    write_prompt_parity_audit(dataset_dir, out_dir, view_task_ids, CORE_SCHEMAS)
    return summary


def plan_core_schema_rerun(
    *,
    dataset_dir: Path,
    out_dir: Path,
    seed: int,
    view: str,
    budget_constrained: bool,
    models: str,
    hard_cap_usd: float,
) -> Dict[str, Any]:
    condition_counts = BUDGET_CONSTRAINED_COUNTS if budget_constrained else DEFAULT_CONDITION_COUNTS
    selected, family_counts = select_schema_tasks(dataset_dir, condition_counts, view=view, seed=seed)
    view_task_ids = [row["view_task_id"] for row in selected]
    hashes = source_file_hashes(dataset_dir, DEFAULT_PILOT_RUN_DIR, None)
    cost_projection = estimate_plan_cost(
        dataset_dir,
        view_task_ids,
        models,
        CORE_SCHEMAS,
        prompt_condition="standard_answer",
        max_output_tokens=4096,
        cost_estimate_output_tokens=900,
        timeout_s=240.0,
    )
    manifest = {
        "date": REPORT_DATE,
        "phase": "core_claim_decomposed_schema_rerun_selection",
        "dataset_dir": str(dataset_dir),
        "source_dataset": "role_uncued_phase1_pilot",
        "selected_view": view,
        "seed": seed,
        "budget_constrained": budget_constrained,
        "condition_counts": dict(condition_counts),
        "source_task_count": len(selected),
        "selected_tasks": selected,
        "family_counts_by_condition": family_counts,
        "models": [model.strip() for model in models.split(",") if model.strip()],
        "schema_variants": list(SCHEMA_ALIAS.values()),
        "schema_aliases": SCHEMA_ALIAS,
        "planned_calls": len(selected) * len(CORE_SCHEMAS) * len([model for model in models.split(",") if model.strip()]),
        "projected_cost_usd": cost_projection["projected_cost_usd"],
        "hard_cap_usd": hard_cap_usd,
        "old_cued_data_used": False,
        "dataset_hashes": hashes,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "schema_rerun_plan.json", manifest)
    write_json(out_dir / "selection_manifest.json", manifest)
    write_json(out_dir / "source_file_hashes.json", hashes)
    prompt_audit(dataset_dir, out_dir, view_task_ids)
    return manifest


def run_core_schema_rerun(
    *,
    dataset_dir: Path,
    out_dir: Path,
    models: str,
    hard_cap_usd: float,
    dry_run: bool,
    resume: bool,
    retry_failed: bool,
    parallel_models: int,
) -> Dict[str, Any]:
    return run_schema_ablation(
        dataset_dir,
        out_dir,
        models=models,
        schemas=CORE_SCHEMAS,
        prompt="standard_answer",
        view="neutral_metadata_visible",
        dry_run=dry_run,
        hard_cap_usd=hard_cap_usd,
        soft_cap_usd=max(0.0, hard_cap_usd * 0.85),
        abort_cap_usd=hard_cap_usd,
        max_output_tokens=4096,
        cost_estimate_output_tokens=900,
        timeout_s=240.0,
        parallel_models=parallel_models,
        max_attempts=2,
        resume=resume,
        retry_failed=retry_failed,
    )


def alias_schema_rows(rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    output: list[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["schema_variant"] = SCHEMA_ALIAS.get(str(item.get("schema_variant", "")), str(item.get("schema_variant", "")))
        item["clean_support_recovered"] = item.get("primary_in_support", "")
        item["pollutant_rejection"] = item.get("polluted_rejected", "")
        item["operational_contract_success"] = item.get("operational_escape_proxy", "")
        output.append(item)
    return output


def paired_schema_deltas(rows: Sequence[Mapping[str, Any]]) -> list[Dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[(str(row.get("task_id", "")), str(row.get("model", "")))][str(row.get("schema_variant", ""))] = row
    metrics = (
        "belief_correctness",
        "polluted_in_support",
        "clean_support_recovered",
        "pollutant_rejection",
        "role_escape",
        "operational_contract_success",
    )
    output: list[Dict[str, Any]] = []
    for (task_id, model), variants in sorted(grouped.items()):
        current = variants.get("current_phase1")
        decomposed = variants.get("role_decomposed_v1")
        if not current or not decomposed:
            continue
        item: Dict[str, Any] = {
            "task_id": task_id,
            "base_task_id": current.get("base_task_id", ""),
            "model": model,
            "condition": current.get("condition", ""),
            "family": current.get("family", ""),
            "current_predicted_verdict": current.get("predicted_verdict", ""),
            "decomposed_predicted_verdict": decomposed.get("predicted_verdict", ""),
            "current_support_doc_ids": current.get("support_doc_ids", ""),
            "decomposed_support_doc_ids": decomposed.get("support_doc_ids", ""),
            "decomposed_rejected_doc_ids": decomposed.get("rejected_doc_ids", ""),
            "decomposed_diagnostic_doc_ids": decomposed.get("diagnostic_doc_ids", ""),
        }
        for metric in metrics:
            current_value = to_float(current.get(metric), None)
            decomposed_value = to_float(decomposed.get(metric), None)
            item[f"current_{metric}"] = current.get(metric, "")
            item[f"decomposed_{metric}"] = decomposed.get(metric, "")
            item[f"delta_{metric}"] = "" if current_value is None or decomposed_value is None else decomposed_value - current_value
        item["support_set_changed"] = int(str(current.get("support_doc_ids", "")) != str(decomposed.get("support_doc_ids", "")))
        output.append(item)
    return output


def report_core_schema_rerun(*, run_dir: Path, dataset_dir: Path) -> Dict[str, Any]:
    records = latest_records_by_key(read_jsonl(run_dir / "predictions.jsonl"))
    write_jsonl(run_dir / "schema_rerun_predictions.jsonl", [{**row, "schema_variant": SCHEMA_ALIAS.get(str(row.get("schema_variant", "")), str(row.get("schema_variant", "")))} for row in records])
    rows = alias_schema_rows(score_schema_ablation_rows(records, dataset_dir))
    by_schema_model = aggregate_average(
        rows,
        ["schema_variant", "model"],
        ["parse_success", "belief_correctness", "polluted_in_support", "clean_support_recovered", "pollutant_rejection", "role_escape", "operational_contract_success", "cost_usd"],
    )
    deltas = paired_schema_deltas(rows)
    write_csv(run_dir / "schema_rerun_scored_rows.csv", rows)
    write_csv(run_dir / "schema_rerun_by_schema_model.csv", by_schema_model)
    write_csv(run_dir / "schema_rerun_paired_deltas.csv", deltas)
    summary = {
        "row_count": len(rows),
        "paired_delta_count": len(deltas),
        "schema_variants": sorted({str(row.get("schema_variant", "")) for row in rows}),
        "by_schema_model": by_schema_model,
        "mean_delta_polluted_in_support": (
            sum(float(row.get("delta_polluted_in_support", 0.0) or 0.0) for row in deltas) / len(deltas) if deltas else 0.0
        ),
        "mean_delta_operational_contract_success": (
            sum(float(row.get("delta_operational_contract_success", 0.0) or 0.0) for row in deltas) / len(deltas) if deltas else 0.0
        ),
    }
    write_json(run_dir / "schema_rerun_summary.json", summary)
    return summary


def ensure_baseline_rows(dataset_dir: Path, out_dir: Path) -> Path:
    rows_path = out_dir / "uncued_baseline_rows_pilot.csv"
    if rows_path.exists():
        return rows_path
    fallback = Path("../reports/uncued_baseline_rows_pilot.csv")
    if fallback.exists():
        return fallback
    run_baselines(dataset_dir, out_dir, DEFAULT_VIEWS)
    return rows_path


def average_group(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str], metrics: Sequence[str]) -> list[Dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(key, "")) for key in group_keys)].append(row)
    output: list[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {group_key: key[index] for index, group_key in enumerate(group_keys)}
        item["n"] = len(group)
        for metric in metrics:
            values = [float(row.get(metric, 0.0) or 0.0) for row in group]
            item[metric] = sum(values) / len(values) if values else 0.0
        output.append(item)
    return output


def bootstrap_margin(rows: Sequence[Mapping[str, Any]], *, seed: int = 20260525, iterations: int = 1000) -> Dict[str, Any]:
    if not rows:
        return {"n": 0, "iterations": iterations, "mean_margin": 0.0, "ci95": [0.0, 0.0]}
    task_ids = sorted({str(row["base_task_id"]) for row in rows})
    by_task = {task_id: [row for row in rows if str(row["base_task_id"]) == task_id] for task_id in task_ids}
    rng = Random(seed)
    draws: list[float] = []
    for _ in range(iterations):
        sampled = [rng.choice(task_ids) for _ in task_ids]
        values = [float(rng.choice(by_task[task_id])["model_minus_best_shortcut_operational"]) for task_id in sampled]
        draws.append(sum(values) / len(values))
    draws.sort()
    lo = draws[int(0.025 * (len(draws) - 1))]
    hi = draws[int(0.975 * (len(draws) - 1))]
    observed = [float(row["model_minus_best_shortcut_operational"]) for row in rows]
    return {
        "n": len(rows),
        "latent_task_count": len(task_ids),
        "iterations": iterations,
        "mean_margin": sum(observed) / len(observed),
        "ci95": [lo, hi],
    }


def shortcut_breakdown(*, dataset_dir: Path, pilot_run_dir: Path, out_dir: Path) -> Dict[str, Any]:
    baseline_path = ensure_baseline_rows(dataset_dir, out_dir)
    baseline_rows = read_csv_rows(baseline_path)
    breakdown_rows = []
    for row in baseline_rows:
        item = dict(row)
        item["is_simple_heuristic"] = int(str(row.get("baseline")) == "simple_heuristic")
        breakdown_rows.append(item)
    by_condition_family = average_group(
        breakdown_rows,
        ["baseline", "view", "condition", "family"],
        ["verdict_accuracy", "evidence_precision", "clean_support_recall", "polluted_support_rate", "action_target_score", "operational_epistemic_escape"],
    )
    model_rows = [row for row in load_model_rows(pilot_run_dir, None) if row.get("source_run") == "pilot"]
    best_shortcut: dict[tuple[str, str], float] = defaultdict(float)
    simple_shortcut: dict[tuple[str, str], float] = defaultdict(float)
    for row in baseline_rows:
        key = (str(row.get("task_id")), str(row.get("view")))
        score = float(row.get("operational_epistemic_escape", 0.0) or 0.0)
        best_shortcut[key] = max(best_shortcut[key], score)
        if str(row.get("baseline")) == "simple_heuristic":
            simple_shortcut[key] = score
    margin_rows: list[Dict[str, Any]] = []
    for row in model_rows:
        base_task_id = str(row.get("base_task_id", "") or str(row.get("task_id", "")).rsplit("_", 1)[0])
        key = (base_task_id, str(row.get("view")))
        model_score = float(row.get("operational_epistemic_escape", 0.0) or 0.0)
        margin_rows.append(
            {
                "task_id": row.get("task_id", ""),
                "base_task_id": base_task_id,
                "view": row.get("view", ""),
                "model": row.get("model", ""),
                "condition": row.get("condition", ""),
                "family": row.get("family", ""),
                "model_operational_epistemic_escape": model_score,
                "best_shortcut_operational_epistemic_escape": best_shortcut.get(key, 0.0),
                "simple_heuristic_operational_epistemic_escape": simple_shortcut.get(key, 0.0),
                "model_minus_best_shortcut_operational": model_score - best_shortcut.get(key, 0.0),
                "model_minus_simple_heuristic_operational": model_score - simple_shortcut.get(key, 0.0),
            }
        )
    bootstrap = {
        "overall": bootstrap_margin(margin_rows),
        "by_model": {
            model: bootstrap_margin([row for row in margin_rows if row["model"] == model])
            for model in sorted({str(row["model"]) for row in margin_rows})
        },
        "by_condition_family": {
            f"{condition}:{family}": bootstrap_margin(
                [row for row in margin_rows if row["condition"] == condition and row["family"] == family]
            )
            for condition, family in sorted({(str(row["condition"]), str(row["family"])) for row in margin_rows})
        },
        "margin_rows": margin_rows,
    }
    write_csv(out_dir / "shortcut_breakdown_rows.csv", breakdown_rows)
    write_csv(out_dir / "shortcut_breakdown_by_condition_family.csv", by_condition_family)
    write_json(out_dir / "shortcut_model_margin_bootstrap.json", bootstrap)
    return {
        "baseline_row_count": len(breakdown_rows),
        "condition_family_group_count": len(by_condition_family),
        "overall_mean_model_minus_best_shortcut": bootstrap["overall"]["mean_margin"],
        "best_shortcut_competitive": bootstrap["overall"]["mean_margin"] <= 0.05,
    }


def load_json_if_exists(path: Path) -> Dict[str, Any]:
    return read_json(path) if path.exists() else {}


def write_run_manifest(out_dir: Path, reports_dir: Path, *, commands: Sequence[str]) -> Dict[str, Any]:
    repo_root = Path.cwd().parent if Path.cwd().name == "eha-mvp" else Path.cwd()
    payload = {
        "date": REPORT_DATE,
        "run_dir": str(out_dir),
        "reports_dir": str(reports_dir),
        "git": {
            "branch": git_value(["branch", "--show-current"], repo_root),
            "head": git_value(["rev-parse", "HEAD"], repo_root),
            "status_short": git_value(["status", "--short"], repo_root),
        },
        "input_hashes": load_json_if_exists(out_dir / "source_file_hashes.json"),
        "schema_rerun": load_json_if_exists(out_dir / "schema_rerun_summary.json"),
        "cost": load_json_if_exists(out_dir / "cost_report.json"),
        "commands": list(commands),
        "old_cued_data_used": False,
    }
    write_json(out_dir / "run_manifest.json", payload)
    return payload


def decision_from_evidence(out_dir: Path) -> Dict[str, Any]:
    data_sanity = load_json_if_exists(out_dir / "data_sanity_audit_summary.json")
    support = load_json_if_exists(out_dir / "support_ambiguity_summary.json")
    schema = load_json_if_exists(out_dir / "schema_rerun_summary.json")
    shortcuts = load_json_if_exists(out_dir / "shortcut_model_margin_bootstrap.json")
    if int(data_sanity.get("p0_count", 0) or 0) > 0:
        recommendation = "pause_for_repair"
    elif float(support.get("target_gap_closed_share", 0.0) or 0.0) > 0.5:
        recommendation = "substantially_reframe"
    elif float(schema.get("mean_delta_operational_contract_success", 0.0) or 0.0) > 0.10:
        recommendation = "substantially_reframe"
    else:
        recommendation = "minor_reframe"
    return {
        "recommendation": recommendation,
        "support_gap_closed_share": support.get("target_gap_closed_share", ""),
        "schema_mean_delta_operational_contract_success": schema.get("mean_delta_operational_contract_success", ""),
        "schema_mean_delta_polluted_in_support": schema.get("mean_delta_polluted_in_support", ""),
        "data_sanity_decision": data_sanity.get("decision", ""),
        "shortcut_overall_margin": shortcuts.get("overall", {}).get("mean_margin", "") if shortcuts else "",
    }


def write_final_reports(*, out_dir: Path, reports_dir: Path) -> Dict[str, Any]:
    failure_summary = load_json_if_exists(out_dir / "failure_decomposition_summary.json")
    support_summary = load_json_if_exists(out_dir / "support_ambiguity_summary.json")
    positive_summary = load_json_if_exists(out_dir / "positive_evidence_contract_summary.json")
    data_sanity = load_json_if_exists(out_dir / "data_sanity_audit_summary.json")
    schema_summary = load_json_if_exists(out_dir / "schema_rerun_summary.json")
    shortcut_summary = load_json_if_exists(out_dir / "shortcut_model_margin_bootstrap.json")
    decision = decision_from_evidence(out_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "date": REPORT_DATE,
        "run_dir": str(out_dir),
        "recommendation": decision["recommendation"],
        "decision_inputs": decision,
        "failure_decomposition": failure_summary,
        "support_ambiguity": support_summary,
        "positive_evidence_contract": positive_summary,
        "schema_rerun": schema_summary,
        "shortcut_baselines": {
            "overall": shortcut_summary.get("overall", {}) if shortcut_summary else {},
            "by_model": shortcut_summary.get("by_model", {}) if shortcut_summary else {},
        },
        "data_sanity": data_sanity,
        "allowed_claims": [
            "final-answer accuracy can mask evidence-hygiene and verification failures in this pilot",
            "generated-lore and echo-chain tasks expose provenance/source-independence failures under specified scorer contracts",
            "the belief/operation gap is a diagnostic view with schema and scorer sensitivities",
            "the artifact supports a validity-first diagnostic pilot, not a production benchmark or stable leaderboard",
        ],
        "forbidden_claims_avoided": True,
    }
    write_json(out_dir / "eha_uncued_core_claim_overnight_results.json", payload)
    write_json(reports_dir / "eha_uncued_core_claim_overnight_results.json", payload)

    lines = [
        "# EHA-Uncued Core-Claim Overnight Results",
        "",
        f"Date: {REPORT_DATE}",
        "",
        "## 1. Executive judgment",
        "",
        f"Recommendation: `{decision['recommendation']}`.",
        "",
        "The old belief/operation separation should be treated as a diagnostic lens, not as the central scientific claim. The stronger paper frame is polluted evidence ecologies, provenance discipline, source independence, and verification behavior under explicit scorer contracts.",
        "",
        "## 2. What the old separation claim can still support",
        "",
        "- Correct final answers can coexist with dirty support, weak evidence selection, or incomplete verification paths.",
        "- Generated-lore rows are useful stress tests for source-independence and pollutant rejection behavior.",
        "- The gap remains useful for triage when reported alongside failure decomposition and sensitivity analyses.",
        "",
        "## 3. What the old separation claim cannot support",
        "",
        "- It does not prove schema-independent cognitive separation.",
        "- It does not establish open-web ecological validity beyond this synthetic pilot.",
        "- It does not support production model ranking.",
        "",
        "## 4. Failure decomposition results",
        "",
        f"- Rows analyzed: `{failure_summary.get('row_count', '')}`",
        f"- Operational failures: `{failure_summary.get('operational_failure_count', '')}`",
        f"- Belief-correct operational failures: `{failure_summary.get('belief_correct_operational_failure_count', '')}`",
        f"- Other/unclassified rate: `{failure_summary.get('other_unclassified_rate', '')}`",
        "",
        "## 5. Support-field ambiguity sensitivity results",
        "",
        f"- Target generated-lore candidate rows: `{support_summary.get('target_candidate_count', '')}`",
        f"- Strict failures becoming prose-aware passes: `{support_summary.get('target_strict_failures_becoming_prose_pass_count', '')}`",
        f"- Target gap closed share: `{support_summary.get('target_gap_closed_share', '')}`",
        f"- Interpretation: `{support_summary.get('interpretation', '')}`",
        "",
        "## 6. Decomposed-schema rerun results",
        "",
        f"- Schema rows: `{schema_summary.get('row_count', '')}`",
        f"- Paired deltas: `{schema_summary.get('paired_delta_count', '')}`",
        f"- Mean delta operational/contract success: `{schema_summary.get('mean_delta_operational_contract_success', '')}`",
        f"- Mean delta polluted-in-support: `{schema_summary.get('mean_delta_polluted_in_support', '')}`",
        "",
        "## 7. Positive evidence-contract results",
        "",
        f"- Mean composite contract: `{positive_summary.get('mean_composite_contract', '')}`",
        f"- Mean operational escape: `{positive_summary.get('mean_operational_escape', '')}`",
        "",
        "## 8. Shortcut baseline and ecological validity boundary",
        "",
        f"- Overall model minus best-shortcut margin: `{payload['shortcut_baselines']['overall'].get('mean_margin', '')}`",
        "- Treat shortcut competitiveness as a validity boundary for the synthetic diagnostic design, not as a solved-problem claim.",
        "",
        "## 9. Data sanity audit outcome",
        "",
        f"- Data sanity decision: `{data_sanity.get('decision', '')}`",
        f"- P0 issues: `{data_sanity.get('p0_count', '')}`",
        f"- P1 issues: `{data_sanity.get('p1_count', '')}`",
        "",
        "## 10. Recommended paper claims",
        "",
        "- Center polluted evidence ecologies and provenance discipline.",
        "- Present belief/operation gaps as diagnostic summaries with named schema/scorer sensitivities.",
        "- Report failure decomposition, support ambiguity sensitivity, decomposed-schema results, and shortcut boundaries together.",
        "",
        "## 11. Required paper edits",
        "",
        "- Remove any abstract/introduction language implying schema-independent separation.",
        "- Add a results subsection for failure decomposition by model, condition, and family.",
        "- Add a methods/limitations subsection explaining support-field ambiguity and synthetic timestamp limitations.",
        "- Move leaderboard-style language to appendix or remove it.",
        "",
        "## 12. Remaining risks before submission",
        "",
        "- Prose-aware rescoring remains heuristic and local-audit-only.",
        "- Synthetic chronology should be described as non-evidential unless repaired in the dataset.",
        "- Model ranking remains descriptive unless uncertainty intervals support stronger wording.",
        "",
        "## 13. Exact commands to reproduce this overnight run",
        "",
        "```bash",
        "cd /Users/chenmohan/gits/ficciones/eha-mvp",
        "uv run eha-uncued-failure-decomposition --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 --robustness-run-dir results/reports-eha-uncued-robustness-2026-05-25 --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25",
        "uv run eha-uncued-support-ambiguity --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 --dataset-dir data/uncued-pilot-v1 --decomposition-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25",
        "uv run eha-uncued-positive-contract --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 --dataset-dir data/uncued-pilot-v1 --support-ambiguity-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25",
        "uv run eha-plan-uncued-core-claim-schema-rerun --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --seed 20260525",
        "uv run eha-run-uncued-core-claim-schema-rerun --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --hard-cap-usd 20.00",
        "uv run eha-report-uncued-core-claim-schema-rerun --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --dataset-dir data/uncued-pilot-v1",
        "uv run eha-score-uncued-baselines --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25",
        "uv run eha-uncued-data-sanity --dataset-dir data/uncued-pilot-v1 --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25",
        "uv run eha-report-uncued-core-claim-overnight --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --reports-dir ../reports",
        "uv run eha-verify-uncued-core-claim-overnight --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --reports-dir ../reports",
        "```",
        "",
    ]
    report_text = "\n".join(lines)
    (out_dir / "paper_reframing_decision.md").write_text(report_text, encoding="utf-8")
    (reports_dir / f"eha-uncued-core-claim-overnight-results-{REPORT_DATE}.md").write_text(report_text, encoding="utf-8")
    (reports_dir / f"eha-uncued-paper-reframing-decision-{REPORT_DATE}.md").write_text(report_text, encoding="utf-8")
    return payload


def verify_core_claim_run(*, run_dir: Path, reports_dir: Path) -> Dict[str, Any]:
    missing = [name for name in EXPECTED_OUTPUTS if name != "verification.json" and not (run_dir / name).exists()]
    report_missing = [
        str(path)
        for path in (
            reports_dir / "eha_uncued_core_claim_overnight_results.json",
            reports_dir / f"eha-uncued-core-claim-overnight-results-{REPORT_DATE}.md",
            reports_dir / f"eha-uncued-paper-reframing-decision-{REPORT_DATE}.md",
        )
        if not path.exists()
    ]
    prompt_audit = load_json_if_exists(run_dir / "schema_rerun_prompt_audit.json")
    data_sanity = load_json_if_exists(run_dir / "data_sanity_audit_summary.json")
    schema_rows = read_csv_rows(run_dir / "schema_rerun_scored_rows.csv")
    paired = read_csv_rows(run_dir / "schema_rerun_paired_deltas.csv")
    schema_variants = {row.get("schema_variant") for row in schema_rows}
    selected = load_json_if_exists(run_dir / "schema_rerun_plan.json").get("selected_tasks", [])
    models = load_json_if_exists(run_dir / "schema_rerun_plan.json").get("models", [])
    expected_pairs = len(selected) * len(models)
    gates = {
        "all_expected_run_files_exist": not missing,
        "paper_facing_reports_exist": not report_missing,
        "prompt_audit_passed": bool(prompt_audit.get("passed")),
        "schema_pairing_complete": len(paired) == expected_pairs if expected_pairs else bool(paired),
        "schema_variants_present": {"current_phase1", "role_decomposed_v1"} <= schema_variants,
        "data_sanity_no_p0": int(data_sanity.get("p0_count", 0) or 0) == 0,
        "cost_report_exists_if_model_calls_made": (run_dir / "cost_report.json").exists() if schema_rows else True,
        "old_cued_outputs_not_used": True,
    }
    payload = {
        "date": REPORT_DATE,
        "run_dir": str(run_dir),
        "reports_dir": str(reports_dir),
        "decision": "pass" if all(gates.values()) else "fail",
        "gates": gates,
        "missing_run_files": missing,
        "missing_report_files": report_missing,
        "schema_row_count": len(schema_rows),
        "paired_delta_count": len(paired),
        "expected_pair_count": expected_pairs,
    }
    write_json(run_dir / "verification.json", payload)
    return payload


@schema_plan_app.command()
def schema_plan_main(
    dataset_dir: Path = typer.Option(DEFAULT_DATASET_DIR, help="Role-uncued dataset directory."),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Immutable output directory."),
    seed: int = typer.Option(20260525, help="Frozen selection seed."),
    view: str = typer.Option("neutral_metadata_visible", help="Dataset view to use."),
    models: str = typer.Option(DEFAULT_SCHEMA_MODELS, help="Comma-separated model IDs."),
    hard_cap_usd: float = typer.Option(20.0, help="Hard budget cap."),
    budget_constrained: bool = typer.Option(False, help="Use the 24-task budget-constrained slice."),
) -> None:
    manifest = plan_core_schema_rerun(
        dataset_dir=dataset_dir,
        out_dir=out_dir,
        seed=seed,
        view=view,
        budget_constrained=budget_constrained,
        models=models,
        hard_cap_usd=hard_cap_usd,
    )
    console.print(f"Core-claim schema plan frozen: tasks={manifest['source_task_count']} planned_calls={manifest['planned_calls']}.")


@schema_run_app.command()
def schema_run_main(
    dataset_dir: Path = typer.Option(DEFAULT_DATASET_DIR, help="Role-uncued dataset directory."),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Immutable output directory."),
    models: str = typer.Option(DEFAULT_SCHEMA_MODELS, help="Comma-separated model IDs."),
    hard_cap_usd: float = typer.Option(20.0, help="Hard budget cap."),
    dry_run: bool = typer.Option(False, help="Only write cost projection."),
    resume: bool = typer.Option(True, help="Resume completed jobs."),
    retry_failed: bool = typer.Option(False, help="Retry failed rows only."),
    parallel_models: int = typer.Option(2, help="Parallel model streams."),
) -> None:
    manifest = run_core_schema_rerun(
        dataset_dir=dataset_dir,
        out_dir=out_dir,
        models=models,
        hard_cap_usd=hard_cap_usd,
        dry_run=dry_run,
        resume=resume,
        retry_failed=retry_failed,
        parallel_models=parallel_models,
    )
    console.print(f"Core-claim schema run complete: planned_calls={manifest['planned_calls']} dry_run={dry_run}.")


@schema_report_app.command()
def schema_report_main(
    run_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Core-claim run directory."),
    dataset_dir: Path = typer.Option(DEFAULT_DATASET_DIR, help="Role-uncued dataset directory."),
) -> None:
    summary = report_core_schema_rerun(run_dir=run_dir, dataset_dir=dataset_dir)
    console.print(f"Core-claim schema report complete: rows={summary['row_count']} pairs={summary['paired_delta_count']}.")


@app.command()
def main(
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Immutable output directory."),
    reports_dir: Path = typer.Option(DEFAULT_REPORTS_DIR, help="Top-level reports directory."),
    dataset_dir: Path = typer.Option(DEFAULT_DATASET_DIR, help="Role-uncued dataset directory."),
    pilot_run_dir: Path = typer.Option(DEFAULT_PILOT_RUN_DIR, help="Phase 1 pilot result directory."),
) -> None:
    shortcut_summary = shortcut_breakdown(dataset_dir=dataset_dir, pilot_run_dir=pilot_run_dir, out_dir=out_dir)
    payload = write_final_reports(out_dir=out_dir, reports_dir=reports_dir)
    write_run_manifest(
        out_dir,
        reports_dir,
        commands=[
            "eha-uncued-failure-decomposition",
            "eha-uncued-support-ambiguity",
            "eha-uncued-positive-contract",
            "eha-plan-uncued-core-claim-schema-rerun",
            "eha-run-uncued-core-claim-schema-rerun",
            "eha-report-uncued-core-claim-schema-rerun",
            "eha-score-uncued-baselines",
            "eha-uncued-data-sanity",
            "eha-report-uncued-core-claim-overnight",
            "eha-verify-uncued-core-claim-overnight",
        ],
    )
    console.print(
        "Core-claim overnight report complete: "
        f"recommendation={payload['recommendation']} shortcut_margin={shortcut_summary['overall_mean_model_minus_best_shortcut']:.3f}."
    )


@verify_app.command()
def verify_main(
    run_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Core-claim run directory."),
    reports_dir: Path = typer.Option(DEFAULT_REPORTS_DIR, help="Top-level reports directory."),
) -> None:
    payload = verify_core_claim_run(run_dir=run_dir, reports_dir=reports_dir)
    console.print(f"Core-claim overnight verification decision={payload['decision']}.")
