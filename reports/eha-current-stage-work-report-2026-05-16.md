# EHA 当前阶段性工作报告：Step 1 释放闸门与 Step 2 启动边界

日期：2026-05-16
报告状态：阶段性研究与工程移交报告
证据范围：仓库内已有实验输出、机器可读闸门、论文草稿、审计包与无 API 设计/校验报告

## 摘要

本阶段工作的核心结论是：EHA 目前已经具备作为“受控诊断性基准与机制研究”进行 Step 1 释放的主要工程条件和论文叙述条件，但还不能声明为完整可释放版本；唯一不能由代码、重跑或 LLM 辅助审计替代的阻塞项，是主动验证任务的独立人工审计仍为 0/50 行完成。与此相对，Step 2 已经形成了较清晰的启动边界：表面线索压力测试、统计分析合同、外部有效性切片、Phase 2S 结构化 schema 修复路径和启动闸门都已经被写成可执行或可校验的准备材料，但它们目前都不是新的模型证据，也不构成 500-1000 任务扩展或 API 试跑的许可。

因此，本报告的主张是保守的：当前阶段的贡献不在于扩大数据规模，而在于把“哪些证据已经足以支持 Step 1 诊断性论文”“哪些环节仍需人类确认”“为什么 Step 2 不能从任务规模直接推进”这三个问题分开。这个拆分避免把工程完成度误读为科学完成度，也避免把 LLM 辅助检查误读为独立人工验证。

## 读者问题与阶段任务

本报告面向需要判断 EHA 项目当前可信度与下一步投入边界的读者：论文作者、实验维护者、审稿前内部评估者，以及决定是否继续花费模型/API 预算的人。读者关心的问题不是“仓库里是否做了很多工作”，而是：

1. 当前结果能够支持什么强度的论文主张？
2. 哪些证据已经由可重复脚本、机器可读 gate 或论文一致性检查覆盖？
3. 哪些关键项仍缺少独立人工证据？
4. Step 2 的下一步应该是扩大任务量，还是先修复测量接口？

本阶段工作的回答是：Step 1 可接近一个诊断性 release candidate，但不应越过人工审计 gate；Step 2 的主要 blocker 是测量有效性，而不是任务数量不足。

## 证据来源与方法

本报告没有新增外部数据、没有新增模型调用，也没有把无 API smoke run 当作模型实验证据。综合依据来自以下内部材料：

- Step 1 释放检查与覆盖矩阵：`eha_step1_readiness_check.json`、Step 1 completion audit、roadmap release-gate coverage。
- 论文与 artifact 包：opaque-ID 主实验输出、论文表格一致性检查、baseline 文件、最小复现实例、文件 hash manifest。
- 主动验证审计包：50 行人工审计 CSV、wide worksheet、model-blinded worksheet、本地 HTML review 页面、protocol、attestation、finalization script。
- Phase 2S 校准报告：v7 bottleneck、v8-v11 结构化 schema 校准切片、support-role guard、critical-risk repair audit、v12 no-API smoke。
- Step 2 准备材料：surface-cue smoke dataset、balance report、scoring pipeline、design-review worksheet、statistical analysis plan、external-validity design、target context、launch gate。

证据整理遵循三个原则：第一，只把已经由报告或机器可读摘要记录的数值写入报告；第二，区分模型证据、无 API 管线证据、人工审计证据和设计文件；第三，把所有尚未验证的内容写成限制或下一步，而不是写成完成项。

## Step 1：诊断性 release candidate 的条件已经基本成形

Step 1 的目标已经从“通用排行榜式 benchmark”收窄为“受控诊断性 benchmark 与机制研究”。这个定位更符合当前证据：EHA v1 可以展示答案正确性、证据角色清洁度、不确定性纪律、主动验证动作可执行性之间的分离，而不必声称已经完成大规模、外部有效、人工充分验证的 benchmark。

当前 Step 1 的主要通过项包括：

| 项目 | 当前证据 | 阶段判断 |
|---|---|---|
| opaque-ID 主实验 | release-facing artifact 使用 opaque `doc_###`，主输出为 100 tasks / 1000 prediction rows | 可作为主结果来源 |
| semantic-ID 泄漏控制 | artifact 与 paper 的 semantic-ID gate 通过 | 可保留 |
| 四种 generated-lore schema ablation | 三个模型、20 个 generated-lore 任务、120 行 parse-success 输出 | 已足以支持 schema sensitivity 发现 |
| 诊断指标与 operational escape | scoring 与论文 benchmark-design section 均已覆盖 | 已成形 |
| required baselines | ID-only、metadata-only、simple heuristic、random valid schema、always insufficient 均已打包 | 已成形 |
| 最小复现包 | `reproduce_minimal.sh`、examples、scorer、README 与 file manifest | 工程上可复验 |
| 论文定位 | abstract、introduction、discussion、limitations 已限制为 controlled diagnostic release | 与证据强度一致 |

