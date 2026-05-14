# EHA Epistemic Resilience Table v1 阶段性工作报告：从检索卫生扩展到污染证据环境中的认知韧性评测

日期：2026-05-14
对象：Epistemic Hygiene Arena / Epistemic Resilience Table v1
状态：阶段性研究报告，依据当前仓库的本地实验输出、审计清单、测试结果与报告包生成

## 摘要

本报告总结当前阶段的 EHA 工作结果。与此前 Matrix v1.x 阶段主要围绕 RAG 检索卫生、hidden-primary failure 和 prompt citation discipline 展开不同，本阶段把研究对象重新界定为污染证据环境中的 LLM epistemic resilience：模型是否能在可见材料包含伪共识、陈旧证据、生成式传闻、被埋没的一手证据或直接矛盾时，维持正确判断、干净证据使用和有纪律的不确定性处理。

本阶段的主要产物是 `eha-mvp` 下的 Epistemic Resilience Table v1 实现与结果包。新增或修改的核心 artifact 包括 `eha/epistemic_resilience.py`、`eha/epistemic_resilience_audit.py`、`tests/test_epistemic_resilience.py`、`data/epistemic-resilience-v1/`、`results/reports-epistemic-resilience-v1/` 以及启发式对照报告 `results/reports-epistemic-resilience-v1-heuristic/`。任务集共 100 条，按三类任务族组织：40 条 fixed evidence packet judgment、40 条 next-evidence selection、20 条 active verification；五类证据条件 clean、conflicting_evidence、false_consensus、buried_primary、generated_lore 各 20 条。

最终 API 结果包包含 624 条预测：`openai/gpt-4o-mini`、`openai/gpt-5-mini`、`openai/gpt-5.4-mini` 各完成 100 个任务 x 2 个 prompt 条件，`openai/gpt-5.5` 完成 12 任务 family-and-condition-stratified 小样本 x 2 个 prompt 条件。两个 prompt 条件分别是 `standard_answer` 与 `epistemic_hygiene_instruction`。成本报告显示 `aborted=false`，总 `spent_usd=2.800352`；最终 artifact audit 通过任务清单、预测数量、表格行数、成本报告、pytest 与 compileall 检查。

阶段性结果显示，Epistemic Resilience Table v1 能把“答案是否正确”与“证据是否干净”“是否知道何时弃答”“是否主动寻找一手或反证证据”分离出来。`openai/gpt-4o-mini` 在完整表上的整体 row-level epistemic escape 为 0.805，`openai/gpt-5.4-mini` 为 0.530，`openai/gpt-5-mini` 为 0.395；`openai/gpt-5.5` 小样本为 0.792，但该结果只覆盖 24 条预测，不能与完整 100 任务运行直接等量比较。按 family 平均的主表中，`openai/gpt-4o-mini + standard_answer` 的 avg epistemic escape 为 0.792，`openai/gpt-5.5 + epistemic_hygiene_instruction` 小样本为 0.833。

本阶段最重要的解释不是“某个模型绝对更强”，而是评测框架已经能定位不同失败机制。`openai/gpt-5-mini` 的主要 caveat 是结构化输出 parse 成功率低：完整 200 条记录中 parse success 约为 0.380，其中 hygiene prompt 为 0.340、standard prompt 为 0.420；这些失败按 benchmark 规则计为失败记录。`openai/gpt-5.4-mini` 的 parse success 为 1.000，belief correctness 也达到 0.960，但 evidence cleanliness 只有 0.470，说明它更常给出方向正确但证据字段不干净的答案。`openai/gpt-4o-mini` 的 parse success 为 1.000，belief correctness 为 0.920，evidence cleanliness 为 0.950，表现更均衡。

因此，本阶段已经足以支持一个比早期 RAG 结论更宽、也更审慎的论文主张：检索系统不是简单地给模型补充事实，而是在构造模型可见的证据环境；LLM 的事实可靠性应被评估为对污染证据环境的认知韧性，包括判断、证据选择、不确定性纪律和主动验证动作。当前证据仍来自合成 mini-web，不应外推为开放 web 或生产 RAG 系统的安全结论；正式论文还需要外部文献、人工审计和更稳健的真实任务对照。

## 1. 读者关切与研究问题

本报告面向两类读者。第一类是研究 RAG factuality、provenance reasoning、hallucination benchmark、信息污染和 agent evaluation 的研究者；他们关心 EHA 是否能提出比“检索到一手证据会更好”更有解释力的评测对象。第二类是构建检索增强系统、事实核查 agent 或企业知识库 agent 的工程实践者；他们关心系统失败究竟来自模型判断、证据供应、证据字段纪律、结构化输出稳定性，还是主动验证策略不足。

