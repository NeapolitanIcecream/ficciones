# EHA Frontier Cohort Main Run

## By Model

| model | budget_setting | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | operational | 200 | 0.830 | 0.830 | 1.000 | 0.960 | 0.945 | 0.960 | 0.567 | 421.010 | 0.000 |
| deepseek-v4-pro | operational | 200 | 0.775 | 0.775 | 1.000 | 0.960 | 0.905 | 0.960 | 0.483 | 370.340 | 0.000 |
| gemini-3.1-pro-preview | operational | 200 | 0.800 | 0.800 | 1.000 | 0.960 | 1.000 | 0.960 | 0.458 | 430.740 | 0.000 |
| gpt-5.4 | operational | 200 | 0.745 | 0.745 | 1.000 | 0.960 | 0.705 | 0.960 | 0.425 | 346.130 | 0.000 |
| kimi-k2.6 | operational | 200 | 0.710 | 0.710 | 1.000 | 0.960 | 0.940 | 0.960 | 0.450 | 377.885 | 0.000 |

## By Prompt

| model | budget_setting | prompt_condition | n | operational_epistemic_escape | conditional_epistemic_escape | parse_success | belief_correctness | evidence_cleanliness | uncertainty_discipline | verification_action_score | visible_output_tokens | overlength_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | operational | epistemic_hygiene_instruction | 100 | 0.870 | 0.870 | 1.000 | 0.960 | 1.000 | 0.960 | 0.583 | 420.690 | 0.000 |
| claude-opus-4-7 | operational | standard_answer | 100 | 0.790 | 0.790 | 1.000 | 0.960 | 0.890 | 0.960 | 0.550 | 421.330 | 0.000 |
| deepseek-v4-pro | operational | epistemic_hygiene_instruction | 100 | 0.820 | 0.820 | 1.000 | 0.960 | 0.990 | 0.960 | 0.517 | 365.040 | 0.000 |
| deepseek-v4-pro | operational | standard_answer | 100 | 0.730 | 0.730 | 1.000 | 0.960 | 0.820 | 0.960 | 0.450 | 375.640 | 0.000 |
| gemini-3.1-pro-preview | operational | epistemic_hygiene_instruction | 100 | 0.790 | 0.790 | 1.000 | 0.960 | 1.000 | 0.960 | 0.467 | 433.830 | 0.000 |
| gemini-3.1-pro-preview | operational | standard_answer | 100 | 0.810 | 0.810 | 1.000 | 0.960 | 1.000 | 0.960 | 0.450 | 427.650 | 0.000 |
| gpt-5.4 | operational | epistemic_hygiene_instruction | 100 | 0.750 | 0.750 | 1.000 | 0.960 | 0.720 | 0.960 | 0.400 | 354.580 | 0.000 |
| gpt-5.4 | operational | standard_answer | 100 | 0.740 | 0.740 | 1.000 | 0.960 | 0.690 | 0.960 | 0.450 | 337.680 | 0.000 |
| kimi-k2.6 | operational | epistemic_hygiene_instruction | 100 | 0.630 | 0.630 | 1.000 | 0.960 | 0.950 | 0.960 | 0.467 | 374.690 | 0.000 |
| kimi-k2.6 | operational | standard_answer | 100 | 0.790 | 0.790 | 1.000 | 0.960 | 0.930 | 0.960 | 0.433 | 381.080 | 0.000 |

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 4.031855,
  "spent_usd": 4.031855,
  "soft_cap_usd": 250.0,
  "hard_cap_usd": 800.0,
  "abort_cap_usd": 1000.0
}
```
