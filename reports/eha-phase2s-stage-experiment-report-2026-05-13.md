# EHA Phase 2S 阶段性实验报告：证据诊断与时间工具路由修复

日期：2026-05-13
对象：Epistemic Hygiene Arena Phase 2S scope diagnosis and temporal routing repair
状态：阶段性实测报告，依据本地实验输出生成

## 摘要

本报告总结 Epistemic Hygiene Arena（EHA）当前最新一轮 Phase 2S 实验。Phase 2R 已经把 false-consensus stress pilot 校准到足以击穿标准 BM25 baseline，并显示 `hygienic_combo_top8` 能在高压伪共识场景中恢复较高 claim accuracy；但 Phase 2R 仍暴露出两个阻塞点：第一，模型能给出相对正确的 claim verdict，却不能稳定诊断证据风险类型；第二，主动工具策略没有可靠把 temporal pollution 映射到 `compare_versions`。Phase 2S 因此不是扩大主实验，而是针对这两个阻塞点做修复性 pilot。

本轮实验由三部分组成。Module A 使用 `EHA-v2S-scope-diagnostic`，共 120 个 episode，直接提供 4-8 篇相关文档，比较旧的 `evidence_graph_v3` 与新的 `evidence_diagnostics_v1`。Module B 使用 `EHA-v2S-temporal-routing`，共 60 个 episode，比较静态检索回答、强制版本比较、路由后回答和上一版 3-call tool agent。Module C 复用 `EHA-v2R-stress-pilot` 的 80 个 episode，并在其中 48 个 hard episode 上比较主动工具策略，检查 Phase 2S 修复是否会破坏 Phase 2R 已建立的 false-consensus stress signal。

API run 使用 `openai/gpt-4o-mini`，产生 864 条预测、864 行评分记录和完整 gate 报告。总成本记录为 `record_cost_usd=0.382412`、`spent_usd=0.422466`，未触发 abort。总体 gate 未通过：23 项检查中 16 项通过、7 项失败。通过项说明，Phase 2S 已经把 temporal routing 修复到可用水平：`route_then_answer_v1` 在 temporal cases 上的 `compare_versions_rate` 为 0.983，useful compare rate 为 0.983，claim accuracy 为 0.967，且 hidden-label leakage 为 false。Module C 也保留了 Phase 2R 的核心压力信号：high-pressure BM25 wrong-answer rate 为 0.917，`hygienic_combo_top8` 的 high-pressure recovery delta 为 0.917，claim accuracy 为 1.0。

失败项同样清楚。Module A 的 `evidence_diagnostics_v1` 虽然把 stale、conflict 和 generated-lore recall 分别提高到 0.900、1.000 和 1.000，但 claim accuracy 只有 0.392，diagnostic macro-F1 只有 0.581，no-primary precision 只有 0.385。也就是说，新 schema 更愿意标出风险，却显著过度诊断，把部分本应 supported 的 full-current-primary cases 判成 insufficient 或带有 `no_primary_source`、`partial_support` 风险。Module C 中 `hygienic_combo_top8` 的 contaminated citation rate 仍为 0.164，高于 0.08 gate；integrated regression 的 diagnostic macro-F1 只有 0.404；主动工具最低 escape rate 为 0.604，低于静态 `static_hygienic_combo` 的 0.750，说明工具修复在压力场景中仍可能伤害逃逸能力。

阶段性结论是：Phase 2S 已经修复 temporal routing，但没有修复 evidence diagnosis calibration。当前结果不支持进入 Phase 3 或更大的多模型主实验。下一步应把 `evidence_diagnostics_v1` 从“高召回风险罗列器”修成“先判 claim、再校准风险标签”的诊断器，尤其要压低 no-primary 与 partial-support false positives，并抑制 `hygienic_combo_top8` 的 contaminated citation。

## 1. 研究问题与读者关切

本阶段面向两类读者。一类是研究检索增强生成、agent provenance reasoning、事实性评测和信息污染传播的研究者；另一类是需要在实际 RAG 或知识库 agent 中部署证据卫生机制的工程实践者。读者关心的问题不是单一模型在合成 benchmark 上是否得到高分，而是更具体的机制问题：

