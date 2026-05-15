# EHA 当前阶段性工作结果报告：从主实验到论文机制案例

日期：2026-05-15

对象：Epistemic Hygiene Arena / Epistemic Resilience Table v1 / Frontier Cohort Main Run 后续论文材料整理

状态：阶段性研究报告；依据当前仓库内实验输出、审计 artifact、机制案例包、模型可用性复测和既有阶段报告生成。本文不是最终论文，也不是开放网络事实核查能力声明。

## 摘要

当前阶段的工作已经从“能否稳定运行 EHA frontier 主实验”推进到“如何把主实验结果写成可防守的论文论证”。截至 2026-05-15，仓库中已经形成三类核心成果：第一，100 个 EHA epistemic-resilience 任务在 5 个 frontier 模型和 2 个 prompt 条件下完成 1000 次主实验调用，并生成模型、任务族、证据条件和 prompt 维度的聚合结果；第二，围绕 `generated_lore` 条件完成了 GPT-5.4 证据角色审计和 clarified-schema mini-rerun；第三，面向论文正文整理了机制案例包、主图数据和读者叙事草稿。

本阶段最重要的研究判断是：EHA 不应被写成普通模型排行榜。它的贡献在于显示 frontier 模型的 factual reliability 会在多个 agent-facing 层面分离：最终 verdict、结构化证据字段、弃答纪律、主动验证行动和 provider-specific 输出稳定性。尤其是 GPT-5.4 在 `generated_lore` 条件上的低分，不应被解释为“无法识别生成式传闻”。本地证据显示，它在 40/40 条 generated-lore 记录中给出正确的 `insufficient` verdict，并且 40/40 条都把污染材料列入拒绝证据；真正的失败是 36/40 条仍把污染材料放入 `supporting_evidence`。这说明问题主要发生在机器可读 evidence-role assignment，而不是自然语言层面的 belief recognition。

这组结果已经足以支撑论文进入主结果与机制分析写作阶段；但正式论文仍需要补充外部相关工作引用、人工审计说明、评分边界和 synthetic-to-real-world 外推限制。

## 1. 读者、问题与本文角色

本文面向两类读者。第一类是研究 RAG factuality、hallucination evaluation、misinformation robustness、provenance reasoning 和 agent evaluation 的研究者；他们会关心 EHA 是否只是另一个 leaderboard，还是确实揭示了不同的证据环境失败机制。第二类是构建检索增强系统、事实核查 agent 或企业知识库 agent 的工程实践者；他们关心结构化输出能否被下游系统安全消费。

本阶段要回答的问题是：

1. 目前 EHA 主实验和后续解释性审计已经完成到什么程度？
2. 当前结果支持什么论文主张，而不是只支持什么模型排名？
3. `generated_lore` 和 `active_verification` 暴露了怎样的 agent-interface 风险？
4. 哪些结论仍然只能限定在当前合成 EHA 环境和固定 schema 内？

本文的角色是阶段性研究报告和论文写作备忘。它整理当前证据、论证路径和限制，不替代最终论文正文。

## 2. 当前阶段新增与定型成果

本阶段的成果可以分为四组。

| 成果组 | 主要 artifact | 当前状态 |
| --- | --- | --- |
| Frontier 主实验 | `eha-mvp/results/reports-eha-frontier-main/` | 1000 条预测、聚合 CSV、summary、manifest 和成本报告已生成 |
| 主实验阶段报告 | `reports/eha-frontier-main-stage-report-2026-05-15.md` | 已整理模型层面、任务族、证据条件、prompt 与预算公平性结论 |
| Generated-lore 证据角色审计 | `eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/` | 已生成 role decomposition、manual audit pack、clarified-schema mini-rerun、cost report 和 checklist |
| 论文机制案例包 | `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/` | 已生成主图数据、SVG 草图、三条 generated-lore case、一条 active-verification case 和论文段落草稿 |
| 模型可用性复测 | `eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-15.json`；`reports/supported-mainstream-models-2026-05-14.md` | 已确认部分空输出由过短 `max_completion_tokens` 触发，而非模型不可用 |

这意味着当前阶段已经完成了从“运行设施”到“论文材料”的过渡。下一步重点不应是继续扩大实验规模，而应是把已有结果写成主文图表、机制 case study、validity analysis 和限制部分。

## 3. 主实验结果：不要只读成排行榜

EHA 主实验覆盖 100 个 Epistemic Resilience Table v1 任务、5 个 frontier 模型、2 个 prompt 条件，共 1000 次调用。任务族包括 `packet_judgment`、`evidence_selection` 和 `active_verification`；证据条件包括 `clean`、`conflicting_evidence`、`false_consensus`、`buried_primary` 和 `generated_lore`。

