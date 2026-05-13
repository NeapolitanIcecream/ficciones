# EHA Matrix v1 阶段性实验报告：模型规模、检索卫生与伪共识逃逸

日期：2026-05-13
对象：Epistemic Hygiene Arena Matrix Escape Table v1
状态：阶段性实测报告，依据当前仓库的本地实验输出生成

## 摘要

本报告总结 Epistemic Hygiene Arena（EHA）当前阶段的 Matrix v1 实验。前一阶段 Phase 2R 已经证明，标准 BM25 在 primary evidence 被隐藏且污染文档高度饱和时会被 false consensus 稳定击穿；但 Phase 2R 仍受 scope-tag 与 temporal-tool planning 失败限制，尚不足以支撑完整主实验。Matrix v1 因此把问题收束到一个更清晰的矩阵：在 L0-L5 六个污染/证据难度等级上，比较模型规模与信息卫生策略对“逃逸污染证据链”的影响。

Matrix v1 主实验使用 `EHA-Matrix-v1` 数据集，seed 为 9133，共 144 个 episode、2096 篇 agent 可见文档、2096 行 gold document 标注和 1174 条 gold graph edge。每个难度等级包含 24 个任务。主矩阵评估 `openai/gpt-4o-mini`、`openai/gpt-5-mini` 和 `openai/gpt-5.4-mini` 三个模型；每个模型在四种策略下运行：`naive_bm25`、`careful_bm25`、`primary_preserve` 和 `hygienic_combo`。主矩阵共写出 1728 条 scored predictions。另有 36-task preflight 和 `openai/gpt-5.5` 的 L3-L5 sanity check，用于验证 gate 与高能力模型边界，但不混入主矩阵平均值。

本轮最重要的结论是：在当前合成 mini-web 中，信息卫生机制的收益可以超过模型规模收益。`openai/gpt-4o-mini + hygienic_combo` 的平均 escape rate 为 0.854，高于 `openai/gpt-5-mini + naive_bm25` 的 0.465，也高于 `openai/gpt-5.4-mini + naive_bm25` 的 0.681。`openai/gpt-5-mini + hygienic_combo` 的平均 escape rate 为 0.917，同样高于更强模型的 naive retrieval。`openai/gpt-5.4-mini + hygienic_combo` 和 `openai/gpt-5.4-mini + primary_preserve` 在主矩阵六个难度等级上均达到 1.000 escape rate。

这些结果支持一个阶段性主张：EHA 当前最有解释力的变量不是“模型是否更强”，而是模型是否被放在一个能保留 primary source、压低同源污染、并要求显式拒绝可疑证据的证据供应链中。更强模型在 naive BM25 下仍会在 L4 hidden-primary 场景中系统性失败；相反，较弱模型配合 hygienic retrieval 能在多数污染等级中保持较高逃逸率。

但本轮不能被解释为正式结论。第一，Matrix v1 是合成数据集，不代表开放 web 或真实企业知识库。第二，escape rate 是严格的复合指标，要求 claim verdict 正确、支持证据不污染、且 L5 不过度断言；部分 claim accuracy 高但 escape 低的结果反映 citation hygiene 或 supporting-evidence 字段失败，而不一定是事实判断失败。第三，GPT-5.5 只运行 L3-L5 sanity check，不是完整主矩阵。第四，Matrix v1 刻意把 scope-tag 与主动工具规划降为次要诊断，因此它解决的是“模型规模 vs 信息卫生”的局部问题，而不是 Phase 2R 暴露出的全部 epistemic hygiene 问题。

## 1. 研究问题与读者关切

本阶段面向两类读者。第一类是研究 RAG、事实性评测、provenance reasoning 和 agentic hallucination 的研究者；他们关心的是模型错误是否来自模型能力不足，还是来自证据供应链被污染。第二类是构建检索增强系统的工程实践者；他们关心的是在预算有限的情况下，是否应该优先换更强模型，还是先改检索与证据卫生。

Matrix v1 回答的问题可以压缩为三条：

