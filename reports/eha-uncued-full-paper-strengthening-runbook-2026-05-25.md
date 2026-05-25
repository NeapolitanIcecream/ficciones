# EHA-Uncued Full-Paper Strengthening Runbook

Date: 2026-05-25

Audience: local Codex agent working in `/Users/chenmohan/gits/ficciones`.

Goal: turn the current EHA-Uncued pilot paper from a credible workshop/artifact-style diagnostic report into a stronger full-paper submission, using the GPT-5.5-Pro blind review as a risk map. The work should strengthen scientific auditability and evidence without overstating the pilot.

Context: the blind review saw only the paper PDF, not the open-source experiment repository. Treat artifact-detail criticism as lower priority than methodological and statistical criticism. The artifact response should be concise: point to the released repository, verifier, manifest, and code paths. Do not spend the main paper budget turning the body into an artifact manual.

## Non-Negotiable Rules

- Do not broaden the claim beyond pilot evidence.
- Keep old cued results quarantined.
- Do not describe Codex-assisted review as independent human validation.
- Keep model ranking descriptive unless uncertainty analysis supports stronger language.
- Preserve the distinction between Phase 1 main results, Phase 1.1 schema ablation, and Phase 1.2 Codex schema audit.
- Prefer auditable formulas, examples, and code links over internal phase/runbook narration.
- If new experiments are run, record manifests, seeds, prompts, costs, and verification outputs.

## Priority Map

P0 work should be done before another serious submission:

- formalize operational epistemic escape with formulas or pseudocode;
- add statistical uncertainty over latent tasks;
- make leakage and shortcut baselines methodologically inspectable;
- add concrete task/scoring examples;
- fix confusing active-verification table wording;
- remove internal run-log flavor from the paper body;
- add model invocation details in an appendix or compact reproducibility subsection.

P1 work materially improves acceptance odds:

- robustness checks: evidence order, metadata/source-type masking, prompt paraphrase;
- larger schema ablation or more conditions/views;
- independent human audit with at least two annotators and adjudication;
- stronger synthetic-template diversity analysis.

P2 work is expansion beyond the current paper:

- semi-real or real document slices;
- larger task set;
- external annotator study;
- open benchmark release process and versioned leaderboard policy.

## Output Layout

Use a new strengthening workspace:

```text
reports/eha-uncued-full-paper-strengthening-start-2026-05-25.md
reports/eha-uncued-operational-escape-spec-2026-05-25.md
reports/eha_uncued_bootstrap_uncertainty.json
reports/eha-uncued-bootstrap-uncertainty-2026-05-25.md
reports/eha-uncued-leakage-shortcut-methods-2026-05-25.md
reports/eha-uncued-task-examples-2026-05-25.md
reports/eha-uncued-full-paper-strengthening-handoff-2026-05-25.md
eha-mvp/results/reports-eha-uncued-statistics-2026-05-25/
paper/sections/
paper/tables/
paper/appendices/
```

If adding scripts, use:

```text
eha-mvp/eha/uncued_statistics.py
eha-mvp/eha/uncued_examples.py
eha-mvp/tests/test_uncued_statistics.py
eha-mvp/tests/test_uncued_examples.py
```

## Phase 0: Baseline

Purpose: record current state and avoid mixing strengthening edits with unrelated work.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones
git status --short
git log --oneline -5

cd eha-mvp
uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports
uv run eha-verify-uncued-schema-ablation --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --reports-dir ../reports
uv run pytest tests/test_uncued_schema_ablation.py tests/test_uncued_schema_codex_audit.py -q
```

Deliverable:

```text
reports/eha-uncued-full-paper-strengthening-start-2026-05-25.md
```

Acceptance:

- Current readiness and schema-ablation verification pass.
- Dirty files are documented before edits.
- Paper claim boundary is recorded.

## Phase 1: Formal Operational Escape Spec

Purpose: make the core metric auditable from the paper alone.

Actions:

- Write a compact formal definition for `operational_epistemic_escape`.
- Define component variables:
  - `belief_correct`;
  - `support_clean`;
  - `clean_support_recovered`;
  - `pollutants_rejected_or_avoided`;
  - `uncertainty_disciplined`;
  - `action_executable`;
  - `required_action_recalled`.
- Give separate rules for:
  - `packet_judgment`;
  - `evidence_selection`;
  - `active_verification`.
- Include pseudocode that matches the scorer implementation.
- Add one worked example each for generated lore, buried primary, and active verification.

Deliverables:

```text
reports/eha-uncued-operational-escape-spec-2026-05-25.md
paper/sections/05_metrics_scoring.tex
paper/appendices/operational_escape_spec.tex
```

Acceptance:

- A reader can recompute operational escape for a row from the paper appendix.
- Tests or a small verifier confirm that the paper pseudocode matches the scorer columns.
- The paper no longer relies only on the phrase "joint success criterion."

## Phase 2: Bootstrap Uncertainty And Paired View Analysis

Purpose: address the small-n/statistical uncertainty concern without pretending the pilot is large.

Actions:

- Resample at the latent task level, not at the 480 model-row level.
- Keep paired hidden/visible views together within each latent task.
- Report 95 percent bootstrap intervals for:
  - operational escape by model;
  - belief correctness by model;
  - evidence precision by model;
  - condition-level operational escape;
  - generated-lore belief-vs-operational gap;
  - visible-hidden paired deltas.
- Add effect sizes or paired deltas where useful.
- Revise model-comparison language to "descriptive" unless intervals are clearly separated.

Suggested command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-uncued-bootstrap-statistics \
  --results-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-statistics-2026-05-25 \
  --resample-unit latent_task \
  --iterations 10000 \
  --seed 20260525
```

