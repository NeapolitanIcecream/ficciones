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

Direct critical-risk macro-F1: `0.369`

| risk | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale_evidence | 3 | 1 | 2 | 29 | 0.750 | 0.600 | 0.667 |
| conflicting_evidence | 5 | 8 | 5 | 17 | 0.385 | 0.500 | 0.435 |
| generated_lore | 3 | 1 | 2 | 29 | 0.750 | 0.600 | 0.667 |
| no_primary_source | 9 | 3 | 1 | 22 | 0.750 | 0.900 | 0.818 |
| citation_laundering | 0 | 3 | 5 | 27 | 0.000 | 0.000 | 0.000 |
| false_consensus | 0 | 2 | 5 | 28 | 0.000 | 0.000 | 0.000 |
| partial_support | 0 | 0 | 5 | 30 | 1.000 | 0.000 | 0.000 |

## 4. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 4 | 18 | 1 | 12 | 0.182 | 0.800 | 0.296 |
| conflict | 7 | 12 | 3 | 13 | 0.368 | 0.700 | 0.483 |
| generated_lore | 5 | 9 | 0 | 21 | 0.357 | 1.000 | 0.526 |
| no_primary | 10 | 3 | 0 | 22 | 0.769 | 1.000 | 0.870 |
| citation_laundering | 0 | 4 | 5 | 26 | 0.000 | 0.000 | 0.000 |
| false_consensus | 0 | 2 | 5 | 28 | 0.000 | 0.000 | 0.000 |
| partial_support | 0 | 0 | 5 | 30 | 1.000 | 0.000 | 0.000 |

## 5. Structural Environment Observations

Observation macro-F1: `0.574`

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| visible_stale_or_superseded_material | 10 | 2 | 0 | 23 | 0.833 | 1.000 | 0.909 |
| visible_conflicting_material | 19 | 0 | 16 | 0 | 1.000 | 0.543 | 0.704 |
| visible_generated_or_synthetic_lore | 10 | 4 | 0 | 21 | 0.714 | 1.000 | 0.833 |
| visible_reposts_or_same_root_repetition | 35 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| visible_citation_chain_problem | 0 | 4 | 5 | 26 | 0.000 | 0.000 | 0.000 |
| visible_partial_or_scope_limited_support | 0 | 0 | 5 | 30 | 1.000 | 0.000 | 0.000 |

## 6. Supporting-Evidence Role Validity

`support_role_valid_rate` requires clean-only evidence and verdict-direct support; `support_role_clean_only_rate` is reported separately so evidence-list cleanliness is not inferred from critical-risk labels.

| module | retriever | strategy | n | claim_accuracy | support_role_valid_rate | support_role_clean_only_rate | support_role_verdict_direct_rate | support_role_contaminated_doc_rate | support_role_missing_clean_verdict_evidence_rate | support_role_nonempty_for_insufficient_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | bm25_top8 | evidence_diagnostics_v8_structural | 16 | 0.812 | 0.812 | 1.000 | 0.812 | 0.000 | 0.000 | 0.000 |
| C | hygienic_combo_top8 | evidence_diagnostics_v8_structural | 9 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |
| C | primary_preserve_top8 | evidence_diagnostics_v8_structural | 10 | 0.900 | 0.900 | 1.000 | 0.900 | 0.000 | 0.000 | 0.100 |

Support-role failures:

| task_id | episode_type | retriever | strategy | predicted_claim_verdict | support_role_contaminated_doc_ids | support_role_clean_verdict_doc_ids | supporting_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| eha2r_014 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v8_structural | insufficient |  |  |  |
| eha2r_029 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v8_structural | insufficient |  |  |  |
| eha2r_031 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v8_structural | insufficient |  |  |  |
| eha2r_076 | mixed_source_corruption_v2 | primary_preserve_top8 | evidence_diagnostics_v8_structural | insufficient |  | eha2r_076_primary_a,eha2r_076_primary_b | eha2r_076_primary_a,eha2r_076_primary_b |

## 7. Temporal Tool Routing

_No rows._

## 8. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | support_role_valid_rate | support_role_contaminated_doc_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v8_structural | 16 | 0.812 | 0.246 | 0.812 | 0.000 | 0.812 | 0.000 | 0.500 | 0.400 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v8_structural | 9 | 1.000 | 0.361 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v8_structural | 10 | 0.900 | 0.383 | 0.900 | 0.000 | 0.900 | 0.000 | 1.000 | 1.000 | 1.000 |

## 9. False-Consensus Stress Regression Check

_No rows._

## 10. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | support_role_valid_rate | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v8_structural | 1.000 | 0.667 | 0.812 | 0.812 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v8_structural | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v8_structural | 1.000 | 0.667 | 0.900 | 0.900 | 0.000 |

## 11. Active Tool Helpfulness And Harmfulness

_No rows._

## 12. Qualitative Failure Cases

See `results/reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 13. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.031281,
  "spent_usd": 0.031281,
  "soft_cap_usd": 0.2,
  "hard_cap_usd": 0.5,
  "abort_cap_usd": 1.0
}
```

## Unsafe Scope Misses

_No rows._
