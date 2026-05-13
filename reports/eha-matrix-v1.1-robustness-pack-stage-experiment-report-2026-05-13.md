# EHA Matrix v1.1 阶段性实验报告：多种子复现、元数据伪装与逃逸指标分解

日期：2026-05-13
对象：Epistemic Hygiene Arena Matrix v1.1 Robustness Pack
状态：阶段性实测报告，依据当前仓库的本地实验输出生成

## 摘要

本报告总结 Epistemic Hygiene Arena（EHA）Matrix v1.1 Robustness Pack 的阶段性结果。Matrix v1 主实验已经给出一个强信号：在合成 mini-web 中，信息卫生策略对污染逃逸的贡献可以超过单纯模型规模提升。Matrix v1.1 的任务不是替换这一主实验，而是围绕其最容易被质疑的部分做四类跟进检查：关键难度的多种子复现、元数据和来源伪装压力测试、escape 指标分解，以及 `claim_first_citation_v1.1` prompt-only preflight。

本轮新增报告包包含 1296 行多种子 scored predictions、576 行 noisy metadata/source spoofing scored predictions、从 Matrix v1 主运行复算得到的 1728 行 escape decomposition rows，以及 96 行 prompt preflight rows。新增 API 运行成本报告显示 `aborted=false`，合计 `spent_usd=2.810599`。所有这些结果都应被解释为合成实验中的机制性证据，而不是开放 web 或生产 RAG 系统的外推结论。

最重要的复现实验结论是：Matrix v1 的核心卫生效应在 L3-L5 关键难度上跨三个新 seed 仍然成立。在 `openai/gpt-4o-mini` 上，L3-L5 平均 escape rate 从 naive BM25 的 0.343 提升到 `primary_preserve` 的 0.917 和 `hygienic_combo` 的 0.898。在 `openai/gpt-5.4-mini` 上，naive BM25 的 L3-L5 平均 escape rate 只有 0.389，而 `primary_preserve` 与 `hygienic_combo` 均达到 1.000。尤其是 L4 hidden-primary 难度，两种模型的 naive BM25 escape rate 均为 0.000，contaminated citation rate 均为 1.000。这说明更强模型在 primary evidence 被污染复读挤出时仍会系统性失败，关键变量仍是证据供应链能否保留干净 primary source。

本轮也收紧了 Matrix v1 的解释边界。L3 false-consensus 在多种子复现中对 naive BM25 并不总是困难：两种模型在 L3 上的 naive escape rate 都是 1.000。真正稳定击穿 naive retrieval 的是 L4 hidden-primary 和 L5 generated-lore 场景。因此，后续论文或主实验不应把所有“污染”难度混成一个结论，而应区分同源复读、primary 隐藏、generated lore 与 metadata spoofing 的机制差异。

第二个新结论来自 noisy metadata/source spoofing stress。该压力测试不改变 gold labels，只改变 agent 可见文档的 `source_type`、标题和可见引用等元数据。结果显示，`hygienic_combo` 比单纯 `primary_preserve` 更抗元数据伪装。`openai/gpt-5-mini` 在 50% metadata noise 下，L3-L5 平均 escape rate 为：`primary_preserve` 0.778，`hygienic_combo` 0.917。最脆弱的是 L4：`primary_preserve` 从 noise 0 的 1.000 降到 noise 50 的 0.333，`hygienic_combo` 从 0.958 降到 0.792。值得注意的是，noisy stress 的 contaminated citation rate 始终为 0.000；失败主要表现为 claim accuracy 和 escape 下降，而不是明显引用污染文档。这提示下一阶段需要检查 primary-preserve 机制是否过度依赖可伪装元数据。

第三个结论来自动因分解。Matrix v1 的 escape rate 是严格复合指标，失败不只来自 verdict 错误。比如 Matrix v1 主运行中，`openai/gpt-4o-mini + careful_bm25` 的平均 claim correctness 为 0.833，clean supporting evidence 为 0.944，但 has-required-supporting-evidence 只有 0.514，最终 full escape 只有 0.458。`openai/gpt-5-mini + naive_bm25` 的 claim correctness 也是 0.833，但 clean supporting evidence 只有 0.472，最终 full escape 为 0.465。这说明同一个低 escape 分数可能对应不同机制：一个是答案方向正确但没有给出必要干净证据，另一个是答案方向较好但证据链被污染。

