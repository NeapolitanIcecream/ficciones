# EHA Step 1 Roadmap Progress

Date: 2026-05-15; updated 2026-05-16

## Objective

Advance the Step 1 workshop/arXiv v1 roadmap without starting Step 2 scale-up. This pass focuses on cheap experimental closures and paper positioning:

- no-API baseline completion;
- diagnostic metric formalization;
- reproducibility artifact package;
- paper repositioning as a controlled diagnostic benchmark;
- clear accounting of remaining Step 1 gaps.

## Completed In This Pass

### Baselines

New unified Step 1 baseline report:

- `eha-mvp/results/reports-eha-step1-baselines-2026-05-15/`

Summary:

| System | Operational escape | Belief | Evidence clean | Uncertainty | Verification | Support empty |
|---|---:|---:|---:|---:|---:|---:|
| ID-only | 0.080 | 0.200 | 1.000 | 0.200 | 0.000 | 1.000 |
| Random valid schema | 0.080 | 0.355 | 0.530 | 0.630 | 0.068 | 0.295 |
| Always insufficient | 0.080 | 0.200 | 1.000 | 0.200 | 0.000 | 1.000 |
| Metadata-only | 0.400 | 0.400 | 1.000 | 0.960 | 0.067 | 0.240 |
| Simple heuristic | 0.560 | 0.600 | 1.000 | 0.960 | 0.000 | 0.240 |

Interpretation: random valid output and ID-only output do not solve the benchmark. Always-insufficient and ID-only are evidence-clean because they leave support empty. Metadata and simple heuristics solve some surface structure, but action behavior remains weak.

### Diagnostic Metrics

`score_record` now exports:

- `support_empty_rate`
- `evidence_precision`
- `clean_support_recall`
- `rejected_pollutant_rate`
- `dual_role_rate`
- `required_action_recall`

These are included in Step 1 baseline rows and summaries.

### Artifact Package

Created a release-facing package at:

- `artifact/`

It contains:

- opaque tasks, documents, and gold labels;
- prompt contracts;
- minimal scorer notes;
- opaque frontier outputs and copied frontier run/report manifests;
- five no-API baselines;
- prompt, generated-lore, and active-verification audit summaries;
- `file_manifest.json`, with byte size and SHA-256 hash for every packaged file except itself;
- a runnable minimal example.

2026-05-16 update: the artifact package now separates the 200-row automatic active-verification action audit from the pilot human-audit sheet:

