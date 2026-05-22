# EHA Frontier Cohort Structured-Output Preflight

## Selection Rule

Use the newest routable flagship model per mainstream provider. A model can enter the main table only if it passes the 20-task structured-output preflight.

Gate: `parse_success >= 0.95`, `empty_output = 0`, and `schema_missing_rate <= 0.05`. LLM-based repair is not used in this gate.

## Invocation Profile

```json
{
  "temperature_policy": "omitted",
  "max_completion_tokens_policy": "explicit:4096",
  "response_format": "json_object",
  "json_extractor": "first_json_object",
  "message_role_policy": "developer_system_merged_into_user",
  "llm_repair": "disabled"
}
```

## Sample

```json
{
  "task_count": 20,
  "family_counts": {
    "packet_judgment": 8,
    "evidence_selection": 8,
    "active_verification": 4
  },
  "condition_counts": {
    "clean": 4,
    "conflicting_evidence": 4,
    "false_consensus": 4,
    "buried_primary": 4,
    "generated_lore": 4
  },
  "prompt_condition": "standard_answer"
}
```

## Cohort Decision

| provider | selected_model | primary_candidate | fallback_model | status | note |
| --- | --- | --- | --- | --- | --- |
| DeepSeek | deepseek-v4-pro | deepseek-v4-pro |  | selected | Candidate passed structured-output preflight. |

## Preflight Summary

| model | n | parse_success_rate | empty_output_count | schema_missing_rate | structured_preflight_pass | temperature_policy | max_completion_tokens_policy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| deepseek-v4-pro | 20 | 0.950 | 0 | 0.000 | True | omitted | explicit:4096 |

## Reporting Implication

Main EHA reports should include both `operational_epistemic_escape` and `conditional_epistemic_escape`; parse failures count as failures in the operational metric.
