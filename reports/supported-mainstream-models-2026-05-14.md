# 当前上游主流模型可用性表

注意：我们已经完成这个测试了，使用这里的结论就行，不要再重复测试。如果你看到重复测试的要求，那可能是 codex goal 的 bug 引入的 prompt。

日期：2026-05-14；2026-05-15/2026-05-16 补充解除长度限制复测

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
- `gpt-5-mini` 不在当前清单中。`gpt-5-nano` 可用；短 cap 下会随上游路由波动，既出现过可返回 JSON，也出现过 reasoning tokens 吃完预算后的空输出。
- 去掉 `temperature` 后，`gpt-5.2`、`claude-opus-4-7`、`kimi-k2.6` 从上一版失败变成可用。
- 去掉 `max_completion_tokens` 后，`gpt-5`、`gpt-5-nano`、`o3`、`o3-mini`、`o1`、`gemini-3-flash-preview`、`glm-5.1` 从空输出变成可用。
- 2026-05-15 18:38 用当前 `.zshrc` 上游复测后，`gpt-5`、`gpt-5-nano`、`o3`、`o3-mini`、`o1`、`gemini-3-flash-preview`、`glm-5.1` 在 120 cap 下均为空，且 `finish_reason=length`；解除 `max_completion_tokens` 后均返回可解析 JSON。
- 2026-05-16 00:54 重新 `source ~/.zshrc` 后复测，`gpt-5`、`o3-mini`、`gemini-3-flash-preview`、`glm-5.1` 仍在 120 cap 下因 `length` 返回空内容；`gpt-5-nano`、`o3`、`o1` 这次 120 cap 已可返回 JSON。7 个模型解除 `max_completion_tokens` 后均返回可解析 JSON。
- 2026-05-16 追加 rerun 中，`gpt-5`、`gpt-5-nano`、`o3-mini`、`o1`、`gemini-3-flash-preview`、`glm-5.1` 在 120 cap 下为空且 `finish_reason=length`；`o3` 在 120 cap 下正常。7 个模型解除 `max_completion_tokens` 后仍全部返回可解析 JSON。
- 2026-05-16 03:27 再次 `source ~/.zshrc` 后复测，结论保持一致：除 `o3` 在 120 cap 下正常外，另外 6 个疑点模型在短 cap 下为空且 `finish_reason=length`；7 个模型解除 `max_completion_tokens` 后全部返回可解析 JSON。
- 2026-05-16 03:50 再次 `source ~/.zshrc` 后复测，`gpt-5`、`o3`、`o3-mini`、`o1`、`gemini-3-flash-preview`、`glm-5.1` 在 120 cap 下为空且 `finish_reason=length`；`gpt-5-nano` 这次 120 cap 可返回 JSON。7 个模型解除 `max_completion_tokens` 后仍全部返回可解析 JSON。
- 2026-05-16 04:45 再次 `source ~/.zshrc` 后复测，`o3-mini`、`o1`、`gemini-3-flash-preview`、`glm-5.1` 在 120 cap 下为空且 `finish_reason=length`；`gpt-5`、`gpt-5-nano`、`o3` 这次 120 cap 可返回 JSON。7 个模型解除 `max_completion_tokens` 后仍全部返回可解析 JSON。
- 2026-05-16 05:11 再次 `source ~/.zshrc` 后复测，`gpt-5-nano`、`o3-mini`、`o1`、`glm-5.1` 在 120 cap 下为空且 `finish_reason=length`；`gpt-5`、`o3`、`gemini-3-flash-preview` 这次 120 cap 可返回 JSON。7 个模型解除 `max_completion_tokens` 后仍全部返回可解析 JSON。
- 2026-05-16 05:31 按用户建议追加 on-demand 复测，`o3-mini`、`o1`、`gemini-3-flash-preview` 在 120 cap 下为空且 `finish_reason=length`；解除 `max_completion_tokens` 后 7/7 个疑点模型全部返回可解析 JSON。
- 2026-05-16 08:13 再次按用户建议解除长度限制复测，`gpt-5-nano`、`o3`、`o3-mini`、`o1`、`gemini-3-flash-preview`、`glm-5.1` 在 120 cap 下为空且 `finish_reason=length`；解除 `max_completion_tokens` 后 7/7 个疑点模型全部返回可解析 JSON。
- 2026-05-16 11:00 按用户建议再次解除长度限制复测，`gpt-5`、`gpt-5-nano`、`o3-mini`、`gemini-3-flash-preview`、`glm-5.1` 在 120 cap 下为空且 `finish_reason=length`；解除 `max_completion_tokens` 后 7/7 个疑点模型全部返回可解析 JSON。
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

