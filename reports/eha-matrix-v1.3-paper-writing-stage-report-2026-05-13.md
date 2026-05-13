# EHA Matrix v1.3 阶段性工作报告：从实验扩展转入论文写作的证据环境主张

日期：2026-05-13
对象：Epistemic Hygiene Arena Matrix v1.3 paper-writing stage
状态：阶段性工作报告，依据当前仓库的本地实验输出、报告包和测试结果生成

## 摘要

本报告总结当前阶段的 EHA Matrix v1.3 工作结果。与前一阶段相比，v1.3 的目标不是继续扩展新的 benchmark、难度层级或工具 agent 体系，而是把已有 Matrix v1、v1.1 与 v1.2 的机制证据收束到论文写作：在完整 L0-L5 子集上确认 `claim_first_citation_v1_1` 与 hygiene retriever 的配合效果，稳定保留 L4 primary-recovery 机制审计，并生成以 evidence environment / evidence supply chain 为中心的论文草稿。

本轮新增的主 artifact 是 `results/reports-matrix-v1.3/` 报告包。它包含 18 行 seed-cluster CI、24 行 prompt hygiene aggregate、576 行 prompt hygiene raw rows、12 行 L4 primary recovery aggregate、288 行 L4 audit raw rows、`manuscript_draft.md`、`prompt_to_artifact_checklist.md`、`audit_manifest.json` 与 `cost_report.json`。新增 API 运行只覆盖一个小型确认实验：`openai/gpt-4o-mini` 在 Matrix v1 的 144 个任务上，用 `claim_first_citation_v1_1` 分别搭配 `primary_preserve` 和 `hygienic_combo`，共 288 条新预测。成本报告显示 `aborted=false`，`spent_usd=0.084495`。

阶段性结论可以概括为：当前工作已经足以把论文主张从“更强模型是否更可靠”转向“检索构造的证据环境是否可靠”。在多种子 L4 hidden-primary 条件下，`naive_bm25` 对 `openai/gpt-4o-mini` 与 `openai/gpt-5.4-mini` 的 escape rate 均为 0.000，seed-cluster CI 均为 0.000-0.000；L4 primary-recovery audit 进一步显示，`naive_bm25` 与 `careful_bm25` 的 `primary_in_context` 均为 0.000。相反，`primary_preserve` 与 `hygienic_combo` 把 primary evidence 放回上下文后，L4 escape 恢复到 0.917-1.000 区间，且 `primary_in_context=1.000`。

v1.3 的新增确认实验说明，严格的 claim-first citation prompt 能在 hygiene retriever 已经提供合格证据时改善证据输出纪律。`claim_first_citation_v1_1 + hygienic_combo` 在 L0-L5 全部达到 escape rate 1.000；`claim_first_citation_v1_1 + primary_preserve` 在 L0-L4 达到 1.000，在 L5 为 0.958。两个 hygiene 策略下，v1.1 prompt 的 contaminated citation rate 均降至 0.000，L0-L2 的 over-abstention rate 均为 0.000。因此，本轮结果支持的不是 prompt-only 解决方案，而是更窄、更可辩护的论文主张：prompt 改善 evidence discipline，但 hidden-primary 失败需要 retrieval-layer evidence recovery 才能解决。

## 1. 读者关切与研究问题

本阶段报告面向两类读者。第一类是研究 RAG factuality、信息污染、provenance reasoning 和 hallucination benchmark 的研究者；他们关心 EHA Matrix 是否不仅报告分数差异，还能解释失败机制。第二类是构建检索增强系统、企业知识库 agent 或事实核查工具的工程实践者；他们关心在有限预算下，应该优先改模型、改 prompt，还是修复检索证据供应链。

当前阶段回答四个问题：

1. Matrix 系列是否已经从实验扩展阶段进入论文写作阶段？
2. `claim_first_citation_v1_1` 在完整 L0-L5 hygiene 条件下是否稳定改善证据输出纪律？
3. L4 hidden-primary 的核心失败是否仍应被写成 evidence availability failure，而不是单纯 generator reasoning failure？
4. 论文主张应该如何收窄，避免把合成 mini-web 结果过度外推为生产系统安全结论？

本报告的角色是阶段性研究报告和论文写作备忘，不是最终论文定稿。

## 2. 本阶段工作范围

v1.3 延续 `prompt_to_artifact_checklist.md` 的约束：进入 manuscript work，只做小型确认实验，不打开新的 benchmark 扩展。实际输出符合这一约束。

