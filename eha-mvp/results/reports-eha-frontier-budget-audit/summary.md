# EHA Frontier Cohort Main Run

## By Model

| model | budget_setting | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-pro | cap_4096_diagnostic | 20 | 0.900 | 0.900 | 1.000 | 0.950 | 1.000 | 0.950 | 0.583 | 392.750 | 0.000 |
| deepseek-v4-pro | cap_8192 | 20 | 0.700 | 0.824 | 0.850 | 0.800 | 1.000 | 0.800 | 0.417 | 328.050 | 0.000 |
| deepseek-v4-pro | no_cap | 20 | 0.900 | 0.900 | 1.000 | 0.950 | 1.000 | 0.950 | 0.500 | 413.800 | 0.000 |
| kimi-k2.6 | cap_4096_diagnostic | 20 | 0.250 | 0.625 | 0.400 | 0.400 | 1.000 | 0.400 | 0.250 | 194.650 | 0.000 |
| kimi-k2.6 | cap_8192 | 20 | 0.750 | 0.789 | 0.950 | 0.900 | 1.000 | 0.900 | 0.333 | 364.300 | 0.000 |
| kimi-k2.6 | no_cap | 20 | 0.800 | 0.800 | 1.000 | 0.950 | 1.000 | 0.950 | 0.417 | 384.550 | 0.000 |

## By Prompt

| model | budget_setting | prompt_condition | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-pro | cap_4096_diagnostic | epistemic_hygiene_instruction | 20 | 0.900 | 0.900 | 1.000 | 0.950 | 1.000 | 0.950 | 0.583 | 392.750 | 0.000 |
| deepseek-v4-pro | cap_8192 | epistemic_hygiene_instruction | 20 | 0.700 | 0.824 | 0.850 | 0.800 | 1.000 | 0.800 | 0.417 | 328.050 | 0.000 |
| deepseek-v4-pro | no_cap | epistemic_hygiene_instruction | 20 | 0.900 | 0.900 | 1.000 | 0.950 | 1.000 | 0.950 | 0.500 | 413.800 | 0.000 |
| kimi-k2.6 | cap_4096_diagnostic | epistemic_hygiene_instruction | 20 | 0.250 | 0.625 | 0.400 | 0.400 | 1.000 | 0.400 | 0.250 | 194.650 | 0.000 |
| kimi-k2.6 | cap_8192 | epistemic_hygiene_instruction | 20 | 0.750 | 0.789 | 0.950 | 0.900 | 1.000 | 0.900 | 0.333 | 364.300 | 0.000 |
| kimi-k2.6 | no_cap | epistemic_hygiene_instruction | 20 | 0.800 | 0.800 | 1.000 | 0.950 | 1.000 | 0.950 | 0.417 | 384.550 | 0.000 |

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.801404,
  "spent_usd": 0.801404,
  "soft_cap_usd": 120.0,
  "hard_cap_usd": 400.0,
  "abort_cap_usd": 600.0
}
```
