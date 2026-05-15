# EHA Frontier Main Run Plan

- Tasks: `100`
- Models: `5`
- Prompt conditions: `standard_answer, epistemic_hygiene_instruction`
- Total calls: `1000`
- Parallel model streams: `5`
- Per-model concurrency: `1`
- Max attempts per call: `2`
- Model-visible document IDs: `opaque_per_task`

## Models

| provider | model | budget_setting | temperature | max_output_tokens | response_format | timeout_s |
| --- | --- | --- | --- | --- | --- | --- |
| OpenAI | gpt-5.4 | operational | None | 4096 | json_schema | 180.000 |
| Anthropic | claude-opus-4-7 | operational | None | 4096 | json_schema | 180.000 |
| Google | gemini-3.1-pro-preview | operational | None | 4096 | json_schema | 180.000 |
| DeepSeek | deepseek-v4-pro | operational | None | None | json_object | 240.000 |
| Kimi | kimi-k2.6 | operational | None | None | json_schema | 300.000 |

## Outputs

- `summary.md`
- `frontier_main_metrics_by_model.csv`
- `frontier_main_metrics_by_family.csv`
- `frontier_main_metrics_by_condition.csv`
- `frontier_main_metrics_by_prompt.csv`
- `operational_vs_conditional_escape.csv`
- `failure_cases_frontier.jsonl`
- `cost_report.json`
