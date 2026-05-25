# EHA-Uncued Phase 1.3 Robustness Mini-Suite Runbook

Date: 2026-05-25

Audience: local Codex agent working in `/Users/chenmohan/gits/ficciones`.

Goal: run a small paired robustness suite for the role-uncued pilot, testing whether the core belief-vs-evidence-hygiene finding survives controlled perturbations to evidence order, metadata, prompt wording, and citation visibility.

This is a robustness check, not a new leaderboard. It should support or narrow the paper's diagnostic claim.

## Non-Negotiable Rules

- Use only role-uncued data from `eha-mvp/data/uncued-pilot-v1`.
- Do not use old cued artifacts or old cued outputs.
- Freeze the task slice before model calls.
- Use paired comparisons: for each `(task, model)`, compare `baseline_original` with each perturbation.
- Change only one presentation factor per variant.
- Keep gold labels, hidden roles, condition labels, and scorer-only fields out of model-visible prompts.
- Keep the schema fixed to the Phase 1 main interface unless the run explicitly states otherwise.
- Do not treat robustness rows as replacements for Phase 1 main results.
- Enforce a hard budget cap and stop before partial unpaired claims are produced.

## Target Question

Use this working question:

> Holding the task and scorer fixed, do the main role-uncued evidence-hygiene findings persist under small changes to presentation order, neutral metadata, prompt wording, and citation visibility?

Allowed claims:

- the core generated-lore belief/operation gap persists or changes under specific perturbations;
- a perturbation exposes sensitivity to a presentation feature;
- the Phase 1 main result is robust to a named mini-suite, if paired deltas support that claim.

Forbidden claims:

- broad model ranking;
- production robustness;
- open-web validity;
- proof that no prompt/schema/order artifact exists;
- replacement of Phase 1 main tables.

## Default Scope

Default full mini-suite:

```text
source_dataset: eha-mvp/data/uncued-pilot-v1
source_task_count: 20
conditions:
  generated_lore: 5
  buried_primary: 5
  conflicting_evidence: 5
  false_consensus: 5
families_per_condition:
  packet_judgment: 2
  evidence_selection: 2
  active_verification: 1
view: neutral_metadata_visible
models: gpt-5.5, gemini-3.1-pro-preview
schema_variant: current_phase1_interface
prompt_condition: standard_answer
variants:
  baseline_original
  order_randomized
  source_type_masked
  prompt_paraphrase
  citation_masked
seed: 20260525
planned_calls: 20 * 2 * 5 = 200
hard_cap_usd: 7.00
```

Budget-constrained minimum:

```text
source_task_count: 12
conditions:
  generated_lore: 4
  buried_primary: 4
  conflicting_evidence: 2
  false_consensus: 2
models: gpt-5.5, gemini-3.1-pro-preview
variants:
  baseline_original
  order_randomized
  source_type_masked
  prompt_paraphrase
planned_calls: 12 * 2 * 4 = 96
hard_cap_usd: 5.00
```

Do not drop `baseline_original`; every perturbation must be paired against a same-suite baseline.

## Perturbation Definitions

### `baseline_original`

Rebuild prompts from the frozen source tasks using the normal Phase 1 role-uncued prompt composer. This is the within-suite anchor. Prefer rerunning it instead of reusing old Phase 1 outputs because provider behavior and invocation code can change over time.

### `order_randomized`

Shuffle document order within each task using the suite seed and task ID. Preserve document contents, doc IDs, titles, source types, timestamps, and citations.

Purpose: test whether the model/scorer result depends on primary or polluted documents appearing in a fixed position.

### `source_type_masked`

Replace all model-visible `source_type` values with a neutral value such as `document`. Preserve title, timestamp, body, doc IDs, and citations.

Purpose: test whether neutral source-type metadata is acting as a shortcut.

### `prompt_paraphrase`

Use the same schema and evidence packet but replace the base policy wording with a semantically equivalent paraphrase. Keep output fields identical.

Purpose: test whether core effects depend on one brittle prompt phrasing.

Example paraphrase constraints:

- still require JSON only;
- still require doc IDs exactly as given;
- still forbid chain-of-thought;
- still require evidence fields and actions;
- do not add extra hygiene instructions beyond the Phase 1 main condition.

### `citation_masked`

Remove or replace visible citations with opaque non-relational placeholders, while preserving document text.

Purpose: stress-test dependence on citation graph surface structure.

Important interpretation boundary: citation relations are legitimate evidence in some tasks. If this perturbation reduces operational escape, report it as evidence that citation/dependency information is task-relevant, not as a benchmark failure by itself.

## Expected Commands