当前阶段回答五个问题：

1. EHA 是否已经从 RAG retrieval hygiene benchmark 扩展为 epistemic resilience benchmark？
2. 新表是否有明确的任务族、证据条件、评分定义和可复现 artifact？
3. 不同模型在 belief correctness、evidence cleanliness、uncertainty discipline 和 active verification 上暴露出什么不同失败模式？
4. `epistemic_hygiene_instruction` 是否稳定优于 `standard_answer`？
5. 当前结果可以支持怎样的论文主张，又必须在哪些地方保持限定？

本报告的角色是阶段性研究备忘与论文写作材料，不是最终论文定稿，也不是对真实开放互联网事实核查能力的外部验证。

## 2. 本阶段工作范围与 artifact

本阶段完成了从问题重构、任务生成、API 运行、评分汇总到 artifact audit 的闭环。核心输出如下：

| 工作项 | Artifact | 当前状态 |
| --- | --- | --- |
| Epistemic resilience 任务构造 | `data/epistemic-resilience-v1/tasks.jsonl` 与 `manifest.json` | 100 任务已生成，family 与 condition 平衡 |
| 运行与评分逻辑 | `eha/epistemic_resilience.py` | 包含 prepare、run、report CLI，评分包括 epistemic_escape 与分项指标 |
| Artifact 审计 | `eha/epistemic_resilience_audit.py` | 检查任务数、预测数、表格结构、成本、测试和 compileall |
| 结果报告包 | `results/reports-epistemic-resilience-v1/` | 包含 summary、main table、by-family、by-condition、scored rows、cost report 与 audit manifest |
| 启发式对照 | `results/reports-epistemic-resilience-v1-heuristic/` | 用于 smoke test 与 plumbing 验证，不作为模型能力主结论 |
| 重构说明 | `results/reports-epistemic-resilience-v1/epistemic_resilience_reframe.md` | 明确把 RAG 改写为 evidence environment construction 的案例 |
| Prompt-to-artifact 对照 | `results/reports-epistemic-resilience-v1/prompt_to_artifact_checklist.md` | 逐项记录需求与 artifact 对应关系 |
| 测试 | `tests/test_epistemic_resilience.py` | 覆盖任务分布、gpt-5.5 分层小样本、评分逻辑 |

最终审计输出 `artifact_audit.json` 显示所有检查通过：任务数为 100，预测数为 624，`main_table.csv` 为 8 行，`by_family.csv` 为 24 行，`by_condition.csv` 为 40 行，`scored_predictions.csv` 为 624 行；`uv run pytest` 通过 45 个测试，`uv run python -m compileall eha` 通过。

## 3. 评测设计：从“答案正确”到“认知逃逸”

Epistemic Resilience Table v1 的中心指标是 `epistemic_escape`。它不是普通 accuracy，而是按任务族定义的复合成功条件。

对 fixed evidence packet judgment，escape 至少要求：

1. `belief_correctness`：模型给出的 verdict 与 gold verdict 一致。
2. `evidence_cleanliness`：supporting evidence 不依赖污染、陈旧、生成式传闻或错误支持材料。
3. `uncertainty_discipline`：证据不足时应输出 insufficient；证据支持确定结论时不应不必要弃答。

对 evidence selection，escape 更偏向 source-oriented：模型必须选择高价值证据、避免重复 upstream root，并避免选择 generated lore。对 active verification，escape 还要求合适的下一步动作，例如寻找 primary source、检查反证、比较版本或追踪 generated lore 的来源。

这一设计把早期 Matrix 系列中的 RAG 机制结果保留为一个更大框架中的案例：retrieval 并不只是召回 facts，而是在构造模型进行判断时可见的 evidence environment。模型的失败可能发生在不同层面：证据根本不可见、证据可见但被污染材料捕获、答案方向正确但引用字段不合格、模型不能稳定产生结构化输出，或模型没有采取必要的主动验证动作。

## 4. 数据、运行与成本

任务集来自 Matrix v1 数据的再组织，而不是引入真实 web 数据。`manifest.json` 记录：

| 维度 | 数量 |
| --- | ---: |
| 总任务 | 100 |
| `packet_judgment` | 40 |
| `evidence_selection` | 40 |
| `active_verification` | 20 |
| `clean` | 20 |
| `conflicting_evidence` | 20 |
| `false_consensus` | 20 |
| `buried_primary` | 20 |
| `generated_lore` | 20 |