第四个结论是 prompt-only 修复存在清晰上限。`claim_first_citation_v1.1` 在 preflight 中把 `openai/gpt-4o-mini + careful_bm25` 的 L0 escape rate 从 0.250 提升到 1.000，L3 从 0.500 提升到 1.000，L5 从 0.917 提升到 1.000，并把 L5 contaminated citation rate 从 0.083 降到 0.000。但在 L4 hidden-primary 上，v1.1 的 escape rate 仍为 0.000，claim accuracy 仍为 0.000，contaminated citation rate 还从 0.333 升到 1.000。也就是说，更严格的支持证据规则可以修复“有干净证据但输出格式或引用不足”的问题，却不能在 BM25 上下文已经被污染材料主导时恢复隐藏 primary source。

本轮阶段性主张可以概括为：EHA Matrix 的核心命题获得了更强支持，但也变得更具体。信息卫生机制确实可以跨 seed 稳定压制 L4/L5 的污染逃逸风险；但这种机制本身会受到 metadata spoofing 影响，且 prompt-only 规则不足以替代检索层面的 primary preservation 和污染抑制。下一阶段不应只扩大样本，而应把 primary recovery 的依据从可见元数据推进到更难伪装的内容、引用链和来源一致性证据。

## 1. 读者关切与研究问题

本报告面向两类读者。第一类是研究 RAG 事实性、provenance reasoning、agentic hallucination 和信息污染评测的研究者；他们关心 EHA 的指标是否只是单 seed 合成巧合，还是能跨样本稳定复现。第二类是构建检索增强系统和知识库 agent 的工程实践者；他们关心在预算有限时，应该先升级模型，还是先修复检索证据链。

Matrix v1.1 回答四个问题：

1. Matrix v1 中“信息卫生超过模型规模”的结论，在 L3-L5 关键污染难度上是否能跨新 seed 复现？
2. 如果攻击者不直接改变事实内容，而是伪装 source type、标题和引用元数据，`primary_preserve` 与 `hygienic_combo` 是否仍然可靠？
3. Escape rate 下降到底来自 claim 判断错误、引用污染、缺少必要支持证据，还是 generated-lore 过度断言？
4. 只加强 claim-first prompt 中的支持证据规则，能否替代检索层面的 evidence hygiene？

本报告的目标不是证明某个生产系统安全，而是为下一轮实验设计和论文论点提供更可审计的中间证据。

## 2. 数据来源与实验范围

Matrix v1.1 的本地报告包包含五类核心 artifact：

| Artifact | 行数或范围 | 在本报告中的角色 |
| --- | ---: | --- |
| `multiseed_replication.csv` | 18 aggregate rows | 汇总 L3-L5 多 seed 复现指标 |
| `scored_multiseed_predictions.csv` | 1296 raw rows | 多 seed 复现的逐任务评分 |
| `noisy_metadata_stress.csv` | 24 aggregate rows | 汇总 metadata/source spoofing 压力测试 |
| `scored_noisy_predictions.csv` | 576 raw rows | noisy stress 的逐任务评分 |
| `escape_decomposition.csv` | 72 aggregate rows | 从 Matrix v1 主运行复算 escape 组成 |
| `escape_decomposition_rows.csv` | 1728 raw rows | Matrix v1 主运行的逐任务 escape 组成 |
| `prompt_v1_1_preflight.csv` | 8 aggregate rows | 对比 `claim_first_citation_v1` 与 `claim_first_citation_v1_1` |
| `prompt_v1_1_preflight_rows.csv` | 96 raw rows | prompt preflight 的逐任务评分 |
| `cost_report.json` | 8 source reports | 新增 API 运行成本与中止状态 |

多种子复现使用新 seed `9201`、`9202`、`9203`。每个 seed 的完整 Matrix 数据集均有 144 个 episode，包含 L0-L5 六个等级，每级 24 个 episode；本轮复现实验只运行关键难度 L3、L4、L5。模型为 `openai/gpt-4o-mini` 与 `openai/gpt-5.4-mini`，策略为 `naive_bm25`、`primary_preserve` 与 `hygienic_combo`。因此 raw rows 数量为 3 seeds x 2 models x 3 strategies x 3 difficulties x 24 episodes = 1296。

