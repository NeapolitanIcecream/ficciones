# EHA Phase 2S Scope Diagnosis & Temporal Routing Repair Summary

## 1. Gate Result

```json
{
  "scope": "module_a",
  "passed": true,
  "checks": {
    "A1_claim_accuracy_at_least_0_90": true,
    "A2_diagnostic_macro_f1_at_least_0_70": true,
    "A3_stale_recall_at_least_0_75": true,
    "A4_conflict_recall_at_least_0_65": true,
    "A5_generated_lore_recall_at_least_0_70": true,
    "A6_no_primary_precision_at_least_0_90": true,
    "A7_unsafe_scope_miss_rate_at_most_0_25": true
  },
  "details": {
    "scope": "module_a",
    "module_a": {
      "n": 120,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 1.0,
      "diagnostic_macro_f1": 0.7481640310908604,
      "stale_recall": 0.9,
      "conflict_recall": 1.0,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 1.0,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 0.7416666666666667,
      "unsafe_scope_miss_rate": 0.0,
      "escape_rate": 0.5,
      "contaminated_citation_rate": 0.0,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.0,
      "confidence": 0.9133333333333333,
      "cost_usd": 0.0005405700000000001,
      "ece": 0.08666666666666659
    },
    "module_a_prompt": "evidence_diagnostics_v4"
  }
}
```

## 2. Module A Prompt Comparison

| prompt | n | claim_accuracy | diagnostic_macro_f1 | stale_recall | conflict_recall | generated_lore_recall | no_primary_precision | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_diagnostics_v4 | 120 | 1.000 | 0.748 | 0.900 | 1.000 | 1.000 | 1.000 | 0.000 |

## 3. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 18 | 40 | 2 | 60 | 0.310 | 0.900 | 0.462 |
| conflict | 40 | 20 | 0 | 60 | 0.667 | 1.000 | 0.800 |
| generated_lore | 20 | 0 | 0 | 100 | 1.000 | 1.000 | 1.000 |
| no_primary | 20 | 0 | 0 | 100 | 1.000 | 1.000 | 1.000 |
| citation_laundering | 20 | 0 | 0 | 100 | 1.000 | 1.000 | 1.000 |
| false_consensus | 0 | 7 | 0 | 113 | 0.000 | 1.000 | 0.000 |
| partial_support | 20 | 1 | 0 | 99 | 0.952 | 1.000 | 0.976 |

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

See `results/reports-phase2s-v4-module-a-gpt4omini-observable/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.064868,
  "spent_usd": 0.064868,
  "soft_cap_usd": 2.0,
  "hard_cap_usd": 5.0,
  "abort_cap_usd": 10.0
}
```

## Unsafe Scope Misses

_No rows._
