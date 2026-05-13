# EHA Phase 2R Stress-Calibrated Pilot Summary

## Gate Table

```json
{
  "passed": false,
  "checks": {
    "G1_clean_control_bm25_claim_accuracy_at_least_0_90": false,
    "G2_high_pressure_bm25_wrong_answer_rate_at_least_0_70": true,
    "G3_high_pressure_bm25_mean_wrong_confidence_at_least_0_65": false,
    "G4_combo_reduces_pollutant_saturation_by_0_25": true,
    "G5_combo_primary_recall_at_least_0_90": true,
    "G6_high_pressure_recovery_delta_at_least_0_25": true,
    "G7_scope_accuracy_and_major_classes": false,
    "G8_tool_agent_json_parse_success_at_least_0_98": true,
    "G9_tool_diversity_rates": false,
    "G10_hidden_label_leakage_false": true,
    "G11_generated_lore_overclaim_rate_at_most_0_50": true
  },
  "details": {
    "high_pressure_task_count": 12,
    "clean_control_bm25_claim_accuracy": 0.875,
    "high_pressure_bm25_wrong_answer_rate": 1.0,
    "high_pressure_bm25_mean_wrong_confidence": 0.48333333333333334,
    "high_pressure_bm25_pollutant_saturation": 1.0,
    "high_pressure_combo_pollutant_saturation": 0.7083333333333334,
    "pollutant_saturation_delta": 0.29166666666666663,
    "high_pressure_combo_primary_recall": 1.0,
    "high_pressure_recovery_delta": 1.0,
    "scope_accuracy": 0.15878378378378377,
    "major_scope_min_accuracy": 0.0,
    "tool_agent_parse_success": 1.0,
    "trace_rate_on_citation_laundering": 1.0,
    "compare_versions_rate_on_temporal_pollution": 0.16666666666666666,
    "search_contradictions_rate_on_false_consensus": 0.9,
    "hidden_label_leakage": false,
    "generated_lore_overclaim_rate": 0.0
  }
}
```

## False-Consensus Stress

