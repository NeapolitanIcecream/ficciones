from __future__ import annotations

import csv
import json
import os
from pathlib import Path

from eha.epistemic_resilience import EpistemicPrediction, EpistemicRunRecord, build_epistemic_tasks, score_record
from eha.epistemic_step1_release import (
    always_insufficient_prediction,
    build_active_verification_audit_package,
    build_artifact_package,
    file_sha256,
    finalize_active_verification_human_audit,
    import_active_verification_model_blinded_human_audit_worksheet,
    import_active_verification_human_audit_worksheet,
    random_valid_schema_prediction,
    run_step1_baselines,
    step1_readiness_check,
    summarize_active_verification_human_audit,
    validate_active_verification_human_audit,
    write_artifact_file_manifest,
)


def test_score_record_reports_diagnostic_metrics_for_support_roles() -> None:
    task = next(task for task in build_epistemic_tasks(Path("data/matrix-v1")) if task.family == "packet_judgment" and task.condition == "false_consensus")
    clean = task.primary_doc_ids[0]
    dirty = task.contaminant_doc_ids[0]
    record = EpistemicRunRecord(
        task_id=task.task_id,
        family=task.family,
        condition=task.condition,
        model="diagnostic-test",
        prompt_condition="standard_answer",
        backend="baseline",
        prediction=EpistemicPrediction(
            claim_verdict=task.gold_verdict,
            confidence=0.7,
            supporting_evidence=[clean, dirty],
            rejected_evidence=[dirty],
        ),
        parse_success=True,
    )

    row = score_record(record, task)

    assert row["support_empty_rate"] == 0.0
    assert row["evidence_precision"] == 0.5
    assert row["clean_support_recall"] == 0.5
    assert row["rejected_pollutant_rate"] == 1.0
    assert row["dual_role_rate"] == 1.0


def test_step1_baseline_predictions_are_valid_schema_outputs() -> None:
    task = build_epistemic_tasks(Path("data/matrix-v1"))[0]

    random_prediction = random_valid_schema_prediction(task, "standard_answer")
    insufficient_prediction = always_insufficient_prediction(task, "standard_answer")

    assert random_prediction.claim_verdict in {"supported", "refuted", "insufficient"}
    assert len(random_prediction.selected_doc_ids) <= task.max_selected_docs
    assert insufficient_prediction.claim_verdict == "insufficient"
    assert insufficient_prediction.supporting_evidence == []
    assert insufficient_prediction.selected_doc_ids == []


