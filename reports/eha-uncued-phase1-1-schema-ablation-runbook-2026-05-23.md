# EHA-Uncued Phase 1.1 Schema Ablation Runbook

Date: 2026-05-23

Audience: local Codex agent working in `/Users/chenmohan/gits/ficciones`.

Goal: run a small role-uncued schema ablation over the completed Phase 1 pilot data, isolating whether output-interface structure changes machine-readable evidence hygiene without changing the evidence packet seen by the model.

This is Phase 1.1 follow-up work. It is not part of the Phase 1 main result and must not replace the Phase 1 frontier table.

## Non-Negotiable Rules

- Use only role-uncued data from `eha-mvp/data/uncued-pilot-v1` and, if needed for packaging or verification, `artifact_uncued_phase1`.
- Do not use old cued data, old cued model outputs, `artifact/data/documents_opaque.jsonl`, or `data/epistemic-resilience-v1` as scientific evidence for this ablation.
- Keep the model-visible evidence fixed across schema variants. The controlled intervention is the output schema and schema-specific instructions only.
- Do not add evidence-role labels, condition labels, hidden roles, gold verdicts, semantic IDs, or task-family labels to model-visible prompts.
- Use the same selected task IDs, view, model list, prompt condition, token cap, retry policy, and document-ID policy for all schema variants.
- Run `standard_answer` only for the primary ablation. The hygiene prompt is a separate prompt ablation, not part of this schema ablation.
- Enforce a hard model-call budget cap of USD 5. If projected cost exceeds USD 5, reduce task count before dropping schemas.
- Interpret results as schema/interface sensitivity only. Do not claim general model capability changes or revise the Phase 1 headline result.

## Target Question

Use this as the working question:

> Holding the role-uncued evidence environment fixed, do different structured output schemas change whether models place polluted or insufficient evidence into machine-actionable support fields?

Allowed claims:

- schema/interface wording can change parse success, evidence-field allocation, and operational hygiene metrics on the mini-slice;
- belief correctness and evidence-role discipline may move independently;
- generated-lore and buried-primary rows are useful stress cases for field-level evidence behavior;
- the result is exploratory Phase 1.1 evidence, not the main benchmark result.

Forbidden claims:

- broad model ranking;
- replacement of Phase 1 role-uncued pilot results;
- conclusions from the old cued schema ablation;
- claims that schema wording caused all observed Phase 1 gaps unless the Phase 1.1 data directly supports that narrower claim.

## Scope

Default mini-slice:

```text
source_dataset: eha-mvp/data/uncued-pilot-v1
conditions: generated_lore, buried_primary
source_task_count: 16
tasks_per_condition: 8
view: neutral_metadata_visible
prompt_condition: standard_answer
models: gpt-5.5, gemini-3.1-pro-preview
schemas: current, clarified, minimal, diagnostic_no_hygiene
hard_cap_usd: 5.00
seed: 20260523
```

Task count means unique source tasks before view expansion. The default uses one view to keep the ablation focused on schema effects and under the USD 5 cap. If both views are run, analyze them separately and reduce source task count first.

Minimum acceptable run:

```text
conditions: generated_lore, buried_primary
source_task_count: 10
tasks_per_condition: 5
models: one of gpt-5.5 or gemini-3.1-pro-preview
schemas: current, clarified, minimal, diagnostic_no_hygiene
hard_cap_usd: 5.00
```

Do not drop `current`; it is the comparison anchor.

## Schema Variants

Use these labels exactly in manifests and output tables:

| Variant | Purpose | Required output fields |
| --- | --- | --- |
| `current` | Phase 1 production interface, used as the comparison anchor. | `claim_verdict`, `confidence`, `supporting_evidence`, `rejected_evidence`, `selected_doc_ids`, `actions`, `evidence_environment_assessment`, `answer` |
| `clarified` | Separates clean support, refutation, rejected/polluted, and diagnostic evidence. | `claim_verdict`, `confidence`, `clean_supporting_evidence`, `refuting_evidence`, `rejected_or_contaminated_evidence`, `diagnostic_evidence`, `selected_doc_ids`, `actions`, `evidence_notes`, `answer` |
| `minimal` | Tests whether field separation itself matters by collapsing evidence roles. | `claim_verdict`, `confidence`, `evidence_doc_ids`, `selected_doc_ids`, `evidence_notes` |
| `diagnostic_no_hygiene` | Keeps diagnostic/rejection fields but removes extra hygiene policy language. | `claim_verdict`, `confidence`, `supporting_evidence`, `rejected_or_contaminated_evidence`, `diagnostic_evidence`, `selected_doc_ids`, `actions`, `evidence_notes`, `answer` |

