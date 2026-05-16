# EHA Roadmap Pause Checkpoint

Date: 2026-05-16 12:57 CST

Status: `paused_at_user_request`

This checkpoint pauses experimental advancement for the active roadmap thread. It records the current state, the evidence already produced, and the exact gates that must be cleared before any future API/model work or Step 2 expansion. The project is not being marked as fully scientifically complete; the active working goal is being closed because the user requested a checkpoint pause and allowed goal completion after recording the state.

## Objective Restatement

The active objective was to keep advancing `/Users/chenmohan/Downloads/eha_two_step_roadmap.md`, which decomposes into:

- Step 1 workshop/arXiv v1 readiness: opaque-ID main results, schema sensitivity, formal metrics, baselines, active-verification human audit, artifact package, and controlled diagnostic benchmark framing.
- Step 2 main-paper preparation: larger-scale plan, surface-cue stress design, schema ablation path, human baseline/scorer audit plan, statistical plan, external-validity design, launch gate, venue/deadline, and budget.
- No further model/API spend should happen unless the relevant gates and approvals are explicit.

## Current Gate State

| Gate | Evidence | Status |
| --- | --- | --- |
| Step 1 release readiness | `reports/eha_step1_readiness_check.json`; `artifact/verify_step1_release.sh --allow-blocked` | `blocked` |
| Independent active-verification human audit | `artifact/audits/active_verification_human_audit.csv`; validation reports | `0/50` complete |
| Artifact package and minimal example | `artifact/`; `artifact/reproduce_minimal.sh`; verifier | ready except human audit |
| Surface-cue design review | `reports/eha-step2-surface-cue-design-review-validation-2026-05-16.md` | `0/90` reviewed, `pilot_ready=false` |
| Structural schema repair | v8-v11 reports and critical-risk audit | blocked; best v10 macro-F1 `0.404`, exact-row `0.143` |
| Support-role guard | `reports/eha-step2-phase2s-support-role-guard-2026-05-16.md` | ready as deterministic guard only |
| v12 critical-risk contract | `reports/eha-step2-phase2s-v12-critical-risk-contract-smoke-2026-05-16.md` | no-API heuristic smoke only; no model evidence |
| External validity | `reports/eha-step2-external-validity-design-2026-05-16.md` | design-only |
| Target venue/deadline/budget | `reports/eha-step2-target-context-2026-05-16.md` | incomplete |
| Step 2 launch gate | `reports/eha-step2-launch-gate-2026-05-16.md` | `blocked`, `launch_ready=false` |

## Prompt-To-Artifact Checklist

| Roadmap requirement | Concrete artifact/evidence | Checkpoint decision |
| --- | --- | --- |
| Opaque-ID main experiment is the release source of truth | `artifact/outputs/frontier_main_opaque_predictions.jsonl`; paper tables; readiness gate | done, preserve |
| Old semantic-ID run is not the main result | paper positioning and release-gate checks | done, preserve |
| Generated-lore schema ablation has four variants | `artifact/audits/generated_lore_schema_ablation.csv`; readiness gate | done |
| Operational escape formula and diagnostic metrics are formalized | `paper/sections/02_benchmark_design.tex`; readiness gate | done |
| Baselines include ID-only, metadata-only, heuristic, random, always-insufficient | `artifact/baselines/`; `paper/tables/opaque_baselines.tex` | done |
| Active-verification human audit has 50 rows | audit package exists | package done, labels incomplete |
| Independent human/manual labels are present | validation/readiness reports | missing: `0/50` |
| Artifact package runs minimal example | `artifact/reproduce_minimal.sh`; verifier | done |
| Paper is framed as controlled diagnostic benchmark | paper sections and readiness gates | done |
| Surface-cue stress tests have paired design | generator, 180-task smoke dataset, balance/scoring reports | no-API design handoff done |
| Surface-cue human design review is complete | worksheet/HTML/validation exist | missing: `0/90` reviewed |
| Step 2 schema ablation/repair path exists | Phase 2S v8-v12 reports and tests | partial; model validation still gated |
| Human baseline/scorer audit plan exists | feasibility report | plan only, blocked on Step 1 human audit |
| Statistical plan exists | `reports/eha-step2-statistical-analysis-plan-2026-05-16.md`; `eha-mvp/eha/step2_statistics.py` | scaffold done |
| External-validity slice is scoped | external-validity design report | design-only |
| Target venue/deadline/budget are explicit | target-context template and validation | missing |
| Launch gate aggregates blockers | launch-gate JSON/Markdown | done; currently blocked |

## Last Verification

- `uv run pytest -q`: `194 passed`
- `artifact/verify_step1_release.sh --allow-blocked`: completed local verification and PDF build; readiness remained `blocked`
- `git diff --check`: passed
- `uv run pytest tests/test_step2_target_context.py -q`: `5 passed`

No model-availability tests were repeated, and no new upstream API/model experiment was run after the user requested not to repeat model testing.

## Work Added Immediately Before Pause

- `eha-mvp/eha/step2_target_context.py`: standalone no-API target venue/deadline/budget context validator and report writer.
- `eha-mvp/tests/test_step2_target_context.py`: tests for incomplete/default context, human-review budget requirement, ready context, Markdown boundary, and artifact writing.
- `reports/eha_step2_target_context.json`: incomplete target-context template.
- `reports/eha_step2_target_context_validation.json`: validation summary showing `ready=false`.
- `reports/eha-step2-target-context-2026-05-16.md`: human-readable target context handoff.

This target-context work is a checkpoint aid, not launch approval. The Step 2 launch gate remains blocked.

## Resume Order

1. Complete the independent Step 1 active-verification human audit: 50 rows, all eight labels, `audit_status=human_labeled`, nonblank notes, completed attestation, then run `artifact/finalize_human_audit.sh`.
2. Complete the 90-pair surface-cue human design review and validate it with `uv run eha-validate-surface-cue-design-review --worksheet-path ../reports/surface_cue_design_review_worksheet.csv --out-dir ../reports`.
3. Fill target venue, deadline, decision owner, API budget, and human-review budget in `reports/eha_step2_target_context.json`; regenerate target-context artifacts before any model calls.
4. Only after those gates, decide whether to run a fixed-slice model validation for `evidence_diagnostics_v12_critical_risk_contract`; do not run a full C-only or 500-1000 task expansion first.
5. Re-run `uv run pytest -q`, `artifact/verify_step1_release.sh --allow-blocked` or strict verifier after human labels, and `uv run eha-step2-launch-gate --reports-dir ../reports --eha-mvp-dir . --out-dir ../reports`.

## Non-Claims

- This checkpoint is not a claim that the full roadmap is scientifically complete.
- This checkpoint does not replace independent human validation.
- This checkpoint does not permit new model/API calls.
- This checkpoint does not make Step 2 launch-ready.