最终 API 运行覆盖四个模型和两个 prompt 条件：

| 模型 | 覆盖范围 |
| --- | --- |
| `openai/gpt-4o-mini` | 100 任务 x 2 prompts |
| `openai/gpt-5-mini` | 100 任务 x 2 prompts |
| `openai/gpt-5.4-mini` | 100 任务 x 2 prompts |
| `openai/gpt-5.5` | 12-task family-and-condition-stratified sample x 2 prompts |

`openai/gpt-5.5` 的小样本覆盖三个任务族，并按 condition 分层：clean 与 conflicting_evidence 各 3 个任务，false_consensus、buried_primary、generated_lore 各 2 个任务。它适合做 sanity sample 或写作参考，不适合与 100 任务全表结果直接比较。

成本报告显示总 `spent_usd=2.800352`，其中最终记录成本 `record_cost_usd=2.130942`；报告中还保留了被 superseded 的前序 sample 成本。预算状态为 `aborted=false`。

## 5. 主结果：模型表现与 prompt 条件

按 family 平均的主表如下：

| Model | Prompt | n | Packet judgment | Evidence selection | Active verification | Avg epistemic escape |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | `standard_answer` | 100 | 0.925 | 0.800 | 0.650 | 0.792 |
| `openai/gpt-4o-mini` | `epistemic_hygiene_instruction` | 100 | 0.925 | 0.800 | 0.500 | 0.742 |
| `openai/gpt-5-mini` | `standard_answer` | 100 | 0.650 | 0.375 | 0.100 | 0.375 |
| `openai/gpt-5-mini` | `epistemic_hygiene_instruction` | 100 | 0.475 | 0.325 | 0.200 | 0.333 |
| `openai/gpt-5.4-mini` | `standard_answer` | 100 | 0.400 | 0.775 | 0.100 | 0.425 |
| `openai/gpt-5.4-mini` | `epistemic_hygiene_instruction` | 100 | 0.625 | 0.700 | 0.200 | 0.508 |
| `openai/gpt-5.5` | `standard_answer` | 12 | 0.750 | 0.750 | 0.750 | 0.750 |
| `openai/gpt-5.5` | `epistemic_hygiene_instruction` | 12 | 1.000 | 0.750 | 0.750 | 0.833 |

这张表支持三个谨慎判断。

第一，`epistemic_hygiene_instruction` 不是稳定的全局改进。它改善了 `openai/gpt-5.4-mini` 的 avg epistemic escape，从 0.425 到 0.508；也改善了 `openai/gpt-5.5` 小样本，从 0.750 到 0.833。但在 `openai/gpt-4o-mini` 和 `openai/gpt-5-mini` 上，hygiene prompt 的 family-average escape 低于 standard prompt。论文中不应把 hygiene instruction 写成 universal prompt fix，而应写成与模型、任务族和输出约束交互的 intervention。

第二，active verification 是当前最困难的任务族。`openai/gpt-4o-mini` 的 active verification escape 为 0.650 或 0.500；`openai/gpt-5.4-mini` 为 0.100 或 0.200；`openai/gpt-5-mini` 为 0.100 或 0.200。该结果提示，要求模型选择验证动作时，单纯给出 verdict 和引用证据不足以代表 epistemic resilience。

第三，gpt-5.5 小样本给出高分但样本量太小。它在 packet judgment hygiene 条件下达到 1.000，在 active verification 与 evidence selection 上均为 0.750，但每个 family 只有 4 条任务。报告和论文只能把它写成 stratified sample evidence，而非完整模型排名。

## 6. 失败机制：parse failure、证据污染与 generated lore

把主表拆开后，可以看到不同模型的失败机制并不相同。

| 模型 | 记录数 | Row-level escape | Parse success | Belief correctness | Evidence cleanliness |
| --- | ---: | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | 200 | 0.805 | 1.000 | 0.920 | 0.950 |
| `openai/gpt-5-mini` | 200 | 0.395 | 0.380 | 0.540 | 0.965 |
| `openai/gpt-5.4-mini` | 200 | 0.530 | 1.000 | 0.960 | 0.470 |
| `openai/gpt-5.5` | 24 | 0.792 | 1.000 | 0.917 | 0.917 |

`openai/gpt-5-mini` 的结果主要受结构化输出失败影响。完整 200 条记录中，parse success 约为 0.380；hygiene 条件为 0.340，standard 条件为 0.420。由于 benchmark 把 parse failure 计为失败记录，该模型的较低 escape 不应被直接解释为“证据推理更差”。更准确的说法是：在当前 endpoint、schema 与运行设置下，它未能稳定返回可评分的结构化输出。

