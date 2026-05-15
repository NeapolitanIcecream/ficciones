# EHA Frontier Cohort Main Run

## By Model

| model | budget_setting | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | operational | 200 | 0.880 | 0.880 | 1.000 | 0.960 | 1.000 | 0.960 | 0.600 | 419.090 | 0.000 |
| deepseek-v4-pro | operational | 200 | 0.790 | 0.794 | 0.995 | 0.950 | 0.935 | 0.950 | 0.475 | 399.825 | 0.000 |
| gemini-3.1-pro-preview | operational | 200 | 0.780 | 0.780 | 1.000 | 0.960 | 1.000 | 0.960 | 0.458 | 455.330 | 0.000 |
| gpt-5.4 | operational | 200 | 0.770 | 0.770 | 1.000 | 0.960 | 0.730 | 0.960 | 0.408 | 372.880 | 0.000 |
| kimi-k2.6 | operational | 200 | 0.790 | 0.790 | 1.000 | 0.960 | 0.950 | 0.960 | 0.450 | 404.205 | 0.000 |

## By Prompt

| model | budget_setting | prompt_condition | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | operational | epistemic_hygiene_instruction | 100 | 0.880 | 0.880 | 1.000 | 0.960 | 1.000 | 0.960 | 0.600 | 418.980 | 0.000 |
| claude-opus-4-7 | operational | standard_answer | 100 | 0.880 | 0.880 | 1.000 | 0.960 | 1.000 | 0.960 | 0.600 | 419.200 | 0.000 |
| deepseek-v4-pro | operational | epistemic_hygiene_instruction | 100 | 0.800 | 0.808 | 0.990 | 0.950 | 1.000 | 0.950 | 0.500 | 395.650 | 0.000 |
| deepseek-v4-pro | operational | standard_answer | 100 | 0.780 | 0.780 | 1.000 | 0.950 | 0.870 | 0.950 | 0.450 | 404.000 | 0.000 |
| gemini-3.1-pro-preview | operational | epistemic_hygiene_instruction | 100 | 0.780 | 0.780 | 1.000 | 0.960 | 1.000 | 0.960 | 0.500 | 460.530 | 0.000 |
| gemini-3.1-pro-preview | operational | standard_answer | 100 | 0.780 | 0.780 | 1.000 | 0.960 | 1.000 | 0.960 | 0.417 | 450.130 | 0.000 |
| gpt-5.4 | operational | epistemic_hygiene_instruction | 100 | 0.790 | 0.790 | 1.000 | 0.960 | 0.760 | 0.960 | 0.417 | 382.500 | 0.000 |
| gpt-5.4 | operational | standard_answer | 100 | 0.750 | 0.750 | 1.000 | 0.960 | 0.700 | 0.960 | 0.400 | 363.260 | 0.000 |
| kimi-k2.6 | operational | epistemic_hygiene_instruction | 100 | 0.770 | 0.770 | 1.000 | 0.960 | 0.970 | 0.960 | 0.467 | 392.870 | 0.000 |
| kimi-k2.6 | operational | standard_answer | 100 | 0.810 | 0.810 | 1.000 | 0.960 | 0.930 | 0.960 | 0.433 | 415.540 | 0.000 |

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 4.034251,
  "spent_usd": 4.037707,
  "soft_cap_usd": 250.0,
  "hard_cap_usd": 800.0,
  "abort_cap_usd": 1000.0
}
```
