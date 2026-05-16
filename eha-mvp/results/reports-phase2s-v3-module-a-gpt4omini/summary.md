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
      "claim_accuracy": 0.4666666666666667,
      "diagnostic_macro_f1": 0.6877961222176158,
      "stale_recall": 0.55,
      "conflict_recall": 0.9,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 0.9090909090909091,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 0.8,
      "unsafe_scope_miss_rate": 0.058333333333333334,
      "escape_rate": 0.43333333333333335,
      "contaminated_citation_rate": 0.0,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.5333333333333333,
      "confidence": 0.8762500000000001,
      "cost_usd": 0.0005199,
      "ece": 0.4095833333333333
    },
    "module_a_prompt": "evidence_diagnostics_v3"
  }
}
```

## 2. Module A Prompt Comparison

| prompt | n | claim_accuracy | diagnostic_macro_f1 | stale_recall | conflict_recall | generated_lore_recall | no_primary_precision | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_diagnostics_v3 | 120 | 0.467 | 0.688 | 0.550 | 0.900 | 1.000 | 0.909 | 0.058 |

## 3. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 11 | 46 | 9 | 54 | 0.193 | 0.550 | 0.286 |
| conflict | 36 | 16 | 4 | 64 | 0.692 | 0.900 | 0.783 |
| generated_lore | 20 | 0 | 0 | 100 | 1.000 | 1.000 | 1.000 |
| no_primary | 20 | 2 | 0 | 98 | 0.909 | 1.000 | 0.952 |
| citation_laundering | 20 | 3 | 0 | 97 | 0.870 | 1.000 | 0.930 |
| false_consensus | 0 | 2 | 0 | 118 | 0.000 | 1.000 | 0.000 |
| partial_support | 19 | 5 | 1 | 95 | 0.792 | 0.950 | 0.864 |

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

See `results/reports-phase2s-v3-module-a-gpt4omini/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.062388,
  "spent_usd": 0.062388,
  "soft_cap_usd": 2.0,
  "hard_cap_usd": 5.0,
  "abort_cap_usd": 10.0
}
```

## Unsafe Scope Misses

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2s_a_028 | A | stale_evidence | evidence_diagnostics_v3 | 0.950 | stale_evidence |  |
| eha2s_a_031 | A | stale_evidence | evidence_diagnostics_v3 | 0.900 | stale_evidence |  |
| eha2s_a_033 | A | stale_evidence | evidence_diagnostics_v3 | 0.900 | stale_evidence |  |
| eha2s_a_043 | A | conflicting_evidence | evidence_diagnostics_v3 | 1.000 | conflicting_evidence |  |
| eha2s_a_044 | A | conflicting_evidence | evidence_diagnostics_v3 | 0.900 | conflicting_evidence |  |
| eha2s_a_047 | A | conflicting_evidence | evidence_diagnostics_v3 | 0.900 | conflicting_evidence |  |
| eha2s_a_058 | A | conflicting_evidence | evidence_diagnostics_v3 | 0.900 | conflicting_evidence |  |
