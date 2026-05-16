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

Direct critical-risk macro-F1: `0.299`

| risk | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale_evidence | 1 | 1 | 4 | 29 | 0.500 | 0.200 | 0.286 |
| conflicting_evidence | 4 | 7 | 6 | 18 | 0.364 | 0.400 | 0.381 |
| generated_lore | 1 | 2 | 4 | 28 | 0.333 | 0.200 | 0.250 |
| no_primary_source | 8 | 4 | 2 | 21 | 0.667 | 0.800 | 0.727 |
| citation_laundering | 1 | 6 | 4 | 24 | 0.143 | 0.200 | 0.167 |
| false_consensus | 2 | 7 | 3 | 23 | 0.222 | 0.400 | 0.286 |
| partial_support | 0 | 0 | 5 | 30 | 1.000 | 0.000 | 0.000 |

## 4. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 4 | 17 | 1 | 13 | 0.190 | 0.800 | 0.308 |
| conflict | 7 | 14 | 3 | 11 | 0.333 | 0.700 | 0.452 |
| generated_lore | 5 | 9 | 0 | 21 | 0.357 | 1.000 | 0.526 |
| no_primary | 9 | 4 | 1 | 21 | 0.692 | 0.900 | 0.783 |
| citation_laundering | 1 | 9 | 4 | 21 | 0.100 | 0.200 | 0.133 |
| false_consensus | 2 | 7 | 3 | 23 | 0.222 | 0.400 | 0.286 |
| partial_support | 2 | 1 | 3 | 29 | 0.667 | 0.400 | 0.500 |

## 5. Structural Environment Observations

Observation macro-F1: `0.643`

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| visible_stale_or_superseded_material | 7 | 1 | 3 | 24 | 0.875 | 0.700 | 0.778 |
| visible_conflicting_material | 21 | 0 | 14 | 0 | 1.000 | 0.600 | 0.750 |
| visible_generated_or_synthetic_lore | 10 | 4 | 0 | 21 | 0.714 | 1.000 | 0.833 |
| visible_reposts_or_same_root_repetition | 35 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| visible_citation_chain_problem | 1 | 9 | 4 | 21 | 0.100 | 0.200 | 0.133 |
| visible_partial_or_scope_limited_support | 2 | 4 | 3 | 26 | 0.333 | 0.400 | 0.364 |

## 6. Supporting-Evidence Role Validity

`support_role_valid_rate` requires clean-only evidence and verdict-direct support; `support_role_clean_only_rate` is reported separately so evidence-list cleanliness is not inferred from critical-risk labels.

| module | retriever | strategy | n | claim_accuracy | support_role_valid_rate | support_role_clean_only_rate | support_role_verdict_direct_rate | support_role_contaminated_doc_rate | support_role_missing_clean_verdict_evidence_rate | support_role_nonempty_for_insufficient_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | bm25_top8 | evidence_diagnostics_v9_structural_recall | 16 | 0.812 | 0.812 | 0.938 | 0.812 | 0.062 | 0.000 | 0.062 |
| C | hygienic_combo_top8 | evidence_diagnostics_v9_structural_recall | 9 | 0.889 | 0.889 | 1.000 | 0.889 | 0.000 | 0.111 | 0.000 |
| C | primary_preserve_top8 | evidence_diagnostics_v9_structural_recall | 10 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |

Support-role failures:

| task_id | episode_type | retriever | strategy | predicted_claim_verdict | support_role_contaminated_doc_ids | support_role_clean_verdict_doc_ids | supporting_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| eha2r_014 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v9_structural_recall | insufficient |  |  |  |
| eha2r_029 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v9_structural_recall | insufficient |  |  |  |
| eha2r_031 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v9_structural_recall | insufficient | eha2r_031_pollutant_root |  | eha2r_031_pollutant_root |
| eha2r_074 | insufficient_or_no_primary | hygienic_combo_top8 | evidence_diagnostics_v9_structural_recall | refuted |  |  |  |

## 7. Temporal Tool Routing

_No rows._

## 8. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | support_role_valid_rate | support_role_contaminated_doc_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v9_structural_recall | 16 | 0.812 | 0.371 | 0.812 | 0.062 | 0.812 | 0.062 | 0.500 | 0.400 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v9_structural_recall | 9 | 0.889 | 0.503 | 0.889 | 0.000 | 0.889 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v9_structural_recall | 10 | 1.000 | 0.359 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |

## 9. False-Consensus Stress Regression Check

_No rows._

## 10. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | support_role_valid_rate | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v9_structural_recall | 1.000 | 0.500 | 0.812 | 0.812 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v9_structural_recall | 1.000 | 1.000 | 0.889 | 0.889 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v9_structural_recall | 1.000 | 0.667 | 1.000 | 1.000 | 0.000 |

## 11. Active Tool Helpfulness And Harmfulness

_No rows._

## 12. Qualitative Failure Cases

See `results/reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 13. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.033729,
  "spent_usd": 0.033729,
  "soft_cap_usd": 0.2,
  "hard_cap_usd": 0.5,
  "abort_cap_usd": 1.0
}
```

## Unsafe Scope Misses

_No rows._