Noisy metadata/source spoofing stress 使用原 Matrix v1 seed `9133` 的 L3-L5 子集，每个 noise level 72 个 episode。噪声水平为 0%、10%、25%、50%。该处理只改变 agent 可见文档的元数据与可见引用，包括把部分 primary source 改写成 secondary digest、把污染文档包装成 authority-style release、清空部分 visible citations、把 repost 包装成 independent analysis，以及把 generated lore 包装成 audit_report。Gold labels 保持不变。该实验只运行 `openai/gpt-5-mini`，策略为 `primary_preserve` 与 `hygienic_combo`。

Escape decomposition 不新增 API 调用，而是从 Matrix v1 主运行复算。它把 full escape 拆成四个组成项：claim 是否正确、supporting evidence 是否干净、在 decisive verdict 下是否有必要 supporting evidence，以及 L5 generated-lore 是否正确 abstain。

Prompt v1.1 preflight 使用 L0、L3、L4、L5 各 12 个 episode，只在 `openai/gpt-4o-mini + careful_bm25` 上比较 `claim_first_citation_v1` 与 `claim_first_citation_v1_1`。v1.1 的新增规则是：如果 verdict 为 supported 或 refuted，supporting evidence 必须包含至少一个干净 doc_id；如果没有干净支持证据，应输出 insufficient。

## 3. 指标解释

本报告沿用 Matrix v1 的核心指标 `escape_rate`。它是严格复合指标，不等同于普通 claim accuracy。一个回答只有同时满足以下条件才算 escape：

1. `claim_verdict` 与 gold verdict 一致。
2. `supporting_evidence` 不包含 contaminated citation。
3. 在需要支持证据时，decisive verdict 必须给出干净 supporting evidence；证据不足时应输出 `insufficient`。
4. 在 L5 generated-lore 场景中，不应把 generated lore 过度断言为 `supported` 或 `refuted`。

因此，claim accuracy 高但 escape rate 低，不一定意味着模型“不知道答案”；也可能意味着它引用了错误证据、没有给出必要干净证据，或在 generated-lore 场景中过度断言。Matrix v1.1 的 escape decomposition 正是为了区分这些机制。

## 4. 多种子复现：信息卫生效应不是单 seed 偶然

多种子复现最直接的结果如下。表中数值为 L3-L5 加权平均，每个单元覆盖 216 个 scored predictions。

| 模型 | 策略 | L3-L5 平均 escape | Claim accuracy | Contaminated citation rate | L5 overclaim rate |
| --- | --- | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | `naive_bm25` | 0.343 | 0.440 | 0.618 | 0.227 |
| `openai/gpt-4o-mini` | `primary_preserve` | 0.917 | 1.000 | 0.012 | 0.000 |
| `openai/gpt-4o-mini` | `hygienic_combo` | 0.898 | 0.995 | 0.042 | 0.005 |
| `openai/gpt-5.4-mini` | `naive_bm25` | 0.389 | 0.565 | 0.606 | 0.102 |
| `openai/gpt-5.4-mini` | `primary_preserve` | 1.000 | 1.000 | 0.000 | 0.000 |
| `openai/gpt-5.4-mini` | `hygienic_combo` | 1.000 | 1.000 | 0.000 | 0.000 |

这张表支持两个判断。第一，检索卫生对 L3-L5 的平均影响远大于 naive retrieval 下的模型规模差异。`openai/gpt-5.4-mini + naive_bm25` 的平均 escape 只有 0.389，低于 `openai/gpt-4o-mini + primary_preserve` 的 0.917 和 `openai/gpt-4o-mini + hygienic_combo` 的 0.898。第二，更强模型并非无用：在 naive BM25 下，`openai/gpt-5.4-mini` 的 L5 claim accuracy 为 0.694，高于 `openai/gpt-4o-mini` 的 0.319，L5 generated-lore overclaim rate 也从 0.681 降到 0.306。但这不足以形成可靠 escape，因为 L5 contaminated citation rate 仍高达 0.819。

