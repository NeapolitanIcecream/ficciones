# EHA Phase 2S Scope Diagnosis & Temporal Routing Repair Summary

## 1. Gate Result

```json
{
  "scope": "partial",
  "passed": false,
  "checks": {},
  "details": {
    "modules": [
      "C"
    ]
  }
}
```

## 2. Module A Prompt Comparison

_No rows._

## 3. Direct Critical-Risk Labels

Direct critical-risk macro-F1: `1.000`

| risk | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale_evidence | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |
| conflicting_evidence | 10 | 0 | 0 | 25 | 1.000 | 1.000 | 1.000 |
| generated_lore | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |
| no_primary_source | 10 | 0 | 0 | 25 | 1.000 | 1.000 | 1.000 |
| citation_laundering | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |
| false_consensus | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |
| partial_support | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |

## 4. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |
| conflict | 10 | 0 | 0 | 25 | 1.000 | 1.000 | 1.000 |
| generated_lore | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |
| no_primary | 10 | 0 | 0 | 25 | 1.000 | 1.000 | 1.000 |
| citation_laundering | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |
| false_consensus | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |
| partial_support | 5 | 0 | 0 | 30 | 1.000 | 1.000 | 1.000 |

## 5. Structural Environment Observations

Observation macro-F1: `0.000`

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| visible_stale_or_superseded_material | 0 | 0 | 10 | 25 | 1.000 | 0.000 | 0.000 |
| visible_conflicting_material | 0 | 0 | 35 | 0 | 1.000 | 0.000 | 0.000 |
| visible_generated_or_synthetic_lore | 0 | 0 | 10 | 25 | 1.000 | 0.000 | 0.000 |
| visible_reposts_or_same_root_repetition | 0 | 0 | 35 | 0 | 1.000 | 0.000 | 0.000 |
| visible_citation_chain_problem | 0 | 0 | 5 | 30 | 1.000 | 0.000 | 0.000 |
| visible_partial_or_scope_limited_support | 0 | 0 | 5 | 30 | 1.000 | 0.000 | 0.000 |

## 6. Supporting-Evidence Role Validity

`support_role_valid_rate` requires clean-only evidence and verdict-direct support; `support_role_clean_only_rate` is reported separately so evidence-list cleanliness is not inferred from critical-risk labels.

| module | retriever | strategy | n | claim_accuracy | support_role_valid_rate | support_role_clean_only_rate | support_role_verdict_direct_rate | support_role_contaminated_doc_rate | support_role_missing_clean_verdict_evidence_rate | support_role_nonempty_for_insufficient_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | bm25_top8 | evidence_diagnostics_v12_critical_risk_contract | 16 | 1.000 | 0.812 | 1.000 | 0.812 | 0.000 | 0.188 | 0.000 |
| C | hygienic_combo_top8 | evidence_diagnostics_v12_critical_risk_contract | 9 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| C | primary_preserve_top8 | evidence_diagnostics_v12_critical_risk_contract | 10 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |

Support-role failures:

| task_id | episode_type | retriever | strategy | predicted_claim_verdict | support_role_contaminated_doc_ids | support_role_clean_verdict_doc_ids | supporting_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| eha2r_014 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v12_critical_risk_contract | refuted |  |  |  |
| eha2r_029 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v12_critical_risk_contract | refuted |  |  |  |
| eha2r_031 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v12_critical_risk_contract | refuted |  |  |  |

## 7. Temporal Tool Routing

_No rows._

## 8. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | support_role_valid_rate | support_role_contaminated_doc_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v12_critical_risk_contract | 16 | 1.000 | 1.000 | 0.812 | 0.000 | 0.812 | 0.000 | 1.000 | 1.000 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v12_critical_risk_contract | 9 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v12_critical_risk_contract | 10 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |

## 9. False-Consensus Stress Regression Check

_No rows._

## 10. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | support_role_valid_rate | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v12_critical_risk_contract | 1.000 | 1.000 | 1.000 | 0.812 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v12_critical_risk_contract | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v12_critical_risk_contract | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

## 11. Active Tool Helpfulness And Harmfulness

_No rows._

## 12. Qualitative Failure Cases

See `results/reports-phase2s-v12-critical-risk-contract-calibration-slice-heuristic/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 13. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.0,
  "spent_usd": 0.0,
  "soft_cap_usd": 50.0,
  "hard_cap_usd": 150.0,
  "abort_cap_usd": 300.0
}
```

## Unsafe Scope Misses

_No rows._
