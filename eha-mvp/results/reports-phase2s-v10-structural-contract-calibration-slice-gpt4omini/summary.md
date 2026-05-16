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

Direct critical-risk macro-F1: `0.404`

| risk | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale_evidence | 3 | 0 | 2 | 30 | 1.000 | 0.600 | 0.750 |
| conflicting_evidence | 4 | 7 | 6 | 18 | 0.364 | 0.400 | 0.381 |
| generated_lore | 2 | 3 | 3 | 27 | 0.400 | 0.400 | 0.400 |
| no_primary_source | 5 | 2 | 5 | 23 | 0.714 | 0.500 | 0.588 |
| citation_laundering | 1 | 3 | 4 | 27 | 0.250 | 0.200 | 0.222 |
| false_consensus | 1 | 4 | 4 | 26 | 0.200 | 0.200 | 0.200 |
| partial_support | 1 | 1 | 4 | 29 | 0.500 | 0.200 | 0.286 |

## 4. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 5 | 16 | 0 | 14 | 0.238 | 1.000 | 0.385 |
| conflict | 7 | 11 | 3 | 14 | 0.389 | 0.700 | 0.500 |
| generated_lore | 5 | 9 | 0 | 21 | 0.357 | 1.000 | 0.526 |
| no_primary | 8 | 3 | 2 | 22 | 0.727 | 0.800 | 0.762 |
| citation_laundering | 1 | 5 | 4 | 25 | 0.167 | 0.200 | 0.182 |
| false_consensus | 1 | 4 | 4 | 26 | 0.200 | 0.200 | 0.200 |
| partial_support | 2 | 5 | 3 | 25 | 0.286 | 0.400 | 0.333 |

## 5. Structural Environment Observations

Observation macro-F1: `0.666`

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| visible_stale_or_superseded_material | 9 | 1 | 1 | 24 | 0.900 | 0.900 | 0.900 |
| visible_conflicting_material | 18 | 0 | 17 | 0 | 1.000 | 0.514 | 0.679 |
| visible_generated_or_synthetic_lore | 10 | 4 | 0 | 21 | 0.714 | 1.000 | 0.833 |
| visible_reposts_or_same_root_repetition | 35 | 0 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| visible_citation_chain_problem | 2 | 9 | 3 | 21 | 0.182 | 0.400 | 0.250 |
| visible_partial_or_scope_limited_support | 2 | 5 | 3 | 25 | 0.286 | 0.400 | 0.333 |

## 6. Supporting-Evidence Role Validity

`support_role_valid_rate` requires clean-only evidence and verdict-direct support; `support_role_clean_only_rate` is reported separately so evidence-list cleanliness is not inferred from critical-risk labels.

| module | retriever | strategy | n | claim_accuracy | support_role_valid_rate | support_role_clean_only_rate | support_role_verdict_direct_rate | support_role_contaminated_doc_rate | support_role_missing_clean_verdict_evidence_rate | support_role_nonempty_for_insufficient_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | bm25_top8 | evidence_diagnostics_v10_structural_contract | 16 | 0.812 | 0.750 | 0.812 | 0.750 | 0.188 | 0.000 | 0.188 |
| C | hygienic_combo_top8 | evidence_diagnostics_v10_structural_contract | 9 | 0.889 | 0.889 | 1.000 | 0.889 | 0.000 | 0.111 | 0.000 |
| C | primary_preserve_top8 | evidence_diagnostics_v10_structural_contract | 10 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 |

Support-role failures:

| task_id | episode_type | retriever | strategy | predicted_claim_verdict | support_role_contaminated_doc_ids | support_role_clean_verdict_doc_ids | supporting_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| eha2r_014 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v10_structural_contract | insufficient | eha2r_014_pollutant_root |  | eha2r_014_pollutant_root |
| eha2r_029 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v10_structural_contract | insufficient |  |  |  |
| eha2r_031 | false_consensus_stress | bm25_top8 | evidence_diagnostics_v10_structural_contract | insufficient | eha2r_031_pollutant_root |  | eha2r_031_pollutant_root |
| eha2r_071 | insufficient_or_no_primary | bm25_top8 | evidence_diagnostics_v10_structural_contract | insufficient | eha2r_071_pollutant_root,eha2r_071_repost_00,eha2r_071_repost_01,eha2r_071_repost_02,eha2r_071_repost_03,eha2r_071_repost_04 |  | eha2r_071_pollutant_root,eha2r_071_repost_00,eha2r_071_repost_01,eha2r_071_repost_02,eha2r_071_repost_03,eha2r_071_repost_04 |
| eha2r_074 | insufficient_or_no_primary | hygienic_combo_top8 | evidence_diagnostics_v10_structural_contract | refuted |  |  |  |

## 7. Temporal Tool Routing

_No rows._

## 8. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | support_role_valid_rate | support_role_contaminated_doc_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v10_structural_contract | 16 | 0.812 | 0.364 | 0.750 | 0.188 | 0.750 | 0.188 | 1.000 | 0.400 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v10_structural_contract | 9 | 0.889 | 0.332 | 0.889 | 0.000 | 0.889 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v10_structural_contract | 10 | 1.000 | 0.495 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |

## 9. False-Consensus Stress Regression Check

_No rows._

## 10. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | support_role_valid_rate | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v10_structural_contract | 1.000 | 0.750 | 0.812 | 0.750 | 0.062 |
| hygienic_combo_top8 | evidence_diagnostics_v10_structural_contract | 1.000 | 0.750 | 0.889 | 0.889 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v10_structural_contract | 1.000 | 0.667 | 1.000 | 1.000 | 0.000 |

## 11. Active Tool Helpfulness And Harmfulness

_No rows._

## 12. Qualitative Failure Cases

See `results/reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 13. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.034349,
  "spent_usd": 0.034349,
  "soft_cap_usd": 0.2,
  "hard_cap_usd": 0.5,
  "abort_cap_usd": 1.0
}
```

## Unsafe Scope Misses

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2r_031 | C | false_consensus_stress | evidence_diagnostics_v10_structural_contract | 0.700 | conflicting_evidence,false_consensus | citation_laundering,false_consensus |
