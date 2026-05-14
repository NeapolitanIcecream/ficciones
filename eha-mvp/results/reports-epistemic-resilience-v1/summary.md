# Epistemic Resilience Table v1

## Main Table

| model | prompt | n | packet_judgment | evidence_selection | active_verification | avg_epistemic_escape |
| --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | 100 | 0.925 | 0.800 | 0.500 | 0.742 |
| openai/gpt-4o-mini | standard_answer | 100 | 0.925 | 0.800 | 0.650 | 0.792 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | 100 | 0.475 | 0.325 | 0.200 | 0.333 |
| openai/gpt-5-mini | standard_answer | 100 | 0.650 | 0.375 | 0.100 | 0.375 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | 100 | 0.625 | 0.700 | 0.200 | 0.508 |
| openai/gpt-5.4-mini | standard_answer | 100 | 0.400 | 0.775 | 0.100 | 0.425 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | 12 | 1.000 | 0.750 | 0.750 | 0.833 |
| openai/gpt-5.5 | standard_answer | 12 | 0.750 | 0.750 | 0.750 | 0.750 |

## By Family

| model | prompt_condition | family | n | epistemic_escape | belief_correctness | evidence_cleanliness | uncertainty_discipline | evidence_value_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | active_verification | 20 | 0.500 | 0.750 | 0.950 | 0.750 | 0.245 |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | evidence_selection | 40 | 0.800 | 0.875 | 0.950 | 0.875 | 0.450 |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | packet_judgment | 40 | 0.925 | 0.950 | 0.975 | 0.950 | 0.473 |
| openai/gpt-4o-mini | standard_answer | active_verification | 20 | 0.650 | 0.800 | 0.900 | 0.900 | 0.242 |
| openai/gpt-4o-mini | standard_answer | evidence_selection | 40 | 0.800 | 1.000 | 0.975 | 1.000 | 0.421 |
| openai/gpt-4o-mini | standard_answer | packet_judgment | 40 | 0.925 | 1.000 | 0.925 | 1.000 | 0.409 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | active_verification | 20 | 0.200 | 0.450 | 1.000 | 0.450 | 0.117 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | evidence_selection | 40 | 0.325 | 0.525 | 0.975 | 0.525 | 0.179 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | packet_judgment | 40 | 0.475 | 0.475 | 1.000 | 0.475 | 0.146 |
| openai/gpt-5-mini | standard_answer | active_verification | 20 | 0.100 | 0.450 | 0.900 | 0.450 | 0.058 |
| openai/gpt-5-mini | standard_answer | evidence_selection | 40 | 0.375 | 0.575 | 0.925 | 0.575 | 0.196 |
| openai/gpt-5-mini | standard_answer | packet_judgment | 40 | 0.650 | 0.675 | 0.975 | 0.675 | 0.254 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | active_verification | 20 | 0.200 | 0.800 | 0.600 | 0.800 | 0.125 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | evidence_selection | 40 | 0.700 | 1.000 | 0.400 | 1.000 | 0.350 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | packet_judgment | 40 | 0.625 | 1.000 | 0.625 | 1.000 | 0.379 |
| openai/gpt-5.4-mini | standard_answer | active_verification | 20 | 0.100 | 0.800 | 0.500 | 0.800 | 0.200 |
| openai/gpt-5.4-mini | standard_answer | evidence_selection | 40 | 0.775 | 1.000 | 0.375 | 1.000 | 0.388 |
| openai/gpt-5.4-mini | standard_answer | packet_judgment | 40 | 0.400 | 1.000 | 0.400 | 1.000 | 0.388 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | active_verification | 4 | 0.750 | 0.750 | 1.000 | 0.750 | 0.250 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | evidence_selection | 4 | 0.750 | 1.000 | 1.000 | 1.000 | 0.375 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | packet_judgment | 4 | 1.000 | 1.000 | 1.000 | 1.000 | 0.542 |
| openai/gpt-5.5 | standard_answer | active_verification | 4 | 0.750 | 0.750 | 1.000 | 0.750 | 0.250 |
| openai/gpt-5.5 | standard_answer | evidence_selection | 4 | 0.750 | 1.000 | 0.750 | 1.000 | 0.375 |
| openai/gpt-5.5 | standard_answer | packet_judgment | 4 | 0.750 | 1.000 | 0.750 | 1.000 | 0.500 |

## By Condition

