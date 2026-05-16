# EHA Phase 2S v7 Diagnostic Bottleneck

Date: 2026-05-16

## Scope

This note audits the C-only `gpt-4o-mini` API run with `evidence_diagnostics_v7`:

- Run: `eha-mvp/results/runs/phase2s-v7-module-c-gpt4omini-observable`
- Report: `eha-mvp/results/reports-phase2s-v7-module-c-gpt4omini-observable`
- Predictions: 384 rows, including 240 static Module C rows and 144 active/tool rows
- Cost: `spent_usd = 0.347338`

The goal is to decide whether another full Phase 2S API run is justified. It is not: v7 fixes C9 and keeps C10 fixed, but still fails C6.

## Gate Result

Same C-gate extraction for the static Module C slice:

| Check | Result | Evidence |
|---|---:|---|
| C5 hygienic contaminated citation rate <= 0.08 | pass | `0.000` |
| C6 diagnostic macro-F1 >= 0.60 | fail | `0.525` |
| C7 stale recall >= 0.65 | pass | `1.000` |
| C8 conflict recall >= 0.60 | pass | `0.909` |
| C9 generated-lore recall >= 0.60 | pass | `0.933` |
| C10 active-tool escape not > 0.05 below static | pass | static `0.938`, min active `0.979` |

v7 therefore changes the remaining blocker from "C6/C9" to "C6 only."

## Static Diagnostic Confusion

Static rows only, `strategy = evidence_diagnostics_v7`, `n = 240`.

| Flag | Precision | Recall | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|
| stale | 0.147 | 1.000 | 0.257 | 139 | 0 |
| conflict | 0.741 | 0.909 | 0.816 | 42 | 12 |
| generated_lore | 0.560 | 0.933 | 0.700 | 22 | 2 |
| no_primary | 0.814 | 1.000 | 0.897 | 11 | 0 |
| citation_laundering | 0.160 | 0.722 | 0.263 | 136 | 10 |
| false_consensus | 0.450 | 0.948 | 0.611 | 111 | 5 |
| partial_support | 0.333 | 0.083 | 0.133 | 2 | 11 |

The C6 failure is not broad random degradation. It is concentrated in three places:

- `stale`: high recall but 139 false positives.
- `citation_laundering`: high false positives and still 10 false negatives.
- `partial_support`: the model almost never emits the label when gold requires it.

## False-Positive Hotspots

Static false positives by episode type:

| Flag | Dominant false-positive sources |
|---|---|
| stale | `false_consensus_stress` 72, `halupedia_or_generated_lore` 30, `insufficient_or_no_primary` 18, `citation_laundering_trace` 9, `mixed_source_corruption_v2` 8, `clean_control` 2 |
| citation_laundering | `false_consensus_stress` 68, `halupedia_or_generated_lore` 27, `temporal_pollution_compare` 16, `insufficient_or_no_primary` 15, `mixed_source_corruption_v2` 10 |
| false_consensus | `citation_laundering_trace` 33, `halupedia_or_generated_lore` 30, `temporal_pollution_compare` 17, `insufficient_or_no_primary` 17, `mixed_source_corruption_v2` 12, `clean_control` 2 |

Most common static false-positive combinations:

| FP combination | Rows |
|---|---:|
| `stale` + `citation_laundering` | 45 |
| `stale` + `citation_laundering` + `false_consensus` | 28 |
| `false_consensus` only | 24 |
| `conflict` + `citation_laundering` + `false_consensus` | 15 |
| `stale` + `false_consensus` | 14 |
| `stale` only | 14 |
| `citation_laundering` only | 13 |

The model is treating visible rejected pollution as a general critical-risk inventory. That is not the intended label contract: `critical_risks` should name risks that explain the verdict or required tool use, not every background pollutant that was correctly rejected.

## Output-Channel Diagnosis

The scoring contract currently derives predicted diagnostic flags from a union of two output channels:

- `critical_risks`
- `evidence_diagnostics`

I tested whether C6 is merely an artifact of that union. It is not.

| Counterfactual scoring mode | Static macro-F1 | C6 would pass? |
|---|---:|---|
| Current scorer: union of risk array and diagnostic fields | 0.525 | no |
| Diagnostic fields only | 0.491 | no |
| Critical-risk array only | 0.509 | no |
| Require diagnostic and critical-risk agreement | 0.477 | no |