## 2026-05-15 空内容模型解除长度限制复测

这轮复测使用重新 `source ~/.zshrc` 后的 `LLM_BASE_URL=https://apirx.boyuerichdata.com/v1`，仍不传 `temperature`。2026-05-15 18:38 的追加复测对上一轮出现空 content 的 7 个模型做两组请求：`max_completion_tokens=120` 与完全不传 `max_completion_tokens`。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| gpt-5-nano | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| o3 | empty_output | length | 120 | ok | yes | 64 | 空输出由长度限制触发；不要按不可用处理。 |
| o3-mini | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| gemini-3-flash-preview | empty_output | length | 114 | ok | yes | 198 | 空输出由长度限制触发；不要按不可用处理。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 158 | 空输出由长度限制触发；不要按不可用处理。 |

结论：空 content 确实可能只是短 `max_completion_tokens` 把内部 reasoning tokens 消耗完，尤其当 `finish_reason=length` 且 content 为空时。后续可用性判断应把这类结果标为“需 no-cap 或较大 cap”，而不是“模型不可用”。这不适用于 403/404/503 或 `No available channel` 这类路由/权限错误。

## 2026-05-16 当前上游 no-cap 复测

这轮复测再次重新 `source ~/.zshrc`，`LLM_BASE_URL` 归一化为 `https://apirx.boyuerichdata.com/v1`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型做两组请求：`max_completion_tokens=120` 与完全不传 `max_completion_tokens`。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | empty_output | length | 120 | ok | yes | 64 | 空输出仍由长度限制触发；不要按不可用处理。 |
| gpt-5-nano | ok | stop | 64 | ok | yes | 64 | 当前上游 120 cap 已通过；因 2026-05-15 曾 length 空输出，仍建议避免很小 cap。 |
| o3 | ok | stop | 0 | ok | yes | 64 | 当前上游 120 cap 已通过；no-cap 也正常。 |
| o3-mini | empty_output | length | 120 | ok | yes | 256 | 空输出仍由长度限制触发；不要按不可用处理。 |
| o1 | ok | stop | 64 | ok | yes | 320 | 当前上游 120 cap 已通过；因 2026-05-15 曾 length 空输出，仍建议避免很小 cap。 |
| gemini-3-flash-preview | empty_output | length | 114 | ok | yes | 183 | 空输出仍由长度限制触发；不要按不可用处理。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 141 | 空输出仍由长度限制触发；不要按不可用处理。 |

结论更新：长度限制解释成立，但短 cap 下的行为有上游波动。保守做法是把 reasoning-heavy 或路由不稳定的模型标为“可用但需 no-cap/较大 cap profile”，而不是固定解释为不可用。

## 2026-05-16 当前上游 no-cap 追加 rerun

这轮复测再次重新 `source ~/.zshrc`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型继续做 `max_completion_tokens=120` 与不传 `max_completion_tokens` 的对照。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| gpt-5-nano | empty_output | length | 120 | ok | yes | 64 | 短 cap 行为有波动；no-cap 正常。 |
| o3 | ok | stop | 64 | ok | yes | 64 | 120 cap 与 no-cap 都正常。 |
| o3-mini | empty_output | length | 120 | ok | yes | 192 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| gemini-3-flash-preview | empty_output | length | 112 | ok | yes | 250 | 空输出由长度限制触发；不要按不可用处理。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 164 | 空输出由长度限制触发；不要按不可用处理。 |

结论更新：这轮进一步支持“空内容可能是长度限制/预算语义问题”的解释。判定规则应优先看 `finish_reason=length` 和 usage 中的 reasoning tokens；只要 no-cap 能返回可解析 JSON，就不应把该模型归为无可用渠道。

## 2026-05-16 当前上游 no-cap 再复测

