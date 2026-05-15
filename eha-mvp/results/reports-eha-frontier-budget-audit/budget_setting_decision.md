# Token-Budget Fairness Audit Decision

Gate: `parse_success >= 0.95`, `empty_output_rate = 0`, `schema_missing_rate <= 0.05`.

## Decision

| model | selected_budget_setting | reason | no_cap_gate_pass | cap_8192_gate_pass | cap_4096_parse_success | cap_4096_empty_output_rate |
| --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-pro | no_cap | 8192 cap failed or was unavailable; no-cap passed gate, so keep provider-compatible operational setting. | True | False | 1.000 | 0.000 |
| kimi-k2.6 | no_cap | 8192 cap failed or was unavailable; no-cap passed gate, so keep provider-compatible operational setting. | True | False | 0.400 | 0.400 |

## Sensitivity Table

| model | budget_setting | n | parse_success | empty_output_rate | schema_missing_rate | visible_output_tokens_mean | visible_output_tokens_median | visible_output_tokens_p95 | overlength_rate | operational_epistemic_escape | conditional_epistemic_escape | evidence_cleanliness | verification_action_score | gate_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-pro | cap_4096_diagnostic | 20 | 1.000 | 0.000 | 0.000 | 392.750 | 409.000 | 464.000 | 0.000 | 0.900 | 0.900 | 1.000 | 0.583 | True |
| deepseek-v4-pro | cap_8192 | 20 | 0.850 | 0.150 | 0.000 | 328.050 | 383.000 | 460.000 | 0.000 | 0.700 | 0.824 | 1.000 | 0.417 | False |
| deepseek-v4-pro | no_cap | 20 | 1.000 | 0.000 | 0.000 | 413.800 | 412.000 | 496.000 | 0.000 | 0.900 | 0.900 | 1.000 | 0.500 | True |
| kimi-k2.6 | cap_4096_diagnostic | 20 | 0.400 | 0.400 | 0.100 | 194.650 | 300.000 | 415.000 | 0.000 | 0.250 | 0.625 | 1.000 | 0.250 | False |
| kimi-k2.6 | cap_8192 | 20 | 0.950 | 0.050 | 0.000 | 364.300 | 388.000 | 464.000 | 0.000 | 0.750 | 0.789 | 1.000 | 0.333 | False |
| kimi-k2.6 | no_cap | 20 | 1.000 | 0.000 | 0.000 | 384.550 | 403.000 | 488.000 | 0.000 | 0.800 | 0.800 | 1.000 | 0.417 | True |
