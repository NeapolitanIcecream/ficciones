# EHA-Uncued Core-Claim Reframing Overnight Runbook

Date: 2026-05-25

Audience: local Codex agent working in `/Users/chenmohan/gits/ficciones`.

Goal: run a long overnight evidence-strengthening pass that decides how much of the observed "belief correctness vs operational epistemic escape" gap reflects real polluted-evidence behavior, and how much reflects schema, harness, scorer, or family-specific metric artifacts. The expected paper direction is to center polluted evidence ecologies, provenance discipline, source independence, and verification behavior; the belief/operation gap should be treated as a diagnostic lens unless the new analyses show that it survives the ambiguity checks below.

This runbook is deliberately broader than the earlier mini-suite. It combines no-call analyses, targeted model reruns, data sanity audits, and a final synthesis report suitable for rewriting the paper.

## Non-Negotiable Rules

- Use only role-uncued artifacts from `eha-mvp/data/uncued-pilot-v1`, `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22`, and later role-uncued Phase 1.x outputs.
- Do not use old cued artifacts or old cued outputs.
- Do not mutate or overwrite Phase 1, Phase 1.1, Phase 1.2, or Phase 1.3 result directories.
- Treat model ranking as descriptive unless uncertainty analysis supports stronger wording.
- Do not describe Codex audit as independent human validation.
- Freeze any new model-call slice before making calls.
- Keep gold labels, hidden roles, condition labels, family labels, and scorer-only fields out of model-visible prompts.
- Record seeds, selected task IDs, prompt hashes, source file hashes, model IDs, invocation settings, costs, and verification output.
- Prefer decomposition and sensitivity analyses over a single new aggregate score.
- If a data sanity audit finds a P0 issue that changes task meaning or labels, stop paper-facing conclusions until the issue is fixed or explicitly scoped out.
- If the decomposed-schema rerun contradicts the current result, report the contradiction plainly; do not tune the scorer until the old headline comes back.

## Working Questions

Use these questions as the organizing frame:

1. When `belief_correct = true` but `operational_escape = false`, what concrete failure happened?
2. How much of the gap is caused by polluted support, missing clean support, weak evidence selection, duplicate/root-source failure, action failure, or uncertainty discipline?
3. In generated-lore and insufficient rows, are polluted documents being used as clean support, or are they being listed as diagnostic/rejected evidence because the schema gives them no better field?
4. If the schema separates clean support from rejected/diagnostic evidence, does the generated-lore gap remain?
5. Are shortcut baselines competitive because of real shallow template leakage, because the task is intentionally synthetic, or because the scoring view is too forgiving?
6. Are timestamps, dependency edges, pollutant labels, and gold labels internally sane enough to support a paper-facing claim?
7. Given the answers above, what should the paper claim in the abstract, introduction, results, and limitations?

Allowed final claims:

- final-answer accuracy can mask evidence-hygiene and verification failures in this pilot;
- generated-lore / echo-chain tasks expose provenance and source-independence failures under specified scorer contracts;
- the belief/operation gap is a useful diagnostic view, with named schema and scorer sensitivities;
- the artifact supports a validity-first diagnostic pilot, not a production benchmark or stable model leaderboard.

Forbidden final claims:

- proof that models cannot escape polluted open-web environments;
- proof that the belief/operation gap is schema-independent;
- production readiness ranking;
- open-web ecological validity beyond the synthetic pilot;
- independent human validation if only Codex or single-author checks were used.

## Overnight Budget And Runtime Shape

Default overnight target:

```text
planned_wall_clock: 6-10 hours
new_model_calls_target: 120-220
hard_cap_usd: 20.00
primary_models: gpt-5.5, gemini-3.1-pro-preview
optional_budget_model: deepseek-v4-pro, only if existing invocation path is stable and budget remains
seed: 20260525
```

Budget-constrained mode:

```text
planned_wall_clock: 3-5 hours
new_model_calls_target: 64-96
hard_cap_usd: 8.00
primary_models: gpt-5.5, gemini-3.1-pro-preview
conditions: generated_lore, buried_primary, conflicting_evidence
```

Do all no-call analyses first. Do not spend model budget before the decomposition and data sanity scaffolding is in place.