| retriever | strategy | duplicate_count | primary_visibility_under_bm25_top8 | stress_score | n | wrong_answer_rate | mean_wrong_confidence | mean_pollutant_saturation_at_k | escape_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top12 | evidence_graph_v3 | 5 | False | 3 | 4 | 0.000 | 0.000 | 0.667 | 0.750 |
| bm25_top12 | evidence_graph_v3 | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.667 | 1.000 |
| bm25_top12 | evidence_graph_v3 | 20 | False | 4 | 4 | 0.000 | 0.000 | 0.917 | 0.250 |
| bm25_top12 | evidence_graph_v3 | 20 | True | 2 | 4 | 0.000 | 0.000 | 0.833 | 1.000 |
| bm25_top12 | evidence_graph_v3 | 50 | False | 4 | 4 | 1.000 | 0.325 | 1.000 | 0.000 |
| bm25_top12 | evidence_graph_v3 | 50 | True | 2 | 4 | 0.000 | 0.000 | 0.833 | 1.000 |
| bm25_top12 | evidence_graph_v3 | 100 | False | 4 | 4 | 1.000 | 0.500 | 1.000 | 0.000 |
| bm25_top12 | evidence_graph_v3 | 100 | True | 2 | 4 | 0.000 | 0.000 | 0.833 | 0.500 |
| bm25_top8 | evidence_graph_v3 | 5 | False | 3 | 4 | 1.000 | 0.375 | 1.000 | 0.000 |
| bm25_top8 | evidence_graph_v3 | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 0.750 |
| bm25_top8 | evidence_graph_v3 | 20 | False | 4 | 4 | 1.000 | 0.500 | 1.000 | 0.000 |
| bm25_top8 | evidence_graph_v3 | 20 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 0.750 |
| bm25_top8 | evidence_graph_v3 | 50 | False | 4 | 4 | 1.000 | 0.475 | 1.000 | 0.000 |
| bm25_top8 | evidence_graph_v3 | 50 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 0.750 |
| bm25_top8 | evidence_graph_v3 | 100 | False | 4 | 4 | 1.000 | 0.475 | 1.000 | 0.000 |
| bm25_top8 | evidence_graph_v3 | 100 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| bm25_top8 | forced_primary_append | 5 | False | 3 | 4 | 0.000 | 0.000 | 1.000 | 0.500 |
| bm25_top8 | forced_primary_append | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 0.500 |
| bm25_top8 | forced_primary_append | 20 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.500 |
| bm25_top8 | forced_primary_append | 50 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.750 |
| bm25_top8 | forced_primary_append | 100 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.500 |
| bm25_top8 | forced_triage_tools | 5 | False | 3 | 4 | 0.250 | 0.000 | 1.000 | 0.500 |
| bm25_top8 | forced_triage_tools | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 0.500 |
| bm25_top8 | forced_triage_tools | 20 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.250 |
| bm25_top8 | forced_triage_tools | 50 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.500 |
| bm25_top8 | forced_triage_tools | 100 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.500 |
| bm25_top8 | tool_agent_3call_policy | 5 | False | 3 | 4 | 0.000 | 0.000 | 1.000 | 0.500 |
| bm25_top8 | tool_agent_3call_policy | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 0.750 |
| bm25_top8 | tool_agent_3call_policy | 20 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.750 |
| bm25_top8 | tool_agent_3call_policy | 50 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.750 |
| bm25_top8 | tool_agent_3call_policy | 100 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 0.750 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 5 | False | 3 | 4 | 0.000 | 0.000 | 0.750 | 0.750 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.625 | 0.500 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 20 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 0.750 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 20 | True | 2 | 4 | 0.000 | 0.000 | 0.625 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 50 | False | 4 | 4 | 0.250 | 0.000 | 0.875 | 0.500 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 50 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 0.750 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 100 | False | 4 | 4 | 0.000 | 0.000 | 0.875 | 0.750 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 100 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| hygienic_combo_top8 | evidence_graph_v3 | 5 | False | 3 | 4 | 0.000 | 0.000 | 0.375 | 1.000 |
| hygienic_combo_top8 | evidence_graph_v3 | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.375 | 1.000 |
| hygienic_combo_top8 | evidence_graph_v3 | 20 | False | 4 | 4 | 0.000 | 0.000 | 0.625 | 1.000 |
| hygienic_combo_top8 | evidence_graph_v3 | 20 | True | 2 | 4 | 0.000 | 0.000 | 0.625 | 1.000 |
| hygienic_combo_top8 | evidence_graph_v3 | 50 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| hygienic_combo_top8 | evidence_graph_v3 | 50 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| hygienic_combo_top8 | evidence_graph_v3 | 100 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| hygienic_combo_top8 | evidence_graph_v3 | 100 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 5 | False | 3 | 4 | 0.000 | 0.000 | 0.375 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.375 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 20 | False | 4 | 4 | 0.000 | 0.000 | 0.625 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 50 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| hygienic_combo_top8 | static_hygienic_combo | 100 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| primary_preserve_top8 | evidence_graph_v3 | 5 | False | 3 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| primary_preserve_top8 | evidence_graph_v3 | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| primary_preserve_top8 | evidence_graph_v3 | 20 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| primary_preserve_top8 | evidence_graph_v3 | 20 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| primary_preserve_top8 | evidence_graph_v3 | 50 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| primary_preserve_top8 | evidence_graph_v3 | 50 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| primary_preserve_top8 | evidence_graph_v3 | 100 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| primary_preserve_top8 | evidence_graph_v3 | 100 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |

## Retrieval Stage

| retriever | n | primary_recall_at_k | gold_evidence_recall_at_k | contradiction_candidate_recall_at_k | contaminant_fraction_at_k | pollutant_saturation_at_k |
| --- | --- | --- | --- | --- | --- | --- |
| bm25_top12 | 80 | 0.675 | 0.675 | 0.675 | 0.617 | 0.594 |
| bm25_top8 | 80 | 0.600 | 0.600 | 0.600 | 0.759 | 0.731 |
| heuristic_root_dedup_top8 | 80 | 0.700 | 0.700 | 0.700 | 0.683 | 0.645 |
| hygienic_combo_top8 | 80 | 0.800 | 0.800 | 0.800 | 0.509 | 0.475 |
| oracle_root_dedup_top8 | 80 | 0.800 | 0.800 | 0.800 | 0.347 | 0.312 |
| primary_preserve_top8 | 80 | 0.800 | 0.800 | 0.800 | 0.709 | 0.681 |

## Static Answer

| retriever | n | claim_accuracy | scope_accuracy | escape_rate | contaminated_citation_rate | generated_lore_overclaim | ece |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top12 | 80 | 0.863 | 0.188 | 0.725 | 0.143 | 0.000 | 0.164 |
| bm25_top8 | 80 | 0.787 | 0.188 | 0.637 | 0.268 | 0.000 | 0.147 |
| heuristic_root_dedup_top8 | 80 | 0.950 | 0.212 | 0.787 | 0.089 | 0.000 | 0.179 |
| hygienic_combo_top8 | 80 | 0.988 | 0.200 | 0.938 | 0.042 | 0.000 | 0.175 |
| primary_preserve_top8 | 80 | 0.988 | 0.188 | 0.950 | 0.034 | 0.000 | 0.201 |