Naming note: Phase 1 run manifests used `schema_variant=clarified` for the production run. For Phase 1.1, call that production interface `current` to avoid confusing it with the new role-separated `clarified` variant.

## Expected Commands

Implement these commands if they do not exist yet. Keep names close to these so reports are reproducible.

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-plan-uncued-schema-ablation --help
uv run eha-run-uncued-schema-ablation --help
uv run eha-report-uncued-schema-ablation --help
uv run eha-verify-uncued-schema-ablation --help
```

Suggested module and test names:

```text
eha-mvp/eha/uncued_schema_ablation.py
eha-mvp/tests/test_uncued_schema_ablation.py
```

Existing `eha.epistemic_generated_lore_audit` code may be reused as an implementation pattern for schema builders, parsers, and role-row scoring. It must not be used as an input data source for this run.

## Output Layout

Use this layout unless the existing implementation strongly suggests a better local convention.

```text
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/selection_manifest.json
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/schema_manifest.json
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/run_manifest.json
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/predictions.jsonl
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/prompt_audit_summary.json
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/stored_hidden_label_audit.json
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/cost_report.json
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/schema_ablation_rows.csv
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/schema_ablation_by_schema_model.csv
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/schema_ablation_by_schema_model_condition.csv
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/schema_ablation_by_schema_model_family.csv
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/schema_ablation_report.md
reports/eha_uncued_schema_ablation_results.json
reports/eha-uncued-schema-ablation-results-2026-05-23.md
```

Do not copy results into `artifact_uncued_phase1` unless a later packaging step explicitly creates a Phase 1.1 artifact. Phase 1.1 outputs should remain visibly separate from the Phase 1 package.

## Gate Summary

The local agent must stop before model calls unless all pre-model gates pass.

| Gate | Pass Requirement |
| --- | --- |
| Data source | `selection_manifest.json` references only `eha-mvp/data/uncued-pilot-v1`. |
| Role-uncued contract | Phase 1 leakage, shortcut-baseline, and human-review reports are present and passing. |
| Task selection | Selected rows are only `generated_lore` and `buried_primary`, with frozen task IDs and seed. |
| Prompt parity | For a given task/model/view, prompts differ only by schema object and schema-specific policy. |
| Visible prompt audit | 0 hidden field hits, 0 semantic doc ID hits, 0 semantic citation hits, 0 condition/family label hits. |
| Stored prompt audit | 0 hidden role, gold verdict, condition, or semantic-ID markers in stored prompt JSON. |
| Cost preflight | Planned calls fit inside USD 5 hard cap using conservative output-token estimates. |
| Current anchor | `current` rows exist for every selected task/model/view pair or the run is blocked. |

## Phase 0: Repository Baseline

Purpose: record the starting state and ensure Phase 1 is the only data dependency.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones
git status --short
cd eha-mvp
uv run pytest tests/test_uncued_run.py tests/test_uncued_report.py tests/test_uncued_scorer_audit.py -q
cd ..
```

Deliverables:

```text
reports/eha-uncued-schema-ablation-start-state-2026-05-23.md
```

Acceptance:

- Report lists branch, dirty files, test status, and any unrelated failures.
- Report states that old cued artifacts are excluded from this ablation.

## Phase 1: Freeze The Task Slice

Purpose: make task selection reproducible and prevent result-shopping.

Selection rules:

- Load task metadata from `eha-mvp/data/uncued-pilot-v1/latent_tasks.jsonl`.
- Select only `condition in {"generated_lore", "buried_primary"}`.
- Default to 8 tasks per condition using seed `20260523`.
- Stratify each condition as `packet_judgment=3`, `evidence_selection=3`, `active_verification=2`.
- If running the 10-task minimum, stratify each condition as `packet_judgment=2`, `evidence_selection=2`, `active_verification=1`.
- Freeze exact task IDs in `selection_manifest.json` before any model calls.