## Output Layout

Use a new immutable output directory:

```text
eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/
```

Expected files:

```text
start_state.md
selection_manifest.json
source_file_hashes.json
failure_decomposition_rows.csv
failure_decomposition_by_model.csv
failure_decomposition_by_condition_family.csv
belief_correct_operational_failure_rows.csv
support_ambiguity_candidate_rows.csv
support_ambiguity_sensitivity_rows.csv
support_ambiguity_sensitivity_summary.csv
positive_evidence_contract_rows.csv
positive_evidence_contract_summary.csv
schema_rerun_plan.json
schema_rerun_prompt_audit.json
schema_rerun_predictions.jsonl
schema_rerun_scored_rows.csv
schema_rerun_by_schema_model.csv
schema_rerun_paired_deltas.csv
shortcut_breakdown_rows.csv
shortcut_breakdown_by_condition_family.csv
shortcut_model_margin_bootstrap.json
data_sanity_audit_rows.csv
data_sanity_audit_summary.json
qualitative_failure_examples.md
paper_reframing_decision.md
run_manifest.json
cost_report.json
verification.json
```

Mirror compact paper-facing summaries into `reports/`:

```text
reports/eha_uncued_core_claim_overnight_results.json
reports/eha-uncued-core-claim-overnight-results-2026-05-25.md
reports/eha-uncued-paper-reframing-decision-2026-05-25.md
```

Suggested implementation files:

```text
eha-mvp/eha/uncued_failure_decomposition.py
eha-mvp/eha/uncued_support_ambiguity.py
eha-mvp/eha/uncued_positive_contract.py
eha-mvp/eha/uncued_data_sanity.py
eha-mvp/eha/uncued_core_claim_report.py
eha-mvp/tests/test_uncued_failure_decomposition.py
eha-mvp/tests/test_uncued_support_ambiguity.py
eha-mvp/tests/test_uncued_positive_contract.py
eha-mvp/tests/test_uncued_data_sanity.py
eha-mvp/tests/test_uncued_core_claim_report.py
```

Add CLI entry points only if needed:

```text
eha-uncued-failure-decomposition
eha-uncued-support-ambiguity
eha-uncued-positive-contract
eha-uncued-data-sanity
eha-report-uncued-core-claim-overnight
eha-verify-uncued-core-claim-overnight
```

## Phase 0: Start State And Existing Gates

Purpose: record the state before edits and prove existing Phase 1 artifacts still verify.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones
git status --short
git log --oneline -8

cd eha-mvp
uv run eha-verify-uncued-phase1 \
  --artifact-dir ../artifact_uncued_phase1 \
  --reports-dir ../reports \
  --out-dir ../reports

uv run eha-verify-uncued-robustness \
  --run-dir results/reports-eha-uncued-robustness-2026-05-25 \
  --reports-dir ../reports

uv run pytest \
  tests/test_uncued_run.py \
  tests/test_uncued_report.py \
  tests/test_uncued_statistics.py \
  tests/test_uncued_examples.py \
  tests/test_uncued_robustness.py \
  -q
```

Deliverable:

```text
eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/start_state.md
```

Acceptance:

- Current branch, latest commits, dirty files, and existing artifact verification are recorded.
- If existing verification fails, stop and write a blocking note before starting new analysis.

## Phase 1: Failure Decomposition From Existing Rows

Purpose: replace the opaque aggregate `operational_escape = false` with concrete failure components.

Inputs:

```text
eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/scored_predictions.csv
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/robustness_rows.csv
eha-mvp/data/uncued-pilot-v1/tasks.jsonl
eha-mvp/data/uncued-pilot-v1/latent_tasks.jsonl
eha-mvp/data/uncued-pilot-v1/gold_labels.jsonl
eha-mvp/data/uncued-pilot-v1/gold_documents.jsonl
eha-mvp/data/uncued-pilot-v1/action_gold.jsonl
eha-mvp/data/uncued-pilot-v1/dependency_edges.jsonl
```

Implement a decomposition that assigns every operational failure one primary failure component plus all applicable secondary tags.

Primary components:

```text
dirty_support
missing_clean_support
empty_support
evidence_value_below_threshold
duplicate_or_same_root_failure
generated_lore_selected
required_action_missing
action_target_mismatch
action_not_executable
uncertainty_discipline_failure
belief_incorrect
parse_or_schema_failure
other_unclassified
```

Secondary tags:

```text
belief_correct_but_operational_failed
insufficient_verdict
supported_or_refuted_verdict
polluted_support_present
clean_support_present
all_support_polluted
support_mentions_primary_source
verification_action_present
verification_action_targets_primary
robustness_variant_row
```

Suggested command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-uncued-failure-decomposition \
  --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --robustness-run-dir results/reports-eha-uncued-robustness-2026-05-25 \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
```