| 工作项 | 本阶段 artifact | 说明 |
| --- | --- | --- |
| 完整 L0-L5 prompt+hygiene sweep | `prompt_hygiene_preflight.csv` 与 raw rows | 比较 `claim_first_citation_v1` 与 `claim_first_citation_v1_1`，覆盖 L0-L5、两种 hygiene strategy |
| L4 primary-recovery 机制表 | `l4_primary_recovery_audit.csv` | 固化 `primary_in_context`、`primary_cited`、`primary_ignored` 与 context rank |
| 多种子稳健性证据 | `multiseed_cluster_ci.csv` | 保留 v1.1 三 seed 复现的 seed-cluster CI |
| 论文草稿骨架 | `manuscript_draft.md` | 给出 abstract draft、reader problem、thesis、contributions、central figure 和 section plan |
| 可审计清单 | `audit_manifest.json` | 记录输入目录、输出行数和成本摘要 |
| 成本记录 | `cost_report.json` | 记录新增 API 成本，显示未触发预算中止 |
| 测试与编译检查 | `tests/test_matrix_paper_pack.py`、`compileall` | 当前运行通过 4 个相关测试与 `python -m compileall eha` |

本阶段还包含一个小的报告器修订：`aggregate_prompt_hygiene` 改用带 CI 的汇总路径，并在 prompt hygiene aggregate 中纳入 `over_abstention_rate`。对应测试补充了该字段存在性的检查。这一修改对论文写作重要，因为 v1.1 prompt 如果只是提高 escape，却以过度弃答为代价，就不能被写成 evidence discipline 的净收益。

## 3. 数据与方法概述

本轮新增确认实验使用 Matrix v1 数据集，而不是生成新的任务分布。实验覆盖 144 个任务、6 个难度层级、2 个 hygiene 检索策略和一个模型：

| 维度 | 设置 |
| --- | --- |
| 数据 | Matrix v1，L0-L5，共 144 个任务 |
| 模型 | `openai/gpt-4o-mini` |
| Prompt | `claim_first_citation_v1_1`；并与既有 `claim_first_citation_v1` baseline 对照 |
| 检索策略 | `primary_preserve`、`hygienic_combo` |
| 新增预测 | 288 条 |
| 对照 raw rows | 576 行，包含 baseline prompt 与 v1.1 prompt |
| 成本 | `spent_usd=0.084495`，`aborted=false` |

核心指标仍然是 `escape_rate`。它不是普通 accuracy，而是一个复合指标：回答必须 claim verdict 正确，supporting evidence 必须干净，decisive verdict 必须给出必要支持证据，并且在 generated-lore 条件下不能过度断言。v1.3 额外强调 `over_abstention_rate`，用来检查更严格 prompt 是否通过不必要弃答来“买”高分。

L4 primary recovery audit 不新增 API 调用，而是复算现有 Matrix v1 主运行。它用于回答一个机制问题：hidden-primary 失败发生在模型看到 primary evidence 后忽略它，还是检索层根本没有把 primary evidence 放进上下文。

## 4. Prompt v1.1 的完整 L0-L5 确认结果

按 prompt 与 strategy 汇总后，v1.3 的主要结果如下。每个单元覆盖 144 条 aggregate-weighted predictions。

| Prompt | Strategy | Escape | Claim accuracy | CCR | Required support | Clean support | Over-abstention |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `claim_first_citation_v1` | `hygienic_combo` | 0.854 | 0.993 | 0.028 | 0.882 | 0.972 | 0.000 |
| `claim_first_citation_v1_1` | `hygienic_combo` | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| `claim_first_citation_v1` | `primary_preserve` | 0.882 | 1.000 | 0.017 | 0.903 | 0.979 | 0.000 |
| `claim_first_citation_v1_1` | `primary_preserve` | 0.993 | 0.993 | 0.000 | 0.993 | 1.000 | 0.000 |

这个结果说明，v1.1 prompt 的收益主要在证据纪律，而不只是 claim direction。Baseline prompt 在两个 hygiene strategy 下已经有很高的 claim accuracy，但 escape 仍被 required support、clean support 或 L5 引用纪律拖低。v1.1 prompt 把 `hygienic_combo` 的 escape 从 0.854 提升到 1.000，把 `primary_preserve` 的 escape 从 0.882 提升到 0.993，并把两个策略下的 contaminated citation rate 都降到 0.000。

更关键的是，v1.1 没有在较容易任务上引入明显过度弃答。L0-L2 中，`claim_first_citation_v1_1` 搭配 `hygienic_combo` 和 `primary_preserve` 的 `over_abstention_rate` 均为 0.000，且各层 escape 都是 1.000。这使论文可以更有把握地说：在 hygiene retriever 提供足够证据时，v1.1 prompt 改善的是 support discipline，而不是通过更多 `insufficient` 回避风险。

