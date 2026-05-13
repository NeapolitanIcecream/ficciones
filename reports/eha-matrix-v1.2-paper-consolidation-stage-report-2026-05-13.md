# EHA Matrix v1.2 论文整合阶段实验报告：seed-cluster CI、prompt hygiene 与 L4 primary recovery 机制审计

日期：2026-05-13
对象：Epistemic Hygiene Arena Matrix v1.2 Paper Consolidation Pack
状态：阶段性实测报告，依据当前仓库的本地实验输出生成

## 摘要

本报告总结 EHA Matrix v1.2 论文整合包的阶段性结果。v1.2 不是一次新的大规模 benchmark，而是承接 Matrix v1 与 Matrix v1.1 的小型巩固工作：为多种子复现结果补充 seed-cluster 置信区间，检查 `claim_first_citation_v1.1` 在 hygiene retriever 下是否提升证据输出纪律，并对 L4 hidden-primary 失败机制做 primary recovery 审计。

本轮报告包的核心 artifact 包括 18 行多种子 cluster CI 汇总、16 行 prompt hygiene preflight 汇总、192 行 prompt preflight raw rows、12 行 L4 primary recovery audit 汇总、288 行 L4 audit raw rows，以及一份机器可读 `audit_manifest.json`。新增 API 调用只用于 prompt v1.1 + hygiene 小预检，共 96 条新预测，成本报告显示 `aborted=false`，`spent_usd=0.027908`。

阶段性主张可以概括为：EHA Matrix 的关键论点得到了更可审计的机制支持。LLM factual reliability 不只是模型能力问题，也是 evidence supply chain 问题。Matrix v1.1 的三 seed 复现显示，L4 hidden-primary 仍是 naive BM25 的稳定失败点：`openai/gpt-4o-mini` 与 `openai/gpt-5.4-mini` 在 L4 上的 naive BM25 escape rate 都是 0.000，seed-cluster CI 也是 0.000-0.000，contaminated citation rate 都是 1.000。相对地，`primary_preserve` 与 `hygienic_combo` 把 primary evidence 放回上下文后，在 L4 上恢复到 0.917-1.000 的 escape rate。

v1.2 的机制审计进一步说明，L4 不是单纯的生成模型弱点。L4 audit 中，naive/careful BM25 的 `primary_in_context` 均为 0.000；`primary_preserve` 与 `hygienic_combo` 的 `primary_in_context` 均为 1.000，且平均最佳 primary context rank 为 1.0。换言之，L4 失败的直接机制是 primary evidence 被检索层排除或挤出，而不是模型在看到 primary evidence 后仍系统性拒绝它。

Prompt v1.1 的小预检也给出一个更细的边界。`claim_first_citation_v1.1` 与 hygiene retriever 结合后，整体上提升了 required-support discipline：在 48-task 子集上，`hygienic_combo` 的 escape rate 从 0.792 提升到 1.000，`primary_preserve` 从 0.854 提升到 0.979；contaminated citation rate 均降到 0.000。但这不能推翻 v1.1 的旧结论：prompt-only 规则不能替代检索层面的 primary preservation。它在 hygiene retriever 已经提供 primary evidence 时有效；在 BM25 本身没有召回 primary evidence 的 L4 hidden-primary 场景中，prompt 仍无从恢复缺失证据。

因此，当前报告建议把论文主张收窄为：当 primary evidence 被污染复读挤出，或 generated lore 被包装成可引用材料时，单纯模型规模提升不能可靠保证污染逃逸；检索层面的 primary preservation、污染抑制和证据供应链卫生是必要条件。不过，v1.1 的 metadata/source spoofing stress 已经表明，hygiene 机制本身也会受到可伪装元数据影响，后续应把 primary 识别建立在更难伪造的内容、引用链和来源一致性信号上。

## 1. 读者关切与研究问题

本报告面向两类读者。第一类是研究 RAG factuality、provenance reasoning、information pollution 和 agentic hallucination 的研究者；他们关心 EHA Matrix 的主效应是否有复现与机制证据，而不只是单次合成运行中的表面差异。第二类是构建检索增强系统和知识库 agent 的工程实践者；他们关心在有限预算下，应优先升级模型、改 prompt，还是修复检索证据链。

v1.2 主要回答四个问题：

