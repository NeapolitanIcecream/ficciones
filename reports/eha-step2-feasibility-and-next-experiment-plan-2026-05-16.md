# EHA Step 2 Feasibility And Next Experiment Plan

Date: 2026-05-16

## Purpose

This note converts `/Users/chenmohan/Downloads/eha_two_step_roadmap.md` into the next non-duplicative work plan after the Step 1 package and Phase 2S v7 diagnostic audit.

The current decision is conservative:

- Do not claim Step 1 is complete until the independent active-verification human audit has 50 completed rows and a completed attestation.
- Do not start a 500-1000 task Step 2 expansion yet.
- Do not run another full Phase 2S API check from v7.
- Use the current waiting period to make the Step 2 design sharper and to isolate the structural schema repair needed before larger spending.

## Current State

Step 1 release readiness is blocked only by independent human labels:

- `reports/eha_step1_readiness_check.json`: `status = blocked`
- active-verification human audit: 50 rows, 0 complete rows
- `artifact/verify_step1_release.sh --allow-blocked`: passes with readiness status `blocked`

Phase 2S now has a localized blocker:

- v7 C-only API run: 384 predictions, `spent_usd = 0.347338`
- C5, C7, C8, C9, and C10 pass
- C6 fails: static diagnostic macro-F1 `0.525 < 0.60`
- Bottleneck report: `reports/eha-phase2s-v7-diagnostic-bottleneck-2026-05-16.md`
- v8-v11 35-row structural calibration slices have now run; the structural field is emitted, support-role validity is now scored separately, but none passes the small-slice critical-risk and citation-cleanliness criteria.
- A no-API Step 2 surface-cue smoke generator now exists at `eha-mvp/eha/surface_cue_generate.py`, with 180 tasks / 900 documents / 30 exact active-verification action-gold rows in `eha-mvp/data/phase2-surface-cue-smoke`; reports are `reports/eha-step2-surface-cue-smoke-2026-05-16.md`, `reports/eha-step2-surface-cue-balance-2026-05-16.md`, `reports/eha-step2-surface-cue-scoring-pipeline-2026-05-16.md`, and `reports/eha-step2-surface-cue-design-review-packet-2026-05-16.md`.
- A Step 2 statistical analysis contract now exists at `reports/eha-step2-statistical-analysis-plan-2026-05-16.md`, with executable task-cluster bootstrap and paired-permutation scaffolding in `eha-mvp/eha/step2_statistics.py`.
- A no-API external-validity design contract now exists at `reports/eha-step2-external-validity-design-2026-05-16.md`, with four candidate slices and explicit gates that keep it design-only until Step 1 human audit and surface-cue design review are complete.
- A no-API deterministic Phase 2S support-role guard now exists at `reports/eha-step2-phase2s-support-role-guard-2026-05-16.md` and `reports/eha_step2_phase2s_support_role_guard.json`; it passes as a consumer-safety validation over already scored v8-v11 rows, but it is not new model evidence and does not repair wrong verdicts or missing critical-risk labels.
- A no-API Phase 2S critical-risk repair audit now exists at `reports/eha-step2-phase2s-critical-risk-audit-2026-05-16.md` and `reports/eha_step2_phase2s_critical_risk_audit.json`; it decomposes v8-v11 failures into exact rows, false negatives, false positives, and mixed errors. It is blocked: the best current run is v10 with critical-risk macro-F1 `0.404` and exact-row rate `0.143`.
- A no-API v12 prompt/schema contract is now implemented as `evidence_diagnostics_v12_critical_risk_contract`. It keeps the v11 support-role hard gate and adds explicit positive/negative boundaries for `false_consensus`, `citation_laundering`, `partial_support`, `conflicting_evidence`, and `stale_evidence`. A deterministic no-API heuristic smoke over the fixed 35-row Module C calibration slice now completes and writes 35 scoreable predictions, but this has not been run against a model and is not model evidence.
- A no-API Step 2 launch gate now exists at `reports/eha-step2-launch-gate-2026-05-16.md` and `reports/eha_step2_launch_gate.json`; it reads the actual Step 1 readiness, surface-cue design-review validation, external-validity design, support-role guard, critical-risk repair audit, and v8-v11 structural calibration outputs and currently blocks API pilot / 500-1000 task expansion.

