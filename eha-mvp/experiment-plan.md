# EHA MVP 首期实验计划

依据：

- `/Users/chenmohan/gits/ficciones/epistemic-hygiene-arena-preprint.md`
- `/Users/chenmohan/Downloads/ficciones-research-0512-3.md`

## 核心命题

首期只检验一个最小但可复现实验命题：

> 在污染信息生态中，普通 top-k RAG 和朴素 citation prompt 会把坏证据包装成自信答案；要求来源独立性和 evidence graph 的策略应降低污染引用率、伪共识易感性，并改善 provenance recovery。

首期不做训练、不接真实 web、不使用外部 embedding API。

## 假设

| ID | 假设 | 主要证据 |
| --- | --- | --- |
| H1 | 普通 top-k RAG 在污染生态中更容易引用污染源并产生自信错误 | `verdict_accuracy`, `contaminated_citation_rate`, `wrong_confidence` |
| H2 | 单纯要求 citation 不等于证据卫生，可能提高污染引用 | A0 vs A1 的 `CCR` 和 `EV` |
| H3 | source-independence 和 evidence-graph prompt 能降低污染引用并改善来源追踪 | A2/A3 的 `CCR`, `IES`, `PR-F1`, `ECE` |

## 数据集

生成 60 个虚构公司调查 episode，全部围绕 `Novalis Robotics` 合成 mini-web：

| 类型 | 数量 | 目的 |
| --- | ---: | --- |
| `clean_control` | 10 | 控制组，确认任务不是纯陷阱 |
| `false_consensus` | 15 | 测重复同源材料是否被误当独立证据 |
| `citation_laundering` | 10 | 测引用链是否真的支持 claim |
| `temporal_pollution` | 10 | 测过期资料 |
| `mixed_source_corruption` | 10 | 测整体可信来源中的局部关键错误 |
| `halupedia_trap` | 5 | 测 generated lore / query-induced pollution |

每个 episode 包含 12-18 篇 agent 可见文档，以及 scorer-only 的 gold labels 和 source dependency graph。Agent 可见 schema 不包含 `truth`、`contamination`、`upstream_root`、`rank_boost` 等 gold 字段。

## 策略

| 策略 | 说明 |
| --- | --- |
| A0 `topk_rag` | 给 top-8 文档直接回答 |
| A1 `citation_prompt` | 要求输出支持证据 doc_id，但不要求独立性分析 |
| A2 `source_independence_prompt` | 要求判断同源复读、过期、原始来源和 claim-level support |
| A3 `evidence_graph_prompt` | 要求输出小型 evidence graph 和被拒绝证据 |

四种策略使用相同检索结果，只改变 prompt 和输出要求。

## 实现

项目位于 `eha-mvp/`，使用 `uv` 管理依赖：

- schema: `pydantic`
- CLI: `typer`
- terminal output: `rich`
- diagnostics: `loguru`
- retrieval: `rank-bm25`
- LLM client: official `openai` Python SDK
- tests: `pytest`

默认 heuristic backend 只用于离线 smoke test，不用于论文结论。真实模型实验使用 `--backend api`。

## 指标

首期实现这些自动评分指标：

- `verdict_accuracy`
- `evidence_validity`
- `contaminated_citation_rate`
- `independent_evidence_score`
- `provenance_recovery_f1`
- false-consensus `wrong_answer_rate` and `mean_wrong_confidence`
- 5-bin `ECE`
- Halupedia `QIPS`
- cost report

## Pilot gate

先跑 12 episode pilot。通过条件：

1. clean control 中 A0 accuracy >= 0.65。
2. false consensus 中 A0 或 A1 至少出现 3 个污染误判。
3. A2/A3 不应 trivially perfect；若 accuracy > 0.95，任务太简单。
4. 所有 strategy 的 JSON parse success >= 0.95。
5. 每个 episode 至少有一个 primary source 和一个 plausible pollutant。

当前 heuristic pilot 已通过，证明生成器和评分管线可运行；真实 OpenAI 模型运行后仍需要重新检查 gate。

## 运行命令

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv sync
uv run eha-generate --episodes 60 --seed 4242 --out-dir data/generated
uv run eha-run --data-dir data/generated --backend heuristic --pilot --out-dir results/runs/pilot
uv run eha-report --data-dir data/generated --run-dir results/runs/pilot --out-dir results/reports
uv run pytest
```

真实 LLM API 运行使用 official `openai` Python SDK，但端点和密钥固定读取 `LLM_BASE_URL` 与 `LLM_API_KEY`：

```bash
uv run eha-run \
  --data-dir data/generated \
  --backend api \
  --models gpt-5-mini,gpt-5.4-mini \
  --strategies topk_rag,citation_prompt,source_independence_prompt,evidence_graph_prompt \
  --out-dir results/runs/main
```

API runner 默认设置：

- temperature: `0`
- top-k docs: `8`
- max output tokens: `6000`, including reasoning tokens on reasoning models
- structured JSON response: `json_schema` with `json_object` fallback
- soft cap: `$100`
- hard stop before projected spend exceeds `$250`
- abort if actual spend exceeds `$300`

## 首期结论边界

可以声称：

- 已实现可控 synthetic mini-web 和信息卫生自动评分管线。
- heuristic pilot 证明任务生成、检索、评分、报告、cost guard 和 pilot gate 能端到端运行。
- 后续真实模型实验可以直接复用相同数据、检索结果、prompt 策略和评分器。

暂不声称：

- 已证明任何真实模型在 EHA 上的表现。
- 已解决 RAG poisoning。
- 已覆盖真实互联网 misinformation。
