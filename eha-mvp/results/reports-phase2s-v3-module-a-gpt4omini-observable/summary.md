# EHA Phase 2S Scope Diagnosis & Temporal Routing Repair Summary

## 1. Gate Result

```json
{
  "scope": "module_a",
  "passed": false,
  "checks": {
    "A1_claim_accuracy_at_least_0_90": true,
    "A2_diagnostic_macro_f1_at_least_0_70": true,
    "A3_stale_recall_at_least_0_75": true,
    "A4_conflict_recall_at_least_0_65": true,
    "A5_generated_lore_recall_at_least_0_70": true,
    "A6_no_primary_precision_at_least_0_90": false,
    "A7_unsafe_scope_miss_rate_at_most_0_25": true
  },
  "details": {
    "scope": "module_a",
    "module_a": {
      "n": 120,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 0.9666666666666667,
      "diagnostic_macro_f1": 0.7109493178765816,
      "stale_recall": 1.0,
      "conflict_recall": 1.0,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 0.8695652173913043,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 0.7416666666666667,
      "unsafe_scope_miss_rate": 0.0,
      "escape_rate": 0.5,
      "contaminated_citation_rate": 0.004166666666666667,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.03333333333333333,
      "confidence": 0.9004166666666666,
      "cost_usd": 0.00050433,
      "ece": 0.06624999999999988
    },
    "module_a_prompt": "evidence_diagnostics_v3"
  }
}
```

## 2. Module A Prompt Comparison

| prompt | n | claim_accuracy | diagnostic_macro_f1 | stale_recall | conflict_recall | generated_lore_recall | no_primary_precision | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_diagnostics_v3 | 120 | 0.967 | 0.711 | 1.000 | 1.000 | 1.000 | 0.870 | 0.000 |

## 3. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 20 | 46 | 0 | 54 | 0.303 | 1.000 | 0.465 |
| conflict | 40 | 20 | 0 | 60 | 0.667 | 1.000 | 0.800 |
| generated_lore | 20 | 0 | 0 | 100 | 1.000 | 1.000 | 1.000 |
| no_primary | 20 | 3 | 0 | 97 | 0.870 | 1.000 | 0.930 |
| citation_laundering | 20 | 7 | 0 | 93 | 0.741 | 1.000 | 0.851 |
| false_consensus | 0 | 1 | 0 | 119 | 0.000 | 1.000 | 0.000 |
| partial_support | 20 | 3 | 0 | 97 | 0.870 | 1.000 | 0.930 |

## 4. Temporal Tool Routing

_No rows._

## 5. Integrated Regression On Phase 2R

_No rows._

## 6. False-Consensus Stress Regression Check

_No rows._

## 7. Generated-Lore Detection Vs No-Primary Abstention

_No rows._

## 8. Active Tool Helpfulness And Harmfulness

_No rows._

## 9. Qualitative Failure Cases

See `results/reports-phase2s-v3-module-a-gpt4omini-observable/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.06052,
  "spent_usd": 0.06052,
  "soft_cap_usd": 2.0,
  "hard_cap_usd": 5.0,
  "abort_cap_usd": 10.0
}
```

## Unsafe Scope Misses

_No rows._
