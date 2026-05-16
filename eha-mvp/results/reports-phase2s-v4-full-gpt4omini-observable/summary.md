# EHA Phase 2S Scope Diagnosis & Temporal Routing Repair Summary

## 1. Gate Result

```json
{
  "scope": "full",
  "passed": false,
  "checks": {
    "A1_claim_accuracy_at_least_0_90": true,
    "A2_diagnostic_macro_f1_at_least_0_70": true,
    "A3_stale_recall_at_least_0_75": true,
    "A4_conflict_recall_at_least_0_65": true,
    "A5_generated_lore_recall_at_least_0_70": true,
    "A6_no_primary_precision_at_least_0_90": true,
    "A7_unsafe_scope_miss_rate_at_most_0_25": true,
    "B1_compare_versions_rate_on_temporal_at_least_0_75": true,
    "B2_useful_compare_versions_rate_at_least_0_60": true,
    "B3_temporal_claim_accuracy_at_least_0_85": true,
    "B4_stale_recall_at_least_0_75": true,
    "B5_tool_parse_success_at_least_0_98": true,
    "B6_hidden_label_leakage_false": true,
    "C1_clean_control_claim_accuracy_at_least_0_90": true,
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
      "claim_accuracy": 0.9916666666666667,
      "diagnostic_macro_f1": 0.7486873173284323,
      "stale_recall": 1.0,
      "conflict_recall": 1.0,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 1.0,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 0.675,
      "unsafe_scope_miss_rate": 0.0,
      "escape_rate": 0.5,
      "contaminated_citation_rate": 0.004166666666666667,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.008333333333333333,
      "confidence": 0.9183333333333333,
      "cost_usd": 0.000542365,
      "ece": 0.0733333333333333
    },
    "module_a_prompt": "evidence_diagnostics_v4",
    "module_b_temporal_route": {
      "n": 50,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 0.98,
      "diagnostic_macro_f1": 0.2857142857142857,
      "stale_recall": 1.0,
      "conflict_recall": 1.0,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 0.0,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 0.0,
      "unsafe_scope_miss_rate": 0.0,
      "escape_rate": 0.98,
      "contaminated_citation_rate": 0.0,
      "compare_versions_rate": 1.0,
      "useful_compare_versions_rate": 1.0,
      "trace_rate": 0.02,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.02,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.02,
      "confidence": 0.938,
      "cost_usd": 0.000598806,
      "ece": 0.04200000000000004
    },
    "module_c_static": {
      "n": 240,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 0.9083333333333333,
      "diagnostic_macro_f1": 0.40707022599838094,
      "stale_recall": 0.6666666666666666,
      "conflict_recall": 0.8787878787878788,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 0.2513089005235602,
      "citation_laundering_recall": 0.8888888888888888,
      "source_independence_accuracy": 0.20416666666666666,
      "unsafe_scope_miss_rate": 0.0,
      "escape_rate": 0.7458333333333333,
      "contaminated_citation_rate": 0.196875,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.016666666666666666,
      "confidence": 0.7695000000000001,
      "cost_usd": 0.00056201625,
      "ece": 0.16799999999999993
    },
    "module_c_clean_bm25_claim_accuracy": 1.0,
    "module_c_high_pressure_bm25_wrong_answer_rate": 1.0,
    "module_c_high_pressure_recovery_delta": 1.0,
    "module_c_hygienic_combo_claim_accuracy": 0.975,
    "module_c_hygienic_combo_contaminated_citation_rate": 0.1453125,
    "module_c_static_hygienic_combo_escape_rate": 0.7291666666666666,
    "module_c_min_active_tool_escape_rate": 0.6458333333333334,
    "hidden_label_leakage": false,
    "wrong_answer_rate_replaces_g3": 1.0,
    "mean_wrong_confidence": 0.4583333333333333,
    "overconfident_wrong_rate": 0.08333333333333333
  }
}
```

## 2. Module A Prompt Comparison

| prompt | n | claim_accuracy | diagnostic_macro_f1 | stale_recall | conflict_recall | generated_lore_recall | no_primary_precision | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_diagnostics_v4 | 120 | 0.992 | 0.749 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