Example command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-plan-uncued-schema-ablation \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 \
  --conditions generated_lore,buried_primary \
  --tasks-per-condition 8 \
  --view neutral_metadata_visible \
  --seed 20260523
```

Acceptance:

- `selection_manifest.json` includes task IDs, conditions, families, selected view, seed, and dataset file digests.
- No model-visible prompt contains `generated_lore`, `buried_primary`, `packet_judgment`, `evidence_selection`, or `active_verification`.

## Phase 2: Define Schemas And Parsers

Purpose: make variants explicit and machine-checkable.

Actions:

- Implement JSON schema builders for `current`, `clarified`, `minimal`, and `diagnostic_no_hygiene`.
- Implement one parser per schema, with shared first-JSON-object fallback only if provider-native schema enforcement fails.
- Normalize doc IDs after parsing using the same opaque-to-audit mapping as Phase 1.
- Record `schema_missing`, `empty_output`, `parse_success`, output token counts, and response format.

Acceptance:

- Unit tests assert every schema is `additionalProperties=false`.
- Unit tests assert each parser rejects missing required fields.
- Unit tests assert `current` exactly matches the Phase 1 production output contract except for the manifest label.

## Phase 3: Build Prompt Composer

Purpose: isolate schema effects from evidence effects.

Rules:

- Use the same task question, document list, document order, opaque doc IDs, and visible citations for all schemas.
- Use the same base policy for all schemas.
- Only append schema-specific field instructions needed to explain the output contract.
- Do not include hidden condition, hidden role, gold verdict, family, or score fields in prompt payload.
- Do not include old cued examples or old cued audit text.

Acceptance:

- A prompt-diff test confirms non-schema prompt content is identical across variants for the same task/view.
- Prompt audits pass before any model calls.
- Stored prompt JSON includes a `schema_variant` field for audit metadata, but that metadata is not inside the model-visible message content.

## Phase 4: Cost And Dry-Run Preflight

Purpose: catch schema and budget failures before spending model calls.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-run-uncued-schema-ablation \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 \
  --models gpt-5.5,gemini-3.1-pro-preview \
  --schemas current,clarified,minimal,diagnostic_no_hygiene \
  --prompt standard_answer \
  --view neutral_metadata_visible \
  --dry-run \
  --hard-cap-usd 5
```

Acceptance:

- Dry run reports planned call count, selected tasks, prompt-token estimates, output-token cap, and projected cost.
- Planned cost is below USD 5 using conservative estimates.
- If projected cost exceeds USD 5, reduce to 10 source tasks before dropping to one model.

## Phase 5: Model Run

Purpose: run paired schema calls under the fixed mini-slice.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-run-uncued-schema-ablation \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 \
  --models gpt-5.5,gemini-3.1-pro-preview \
  --schemas current,clarified,minimal,diagnostic_no_hygiene \
  --prompt standard_answer \
  --view neutral_metadata_visible \
  --max-output-tokens 4096 \
  --parallel-models 2 \
  --resume \
  --soft-cap-usd 4 \
  --hard-cap-usd 5 \
  --abort-cap-usd 6