1. Matrix v1.1 的多种子复现结论在 seed-cluster 置信区间下是否仍然稳健？
2. `claim_first_citation_v1.1` 与 `primary_preserve`、`hygienic_combo` 结合时，能否修复 required-support discipline 和 contaminated citation？
3. L4 hidden-primary 中，BM25 失败是否来自 primary evidence 没进上下文，还是模型忽略了已进入上下文的 primary evidence？
4. 这些结果如何帮助论文收窄主张，避免把合成 benchmark 结果外推成过强的生产系统安全声明？

本报告的角色是阶段性研究备忘和论文整合说明，不是最终论文定稿。

## 2. 数据来源与实验范围

v1.2 报告包记录为 `matrix-paper-consolidation-0513-5`。其输入与输出如下：

| Artifact | 行数或范围 | 在本报告中的角色 |
| --- | ---: | --- |
| `multiseed_cluster_ci.csv` | 18 aggregate rows | 为 v1.1 三 seed 复现补充 row-level 与 seed-cluster CI |
| `prompt_hygiene_preflight.csv` | 16 aggregate rows | 比较 `claim_first_citation_v1` 与 `claim_first_citation_v1_1` 在 hygiene retriever 下的表现 |
| `prompt_hygiene_preflight_rows.csv` | 192 raw rows | prompt preflight 的逐任务评分，其中 96 条为本轮新增 API 预测 |
| `l4_primary_recovery_audit.csv` | 12 aggregate rows | 审计 L4 hidden-primary 中 primary source 是否进入上下文、是否被引用、拒绝或忽略 |
| `l4_primary_recovery_audit_rows.csv` | 288 raw rows | 从 Matrix v1 主运行复算的 L4 逐任务机制记录 |
| `paper_consolidation_notes.md` | 研究说明 | 记录论文主张、应居中的结果、结构建议和应避免的过度声明 |
| `audit_manifest.json` | 机器可读清单 | 记录输入目录、输出行数和成本报告 |
| `cost_report.json` | 成本报告 | 记录新增 API 调用成本与中止状态 |

多种子 CI 来自 Matrix v1.1 的三个新 seed：9201、9202、9203。每个 seed 在 L3-L5 难度上包含 24 个 episode；模型为 `openai/gpt-4o-mini` 与 `openai/gpt-5.4-mini`；策略为 `naive_bm25`、`primary_preserve` 与 `hygienic_combo`。每个 model-strategy-difficulty 单元有 72 条 scored predictions，cluster_count 为 3。

Prompt hygiene preflight 使用 `openai/gpt-4o-mini`、L0/L3/L4/L5 四个难度、每级 12 个 episode，并比较两个 prompt 版本和两个 hygiene 策略。新运行的 96 条预测只覆盖 `claim_first_citation_v1_1` 与 `primary_preserve`/`hygienic_combo`；汇总表同时纳入旧 prompt baseline 以便对比。

L4 primary recovery audit 不新增 API 调用，而是从 Matrix v1 主运行复算。它覆盖三个模型、四种策略或 prompt/retriever 组合，共 12 个 aggregate rows。该审计的目的不是提高分数，而是解释 L4 hidden-primary 失败发生在检索层还是生成层。

## 3. 指标解释

本报告沿用 Matrix 系列的核心指标 `escape_rate`。它是一个严格复合指标，不等同于普通 claim accuracy。一次回答只有同时满足以下条件，才算 escape：

1. `claim_verdict` 与 gold verdict 一致。
2. `supporting_evidence` 不包含 contaminated citation。
3. 在需要支持证据时，decisive verdict 必须给出干净 supporting evidence；证据不足时应输出 `insufficient`。
4. 在 L5 generated-lore 场景中，不应把 generated lore 过度断言为 `supported` 或 `refuted`。

因此，claim accuracy 高但 escape rate 低，可能意味着输出方向正确但证据链不合格；也可能意味着引用了污染材料、没有给出必要干净证据，或在 generated-lore 场景中过度断言。

v1.2 新增的机制指标包括：

| 指标 | 含义 |
| --- | --- |
| `primary_in_context` | 目标 primary source 是否进入模型可见上下文 |
| `primary_cited` | 模型是否在 supporting evidence 中引用 primary source |
| `primary_ignored` | primary source 已进入上下文但未被引用 |
| `primary_rejected` | primary source 已进入上下文但模型显式或隐式拒绝其支持作用 |
| `mean_best_primary_context_rank` | 已召回 primary source 在上下文中的最佳排名 |
| `has_required_supporting_evidence` | decisive verdict 是否附带必要 supporting evidence |
| `clean_supporting_evidence` | supporting evidence 是否不含污染引用 |

