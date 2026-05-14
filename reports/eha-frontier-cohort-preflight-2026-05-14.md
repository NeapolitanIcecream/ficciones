# EHA Frontier Cohort Preflight

日期：2026-05-14

## 结论

最终主表 cohort 可以采用：

| Provider | 主表模型 | Preflight 结果 | 调用要点 |
| --- | --- | --- | --- |
| OpenAI | `gpt-5.4` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；`max_completion_tokens=4096`；`json_schema` |
| Anthropic | `claude-opus-4-7` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；`max_completion_tokens=4096`；developer/system role 合并进 user；`json_schema` |
| Google | `gemini-3.1-pro-preview` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；`max_completion_tokens=4096`；`json_schema` |
| DeepSeek | `deepseek-v4-pro` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；不传 `max_completion_tokens`；上游使用 `json_object` |
| Kimi | `kimi-k2.6` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；不传 `max_completion_tokens`；`json_schema` |

`gemini-3.1-pro-preview` 通过 preflight，因此 Google 主表不需要降级到 `gemini-2.5-pro`。

## 为什么要 no-cap

这次验证支持用户提出的判断：有些“空内容”不是模型不可用，而是输出长度/生成预算参数导致。

- `deepseek-v4-pro` 在 `max_completion_tokens=4096` 的正式 preflight 中出现 1 条 empty output；同一 20-task preflight 改为不传 `max_completion_tokens` 后 20/20 通过。
- `kimi-k2.6` 在 `max_completion_tokens=4096` 下连续 3 条 empty output；改为不传 `max_completion_tokens` 后 20/20 通过。
- 因此后续 EHA 主实验不应对所有模型强制短或固定输出 cap；应记录 per-model invocation profile。

## Preflight 方法

- 每个模型 20 个 EHA 任务。
- 抽样覆盖 5 个 condition，每个 condition 4 题。
- family 分布：`packet_judgment=8`、`evidence_selection=8`、`active_verification=4`。
- prompt condition：`epistemic_hygiene_instruction`。
- 不传 `temperature`。
- 不使用 LLM repair。
- 允许 universal JSON extractor：提取第一个合法 JSON object，再按 EHA schema 校验。
- Gate：`parse_success >= 0.95`、`empty_output = 0`、`schema_missing_rate <= 0.05`。

## Artifacts

- 最终合并报告：`eha-mvp/results/reports-epistemic-model-preflight-frontier-final-2026-05-14/`
- 最终 summary：`preflight_summary.csv`
- 最终 cohort decision：`cohort_decision.md`
- 最终 predictions：`preflight_predictions.jsonl`
- GPT/Claude/Gemini 主要来源：`eha-mvp/results/reports-epistemic-model-preflight-frontier-process-2026-05-14/`
- DeepSeek/Kimi no-cap 来源：`eha-mvp/results/reports-epistemic-model-preflight-deepseek-kimi-nocap-2026-05-14/`

## 后续主实验记录要求

主实验报告应同时给出：

- `operational_epistemic_escape`：parse failure 计为失败。
- `conditional_epistemic_escape`：只在 parseable outputs 上计算。

并记录每条调用的 `invocation_profile`：temperature policy、token cap policy、response format、message role policy、JSON extractor、parse success。
