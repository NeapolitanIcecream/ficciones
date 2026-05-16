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

Direct critical-risk macro-F1: `0.240`

| risk | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale_evidence | 0 | 0 | 5 | 30 | 1.000 | 0.000 | 0.000 |
| conflicting_evidence | 6 | 11 | 4 | 14 | 0.353 | 0.600 | 0.444 |
| generated_lore | 1 | 1 | 4 | 29 | 0.500 | 0.200 | 0.286 |
| no_primary_source | 6 | 3 | 4 | 22 | 0.667 | 0.600 | 0.632 |
| citation_laundering | 0 | 5 | 5 | 25 | 0.000 | 0.000 | 0.000 |
| false_consensus | 3 | 11 | 2 | 19 | 0.214 | 0.600 | 0.316 |
| partial_support | 0 | 1 | 5 | 29 | 0.000 | 0.000 | 0.000 |

## 4. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 3 | 17 | 2 | 13 | 0.150 | 0.600 | 0.240 |
| conflict | 7 | 12 | 3 | 13 | 0.368 | 0.700 | 0.483 |
| generated_lore | 5 | 6 | 0 | 24 | 0.455 | 1.000 | 0.625 |
| no_primary | 8 | 3 | 2 | 22 | 0.727 | 0.800 | 0.762 |
| citation_laundering | 0 | 6 | 5 | 24 | 0.000 | 0.000 | 0.000 |
| false_consensus | 3 | 11 | 2 | 19 | 0.214 | 0.600 | 0.316 |
| partial_support | 1 | 1 | 4 | 29 | 0.500 | 0.200 | 0.286 |

## 5. Structural Environment Observations

Observation macro-F1: `0.582`

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| visible_stale_or_superseded_material | 9 | 0 | 1 | 25 | 1.000 | 0.900 | 0.947 |
| visible_conflicting_material | 19 | 0 | 16 | 0 | 1.000 | 0.543 | 0.704 |
| visible_generated_or_synthetic_lore | 9 | 2 | 1 | 23 | 0.818 | 0.900 | 0.857 |
| visible_reposts_or_same_root_repetition | 34 | 0 | 1 | 0 | 1.000 | 0.971 | 0.986 |
| visible_citation_chain_problem | 0 | 8 | 5 | 22 | 0.000 | 0.000 | 0.000 |
| visible_partial_or_scope_limited_support | 0 | 1 | 5 | 29 | 0.000 | 0.000 | 0.000 |

## 6. Supporting-Evidence Role Validity

`support_role_valid_rate` requires clean-only evidence and verdict-direct support; `support_role_clean_only_rate` is reported separately so evidence-list cleanliness is not inferred from critical-risk labels.

| module | retriever | strategy | n | claim_accuracy | support_role_valid_rate | support_role_clean_only_rate | support_role_verdict_direct_rate | support_role_contaminated_doc_rate | support_role_missing_clean_verdict_evidence_rate | support_role_nonempty_for_insufficient_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | bm25_top8 | evidence_diagnostics_v11_role_disciplined_contract | 16 | 0.750 | 0.750 | 1.000 | 0.750 | 0.000 | 0.062 | 0.000 |
| C | hygienic_combo_top8 | evidence_diagnostics_v11_role_disciplined_contract | 9 | 0.889 | 0.889 | 1.000 | 0.889 | 0.000 | 0.111 | 0.000 |
| C | primary_preserve_top8 | evidence_diagnostics_v11_role_disciplined_contract | 10 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |

Support-role failures:

| task_id | episode_type | retriever | strategy | predicted_claim_verdict | support_role_contaminated_doc_ids | support_role_clean_verdict_doc_ids | supporting_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| eha2r_014 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v11_role_disciplined_contract | insufficient |  |  |  |
| eha2r_029 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v11_role_disciplined_contract | insufficient |  |  |  |
| eha2r_031 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v11_role_disciplined_contract | insufficient |  |  |  |
| eha2r_073 | insufficient_or_no_primary | bm25_top8 | evidence_diagnostics_v11_role_disciplined_contract | refuted |  |  |  |
| eha2r_074 | insufficient_or_no_primary | hygienic_combo_top8 | evidence_diagnostics_v11_role_disciplined_contract | refuted |  |  |  |

## 7. Temporal Tool Routing

_No rows._

## 8. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | support_role_valid_rate | support_role_contaminated_doc_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v11_role_disciplined_contract | 16 | 0.750 | 0.273 | 0.750 | 0.000 | 0.750 | 0.000 | 0.000 | 0.400 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v11_role_disciplined_contract | 9 | 0.889 | 0.509 | 0.889 | 0.000 | 0.889 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v11_role_disciplined_contract | 10 | 1.000 | 0.429 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |

## 9. False-Consensus Stress Regression Check

_No rows._

## 10. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | support_role_valid_rate | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v11_role_disciplined_contract | 1.000 | 0.500 | 0.750 | 0.750 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v11_role_disciplined_contract | 1.000 | 1.000 | 0.889 | 0.889 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v11_role_disciplined_contract | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

## 11. Active Tool Helpfulness And Harmfulness

_No rows._

## 12. Qualitative Failure Cases

See `results/reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 13. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.037478,
  "spent_usd": 0.037478,
  "soft_cap_usd": 0.2,
  "hard_cap_usd": 0.5,
  "abort_cap_usd": 1.0
}
```

## Unsafe Scope Misses

_No rows._