1. Phase 2R 发现的证据诊断失败，是否可以通过多标签 `evidence_diagnostics_v1` schema 修复？
2. Temporal pollution 场景中的工具选择失败，是否可以通过 route-then-answer 策略修复？
3. 修复 temporal routing 后，是否仍能保留 Phase 2R 中 `hygienic_combo_top8` 对 high-pressure false consensus 的恢复能力？
4. 新 schema 是否会因为过度标记风险而牺牲 clean 或 fully-supported cases 的 claim accuracy？
5. 当前阶段是否已经足以进入更大的多模型主实验？

本报告的回答是保守的：Phase 2S 支持继续推进 temporal routing 方向，但不支持扩大实验规模。它显示 EHA harness 现在能分别制造 scope diagnosis、temporal routing 和 false-consensus regression 三类压力；但 evidence diagnosis 仍未达到作为主实验测量工具的稳定性要求。

## 2. 实验设计

### 2.1 Module A：Scope Diagnosis

Module A 使用 `EHA-v2S-scope-diagnostic`，seed 为 7319，共 120 个 episode。该模块不测试 retrieval，而是直接向模型提供相关文档，目的是隔离 prompt/schema 对证据风险诊断的影响。episode 分布如下：

| Episode type | 数量 | 目标风险 |
| --- | ---: | --- |
| `full_current_primary_support` | 20 | 当前 primary evidence 完整支持 claim |
| `stale_evidence` | 20 | 证据过期或被新版本覆盖 |
| `conflicting_evidence` | 20 | 当前证据存在冲突 |
| `generated_lore_with_no_primary` | 20 | 缺少 primary source，存在 generated lore |
| `partial_support` | 20 | 证据只支持部分 claim |
| `citation_laundering` | 20 | 引用链存在，但链条不真正支持 claim |

Module A 比较两个 prompt/schema：旧的 `evidence_graph_v3` 与新的 `evidence_diagnostics_v1`。`evidence_diagnostics_v1` 明确要求输出 `claim_verdict`、`evidence_diagnostics`、`critical_risks`、`verification_ledger`、`supporting_evidence` 和 `rejected_evidence`。它的设计意图是把 claim verdict 和多标签风险诊断分开，避免 Phase 2R 中 scope tag 粗粒度分类过于不稳定的问题。

### 2.2 Module B：Temporal Routing

Module B 使用 `EHA-v2S-temporal-routing`，seed 为 8144，共 60 个 episode。该模块专门测试时间版本冲突和工具路由，episode 分布如下：

| Episode type | 数量 | 目标路由行为 |
| --- | ---: | --- |
| `current_policy_overrides_old` | 15 | 比较新旧政策版本 |
| `old_report_retracted_by_new_audit` | 15 | 识别旧报告被新审计撤回 |
| `certification_expired_or_renewed` | 10 | 检查认证过期或更新 |
| `version_history_changes_claim` | 10 | 比较版本历史后改变 claim 判断 |
| `non_temporal_control` | 10 | 非 temporal 控制组 |

比较策略包括 `static_hygienic_combo`、`forced_compare_versions`、`route_then_answer_v1` 和 `tool_agent_3call_policy`。核心 gate 不是工具使用总量，而是 temporal cases 上是否实际调用并有效使用 `compare_versions`。

### 2.3 Module C：Phase 2R Integrated Regression

Module C 复用 `EHA-v2R-stress-pilot`，seed 为 6271，共 80 个 episode。该模块不是新压力构造，而是回归检查：Phase 2S 的新 schema 和 temporal routing 是否破坏 Phase 2R 中已经获得的 false-consensus stress signal。

静态检索器包括 `bm25_top8`、`primary_preserve_top8` 和 `hygienic_combo_top8`。主动工具策略在 48 个 Phase 2R hard episode 上运行，包括 `static_hygienic_combo`、`route_then_answer_v1` 和 `forced_triage_tools`。Module C 的关键指标包括 high-pressure BM25 wrong-answer rate、`hygienic_combo_top8` recovery delta、claim accuracy、contaminated citation rate、diagnostic macro-F1 和 active tool escape rate。

## 3. Gate 结果

Phase 2S API run 未通过总体 gate。失败不是运行失败：`parse_success` 和 `tool_parse_success` 在主要模块中均为 1.0，成本报告显示 `aborted=false`。Gate 失败说明当前修复仍有机制性缺口。

