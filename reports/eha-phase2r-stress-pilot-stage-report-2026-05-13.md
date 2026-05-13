# EHA Phase 2R Stress Pilot 阶段性实验报告：压力校准、检索卫生与主动验证

日期：2026-05-13
对象：Epistemic Hygiene Arena Phase 2R stress-calibrated API pilot
状态：阶段性实测报告，依据本地实验输出生成

## 摘要

本报告总结 Epistemic Hygiene Arena（EHA）当前阶段的 Phase 2R stress pilot。上一阶段 Phase 2 API pilot 已经暴露出一个关键问题：false-consensus baseline 在 24-task pilot 中没有稳定制造足够压力，导致检索防御收益难以可靠估计。Phase 2R 因此不直接扩大主实验，而是先重做压力校准：构造 80 个 episode 的 stress pilot，把 false-consensus 条件按 duplicate count、primary visibility 与 pollutant saturation 分层，并加入 citation laundering trace、temporal comparison、generated-lore abstention 和 no-primary-source 场景。

本轮 API pilot 使用 `openai/gpt-4o-mini`，在 `EHA-v2R-stress-pilot` 数据集上产生 592 条预测、480 行检索指标和 592 行评分预测。总体结论是：Phase 2R 已经修复了上一轮最主要的实验设计问题，即高压 false-consensus 条件现在能稳定击穿标准 BM25 baseline；但本轮仍不应进入完整主实验。Gate 的 11 项检查中 7 项通过、4 项失败。通过项显示，`hygienic_combo_top8` 能降低污染饱和度并保持 primary recall，主动工具管线没有 hidden-label leakage，generated-lore 场景没有出现过度断言。失败项则显示，clean-control 稳定性、wrong confidence、scope tag 校准和 temporal-pollution 工具规划仍未达到主实验要求。

最强的积极信号来自检索层。标准 `bm25_top8` 的 overall primary recall 只有 0.600，contaminant fraction 为 0.759，pollutant saturation 为 0.731；`hygienic_combo_top8` 将 primary recall 提高到 0.800，并把 contaminant fraction 降至 0.509、pollutant saturation 降至 0.475。在 high-pressure false-consensus 子集上，BM25 的 wrong answer rate 达到 1.0，pollutant saturation 为 1.0；`hygienic_combo_top8` 把 saturation 降至 0.708，并保持 primary recall 为 1.0。最终回答层也显示防御进入了答案质量：静态 `hygienic_combo_top8` 的 claim accuracy 为 0.988，contaminated citation rate 为 0.042，明显优于 `bm25_top8` 的 claim accuracy 0.787 与 contaminated citation rate 0.268。

最主要的负面信号来自 scope tag。总体 scope accuracy 只有 0.159，major-scope minimum accuracy 为 0.0。混淆矩阵显示，gold `conflicting` 有 78.9% 被预测为 `full`，gold `stale` 全部被预测为 `full`，gold `generated_lore` 有 96.3% 被预测为 `no_primary_source`。这意味着模型经常能判断目标 claim 的方向，却不能可靠描述证据范围、冲突类型、过期状态或 generated-lore 特性。主动验证工具也存在结构性偏差：`tool_agent_3call_policy` 的 trace 与 search_contradictions 使用率很高，但 compare_versions 使用率只有 0.042；gate 中 temporal-pollution compare rate 也只有 0.167。下一阶段应先修复 scope 标注与 temporal comparison planning，再考虑更大的多模型实验。

## 1. 研究问题与读者关切

本阶段面向两类读者：一类是研究 RAG agent 可靠性、事实性评测、信息供应链污染与 provenance reasoning 的研究者；另一类是需要在检索增强系统中部署证据卫生机制的工程实践者。读者关心的问题不是“模型在一个合成 benchmark 上是否高分”，而是更具体的机制问题：

1. 当大量文档复读同一上游错误时，标准检索是否会把 primary evidence 挤出上下文，并诱发错误回答？
2. 检索层的 primary preservation、root dedup 与 hygienic combo 是否能降低污染饱和度，而不仅仅是改善最终 prompt 的措辞？
3. 主动验证工具是否能在 citation laundering、temporal pollution 与 false consensus 场景中执行合适动作？
4. answer schema v3 是否能稳定区分 claim verdict 与 scope tag，避免把“主张方向正确”误当成“证据状态解释正确”？
5. 经过压力校准后，当前实验是否已经足以进入更大的多模型主实验？