1. 在污染文档、同源复读、过期资料和 generated-lore 混合存在时，较强模型加 naive retrieval 是否足够可靠？
2. primary preservation 与 hygienic combo 能否在不同模型规模上稳定降低 contaminated citation，并提升 escape rate？
3. 较弱模型配合信息卫生机制，能否超过更强模型配合 naive BM25？

本报告的回答范围是阶段性矩阵实验。它可以支持下一轮实验设计和论文论点筛选；它不能证明某个生产系统已经安全，也不能替代开放域评测、人工标注审计或自适应攻击测试。

## 2. 数据集与难度设计

Matrix v1 使用 6 个难度等级，每级 24 个 episode：

| 难度 | Episode type | 目标压力 |
| --- | --- | --- |
| L0 | `L0_clean_web` | 干净网页，检查任务和 schema 是否可解 |
| L1 | `L1_mild_pollution` | 轻度污染，检查基本污染拒绝能力 |
| L2 | `L2_temporal_drift` | 时间漂移，检查过期资料处理 |
| L3 | `L3_false_consensus` | 伪共识，检查同源复读识别 |
| L4 | `L4_hidden_primary` | primary 被挤出或隐藏，检查污染洪泛下的 recovery |
| L5 | `L5_halluweb_generated_lore` | generated lore 和百科式伪证据，检查 abstention 与过度断言 |

数据集的 gold labels、污染标签和 upstream roots 均为 scorer-only。模型只能看到检索返回的文档和 prompt 中的任务描述，不能读取隐藏标签。这一点对 Matrix v1 的解释很重要：`hygienic_combo` 和 `primary_preserve` 可以改变上下文中证据的组成，但它们不能直接读取 scorer 的 gold truth。

Preflight 数据集 `EHA-Matrix-v1-preflight` 使用同一 seed，每级 6 个 episode，共 36 个任务。Preflight 的作用是先检查 L0 可解性、L3/L4 hygiene 优势、claim-first prompt 的 contaminated-citation 控制，以及 L5 overclaim 是否恶化。API preflight gate 全部通过：L0 claim accuracy 为 1.0，L0 over-abstention 为 0.0，L3/L4 BM25 escape rate 为 0.333，hygienic_combo escape rate 为 1.0，claim-first contaminated citation rate 为 0.042，低于 baseline 的 0.083，L5 overclaim rate 没有恶化。

## 3. 模型、策略与指标

主矩阵包含三个模型：

| 模型 | 角色 |
| --- | --- |
| `openai/gpt-4o-mini` | 较弱、低成本 baseline |
| `openai/gpt-5-mini` | 中间能力层 |
| `openai/gpt-5.4-mini` | 主矩阵中的较强模型 |

策略分为四类：

| 策略 | Retriever / prompt | 含义 |
| --- | --- | --- |
| `naive_bm25` | `bm25_top8` + `simple_answer_v1` | 标准检索和朴素回答 |
| `careful_bm25` | `bm25_top8` + `claim_first_citation_v1` | 不改检索，只加强 claim-first 与 citation hygiene prompt |
| `primary_preserve` | `primary_preserve_top8` + `claim_first_citation_v1` | 强制保留 primary evidence |
| `hygienic_combo` | `hygienic_combo_top8` + `claim_first_citation_v1` | 组合 primary preservation、污染抑制与证据卫生约束 |

核心指标是 `escape_rate`。它不是普通准确率，而是一个严格复合指标：claim verdict 必须正确；supporting evidence 中 contaminated citation rate 必须为 0；在需要证据时必须给出干净 supporting evidence，或在证据不足时给出 `insufficient`；L5 generated-lore 场景不得过度断言为 `supported` 或 `refuted`。因此，claim accuracy 高但 escape rate 低，通常说明模型知道答案方向，但证据使用、引用卫生或 abstention 仍不合格。

辅助指标包括 claim accuracy、contaminated citation rate、L5 abstention quality、generated-lore overclaim rate、overconfident wrong rate、primary recovery rate 和 ECE。Matrix v1 的 evidence diagnostics 是次要诊断，不作为 blocking gate；这与 Phase 2R 中 scope-tag 和 tool-planning gate 的定位不同。