| model | prompt_condition | condition | n | epistemic_escape | primary_seeking_rate | duplicate_avoidance_rate | generated_lore_avoidance_rate | contradiction_seeking_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | buried_primary | 20 | 0.800 | 0.800 | 0.800 | 1.000 | 0.800 |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | clean | 20 | 0.800 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | conflicting_evidence | 20 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | false_consensus | 20 | 0.950 | 1.000 | 0.800 | 1.000 | 1.000 |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | generated_lore | 20 | 0.400 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-4o-mini | standard_answer | buried_primary | 20 | 0.750 | 0.800 | 0.750 | 1.000 | 0.800 |
| openai/gpt-4o-mini | standard_answer | clean | 20 | 0.950 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-4o-mini | standard_answer | conflicting_evidence | 20 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | standard_answer | false_consensus | 20 | 1.000 | 1.000 | 0.800 | 1.000 | 1.000 |
| openai/gpt-4o-mini | standard_answer | generated_lore | 20 | 0.400 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | buried_primary | 20 | 0.350 | 0.350 | 1.000 | 1.000 | 0.350 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | clean | 20 | 0.400 | 0.400 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | conflicting_evidence | 20 | 0.300 | 0.400 | 1.000 | 1.000 | 0.400 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | false_consensus | 20 | 0.300 | 0.300 | 0.950 | 1.000 | 0.300 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | generated_lore | 20 | 0.450 | 0.000 | 0.750 | 0.750 | 0.000 |
| openai/gpt-5-mini | standard_answer | buried_primary | 20 | 0.400 | 0.400 | 1.000 | 1.000 | 0.400 |
| openai/gpt-5-mini | standard_answer | clean | 20 | 0.450 | 0.450 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | standard_answer | conflicting_evidence | 20 | 0.500 | 0.550 | 1.000 | 1.000 | 0.550 |
| openai/gpt-5-mini | standard_answer | false_consensus | 20 | 0.450 | 0.550 | 0.850 | 1.000 | 0.550 |
| openai/gpt-5-mini | standard_answer | generated_lore | 20 | 0.350 | 0.000 | 0.850 | 0.850 | 0.000 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | buried_primary | 20 | 0.550 | 0.800 | 0.700 | 1.000 | 0.800 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | clean | 20 | 0.700 | 1.000 | 0.850 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | conflicting_evidence | 20 | 0.700 | 1.000 | 0.850 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | false_consensus | 20 | 0.600 | 1.000 | 0.800 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | generated_lore | 20 | 0.300 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5.4-mini | standard_answer | buried_primary | 20 | 0.450 | 0.800 | 0.750 | 1.000 | 0.800 |
| openai/gpt-5.4-mini | standard_answer | clean | 20 | 0.850 | 1.000 | 0.950 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | standard_answer | conflicting_evidence | 20 | 0.550 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | standard_answer | false_consensus | 20 | 0.450 | 1.000 | 0.800 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | standard_answer | generated_lore | 20 | 0.150 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | buried_primary | 2 | 0.500 | 0.500 | 0.500 | 1.000 | 0.500 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | clean | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | conflicting_evidence | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | false_consensus | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | generated_lore | 2 | 0.500 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5.5 | standard_answer | buried_primary | 2 | 0.500 | 0.500 | 0.500 | 1.000 | 0.500 |
| openai/gpt-5.5 | standard_answer | clean | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | standard_answer | conflicting_evidence | 3 | 0.667 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.5 | standard_answer | false_consensus | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.5 | standard_answer | generated_lore | 2 | 0.500 | 0.000 | 0.000 | 0.000 | 0.000 |

## Cost Report

```json
{
  "aborted": false,
  "spent_usd": 2.800352,
  "record_cost_usd": 2.130942,
  "source_reports": [
    {
      "aborted": false,
      "record_cost_usd": 2.130942,
      "spent_usd": 2.800352,
      "superseded_record_cost_usd": 0.66941,
      "source_reports": [
        {
          "aborted": false,
          "record_cost_usd": 2.134102,
          "spent_usd": 2.134102,
          "soft_cap_usd": 75.0,
          "hard_cap_usd": 200.0,
          "abort_cap_usd": 300.0
        },
        {
          "aborted": false,
          "record_cost_usd": 0.66625,
          "spent_usd": 0.66625,
          "soft_cap_usd": 75.0,
          "hard_cap_usd": 200.0,
          "abort_cap_usd": 300.0
        }
      ]
    }
  ]
}
```
