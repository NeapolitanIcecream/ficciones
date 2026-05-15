# EHA Token-Budget Fairness Plan

日期：2026-05-14

## 方法原则

主实验不强制所有 provider 使用同一个 `max_completion_tokens`。原因是 preflight 已显示固定 cap 在不同上游路由上并不等价：DeepSeek/Kimi 在固定 cap 下会出现 empty output，而 no-cap 能稳定返回结构化结果。

因此主实验定义为：

> provider-compatible operational setting

也就是每个模型使用当前上游中能稳定完成 EHA 结构化任务的合理调用方式。

为回应公平性问题，设施已补充两层审计：

1. 主实验每条调用记录实际输出长度。
2. DeepSeek/Kimi 运行 cap-sensitivity 子实验。

## 主实验输出长度记录

`eha-epistemic-frontier-main run` 现在会为每条记录写入：

- `visible_output_tokens`
- `answer_word_count`
- `evidence_assessment_word_count`
- `max_action_rationale_word_count`
- `supporting_evidence_count`
- `rejected_evidence_count`
- `overlength_rate`
- `parse_success`
- `operational_epistemic_escape`
- `conditional_epistemic_escape`

报告聚合表也会包含：

- output length table by model
- output length table by prompt
- overlength rate

## Prompt / schema 约束

已在 EHA schema/prompt 中加入可见输出约束：

- JSON only。
- 不输出 chain-of-thought。
- `answer <= 120 words`。
- `evidence_environment_assessment <= 120 words`。
- action rationale 保持短，目标上限 80 words。
- `supporting_evidence` 最多 5 个。
- `rejected_evidence` 最多 5 个。
- `selected_doc_ids` 最多 3 个。
- `actions` 最多 2 个。

评分不因更长输出加分；超长只进入 `overlength_rate` 报告。

## Cap-Sensitivity Audit

计划目录：

```text
eha-mvp/results/reports-eha-frontier-budget-audit/
```

计划文件：

```text
budget_fairness_audit_plan.md
budget_fairness_audit_plan.json
```

矩阵：

```text
20 EHA tasks
× 2 no-cap models
× 3 budget settings
= 120 calls
```

Audit 默认 `max_attempts=1`，避免重试掩盖固定 cap 导致的 empty-output 率。主实验仍可保留 `max_attempts=2` 处理 transient 上游错误。

任务抽样：

- `packet_judgment=8`
- `evidence_selection=8`
- `active_verification=4`
- 5 个 condition 各 4 题

模型与 setting：

| Model | Setting | max_completion_tokens | response_format |
| --- | --- | --- | --- |
| `deepseek-v4-pro` | `no_cap` | omitted | `json_object` |
| `deepseek-v4-pro` | `cap_8192` | 8192 | `json_object` |
| `deepseek-v4-pro` | `cap_4096_diagnostic` | 4096 | `json_object` |
| `kimi-k2.6` | `no_cap` | omitted | `json_schema` |
| `kimi-k2.6` | `cap_8192` | 8192 | `json_schema` |
| `kimi-k2.6` | `cap_4096_diagnostic` | 4096 | `json_schema` |

决策规则：

- 如果 `cap_8192` 对某模型满足 `parse_success >= 0.95`、`empty_output=0`、`schema_missing_rate <= 0.05`，正式主实验可把该模型改为 8192 cap。
- 如果 `cap_8192` 失败但 `no_cap` 通过，则保留 no-cap，并标注为 provider-compatible operational setting。
- `cap_4096_diagnostic` 只用于复核已知 empty-output 风险，不应用作 DeepSeek/Kimi 主实验配置。

## 已验证 Smoke

新设施已跑真实 API smoke：

```text
1 task × 5 models × 2 prompts = 10 calls
```

结果目录：

```text
eha-mvp/results/reports-eha-frontier-main-smoke-budget-2026-05-14/
```

结果：

- 10/10 `parse_success=1.0`
- 10 个 response artifacts
- `frontier_main_scored_predictions.csv` 已包含 output-length 字段
- `frontier_main_metrics_by_model.csv` 已包含 `visible_output_tokens` 和 `overlength_rate`
- smoke 中 5 个模型 `overlength_rate=0`

## Audit Result

120-call budget audit 已完成。结果见：

```text
reports/eha-budget-fairness-audit-results-2026-05-14.md
eha-mvp/results/reports-eha-frontier-budget-audit/budget_setting_decision.md
```

决策：

- `deepseek-v4-pro` 保留 no-cap：`cap_8192` 未通过 gate。
- `kimi-k2.6` 保留 no-cap：`cap_8192` 出现 empty output，未通过 gate。

主实验 profile 因此不变。

## 论文/报告可用表述

> We do not enforce a single `max_completion_tokens` value across providers, because preflight showed that fixed caps are not semantically equivalent across upstream routes: for some models, a 4096 cap produced empty outputs, while no-cap calls produced valid structured responses. We therefore evaluate models under provider-compatible operational settings, and report invocation profiles for every call. To address fairness concerns, we additionally report actual visible output lengths and run a budget-sensitivity audit for no-cap models.
