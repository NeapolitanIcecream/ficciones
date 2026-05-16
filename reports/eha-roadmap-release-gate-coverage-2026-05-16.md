# EHA Roadmap Release-Gate Coverage

Date: 2026-05-16

Source roadmap: `/Users/chenmohan/Downloads/eha_two_step_roadmap.md`.

This file maps the Step 1 roadmap requirements to concrete release artifacts and verifier gates. It is meant to prevent treating broad progress as release completion. The current Step 1 release state remains blocked by the missing independent human/manual active-verification labels.

## Current Verdict

Step 1 is not fully releasable yet.

`reports/eha_step1_readiness_check.json` currently reports:

- `status = blocked`
- passing gates: 29/31
- failing gates:
  - `active_verification_human_audit`: validation is `incomplete`, `n_complete_rows = 0`
  - `artifact_manifest`: `active_verification_human_audit.status = incomplete`, `n_labeled = 0`

The block is not a software packaging issue. It is a missing independent human/manual annotation issue: the 50 audit rows still need all eight binary labels, `audit_status = human_labeled`, nonblank `auditor_notes`, and a completed human-audit attestation after labeling. The Codex-assisted `gpt-5.5` xhigh audit is retained only as triage evidence and must not be counted as human validation.

## Step 1 Success Criteria

| Roadmap requirement | Current evidence | Verifier coverage | Status |
|---|---|---|---|
| Opaque-ID main experiment is the only main result | `artifact/outputs/frontier_main_opaque_predictions.jsonl`, `artifact/outputs/frontier_main_opaque_scored.csv`, `paper/sections/03_model_cohort.tex` | `opaque_main_outputs`, `paper_frontier_results_consistency`, `semantic_id_leakage`, `paper_semantic_id_leakage` | Pass |
| Old semantic-ID run is audit history only | `artifact/manifest.json`; no semantic run copied into `artifact/outputs/`; paper validity-audit prose | `opaque_main_outputs`, `semantic_id_leakage`, `paper_positioning` | Pass |
| Generated-lore has four-schema ablation or a clear explanation | `artifact/audits/generated_lore_schema_ablation.csv`, `artifact/audits/generated_lore_schema_ablation_rows.csv`, `paper/sections/05_generated_lore_case.tex` | `generated_lore_schema_ablation`, `paper_frontier_results_consistency` | Pass |
| Operational escape is formalized | `paper/sections/02_benchmark_design.tex`, `eha-mvp/eha/epistemic_resilience.py` | Unit tests and paper source scan through `paper_required_files` / `paper_positioning`; release tests cover scoring metrics | Pass |
| Diagnostic metrics are reported or supported | `eha-mvp/eha/epistemic_resilience.py`, `eha-mvp/tests/test_epistemic_step1_release.py`, paper result tables | `uv run pytest`, `paper_frontier_results_consistency` | Pass |
| Baselines include ID-only, metadata-only, heuristic, random, and always-insufficient | `artifact/baselines/*.csv`, `paper/tables/opaque_baselines.tex`, `paper/sections/09_limitations.tex` | `baseline_files`, `paper_baseline_table_consistency` | Pass |
| Active-verification has 50-row human audit or explicit pilot audit | `artifact/audits/active_verification_human_audit.csv`, worksheet, model-blinded worksheet, HTML review page, launcher, finalization script, protocol, attestation template, validation report, paper-update memo, handoff | `active_verification_human_audit`, `active_verification_human_audit_worksheet`, `active_verification_human_audit_model_blinded_worksheet`, `active_verification_human_audit_protocol`, `active_verification_human_audit_attestation`, `active_verification_human_audit_paper_update`, `active_verification_human_audit_review`, `active_verification_human_audit_finalize_script`, `paper_human_audit_claim_consistency`, `artifact_manifest` | Blocked: 50 rows exist, 0 human-labeled, notes blank; attestation template is present and must be completed after labels |
| Artifact package can run minimal example | `artifact/reproduce_minimal.sh`, `artifact/examples/*`, `artifact/scorer/*` | `minimal_example`; manual rerun returned expected JSON score keys | Pass |
| Paper is positioned as a controlled diagnostic benchmark | Title, abstract, introduction, discussion, limitations, artifact appendix | `paper_positioning`, `paper_step_boundary`, `paper_artifact_appendix`, `paper_unresolved_markers` | Pass |
| Semantic doc IDs no longer appear as model-visible IDs | `artifact/` package and `paper/` sources | `semantic_id_leakage` scans 54 artifact files; `paper_semantic_id_leakage` scans 24 paper files; manual `rg "eham_" artifact` has no hits | Pass |
| All main figures/tables use opaque-run data | `paper/tables/*.tex`, `artifact/outputs/frontier_main_opaque_scored.csv` | `paper_frontier_results_consistency`, `paper_baseline_table_consistency`, `paper_action_audit_table_consistency`, `paper_codex_triage_consistency`, `paper_human_audit_claim_consistency` | Pass |