```

Acceptance:

- `run_manifest.json` records selected tasks, models, schemas, view, prompt, retry policy, token caps, provider response formats, and budget caps.
- `predictions.jsonl` has one row per planned call, unless a budget abort is explicitly recorded.
- No schema variant is partially missing while others complete for the same model/task pair, except for documented budget aborts.

Failure handling:

- If one provider fails before spending substantial budget, finish the other provider and mark the failed provider as unavailable.
- If parse failures cluster in one schema, keep the failures in the table; do not silently repair away schema sensitivity.
- If the budget aborts, report the run as incomplete and do not make schema-comparison claims from partial paired rows.

## Phase 6: Score Schema Rows

Purpose: score field-level evidence behavior in a way comparable across schemas.

Use hidden gold only inside the scorer. Hidden gold must not enter prompts.

Core row metrics:

```text
parse_success
empty_output
schema_missing
belief_correctness
insufficient_verdict
primary_selected
primary_in_support
polluted_in_support
polluted_rejected
polluted_diagnostic
dual_role_pollutant
action_search_primary
action_trace_source
role_escape
operational_escape_proxy
```

Field mapping:

- `current`: support = `supporting_evidence`; rejection = `rejected_evidence`; diagnostic = blank.
- `clarified`: support = `clean_supporting_evidence`; rejection = `rejected_or_contaminated_evidence`; diagnostic = `diagnostic_evidence`.
- `minimal`: support = `evidence_doc_ids`; rejection and diagnostic are blank by design.
- `diagnostic_no_hygiene`: support = `supporting_evidence`; rejection = `rejected_or_contaminated_evidence`; diagnostic = `diagnostic_evidence`.

Condition-specific interpretation:

- For `generated_lore`, the key field failure is polluted/generated evidence appearing in support fields.
- For `buried_primary`, the key field failure is missing clean primary support or relying on pollutant/pseudo-consensus support when a clean primary exists.
- For active-verification rows, action quality must be scored separately from evidence field allocation.

Acceptance:

- Scoring produces row-level CSV and aggregate CSVs by schema/model/condition/family.
- Metrics unavailable by schema design are blank or explicitly `not_applicable`; do not coerce them to zero.
- Paired comparisons use only complete schema sets for a given task/model/view.

## Phase 7: Manual Audit

Purpose: make sure the scorer is not over-interpreting schema artifacts.

Audit sample:

- Minimum 16 rows if the full default run completes.
- Include both conditions.
- Include every schema.
- Include at least one parse failure if any occurred.
- Include at least four rows where verdict is correct but support-field hygiene fails.

Audit questions:

- Is the semantic verdict correct?
- Does the schema make polluted evidence machine-actionable as support?
- Is a polluted document both rejected/diagnostic and used as support?
- For buried-primary rows, did the model select or use the clean primary evidence?
- For active-verification rows, would the listed action actually reduce uncertainty?

Acceptance:

- Manual audit agreement is recorded in `schema_ablation_report.md`.
- Any scorer bug found in audit is fixed and all schema rows are rescored.

## Phase 8: Report

Purpose: produce a narrow result that can be cited without overstating it.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-report-uncued-schema-ablation \
  --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 \
  --reports-dir ../reports

uv run eha-verify-uncued-schema-ablation \
  --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 \
  --reports-dir ../reports
```

Required report sections:

- scope and non-use of cued data;
- selected tasks, views, models, schemas, prompt condition, call count, and cost;
- prompt audit and stored hidden-label audit;
- parse success and schema-missing rates;
- row-level evidence-role metrics;
- paired schema comparison by condition;
- manual audit summary;
- reporting boundary for paper text.

Acceptance:

- `reports/eha-uncued-schema-ablation-results-2026-05-23.md` says this is Phase 1.1 exploratory evidence.
- It does not revise the Phase 1 main table.
- It does not cite old cued model outputs as evidence.
- It states exact task count, model count, schemas, and budget actually used.

## Paper Integration Rule

If Phase 1.1 completes, the paper may say:

> In a small role-uncued Phase 1.1 ablation over generated-lore and buried-primary rows, we held evidence fixed and varied only the structured output interface. Results suggest that schema design changes machine-readable evidence-role allocation, so schema wording should be treated as an experimental factor rather than a neutral logging detail.

The paper must also say:

- this ablation is exploratory;
- it is not the basis of the main benchmark result;
- old cued schema-ablation results remain quarantined and are not used as evidence.

If Phase 1.1 does not run, keep the existing paper language: schema/interface analysis is planned follow-up only.

## Final Acceptance Checklist

- `selection_manifest.json` freezes role-uncued task IDs before model calls.
- All prompts pass leakage audits.
- All four schemas are represented in complete paired rows.
- USD 5 hard cap is enforced.
- Results are separated from Phase 1 outputs.
- Report explicitly says no old cued data or cued outputs were used.
- Report claims only schema/interface sensitivity, not replacement of the Phase 1 result.

## Execution Status: Complete Through Phase 8

Status date: 2026-05-23

Phases 0-8 are complete. The main two-model schema-ablation run initially produced two transient Gemini 429 failure rows; both were resolved by a targeted `--retry-failed` pass. The scored report uses the latest record for each schema/model/task/prompt key: 128 latest rows from 130 raw records, with 128/128 latest parse successes. A supplemental DeepSeek-only documented retry is complete in a separate directory and is not part of the main paired GPT/Gemini schema-ablation table.

