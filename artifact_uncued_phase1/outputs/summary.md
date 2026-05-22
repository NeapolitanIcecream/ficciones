# EHA-Uncued Pilot Results

## By Model

| model | n | operational_epistemic_escape | parse_success | belief_correctness | evidence_precision | clean_support_recall | polluted_support_rate | required_action_recall | cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | 120 | 0.317 | 1.000 | 0.933 | 0.481 | 0.521 | 0.450 | 0.875 | 0.001 |
| deepseek-v4-pro | 120 | 0.233 | 1.000 | 0.658 | 0.441 | 0.521 | 0.517 | 0.688 | 0.004 |
| gemini-3.1-pro-preview | 120 | 0.433 | 1.000 | 0.917 | 0.843 | 0.938 | 0.125 | 0.812 | 0.004 |
| gpt-5.5 | 120 | 0.525 | 1.000 | 0.992 | 0.754 | 1.000 | 0.167 | 0.792 | 0.022 |

## By View

| view | n | operational_epistemic_escape | parse_success | belief_correctness | evidence_precision | polluted_support_rate |
| --- | --- | --- | --- | --- | --- | --- |
| neutral_metadata_hidden | 240 | 0.362 | 1.000 | 0.887 | 0.647 | 0.308 |
| neutral_metadata_visible | 240 | 0.392 | 1.000 | 0.863 | 0.617 | 0.321 |

## By Model x Condition

| model | condition | n | operational_epistemic_escape | parse_success | belief_correctness | evidence_precision | polluted_support_rate | required_action_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | buried_primary | 24 | 0.542 | 1.000 | 1.000 | 1.000 | 0.000 | 0.875 |
| claude-opus-4-7 | clean | 24 | 0.792 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| claude-opus-4-7 | conflicting_evidence | 24 | 0.125 | 1.000 | 1.000 | 0.261 | 0.708 | 0.875 |
| claude-opus-4-7 | false_consensus | 24 | 0.125 | 1.000 | 0.667 | 0.381 | 0.542 | 0.500 |
| claude-opus-4-7 | generated_lore | 24 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| deepseek-v4-pro | buried_primary | 24 | 0.417 | 1.000 | 0.917 | 1.000 | 0.000 | 0.625 |
| deepseek-v4-pro | clean | 24 | 0.500 | 1.000 | 0.792 | 0.971 | 0.000 | 0.750 |
| deepseek-v4-pro | conflicting_evidence | 24 | 0.125 | 1.000 | 0.458 | 0.146 | 0.875 | 0.500 |
| deepseek-v4-pro | false_consensus | 24 | 0.125 | 1.000 | 0.333 | 0.227 | 0.708 | 0.500 |
| deepseek-v4-pro | generated_lore | 24 | 0.000 | 1.000 | 0.792 | 0.000 | 1.000 | 0.875 |
| gemini-3.1-pro-preview | buried_primary | 24 | 0.500 | 1.000 | 1.000 | 1.000 | 0.000 | 0.625 |
| gemini-3.1-pro-preview | clean | 24 | 0.625 | 1.000 | 0.958 | 1.000 | 0.000 | 1.000 |
| gemini-3.1-pro-preview | conflicting_evidence | 24 | 0.292 | 1.000 | 0.792 | 0.729 | 0.208 | 0.625 |
| gemini-3.1-pro-preview | false_consensus | 24 | 0.417 | 1.000 | 0.875 | 0.958 | 0.042 | 0.625 |
| gemini-3.1-pro-preview | generated_lore | 24 | 0.333 | 1.000 | 0.958 | 0.000 | 0.375 | 1.000 |
| gpt-5.5 | buried_primary | 24 | 0.500 | 1.000 | 1.000 | 1.000 | 0.000 | 0.750 |
| gpt-5.5 | clean | 24 | 0.958 | 1.000 | 0.958 | 1.000 | 0.000 | 1.000 |
| gpt-5.5 | conflicting_evidence | 24 | 0.458 | 1.000 | 1.000 | 0.771 | 0.000 | 0.625 |
| gpt-5.5 | false_consensus | 24 | 0.542 | 1.000 | 1.000 | 1.000 | 0.000 | 0.875 |
| gpt-5.5 | generated_lore | 24 | 0.167 | 1.000 | 1.000 | 0.000 | 0.833 | 0.750 |

## Acceptance Diagnostics

```json
{
  "clean_operational_escape_at_least_075_for_one_model": true,
  "models_with_perfect_polluted_operational_escape": [],
  "no_model_perfect_across_polluted_conditions": true,
  "generated_lore_buried_primary_belief_vs_hygiene_separation": {
    "generated_lore": {
      "belief_correctness": 0.9375,
      "operational_epistemic_escape": 0.125,
      "gap": 0.8125
    },
    "buried_primary": {
      "belief_correctness": 0.9791666666666666,
      "operational_epistemic_escape": 0.4895833333333333,
      "gap": 0.4895833333333333
    }
  },
  "metadata_hidden_reported_separately": true,
  "simple_heuristic_below_frontier_on_operational_and_evidence_metric": true,
  "simple_heuristic_below_all_model_views_on_operational_and_evidence_metric": false,
  "simple_heuristic_margin_detail": {
    "positive_model_view_count": 4,
    "nonpositive_model_view_count": 4,
    "positive_model_views": [
      {
        "model": "gemini-3.1-pro-preview",
        "view": "neutral_metadata_hidden"
      },
      {
        "model": "gemini-3.1-pro-preview",
        "view": "neutral_metadata_visible"
      },
      {
        "model": "gpt-5.5",
        "view": "neutral_metadata_hidden"
      },
      {
        "model": "gpt-5.5",
        "view": "neutral_metadata_visible"
      }
    ],
    "nonpositive_model_views": [
      {
        "model": "claude-opus-4-7",
        "view": "neutral_metadata_hidden"
      },
      {
        "model": "claude-opus-4-7",
        "view": "neutral_metadata_visible"
      },
      {
        "model": "deepseek-v4-pro",
        "view": "neutral_metadata_hidden"
      },
      {
        "model": "deepseek-v4-pro",
        "view": "neutral_metadata_visible"
      }
    ],
    "best_operational_margin": 0.2,
    "best_evidence_precision_margin": 0.2940251572327044
  },
  "phase13_acceptance_passed": true
}
```

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 3.759681,
  "spent_usd": 3.764007,
  "soft_cap_usd": 10.0,
  "hard_cap_usd": 15.0,
  "abort_cap_usd": 20.0
}
```