最近一次 dry-run 验证显示：`uv run pytest -q` 为 194 passed；`verify_step1_release.sh --allow-blocked` 完成最小示例、测试套件、论文构建、paper-aware readiness check 和 diff whitespace 检查；readiness 仍为 `blocked`，但 blocker 集中在人工审计，而不是 artifact 包或论文一致性。

## 仍阻塞 Step 1 的不是工程，而是独立人工审计

Step 1 目前最重要的限制是主动验证 human audit 仍未完成。审计包已经存在 50 行，覆盖 clean、generated_lore、false_consensus、buried_primary、conflicting_evidence 五类条件，每类 10 行；但当前 human-audit manifest 和 validation report 均显示：

| 审计项 | 当前状态 |
|---|---:|
| human audit rows | 50 |
| complete human-labeled rows | 0 |
| required binary labels | 8 个字段，当前未填 |
| auditor notes | 当前为空 |
| attestation | 模板已存在，尚未完成 |
| readiness outcome | blocked |

这意味着 Codex-assisted audit 或浏览器界面验证只能说明审计流程可执行，不能说明独立人工判断已经发生。现有 Codex xhigh audit 可以作为 triage 证据，例如它给出了语义有用性、机器可执行性、动作类型等辅助判断，但报告和论文都必须继续把它标为 LLM-assisted triage，而非 human validation。

这个限制不是形式主义。主动验证任务评估的是模型是否提出可执行、有用且目标正确的验证动作；这种判断涉及人类对动作含义、执行成本和任务语境的解释。如果没有独立人工标签，Step 1 论文最多能声称“审计机制和样本已经准备好”，不能声称“主动验证动作已通过人类验证”。

## Step 2：当前不应扩展规模，原因是测量接口仍未稳定

Step 2 的准备工作已经显著推进，但结论是 no-go，而不是 launch ready。`eha_step2_launch_gate.json` 和对应 Markdown 报告汇总了各 gate，当前结果为：

| Gate | 状态 |
|---|---|
| Step 1 release ready | false |
| surface-cue design review complete | false |
| surface-cue pilot ready | false |
| external validity API ready | false |
| deterministic support-role validation ready | true |
| structural schema repair passed | false |
| target venue and budget defined | false |

这组结果说明，Step 2 的关键问题不在于“还没有 500-1000 个任务”，而在于如果现在扩大任务量，会把尚未稳定的 measurement interface 放大。尤其是 Phase 2S 的 static diagnostic labels 暴露出结构化风险标签的混淆：模型可以看到污染材料并正确拒绝它们，但 schema 仍可能把“可见污染环境”误写成“最终 verdict 的关键风险”。

## Phase 2S：support-role guard 已可用，critical-risk repair 仍未通过

Phase 2S v8-v11 的 35 行结构化校准切片专门从 v7 失败模式中抽样，覆盖 clean control、false consensus、citation laundering、temporal pollution、generated lore、no primary、mixed source corruption 等七类，每类五行。这个切片不是代表性 benchmark 估计，而是用于压力测试 schema 能否分开两类内容：

- `environment_observations`：模型可以记录检索环境中可见的污染、冲突、过时或重复线索。
- `critical_risks`：只记录真正影响最终 verdict 或必要工具动作的风险。

四个 API 校准尝试都未达到小切片通过标准：

| Run | Rows | Claim accuracy | Contaminated citation rate | Critical-risk macro-F1 | Support-role valid | Decision |
|---|---:|---:|---:|---:|---:|---|
| v8 structural | 35 | 0.886 | 0.000 | 0.369 | 0.886 | no-go |
| v9 structural-recall | 35 | 0.886 | 0.029 | 0.299 | 0.886 | no-go |
| v10 structural-contract | 35 | 0.886 | 0.086 | 0.404 | 0.857 | no-go |
| v11 role-disciplined | 35 | 0.857 | 0.000 | 0.240 | 0.857 | no-go |

这四组结果给出一个有用的负发现：仅靠 prompt wording 或单一 JSON schema 约束，很难同时获得干净的 supporting evidence 与足够好的 critical-risk recall。v10 的 critical-risk macro-F1 相对最好，但 contaminated citation rate 超过 0.08 阈值；v11 恢复了引用清洁度，却牺牲了 claim accuracy 和 risk recall。

因此，support-role guard 的完成只解决了一个下游消费安全问题：它可以过滤 contaminated、unknown、extraneous、non-empty insufficient 或 not-verdict-direct 的 supporting evidence。它不能替代 critical-risk repair，也不能证明 final-answer-only risk labels 已经可靠。

v12 critical-risk contract 已经作为 no-API heuristic smoke 跑通：35 行预测、report pipeline、parse success 和 scorer path 均可运行，且 API calls 为 0。这个结果只能说明管线和 contract 形状可执行；它不是任何上游模型满足 v12 contract 的证据。

## Surface-Cue：设计烟测完成，但人工设计审查为 0/90

