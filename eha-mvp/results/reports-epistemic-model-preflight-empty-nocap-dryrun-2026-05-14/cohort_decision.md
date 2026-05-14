# EHA Frontier Cohort Structured-Output Preflight

## Selection Rule

Use the newest routable flagship model per mainstream provider. A model can enter the main table only if it passes the 20-task structured-output preflight.

Gate: `parse_success >= 0.95`, `empty_output = 0`, and `schema_missing_rate <= 0.05`. LLM-based repair is not used in this gate.

## Invocation Profile

```json
{
  "temperature_policy": "omitted",
  "max_completion_tokens_policy": "omitted",
  "response_format": "json_schema",
  "json_extractor": "first_json_object",
  "message_role_policy": "developer_system_merged_into_user",
  "llm_repair": "disabled"
}
```

## Sample

```json
{
  "task_count": 1,
  "family_counts": {
    "packet_judgment": 1
  },
  "condition_counts": {
    "clean": 1
  },
  "prompt_condition": "epistemic_hygiene_instruction"
}
```

## Cohort Decision

| provider | selected_model | primary_candidate | fallback_model | status | note |
| --- | --- | --- | --- | --- | --- |
| Anthropic |  | claude-opus-4-7 |  | blocked | Primary candidate did not pass structured-output preflight. |
| DeepSeek | deepseek-v4-pro | deepseek-v4-pro |  | selected | Latest routable flagship passed structured-output preflight. |
| Google |  | gemini-3.1-pro-preview | gemini-2.5-pro | blocked | Neither Google primary nor fallback passed structured-output preflight. |
| Kimi | kimi-k2.6 | kimi-k2.6 |  | selected | Latest routable flagship passed structured-output preflight. |
| OpenAI |  | gpt-5.4 |  | blocked | Primary candidate did not pass structured-output preflight. |

## Preflight Summary

| model | n | parse_success_rate | empty_output_count | schema_missing_rate | structured_preflight_pass | temperature_policy | max_completion_tokens_policy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-pro | 1 | 1.000 | 0 | 0.000 | True | omitted | omitted |
| kimi-k2.6 | 1 | 1.000 | 0 | 0.000 | True | omitted | omitted |

## Reporting Implication

Main EHA reports should include both `operational_epistemic_escape` and `conditional_epistemic_escape`; parse failures count as failures in the operational metric.
