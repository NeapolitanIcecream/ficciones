# EHA Phase 2 API Pilot 阶段性实验报告：检索阶段信息卫生与主动验证

日期：2026-05-13
对象：Epistemic Hygiene Arena Phase 2 API pilot
状态：阶段性实测报告，依据本地实验输出生成

## 摘要

本报告总结 Epistemic Hygiene Arena（EHA）当前阶段的 Phase 2 API pilot。前一阶段主实验已经显示，单纯在 final-answer prompt 中要求 citation、来源独立性或 evidence graph 并不足以抵抗同源污染检索洪泛；Phase 2 因此把问题前移到检索阶段，并加入主动验证动作。本轮 pilot 使用 `openai/gpt-4o-mini`，在 24 个合成调查任务、356 篇 agent 可见文档和 147 条 scorer-only 来源依赖边上运行，共产生 168 条预测和 120 行检索指标。

最重要的阶段性结论是：Phase 2 harness 已经能测量检索卫生、primary record recovery、scope tag、工具使用和泄漏风险，但当前 API pilot 还不应升级为完整主实验。Pilot gate 的 7 项检查中有 6 项通过，唯一失败项是 `false_consensus_bm25_wrong_answer_rate_at_least_0_60`：实际 false-consensus BM25 wrong answer rate 只有 0.25，低于预设的 0.60。这说明当前 pilot 的 false-consensus baseline 没有稳定制造预期压力，或者 evidence-graph baseline 已经能在这个小样本中逃逸多数伪共识陷阱。无论哪一种解释成立，结论都应是先修正任务难度与 gate 口径，再启动 120-episode 或多模型正式运行。

在通过的检查中，几个信号仍然有研究价值。`primary_preserve_top8` 在 false-consensus 子集上把 primary recall 从 0.75 提高到 1.00；`oracle_root_dedup_top8` 把 false-consensus pollutant saturation 从 0.6875 降到 0.125，但它使用 scorer-only upstream roots，只能作为诊断上界。全体任务上，`primary_preserve_top8` 的 claim accuracy 为 0.958，`heuristic_root_dedup_top8` 为 0.917，标准 `bm25_top8` 为 0.903。主动验证的 `tool_agent_2call` claim accuracy 为 0.958，JSON parse success 为 1.0，且没有 hidden-label leakage。不过 scope accuracy 只有 0.417，`halupedia_trap` 的 claim accuracy 只有 0.143，说明当前系统仍不善于区分“主张对错”和“证据范围是否足够”。

## 1. 研究问题与读者关切

本阶段的目标读者是研究 RAG agent 可靠性、信息供应链安全、事实性评测和可复现实验设计的研究者与系统开发者。Phase 1 的问题是：在污染信息生态中，prompt 级信息卫生要求能否避免模型被坏证据带偏。Phase 2 的问题更具体：

1. 检索阶段的 primary-preserve、root-dedup 和更大的 top-k 是否能改善 primary record 可见性与证据覆盖率？
2. 当同一上游错误被大量复读时，检索器和 agent 能否识别伪共识并逃逸污染叙事？
3. 主动验证工具是否能把“证据不足”转化为可执行动作，而不是只在最终回答中声明不确定？
4. 新的 verdict schema v2 是否修复 Phase 1 中 `mixed`、`refuted` 和 `insufficient` 混淆的问题？

本报告只回答 pilot 能支持的范围：一个模型、一个 24-task pilot set、一组固定检索器与工具策略。它不声称 Phase 2 已经证明某个检索防御在真实开放 web 上有效，也不把 diagnostic oracle baseline 当作可部署系统。

## 2. 实验设计

### 2.1 数据集

Pilot 数据集由 `eha-mvp/data/phase2-pilot/manifest.json` 记录，seed 为 5252，共 24 个 episode。

| Episode type | 数量 | 目标失效模式 |
| --- | ---: | --- |
| `clean_control` | 4 | 非污染控制组，确认任务可解 |
| `false_consensus` | 8 | 同源错误被多篇文档复读，模拟伪共识 |
| `citation_laundering` | 4 | 引用链存在但不真正支持目标 claim |
| `temporal_pollution` | 3 | 过期资料与当前记录冲突 |
| `mixed_source_corruption_v2` | 3 | 以 schema v2 拆分 claim verdict 与 scope tag |
| `halupedia_trap` | 2 | 生成式/百科式污染材料被误当证据 |

Phase 2 的 schema v2 不再使用顶层 `mixed` verdict，而是拆成 `claim_verdict` 与 `scope_tag`。这个改动的目标是把“目标主张是否成立”和“证据是否完整、过期、冲突或缺 primary source”分开评分。

### 2.2 检索器与策略

本轮比较 5 个检索器：