但这个结果必须限定解释。v1.1 prompt 的成功发生在 `primary_preserve` 与 `hygienic_combo` 已经提供较好 evidence environment 的条件下。它不证明 prompt 可以从缺失上下文中恢复 primary evidence，也不推翻前序 careful BM25 结果。

## 5. L4 primary recovery：证据缺席而非单纯推理失败

L4 hidden-primary 是当前论文最强的机制证据。多种子结果显示，在 L4 上，`naive_bm25` 对 `openai/gpt-4o-mini` 与 `openai/gpt-5.4-mini` 的 escape rate 均为 0.000，seed-cluster CI 均为 0.000-0.000，contaminated citation rate 均为 1.000。模型升级没有解决 primary evidence 被挤出上下文的问题。

L4 primary recovery audit 把这个现象进一步拆开：

| 条件 | Primary in context | Escape | 机制解释 |
| --- | ---: | ---: | --- |
| `naive_bm25` | 0.000 | 0.000 | primary evidence 没有进入上下文 |
| `careful_bm25` | 0.000 | 0.000 | 更谨慎 prompt 不能恢复缺失证据 |
| `primary_preserve` | 1.000 | 0.958-1.000 | primary evidence 被放回上下文，answer 恢复 |
| `hygienic_combo` | 1.000 | 0.917-1.000 | primary evidence 被放回上下文，并抑制污染材料 |

这个审计支持一个比“模型不会推理”更准确的因果解释：L4 失败首先发生在证据供应链。模型不能引用、比较或基于一个没有进入上下文的 primary source 作答。只要 primary evidence 被放到上下文第一位，三个模型的 claim accuracy 均恢复到 1.000，escape 也恢复到 0.917-1.000。

这并不意味着生成模型能力不重要。模型能力仍可能影响 JSON 稳定性、L5 generated-lore overclaim、abstention 与证据选择。但在当前 L4 hidden-primary 机制中，关键瓶颈是 evidence availability，而不是模型看到证据后的系统性误读。

## 6. 论文写作状态

`manuscript_draft.md` 已经把论文主张整理为以下结构：

1. 题名方向：Evidence Environments: Evaluating Retrieval Hygiene Under Polluted Information Ecosystems。
2. Abstract draft：强调 RAG 可靠性不仅是 generator 属性，也是 retrieval 构造的 evidence environment 属性。
3. Reader problem：区分 evidence discipline failure 与 evidence availability failure。
4. Thesis：LLM factual reliability in RAG systems is partly an evidence-supply-chain problem。
5. Contributions：包括 EHA Matrix、复合 escape 指标、多种子 CI、L4 mechanism audit 和 prompt+hygiene confirmation sweep。
6. Central figure：建议以 L4 hidden-primary 为主图，展示 `primary_in_context` 与 `escape_rate` 的同步恢复。
7. Section plan：Introduction、Related Work、Benchmark、Methods、Main Results、L4 Primary Recovery、Prompt Analysis、Robustness and Limits、Conclusion。
8. AI-use disclosure draft：标注实验编排、报告生成和草稿写作受到 AI 助手辅助，但外部文献与最终判断需作者负责。

这意味着当前阶段已经从“继续找新现象”转入“把最强机制证据写清楚”的阶段。下一步写作不应继续扩大实验面，而应补齐 related work、固定主表和主图、对 limitation 做严格表述。

## 7. 当前应坚持的论文主张

最稳妥的中心主张是：

> 在污染信息生态中，RAG 系统的事实可靠性不仅取决于生成模型能力，也取决于检索层构造的证据环境。EHA Matrix 的 L4 hidden-primary 机制显示，当 primary evidence 被污染复读或弱证据挤出上下文时，更强模型和更谨慎 prompt 都不能可靠恢复；只有 retrieval-layer primary preservation 和信息卫生机制把决定性证据放回上下文后，escape 才恢复。

这个主张比“模型规模不重要”更准确，也比“hygienic retrieval 已经解决 RAG 污染”更谨慎。它只承诺当前实验能支持的机制判断：retrieval 决定模型可见证据；当证据缺席时，prompt 无法补回事实依据；当证据存在时，更严格 prompt 可以提高 citation 和 support discipline。

论文中应避免以下过强写法：

