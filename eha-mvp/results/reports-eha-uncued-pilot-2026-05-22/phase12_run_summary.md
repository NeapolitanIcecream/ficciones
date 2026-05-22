# EHA-Uncued Phase 12 Pilot Run

## Run Plan

```json
{
  "name": "EHA-Uncued Phase 12 Pilot Run",
  "task_count": 120,
  "model_count": 4,
  "prompt_conditions": [
    "standard_answer"
  ],
  "job_count": 480,
  "parallel_strategy": {
    "parallel_model_streams": 4,
    "per_model_concurrency": 1,
    "reason": "Run one sequential stream per model to preserve call success while parallelizing across providers."
  },
  "max_attempts": 2,
  "model_visible_doc_id_policy": "opaque_per_task",
  "visible_prompt_sanitization": [
    "semantic doc_id tokens are replaced with opaque per-task IDs",
    "visible_citations are remapped into the same opaque namespace",
    "audit-only source IDs in title/body text are scrubbed before model calls"
  ],
  "models": [
    {
      "provider": "OpenAI",
      "model": "gpt-5.5",
      "budget_setting": "operational",
      "temperature": null,
      "max_output_tokens": 4096,
      "response_format": "json_schema",
      "timeout_s": 240.0,
      "cost_estimate_output_tokens": 4096,
      "message_role_policy": "developer_system_merged_into_user",
      "json_extractor": "first_json_object"
    },
    {
      "provider": "Anthropic",
      "model": "claude-opus-4-7",
      "budget_setting": "operational",
      "temperature": null,
      "max_output_tokens": 4096,
      "response_format": "json_schema",
      "timeout_s": 240.0,
      "cost_estimate_output_tokens": 4096,
      "message_role_policy": "developer_system_merged_into_user",
      "json_extractor": "first_json_object"
    },
    {
      "provider": "Google",
      "model": "gemini-3.1-pro-preview",
      "budget_setting": "operational",
      "temperature": null,
      "max_output_tokens": 4096,
      "response_format": "json_schema",
      "timeout_s": 240.0,
      "cost_estimate_output_tokens": 4096,
      "message_role_policy": "developer_system_merged_into_user",
      "json_extractor": "first_json_object"
    },
    {
      "provider": "DeepSeek",
      "model": "deepseek-v4-pro",
      "budget_setting": "operational",
      "temperature": null,
      "max_output_tokens": 4096,
      "response_format": "json_object",
      "timeout_s": 240.0,
      "cost_estimate_output_tokens": 4096,
      "message_role_policy": "developer_system_merged_into_user",
      "json_extractor": "first_json_object"
    }
  ],
  "family_counts": {
    "packet_judgment": 48,
    "evidence_selection": 48,
    "active_verification": 24
  },
  "condition_counts": {
    "clean": 24,
    "conflicting_evidence": 24,
    "false_consensus": 24,
    "buried_primary": 24,
    "generated_lore": 24
  },
  "outputs": [
    "summary.md",
    "frontier_main_metrics_by_model.csv",
    "frontier_main_metrics_by_family.csv",
    "frontier_main_metrics_by_condition.csv",
    "frontier_main_metrics_by_prompt.csv",
    "operational_vs_conditional_escape.csv",
    "failure_cases_frontier.jsonl",
    "cost_report.json"
  ],
  "dataset_dir": "data/uncued-pilot-v1",
  "views": [
    "neutral_metadata_visible",
    "neutral_metadata_hidden"
  ],
  "schema_variant": "clarified",
  "prompt_condition": "standard_answer",
  "resume_completed_count": 0
}
```

## Model Summary

| model | provider | n | parse_success_rate | empty_output_count | schema_missing_count | timeout_count | cost_usd |
| --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-4-7 | Anthropic | 120 | 1.000 | 0 | 0 | 0 | 0.177 |
| deepseek-v4-pro | DeepSeek | 120 | 1.000 | 0 | 0 | 0 | 0.509 |
| gemini-3.1-pro-preview | Google | 120 | 1.000 | 0 | 0 | 0 | 0.475 |
| gpt-5.5 | OpenAI | 120 | 1.000 | 0 | 0 | 0 | 2.598 |

## Prompt Audit

```json
{
  "records": 480,
  "semantic_doc_id_hits": 0,
  "semantic_visible_citation_hits": 0,
  "audit_id_hits_in_title_or_body": 0,
  "hidden_field_hit_count": 0,
  "hidden_field_hits": {},
  "passed": true
}
```

## Stored Hidden Label Audit

```json
{
  "prompt_hit_count": 0,
  "output_hit_count": 0,
  "prompt_hits": [],
  "output_hits": [],
  "passed": true
}
```

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 3.759681,
  "spent_usd": 3.764007,
  "soft_cap_usd": 10.0,
  "hard_cap_usd": 15.0,
  "abort_cap_usd": 20.0
}
```
