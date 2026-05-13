# EHA Phase 2 Pilot Summary

## Pilot Gate

```json
{
  "passed": true,
  "checks": {
    "clean_control_bm25_evidence_graph_v2_accuracy_at_least_0_90": true,
    "false_consensus_bm25_wrong_answer_rate_at_least_0_60": true,
    "primary_preserve_improves_primary_recall_by_0_25": true,
    "oracle_root_dedup_lowers_pollutant_saturation": true,
    "mixed_source_v2_not_all_zero_accuracy": true,
    "tool_agent_json_parse_success_at_least_0_95": true,
    "tool_outputs_do_not_leak_hidden_labels": true
  },
  "details": {
    "clean_control_bm25_accuracy": 1.0,
    "false_consensus_bm25_wrong_answer_rate": 0.75,
    "bm25_primary_recall": 0.75,
    "primary_preserve_primary_recall": 1.0,
    "primary_recall_delta": 0.25,
    "bm25_false_consensus_pollutant_saturation": 0.6875,
    "oracle_false_consensus_pollutant_saturation": 0.125,
    "pollutant_saturation_delta": 0.5625,
    "mixed_source_v2_accuracy": 1.0,
    "tool_agent_json_parse_success": 1.0,
    "tool_outputs_leak_hidden_labels": false
  }
}
```

## Retrieval Stage

| retriever | n | primary_recall_at_k | gold_evidence_recall_at_k | contaminant_fraction_at_k | unique_upstream_roots_at_k | pollutant_saturation_at_k |
| --- | --- | --- | --- | --- | --- | --- |
| bm25_top12 | 24 | 0.917 | 0.917 | 0.469 | 7.792 | 0.434 |
| bm25_top8 | 24 | 0.875 | 0.875 | 0.583 | 4.708 | 0.536 |
| heuristic_root_dedup_top8 | 24 | 1.000 | 1.000 | 0.479 | 5.583 | 0.427 |
| oracle_root_dedup_top8 | 24 | 0.958 | 0.958 | 0.172 | 8.000 | 0.125 |
| primary_preserve_top8 | 24 | 1.000 | 1.000 | 0.562 | 4.875 | 0.516 |

## Final Answer By Retriever

| retriever | n | claim_accuracy | scope_accuracy | escape_rate | primary_recovery_rate | contaminated_citation_rate | ece |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top12 | 24 | 0.833 | 1.000 | 0.833 | 0.958 | 0.167 | 0.376 |
| bm25_top8 | 72 | 0.764 | 1.000 | 0.764 | 0.972 | 0.236 | 0.417 |
| heuristic_root_dedup_top8 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.277 |
| oracle_root_dedup_top8 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.277 |
| primary_preserve_top8 | 24 | 0.750 | 1.000 | 0.750 | 1.000 | 0.250 | 0.425 |

## Final Answer By Model

| model | n | claim_accuracy | scope_accuracy | escape_rate | primary_recovery_rate | cost_usd | ece |
| --- | --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | 168 | 0.839 | 1.000 | 0.839 | 0.982 | 0.000 | 0.372 |

## Episode Type

| episode_type | n | claim_accuracy | scope_accuracy | escape_rate | contaminated_citation_rate | laundered_support_rate |
| --- | --- | --- | --- | --- | --- | --- |
| citation_laundering | 28 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| clean_control | 28 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| false_consensus | 56 | 0.518 | 1.000 | 0.518 | 0.482 | 0.482 |
| halupedia_trap | 14 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| mixed_source_corruption_v2 | 21 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| temporal_pollution | 21 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |

## False Consensus V2

