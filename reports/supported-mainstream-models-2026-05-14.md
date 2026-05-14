# 当前上游主流模型可用性表

日期：2026-05-14

## 检查方法

- `LLM_BASE_URL` 已归一化为 `https://apirx.boyuerichdata.com/v1`。
- 模型清单来自 `/v1/models`。
- 主 smoke test 使用 OpenAI-compatible `chat.completions.create`，`response_format={"type":"json_object"}`，不传 `temperature`，`max_completion_tokens=120`。
- 对主 smoke 中返回空 content 的模型，追加复测：不传 `temperature`，也不传 `max_completion_tokens`。
- prompt 为：`Return JSON only: {"ok": true}`。
- 这个表只判断当前网关路由和短 JSON 输出是否可用，不代表模型能力排名、价格、上下文长度或长期稳定性。

## 快速结论

- `gpt-5.4-nano` 不在当前 `/v1/models` 清单中，调用返回无可用渠道。
- `gpt-5.5` 在清单中，但当前分组无可用渠道；没有 `gpt-5.5-pro` 这个可见模型 ID。
- `gpt-5-mini` 不在当前清单中。`gpt-5-nano` 可用，但需要去掉 `max_completion_tokens`，否则短上限会被 reasoning tokens 吃掉而空输出。
- 去掉 `temperature` 后，`gpt-5.2`、`claude-opus-4-7`、`kimi-k2.6` 从上一版失败变成可用。
- 去掉 `max_completion_tokens` 后，`gpt-5`、`gpt-5-nano`、`o3`、`o3-mini`、`o1`、`gemini-3-flash-preview`、`glm-5.1` 从空输出变成可用。
- 当前最适合 EHA parse repair surrogate 的优先候选是：`gpt-5.4-mini`、`gpt-5.4`、`gpt-5.2`、`gpt-5.1`、`gpt-5-chat`。若使用 reasoning-heavy 模型如 `gpt-5`/`gpt-5-nano`/`o3`，不要设置很小的 `max_completion_tokens`。
- 进一步的 20-task EHA structured-output preflight 已完成：`gpt-5.4`、`claude-opus-4-7`、`gemini-3.1-pro-preview`、`deepseek-v4-pro`、`kimi-k2.6` 均通过。详见 `reports/eha-frontier-cohort-preflight-2026-05-14.md`。
- 在 EHA 长 prompt 预检中，`deepseek-v4-pro` 和 `kimi-k2.6` 的空输出可由去掉 `max_completion_tokens` 解决；后续主实验应对这两个模型使用 no-cap profile 并显式记录。

## 主流文本模型表

