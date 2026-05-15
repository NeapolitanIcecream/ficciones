# EHA Frontier Cohort Main Results

日期：2026-05-14 批次；主跑完成于 Asia/Shanghai 2026-05-15 02:20。

## 结论

主实验已经完成：100 tasks × 5 models × 2 prompts = 1000 calls。

最重要的运行质量结论是：全局 `empty_output = 0/1000`，`overlength_rate = 0/1000`。这支持此前判断：早期若干模型的空内容主要是短 `max_completion_tokens` 与 provider/model 预算语义交互导致，不应直接解释为模型不可用。DeepSeek/Kimi 在主跑中继续使用 no-cap profile；Kimi 200/200 parse success，DeepSeek 199/200 parse success，唯一失败不是空内容，而是一次 schema-missing。

## Model-Level Metrics

| Model | n | Operational escape | Conditional escape | Parse success | Evidence cleanliness | Verification action | Mean visible tokens | Overlength |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 200 | 0.880 | 0.880 | 1.000 | 1.000 | 0.600 | 419.090 | 0.000 |
| `deepseek-v4-pro` | 200 | 0.790 | 0.794 | 0.995 | 0.935 | 0.475 | 399.825 | 0.000 |
| `gemini-3.1-pro-preview` | 200 | 0.780 | 0.780 | 1.000 | 1.000 | 0.458 | 455.330 | 0.000 |
| `gpt-5.4` | 200 | 0.770 | 0.770 | 1.000 | 0.730 | 0.408 | 372.880 | 0.000 |
| `kimi-k2.6` | 200 | 0.790 | 0.790 | 1.000 | 0.950 | 0.450 | 404.205 | 0.000 |

Claude has the highest row-level epistemic escape in this cohort. GPT-5.4 is not parse-weak here, but its evidence-cleanliness score is lower than the other frontier models. The active-verification family remains the hardest slice across models.

## Prompt Effects

The hygiene prompt is not a universal improvement in this run.

| Model | Standard escape | Hygiene escape | Direction |
| --- | ---: | ---: | --- |
| `claude-opus-4-7` | 0.880 | 0.880 | flat |
| `deepseek-v4-pro` | 0.780 | 0.800 | slight gain, with one schema-missing row |
| `gemini-3.1-pro-preview` | 0.780 | 0.780 | flat |
| `gpt-5.4` | 0.750 | 0.790 | gain |
| `kimi-k2.6` | 0.810 | 0.770 | decline |

## Token-Budget Finding

The separate 120-call budget audit selected no-cap for both no-cap models:

| Model | Decision | Reason |
| --- | --- | --- |
| `deepseek-v4-pro` | keep `no_cap` | `cap_8192` failed the stability gate with empty output rate 0.15. |
| `kimi-k2.6` | keep `no_cap` | `cap_8192` had empty output rate 0.05, and `cap_4096_diagnostic` had parse success 0.40 with empty output rate 0.40. |

In the full main run, no-cap did not produce visible-output inflation: mean visible output was about 400 tokens for DeepSeek and 404 for Kimi, and both had `overlength_rate=0`.

## Artifacts

- Main output directory: `eha-mvp/results/reports-eha-frontier-main/`
- Main predictions: `predictions.jsonl` has 1000 rows.
- Per-call raw response artifacts: `artifacts/*/*.response.json` count is 1000.
- Main summary: `summary.md`.
- Main aggregate CSVs: `frontier_main_metrics_by_model.csv`, `frontier_main_metrics_by_family.csv`, `frontier_main_metrics_by_condition.csv`, `frontier_main_metrics_by_prompt.csv`, `operational_vs_conditional_escape.csv`.
- Budget audit directory: `eha-mvp/results/reports-eha-frontier-budget-audit/`.
- Budget decision: `budget_setting_decision.md`.
- Verification: `uv run pytest -q` passed 70 tests; `uv run python -m compileall eha` passed.
