from __future__ import annotations

from pathlib import Path

from eha.uncued_core_claim_report import (
    paired_schema_deltas,
    plan_core_schema_rerun,
    verify_core_claim_run,
)


DATASET_DIR = Path("data/uncued-pilot-v1")


def test_core_claim_schema_plan_freezes_default_slice_and_prompt_audit(tmp_path: Path) -> None:
    manifest = plan_core_schema_rerun(
        dataset_dir=DATASET_DIR,
        out_dir=tmp_path,
        seed=20260525,
        view="neutral_metadata_visible",
        budget_constrained=False,
        models="gpt-5.5,gemini-3.1-pro-preview",
        hard_cap_usd=20.0,
    )

    assert manifest["source_task_count"] == 36
    assert manifest["planned_calls"] == 144
    assert manifest["schema_variants"] == ["current_phase1", "role_decomposed_v1"]
    assert (tmp_path / "selection_manifest.json").exists()
    assert (tmp_path / "schema_rerun_prompt_audit.json").exists()


def test_paired_schema_deltas_use_current_and_decomposed_pair() -> None:
    rows = [
        {
            "task_id": "uncued_048_visible",
            "base_task_id": "uncued_048",
            "model": "fixture-model",
            "schema_variant": "current_phase1",
            "condition": "generated_lore",
            "family": "packet_judgment",
            "belief_correctness": 1,
            "polluted_in_support": 1,
            "clean_support_recovered": 0,
            "pollutant_rejection": 0,
            "role_escape": 0,
            "operational_contract_success": 0,
        },
        {
            "task_id": "uncued_048_visible",
            "base_task_id": "uncued_048",
            "model": "fixture-model",
            "schema_variant": "role_decomposed_v1",
            "condition": "generated_lore",
            "family": "packet_judgment",
            "belief_correctness": 1,
            "polluted_in_support": 0,
            "clean_support_recovered": 0,
            "pollutant_rejection": 1,
            "role_escape": 1,
            "operational_contract_success": 1,
        },
    ]

    deltas = paired_schema_deltas(rows)

    assert len(deltas) == 1
    assert deltas[0]["delta_polluted_in_support"] == -1
    assert deltas[0]["delta_operational_contract_success"] == 1


def test_verifier_fails_when_required_outputs_are_missing(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    reports_dir = tmp_path / "reports"
    run_dir.mkdir()
    reports_dir.mkdir()

    result = verify_core_claim_run(run_dir=run_dir, reports_dir=reports_dir)

    assert result["decision"] == "fail"
    assert result["missing_run_files"]