模型层面结果如下。

| Model | Operational escape | Belief correctness | Evidence cleanliness | Verification action |
| --- | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 0.880 | 0.960 | 1.000 | 0.600 |
| `deepseek-v4-pro` | 0.790 | 0.950 | 0.935 | 0.475 |
| `kimi-k2.6` | 0.790 | 0.960 | 0.950 | 0.450 |
| `gemini-3.1-pro-preview` | 0.780 | 0.960 | 1.000 | 0.458 |
| `gpt-5.4` | 0.770 | 0.960 | 0.730 | 0.408 |

如果只按 operational escape 排序，最容易得出的结论是 Claude 最高、GPT-5.4 最低。但这不是论文最有价值的主张。更重要的是，模型会在不同 epistemic layer 上失效：有些模型能给出正确 verdict，却把污染材料放进机器可读支持字段；有些模型能判断当前证据不足，却不能表达清楚下一步应采取的验证行动；prompt hygiene 对某些模型有帮助，对另一些模型持平或负向。

因此，论文主张应写成：

> 在污染证据环境中，LLM factual reliability 不能只按最终答案评价。EHA 显示，frontier 模型的最终判断、证据字段纪律、弃答纪律和主动验证行动可以分离，且这些分离会影响下游 agent 系统能否安全消费模型输出。

## 4. 机制发现一：Generated lore 是证据角色失败，不是简单 belief failure

当前最清楚的机制案例来自 `generated_lore` 条件。GPT-5.4 在该条件下的 operational escape 只有 0.100，但 belief correctness 是 1.000。这一组数字如果不拆开，容易被误写为“GPT-5.4 被 generated lore 欺骗”。本阶段审计显示，这种写法过强。

当前 schema 下的 generated-lore 分解如下。

| Model | Belief correctness | Rejected pollutant rate | Polluted supporting rate | Full escape |
| --- | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 1.000 | 1.000 | 0.000 | 0.600 |
| `gemini-3.1-pro-preview` | 1.000 | 1.000 | 0.000 | 0.425 |
| `gpt-5.4` | 1.000 | 1.000 | 0.900 | 0.100 |

对 GPT-5.4 而言，本地审计支持以下更窄也更准确的解释：

- 40/40 条 generated-lore 记录给出正确的 `insufficient` verdict。
- 40/40 条把污染材料列入 `rejected_evidence`。
- 36/40 条仍把污染材料放入 `supporting_evidence`。
- 35/40 条出现同一污染材料同时处于支持与拒绝角色的 dual-role 现象。

换句话说，模型通常知道证据不足，也知道 generated lore 或 repost chain 不可靠；失败发生在结构化字段的角色分配上。对只消费 `supporting_evidence` 的下游系统来说，这仍然是严重 failure，因为被自然语言拒绝的污染材料可能被机器重新解释为支持证据。

Clarified-schema mini-rerun 进一步支持这个解释。该 rerun 不改写主实验结果，只测试字段语义是否是 role failure 的重要诱因。字段拆分为 `clean_supporting_evidence`、`refuting_evidence`、`rejected_or_contaminated_evidence` 和 `diagnostic_evidence` 后，GPT-5.4 在同一 generated-lore 切片上的 polluted-supporting rate 从 0.900 降为 0.000，dual-role pollutant rate 从 0.875 降为 0.000，parse success 保持 1.000。

论文应采用这样的表述：

> GPT-5.4 often recognizes generated lore at the belief layer, but the current schema exposes unstable evidence-role assignment: polluted material appears in machine-readable support fields even when the prose rejects it.

不应写成：

> GPT-5.4 cannot detect generated lore.

## 5. 机制发现二：Active verification 是行动接口问题

第二个机制案例来自 `active_verification`。在 `gpt-5.4` 的 `ert_082` 案例中，模型给出了正确的 `supported` verdict，也列出了干净的一手支持证据 `eham_002_primary_a` 和 `eham_002_primary_b`。但它的 `verification_action_score` 为 0.000，因为 action target 把多个文档 ID 和污染材料打包成一串人类可读、机器难以精确执行的字符串。

这个案例说明，active verification 的失败不等同于普通答案错误。更准确地说，它测试的是模型是否能把下一步验证动作表达成 agent 系统可执行、可审计、可恢复的形式。一个模型可以知道答案，也可以引用干净证据，但仍然在行动接口上失败。

这一点应进入正文，而不应只作为 appendix 指标。EHA 的价值恰恰在于把“答对”之外的 agent-facing 能力拆出来。

## 6. Prompt hygiene 与模型可用性复测的含义