| retriever | strategy | duplicate_count | primary_visibility_under_bm25_top8 | n | wrong_answer_rate | mean_wrong_confidence | mean_pollutant_saturation_at_k |
| --- | --- | --- | --- | --- | --- | --- | --- |
| bm25_top12 | evidence_graph_v2 | 1 | True | 2 | 0.000 | 0.000 | 0.167 |
| bm25_top12 | evidence_graph_v2 | 5 | True | 2 | 0.000 | 0.000 | 0.500 |
| bm25_top12 | evidence_graph_v2 | 20 | False | 1 | 1.000 | 0.860 | 0.750 |
| bm25_top12 | evidence_graph_v2 | 20 | True | 1 | 1.000 | 0.860 | 0.750 |
| bm25_top12 | evidence_graph_v2 | 50 | False | 1 | 1.000 | 0.860 | 1.000 |
| bm25_top12 | evidence_graph_v2 | 50 | True | 1 | 1.000 | 0.860 | 0.833 |
| bm25_top8 | evidence_graph_v2 | 1 | True | 2 | 0.000 | 0.000 | 0.250 |
| bm25_top8 | evidence_graph_v2 | 5 | True | 2 | 1.000 | 0.860 | 0.750 |
| bm25_top8 | evidence_graph_v2 | 20 | False | 1 | 1.000 | 0.860 | 1.000 |
| bm25_top8 | evidence_graph_v2 | 20 | True | 1 | 1.000 | 0.860 | 0.750 |
| bm25_top8 | evidence_graph_v2 | 50 | False | 1 | 1.000 | 0.860 | 1.000 |
| bm25_top8 | evidence_graph_v2 | 50 | True | 1 | 1.000 | 0.860 | 0.750 |
| bm25_top8 | forced_primary_append | 1 | True | 2 | 0.000 | 0.000 | 0.250 |
| bm25_top8 | forced_primary_append | 5 | True | 2 | 1.000 | 0.860 | 0.750 |
| bm25_top8 | forced_primary_append | 20 | False | 1 | 1.000 | 0.860 | 1.000 |
| bm25_top8 | forced_primary_append | 20 | True | 1 | 1.000 | 0.860 | 0.750 |
| bm25_top8 | forced_primary_append | 50 | False | 1 | 1.000 | 0.860 | 1.000 |
| bm25_top8 | forced_primary_append | 50 | True | 1 | 1.000 | 0.860 | 0.750 |
| bm25_top8 | tool_agent_2call | 1 | True | 2 | 0.000 | 0.000 | 0.250 |
| bm25_top8 | tool_agent_2call | 5 | True | 2 | 1.000 | 0.860 | 0.750 |
| bm25_top8 | tool_agent_2call | 20 | False | 1 | 1.000 | 0.860 | 1.000 |
| bm25_top8 | tool_agent_2call | 20 | True | 1 | 1.000 | 0.860 | 0.750 |
| bm25_top8 | tool_agent_2call | 50 | False | 1 | 1.000 | 0.860 | 1.000 |
| bm25_top8 | tool_agent_2call | 50 | True | 1 | 0.000 | 0.000 | 0.750 |
| heuristic_root_dedup_top8 | evidence_graph_v2 | 1 | True | 2 | 0.000 | 0.000 | 0.250 |
| heuristic_root_dedup_top8 | evidence_graph_v2 | 5 | True | 2 | 0.000 | 0.000 | 0.625 |
| heuristic_root_dedup_top8 | evidence_graph_v2 | 20 | False | 1 | 0.000 | 0.000 | 0.625 |
| heuristic_root_dedup_top8 | evidence_graph_v2 | 20 | True | 1 | 0.000 | 0.000 | 0.625 |
| heuristic_root_dedup_top8 | evidence_graph_v2 | 50 | False | 1 | 0.000 | 0.000 | 0.625 |
| heuristic_root_dedup_top8 | evidence_graph_v2 | 50 | True | 1 | 0.000 | 0.000 | 0.625 |
| oracle_root_dedup_top8 | evidence_graph_v2 | 1 | True | 2 | 0.000 | 0.000 | 0.125 |
| oracle_root_dedup_top8 | evidence_graph_v2 | 5 | True | 2 | 0.000 | 0.000 | 0.125 |
| oracle_root_dedup_top8 | evidence_graph_v2 | 20 | False | 1 | 0.000 | 0.000 | 0.125 |
| oracle_root_dedup_top8 | evidence_graph_v2 | 20 | True | 1 | 0.000 | 0.000 | 0.125 |
| oracle_root_dedup_top8 | evidence_graph_v2 | 50 | False | 1 | 0.000 | 0.000 | 0.125 |
| oracle_root_dedup_top8 | evidence_graph_v2 | 50 | True | 1 | 0.000 | 0.000 | 0.125 |
| primary_preserve_top8 | evidence_graph_v2 | 1 | True | 2 | 0.000 | 0.000 | 0.250 |
| primary_preserve_top8 | evidence_graph_v2 | 5 | True | 2 | 1.000 | 0.860 | 0.750 |
| primary_preserve_top8 | evidence_graph_v2 | 20 | False | 1 | 1.000 | 0.860 | 0.750 |
| primary_preserve_top8 | evidence_graph_v2 | 20 | True | 1 | 1.000 | 0.860 | 0.750 |
| primary_preserve_top8 | evidence_graph_v2 | 50 | False | 1 | 1.000 | 0.860 | 0.750 |
| primary_preserve_top8 | evidence_graph_v2 | 50 | True | 1 | 1.000 | 0.860 | 0.750 |

