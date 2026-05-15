# EHA Frontier Cohort Main Run

## By Model

| model | budget_setting | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | operational | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 380.000 | 0.000 |
| deepseek-v4-pro | operational | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 364.500 | 0.000 |
| gemini-3.1-pro-preview | operational | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 350.500 | 0.000 |
| gpt-5.4 | operational | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 374.500 | 0.000 |
| kimi-k2.6 | operational | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 310.000 | 0.000 |

## By Prompt

| model | budget_setting | prompt_condition | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | operational | epistemic_hygiene_instruction | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 362.000 | 0.000 |
| claude-opus-4-7 | operational | standard_answer | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 398.000 | 0.000 |
| deepseek-v4-pro | operational | epistemic_hygiene_instruction | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 351.000 | 0.000 |
| deepseek-v4-pro | operational | standard_answer | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 378.000 | 0.000 |
| gemini-3.1-pro-preview | operational | epistemic_hygiene_instruction | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 349.000 | 0.000 |
| gemini-3.1-pro-preview | operational | standard_answer | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 352.000 | 0.000 |
| gpt-5.4 | operational | epistemic_hygiene_instruction | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 393.000 | 0.000 |
| gpt-5.4 | operational | standard_answer | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 356.000 | 0.000 |
| kimi-k2.6 | operational | epistemic_hygiene_instruction | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 340.000 | 0.000 |
| kimi-k2.6 | operational | standard_answer | 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 280.000 | 0.000 |

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.036219,
  "spent_usd": 0.036219,
  "soft_cap_usd": 250.0,
  "hard_cap_usd": 80.0,
  "abort_cap_usd": 120.0
}
```