Deliverables:

```text
failure_decomposition_rows.csv
failure_decomposition_by_model.csv
failure_decomposition_by_condition_family.csv
belief_correct_operational_failure_rows.csv
```

Acceptance:

- Every row with `operational_escape = false` has exactly one primary component.
- Every row with `belief_correct = true` and `operational_escape = false` is separately extractable.
- Generated-lore, evidence-selection, and active-verification failures are not collapsed into one bucket.
- `other_unclassified` is below 5 percent of operational failures, or each unclassified case is explained in the report.

Interpretation:

- If most gap rows are `dirty_support`, separation remains a meaningful evidence-hygiene symptom.
- If most gap rows are `evidence_value_below_threshold`, `duplicate_or_same_root_failure`, or `action_target_mismatch`, the paper should avoid presenting the gap as one unified cognitive failure.
- If many rows are `parse_or_schema_failure`, the paper should foreground interface fragility and demote the gap further.

## Phase 2: Support-Field Ambiguity Sensitivity

Purpose: test the strongest objection to the current headline: the model may correctly identify pollution, but the schema leaves no clean place to put reviewed/rejected/diagnostic documents except `supporting_evidence`.

Analyze at least these row classes:

```text
condition = generated_lore
gold_verdict = insufficient
belief_correct = true
operational_escape = false
polluted_support_present = true
```

Create three rescoring views:

```text
strict_current
  Current Phase 1 scorer. Any polluted document in support can fail support cleanliness.

prose_aware_rejected
  If the answer explicitly describes the polluted docs as unsourced, derivative, generated, same-chain, recap, roundup, unverified, circular, or requiring primary-source tracing, classify those docs as diagnostic/rejected rather than clean support.

action_aware_partial
  Same as prose_aware_rejected, plus give partial credit when verification actions explicitly seek primary records, official pages, source repository, original notice, event archive, or independent confirmation.
```

Do not use `prose_aware_rejected` as a new main result without reporting its subjectivity. It is a sensitivity analysis.

Use deterministic candidate extraction first, then a Codex qualitative audit for borderline cases. Codex audit is an internal audit only, not independent human validation.

Suggested command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-uncued-support-ambiguity \
  --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --dataset-dir data/uncued-pilot-v1 \
  --decomposition-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 \
  --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
```

Deliverables:

```text
support_ambiguity_candidate_rows.csv
support_ambiguity_sensitivity_rows.csv
support_ambiguity_sensitivity_summary.csv
qualitative_failure_examples.md
```

Acceptance:

- The report states how many strict failures become passes or partial passes under ambiguity-aware rescoring.
- At least 12 concrete examples are quoted or summarized: 4 strict true failures, 4 likely schema-allocation artifacts, 4 borderline rows.
- The generated-lore belief/operation gap is reported under all three rescoring views.
- The report explicitly says whether the old headline survives, shrinks, or becomes mostly a support-field artifact.

Decision criteria:

- If ambiguity-aware rescoring closes more than half of the generated-lore gap, demote separation strongly and rewrite the paper around polluted-ecology diagnostics.
- If the gap remains large even after ambiguity-aware rescoring, keep the gap as a robust symptom of evidence-hygiene failure, but still avoid calling it schema-independent.
- If the result is mixed by family, present family-specific mechanisms instead of a single global separation claim.

## Phase 3: Positive Evidence-Contract Check

Purpose: make operational escape mean more than "did not put bad docs in support." The paper needs to show whether the model produced a usable evidence contract for each task type.

Define contract metrics:

```text
clean_support_contract
  For supported/refuted packet-judgment rows, the model must cite at least one correct clean support/refutation document and avoid polluted support.

