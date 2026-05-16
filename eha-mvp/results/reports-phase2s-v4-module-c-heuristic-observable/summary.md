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
| stale | 42 | 0 | 0 | 342 | 1.000 | 1.000 | 1.000 |
| conflict | 216 | 0 | 0 | 168 | 1.000 | 1.000 | 1.000 |
| generated_lore | 54 | 0 | 0 | 330 | 1.000 | 1.000 | 1.000 |
| no_primary | 84 | 0 | 0 | 300 | 1.000 | 1.000 | 1.000 |
| citation_laundering | 60 | 0 | 0 | 324 | 1.000 | 1.000 | 1.000 |
| false_consensus | 156 | 0 | 0 | 228 | 1.000 | 1.000 | 1.000 |
| partial_support | 18 | 0 | 0 | 366 | 1.000 | 1.000 | 1.000 |

## 4. Temporal Tool Routing

_No rows._

## 5. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v4 | 80 | 1.000 | 1.000 | 0.800 | 0.000 | 1.000 | 1.000 | 1.000 |
| bm25_top8 | forced_triage_tools | 48 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| bm25_top8 | route_then_answer_v1 | 48 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v4 | 80 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 48 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v4 | 80 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |

## 6. False-Consensus Stress Regression Check

_No rows._

## 7. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v4 | 1.000 | 1.000 | 1.000 | 0.000 |
| bm25_top8 | forced_triage_tools | 1.000 | 1.000 | 1.000 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 1.000 | 1.000 | 1.000 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v4 | 1.000 | 1.000 | 1.000 | 0.000 |
| hygienic_combo_top8 | static_hygienic_combo | 1.000 | 1.000 | 1.000 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v4 | 1.000 | 1.000 | 1.000 | 0.000 |

## 8. Active Tool Helpfulness And Harmfulness

| module | strategy | n | escape_rate | claim_accuracy | compare_versions_rate | useful_compare_versions_rate | trace_rate | search_contradictions_rate | primary_request_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | forced_triage_tools | 48 | 1.000 | 1.000 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |
| C | route_then_answer_v1 | 48 | 1.000 | 1.000 | 1.000 | 0.750 | 0.000 | 0.000 | 1.000 |
| C | static_hygienic_combo | 48 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 9. Qualitative Failure Cases

See `results/reports-phase2s-v4-module-c-heuristic-observable/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

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
