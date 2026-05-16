# EHA Step 2 Phase 2S v12 Critical-Risk Contract Smoke

Date: 2026-05-16

- Status: `no_api_smoke_complete`
- Model evidence: `false`
- API calls: `0`
- Cost: `0.0`

This smoke run validates that `evidence_diagnostics_v12_critical_risk_contract` can pass through the fixed Module C calibration-slice runner, emit Phase 2S-shaped predictions, and feed the existing scorer/report pipeline. It uses the deterministic `heuristic` backend only and must not be read as evidence that an upstream model satisfies the v12 contract.

## Inputs

- Calibration slice: `eha-mvp/results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv`
- Run output: `eha-mvp/results/runs/phase2s-v12-critical-risk-contract-calibration-slice-heuristic`
- Report output: `eha-mvp/results/reports-phase2s-v12-critical-risk-contract-calibration-slice-heuristic`
- Prompt/schema: `evidence_diagnostics_v12_critical_risk_contract`
- Backend/model label: `heuristic` / `heuristic-sim`

## Smoke Result

| check | result |
| --- | --- |
| predictions written | 35 |
| report pipeline completed | yes |
| parse success | 1.000 |
| tool parse success | 1.000 |
| direct critical-risk macro-F1 | 1.000 |
| contaminated citation rate | 0.000 |
| cost | 0.000 |

The Phase 2S gate reports `scope = partial` and `passed = false` because this smoke intentionally runs Module C only. That is expected for a partial pipeline check and is not a launch approval.

## Support-Role Smoke Metrics

| retriever | n | claim_accuracy | support_role_valid_rate | support_role_clean_only_rate | support_role_contaminated_doc_rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25_top8 | 16 | 1.000 | 0.812 | 1.000 | 0.000 |
| hygienic_combo_top8 | 9 | 1.000 | 1.000 | 1.000 | 0.000 |
| primary_preserve_top8 | 10 | 1.000 | 1.000 | 1.000 | 0.000 |

The three `bm25_top8` support-role failures are not contaminated-support failures; they are missing clean verdict-direct evidence on false-consensus rows in the deterministic heuristic path.

## Non-Claims

- This is not a new model run.
- This does not validate v12 against `gpt-4o-mini`, `gpt-5.4`, or any other upstream model.
- This does not unblock the Step 2 launch gate.
- This does not replace the independent Step 1 human audit or the 90-pair surface-cue design review.
