# EHA-Uncued Phase 12 Pilot Run

Date: 2026-05-22

Status: passed.

## Scope

Phase 12 ran the 60-task role-uncued pilot across two metadata views and four models:

- Views: `neutral_metadata_visible`, `neutral_metadata_hidden`.
- Models: `gpt-5.5`, `claude-opus-4-7`, `gemini-3.1-pro-preview`, `deepseek-v4-pro`.
- Prompt/schema: `standard_answer`, clarified schema.
- Expected records: 480 = 60 latent tasks x 2 views x 4 models x 1 prompt.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-run-uncued-pilot \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --models gpt-5.5,claude-opus-4-7,gemini-3.1-pro-preview,deepseek-v4-pro \
  --views neutral_metadata_visible,neutral_metadata_hidden \
  --schema clarified \
  --prompt standard_answer \
  --hard-cap-usd 15 \
  --soft-cap-usd 10 \
  --abort-cap-usd 20 \
  --max-output-tokens 4096 \
  --timeout-s 240 \
  --parallel-models 4 \
  --max-attempts 2 \
  --deepseek-response-format json_object
```

## Run Outputs

Primary run directory:

```text
eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/
```

Key artifacts:

- `predictions.jsonl`
- `run_manifest.json`
- `invocation_profiles.json`
- `run_summary_by_model.csv`
- `prompt_audit_summary.json`
- `stored_hidden_label_audit.json`
- `cost_report.json`
- `phase12_run_summary.md`
- per-call prompt and response artifacts under `artifacts/`

## Acceptance Evidence

| Check | Result |
| --- | --- |
| Expected records | 480 |
| Actual records | 480 |
| Unique model/task/prompt/budget keys | 480 |
| Duplicate keys | 0 |
| Visible view records | 240 |
| Hidden view records | 240 |
| Prompt audit hits | 0 |
| Stored hidden-label prompt hits | 0 |
| Stored hidden-label output hits | 0 |
| Budget status | not aborted |
| Total spent | USD 3.764007 |

Model summary:

| Model | Provider | Records | Parse Success | Empty Outputs | Schema Missing | Timeouts | Cost USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | Anthropic | 120 | 1.000 | 0 | 0 | 0 | 0.177029 |
| `deepseek-v4-pro` | DeepSeek | 120 | 1.000 | 0 | 0 | 0 | 0.509400 |
| `gemini-3.1-pro-preview` | Google | 120 | 1.000 | 0 | 0 | 0 | 0.475382 |
| `gpt-5.5` | OpenAI | 120 | 1.000 | 0 | 0 | 0 | 2.597870 |

## DeepSeek Invocation Profile

The Phase 12 DeepSeek calls used the documented Phase 11 retry profile:

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
  "timeout_s": 240.0
}
```

This is recorded separately in `invocation_profiles.json` and on each `deepseek-v4-pro` prediction row.

## Hashes

| Artifact | SHA-256 |
| --- | --- |
| `predictions.jsonl` | `e0d6f072c4e260997b68a6055c1583331aa6a355981a2d9f417cf893ed705ca4` |
| `run_summary_by_model.csv` | `74a55842eef9c8da2a9a18b90a41919ee71001817cdb4cf9f8405f77a63ee4ac` |
| `prompt_audit_summary.json` | `4110a36d1b165761ff326f862787c89efedc2ff44ceddf5985a29ef31b0ecf2d` |
| `stored_hidden_label_audit.json` | `5069bd02061d2ff590349a12f9cb2922f62f106081445609195fb2c80e845156` |
| `cost_report.json` | `5d7291ae05a819f20ece4b287261bc4ccf17736e8c8244554ce00ad40728274b` |
| `invocation_profiles.json` | `d806153c5a797d738bc3fb7e648a8f1c3d8a34a62260fb47474627a4b9783670` |
| `run_manifest.json` | `913ae8be97d394ace5904209f4d0beb2aa29f2b3c7b3e4c29622b442eb412572` |

## Decision

Phase 12 passes. The pilot run is complete and ready for Phase 13 scoring/reporting.
