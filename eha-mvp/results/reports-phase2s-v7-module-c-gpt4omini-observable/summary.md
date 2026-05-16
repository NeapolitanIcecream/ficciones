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
| stale | 42 | 226 | 0 | 116 | 0.157 | 1.000 | 0.271 |
| conflict | 204 | 70 | 12 | 98 | 0.745 | 0.944 | 0.833 |
| generated_lore | 46 | 35 | 8 | 295 | 0.568 | 0.852 | 0.681 |
| no_primary | 84 | 12 | 0 | 288 | 0.875 | 1.000 | 0.933 |
| citation_laundering | 44 | 210 | 16 | 114 | 0.173 | 0.733 | 0.280 |
| false_consensus | 130 | 176 | 26 | 52 | 0.425 | 0.833 | 0.563 |
| partial_support | 2 | 2 | 16 | 364 | 0.500 | 0.111 | 0.182 |

## 4. Temporal Tool Routing

_No rows._

## 5. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v7 | 80 | 0.812 | 0.460 | 0.762 | 0.037 | 1.000 | 0.727 | 0.900 |
| bm25_top8 | forced_triage_tools | 48 | 1.000 | 0.471 | 1.000 | 0.000 | 1.000 | 1.000 | 0.375 |
| bm25_top8 | route_then_answer_v1 | 48 | 0.979 | 0.490 | 0.979 | 0.000 | 1.000 | 1.000 | 0.875 |
| hygienic_combo_top8 | evidence_diagnostics_v7 | 80 | 0.975 | 0.527 | 0.975 | 0.000 | 1.000 | 1.000 | 0.900 |
| hygienic_combo_top8 | static_hygienic_combo | 48 | 0.938 | 0.652 | 0.938 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v7 | 80 | 0.988 | 0.595 | 0.988 | 0.000 | 1.000 | 1.000 | 1.000 |

## 6. False-Consensus Stress Regression Check

_No rows._

## 7. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v7 | 0.900 | 0.593 | 0.812 | 0.025 |
| bm25_top8 | forced_triage_tools | 0.375 | 0.923 | 1.000 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 0.875 | 1.000 | 0.979 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v7 | 0.900 | 1.000 | 0.975 | 0.000 |
| hygienic_combo_top8 | static_hygienic_combo | 1.000 | 1.000 | 0.938 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v7 | 1.000 | 1.000 | 0.988 | 0.000 |

## 8. Active Tool Helpfulness And Harmfulness

| module | strategy | n | escape_rate | claim_accuracy | compare_versions_rate | useful_compare_versions_rate | trace_rate | search_contradictions_rate | primary_request_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | forced_triage_tools | 48 | 1.000 | 1.000 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |
| C | route_then_answer_v1 | 48 | 0.979 | 0.979 | 0.375 | 0.375 | 0.229 | 0.583 | 0.625 |
| C | static_hygienic_combo | 48 | 0.938 | 0.938 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 9. Qualitative Failure Cases

See `results/reports-phase2s-v7-module-c-gpt4omini-observable/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.331826,
  "spent_usd": 0.347338,
  "soft_cap_usd": 1.0,
  "hard_cap_usd": 2.0,
  "abort_cap_usd": 5.0
}
```

## Unsafe Scope Misses

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2r_013 | C | false_consensus_stress | evidence_diagnostics_v7 | 0.800 | conflicting_evidence,false_consensus | false_consensus,citation_laundering |
| eha2r_015 | C | false_consensus_stress | evidence_diagnostics_v7 | 0.750 | conflicting_evidence,false_consensus | false_consensus,citation_laundering |