- `artifact/audits/active_verification_action_audit_summary.csv` is the automatic action-interface summary.
- `artifact/audits/active_verification_human_audit.csv` is the 50-row pilot human-audit label sheet, currently unlabeled.
- `artifact/audits/active_verification_human_audit_manifest.json` records the eight roadmap audit label fields, including the three needed-action fields.
- `artifact/audits/active_verification_human_audit_readme.md` is the self-contained quickstart for labeling, finalization, artifact rebuild, and readiness verification.
- `artifact/audits/active_verification_human_audit_reviewer_brief.md` is a short task-focused brief for the human reviewer, covering review-surface choice, the eight binary labels, required notes, Codex-triage separation, attestation, and finalization commands.
- `artifact/audits/active_verification_human_audit_protocol.md` records the 50-row single-auditor pilot design, condition stratification, boundary rules, and finalization gate.
- `artifact/audits/active_verification_human_audit_attestation.md` is the provenance attestation template for auditor identifier/role, date, review surface, independent-review confirmation, no-copy-from-Codex confirmation, all-50-row coverage, and completion of all eight binary labels plus notes; readiness allows placeholders while the human audit is incomplete and rejects them once labels are complete.
- `artifact/audits/active_verification_human_audit_review.html` is a local browser review/import/export page for filling labels and notes, importing strict CSV drafts, filtering by evidence condition, jumping to the next incomplete row, and downloading the strict `active_verification_human_audit.csv` only after all rows have the eight binary labels and nonblank `auditor_notes`.
- `artifact/audits/active_verification_pilot_human_audit_worksheet_50.csv` is an optional wide worksheet with row context; the import command strips it back to the strict label CSV without allowing non-label metadata edits.
- `artifact/audits/active_verification_pilot_human_audit_context_50.jsonl` provides opaque-ID context for the label sheet.
- `artifact/audits/active_verification_pilot_human_audit_packet_50.md` provides a row-by-row Markdown packet for a human annotator.
- `artifact/audits/active_verification_pilot_human_audit_validation.json` and `_rows.csv` provide an executable gate check; current status is incomplete with 0 complete rows, and the row report fails the blank sheet for missing labels, `audit_status is not human_labeled`, and blank `auditor_notes`. The report records `labels_sha256` so readiness can detect stale validation after CSV edits.
- `artifact/audits/generated_lore_schema_ablation_rows.csv` provides sanitized row-level schema-ablation evidence over 360 rows; audit-only `eham_*` IDs are mapped to opaque `doc_###` IDs before release packaging.
- `artifact/manifest.json` records `active_verification_human_audit.status = incomplete`, `n_rows = 50`, and `n_labeled = 0`.
- `artifact/audits/active_verification_pilot_codex_xhigh_audit_50.csv` and related summary/notes record a separate Codex-assisted audit, with `active_verification_codex_xhigh_audit.status = complete`, `n_rows = 50`, and `n_labeled = 50`.
- `artifact/manifest.json` records main-output provenance under `frontier_main_outputs`: `source_kind = opaque_run`, `model_visible_doc_id_policy = opaque_per_task`, `source_task_count = 100`, `source_record_count = 1000`, copied `run_manifest_file` / `report_manifest_file`, and their SHA-256 hashes.
- `artifact/serve_human_audit_review.sh` starts a local `127.0.0.1` review server for the HTML human-audit page.
- `artifact/finalize_human_audit.sh` validates completed labels, can import the wide worksheet with `--from-worksheet` or model-blinded worksheet with `--from-model-blinded-worksheet`, syncs the completed attestation into the source results directory, rebuilds the artifact package, and reruns the paper-aware readiness check.
- `artifact/file_manifest.json` records 53 packaged files, excluding itself, with byte sizes and SHA-256 hashes.
- `reports/eha_step1_readiness_check.json` and `.md` provide an executable Step 1 release gate over the artifact package and paper sources.
- 2026-05-16 05:34 update: `artifact/serve_human_audit_review.sh 8765` is running in tmux session `eha-human-audit-review`; `curl -I` returned `200 OK` for `http://127.0.0.1:8765/audits/active_verification_human_audit_review.html`, and the page starts at `0 / 50` complete rows.

Minimal reproduction command:

```bash
cd artifact
./reproduce_minimal.sh
```

### Active-Verification Human-Audit Prep

Created a 50-row annotation sheet for the required pilot human audit:

- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv`
- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_context_50.jsonl`
- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_packet_50.md`
- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_validation.json`
- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_human_audit_guidelines.md`
- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_human_audit_review.html`
- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_summary.json`
- `artifact/audits/active_verification_pilot_human_audit_sample_50.csv`

The sheet is stratified across the five evidence conditions with 10 rows each: clean, generated_lore, false_consensus, buried_primary, and conflicting_evidence. It includes human-label fields for semantic usefulness, machine executability, exact target, required action type, contradiction-search need, primary-search need, trace-source need, and scorer strictness. The three needed-action fields are prefilled but validator-visible as labels so an annotator can confirm or revise them. It also carries automatic prelabels from the 200-row action-interface audit. Action strings are translated back to opaque model-visible `doc_###` IDs for release-facing review. These rows are not yet human-labeled.

An external tmux Codex CLI audit was completed with `gpt-5.5` and `model_reasoning_effort="xhigh"` under `.codex-workflows/eha-active-verification-codex-xhigh-audit/`. It produced:

- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_codex_xhigh_audit_50.csv`
- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_codex_xhigh_audit_notes.md`
- `eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_codex_xhigh_audit_summary.csv`

This is useful as LLM-assisted triage, but it is not counted as independent human validation.

## Roadmap Gate Checklist