## Artifact Checklist

The roadmap asks for a minimal `artifact/` package. The current package contains all requested core files plus extra audit materials:

| Roadmap path | Current file(s) | Status |
|---|---|---|
| `artifact/README.md` | `artifact/README.md` | Present; includes controlled-diagnostic scope, paper-aware readiness command, not-human-validation boundary, the human-audit success contract (`audit_status = human_labeled`, `n_labeled = 50`, nonblank `auditor_notes`), and deployment-safety limits |
| `artifact/data/tasks_opaque.jsonl` | `artifact/data/tasks_opaque.jsonl` | Present |
| `artifact/data/documents_opaque.jsonl` | `artifact/data/documents_opaque.jsonl` | Present |
| `artifact/data/gold_labels.jsonl` | `artifact/data/gold_labels.jsonl` | Present |
| `artifact/prompts/standard_answer.txt` | `artifact/prompts/standard_answer.txt` | Present |
| `artifact/prompts/epistemic_hygiene_instruction.txt` | `artifact/prompts/epistemic_hygiene_instruction.txt` | Present |
| `artifact/scorer/scoring_contract.py` | `artifact/scorer/scoring_contract.py` | Present |
| `artifact/scorer/README.md` | `artifact/scorer/README.md` | Present |
| `artifact/outputs/frontier_main_opaque_predictions.jsonl` | `artifact/outputs/frontier_main_opaque_predictions.jsonl` | Present |
| `artifact/outputs/frontier_main_opaque_scored.csv` | `artifact/outputs/frontier_main_opaque_scored.csv` | Present |
| `artifact/baselines/id_only.csv` | `artifact/baselines/id_only.csv` | Present |
| `artifact/baselines/metadata_only.csv` | `artifact/baselines/metadata_only.csv` | Present |
| `artifact/baselines/simple_heuristic.csv` | `artifact/baselines/simple_heuristic.csv` | Present |
| `artifact/baselines/random_valid_schema.csv` | `artifact/baselines/random_valid_schema.csv` | Present |
| `artifact/baselines/always_insufficient.csv` | `artifact/baselines/always_insufficient.csv` | Present |
| `artifact/audits/opaque_prompt_audit_summary.json` | `artifact/audits/opaque_prompt_audit_summary.json` | Present |
| `artifact/audits/generated_lore_schema_ablation.csv` | `artifact/audits/generated_lore_schema_ablation.csv` | Present |
| `artifact/audits/active_verification_human_audit.csv` | `artifact/audits/active_verification_human_audit.csv` | Present but unlabeled |
| `artifact/examples/minimal_task.json` | `artifact/examples/minimal_task.json` | Present |
| `artifact/examples/minimal_model_output.json` | `artifact/examples/minimal_model_output.json` | Present |
| `artifact/examples/minimal_score.json` | `artifact/examples/minimal_score.json` | Present |
| `artifact/reproduce_minimal.sh` | `artifact/reproduce_minimal.sh` | Present and executable |
| Human-audit review launcher | `artifact/serve_human_audit_review.sh` | Present and executable |
| Human-audit finalization shortcut | `artifact/finalize_human_audit.sh` | Present and executable; prints readiness status and failing gate names after finalization |
| Final pre-release verifier | `artifact/verify_step1_release.sh` | Present and executable |

Additional release controls now present:

- `artifact/file_manifest.json`: 53 packaged files, excluding itself, with byte size and SHA-256 hashes.
- `artifact/audits/active_verification_human_audit_reviewer_brief.md`: short reviewer-facing audit instructions covering review surfaces, labels, notes, triage separation, attestation, and finalization.
- `artifact/manifest.json`: package-level provenance and audit status.
- `artifact/outputs/frontier_main_opaque_run_manifest.json` and `_report_manifest.json`: copied opaque-run provenance.
- `artifact/README.md`: release entrypoint with the readiness command, dry-run verifier command, human-audit success contract, and warning that Codex-assisted outputs are triage artifacts, not human validation.
- `artifact/audits/active_verification_human_audit_review.html`: local review/import/export page for human labels and notes. It supports evidence-condition filtering, jumps to the next incomplete row, and disables strict CSV download until all rows have the eight binary labels and nonblank `auditor_notes`.
- `artifact/audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`: model-blinded CSV worksheet that omits model identity, prompt condition, and automatic scorer fields while preserving row order with `row_index`; it can be imported back into the strict CSV with `--from-model-blinded-worksheet`.
- `artifact/audits/active_verification_pilot_human_audit_model_blinded_packet_50.md`: model-blinded reading packet that omits model identity, prompt condition, and automatic scorer outcomes while preserving row order for transfer into the strict CSV or worksheet.
- `artifact/audits/active_verification_pilot_human_audit_paper_update.md`: paper-update memo that records incomplete status now and, after complete human validation, provides exact paper-ready counts while keeping Codex-assisted triage separate.
- `artifact/audits/active_verification_human_audit_attestation.md`: provenance template for auditor identifier/role, date, review surface, independent-review confirmation, no-copy-from-Codex confirmation, all-50-row coverage, and completion of all eight binary labels plus notes; readiness allows placeholders while labels are incomplete and rejects them once validation is complete.
- `artifact/serve_human_audit_review.sh`: local `127.0.0.1` launcher for the HTML review page.
- `artifact/finalize_human_audit.sh`: local post-labeling shortcut that can import the wide worksheet with `--from-worksheet` or model-blinded worksheet with `--from-model-blinded-worksheet`, finalize labels, sync the completed attestation into the source results directory, rebuild the artifact package, and rerun readiness.
- `artifact/verify_step1_release.sh`: final pre-release verifier that runs the minimal example, test suite, paper build, paper-aware readiness check, and `git diff --check`; `--allow-blocked` supports current dry runs before human labels are complete.
- `artifact/audits/active_verification_human_audit_protocol.md`: single-auditor pilot protocol and boundary rules.
- `artifact/audits/active_verification_pilot_codex_xhigh_audit_50.csv`: separate LLM-assisted triage audit, not human validation.

## Paper Section Coverage

| Roadmap writing task | Current location | Status |
|---|---|---|
| Reposition title/abstract/contributions around controlled diagnostic benchmark | `paper/main.tex`, `paper/sections/00_abstract.tex`, `paper/sections/01_intro.tex` | Pass |
| Avoid universal benchmark / provider leaderboard framing | `paper/sections/03_model_cohort.tex`, `paper/sections/08_discussion.tex`, `paper/sections/09_limitations.tex`; enforced by `paper_step_boundary` | Pass |
| Add operational escape formula | `paper/sections/02_benchmark_design.tex` | Pass |
| Add baselines and explain why clean evidence alone is insufficient | `paper/tables/opaque_baselines.tex`, `paper/sections/04_results.tex`, `paper/sections/09_limitations.tex` | Pass |
| Make schema sensitivity a finding | `paper/sections/05_generated_lore_case.tex`, `paper/sections/08_discussion.tex` | Pass |
| Active verification distinguishes human interpretability from machine executability | `paper/sections/06_active_verification_case.tex`, `paper/appendix/b_scoring_contract.tex` | Pass, but human validation remains pending |
| Ethics / scope note for deployment safety | `paper/sections/09_limitations.tex`, `artifact/README.md` | Pass |
| Artifact appendix describes release package rather than only local paths | `paper/appendix/e_artifacts.tex` | Pass; now includes the review launcher, finalization shortcut, reviewer brief, human-audit attestation, and release verifier |

