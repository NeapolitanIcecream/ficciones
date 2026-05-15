# EHA Frontier 主实验阶段性工作报告

日期：2026-05-15

对象：Epistemic Hygiene Arena / Epistemic Resilience Table v1 / Frontier Cohort Main Run

状态：阶段性研究与工程报告；依据当前仓库内代码、实验输出、预算审计、聚合表、验证命令和已有阶段报告生成

## 摘要

本阶段工作已经从 frontier cohort 预检和主实验设施准备，推进到完整的跨 provider 主实验结果。EHA 当前主实验覆盖 100 个 Epistemic Resilience Table v1 任务、5 个 frontier 模型、2 个 prompt 条件，共 1000 次调用。主跑完成于 Asia/Shanghai 2026-05-15 02:20；本报告在 2026-05-15 重新核查本地测试与编译状态。

核心结论有四点。第一，跨 provider structured-output 运行已经具备可用的工程稳定性：1000 条预测中 `empty_output=0`，`overlength_rate=0`；除 `deepseek-v4-pro` 的 1 条 schema-missing 外，其余模型均为 200/200 parse success。第二，模型差异不应只写成 leaderboard：`claude-opus-4-7` 的 operational epistemic escape 最高，为 0.880；`deepseek-v4-pro` 与 `kimi-k2.6` 均为 0.790；`gemini-3.1-pro-preview` 为 0.780；`gpt-5.4` 为 0.770。第三，主要机制性难点仍集中在 `active_verification` 与 `generated_lore`，这支持 EHA 把答案正确、证据干净、弃答纪律和验证行动拆开评价。第四，token-budget fairness audit 支持继续让 DeepSeek 与 Kimi 使用 no-cap provider-compatible setting；实际主跑没有出现可见输出膨胀，因此 no-cap 在本阶段是稳定性需要，不是给特定模型额外表达空间。

本阶段结果已经足以支撑论文写作进入主实验分析与限制论证阶段，但还不应被写成开放网络事实核查能力的外部验证。当前证据来自合成 mini-web 和结构化评分；正式论文仍需把相关工作、人工审计和评分边界写入正文或 appendix。

## 1. 读者、研究问题与当前角色

本报告面向两类读者。第一类是研究 RAG factuality、hallucination evaluation、misinformation robustness、provenance reasoning 和 agent evaluation 的研究者；他们会关心 EHA 是否把“最终答案正确”之外的证据环境适应能力转化为可测量对象。第二类是构建检索增强系统、事实核查 agent 或企业知识库 agent 的工程实践者；他们会关心模型失败究竟来自答案判断、证据字段纪律、结构化输出、输出预算、prompt intervention，还是主动验证策略。

本阶段报告回答五个问题：

1. 当前 frontier 主实验是否已经完成，并且运行质量是否足以支撑分析？
2. 五个 frontier 模型在 epistemic escape、parse stability、证据干净程度和验证行动上表现如何？
3. `epistemic_hygiene_instruction` 是否构成稳定的全局 prompt 改进？
4. DeepSeek 与 Kimi 的 no-cap 设置是否造成预算或输出长度不公平？
5. 这些结果能支持怎样的论文主张，哪些外推仍需保留为限制？

本报告的角色是阶段性研究备忘与论文材料整理，不是最终论文，也不是外部产品评测。

## 2. 当前 artifact 范围

本阶段新增或定型的关键 artifact 如下。

| 工作项 | 主要 artifact | 当前状态 |
| --- | --- | --- |
| Frontier 主实验设施 | `eha-mvp/eha/epistemic_frontier_main.py`、`eha-epistemic-frontier-main` CLI | 已支持计划生成、主跑、resume、报告生成和预算审计 |
| 主实验结果 | `eha-mvp/results/reports-eha-frontier-main/` | 1000 条预测、1000 个 response artifact、聚合 CSV 与 summary 已生成 |
| 预算公平性审计 | `eha-mvp/results/reports-eha-frontier-budget-audit/` | 120-call sensitivity audit 完成；DeepSeek/Kimi 均保留 no-cap |
| 阶段报告 | `reports/eha-frontier-main-results-2026-05-14.md`、`reports/eha-budget-fairness-audit-results-2026-05-14.md` | 已总结主结果和预算设置决策 |
| 测试覆盖 | `eha-mvp/tests/test_epistemic_frontier_main.py` 等 | 本报告生成前 `uv run pytest -q` 通过 70 个测试；`uv run python -m compileall eha` 通过 |

相较上一阶段的 “frontier cohort preflight”，当前阶段的实质变化是：preflight 只证明 route/schema 可进入主实验；本阶段已经完成 1000-call 主实验，并生成可用于论文主表和机制分析的模型、任务族、证据条件与 prompt 聚合结果。