Implement these commands if they do not already exist:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-plan-uncued-robustness --help
uv run eha-run-uncued-robustness --help
uv run eha-report-uncued-robustness --help
uv run eha-verify-uncued-robustness --help
```

Suggested implementation files:

```text
eha-mvp/eha/uncued_robustness.py
eha-mvp/tests/test_uncued_robustness.py
```

Reuse existing helpers from:

```text
eha-mvp/eha/uncued_run.py
eha-mvp/eha/uncued_schema_ablation.py
eha-mvp/eha/epistemic_resilience.py
```

but do not mutate Phase 1 or Phase 1.1 outputs.

## Output Layout

Use:

```text
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/selection_manifest.json
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/perturbation_manifest.json
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/dry_run_cost_projection.json
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/run_manifest.json
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/invocation_profiles.json
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/predictions.jsonl
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/prompt_audit_summary.json
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/stored_hidden_label_audit.json
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/cost_report.json
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/robustness_rows.csv
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/robustness_by_variant_model.csv
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/robustness_by_variant_condition.csv
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/paired_deltas_by_variant.csv
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/paired_flip_rows.csv
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/robustness_report.md
reports/eha_uncued_robustness_results.json
reports/eha-uncued-robustness-results-2026-05-25.md
```

## Pre-Model Gates

The local agent must stop before model calls unless these pass:

| Gate | Requirement |
| --- | --- |
| Data source | Selection manifest references only `eha-mvp/data/uncued-pilot-v1`. |
| Frozen selection | Exact latent task IDs and view task IDs are recorded before calls. |
| Perturbation isolation | Prompt diff shows only the intended factor changes for each variant. |
| Prompt audit | 0 hidden field hits, 0 semantic doc ID hits, 0 condition/family label hits. |
| Cost preflight | Conservative projected spend below hard cap. |
| Pairing | Every planned perturbation has a `baseline_original` row for the same `(task, model)`. |
| Current artifact safety | No outputs are written into `artifact_uncued_phase1`. |

## Phase 0: Start State

Purpose: record current repository state.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones
git status --short
git log --oneline -5
cd eha-mvp
uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports
uv run pytest tests/test_uncued_run.py tests/test_uncued_report.py -q
```

Deliverable:

```text
reports/eha-uncued-robustness-start-state-2026-05-25.md
```

Acceptance:

- Dirty files are documented.
- Existing Phase 1 readiness still passes.

## Phase 1: Freeze Robustness Slice

Purpose: prevent cherry-picking and guarantee paired analysis.

Selection rules:

- Load latent tasks from `eha-mvp/data/uncued-pilot-v1/latent_tasks.jsonl`.
- Default to 20 source tasks across four polluted conditions.
- Stratify each condition by family where possible.
- Use seed `20260525`.
- Use only `neutral_metadata_visible` unless explicitly expanding the suite.
- Write source file hashes.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-plan-uncued-robustness \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-robustness-2026-05-25 \
  --conditions generated_lore,buried_primary,conflicting_evidence,false_consensus \
  --tasks-per-condition 5 \
  --view neutral_metadata_visible \
  --seed 20260525
```

Acceptance:

- `selection_manifest.json` has selected task IDs, condition, family, view, seed, and input hashes.
- No clean rows are needed in the default run; this suite focuses on polluted-stress robustness.

## Phase 2: Build Perturbation Composer

Purpose: implement perturbations as controlled transformations.

Actions:

- Build a single prompt composer that accepts `variant`.
- For each `(task, variant)`, emit a prompt artifact before model calls.
- Write `perturbation_manifest.json` with exact transformation rules.
- Write a prompt parity audit:
  - `baseline_original` vs `order_randomized`: same documents, different order only.
  - `baseline_original` vs `source_type_masked`: only `source_type` changed.
  - `baseline_original` vs `prompt_paraphrase`: only policy text changed.
  - `baseline_original` vs `citation_masked`: only visible citation field changed.

Acceptance:

- Unit tests assert each perturbation changes only intended fields.
- Prompt audit finds no hidden labels or condition/family labels.
- `citation_masked` does not alter document body text.

## Phase 3: Dry Run And Budget Check

Purpose: avoid partial paired runs.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-run-uncued-robustness \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-robustness-2026-05-25 \
  --models gpt-5.5,gemini-3.1-pro-preview \
  --variants baseline_original,order_randomized,source_type_masked,prompt_paraphrase,citation_masked \
  --schema current_phase1_interface \
  --prompt standard_answer \
  --view neutral_metadata_visible \
  --dry-run \
  --hard-cap-usd 7
```

Acceptance:

- Dry run reports planned calls and cost by model and variant.
- Planned calls are complete paired groups.
- If projected cost exceeds cap, reduce tasks before dropping variants.

## Phase 4: Model Calls

Purpose: run the robustness suite.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-run-uncued-robustness \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-robustness-2026-05-25 \
  --models gpt-5.5,gemini-3.1-pro-preview \
  --variants baseline_original,order_randomized,source_type_masked,prompt_paraphrase,citation_masked \
  --schema current_phase1_interface \
  --prompt standard_answer \
  --view neutral_metadata_visible \
  --max-output-tokens 4096 \
  --parallel-models 2 \
  --resume \
  --soft-cap-usd 5 \
  --hard-cap-usd 7 \
  --abort-cap-usd 8
