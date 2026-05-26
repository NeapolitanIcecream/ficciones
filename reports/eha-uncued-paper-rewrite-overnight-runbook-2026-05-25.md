# EHA-Uncued Paper Rewrite And Audit Closure Overnight Runbook

Date: 2026-05-25

Audience: local Codex coordinator and external Codex CLI sessions working in `/Users/chenmohan/gits/ficciones`.

Goal: finish the next paper pass after the core-claim overnight result. The paper should be rewritten around polluted evidence ecologies, provenance discipline, source independence, pollutant rejection, and verification behavior. The old belief-correctness vs operational-escape separation must be demoted to a diagnostic view with schema/scorer sensitivity. No new large experiment is planned. The only remaining empirical work is narrow audit closure and paper-facing integration.

This runbook uses independent `tmux` Codex CLI sessions for the pieces that would normally require human review. Each independent Codex CLI session must handle exactly one audit issue and write exactly one audit report.

## Non-Negotiable Rules

- Do not run new broad model experiments.
- Do not try to rescue the old schema-independent separation headline.
- Do not describe Codex CLI audit as independent human validation.
- Do not use old cued artifacts or old cued outputs.
- Do not overwrite or mutate existing Phase 1, Phase 1.1, Phase 1.2, Phase 1.3, or core-claim overnight result directories.
- Every audit session is scoped to one audit issue only.
- Audit sessions may inspect files and write their own `process.md` plus one audit report; they must not edit paper, code, data, or shared results.
- The main rewrite worker owns paper edits and synthesis.
- Do not read Codex CLI stdout/stderr logs unless debugging a blocked session. Use `process.md` and the audit report as the handoff.
- Keep final claims narrower than the evidence: synthetic diagnostic pilot, not open-web benchmark, production readiness test, or stable leaderboard.

## Target Paper Position

The rewritten paper should argue:

> EHA-Uncued is a validity-first diagnostic pilot for testing whether models maintain evidence hygiene in polluted evidence ecologies. It separates final verdict correctness from provenance discipline, source independence, pollutant rejection, and executable verification behavior. The old belief/operation gap is retained as a diagnostic warning signal, but the current evidence shows it is sensitive to schema and scorer semantics, especially support-field ambiguity.

Allowed claims:

- Final-answer accuracy can hide evidence-hygiene and verification-contract failures.
- Generated-lore and echo-chain settings are useful stress tests for source independence and pollutant rejection.
- Current operational scores need decomposition and sensitivity analysis to be interpretable.
- The benchmark is an auditable diagnostic artifact, not a leaderboard.

Forbidden claims:

- A schema-independent belief/action separation has been proven.
- Models are broadly unable to escape polluted open-web environments.
- The pilot establishes production agent readiness.
- Model ordering is stable enough for ranking.
- Codex audit is equivalent to independent human annotation.

## Required Inputs

Primary decision inputs:

```text
reports/eha-uncued-core-claim-overnight-results-2026-05-25.md
reports/eha-uncued-paper-reframing-decision-2026-05-25.md
reports/eha_uncued_core_claim_overnight_results.json
eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/
```

Paper files likely to edit:

```text
paper/sections/00_abstract.tex
paper/sections/01_intro.tex
paper/sections/02_polluted_evidence_environments.tex
paper/sections/03_uncued_dataset_design.tex
paper/sections/05_metrics_scoring.tex
paper/sections/07_results.tex
paper/sections/08_schema_interface.tex
paper/sections/10_limitations.tex
paper/sections/13_conclusion.tex
paper/appendices/operational_escape_spec.tex
paper/appendices/leakage_shortcut_methods.tex
paper/appendices/robustness_mini_suite.tex
paper/tables/
```

New output workspace:

```text
eha-mvp/results/reports-eha-uncued-paper-rewrite-overnight-2026-05-25/
reports/eha-uncued-paper-rewrite-overnight-results-2026-05-25.md
reports/eha-uncued-paper-rewrite-claim-audit-2026-05-25.md
```

Codex workflow workspace:

```text
.codex-workflows/uncued-paper-rewrite-overnight/
```

## Phase 0: Start State

Purpose: record the current repo state, including the uncommitted core-claim overnight artifacts.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones
git status --short
git log --oneline -8

cd eha-mvp
uv run eha-verify-uncued-core-claim-overnight \
  --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 \
  --reports-dir ../reports
