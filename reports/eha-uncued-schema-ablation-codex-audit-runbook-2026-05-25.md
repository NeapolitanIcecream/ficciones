# EHA-Uncued Schema Ablation Codex Audit Runbook

Date: 2026-05-25

Audience: a local Codex agent auditing the completed role-uncued Phase 1.1 schema ablation in `/Users/chenmohan/gits/ficciones`.

Goal: perform a Codex manual audit of the Phase 1.1 schema-ablation scorer and reporting claims. The audit should inspect row-level prompt, response, parsed prediction, hidden gold, and scored metrics, then produce an auditable disagreement table and summary.

This is a Codex-assisted manual audit. It can strengthen local quality control because Codex has already been effective at these evidence-role checks, but it is not independent human-subject validation and must not be described that way.

## Non-Negotiable Rules

- Use only role-uncued Phase 1.1 ablation data under `eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/` and gold/reference data under `eha-mvp/data/uncued-pilot-v1/`.
- Do not use old cued artifacts, old cued outputs, or `data/epistemic-resilience-v1` as evidence.
- Do not change model outputs, prompts, or scored rows while auditing. If the audit finds a scorer bug, record the disagreement first, then fix and rerun scoring as a separate step.
- Audit conclusions must distinguish `Codex manual audit` from `independent human review`.
- Every audited row must include a short note explaining the judgment. Blank notes fail the audit.
- Any paper update must preserve the Phase 1.1 boundary: exploratory schema/interface sensitivity only, not a replacement for the Phase 1 main table.

## Audit Scope

Recommended scope: audit all latest 128 complete rows.

Minimum acceptable scope if time-constrained: 64 rows, stratified across:

```text
schemas: current, clarified, minimal, diagnostic_no_hygiene
models: gpt-5.5, gemini-3.1-pro-preview
conditions: generated_lore, buried_primary
families: packet_judgment, evidence_selection, active_verification
```

The full run is preferred because the ablation is small and all 128 latest rows are already complete.

Existing 16-row `schema_ablation_manual_audit.csv` is useful as a smoke audit, but it is not enough for the post-ablation claim review.

## Inputs

Primary run:

```text
eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/
```

Required files:

```text
selection_manifest.json
schema_manifest.json
run_manifest.json
predictions.jsonl
schema_ablation_rows.csv
schema_ablation_by_schema_model.csv
schema_ablation_by_schema_model_condition.csv
schema_ablation_manual_audit.csv
artifacts/*/*/*/*.prompt.json
artifacts/*/*/*/*.response.json
```

Gold/reference files:

```text
eha-mvp/data/uncued-pilot-v1/latent_tasks.jsonl
eha-mvp/data/uncued-pilot-v1/gold_documents.jsonl
eha-mvp/data/uncued-pilot-v1/action_gold.jsonl
```

Paper/report claims to check:

```text
reports/eha-uncued-schema-ablation-results-2026-05-23.md
reports/eha_uncued_schema_ablation_results.json
paper/sections/08_schema_interface.tex
paper/sections/10_limitations.tex
```

## Outputs

Write audit outputs under:

```text
eha-mvp/results/reports-eha-uncued-schema-ablation-codex-audit-2026-05-25/
```

Expected files:

```text
codex_schema_audit_manifest.json
codex_schema_audit_sample.csv
codex_schema_audit_rows.csv
codex_schema_audit_disagreements.csv
codex_schema_audit_summary.json
codex_schema_audit_summary.md
codex_schema_audit_claim_review.md
```

Also write a concise top-level report:

```text
reports/eha-uncued-schema-ablation-codex-audit-2026-05-25.md
reports/eha_uncued_schema_ablation_codex_audit.json
```

## Label Contract

For each audited row, record these fields:

```text
audit_id
task_id
base_task_id
condition
family
model
schema_variant
prompt_condition
semantic_verdict_agrees
support_hygiene_agrees
rejection_hygiene_agrees
diagnostic_field_agrees
selected_primary_agrees
action_quality_agrees
role_escape_agrees
operational_escape_proxy_agrees
scorer_fix_needed
severity
auditor_note
evidence_refs
```

Allowed values:

- Agreement fields: `1`, `0`, or `not_applicable`.
- `scorer_fix_needed`: `1` or `0`.
- `severity`: `none`, `minor`, `material`, or `blocking`.
- `auditor_note`: nonblank, one or two concrete sentences.
- `evidence_refs`: comma-separated local file references or row IDs used for the judgment.

Severity definitions:

- `none`: scorer/report row is correct.
- `minor`: wording or note could be clearer, but metrics and claims are unaffected.
- `material`: row-level metric or aggregate could change.
- `blocking`: paper/report claim becomes unsupported or the audit cannot be trusted.

## Audit Questions

For every row, answer these questions from the row artifacts and gold files:

- Does the model's `claim_verdict` match the gold verdict?
- Does the support field contain any known polluted/generated/stale/pseudo-consensus document?
- For `buried_primary`, does the support/selection behavior correctly use the clean primary evidence when required?
- For `generated_lore`, does the schema make generated or unsupported authority-like evidence machine-actionable as support?
- For schemas with rejection fields, are polluted documents correctly rejected when the scorer says they are?
- For schemas with diagnostic fields, is diagnostic placement consistent with the scorer's interpretation?
- Are any polluted documents assigned incompatible dual roles?
- For active-verification rows, would the action reduce uncertainty under the task's action gold?
- Does `role_escape` follow from belief correctness plus field hygiene?
- Does `operational_escape_proxy` follow from the row's field and action requirements?

Schema-specific support field mapping:

```text
current: support = supporting_evidence
clarified: support = clean_supporting_evidence
minimal: support = evidence_doc_ids
diagnostic_no_hygiene: support = supporting_evidence
```