## 3. 方法：EHA 如何评价 epistemic resilience

EHA 当前的研究问题不是“模型能不能在普通问答中答对”，而是：

> 当可见证据环境包含伪共识、陈旧证据、生成式传闻、被埋没的一手证据或直接矛盾时，模型能否维持正确判断、干净证据使用、有纪律的不确定性处理，以及必要的主动验证行动？

Epistemic Resilience Table v1 包含 100 个任务，任务族为 `packet_judgment=40`、`evidence_selection=40`、`active_verification=20`；证据条件为 `clean`、`conflicting_evidence`、`false_consensus`、`buried_primary`、`generated_lore`，每类 20 个任务。主实验把这 100 个任务分别交给 5 个模型和 2 个 prompt 条件，因此总调用量为 1000。

核心指标 `operational_epistemic_escape` 把 parse/schema failure 计入失败，更接近“系统作为可运行评测对象时是否成功”。`conditional_epistemic_escape` 只在可解析输出上计算，更接近“模型在成功给出结构化输出后是否完成 epistemic 任务”。本阶段同时报告两者，避免把 API/结构化输出问题混同为纯推理能力问题。

主实验模型 profile 已冻结：

| Provider | Model | response format | max output setting | timeout |
| --- | --- | --- | --- | ---: |
| OpenAI | `gpt-5.4` | `json_schema` | 4096 | 180s |
| Anthropic | `claude-opus-4-7` | `json_schema` | 4096 | 180s |
| Google | `gemini-3.1-pro-preview` | `json_schema` | 4096 | 180s |
| DeepSeek | `deepseek-v4-pro` | `json_object` | omitted | 240s |
| Kimi | `kimi-k2.6` | `json_schema` | omitted | 300s |

DeepSeek 与 Kimi 的 no-cap 设置并非任意放宽，而是由 preflight 与 budget audit 共同决定的 provider-compatible operational setting。主报告同时记录实际可见输出长度、字段长度与 overlength。

## 4. 主结果：模型层面

主实验的模型层面结果如下。

| Model | n | Operational escape | Conditional escape | Parse success | Evidence cleanliness | Verification action | Mean visible tokens | Overlength |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 200 | 0.880 | 0.880 | 1.000 | 1.000 | 0.600 | 419.090 | 0.000 |
| `deepseek-v4-pro` | 200 | 0.790 | 0.794 | 0.995 | 0.935 | 0.475 | 399.825 | 0.000 |
| `gemini-3.1-pro-preview` | 200 | 0.780 | 0.780 | 1.000 | 1.000 | 0.458 | 455.330 | 0.000 |
| `gpt-5.4` | 200 | 0.770 | 0.770 | 1.000 | 0.730 | 0.408 | 372.880 | 0.000 |
| `kimi-k2.6` | 200 | 0.790 | 0.790 | 1.000 | 0.950 | 0.450 | 404.205 | 0.000 |

这张表支持三个谨慎判断。

第一，`claude-opus-4-7` 是本阶段 frontier cohort 中 row-level epistemic escape 最高的模型。它在 evidence cleanliness 上为 1.000，belief correctness 与 uncertainty discipline 均为 0.960，说明它在当前合成证据环境中既能较稳定地给出正确判断，也较少把污染材料放入结构化证据字段。

第二，`gpt-5.4` 不是 parse-weak 模型；它的 parse success 为 1.000。但它的 evidence cleanliness 为 0.730，显著低于 Claude、Gemini、Kimi 与 DeepSeek。这说明它的主要失败不是不能生成结构化输出，而是答案判断与证据字段纪律之间存在断裂：模型可以给出正确方向，却仍把不应作为支持的材料列入支持字段。

第三，DeepSeek 与 Kimi 在 no-cap 设置下没有出现输出膨胀。二者平均可见输出长度分别约为 400 与 404 tokens，低于 Gemini 的 455 tokens，且 overlength 均为 0。这支持把 no-cap 解释为稳定性配置，而非不公平的输出预算优势。

## 5. 任务族与证据条件：机制性困难在哪里

按任务族看，`packet_judgment` 与 `evidence_selection` 已经能区分不同模型的证据纪律，但真正拉开机制性差异的是 `active_verification`。

| Model | Packet judgment | Evidence selection | Active verification |
| --- | ---: | ---: | ---: |
| `claude-opus-4-7` | 1.000 | 0.800 | 0.800 |
| `deepseek-v4-pro` | 0.963 | 0.763 | 0.500 |
| `gemini-3.1-pro-preview` | 1.000 | 0.800 | 0.300 |
| `gpt-5.4` | 0.838 | 0.788 | 0.600 |
| `kimi-k2.6` | 1.000 | 0.775 | 0.400 |