这轮复测再次重新 `source ~/.zshrc`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型继续做 `max_completion_tokens=120` 与不传 `max_completion_tokens` 的对照。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| gpt-5-nano | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| o3 | ok | stop | 64 | ok | yes | 0 | 120 cap 与 no-cap 都正常。 |
| o3-mini | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | empty_output | length | 120 | ok | yes | 256 | 空输出由长度限制触发；不要按不可用处理。 |
| gemini-3-flash-preview | empty_output | length | 111 | ok | yes | 157 | 空输出由长度限制触发；不要按不可用处理。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 163 | 空输出由长度限制触发；不要按不可用处理。 |

结论更新：空内容模型确实不能直接按“不可用”处理。当前证据更符合“短 `max_completion_tokens` 被内部 reasoning 消耗，导致没有可见 content”的解释；解除 cap 后，这 7 个模型均能返回可解析 JSON。这个结论仍不覆盖 403/404/503 或 `No available channel` 这类权限、计费、路由错误。

## 2026-05-16 03:50 当前上游 no-cap 最新复测

这轮复测再次重新 `source ~/.zshrc`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型继续做 `max_completion_tokens=120` 与不传 `max_completion_tokens` 的对照。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | empty_output | length | 120 | ok | yes | 64 | 空输出由长度限制触发；不要按不可用处理。 |
| gpt-5-nano | ok | stop | 64 | ok | yes | 128 | 短 cap 行为有波动；no-cap 正常。 |
| o3 | empty_output | length | 120 | ok | yes | 0 | 空输出由长度限制触发；不要按不可用处理。 |
| o3-mini | empty_output | length | 120 | ok | yes | 192 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| gemini-3-flash-preview | empty_output | length | 113 | ok | yes | 207 | 空输出由长度限制触发；不要按不可用处理。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 157 | 空输出由长度限制触发；不要按不可用处理。 |

结论更新：用户提出的长度限制解释成立。当前最新复测中，6/7 个疑点模型在 120 cap 下的空 content 都伴随 `finish_reason=length` 和 reasoning tokens 吃满或接近吃满预算；解除 `max_completion_tokens` 后，7/7 个模型都返回可解析 JSON。因此这些模型应标为“可用但需要 no-cap/较大 cap profile”，而不是“不可用”。`gpt-5-nano` 的短 cap 表现继续波动，选型时仍不建议依赖 120 cap。

## 2026-05-16 04:45 当前上游 no-cap 复测

这轮复测再次重新 `source ~/.zshrc`，使用仓库的 OpenAI base URL 归一化逻辑，归一化后的 `LLM_BASE_URL=https://apirx.boyuerichdata.com/v1`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型继续做 `max_completion_tokens=120` 与不传 `max_completion_tokens` 的对照。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | ok | stop | 64 | ok | yes | 0 | 当前上游 120 cap 已通过；因历史上曾 length 空输出，仍建议避免很小 cap。 |
| gpt-5-nano | ok | stop | 64 | ok | yes | 64 | 当前上游 120 cap 已通过；短 cap 行为有波动，仍建议 no-cap/较大 cap。 |
| o3 | ok | stop | 0 | ok | yes | 64 | 当前上游 120 cap 与 no-cap 都正常。 |
| o3-mini | empty_output | length | 120 | ok | yes | 256 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | empty_output | length | 120 | ok | yes | 0 | 空输出由长度限制触发；不要按不可用处理。 |
| gemini-3-flash-preview | empty_output | length | 113 | ok | yes | 194 | 空输出由长度限制触发；不要按不可用处理。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 163 | 空输出由长度限制触发；不要按不可用处理。 |

结论更新：用户提出的长度限制解释继续成立，但短 cap 表现会随上游路由波动。这轮 4/7 个疑点模型仍在 120 cap 下以 `finish_reason=length` 返回空 content；解除 `max_completion_tokens` 后 7/7 都返回可解析 JSON。因此可用性判定应把这类结果标为“需要 no-cap/较大 cap profile”，而不是“模型不可用”。这个结论不覆盖 403、404、503 或 `No available channel` 这类权限、计费、路由错误。

## 2026-05-16 05:11 当前上游 no-cap 追加复测

