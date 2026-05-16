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
| stale | 42 | 322 | 0 | 20 | 0.115 | 1.000 | 0.207 |
| conflict | 202 | 71 | 14 | 97 | 0.740 | 0.935 | 0.826 |
| generated_lore | 28 | 24 | 26 | 306 | 0.538 | 0.519 | 0.528 |
| no_primary | 78 | 12 | 6 | 288 | 0.867 | 0.929 | 0.897 |
| citation_laundering | 55 | 273 | 5 | 51 | 0.168 | 0.917 | 0.284 |
| false_consensus | 135 | 200 | 21 | 28 | 0.403 | 0.865 | 0.550 |
| partial_support | 2 | 6 | 16 | 360 | 0.250 | 0.111 | 0.154 |

## 4. Temporal Tool Routing

_No rows._

## 5. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v6 | 80 | 0.812 | 0.431 | 0.787 | 0.037 | 1.000 | 0.682 | 0.600 |
| bm25_top8 | forced_triage_tools | 48 | 1.000 | 0.410 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 48 | 0.979 | 0.470 | 0.979 | 0.000 | 1.000 | 1.000 | 0.750 |
| hygienic_combo_top8 | evidence_diagnostics_v6 | 80 | 0.975 | 0.469 | 0.975 | 0.000 | 1.000 | 1.000 | 0.400 |
| hygienic_combo_top8 | static_hygienic_combo | 48 | 1.000 | 0.592 | 1.000 | 0.000 | 1.000 | 1.000 | 0.750 |
| primary_preserve_top8 | evidence_diagnostics_v6 | 80 | 1.000 | 0.545 | 1.000 | 0.000 | 1.000 | 1.000 | 0.600 |

## 6. False-Consensus Stress Regression Check

_No rows._

## 7. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v6 | 0.600 | 0.615 | 0.812 | 0.013 |
| bm25_top8 | forced_triage_tools | 0.000 | 1.000 | 1.000 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 0.750 | 1.000 | 0.979 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v6 | 0.400 | 0.938 | 0.975 | 0.000 |
| hygienic_combo_top8 | static_hygienic_combo | 0.750 | 1.000 | 1.000 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v6 | 0.600 | 0.938 | 1.000 | 0.000 |

## 8. Active Tool Helpfulness And Harmfulness

| module | strategy | n | escape_rate | claim_accuracy | compare_versions_rate | useful_compare_versions_rate | trace_rate | search_contradictions_rate | primary_request_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | forced_triage_tools | 48 | 1.000 | 1.000 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |
| C | route_then_answer_v1 | 48 | 0.979 | 0.979 | 0.312 | 0.312 | 0.312 | 0.625 | 0.688 |
| C | static_hygienic_combo | 48 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 9. Qualitative Failure Cases

See `results/reports-phase2s-v6-module-c-gpt4omini-observable/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.315169,
  "spent_usd": 0.330858,
  "soft_cap_usd": 1.0,
  "hard_cap_usd": 2.0,
  "abort_cap_usd": 5.0
}
```

## Unsafe Scope Misses

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2r_038 | C | false_consensus_stress | evidence_diagnostics_v6 | 0.900 | conflicting_evidence,false_consensus | false_consensus,citation_laundering |