分难度看，L4 是最稳定的 naive retrieval 失败点：

| 模型 | 策略 | L3 escape | L4 escape | L5 escape | L4 CCR |
| --- | --- | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | `naive_bm25` | 1.000 | 0.000 | 0.028 | 1.000 |
| `openai/gpt-4o-mini` | `primary_preserve` | 0.875 | 0.917 | 0.958 | 0.000 |
| `openai/gpt-4o-mini` | `hygienic_combo` | 0.931 | 0.903 | 0.861 | 0.000 |
| `openai/gpt-5.4-mini` | `naive_bm25` | 1.000 | 0.000 | 0.167 | 1.000 |
| `openai/gpt-5.4-mini` | `primary_preserve` | 1.000 | 1.000 | 1.000 | 0.000 |
| `openai/gpt-5.4-mini` | `hygienic_combo` | 1.000 | 1.000 | 1.000 | 0.000 |

L3 的 naive escape 为 1.000，说明当前 L3 false-consensus 构造在这三个新 seed 上没有稳定压垮模型。相反，L4 hidden-primary 把 BM25 的弱点暴露得非常清楚：primary source 被隐藏或挤出后，两个模型都引用污染材料，L4 contaminated citation rate 均为 1.000。L5 则说明 generated lore 的问题不只是 verdict 判断，还包括污染引用和 abstention 纪律。

这要求后续叙述更精确：Matrix v1.1 不是证明“所有污染都会击穿 naive BM25”，而是证明“当 primary source 被污染复读挤出，或 generated lore 被包装成可引用材料时，单纯升级模型不足以保证 escape”。

## 5. Metadata/source spoofing：卫生机制本身也需要抗伪装

Noisy metadata/source spoofing stress 的核心发现是：`hygienic_combo` 对高噪声更稳健，而单纯 `primary_preserve` 在 L4 上退化明显。

| Metadata noise | `primary_preserve` 平均 escape | `hygienic_combo` 平均 escape | `primary_preserve` claim accuracy | `hygienic_combo` claim accuracy |
| ---: | ---: | ---: | ---: | ---: |
| 0% | 0.986 | 0.986 | 1.000 | 1.000 |
| 10% | 0.958 | 0.958 | 0.972 | 0.972 |
| 25% | 0.917 | 0.972 | 0.931 | 0.986 |
| 50% | 0.778 | 0.917 | 0.778 | 0.944 |

L4 是退化中心：

| Metadata noise | `primary_preserve` L4 escape | `hygienic_combo` L4 escape |
| ---: | ---: | ---: |
| 0% | 1.000 | 0.958 |
| 10% | 0.875 | 1.000 |
| 25% | 0.750 | 0.958 |
| 50% | 0.333 | 0.792 |

该结果的解释需要谨慎。Noisy stress 中 contaminated citation rate 始终为 0.000，generated-lore overclaim rate 也始终为 0.000。这意味着模型并不是明显“引用了污染文档”而失败，而是在 metadata 被伪装后更难恢复正确 claim verdict 或正确识别哪些材料应被作为 primary support。换言之，当前 scorer 能看到引用没有污染，但模型和检索器仍可能因 source-type、title、visible-citation 等可见线索被扰动而错过正确证据。

这对系统设计有直接含义：primary preservation 不能只依赖容易伪造的 metadata 字段。下一步应将 primary 识别建立在多重信号上，例如内容结构、时间一致性、引用链可追踪性、声明粒度和跨文档矛盾关系，而不是只看 source type 或标题。

## 6. Escape decomposition：同一低分可能对应不同失败机制

Escape decomposition 从 Matrix v1 主运行复算，并把 full escape 拆成四个条件。按 L0-L5 加权平均后，可以看到不同策略的失败机制差异。

