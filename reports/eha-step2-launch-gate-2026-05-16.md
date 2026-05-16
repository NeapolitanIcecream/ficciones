# EHA Step 2 Launch Gate

Date: 2026-05-16

- Status: `blocked`
- Launch ready: `false`
- Decision: do not launch a Step 2 API pilot or 500-1000 task expansion

This is a no-API launch gate. It is not model evidence and does not substitute for independent human validation.

## Checks

- `step1_release_ready`: `false`
- `surface_cue_design_review_complete`: `false`
- `surface_cue_pilot_ready`: `false`
- `external_validity_api_ready`: `false`
- `deterministic_support_role_validation_ready`: `true`
- `structural_schema_repair_passed`: `false`
- `target_venue_and_budget_defined`: `false`

## Required Next Actions

- complete Step 1 independent human audit
- complete 90-pair surface-cue human design review
- repair critical-risk structural schema; support-role guard is ready but not a substitute
- keep external-validity work design-only until prerequisite gates clear
- define target venue and budget before model calls

## Step 1 Readiness

- Status: `blocked`
- Error: human audit validation is not complete: incomplete
- Error: human audit has fewer than 50 complete rows: 0
- Error: manifest active_verification_human_audit status is incomplete
- Error: manifest active_verification_human_audit n_labeled is 0

## Surface-Cue Design Review

- Status: `incomplete`
- Reviewed pairs: 0 / 90
- Pilot ready: `false`
- Blocker: `missing_label_cells`
- Blocker: `missing_notes`
- Blocker: `review_status_incomplete`

## External Validity

- Status: `design_only`
- API ready: `false`
- Recommended first slice: `semi_real_enterprise_wiki`

## Structural Schema Calibration

| run | n | claim | critical-risk F1 | contaminated support | support-role valid | passed |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini` | 35 | 0.886 | 0.369 | 0.000 | 0.886 | `false` |
| `reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini` | 35 | 0.886 | 0.299 | 0.029 | 0.886 | `false` |
| `reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini` | 35 | 0.886 | 0.404 | 0.086 | 0.857 | `false` |
| `reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini` | 35 | 0.857 | 0.240 | 0.000 | 0.857 | `false` |

## Deterministic Support-Role Guard

- Status: `ready`
- Guard ready: `true`
- Recommended run: `reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini`
- Allow rate: `0.857`
- Invalid accepted rate: `0.000`

## Critical-Risk Repair Audit

- Status: `blocked`
- Repair ready: `false`
- Best current run: `reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini`
- Critical-risk macro-F1: `0.404`
- Exact-row rate: `0.143`

## v12 Critical-Risk Contract Smoke

- Status: `no_api_smoke_complete`
- Prompt: `evidence_diagnostics_v12_critical_risk_contract`
- Backend: `heuristic`
- Predictions: `35`
- Report completed: `true`
- Model evidence: `false`
- API calls: `0`
- Gate scope: `partial`
- Gate passed: `false`

## Non-Claims

- not model evidence
- not a substitute for Step 1 human validation
- not permission to run a 500-1000 task expansion