| Gate group | 通过 | 失败 | 主要含义 |
| --- | ---: | ---: | --- |
| Module A scope diagnosis | 4 | 3 | 高召回改善明显，但 claim accuracy、macro-F1 与 no-primary precision 未达标 |
| Module B temporal routing | 6 | 0 | temporal route-then-answer 已达到本阶段要求 |
| Module C integrated regression | 6 | 4 | false-consensus pressure 保留，但 citation contamination、diagnostic F1 与 active-tool harm 未修复 |
| 总计 | 16 | 7 | 不应进入更大主实验 |

失败项集中在两类问题。第一类是 diagnosis calibration：Module A claim accuracy 只有 0.392，diagnostic macro-F1 为 0.581，no-primary precision 为 0.385。第二类是 integrated hygiene：Module C clean-control BM25 claim accuracy 为 0.875，低于 0.90；`hygienic_combo_top8` contaminated citation rate 为 0.164，高于 0.08；Module C diagnostic macro-F1 为 0.404；active tool 最低 escape rate 比静态策略低 0.146，超过 gate 容忍范围。

## 4. Module A：证据诊断修复的收益与代价

| Prompt | n | Claim accuracy | Diagnostic macro-F1 | Stale recall | Conflict recall | Generated-lore recall | No-primary precision | Unsafe miss rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `evidence_diagnostics_v1` | 120 | 0.392 | 0.581 | 0.900 | 1.000 | 1.000 | 0.385 | 0.000 |
| `evidence_graph_v3` | 120 | 0.425 | 0.316 | 0.000 | 0.025 | 0.050 | 0.800 | 0.442 |

`evidence_diagnostics_v1` 的积极信号很明确。相较 `evidence_graph_v3`，它把 diagnostic macro-F1 从 0.316 提高到 0.581，并把 stale、conflict、generated-lore recall 从几乎不可用的 0.000、0.025、0.050 提高到 0.900、1.000、1.000。unsafe scope miss rate 也从 0.442 降到 0.000。这说明新 schema 确实让模型开始显式识别风险，而不是像旧 schema 那样把多数风险吞进粗粒度 `full` 或 supported 判断中。

但代价同样严重。`evidence_diagnostics_v1` 的 claim accuracy 只有 0.392，甚至低于 `evidence_graph_v3` 的 0.425。失败案例显示，在 `full_current_primary_support` 场景中，模型经常在已有 current primary evidence 的情况下预测 `no_primary_source` 或 `partial_support`，甚至把 gold `supported` 判为 `insufficient`。这不是“模型更谨慎”的简单胜利，因为目标任务本身要求在证据充分时承认支持，而不是把所有场景都推向不足。

因此，Module A 的核心结论不是“新 schema 失败”或“旧 schema 更好”，而是：新 schema 修复了风险召回，却引入了严重过度诊断。下一轮必须把 claim verdict calibration 作为一等目标，否则多标签风险诊断会把 benchmark 推向另一个偏差：少犯 overclaim，但大量制造 false alarm。

## 5. 多标签诊断的具体失衡

| Flag | Precision | Recall | F1 | 解释 |
| --- | ---: | ---: | ---: | --- |
| `stale` | 0.447 | 0.879 | 0.593 | 召回可用，但 false positives 偏多 |
| `conflict` | 0.468 | 0.804 | 0.591 | 能识别冲突，但边界仍粗 |
| `generated_lore` | 0.352 | 0.798 | 0.489 | 比 Phase 2R 有改善，但 precision 不足 |
| `no_primary` | 0.210 | 1.000 | 0.347 | 过度触发最严重 |
| `citation_laundering` | 0.237 | 0.710 | 0.356 | 能捕捉部分 laundering，但误报多 |
| `false_consensus` | 0.341 | 0.859 | 0.488 | 高召回、低 precision |
| `partial_support` | 0.064 | 0.690 | 0.116 | 最严重的误报来源 |

这张表解释了为什么 macro-F1 未过 gate。`evidence_diagnostics_v1` 不是没有学会风险概念，而是把风险概念当作宽泛警报。尤其是 `partial_support` precision 只有 0.064，说明模型几乎把大量非 partial 场景也标成 partial。`no_primary` recall 为 1.000 但 precision 只有 0.210，说明它能找到缺少 primary 的情形，却经常在 primary 已存在时仍触发 no-primary risk。