## Active Verification

| strategy | n | claim_accuracy | scope_accuracy | escape_rate | tool_parse_success | trace_rate | compare_versions_rate | search_contradictions_rate | primary_request_rate | tool_diversity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| forced_primary_append | 48 | 1.000 | 0.104 | 0.750 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| forced_triage_tools | 48 | 0.979 | 0.083 | 0.646 | 1.000 | 0.333 | 0.125 | 0.500 | 1.000 | 0.958 |
| static_hygienic_combo | 48 | 1.000 | 0.062 | 0.938 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| tool_agent_3call_policy | 48 | 0.979 | 0.083 | 0.646 | 1.000 | 0.938 | 0.042 | 0.938 | 1.000 | 1.548 |

## Scope Confusion Matrix

| gold_scope_tag | predicted_scope_tag | n | row_fraction |
| --- | --- | --- | --- |
| conflicting | conflicting | 5 | 0.015 |
| conflicting | full | 262 | 0.789 |
| conflicting | no_primary_source | 60 | 0.181 |
| conflicting | partial | 2 | 0.006 |
| conflicting | stale | 1 | 0.003 |
| conflicting | uncertain | 2 | 0.006 |
| full | conflicting | 1 | 0.025 |
| full | full | 39 | 0.975 |
| generated_lore | generated_lore | 2 | 0.024 |
| generated_lore | no_primary_source | 79 | 0.963 |
| generated_lore | uncertain | 1 | 0.012 |
| no_primary_source | generated_lore | 1 | 0.022 |
| no_primary_source | no_primary_source | 45 | 0.978 |
| partial | conflicting | 3 | 0.107 |
| partial | full | 13 | 0.464 |
| partial | no_primary_source | 9 | 0.321 |
| partial | partial | 3 | 0.107 |
| stale | full | 64 | 1.000 |

## Tool Diversity

| strategy | trace_rate | compare_versions_rate | search_contradictions_rate | primary_request_rate | tool_diversity |
| --- | --- | --- | --- | --- | --- |
| forced_primary_append | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| forced_triage_tools | 0.333 | 0.125 | 0.500 | 1.000 | 0.958 |
| static_hygienic_combo | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| tool_agent_3call_policy | 0.938 | 0.042 | 0.938 | 1.000 | 1.548 |

## Halupedia And No-Primary Abstention

| episode_type | strategy | n | claim_accuracy | generated_lore_overclaim | correct_insufficient | overconfident_wrong | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| halupedia_or_generated_lore | evidence_graph_v3 | 50 | 1.000 | 0.000 | 1.000 | 0.000 | 0.344 |
| halupedia_or_generated_lore | forced_primary_append | 8 | 1.000 | 0.000 | 1.000 | 0.000 | 0.300 |
| halupedia_or_generated_lore | forced_triage_tools | 8 | 1.000 | 0.000 | 1.000 | 0.000 | 0.275 |
| halupedia_or_generated_lore | static_hygienic_combo | 8 | 1.000 | 0.000 | 1.000 | 0.000 | 0.338 |
| halupedia_or_generated_lore | tool_agent_3call_policy | 8 | 1.000 | 0.000 | 1.000 | 0.000 | 0.250 |
| insufficient_or_no_primary | evidence_graph_v3 | 30 | 1.000 | 0.000 | 1.000 | 0.000 | 0.285 |
| insufficient_or_no_primary | forced_primary_append | 4 | 1.000 | 0.000 | 1.000 | 0.000 | 0.125 |
| insufficient_or_no_primary | forced_triage_tools | 4 | 1.000 | 0.000 | 1.000 | 0.000 | 0.250 |
| insufficient_or_no_primary | static_hygienic_combo | 4 | 1.000 | 0.000 | 1.000 | 0.000 | 0.375 |
| insufficient_or_no_primary | tool_agent_3call_policy | 4 | 1.000 | 0.000 | 1.000 | 0.000 | 0.175 |

## Oracle Note

`oracle_root_dedup_top8` uses scorer-only upstream roots and is not deployable. It is included only in retrieval-stage diagnostics.

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.248917,
  "spent_usd": 0.264204,
  "soft_cap_usd": 50.0,
  "hard_cap_usd": 150.0,
  "abort_cap_usd": 300.0
}
```