| Retriever | 说明 |
| --- | --- |
| `bm25_top8` | 标准 BM25 top-8 baseline |
| `bm25_top12` | 扩大上下文窗口的 BM25 top-12 |
| `primary_preserve_top8` | 在 top-8 中强制保留 primary records |
| `heuristic_root_dedup_top8` | 用可部署启发式减少同源重复 |
| `oracle_root_dedup_top8` | 使用 scorer-only upstream roots 的诊断上界，不可部署 |

最终回答策略包括 `evidence_graph_v2`、`forced_primary_append` 和 `tool_agent_2call`。其中 `tool_agent_2call` 允许两轮 corpus-only 工具动作，例如 `request_primary_record`；工具不得访问 gold labels、污染标签或隐藏 upstream roots。

### 2.3 指标

报告使用三组指标。检索阶段包括 `primary_recall_at_k`、`gold_evidence_recall_at_k`、`contaminant_fraction_at_k`、`unique_upstream_roots_at_k` 和 `pollutant_saturation_at_k`。最终回答包括 `claim_accuracy`、`scope_accuracy`、`escape_rate`、`primary_recovery_rate`、`valid_primary_support_rate`、`contaminated_citation_rate` 和 ECE。工具相关指标包括 `tool_parse_success`、`primary_request_rate`、`useful_tool_rate` 和 hidden-label leakage 检查。

## 3. Pilot Gate 结果

API pilot 未通过 gate。失败不是因为运行管线崩溃，而是因为 stress baseline 没有达到预设难度。

| Check | 结果 | 观测值 |
| --- | --- | --- |
| Clean-control BM25 evidence-graph accuracy >= 0.90 | 通过 | 1.0 |
| False-consensus BM25 wrong answer rate >= 0.60 | 未通过 | 0.25 |
| Primary-preserve primary recall 提升 >= 0.25 | 通过 | 0.75 -> 1.00 |
| Oracle root dedup 降低 pollutant saturation | 通过 | 0.6875 -> 0.125 |
| Mixed-source v2 不再全零 accuracy | 通过 | 1.0 |
| Tool-agent JSON parse success >= 0.95 | 通过 | 1.0 |
| Tool outputs 不泄漏 hidden labels | 通过 | false |

这个 gate 结果的含义应谨慎解释。False-consensus BM25 wrong answer rate 低于门槛，不能简单写成“防御成功”，因为 gate 的目的正是确认 baseline 足够难。如果 baseline 本身不稳定地产生失败，那么后续比较 primary-preserve、root-dedup 或 tool-agent 的收益就会被高估。

## 4. 检索阶段结果

