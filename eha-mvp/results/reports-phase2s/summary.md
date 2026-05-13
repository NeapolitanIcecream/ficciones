# EHA Phase 2S Scope Diagnosis & Temporal Routing Repair Summary

## 1. Gate Result

```json
{
  "passed": false,
  "checks": {
    "A1_claim_accuracy_at_least_0_90": false,
    "A2_diagnostic_macro_f1_at_least_0_70": false,
    "A3_stale_recall_at_least_0_75": true,
    "A4_conflict_recall_at_least_0_65": true,
    "A5_generated_lore_recall_at_least_0_70": true,
    "A6_no_primary_precision_at_least_0_90": false,
    "A7_unsafe_scope_miss_rate_at_most_0_25": true,
    "B1_compare_versions_rate_on_temporal_at_least_0_75": true,
    "B2_useful_compare_versions_rate_at_least_0_60": true,
    "B3_temporal_claim_accuracy_at_least_0_85": true,
    "B4_stale_recall_at_least_0_75": true,
    "B5_tool_parse_success_at_least_0_98": true,
    "B6_hidden_label_leakage_false": true,
    "C1_clean_control_claim_accuracy_at_least_0_90": false,
    "C2_high_pressure_bm25_wrong_answer_rate_at_least_0_70": true,
    "C3_hygienic_combo_high_pressure_recovery_delta_at_least_0_25": true,
    "C4_hygienic_combo_claim_accuracy_at_least_0_95": true,
    "C5_hygienic_combo_contaminated_citation_rate_at_most_0_08": false,
    "C6_diagnostic_macro_f1_at_least_0_60": false,
    "C7_stale_recall_at_least_0_65": true,
    "C8_conflict_recall_at_least_0_60": true,
    "C9_generated_lore_recall_at_least_0_60": true,
    "C10_active_tool_escape_not_more_than_0_05_below_static": false
  },
  "details": {
    "module_a": {
      "n": 120,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 0.39166666666666666,
      "diagnostic_macro_f1": 0.5812290351588436,
      "stale_recall": 0.9,
      "conflict_recall": 1.0,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 0.38461538461538464,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 0.7833333333333333,
      "unsafe_scope_miss_rate": 0.0,
      "escape_rate": 0.31666666666666665,
      "contaminated_citation_rate": 0.04922619047619047,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.6083333333333333,
      "confidence": 0.7883333333333333,
      "cost_usd": 0.000390555,
      "ece": 0.5283333333333333
    },
    "module_b_temporal_route": {
      "n": 50,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 0.96,
      "diagnostic_macro_f1": 0.2857142857142857,
      "stale_recall": 1.0,
      "conflict_recall": 1.0,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 0.0,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 0.0,
      "unsafe_scope_miss_rate": 0.0,
      "escape_rate": 0.94,
      "contaminated_citation_rate": 0.016,
      "compare_versions_rate": 1.0,
      "useful_compare_versions_rate": 1.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.02,
      "confidence": 0.9189999999999999,
      "cost_usd": 0.00047955299999999997,
      "ece": 0.057000000000000044
    },
    "module_c_static": {
      "n": 240,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 0.9083333333333333,
      "diagnostic_macro_f1": 0.4040549107228354,
      "stale_recall": 0.6666666666666666,
      "conflict_recall": 0.8712121212121212,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 0.24120603015075376,
      "citation_laundering_recall": 0.8611111111111112,
      "source_independence_accuracy": 0.22083333333333333,
      "unsafe_scope_miss_rate": 0.008333333333333333,
      "escape_rate": 0.7333333333333333,
      "contaminated_citation_rate": 0.21493055555555557,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.0125,
      "confidence": 0.7641666666666667,
      "cost_usd": 0.00045434625000000003,
      "ece": 0.1912500000000001
    },
    "module_c_clean_bm25_claim_accuracy": 0.875,
    "module_c_high_pressure_bm25_wrong_answer_rate": 0.9166666666666666,
    "module_c_high_pressure_recovery_delta": 0.9166666666666666,
    "module_c_hygienic_combo_claim_accuracy": 1.0,
    "module_c_hygienic_combo_contaminated_citation_rate": 0.1640625,
    "module_c_static_hygienic_combo_escape_rate": 0.75,
    "module_c_min_active_tool_escape_rate": 0.6041666666666666,
    "hidden_label_leakage": false,
    "wrong_answer_rate_replaces_g3": 0.9166666666666666,
    "mean_wrong_confidence": 0.45454545454545453,
    "overconfident_wrong_rate": 0.0
  }
}
```

## 2. Module A Prompt Comparison

| prompt | n | claim_accuracy | diagnostic_macro_f1 | stale_recall | conflict_recall | generated_lore_recall | no_primary_precision | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_diagnostics_v1 | 120 | 0.392 | 0.581 | 0.900 | 1.000 | 1.000 | 0.385 | 0.000 |
| evidence_graph_v3 | 120 | 0.425 | 0.316 | 0.000 | 0.025 | 0.050 | 0.800 | 0.442 |

