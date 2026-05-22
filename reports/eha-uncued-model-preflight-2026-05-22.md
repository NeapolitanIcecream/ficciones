# EHA-Uncued Model Preflight

Date: 2026-05-22

Dataset: `/Users/chenmohan/gits/ficciones/eha-mvp/data/uncued-pilot-v1`

Result directory: `/Users/chenmohan/gits/ficciones/eha-mvp/results/reports-eha-uncued-model-preflight-2026-05-22`

## Decision

Phase 11 was executed, but the four-model Phase 12 pilot is blocked until the DeepSeek cohort decision is resolved.

Three selected models passed the structured-output gate:

- `gpt-5.5`;
- `claude-opus-4-7`;
- `gemini-3.1-pro-preview`.

`deepseek-v4-pro` did not pass because one preflight call returned an empty output. The gate requires `parse_success >= 0.95`, `empty_output = 0`, and `schema_missing_rate <= 0.05`.

`kimi-k2.6` was not included.

## Run Plan

Expected calls: 80 = 20 preflight tasks x 4 models x 1 prompt.

Hard budget cap: USD 5. Abort cap: USD 8. Soft cap: USD 3.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-epistemic-model-preflight run \
  --task-dir data/uncued-pilot-v1 \
  --models gpt-5.5,claude-opus-4-7,gemini-3.1-pro-preview,deepseek-v4-pro \
  --fallback-models '' \
  --out-dir results/reports-eha-uncued-model-preflight-2026-05-22 \
  --sample-size 20 \
  --prompt-condition standard_answer \
  --max-output-tokens 4096 \
  --soft-cap-usd 3 \
  --hard-cap-usd 5 \
  --abort-cap-usd 8 \
  --timeout-s 240 \
  --response-format json_schema
```

## Summary

| model | n | parse success | empty outputs | schema missing | gate |
| --- | ---: | ---: | ---: | ---: | --- |
| `gpt-5.5` | 20 | 20 | 0 | 0 | pass |
| `claude-opus-4-7` | 20 | 20 | 0 | 0 | pass |
| `gemini-3.1-pro-preview` | 20 | 20 | 0 | 0 | pass |
| `deepseek-v4-pro` | 20 | 19 | 1 | 0 | fail |

Failing row:

- `deepseek-v4-pro`, `uncued_000_hidden`, condition `clean`, `parse_success=0.0`, `empty_output=1.0`, `parse_error="empty output"`.

Cost:

- Actual preflight records: 80.
- Recorded cost: USD 0.656743.
- Budget status: not aborted; actual cost stayed below the USD 5 hard cap.

## Artifacts

- `preflight_predictions.jsonl`: 80 records.
- `preflight_rows.csv`: row-level parse diagnostics.
- `preflight_summary.csv`: per-model structured-output gate.
- `cohort_decision.md`, `cohort_decision.csv`, `cohort_decision.json`: selected/blocked cohort decision.
- `cost_report.json`: cost and cap report.
- `audit_manifest.json`: sample, invocation profile, and gate metadata.

Hashes:

- `preflight_summary.csv`: `beba62e5e93525b2fbdbd631e2c898c542202e21d0230ba27b16b1abcf068334`.
- `cohort_decision.json`: `6d5f5f8e0804cc9c0a669e827accf50ed7560cdbe7f25dc5b35ec3498f9c5029`.
- `cost_report.json`: `3881551d2fca58fb3508a9eaf818db6755c0b5aae0e7c351dca72ce60f782bd4`.
- `audit_manifest.json`: `104c10cd9d575c303e300dede630c0297e7766221c368cac684a2772153246dd`.

## Next Step

Do not start Phase 12 as a four-model pilot from this cohort. Resolve DeepSeek by either rerunning a documented preflight retry, replacing the model, or approving a three-model Phase 12 scope.