| 模型 | 策略 | Claim correct | Clean support | Has required support | L5 abstention ok | Full escape |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | `naive_bm25` | 0.722 | 0.653 | 1.000 | 0.896 | 0.646 |
| `openai/gpt-4o-mini` | `careful_bm25` | 0.833 | 0.944 | 0.514 | 1.000 | 0.458 |
| `openai/gpt-4o-mini` | `primary_preserve` | 1.000 | 0.979 | 0.903 | 1.000 | 0.882 |
| `openai/gpt-4o-mini` | `hygienic_combo` | 0.993 | 0.972 | 0.882 | 0.993 | 0.854 |
| `openai/gpt-5-mini` | `naive_bm25` | 0.833 | 0.472 | 0.993 | 1.000 | 0.465 |
| `openai/gpt-5-mini` | `careful_bm25` | 0.819 | 0.910 | 0.986 | 1.000 | 0.715 |
| `openai/gpt-5-mini` | `primary_preserve` | 0.979 | 0.903 | 0.993 | 1.000 | 0.875 |
| `openai/gpt-5-mini` | `hygienic_combo` | 1.000 | 0.931 | 0.986 | 1.000 | 0.917 |
| `openai/gpt-5.4-mini` | `naive_bm25` | 0.771 | 0.681 | 1.000 | 0.938 | 0.681 |
| `openai/gpt-5.4-mini` | `careful_bm25` | 0.833 | 0.993 | 1.000 | 1.000 | 0.833 |
| `openai/gpt-5.4-mini` | `primary_preserve` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| `openai/gpt-5.4-mini` | `hygienic_combo` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

三种失败机制值得区分。

第一，`openai/gpt-4o-mini + careful_bm25` 的 claim correctness 和 clean support 都不低，但 required support 只有 0.514。这说明 prompt 让模型更谨慎，却经常没有在 decisive verdict 下给出必要 clean doc_id。它失败在输出纪律和证据结构，而不主要失败在引用污染。

第二，`openai/gpt-5-mini + naive_bm25` 的 claim correctness 为 0.833，但 clean support 只有 0.472。这说明模型经常能判断方向，却仍把污染材料放进 supporting evidence。这个机制与 `careful_bm25` 的“缺支持证据”不同。

第三，`openai/gpt-5.4-mini + primary_preserve/hygienic_combo` 的四个组成项均为 1.000，说明在当前 Matrix v1 主运行中，高能力模型加证据卫生策略可以同时满足 claim 判断、引用干净、必要证据和 L5 abstention 条件。但这不能直接外推到 noisy metadata stress，因为后者已经显示高噪声下检索卫生策略会退化。

因此，后续报告不应只报一个 escape rate。至少应同步报告 claim correctness、clean support、required support 和 generated-lore abstention，否则难以判断修复应落在 prompt、retriever、scorer 还是数据构造上。

## 7. Prompt v1.1 preflight：规则增强有效，但不能替代检索修复

`claim_first_citation_v1.1` 的设计目标很窄：要求 supported/refuted verdict 必须给出至少一个干净 supporting doc_id，没有干净支持证据时应输出 insufficient。Preflight 结果如下：