`active_verification` 要求模型不仅判断当前材料，还要选择下一步应做的验证动作，例如追踪源头、寻找一手材料、比较版本或检查反证。Gemini、Kimi 与 DeepSeek 在这个切片明显弱于它们在 packet judgment 中的表现。这个结果支持 EHA 的一个核心设计选择：事实可靠性评测不能只看最终 verdict，因为“知道当前证据不足并采取正确验证行动”是另一种能力。

按证据条件看，`generated_lore` 是最稳定的困难条件之一。

| Model | Clean | Conflicting evidence | False consensus | Buried primary | Generated lore |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 1.000 | 1.000 | 1.000 | 0.800 | 0.600 |
| `deepseek-v4-pro` | 0.875 | 0.825 | 0.950 | 0.800 | 0.500 |
| `gemini-3.1-pro-preview` | 0.950 | 0.900 | 0.825 | 0.800 | 0.425 |
| `gpt-5.4` | 0.975 | 0.975 | 1.000 | 0.800 | 0.100 |
| `kimi-k2.6` | 0.925 | 0.850 | 0.850 | 0.800 | 0.525 |

`generated_lore` 的困难点不只是模型是否能答对，而是它是否能避免把生成式传闻、转述材料或缺乏来源链的文本当作干净支持。`gpt-5.4` 在该条件下 escape 仅为 0.100，主要由 evidence cleanliness 拉低；这为论文提供了一个清晰机制案例：高 belief correctness 不能自动推出高 epistemic resilience。

## 6. Prompt 影响：hygiene instruction 不是全局修复

本阶段结果继续反驳一个过强的 prompt 工程假设：`epistemic_hygiene_instruction` 不是稳定的全局改进。

| Model | Standard escape | Hygiene escape | 方向 |
| --- | ---: | ---: | --- |
| `claude-opus-4-7` | 0.880 | 0.880 | 持平 |
| `deepseek-v4-pro` | 0.780 | 0.800 | 小幅提升，但 hygiene 条件有 1 条 schema-missing |
| `gemini-3.1-pro-preview` | 0.780 | 0.780 | 持平 |
| `gpt-5.4` | 0.750 | 0.790 | 提升 |
| `kimi-k2.6` | 0.810 | 0.770 | 下降 |

因此，论文中不应把 hygiene prompt 写成 universal prompt fix。更稳妥的主张是：显式证据卫生指令会与模型、任务族、证据条件和结构化输出 schema 交互；它可能改善某些模型的证据字段纪律，也可能没有效果，甚至在某些模型上降低 row-level escape。

## 7. Token-budget fairness audit

预算公平性审计专门检查 DeepSeek 与 Kimi 的 no-cap 设置是否应该改为统一的 `cap_8192`。审计 gate 为：

```text
parse_success >= 0.95
empty_output_rate = 0
schema_missing_rate <= 0.05
```

结果如下。

| Model | Setting | n | Parse success | Empty output | Schema missing | Mean visible tokens | Gate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `deepseek-v4-pro` | `no_cap` | 20 | 1.00 | 0.00 | 0.00 | 413.8 | pass |
| `deepseek-v4-pro` | `cap_8192` | 20 | 0.85 | 0.15 | 0.00 | 328.1 | fail |
| `deepseek-v4-pro` | `cap_4096_diagnostic` | 20 | 1.00 | 0.00 | 0.00 | 392.8 | diagnostic only |
| `kimi-k2.6` | `no_cap` | 20 | 1.00 | 0.00 | 0.00 | 384.6 | pass |
| `kimi-k2.6` | `cap_8192` | 20 | 0.95 | 0.05 | 0.00 | 364.3 | fail |
| `kimi-k2.6` | `cap_4096_diagnostic` | 20 | 0.40 | 0.40 | 0.10 | 194.7 | fail |

审计结论是：DeepSeek 与 Kimi 都应继续使用 no-cap operational setting。这个决定的论证重点不是“无上限更好”，而是“固定 cap 在这些 provider/model 路由上会降低结构化输出稳定性”。主实验中的实际输出长度记录进一步降低了公平性疑虑：no-cap 模型没有产生明显更长的可见输出，也没有触发 overlength。

## 8. 对论文主张的含义

本阶段最强、最可防守的论文主张可以写成：

> 在污染证据环境中，LLM factual reliability 不应只按最终答案评价，也应按其对证据环境的认知韧性评价。EHA 显示，模型可以在结构化输出、答案方向、证据干净程度、弃答纪律和主动验证行动上呈现不同失败剖面；prompt 指令和 provider-specific invocation profile 也会改变评测的 operational validity。

这个主张比“某模型最好”更有研究价值。当前结果中，Claude 的总体 escape 最高，但 EHA 的核心贡献不是排名本身，而是把不同失败机制拆出来：`gpt-5.4` 的证据字段问题、Gemini 的 active-verification 弱项、DeepSeek 的一处 schema-missing、Kimi 的 prompt sensitivity，以及 generated-lore 条件对所有模型的持续压力。