## 4. 主矩阵结果

### 4.1 平均 escape rate

| 模型 | `naive_bm25` | `careful_bm25` | `primary_preserve` | `hygienic_combo` |
| --- | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | 0.646 | 0.458 | 0.882 | 0.854 |
| `openai/gpt-5-mini` | 0.465 | 0.715 | 0.875 | 0.917 |
| `openai/gpt-5.4-mini` | 0.681 | 0.833 | 1.000 | 1.000 |

主表显示两个方向的结果。第一，单纯增强 prompt 并不总是足够。`careful_bm25` 相比 `naive_bm25` 在 GPT-5-mini 和 GPT-5.4-mini 上改善了平均 escape rate，但在 GPT-4o-mini 上反而更低。结合 scored predictions 看，原因并非 claim verdict 大面积错误，而是 claim-first prompt 有时没有列出 supporting evidence，导致严格 escape 指标失败。这说明 prompt hygiene 与 retrieval hygiene 应分开解释。

第二，检索卫生的作用非常稳定。`primary_preserve` 在三个模型上的平均 escape rate 分别为 0.882、0.875 和 1.000；`hygienic_combo` 分别为 0.854、0.917 和 1.000。相较之下，`naive_bm25` 分别只有 0.646、0.465 和 0.681。换言之，模型变强不能自动修复被污染上下文；保留 primary source 和压低污染证据才是主要改变量。

### 4.2 Claim accuracy 与 citation hygiene

| 模型 | 策略 | Claim accuracy avg | Contaminated citation rate avg |
| --- | --- | ---: | ---: |
| `openai/gpt-4o-mini` | `naive_bm25` | 0.722 | 0.336 |
| `openai/gpt-4o-mini` | `primary_preserve` | 1.000 | 0.017 |
| `openai/gpt-4o-mini` | `hygienic_combo` | 0.993 | 0.028 |
| `openai/gpt-5-mini` | `naive_bm25` | 0.833 | 0.413 |
| `openai/gpt-5-mini` | `primary_preserve` | 0.979 | 0.032 |
| `openai/gpt-5-mini` | `hygienic_combo` | 1.000 | 0.023 |
| `openai/gpt-5.4-mini` | `naive_bm25` | 0.771 | 0.319 |
| `openai/gpt-5.4-mini` | `primary_preserve` | 1.000 | 0.000 |
| `openai/gpt-5.4-mini` | `hygienic_combo` | 1.000 | 0.000 |

Claim accuracy 与 contaminated citation rate 共同说明了 Matrix v1 的核心机制。Naive BM25 下，即使更强模型也会大量引用污染文档。GPT-5-mini 的 naive contaminated citation rate 甚至达到 0.413，高于 GPT-4o-mini 的 0.336；GPT-5.4-mini naive 也有 0.319。模型规模没有自动解决“引用了错误证据链”的问题。

`primary_preserve` 与 `hygienic_combo` 则显著降低 contaminated citation rate。在 GPT-5.4-mini 上，两者均降到 0.000；在 GPT-4o-mini 和 GPT-5-mini 上，也分别降到约 0.017-0.032 与 0.023-0.028 的范围。这个结果比单纯的 claim accuracy 更有价值，因为 EHA 评估的不是“最终字符串是否正确”，而是模型是否能把正确回答锚定到干净证据。

## 5. 难度曲线：L4 与 L5 是关键压力点

L4 hidden-primary 是主矩阵最强的失败放大器。三种主模型在 `naive_bm25` 下的 L4 escape rate 全部为 0.000，claim accuracy 也全部为 0.000。`careful_bm25` 在 L4 上同样为 0.000 claim accuracy。换言之，只改 prompt 而不改变检索上下文，不能修复 primary 被隐藏或污染证据挤占上下文的问题。

对照组非常清楚：