Completed artifacts:

- Phase 0 start state: `reports/eha-uncued-schema-ablation-start-state-2026-05-23.md`.
- Phase 1 task selection: `eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/selection_manifest.json`.
- Phase 2 schema manifest: `eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/schema_manifest.json`.
- Phase 3 prompt parity audit: `eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/prompt_parity_audit.json`.
- Phase 4 dry-run preflight: `eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/run_manifest.json`, `dry_run_cost_projection.json`, and `cost_report.json`.
- Phase 5 main run artifacts: `eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/predictions.jsonl`, `run_manifest.json`, `prompt_audit_summary.json`, `stored_hidden_label_audit.json`, and `cost_report.json`.
- Phase 6 scoring outputs: `schema_ablation_rows.csv`, `schema_ablation_by_schema_model.csv`, `schema_ablation_by_schema_model_condition.csv`, and `schema_ablation_by_schema_model_family.csv`.
- Phase 7 manual audit: `schema_ablation_manual_audit.csv`.
- Phase 8 report and verifier: `schema_ablation_report.md`, `reports/eha_uncued_schema_ablation_results.json`, `reports/eha-uncued-schema-ablation-results-2026-05-23.md`, and `reports/eha_uncued_schema_ablation_verification.json`.
- Paper integration: `paper/sections/08_schema_interface.tex`, `paper/sections/10_limitations.tex`, `paper/sections/13_conclusion.tex`, and rebuilt `paper/main.pdf`.
- Supplemental DeepSeek-only retry: `reports/eha-uncued-schema-ablation-deepseek-retry-2026-05-23.md`, `reports/eha_uncued_schema_ablation_deepseek_retry.json`, and `eha-mvp/results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23/`.
- Command implementation: `eha-mvp/eha/uncued_schema_ablation.py`, `eha-mvp/tests/test_uncued_schema_ablation.py`, and `eha-mvp/pyproject.toml`.

Phase 0 evidence:

- Branch: `codex/add-reality-testing-benchmarks`.
- Dirty files recorded before Phase 0 commit: modified `reports/eha-uncued-schema-ablation-plan-2026-05-22.md` and untracked `reports/eha-uncued-phase1-1-schema-ablation-runbook-2026-05-23.md`.
- Phase 1 role-uncued pilot data boundary confirmed: `eha-mvp/data/uncued-pilot-v1`.
- Old cued artifacts excluded: yes.
- Pilot leakage gate inherited from Phase 1: passed.
- Pilot shortcut baselines inherited from Phase 1: passed.
- Pilot surface review inherited from Phase 1: passed.
- Baseline test command: `uv run pytest tests/test_uncued_run.py tests/test_uncued_report.py tests/test_uncued_scorer_audit.py -q`.
- Baseline test result: 6 passed in 0.44s.

Phase 1 task-slice evidence:

- Command: `uv run eha-plan-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --conditions generated_lore,buried_primary --tasks-per-condition 8 --view neutral_metadata_visible --seed 20260523`.
- Source task count: 16.
- Selected view: `neutral_metadata_visible`.
- Seed: 20260523.
- Conditions: 8 `generated_lore`, 8 `buried_primary`.
- Per-condition family split: 3 packet judgment, 3 evidence selection, 2 active verification.
- Selected task IDs: `uncued_048`, `uncued_049`, `uncued_051`, `uncued_052`, `uncued_054`, `uncued_055`, `uncued_056`, `uncued_058`, `uncued_037`, `uncued_039`, `uncued_040`, `uncued_041`, `uncued_042`, `uncued_045`, `uncued_046`, `uncued_047`.
- Old cued data used: false.
- Selection manifest hash: `84c6dc89077a429d5ecda1d543d294df2b4db2336ecd4bee6364313a0de3e3c0`.

Phase 2 schema/parser evidence:

- Schema variants implemented with exact labels: `current`, `clarified`, `minimal`, `diagnostic_no_hygiene`.
- `current` uses the Phase 1 production contract under the Phase 1.1 label.
- Every schema has `additionalProperties=false`.
- Parser tests reject missing required fields for every schema.
- Schema manifest hash: `8c9cbc95b386cf7f9f6b4b4f33b6fe59e3d6a06b3be84652ae442253540cee1b`.

