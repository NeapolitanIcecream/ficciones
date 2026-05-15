# EHA Frontier Cohort Main Run

## By Model

| model | budget_setting | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-5.4 | operational | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 311.000 | 0.000 |

## By Prompt

| model | budget_setting | prompt_condition | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-5.4 | operational | epistemic_hygiene_instruction | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 349.000 | 0.000 |
| gpt-5.4 | operational | standard_answer | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 273.000 | 0.000 |

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.002018,
  "spent_usd": 0.002018,
  "soft_cap_usd": 10.0,
  "hard_cap_usd": 20.0,
  "abort_cap_usd": 30.0
}
```
