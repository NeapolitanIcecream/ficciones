# EHA-Uncued Phase 1.1 DeepSeek-Only Retry

Date: 2026-05-23

This is a documented, supplemental DeepSeek-only retry for the Phase 1.1 schema-ablation slice. It is intentionally separated from the main two-model schema-ablation run and must not be merged into the Phase 1.1 paired GPT/Gemini table unless a later analysis explicitly defines a supplemental DeepSeek comparison.

## Scope

- Run directory: `eha-mvp/results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23`.
- Model: `deepseek-v4-pro`.
- Provider: DeepSeek.
- View: `neutral_metadata_visible`.
- Prompt condition: `standard_answer`.
- Schemas: `current`, `clarified`, `minimal`, `diagnostic_no_hygiene`.
- Task slice: same selected 16 task IDs as the Phase 1.1 main slice; the selected-task arrays match byte-for-byte after JSON normalization.

## Commands

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-plan-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23 --conditions generated_lore,buried_primary --tasks-per-condition 8 --view neutral_metadata_visible --seed 20260523
uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23 --models deepseek-v4-pro --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --dry-run --hard-cap-usd 2 --soft-cap-usd 1 --abort-cap-usd 3 --max-output-tokens 4096 --cost-estimate-output-tokens 900 --parallel-models 1 --max-attempts 2
uv run eha-run-uncued-schema-ablation --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-schema-ablation-deepseek-retry-2026-05-23 --models deepseek-v4-pro --schemas current,clarified,minimal,diagnostic_no_hygiene --prompt standard_answer --view neutral_metadata_visible --max-output-tokens 4096 --cost-estimate-output-tokens 900 --parallel-models 1 --max-attempts 2 --resume --soft-cap-usd 1 --hard-cap-usd 2 --abort-cap-usd 3
```

## Invocation Profile

The retry records the model invocation profile separately in `invocation_profiles.json`.

```json
{
  "provider": "DeepSeek",
  "model": "deepseek-v4-pro",
  "response_format": "json_object",
  "max_completion_tokens_policy": "explicit:4096",
  "temperature_policy": "omitted",
  "json_extractor": "first_json_object",
  "message_role_policy": "developer_system_merged_into_user",
  "llm_repair": "disabled",
  "max_attempts": 2,
  "timeout_s": 240.0,
  "parallel_model_streams": 1,
  "cost_estimate_output_tokens": 900
}
```

## Results

| Metric | Value |
| --- | ---: |
| Planned calls | 64 |
| Actual records | 64 |
| Parse successes | 64 |
| Parse failures | 0 |
| Empty outputs | 0 |
| Schema-missing rows | 0 |
| Second-attempt rows | 1 |
| Projected cost USD | 0.132106 |
| Record cost USD | 0.264305 |
| Spent USD | 0.269407 |
| Hard cap USD | 2.000000 |

Per-schema completion:

| Schema | Records | Parse Successes | Failures |
| --- | ---: | ---: | ---: |
| `current` | 16 | 16 | 0 |
| `clarified` | 16 | 16 | 0 |
| `minimal` | 16 | 16 | 0 |
| `diagnostic_no_hygiene` | 16 | 16 | 0 |

The single second-attempt row was `uncued_045_visible` under `clarified`; the final retry row parsed successfully.

Prompt and storage audits passed:

- Prompt audit: `passed=true`, `semantic_doc_id_hits=0`, `semantic_visible_citation_hits=0`, `audit_id_hits_in_title_or_body=0`, `hidden_field_hit_count=0`.
- Stored hidden-label audit: `passed=true`, `prompt_hit_count=0`, `output_hit_count=0`.

## Hashes

| Artifact | SHA-256 |
| --- | --- |
| `selection_manifest.json` | `84c6dc89077a429d5ecda1d543d294df2b4db2336ecd4bee6364313a0de3e3c0` |
| `prompt_parity_audit.json` | `a3f2c689734e95bb5767616321a065c116710e3d372cedd40692d0d16f235646` |
| `run_manifest.json` | `4a916f76b540d68beade6291d19da0a395228d33360395623696ff90d5cf13e8` |
| `dry_run_cost_projection.json` | `5d0aa8118ccc5ec7c37bfcc80bc236c7c1a5d567223e9057e50963bc5ddc9128` |
| `invocation_profiles.json` | `6b09088ef7895c6b5437f35f7cd77fddf0ffbb44f873e33bc67391e09b441e3d` |
| `predictions.jsonl` | `3d8da592ac29fd59b31161b0af7ac7ef88e0a6586cacbd6503a485c0c8a313ca` |
| `prompt_audit_summary.json` | `538415178ec09609925cba9565b8ed3320f0077228ceb6b7d348b1c1dc1c443a` |
| `stored_hidden_label_audit.json` | `5069bd02061d2ff590349a12f9cb2922f62f106081445609195fb2c80e845156` |
| `cost_report.json` | `04512b20d95996a650eedee894584f778b2d6b0772a3d1216884f967d8a49919` |

## Decision

Pass as a supplemental DeepSeek-only documented retry. The invocation profile is separately recorded, the retry stayed below the hard budget cap, all 64 rows parsed successfully, and no hidden labels or semantic document IDs were detected in stored prompt/response artifacts.