Phase 3 prompt-composer evidence:

- Prompt composer uses the same question, document list, document order, opaque doc IDs, visible citations, and base policy across schema variants.
- Model-visible prompt payload omits condition labels, family labels, hidden roles, gold verdicts, and semantic document IDs.
- Prompt parity audit: passed.
- Prompt parity failure count: 0.
- Prompt audit failure count: 0.
- Prompt parity audit hash: `a3f2c689734e95bb5767616321a065c116710e3d372cedd40692d0d16f235646`.

Phase 4 dry-run preflight evidence:

- Command: `uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --models gpt-5.5,gemini-3.1-pro-preview --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --dry-run --hard-cap-usd 5`.
- Planned calls: 128 = 16 selected tasks x 2 models x 4 schemas x 1 prompt.
- Models: `gpt-5.5`, `gemini-3.1-pro-preview`.
- Schemas: `current`, `clarified`, `minimal`, `diagnostic_no_hygiene`.
- Prompt condition: `standard_answer`.
- View: `neutral_metadata_visible`.
- Max output tokens: 4096.
- Conservative output-token cost estimate: 900.
- Projected cost: USD 2.198226.
- Hard cap: USD 5.
- Abort cap: USD 6.
- Dry-run status: not aborted.
- Note: the dry-run `run_manifest.json` hash below records the pre-Phase-5 dry-run state. The same path is intentionally overwritten by the actual Phase 5 run manifest after model execution.
- Dry-run run manifest hash: `7a87ae4b330513d247ca1b286662b231a2a5a4cd9ebf5e11894f854c22191ac1`.
- Dry-run cost projection hash: `5c6f9166c2655af4185b73e4fefa0a7c628f762051cf63cd6ee0b506b8b411da`.
- Dry-run cost report hash: `caaed9d8f2719a1c3a213cdda783d8c6fb0296dbf3762cfd975a93fdd31a4ec2`.

Phase 5 main-run evidence:

- Command: `uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --models gpt-5.5,gemini-3.1-pro-preview --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --max-output-tokens 4096 --parallel-models 2 --resume --soft-cap-usd 4 --hard-cap-usd 5 --abort-cap-usd 6`.
- Targeted retry command: `uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --models gpt-5.5,gemini-3.1-pro-preview --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --max-output-tokens 4096 --cost-estimate-output-tokens 900 --parallel-models 1 --max-attempts 2 --resume --retry-failed --soft-cap-usd 4 --hard-cap-usd 5 --abort-cap-usd 6`.
- Planned calls: 128.
- Raw records after targeted retry: 130.
- Unique latest records: 128.
- Latest parse successes: 128.
- Latest parse failures: 0.
- Budget status: not aborted.
- Record cost: USD 1.890321.
- Spent: USD 1.890321.
- Targeted retry spend: USD 0.005380.
- Hard cap: USD 5.
- Prompt audit: passed; semantic doc ID hits 0, visible citation hits 0, audit-ID title/body hits 0, hidden-field hits 0.
- Stored hidden-label audit: passed; prompt hits 0, output hits 0.
- `gpt-5.5`: 64/64 parse success.
- `gemini-3.1-pro-preview`: 64/64 latest parse success.
- Gemini retry items:
  - `uncued_046_visible`, schema `diagnostic_no_hygiene`, initial `RateLimitError` 429 after 2 attempts; retry parsed successfully on attempt 1.
  - `uncued_047_visible`, schema `current`, initial `RateLimitError` 429 after 2 attempts; retry parsed successfully on attempt 1.
- Phase 5 current run manifest hash: `de5349eef3fa41d6075e577fb618ed4304e3846fbe2869bd1f6e831412f45685`.
- Phase 5 invocation profile hash: `37346db63d3e92220d5faa008109dd94c82006ccccb7cb08c8497117d9ed4702`.
- Phase 5 predictions hash: `89e630413285c516efc14a65e33d58148a7b8a757d7bfed81873bbbd5ff54b0e`.
- Phase 5 prompt audit hash: `3d752d16d8da302567e9365f6e3eb4092307c8a8e55527639c077051b29f3a84`.
- Phase 5 stored hidden-label audit hash: `5069bd02061d2ff590349a12f9cb2922f62f106081445609195fb2c80e845156`.
- Phase 5 cost report hash: `033b3bca0d881c3925b25c298b9cca32f43f452847d024330b0b1473d49b5b51`.

