from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import typer
from rich.console import Console

from .epistemic_resilience import epistemic_prediction_json_schema
from .schemas import write_json
from .uncued_contract import DEFAULT_REPORT_DATE
from .uncued_run import HIDDEN_PROMPT_MARKERS


package_app = typer.Typer(add_completion=False, help="Package EHA-Uncued Phase 1 artifacts.")
verify_app = typer.Typer(add_completion=False, help="Verify and freeze EHA-Uncued Phase 1 gates.")
console = Console()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_scientific_status(artifact_dir: Path) -> str:
    manifest_path = artifact_dir / "manifest.json"
    if not manifest_path.exists():
        return "missing_manifest"
    manifest = read_json(manifest_path)
    return str(manifest.get("scientific_status", "unknown"))


def refuses_cued_artifact_as_uncued_evidence(artifact_dir: Path) -> bool:
    return artifact_scientific_status(artifact_dir) == "quarantined_cued_internal" and (artifact_dir / "CUED_INTERNAL_ONLY.md").exists()


def required_micro_gate_inputs(dataset_dir: Path, reports_dir: Path) -> Dict[str, Path]:
    return {
        "micro_generation_manifest": dataset_dir / "manifest.json",
        "leakage_report": reports_dir / "eha_uncued_leakage_micro.json",
        "baseline_report": reports_dir / "eha_uncued_baselines_micro.json",
        "human_review_validation": reports_dir / "eha_uncued_human_leakage_review_validation.json",
    }