pollutant_rejection_contract
  For insufficient/generated-lore rows, the model must avoid polluted clean support and either identify the pollution reason or propose primary-source tracing.

evidence_selection_contract
  For evidence-selection rows, the selected set must include high-value independent evidence, avoid generated lore, and avoid duplicate/same-root evidence when the task requires independence.

verification_contract
  For active-verification rows, the action must be executable, target the right source class, and recover the missing primary/independent evidence path.

composite_evidence_hygiene_contract
  Family-specific conjunction of the relevant contract fields, reported separately from `operational_escape`.
```

Suggested command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-uncued-positive-contract \
  --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --dataset-dir data/uncued-pilot-v1 \
  --support-ambiguity-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 \
  --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
```

Deliverables:

```text
positive_evidence_contract_rows.csv
positive_evidence_contract_summary.csv
```

Acceptance:

- The paper can distinguish "correct final verdict," "no dirty support," "clean support recovered," "pollutant rejected," and "verification path executable."
- Contract results are reported by family and condition.
- The report identifies whether current `operational_escape` is too permissive, too strict, or directionally right.

## Phase 4: Targeted Decomposed-Schema Rerun

Purpose: test whether the key finding survives a schema that gives the model explicit places for clean support, rejected pollution, diagnostic evidence, refutation evidence, and verification actions.

Schema variants:

```text
current_phase1
  The existing Phase 1 interface.

role_decomposed_v1
  Same task and same answer obligation, but output fields are split:
    final_verdict
    clean_supporting_evidence
    refuting_evidence
    rejected_or_contaminated_evidence
    diagnostic_evidence
    uncertainty_or_insufficiency_reason
    verification_actions
```

Default selection:

```text
source_dataset: eha-mvp/data/uncued-pilot-v1
view: neutral_metadata_visible
latent_task_count: 36
conditions:
  generated_lore: 12
  buried_primary: 8
  conflicting_evidence: 8
  false_consensus: 8
families:
  packet_judgment: prioritize generated_lore and conflicting_evidence
  evidence_selection: include enough rows to test duplicate/root failures
  active_verification: include enough rows to test action mapping
models: gpt-5.5, gemini-3.1-pro-preview
schema_variants: current_phase1, role_decomposed_v1
planned_calls: 36 * 2 * 2 = 144
seed: 20260525
```

Budget-constrained selection:

```text
latent_task_count: 24
conditions:
  generated_lore: 10
  buried_primary: 6
  conflicting_evidence: 4
  false_consensus: 4
models: gpt-5.5, gemini-3.1-pro-preview
schema_variants: current_phase1, role_decomposed_v1
planned_calls: 24 * 2 * 2 = 96
```

Pre-model gates:

| Gate | Requirement |
| --- | --- |
| Frozen selection | Task IDs, view IDs, model list, schema variants, and seed recorded before calls. |
| Prompt isolation | Diff between schema variants changes only output-field contract and necessary instructions. |
| Hidden label audit | 0 hidden role, condition, family, gold verdict, or scorer-field leaks. |
| Cost preflight | Conservative spend projection below hard cap. |
| Pairing | Every `(task, model)` has both schema variants. |
| Output safety | New outputs go only under `reports-eha-uncued-core-claim-overnight-2026-05-25/`. |

Suggested implementation:

- Extend `eha-mvp/eha/uncued_schema_ablation.py` if it already supports the needed schema-variant machinery cleanly.
- Otherwise implement a narrow wrapper for this run in `eha-mvp/eha/uncued_support_ambiguity.py` or `eha-mvp/eha/uncued_core_claim_report.py`.
- Reuse existing prompt builders and hidden-label audit helpers from `uncued_run.py`, `uncued_schema_ablation.py`, and `uncued_robustness.py`.

Suggested commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-plan-uncued-schema-ablation \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 \
  --seed 20260525

uv run eha-run-uncued-schema-ablation \
  --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 \
  --hard-cap-usd 20.00

uv run eha-report-uncued-schema-ablation \
  --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 \
  --reports-dir ../reports
