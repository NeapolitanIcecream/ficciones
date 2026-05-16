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
| stale | 17 | 148 | 25 | 194 | 0.103 | 0.405 | 0.164 |
| conflict | 192 | 66 | 24 | 102 | 0.744 | 0.889 | 0.810 |
| generated_lore | 48 | 112 | 6 | 218 | 0.300 | 0.889 | 0.449 |
| no_primary | 80 | 45 | 4 | 255 | 0.640 | 0.952 | 0.766 |
| citation_laundering | 3 | 128 | 57 | 196 | 0.023 | 0.050 | 0.031 |
| false_consensus | 3 | 35 | 153 | 193 | 0.079 | 0.019 | 0.031 |
| partial_support | 2 | 17 | 16 | 349 | 0.105 | 0.111 | 0.108 |

## 4. Temporal Tool Routing

_No rows._

## 5. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v4 | 80 | 0.812 | 0.323 | 0.787 | 0.037 | 0.500 | 0.682 | 1.000 |
| bm25_top8 | forced_triage_tools | 48 | 0.979 | 0.360 | 0.979 | 0.000 | 0.500 | 1.000 | 0.750 |
| bm25_top8 | route_then_answer_v1 | 48 | 0.833 | 0.318 | 0.833 | 0.021 | 0.333 | 0.821 | 0.875 |
| hygienic_combo_top8 | evidence_diagnostics_v4 | 80 | 0.975 | 0.340 | 0.975 | 0.000 | 0.375 | 0.932 | 0.900 |
| hygienic_combo_top8 | static_hygienic_combo | 48 | 0.979 | 0.310 | 0.979 | 0.000 | 0.167 | 0.964 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v4 | 80 | 1.000 | 0.361 | 1.000 | 0.000 | 0.500 | 0.977 | 0.800 |

## 6. False-Consensus Stress Regression Check

_No rows._

## 7. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v4 | 1.000 | 0.516 | 0.812 | 0.013 |
| bm25_top8 | forced_triage_tools | 0.750 | 0.857 | 0.979 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 0.875 | 0.625 | 0.833 | 0.021 |
| hygienic_combo_top8 | evidence_diagnostics_v4 | 0.900 | 0.652 | 0.975 | 0.025 |
| hygienic_combo_top8 | static_hygienic_combo | 1.000 | 0.611 | 0.979 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v4 | 0.800 | 0.696 | 1.000 | 0.013 |

## 8. Active Tool Helpfulness And Harmfulness

| module | strategy | n | escape_rate | claim_accuracy | compare_versions_rate | useful_compare_versions_rate | trace_rate | search_contradictions_rate | primary_request_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | forced_triage_tools | 48 | 0.979 | 0.979 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |
| C | route_then_answer_v1 | 48 | 0.833 | 0.833 | 0.562 | 0.333 | 0.062 | 0.250 | 0.479 |
| C | static_hygienic_combo | 48 | 0.979 | 0.979 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 9. Qualitative Failure Cases

See `results/reports-phase2s-v4-module-c-gpt4omini-observable/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.253793,
  "spent_usd": 0.267693,
  "soft_cap_usd": 1.0,
  "hard_cap_usd": 2.0,
  "abort_cap_usd": 5.0
}
```

## Unsafe Scope Misses

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2r_022 | C | false_consensus_stress | evidence_diagnostics_v4 | 0.800 | conflicting_evidence,false_consensus |  |
| eha2r_041 | C | citation_laundering_trace | evidence_diagnostics_v4 | 1.000 | citation_laundering,conflicting_evidence |  |
| eha2r_042 | C | citation_laundering_trace | evidence_diagnostics_v4 | 1.000 | citation_laundering,conflicting_evidence |  |
| eha2r_042 | C | citation_laundering_trace | evidence_diagnostics_v4 | 1.000 | citation_laundering,conflicting_evidence |  |
| eha2r_036 | C | false_consensus_stress | route_then_answer_v1 | 0.700 | conflicting_evidence,false_consensus | partial_support,citation_laundering |