`openai/gpt-5.4-mini` 暴露出另一类问题。它的 parse success 与 belief correctness 都高，但 evidence cleanliness 低，尤其在 false_consensus、buried_primary 和 generated_lore 条件下明显。按 condition 聚合，`openai/gpt-5.4-mini` 的 evidence cleanliness 在 buried_primary 为 0.250，在 false_consensus 为 0.275，在 generated_lore 为 0.325。这说明它经常判断方向正确，却仍把污染或不合格材料放进证据字段；这正是 epistemic resilience 指标相对于普通 accuracy 的价值。

`generated_lore` 是全表中最稳定的困难条件之一。`openai/gpt-4o-mini` 在 generated_lore 上的 escape 为 0.400，`openai/gpt-5.4-mini` 为 0.225，`openai/gpt-5-mini` 为 0.400，`openai/gpt-5.5` 小样本为 0.500。即使 belief correctness 常常较高，generated-lore avoidance、source tracing 或证据选择指标仍会拉低 escape。后续论文可以把它写成“答案正确不足以证明模型抵抗了生成式传闻的证据捕获”。

## 7. 与前序 Matrix 结果的关系

本阶段不是推翻 Matrix v1.x，而是把它重新安放在更宽的研究问题中。Matrix v1.2 和 v1.3 已经表明，L4 hidden-primary 失败首先是 evidence supply chain failure：naive 或 careful BM25 没有把 decisive primary evidence 放进上下文时，更谨慎 prompt 也不能从缺失证据中恢复判断；当 primary evidence 被 `primary_preserve` 或 `hygienic_combo` 放回上下文后，escape 恢复。

Epistemic Resilience Table v1 则把这个机制推广为一个评测框架：RAG 是 evidence environment construction 的一个例子，而不是唯一对象。新的任务族覆盖 fixed packet judgment、next-evidence selection 和 active verification，使研究问题从“检索器是否召回正确文档”转向“模型在污染证据环境中能否维持判断、证据与行动纪律”。

这使论文主张可以更清晰地收窄为：

> 在污染信息生态中，LLM factual reliability 不应只按最终答案评价，也应按其对证据环境的认知韧性评价。检索层、证据包、prompt 和结构化输出 schema 共同构造了模型可见的证据环境；模型可能在答案、证据、弃答或验证动作任一层失败。

这个主张比“RAG 中一手证据很重要”更不平凡，也比“某个 prompt 能解决污染问题”更谨慎。

## 8. 论文写作建议

当前阶段建议把论文写成“epistemic resilience benchmark”而非单纯 RAG benchmark。可能的论文结构如下：

1. Introduction：从污染证据环境中的 factual reliability 问题进入，说明为什么 answer accuracy 不足。
2. Conceptual frame：定义 epistemic resilience、evidence environment、evidential capture 与 epistemic escape。
3. Benchmark design：介绍三类任务族、五类证据条件、合成 mini-web、gold labels 与污染标签。
4. Metrics：解释 belief correctness、evidence cleanliness、uncertainty discipline、source selection 和 active verification metrics。
5. Main results：报告主表、family breakdown、condition breakdown 与 parse-success caveat。
6. Mechanism analysis：把 Matrix L4 hidden-primary 写成 evidence environment construction 的案例。
7. Prompt and schema caveats：讨论 hygiene instruction 的非单调效果、structured-output failures 与模型特异性。
8. Limitations：说明合成数据、自动评分、样本量、缺乏外部文献与真实任务验证的边界。
9. Conclusion：回到主张，即事实可靠性评测应同时看答案、证据和验证行动。

中心图表建议包括三类：第一，主表或模型 x prompt 的 family-average escape；第二，generated_lore 与 active_verification 的 condition/family failure profile；第三，Matrix L4 primary-in-context 与 escape recovery 的机制图，用作 RAG case study。

## 9. 局限与替代解释

第一，当前数据仍是合成 mini-web。合成数据的优势是 gold verdict、污染标签、source dependency 和任务条件可审计；限制是不能直接代表开放 web、企业知识库、新闻检索、法律医学场景或自适应攻击者环境。

第二，自动评分本身需要审计。`epistemic_escape` 的价值在于分解答案和证据质量，但它也依赖 gold labels、污染标签、doc_id 归一化和 schema 字段解释。正式论文若要提出更广泛结论，应抽样进行人工审计，确认 scorer 没有系统性奖励或惩罚某种表达模式。