```

If the existing schema-ablation CLI cannot express this design, add a dedicated `eha-run-uncued-core-claim-schema-rerun` command and document it.

Deliverables:

```text
schema_rerun_plan.json
schema_rerun_prompt_audit.json
schema_rerun_predictions.jsonl
schema_rerun_scored_rows.csv
schema_rerun_by_schema_model.csv
schema_rerun_paired_deltas.csv
```

Acceptance:

- Report paired current-vs-decomposed deltas for belief correctness, polluted support rate, clean support recovered, pollutant rejection, and operational/contract success.
- Explicitly test generated-lore rows where current scoring previously produced "belief correct, operational failed."
- Include at least 8 example rows comparing current vs decomposed schema behavior.
- If the decomposed schema materially improves support cleanliness, state that interface design is a first-order experimental variable.
- If the decomposed schema does not improve support cleanliness, state that the failure is less likely to be only support-field ambiguity.

## Phase 5: Shortcut Baseline Breakdown

Purpose: answer whether shallow heuristics explain the current results or only mark the synthetic pilot's boundary.

Inputs:

```text
reports/eha_uncued_baselines_pilot.json
reports/uncued_baseline_rows_pilot.csv
reports/uncued_baseline_aggregate_pilot.csv
eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/scored_predictions.csv
```

Required breakdowns:

```text
baseline_by_condition
baseline_by_family
baseline_by_view
baseline_by_verdict
model_minus_best_shortcut_by_latent_task
model_minus_simple_heuristic_by_condition_family
shortcut_success_examples
shortcut_failure_examples
```

Use latent-task bootstrap for model-vs-shortcut margins.

Suggested command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-score-uncued-baselines \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
```

If the existing baseline command does not produce the breakdowns above, extend it or add the breakdown in `eha-mvp/eha/uncued_core_claim_report.py`.

Deliverables:

```text
shortcut_breakdown_rows.csv
shortcut_breakdown_by_condition_family.csv
shortcut_model_margin_bootstrap.json
```

Acceptance:

- The report names where the simple heuristic is competitive and where it fails.
- The report distinguishes template leakage risk from intentionally diagnostic synthetic structure.
- Paper-facing language says shortcut baselines define a validity boundary, not a solved problem.

## Phase 6: Data Sanity And Label Audit

Purpose: catch errors that could undermine the ecological and provenance claims, especially chronology, synthetic timestamps, dependency edges, and pollutant labels.

Checks:

```text
chronology_consistency
  Claims involving dates/months should not be contradicted by model-visible timestamps unless the timestamp is explicitly synthetic and non-evidential.

gold_verdict_consistency
  Gold verdict should match clean evidence and known pollutants.

pollutant_label_consistency
  Generated lore, derivative summaries, recaps, roundups, and repost chains should be labeled consistently across documents.

dependency_edge_consistency
  Citation/dependency edges should not create impossible roots, cycles where none are intended, or missing referenced IDs.

view_consistency
  Hidden and visible neutral metadata views should differ only by intended metadata visibility.

doc_id_consistency
  All support, gold, dependency, prompt, and scored rows should reference existing document IDs.

action_gold_consistency
  Required active-verification targets should be executable and mapped to the right task IDs.
```

Severity levels:

```text
P0
  Changes task meaning, gold answer, pollutant status, or scorer outcome.

P1
  Confuses paper explanation or ecological interpretation but probably does not change scoring.

P2
  Cosmetic, naming, or documentation inconsistency.
```

Suggested command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-uncued-data-sanity \
  --dataset-dir data/uncued-pilot-v1 \
  --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