本报告的回答范围是一个 stress-calibrated pilot，而不是正式主实验。它可以判断当前 harness、gate 和机制是否准备好进入下一轮；它不能证明某个检索防御已经适用于开放 web、真实企业知识库或攻击者自适应环境。

## 2. 实验设计

### 2.1 数据集与压力分布

Phase 2R 使用 `EHA-v2R-stress-pilot`，seed 为 6271，共 80 个 episode。数据集中包含 1160 篇 agent 可见文档、1160 行 gold document 标注和 630 条 gold graph edge。

| Episode type | 数量 | 目标失效模式 |
| --- | ---: | --- |
| `clean_control` | 8 | 非污染控制组，检查任务本身是否可解 |
| `false_consensus_stress` | 32 | 同一上游错误被多篇文档复读，形成伪共识 |
| `citation_laundering_trace` | 12 | 引用链存在，但链条不真正支持目标 claim |
| `temporal_pollution_compare` | 8 | 过期资料与当前 primary record 冲突 |
| `halupedia_or_generated_lore` | 10 | 生成式或百科式 lore 被误当成证据 |
| `insufficient_or_no_primary` | 6 | 缺少 primary source，要求承认证据不足 |
| `mixed_source_corruption_v2` | 4 | claim verdict 与 scope tag 分离后的混合污染场景 |

False-consensus 子集按 duplicate count 和 primary visibility 分层。Duplicate count 取 5、20、50、100；`primary_visibility_under_bm25_top8` 同时覆盖 visible 与 hidden 条件，每个格子重复 4 次。高压 false-consensus 行被定义为 primary evidence 在 BM25 top-8 下不可见、duplicate count 至少为 20、且 pollutant saturation@8 至少为 0.75。这个定义直接回应上一轮 Phase 2 的问题：不能只按 episode type 汇总，而必须确保 baseline 真的处在 primary 被挤出、污染高度饱和的条件下。

### 2.2 检索器、策略与工具

Phase 2R 比较了 6 个检索器或检索诊断条件：

| Retriever | 说明 |
| --- | --- |
| `bm25_top8` | 标准 BM25 top-8 baseline |
| `bm25_top12` | 扩大上下文窗口的 BM25 top-12 |
| `primary_preserve_top8` | 在 top-8 中强制保留 primary records |
| `heuristic_root_dedup_top8` | 使用可部署启发式减少同源重复 |
| `hygienic_combo_top8` | 组合 primary preservation、root dedup 与检索卫生约束 |
| `oracle_root_dedup_top8` | 使用 scorer-only upstream roots 的诊断上界，不可部署 |

最终回答使用 `evidence_graph_v3` schema，要求输出 `claim_verdict`、`scope_tag`、evidence edges 与 `generated_from` relations。主动验证策略包括 `forced_primary_append`、`forced_triage_tools`、`static_hygienic_combo` 和 `tool_agent_3call_policy`。工具动作覆盖 `trace_citation`、`request_primary_record`、`compare_versions` 和 `search_contradictions`，但这些工具只能访问 corpus-visible 信息，不得读取 gold labels、污染标签或隐藏 upstream roots。

### 2.3 Gate 与指标

Phase 2R gate 共 11 项，分成四类。第一类检查压力校准：clean-control baseline 是否足够稳定、高压 BM25 是否足够脆弱、wrong confidence 是否达到预设门槛。第二类检查检索防御：combo 是否降低污染饱和度、是否保持 primary recall、是否提高高压条件下的 recovery。第三类检查 schema 与工具：scope accuracy 是否过关、tool-agent parse 是否稳定、工具动作是否覆盖 citation、temporal 和 contradiction 场景。第四类检查研究伦理与泄漏：hidden-label leakage 必须为 false，generated-lore overclaim rate 必须受控。

报告使用三组结果。检索阶段关注 `primary_recall_at_k`、`gold_evidence_recall_at_k`、`contaminant_fraction_at_k` 和 `pollutant_saturation_at_k`。最终回答关注 `claim_accuracy`、`scope_accuracy`、`escape_rate`、`contaminated_citation_rate`、`generated_lore_overclaim` 和 ECE。工具阶段关注 `tool_parse_success`、`trace_rate`、`compare_versions_rate`、`search_contradictions_rate`、`primary_request_rate` 和 `tool_diversity`。