1. 不应说 EHA Matrix 证明了真实开放 web 上的 RAG poisoning 防御有效。
2. 不应把 L3 false consensus 写成稳定主效应，因为多种子结果中 L3 naive BM25 并不总是困难。
3. 不应说 prompt v1.1 是通用防御；它依赖 hygiene retriever 已经提供合格证据。
4. 不应把 `primary_preserve` 写成生产级 primary identification 方案；v1.1 noisy metadata/source spoofing stress 已经显示，依赖可伪装元数据的 hygiene 机制会退化。
5. 不应把自动 scorer 的合成 gold label 当作外部事实性真值；正式投稿前应考虑人工审计或外部对照。

## 8. 局限与替代解释

第一，EHA Matrix 仍是合成 mini-web。它的优势是可控、可复现、有 gold graph 和污染标签；限制是不能直接代表开放 web、企业知识库或自适应攻击者环境。

第二，seed-cluster CI 只有三个 seed cluster。它比 row-level bootstrap 更适合表达复现不确定性，但 cluster 数仍少，不支持精细分布推断。

第三，L4 primary recovery audit 解释的是当前 Matrix v1 主运行中的 hidden-primary 机制，不证明所有检索失败都来自 primary 缺席。其他场景仍可能存在模型看到 primary evidence 后忽略、误读或过度弃答的失败。

第四，v1.3 的新增确认实验只使用 `openai/gpt-4o-mini`。它足以验证 prompt+hygiene 的小型写作前置问题，但不能直接外推到所有模型。

第五，metadata/source spoofing stress 已经提示，当前 hygiene 机制仍可能被不可靠元数据削弱。后续如果要提出更强系统建议，应把 primary 识别建立在内容结构、引用链一致性、时间一致性和跨文档来源关系上。

第六，本阶段没有引入外部文献。当前草稿中的 related work 仍是占位区，正式论文需要补充并人工核对 RAG factuality、hallucination benchmark、data poisoning、misinformation、provenance 与 synthetic benchmark 等文献。

## 9. 下一步建议

建议下一阶段继续写作和审计，而不是开新实验矩阵：

1. 固定论文主图：以 L4 hidden-primary 的 `primary_in_context` 与 `escape_rate` 为中心，展示证据进入上下文后 escape 恢复。
2. 固定主表：同时报告 escape、claim accuracy、contaminated citation rate、generated-lore overclaim、required support、clean support 和 L4 primary recovery 指标。
3. 补 related work：所有外部文献先做可核对笔记，再进入正文；不要用自动生成的 citation metadata。
4. 增加 scorer/gold-label audit 小节：说明合成标签如何生成、哪些指标自动评分、哪些结论需要人工复核。
5. 将 prompt v1.1 写成 hygiene retriever 的证据纪律补丁，而不是 retrieval failure 的替代方案。
6. 把 metadata spoofing stress 放进 robustness/limits，而不是弱化它；它正好限定了 primary preservation 的适用边界。
7. 在投稿前运行一次 full artifact audit，确认表格、数字、成本报告、seed 列表和论文陈述完全一致。

## 10. 可复现信息

本报告依据以下仓库内材料：

- `results/reports-matrix-v1.3/summary.md`
- `results/reports-matrix-v1.3/manuscript_draft.md`
- `results/reports-matrix-v1.3/prompt_to_artifact_checklist.md`
- `results/reports-matrix-v1.3/audit_manifest.json`
- `results/reports-matrix-v1.3/cost_report.json`
- `results/reports-matrix-v1.3/prompt_hygiene_preflight.csv`
- `results/reports-matrix-v1.3/l4_primary_recovery_audit.csv`
- `results/reports-matrix-v1.3/multiseed_cluster_ci.csv`
- `results/runs/matrix-v1.3/prompt-v1_1-hygiene-full/predictions.jsonl`
- `eha/matrix_paper_pack.py`
- `tests/test_matrix_paper_pack.py`

本轮核查命令：

```bash
cd eha-mvp
uv run pytest tests/test_matrix_paper_pack.py
uv run python -m compileall eha
```

核查结果：`tests/test_matrix_paper_pack.py` 的 4 个测试通过，`python -m compileall eha` 通过。

## 11. 研究伦理与 AI 辅助写作说明

本报告没有引入外部文献、真实个人数据或真实机构事实。实验对象均为 EHA 合成数据集中的任务、文档和评分 artifact。报告中的数值来自当前仓库的本地实验输出、CSV 汇总、manifest 与成本记录。

本报告由 AI 助手根据本地实验材料起草，并按 academic-paper-writing 的读者、问题、证据、限制和替代解释框架组织。报告没有编造实验结果、外部引用或未运行模型结论；凡涉及外推处均以“当前阶段”“合成 mini-web”“下一步建议”等方式限定。最终论文若加入外部文献、正式贡献声明或安全含义，应由作者逐项核对。