## 3. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 253 | 280 | 9 | 202 | 0.475 | 0.966 | 0.636 |
| conflict | 234 | 265 | 22 | 223 | 0.469 | 0.914 | 0.620 |
| generated_lore | 74 | 124 | 0 | 546 | 0.374 | 1.000 | 0.544 |
| no_primary | 104 | 419 | 0 | 221 | 0.199 | 1.000 | 0.332 |
| citation_laundering | 74 | 252 | 6 | 412 | 0.227 | 0.925 | 0.365 |
| false_consensus | 132 | 266 | 24 | 322 | 0.332 | 0.846 | 0.477 |
| partial_support | 38 | 507 | 0 | 199 | 0.070 | 1.000 | 0.130 |

## 4. Temporal Tool Routing

| strategy | n | claim_accuracy | stale_recall | compare_versions_rate | useful_compare_versions_rate | tool_parse_success | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| forced_compare_versions | 60 | 0.983 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| route_then_answer_v1 | 60 | 0.983 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| static_hygienic_combo | 60 | 0.983 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| tool_agent_3call_policy | 60 | 0.983 | 0.980 | 1.000 | 0.983 | 1.000 | 0.017 |

## 5. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 80 | 0.775 | 0.369 | 0.625 | 0.330 | 0.625 | 0.636 | 1.000 |
| bm25_top8 | forced_triage_tools | 48 | 0.917 | 0.426 | 0.688 | 0.247 | 1.000 | 0.964 | 1.000 |
| bm25_top8 | route_then_answer_v1 | 48 | 0.917 | 0.416 | 0.646 | 0.317 | 1.000 | 0.857 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 80 | 0.975 | 0.427 | 0.775 | 0.145 | 0.750 | 1.000 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 48 | 0.958 | 0.452 | 0.729 | 0.163 | 1.000 | 0.964 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v1 | 80 | 0.975 | 0.427 | 0.838 | 0.116 | 0.625 | 1.000 | 1.000 |

## 6. False-Consensus Stress Regression Check

| retriever | strategy | claim_accuracy | escape_rate | contaminated_citation_rate | diagnostic_macro_f1 |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 0.775 | 0.625 | 0.330 | 0.369 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 0.975 | 0.775 | 0.145 | 0.427 |

## 7. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 1.000 | 0.235 | 0.775 | 0.000 |
| bm25_top8 | forced_triage_tools | 1.000 | 0.267 | 0.917 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 1.000 | 0.267 | 0.917 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 1.000 | 0.250 | 0.975 | 0.000 |
| hygienic_combo_top8 | static_hygienic_combo | 1.000 | 0.273 | 0.958 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v1 | 1.000 | 0.271 | 0.975 | 0.000 |

## 8. Active Tool Helpfulness And Harmfulness

| module | strategy | n | escape_rate | claim_accuracy | compare_versions_rate | useful_compare_versions_rate | trace_rate | search_contradictions_rate | primary_request_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | forced_compare_versions | 60 | 0.983 | 0.983 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| B | route_then_answer_v1 | 60 | 0.983 | 0.983 | 1.000 | 1.000 | 0.017 | 0.000 | 0.017 |
| B | static_hygienic_combo | 60 | 0.983 | 0.983 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| B | tool_agent_3call_policy | 60 | 0.983 | 0.983 | 1.000 | 0.983 | 0.400 | 0.283 | 0.300 |
| C | forced_triage_tools | 48 | 0.688 | 0.917 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |
| C | route_then_answer_v1 | 48 | 0.646 | 0.917 | 0.562 | 0.396 | 0.042 | 0.188 | 0.521 |
| C | static_hygienic_combo | 48 | 0.729 | 0.958 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 9. Qualitative Failure Cases

See `results/reports-phase2s-v4-full-gpt4omini-observable/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

## 10. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.430473,
  "spent_usd": 0.470679,
  "soft_cap_usd": 2.0,
  "hard_cap_usd": 5.0,
  "abort_cap_usd": 10.0
}
```

## Unsafe Scope Misses

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2s_b_036 | B | certification_expired_or_renewed | tool_agent_3call_policy | 0.950 | stale_evidence |  |