## 3. Gate 结果

本轮 Phase 2R API pilot 未通过 gate。失败不是因为运行管线中断：成本报告显示 `aborted=false`，预测、检索指标和评分文件均完整写出。Gate 失败说明当前 stress pilot 仍有机制性缺口，不应升级为完整主实验。

| Check | 结果 | 观测值 |
| --- | --- | --- |
| G1 clean-control BM25 claim accuracy >= 0.90 | 未通过 | 0.875 |
| G2 high-pressure BM25 wrong-answer rate >= 0.70 | 通过 | 1.000 |
| G3 high-pressure BM25 mean wrong confidence >= 0.65 | 未通过 | 0.483 |
| G4 combo 降低 pollutant saturation 至少 0.25 | 通过 | 1.000 -> 0.708，delta 0.292 |
| G5 high-pressure combo primary recall >= 0.90 | 通过 | 1.000 |
| G6 high-pressure recovery delta >= 0.25 | 通过 | 1.000 |
| G7 scope accuracy and major classes | 未通过 | overall 0.159，major min 0.000 |
| G8 tool-agent JSON parse success >= 0.98 | 通过 | 1.000 |
| G9 tool diversity rates | 未通过 | temporal compare rate 0.167 |
| G10 hidden-label leakage is false | 通过 | false |
| G11 generated-lore overclaim rate <= 0.50 | 通过 | 0.000 |

这个结果应分两层解释。第一，Phase 2R 成功修复了上一轮最关键的压力问题：高压 BM25 wrong-answer rate 达到 1.0，说明 false-consensus stress condition 已经足够强。第二，gate 仍然失败，说明 stress condition 足够强并不等于实验已经准备好扩大。尤其是 G7 与 G9 失败直接影响研究主张：如果 scope tag 和 temporal comparison 工具规划不稳定，那么系统即使 claim verdict 正确，也可能无法解释证据状态为什么充分、冲突、过期或不足。

## 4. 检索阶段结果

| Retriever | n | Primary recall | Gold evidence recall | Contaminant fraction | Pollutant saturation |
| --- | ---: | ---: | ---: | ---: | ---: |
| `bm25_top8` | 80 | 0.600 | 0.600 | 0.759 | 0.731 |
| `bm25_top12` | 80 | 0.675 | 0.675 | 0.617 | 0.594 |
| `heuristic_root_dedup_top8` | 80 | 0.700 | 0.700 | 0.683 | 0.645 |
| `primary_preserve_top8` | 80 | 0.800 | 0.800 | 0.709 | 0.681 |
| `hygienic_combo_top8` | 80 | 0.800 | 0.800 | 0.509 | 0.475 |
| `oracle_root_dedup_top8` | 80 | 0.800 | 0.800 | 0.347 | 0.312 |

`bm25_top8` 在 Phase 2R 中暴露出明确缺陷：primary recall 只有 0.600，且污染文档占比和污染饱和度都很高。这说明 stress pilot 确实把检索器推入了 Phase 2 想测的失效区间，而不是像上一轮那样让 baseline 过于容易。

扩大到 `bm25_top12` 能改善 primary recall，并降低污染占比，但仍不能解决同源污染饱和。`primary_preserve_top8` 把 primary recall 提高到 0.800，但 contaminant fraction 仍为 0.709、pollutant saturation 仍为 0.681，说明“保留好证据”并不等同于“清理坏证据”。`heuristic_root_dedup_top8` 降低污染的幅度也有限。

`hygienic_combo_top8` 是当前最值得继续推进的可部署方案。它达到与 `primary_preserve_top8` 相同的 primary recall，同时把 contaminant fraction 从 0.709 降到 0.509，把 pollutant saturation 从 0.681 降到 0.475。`oracle_root_dedup_top8` 仍然表现更好，但它使用 scorer-only upstream roots，只能作为诊断上界，不能作为实际系统能力宣称。

## 5. False-Consensus Stress 分析

Phase 2R 的 false-consensus 结果比上一轮更有解释力。`bm25_top8` + `evidence_graph_v3` 在 primary hidden 的四组 duplicate count 下全部出现严重问题：

| duplicate count | primary visibility | n | wrong-answer rate | pollutant saturation | escape rate |
| ---: | --- | ---: | ---: | ---: | ---: |
| 5 | hidden | 4 | 1.000 | 1.000 | 0.000 |
| 20 | hidden | 4 | 1.000 | 1.000 | 0.000 |
| 50 | hidden | 4 | 1.000 | 1.000 | 0.000 |
| 100 | hidden | 4 | 1.000 | 1.000 | 0.000 |

