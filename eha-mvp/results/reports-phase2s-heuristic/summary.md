# EHA Phase 2S Scope Diagnosis & Temporal Routing Repair Summary

## 1. Gate Result

```json
{
  "passed": true,
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
    "C5_hygienic_combo_contaminated_citation_rate_at_most_0_08": true,
    "C6_diagnostic_macro_f1_at_least_0_60": true,
    "C7_stale_recall_at_least_0_65": true,
    "C8_conflict_recall_at_least_0_60": true,
    "C9_generated_lore_recall_at_least_0_60": true,
    "C10_active_tool_escape_not_more_than_0_05_below_static": true
  },
  "details": {
    "module_a": {
      "n": 120,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 1.0,
      "diagnostic_macro_f1": 1.0,
      "stale_recall": 1.0,
      "conflict_recall": 1.0,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 1.0,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 1.0,
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
      "confidence": 0.7133333333333333,
      "cost_usd": 0.0,
      "ece": 0.28666666666666674
    },
    "module_b_temporal_route": {
      "n": 50,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 1.0,
      "diagnostic_macro_f1": 1.0,
      "stale_recall": 1.0,
      "conflict_recall": 1.0,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 1.0,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 1.0,
      "unsafe_scope_miss_rate": 0.0,
      "escape_rate": 1.0,
      "contaminated_citation_rate": 0.0,
      "compare_versions_rate": 1.0,
      "useful_compare_versions_rate": 1.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 1.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.0,
      "confidence": 0.76,
      "cost_usd": 0.0,
      "ece": 0.24
    },
    "module_c_static": {
      "n": 240,
      "parse_success": 1.0,
      "tool_parse_success": 1.0,
      "claim_accuracy": 0.95,
      "diagnostic_macro_f1": 0.9931972789115646,
      "stale_recall": 1.0,
      "conflict_recall": 0.9090909090909091,
      "generated_lore_recall": 1.0,
      "no_primary_precision": 1.0,
      "citation_laundering_recall": 1.0,
      "source_independence_accuracy": 0.95,
      "unsafe_scope_miss_rate": 0.05,
      "escape_rate": 0.9333333333333333,
      "contaminated_citation_rate": 0.05,
      "compare_versions_rate": 0.0,
      "useful_compare_versions_rate": 0.0,
      "trace_rate": 0.0,
      "search_contradictions_rate": 0.0,
      "primary_request_rate": 0.0,
      "hidden_label_leakage": 0.0,
      "overconfident_wrong_rate": 0.05,
      "confidence": 0.73,
      "cost_usd": 0.0,
      "ece": 0.21999999999999997
    },
    "module_c_clean_bm25_claim_accuracy": 1.0,
    "module_c_high_pressure_bm25_wrong_answer_rate": 1.0,
    "module_c_high_pressure_recovery_delta": 1.0,
    "module_c_hygienic_combo_claim_accuracy": 1.0,
    "module_c_hygienic_combo_contaminated_citation_rate": 0.0,
    "module_c_static_hygienic_combo_escape_rate": 1.0,
    "module_c_min_active_tool_escape_rate": 1.0,
    "hidden_label_leakage": false,
    "wrong_answer_rate_replaces_g3": 1.0,
    "mean_wrong_confidence": 0.7200000000000001,
    "overconfident_wrong_rate": 1.0
  }
}
```

## 2. Module A Prompt Comparison

| prompt | n | claim_accuracy | diagnostic_macro_f1 | stale_recall | conflict_recall | generated_lore_recall | no_primary_precision | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| evidence_diagnostics_v1 | 120 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| evidence_graph_v3 | 120 | 1.000 | 0.857 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

## 3. Diagnostic Macro-F1 And Per-Risk Recall