| 模型 | L4 `naive_bm25` escape | L4 `primary_preserve` escape | L4 `hygienic_combo` escape |
| --- | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | 0.000 | 0.958 | 0.917 |
| `openai/gpt-5-mini` | 0.000 | 1.000 | 1.000 |
| `openai/gpt-5.4-mini` | 0.000 | 1.000 | 1.000 |

这说明 Matrix v1 成功构造了一个对模型规模不友好、但对信息供应链干预敏感的压力区。只要 primary evidence 被系统性恢复，三个模型都能大幅改善；若仍使用 naive BM25，模型增强本身无法逃出 L4。

L5 generated-lore 的图景更细。GPT-4o-mini 在 `naive_bm25` 下 L5 claim accuracy 只有 0.375，escape rate 为 0.000，contaminated citation rate 为 0.990，generated-lore overclaim rate 为 0.625。GPT-5.4-mini 在 naive L5 下 claim accuracy 为 0.625，escape rate 只有 0.083，contaminated citation rate 为 0.917，overclaim rate 为 0.375。GPT-5-mini 的 naive L5 claim accuracy 达到 1.000，但 escape rate 仍为 0.000，主要因为 contaminated citation rate 为 0.979。这说明 generated-lore 场景中，正确 abstention 与干净证据行为不能混为一谈。

使用 `primary_preserve` 或 `hygienic_combo` 后，L5 明显改善。GPT-5-mini 和 GPT-5.4-mini 在这两种策略下 L5 escape rate 均为 1.000；GPT-4o-mini 的 L5 escape rate 分别为 0.875 和 0.792，仍有残余污染引用和一次 overclaim。这提示下一阶段若要提高较弱模型，需要重点处理 L5 的 rejected-evidence 显式化和 generated-lore abstention 稳定性。

## 6. 弱模型加卫生机制 vs 强模型加 naive retrieval

Matrix v1 最有论文价值的比较是跨模型、跨策略对照：

| 比较 | 左侧 escape | 右侧 escape | 差值 |
| --- | ---: | ---: | ---: |
| `gpt-4o-mini + hygienic_combo` vs `gpt-5-mini + naive_bm25` | 0.854 | 0.465 | +0.389 |
| `gpt-4o-mini + hygienic_combo` vs `gpt-5.4-mini + naive_bm25` | 0.854 | 0.681 | +0.174 |
| `gpt-5-mini + hygienic_combo` vs `gpt-5.4-mini + naive_bm25` | 0.917 | 0.681 | +0.236 |
| `gpt-5.4-mini + hygienic_combo` vs `gpt-5-mini + naive_bm25` | 1.000 | 0.465 | +0.535 |

这些比较支持一个保守但重要的结论：在污染证据链问题上，“更强模型 + 脏上下文”可以输给“较弱模型 + 干净证据供应链”。这不是说模型规模不重要；GPT-5.4-mini 在 hygienic conditions 下达到了最强表现。更准确的解释是：模型规模和信息卫生不是可替代变量。强模型需要干净证据结构才能稳定发挥，弱模型也可以通过更好的证据结构获得大幅收益。

这也解释了为什么 EHA 不应只报告 leaderboard 式模型排名。如果检索条件不固定或不健康，模型排名会把证据供应链失败误写成模型能力差异；如果只比较检索器而不比较模型，也会低估推理能力与 citation discipline 的交互。Matrix v1 的贡献在于把这两个维度放在同一张表中。

## 7. GPT-5.5 sanity check

GPT-5.5 sanity check 只覆盖 L3-L5，不进入主矩阵平均值。它写出 216 条 scored predictions，策略包括 `naive_bm25`、`primary_preserve` 和 `hygienic_combo`。

结果与主矩阵的机制解释一致。GPT-5.5 在 L3 和 L5 的 naive BM25 下 escape rate 为 1.000，但在 L4 hidden-primary 下仍为 0.000；使用 `primary_preserve` 或 `hygienic_combo` 后，L3-L5 全部达到 1.000 escape rate，contaminated citation rate 为 0.000。也就是说，即使 sanity check 中的更强模型可以处理 L5，它仍不能在 L4 中靠模型能力 alone 修复 primary 被隐藏的问题。这个结果强化了 Matrix v1 的主张：L4 主要是证据供应链问题，不是单纯模型推理问题。