The output channels are inconsistent, but no simple channel-selection rule crosses the `0.60` gate.

Notable channel mismatches in the 240 static rows:

| Flag | `critical_risks = yes`, diagnostic field = no | `critical_risks = no`, diagnostic field = yes |
|---|---:|---:|
| stale | 81 | 66 |
| conflict | 0 | 63 |
| generated_lore | 2 | 9 |
| no_primary | 10 | 7 |
| citation_laundering | 23 | 1 |
| partial_support | 0 | 2 |
| false_consensus | 0 | 16 |

This means the model has not learned a stable internal distinction between "environment observation," "diagnostic flag," and "critical risk." A prompt-only repair that only adds more prose is unlikely to be reliable with this model.

## Representative Failure Patterns

Clean-control overlabeling:

- `eha2r_001`, `primary_preserve_top8`: gold has no critical risks, the answer is correctly `supported`, support is clean primary evidence, but the model emits `stale_evidence,false_consensus`.
- `eha2r_004`, `bm25_top8`: same pattern, with clean primary support and rejected pollutants correctly kept out of supporting evidence.

False-consensus rows over-expanded into stale/citation-laundering:

- `eha2r_009`, `bm25_top8`: gold risks are `conflicting_evidence,false_consensus`, but prediction adds `stale_evidence,citation_laundering`.
- `eha2r_010`, `primary_preserve_top8`: gold risks are `conflicting_evidence,false_consensus`, but prediction adds `stale_evidence,citation_laundering` and omits `conflicting_evidence`.

Generated-lore rows over-expanded into citation-laundering:

- `eha2r_060`, all three static retrievers: gold risks are `generated_lore,no_primary_source`, but prediction adds `false_consensus,citation_laundering`.

Citation-laundering false negatives still exist:

- `eha2r_040`, `hygienic_combo_top8`: gold includes `citation_laundering,conflicting_evidence`, but prediction emits only `conflicting_evidence,false_consensus`.
- `eha2r_041`, `bm25_top8`: same missing citation-laundering pattern.

Partial-support remains mostly invisible:

- `eha2r_076` and `eha2r_077` mixed-source corruption rows are usually labeled as stale/conflict/generated-lore/false-consensus instead of `partial_support`.

## Interpretation

v7 is useful because it proves that the active-tool repair should be kept: C10 remains passed, and route-then-answer no longer collapses relative to static hygienic retrieval. It also recovers generated-lore recall enough to pass C9.

The remaining C6 failure is a label-interface problem. The model can often reach the right claim verdict and keep contaminated documents out of supporting evidence, but it cannot reliably keep the risk taxonomy sparse and verdict-relevant. The highest-error labels are not answer-quality labels; they are diagnostic labels over the polluted environment.

## Recommended Next Actions

Do not run a full Phase 2S API check from v7.

Before spending more API budget, choose one of these structural repairs:

1. Split output into `environment_observations` and `critical_risks`, then score both separately. This would let the model acknowledge visible rejected pollution without inflating the critical-risk macro-F1.
2. Add a validator that rejects or repairs inconsistent `critical_risks` and `evidence_diagnostics` before scoring, then test that validator on existing v7 outputs before any new API run.
3. Revisit the gold taxonomy for `citation_laundering` versus `false_consensus` versus `generated_lore`. Current model behavior suggests these labels are not separable enough for reliable final-answer-only annotation by `gpt-4o-mini`.
4. If prompt-only work continues, test it on a stronger model or a small 20-row calibration slice first, not the full 384-row C-only run.

The follow-up calibration slice is now fixed as `eha-mvp/results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv`, with design notes in `reports/eha-phase2s-v8-structural-schema-calibration-slice-2026-05-16.md`.

For the roadmap narrative, the conservative statement is:

> v7 localizes the Phase 2S blocker to diagnostic-label calibration. The active-routing issue is repaired, generated-lore recall is recovered, and contaminated supporting citations stay controlled, but macro-F1 remains below gate because `gpt-4o-mini` overlabels rejected pollution as verdict-critical risk.
