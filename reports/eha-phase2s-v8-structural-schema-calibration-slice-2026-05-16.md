# EHA Phase 2S v8 Structural-Schema Calibration Slice

Date: 2026-05-16

## Purpose

This is the fixed input slice for the next Phase 2S structural-schema repair. It is derived from the v7 C-only API run and is meant to test whether a new schema can separate:

- visible polluted-environment observations; from
- sparse verdict-critical risks.

Do not treat this slice as a representative benchmark estimate. It is deliberately enriched for v7 failure modes so that a v8 prompt/schema cannot pass by only preserving easy rows.

## Source

- Source run: `eha-mvp/results/runs/phase2s-v7-module-c-gpt4omini-observable`
- Source report: `eha-mvp/results/reports-phase2s-v7-module-c-gpt4omini-observable`
- Slice CSV: `eha-mvp/results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv`
- Rows: 35 static Module C rows
- Coverage: 7 episode types x 5 rows each

## Slice Composition

| Episode type | Rows | Why included |
|---|---:|---|
| `clean_control` | 5 | Checks that visible rejected pollutants do not inflate critical risks. |
| `false_consensus_stress` | 5 | Tests same-root repetition versus citation laundering, generated lore, and no-primary. |
| `citation_laundering_trace` | 5 | Preserves true citation-laundering positives and false-negative cases. |
| `temporal_pollution_compare` | 5 | Tests stale-only rows that v7 over-expanded into conflict/citation-laundering/false-consensus. |
| `halupedia_or_generated_lore` | 5 | Tests generated-lore/no-primary rows that v7 over-expanded into citation-laundering and false-consensus. |
| `insufficient_or_no_primary` | 5 | Tests no-primary rows that v7 sometimes turned into refuted conflict/generated-lore cases. |
| `mixed_source_corruption_v2` | 5 | Tests partial-support rows, the weakest v7 recall point. |

## v7 Baseline On This Slice

Because the slice is failure-enriched, v7 scores are lower than the full static C slice:

| Metric | Value |
|---|---:|
| Rows | 35 |
| Claim accuracy | 0.800 |
| Contaminated supporting citation rate | 0.000 |
| Diagnostic macro-F1 | 0.393 |

Per-flag confusion:

| Flag | Precision | Recall | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|
| stale | 0.200 | 1.000 | 0.333 | 20 | 0 |
| conflict | 0.333 | 0.700 | 0.452 | 14 | 3 |
| generated_lore | 0.250 | 0.600 | 0.353 | 9 | 2 |
| no_primary | 0.833 | 1.000 | 0.909 | 2 | 0 |
| citation_laundering | 0.083 | 0.400 | 0.138 | 22 | 3 |
| false_consensus | 0.161 | 1.000 | 0.278 | 26 | 0 |
| partial_support | 0.500 | 0.200 | 0.286 | 1 | 4 |

The repair target is not just a higher macro-F1. It should specifically reduce over-expanded `stale`, `citation_laundering`, and `false_consensus` while improving `partial_support` recall.

## Required v8 Output Contract

The implemented structural schema splits observations from verdict-critical risks:

```text
environment_observations:
  visible_stale_or_superseded_material
  visible_conflicting_material
  visible_generated_or_synthetic_lore
  visible_reposts_or_same_root_repetition
  visible_citation_chain_problem
  visible_partial_or_scope_limited_support

critical_risks:
  stale_evidence
  conflicting_evidence
  generated_lore
  no_primary_source
  citation_laundering
  false_consensus
  partial_support
```

Expected behavior:

- `environment_observations` may mention visible rejected pollutants.
- `critical_risks` should only name risks that explain the verdict or required tool use.
- Clean controls with clean primary support should keep `critical_risks = []`, even when rejected pollutants are visible.
- Same-root repetition is not automatically citation laundering.
- Generated lore/no-primary is not automatically citation laundering.
- Stale evidence is not automatically conflict or citation laundering.
- Partial support should be explicit when the claim's scope or strength is only partially established.

## Initial Success Criteria

For a first 35-row calibration run, use these criteria before spending on a full 384-row C-only run:

| Metric | Minimum |
|---|---:|
| critical-risk macro-F1 | 0.60 |
| stale critical-risk precision | 0.50 |
| citation-laundering critical-risk precision | 0.50 |
| false-consensus critical-risk precision | 0.50 |
| generated-lore critical-risk recall | 0.80 |
| partial-support critical-risk recall | 0.50 |
| contaminated supporting citation rate | <= 0.08 |

Also report observation recall separately. A model should be allowed to observe visible pollution without putting every observed issue into `critical_risks`.

## Implementation Status

The runner and prompt layer now support this slice and the structural output contract:

- `--calibration-slice PATH` filters Module C to the listed static `(task_id, retriever)` rows and skips active-tool rows.
- `evidence_diagnostics_v8_structural` requires `environment_observations` in the JSON schema and preserves legacy output parsing for older prompts.
- `evidence_diagnostics_v9_structural_recall` keeps the same structural schema and adds recall-focused wording for true citation-laundering, false-consensus, and partial-support blockers.
- `evidence_diagnostics_v10_structural_contract` keeps the structural schema and adds a decision table for when same-root repetition, failed citation chains, partial support, stale support, generated lore, no-primary, and direct contradiction should enter `critical_risks`.
- `evidence_diagnostics_v11_role_disciplined_contract` keeps the v10 decision table and adds a hard role gate: polluted, failed-support, stale, generated, corrupted, or no-primary documents must not enter `supporting_evidence`; if no clean verdict-direct evidence is visible, `supporting_evidence` should be empty.
- The Phase 2S report now writes `critical_risk_confusion_by_flag.csv` for direct `critical_risks` scoring, `observation_confusion_by_flag.csv` derived from visible `final_doc_ids` and gold document metadata, and `support_role_metrics.csv` / `support_role_failures.csv` for independent `supporting_evidence` role validity.
- `uv run pytest tests/test_phase2s.py -q`: 28 passed.
- `uv run pytest -q`: 194 passed.

## Selected Rows

The machine-readable row list is in the CSV file. The row IDs are stable for v8 calibration:

| Range | Episode type |
|---|---|
| `cal_001`-`cal_005` | `clean_control` |
| `cal_006`-`cal_010` | `false_consensus_stress` |
| `cal_011`-`cal_015` | `citation_laundering_trace` |
| `cal_016`-`cal_020` | `temporal_pollution_compare` |
| `cal_021`-`cal_025` | `halupedia_or_generated_lore` |
| `cal_026`-`cal_030` | `insufficient_or_no_primary` |
| `cal_031`-`cal_035` | `mixed_source_corruption_v2` |

## Heuristic Smoke Commands

The runner now supports `--calibration-slice`, which runs only the listed static Module C `(task_id, retriever)` rows and skips active-tool rows. Heuristic smoke runs for v8, v9, v10, and v11 each wrote 35 predictions and 35 retrieval metric rows; the v8 command shape is:

```bash
uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend heuristic \
  --models heuristic-sim \
  --modules C \
  --final-diagnostic-prompt evidence_diagnostics_v8_structural \
  --calibration-slice results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv \
  --out-dir results/runs/phase2s-v8-structural-schema-calibration-slice-heuristic-v8 \
  --max-output-tokens 3000
```

## API Calibration Results

Both API slices used `gpt-4o-mini`, omitted `temperature`, used `max-output-tokens = 3000`, and ran exactly the 35 static C rows.

| Run | Output path | Report path | Cost | Claim accuracy | Contaminated citation rate | Direct critical-risk macro-F1 | Observation macro-F1 | Support-role valid rate | Interpretation |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| v8 structural | `eha-mvp/results/runs/phase2s-v8-structural-schema-calibration-slice-gpt4omini` | `eha-mvp/results/reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini` | 0.031281 | 0.886 | 0.000 | 0.369 | 0.574 | 0.886 | clean controls stay risk-empty, but citation-laundering, false-consensus, and partial-support critical recall are 0 |
| v9 structural-recall | `eha-mvp/results/runs/phase2s-v9-structural-recall-calibration-slice-gpt4omini` | `eha-mvp/results/reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini` | 0.033729 | 0.886 | 0.029 | 0.299 | 0.643 | 0.886 | observation reporting improves, but the direct critical-risk contract is still not followed |
| v10 structural-contract | `eha-mvp/results/runs/phase2s-v10-structural-contract-calibration-slice-gpt4omini` | `eha-mvp/results/reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini` | 0.034349 | 0.886 | 0.086 | 0.404 | 0.666 | 0.857 | direct critical-risk macro-F1 improves, but contaminated citation crosses the 0.08 threshold |
| v11 role-disciplined contract | `eha-mvp/results/runs/phase2s-v11-role-disciplined-calibration-slice-gpt4omini` | `eha-mvp/results/reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini` | 0.037478 | 0.857 | 0.000 | 0.240 | 0.582 | 0.857 | hard supporting-evidence gate restores citation cleanliness but suppresses stale, citation-laundering, and partial-support critical recall |

Observation fields are present in 35/35 API outputs for v8, v9, v10, and v11. The structural output format works mechanically, but all four prompts miss the `0.60` direct-risk target. v10 gives the best direct critical-risk macro-F1 at `0.404` but fails the contaminated-citation threshold; v11 restores contaminated citation to `0.000` but drops direct critical-risk macro-F1 to `0.240`. Do not run the full C-only 384-row API job from these prompts.

The regenerated report path now quantifies support-role validity independently from critical-risk labels. Across the 35-row slice, support-role valid rates are v8 `0.886`, v9 `0.886`, v10 `0.857`, and v11 `0.857`; clean-only rates are v8 `1.000`, v9 `0.971`, v10 `0.914`, and v11 `1.000`. This confirms the tradeoff rather than replacing it: v10 improves critical labels while weakening support-role cleanliness, and v11 fixes clean-only support while losing critical-risk recall and claim accuracy. The next repair should not be another wording-only prompt. It should make support-role validation and risk-label validation separate contractual surfaces, or add a deterministic post-hoc role validator before spending on a full C-only run.