The Phase 2S result is useful for Step 2 because it shows that active-tool routing and generated-lore recall can be repaired, while the remaining failure is a schema/taxonomy problem around diagnostic labels.

## Prompt-To-Artifact Checklist For The Roadmap

| Roadmap requirement | Current evidence | Status | Next action |
|---|---|---|---|
| Step 1: opaque-ID main experiment only | `artifact/outputs/frontier_main_opaque_predictions.jsonl`, `reports/eha_step1_readiness_check.json` | ready except human audit | Keep as release source of truth. |
| Step 1: four-schema generated-lore ablation | `artifact/audits/generated_lore_schema_ablation.csv`, readiness gate | done | No more Step 1 API needed. |
| Step 1: operational escape formula and diagnostic metrics | `paper/sections/02_benchmark_design.tex`, readiness gate | done | Preserve in v1 paper. |
| Step 1: baselines | `artifact/baselines/`, `paper/tables/opaque_baselines.tex` | done | Preserve corrected baseline values. |
| Step 1: 50-row active-verification human audit | `artifact/audits/active_verification_human_audit.csv` | blocked | Needs independent human/manual labels; Codex must not substitute labels. |
| Step 1: artifact package and minimal example | `artifact/`, `artifact/reproduce_minimal.sh` | done | Rerun final verifier after human labels. |
| Step 2: 500-1000 tasks | no Step 2 expanded dataset yet | not started | Wait until Step 1 release/feedback and schema repair decision. |
| Step 2: surface-cue stress tests | no-API 6-family x 3-template x 5-axis x 2-condition smoke generator, dataset, exact active-verification action gold, balance report, scoring-pipeline baselines, and design-review worksheet exist | review handoff ready | Complete 90-pair human design review before any API run. |
| Step 2: full schema ablation | Step 1 generated-lore-only ablation exists; Phase 2S v7 exposes C-label schema issue; v8-v11 structural slices are negative; deterministic support-role guard is ready; critical-risk repair audit is blocked with v10 best at macro-F1 0.404 / exact-row 0.143; v12 critical-risk contract is implemented and has a no-API heuristic smoke, but no model evidence | partial design evidence | Validate v12 on the fixed 35-row slice only after human/design gates or explicit approval. |
| Step 2: human baseline / scorer audit | Step 1 active-verification audit package exists but labels incomplete | not ready | Complete Step 1 human audit first; then design 100-200 task human baseline. |
| Step 2: statistical plan | `reports/eha-step2-statistical-analysis-plan-2026-05-16.md` plus `eha-mvp/eha/step2_statistics.py` and tests for task-cluster bootstrap / paired permutation | scaffold done | Add mixed-effects implementation only after scaled scored rows exist. |
| Step 2: external validity slice | design-only contract exists with semi-real enterprise wiki, open-web-like synthetic, human-written pollutant, and adaptive generated-lore candidates | design scoped | Do not generate a dataset or run API until Step 1 human audit and surface-cue human design review are complete. |
| Step 2: launch gate | `reports/eha-step2-launch-gate-2026-05-16.md` and `reports/eha_step2_launch_gate.json` aggregate Step 1 readiness, surface-cue review, external-validity design, deterministic support-role validation, critical-risk repair audit, structural schema repair, venue, and budget checks | blocked | Do not launch API pilot or 500-1000 task expansion. |

## Feasibility Assessment

### What Is Ready

The project is ready for a controlled diagnostic Step 1 release once human labels are complete:

- Opaque ID leakage is gated.
- Main tables are recomputed from opaque-run outputs.
- Generated-lore schema sensitivity is already a defensible finding.
- Baselines and minimal reproducibility are packaged.
- Paper framing already avoids universal benchmark and provider-leaderboard claims.

The project is not ready for the Step 2 scale-up yet, mainly because the Phase 2S v7 result shows that the current diagnostic label interface is too entangled for reliable large-scale scoring.

### What Is Not Ready

The next Step 2 blocker is not task count. It is measurement validity:

- `critical_risks` mixes verdict-critical risks with general observations about rejected pollution.
- `evidence_diagnostics` and `critical_risks` disagree frequently.
- `stale`, `citation_laundering`, and `false_consensus` are over-applied to rows where rejected pollutants are visible but not verdict-critical.
- `partial_support` is under-applied in mixed-source corruption rows.