## 3. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 248 | 307 | 34 | 275 | 0.447 | 0.879 | 0.593 |
| conflict | 238 | 271 | 58 | 297 | 0.468 | 0.804 | 0.591 |
| generated_lore | 75 | 138 | 19 | 632 | 0.352 | 0.798 | 0.489 |
| no_primary | 124 | 466 | 0 | 274 | 0.210 | 1.000 | 0.347 |
| citation_laundering | 71 | 228 | 29 | 536 | 0.237 | 0.710 | 0.356 |
| false_consensus | 134 | 259 | 22 | 449 | 0.341 | 0.859 | 0.488 |
| partial_support | 40 | 589 | 18 | 217 | 0.064 | 0.690 | 0.116 |

## 4. Temporal Tool Routing

| strategy | n | claim_accuracy | stale_recall | compare_versions_rate | useful_compare_versions_rate | tool_parse_success | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| forced_compare_versions | 60 | 0.983 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| route_then_answer_v1 | 60 | 0.967 | 1.000 | 0.983 | 0.983 | 1.000 | 0.000 |
| static_hygienic_combo | 60 | 0.983 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| tool_agent_3call_policy | 60 | 1.000 | 1.000 | 1.000 | 0.967 | 1.000 | 0.000 |

## 5. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 80 | 0.775 | 0.361 | 0.588 | 0.361 | 0.625 | 0.659 | 1.000 |
| bm25_top8 | forced_triage_tools | 48 | 0.938 | 0.447 | 0.604 | 0.234 | 0.667 | 1.000 | 1.000 |
| bm25_top8 | route_then_answer_v1 | 48 | 0.958 | 0.414 | 0.688 | 0.301 | 1.000 | 0.929 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 80 | 1.000 | 0.427 | 0.812 | 0.164 | 0.625 | 1.000 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 48 | 0.979 | 0.426 | 0.750 | 0.146 | 0.667 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v1 | 80 | 0.950 | 0.426 | 0.800 | 0.120 | 0.750 | 0.955 | 1.000 |

## 6. False-Consensus Stress Regression Check

| retriever | strategy | claim_accuracy | escape_rate | contaminated_citation_rate | diagnostic_macro_f1 |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 0.775 | 0.588 | 0.361 | 0.361 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 1.000 | 0.812 | 0.164 | 0.427 |

## 7. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 1.000 | 0.222 | 0.775 | 0.000 |
| bm25_top8 | forced_triage_tools | 1.000 | 0.261 | 0.938 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 1.000 | 0.261 | 0.958 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 1.000 | 0.242 | 1.000 | 0.000 |
| hygienic_combo_top8 | static_hygienic_combo | 1.000 | 0.279 | 0.979 | 0.021 |
| primary_preserve_top8 | evidence_diagnostics_v1 | 1.000 | 0.262 | 0.950 | 0.025 |

## 8. Active Tool Helpfulness And Harmfulness

| module | strategy | n | escape_rate | claim_accuracy | compare_versions_rate | useful_compare_versions_rate | trace_rate | search_contradictions_rate | primary_request_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | forced_compare_versions | 60 | 0.983 | 0.983 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| B | route_then_answer_v1 | 60 | 0.950 | 0.967 | 0.983 | 0.983 | 0.000 | 0.000 | 0.000 |
| B | static_hygienic_combo | 60 | 0.983 | 0.983 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| B | tool_agent_3call_policy | 60 | 1.000 | 1.000 | 1.000 | 0.967 | 0.267 | 0.267 | 0.433 |
| C | forced_triage_tools | 48 | 0.604 | 0.938 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |
| C | route_then_answer_v1 | 48 | 0.688 | 0.958 | 0.479 | 0.354 | 0.062 | 0.271 | 0.521 |
| C | static_hygienic_combo | 48 | 0.750 | 0.979 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 9. Qualitative Failure Cases

See `results/reports-phase2s/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.382412,
  "spent_usd": 0.422466,
  "soft_cap_usd": 50.0,
  "hard_cap_usd": 150.0,
  "abort_cap_usd": 300.0
}
```

## Unsafe Scope Misses

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2s_a_020 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_021 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_022 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_023 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_024 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_025 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_026 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_027 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_028 | A | stale_evidence | evidence_graph_v3 | 0.850 | stale_evidence |  |
| eha2s_a_029 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_030 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_031 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_032 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_033 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_035 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_036 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_037 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_038 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_039 | A | stale_evidence | evidence_graph_v3 | 0.900 | stale_evidence |  |
| eha2s_a_040 | A | conflicting_evidence | evidence_graph_v3 | 0.950 | conflicting_evidence |  |