这个问题会影响 EHA 的研究主张。如果 benchmark 的目标是评估 epistemic hygiene，模型既不能在污染场景中盲目相信证据，也不能在证据充分场景中盲目拒绝。真正有用的 hygiene system 必须同时降低 false negative 和 false positive；Phase 2S 目前只在前者上取得明显进展。

## 6. Module B：Temporal Routing 已基本修复

| Strategy | n | Claim accuracy | Stale recall | Compare versions rate | Useful compare rate | Tool parse success | Unsafe miss rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `forced_compare_versions` | 60 | 0.983 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| `route_then_answer_v1` | 60 | 0.967 | 1.000 | 0.983 | 0.983 | 1.000 | 0.000 |
| `static_hygienic_combo` | 60 | 0.983 | 1.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| `tool_agent_3call_policy` | 60 | 1.000 | 1.000 | 1.000 | 0.967 | 1.000 | 0.000 |

Module B 是本轮最明确的成功项。`route_then_answer_v1` 在 temporal routing task 上达到 0.967 claim accuracy、1.000 stale recall、0.983 compare rate 和 0.983 useful compare rate，全部通过 gate。相较 Phase 2R 中 tool agent 对 `compare_versions` 使用不足的问题，Phase 2S 的 routing prompt 已经能把 temporal 信号映射到正确工具动作。

不过，这个成功需要限定解释。`static_hygienic_combo` 在 Module B 中也有 0.983 claim accuracy 和 1.000 stale recall，尽管它没有调用 `compare_versions`。这说明部分 temporal task 可以被上下文直接解决；因此，`route_then_answer_v1` 的价值不应只看 claim accuracy，而应看它是否形成可审计的工具路径。就这个目标而言，0.983 useful compare rate 是强信号。

下一轮应保留 Module B gate，但不需要把 temporal routing 当作当前最大阻塞点。更重要的是把 Module B 学到的路由能力迁移到 Module C 的污染压力场景，因为 Module C 中主动工具仍然伤害 escape rate。

## 7. Module C：False-Consensus 压力保留，但污染引用仍未压住

