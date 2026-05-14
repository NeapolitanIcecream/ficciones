from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import typer
from rich.console import Console


app = typer.Typer(add_completion=False, help="Audit Epistemic Resilience Table artifacts.")
console = Console()

EXPECTED_FAMILIES = {
    "packet_judgment": 40,
    "evidence_selection": 40,
    "active_verification": 20,
}
EXPECTED_CONDITIONS = {
    "clean": 20,
    "conflicting_evidence": 20,
    "false_consensus": 20,
    "buried_primary": 20,
    "generated_lore": 20,
}
EXPECTED_MODELS = {
    "openai/gpt-4o-mini",
    "openai/gpt-5-mini",
    "openai/gpt-5.4-mini",
    "openai/gpt-5.5",
}
EXPECTED_PROMPTS = {
    "standard_answer",
    "epistemic_hygiene_instruction",
}
REQUIRED_REPORT_FILES = {
    "summary.md",
    "main_table.csv",
    "by_family.csv",
    "by_condition.csv",
    "scored_predictions.csv",
    "cost_report.json",
    "audit_manifest.json",
}
REQUIRED_MAIN_TABLE_COLUMNS = {
    "model",
    "prompt",
    "n",
    "packet_judgment",
    "evidence_selection",
    "active_verification",
    "avg_epistemic_escape",
}
REQUIRED_SCORED_COLUMNS = {
    "task_id",
    "family",
    "condition",
    "model",
    "prompt_condition",
    "parse_success",
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
    "epistemic_escape",
    "cost_usd",
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def check(name: str, passed: bool, details: Mapping[str, Any]) -> Dict[str, Any]:
    return {"name": name, "status": "pass" if passed else "fail", "details": dict(details)}


def run_command(command: List[str]) -> Dict[str, Any]:
    completed = subprocess.run(command, check=False, text=True, capture_output=True)
    return {
        "cmd": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }


def model_counts(records: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for record in records:
        model = str(record["model"])
        counts[model] = counts.get(model, 0) + 1
    return counts


@app.command("run")
def run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared task directory."),
    run_dir: Path = typer.Option(Path("results/runs/epistemic-resilience-v1-api-final"), help="Final merged run directory."),
    report_dir: Path = typer.Option(Path("results/reports-epistemic-resilience-v1"), help="Report directory."),
    out: Path = typer.Option(Path("results/reports-epistemic-resilience-v1/artifact_audit.json"), help="Machine-readable audit output."),
    run_tests: bool = typer.Option(True, "--run-tests/--skip-tests", help="Run uv test gate during audit."),
    run_compile: bool = typer.Option(True, "--run-compile/--skip-compile", help="Run compileall gate during audit."),
) -> None:
    checks: List[Dict[str, Any]] = []
    commands: List[Dict[str, Any]] = []

    task_manifest = read_json(task_dir / "manifest.json")
    checks.append(
        check(
            "task_manifest",
            task_manifest.get("task_count") == 100
            and task_manifest.get("family_counts") == EXPECTED_FAMILIES
            and task_manifest.get("condition_counts") == EXPECTED_CONDITIONS,
            {
                "task_count": task_manifest.get("task_count"),
                "family_counts": task_manifest.get("family_counts"),
                "condition_counts": task_manifest.get("condition_counts"),
            },
        )
    )

    records = read_jsonl(run_dir / "predictions.jsonl")
    run_manifest = read_json(run_dir / "run_manifest.json")
    prompts = {str(record["prompt_condition"]) for record in records}
    checks.append(
        check(
            "run_predictions",
            len(records) == 624 and set(model_counts(records)) == EXPECTED_MODELS and prompts == EXPECTED_PROMPTS,
            {
                "prediction_count": len(records),
                "model_counts": model_counts(records),
                "prompt_conditions": sorted(prompts),
                "run_manifest": run_manifest,
            },
        )
    )

    gpt55 = [record for record in records if record["model"] == "openai/gpt-5.5"]
    gpt55_conditions: Dict[str, int] = {}
    for record in gpt55:
        condition = str(record["condition"])
        gpt55_conditions[condition] = gpt55_conditions.get(condition, 0) + 1
    checks.append(
        check(
            "sample_model_condition_coverage",
            len(gpt55) == 24 and set(gpt55_conditions) == set(EXPECTED_CONDITIONS),
            {"record_count": len(gpt55), "condition_counts": gpt55_conditions},
        )
    )

    existing_files = {path.name for path in report_dir.iterdir() if path.is_file()}
    checks.append(check("report_files", REQUIRED_REPORT_FILES.issubset(existing_files), {"missing": sorted(REQUIRED_REPORT_FILES - existing_files)}))

    main_rows = read_csv(report_dir / "main_table.csv")
    by_family_rows = read_csv(report_dir / "by_family.csv")
    by_condition_rows = read_csv(report_dir / "by_condition.csv")
    scored_rows = read_csv(report_dir / "scored_predictions.csv")
    main_columns = set(main_rows[0]) if main_rows else set()
    scored_columns = set(scored_rows[0]) if scored_rows else set()
    checks.append(
        check(
            "report_tables",
            len(main_rows) == 8
            and len(by_family_rows) == 24
            and len(by_condition_rows) == 40
            and len(scored_rows) == 624
            and REQUIRED_MAIN_TABLE_COLUMNS.issubset(main_columns)
            and REQUIRED_SCORED_COLUMNS.issubset(scored_columns),
            {
                "main_table_rows": len(main_rows),
                "by_family_rows": len(by_family_rows),
                "by_condition_rows": len(by_condition_rows),
                "scored_rows": len(scored_rows),
                "missing_main_columns": sorted(REQUIRED_MAIN_TABLE_COLUMNS - main_columns),
                "missing_scored_columns": sorted(REQUIRED_SCORED_COLUMNS - scored_columns),
            },
        )
    )

    report_manifest = read_json(report_dir / "audit_manifest.json")
    checks.append(
        check(
            "report_manifest",
            report_manifest.get("task_count") == 100
            and report_manifest.get("prediction_count") == 624
            and report_manifest.get("scored_rows") == 624
            and report_manifest.get("main_table_rows") == 8
            and report_manifest.get("by_family_rows") == 24
            and report_manifest.get("by_condition_rows") == 40,
            report_manifest,
        )
    )

    cost_report = read_json(report_dir / "cost_report.json")
    checks.append(check("cost_report", not bool(cost_report.get("aborted")), {"aborted": cost_report.get("aborted"), "spent_usd": cost_report.get("spent_usd")}))

    if run_tests:
        result = run_command(["uv", "run", "pytest"])
        commands.append(result)
        checks.append(check("pytest", result["returncode"] == 0, {"cmd": result["cmd"], "returncode": result["returncode"]}))

    if run_compile:
        result = run_command(["uv", "run", "python", "-m", "compileall", "eha"])
        commands.append(result)
        checks.append(check("compileall", result["returncode"] == 0, {"cmd": result["cmd"], "returncode": result["returncode"]}))

    passed = all(item["status"] == "pass" for item in checks)
    payload = {"status": "pass" if passed else "fail", "checks": checks, "commands": commands}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not passed:
        console.print(f"[red]Artifact audit failed[/red]: {out}")
        raise typer.Exit(code=1)
    console.print(f"[green]Artifact audit passed[/green]: {out}")


if __name__ == "__main__":
    app()
