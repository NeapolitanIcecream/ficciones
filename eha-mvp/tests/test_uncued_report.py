from __future__ import annotations

import json
from pathlib import Path

from eha.epistemic_resilience import EpistemicPrediction, EpistemicRunRecord
from eha.schemas import model_to_dict, write_jsonl
from eha.uncued_report import write_uncued_pilot_report
from eha.uncued_run import selected_uncued_tasks


def test_uncued_report_writes_required_phase13_tables(tmp_path: Path) -> None:
    tasks = selected_uncued_tasks(Path("data/uncued-pilot-v1"), ["neutral_metadata_visible"])
    records = [
        EpistemicRunRecord(
            task_id=task.task_id,
            family=task.family,
            condition=task.condition,
            model="spec-model",
            provider="Spec",
            budget_setting="operational",
            prompt_condition="standard_answer",
            backend="api",
            prediction=EpistemicPrediction(
                claim_verdict=task.gold_verdict,
                confidence=0.8,
                supporting_evidence=task.primary_doc_ids[:1],
                rejected_evidence=task.contaminant_doc_ids[:1],
                selected_doc_ids=task.primary_doc_ids[:1],
                actions=[],
                evidence_environment_assessment="Structured report fixture.",
                answer="Fixture answer.",
            ),
            parse_success=True,
            cost_usd=0.01,
        )
        for task in tasks[:6]
    ]
    run_dir = tmp_path / "run"
    out_dir = tmp_path / "report"
    run_dir.mkdir()
    write_jsonl(run_dir / "predictions.jsonl", [model_to_dict(record) for record in records])
    (run_dir / "cost_report.json").write_text(
        json.dumps({"aborted": False, "spent_usd": 0.06, "record_cost_usd": 0.06}),
        encoding="utf-8",
    )

    manifest = write_uncued_pilot_report(
        dataset_dir=Path("data/uncued-pilot-v1"),
        run_dir=run_dir,
        out_dir=out_dir,
    )

    assert manifest["prediction_count"] == 6
    assert manifest["required_tables_present"] is True
    for name in [
        "uncued_pilot_metrics_by_model.csv",
        "uncued_pilot_metrics_by_view.csv",
        "uncued_pilot_metrics_by_condition.csv",
        "uncued_pilot_metrics_by_family.csv",
        "uncued_pilot_metrics_by_model_view.csv",
        "uncued_pilot_metrics_by_model_condition.csv",
        "uncued_pilot_baselines_vs_models.csv",
        "uncued_pilot_active_verification_action_metrics.csv",
        "uncued_pilot_acceptance_diagnostics.json",
        "summary.md",
    ]:
        assert (out_dir / name).exists()