```

Acceptance:

- `predictions.jsonl` contains one row per planned `(task, model, variant)`.
- Cost report is below hard cap.
- Prompt and stored hidden-label audits pass.
- No unpaired perturbation rows are used for claims.

Failure handling:

- If a provider fails, keep complete rows for the other provider but mark cross-model claims unavailable.
- If one perturbation fails broadly, report it as incomplete and do not infer robustness for that variant.
- If budget aborts, stop and report incomplete paired groups.

## Phase 5: Score And Pair

Purpose: score rows with the existing uncued scorer and compute paired deltas.

Required row metrics:

```text
task_id
base_task_id
condition
family
model
variant
parse_success
belief_correctness
operational_epistemic_escape
evidence_precision
polluted_support_rate
rejected_pollutant_rate
clean_support_recall
verification_action_score
exact_target_rate
required_action_recall
selected_doc_ids
support_doc_ids
rejected_doc_ids
predicted_verdict
gold_verdict
```

Paired metrics:

```text
delta_operational_escape
delta_belief_correctness
delta_evidence_precision
delta_polluted_support_rate
delta_action_score
pass_to_fail_operational
fail_to_pass_operational
support_set_changed
verdict_changed
```

Aggregation:

- by variant;
- by variant and model;
- by variant and condition;
- by variant and family;
- generated-lore belief/operation gap by variant.

Acceptance:

- Paired deltas include only complete `(task, model, baseline, perturbation)` groups.
- Flip rows are exported for manual inspection.
- `citation_masked` is analyzed separately as a stress test.

## Phase 6: Manual Review Of Flip Rows

Purpose: understand major sensitivity cases.

Sample all rows where:

- operational escape flips;
- verdict flips;
- polluted support changes from 0 to 1 or 1 to 0;
- action score changes in active-verification rows.

Write:

```text
eha-mvp/results/reports-eha-uncued-robustness-2026-05-25/robustness_flip_review.csv
```

Fields:

```text
review_id
task_id
model
variant
flip_type
baseline_summary
perturbation_summary
likely_cause
claim_impact
review_note
```

Acceptance:

- Every operational flip is reviewed.
- Review distinguishes meaningful sensitivity from harmless output variation.

## Phase 7: Report

Purpose: produce a narrow robustness result.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-report-uncued-robustness \
  --run-dir results/reports-eha-uncued-robustness-2026-05-25 \
  --reports-dir ../reports

uv run eha-verify-uncued-robustness \
  --run-dir results/reports-eha-uncued-robustness-2026-05-25 \
  --reports-dir ../reports
```

Required report sections:

- scope and task selection;
- perturbation definitions;
- prompt audit;
- cost and invocation profile;
- aggregate metrics by variant;
- paired deltas;
- generated-lore belief/operation gap by variant;
- flip review summary;
- claim boundary.

Acceptance:

- Report states whether each perturbation preserves, weakens, or reverses the core finding.
- No unpaired or incomplete groups are used for robustness claims.
- Report does not claim open-web validity.

## Interpretation Rules

### If results are stable

Allowed wording:

> In a paired Phase 1.3 robustness mini-suite, the generated-lore belief/operation gap persisted under evidence-order randomization, source-type masking, and prompt paraphrase.

Still required:

- report sample size;
- report perturbations;
- state that this is a mini-suite, not full robustness proof.

### If one perturbation is sensitive

Allowed wording:

> The robustness suite showed sensitivity to citation masking, suggesting that visible dependency structure is part of the task signal rather than a neutral presentation detail.

Do not call this a failure unless the perturbation was intended to preserve all task-relevant information.

### If order or prompt paraphrase breaks the finding

Required action:

- narrow the paper claim;
- inspect flip rows;
- do not claim robustness;
- consider rerunning with more tasks or fixing prompt/task construction.

## Paper Integration

If successful, update:

```text
paper/sections/07_results.tex
paper/sections/10_limitations.tex
paper/appendices/
```

Add at most one compact table unless the result is central:

```text
paper/tables/robustness_paired_deltas.tex
```

Keep paper wording concise. This is supporting evidence, not a new main result.

## Final Verification

Commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run pytest tests/test_uncued_robustness.py -q
uv run eha-verify-uncued-robustness \
  --run-dir results/reports-eha-uncued-robustness-2026-05-25 \
  --reports-dir ../reports

cd /Users/chenmohan/gits/ficciones/paper
make pdf

cd /Users/chenmohan/gits/ficciones
git diff --check
```

Acceptance:

- Tests pass.
- Robustness verifier passes.
- PDF builds if paper changed.
- `git diff --check` passes.

## Final Handoff

Write:

```text
reports/eha-uncued-robustness-handoff-2026-05-25.md
```

Include:

- selected tasks and variants;
- model calls and cost;
- verification outcomes;
- paired delta summary;
- flip review summary;
- exact paper claim changes;
- remaining robustness gaps.

## Final Acceptance Checklist

- Task slice frozen before model calls.
- Perturbations are isolated and tested.
- Prompt audits pass.
- Same-suite baseline exists for every perturbation row.
- Paired deltas are computed only on complete groups.
- Operational flip rows are manually reviewed.
- Results are reported as mini-suite robustness checks.
- Paper claims are narrowed if perturbations expose sensitivity.