GPT-5.5 sanity check 的限制也很明确：它没有运行 L0-L2，没有与 `careful_bm25` 做完整对照，也不是预注册主矩阵的一部分。因此它只能作为边界检查，不能作为主结论来源。

## 8. 失败案例

失败案例集中在 L4。典型任务 `eham_096`、`eham_097`、`eham_098` 和 `eham_099` 的 gold verdict 均为 `refuted`，但 `naive_bm25` 经常把污染 root 和多个 repost 当作 supporting evidence，预测为 `supported`，confidence 通常在 0.88 到 0.95 之间。GPT-4o-mini、GPT-5-mini 和 GPT-5.4-mini 都出现过这种模式。

这些失败不是普通随机错题，而是结构性污染失败。模型不是没有输出证据；它输出的是被污染或同源复读的证据。尤其在 `eham_096` 中，GPT-5.4-mini 的 naive 输出甚至把多个 repost 同时列在 supporting evidence 和 rejected evidence 中，却仍预测为 `supported`。这说明 prompt 让模型意识到部分证据可疑，并不保证它能在最终 claim verdict 中正确使用这种怀疑。

因此，下一阶段的 failure-case review 不应只问“为什么答案错”，而应问三件事：primary evidence 是否进入上下文；模型是否把同源 repost 当成独立证据；模型是否能把 rejected evidence 的判断传播到 final verdict。Matrix v1 已经显示，第一项可以通过 retrieval intervention 大幅改善；第二和第三项仍需要 prompt/schema 和评分细化。

## 9. 与 Phase 2R 的关系

Phase 2R 的主要成就是压力校准：它证明 high-pressure false-consensus 条件能稳定击穿 BM25，并显示 `hygienic_combo_top8` 在检索层和最终回答层都有积极信号。但 Phase 2R 的 gate 未通过，主要失败在 scope accuracy 和 temporal comparison planning。换言之，Phase 2R 回答的是“压力够不够”和“检索卫生是否值得继续”，但还不能回答更大的模型/策略矩阵问题。

Matrix v1 接续这个问题，但有意简化目标。它暂时不把 scope tag 和主动工具规划作为主 gate，而是把主指标改成 escape rate、claim accuracy、contaminated citation rate 和 L5 abstention quality。这样做的好处是，模型规模与信息卫生的交互变得更清晰；坏处是，Matrix v1 不能替代 Phase 2R 对 scope diagnosis 的要求。

因此，本阶段应被理解为一个“论文论点筛选实验”：它为“信息卫生可胜过模型规模”提供了强阶段性证据，也指出 L4 hidden-primary 是最具区分度的压力场景。它尚未完成 EHA 全部研究目标。

## 10. 局限性

第一，Matrix v1 仍是合成 mini-web。文档、污染链、primary source 和 generated-lore 场景由本地生成器构造，不代表真实网页生态、企业知识库、搜索排序或自适应攻击者。

第二，样本量仍有限。144 个主任务对阶段矩阵足够，但每个模型、策略、难度组合只有 24 个 episode。若进一步按 episode subtype、污染根、primary visibility 或 prompt failure 类型拆分，每格样本更小。

第三，escape rate 是合理但严格的复合指标。它会惩罚污染引用、supporting evidence 缺失和 L5 overclaim，这符合 epistemic hygiene 的研究目标；但在解释时必须把 claim correctness、citation hygiene 和 abstention 分开看。

第四，Matrix v1 没有把 Phase 2R 中失败的 scope-tag 与 temporal tool planning 纳入 blocking gate。因此，它不能宣称模型已经理解证据范围、冲突类型或时效性，只能宣称在当前 schema 下更少引用污染证据并更常逃出伪共识。