Deliverables:

```text
reports/eha_uncued_bootstrap_uncertainty.json
reports/eha-uncued-bootstrap-uncertainty-2026-05-25.md
paper/tables/model_metrics_with_ci.tex
paper/tables/condition_metrics_with_ci.tex
```

Acceptance:

- Intervals are reported at latent-task resampling level.
- The paper states that model differences are descriptive unless supported by uncertainty analysis.
- Visible/hidden view differences are handled as paired deltas.

## Phase 3: Leakage And Shortcut Method Detail

Purpose: make validity gates inspectable without overloading the paper with artifact mechanics.

Actions:

- Document automatic leakage levels, scanned fields, forbidden labels, semantic-ID checks, and direct-answer cue checks.
- Document local surface review sampling: why 400 rows and 50 unique tasks, or rerun/extend to cover all 60 latent tasks if cheap.
- Document shortcut baselines:
  - ID-only;
  - order-only;
  - title-only;
  - source-type-only;
  - metadata-only;
  - timestamp-only;
  - citation-graph-only;
  - claim-overlap-only;
  - simple heuristic.
- Include thresholds and one example of a shortcut failure mode.

Deliverables:

```text
reports/eha-uncued-leakage-shortcut-methods-2026-05-25.md
paper/sections/04_leakage_controls.tex
paper/appendices/leakage_shortcut_methods.tex
```

Acceptance:

- The paper body summarizes methods; appendix gives enough detail to reproduce from the open repo.
- Artifact criticism is answered by repository pointers, not by adding run-log clutter to the body.
- If surface review remains 50/60 tasks, the sampling reason is explicit.

## Phase 4: Concrete Task And Scoring Examples

Purpose: make the benchmark understandable without requiring artifact inspection.

Actions:

- Add at least three examples:
  - one clean or buried-primary row;
  - one generated-lore row;
  - one active-verification row.
- For each example, include:
  - task question;
  - abbreviated document packet;
  - hidden gold roles in an explanatory box or appendix;
  - representative model output fields;
  - scorer decision;
  - operational escape result.
- Keep examples short enough for paper readability.

Deliverables:

```text
reports/eha-uncued-task-examples-2026-05-25.md
paper/sections/03_uncued_dataset_design.tex
paper/appendices/task_examples.tex
```

Acceptance:

- Reader can see what generated lore means.
- Reader can distinguish false consensus, conflicting evidence, and buried primary.
- At least one example demonstrates correct answer but failed evidence hygiene.

## Phase 5: Fix Active-Verification Table Semantics

Purpose: resolve the blind-review confusion around Table 6.

Actions:

- Inspect how `Overall operational` in `paper/tables/active_verification_action_exactness.tex` is computed.
- If it is overall across all task families, rename it to `Overall op. across all families` or move it out of the active-verification table.
- Prefer replacing it with active-verification subset operational escape if available.
- Update caption to state exactly what each column measures.

Deliverables:

```text
paper/tables/active_verification_action_exactness.tex
paper/sections/07_results.tex
```

Acceptance:

- The active-verification table no longer mixes subset action metrics with unlabeled all-task operational metrics.
- A reader cannot confuse active-verification operational escape with global operational escape.

## Phase 6: Model Invocation Details Without Run-Log Flavor

Purpose: answer reproducibility concerns while reducing internal phase-number noise.

Actions:

- Add a compact reproducibility table:
  - model label;
  - provider;
  - API/run date;
  - response format;
  - temperature policy;
  - max output tokens;
  - retry policy;
  - prompt role policy;
  - parser/extractor.
