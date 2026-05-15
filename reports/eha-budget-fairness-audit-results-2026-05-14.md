# EHA Budget Fairness Audit Results

日期：2026-05-14

## 结论

DeepSeek 和 Kimi 都应继续使用 no-cap provider-compatible operational setting。

| Model | Decision | Reason |
| --- | --- | --- |
| `deepseek-v4-pro` | keep `no_cap` | `cap_8192` 只有 0.85 parse success，empty output rate 0.15，未通过 gate。 |
| `kimi-k2.6` | keep `no_cap` | `cap_8192` parse success 为 0.95，但 empty output rate 0.05，不满足 empty output 必须为 0 的 gate。 |

Gate：

```text
parse_success >= 0.95
empty_output_rate = 0
schema_missing_rate <= 0.05
```

## Sensitivity Table

| Model | Setting | n | parse_success | empty_output_rate | schema_missing_rate | mean visible tokens | p95 visible tokens | overlength_rate | gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `deepseek-v4-pro` | `no_cap` | 20 | 1.00 | 0.00 | 0.00 | 413.8 | 496.0 | 0.00 | pass |
| `deepseek-v4-pro` | `cap_8192` | 20 | 0.85 | 0.15 | 0.00 | 328.1 | 460.0 | 0.00 | fail |
| `deepseek-v4-pro` | `cap_4096_diagnostic` | 20 | 1.00 | 0.00 | 0.00 | 392.8 | 464.0 | 0.00 | diagnostic only |
| `kimi-k2.6` | `no_cap` | 20 | 1.00 | 0.00 | 0.00 | 384.6 | 488.0 | 0.00 | pass |
| `kimi-k2.6` | `cap_8192` | 20 | 0.95 | 0.05 | 0.00 | 364.3 | 464.0 | 0.00 | fail |
| `kimi-k2.6` | `cap_4096_diagnostic` | 20 | 0.40 | 0.40 | 0.10 | 194.7 | 415.0 | 0.00 | fail |

`deepseek-v4-pro` 的 `cap_4096_diagnostic` 在这次 20-task audit 中通过，但此前 preflight 已观察到 4096 cap 会产生 empty output；该 setting 保留为 diagnostic，不作为主实验设置。

## Artifact

完整结果：

```text
eha-mvp/results/reports-eha-frontier-budget-audit/
```

关键文件：

- `budget_setting_decision.md`
- `budget_sensitivity_table.csv`
- `budget_setting_decision.csv`
- `predictions.jsonl`
- `frontier_main_scored_predictions.csv`
- `failure_cases_frontier.jsonl`

## 对主实验的影响

主实验 profile 不变：

```text
deepseek-v4-pro: no max_completion_tokens, json_object
kimi-k2.6: no max_completion_tokens, json_schema
```

解释口径：

> 8192 cap did not pass the structured-output stability gate for the two no-cap models. We therefore keep no-cap as the provider-compatible operational setting, while reporting actual visible output lengths and overlength rates. The no-cap runs did not produce materially longer visible outputs than the capped settings, and all overlength rates were zero.