| 模型 ID | 家族 | owned_by | 列表中 | 主 smoke（无温度，120 cap） | 解除 token cap 后 | 最终 JSON 可用性 | 选型建议 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-5.5 | OpenAI / GPT-o | custom | yes | error | - | no | 不建议/不可用 | 列表/名称存在但当前分组无可用渠道或未部署。 |
| gpt-5.4-pro | OpenAI / GPT-o | openai | yes | error | - | no | 不建议/不可用 | 该路由不支持当前 chat/json_object 调用形态。 |
| gpt-5.4 | OpenAI / GPT-o | codex | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-5.4-mini | OpenAI / GPT-o | custom | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-5.2 | OpenAI / GPT-o | codex | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-5.2-chat | OpenAI / GPT-o | custom | yes | error | - | no | 不建议/不可用 | 上游部署不存在或未映射。 |
| gpt-5.2-codex | OpenAI / GPT-o | codex | yes | error | - | no | 不建议/不可用 | 上游部署不存在或未映射。 |
| gpt-5.1 | OpenAI / GPT-o | codex | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-5.1-codex-max | OpenAI / GPT-o | codex | yes | error | - | no | 不建议/不可用 | 上游部署不存在或未映射。 |
| gpt-5.1-codex | OpenAI / GPT-o | codex | yes | error | - | no | 不建议/不可用 | 上游部署不存在或未映射。 |
| gpt-5.1-codex-mini | OpenAI / GPT-o | codex | yes | error | - | no | 不建议/不可用 | 上游部署不存在或未映射。 |
| gpt-5-pro | OpenAI / GPT-o | openai | yes | error | - | no | 不建议/不可用 | 该路由不支持当前 chat/json_object 调用形态。 |
| gpt-5 | OpenAI / GPT-o | codex | yes | empty_output | ok | yes | 可用但需去掉 token cap | 120 token cap 下空输出；去掉 max_completion_tokens 后可返回可解析 JSON。 |
| gpt-5-chat | OpenAI / GPT-o | custom | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-5-codex | OpenAI / GPT-o | codex | yes | error | - | no | 不建议/不可用 | 上游部署不存在或未映射。 |
| gpt-5-nano | OpenAI / GPT-o | openai | yes | empty_output | ok | yes | 可用但需去掉 token cap | 120 token cap 下空输出；去掉 max_completion_tokens 后可返回可解析 JSON。 |
| gpt-4o | OpenAI / GPT-o | openai | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-4o-mini | OpenAI / GPT-o | openai | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-4.1 | OpenAI / GPT-o | openai | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-4.1-mini | OpenAI / GPT-o | openai | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gpt-4.1-nano | OpenAI / GPT-o | openai | yes | ok | - | yes | 可用候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| o4-mini | OpenAI / GPT-o | openai | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| o3-pro | OpenAI / GPT-o | openai | yes | error | - | no | 不建议/不可用 | 该路由不支持当前 chat/json_object 调用形态。 |
| o3 | OpenAI / GPT-o | openai | yes | empty_output | ok | yes | 可用但需去掉 token cap | 120 token cap 下空输出；去掉 max_completion_tokens 后可返回可解析 JSON。 |
| o3-mini | OpenAI / GPT-o | openai | yes | empty_output | ok | yes | 可用但需去掉 token cap | 120 token cap 下空输出；去掉 max_completion_tokens 后可返回可解析 JSON。 |
| o1 | OpenAI / GPT-o | openai | yes | empty_output | ok | yes | 可用但需去掉 token cap | 120 token cap 下空输出；去掉 max_completion_tokens 后可返回可解析 JSON。 |
| claude-opus-4-7 | Anthropic Claude | vertex-ai | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| claude-opus-4-6 | Anthropic Claude | vertex-ai | yes | non_json_output | - | no | 需解析/提示适配 | 返回非严格 JSON 内容：```json {"ok": true} ```。 |
| claude-sonnet-4-6 | Anthropic Claude | vertex-ai | yes | non_json_output | - | no | 需解析/提示适配 | 返回非严格 JSON 内容：```json {"ok": true} ```。 |
| claude-sonnet-4-5-20250929 | Anthropic Claude | vertex-ai | yes | non_json_output | - | no | 需解析/提示适配 | 返回非严格 JSON 内容：```json {"ok": true} ```。 |
| claude-haiku-4-5-20251001 | Anthropic Claude | vertex-ai | yes | non_json_output | - | no | 需解析/提示适配 | 返回非严格 JSON 内容：```json {"ok": true} ```。 |
| gemini-3.1-pro-preview | Google Gemini | vertex-ai | yes | non_json_output | - | no | 需解析/提示适配 | 返回非严格 JSON 内容：Here。 |
| gemini-3-flash-preview | Google Gemini | vertex-ai | yes | empty_output | ok | yes | 可用但需去掉 token cap | 120 token cap 下空输出；去掉 max_completion_tokens 后可返回可解析 JSON。 |
| gemini-2.5-pro | Google Gemini | vertex-ai | yes | ok | - | yes | 可用候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gemini-2.5-flash | Google Gemini | vertex-ai | yes | ok | - | yes | 可用候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| gemini-2.5-flash-lite | Google Gemini | vertex-ai | yes | ok | - | yes | 可用候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| deepseek-v4-pro | DeepSeek | deepseek | yes | ok | - | yes | 可用候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| deepseek-v4-flash | DeepSeek | deepseek | yes | ok | - | yes | 可用候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| bailian/deepseek-v4-pro | DeepSeek | custom | yes | ok | - | yes | 可用候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| bailian/deepseek-v4-flash | DeepSeek | custom | yes | ok | - | yes | 可用候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| kimi-k2.6 | Kimi | custom | yes | ok | - | yes | 优先候选 | 无 temperature、120 token cap 下可返回可解析 JSON。 |
| glm-5.1 | GLM | custom | yes | empty_output | ok | yes | 可用但需去掉 token cap | 120 token cap 下空输出；去掉 max_completion_tokens 后可返回可解析 JSON。 |

## 推荐给 GPT-5.5-Pro 重新选型时重点比较

| 用途 | 首选 | 备选 | 注意事项 |
| --- | --- | --- | --- |
| EHA `gpt-5-mini` parse repair surrogate | `gpt-5.4-mini` | `gpt-5.4`, `gpt-5.2`, `gpt-5.1`, `gpt-5-chat` | 这些在无温度、120 cap 下就能返回严格 JSON。 |
| reasoning-heavy GPT/o 系列 | `gpt-5`, `o3` | `gpt-5-nano`, `o3-mini`, `o1` | 不要设置很小的 `max_completion_tokens`；短 cap 会导致空输出。 |
| 低成本 sanity / cross-provider 对照 | `gpt-4o-mini`, `gpt-4.1-mini`, `o4-mini` | `deepseek-v4-flash`, `gemini-2.5-flash` | 当前 smoke 稳定返回 JSON。 |
| 非 OpenAI 对照 | `deepseek-v4-pro`, `gemini-2.5-pro`, `kimi-k2.6` | `deepseek-v4-flash`, `gemini-2.5-flash-lite` | `kimi-k2.6` 不要传 `temperature=0`。 |
| Claude 路线 | `claude-opus-4-7` | `claude-opus-4-6`, `claude-sonnet-*` | Opus 4.7 在无温度下可用；其他 Claude 返回 fenced JSON，需解析/提示适配。 |

## 复现信息

- 主 smoke 原始结果：`eha-mvp/results/model-selection-smoke-mainstream-no-temperature-2026-05-14.json`。
- 空输出复测原始结果：`eha-mvp/results/model-selection-empty-output-no-token-limit-2026-05-14.json`。
- 上一版带 `temperature=0` 的原始结果保留在：`eha-mvp/results/model-selection-smoke-mainstream-2026-05-14.json`。
- 生成时没有打印或保存 `LLM_API_KEY`。