```

Deliverable:

```text
eha-mvp/results/reports-eha-uncued-paper-rewrite-overnight-2026-05-25/start_state.md
```

Acceptance:

- Dirty files are documented.
- Core-claim overnight verifier passes.
- No paper rewrite begins before start state is recorded.

## Phase 1: Prepare Narrow Audit Packets

Purpose: create small, stable packets for the independent Codex CLI audit sessions.

Create:

```text
eha-mvp/results/reports-eha-uncued-paper-rewrite-overnight-2026-05-25/audit_packets/
  support_ambiguity_packet.csv
  timestamp_semantics_packet.csv
  citation_cycle_packet.csv
  shortcut_boundary_packet.json
  paper_claim_scan_packet.md
```

Packet definitions:

- `support_ambiguity_packet.csv`: the 72 generated-lore target rows from `support_ambiguity_candidate_rows.csv` or `support_ambiguity_sensitivity_rows.csv`, plus task ID, model, verdict, support docs, rejected docs, diagnostic/action text if available, strict/prose/action sensitivity labels.
- `timestamp_semantics_packet.csv`: all P1 chronology rows and representative affected tasks/documents; include the data-sanity note that timestamps may be synthetic/non-evidential.
- `citation_cycle_packet.csv`: all dependency-cycle rows and dependency edges needed to inspect whether the cycles are intentional echo-chain structure or dataset mistakes.
- `shortcut_boundary_packet.json`: shortcut model margin summary, by-condition-family margins, and examples where shortcut baselines match or beat models.
- `paper_claim_scan_packet.md`: current abstract/introduction/results/limitations snippets that mention belief correctness, operational escape, leaderboard, agent readiness, schema ablation, robustness, shortcut baselines, and ecological validity.

Acceptance:

- Packets are small enough for one audit session each.
- Packets contain enough context that each audit session does not need to infer scope from the whole repository.
- Packets contain no hidden labels except where the audit explicitly requires scorer-facing context.

## Phase 2: Launch Independent Codex CLI Audit Sessions

Purpose: replace the remaining manual-review steps with bounded independent Codex CLI reviews.

Use one session per issue:

```text
audit-support-ambiguity
audit-timestamp-semantics
audit-citation-cycles
audit-shortcut-boundary
audit-claim-consistency
```

Each session writes under:

```text
.codex-workflows/uncued-paper-rewrite-overnight/audits/<audit-id>/
  prompt.md
  process.md
  run.sh
  audit_report.md
  cli.log
```

### Common Codex CLI Invocation

Use the same invocation shape for every audit session:

```bash
codex exec \
  -C /Users/chenmohan/gits/ficciones \
  -m gpt-5.5 \
  -c model_reasoning_effort=\"xhigh\" \
  --dangerously-bypass-approvals-and-sandbox \
  - < .codex-workflows/uncued-paper-rewrite-overnight/audits/<audit-id>/prompt.md \
  > .codex-workflows/uncued-paper-rewrite-overnight/audits/<audit-id>/cli.log \
  2>&1
```

Start each one in `tmux`:

```bash
tmux new-session -d -s eha-audit-support-ambiguity \
  '.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-support-ambiguity/run.sh'

tmux new-session -d -s eha-audit-timestamp-semantics \
  '.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-timestamp-semantics/run.sh'

tmux new-session -d -s eha-audit-citation-cycles \
  '.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-citation-cycles/run.sh'

tmux new-session -d -s eha-audit-shortcut-boundary \
  '.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-shortcut-boundary/run.sh'

tmux new-session -d -s eha-audit-claim-consistency \
  '.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-claim-consistency/run.sh'
```

Before launching, check for existing sessions:

```bash
tmux list-sessions -F '#S'
```

Do not read `cli.log` during normal progress checks. Read:

```text
.codex-workflows/uncued-paper-rewrite-overnight/audits/<audit-id>/process.md
.codex-workflows/uncued-paper-rewrite-overnight/audits/<audit-id>/audit_report.md
```

### Required Audit Report Format

Every `audit_report.md` must use this structure:

```markdown
# Audit Report: <audit-id>

status: pass | pass_with_qualifications | issues_found | blocked

## Scope
One paragraph naming the single audit issue.

## Files Inspected
List exact files.

## Method
Briefly explain how the audit was performed.

## Findings
Numbered findings with severity: P0, P1, P2.

## Examples
Concrete row/task/file examples.

## Paper Implication
What the paper should say or avoid saying.