Phase 6 scoring evidence:

- Command: `uv run eha-report-uncued-schema-ablation --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --reports-dir ../reports`.
- Scored rows: 128 latest rows from 130 raw records.
- Models: `gpt-5.5`, `gemini-3.1-pro-preview`.
- Schemas: `current`, `clarified`, `minimal`, `diagnostic_no_hygiene`.
- Complete schema/model/task groups: 32 complete, 0 incomplete.
- Minimal schema: polluted-in-support rate 1.000 and role-escape rate 0.000 for both models in this slice.
- Current and clarified schemas: polluted-in-support rate 0.000 for both models in this slice.
- `diagnostic_no_hygiene`: mixed role-allocation behavior; `gpt-5.5` role escape 0.500, `gemini-3.1-pro-preview` role escape 1.000.
- Scored rows hash: `d83c5f083f6c809aca6b0fb053c1b649d03400232251d0897900b3bd53b14db2`.
- By schema/model hash: `cd09eeca4cb1d68132206986e8d117a22ab54d14f07d2d265d123b313643f2e2`.
- By schema/model/condition hash: `eba0fa014fd86b8ccfe074d628eeecda2e4f7eafadb5c515764b2348351b470f`.
- By schema/model/family hash: `5a8b2ffbabb1f6f460857a92226f1d3d308b2d4d2b1f4acca81bce70a1dcd39d`.

Phase 7 manual-audit evidence:

- Audit mode: local Codex-assisted manual schema-ablation audit.
- Reviewed rows: 16.
- Scorer fixes needed: 0.
- Independent human review: false.
- Manual audit hash: `951db080fd1a37ab813ffd087d28aad317e5ba963d502e49e832da56b23b169f`.

Phase 8 report and verification evidence:

- Report command: `uv run eha-report-uncued-schema-ablation --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --reports-dir ../reports`.
- Verify command: `uv run eha-verify-uncued-schema-ablation --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --reports-dir ../reports`.
- Verification decision: pass.
- Verification gates passing: data source role-uncued, Phase 1 gates present/passing, selected conditions only, prompt audit passed, stored hidden-label audit passed, cost under hard cap, current anchor complete, all latest rows parse-successful, all schemas represented, results separated from Phase 1 artifact, report boundary present, and no old-cued evidence claim.
- Result report hash: `1d5f4803776bc4529c4209b6875de9f3c30e6bede468e7bade9e30bf28d124f3`.
- Result JSON hash: `f68cf4c4ac1e57968e153fcca6af9a0bc621f85f04c8be9bd184a498f050ebc9`.
- Verification JSON hash: `db3281c69f4b1cd1db4e6fee22cca9a5457b747f2ca56db3901bea2da0dea62f`.
- Allowed paper claim: exploratory Phase 1.1 schema/interface sensitivity only; not a replacement for the Phase 1 result and not evidence from old cued outputs.

Paper integration evidence:

- Updated `paper/sections/08_schema_interface.tex` to describe the completed Phase 1.1 ablation as exploratory follow-up evidence.
- Updated `paper/sections/10_limitations.tex` to limit the ablation to 16 source tasks, one visible view, two main models, and a local Codex-assisted audit.
- Updated `paper/sections/13_conclusion.tex` to treat schema/interface choices as experimental factors.
- Rebuilt `paper/main.pdf` with `make` in `paper/`; Tectonic completed with only the existing bibliography underfull-box warning.
- `paper/sections/08_schema_interface.tex` hash: `d45bd1718ae5ec5fc15d0f4631508624cba0f09058bf96d7d80ac7bac55149c6`.
- `paper/sections/10_limitations.tex` hash: `89877345d4450d8d77891e38f9f8044ebfe4a06ed83ea1dfcb6d55a35d3754b8`.
- `paper/sections/13_conclusion.tex` hash: `c9d63af613bded1f1d3f9adc21406198f46b28517aa48a549314de15b74506b7`.
- `paper/main.pdf` hash: `9451f402ac9bd9ce02a77d53bbedaf1b3ceb5be54d3a22f8a7f3b6eb494acfd0`.