```

Deliverables:

```text
data_sanity_audit_rows.csv
data_sanity_audit_summary.json
```

Acceptance:

- All P0 issues are fixed or clearly marked as blockers.
- P1 issues have either a fix, a paper limitation, or a naming change.
- If timestamps are synthetic and non-evidential, rename or document them so the paper does not imply real chronology.
- If the audit is partly heuristic, list false-positive categories.

## Phase 7: Synthesis And Paper Reframing Decision

Purpose: turn the overnight evidence into a concrete paper plan.

Write a final report with these sections:

```text
1. Executive judgment
2. What the old separation claim can still support
3. What the old separation claim cannot support
4. Failure decomposition results
5. Support-field ambiguity sensitivity results
6. Decomposed-schema rerun results
7. Positive evidence-contract results
8. Shortcut baseline and ecological validity boundary
9. Data sanity audit outcome
10. Recommended paper claims
11. Required paper edits
12. Remaining risks before submission
13. Exact commands to reproduce this overnight run
```

Decision table:

| Evidence pattern | Paper decision |
| --- | --- |
| Gap remains under ambiguity-aware scoring and decomposed schema | Keep belief/operation gap as a robust diagnostic symptom, but not the central scientific claim. |
| Gap shrinks substantially under ambiguity-aware scoring | Demote gap strongly; foreground schema sensitivity and polluted-ecology framework. |
| Gap mostly comes from evidence-selection thresholds or active-verification target matching | Stop using a single global gap headline; report family-specific failure modes. |
| Shortcut baselines match model performance in key cells | Narrow claims and frame synthetic task design as a diagnostic stress test with known shortcuts. |
| Data sanity P0 issues exist | Pause paper-facing results until fixed and rerun affected analyses. |
| Decomposed schema improves support hygiene but does not eliminate pollution failures | Claim that interface design matters and polluted-evidence behavior remains partially real. |

Deliverables:

```text
paper_reframing_decision.md
reports/eha_uncued_core_claim_overnight_results.json
reports/eha-uncued-core-claim-overnight-results-2026-05-25.md
reports/eha-uncued-paper-reframing-decision-2026-05-25.md
```

Acceptance:

- The report gives an explicit recommendation: `substantially_reframe`, `minor_reframe`, or `pause_for_repair`.
- The recommendation states which paper sections need changes.
- The report includes exact tables/figures to add or remove.
- It identifies which claims should move to appendix/methods/limitations.

## Phase 8: Verification

Purpose: make the run auditable before handing it back.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run pytest \
  tests/test_uncued_failure_decomposition.py \
  tests/test_uncued_support_ambiguity.py \
  tests/test_uncued_positive_contract.py \
  tests/test_uncued_data_sanity.py \
  tests/test_uncued_core_claim_report.py \
  tests/test_uncued_run.py \
  tests/test_uncued_report.py \
  tests/test_uncued_schema_ablation.py \
  tests/test_uncued_robustness.py \
  -q

uv run eha-verify-uncued-core-claim-overnight \
  --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 \
  --reports-dir ../reports
```

If paper files are edited during the same overnight run:

```bash
cd /Users/chenmohan/gits/ficciones
make pdf
git diff --check
```

Deliverables:

```text
verification.json
```

Acceptance:

- All generated CSV/JSON/MD outputs referenced by the summary exist.
- Prompt audits pass for new model calls.
- Pairing checks pass for schema rerun rows.
- Model-cost report exists if model calls were made.
- Test failures are either fixed or documented as blockers.

## Codex Process Requirements

If running through an external Codex CLI worker, maintain a process file such as:

```text
.codex-workflows/uncued-core-claim-overnight/worker/process.md
```

The worker must update it at least at the end of each phase:

```text
status: working | blocked | delivered
updated: ISO timestamp
current_phase: Phase N
summary: one-paragraph status
files_changed: ...
artifacts_produced: ...
verification: ...
blockers: ...
next_step: ...
```

Do not rely on terminal logs as the primary handoff. The final handoff must point to the run directory and the paper-facing reports.

## Final Handoff Checklist

Before marking the run delivered:

- `git status --short` is recorded.
- All new commands have `--help` output that works.
- No old cued outputs were used.
- New result directory is self-contained.
- `run_manifest.json` includes input hashes, code commit, model calls, seeds, and command history.
- `cost_report.json` exists if model calls were made.
- `verification.json` exists.
- `paper_reframing_decision.md` gives a concrete recommendation.
- The handoff states whether the paper should:
  - demote the belief/operation separation;
  - keep it as a diagnostic view;
  - remove it from abstract/introduction;
  - add failure decomposition;
  - add support-field ambiguity sensitivity;
  - add decomposed-schema rerun results;
  - add shortcut baseline boundaries;
  - repair or qualify data sanity issues.