| Prompt | L0 escape | L3 escape | L4 escape | L5 escape | L5 CCR |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claim_first_citation_v1` | 0.250 | 0.500 | 0.000 | 0.917 | 0.083 |
| `claim_first_citation_v1_1` | 1.000 | 1.000 | 0.000 | 1.000 | 0.000 |

这个结果支持 prompt v1.1 在 L0、L3 和 L5 的局部价值。它修复了很多“claim 正确但 evidence 字段不满足复合 escape 条件”的问题，并减少 L5 污染引用。

但 L4 是关键反例。在 L4 上，v1.1 的 claim accuracy 仍为 0.000，escape 仍为 0.000，contaminated citation rate 从 0.333 升到 1.000。这并不说明 v1.1 的规则没有意义，而是说明规则在 hidden-primary 场景下被 BM25 上下文上限限制：如果上下文里最可见的材料仍是污染复读，模型可能会更稳定地把污染 doc_id 当作唯一可用支持证据。

因此，v1.1 prompt 不应单独作为主实验修复发布。更合理的下一步是把 v1.1 prompt 与 `primary_preserve`、`hygienic_combo` 结合做完整 preflight，并比较它是否能在不伤害 L4 primary recovery 的前提下提高 required-support discipline。

## 8. 阶段性结论

Matrix v1.1 对 Matrix v1 的主张既加强又限定。

加强之处在于：在三个新 seed 的 L3-L5 关键难度上，信息卫生策略相对 naive BM25 的优势稳定存在。最有力的证据是 L4 hidden-primary：两个模型的 naive BM25 escape rate 均为 0.000，contaminated citation rate 均为 1.000；而 `primary_preserve` 和 `hygienic_combo` 在 `openai/gpt-5.4-mini` 上均达到 1.000 escape，在 `openai/gpt-4o-mini` 上也保持 0.875 到 0.958 的单难度 escape。

限定之处在于：L3 false-consensus 在多种子复现中对 naive BM25 并不稳定困难；metadata spoofing 可以在不产生 contaminated citation 的情况下显著降低 L4 escape；prompt-only 支持证据规则可以修复输出纪律，但不能恢复被 BM25 挤出的 primary source。因此，当前证据最强支持的是一个更具体的命题：

> 当 primary evidence 被污染复读挤出，或 generated lore 被包装成可引用材料时，单纯模型规模提升不能可靠保证污染逃逸；检索层面的 primary preservation、污染抑制和证据供应链卫生是必要条件。但这些卫生机制自身必须接受元数据伪装压力测试。

这个命题比“更强模型不重要”更准确。模型能力仍然影响 claim accuracy、overclaim 和 JSON 输出稳定性；但如果检索器持续供给污染证据，模型能力无法自动补上缺失的 primary source。

## 9. 局限与替代解释

第一，本轮仍是合成 mini-web 实验，不代表开放 web、企业知识库或真实 adversarial SEO 环境。合成数据的优点是 gold labels、污染标签和 upstream roots 可审计；代价是分布、文体和攻击策略受生成器约束。

第二，多种子复现只覆盖 L3、L4、L5。它强化了关键污染难度的结论，但没有检查 L0-L2 在新 seed 下是否保持同样的 clean control、mild pollution 和 temporal drift 行为。

第三，bootstrap CI 是按 scored rows 抽样得到的近似区间，不是严格按 seed 或 episode family 聚类的层级置信区间。由于每个 seed 内的任务由同一生成器产生，后续正式论文应考虑 cluster bootstrap 或 mixed-effects 分析。

第四，metadata noise 是受控扰动，不等同于真实攻击者的自适应伪装。当前处理改动 source type、标题和 visible citations，但没有生成更复杂的语义伪装、跨站引用环、时间戳操纵或 search-rank manipulation。

第五，prompt v1.1 只在 `openai/gpt-4o-mini + careful_bm25` 的 48-task preflight 上运行。它不能证明 v1.1 在其他模型、其他 retriever 或完整 L0-L5 矩阵中都有收益。

第六，scorer 的 gold truth 和污染判断仍由合成数据生成。虽然这使自动评分可复现，但后续论文若要主张更广泛的事实性评测意义，需要加入人工审计或外部 benchmark 对照。

## 10. 下一步实验建议

1. 把 `claim_first_citation_v1.1` 与 `primary_preserve`、`hygienic_combo` 组合做完整 preflight，确认它是否能提升 required-support discipline，同时不恶化 L4 hidden-primary。
2. 为 noisy metadata stress 增加内容级伪装和引用链伪装，避免只测试 source type、标题和 visible citations。
3. 对 L4 primary recovery 做机制审计：记录 primary 被检索到的位置、被 prompt 使用的位置，以及被模型拒绝或忽略的原因。
4. 将多种子复现扩展到 L0-L2，至少确认 clean control 与 temporal drift 在新 seed 下没有回归。
5. 在报告层面固定同时呈现 full escape、claim correctness、clean support、required support 和 L5 abstention，避免单指标遮蔽失败机制。
6. 对 bootstrap CI 做按 seed 或 episode family 聚类的稳健性分析。

## 11. 研究伦理与 AI 辅助写作声明

本报告没有引入外部文献、真实个人数据或真实机构事实。所有实验对象均为 EHA 合成数据集中的虚构任务和文档。报告中的数值来自本地实验 artifact 和自动评分结果。

本报告由 AI 助手根据本地实验输出起草，并按 academic-paper-writing 的读者、问题、证据、限制与反驳框架组织。报告没有手工编造实验结果、引用或外部来源；凡涉及结论外推处均以阶段性、合成实验或下一步建议限定。