这组结果说明，当 primary evidence 被挤出 top-8 且同源污染占满上下文时，标准 BM25 baseline 几乎完全无法逃逸伪共识。相比之下，只要 primary visible，`bm25_top8` 的 wrong-answer rate 在对应格子中为 0，escape rate 多数在 0.75 到 1.00 之间。这支持一个机制性解释：失败并不只是模型“不会推理”，而是检索阶段把证据供应链推入了错误结构。

`hygienic_combo_top8` 在同一 false-consensus stress 表中没有出现 wrong-answer rate 大于 0 的格子，并且所有格子的 escape rate 都为 1.0。这个结果非常强，但仍需保守解释。当前样本每格只有 4 个 episode，且只评估了一个 API 模型；因此它支持“进入更大测试的候选机制”，不支持“已经证明防御有效”的结论。

## 6. 最终回答结果

| Retriever | n | Claim accuracy | Scope accuracy | Escape rate | Contaminated citation rate | ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25_top8` | 80 | 0.787 | 0.188 | 0.637 | 0.268 | 0.147 |
| `bm25_top12` | 80 | 0.863 | 0.188 | 0.725 | 0.143 | 0.164 |
| `heuristic_root_dedup_top8` | 80 | 0.950 | 0.212 | 0.787 | 0.089 | 0.179 |
| `primary_preserve_top8` | 80 | 0.988 | 0.188 | 0.950 | 0.034 | 0.201 |
| `hygienic_combo_top8` | 80 | 0.988 | 0.200 | 0.938 | 0.042 | 0.175 |

静态回答结果显示，检索防御确实传导到最终答案。相较 `bm25_top8`，`hygienic_combo_top8` 的 claim accuracy 从 0.787 提高到 0.988，escape rate 从 0.637 提高到 0.938，contaminated citation rate 从 0.268 降到 0.042。`primary_preserve_top8` 的 claim accuracy 同样为 0.988，CCR 甚至略低，但它在检索层保留了较高污染饱和度。因此，如果下一轮要测试可部署机制，`hygienic_combo_top8` 比单独 primary preservation 更符合 Phase 2R 的研究问题。

不过，scope accuracy 几乎没有随 claim accuracy 改善。所有静态 retriever 的 scope accuracy 都只有约 0.188 到 0.212。换言之，模型已经能在许多场景中给出正确的 claim verdict，却仍不能稳定说清楚证据范围。这个缺陷会影响论文主张的可信度：EHA 不只是评估“答案对错”，还要评估 agent 是否理解证据供应链的结构性风险。

## 7. 主动验证结果

| Strategy | n | Claim accuracy | Scope accuracy | Escape rate | Trace rate | Compare versions rate | Search contradictions rate | Primary request rate | Tool diversity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `forced_primary_append` | 48 | 1.000 | 0.104 | 0.750 | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| `forced_triage_tools` | 48 | 0.979 | 0.083 | 0.646 | 0.333 | 0.125 | 0.500 | 1.000 | 0.958 |
| `static_hygienic_combo` | 48 | 1.000 | 0.062 | 0.938 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `tool_agent_3call_policy` | 48 | 0.979 | 0.083 | 0.646 | 0.938 | 0.042 | 0.938 | 1.000 | 1.548 |

主动验证管线的工程稳定性已经基本可用：tool parse success 为 1.0，hidden-label leakage 为 false。`tool_agent_3call_policy` 也不是完全不会使用工具；它的 trace rate 和 search contradictions rate 都达到 0.938，tool diversity 为 1.548。

问题在于工具使用不够贴合机制。Temporal pollution 需要版本比较，但 `tool_agent_3call_policy` 的 compare_versions rate 只有 0.042；gate 中按 temporal-pollution 场景计算的 compare rate 也只有 0.167。因此，当前 agent 更像是学会了“请求 primary、追踪引用、找反证”的通用动作，而不是能按 episode 机制选择最关键工具。下一轮应把 temporal comparison 作为单独训练和 gate 对象，而不是让它淹没在整体 tool diversity 指标里。

另一个问题是，主动验证没有修复 scope tag。所有主动策略的 scope accuracy 只有 0.062 到 0.104，比静态检索还低。这可能说明工具输出帮助 claim verdict，却没有被 prompt 明确转化为 scope reasoning。后续 prompt 应要求模型把每次工具动作映射到一个 scope diagnosis：例如“版本比较发现当前记录推翻旧记录，因此 scope_tag 应为 stale 而不是 full”。

## 8. Scope Tag 失效模式

Scope confusion matrix 是本轮最重要的失败证据。

| Gold scope | 主要错误预测 | 比例 |
| --- | --- | ---: |
| `conflicting` | `full` | 0.789 |
| `stale` | `full` | 1.000 |
| `generated_lore` | `no_primary_source` | 0.963 |
| `partial` | `full` | 0.464 |
| `partial` | `no_primary_source` | 0.321 |

相对稳定的标签只有 `full` 和 `no_primary_source`：gold `full` 有 97.5% 被预测为 `full`，gold `no_primary_source` 有 97.8% 被预测为 `no_primary_source`。这说明模型不是完全无法输出 scope tag，而是偏向少数粗粒度类别，无法区分更细的证据风险类型。

最严重的是 `conflicting` 与 `stale`。Gold `conflicting` 被预测为 `full` 的比例接近 79%，说明模型即使看到相互冲突或同源污染证据，也倾向于把“有证据”误解释成“证据完整”。Gold `stale` 全部被预测为 `full`，说明 temporal reasoning 基本没有进入 scope tag。Gold `generated_lore` 大多被预测为 `no_primary_source`，这比 overclaim 更安全，但仍然丢失了 generated-lore 这一机制标签，削弱了 benchmark 对生成式污染的诊断能力。

这部分结果要求下一版把 scope tag 从附属字段提升为核心任务。仅仅提高 claim accuracy 会掩盖证据状态解释错误；如果论文目标是评估 epistemic hygiene，scope diagnosis 必须成为一等指标。

## 9. Halupedia 与 No-Primary Abstention

上一轮 Phase 2 中，halupedia trap 是最弱机制之一。本轮 Phase 2R 在 claim 层面有明显改善：`halupedia_or_generated_lore` 和 `insufficient_or_no_primary` 的 claim accuracy 均为 1.0，generated-lore overclaim rate 为 0.0，correct insufficient 为 1.0。这说明模型已经学会在缺少 primary evidence 或面对 generated lore 时避免直接过度断言。

但这一改善主要发生在 claim verdict 层面，不代表 generated-lore diagnosis 已经解决。`halupedia_or_generated_lore` 在 `evidence_graph_v3` 下的 scope accuracy 只有 0.04，主动策略下甚至为 0。结合混淆矩阵看，模型通常把 generated lore 当成 no-primary-source，而不是识别为独立的 generated-lore 风险类别。因此下一轮应把 generated-lore abstention 和 generated-lore classification 分开评分：前者已经有积极信号，后者仍是失败点。

## 10. 与前两阶段结果的关系

Phase 1 的主要结论是，单纯在 final-answer prompt 中要求 citation、source independence 或 evidence graph，无法稳定抵抗同源污染检索洪泛。Phase 2 把问题前移到检索阶段和主动验证，但 24-task API pilot 发现 false-consensus baseline 过弱：BM25 wrong-answer rate 只有 0.25，未达到 gate 预设的 0.60。

Phase 2R 正是在这个缺口上推进。它没有直接宣称防御有效，而是先修正实验设计：把 high-pressure false-consensus 明确定义为 primary hidden、高 duplicate count、高 pollutant saturation 的组合。结果显示，这一修正确实让 BM25 baseline 暴露出稳定失败，wrong-answer rate 达到 1.0。

因此，Phase 2R 相比 Phase 2 的主要贡献是实验校准，而不是最终主结论。它证明当前 harness 可以制造足够强的污染压力，也显示 `hygienic_combo_top8` 值得进入下一轮；但由于 scope tag 和 temporal tool planning 未过 gate，它还没有达到主实验前置条件。

## 11. 局限性

第一，本轮只评估 `openai/gpt-4o-mini`，不能代表更强或更弱的模型，也不能代表不同 agent 架构。第二，80 个 episode 对 stress pilot 足够，但若按 episode type、duplicate count、primary visibility、retriever 和 strategy 继续分层，每格样本仍然很小。第三，所有数据仍是合成 mini-web，不能直接外推到开放 web、真实知识库或自适应攻击者环境。第四，`oracle_root_dedup_top8` 使用 scorer-only upstream roots，只能作为诊断上界。第五，当前成本估计只覆盖本地 API pilot 的记录成本，不代表更大多模型矩阵的真实预算。第六，scope tag 与工具规划的失败说明，当前系统尚未真正学会把证据结构诊断转化为最终回答字段。

## 12. 下一阶段建议

建议先做 Phase 2R 修订版，而不是启动完整 Phase 2 主实验。

1. 重写 scope-tag prompt 与 few-shot：重点覆盖 `conflicting`、`stale`、`generated_lore`、`partial` 和 `no_primary_source` 的边界。
2. 把 scope diagnosis 与工具动作绑定：要求模型说明每个工具结果如何改变 `scope_tag`，尤其是 temporal comparison 如何对应 `stale`。
3. 为 temporal-pollution 单独设 gate：`compare_versions_rate_on_temporal_pollution` 应显著高于当前 0.167，并报告比较动作是否真正使用了新旧记录。
4. 保留 Phase 2R 的 high-pressure false-consensus 分层：BM25 wrong-answer rate 1.0 说明该 stress definition 已经有效，不应退回 episode-type 汇总 gate。
5. 扩大 `hygienic_combo_top8` 的验证：下一轮应比较它与 `primary_preserve_top8`、`heuristic_root_dedup_top8` 的稳定性，并报告污染降低是否独立于 primary recall 改善。
6. 分离 generated-lore abstention 与 generated-lore classification：当前系统能避免 overclaim，但不能可靠标出 generated-lore scope。
7. 在修订版 gate 通过后，再运行 120-episode 或多模型矩阵；否则更大的运行只会放大当前 scope 与工具规划缺陷。

## 13. 可复现信息

本报告依据以下本地项目材料和实验输出：

- `eha-mvp/phase2r-experiment.md`
- `eha-mvp/data/phase2r-stress-pilot/manifest.json`
- `eha-mvp/data/phase2r-stress-pilot/tasks.jsonl`
- `eha-mvp/data/phase2r-stress-pilot/documents.jsonl`
- `eha-mvp/data/phase2r-stress-pilot/gold_graph.jsonl`
- `eha-mvp/results/runs/phase2r-stress-pilot-gpt4omini/predictions.jsonl`
- `eha-mvp/results/runs/phase2r-stress-pilot-gpt4omini/phase2r_gate.json`
- `eha-mvp/results/reports-phase2r/summary.md`
- `eha-mvp/results/reports-phase2r/retrieval_metrics.csv`
- `eha-mvp/results/reports-phase2r/static_metrics_by_retriever.csv`
- `eha-mvp/results/reports-phase2r/active_tool_metrics.csv`
- `eha-mvp/results/reports-phase2r/false_consensus_stress.csv`
- `eha-mvp/results/reports-phase2r/scope_confusion_matrix.csv`
- `eha-mvp/results/reports-phase2r/halupedia_abstention.csv`
- `eha-mvp/results/reports-phase2r/failure_cases_phase2r.md`
- `eha-mvp/results/reports-phase2r/cost_report.json`

复现当前 API stress pilot 的核心命令如下：

```bash
uv run eha-generate-2r --seed 6271 --out-dir data/phase2r-stress-pilot
uv run eha-phase2r \
  --data-dir data/phase2r-stress-pilot \
  --backend api \
  --models openai/gpt-4o-mini \
  --out-dir results/runs/phase2r-stress-pilot-gpt4omini \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 50 \
  --hard-cap-usd 150 \
  --abort-cap-usd 300
uv run eha-report-2r \
  --data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2r-stress-pilot-gpt4omini \
  --out-dir results/reports-phase2r
```

成本报告显示本轮没有触发预算中止：`aborted=false`，`record_cost_usd=0.248917`，`spent_usd=0.264204`，soft cap 为 50 美元，hard cap 为 150 美元，abort cap 为 300 美元。

## 14. AI 使用说明

本报告由 Codex 根据用户指定的本地实验材料、结果表、gate 输出和失败案例生成。报告中的数值均来自当前仓库的实验输出；未引入新的外部实验证据，未编造未运行的模型结果。解释性判断以“stress pilot”“当前阶段”“应谨慎解释”等方式限定，以避免把阶段性校准结果外推为正式主实验结论。
