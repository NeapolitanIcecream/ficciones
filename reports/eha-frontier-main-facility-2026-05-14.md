# EHA Frontier Main Run Facility

日期：2026-05-14

## 设施状态

已准备正式主实验设施：`eha-epistemic-frontier-main`。

它支持：

- 冻结 5 个 frontier 模型 profile。
- 100 EHA tasks × 5 models × 2 prompt conditions = 1000 calls。
- 5 条模型流并行，每个模型内部串行，降低同一 provider 的限流/成功率风险。
- `resume=True`，从已有 `predictions.jsonl` 跳过已完成 `(model, task_id, prompt_condition)`。
- 每次调用独立 process timeout，避免单个上游请求卡死整轮实验。
- macOS 使用 `spawn` 子进程，避免在线程池中 `fork` 触发 Objective-C fork-safety crash。
- 每条调用写 prompt/response artifact。
- 每条调用记录可见输出长度、JSON 字段长度和 `overlength_rate`。
- transient API/timeout/empty-output 可按同一 profile 重试，默认 `max_attempts=2`。
- 不使用 LLM repair；只用 universal JSON extractor 和 schema validation。
- DeepSeek/Kimi cap-sensitivity audit 已有独立 plan/run 命令。

## 冻结模型 profile

| Provider | Model | temperature | max_completion_tokens | response_format | timeout |
| --- | --- | --- | --- | --- | --- |
| OpenAI | `gpt-5.4` | omitted | `4096` | `json_schema` | 180s |
| Anthropic | `claude-opus-4-7` | omitted | `4096` | `json_schema` | 180s |
| Google | `gemini-3.1-pro-preview` | omitted | `4096` | `json_schema` | 180s |
| DeepSeek | `deepseek-v4-pro` | omitted | omitted | `json_object` | 240s |
| Kimi | `kimi-k2.6` | omitted | omitted | `json_schema` | 300s |

DeepSeek 和 Kimi 使用 no-cap profile，是因为 preflight 已证明固定 `4096` cap 会造成 empty output。

## 正式运行命令

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
source ~/.zshrc
uv run eha-epistemic-frontier-main run \
  --out-dir results/reports-eha-frontier-main \
  --parallel-models 5 \
  --max-attempts 2
```

重新生成报告：

```bash
uv run eha-epistemic-frontier-main report \
  --run-dir results/reports-eha-frontier-main
```

生成 token-budget fairness audit 计划：

```bash
uv run eha-epistemic-frontier-main budget-plan \
  --out-dir results/reports-eha-frontier-budget-audit
```

运行 token-budget fairness audit：

```bash
uv run eha-epistemic-frontier-main budget-run \
  --out-dir results/reports-eha-frontier-budget-audit
```

只生成计划、不调用 API：

```bash
uv run eha-epistemic-frontier-main plan \
  --out-dir results/reports-eha-frontier-main
```

## 输出文件

正式 run 会生成：

- `summary.md`
- `frontier_main_metrics_by_model.csv`
- `frontier_main_metrics_by_family.csv`
- `frontier_main_metrics_by_condition.csv`
- `frontier_main_metrics_by_prompt.csv`
- `operational_vs_conditional_escape.csv`
- `failure_cases_frontier.jsonl`
- `cost_report.json`
- `predictions.jsonl`
- `run_manifest.json`
- `artifacts/`

聚合 CSV 还会包含：

- `visible_output_tokens`
- `answer_word_count`
- `evidence_assessment_word_count`
- `max_action_rationale_word_count`
- `overlength_rate`

## Smoke 验证

已跑真实 API smoke：

```text
1 EHA task × 5 models × 2 prompt conditions = 10 calls
```

结果目录：

```text
eha-mvp/results/reports-eha-frontier-main-smoke-budget-2026-05-14/
```

验证结果：

- `predictions.jsonl`：10 行。
- `frontier_main_scored_predictions.csv`：10 条记录 + header。
- `artifacts/`：10 个 response artifacts。
- 5 个模型、2 个 prompt condition 全部 `parse_success=1.0`。
- 输出长度字段已写入；smoke 中 5 个模型 `overlength_rate=0`。
- 报告文件全部生成。

## Plan artifact

正式 1000-call plan 已写入：

```text
eha-mvp/results/reports-eha-frontier-main/frontier_main_run_plan.md
eha-mvp/results/reports-eha-frontier-main/frontier_main_run_plan.json
```

plan 显示：

- `task_count=100`
- `model_count=5`
- `job_count=1000`
- `parallel_model_streams=5`
- `per_model_concurrency=1`
- `max_attempts=2`

## Token-Budget Fairness

补充说明见：

```text
reports/eha-token-budget-fairness-plan-2026-05-14.md
```

预算公平性设施包括：

- 主实验每条调用记录实际可见输出长度。
- 对 no-cap 模型 `deepseek-v4-pro`、`kimi-k2.6` 做 20-task cap-sensitivity audit。
- 比较 `no_cap`、`cap_8192`、`cap_4096_diagnostic`。
- 根据 `parse_success`、`empty_output`、`schema_missing_rate` 决定是否可把 no-cap 改为 8192 cap。

## 解释原则

主实验报告应避免只做总分 leaderboard。正式分析应比较不同 frontier 模型在污染证据环境下的失败模式，包括：

- parse stability
- evidence cleanliness
- uncertainty discipline
- prompt sensitivity
- active verification behavior
- operational vs conditional epistemic escape