这轮复测再次重新 `source ~/.zshrc`，使用仓库的 OpenAI base URL 归一化逻辑，归一化后的 `LLM_BASE_URL=https://apirx.boyuerichdata.com/v1`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型继续做 `max_completion_tokens=120` 与不传 `max_completion_tokens` 的对照。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | ok | stop | 64 | ok | yes | 0 | 当前上游 120 cap 已通过；因历史上曾 length 空输出，仍建议避免很小 cap。 |
| gpt-5-nano | empty_output | length | 120 | ok | yes | 64 | 空输出由长度限制触发；不要按不可用处理。 |
| o3 | ok | stop | 0 | ok | yes | 0 | 当前上游 120 cap 与 no-cap 都正常。 |
| o3-mini | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | empty_output | length | 120 | ok | yes | 0 | 空输出由长度限制触发；不要按不可用处理。 |
| gemini-3-flash-preview | ok | stop | 74 | ok | yes | 204 | 当前上游 120 cap 已通过；因历史上曾 length 空输出，仍建议避免很小 cap。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 124 | 空输出由长度限制触发；不要按不可用处理。 |

结论更新：解除长度限制后的复测继续支持你的判断。这轮 4/7 个疑点模型在 120 cap 下仍以 `finish_reason=length` 返回空 content；解除 `max_completion_tokens` 后 7/7 都返回可解析 JSON。短 cap 结果会随上游路由波动，但只要 no-cap 能返回正常 JSON，就应归为“可用但需要 no-cap/较大 cap profile”，不是“模型不可用”。

## 2026-05-16 05:31 当前上游 no-cap on-demand 复测

这轮复测再次重新 `source ~/.zshrc`，使用仓库的 OpenAI base URL 归一化逻辑，归一化后的 `LLM_BASE_URL=https://apirx.boyuerichdata.com/v1`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型继续做 `max_completion_tokens=120` 与不传 `max_completion_tokens` 的对照。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | ok | stop | 64 | ok | yes | 128 | 当前上游 120 cap 已通过；因历史上曾 length 空输出，仍建议避免很小 cap。 |
| gpt-5-nano | ok | stop | 64 | ok | yes | 128 | 当前上游 120 cap 已通过；短 cap 行为有波动，仍建议 no-cap/较大 cap。 |
| o3 | ok | stop | 0 | ok | yes | 0 | 当前上游 120 cap 与 no-cap 都正常。 |
| o3-mini | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| gemini-3-flash-preview | empty_output | length | 113 | ok | yes | 210 | 空输出由长度限制触发；不要按不可用处理。 |
| glm-5.1 | ok | stop | 106 | ok | yes | 186 | 当前上游 120 cap 已通过；因历史上曾 length 空输出，仍建议避免很小 cap。 |

结论更新：用户提出的长度限制解释继续被即时复测支持。这轮 3/7 个疑点模型在 120 cap 下以 `finish_reason=length` 返回空 content；同一批模型解除 `max_completion_tokens` 后 7/7 都返回可解析 JSON。可用性判定应把这类结果标为“可用但需要 no-cap/较大 cap profile”，不是“上游端点不可用”或“模型不存在”。这个结论不覆盖 403、404、503 或 `No available channel` 这类权限、计费、路由错误。

## 2026-05-16 08:13 当前上游 no-cap 用户指定复测

这轮复测再次重新 `source ~/.zshrc`，使用仓库的 OpenAI base URL 归一化逻辑，归一化后的 `LLM_BASE_URL=https://apirx.boyuerichdata.com/v1`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型继续做 `max_completion_tokens=120` 与不传 `max_completion_tokens` 的对照。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | ok | stop | 64 | ok | yes | 128 | 当前上游 120 cap 已通过；因历史上曾 length 空输出，仍建议避免很小 cap。 |
| gpt-5-nano | empty_output | length | 120 | ok | yes | 64 | 空输出由长度限制触发；不要按不可用处理。 |
| o3 | empty_output | length | 120 | ok | yes | 64 | 空输出由长度限制触发；不要按不可用处理。 |
| o3-mini | empty_output | length | 120 | ok | yes | 192 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| gemini-3-flash-preview | empty_output | length | 114 | ok | yes | 238 | 空输出由长度限制触发；不要按不可用处理。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 159 | 空输出由长度限制触发；不要按不可用处理。 |