论文主表建议包括三层：

1. model-level operational/conditional escape、parse success、evidence cleanliness、verification action；
2. family breakdown，突出 active verification；
3. condition breakdown，突出 generated lore 与 buried primary。

机制分析建议至少写两个 case study：一个关于 generated lore 的证据捕获，一个关于答案正确但 supporting evidence 不干净的结构化字段失败。这样可以避免论文退化为总分榜单。

## 9. 局限与替代解释

第一，当前任务来自合成 mini-web。合成任务的优势是 gold labels、污染标签、source dependency 和任务条件可审计；限制是不能直接代表开放互联网、企业知识库、新闻事实核查、法律医学场景或对抗性信息环境。

第二，自动评分依赖 schema 字段解释。EHA 有意惩罚把污染材料列入 `supporting_evidence` 或 `selected_doc_ids` 的输出，即使自然语言回答看起来谨慎。这是指标设计的一部分，但论文必须说明它评价的是可审计结构化证据纪律，而不只是自然语言语义质量。

第三，`active_verification` 的 scoring 需要继续人工审计。当前指标能显示模型是否选择了合适动作类别，但行动质量、目标文档选择和实际检索收益之间仍可能存在更细粒度差异。

第四，no-cap 设置虽然在本阶段没有造成输出长度膨胀，但它仍是 provider-specific operational profile。正式论文中应保留可见输出长度、overlength、cost 与 budget audit 表，以便读者判断公平性。

第五，本报告没有引入外部文献。正式论文中的 RAG factuality、provenance、misinformation robustness、hallucination evaluation、epistemic vigilance 与 synthetic benchmark 相关主张都需要人工核对文献并补充引用。

## 10. 下一步建议

下一阶段应优先做四件事。

1. 固定论文主表和三张关键图：模型层面主表、任务族分解图、证据条件分解图。
2. 从 `failure_cases_frontier.jsonl` 中抽取少量可读 case study，分别覆盖 generated lore、dirty support、active verification failure 和 schema-missing。
3. 对 active-verification 和 generated-lore 切片做人工审计抽样，确认自动评分边界。
4. 补充相关工作笔记，并把所有外部理论主张标注为可核对引用。

后续可选工作包括：把前一阶段的 80 行人工审计与本阶段 frontier 主结果对齐；在路由恢复后重跑早期 `gpt-5-mini` parse repair；将 Matrix L4 hidden-primary recovery 作为 evidence environment construction 的附录案例。

## 11. 可复现信息

本报告依据以下仓库内材料：

- `eha-mvp/results/reports-eha-frontier-main/summary.md`
- `eha-mvp/results/reports-eha-frontier-main/frontier_main_metrics_by_model.csv`
- `eha-mvp/results/reports-eha-frontier-main/frontier_main_metrics_by_family.csv`
- `eha-mvp/results/reports-eha-frontier-main/frontier_main_metrics_by_condition.csv`
- `eha-mvp/results/reports-eha-frontier-main/frontier_main_metrics_by_prompt.csv`
- `eha-mvp/results/reports-eha-frontier-main/operational_vs_conditional_escape.csv`
- `eha-mvp/results/reports-eha-frontier-main/run_manifest.json`
- `eha-mvp/results/reports-eha-frontier-main/report_manifest.json`
- `eha-mvp/results/reports-eha-frontier-main/cost_report.json`
- `eha-mvp/results/reports-eha-frontier-budget-audit/budget_sensitivity_table.csv`
- `eha-mvp/results/reports-eha-frontier-budget-audit/budget_setting_decision.md`
- `reports/eha-frontier-main-results-2026-05-14.md`
- `reports/eha-budget-fairness-audit-results-2026-05-14.md`
- `reports/eha-frontier-main-facility-2026-05-14.md`

本报告生成前已运行：

```bash
cd eha-mvp
uv run pytest -q
uv run python -m compileall eha
```

核查结果：`pytest` 共 70 个测试通过；`compileall` 通过。

## 12. 研究伦理与 AI 辅助写作说明

本报告没有引入真实个人数据、真实机构事实或外部文献断言。实验对象为 EHA 合成数据中的任务与文档。报告中的数值来自当前仓库的本地实验输出、CSV 汇总、manifest、成本报告、预算审计和验证命令。

本报告由 AI 助手根据本地实验材料起草，并按 academic-paper-writing 的读者、问题、证据、限制与替代解释框架组织。报告没有编造实验结果、外部引用或未运行模型结论；涉及外推处均以“本阶段”“当前合成任务”“provider-specific operational profile”“正式论文仍需人工审计或文献核对”等方式限定。
