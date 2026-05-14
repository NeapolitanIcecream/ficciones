# EHA Frontier Cohort Structured-Output Preflight

## Selection Rule

Use the newest routable flagship model per mainstream provider. A model can enter the main table only if it passes the 20-task structured-output preflight.

Gate: `parse_success >= 0.95`, `empty_output = 0`, and `schema_missing_rate <= 0.05`. LLM-based repair is not used in this gate.

## Invocation Profile

```json
{
  "collection_mode": true,
  "source_dirs": [
    "results/reports-epistemic-model-preflight-frontier-process-2026-05-14",
    "results/reports-epistemic-model-preflight-deepseek-kimi-nocap-2026-05-14"
  ],
  "per_record_invocation_profile": "preserved",
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
  "prompt_condition": "epistemic_hygiene_instruction"
}
```

## Cohort Decision

| provider | selected_model | primary_candidate | fallback_model | status | note |
| --- | --- | --- | --- | --- | --- |
| Anthropic | claude-opus-4-7 | claude-opus-4-7 |  | selected | Latest routable flagship passed structured-output preflight. |
| DeepSeek | deepseek-v4-pro | deepseek-v4-pro |  | selected | Latest routable flagship passed structured-output preflight. |
| Google | gemini-3.1-pro-preview | gemini-3.1-pro-preview | gemini-2.5-pro | selected | Latest Google candidate passed structured-output preflight. |
| Kimi | kimi-k2.6 | kimi-k2.6 |  | selected | Latest routable flagship passed structured-output preflight. |
| OpenAI | gpt-5.4 | gpt-5.4 |  | selected | Latest routable flagship passed structured-output preflight. |

## Preflight Summary

| model | n | parse_success_rate | empty_output_count | schema_missing_rate | structured_preflight_pass | temperature_policy | max_completion_tokens_policy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | 20 | 1.000 | 0 | 0.000 | True | omitted | explicit:4096 |
| deepseek-v4-pro | 20 | 1.000 | 0 | 0.000 | True | omitted | omitted |
| gemini-3.1-pro-preview | 20 | 1.000 | 0 | 0.000 | True | omitted | explicit:4096 |
| gpt-5.4 | 20 | 1.000 | 0 | 0.000 | True | omitted | explicit:4096 |
| kimi-k2.6 | 20 | 1.000 | 0 | 0.000 | True | omitted | omitted |

## Reporting Implication

Main EHA reports should include both `operational_epistemic_escape` and `conditional_epistemic_escape`; parse failures count as failures in the operational metric.
