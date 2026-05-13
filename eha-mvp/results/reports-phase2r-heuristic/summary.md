# EHA Phase 2R Stress-Calibrated Pilot Summary

## Gate Table

```json
{
  "passed": true,
  "checks": {
    "G1_clean_control_bm25_claim_accuracy_at_least_0_90": true,
    "G2_high_pressure_bm25_wrong_answer_rate_at_least_0_70": true,
    "G3_high_pressure_bm25_mean_wrong_confidence_at_least_0_65": true,
    "G4_combo_reduces_pollutant_saturation_by_0_25": true,
    "G5_combo_primary_recall_at_least_0_90": true,
    "G6_high_pressure_recovery_delta_at_least_0_25": true,
    "G7_scope_accuracy_and_major_classes": true,
    "G8_tool_agent_json_parse_success_at_least_0_98": true,
    "G9_tool_diversity_rates": true,
    "G10_hidden_label_leakage_false": true,
    "G11_generated_lore_overclaim_rate_at_most_0_50": true
  },
  "details": {
    "high_pressure_task_count": 12,
    "clean_control_bm25_claim_accuracy": 1.0,
    "high_pressure_bm25_wrong_answer_rate": 1.0,
    "high_pressure_bm25_mean_wrong_confidence": 0.82,
    "high_pressure_bm25_pollutant_saturation": 1.0,
    "high_pressure_combo_pollutant_saturation": 0.7083333333333334,
    "pollutant_saturation_delta": 0.29166666666666663,
    "high_pressure_combo_primary_recall": 1.0,
    "high_pressure_recovery_delta": 1.0,
    "scope_accuracy": 0.9425675675675675,
    "major_scope_min_accuracy": 0.8780487804878049,
    "tool_agent_parse_success": 1.0,
    "trace_rate_on_citation_laundering": 1.0,
    "compare_versions_rate_on_temporal_pollution": 1.0,
    "search_contradictions_rate_on_false_consensus": 1.0,
    "hidden_label_leakage": false,
    "generated_lore_overclaim_rate": 0.078125
  }
}
```

## False-Consensus Stress

| retriever | strategy | duplicate_count | primary_visibility_under_bm25_top8 | stress_score | n | wrong_answer_rate | mean_wrong_confidence | mean_pollutant_saturation_at_k | escape_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top12 | evidence_graph_v3 | 5 | False | 3 | 4 | 0.000 | 0.000 | 0.667 | 1.000 |
| bm25_top12 | evidence_graph_v3 | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.667 | 1.000 |
| bm25_top12 | evidence_graph_v3 | 20 | False | 4 | 4 | 1.000 | 0.820 | 0.917 | 0.000 |
| bm25_top12 | evidence_graph_v3 | 20 | True | 2 | 4 | 0.000 | 0.000 | 0.833 | 1.000 |
| bm25_top12 | evidence_graph_v3 | 50 | False | 4 | 4 | 1.000 | 0.820 | 1.000 | 0.000 |
| bm25_top12 | evidence_graph_v3 | 50 | True | 2 | 4 | 0.000 | 0.000 | 0.833 | 1.000 |
| bm25_top12 | evidence_graph_v3 | 100 | False | 4 | 4 | 1.000 | 0.820 | 1.000 | 0.000 |
| bm25_top12 | evidence_graph_v3 | 100 | True | 2 | 4 | 0.000 | 0.000 | 0.833 | 1.000 |
| bm25_top8 | evidence_graph_v3 | 5 | False | 3 | 4 | 0.000 | 0.000 | 1.000 | 0.000 |
| bm25_top8 | evidence_graph_v3 | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| bm25_top8 | evidence_graph_v3 | 20 | False | 4 | 4 | 1.000 | 0.820 | 1.000 | 0.000 |
| bm25_top8 | evidence_graph_v3 | 20 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| bm25_top8 | evidence_graph_v3 | 50 | False | 4 | 4 | 1.000 | 0.820 | 1.000 | 0.000 |
| bm25_top8 | evidence_graph_v3 | 50 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| bm25_top8 | evidence_graph_v3 | 100 | False | 4 | 4 | 1.000 | 0.820 | 1.000 | 0.000 |
| bm25_top8 | evidence_graph_v3 | 100 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| bm25_top8 | forced_primary_append | 5 | False | 3 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | forced_primary_append | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| bm25_top8 | forced_primary_append | 20 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | forced_primary_append | 50 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | forced_primary_append | 100 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | forced_triage_tools | 5 | False | 3 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | forced_triage_tools | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| bm25_top8 | forced_triage_tools | 20 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | forced_triage_tools | 50 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | forced_triage_tools | 100 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | tool_agent_3call_policy | 5 | False | 3 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | tool_agent_3call_policy | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| bm25_top8 | tool_agent_3call_policy | 20 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | tool_agent_3call_policy | 50 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| bm25_top8 | tool_agent_3call_policy | 100 | False | 4 | 4 | 0.000 | 0.000 | 1.000 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 5 | False | 3 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 5 | True | 1 | 4 | 0.000 | 0.000 | 0.625 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 20 | False | 4 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 20 | True | 2 | 4 | 0.000 | 0.000 | 0.625 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 50 | False | 4 | 4 | 0.000 | 0.000 | 0.875 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 50 | True | 2 | 4 | 0.000 | 0.000 | 0.750 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v3 | 100 | False | 4 | 4 | 0.000 | 0.000 | 0.875 | 1.000 |
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
| bm25_top12 | 80 | 0.850 | 0.850 | 0.850 | 0.150 | 0.000 | 0.383 |
| bm25_top8 | 80 | 0.725 | 0.725 | 0.675 | 0.275 | 0.125 | 0.439 |
| heuristic_root_dedup_top8 | 80 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.300 |
| hygienic_combo_top8 | 80 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.300 |
| primary_preserve_top8 | 80 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.300 |