def freeze_micro_gate(dataset_dir: Path, reports_dir: Path, out_dir: Path, *, report_date: str = DEFAULT_REPORT_DATE) -> Dict[str, Any]:
    inputs = required_micro_gate_inputs(dataset_dir, reports_dir)
    missing = [name for name, path in inputs.items() if not path.exists()]
    hashes = {name: file_sha256(path) for name, path in inputs.items() if path.exists()}
    leakage = read_json(inputs["leakage_report"]) if inputs["leakage_report"].exists() else {}
    baselines = read_json(inputs["baseline_report"]) if inputs["baseline_report"].exists() else {}
    review = read_json(inputs["human_review_validation"]) if inputs["human_review_validation"].exists() else {}
    manifest = read_json(inputs["micro_generation_manifest"]) if inputs["micro_generation_manifest"].exists() else {}
    gates = {
        "manifest_present": "micro_generation_manifest" not in missing,
        "leakage_passed": bool(leakage.get("passed")),
        "baselines_passed": bool(baselines.get("passed")),
        "human_review_validation_passed": bool(review.get("passed")),
        "critical_leaks_zero": int(leakage.get("critical_hits", 1)) == 0 and int(review.get("critical_leaks", 1)) == 0,
        "high_leaks_zero": int(leakage.get("high_hits", 1)) == 0,
        "direct_answer_cues_zero": int(leakage.get("direct_answer_cue_hits", 1)) == 0 and int(review.get("direct_answer_cue_rows", 1)) == 0,
    }
    decision = "go" if not missing and all(gates.values()) else "no-go"
    payload = {
        "date": report_date,
        "dataset_dir": str(dataset_dir),
        "reports_dir": str(reports_dir),
        "phase": "micro_gate",
        "decision": decision,
        "missing_inputs": missing,
        "gates": gates,
        "hashes": hashes,
        "manifest": {
            "name": manifest.get("name"),
            "task_count": manifest.get("task_count"),
            "views": manifest.get("views"),
            "condition_counts": manifest.get("condition_counts"),
            "family_counts": manifest.get("family_counts"),
        },
        "review_mode": review.get("review_mode", []),
        "independent_human_review": bool(review.get("independent_human_review", False)),
        "scope_note": "Decision covers the micro-pilot pre-model gate only; no frontier/API model call was made.",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_uncued_micro_gate.json", payload)
    lines = [
        "# EHA-Uncued Micro Gate",
        "",
        f"Date: {report_date}",
        "",
        f"Decision: `{decision}`",
        "",
        "This freezes the 10-task micro-pilot gate. It records hashes for generation, leakage, baseline, and surface-review validation artifacts. No frontier/API model calls were made.",
        "",
        "## Hashes",
        "",
    ]
    for name, digest in hashes.items():
        lines.append(f"- `{name}`: `{digest}`")
    lines.extend(["", "## Gate Evidence", "", "```json", json.dumps(payload["gates"], ensure_ascii=False, indent=2), "```", ""])
    (out_dir / f"eha-uncued-micro-gate-{report_date}.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


DATA_FILE_MAP = {
    "tasks.jsonl": "data/tasks.jsonl",
    "documents_neutral_metadata_visible.jsonl": "data/documents_neutral_metadata_visible.jsonl",
    "documents_neutral_metadata_hidden.jsonl": "data/documents_neutral_metadata_hidden.jsonl",
    "gold_documents.jsonl": "data/gold_labels.jsonl",
    "dependency_edges.jsonl": "data/dependency_edges.jsonl",
    "action_gold.jsonl": "data/action_gold.jsonl",
    "manifest.json": "data/dataset_manifest.json",
}

BASELINE_REPORT_FILES = (
    "eha_uncued_baselines_pilot.json",
    f"eha-uncued-baselines-pilot-{DEFAULT_REPORT_DATE}.md",
    "uncued_baseline_rows_pilot.csv",
    "uncued_baseline_aggregate_pilot.csv",
)

AUDIT_REPORT_FILES = (
    "eha_uncued_leakage_pilot.json",
    f"eha-uncued-leakage-pilot-{DEFAULT_REPORT_DATE}.md",
    "uncued_leakage_pilot_rows.csv",
    "uncued_human_leakage_review_pilot.csv",
    "eha_uncued_human_leakage_review_pilot_validation.json",
    f"eha-uncued-human-leakage-review-pilot-{DEFAULT_REPORT_DATE}.md",
    "eha_uncued_scorer_audit.json",
    f"eha-uncued-scorer-audit-{DEFAULT_REPORT_DATE}.md",
    "uncued_scorer_audit_rows.csv",
    "eha_uncued_schema_ablation_plan.json",
    f"eha-uncued-schema-ablation-plan-{DEFAULT_REPORT_DATE}.md",
)

REQUIRED_ARTIFACT_FILES = (
    "README.md",
    "manifest.json",
    "data/tasks.jsonl",
    "data/documents_neutral_metadata_visible.jsonl",
    "data/documents_neutral_metadata_hidden.jsonl",
    "data/gold_labels.jsonl",
    "data/dependency_edges.jsonl",
    "data/action_gold.jsonl",
    "prompts/prompt_manifest.json",
    "schemas/epistemic_prediction_schema.json",
    "scorer/scoring_contract.md",
    "outputs/predictions.jsonl",
    "baselines/eha_uncued_baselines_pilot.json",
    "audits/eha_uncued_leakage_pilot.json",
    "audits/eha_uncued_human_leakage_review_pilot_validation.json",
    "audits/eha_uncued_scorer_audit.json",
    "examples/example_task_visible.json",
    "reproduce_minimal.sh",
    "verify_uncued_phase1.sh",
)


def _copy_file(src: Path, dst: Path, *, copied: Dict[str, list[str]], category: str, missing_required: list[str], required: bool) -> None:
    if not src.exists():
        if required:
            missing_required.append(str(src))
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    if dst.suffix in {".md", ".sh"}:
        dst.write_text(dst.read_text(encoding="utf-8").rstrip() + "\n", encoding="utf-8")
    copied.setdefault(category, []).append(str(dst))


def _copy_many_from_reports(reports_dir: Path, out_dir: Path, filenames: Iterable[str], category: str, copied: Dict[str, list[str]]) -> None:
    for filename in filenames:
        _copy_file(reports_dir / filename, out_dir / category / filename, copied=copied, category=category, missing_required=[], required=False)


def _first_jsonl(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                return json.loads(line)
    return {}


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o755)


def _artifact_hashes(out_dir: Path) -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for path in sorted(out_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            hashes[str(path.relative_to(out_dir))] = file_sha256(path)
    return hashes


def _write_package_readme(out_dir: Path) -> None:
    lines = [
        "# EHA-Uncued Phase 1 Artifact",
        "",
        "This package contains the role-uncued Phase 1 pilot dataset, prompts, model outputs, scorer inputs, gate reports, and verifier scripts.",
        "",
        "Scientific status: diagnostic pilot artifact. It is not a deployment certification or a universal model leaderboard.",
        "",
        "The older cued artifact is intentionally excluded. Hidden labels and gold/scorer files are included only under non-model-visible paths.",
        "",
        "## Local Checks",
        "",
        "From the repository root:",
        "",
        "```bash",
        "cd eha-mvp",
        "uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports",
        "```",
        "",
        "For a no-dependency smoke check, run `artifact_uncued_phase1/reproduce_minimal.sh`.",
        "",
    ]
    (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def _write_scoring_contract(out_dir: Path) -> None:
    lines = [
        "# Scoring Contract",
        "",
        "The Phase 1 scorer evaluates parsed prediction records against role-uncued gold labels.",
        "",
        "- `belief_correctness`: claim verdict matches the gold verdict.",
        "- `evidence_precision`: selected supporting evidence avoids polluted evidence and aligns with gold support.",
        "- `operational_escape`: joint success criterion combining belief correctness and evidence hygiene.",
        "- `verification_action_score`: active-verification action quality for tasks that require source tracing.",
        "",
        "The Phase 14 scorer audit found no systematic scorer bug and did not require rescoring. The audit is included under `audits/`.",
        "",
    ]
    scorer_dir = out_dir / "scorer"
    scorer_dir.mkdir(parents=True, exist_ok=True)
    (scorer_dir / "scoring_contract.md").write_text("\n".join(lines), encoding="utf-8")


def _write_scripts(out_dir: Path) -> None:
    _write_executable(
        out_dir / "reproduce_minimal.sh",
        """#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
test -s "$ROOT/manifest.json"
test -s "$ROOT/data/tasks.jsonl"
test -s "$ROOT/data/documents_neutral_metadata_visible.jsonl"
test -s "$ROOT/data/gold_labels.jsonl"
test -s "$ROOT/outputs/predictions.jsonl"
test -s "$ROOT/audits/eha_uncued_scorer_audit.json"
echo "minimal uncued phase1 artifact files present"
""",
    )
    _write_executable(
        out_dir / "verify_uncued_phase1.sh",
        """#!/usr/bin/env bash
set -euo pipefail
ARTIFACT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ARTIFACT_ROOT/.." && pwd)"
cd "$REPO_ROOT/eha-mvp"
uv run eha-verify-uncued-phase1 --artifact-dir "$ARTIFACT_ROOT" --reports-dir "$REPO_ROOT/reports" --out-dir "$REPO_ROOT/reports"
""",
    )


def _copy_prompt_and_response_artifacts(run_dir: Path, out_dir: Path, copied: Dict[str, list[str]], missing_required: list[str]) -> Dict[str, Any]:
    artifacts_dir = run_dir / "artifacts"
    prompt_files = sorted(artifacts_dir.rglob("*.prompt.json")) if artifacts_dir.exists() else []
    response_files = sorted(artifacts_dir.rglob("*.response.json")) if artifacts_dir.exists() else []
    if not prompt_files:
        missing_required.append(str(artifacts_dir / "*.prompt.json"))
    for src in prompt_files:
        dst = out_dir / "prompts" / src.relative_to(artifacts_dir)
        _copy_file(src, dst, copied=copied, category="prompts", missing_required=missing_required, required=True)
    for src in response_files:
        dst = out_dir / "outputs" / "responses" / src.relative_to(artifacts_dir)
        _copy_file(src, dst, copied=copied, category="outputs", missing_required=missing_required, required=True)
    prompt_manifest = {
        "source_artifacts_dir": str(artifacts_dir),
        "prompt_file_count": len(prompt_files),
        "response_file_count": len(response_files),
        "prompt_files": [str((Path("prompts") / src.relative_to(artifacts_dir)).as_posix()) for src in prompt_files],
        "response_files": [str((Path("outputs") / "responses" / src.relative_to(artifacts_dir)).as_posix()) for src in response_files],
    }
    write_json(out_dir / "prompts" / "prompt_manifest.json", prompt_manifest)
    copied.setdefault("prompts", []).append(str(out_dir / "prompts" / "prompt_manifest.json"))
    return prompt_manifest


def package_uncued_phase1(
    dataset_dir: Path,
    run_dir: Path,
    out_dir: Path,
    *,
    reports_dir: Path | None = None,
    repo_root: Path | None = None,
    report_date: str = DEFAULT_REPORT_DATE,
) -> Dict[str, Any]:
    reports_dir = Path("../reports") if reports_dir is None else reports_dir
    project_dir = Path(__file__).resolve().parents[1]
    repo_root = project_dir.parent if repo_root is None else repo_root
    out_dir.mkdir(parents=True, exist_ok=True)
    copied: Dict[str, list[str]] = {}
    missing_required: list[str] = []

    for src_name, dst_name in DATA_FILE_MAP.items():
        _copy_file(dataset_dir / src_name, out_dir / dst_name, copied=copied, category="data", missing_required=missing_required, required=True)

    for src in sorted(run_dir.iterdir()) if run_dir.exists() else []:
        if src.is_file():
            _copy_file(src, out_dir / "outputs" / src.name, copied=copied, category="outputs", missing_required=missing_required, required=False)
    prompt_manifest = _copy_prompt_and_response_artifacts(run_dir, out_dir, copied, missing_required)

    _copy_many_from_reports(reports_dir, out_dir, BASELINE_REPORT_FILES, "baselines", copied)
    _copy_many_from_reports(reports_dir, out_dir, AUDIT_REPORT_FILES, "audits", copied)
    for filename in (
        "eha_uncued_pilot_run.json",
        f"eha-uncued-pilot-run-{report_date}.md",
        "eha_uncued_pilot_results.json",
        f"eha-uncued-pilot-results-{report_date}.md",
        "eha_uncued_pilot_gates.json",
        f"eha-uncued-pilot-gates-{report_date}.md",
    ):
        _copy_file(reports_dir / filename, out_dir / "outputs" / filename, copied=copied, category="outputs", missing_required=[], required=False)

    schemas_dir = out_dir / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    write_json(schemas_dir / "epistemic_prediction_schema.json", epistemic_prediction_json_schema())
    copied.setdefault("schemas", []).append(str(schemas_dir / "epistemic_prediction_schema.json"))
    _copy_file(reports_dir / "eha_uncued_data_contract.json", schemas_dir / "eha_uncued_data_contract.json", copied=copied, category="schemas", missing_required=[], required=False)
    _copy_file(reports_dir / f"eha-uncued-data-contract-{report_date}.md", schemas_dir / f"eha-uncued-data-contract-{report_date}.md", copied=copied, category="schemas", missing_required=[], required=False)

    _write_scoring_contract(out_dir)
    copied.setdefault("scorer", []).append(str(out_dir / "scorer" / "scoring_contract.md"))
    for source_name in ("epistemic_resilience.py", "uncued_report.py", "uncued_scorer_audit.py"):
        _copy_file(project_dir / "eha" / source_name, out_dir / "scorer" / source_name, copied=copied, category="scorer", missing_required=[], required=False)

    examples_dir = out_dir / "examples"
    examples_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        examples_dir / "example_task_visible.json",
        {
            "task": _first_jsonl(dataset_dir / "tasks.jsonl"),
            "visible_document": _first_jsonl(dataset_dir / "documents_neutral_metadata_visible.jsonl"),
            "prediction": _first_jsonl(run_dir / "predictions.jsonl"),
        },
    )
    copied.setdefault("examples", []).append(str(examples_dir / "example_task_visible.json"))

    _write_package_readme(out_dir)
    _write_scripts(out_dir)
    copied.setdefault("root", []).extend([str(out_dir / "README.md"), str(out_dir / "reproduce_minimal.sh"), str(out_dir / "verify_uncued_phase1.sh")])

    if not (out_dir / "outputs" / "predictions.jsonl").exists():
        missing_required.append(str(run_dir / "predictions.jsonl"))
    if not (out_dir / "baselines" / "eha_uncued_baselines_pilot.json").exists():
        missing_required.append(str(reports_dir / "eha_uncued_baselines_pilot.json"))
    if not (out_dir / "audits" / "eha_uncued_leakage_pilot.json").exists():
        missing_required.append(str(reports_dir / "eha_uncued_leakage_pilot.json"))
    if not (out_dir / "audits" / "eha_uncued_human_leakage_review_pilot_validation.json").exists():
        missing_required.append(str(reports_dir / "eha_uncued_human_leakage_review_pilot_validation.json"))
    if not (out_dir / "audits" / "eha_uncued_scorer_audit.json").exists():
        missing_required.append(str(reports_dir / "eha_uncued_scorer_audit.json"))

    hashes = _artifact_hashes(out_dir)
    manifest = {
        "scientific_status": "role_uncued_phase1_pilot_artifact",
        "phase": 16,
        "date": report_date,
        "dataset_dir": str(dataset_dir),
        "run_dir": str(run_dir),
        "reports_dir": str(reports_dir),
        "repo_root": str(repo_root),
        "cued_artifacts_included": False,
        "visible_file_policy": "model-visible data and prompts must exclude hidden labels, gold verdicts, and construction roles",
        "prompt_file_count": prompt_manifest["prompt_file_count"],
        "response_file_count": prompt_manifest["response_file_count"],
        "missing_required_inputs": sorted(set(missing_required)),
        "copied_files": {name: sorted(paths) for name, paths in sorted(copied.items())},
        "hashes": hashes,
    }
    write_json(out_dir / "manifest.json", manifest)
    if missing_required:
        raise FileNotFoundError("missing required uncued phase1 package inputs: " + ", ".join(sorted(set(missing_required))))
    return manifest


def _load_json_if_exists(path: Path) -> Dict[str, Any]:
    return read_json(path) if path.exists() else {}


def _bool_path(payload: Mapping[str, Any], *path: str) -> bool:
    current: Any = payload
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return False
        current = current[key]
    return bool(current)


def _scan_hidden_markers(paths: Sequence[Path], root: Path) -> list[Dict[str, str]]:
    hits: list[Dict[str, str]] = []
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in HIDDEN_PROMPT_MARKERS:
            if marker in text:
                hits.append({"file": str(path.relative_to(root)), "marker": marker})
    return hits


def _hash_mismatches(artifact_dir: Path, manifest: Mapping[str, Any]) -> list[Dict[str, str]]:
    mismatches: list[Dict[str, str]] = []
    hashes = manifest.get("hashes", {})
    if not isinstance(hashes, Mapping):
        return [{"file": "manifest.json", "expected": "hash mapping", "actual": "missing_or_invalid"}]
    for rel_path, expected in sorted(hashes.items()):
        path = artifact_dir / str(rel_path)
        if not path.exists():
            mismatches.append({"file": str(rel_path), "expected": str(expected), "actual": "missing"})
            continue
        actual = file_sha256(path)
        if actual != expected:
            mismatches.append({"file": str(rel_path), "expected": str(expected), "actual": actual})
    return mismatches


def verify_uncued_phase1(
    artifact_dir: Path,
    *,
    reports_dir: Path,
    out_dir: Path,
    report_date: str = DEFAULT_REPORT_DATE,
) -> Dict[str, Any]:
    manifest_path = artifact_dir / "manifest.json"
    manifest = _load_json_if_exists(manifest_path)
    missing_layout = [rel for rel in REQUIRED_ARTIFACT_FILES if not (artifact_dir / rel).exists()]
    hash_mismatches = _hash_mismatches(artifact_dir, manifest) if manifest else [{"file": "manifest.json", "expected": "present", "actual": "missing"}]
    visible_scan_paths = [artifact_dir / "data" / "documents_neutral_metadata_visible.jsonl"]
    prompts_dir = artifact_dir / "prompts"
    if prompts_dir.exists():
        visible_scan_paths.extend(sorted(prompts_dir.rglob("*.prompt.json")))
    visible_hidden_label_hits = _scan_hidden_markers(visible_scan_paths, artifact_dir)

    leakage = _load_json_if_exists(reports_dir / "eha_uncued_leakage_pilot.json")
    baselines = _load_json_if_exists(reports_dir / "eha_uncued_baselines_pilot.json")
    human_review = _load_json_if_exists(reports_dir / "eha_uncued_human_leakage_review_pilot_validation.json")
    pilot_run = _load_json_if_exists(reports_dir / "eha_uncued_pilot_run.json")
    pilot_results = _load_json_if_exists(reports_dir / "eha_uncued_pilot_results.json")
    scorer_audit = _load_json_if_exists(reports_dir / "eha_uncued_scorer_audit.json")
    schema_ablation = _load_json_if_exists(reports_dir / "eha_uncued_schema_ablation_plan.json")

    expected_records = int(pilot_run.get("expected_records", 0) or 0)
    actual_records = int(pilot_run.get("actual_records", 0) or 0)
    pilot_results_acceptance = _bool_path(pilot_results, "acceptance", "phase13_acceptance_passed") or bool(pilot_results.get("phase13_acceptance_passed"))
    scorer_reviewed_rows = int(scorer_audit.get("reviewed_rows", 0) or 0)
    gates = {
        "required_layout_present": not missing_layout,
        "manifest_status_role_uncued": manifest.get("scientific_status") == "role_uncued_phase1_pilot_artifact",
        "manifest_hashes_match": not hash_mismatches,
        "model_visible_files_exclude_hidden_labels": not visible_hidden_label_hits,
        "gold_and_scorer_data_included": (artifact_dir / "data" / "gold_labels.jsonl").exists() and (artifact_dir / "audits" / "eha_uncued_scorer_audit.json").exists(),
        "prompt_files_included": int(manifest.get("prompt_file_count", 0) or 0) > 0,
        "leakage_gate_passed": bool(leakage.get("passed")) and int(leakage.get("critical_hits", 0) or 0) == 0 and int(leakage.get("high_hits", 0) or 0) == 0,
        "baseline_gate_passed": bool(baselines.get("passed")),
        "human_leakage_gate_passed": bool(human_review.get("passed")) and int(human_review.get("critical_leaks", 0) or 0) == 0,
        "model_run_complete": expected_records > 0 and actual_records == expected_records and _bool_path(pilot_run, "prompt_audit", "passed") and _bool_path(pilot_run, "stored_hidden_label_audit", "passed"),
        "scored_results_complete": pilot_results_acceptance and int(pilot_results.get("scored_rows", 0) or 0) > 0 and bool(pilot_results.get("required_tables_present", True)),
        "scorer_audit_complete": scorer_reviewed_rows >= 30 and not bool(scorer_audit.get("systematic_scorer_bug_found", True)) and not bool(scorer_audit.get("rescoring_required", True)),
        "schema_ablation_status_explicit": schema_ablation.get("status") == "skipped_under_runbook_rule" and schema_ablation.get("model_calls_made") == 0,
        "minimal_reproduction_script_present": (artifact_dir / "reproduce_minimal.sh").exists(),
        "artifact_verifier_script_present": (artifact_dir / "verify_uncued_phase1.sh").exists(),
    }
    decision = "pass" if all(gates.values()) else "fail"
    payload = {
        "date": report_date,
        "phase": 17,
        "artifact_dir": str(artifact_dir),
        "reports_dir": str(reports_dir),
        "decision": decision,
        "gates": gates,
        "missing_layout": missing_layout,
        "hash_mismatches": hash_mismatches,
        "visible_hidden_label_hits": visible_hidden_label_hits,
        "model_run": {
            "expected_records": expected_records,
            "actual_records": actual_records,
            "status": pilot_run.get("status"),
            "cost": pilot_run.get("cost", {}),
        },
        "scored_results": {
            "status": pilot_results.get("status"),
            "scored_rows": pilot_results.get("scored_rows"),
            "phase13_acceptance_passed": pilot_results_acceptance,
        },
        "scorer_audit": {
            "reviewed_rows": scorer_reviewed_rows,
            "systematic_scorer_bug_found": scorer_audit.get("systematic_scorer_bug_found"),
            "rescoring_required": scorer_audit.get("rescoring_required"),
            "independent_human_review": scorer_audit.get("independent_human_review", False),
        },
        "schema_ablation": {
            "status": schema_ablation.get("status"),
            "model_calls_made": schema_ablation.get("model_calls_made"),
            "decision": schema_ablation.get("decision"),
        },
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_uncued_phase1_readiness.json", payload)
    lines = [
        "# EHA-Uncued Phase 1 Readiness",
        "",
        f"Date: {report_date}",
        "",
        f"Decision: `{decision}`",
        "",
        "## Gates",
        "",
    ]
    for gate, passed in gates.items():
        lines.append(f"- `{gate}`: {str(passed).lower()}")
    if missing_layout:
        lines.extend(["", "## Missing Layout", ""])
        lines.extend(f"- `{item}`" for item in missing_layout)
    if hash_mismatches:
        lines.extend(["", "## Hash Mismatches", ""])
        lines.extend(f"- `{item['file']}`" for item in hash_mismatches)
    if visible_hidden_label_hits:
        lines.extend(["", "## Visible Hidden-Label Hits", ""])
        lines.extend(f"- `{hit['file']}` matched `{hit['marker']}`" for hit in visible_hidden_label_hits)
    lines.append("")
    (out_dir / f"eha-uncued-phase1-readiness-{report_date}.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


@package_app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Pilot dataset directory."),
    run_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Pilot run directory."),
    out_dir: Path = typer.Option(Path("../artifact_uncued_phase1"), help="Artifact output directory."),
    reports_dir: Path = typer.Option(Path("../reports"), help="Reports directory."),
) -> None:
    manifest = package_uncued_phase1(dataset_dir, run_dir, out_dir, reports_dir=reports_dir)
    console.print(f"Wrote uncued package manifest to {out_dir / 'manifest.json'} with {len(manifest['hashes'])} hashed files.")


@verify_app.callback(invoke_without_command=True)
def verify_root(
    ctx: typer.Context,
    artifact_dir: Path = typer.Option(Path("../artifact_uncued_phase1"), help="Uncued Phase 1 artifact directory."),
    reports_dir: Path = typer.Option(Path("../reports"), help="Reports directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Readiness output directory."),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    payload = verify_uncued_phase1(artifact_dir, reports_dir=reports_dir, out_dir=out_dir)
    console.print(f"Uncued Phase 1 readiness decision={payload['decision']}.")
    if payload["decision"] != "pass":
        raise typer.Exit(code=1)


@verify_app.command("micro-gate")
def micro_gate(
    dataset_dir: Path = typer.Option(Path("data/uncued-micro"), help="Micro dataset directory."),
    reports_dir: Path = typer.Option(Path("../reports"), help="Reports directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Gate output directory."),
) -> None:
    payload = freeze_micro_gate(dataset_dir, reports_dir, out_dir)
    console.print(f"Micro gate decision={payload['decision']}.")


@verify_app.command("reject-cued-artifact")
def reject_cued_artifact(
    artifact_dir: Path = typer.Option(Path("../artifact"), help="Existing cued artifact directory."),
) -> None:
    if not refuses_cued_artifact_as_uncued_evidence(artifact_dir):
        raise typer.Exit(code=1)
    console.print(f"Rejected {artifact_dir} as EHA-Uncued Phase 1 evidence.")