第三，`openai/gpt-5-mini` 的结果混合了模型行为与结构化输出适配问题。当前运行记录显示 parse success 低，不能把低 escape 简化为证据推理能力差。后续应检查 endpoint、response_format、schema 严格度、max_output_tokens 和重试策略。

第四，`openai/gpt-5.5` 只运行了 12 个任务的小样本。它可以显示较强候选表现，但不能作为全表排名或置信区间证据。若论文需要比较 gpt-5.5，应扩展到完整 100 任务，或明确把它放在 exploratory sample 小节。

第五，hygiene prompt 的结果不是单调改善。它可能让某些模型更谨慎，也可能降低 active verification 或 evidence selection 的 escape。后续应做错误案例分析，而不是只比较 aggregate。

第六，当前报告没有引入外部文献。正式论文需要人工核对 RAG factuality、retrieval robustness、misinformation、provenance、hallucination evaluation、epistemic vigilance 和 synthetic benchmark 相关文献。未经核对的外部主张应保留 `[citation needed]`，不能由本地实验自动推出。

## 10. 下一步建议

下一阶段不宜盲目扩展新 benchmark，而应先把当前表的解释性打磨清楚。

1. 对 `openai/gpt-5-mini` 做结构化输出复核，区分 schema/endpoint 失败与真实任务失败。
2. 对 `openai/gpt-5.4-mini` 做 evidence cleanliness 错误案例审计，尤其是 false_consensus、buried_primary 和 generated_lore。
3. 抽样人工审计 `scored_predictions.csv`，确认自动 scorer 对 supporting evidence、selected_doc_ids 和 actions 的判定可信。
4. 若预算允许，把 `openai/gpt-5.5` 从 12-task stratified sample 扩展到完整 100 任务。
5. 把 Matrix L4 primary recovery 写成 case study，而不是继续增加并行机制。
6. 补 related work，所有引用先建立可核对笔记，再进入正文。
7. 为论文固定一张主表、一张机制图和一张 failure-profile 图，避免结果展示继续膨胀。

## 11. 可复现信息

本报告依据以下仓库内材料：

- `eha-mvp/data/epistemic-resilience-v1/manifest.json`
- `eha-mvp/data/epistemic-resilience-v1/tasks.jsonl`
- `eha-mvp/eha/epistemic_resilience.py`
- `eha-mvp/eha/epistemic_resilience_audit.py`
- `eha-mvp/tests/test_epistemic_resilience.py`
- `eha-mvp/results/runs/epistemic-resilience-v1-api-final/run_manifest.json`
- `eha-mvp/results/reports-epistemic-resilience-v1/summary.md`
- `eha-mvp/results/reports-epistemic-resilience-v1/main_table.csv`
- `eha-mvp/results/reports-epistemic-resilience-v1/by_family.csv`
- `eha-mvp/results/reports-epistemic-resilience-v1/by_condition.csv`
- `eha-mvp/results/reports-epistemic-resilience-v1/scored_predictions.csv`
- `eha-mvp/results/reports-epistemic-resilience-v1/cost_report.json`
- `eha-mvp/results/reports-epistemic-resilience-v1/audit_manifest.json`
- `eha-mvp/results/reports-epistemic-resilience-v1/artifact_audit.json`
- `eha-mvp/results/reports-epistemic-resilience-v1/epistemic_resilience_reframe.md`
- `eha-mvp/results/reports-epistemic-resilience-v1/prompt_to_artifact_checklist.md`

已记录的核查命令：

```bash
cd eha-mvp
uv run pytest
uv run python -m compileall eha
```

核查结果：`pytest` 共 45 个测试通过，`compileall` 通过。artifact audit 记录在 `results/reports-epistemic-resilience-v1/artifact_audit.json`。

## 12. 研究伦理与 AI 辅助写作说明

本报告没有引入外部文献、真实个人数据或真实机构事实。实验对象均为 EHA 合成数据中的虚构任务与文档。报告中的数值来自当前仓库的本地实验输出、CSV 汇总、manifest、成本报告和审计记录。

本报告由 AI 助手根据本地实验材料起草，并按 academic-paper-writing 的读者、问题、证据、限制与替代解释框架组织。报告没有编造实验结果、外部引用或未运行模型结论；凡涉及外推处均以“当前阶段”“合成 mini-web”“小样本”“后续需要人工审计”等方式限定。正式论文若加入外部文献、真实系统含义或安全建议，应由作者逐项核对。