Supplemental DeepSeek-only documented retry:

- Status: pass as a supplemental retry; not part of the main paired GPT/Gemini schema-ablation table.
- Report: `reports/eha-uncued-schema-ablation-deepseek-retry-2026-05-23.md`.
- Machine-readable summary: `reports/eha_uncued_schema_ablation_deepseek_retry.json`.
- Run directory: `eha-mvp/results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23`.
- Retry model: `deepseek-v4-pro`.
- Invocation profile artifact: `invocation_profiles.json`.
- Invocation profile: `response_format=json_object`, `max_completion_tokens=4096`, temperature omitted, `json_extractor=first_json_object`, developer/system merged into user, LLM repair disabled, max attempts 2, timeout 240 seconds, parallel model streams 1.
- Planned calls: 64.
- Actual records: 64.
- Parse successes: 64.
- Parse failures: 0.
- Empty outputs: 0.
- Schema-missing rows: 0.
- Second-attempt rows: 1 (`uncued_045_visible`, schema `clarified`, final row parsed successfully).
- Prompt audit: passed.
- Stored hidden-label audit: passed.
- Projected cost: USD 0.132106.
- Record cost: USD 0.264305.
- Spent: USD 0.269407.
- Hard cap: USD 2.
- DeepSeek retry predictions hash: `3d8da592ac29fd59b31161b0af7ac7ef88e0a6586cacbd6503a485c0c8a313ca`.
- DeepSeek retry invocation profile hash: `6b09088ef7895c6b5437f35f7cd77fddf0ffbb44f873e33bc67391e09b441e3d`.
- DeepSeek retry run manifest hash: `4a916f76b540d68beade6291d19da0a395228d33360395623696ff90d5cf13e8`.
- DeepSeek retry cost report hash: `04512b20d95996a650eedee894584f778b2d6b0772a3d1216884f967d8a49919`.

Commands verified:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-plan-uncued-schema-ablation --help
uv run eha-run-uncued-schema-ablation --help
uv run eha-report-uncued-schema-ablation --help
uv run eha-verify-uncued-schema-ablation --help
uv run pytest tests/test_uncued_schema_ablation.py -q
# 12 passed in 0.70s
uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --models gpt-5.5,gemini-3.1-pro-preview --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --dry-run --hard-cap-usd 5
uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --models gpt-5.5,gemini-3.1-pro-preview --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --max-output-tokens 4096 --parallel-models 2 --resume --soft-cap-usd 4 --hard-cap-usd 5 --abort-cap-usd 6
uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --models gpt-5.5,gemini-3.1-pro-preview --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --max-output-tokens 4096 --cost-estimate-output-tokens 900 --parallel-models 1 --max-attempts 2 --resume --retry-failed --soft-cap-usd 4 --hard-cap-usd 5 --abort-cap-usd 6
uv run eha-report-uncued-schema-ablation --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --reports-dir ../reports
uv run eha-verify-uncued-schema-ablation --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --reports-dir ../reports
uv run eha-plan-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23 --conditions generated_lore,buried_primary --tasks-per-condition 8 --view neutral_metadata_visible --seed 20260523
uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23 --models deepseek-v4-pro --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --dry-run --hard-cap-usd 2 --soft-cap-usd 1 --abort-cap-usd 3 --max-output-tokens 4096 --cost-estimate-output-tokens 900 --parallel-models 1 --max-attempts 2
uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23 --models deepseek-v4-pro --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --max-output-tokens 4096 --cost-estimate-output-tokens 900 --parallel-models 1 --max-attempts 2 --resume --soft-cap-usd 1 --hard-cap-usd 2 --abort-cap-usd 3
cd /Users/chenmohan/gits/ficciones/paper && make
```

Final acceptance status:

- Selection manifest was frozen before model calls.
- Prompt audits passed.
- All four schemas are represented in complete paired latest rows.
- Main run stayed under the USD 5 hard cap.
- Results are separated from Phase 1 outputs.
- The report says no old cued data or outputs are used.
- The report claims only schema/interface sensitivity, not replacement of the Phase 1 result.
- Phase 1.1 is complete through Phase 8.