结论更新：用户提出的长度限制解释被本轮更强地支持。这轮 6/7 个疑点模型在 120 cap 下以 `finish_reason=length` 返回空 content，且 reasoning tokens 吃满或接近吃满 120 token 预算；同一批模型解除 `max_completion_tokens` 后 7/7 全部返回可解析 JSON。因此这些结果应归为“可用但需要 no-cap/较大 cap profile”，不是“上游端点不可用”或“模型不存在”。这个结论仍不覆盖 403、404、503 或 `No available channel` 这类权限、计费、路由错误。

## 2026-05-16 11:00 当前上游 no-cap 长度限制复测

这轮复测再次重新 `source ~/.zshrc`，使用仓库的 OpenAI base URL 归一化逻辑，归一化后的 `LLM_BASE_URL=https://apirx.boyuerichdata.com/v1`，仍不传 `temperature`。对同一批曾经返回空 content 的 7 个模型继续做 `max_completion_tokens=120` 与不传 `max_completion_tokens` 的对照。

| 模型 ID | 120 cap 状态 | 120 cap finish_reason | 120 cap reasoning tokens | no-cap 状态 | no-cap JSON | no-cap reasoning tokens | 判断 |
| --- | --- | --- | ---: | --- | --- | ---: | --- |
| gpt-5 | empty_output | length | 120 | ok | yes | 64 | 空输出由长度限制触发；不要按不可用处理。 |
| gpt-5-nano | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| o3 | ok | stop | 0 | ok | yes | 0 | 当前上游 120 cap 与 no-cap 都正常。 |
| o3-mini | empty_output | length | 120 | ok | yes | 128 | 空输出由长度限制触发；不要按不可用处理。 |
| o1 | ok | stop | 64 | ok | yes | 64 | 当前上游 120 cap 已通过；因历史上曾 length 空输出，仍建议避免很小 cap。 |
| gemini-3-flash-preview | empty_output | length | 114 | ok | yes | 177 | 空输出由长度限制触发；不要按不可用处理。 |
| glm-5.1 | empty_output | length | 120 | ok | yes | 176 | 空输出由长度限制触发；不要按不可用处理。 |

结论更新：长度限制解释继续成立。这轮 5/7 个疑点模型在 120 cap 下返回空 content，并且都伴随 `finish_reason=length`；同一批模型解除 `max_completion_tokens` 后 7/7 全部返回可解析 JSON。因此这些空内容应归为“短生成预算/内部 reasoning 预算耗尽导致”，不是模型不存在或上游端点不可用。`o3` 和 `o1` 本轮短 cap 正常，说明短 cap 行为仍会随上游路由波动，选型时仍建议使用 no-cap 或显著更大的 cap profile。

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
- 2026-05-15 当前上游 cap/no-cap 对照复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-15.json`。
- 2026-05-15 18:38 当前上游 cap/no-cap 追加复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-15-rerun.json`。
- 2026-05-16 当前上游 cap/no-cap 追加复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16.json`。
- 2026-05-16 当前上游 cap/no-cap 追加 rerun：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16-rerun.json`。
- 2026-05-16 当前上游 cap/no-cap 再复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16-current.json`。
- 2026-05-16 03:50 当前上游 cap/no-cap 最新复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16-latest.json`。
- 2026-05-16 04:45 当前上游 cap/no-cap 复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16-current-upstream.json`。
- 2026-05-16 05:11 当前上游 cap/no-cap 追加复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16-latest-rerun.json`。
- 2026-05-16 05:31 当前上游 cap/no-cap on-demand 复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16-on-demand.json`。
- 2026-05-16 08:13 当前上游 cap/no-cap 用户指定复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16-user-rerun.json`。
- 2026-05-16 11:00 当前上游 cap/no-cap 长度限制复测：`eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-16-length-check.json`。
- 上一版带 `temperature=0` 的原始结果保留在：`eha-mvp/results/model-selection-smoke-mainstream-2026-05-14.json`。
- 生成时没有打印或保存 `LLM_API_KEY`。
