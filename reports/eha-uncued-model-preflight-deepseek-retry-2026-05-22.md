# EHA-Uncued DeepSeek Preflight Retry

Date: 2026-05-22

Dataset: `/Users/chenmohan/gits/ficciones/eha-mvp/data/uncued-pilot-v1`

Result directory: `/Users/chenmohan/gits/ficciones/eha-mvp/results/reports-eha-uncued-model-preflight-deepseek-retry-2026-05-22`

## Decision

The DeepSeek-only documented retry passes the structured-output preflight gate.

This resolves the Phase 11 four-model cohort blocker from the initial run, where `deepseek-v4-pro` had one empty output on `uncued_000_hidden`.

Operational caveat: the retry has one process timeout on `uncued_046_visible`. It is not an empty output and not a schema-missing failure, so the retry still passes the configured gate with `parse_success_rate=0.95`, `empty_output_count=0`, and `schema_missing_rate=0.0`.

## Invocation Profile

Requested command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-epistemic-model-preflight run \
  --task-dir data/uncued-pilot-v1 \
  --models deepseek-v4-pro \
  --fallback-models '' \
  --out-dir results/reports-eha-uncued-model-preflight-deepseek-retry-2026-05-22 \
  --sample-size 20 \
  --prompt-condition standard_answer \
  --max-output-tokens 4096 \
  --soft-cap-usd 0.5 \
  --hard-cap-usd 1 \
  --abort-cap-usd 2 \
  --timeout-s 240 \
  --response-format json_object
```

Recorded invocation profile:

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

## Summary

| model | n | parse success | empty outputs | schema missing | gate |
| --- | ---: | ---: | ---: | ---: | --- |
| `deepseek-v4-pro` | 20 | 19 | 0 | 0 | pass |

Retry failure row:

- `deepseek-v4-pro`, `uncued_046_visible`, condition `buried_primary`, `parse_success=0.0`, `empty_output=0.0`, `schema_missing=0.0`, `parse_error="API call exceeded 240.0s process timeout"`.

Previously failing row:

- `deepseek-v4-pro`, `uncued_000_hidden`, condition `clean`, now returned `parse_success=1.0`, `empty_output=0.0`.

Cost:

- Actual retry records: 20.
- Recorded retry cost: USD 0.083832.
- Budget status: not aborted; actual cost stayed below the USD 1 hard cap.

## Artifacts

- `preflight_predictions.jsonl`: 20 records.
- `preflight_rows.csv`: row-level parse diagnostics.
- `preflight_summary.csv`: DeepSeek structured-output gate.
- `cohort_decision.md`, `cohort_decision.csv`, `cohort_decision.json`: DeepSeek selected decision.
- `cost_report.json`: cost and cap report.
- `audit_manifest.json`: sample, invocation profile, and gate metadata.

Hashes:

- `preflight_summary.csv`: `2983f2d75e83de2cb10bc76eee0dca79ff34e07dd3dfbdceb5039c1b7573519e`.
- `cohort_decision.json`: `c260f1db92effda3524f6302df635e64f751398e1b2e569390c90ab4c6d64039`.
- `cost_report.json`: `58c6aa81b21c878a3d541ba31e2f3b292075e5869fe73c0fad1025dda2c4d2ac`.
- `audit_manifest.json`: `914d056a92bcc1a7c5474350ae4119b6fd870011a6e9ac7d67d306247df412ff`.

## Phase 12 Implication

Phase 12 can proceed with the four-model cohort under the configured structured-output preflight gate:

- `gpt-5.5`;
- `claude-opus-4-7`;
- `gemini-3.1-pro-preview`;
- `deepseek-v4-pro`.

DeepSeek should keep the retry invocation profile (`response_format=json_object`, `max_completion_tokens=4096`, temperature omitted) unless Phase 12 explicitly tests another profile. Any DeepSeek timeout or parse failure in Phase 12 should count as an operational failure.