| Retriever | n | Primary recall | Gold evidence recall | Contaminant fraction | Unique roots | Pollutant saturation |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25_top8` | 24 | 0.875 | 0.875 | 0.583 | 4.708 | 0.536 |
| `bm25_top12` | 24 | 0.917 | 0.917 | 0.469 | 7.792 | 0.434 |
| `primary_preserve_top8` | 24 | 1.000 | 1.000 | 0.562 | 4.875 | 0.516 |
| `heuristic_root_dedup_top8` | 24 | 1.000 | 1.000 | 0.479 | 5.583 | 0.427 |
| `oracle_root_dedup_top8` | 24 | 0.958 | 0.958 | 0.172 | 8.000 | 0.125 |

三点值得保留。第一，`primary_preserve_top8` 成功解决 primary visibility 问题，但不等于污染去除：它的 contaminant fraction 仍为 0.562，pollutant saturation 仍为 0.516。第二，`heuristic_root_dedup_top8` 同时达到 1.000 primary recall 和较低污染饱和度，说明可部署启发式值得继续扩大测试。第三，`oracle_root_dedup_top8` 显著降低污染饱和度，但它使用隐藏 upstream roots，只能用于估计上界和校准启发式方法。

## 5. 最终回答结果

| Retriever | n | Claim accuracy | Scope accuracy | Escape rate | Primary recovery | CCR | ECE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `bm25_top8` | 72 | 0.903 | 0.417 | 0.889 | 0.972 | 0.032 | 0.042 |
| `bm25_top12` | 24 | 0.875 | 0.417 | 0.875 | 0.958 | 0.042 | 0.044 |
| `primary_preserve_top8` | 24 | 0.958 | 0.458 | 0.875 | 1.000 | 0.014 | 0.019 |
| `heuristic_root_dedup_top8` | 24 | 0.917 | 0.417 | 0.917 | 1.000 | 0.000 | 0.019 |
| `oracle_root_dedup_top8` | 24 | 0.875 | 0.375 | 0.875 | 1.000 | 0.000 | 0.029 |

表面上看，claim accuracy 已经较高，尤其 `primary_preserve_top8` 达到 0.958。但这不能直接作为 Phase 2 成功结论，因为 gate 显示 false-consensus baseline 难度不足。更稳健的读法是：当前 pipeline 能让 primary-preserve 和 root-dedup 的检索收益进入最终答案，但现有 pilot 还不够难，无法估计这些收益在强污染条件下是否稳定。

Scope accuracy 是更明显的薄弱点。全模型总 scope accuracy 只有 0.417；`citation_laundering` 和 `false_consensus` 的 scope accuracy 都是 0.0。这说明模型经常能判断 claim 方向，却不能可靠标注证据范围、冲突状态或 primary-source 缺失。Phase 2 的 schema v2 方向正确，但 prompt、few-shot 和评分拆分还需要继续改。

## 6. 分机制分析

### 6.1 False consensus：当前 pilot 没有提供足够压力

False-consensus 是本轮 gate 失败的核心。`bm25_top8` + `evidence_graph_v2` 在 duplicate count 为 20 且 primary 不可见时出现 wrong answer rate 1.0；duplicate count 为 50 且 primary 不可见时也为 1.0。但是这些高压格子各只有 1 个样本。按整个 false-consensus BM25 gate 口径汇总后，wrong answer rate 只有 0.25。

这提示下一版 pilot 应按 primary visibility 和 pollutant saturation 分层设 gate，而不是只按 episode type 汇总。否则一个小样本中 primary 可见的任务会掩盖真正需要测量的“primary 被挤出 top-k 后，污染复读是否击穿系统”。

### 6.2 Primary preserve：改善可见性，但不自动降低污染

`primary_preserve_top8` 在全体任务上 primary recall 和 gold evidence recall 都达到 1.000，在 false-consensus 子集上也把 primary recall 从 0.75 提高到 1.00。最终回答中，它的 claim accuracy 为 0.958，primary recovery rate 为 1.000，CCR 为 0.014。

不过它的污染占比仍接近 BM25 baseline。这说明 primary preserve 是“确保好证据进入上下文”的机制，不是“清洗上下文”的机制。后续应把它和 root dedup、source-type diversity 或污染饱和度约束结合，而不是单独作为完整防御。

### 6.3 Root dedup：启发式方法值得扩展，oracle 只能作上界

`heuristic_root_dedup_top8` 的 primary recall 为 1.000，pollutant saturation 为 0.427，最终 CCR 为 0.000。这个结果支持继续发展可部署 root-dedup，但样本量仍太小。

`oracle_root_dedup_top8` 的 pollutant saturation 只有 0.125，显示如果能准确识别同源上游，污染饱和度可被大幅压低。但 oracle 使用 scorer-only upstream roots，不应在论文中作为实用 baseline 宣称，只能作为“防御空间上界”。

### 6.4 Tool agent：主动验证方向可行，但工具策略仍单一

`tool_agent_2call` 的 claim accuracy 为 0.958，tool parse success 为 1.000，primary request rate 和 useful tool rate 都为 0.667，且没有 hidden-label leakage。这个结果说明 corpus-only 主动验证可以安全接入评测管线。

但当前工具使用几乎集中在 `request_primary_record`，`trace_rate` 为 0。对于 citation laundering 和 false consensus，真正需要的是追踪引用链、比较版本和搜索反证。下一阶段应把工具选择压力做进任务和 prompt，而不是让 tool agent 只学会请求 primary record。

### 6.5 Halupedia trap：仍是最弱机制

`halupedia_trap` 的 claim accuracy 只有 0.143，scope accuracy 也只有 0.143，ECE 高达 0.854。这个机制暴露的问题不同于 false consensus：模型不只是被同源复读带偏，也可能在没有足够 primary evidence 时给出过强的 refutation 或错误 scope tag。下一阶段应增加 Halupedia-like 样本，并单独检查 abstention calibration。

### 6.6 Mixed-source v2：schema 修正有效，但不能过早乐观

`mixed_source_corruption_v2` 的 claim accuracy、scope accuracy 和 escape rate 均为 1.000。相较 Phase 1 中 mixed-source corruption 全部失败，这说明把顶层 `mixed` 拆成 `claim_verdict` 与 `scope_tag` 是有效方向。

但这个子集只有 3 个 episode，在 7 个检索/策略组合下形成 21 条预测。它足以说明 schema v2 通过 smoke test，不足以证明混合来源污染已经解决。

## 7. 与前一阶段结果的关系

Phase 1 主实验显示：朴素 `citation_prompt` accuracy 为 0.300，低于 `topk_rag` 的 0.433；`source_independence_prompt` 和 `evidence_graph_prompt` 改善了 provenance recovery 与污染引用率，但在 false-consensus duplicate count >= 5 时仍全部失败。Phase 2 正是在这个发现上推进：不再只调 final-answer prompt，而是测检索阶段和工具动作。

当前 Phase 2 pilot 没有推翻 Phase 1 结论。它更像是暴露了一个实验设计问题：如果新数据集让 baseline 不够脆弱，防御收益就无法被可靠估计。换言之，Phase 2 的下一步不是直接扩大样本，而是先让 stress condition 重新对齐研究问题。

## 8. 局限性

第一，本轮只评估 `openai/gpt-4o-mini`，不能代表其他模型或 agent 架构。第二，pilot set 只有 24 个 episode；若按机制和 primary visibility 继续分层，许多格子只有 1 到 2 个样本。第三，所有数据仍是合成 mini-web，不能直接外推到开放 web、企业知识库或真实攻击环境。第四，`oracle_root_dedup_top8` 使用隐藏 upstream roots，只能作为诊断上界。第五，当前工具策略还没有充分使用 `trace_citation`、`compare_versions` 和 `search_contradictions`。第六，scope accuracy 明显偏低，说明 schema v2 虽然修复了顶层 `mixed` 问题，但 scope 标签教学还不够稳定。

## 9. 下一阶段建议

建议先做一次 Phase 2 pilot 修订，而不是立即启动完整主实验。

1. 重做 false-consensus gate：按 `primary_visibility_under_bm25_top8=False` 和高 `pollutant_saturation_at_k` 分层，确保每个高压格子至少有足够样本。
2. 调整生成器：增加 primary record 被挤出 top-k 的 false-consensus 任务，提高同源复读在 top-k 中的占比，同时保留少量 primary-visible 对照。
3. 组合检索防御：把 primary-preserve 与可部署 root-dedup、source-type diversity 一起测试，避免只保留 primary 而不降低污染饱和度。
4. 强化 tool-agent 策略：让任务需要 `trace_citation`、`compare_versions` 和 `search_contradictions`，并报告不同工具的边际收益。
5. 改进 scope tag prompt：为 `no_primary_source`、`conflicting`、`stale`、`partial` 和 `full` 加入 few-shot 校准，降低 claim 正确但 scope 错误的情况。
6. 在 gate 通过后再扩展到 120-episode 和多模型矩阵，避免把当前 pilot 的小样本偶然性扩大成主结论。

## 10. 可复现信息

本报告依据以下本地项目材料和实验输出：

- `eha-mvp/phase2-experiment.md`
- `eha-mvp/data/phase2-pilot/manifest.json`
- `eha-mvp/data/phase2-pilot/tasks.jsonl`
- `eha-mvp/data/phase2-pilot/documents.jsonl`
- `eha-mvp/data/phase2-pilot/gold_graph.jsonl`
- `eha-mvp/results/runs/phase2-pilot-gpt4omini/predictions.jsonl`
- `eha-mvp/results/runs/phase2-pilot-gpt4omini/pilot_gate.json`
- `eha-mvp/results/reports-phase2-pilot-gpt4omini/summary.md`
- `eha-mvp/results/reports-phase2-pilot-gpt4omini/retrieval_metrics.csv`
- `eha-mvp/results/reports-phase2-pilot-gpt4omini/metrics_by_retriever.csv`
- `eha-mvp/results/reports-phase2-pilot-gpt4omini/metrics_by_episode_type.csv`
- `eha-mvp/results/reports-phase2-pilot-gpt4omini/tool_agent_metrics.csv`
- `eha-mvp/results/reports-phase2-pilot-gpt4omini/false_consensus_v2.csv`
- `eha-mvp/results/reports-phase2-pilot-gpt4omini/failure_cases_phase2.md`
- `eha-mvp/results/reports-phase2-pilot-gpt4omini/cost_report.json`

复现当前 API pilot 的核心命令如下：

```bash
uv run eha-generate-v2 --pilot --seed 5252 --out-dir data/phase2-pilot
uv run eha-phase2 \
  --data-dir data/phase2-pilot \
  --backend api \
  --models openai/gpt-4o-mini \
  --out-dir results/runs/phase2-pilot-gpt4omini \
  --max-output-tokens 3000 \
  --timeout-s 180
uv run eha-report-v2 \
  --data-dir data/phase2-pilot \
  --run-dir results/runs/phase2-pilot-gpt4omini \
  --out-dir results/reports-phase2-pilot-gpt4omini
```

成本报告显示本轮没有触发预算中止：`aborted=false`，`record_cost_usd=0.061351`，`spent_usd=0.067071`，soft cap 为 100 美元，hard cap 为 250 美元，abort cap 为 300 美元。

## 11. AI 使用说明

本报告由 Codex 根据用户指定的本地实验材料、结果表、pilot gate 和失败案例生成。报告中的数值均来自当前仓库的实验输出；未引入新的外部实验证据，未编造未运行的模型结果。解释性判断以“pilot”“当前阶段”“应谨慎限定”等方式标注，以避免把小样本阶段结果外推为正式主实验结论。
