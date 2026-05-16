# EHA Phase 2S Scope Diagnosis & Temporal Routing Repair Summary

## 1. Gate Result

```json
{
  "scope": "module_a",
  "passed": false,
  "checks": {
    "A1_claim_accuracy_at_least_0_90": false,
    "A2_diagnostic_macro_f1_at_least_0_70": false,
    "A3_stale_recall_at_least_0_75": false,
    "A4_conflict_recall_at_least_0_65": false,
    "A5_generated_lore_recall_at_least_0_70": true,
    "A6_no_primary_precision_at_least_0_90": true,
    "A7_unsafe_scope_miss_rate_at_most_0_25": false
  },
  "details": {
    "scope": "module_a",
    "module_a": {
      "n": 120,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 0.3333333333333333,
      "diagnostic_macro_f1": 0.4996067507063109,
      "stale_recall": 0.0,
      "conflict_recall": 0.475,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 0.9523809523809523,
      "citation_laundering_recall": 0.9,
      "source_independence_accuracy": 0.7333333333333333,
      "unsafe_scope_miss_rate": 0.325,
      "escape_rate": 0.3333333333333333,
      "contaminated_citation_rate": 0.0,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.6666666666666666,
      "confidence": 0.9479166666666666,
      "cost_usd": 0.00045463999999999997,
      "ece": 0.6445833333333333
    },
    "module_a_prompt": "evidence_diagnostics_v2"
  }
}
```

## 2. Module A Prompt Comparison

| prompt | n | claim_accuracy | diagnostic_macro_f1 | stale_recall | conflict_recall | generated_lore_recall | no_primary_precision | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_diagnostics_v1 | 120 | 0.367 | 0.576 | 0.650 | 1.000 | 1.000 | 0.455 | 0.008 |
| evidence_diagnostics_v2 | 120 | 0.333 | 0.500 | 0.000 | 0.475 | 1.000 | 0.952 | 0.325 |
| evidence_graph_v3 | 120 | 0.433 | 0.302 | 0.000 | 0.000 | 0.000 | 0.667 | 0.467 |

## 3. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 13 | 76 | 47 | 224 | 0.146 | 0.217 | 0.174 |
| conflict | 59 | 21 | 61 | 219 | 0.738 | 0.492 | 0.590 |
| generated_lore | 40 | 1 | 20 | 299 | 0.976 | 0.667 | 0.792 |
| no_primary | 60 | 35 | 0 | 265 | 0.632 | 1.000 | 0.774 |
| citation_laundering | 38 | 4 | 22 | 296 | 0.905 | 0.633 | 0.745 |
| false_consensus | 0 | 19 | 0 | 341 | 0.000 | 1.000 | 0.000 |
| partial_support | 24 | 72 | 36 | 228 | 0.250 | 0.400 | 0.308 |

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

See `results/reports-phase2s-v2-module-a-gpt4omini/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.148394,
  "spent_usd": 0.148394,
  "soft_cap_usd": 2.0,
  "hard_cap_usd": 5.0,
  "abort_cap_usd": 10.0
}
```

## Unsafe Scope Misses

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2s_a_020 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence | partial_support |
| eha2s_a_020 | A | stale_evidence | evidence_diagnostics_v2 | 1.000 | stale_evidence |  |
| eha2s_a_021 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_021 | A | stale_evidence | evidence_diagnostics_v2 | 1.000 | stale_evidence |  |
| eha2s_a_022 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_023 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_023 | A | stale_evidence | evidence_diagnostics_v2 | 1.000 | stale_evidence |  |
| eha2s_a_024 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_024 | A | stale_evidence | evidence_diagnostics_v2 | 1.000 | stale_evidence |  |
| eha2s_a_025 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_025 | A | stale_evidence | evidence_diagnostics_v2 | 1.000 | stale_evidence |  |
| eha2s_a_026 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_026 | A | stale_evidence | evidence_diagnostics_v1 | 0.950 | stale_evidence |  |
| eha2s_a_026 | A | stale_evidence | evidence_diagnostics_v2 | 1.000 | stale_evidence |  |
| eha2s_a_027 | A | stale_evidence | evidence_diagnostics_v2 | 1.000 | stale_evidence |  |
| eha2s_a_028 | A | stale_evidence | evidence_graph_v3 | 0.950 | stale_evidence |  |
| eha2s_a_028 | A | stale_evidence | evidence_diagnostics_v2 | 1.000 | stale_evidence |  |
| eha2s_a_029 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_029 | A | stale_evidence | evidence_diagnostics_v2 | 0.950 | stale_evidence |  |
| eha2s_a_030 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
