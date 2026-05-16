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

## 3. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 42 | 329 | 0 | 13 | 0.113 | 1.000 | 0.203 |
| conflict | 199 | 78 | 17 | 90 | 0.718 | 0.921 | 0.807 |
| generated_lore | 48 | 118 | 6 | 212 | 0.289 | 0.889 | 0.436 |
| no_primary | 76 | 23 | 8 | 277 | 0.768 | 0.905 | 0.831 |
| citation_laundering | 52 | 287 | 8 | 37 | 0.153 | 0.867 | 0.261 |
| false_consensus | 150 | 216 | 6 | 12 | 0.410 | 0.962 | 0.575 |
| partial_support | 3 | 27 | 15 | 339 | 0.100 | 0.167 | 0.125 |

## 4. Temporal Tool Routing

_No rows._

## 5. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v5 | 80 | 0.800 | 0.386 | 0.762 | 0.000 | 1.000 | 0.705 | 0.800 |
| bm25_top8 | forced_triage_tools | 48 | 0.958 | 0.542 | 0.958 | 0.000 | 1.000 | 1.000 | 0.750 |
| bm25_top8 | route_then_answer_v1 | 48 | 0.854 | 0.422 | 0.812 | 0.000 | 1.000 | 0.857 | 0.875 |
| hygienic_combo_top8 | evidence_diagnostics_v5 | 80 | 0.975 | 0.494 | 0.975 | 0.000 | 1.000 | 1.000 | 0.900 |
| hygienic_combo_top8 | static_hygienic_combo | 48 | 0.979 | 0.493 | 0.979 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v5 | 80 | 0.975 | 0.479 | 0.975 | 0.000 | 1.000 | 1.000 | 1.000 |

## 6. False-Consensus Stress Regression Check

_No rows._

## 7. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v5 | 0.800 | 0.500 | 0.800 | 0.000 |
| bm25_top8 | forced_triage_tools | 0.750 | 0.917 | 0.958 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 0.875 | 0.611 | 0.854 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v5 | 0.900 | 1.000 | 0.975 | 0.000 |
| hygienic_combo_top8 | static_hygienic_combo | 1.000 | 0.923 | 0.979 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v5 | 1.000 | 1.000 | 0.975 | 0.000 |

## 8. Active Tool Helpfulness And Harmfulness

| module | strategy | n | escape_rate | claim_accuracy | compare_versions_rate | useful_compare_versions_rate | trace_rate | search_contradictions_rate | primary_request_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | forced_triage_tools | 48 | 0.958 | 0.958 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |
| C | route_then_answer_v1 | 48 | 0.812 | 0.854 | 0.542 | 0.312 | 0.062 | 0.396 | 0.583 |
| C | static_hygienic_combo | 48 | 0.979 | 0.979 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 9. Qualitative Failure Cases

See `results/reports-phase2s-v5-module-c-gpt4omini-observable/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.299255,
  "spent_usd": 0.31363,
  "soft_cap_usd": 1.0,
  "hard_cap_usd": 2.0,
  "abort_cap_usd": 5.0
}
```

## Unsafe Scope Misses

_No rows._