def test_run_step1_baselines_writes_random_and_always_insufficient_outputs(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    out_dir = tmp_path / "reports"
    task_dir.mkdir()
    tasks = build_epistemic_tasks(Path("data/matrix-v1"))[:2]
    (task_dir / "tasks.jsonl").write_text("\n".join(json.dumps(task.model_dump(), ensure_ascii=False) for task in tasks) + "\n", encoding="utf-8")

    run_step1_baselines(task_dir=task_dir, out_dir=out_dir, baselines=["random_valid_schema", "always_insufficient"])

    summary_rows = list(csv.DictReader((out_dir / "baseline_summary.csv").open()))
    assert {row["model"] for row in summary_rows} == {"random_valid_schema_baseline", "always_insufficient_baseline"}
    assert (out_dir / "random_valid_schema_baseline_predictions.jsonl").exists()
    assert (out_dir / "always_insufficient_baseline.csv").exists()


def test_artifact_package_contains_required_release_files(tmp_path: Path) -> None:
    task_dir = tmp_path / "tasks"
    baseline_dir = tmp_path / "baselines"
    generated_lore_dir = tmp_path / "generated_lore"
    artifact_dir = tmp_path / "artifact"
    task_dir.mkdir()
    generated_lore_dir.mkdir()
    all_tasks = build_epistemic_tasks(Path("data/matrix-v1"))
    generated_task = next((task for task in all_tasks if task.generated_doc_ids), all_tasks[0])
    tasks = [generated_task, *[task for task in all_tasks if task.task_id != generated_task.task_id][:2]]
    (task_dir / "tasks.jsonl").write_text("\n".join(json.dumps(task.model_dump(), ensure_ascii=False) for task in tasks) + "\n", encoding="utf-8")
    (generated_lore_dir / "schema_clarification_mini_rerun.csv").write_text("schema_variant\nclarified_schema\n", encoding="utf-8")
    (generated_lore_dir / "generated_lore_schema_ablation_4variant.csv").write_text("schema_variant\nminimal_schema\n", encoding="utf-8")
    (generated_lore_dir / "generated_lore_schema_ablation_4variant_rows.csv").write_text(
        "schema_variant,model,task_id,prompt_condition,polluted_supporting_ids\nminimal_schema,gpt-5.4,"
        f"{tasks[0].task_id},standard_answer,{tasks[0].generated_doc_ids[0]}\n",
        encoding="utf-8",
    )
    run_step1_baselines(task_dir=task_dir, out_dir=baseline_dir, baselines=["always_insufficient"])

    build_artifact_package(
        task_dir=task_dir,
        frontier_main_dir=Path("results/reports-eha-frontier-main-opaque-2026-05-15"),
        baseline_dir=baseline_dir,
        generated_lore_dir=generated_lore_dir,
        active_verification_dir=Path("results/reports-eha-active-verification-audit-opaque-2026-05-15"),
        out_dir=artifact_dir,
    )

    required = [
        "README.md",
        "file_manifest.json",
        "data/tasks_opaque.jsonl",
        "data/gold_labels.jsonl",
        "prompts/standard_answer.txt",
        "scorer/README.md",
        "outputs/frontier_main_opaque_scored.csv",
        "outputs/frontier_main_opaque_run_manifest.json",
        "outputs/frontier_main_opaque_report_manifest.json",
        "baselines/always_insufficient.csv",
        "audits/opaque_prompt_audit_summary.json",
        "audits/active_verification_action_audit_summary.csv",
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
        "audits/active_verification_pilot_human_audit_summary.json",
        "audits/active_verification_pilot_human_audit_paper_update.md",
        "examples/minimal_task.json",
        "examples/minimal_score.json",
        "reproduce_minimal.sh",
        "serve_human_audit_review.sh",
        "finalize_human_audit.sh",
        "verify_step1_release.sh",
    ]
    for relative in required:
        assert (artifact_dir / relative).exists(), relative

    action_header = (artifact_dir / "audits" / "active_verification_action_audit_summary.csv").read_text(encoding="utf-8").splitlines()[0]
    human_header = (artifact_dir / "audits" / "active_verification_human_audit.csv").read_text(encoding="utf-8").splitlines()[0]
    manifest = json.loads((artifact_dir / "manifest.json").read_text(encoding="utf-8"))
    file_manifest = json.loads((artifact_dir / "file_manifest.json").read_text(encoding="utf-8"))
    file_manifest_paths = {row["path"] for row in file_manifest["files"]}
    assert "manifest.json" in file_manifest_paths
    assert "file_manifest.json" not in file_manifest_paths
    assert "auto_action_gate_pass" in human_header
    assert "model_actions" not in action_header
    assert (artifact_dir / "audits" / "generated_lore_schema_ablation.csv").read_text(encoding="utf-8") == "schema_variant\nminimal_schema\n"
    assert "eham_" not in (artifact_dir / "audits" / "generated_lore_schema_ablation_rows.csv").read_text(encoding="utf-8")
    assert "eham_" not in (artifact_dir / "outputs" / "frontier_main_opaque_predictions.jsonl").read_text(encoding="utf-8")
    assert "eham_" not in (artifact_dir / "outputs" / "frontier_main_opaque_scored.csv").read_text(encoding="utf-8")
    assert "eham_" not in (artifact_dir / "baselines" / "always_insufficient.csv").read_text(encoding="utf-8")
    readme = (artifact_dir / "README.md").read_text(encoding="utf-8")
    assert "step1-readiness-check" in readme
    assert "file_manifest.json" in readme
    assert "serve_human_audit_review.sh" in readme
    assert "finalize_human_audit.sh" in readme
    assert "verify_step1_release.sh" in readme
    assert "reviewer brief" in readme
    assert "not human validation" in readme
    assert "eight required label fields" in readme
    assert "audit_status = human_labeled" in readme
    assert "n_labeled = 50" in readme
    assert "auditor_notes" in readme
    assert "prints the readiness status plus any failing gates" in readme
    assert "legal, medical, financial" in readme
    audit_manifest = json.loads((artifact_dir / "audits" / "active_verification_human_audit_manifest.json").read_text(encoding="utf-8"))
    assert "trace_source_needed" in audit_manifest["label_fields"]
    audit_readme = (artifact_dir / "audits" / "active_verification_human_audit_readme.md").read_text(encoding="utf-8")
    assert "finalize-active-verification-human-audit" in audit_readme
    assert "./finalize_human_audit.sh --from-worksheet" in audit_readme
    assert "./finalize_human_audit.sh --from-model-blinded-worksheet" in audit_readme
    assert "reference-only triage" in audit_readme
    assert "eight binary label columns" in audit_readme
    assert "paper-update memo" in audit_readme
    assert "active_verification_human_audit_reviewer_brief.md" in audit_readme
    assert "active_verification_human_audit_attestation.md" in audit_readme
    assert "prints the readiness status and failing gates" in audit_readme
    reviewer_brief = (artifact_dir / "audits" / "active_verification_human_audit_reviewer_brief.md").read_text(
        encoding="utf-8"
    )
    assert "Use this brief" in reviewer_brief
    assert "50 rows" in reviewer_brief
    assert "audit_status = human_labeled" in reviewer_brief
    assert "`semantically_useful_action`" in reviewer_brief
    assert "`scorer_too_strict`" in reviewer_brief
    assert "auditor_notes" in reviewer_brief
    assert "reference-only triage" in reviewer_brief
    assert "active_verification_human_audit_attestation.md" in reviewer_brief
    assert "./finalize_human_audit.sh --from-model-blinded-worksheet" in reviewer_brief
    audit_protocol = (artifact_dir / "audits" / "active_verification_human_audit_protocol.md").read_text(encoding="utf-8")
    assert "single-auditor pilot audit" in audit_protocol
    assert "10 rows per condition" in audit_protocol
    assert "Codex-assisted labels are triage evidence only" in audit_protocol
    assert "Model identities, prompt conditions, and automatic scorer outcomes are intentionally omitted" in audit_protocol
    assert "n_complete_rows = 50" in audit_protocol
    assert "active_verification_human_audit_attestation.md" in audit_protocol
    attestation = (artifact_dir / "audits" / "active_verification_human_audit_attestation.md").read_text(encoding="utf-8")
    assert "auditor_identifier:" in attestation
    assert "independent_human_review_completed:" in attestation
    assert "codex_triage_not_copied_as_human_labels:" in attestation
    assert "all_eight_binary_fields_and_auditor_notes_completed:" in attestation
    model_blinded_packet = (artifact_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_packet_50.md").read_text(
        encoding="utf-8"
    )
    assert "Model identities and prompt conditions are intentionally omitted" in model_blinded_packet
    assert "Auto scorer outcomes are intentionally omitted" in model_blinded_packet
    assert "Use row order to transfer labels" in model_blinded_packet
    assert "active_verification_human_audit.csv" in model_blinded_packet
    assert "standard_answer" not in model_blinded_packet
    assert "epistemic_hygiene_instruction" not in model_blinded_packet
    assert "gpt-5.4" not in model_blinded_packet
    assert "action_gate_pass" not in model_blinded_packet
    model_blinded_worksheet = list(csv.DictReader((artifact_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv").open()))
    assert model_blinded_worksheet
    assert "row_index" in model_blinded_worksheet[0]
    assert "model" not in model_blinded_worksheet[0]
    assert "task_id" not in model_blinded_worksheet[0]
    assert "prompt_condition" not in model_blinded_worksheet[0]
    assert "auto_action_gate_pass" not in model_blinded_worksheet[0]
    assert "model_actions" in model_blinded_worksheet[0]
    review_html = (artifact_dir / "audits" / "active_verification_human_audit_review.html").read_text(encoding="utf-8")
    assert "Download strict CSV" in review_html
    assert "Import strict CSV draft" in review_html
    assert "Next incomplete row" in review_html
    assert "condition-filter" in review_html
    assert "active_verification_human_audit.csv" in review_html
    assert "const referenceRows" in review_html
    assert "validateImportedRows" in review_html
    assert "applyConditionFilter" in review_html
    assert "download.disabled" in review_html
    assert "human_labeled" in review_html
    assert "eham_" not in review_html
    serve_script = (artifact_dir / "serve_human_audit_review.sh").read_text(encoding="utf-8")
    assert "127.0.0.1" in serve_script
    assert "active_verification_human_audit_review.html" in serve_script
    assert "python3 -m http.server" in serve_script
    assert serve_script.startswith("#!/usr/bin/env bash")
    finalize_script = (artifact_dir / "finalize_human_audit.sh").read_text(encoding="utf-8")
    assert "finalize-active-verification-human-audit" in finalize_script
    assert "import-active-verification-human-audit-worksheet" in finalize_script
    assert "artifact-package" in finalize_script
    assert "step1-readiness-check" in finalize_script
    assert "--from-worksheet" in finalize_script
    assert "active_verification_human_audit_attestation.md" in finalize_script
    assert 'cp "$attestation_md"' in finalize_script
    assert "Step 1 readiness status:" in finalize_script
    assert "Failing gates:" in finalize_script
    assert finalize_script.startswith("#!/usr/bin/env bash")
    verify_script = (artifact_dir / "verify_step1_release.sh").read_text(encoding="utf-8")
    assert "./reproduce_minimal.sh" in verify_script
    assert "uv run pytest" in verify_script
    assert "step1-readiness-check" in verify_script
    assert "git diff --check" in verify_script
    assert "--allow-blocked" in verify_script
    assert verify_script.startswith("#!/usr/bin/env bash")
    assert manifest["active_verification_human_audit"]["n_rows"] == 50
    assert manifest["active_verification_human_audit"]["status"] == "incomplete"
    completed_attestation = "\n".join(
        [
            "# Active-Verification Human-Audit Attestation",
            "",
            "auditor_identifier: preserved-auditor",
            "date_completed: 2026-05-16",
            "audit_surface_used: model_blinded_worksheet",
            "independent_human_review_completed: yes",
            "codex_triage_not_copied_as_human_labels: yes",
            "all_50_rows_reviewed: yes",
            "all_eight_binary_fields_and_auditor_notes_completed: yes",
            "",
            "The independent human review covered all 50 rows.",
            "Codex-assisted audit was not copied as human labels.",
            "All eight binary label fields and auditor_notes were completed.",
        ]
    )
    (artifact_dir / "audits" / "active_verification_human_audit_attestation.md").write_text(completed_attestation + "\n", encoding="utf-8")
    build_artifact_package(
        task_dir=task_dir,
        frontier_main_dir=Path("results/reports-eha-frontier-main-opaque-2026-05-15"),
        baseline_dir=baseline_dir,
        generated_lore_dir=generated_lore_dir,
        active_verification_dir=Path("results/reports-eha-active-verification-audit-opaque-2026-05-15"),
        out_dir=artifact_dir,
    )
    preserved_attestation = (artifact_dir / "audits" / "active_verification_human_audit_attestation.md").read_text(encoding="utf-8")
    assert "auditor_identifier: preserved-auditor" in preserved_attestation
    assert "[TO BE COMPLETED" not in preserved_attestation


def test_active_verification_audit_package_contains_context_with_opaque_ids(tmp_path: Path) -> None:
    sample_path = tmp_path / "sample.csv"
    sample_path.write_text(
        "\n".join(
            [
                "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids",
                'needs_human_label,gpt-5.4,ert_082,clean,standard_answer,,,,,0.0,1.0,0.0,,,0.0,1.0,0.0,0.0,"[{""action"": ""trace_source"", ""target"": ""doc_007"", ""rationale"": ""Check stale path.""}]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "audit"

    build_active_verification_audit_package(
        sample_csv=sample_path,
        task_dir=Path("data/epistemic-resilience-v1"),
        out_dir=out_dir,
    )

    context = json.loads((out_dir / "active_verification_pilot_human_audit_context_50.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert context["task_id"] == "ert_082"
    assert context["question"]
    assert context["model_actions"][0]["target"] == "doc_007"
    assert all(doc["doc_id"].startswith("doc_") for doc in context["documents"])
    assert "audit_role" in context["documents"][0]
    serialized = json.dumps(context, ensure_ascii=False)
    assert "eham_" not in serialized
    assert "pollutant_root" not in serialized
    assert (out_dir / "active_verification_human_audit_guidelines.md").exists()
    assert (out_dir / "active_verification_human_audit_readme.md").exists()
    assert (out_dir / "active_verification_human_audit_reviewer_brief.md").exists()
    assert (out_dir / "active_verification_human_audit_protocol.md").exists()
    assert (out_dir / "active_verification_human_audit_attestation.md").exists()
    assert (out_dir / "active_verification_human_audit_review.html").exists()
    packet = (out_dir / "active_verification_pilot_human_audit_packet_50.md").read_text(encoding="utf-8")
    assert "## Row 01: ert_082 / gpt-5.4 / clean / standard_answer" in packet
    assert "target=`doc_007`" in packet
    assert "- semantically_useful_action: " in packet
    assert "- contradiction_search_needed: " in packet
    assert "eham_" not in packet
    assert "pollutant_root" not in packet
    model_blinded_packet = (out_dir / "active_verification_pilot_human_audit_model_blinded_packet_50.md").read_text(encoding="utf-8")
    assert "## Row 01" in model_blinded_packet
    assert "Evidence condition: clean" in model_blinded_packet
    assert "target=`doc_007`" in model_blinded_packet
    assert "Model identities and prompt conditions are intentionally omitted" in model_blinded_packet
    assert "Auto scorer outcomes are intentionally omitted" in model_blinded_packet
    assert "gpt-5.4" not in model_blinded_packet
    assert "standard_answer" not in model_blinded_packet
    assert "action_gate_pass" not in model_blinded_packet
    assert "eham_" not in model_blinded_packet
    assert "pollutant_root" not in model_blinded_packet
    worksheet = list(csv.DictReader((out_dir / "active_verification_pilot_human_audit_worksheet_50.csv").open()))
    assert worksheet[0]["task_id"] == "ert_082"
    assert worksheet[0]["question"]
    assert "trace_source target=doc_007" in worksheet[0]["model_actions"]
    assert "doc_007" in worksheet[0]["documents"]
    assert worksheet[0]["primary_search_needed"] == "1.0"
    assert "eham_" not in json.dumps(worksheet[0], ensure_ascii=False)
    assert "pollutant_root" not in json.dumps(worksheet[0], ensure_ascii=False)
    model_blinded_worksheet = list(csv.DictReader((out_dir / "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv").open()))
    assert model_blinded_worksheet[0]["row_index"] == "1"
    assert model_blinded_worksheet[0]["evidence_condition"] == "clean"
    assert "trace_source target=doc_007" in model_blinded_worksheet[0]["model_actions"]
    assert "model" not in model_blinded_worksheet[0]
    assert "task_id" not in model_blinded_worksheet[0]
    assert "prompt_condition" not in model_blinded_worksheet[0]
    assert "auto_action_gate_pass" not in model_blinded_worksheet[0]
    assert "gpt-5.4" not in json.dumps(model_blinded_worksheet[0], ensure_ascii=False)
    assert "standard_answer" not in json.dumps(model_blinded_worksheet[0], ensure_ascii=False)
    guidelines = (out_dir / "active_verification_human_audit_guidelines.md").read_text(encoding="utf-8")
    assert "Do not sort, delete, duplicate, or reorder rows" in guidelines
    assert "reference-only triage" in guidelines
    assert "`primary_search_needed`" in guidelines
    protocol = (out_dir / "active_verification_human_audit_protocol.md").read_text(encoding="utf-8")
    assert "single-auditor pilot audit" in protocol
    assert "`generated_lore`" in protocol
    assert "not as independent human-validation evidence" in protocol
    review_html = (out_dir / "active_verification_human_audit_review.html").read_text(encoding="utf-8")
    assert "Download strict CSV" in review_html
    assert "Import strict CSV draft" in review_html
    assert "Next incomplete row" in review_html
    assert "trace_source" in review_html
    assert "active_verification_human_audit.csv" in review_html
    assert "validateImportedRows" in review_html
    assert "applyConditionFilter" in review_html
    assert "row count does not match" in review_html
    assert "eham_" not in review_html
    audit_readme = (out_dir / "active_verification_human_audit_readme.md").read_text(encoding="utf-8")
    assert "step1-readiness-check" in audit_readme
    assert "active_verification_human_audit_attestation.md" in audit_readme
    assert "import-active-verification-human-audit-worksheet" in audit_readme
    reviewer_brief = (out_dir / "active_verification_human_audit_reviewer_brief.md").read_text(encoding="utf-8")
    assert "50-row active-verification pilot audit" in reviewer_brief
    assert "Model-blinded worksheet" in reviewer_brief
    assert "Do not copy those labels" in reviewer_brief
    assert "`machine_executable_action`" in reviewer_brief
    assert "`trace_source_needed`" in reviewer_brief
    assert "Blank `auditor_notes` fails validation" in reviewer_brief


def test_summarize_active_verification_human_audit_reports_labeled_rates(tmp_path: Path) -> None:
    labels = tmp_path / "labels.csv"
    labels.write_text(
        "\n".join(
            [
                "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids",
                'human_labeled,m1,t1,clean,standard_answer,1,0,0,1,0,1,0,0,,0,1,0,0,"[]"',
                'human_labeled,m1,t2,generated_lore,standard_answer,0,1,1,1,0,0,1,1,,1,0,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "summary"

    summarize_active_verification_human_audit(labels_csv=labels, out_dir=out_dir)

    rows = list(csv.DictReader((out_dir / "active_verification_pilot_human_audit_summary.csv").open()))
    overall = next(row for row in rows if row["grouping"] == "overall")
    assert overall["n_labeled"] == "2"
    assert float(overall["semantically_useful_action_rate"]) == 0.5
    assert float(overall["machine_executable_action_rate"]) == 0.5
    assert float(overall["primary_search_needed_rate"]) == 0.5
    assert float(overall["trace_source_needed_rate"]) == 0.5
    assert float(overall["scorer_too_strict_rate"]) == 0.5
    paper_update = (out_dir / "active_verification_pilot_human_audit_paper_update.md").read_text(encoding="utf-8")
    assert "human-labeled active-verification audit" in paper_update
    assert "1/2 as semantically useful" in paper_update
    assert "1/2 automatic rejections as plausibly too strict" in paper_update


def test_summarize_active_verification_audit_supports_custom_output_stem(tmp_path: Path) -> None:
    labels = tmp_path / "labels.csv"
    labels.write_text(
        "\n".join(
            [
                "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids",
                'codex_xhigh_labeled,m1,t1,clean,standard_answer,1,1,1,1,0,1,0,0,,1,0,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "summary"

    summarize_active_verification_human_audit(
        labels_csv=labels,
        out_dir=out_dir,
        output_stem="active_verification_pilot_codex_xhigh_audit_summary",
    )

    assert (out_dir / "active_verification_pilot_codex_xhigh_audit_summary.csv").exists()
    payload = json.loads((out_dir / "active_verification_pilot_codex_xhigh_audit_summary.json").read_text(encoding="utf-8"))
    assert payload["status"] == "complete"
    assert payload["summary_csv"] == "active_verification_pilot_codex_xhigh_audit_summary.csv"
    assert payload["paper_update_md"] == "active_verification_pilot_codex_xhigh_audit_paper_update.md"
    codex_update = (out_dir / "active_verification_pilot_codex_xhigh_audit_paper_update.md").read_text(encoding="utf-8")
    assert "not human validation" in codex_update
    assert "single-auditor pilot human audit reports" not in codex_update


def test_validate_active_verification_human_audit_requires_human_labels_and_unchanged_context(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    labels = tmp_path / "labels.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    labels.write_text(
        "\n".join(
            [
                header,
                'human_labeled,m1,t1,clean,standard_answer,1,0,1,1,1,0,1,0,checked,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "validation"

    report = validate_active_verification_human_audit(labels_csv=labels, reference_csv=reference, out_dir=out_dir)

    assert report["status"] == "complete"
    assert report["n_complete_rows"] == 1
    assert set(report["label_fields"]) == {
        "semantically_useful_action",
        "machine_executable_action",
        "exact_target_present",
        "required_action_type_present",
        "contradiction_search_needed",
        "primary_search_needed",
        "trace_source_needed",
        "scorer_too_strict",
    }
    assert (out_dir / "active_verification_pilot_human_audit_validation.json").exists()
    row_report = list(csv.DictReader((out_dir / "active_verification_pilot_human_audit_validation_rows.csv").open()))
    assert row_report[0]["complete"] == "True"


def test_validate_active_verification_human_audit_requires_auditor_notes(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    labels = tmp_path / "labels.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    labels.write_text(
        "\n".join(
            [
                header,
                'human_labeled,m1,t1,clean,standard_answer,1,0,1,1,1,0,1,0,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "validation"

    report = validate_active_verification_human_audit(labels_csv=labels, reference_csv=reference, out_dir=out_dir)

    assert report["status"] == "incomplete"
    assert report["n_complete_rows"] == 0
    row_report = list(csv.DictReader((out_dir / "active_verification_pilot_human_audit_validation_rows.csv").open()))
    assert "auditor_notes is blank" in row_report[0]["errors"]


def test_import_active_verification_human_audit_worksheet_preserves_strict_csv_shape(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    worksheet = tmp_path / "worksheet.csv"
    imported = tmp_path / "imported.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    worksheet.write_text(
        "\n".join(
            [
                header + ",question,documents",
                'human_labeled,m1,t1,clean,standard_answer,1,0,1,1,0,1,0,0,checked,1,0,0,0,"[]",Does this action work?,doc_001 primary',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = import_active_verification_human_audit_worksheet(worksheet_csv=worksheet, reference_csv=reference, out_csv=imported)

    assert manifest["status"] == "imported"
    imported_rows = list(csv.DictReader(imported.open()))
    assert list(imported_rows[0].keys()) == header.split(",")
    assert imported_rows[0]["audit_status"] == "human_labeled"
    assert imported_rows[0]["auto_action_gate_pass"] == "0"
    assert "question" not in imported_rows[0]
    report = validate_active_verification_human_audit(labels_csv=imported, reference_csv=reference, out_dir=tmp_path / "validation")
    assert report["status"] == "complete"


def test_import_active_verification_human_audit_worksheet_rejects_changed_row_order(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    worksheet = tmp_path / "worksheet.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    worksheet.write_text(
        "\n".join(
            [
                header,
                'human_labeled,m1,t2,clean,standard_answer,1,0,1,1,0,1,0,0,checked,1,0,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        import_active_verification_human_audit_worksheet(
            worksheet_csv=worksheet,
            reference_csv=reference,
            out_csv=tmp_path / "imported.csv",
        )
    except ValueError as exc:
        assert "row 1 key changed or row order mismatch" in str(exc)
    else:
        raise AssertionError("expected changed worksheet row key to be rejected")


def test_import_model_blinded_human_audit_worksheet_preserves_strict_csv_shape(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    worksheet = tmp_path / "model_blinded_worksheet.csv"
    imported = tmp_path / "imported.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    worksheet.write_text(
        "\n".join(
            [
                "row_index,audit_status,evidence_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,question,model_actions,documents",
                '1,human_labeled,clean,1,0,1,1,0,1,0,0,checked,Does this action work?,trace_source target=doc_001,doc_001 primary',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = import_active_verification_model_blinded_human_audit_worksheet(
        worksheet_csv=worksheet,
        reference_csv=reference,
        out_csv=imported,
    )

    assert manifest["status"] == "imported"
    imported_rows = list(csv.DictReader(imported.open()))
    assert list(imported_rows[0].keys()) == header.split(",")
    assert imported_rows[0]["audit_status"] == "human_labeled"
    assert imported_rows[0]["model"] == "m1"
    assert imported_rows[0]["task_id"] == "t1"
    assert imported_rows[0]["auto_action_gate_pass"] == "0"
    assert "question" not in imported_rows[0]
    report = validate_active_verification_human_audit(labels_csv=imported, reference_csv=reference, out_dir=tmp_path / "validation")
    assert report["status"] == "complete"


def test_import_model_blinded_human_audit_worksheet_rejects_row_index_mismatch(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    worksheet = tmp_path / "model_blinded_worksheet.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    worksheet.write_text(
        "\n".join(
            [
                "row_index,audit_status,evidence_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes",
                "2,human_labeled,clean,1,0,1,1,0,1,0,0,checked",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    try:
        import_active_verification_model_blinded_human_audit_worksheet(
            worksheet_csv=worksheet,
            reference_csv=reference,
            out_csv=tmp_path / "imported.csv",
        )
    except ValueError as exc:
        assert "row 1 row_index mismatch" in str(exc)
    else:
        raise AssertionError("expected changed row_index to be rejected")


def test_validate_active_verification_human_audit_rejects_codex_or_changed_rows(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    labels = tmp_path / "labels.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    labels.write_text(
        "\n".join(
            [
                header,
                'codex_xhigh_labeled,m1,t1,generated_lore,standard_answer,1,1,1,1,0,1,0,0,checked,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "validation"

    report = validate_active_verification_human_audit(labels_csv=labels, reference_csv=reference, out_dir=out_dir)

    assert report["status"] == "incomplete"
    assert any("failed validation" in error for error in report["errors"])
    row_report = list(csv.DictReader((out_dir / "active_verification_pilot_human_audit_validation_rows.csv").open()))
    assert "row key changed or row order mismatch" in row_report[0]["errors"]
    assert "audit_status is not human_labeled" in row_report[0]["errors"]
    assert "non-label field changed: condition" in row_report[0]["errors"]


def test_finalize_active_verification_human_audit_imports_valid_labels_and_writes_summary(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    labels = tmp_path / "labels.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    labels.write_text(
        "\n".join(
            [
                header,
                'human_labeled,m1,t1,clean,standard_answer,1,0,1,1,0,1,0,0,checked,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "final"

    manifest = finalize_active_verification_human_audit(labels_csv=labels, reference_csv=reference, out_dir=out_dir)

    assert manifest["status"] == "complete"
    assert manifest["imported_labels_csv"] == "active_verification_pilot_human_audit_labeled_50.csv"
    assert (out_dir / "active_verification_pilot_human_audit_labeled_50.csv").read_text(encoding="utf-8") == labels.read_text(encoding="utf-8")
    summary = json.loads((out_dir / "active_verification_pilot_human_audit_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "complete"
    assert summary["n_labeled"] == 1
    assert manifest["paper_update_md"] == "active_verification_pilot_human_audit_paper_update.md"
    paper_update = (out_dir / "active_verification_pilot_human_audit_paper_update.md").read_text(encoding="utf-8")
    assert "single-auditor pilot human audit" in paper_update
    assert "human-labeled active-verification audit" in paper_update
    assert "1/1 as semantically useful" in paper_update
    assert "0/1 automatic rejections as plausibly too strict" in paper_update


def test_finalize_active_verification_human_audit_does_not_import_invalid_labels(tmp_path: Path) -> None:
    reference = tmp_path / "reference.csv"
    labels = tmp_path / "labels.csv"
    header = "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    reference.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    labels.write_text(
        "\n".join(
            [
                header,
                'needs_human_label,m1,t1,clean,standard_answer,,,,,0,1,0,,,0,1,0,0,"[]"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    out_dir = tmp_path / "final"

    try:
        finalize_active_verification_human_audit(labels_csv=labels, reference_csv=reference, out_dir=out_dir)
    except ValueError:
        pass
    else:
        raise AssertionError("expected invalid labels to be rejected")

    assert not (out_dir / "active_verification_pilot_human_audit_labeled_50.csv").exists()
    validation = json.loads((out_dir / "active_verification_pilot_human_audit_validation.json").read_text(encoding="utf-8"))
    assert validation["status"] == "incomplete"


def write_fake_readiness_artifact(
    artifact_dir: Path,
    *,
    validation_status: str = "complete",
    n_complete_rows: int = 50,
    include_all_human_audit_conditions: bool = True,
) -> None:
    required_text_files = [
        "README.md",
        "prompts/standard_answer.txt",
        "prompts/epistemic_hygiene_instruction.txt",
        "scorer/scoring_contract.py",
        "scorer/README.md",
        "reproduce_minimal.sh",
        "serve_human_audit_review.sh",
        "finalize_human_audit.sh",
        "verify_step1_release.sh",
    ]
    for relative in required_text_files:
        path = artifact_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("release artifact\n", encoding="utf-8")
    (artifact_dir / "README.md").write_text(
        "controlled diagnostic package\n"
        "step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports\n"
        "not human validation\n"
        "audit_status = human_labeled\n"
        "n_labeled = 50\n"
        "auditor_notes\n"
        "legal, medical, financial\n",
        encoding="utf-8",
    )
    (artifact_dir / "scorer" / "scoring_contract.py").write_text(
        "\n".join(
            [
                "import json, sys",
                "from pathlib import Path",
                "task = json.loads(Path(sys.argv[1]).read_text())",
                "output = json.loads(Path(sys.argv[2]).read_text())",
                "gold = task['gold']",
                "support = set(output.get('supporting_evidence', []))",
                "pollutants = set(gold.get('contaminant_doc_ids', [])) | set(gold.get('generated_doc_ids', [])) | set(gold.get('stale_doc_ids', []))",
                "belief = output.get('claim_verdict') == gold.get('gold_verdict')",
                "clean = not bool(support & pollutants)",
                "uncertainty = output.get('claim_verdict') == 'insufficient' if gold.get('gold_verdict') == 'insufficient' else output.get('claim_verdict') != 'insufficient'",
                "print(json.dumps({'belief_correctness': float(belief), 'evidence_cleanliness': float(clean), 'uncertainty_discipline': float(uncertainty), 'operational_epistemic_escape': float(belief and clean and uncertainty)}))",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    for relative in [
        "data/tasks_opaque.jsonl",
        "data/documents_opaque.jsonl",
        "data/gold_labels.jsonl",
        "examples/minimal_task.json",
        "examples/minimal_model_output.json",
        "examples/minimal_score.json",
    ]:
        path = artifact_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"ok": true}\n', encoding="utf-8")
    predictions_path = artifact_dir / "outputs" / "frontier_main_opaque_predictions.jsonl"
    predictions_path.parent.mkdir(parents=True, exist_ok=True)
    predictions_path.write_text(
        json.dumps(
            {
                "task_id": "ert_000",
                "model": "gpt-5.4",
                "invocation_profile": {
                    "doc_id_policy": "opaque_per_task",
                    "visible_prompt_audit": {
                        "semantic_doc_id_hits": 0,
                        "semantic_visible_citation_hits": 0,
                        "audit_id_hits_in_title_or_body": 0,
                    },
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "examples" / "minimal_task.json").write_text(
        json.dumps({"gold": {"gold_verdict": "supported", "contaminant_doc_ids": [], "generated_doc_ids": [], "stale_doc_ids": []}}) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "examples" / "minimal_model_output.json").write_text(
        json.dumps({"claim_verdict": "supported", "supporting_evidence": []}) + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "examples" / "minimal_score.json").write_text(
        json.dumps(
            {
                "belief_correctness": 1.0,
                "evidence_cleanliness": 1.0,
                "uncertainty_discipline": 1.0,
                "operational_epistemic_escape": 1.0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    frontier_models = ["gpt-5.4", "claude-opus-4-7", "gemini-3.1-pro-preview", "deepseek-v4-pro", "kimi-k2.6"]
    frontier_families = ["packet_judgment", "evidence_selection", "active_verification", "packet_judgment", "evidence_selection"] * 2
    frontier_conditions = ["clean", "conflicting_evidence", "false_consensus", "buried_primary", "generated_lore"] * 2
    frontier_prompts = ["standard_answer", "epistemic_hygiene_instruction"] * 5
    prediction_payload = {
        "task_id": "ert_000",
        "model": "gpt-5.4",
        "invocation_profile": {
            "doc_id_policy": "opaque_per_task",
            "visible_prompt_audit": {
                "semantic_doc_id_hits": 0,
                "semantic_visible_citation_hits": 0,
                "audit_id_hits_in_title_or_body": 0,
            },
        },
    }
    scored_rows = [
        "task_id,model,family,condition,prompt_condition,operational_epistemic_escape,belief_correctness,evidence_cleanliness,verification_action_score"
    ]
    prediction_lines = []
    for model in frontier_models:
        for index in range(10):
            task_id = f"ert_{index:03d}"
            scored_rows.append(
                f"{task_id},{model},{frontier_families[index]},{frontier_conditions[index]},{frontier_prompts[index]},1.0,1.0,1.0,1.0"
            )
            payload = dict(prediction_payload)
            payload["task_id"] = task_id
            payload["model"] = model
            prediction_lines.append(json.dumps(payload))
    predictions_path.write_text("\n".join(prediction_lines) + "\n", encoding="utf-8")
    scored_path = artifact_dir / "outputs" / "frontier_main_opaque_scored.csv"
    scored_path.write_text("\n".join(scored_rows) + "\n", encoding="utf-8")
    run_manifest_path = artifact_dir / "outputs" / "frontier_main_opaque_run_manifest.json"
    run_manifest_path.write_text(
        json.dumps(
            {
                "task_count": 100,
                "model_count": 5,
                "job_count": 50,
                "model_visible_doc_id_policy": "opaque_per_task",
                "prompt_conditions": ["standard_answer", "epistemic_hygiene_instruction"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report_manifest_path = artifact_dir / "outputs" / "frontier_main_opaque_report_manifest.json"
    report_manifest_path.write_text(
        json.dumps(
            {
                "record_count": 50,
                "task_count": 100,
                "model_count": 5,
                "prompt_conditions": ["standard_answer", "epistemic_hygiene_instruction"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    baseline_dir = artifact_dir / "baselines"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    baseline_values = {
        "id_only": ("0.080", "0.200", "1.000", "0.200", "0.000", "1.000"),
        "metadata_only": ("0.400", "0.400", "1.000", "0.960", "0.067", "0.240"),
        "simple_heuristic": ("0.560", "0.600", "1.000", "0.960", "0.000", "0.240"),
        "random_valid_schema": ("0.080", "0.355", "0.530", "0.630", "0.068", "0.295"),
        "always_insufficient": ("0.080", "0.200", "1.000", "0.200", "0.000", "1.000"),
    }
    baseline_header = (
        "model,operational_epistemic_escape,belief_correctness,evidence_cleanliness,"
        "uncertainty_discipline,verification_action_score,support_empty_rate\n"
    )
    for baseline, values in baseline_values.items():
        (baseline_dir / f"{baseline}.csv").write_text(
            baseline_header + f"{baseline}_baseline,{','.join(values)}\n",
            encoding="utf-8",
        )
    audit_dir = artifact_dir / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "opaque_prompt_audit_summary.json").write_text('{"semantic_id_hits": 0}\n', encoding="utf-8")
    (audit_dir / "active_verification_action_audit_summary.csv").write_text(
        "\n".join(
            [
                "grouping,model,prompt_condition,condition,n,action_gate_pass,missing_primary_action,missing_contradiction_action,missing_trace_source_action",
                "model,claude-opus-4-7,,,40,0.700,0.075,0.200,0.025",
                "model,gpt-5.4,,,40,0.725,0.225,0.200,0.000",
                "model,deepseek-v4-pro,,,40,0.575,0.150,0.275,0.000",
                "model,gemini-3.1-pro-preview,,,40,0.425,0.125,0.450,0.025",
                "model,kimi-k2.6,,,40,0.375,0.150,0.425,0.050",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (audit_dir / "generated_lore_schema_ablation.csv").write_text(
        "\n".join(
            [
                "schema_variant,model,n,prompt_condition,belief_correctness",
                "current_schema,gpt-5.4,20,standard_answer,1",
                "current_schema,claude-opus-4-7,20,standard_answer,1",
                "current_schema,gemini-3.1-pro-preview,20,standard_answer,1",
                "minimal_schema,gpt-5.4,20,standard_answer,1",
                "minimal_schema,claude-opus-4-7,20,standard_answer,1",
                "minimal_schema,gemini-3.1-pro-preview,20,standard_answer,1",
                "diagnostic_schema_no_hygiene,gpt-5.4,20,standard_answer,1",
                "diagnostic_schema_no_hygiene,claude-opus-4-7,20,standard_answer,1",
                "diagnostic_schema_no_hygiene,gemini-3.1-pro-preview,20,standard_answer,1",
                "clarified_schema,gpt-5.4,20,standard_answer,1",
                "clarified_schema,claude-opus-4-7,20,standard_answer,1",
                "clarified_schema,gemini-3.1-pro-preview,20,standard_answer,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    schema_detail_rows = ["schema_variant,model,task_id,prompt_condition,condition,polluted_supporting_ids"]
    for variant in ["current_schema", "minimal_schema", "diagnostic_schema_no_hygiene", "clarified_schema"]:
        for model in ["gpt-5.4", "claude-opus-4-7", "gemini-3.1-pro-preview"]:
            for index in range(20):
                schema_detail_rows.append(f"{variant},{model},ert_{index:03d},standard_answer,generated_lore,doc_001")
    (audit_dir / "generated_lore_schema_ablation_rows.csv").write_text("\n".join(schema_detail_rows) + "\n", encoding="utf-8")
    conditions = ["clean", "generated_lore", "false_consensus", "buried_primary", "conflicting_evidence"]
    if not include_all_human_audit_conditions:
        conditions = ["clean", "false_consensus", "buried_primary", "conflicting_evidence"]
    audit_header = (
        "audit_status,model,task_id,condition,prompt_condition,"
        "semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,"
        "contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,"
        "auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    )
    audit_rows = [audit_header]
    for index in range(50):
        condition = conditions[index % len(conditions)]
        audit_rows.append(
            ",".join(
                [
                    "human_labeled",
                    "m1",
                    f"t{index:02d}",
                    condition,
                    "standard_answer",
                    "1",
                    "1" if index < 47 else "0",
                    "1" if index < 47 else "0",
                    "1" if index < 37 else "0",
                    "0",
                    "1",
                    "0",
                    "1" if index < 2 else "0",
                    "checked",
                    "1",
                    "0",
                    "0",
                    "0",
                    "\"[]\"",
                ]
            )
        )
    human_audit_csv = audit_dir / "active_verification_human_audit.csv"
    human_audit_csv.write_text("\n".join(audit_rows) + "\n", encoding="utf-8")
    worksheet_rows = [
        (
            "row_index,audit_status,model,task_id,condition,prompt_condition,"
            "semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,"
            "contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,"
            "question,model_actions,documents"
        )
    ]
    for index in range(50):
        condition = conditions[index % len(conditions)]
        worksheet_rows.append(
            f"{index + 1},human_labeled,m1,t{index:02d},{condition},standard_answer,1,1,1,1,0,1,0,0,checked,question,trace_source target=doc_001,doc_001 primary"
        )
    (audit_dir / "active_verification_pilot_human_audit_worksheet_50.csv").write_text("\n".join(worksheet_rows) + "\n", encoding="utf-8")
    model_blinded_worksheet_rows = [
        (
            "row_index,audit_status,evidence_condition,"
            "semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,"
            "contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,"
            "question,model_actions,documents"
        )
    ]
    for index in range(50):
        condition = conditions[index % len(conditions)]
        model_blinded_worksheet_rows.append(
            f"{index + 1},human_labeled,{condition},1,1,1,1,0,1,0,0,checked,question,trace_source target=doc_001,doc_001 primary"
        )
    (audit_dir / "active_verification_pilot_human_audit_model_blinded_worksheet_50.csv").write_text(
        "\n".join(model_blinded_worksheet_rows) + "\n",
        encoding="utf-8",
    )
    codex_rows = [
        "audit_status,model,task_id,condition,prompt_condition,semantically_useful_action,machine_executable_action,exact_target_present,required_action_type_present,contradiction_search_needed,primary_search_needed,trace_source_needed,scorer_too_strict,auditor_notes,auto_action_gate_pass,auto_missing_primary_action,auto_missing_contradiction_action,auto_missing_trace_source_action,auto_actions_visible_ids"
    ]
    for index in range(50):
        codex_rows.append(
            ",".join(
                [
                    "codex_xhigh_labeled",
                    "m1",
                    f"t{index:02d}",
                    "clean",
                    "standard_answer",
                    "1",
                    "1" if index < 47 else "0",
                    "1" if index < 47 else "0",
                    "1" if index < 37 else "0",
                    "0",
                    "1",
                    "0",
                    "1" if index < 2 else "0",
                    "checked",
                    "1",
                    "0",
                    "0",
                    "0",
                    "\"[]\"",
                ]
            )
        )
    (audit_dir / "active_verification_pilot_codex_xhigh_audit_50.csv").write_text("\n".join(codex_rows) + "\n", encoding="utf-8")
    (audit_dir / "active_verification_human_audit_manifest.json").write_text(
        json.dumps(
            {
                "label_status": "complete",
                "context_rows": 50,
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
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (audit_dir / "active_verification_human_audit_readme.md").write_text("human audit readme\n", encoding="utf-8")
    (audit_dir / "active_verification_human_audit_reviewer_brief.md").write_text(
        "\n".join(
            [
                "# Human-Audit Reviewer Brief",
                "Use this brief when you are the independent reviewer for the 50-row active-verification pilot audit.",
                "Set `audit_status = human_labeled` and fill all eight labels.",
                "`semantically_useful_action`",
                "`machine_executable_action`",
                "`trace_source_needed`",
                "`scorer_too_strict`",
                "Blank `auditor_notes` fails validation.",
                "`active_verification_pilot_codex_xhigh_audit_50.csv` is reference-only triage.",
                "Do not copy those labels into the human sheet unless you independently reviewed the row.",
                "Complete `active_verification_human_audit_attestation.md`.",
                "./finalize_human_audit.sh --from-model-blinded-worksheet",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (audit_dir / "active_verification_human_audit_protocol.md").write_text(
        "\n".join(
            [
                "single-auditor pilot audit",
                "stratified across five evidence conditions with 10 rows per condition",
                "all eight binary label fields",
                "audit_status` to `human_labeled",
                "Codex-assisted labels are triage evidence only",
                "does not create human-validation evidence by itself",
                "Model identities, prompt conditions, and automatic scorer outcomes are intentionally omitted",
                "active_verification_human_audit_attestation.md",
                "n_complete_rows = 50",
                "no blank `auditor_notes` rows",
                "n_labeled = 50",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if validation_status == "complete" and n_complete_rows >= 50:
        attestation_text = "\n".join(
            [
                "# Active-Verification Human-Audit Attestation",
                "",
                "auditor_identifier: test-auditor",
                "date_completed: 2026-05-16",
                "audit_surface_used: model_blinded_worksheet",
                "independent_human_review_completed: yes",
                "codex_triage_not_copied_as_human_labels: yes",
                "all_50_rows_reviewed: yes",
                "all_eight_binary_fields_and_auditor_notes_completed: yes",
                "",
                "The independent human review covered all 50 rows.",
                "Codex-assisted audit was not copied as human labels.",
                "All eight binary label fields and auditor_notes were completed.",
            ]
        )
    else:
        attestation_text = "\n".join(
            [
                "# Active-Verification Human-Audit Attestation",
                "",
                "auditor_identifier: [TO BE COMPLETED]",
                "date_completed: [TO BE COMPLETED]",
                "audit_surface_used: [TO BE COMPLETED: strict_csv | wide_worksheet | model_blinded_worksheet | html_review]",
                "independent_human_review_completed: [TO BE COMPLETED: yes]",
                "codex_triage_not_copied_as_human_labels: [TO BE COMPLETED: yes]",
                "all_50_rows_reviewed: [TO BE COMPLETED: yes]",
                "all_eight_binary_fields_and_auditor_notes_completed: [TO BE COMPLETED: yes]",
                "",
                "The independent human review covered all 50 rows.",
                "Codex-assisted audit was not copied as human labels.",
                "All eight binary label fields and auditor_notes were completed.",
            ]
        )
    (audit_dir / "active_verification_human_audit_attestation.md").write_text(attestation_text + "\n", encoding="utf-8")
    (audit_dir / "active_verification_pilot_human_audit_packet_50.md").write_text(
        "# Active-Verification Pilot Human-Audit Packet\n## Row 01: t00 / m1 / clean / standard_answer\n",
        encoding="utf-8",
    )
    model_blinded_lines = [
        "# Active-Verification Pilot Model-Blinded Human-Audit Packet",
        "Model identities and prompt conditions are intentionally omitted",
        "Auto scorer outcomes are intentionally omitted",
        "Use row order to transfer labels to `active_verification_human_audit.csv` or the wide worksheet.",
    ]
    for index in range(50):
        model_blinded_lines.extend([f"## Row {index + 1:02d}", "Evidence condition: clean", "Proposed actions:", "- `trace_source` target=`doc_001`"])
    (audit_dir / "active_verification_pilot_human_audit_model_blinded_packet_50.md").write_text(
        "\n".join(model_blinded_lines) + "\n",
        encoding="utf-8",
    )
    (audit_dir / "active_verification_human_audit_review.html").write_text(
        "<!doctype html><button>Download strict CSV</button><button>Import strict CSV draft</button><select id='condition-filter'></select><button>Next incomplete row</button><script>const referenceRows=[]; function validateImportedRows(){}; function applyConditionFilter(){}; download.disabled=false; const status='human_labeled';</script>active_verification_human_audit.csv\n",
        encoding="utf-8",
    )
    (artifact_dir / "serve_human_audit_review.sh").write_text(
        '#!/usr/bin/env bash\ncd "$(dirname "$0")"\npython3 -m http.server "${1:-8765}" --bind 127.0.0.1\n# active_verification_human_audit_review.html\n',
        encoding="utf-8",
    )
    (artifact_dir / "serve_human_audit_review.sh").chmod(0o755)
    (artifact_dir / "finalize_human_audit.sh").write_text(
        '#!/usr/bin/env bash\ncd "$(dirname "$0")"\n# --from-worksheet\n# --from-model-blinded-worksheet\nattestation_md="${artifact_dir}/audits/active_verification_human_audit_attestation.md"\nuv run eha-step1-release import-active-verification-human-audit-worksheet\nuv run eha-step1-release import-active-verification-model-blinded-human-audit-worksheet\nuv run eha-step1-release finalize-active-verification-human-audit\ncp "$attestation_md" active_verification_human_audit_attestation.md\nuv run eha-step1-release artifact-package\nuv run eha-step1-release step1-readiness-check\necho "Step 1 readiness status:"\necho "Failing gates:"\n',
        encoding="utf-8",
    )
    (artifact_dir / "finalize_human_audit.sh").chmod(0o755)
    (artifact_dir / "verify_step1_release.sh").write_text(
        '#!/usr/bin/env bash\ncd "$(dirname "$0")"\n# --allow-blocked\n./reproduce_minimal.sh\nuv run pytest\nmake\nuv run eha-step1-release step1-readiness-check --out-dir ../reports\npython3 -c "print(\'eha_step1_readiness_check.json\')"\ngit diff --check\n',
        encoding="utf-8",
    )
    (artifact_dir / "verify_step1_release.sh").chmod(0o755)
    (audit_dir / "active_verification_pilot_human_audit_validation.json").write_text(
        json.dumps(
            {
                "status": validation_status,
                "n_rows": 50,
                "reference_rows": 50,
                "n_complete_rows": n_complete_rows,
                "labels_sha256": file_sha256(human_audit_csv),
                "reference_sha256": file_sha256(human_audit_csv),
                "errors": [] if validation_status == "complete" else ["50 row(s) failed validation"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (audit_dir / "active_verification_pilot_human_audit_summary.csv").write_text(
        "\n".join(
            [
                (
                    "grouping,group,n_rows,n_labeled,semantically_useful_action_rate,"
                    "machine_executable_action_rate,exact_target_present_rate,required_action_type_present_rate,"
                    "contradiction_search_needed_rate,primary_search_needed_rate,trace_source_needed_rate,scorer_too_strict_rate"
                ),
                (
                    "overall,all,50,"
                    f"{n_complete_rows},1.0,0.94,0.94,0.74,0.0,1.0,0.0,0.04"
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (audit_dir / "active_verification_pilot_human_audit_summary.json").write_text(
        json.dumps(
            {
                "labels_csv": "active_verification_human_audit.csv",
                "n_rows": 50,
                "n_labeled": n_complete_rows,
                "status": "complete" if validation_status == "complete" else "incomplete",
                "summary_csv": "active_verification_pilot_human_audit_summary.csv",
                "paper_update_md": "active_verification_pilot_human_audit_paper_update.md",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (audit_dir / "active_verification_pilot_human_audit_paper_update.md").write_text(
        (
            "\n".join(
                [
                    "# Active-Verification Human-Audit Paper Update",
                    "",
                    f"- status: `{'complete' if validation_status == 'complete' else 'incomplete'}`",
                    f"- n_labeled: {n_complete_rows}",
                    "",
                    "A single-auditor pilot human audit reports the human-labeled active-verification audit separately from Codex-assisted triage: 50/50 as semantically useful, 47/50 as machine executable, 37/50 as containing the required action type, and 2/50 automatic rejections as plausibly too strict.",
                ]
            )
            if validation_status == "complete"
            else "\n".join(
                [
                    "# Active-Verification Human-Audit Paper Update",
                    "",
                    "- status: `incomplete`",
                    f"- n_labeled: {n_complete_rows}",
                    "",
                    "Do not use this memo to make completed human-audit claims yet.",
                    "",
                    "The current human audit is incomplete or not fully marked `human_labeled`, and is not human validation.",
                ]
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (artifact_dir / "manifest.json").write_text(
        json.dumps(
            {
                "task_count": 100,
                "opaque_task_count": 100,
                "frontier_outputs_present": True,
                "frontier_main_outputs": {
                    "source_kind": "opaque_run",
                    "source_dir": "results/reports-eha-frontier-main-opaque-2026-05-15",
                    "source_run_manifest": "run_manifest.json",
                    "source_report_manifest": "report_manifest.json",
                    "run_manifest_file": "outputs/frontier_main_opaque_run_manifest.json",
                    "report_manifest_file": "outputs/frontier_main_opaque_report_manifest.json",
                    "model_visible_doc_id_policy": "opaque_per_task",
                    "source_task_count": 100,
                    "source_record_count": 50,
                    "source_model_count": 5,
                    "source_prompt_conditions": ["standard_answer", "epistemic_hygiene_instruction"],
                    "predictions_file": "outputs/frontier_main_opaque_predictions.jsonl",
                    "scored_file": "outputs/frontier_main_opaque_scored.csv",
                    "predictions_sha256": file_sha256(predictions_path),
                    "scored_sha256": file_sha256(scored_path),
                    "run_manifest_sha256": file_sha256(run_manifest_path),
                    "report_manifest_sha256": file_sha256(report_manifest_path),
                },
                "baseline_files": [
                    "id_only.csv",
                    "metadata_only.csv",
                    "simple_heuristic.csv",
                    "random_valid_schema.csv",
                    "always_insufficient.csv",
                ],
                "active_verification_human_audit": {
                    "status": "complete" if validation_status == "complete" else "incomplete",
                    "n_rows": 50,
                    "n_labeled": n_complete_rows,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)


def write_fake_readiness_paper(paper_dir: Path, *, include_required_phrases: bool = True) -> None:
    required_files = [
        "main.tex",
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
    ]
    for relative in required_files:
        path = paper_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("paper source\n", encoding="utf-8")
    (paper_dir / "tables" / "opaque_baselines.tex").write_text(
        "\n".join(
            [
                r"\begin{table}[t]",
                r"ID-only & 0.080 & 0.200 & 1.000 & 0.200 & 0.000 & 1.000 \\",
                r"Random valid schema & 0.080 & 0.355 & 0.530 & 0.630 & 0.068 & 0.295 \\",
                r"Always insufficient & 0.080 & 0.200 & 1.000 & 0.200 & 0.000 & 1.000 \\",
                r"Metadata-only & 0.400 & 0.400 & 1.000 & 0.960 & 0.067 & 0.240 \\",
                r"Simple heuristic & 0.560 & 0.600 & 1.000 & 0.960 & 0.000 & 0.240 \\",
                r"\end{table}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    frontier_models = ["gpt-5.4", "claude-opus-4-7", "gemini-3.1-pro-preview", "deepseek-v4-pro", "kimi-k2.6"]
    (paper_dir / "tables" / "main_model_decomposition.tex").write_text(
        "\n".join([rf"\code{{{model}}} & 10 & 1.000 & [0.722, 1.000] & 1.000 & 1.000 & 1.000 \\" for model in frontier_models])
        + "\n",
        encoding="utf-8",
    )
    (paper_dir / "tables" / "task_family_breakdown.tex").write_text(
        "\n".join([rf"\code{{{model}}} & 1.000 & 1.000 & 1.000 \\" for model in frontier_models]) + "\n",
        encoding="utf-8",
    )
    (paper_dir / "tables" / "evidence_condition_breakdown.tex").write_text(
        "\n".join([rf"\code{{{model}}} & 1.000 & 1.000 & 1.000 & 1.000 & 1.000 \\" for model in frontier_models]) + "\n",
        encoding="utf-8",
    )
    (paper_dir / "tables" / "prompt_hygiene.tex").write_text(
        "\n".join([rf"\code{{{model}}} & 1.000 & 1.000 & No change \\" for model in frontier_models]) + "\n",
        encoding="utf-8",
    )
    (paper_dir / "main.pdf").write_text("fake pdf placeholder\n", encoding="utf-8")
    max_source_mtime = max((paper_dir / relative).stat().st_mtime for relative in required_files)
    os.utime(paper_dir / "main.pdf", (max_source_mtime + 1, max_source_mtime + 1))
    if include_required_phrases:
        (paper_dir / "sections" / "01_intro.tex").write_text(
            "controlled diagnostic benchmark; not as a universal provider leaderboard\n",
            encoding="utf-8",
        )
        (paper_dir / "sections" / "09_limitations.tex").write_text(
            "not to certify deployment safety\n"
            "metadata-only and simple heuristic baselines reach 0.400 and 0.560 operational escape\n",
            encoding="utf-8",
        )
        (paper_dir / "sections" / "08_discussion.tex").write_text(
            "The present contribution is therefore best read as a diagnostic release, not a completed scalable benchmark. "
            "A larger benchmark claim would require substantially more tasks, surface-cue stress tests, broader schema ablations, "
            "and independent human audit of active-verification judgments.\n",
            encoding="utf-8",
        )
        (paper_dir / "appendix" / "e_artifacts.tex").write_text(
            "artifact/serve_human_audit_review.sh\n"
            "artifact/finalize_human_audit.sh\n"
            "artifact/verify_step1_release.sh\n"
            "model-blinded\n"
            "model-blinded worksheet\n"
            "reviewer brief\n"
            "human-audit attestation\n"
            "paper-update memo\n"
            "--from-worksheet\n"
            "paper-aware readiness check\n"
            "not counted as human validation\n",
            encoding="utf-8",
        )
        (paper_dir / "sections" / "06_active_verification_case.tex").write_text(
            "\n".join(
                [
                    r"\code{claude-opus-4-7} & 40 & 0.700 & 0.075 & 0.200 \\",
                    r"\code{gpt-5.4} & 40 & 0.725 & 0.225 & 0.200 \\",
                    r"\code{deepseek-v4-pro} & 40 & 0.575 & 0.150 & 0.275 \\",
                    r"\code{gemini-3.1-pro-preview} & 40 & 0.425 & 0.125 & 0.450 \\",
                    r"\code{kimi-k2.6} & 40 & 0.375 & 0.150 & 0.425 \\",
                    "Action-gate pass rates range from 0.375 to 0.725 across models.",
                    "This audit is not treated as human validation. It labels all 50 sampled action sets as semantically useful, "
                    "47/50 as machine executable under the strict target rule, 37/50 as containing the required action type, "
                    "and 2/50 automatic rejections as plausibly too strict.",
                    "A single-auditor pilot human audit should be reported separately once finalized. The human-labeled active-verification audit "
                    "labels 50/50 as semantically useful, 47/50 as machine executable, 37/50 as containing the required action type, "
                    "and 2/50 automatic rejections as plausibly too strict.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (paper_dir / "appendix" / "d_extra_tables.tex").write_text(
            "\n".join(
                [
                    r"\code{claude-opus-4-7} & 40 & 0.700 & 0.075 & 0.200 & 0.025 \\",
                    r"\code{gpt-5.4} & 40 & 0.725 & 0.225 & 0.200 & 0.000 \\",
                    r"\code{deepseek-v4-pro} & 40 & 0.575 & 0.150 & 0.275 & 0.000 \\",
                    r"\code{gemini-3.1-pro-preview} & 40 & 0.425 & 0.125 & 0.450 & 0.025 \\",
                    r"\code{kimi-k2.6} & 40 & 0.375 & 0.150 & 0.425 & 0.050 \\",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        max_source_mtime = max((paper_dir / relative).stat().st_mtime for relative in required_files)
        os.utime(paper_dir / "main.pdf", (max_source_mtime + 1, max_source_mtime + 1))


def test_step1_readiness_check_blocks_when_human_audit_is_incomplete(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir, validation_status="incomplete", n_complete_rows=0)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    human_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit")
    assert human_gate["status"] == "fail"
    assert "human audit validation is not complete" in human_gate["errors"][0]
    assert (report_dir / "eha_step1_readiness_check.json").exists()
    assert (report_dir / "eha_step1_readiness_check.md").exists()


def test_step1_readiness_check_validates_human_audit_worksheet_import_path(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    worksheet_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_worksheet")
    assert worksheet_gate["status"] == "pass"
    assert "worksheet_rows=50" in worksheet_gate["evidence"]
    assert "importable_to_strict_csv=True" in worksheet_gate["evidence"]


def test_step1_readiness_check_blocks_when_human_audit_worksheet_row_order_changes(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    worksheet_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_worksheet_50.csv"
    rows = list(csv.DictReader(worksheet_path.open()))
    rows[0]["task_id"] = "t99"
    with worksheet_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    worksheet_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_worksheet")
    assert worksheet_gate["status"] == "fail"
    assert any("worksheet row 1 key mismatch" in error for error in worksheet_gate["errors"])
    assert any("worksheet import failed" in error for error in worksheet_gate["errors"])


def test_step1_readiness_check_blocks_when_human_audit_protocol_lacks_claim_boundary(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    protocol_path = artifact_dir / "audits" / "active_verification_human_audit_protocol.md"
    protocol_path.write_text("Protocol exists but lacks the Step 1 audit contract.\n", encoding="utf-8")
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    protocol_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_protocol")
    assert protocol_gate["status"] == "fail"
    assert "missing human-audit protocol phrase: sample stratification" in protocol_gate["errors"]
    assert "missing human-audit protocol phrase: not human validation by itself" in protocol_gate["errors"]


def test_step1_readiness_check_allows_attestation_template_before_human_labels_complete(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir, validation_status="incomplete", n_complete_rows=0)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    attestation_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_attestation")
    human_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit")
    assert report["status"] == "blocked"
    assert human_gate["status"] == "fail"
    assert attestation_gate["status"] == "pass"
    assert "attestation_template_present=True" in attestation_gate["evidence"]


def test_step1_readiness_check_blocks_when_completed_human_audit_lacks_attestation(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "audits" / "active_verification_human_audit_attestation.md").write_text(
        "\n".join(
            [
                "# Active-Verification Human-Audit Attestation",
                "",
                "auditor_identifier: [TO BE COMPLETED]",
                "date_completed: [TO BE COMPLETED]",
                "audit_surface_used: [TO BE COMPLETED: strict_csv | wide_worksheet | model_blinded_worksheet | html_review]",
                "independent_human_review_completed: [TO BE COMPLETED: yes]",
                "codex_triage_not_copied_as_human_labels: [TO BE COMPLETED: yes]",
                "all_50_rows_reviewed: [TO BE COMPLETED: yes]",
                "all_eight_binary_fields_and_auditor_notes_completed: [TO BE COMPLETED: yes]",
                "",
                "The independent human review covered all 50 rows.",
                "Codex-assisted audit was not copied as human labels.",
                "All eight binary label fields and auditor_notes were completed.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    attestation_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_attestation")
    assert report["status"] == "blocked"
    assert attestation_gate["status"] == "fail"
    assert "human-audit attestation still contains completion placeholders" in attestation_gate["errors"]


def test_step1_readiness_check_blocks_when_incomplete_human_audit_memo_claims_completion(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir, validation_status="incomplete", n_complete_rows=0)
    (artifact_dir / "audits" / "active_verification_pilot_human_audit_paper_update.md").write_text(
        "\n".join(
            [
                "# Active-Verification Human-Audit Paper Update",
                "",
                "- status: `incomplete`",
                "- n_labeled: 0",
                "",
                "A single-auditor pilot human audit reports the human-labeled active-verification audit separately from Codex-assisted triage: 50/50 as semantically useful, 47/50 as machine executable, 37/50 as containing the required action type, and 2/50 automatic rejections as plausibly too strict.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    memo_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_paper_update")
    assert memo_gate["status"] == "fail"
    assert "human-audit paper-update memo contains paper-ready sentence before completion" in memo_gate["errors"]


def test_step1_readiness_check_blocks_when_completed_human_audit_memo_counts_are_stale(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    memo_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_paper_update.md"
    memo_path.write_text(
        memo_path.read_text(encoding="utf-8").replace("47/50 as machine executable", "48/50 as machine executable"),
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    memo_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_paper_update")
    assert memo_gate["status"] == "fail"
    assert "human-audit paper-update memo missing or stale phrase: 47/50 as machine executable" in memo_gate["errors"]


def test_step1_readiness_check_blocks_when_model_blinded_packet_leaks_model_identity(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    packet_path = artifact_dir / "audits" / "active_verification_pilot_human_audit_model_blinded_packet_50.md"
    packet_path.write_text(
        packet_path.read_text(encoding="utf-8") + "gpt-5.4\nstandard_answer\naction_gate_pass\n",
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    packet_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_model_blinded_packet")
    assert packet_gate["status"] == "fail"
    assert "model-blinded packet exposes forbidden phrase: gpt-5.4" in packet_gate["errors"]
    assert "model-blinded packet exposes forbidden phrase: standard_answer" in packet_gate["errors"]
    assert "model-blinded packet exposes forbidden phrase: action_gate_pass" in packet_gate["errors"]


def test_step1_readiness_check_blocks_when_human_audit_review_page_lacks_completion_guard(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "audits" / "active_verification_human_audit_review.html").write_text(
        "<!doctype html><button>Download strict CSV</button>\n",
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    review_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_review")
    assert review_gate["status"] == "fail"
    assert "missing human-audit review HTML phrase: completion download guard" in review_gate["errors"]
    assert "missing human-audit review HTML phrase: strict CSV import validator" in review_gate["errors"]


def test_step1_readiness_check_blocks_when_human_audit_review_launcher_is_invalid(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "serve_human_audit_review.sh").write_text(
        "#!/usr/bin/env bash\npython3 -m http.server\n",
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    review_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_review")
    assert review_gate["status"] == "fail"
    assert "missing human-audit review launcher phrase: localhost bind" in review_gate["errors"]
    assert "missing human-audit review launcher phrase: review HTML target" in review_gate["errors"]


def test_step1_readiness_check_blocks_when_human_audit_finalize_script_is_invalid(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "finalize_human_audit.sh").write_text(
        "#!/usr/bin/env bash\nuv run eha-step1-release finalize-active-verification-human-audit\n",
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    finalize_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit_finalize_script")
    assert finalize_gate["status"] == "fail"
    assert "missing human-audit finalization script phrase: worksheet import option" in finalize_gate["errors"]
    assert "missing human-audit finalization script phrase: artifact rebuild command" in finalize_gate["errors"]
    assert "missing human-audit finalization script phrase: readiness status summary" in finalize_gate["errors"]
    assert "missing human-audit finalization script phrase: failing gates summary" in finalize_gate["errors"]


def test_step1_readiness_check_blocks_when_release_verifier_script_is_invalid(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "verify_step1_release.sh").write_text(
        "#!/usr/bin/env bash\nuv run eha-step1-release step1-readiness-check\n",
        encoding="utf-8",
    )
    write_artifact_file_manifest(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    verifier_gate = next(gate for gate in report["gates"] if gate["name"] == "step1_release_verify_script")
    assert verifier_gate["status"] == "fail"
    assert "missing Step 1 release verifier script phrase: minimal example command" in verifier_gate["errors"]
    assert "missing Step 1 release verifier script phrase: allow blocked option" in verifier_gate["errors"]


def test_step1_readiness_check_blocks_on_semantic_id_leakage(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "README.md").write_text("leaked eham_001_pollutant_root\n", encoding="utf-8")

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    leakage_gate = next(gate for gate in report["gates"] if gate["name"] == "semantic_id_leakage")
    assert leakage_gate["status"] == "fail"
    assert "README.md" in leakage_gate["errors"][0]


def test_step1_readiness_check_blocks_when_file_manifest_is_stale(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "README.md").write_text(
        "controlled diagnostic package\n"
        "step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports\n"
        "not human validation\n"
        "legal, medical, financial\n"
        "changed after file manifest\n",
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    file_gate = next(gate for gate in report["gates"] if gate["name"] == "file_manifest")
    assert file_gate["status"] == "fail"
    assert "file_manifest sha256 mismatch for README.md" in file_gate["errors"]


def test_step1_readiness_check_blocks_when_artifact_readme_lacks_scope_notes(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "README.md").write_text("step1-readiness-check\nnot human validation\n", encoding="utf-8")

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    readme_gate = next(gate for gate in report["gates"] if gate["name"] == "artifact_readme_scope")
    assert readme_gate["status"] == "fail"
    assert "missing artifact README scope phrase: controlled diagnostic package" in readme_gate["errors"]
    assert "missing artifact README scope phrase: deployment safety scope limit" in readme_gate["errors"]
    assert "missing artifact README scope phrase: human audit status label" in readme_gate["errors"]


def test_step1_readiness_check_blocks_when_schema_ablation_lacks_model_task_coverage(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "audits" / "generated_lore_schema_ablation.csv").write_text(
        "\n".join(
            [
                "schema_variant,model,n,prompt_condition,belief_correctness",
                "current_schema,gpt-5.4,20,standard_answer,1",
                "current_schema,claude-opus-4-7,20,standard_answer,1",
                "minimal_schema,gpt-5.4,20,standard_answer,1",
                "minimal_schema,claude-opus-4-7,20,standard_answer,1",
                "diagnostic_schema_no_hygiene,gpt-5.4,20,standard_answer,1",
                "diagnostic_schema_no_hygiene,claude-opus-4-7,20,standard_answer,1",
                "clarified_schema,gpt-5.4,20,standard_answer,1",
                "clarified_schema,claude-opus-4-7,19,standard_answer,1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    schema_gate = next(gate for gate in report["gates"] if gate["name"] == "generated_lore_schema_ablation")
    assert schema_gate["status"] == "fail"
    assert "generated-lore schema ablation covers fewer than 3 models: 2" in schema_gate["errors"]
    assert "schema ablation clarified_schema/claude-opus-4-7 has n=19; expected at least 20" in schema_gate["errors"]


def test_step1_readiness_check_blocks_when_main_outputs_are_not_opaque(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    manifest_path = artifact_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["frontier_main_outputs"]["source_kind"] = "semantic_run"
    manifest["frontier_main_outputs"]["model_visible_doc_id_policy"] = "semantic_ids"
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    outputs_gate = next(gate for gate in report["gates"] if gate["name"] == "opaque_main_outputs")
    assert outputs_gate["status"] == "fail"
    assert "frontier main source_kind is not opaque_run: semantic_run" in outputs_gate["errors"]
    assert "frontier main doc_id policy is not opaque_per_task: semantic_ids" in outputs_gate["errors"]


def test_step1_readiness_check_blocks_when_frontier_manifests_are_stale(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    run_manifest_path = artifact_dir / "outputs" / "frontier_main_opaque_run_manifest.json"
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8"))
    run_manifest["model_visible_doc_id_policy"] = "semantic_ids"
    run_manifest_path.write_text(json.dumps(run_manifest) + "\n", encoding="utf-8")

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    outputs_gate = next(gate for gate in report["gates"] if gate["name"] == "opaque_main_outputs")
    assert outputs_gate["status"] == "fail"
    assert "copied run manifest doc_id policy is not opaque_per_task: semantic_ids" in outputs_gate["errors"]
    assert "frontier main run_manifest_sha256 does not match copied file" in outputs_gate["errors"]


def test_step1_readiness_check_blocks_when_human_audit_sample_lacks_required_condition(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir, include_all_human_audit_conditions=False)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    human_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit")
    assert human_gate["status"] == "fail"
    assert "human-audit label sheet missing required condition: generated_lore" in human_gate["errors"]


def test_step1_readiness_check_blocks_on_stale_human_audit_validation(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    labels_path = artifact_dir / "audits" / "active_verification_human_audit.csv"
    labels_text = labels_path.read_text(encoding="utf-8")
    labels_path.write_text(labels_text.replace("human_labeled,m1,t00,clean,standard_answer,1", "human_labeled,m1,t00,clean,standard_answer,0"), encoding="utf-8")

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    human_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit")
    assert "human audit validation is stale: labels_sha256 does not match current CSV" in human_gate["errors"]


def test_step1_readiness_check_blocks_when_human_audit_manifest_lacks_label_fields(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    manifest_path = artifact_dir / "audits" / "active_verification_human_audit_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["label_fields"].remove("trace_source_needed")
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    human_gate = next(gate for gate in report["gates"] if gate["name"] == "active_verification_human_audit")
    assert "human audit manifest missing label field: trace_source_needed" in human_gate["errors"]


def test_step1_readiness_check_blocks_when_minimal_example_does_not_run(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    (artifact_dir / "scorer" / "scoring_contract.py").write_text("raise SystemExit(3)\n", encoding="utf-8")

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    minimal_gate = next(gate for gate in report["gates"] if gate["name"] == "minimal_example")
    assert minimal_gate["status"] == "fail"
    assert any("minimal example exited nonzero" in error for error in minimal_gate["errors"])


def test_step1_readiness_check_blocks_on_missing_paper_positioning(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir, include_required_phrases=False)

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    paper_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_positioning")
    assert paper_gate["status"] == "fail"
    assert any("controlled diagnostic benchmark" in error for error in paper_gate["errors"])


def test_step1_readiness_check_blocks_when_artifact_appendix_omits_finalization_shortcut(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)
    (paper_dir / "appendix" / "e_artifacts.tex").write_text(
        "artifact/serve_human_audit_review.sh\nnot counted as human validation\n",
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    appendix_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_artifact_appendix")
    assert appendix_gate["status"] == "fail"
    assert "missing artifact appendix phrase: finalization shortcut" in appendix_gate["errors"]
    assert "missing artifact appendix phrase: worksheet finalization option" in appendix_gate["errors"]
    assert "missing artifact appendix phrase: human-audit reviewer brief" in appendix_gate["errors"]


def test_step1_readiness_check_blocks_when_step_boundary_is_missing(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)
    (paper_dir / "sections" / "08_discussion.tex").write_text(
        "The paper presents a benchmark and discusses future work.\n",
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    boundary_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_step_boundary")
    assert boundary_gate["status"] == "fail"
    assert "missing Step 1/Step 2 boundary phrase: diagnostic release" in boundary_gate["errors"]
    assert "missing Step 1/Step 2 boundary phrase: independent human audit" in boundary_gate["errors"]


def test_step1_readiness_check_blocks_when_paper_pdf_is_stale(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)
    source = paper_dir / "sections" / "02_benchmark_design.tex"
    source.write_text(source.read_text(encoding="utf-8") + "new source change\n", encoding="utf-8")
    source_mtime = source.stat().st_mtime
    os.utime(paper_dir / "main.pdf", (source_mtime - 10, source_mtime - 10))

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    assert report["status"] == "blocked"
    freshness_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_pdf_freshness")
    assert freshness_gate["status"] == "fail"
    assert any("rebuild paper" in error for error in freshness_gate["errors"])


def test_step1_readiness_check_blocks_when_paper_baseline_values_are_stale(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)
    baseline_table = paper_dir / "tables" / "opaque_baselines.tex"
    baseline_table.write_text(
        baseline_table.read_text(encoding="utf-8").replace("Metadata-only & 0.400", "Metadata-only & 0.520"),
        encoding="utf-8",
    )
    (paper_dir / "sections" / "09_limitations.tex").write_text(
        "not to certify deployment safety\nmetadata-only and simple heuristic baselines reach 0.520 and 0.560 operational escape\n",
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    baseline_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_baseline_table_consistency")
    assert baseline_gate["status"] == "fail"
    assert any("paper opaque baseline table row mismatch for Metadata-only" in error for error in baseline_gate["errors"])
    assert "paper limitations baseline prose does not match current artifact baseline escape values" in baseline_gate["errors"]


def test_step1_readiness_check_blocks_when_frontier_result_tables_are_stale(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)
    main_table = paper_dir / "tables" / "main_model_decomposition.tex"
    main_table.write_text(
        main_table.read_text(encoding="utf-8").replace(r"\code{gpt-5.4} & 10 & 1.000", r"\code{gpt-5.4} & 10 & 0.500"),
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    frontier_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_frontier_results_consistency")
    assert frontier_gate["status"] == "fail"
    assert any("main_model_decomposition row mismatch for gpt-5.4" in error for error in frontier_gate["errors"])


def test_step1_readiness_check_blocks_when_action_audit_table_values_are_stale(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)
    section_path = paper_dir / "sections" / "06_active_verification_case.tex"
    section_path.write_text(
        section_path.read_text(encoding="utf-8").replace(r"\code{gpt-5.4} & 40 & 0.725", r"\code{gpt-5.4} & 40 & 0.525"),
        encoding="utf-8",
    )
    appendix_path = paper_dir / "appendix" / "d_extra_tables.tex"
    appendix_path.write_text(
        appendix_path.read_text(encoding="utf-8").replace(r"\code{gpt-5.4} & 40 & 0.725", r"\code{gpt-5.4} & 40 & 0.525"),
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    action_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_action_audit_table_consistency")
    assert action_gate["status"] == "fail"
    assert any("active-verification section table mismatch for gpt-5.4" in error for error in action_gate["errors"])
    assert any("active-verification appendix table mismatch for gpt-5.4" in error for error in action_gate["errors"])


def test_step1_readiness_check_blocks_when_codex_triage_numbers_are_stale(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)
    section_path = paper_dir / "sections" / "06_active_verification_case.tex"
    section_path.write_text(
        section_path.read_text(encoding="utf-8").replace("47/50 as machine executable", "45/50 as machine executable"),
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    triage_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_codex_triage_consistency")
    assert triage_gate["status"] == "fail"
    assert "active-verification section missing Codex triage phrase: 47/50 as machine executable" in triage_gate["errors"]


def test_step1_readiness_check_blocks_when_incomplete_human_audit_boundary_is_missing(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir, validation_status="incomplete", n_complete_rows=0)
    write_fake_readiness_paper(paper_dir)
    section_path = paper_dir / "sections" / "06_active_verification_case.tex"
    section_path.write_text(
        section_path.read_text(encoding="utf-8").replace("This audit is not treated as human validation.", "This audit is complete."),
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    claim_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_human_audit_claim_consistency")
    assert claim_gate["status"] == "fail"
    assert "active-verification section or limitations must state incomplete audit is not human validation" in claim_gate["errors"]


def test_step1_readiness_check_blocks_when_complete_human_audit_counts_are_absent_from_paper(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)
    section_path = paper_dir / "sections" / "06_active_verification_case.tex"
    section_path.write_text(
        section_path.read_text(encoding="utf-8").replace("50/50 as semantically useful", "49/50 as semantically useful"),
        encoding="utf-8",
    )

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    claim_gate = next(gate for gate in report["gates"] if gate["name"] == "paper_human_audit_claim_consistency")
    assert claim_gate["status"] == "fail"
    assert "active-verification section missing human-audit phrase: 50/50 as semantically useful" in claim_gate["errors"]


def test_step1_readiness_check_reports_ready_when_all_release_gates_pass(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, out_dir=report_dir)

    assert report["status"] == "ready"
    assert all(gate["status"] == "pass" for gate in report["gates"])
    assert next(gate for gate in report["gates"] if gate["name"] == "minimal_example")["status"] == "pass"
    markdown = (report_dir / "eha_step1_readiness_check.md").read_text(encoding="utf-8")
    assert "status: `ready`" in markdown


def test_step1_readiness_check_reports_ready_when_artifact_and_paper_gates_pass(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifact"
    paper_dir = tmp_path / "paper"
    report_dir = tmp_path / "reports"
    write_fake_readiness_artifact(artifact_dir)
    write_fake_readiness_paper(paper_dir)

    report = step1_readiness_check(artifact_dir=artifact_dir, paper_dir=paper_dir, out_dir=report_dir)

    assert report["status"] == "ready"
    assert {gate["name"] for gate in report["gates"]} >= {
        "paper_required_files",
        "paper_positioning",
        "paper_artifact_appendix",
        "paper_unresolved_markers",
        "paper_pdf_freshness",
        "paper_semantic_id_leakage",
    }