## Required Closure
Exact required edits or "none".
```

### Audit Session 1: Support Ambiguity

Scope: audit only whether generated-lore strict failures are genuine evidence-hygiene failures or support-field allocation artifacts.

Inputs:

```text
audit_packets/support_ambiguity_packet.csv
eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/support_ambiguity_sensitivity_summary.csv
eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/qualitative_failure_examples.md
```

Task:

- Inspect all 72 target generated-lore rows if feasible; otherwise inspect every row where prose-aware rescoring changed strict fail to pass plus a stratified sample of the rest.
- Decide whether each changed row is:
  - `likely_schema_allocation_artifact`;
  - `likely_true_dirty_support_failure`;
  - `unclear_or_needs_human`.
- Report whether the 98.6 percent gap-closure result is directionally credible.

Forbidden:

- Do not review timestamp or shortcut issues.
- Do not edit code, paper, data, or result files.

Expected output:

```text
.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-support-ambiguity/audit_report.md
```

### Audit Session 2: Timestamp Semantics

Scope: audit only whether synthetic timestamp warnings require dataset repair or paper/documentation qualification.

Inputs:

```text
audit_packets/timestamp_semantics_packet.csv
eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/data_sanity_audit_rows.csv
eha-mvp/data/uncued-pilot-v1/README.md
eha-mvp/data/uncued-pilot-v1/documents_neutral_metadata_visible.jsonl
eha-mvp/data/uncued-pilot-v1/documents_neutral_metadata_hidden.jsonl
```

Task:

- Determine whether timestamps are model-visible evidential information, neutral synthetic metadata, or ambiguous.
- Decide whether paper text can simply qualify timestamps as synthetic/non-evidential, or whether dataset docs must be patched.
- Identify any P0 row where timestamp order changes task interpretation.

Forbidden:

- Do not inspect support ambiguity or shortcut boundaries.
- Do not edit files.

Expected output:

```text
.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-timestamp-semantics/audit_report.md
```

### Audit Session 3: Citation Cycles

Scope: audit only dependency/citation graph cycles found by data sanity checks.

Inputs:

```text
audit_packets/citation_cycle_packet.csv
eha-mvp/data/uncued-pilot-v1/dependency_edges.jsonl
eha-mvp/data/uncued-pilot-v1/documents_neutral_metadata_visible.jsonl
eha-mvp/data/uncued-pilot-v1/documents_neutral_metadata_hidden.jsonl
```

Task:

- Determine whether citation cycles are intentional false-consensus / echo-chain constructions or unintended graph errors.
- Identify whether any cycle affects scoring, shortcut baselines, or paper examples.
- Recommend one of:
  - document as synthetic echo-chain structure;
  - repair dataset docs only;
  - repair data and rerun affected analyses.

Forbidden:

- Do not review timestamp warnings.
- Do not edit data.

Expected output:

```text
.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-citation-cycles/audit_report.md
```

### Audit Session 4: Shortcut Boundary

Scope: audit only how shortcut baseline results constrain paper claims.

Inputs:

```text
audit_packets/shortcut_boundary_packet.json
eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/shortcut_model_margin_bootstrap.json
eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/shortcut_breakdown_by_condition_family.csv
reports/eha-uncued-core-claim-overnight-results-2026-05-25.md
```

Task:

- Decide which claims the shortcut margins rule out.
- Identify which condition/family cells are still meaningfully above shortcuts.
- Recommend exact wording for limitations and results.

Forbidden:

- Do not review support ambiguity, timestamps, or citation cycles.
- Do not edit paper files.

Expected output:

```text
.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-shortcut-boundary/audit_report.md
```

### Audit Session 5: Claim Consistency

Scope: audit only whether the current paper still makes claims that conflict with the reframing decision.

Inputs:

```text
audit_packets/paper_claim_scan_packet.md
paper/sections/00_abstract.tex
paper/sections/01_intro.tex
paper/sections/07_results.tex
paper/sections/08_schema_interface.tex
paper/sections/10_limitations.tex
paper/sections/13_conclusion.tex
reports/eha-uncued-paper-reframing-decision-2026-05-25.md
```

Task:

- Find text that still frames belief/operation separation as the central scientific claim.
- Find leaderboard, agent-readiness, open-web, schema-independent, or over-robustness language.
- Produce a list of required paper edits with file and line references.

Forbidden:

- Do not edit the paper.
- Do not inspect data sanity details except as needed to flag claim mismatch.

Expected output:

```text
.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-claim-consistency/audit_report.md
```

## Phase 3: Main Rewrite Worker

Purpose: rewrite the paper after audit reports are available.

The main rewrite worker may edit paper and report files. It must wait until all audit sessions are `pass`, `pass_with_qualifications`, or `issues_found` with actionable closure. If any audit is `blocked`, either fix the packet or explicitly defer that issue in the handoff.

Primary edits:

### Abstract

- Center polluted evidence ecologies and evidence hygiene.
- Remove schema-independent separation as the headline.
- Mention final-answer correctness only as insufficient by itself.
- Avoid model ranking.

### Introduction

- Start from polluted AI-generated evidence ecologies, echo chains, false consensus, stale/derivative records, and primary-source recovery.
- Present the benchmark as a diagnostic pilot.
- Make the old belief/operation gap a motivation for decomposition, not the thesis.

### Dataset / Method

- Define evidence roles more explicitly:
  - clean support;
  - refuting evidence;
  - polluted/generated/derivative material;
  - rejected or diagnostic evidence;
  - verification action.
- Explain that support-field ambiguity was found and audited.
- Clarify synthetic timestamps as non-evidential or neutral metadata, depending on the timestamp audit.
- Clarify citation cycles, depending on the citation audit.

### Metrics / Scoring

- Present `operational_epistemic_escape` as one scorer contract among several.
- Add decomposition logic: dirty support, generated-lore selected, evidence-value threshold, duplicate/root failure, action failure, belief incorrect.
- Explain positive evidence-contract check.

### Results

- Add or replace with paper-facing summaries for:
  - failure decomposition;
  - support ambiguity sensitivity;
  - decomposed-schema rerun;
  - positive evidence contract;
  - shortcut boundary.
- Use old belief/operation table only if it is captioned as diagnostic and sensitivity-bound.

### Schema / Interface

- State that interface design is a first-order variable.
- Avoid saying schema ablation "solves" schema artifacts.
- Use the decomposed-schema rerun to show sensitivity and clarify interpretation.

### Limitations

- Add explicit limits:
  - synthetic diagnostic pilot;
  - no open-web ecological validity claim;
  - shortcut baselines are competitive in important cells;
  - support ambiguity sensitivity is local-audit-only;
  - timestamps/citation graph are synthetic artifacts if confirmed;
  - model ranking is descriptive.

### Conclusion

- End with the polluted-evidence diagnostic framework, not the old separation headline.

Deliverables:

```text
reports/eha-uncued-paper-rewrite-overnight-results-2026-05-25.md
reports/eha-uncued-paper-rewrite-claim-audit-2026-05-25.md
paper/main.pdf
```

Acceptance:

- The abstract and intro no longer make schema-independent separation the core claim.
- Results include decomposition and support ambiguity.
- Limitations include shortcut boundary and synthetic artifact qualifications.
- The paper still has a positive contribution, not only a self-critique.

## Phase 4: Paper Claim Audit After Rewrite

Purpose: run a final claim-level pass after edits.

The main worker should run a local text scan:

```bash
cd /Users/chenmohan/gits/ficciones
rg -n "belief|operational escape|separation|leaderboard|agent readiness|open-web|schema-independent|robust|production|ranking" paper/sections paper/appendices
```

Then create a fresh independent reviewer session:

```text
audit-final-paper-claim-consistency
```

Scope: review only the rewritten paper for claim consistency with the reframing decision.

This final reviewer must not edit files. It writes:

```text
.codex-workflows/uncued-paper-rewrite-overnight/audits/audit-final-paper-claim-consistency/audit_report.md
```

Acceptance:

- No P0 overclaim remains.
- Any remaining P1 claim risks are either fixed or explicitly listed in the handoff.

## Phase 5: Verification

Purpose: prove the rewrite compiles and the evidence pipeline still verifies.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-verify-uncued-core-claim-overnight \
  --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 \
  --reports-dir ../reports

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

cd /Users/chenmohan/gits/ficciones
make pdf
git diff --check
```

