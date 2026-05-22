from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import typer
from rich.console import Console

from .schemas import write_json
from .uncued_contract import DEFAULT_REPORT_DATE


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


@package_app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Pilot dataset directory."),
    run_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Pilot run directory."),
    out_dir: Path = typer.Option(Path("../artifact_uncued_phase1"), help="Artifact output directory."),
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": "not_built_by_phase8",
        "dataset_dir": str(dataset_dir),
        "run_dir": str(run_dir),
        "note": "Packaging is intentionally deferred until after the 60-task pilot and model/scorer audit phases.",
    }
    write_json(out_dir / "manifest.json", manifest)
    console.print(f"Wrote placeholder uncued package manifest to {out_dir / 'manifest.json'}.")


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