| Step 1 requirement | Current evidence | Status |
|---|---|---|
| Opaque-ID main experiment is the only main result | Paper tables and `artifact/outputs/frontier_main_opaque_*` use the opaque run; artifact packaging now translates saved prediction/scored doc IDs back to opaque `doc_###` IDs. | Done |
| Old semantic-ID history quarantined | Current paper and artifact package are opaque-run based; semantic run is not copied into `artifact/`. | Done |
| Generated-lore schema ablation has 4 variants or explains 2 variants | `generated_lore_schema_ablation_4variant.csv` covers current, minimal, diagnostic/no-hygiene, and clarified schemas for the 20 generated-lore tasks and three audited models. Readiness now checks the four variants, at least three models, `n >= 20` summary coverage for each variant/model standard/all row, and sanitized row-level coverage over 20 tasks and 3 models. | Done |
| Operational escape formula | `paper/sections/02_benchmark_design.tex` defines the formula and diagnostic metrics. | Done |
| Required no-API baselines | `eha-mvp/results/reports-eha-step1-baselines-2026-05-15/` and `artifact/baselines/` include ID-only, metadata-only, simple heuristic, random valid schema, and always-insufficient. The paper baseline table and limitations prose now match artifact-derived values; metadata-only and simple heuristic operational escape are `0.400` and `0.560`. | Done |
| Active-verification 50-row human audit or explicit pilot audit | 50-row sheet, wide worksheet, model-blinded worksheet, local HTML review/import/export page, local finalization script, final pre-release verifier, context JSONL, guidelines, quickstart, protocol, audit manifest, attestation template, and incomplete human summary exist with `n_labeled = 0`; the validator now requires all eight roadmap audit fields, `audit_status = human_labeled`, and nonblank `auditor_notes`; the worksheet import path preserves the strict CSV shape, rejects row-order/key changes, and has its own readiness gate with `worksheet_rows=50` and `importable_to_strict_csv=True`; the model-blinded worksheet imports by row order without exposing model identity, prompt condition, or automatic scorer fields; the HTML page can import strict CSV drafts, filter by evidence condition, jump to the next incomplete row, rejects row-count or non-label metadata changes, and enables strict CSV export only after all rows have the eight binary labels and auditor notes; the attestation gate passes as a template while labels are incomplete and will reject placeholders after validation is complete; the finalization script can import a filled worksheet with `--from-worksheet` or `--from-model-blinded-worksheet`, finalize labels, sync completed attestation, rebuild the artifact, rerun readiness, and print readiness status plus failing gate names; the readiness check confirms 10 rows per required evidence condition, compares the current CSV to validation `labels_sha256`, and checks the audit manifest for 50 context rows and 8 label fields; a separate Codex-assisted `gpt-5.5` xhigh audit is complete with 50 labeled rows, readiness checks the paper's 50/47/37/2 Codex-triage counts against the artifact CSV, and the paper human-audit claim gate keeps incomplete human-audit claims separate from Codex triage; readiness check blocks on the missing human labels and notes. | Partially done |
| Artifact package runs minimal example | `artifact/reproduce_minimal.sh` returns a JSON score; readiness includes a `minimal_example` execution gate that checks the scorer output keys. | Done |
| Artifact README carries release scope warnings | `artifact/README.md` states the controlled-diagnostic scope, the full paper-aware readiness command with `--paper-dir ../paper`, Codex triage not-human-validation distinction, the human-audit success contract (`audit_status = human_labeled`, `n_labeled = 50`, and nonblank `auditor_notes`), and legal/medical/financial deployment limit; readiness includes an `artifact_readme_scope` gate. | Done |
| Artifact file manifest is current | `artifact/file_manifest.json` lists all 53 packaged files except itself with byte sizes and SHA-256 hashes; readiness includes a `file_manifest` gate and passes with `manifest_files=53`, `current_files=53`. | Done |
| Paper positioning as controlled diagnostic benchmark | Title, abstract, introduction, limitations, and artifact appendix have been revised; readiness paper gates pass for required files, positioning language, artifact-appendix coverage including the reviewer brief, unresolved markers, PDF freshness, and semantic-ID leakage. | Done |
| No semantic doc IDs as model-visible IDs | `reports/eha_step1_readiness_check.json` scans 54 release artifact files and the `semantic_id_leakage` gate now passes after output/baseline sanitization, HTML review-page packaging, human-audit reviewer-brief packaging, human-audit attestation packaging, model-blinded worksheet packaging, model-blinded audit-packet packaging, paper-update memo packaging, launcher-script packaging, finalization-script packaging, and pre-release verifier packaging. | Done |
| Main figures/tables use opaque-run data | Paper tables and copied frontier outputs are from `results/reports-eha-frontier-main-opaque-2026-05-15/`. Readiness includes `opaque_main_outputs`, which passes with copied run/report manifest checks, 1000 opaque prediction rows and 1000 opaque scored rows from `doc_id_policy = opaque_per_task`, and `paper_frontier_results_consistency`, which recomputes the main model, family, condition, and prompt tables from the scored rows. | Done |

