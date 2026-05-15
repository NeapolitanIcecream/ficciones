# EHA Frontier Main Run Plan

- Tasks: `20`
- Models: `6`
- Prompt conditions: `epistemic_hygiene_instruction`
- Total calls: `120`
- Parallel model streams: `2`
- Per-model concurrency: `1`
- Max attempts per call: `1`

## Models

| provider | model | budget_setting | temperature | max_output_tokens | response_format | timeout_s |
| --- | --- | --- | --- | --- | --- | --- |
| DeepSeek | deepseek-v4-pro | no_cap | None | None | json_object | 240.000 |
| DeepSeek | deepseek-v4-pro | cap_8192 | None | 8192 | json_object | 240.000 |
| DeepSeek | deepseek-v4-pro | cap_4096_diagnostic | None | 4096 | json_object | 240.000 |
| Kimi | kimi-k2.6 | no_cap | None | None | json_schema | 300.000 |
| Kimi | kimi-k2.6 | cap_8192 | None | 8192 | json_schema | 300.000 |
| Kimi | kimi-k2.6 | cap_4096_diagnostic | None | 4096 | json_schema | 300.000 |

## Outputs

- `summary.md`
- `frontier_main_metrics_by_model.csv`
- `frontier_main_metrics_by_family.csv`
- `frontier_main_metrics_by_condition.csv`
- `frontier_main_metrics_by_prompt.csv`
- `operational_vs_conditional_escape.csv`
- `failure_cases_frontier.jsonl`
- `cost_report.json`