Scaling this schema to 500-1000 tasks would make the dataset larger but not necessarily more valid.

The support-role side of this problem is now separated from the critical-risk side. The no-API guard report accepts only rows whose `supporting_evidence` is clean-only and verdict-direct, and blocks rows with contaminated support, unknown support, extraneous support, non-empty support on an insufficient verdict, or no verdict-direct support. On the v11 slice it allows 30/35 rows, blocks 5/35 as not verdict-direct, and accepts 0 invalid rows. This is enough to say the support-role consumption guard is ready for future scored rows, but not enough to launch Step 2 because the critical-risk macro-F1 remains far below the small-slice threshold.

The critical-risk side now has a no-API repair audit. It shows no structural variant is close to ready: exact critical-risk rows range from 5/35 to 9/35, false-negative row rates are 0.543-0.743, and false-positive row rates are 0.457-0.600. v10 is the best current run by macro-F1 (`0.404`) but also crosses the contaminated-support threshold (`0.086 > 0.08`) and has only 5 exact rows. The next contract is now codified as `evidence_diagnostics_v12_critical_risk_contract`: it adds explicit positive and negative examples for `false_consensus`, `citation_laundering`, and `partial_support`, keeps the v11 support-role hard gate, and states whether visible rejected pollution is only an environment observation or a verdict-critical risk. Its deterministic no-API heuristic smoke is complete, but model validation remains unrun until a future fixed-slice validation is explicitly approved.

## Next Experiment: Structural Schema Repair

Before any full Phase 2S or Step 2 expansion, test a structural split:

```text
environment_observations:
  visible_stale_or_superseded_material
  visible_conflicting_material
  visible_generated_or_synthetic_lore
  visible_reposts_or_same_root_repetition
  visible_citation_chain_problem
  visible_partial_or_scope-limited_support

critical_risks:
  stale_evidence
  conflicting_evidence
  generated_lore
  no_primary_source
  citation_laundering
  false_consensus
  partial_support
```

Scoring principle:

- `environment_observations` may acknowledge all visible pollution, including correctly rejected documents.
- `critical_risks` should be sparse and verdict-relevant.
- C6 should be computed separately for environment-observation recall and critical-risk precision/recall.
- A row should not fail critical-risk precision merely because the model noticed rejected pollution in the environment-observation field.

Minimal validation path:

1. Implement a new schema/prompt variant on a small C-only calibration slice, not the full 384-row C-only run. Done for v8-v11.
2. Use a balanced slice of 20-40 rows covering clean, false-consensus, citation-laundering, generated-lore, no-primary, temporal, and partial-support cases. Done with the fixed 35-row slice.
3. Run one cheap model first, then one stronger model only if the cheap run indicates the schema can separate observations from risks. The cheap `gpt-4o-mini` v8-v11 runs are negative.
4. Gate on all three:
   - critical-risk macro-F1
   - observation recall for visible pollution types
   - support-role validity for `supporting_evidence`, now with the deterministic guard reported separately
5. Only then consider a full C-only run.

Suggested success criteria for the small slice:

| Metric | Minimum |
|---|---:|
| critical-risk macro-F1 | 0.60 |
| stale critical-risk precision | 0.50 |
| citation-laundering critical-risk precision | 0.50 |
| generated-lore critical-risk recall | 0.80 |
| partial-support recall | 0.50 |
| observation recall for visible pollution | 0.80 |
| contaminated supporting citation rate | <= 0.08 |
| support-role valid rate | >= 0.95 |

## Surface-Cue Stress Test Design

Do not generate the full stress suite yet. First implement generator switches that can produce paired rows. A small no-API smoke version is now implemented:

- Generator: `eha-mvp/eha/surface_cue_generate.py`
- Output: `eha-mvp/data/phase2-surface-cue-smoke`
- Report: `reports/eha-step2-surface-cue-smoke-2026-05-16.md`
- Balance report: `reports/eha-step2-surface-cue-balance-2026-05-16.md`
- Scoring report: `reports/eha-step2-surface-cue-scoring-pipeline-2026-05-16.md`
- Design-review packet: `reports/eha-step2-surface-cue-design-review-packet-2026-05-16.md`
- Design-review worksheet: `reports/surface_cue_design_review_worksheet.csv`
- Design-review HTML: `reports/surface_cue_design_review.html`
- Design-review launcher: `reports/serve_surface_cue_design_review.sh`
- Design-review validation: `reports/eha-step2-surface-cue-design-review-validation-2026-05-16.md`
- Scale: 180 tasks, 900 documents, 360 graph edges, 30 active-verification action-gold rows
- Test: `uv run pytest tests/test_surface_cue_generate.py tests/test_surface_cue_report.py tests/test_surface_cue_score.py tests/test_surface_cue_design_review.py -q`

| Stress axis | Paired condition | Purpose |
|---|---|---|
| source-type visibility | visible vs hidden | Tests whether models rely on explicit source labels. |
| metadata perturbation | truthful vs shuffled timestamps/title authority | Tests source-cue brittleness. |
| style normalization | original vs normalized tone | Tests whether official-sounding prose drives judgments. |
| adversarial spoofing | plain pollutant vs regulator/audit-style pollutant | Tests authority-cue vulnerability. |
| content-only baseline | full evidence vs metadata-stripped content | Separates source reasoning from metadata shortcuts. |

The smoke generator uses deterministic paired task IDs and gold labels, keeps pair-level verdicts fixed, covers conflict, stale, partial, generated-lore, no-primary, and active-verification families with three claim templates per family, checks `bm25_top8` observability for clean support when present and false-support documents in every row, writes exact active-verification action targets, and rejects hidden-label leakage in model-visible task/document payloads. The no-API balance report shows 0 pair-contract violations, 0 visible-leakage hits, 0 action-target violations, 120/120 clean-support observable rows, and 180/180 contaminated-observable rows. The scoring-pipeline report writes 540 no-API Phase 2S-shaped baseline rows: the oracle contract validates the scorer path, always-insufficient gives a conservative floor, and source-type prior reaches only 0.500 claim accuracy while adding contaminated support under metadata perturbation and adversarial spoofing. The design-review handoff now has 90 pair-level worksheet rows, 6 required yes/no labels per row, a browser review page, and a local launcher; validation reports `incomplete`, 0 reviewed pairs, 540 missing label cells, 90 missing notes, and `pilot_ready=false`. This is design evidence only: the templates are synthetic smoke cases and still need completed human design review before any model/API run.

To conduct the review locally:

```bash
cd reports
./serve_surface_cue_design_review.sh
```

After downloading the completed worksheet, validate it with:

```bash
cd eha-mvp
uv run eha-validate-surface-cue-design-review --worksheet-path ../reports/surface_cue_design_review_worksheet.csv --out-dir ../reports
```

## Human Baseline Path

The Step 1 human audit should be completed before designing the Step 2 human baseline. Reuse its machinery:

- local HTML review page
- model-blinded worksheet
- strict CSV validation
- attestation
- finalization script

Step 2 human baseline should be larger and task-facing, not just scorer-facing:

| Human task | Suggested sample |
|---|---:|
| verdict | 100-200 tasks |
| clean support selection | same rows |
| rejected evidence labeling | same rows |
| useful verification action | active-verification subset |
| scorer audit of model rows | 200 model outputs |

Do not report Step 2 human results without at least one independent human/manual annotator and a completed attestation. If two annotators are available, add agreement; otherwise state single-auditor pilot status.

## Statistical Plan

Before scaling, use the statistical contract in `reports/eha-step2-statistical-analysis-plan-2026-05-16.md`. A first executable scaffold exists in `eha-mvp/eha/step2_statistics.py` for task-cluster bootstrap summaries and paired permutation tests. The plan requires:

- task-cluster bootstrap confidence intervals, with pair-level resampling for paired stress/schema contrasts;
- paired permutation tests for model, prompt, schema, and surface-cue comparisons on the same tasks or pairs;
- prompt/schema effect confidence intervals;
- mixed-effects robustness models with model, condition, family, schema, stress axis, task, seed, and pair factors when enough data exist;
- explicit multiple-comparison boundaries distinguishing pre-specified headline contrasts from exploratory tables.