- Move cost and internal phase-number details to appendix or artifact docs.
- Replace body text like "Phase 12/14/17" with method names:
  - model run;
  - scorer audit;
  - readiness verifier;
  - schema-ablation follow-up.

Deliverables:

```text
paper/sections/06_experimental_setup.tex
paper/sections/09_human_scorer_audit.tex
paper/sections/12_artifact.tex
paper/appendices/invocation_details.tex
```

Acceptance:

- Paper reads like a methods paper, not an internal execution log.
- Reproducibility details remain available.

## Phase 7: Robustness Checks

Purpose: reduce prompt/schema/order shortcut concerns.

Recommended mini-runs:

- evidence order randomization on a subset;
- source-type masking on a subset;
- prompt paraphrase robustness;
- schema ablation expanded beyond generated-lore/buried-primary or to both views;
- optional citation masking if it does not destroy task semantics.

Each robustness run should have:

```text
selection manifest
prompt audit
cost report
scored rows
summary report
claim boundary
```

Acceptance:

- Robustness results are reported as checks, not new leaderboards.
- If a robustness check fails, paper language is narrowed accordingly.

## Phase 8: Independent Human Audit Plan

Purpose: address the biggest evidence-strength gap, while keeping Codex audits in their proper role.

Actions:

- Design an independent human audit with at least two annotators.
- Include rows from all conditions and task families, oversampling:
  - generated lore;
  - conflicting evidence;
  - active verification;
  - scorer/model disagreement-like cases.
- Blind annotators to model identity where practical.
- Collect labels for:
  - semantic verdict;
  - support-field hygiene;
  - polluted evidence rejection;
  - action executability;
  - exact target;
  - scorer too strict / too lenient.
- Report inter-annotator agreement and adjudication policy.

Deliverables:

```text
reports/eha-uncued-independent-human-audit-runbook-2026-05-25.md
reports/eha-uncued-independent-human-audit-packet-2026-05-25.md
```

Acceptance:

- The paper does not claim independent validation until labels exist.
- Codex audit remains described as local/manual QA.
- If independent audit is completed, update limitations and scorer-audit sections with exact counts and agreement.

## Phase 9: Synthetic Validity And Template Diversity

Purpose: address ecological-validity and template-shortcut concerns.

Actions:

- Measure document length distributions by condition and role.
- Measure title/source-type/timestamp distributions by condition and role.
- Run n-gram/template overlap checks across conditions.
- Document generation templates and randomization knobs.
- Identify any features that could leak condition or role.

Deliverables:

```text
reports/eha-uncued-template-diversity-audit-2026-05-25.md
paper/appendices/template_diversity.tex
```

Acceptance:

- If distributions are imbalanced, paper says so and narrows claims.
- If no obvious shortcut dominates, report this as supporting evidence, not proof of ecological validity.

## Phase 10: Paper Rewrite Pass

Purpose: integrate the above without making the paper too long or too artifact-heavy.

Actions:

- Rewrite abstract to foreground:
  - problem;
  - role-uncued method;
  - core finding;
  - pilot limitations.
- Expand metrics/scoring and examples.
- Add uncertainty intervals.
- Make related work more explicit:
  - fact verification;
  - RAG evaluation;
  - retrieval poisoning;
  - citation faithfulness;
  - agent benchmarks.
- Reduce internal phase numbering in the body.
- Keep artifact/repository notes concise.

Verification:

```bash
cd /Users/chenmohan/gits/ficciones/paper
make pdf

cd /Users/chenmohan/gits/ficciones
git diff --check
pdftotext paper/main.pdf - | rg -n "independent human validation|deployment certification|universal leaderboard"
```

Acceptance:

- Paper no longer depends on readers trusting unexplained scorer internals.
- Main claims remain pilot-scale and diagnostic.
- Artifact concerns are answered by open repository pointers and verifier details, not excessive body text.

## Final Handoff

Write:

```text
reports/eha-uncued-full-paper-strengthening-handoff-2026-05-25.md
```

Include:

- phases completed;
- new analyses run;
- paper files changed;
- verification commands and outcomes;
- remaining limitations;
- what still requires independent human review or larger data.

## Final Acceptance Checklist

- Operational escape is formally specified.
- At least one worked scoring example exists.
- Bootstrap uncertainty is reported by latent-task resampling.
- Active-verification table ambiguity is fixed.
- Leakage and shortcut methods are inspectable.
- Paper body has less internal run-log language.
- Phase 1.1/1.2 schema audit claims remain bounded.
- No independent human validation is claimed before it exists.
- Open-source artifact availability is noted concisely without dominating the paper.