## Primary Visibility Stratification

| retriever | primary_visibility_under_bm25_top8 | n | claim_accuracy | escape_rate | mean_confidence |
| --- | --- | --- | --- | --- | --- |
| bm25_top12 | False | 2 | 0.000 | 0.000 | 0.860 |
| bm25_top12 | True | 6 | 0.667 | 0.667 | 0.773 |
| bm25_top8 | False | 6 | 0.000 | 0.000 | 0.860 |
| bm25_top8 | True | 18 | 0.389 | 0.389 | 0.809 |
| heuristic_root_dedup_top8 | False | 2 | 1.000 | 1.000 | 0.730 |
| heuristic_root_dedup_top8 | True | 6 | 1.000 | 1.000 | 0.730 |
| oracle_root_dedup_top8 | False | 2 | 1.000 | 1.000 | 0.730 |
| oracle_root_dedup_top8 | True | 6 | 1.000 | 1.000 | 0.730 |
| primary_preserve_top8 | False | 2 | 0.000 | 0.000 | 0.860 |
| primary_preserve_top8 | True | 6 | 0.333 | 0.333 | 0.817 |

## Oracle Vs Non-Oracle Note

`oracle_root_dedup_top8` is a diagnostic upper bound, not a deployable baseline; it uses scorer-only upstream roots.

## Tool-Agent Comparison

| strategy | n | claim_accuracy | escape_rate | tool_parse_success | primary_request_rate | useful_tool_rate |
| --- | --- | --- | --- | --- | --- | --- |
| forced_primary_append | 24 | 0.750 | 0.750 | 1.000 | 1.000 | 1.000 |
| tool_agent_2call | 24 | 0.792 | 0.792 | 1.000 | 0.083 | 1.000 |

## Mixed-Source Schema V2

| retriever | strategy | n | claim_accuracy | scope_accuracy | escape_rate |
| --- | --- | --- | --- | --- | --- |
| bm25_top12 | evidence_graph_v2 | 3 | 1.000 | 1.000 | 1.000 |
| bm25_top8 | evidence_graph_v2 | 3 | 1.000 | 1.000 | 1.000 |
| bm25_top8 | forced_primary_append | 3 | 1.000 | 1.000 | 1.000 |
| bm25_top8 | tool_agent_2call | 3 | 1.000 | 1.000 | 1.000 |
| heuristic_root_dedup_top8 | evidence_graph_v2 | 3 | 1.000 | 1.000 | 1.000 |
| oracle_root_dedup_top8 | evidence_graph_v2 | 3 | 1.000 | 1.000 | 1.000 |
| primary_preserve_top8 | evidence_graph_v2 | 3 | 1.000 | 1.000 | 1.000 |

## Cost

```json
{
  "aborted": false,
  "record_cost_usd": 0.0,
  "spent_usd": 0.0,
  "soft_cap_usd": 100.0,
  "hard_cap_usd": 250.0,
  "abort_cap_usd": 300.0
}
```