The main Step 2 table should report `mean [95% CI low, 95% CI high]`, not only three-decimal point estimates. Passing this planning step does not make current Step 1 data statistically powered for provider ranking.

## Go / No-Go Criteria

Step 2 expansion should not start until all are true:

- Step 1 human audit is complete or the project explicitly decides to release v1 as incomplete-pilot only.
- The structural schema repair passes a small C-only calibration slice; the deterministic support-role guard is ready, but this does not satisfy the critical-risk repair requirement.
- The critical-risk repair audit reaches its small-slice thresholds: macro-F1 >= 0.60, exact-row rate >= 0.60, claim accuracy >= 0.85, and contaminated supporting citation rate <= 0.08.
- Surface-cue paired generators have completed human design review beyond the current synthetic multi-template smoke dataset and no-API scoring scaffold.
- A budget exists for at least one human baseline/scorer-audit pass.
- The target venue and deadline are explicit.

The small structural-schema calibration has now replaced task-scale expansion as the next evidence point; it was intentionally run before any full v7 rerun or 500-1000 task expansion.

The fixed 35-row calibration slice for that experiment is now defined in:

- `eha-mvp/results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv`
- `reports/eha-phase2s-v8-structural-schema-calibration-slice-2026-05-16.md`

It covers seven episode types with five rows each and is intentionally enriched for v7 overlabeling and partial-support failures.

The Phase 2S runner now supports this slice with `--calibration-slice`; heuristic smoke runs wrote 35 static C predictions and 35 retrieval metric rows for `evidence_diagnostics_v8_structural`, `evidence_diagnostics_v9_structural_recall`, `evidence_diagnostics_v10_structural_contract`, and `evidence_diagnostics_v11_role_disciplined_contract`.

The first API structural-slice attempts are complete:

| Run | Rows | Cost | Claim accuracy | Contaminated citation rate | Direct critical-risk macro-F1 | Support-role valid rate | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| v8 structural | 35 | 0.031281 | 0.886 | 0.000 | 0.369 | 0.886 | no-go for full C-only run |
| v9 structural-recall | 35 | 0.033729 | 0.886 | 0.029 | 0.299 | 0.886 | no-go for full C-only run |
| v10 structural-contract | 35 | 0.034349 | 0.886 | 0.086 | 0.404 | 0.857 | no-go for full C-only run |
| v11 role-disciplined contract | 35 | 0.037478 | 0.857 | 0.000 | 0.240 | 0.857 | no-go for full C-only run |

The report path now includes direct `critical_risks` scoring, explicit gold scoring for `environment_observations`, support-role scoring for `supporting_evidence`, a deterministic support-role guard, and a critical-risk repair audit. v8 observation macro-F1 is `0.574`, v9 improves it to `0.643`, v10 reaches `0.666`, and v11 falls back to `0.582`. The support-role guard report shows v11 has 0 contaminated-support rows, 0 unknown-support rows, 0 non-empty-insufficient rows, 5 not-verdict-direct blocks, and 0 invalid accepted rows. The critical-risk audit shows the best current variant is v10, but still only reaches macro-F1 `0.404` and exact-row rate `0.143`; v11 preserves support cleanliness but drops macro-F1 to `0.240`. This updates the recommendation: the next useful Step 2 preparation is not another full API run and not another wording-only prompt. v10 shows that better critical-risk recall can reintroduce contaminated supporting citations; v11 shows that a hard evidence-role gate can restore citation cleanliness and clean-only support lists, but still suppresses critical-risk recall. The next design should repair critical-risk diagnosis while keeping support-role validation as an independently checked contract.

## Recommended Reader-Facing Framing

For the Step 1 paper:

> EHA v1 is a controlled diagnostic benchmark and mechanism study. It shows that answer correctness, evidence-role cleanliness, uncertainty discipline, and verification-action executability can diverge in polluted evidence environments.

For the Step 2 proposal:

> The main-conference version should test whether these diagnostic findings scale under larger task coverage, stronger surface-cue controls, broader schema ablations, human baselines, and inferential statistics.

For the Phase 2S v7 result:

> v7 localizes the remaining blocker to diagnostic-label calibration. The active-tool repair works, generated-lore recall recovers, and contaminated support remains controlled, but final-answer-only risk labels over-expand rejected pollution into verdict-critical risks.