主实验显示，`epistemic_hygiene_instruction` 不是全局 prompt 修复。

| Model | Standard escape | Hygiene instruction | 方向 |
| --- | ---: | ---: | --- |
| `claude-opus-4-7` | 0.880 | 0.880 | 持平 |
| `deepseek-v4-pro` | 0.780 | 0.800 | 小幅提升 |
| `gemini-3.1-pro-preview` | 0.780 | 0.780 | 持平 |
| `gpt-5.4` | 0.750 | 0.790 | 提升 |
| `kimi-k2.6` | 0.810 | 0.770 | 下降 |

这说明证据卫生不能可靠地通过一句“请注意证据”来解决。prompt 与模型习惯、schema 字段、任务族和证据条件交互，可能改善某些模型的字段纪律，也可能没有效果，甚至降低 row-level escape。

同日完成的模型可用性复测还澄清了一个工程层面的误判风险：`gpt-5-nano`、`o3-mini`、`gemini-3-flash-preview` 和 `glm-5.1` 在 120 token cap 下仍会出现空 content 且 `finish_reason=length`，但解除 `max_completion_tokens` 后均能返回可解析 JSON。因此，后续模型选型不应把这类结果直接标为“模型不可用”；更准确的状态是“需 no-cap 或更大 cap”。这一区分对 EHA 的 operational validity 重要，因为过短输出上限可能把 provider/profile 设置问题误计为模型能力问题。

## 7. 方法边界与替代解释

第一，当前结果来自 EHA 合成 mini-web。合成环境的优势是 gold labels、污染标签、来源链和任务条件可审计；限制是不能直接代表开放互联网、企业知识库、新闻事实核查、法律医学场景或真实对抗性信息环境。

第二，自动评分依赖 schema 语义。EHA 有意把污染材料进入 `supporting_evidence` 判为失败，即使自然语言解释已经拒绝该材料。这是因为下游 agent 可能只读取结构化字段。论文必须明确：EHA 评价的是 schema-grounded evidence hygiene，而不只是自然语言回答看起来是否谨慎。

第三，clarified-schema mini-rerun 是 validity analysis，不是主实验替换分数。主实验使用冻结的 schema 和 scoring contract；clarified schema 说明字段语义会影响 role assignment，但不应被写成 retroactive correction。

第四，active-verification 指标仍需要人工审计抽样。当前分数能暴露行动表达问题，但行动质量、目标文档选择、真实检索收益之间仍可能存在更细的差异。

第五，正式论文仍需补充外部文献。本报告没有引入 RAG factuality、provenance、misinformation robustness、hallucination evaluation、epistemic vigilance 或 agent evaluation 的外部引用，因此不能把相关工作定位写成已完成。

## 8. 下一步写作建议

下一阶段应优先把当前材料转化为论文主文。

1. 固定三张主图：模型能力分解、任务族难度、证据条件分解，并把 generated lore 高亮为机制案例。
2. 将 GPT-5.4 generated-lore 案例写成正文 case study：先给低 escape，再拆 belief correctness、rejected pollutant rate 和 polluted supporting rate，最后用 clarified schema 作为 validity analysis。
3. 将 `ert_082` active-verification 案例写成第二个机制案例，说明行动表达也是 agent interface 的一部分。
4. 为正式论文补充人工核验后的相关工作引用，并把所有外推限定在当前证据支持范围内。
5. 保留模型可用性复测结论，避免把短 token cap 导致的空输出误写为模型不可用。

## 9. 主要本地材料索引

本文依据以下仓库内材料整理：

- `reports/eha-frontier-main-stage-report-2026-05-15.md`
- `reports/eha-generated-lore-role-audit-stage-report-2026-05-15.md`
- `reports/eha-frontier-reader-facing-narrative-2026-05-15.md`
- `reports/eha-gpt54-generated-lore-evidence-role-side-note-2026-05-15.md`
- `reports/eha-paper-mechanism-case-section-2026-05-15.md`
- `reports/supported-mainstream-models-2026-05-14.md`
- `eha-mvp/results/reports-eha-frontier-main/`
- `eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/`
- `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/`
- `eha-mvp/results/model-selection-empty-output-cap-vs-nocap-2026-05-15.json`

## 10. AI 辅助写作说明

本报告由 AI 助手根据当前仓库内代码、实验 artifact、CSV 汇总、阶段报告、机制案例草稿、模型可用性复测和 checklist 起草，并按读者问题、主张、证据、替代解释、限制和下一步写作任务组织。报告没有编造外部引用、真实世界事实、未运行模型结果或未生成 artifact；所有数值均来自当前本地实验输出或既有阶段报告。