| flag | tp | fp | fn | tn | precision | recall | f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| stale | 282 | 0 | 0 | 582 | 1.000 | 1.000 | 1.000 |
| conflict | 284 | 0 | 12 | 568 | 1.000 | 0.959 | 0.979 |
| generated_lore | 94 | 0 | 0 | 770 | 1.000 | 1.000 | 1.000 |
| no_primary | 124 | 0 | 0 | 740 | 1.000 | 1.000 | 1.000 |
| citation_laundering | 80 | 0 | 20 | 764 | 1.000 | 0.800 | 0.889 |
| false_consensus | 156 | 0 | 0 | 708 | 1.000 | 1.000 | 1.000 |
| partial_support | 58 | 0 | 0 | 806 | 1.000 | 1.000 | 1.000 |

## 4. Temporal Tool Routing

| strategy | n | claim_accuracy | stale_recall | compare_versions_rate | useful_compare_versions_rate | tool_parse_success | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| forced_compare_versions | 60 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| route_then_answer_v1 | 60 | 1.000 | 1.000 | 0.833 | 0.833 | 1.000 | 0.000 |
| static_hygienic_combo | 60 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| tool_agent_3call_policy | 60 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 |

## 5. Integrated Regression On Phase 2R

| retriever | strategy | n | claim_accuracy | diagnostic_macro_f1 | escape_rate | contaminated_citation_rate | stale_recall | conflict_recall | generated_lore_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 80 | 0.850 | 0.977 | 0.800 | 0.150 | 1.000 | 0.727 | 1.000 |
| bm25_top8 | forced_triage_tools | 48 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| bm25_top8 | route_then_answer_v1 | 48 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 80 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 48 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_diagnostics_v1 | 80 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 1.000 |

## 6. False-Consensus Stress Regression Check

| retriever | strategy | claim_accuracy | escape_rate | contaminated_citation_rate | diagnostic_macro_f1 |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 0.850 | 0.800 | 0.150 | 0.977 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 1.000 | 1.000 | 0.000 | 1.000 |

## 7. Generated-Lore Detection Vs No-Primary Abstention

| retriever | strategy | generated_lore_recall | no_primary_precision | claim_accuracy | unsafe_scope_miss_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top8 | evidence_diagnostics_v1 | 1.000 | 1.000 | 0.850 | 0.150 |
| bm25_top8 | forced_triage_tools | 1.000 | 1.000 | 1.000 | 0.000 |
| bm25_top8 | route_then_answer_v1 | 1.000 | 1.000 | 1.000 | 0.000 |
| hygienic_combo_top8 | evidence_diagnostics_v1 | 1.000 | 1.000 | 1.000 | 0.000 |
| hygienic_combo_top8 | static_hygienic_combo | 1.000 | 1.000 | 1.000 | 0.000 |
| primary_preserve_top8 | evidence_diagnostics_v1 | 1.000 | 1.000 | 1.000 | 0.000 |

## 8. Active Tool Helpfulness And Harmfulness

| module | strategy | n | escape_rate | claim_accuracy | compare_versions_rate | useful_compare_versions_rate | trace_rate | search_contradictions_rate | primary_request_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | forced_compare_versions | 60 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| B | route_then_answer_v1 | 60 | 1.000 | 1.000 | 0.833 | 0.833 | 0.000 | 0.000 | 1.000 |
| B | static_hygienic_combo | 60 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| B | tool_agent_3call_policy | 60 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| C | forced_triage_tools | 48 | 1.000 | 1.000 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |
| C | route_then_answer_v1 | 48 | 1.000 | 1.000 | 1.000 | 0.750 | 0.000 | 0.000 | 1.000 |
| C | static_hygienic_combo | 48 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 9. Qualitative Failure Cases

See `results/reports-phase2s-heuristic/failure_cases_phase2s.md` for at least 10 qualitative cases when available.

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

| task_id | module | episode_type | strategy | confidence | gold_critical_risks | predicted_critical_risks |
| --- | --- | --- | --- | --- | --- | --- |
| eha2r_020 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_021 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_022 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_023 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_028 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_029 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_030 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_031 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_036 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_037 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_038 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
| eha2r_039 | C | false_consensus_stress | evidence_diagnostics_v1 | 0.720 | conflicting_evidence,false_consensus | false_consensus |