| Retriever / Strategy | n | Claim accuracy | Diagnostic macro-F1 | Escape rate | Contaminated citation rate | Stale recall | Conflict recall | Generated-lore recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25_top8` + `evidence_diagnostics_v1` | 80 | 0.775 | 0.361 | 0.588 | 0.361 | 0.625 | 0.659 | 1.000 |
| `hygienic_combo_top8` + `evidence_diagnostics_v1` | 80 | 1.000 | 0.427 | 0.812 | 0.164 | 0.625 | 1.000 | 1.000 |
| `primary_preserve_top8` + `evidence_diagnostics_v1` | 80 | 0.950 | 0.426 | 0.800 | 0.120 | 0.750 | 0.955 | 1.000 |
| `bm25_top8` + `route_then_answer_v1` | 48 | 0.958 | 0.414 | 0.688 | 0.301 | 1.000 | 0.929 | 1.000 |
| `hygienic_combo_top8` + `static_hygienic_combo` | 48 | 0.979 | 0.426 | 0.750 | 0.146 | 0.667 | 1.000 | 1.000 |
| `bm25_top8` + `forced_triage_tools` | 48 | 0.938 | 0.447 | 0.604 | 0.234 | 0.667 | 1.000 | 1.000 |

Module C 传递出两个相互拉扯的信号。积极的一面是，Phase 2R 的压力校准没有被 Phase 2S 破坏。`bm25_top8` 在 high-pressure false-consensus 子集上的 wrong-answer rate 为 0.917，`hygienic_combo_top8` 的 high-pressure recovery delta 也是 0.917，且 `hygienic_combo_top8` 静态 claim accuracy 达到 1.000。这说明当前 harness 仍能制造强伪共识压力，并且 hygienic retrieval 仍然是值得推进的候选机制。

消极的一面是，`hygienic_combo_top8` 仍没有把污染引用压到 gate 要求内。它的 contaminated citation rate 为 0.164，高于 0.08 阈值。相较 `bm25_top8` 的 0.361，这当然是改善；但如果论文主张是“hygienic combo 减少污染证据被引用”，0.164 仍过高。更重要的是，`primary_preserve_top8` 的 contaminated citation rate 为 0.120，低于 `hygienic_combo_top8`，这会削弱“combo 优于 primary preservation”的直接叙述。下一轮必须把 contaminated citation 作为单独优化目标，而不是只看 claim accuracy 和 recovery delta。

## 8. 主动工具：路由能成功，但压力场景中仍可能伤害 escape

| Module | Strategy | n | Escape rate | Claim accuracy | Compare rate | Useful compare rate | Trace rate | Search contradictions rate | Primary request rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| B | `route_then_answer_v1` | 60 | 0.950 | 0.967 | 0.983 | 0.983 | 0.000 | 0.000 | 0.000 |
| B | `tool_agent_3call_policy` | 60 | 1.000 | 1.000 | 1.000 | 0.967 | 0.267 | 0.267 | 0.433 |
| C | `static_hygienic_combo` | 48 | 0.750 | 0.979 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C | `route_then_answer_v1` | 48 | 0.688 | 0.958 | 0.479 | 0.354 | 0.062 | 0.271 | 0.521 |
| C | `forced_triage_tools` | 48 | 0.604 | 0.938 | 0.125 | 0.125 | 0.333 | 0.500 | 1.000 |

Module B 说明工具路由本身可以被修复；Module C 说明修复后的工具行为还没有在综合压力条件下稳定产生收益。`route_then_answer_v1` 在 Module C 中的 escape rate 为 0.688，低于 `static_hygienic_combo` 的 0.750；`forced_triage_tools` 更低，为 0.604。Gate 要求主动工具 escape 不得比静态低超过 0.05，本轮最低差距为 0.146，因此失败。

这表明，工具动作的存在不等于 hygiene improvement。主动工具可能引入额外上下文、额外冲突或额外引用机会，使模型虽然调用了正确动作，却没有把工具结果转化为更干净的 evidence selection。下一轮应把工具结果与证据选择绑定：每个工具调用不仅要返回信息，还要要求模型明确说明哪些 evidence 被纳入 supporting、哪些 evidence 被 rejection、以及为什么它们不应进入最终 citation。

## 9. 与 Phase 2R 的关系

Phase 2R 的主要贡献是压力校准：它证明 high-pressure false consensus 可以稳定击穿标准 BM25，并显示 `hygienic_combo_top8` 是有希望的防御候选。但 Phase 2R 的 scope tag 和 temporal tool planning 失败，使主实验还不能启动。

Phase 2S 对这个问题做了更细拆分。Temporal planning 已经通过 Module B 明确改善；scope diagnosis 则从旧的低召回失败变成新的高召回低精度失败。这个变化有研究价值，因为它把问题从“模型根本不标风险”缩小到“模型不会校准风险边界”。但从实验推进角度看，这仍是阻塞点。

因此，Phase 2S 不是 Phase 2R 的终结版，而是一个诊断性修复回合。它把下一步工作清楚地指向 claim-verdict calibration、risk precision、citation contamination suppression 和 active-tool harm analysis。

## 10. 局限性与替代解释

第一，本轮只评估 `openai/gpt-4o-mini`，不能代表更强模型、更弱模型或不同 agent 架构。第二，Module A 和 Module B 的数据是专门构造的合成压力集，能隔离机制，但不能直接外推到开放 web 或真实企业知识库。第三，Module A 直接提供相关文档，不测试 retrieval；因此它的失败主要归因于 schema/prompt 与诊断校准，而不是检索缺失。第四，Module C 复用 80 个 Phase 2R episode，适合作为 regression check，但按 episode type、retriever 和 strategy 继续切分后，每个子格样本仍有限。第五，当前 cost report 只覆盖本地 API run 的记录成本和花费估计，不代表完整多模型矩阵预算。

一个重要替代解释是：Module A 的低 claim accuracy 可能并非 `evidence_diagnostics_v1` schema 本身不可行，而是 prompt 在“风险诊断”措辞上过度鼓励保守判断。现有结果支持这个解释，因为 stale/conflict/generated-lore recall 已经明显提高，但 `no_primary` 和 `partial_support` precision 极低。换言之，问题更像 calibration failure，而不是 feature failure。

另一个替代解释是：Module C 中主动工具伤害 escape rate，可能不是工具本身有害，而是工具输出后的 evidence selection 和 final citation policy 不够严格。现有结果无法排除这个可能，因为报告指标显示工具调用率和 claim accuracy，却没有逐条审计工具结果如何进入 supporting/rejected evidence。下一轮应增加这个中间层诊断。

## 11. 下一阶段建议

建议暂缓 Phase 3 或多模型主实验，先做 Phase 2S 修订版。

1. 重写 `evidence_diagnostics_v1` 的决策顺序：先判断 current primary 是否完整支持 claim，再判断风险标签；风险标签不得反向覆盖已充分支持的 claim verdict。
2. 单独校准 `no_primary_source` 与 `partial_support`：当前 precision 分别只有 0.210 和 0.064，应加入 hard negative examples，尤其是 full-current-primary cases。
3. 把风险标签分成 critical 与 non-critical 两层：避免模型把边缘上下文噪声升级为会改变 claim verdict 的关键风险。
4. 对 `hygienic_combo_top8` 加入 citation suppression gate：不只报告 claim accuracy，也要求 supporting evidence 和 final citation 排除 contaminated documents。
5. 将 Module B 的 `route_then_answer_v1` 迁移到 Module C 时增加 evidence-selection audit：比较工具调用前后 supporting/rejected evidence 的变化。
6. 保留 Phase 2R high-pressure false-consensus gate：BM25 wrong-answer rate 0.917 说明该压力条件仍有效，不应被更宽松的 aggregate 指标替代。
7. 在 Phase 2S 修订版同时达到 claim accuracy、risk macro-F1、no-primary precision、contaminated citation rate 和 active-tool escape gate 后，再启动更大模型矩阵。

## 12. 可复现信息

本报告依据以下本地项目材料和实验输出生成：

| 类型 | 文件 |
| --- | --- |
| 实验说明 | `eha-mvp/phase2s-experiment.md` |
| Module A 数据 | `eha-mvp/data/phase2s-scope-diagnostic/manifest.json`、`tasks.jsonl`、`documents.jsonl`、`gold_graph.jsonl` |
| Module B 数据 | `eha-mvp/data/phase2s-temporal-routing/manifest.json`、`tasks.jsonl`、`documents.jsonl`、`gold_graph.jsonl` |
| Module C 数据 | `eha-mvp/data/phase2r-stress-pilot/manifest.json`、`tasks.jsonl`、`documents.jsonl`、`gold_graph.jsonl` |
| API run | `eha-mvp/results/runs/phase2s-gpt4omini/predictions.jsonl` |
| 主报告 | `eha-mvp/results/reports-phase2s/summary.md` |
| Gate | `eha-mvp/results/reports-phase2s/phase2s_gate.json` |
| 指标表 | `scope_diagnostic_metrics.csv`、`temporal_routing_metrics.csv`、`integrated_regression_metrics.csv`、`tool_routing_metrics.csv`、`diagnostic_confusion_by_flag.csv` |
| 失败案例 | `eha-mvp/results/reports-phase2s/failure_cases_phase2s.md`、`unsafe_scope_misses.csv` |
| 成本 | `eha-mvp/results/reports-phase2s/cost_report.json` |

复现当前 API run 的核心命令如下：

```bash
uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models openai/gpt-4o-mini \
  --out-dir results/runs/phase2s-gpt4omini \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 50 \
  --hard-cap-usd 150 \
  --abort-cap-usd 300
```

生成报告的命令如下：

```bash
uv run eha-report-2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2s-gpt4omini \
  --out-dir results/reports-phase2s
```

## 13. 研究伦理与 AI 使用说明

本报告没有引入外部文献、未声称真实世界部署有效性，也未把合成 benchmark 结果外推为开放 web 或真实知识库结论。所有数值结论均来自本地实验输出文件；解释性文字由 AI 助手根据这些输出整理，并保留 gate failure、样本规模、合成数据和单模型评估等限制。报告未使用隐藏 gold labels 作为 agent 可见信息的证据；hidden-label leakage gate 在本轮结果中为 false。