## Active Verification

| strategy | n | claim_accuracy | scope_accuracy | escape_rate | tool_parse_success | trace_rate | compare_versions_rate | search_contradictions_rate | primary_request_rate | tool_diversity |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| forced_primary_append | 48 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| forced_triage_tools | 48 | 1.000 | 1.000 | 1.000 | 1.000 | 0.333 | 0.125 | 0.500 | 1.000 | 0.958 |
| static_hygienic_combo | 48 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| tool_agent_3call_policy | 48 | 1.000 | 1.000 | 1.000 | 1.000 | 0.750 | 0.125 | 0.667 | 1.000 | 1.300 |

## Scope Confusion Matrix

| gold_scope_tag | predicted_scope_tag | n | row_fraction |
| --- | --- | --- | --- |
| conflicting | conflicting | 308 | 0.928 |
| conflicting | full | 24 | 0.072 |
| full | full | 40 | 1.000 |
| generated_lore | full | 10 | 0.122 |
| generated_lore | generated_lore | 72 | 0.878 |
| no_primary_source | no_primary_source | 46 | 1.000 |
| partial | partial | 28 | 1.000 |
| stale | stale | 64 | 1.000 |

## Tool Diversity

| strategy | trace_rate | compare_versions_rate | search_contradictions_rate | primary_request_rate | tool_diversity |
| --- | --- | --- | --- | --- | --- |
| forced_primary_append | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| forced_triage_tools | 0.333 | 0.125 | 0.500 | 1.000 | 0.958 |
| static_hygienic_combo | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| tool_agent_3call_policy | 0.750 | 0.125 | 0.667 | 1.000 | 1.300 |

## Halupedia And No-Primary Abstention

| episode_type | strategy | n | claim_accuracy | generated_lore_overclaim | correct_insufficient | overconfident_wrong | confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| halupedia_or_generated_lore | evidence_graph_v3 | 50 | 0.800 | 0.200 | 0.800 | 0.200 | 0.628 |
| halupedia_or_generated_lore | forced_primary_append | 8 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |
| halupedia_or_generated_lore | forced_triage_tools | 8 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |
| halupedia_or_generated_lore | static_hygienic_combo | 8 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |
| halupedia_or_generated_lore | tool_agent_3call_policy | 8 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |
| insufficient_or_no_primary | evidence_graph_v3 | 30 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |
| insufficient_or_no_primary | forced_primary_append | 4 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |
| insufficient_or_no_primary | forced_triage_tools | 4 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |
| insufficient_or_no_primary | static_hygienic_combo | 4 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |
| insufficient_or_no_primary | tool_agent_3call_policy | 4 | 1.000 | 0.000 | 1.000 | 0.000 | 0.580 |

## Oracle Note

`oracle_root_dedup_top8` uses scorer-only upstream roots and is not deployable. It is included only in retrieval-stage diagnostics.

## Cost Report

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