## Commands Verified

Recent verification commands:

```bash
cd eha-mvp && uv run pytest
cd paper && make
cd eha-mvp && uv run eha-step1-release step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports
cd artifact && ./reproduce_minimal.sh
git diff --check
rg -n "eham_" artifact
```

Observed results:

- `uv run pytest`: 194 passed.
- `uv run pytest tests/test_epistemic_step1_release.py -q`: 51 passed.
- `make`: rebuilt `paper/main.pdf`.
- `step1-readiness-check`: `status = blocked`, with 29/31 gates passing. The `paper_human_audit_claim_consistency` gate passes because the paper still treats the incomplete 0/50 human audit as not-human-validation evidence; `paper_step_boundary` passes because the discussion frames Step 1 as a diagnostic release rather than a completed scalable benchmark; `active_verification_human_audit_attestation` passes as an incomplete-audit template and will reject placeholders after validation is complete; `active_verification_human_audit_paper_update` passes with `incomplete_paper_update_boundary=True` and will reject stale or paper-ready human-audit counts after validation is complete; `active_verification_human_audit_model_blinded_packet` passes with 50 rows and no model/prompt/scorer leakage; `active_verification_human_audit_model_blinded_worksheet` passes with 50 rows and strict-CSV importability; `active_verification_human_audit_finalize_script` now checks the attestation sync path and readiness/failing-gate summary output; the artifact appendix gate now covers the model-blinded worksheet, reviewer brief, human-audit attestation, and paper-update memo; `step1_release_verify_script` passes with syntax and command coverage; only the human-audit and manifest human-label gates fail.
- `./verify_step1_release.sh --allow-blocked`: ran the minimal example, 194-test suite, paper build, paper-aware readiness check, and `git diff --check`; completed with readiness status `blocked`.
- `paper_pdf_freshness`: passed after rebuilding `paper/main.pdf`; latest source was `appendix/e_artifacts.tex`.
- `paper_artifact_appendix`: passed with review launcher, finalization shortcut, worksheet finalization option, paper-aware readiness check, and not-human-validation evidence.
- `bash -n artifact/serve_human_audit_review.sh` and `bash -n artifact/finalize_human_audit.sh`: passed; the review script serves `artifact/` on `127.0.0.1` and opens the HTML review page when available, and the finalization script is syntax-valid and prints readiness status plus failing gates.
- Playwright browser verification for `artifact/audits/active_verification_human_audit_review.html`: 50 row cards loaded; initial download was disabled at `0 / 50`; filling all eight labels and auditor notes on all rows enabled download at `50 / 50`; strict CSV import accepted valid rows and rejected row-count or non-label metadata changes; condition filters showed 10 rows for `clean` and 10 rows for `generated_lore`; `Next incomplete row` navigated to `#row-1` on the initial blank sheet.
- `./reproduce_minimal.sh`: returned a JSON score with `belief_correctness`, `evidence_cleanliness`, `operational_epistemic_escape`, and `uncertainty_discipline`.
- `git diff --check`: passed.
- `rg -n "eham_" artifact`: no hits.

## Next Gate-Closing Action

The only Step 1 release gate that cannot be closed by more code or LLM triage is the independent human/manual active-verification audit:

1. A human annotator labels the 50 rows and writes auditor notes using one of:
   - `artifact/audits/active_verification_human_audit.csv`
   - `artifact/audits/active_verification_pilot_human_audit_worksheet_50.csv`
   - `artifact/audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`
   - `artifact/audits/active_verification_human_audit_review.html`
2. Complete `artifact/audits/active_verification_human_audit_attestation.md` with the auditor identifier or role, date, review surface, and required yes confirmations.
3. Run `artifact/finalize_human_audit.sh`, `artifact/finalize_human_audit.sh --from-worksheet` if the wide worksheet was filled, or `artifact/finalize_human_audit.sh --from-model-blinded-worksheet` if the model-blinded worksheet was filled.
4. Rebuild `paper/main.pdf` after updating human-audit claims.
5. Rerun `step1-readiness-check` if paper claims changed after the shortcut ran.

Until that happens, do not mark Step 1 as complete and do not present the Codex-assisted audit as human validation.