表面线索压力测试是 Step 2 的一个关键外部有效性方向，因为它测试模型是否依赖 source labels、metadata、official-sounding prose、authority spoofing 或 metadata-stripped content 等可见表面特征。当前已完成的是 no-API smoke dataset，而不是模型实验：

| 输出 | 数量 |
|---|---:|
| tasks | 180 |
| documents | 900 |
| gold graph edges | 360 |
| active-verification action-gold rows | 30 |
| pair-level design-review rows | 90 |

该 smoke grid 覆盖六个 task families、三个 claim templates、五个 stress axes 和两种 paired conditions。balance report 显示 0 pair-contract violations、0 visible-leakage hits、0 action-target violations、120/120 clean-support observable rows、180/180 contaminated-observable rows。scoring pipeline 还生成了 540 行 no-API baseline rows，用于验证 scorer path 和暴露 source-type-prior 的失败模式。

但设计审查仍未完成：当前 90 个 pair-level worksheet rows 中，reviewed pairs 为 0，缺少 540 个 label cells 和 90 条 notes，`pilot_ready=false`。因此，这个部分的正确结论是“surface-cue 压力测试具备人工设计审查的材料”，而不是“surface-cue benchmark 已可用于 API 试跑”。

## 统计与外部有效性：合同已成形，实证尚未开始

Step 2 统计计划已经把未来 scaled run 的分析单元、主要 outcomes、task-cluster bootstrap、paired permutation tests、mixed-effects robustness 和 multiple-comparison boundary 写成预注册式合同。它强调主分析单元应该是 task，而不是 model call；主要表格应报告 mean 与 95% CI，而不是仅按三位小数排序模型。

外部有效性设计也已经列出四个候选切片：semi-real enterprise wiki、open-web-like synthetic corpus、human-written pollutants、adaptive generated lore。当前推荐的第一切片是 semi-real enterprise wiki，最小 pilot tasks 为 40；但 API ready 为 false，且必须先完成 Step 1 human audit 和 90-pair surface-cue human design review。

target context 仍不完整：target venue、deadline、submission track、decision owner、API budget、human review budget 都为 TBD 或未确认。这个缺口很重要，因为它避免在没有明确发表目标和预算边界时启动新的模型开销。

## 阶段性主张

基于上述证据，当前阶段可以支持以下主张：

1. EHA v1 已接近一个受控诊断性 release candidate；工程包装、opaque-ID 主结果、论文一致性、baseline、schema sensitivity 和最小复现路径都已基本就绪。
2. EHA v1 还不能被称为完整 release；主动验证 human audit 的 50 行独立人工标签、notes 和 attestation 尚未完成。
3. Step 2 不应从任务规模扩张开始；Phase 2S 已显示测量接口，尤其是 critical-risk labels，与 supporting evidence role validation 之间仍有结构性冲突。
4. 当前最有价值的 Step 2 准备，是先完成人工 gate 与设计 gate，再用固定小切片验证 v12 或后续 schema，而不是直接运行 full C-only 或 500-1000 task expansion。
5. 所有 no-API smoke、heuristic smoke、browser verification 和 Codex-assisted audit 都应按其证据类型陈述，不能升级为模型证据或人工验证。

## 下一步优先级

第一优先级是完成 Step 1 独立人工审计。审计员需要为 50 行填写全部八个 binary labels、设置 `audit_status = human_labeled`、写入非空 `auditor_notes`，并完成 attestation。随后运行 finalization script，重建 artifact，重新跑 paper-aware readiness check 和 release verifier。

第二优先级是完成 90-pair surface-cue human design review。只有当设计审查通过、pilot_ready 变为 true，surface-cue smoke dataset 才能从“设计材料”进入“可考虑小规模模型试跑”的状态。

第三优先级是补齐 target venue、deadline、decision owner、API budget 和 human-review budget。没有这些边界，不应启动新的模型调用。

第四优先级是在上述 gate 清楚后，用固定 35 行切片验证 v12 或后续 critical-risk contract。成功标准应至少包括 critical-risk macro-F1、exact-row rate、claim accuracy、contaminated citation rate 和 support-role validity，而不是只看 claim accuracy。

## 限制与伦理边界

本报告是阶段性综合，不是新的实验论文结果。它没有新增模型调用，也没有新增人工标注。所有数值都来自现有内部报告和机器可读摘要；如果后续 artifact 或 paper 被修改，本文中的 gate 计数和指标需要重新生成。

EHA 当前仍应被描述为 controlled diagnostic benchmark，而不是通用安全评估、生产部署认证、法律/医疗/金融建议系统验证，或模型供应商排行榜。主动验证 action audit 的人工部分未完成前，任何关于“人类验证过模型动作可执行性”的表述都应避免。

## AI 使用说明

本报告由 Codex 根据仓库内已有报告、测试结果、机器可读 gate 和论文/artifact 摘要整理起草；未引入外部来源，未新增实验数据，未替代人工审计。报告中的解释性归纳用于阶段性移交，后续正式论文或 release note 应在人工审计完成后重新核对相应数值与表述。