这些指标使本轮报告能区分三类问题：检索器没有提供 primary evidence、模型看到 primary evidence 但没有使用、以及模型使用了证据但证据字段不满足 escape 条件。

## 4. Seed-cluster CI：L4 hidden-primary 是稳定失败点

多种子复现的 L3-L5 加权平均如下。每个单元覆盖 216 条 scored predictions。

| 模型 | 策略 | L3-L5 平均 escape | Claim accuracy | Contaminated citation rate | L5 overclaim rate |
| --- | --- | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | `naive_bm25` | 0.343 | 0.440 | 0.618 | 0.227 |
| `openai/gpt-4o-mini` | `primary_preserve` | 0.917 | 1.000 | 0.012 | 0.000 |
| `openai/gpt-4o-mini` | `hygienic_combo` | 0.898 | 0.995 | 0.042 | 0.005 |
| `openai/gpt-5.4-mini` | `naive_bm25` | 0.389 | 0.565 | 0.606 | 0.102 |
| `openai/gpt-5.4-mini` | `primary_preserve` | 1.000 | 1.000 | 0.000 | 0.000 |
| `openai/gpt-5.4-mini` | `hygienic_combo` | 1.000 | 1.000 | 0.000 | 0.000 |

这张表支持一个谨慎但有力的判断：在 L3-L5 污染难度上，检索层 information hygiene 的影响大于 naive BM25 条件下的模型升级。`openai/gpt-5.4-mini + naive_bm25` 的平均 escape rate 为 0.389，仍显著低于 `openai/gpt-4o-mini + primary_preserve` 的 0.917 和 `openai/gpt-4o-mini + hygienic_combo` 的 0.898。

分难度看，L4 hidden-primary 是最稳定的失败点：

| 模型 | 策略 | L3 escape | L4 escape | L4 cluster CI | L5 escape | L4 contaminated citation rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | `naive_bm25` | 1.000 | 0.000 | 0.000-0.000 | 0.028 | 1.000 |
| `openai/gpt-4o-mini` | `primary_preserve` | 0.875 | 0.917 | 0.833-1.000 | 0.958 | 0.000 |
| `openai/gpt-4o-mini` | `hygienic_combo` | 0.931 | 0.903 | 0.875-0.917 | 0.861 | 0.000 |
| `openai/gpt-5.4-mini` | `naive_bm25` | 1.000 | 0.000 | 0.000-0.000 | 0.167 | 1.000 |
| `openai/gpt-5.4-mini` | `primary_preserve` | 1.000 | 1.000 | 1.000-1.000 | 1.000 | 0.000 |
| `openai/gpt-5.4-mini` | `hygienic_combo` | 1.000 | 1.000 | 1.000-1.000 | 1.000 | 0.000 |

这个结果同时加强和限定了 Matrix v1 的主张。加强之处在于，L4 的 naive BM25 失败跨三个 seed 没有松动；两个模型的 L4 escape 都为 0.000，cluster CI 也为 0.000-0.000。限定之处在于，L3 false-consensus 在这三个 seed 上对 naive BM25 并不稳定困难，两种模型的 L3 naive escape 都是 1.000。因此，后续论文不应把所有污染难度合并成一个笼统结论，而应把 L4 hidden-primary 和 L5 generated-lore 作为更强的机制证据。

## 5. L4 primary recovery audit：失败首先发生在证据供应链

L4 primary recovery audit 是 v1.2 最重要的机制补充。它直接检查 L4 hidden-primary 中 primary source 是否进入上下文，以及进入后是否被模型引用。

| 模型 | 策略 | Claim accuracy | Escape rate | CCR | Primary in context | Primary cited | Primary ignored | Mean primary rank |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | `naive_bm25` | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |  |
| `openai/gpt-4o-mini` | `primary_preserve` | 1.000 | 0.958 | 0.000 | 1.000 | 0.958 | 0.042 | 1.0 |
| `openai/gpt-4o-mini` | `hygienic_combo` | 1.000 | 0.917 | 0.000 | 1.000 | 0.917 | 0.083 | 1.0 |
| `openai/gpt-5-mini` | `naive_bm25` | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |  |
| `openai/gpt-5-mini` | `primary_preserve` | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.0 |
| `openai/gpt-5-mini` | `hygienic_combo` | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.0 |
| `openai/gpt-5.4-mini` | `naive_bm25` | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 | 0.000 |  |
| `openai/gpt-5.4-mini` | `primary_preserve` | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.0 |
| `openai/gpt-5.4-mini` | `hygienic_combo` | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.0 |