Deliverables:

```text
eha-mvp/results/reports-eha-uncued-paper-rewrite-overnight-2026-05-25/verification.json
reports/eha-uncued-paper-rewrite-overnight-results-2026-05-25.md
```

Acceptance:

- Verifier passes.
- Relevant tests pass, or failures are documented as blockers.
- PDF builds.
- `git diff --check` passes.

## Phase 6: Final Handoff

The final handoff must include:

- Which audit sessions ran and their statuses.
- Which audit findings changed the paper.
- Exact paper files edited.
- Tables/figures added, removed, or recaptioned.
- Remaining risks before the next GPT-5.5-Pro blind review.
- Whether the rewritten paper is ready for a blind-review evidence package.
- Current `git status --short`.

Recommended final decision labels:

```text
ready_for_blind_review
ready_after_minor_edits
blocked_by_audit_issue
blocked_by_pdf_or_tests
```

## Expected Overnight Outcome

Expected successful outcome:

- The old separation headline is removed from abstract/introduction.
- The paper has a stronger and clearer core: polluted evidence ecology diagnostics.
- Support ambiguity is audited and framed as a scorer/schema sensitivity.
- Timestamp and citation-cycle warnings are either documented or marked for repair.
- Shortcut baselines are used to bound ecological validity.
- The paper compiles and is ready for another GPT-5.5-Pro blind review.