### Paper Updates

Updated the paper to:

- title EHA as a controlled diagnostic benchmark;
- weaken universal benchmark / provider-ranking framing;
- add an operational escape formula;
- add diagnostic metrics to the scoring discussion;
- update the baseline table to five baselines;
- make schema sensitivity an explicit finding;
- clarify in Discussion that this is a Step 1 diagnostic release, not a completed scalable benchmark, and name the larger validation program needed for a stronger benchmark claim;
- describe the reproducibility package rather than only local result paths;
- report a four-variant generated-lore schema ablation over the audited three-model subset.
- tighten the active-verification case study so the 200-row action audit is evidence of an interface issue, while scorer validity and action-error prevalence remain explicitly contingent on independent human audit.
- tighten the conclusion so it presents Step 1 as a controlled diagnostic release and names scale-up, surface-cue stress tests, broader schema ablations, and independent active-verification human audit as the path toward a larger benchmark.
- clean formal-paper wording so the LaTeX sources no longer contain draft/TODO/placeholder wording outside the intentionally incomplete human-audit attestation template.

## Verification Run

- `uv run pytest`: 194 passed.
- `uv run pytest tests/test_epistemic_step1_release.py -q`: 51 passed, including readiness-check gates, file-manifest generation and stale-hash rejection, generated-lore schema/model/task-count coverage checks, human-audit manifest label-field validation, human-audit protocol, reviewer brief, and attestation content checks, completed-audit attestation placeholder rejection, completed-attestation preservation during artifact rebuild, model-blinded packet and model-blinded worksheet leakage/import checks, human-audit review-page/launcher/finalization-script content checks, release-verifier script content checks, worksheet readiness/import checks, worksheet row-order rejection, `auditor_notes` validation, opaque main-output provenance and copied-manifest staleness checks, paper frontier-results table consistency, paper artifact-appendix coverage, paper Step 1/Step 2 boundary coverage, artifact README scope and human-audit success-contract checks, artifact output/baseline doc-ID sanitization, paper baseline table/prose consistency, paper active-verification action-audit table consistency, paper Codex-triage consistency, paper human-audit claim consistency, human-audit paper-update memo consistency, paper PDF freshness, and minimal-example execution.
- `uv run eha-step1-release baselines ...`: wrote 1000 no-API baseline rows.
- `uv run eha-generated-lore-audit schema-ablation-run ...`: wrote 120 new rows for `minimal_schema` and `diagnostic_schema_no_hygiene`, completing the four-variant generated-lore ablation.
- `uv run eha-step1-release active-verification-audit-package ...`: wrote 50 context rows, guidelines, a single-auditor protocol, a row-by-row Markdown packet, the wide human-audit worksheet, the model-blinded worksheet, the human-audit attestation template, and the local HTML review/import/export page.
- `uv run eha-step1-release validate-active-verification-human-audit ...`: wrote an incomplete validation report with 0 complete human-labeled rows; blank rows fail for missing labels, `audit_status`, and `auditor_notes`.
- `uv run pytest tests/test_epistemic_step1_release.py`: covers the finalization path that imports labels only after validation passes.
- `uv run eha-step1-release summarize-active-verification-human-audit ...`: wrote an incomplete summary with `n_labeled = 0`.
- `tmux` + `codex exec -m gpt-5.5 -c model_reasoning_effort="xhigh" ...`: delivered a separate 50-row Codex-assisted active-verification audit.
- `uv run eha-step1-release summarize-active-verification-human-audit --labels-csv ...codex_xhigh... --output-stem active_verification_pilot_codex_xhigh_audit_summary`: wrote a complete Codex-assisted audit summary.
- `uv run eha-step1-release artifact-package ...`: wrote `artifact/`.
- `uv run eha-step1-release step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports`: wrote a blocked readiness report; 29/31 gates pass, including required files, `file_manifest` (`manifest_files=53`, `current_files=53`), baselines, four-schema ablation with three-model, `n >= 20`, row-level 20-task coverage, human-audit protocol content, human-audit attestation template status, `active_verification_human_audit_paper_update` with `incomplete_paper_update_boundary=True`, model-blinded worksheet importability, model-blinded packet coverage, paper-update memo coverage, human-audit review-page/launcher/finalization-script content, release-verifier script content, worksheet row/importability checks, opaque main-output provenance with copied run/report manifest checks, paper frontier-results table consistency, minimal-example execution, artifact and paper semantic-ID leakage, paper positioning, paper Step 1/Step 2 boundary, paper artifact-appendix coverage, baseline table/prose consistency, active-verification action-audit table consistency, Codex-triage consistency, paper human-audit claim consistency, unresolved-marker, and PDF-freshness gates; active-verification human labels remain incomplete at 0/50, with notes also blank.
- `./verify_step1_release.sh --allow-blocked` from `artifact/`: ran the minimal example, 194-test suite, paper build, paper-aware readiness check, and `git diff --check`; completed with readiness status `blocked`.
- `bash -n artifact/serve_human_audit_review.sh` and `bash -n artifact/finalize_human_audit.sh`: passed; the review script launches the local HTML review page on `127.0.0.1`, and the finalization script is syntax-valid and prints readiness status plus failing gate names after finalization.
- Playwright browser verification for `artifact/audits/active_verification_human_audit_review.html`: 50 rows loaded, CSV download was disabled until all eight labels and auditor notes were complete for all rows, valid strict CSV import passed, row-count/non-label metadata changes were rejected, condition filters showed 10 rows for `clean` and `generated_lore`, and `Next incomplete row` navigated to the first incomplete visible row.
- `cd artifact && ./reproduce_minimal.sh`: returned a JSON score.
- `make` in `paper/`: rebuilt `paper/main.pdf` with no TeX warnings after formula repair.
- `git diff --check`: passed.
- Release-facing artifact semantic-ID grep found no semantic model-visible ID remnants.
- `reports/eha_step1_readiness_check.md` is the current executable prompt-to-artifact release checklist.