这个审计支持一个机制性解释：L4 中 naive BM25 不是把 primary source 给了模型而模型仍然系统性失败；它是没有把 primary source 放进上下文。只要 `primary_preserve` 或 `hygienic_combo` 把 primary evidence 放到上下文第一位，模型就基本能恢复 claim accuracy、clean support 和 escape。

`careful_bm25` 也说明 prompt 谨慎性不能替代 evidence recovery。三个模型在 careful BM25 下的 `primary_in_context` 仍为 0.000，escape rate 仍为 0.000。`openai/gpt-4o-mini + careful_bm25` 的 contaminated citation rate 降到 0.208，`openai/gpt-5-mini + careful_bm25` 甚至为 0.000，但 claim accuracy 仍是 0.000。这表明模型可以减少污染引用，甚至给出看似干净的证据字段，却仍无法在缺失 primary source 的情况下恢复正确判定。

因此，L4 的最小充分解释不是“模型不会推理”，而是“检索器没有提供决定性证据”。这对论文写法很关键：应把 EHA Matrix 定位为 evidence supply chain benchmark，而不是单纯的 generator hallucination benchmark。

## 6. Prompt hygiene preflight：v1.1 提升输出纪律，但依赖 hygiene retriever

Prompt hygiene preflight 检查 `claim_first_citation_v1.1` 是否能在 hygiene retriever 已经提供较好证据的情况下提高 escape。按 prompt 和策略加权平均后，结果如下：

| Prompt | 策略 | Escape rate | Claim accuracy | CCR | Has required support | Clean support | Primary cited | Primary ignored |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `claim_first_citation_v1` | `hygienic_combo` | 0.792 | 1.000 | 0.042 | 0.833 | 0.958 | 0.583 | 0.167 |
| `claim_first_citation_v1_1` | `hygienic_combo` | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.750 | 0.000 |
| `claim_first_citation_v1` | `primary_preserve` | 0.854 | 1.000 | 0.036 | 0.896 | 0.958 | 0.646 | 0.104 |
| `claim_first_citation_v1_1` | `primary_preserve` | 0.979 | 1.000 | 0.000 | 0.979 | 1.000 | 0.729 | 0.021 |

v1.1 的主要收益不是提高 claim accuracy，因为 baseline claim accuracy 已经是 1.000。它修复的是证据字段纪律：required support 更完整，clean support 达到 1.000，contaminated citation rate 降到 0.000，primary ignored 显著下降。

分难度看，`hygienic_combo + claim_first_citation_v1_1` 在 L0、L3、L4、L5 四个 12-task 子集上都达到 1.000 escape。`primary_preserve + claim_first_citation_v1_1` 在 L0、L3、L5 达到 1.000，在 L4 为 0.917。这个结果说明 v1.1 可以作为 hygiene retriever 的输出规范补丁，尤其适合修复“模型答案正确但 supporting evidence 不满足复合指标”的问题。

但该结果不应被解读为 prompt-only 解决方案。旧的 careful BM25 preflight 已显示，v1.1 在 BM25 上下文被污染材料主导的 L4 场景中无法恢复 missing primary evidence。v1.2 的合理结论是：prompt v1.1 与 evidence hygiene 互补，而不是替代 evidence hygiene。

## 7. 与 metadata/source spoofing stress 的关系

v1.2 的 consolidation notes 特别提醒，hygiene 机制自身也要接受压力测试。Matrix v1.1 的 noisy metadata/source spoofing stress 已经显示，当 source type、标题和 visible citations 等可见元数据被扰动时，`primary_preserve` 在 L4 上会明显退化；50% metadata noise 下，`primary_preserve` 的 L4 escape 降到 0.333，而 `hygienic_combo` 仍为 0.792。

这与 v1.2 的 L4 recovery audit 并不矛盾。v1.2 说明，在干净元数据或当前主运行设定下，把 primary source 放进上下文可以恢复 L4；v1.1 noisy stress 则说明，识别 primary source 的机制若过度依赖可伪装元数据，就可能在更强压力下失效。

因此，后续系统设计不应止步于 source_type 标签。更稳健的 primary preservation 应结合内容结构、时间一致性、引用链可追踪性、声明粒度、跨文档矛盾关系和来源一致性信号。

## 8. 阶段性结论