For `minimal`, rejection, diagnostic, and action metrics may be `not_applicable` by design. Do not force them to zero unless the scorer explicitly defines them that way.

## Phase 0: Baseline And Isolation

Purpose: confirm the audit starts from the completed Phase 1.1 state.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones
git status --short
cd eha-mvp
uv run eha-verify-uncued-schema-ablation \
  --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 \
  --reports-dir ../reports
```

Acceptance:

- Verification passes before the audit starts.
- Any unrelated dirty files are listed in `codex_schema_audit_manifest.json`.
- The audit manifest records the current commit hash.

## Phase 1: Build The Audit Packet

Purpose: construct a review packet that lets Codex audit rows without relying on aggregate tables.

Actions:

- Load `schema_ablation_rows.csv`.
- Deduplicate to the latest complete rows represented in the existing result report.
- Join each row with:
  - parsed prediction from `predictions.jsonl`;
  - prompt artifact path;
  - response artifact path;
  - latent task metadata;
  - gold documents for the selected view;
  - action gold for active-verification rows.
- Emit `codex_schema_audit_sample.csv`.

Suggested implementation command if no helper exists yet:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-build-uncued-schema-codex-audit \
  --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-schema-ablation-codex-audit-2026-05-25 \
  --scope full
```

If the helper does not exist, implement it in:

```text
eha-mvp/eha/uncued_schema_codex_audit.py
eha-mvp/tests/test_uncued_schema_codex_audit.py
```

Acceptance:

- `codex_schema_audit_sample.csv` has 128 rows for full scope, or a documented stratified subset.
- Every row has prompt and response artifact paths.
- No row is missing gold document role information.

## Phase 2: Codex Row Audit

Purpose: review the rows as a manual evidence-role audit.

Process:

1. For each row, open the prompt artifact and response artifact.
2. Read the parsed/scored row from `schema_ablation_rows.csv`.
3. Read the hidden gold only from `gold_documents.jsonl` and `latent_tasks.jsonl`.
4. Apply the audit questions above.
5. Record labels in `codex_schema_audit_rows.csv`.
6. Record every disagreement in `codex_schema_audit_disagreements.csv`.

Codex reviewer instruction:

```text
You are auditing scorer correctness for a role-uncued schema ablation. Do not judge whether the model sounds persuasive. Judge whether the structured fields make the right evidence machine-actionable under the gold evidence roles. If the model's prose rejects polluted evidence but the support field includes it, mark support hygiene as failed. If the row is ambiguous, write the ambiguity in auditor_note and use severity=minor or material as appropriate.
```

Acceptance:

- Every audited row has all agreement fields filled.
- Every audited row has a nonblank `auditor_note`.
- Every disagreement has a concrete file/row reference.
- `scorer_fix_needed=1` rows are not silently ignored.

## Phase 3: Disagreement Triage

Purpose: decide whether any audit disagreement changes scorer outputs or paper claims.

For each disagreement, classify:

```text
scorer_bug
paper_wording_issue
ambiguous_but_no_change
audit_error
```

Actions:

- If `scorer_bug`, fix scorer code, rerun report generation, rerun verification, and re-audit affected rows.
- If `paper_wording_issue`, update paper/report language without changing scored data.
- If `ambiguous_but_no_change`, document why current scoring is retained.
- If `audit_error`, correct the audit row and explain the correction.

Acceptance:

- No unresolved `material` or `blocking` disagreement remains.
- Summary reports exact counts by disagreement type and severity.

## Phase 4: Claim Review

Purpose: verify that reports and paper say only what the audit supports.

Check these claims:

- Phase 1.1 is exploratory and not a replacement for Phase 1 main results.
- Old cued results are not used.
- The ablation holds evidence fixed and varies structured output interface.
- Minimal schema placed polluted evidence in support fields on all rows for both evaluated models.
- Current and clarified avoided polluted support in this slice.
- Diagnostic-without-hygiene showed mixed role allocation, especially for GPT-5.5.
- The paper does not claim independent human validation.
- The paper does not claim schema wording explains every Phase 1 gap.

Write:

```text
codex_schema_audit_claim_review.md
```

Acceptance:

- Each claim is marked `supported`, `needs_revision`, or `unsupported`.
- Any `needs_revision` or `unsupported` claim has an exact suggested text change.

## Phase 5: Final Report

Purpose: produce a compact audit result that can be cited internally.

Required summary fields:

```text
audit_scope
rows_audited
rows_with_scorer_fix_needed
material_disagreements
blocking_disagreements
paper_claims_supported
paper_claims_needing_revision
independent_human_review: false
```

Write:

```bash
reports/eha-uncued-schema-ablation-codex-audit-2026-05-25.md
reports/eha_uncued_schema_ablation_codex_audit.json
```

Allowed final wording:

> A full Codex manual audit of the Phase 1.1 schema-ablation rows found no material scorer disagreements.

Only use that sentence if the audit actually reviews all 128 rows and finds no material scorer disagreement.

Forbidden final wording:

- "independent human validation"
- "human subjects audit"
- "schema ablation proves"
- "model ranking"
- "schema wording explains all Phase 1 failures"

## Final Verification

Commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-verify-uncued-schema-ablation \
  --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 \
  --reports-dir ../reports

cd /Users/chenmohan/gits/ficciones
git diff --check
```

If the paper is edited:

```bash
cd /Users/chenmohan/gits/ficciones/paper
make pdf
```

Acceptance:

- Schema-ablation verification still passes.
- `git diff --check` passes.
- If paper changed, PDF builds.
- Final report clearly labels the audit as Codex manual audit, not independent human review.
