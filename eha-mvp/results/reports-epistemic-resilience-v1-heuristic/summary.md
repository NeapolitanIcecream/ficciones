# Epistemic Resilience Table v1

## Main Table

| model | prompt | n | packet_judgment | evidence_selection | active_verification | avg_epistemic_escape |
| --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | epistemic_hygiene_instruction | 100 | 1.000 | 0.800 | 0.200 | 0.667 |
| heuristic-sim | standard_answer | 100 | 1.000 | 0.800 | 0.200 | 0.667 |

## By Family

| model | prompt_condition | family | n | epistemic_escape | belief_correctness | evidence_cleanliness | uncertainty_discipline | evidence_value_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | epistemic_hygiene_instruction | active_verification | 20 | 0.200 | 0.800 | 1.000 | 0.800 | 0.000 |
| heuristic-sim | epistemic_hygiene_instruction | evidence_selection | 40 | 0.800 | 0.200 | 1.000 | 0.200 | 0.679 |
| heuristic-sim | epistemic_hygiene_instruction | packet_judgment | 40 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | standard_answer | active_verification | 20 | 0.200 | 0.800 | 0.800 | 1.000 | 0.000 |
| heuristic-sim | standard_answer | evidence_selection | 40 | 0.800 | 0.200 | 1.000 | 0.200 | 0.679 |
| heuristic-sim | standard_answer | packet_judgment | 40 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

## By Condition

| model | prompt_condition | condition | n | epistemic_escape | primary_seeking_rate | duplicate_avoidance_rate | generated_lore_avoidance_rate | contradiction_seeking_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | epistemic_hygiene_instruction | buried_primary | 20 | 0.800 | 0.400 | 1.000 | 1.000 | 0.400 |
| heuristic-sim | epistemic_hygiene_instruction | clean | 20 | 0.800 | 0.400 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | epistemic_hygiene_instruction | conflicting_evidence | 20 | 0.800 | 0.400 | 1.000 | 1.000 | 0.400 |
| heuristic-sim | epistemic_hygiene_instruction | false_consensus | 20 | 0.800 | 0.400 | 1.000 | 1.000 | 0.400 |
| heuristic-sim | epistemic_hygiene_instruction | generated_lore | 20 | 0.600 | 0.000 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | standard_answer | buried_primary | 20 | 0.800 | 0.400 | 1.000 | 1.000 | 0.400 |
| heuristic-sim | standard_answer | clean | 20 | 0.800 | 0.400 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | standard_answer | conflicting_evidence | 20 | 0.800 | 0.400 | 1.000 | 1.000 | 0.400 |
| heuristic-sim | standard_answer | false_consensus | 20 | 0.800 | 0.400 | 1.000 | 1.000 | 0.400 |
| heuristic-sim | standard_answer | generated_lore | 20 | 0.600 | 0.000 | 1.000 | 1.000 | 0.000 |

## Cost Report

```json
{
  "aborted": false,
  "spent_usd": 0.0,
  "record_cost_usd": 0.0,
  "source_reports": [
    {
      "aborted": false,
      "record_cost_usd": 0.0,
      "spent_usd": 0.0,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    }
  ]
}
```