v1.2 把 Matrix 系列的论点从“检索卫生很重要”推进到更具体的机制陈述：

> 在 hidden-primary 和 generated-lore 等污染机制中，失败首先表现为 evidence supply chain 失效：检索层没有提供决定性 primary evidence，或将污染材料包装为可引用上下文。更强模型能改善部分 claim 判断和 overclaim 行为，但不能从不存在于上下文的 primary source 中恢复证据。Prompt v1.1 能改善输出证据纪律，却必须与检索层 primary preservation 和污染抑制配合。

这个结论比“模型规模不重要”更准确。模型能力仍然影响 JSON 稳定性、claim accuracy、overclaim 与 abstention；但在 L4 hidden-primary 中，关键瓶颈是证据是否进入上下文。在当前三 seed 结果里，naive BM25 对两个模型都没有召回 primary evidence，L4 escape 因而稳定为 0.000。

论文写作中应居中的结果包括：

1. L4 naive BM25 的 escape rate 为 0.000，seed-cluster CI 为 0.000-0.000。
2. `primary_preserve` 与 `hygienic_combo` 通过恢复 primary evidence，将 L4 escape 提升到 0.917-1.000。
3. L4 audit 显示 naive/careful BM25 的 `primary_in_context=0.000`，而 hygiene strategies 的 `primary_in_context=1.000`。
4. Prompt v1.1 在 hygiene retriever 下修复 required-support discipline，但不应被写成缺失证据的替代方案。
5. Metadata/source spoofing stress 限定了 hygiene 机制的适用边界：单纯元数据标签不足以承担 primary 识别。

## 9. 局限与替代解释

第一，本报告仍基于合成 mini-web，不代表开放 web、企业知识库或真实 adversarial SEO 环境。合成数据的优势是 gold labels、污染标签和 primary roots 可审计；代价是任务分布和攻击策略受生成器约束。

第二，seed-cluster CI 只有三个 seed cluster。它比 row-level bootstrap 更接近复现不确定性，但 cluster 数量仍少，不足以支持精细的分布推断。正式论文中应明确把这些区间称为阶段性 cluster bootstrap evidence。

第三，L4 audit 解释了当前 Matrix v1 主运行中的 hidden-primary 机制，但不证明所有 retrieval failure 都是 primary source 缺失。其他任务中仍可能存在模型看到 primary evidence 后忽略、误读或拒绝它的情况。

第四，prompt hygiene preflight 是小样本预检。它覆盖 4 个难度、2 个策略和 `openai/gpt-4o-mini`，不能直接证明 v1.1 在所有模型、所有 retriever 或完整 L0-L5 矩阵中都有同等收益。

第五，metadata/source spoofing stress 是非自适应扰动。真实攻击者可能构造更复杂的语义伪装、引用环、时间戳操纵、跨站转载网络或搜索排序操纵。

第六，scorer 的 gold truth 与污染判断来自合成数据生成流程。自动评分提高了可复现性，但如果要主张更广泛的事实性评测意义，后续仍需要人工审计或外部 benchmark 对照。

## 10. 下一步建议

1. 将 `claim_first_citation_v1_1` 与 `primary_preserve`、`hygienic_combo` 扩展到完整 L0-L5 矩阵，确认 required-support discipline 的收益不会引入新的 abstention 或 evidence-selection 代价。
2. 把 L4 primary recovery audit 固化为常规报告项，至少同步报告 `primary_in_context`、`primary_cited`、`primary_ignored` 与 context rank。
3. 对 metadata/source spoofing 增加内容级与引用链级伪装，检查 primary preservation 是否能超越 source_type、title 和 visible citation 等可伪装字段。
4. 在论文主表之外增加机制表，把 full escape 拆成 claim correctness、clean support、required support、generated-lore abstention 和 primary recovery。
5. 在三 seed 之外继续扩展 cluster 数量，或采用 episode family/mixed-effects 分析，降低对单一生成器分布的依赖。

## 11. 研究伦理与 AI 辅助写作声明

本报告没有引入外部文献、真实个人数据或真实机构事实。所有实验对象均为 EHA 合成数据集中的虚构任务和文档。报告中的数值来自当前仓库的本地实验 artifact 与自动评分结果。

本报告由 AI 助手根据本地实验输出起草，并按 academic-paper-writing 的读者、问题、证据、限制与反驳框架组织。报告没有手工编造实验结果、引用或外部来源；凡涉及结论外推处均以阶段性、合成实验或下一步建议限定。