## Remaining Step 1 Gaps

- Active-verification has a 200-row action-interface audit, a prepared 50-row human-audit sheet, a wide worksheet, a model-blinded worksheet, a local HTML review/import/export page, a single-auditor protocol, an attestation template, and a completed 50-row Codex-assisted xhigh audit. The human sheet is not yet human-labeled and has no auditor notes, and the attestation remains a template, so an independent human/manual annotation pass is still needed before claiming human-validation evidence.
- The artifact package has a minimal scorer and copied release artifacts; it is sufficient for a minimal check, not yet a full standalone benchmark distribution with installer-level polish.
- The paper should receive one final end-to-end read after any human-audit addition.

See also `reports/eha-step1-completion-audit-2026-05-16.md` for the explicit prompt-to-artifact completion checklist.
See `reports/eha-roadmap-release-gate-coverage-2026-05-16.md` for the roadmap-to-release-gate coverage matrix.
See `reports/eha-active-verification-human-audit-handoff-2026-05-16.md` for the exact human-labeling and safe finalization steps.
See `reports/eha-step2-feasibility-and-next-experiment-plan-2026-05-16.md` for the conservative Step 2 plan and the structural schema repair gate that should precede any scale-up.

## Next Recommended Action

If independent human validation is required for the workshop/arXiv claim, do the active-verification single-auditor pilot audit as a separate human/manual annotation artifact, complete the attestation, or have the user nominate a human annotator. The Codex-assisted audit is already separated and can be cited only as triage evidence.