第五，`primary_preserve` 和 `hygienic_combo` 的可部署性仍需进一步分析。它们不能读取 gold labels，但在真实系统中如何识别 primary source、上游根和同源复读，需要额外工程定义和误差评估。

第六，GPT-5.5 只做了 sanity check。它支持 L4 仍是 evidence-supply problem 的解释，但不能纳入主矩阵的完整模型排名。

## 11. 下一阶段建议

建议把 Matrix v1 作为当前论文主线的阶段性证据，但不要直接升级为最终结论。下一阶段应做四件事。

1. 把 L4 hidden-primary 保留为核心压力场景，并扩大每格样本量。当前结果显示 L4 对模型规模和检索卫生的区分最清楚。
2. 修复 claim-first prompt 的 supporting-evidence 省略问题。`careful_bm25` 在若干干净任务中 claim 正确但 escape 失败，说明 schema compliance 仍会干扰主指标。
3. 把 generated-lore abstention 与 contaminated citation 分开报告。L5 中有模型能给出正确 insufficient，却仍引用污染文档；这两种失败应分别建模。
4. 将 Matrix v1 与 Phase 2R 修订版合并：保留 Matrix v1 的模型/策略矩阵，同时恢复 scope diagnosis 与 temporal planning gate。只有当 claim、citation、scope 和 tool planning 同时稳定，EHA 才能支撑更强的主实验结论。

## 12. 可复现信息

本报告依据以下本地实验材料和输出：

- `eha-mvp/data/matrix-v1/manifest.json`
- `eha-mvp/data/matrix-v1/tasks.jsonl`
- `eha-mvp/data/matrix-v1/documents.jsonl`
- `eha-mvp/data/matrix-v1/gold_documents.jsonl`
- `eha-mvp/data/matrix-v1/gold_graph.jsonl`
- `eha-mvp/results/reports-matrix-v1/summary.md`
- `eha-mvp/results/reports-matrix-v1/matrix_escape_rate.csv`
- `eha-mvp/results/reports-matrix-v1/matrix_claim_accuracy.csv`
- `eha-mvp/results/reports-matrix-v1/matrix_contaminated_citation_rate.csv`
- `eha-mvp/results/reports-matrix-v1/matrix_abstention_quality.csv`
- `eha-mvp/results/reports-matrix-v1/model_vs_hygiene_comparisons.csv`
- `eha-mvp/results/reports-matrix-v1/difficulty_curves.csv`
- `eha-mvp/results/reports-matrix-v1/failure_cases_matrix_v1.md`
- `eha-mvp/results/reports-matrix-v1/cost_report.json`
- `eha-mvp/results/reports-matrix-v1-preflight-gpt4omini/preflight_gate.json`
- `eha-mvp/results/reports-matrix-v1-gpt55-sanity/summary.md`
- `eha-mvp/results/reports-matrix-v1-gpt55-sanity/cost_report.json`
- `eha-mvp/results/reports-matrix-v1/prompt_to_artifact_checklist.md`

主矩阵成本报告显示 `aborted=false`，`spent_usd=2.676095`，soft cap 为 75 美元，hard cap 为 200 美元，abort cap 为 300 美元。Preflight API 运行花费 0.050270 美元；GPT-5.5 sanity check 花费 4.257095 美元。加总来看，当前 Matrix v1 阶段的 API 实验支出为 6.983460 美元，均未触发预算中止。

当前 checklist 记录：主矩阵包含三个模型各 576 条 predictions；preflight gate 全部通过；GPT-5.5 sanity check 含 216 条 predictions；`uv run pytest` 通过 32 个测试；`uv run python -m compileall eha` 通过。报告没有重新运行 API 实验，也没有引入外部实验结果。

## 13. AI 使用说明

本报告由 Codex 根据用户指定的本地仓库、阶段性实验结果、报告表和失败案例生成。报告中的数值均来自当前仓库已有输出；未编造未运行模型、未补写缺失实验证据，也未把阶段性结果外推为生产系统结论。解释性判断使用“当前阶段”“合成 mini-web”“阶段性证据”等限定语，以保留实验范围和不确定性。
