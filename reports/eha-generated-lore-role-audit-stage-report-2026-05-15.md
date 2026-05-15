# EHA Generated-Lore 证据角色审计阶段性工作报告

日期：2026-05-15

对象：Epistemic Hygiene Arena / Frontier Cohort Main Run 后续解释性审计

状态：阶段性研究报告；依据当前仓库内实验输出、审计代码、CSV 汇总、side note、读者叙事草稿和测试记录生成

## 摘要

本阶段工作完成了 EHA frontier 主实验之后的一次解释性收束：把原本容易被读成模型排行榜的结果，重新组织为面向外部读者的“污染证据环境中的认知韧性”叙事，并针对 `generated_lore` 条件下 `gpt-5.4` 的低分进行了证据角色审计。

核心结论是：`gpt-5.4` 在 `generated_lore` 条件上的失败不应简单写成“无法识别生成式传闻”。在当前主实验输出中，它在 40/40 条 generated-lore 记录上都给出了正确的 `insufficient` verdict，并且 40/40 条都把污染材料列入了拒绝证据；真正拉低分数的是结构化字段中的 evidence-role assignment，即 36/40 条记录仍把污染材料放入 `supporting_evidence`，35/40 条出现同一污染材料同时处于支持与拒绝角色的 dual-role 现象。追加的 clarified-schema mini-rerun 进一步支持这一解释：当字段拆为 `clean_supporting_evidence`、`rejected_or_contaminated_evidence` 和 `diagnostic_evidence` 后，`gpt-5.4` 在同一 generated-lore 切片上的 polluted-supporting rate 从 0.900 降至 0.000，parse success 保持 1.000。

这项工作没有修改 frontier 主实验主表，也没有重跑完整主实验。它的贡献是为论文写作补上一个关键解释层：EHA 测到的不只是答案正确性，而是自然语言判断、机器可读证据字段、弃答纪律和后续验证行动之间是否一致。当前证据支持把 generated lore 写成“结构化证据卫生与 agent interface 风险”的案例，而不是单纯的模型知识或事实判断失败。

## 1. 读者问题与阶段定位

本报告面向两类读者。第一类是研究 RAG factuality、hallucination evaluation、misinformation robustness、provenance reasoning 和 agent evaluation 的研究者；他们会追问 EHA 的主结果是否只是另一个 leaderboard，还是确实揭示了不同的失败机制。第二类是构建检索增强系统、事实核查 agent 或企业知识库 agent 的工程实践者；他们更关心模型的结构化输出能否被下游系统安全消费。

本阶段要回答的问题是：

1. 2026-05-15 新增工作相对 frontier 主实验推进了什么？
2. `gpt-5.4` 在 `generated_lore` 条件上的低分应如何解释？
3. 追加的 clarified-schema mini-rerun 是否改变主实验结论？
4. 这些结果应如何进入论文正文、图表和限制部分？

本报告的角色是阶段性研究报告和论文写作备忘，不是最终论文，也不是开放网络事实核查能力声明。

## 2. 本阶段新增 artifact

本阶段围绕两个目标产出材料：外部读者叙事重构，以及 generated-lore 证据角色审计。

| 工作项 | 主要 artifact | 当前状态 |
| --- | --- | --- |
| 读者叙事重构 | `reports/eha-frontier-reader-facing-narrative-2026-05-15.md` | 已完成一页式叙事、核心术语、五张主图计划和三个 case study |
| GPT-5.4 generated-lore side note | `reports/eha-gpt54-generated-lore-evidence-role-side-note-2026-05-15.md` | 已加入 schema clarification mini-rerun 解释 |
| 审计代码 | `eha-mvp/eha/epistemic_generated_lore_audit.py` | 已实现当前 schema 分解、clarified schema、mini-rerun、聚合表和 side note 输出 |
| 审计测试 | `eha-mvp/tests/test_epistemic_generated_lore_audit.py` | 已覆盖 polluted supporting、dual-role、clarified schema 字段和 JSON 提取 |
| 审计输出目录 | `eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/` | 已生成 decomposition CSV、manual audit pack、mini-rerun CSV、cost report 和 checklist |

本阶段明确没有启动新的完整 frontier main run。新增 API 调用只用于 clarified-schema mini-rerun，规模为 20 个 generated-lore tasks × 2 个 prompt 条件 × 3 个模型，共 120 次调用。

## 3. 为什么需要解释性审计

frontier 主实验已经显示，`generated_lore` 是 EHA 中最能暴露证据卫生问题的条件之一。对 `gpt-5.4` 而言，主实验 condition-level 表中 `generated_lore` 的 operational escape 只有 0.100，而 belief correctness 为 1.000。这组数字如果只看总分，容易被误写成模型被 generated lore 欺骗；但如果拆开证据字段，会看到更细的失败机制。

EHA 的关键问题不是“模型最后一句话是不是答对”，而是：

> 当污染材料看起来像来源、摘要或共识时，模型能否把它们放在正确的机器可读角色中：干净支持、反驳证据、污染证据、诊断性证据，或下一步验证目标？

这个问题对 agent 系统尤其重要。人类读者能从自然语言解释中看出模型在拒绝 generated lore；但下游系统可能只读取 `supporting_evidence` 字段。如果污染材料进入这个字段，系统可能把被模型口头拒绝的材料重新解释为机器可执行的支持证据。

## 4. 主要发现

### 4.1 当前 schema 下的 GPT-5.4 不是 belief failure

在既有主实验输出中，`gpt-5.4` 的 generated-lore 切片结果如下。

| 指标 | 数值 |
| --- | ---: |
| n | 40 |
| parse success | 1.000 |
| belief correctness | 1.000 |
| insufficient verdict rate | 1.000 |
| rejected pollutant rate | 1.000 |
| polluted supporting evidence rate | 0.900 |
| dual-role pollutant rate | 0.875 |
| full escape | 0.100 |

这些结果支持一个更窄也更准确的判断：`gpt-5.4` 通常能在自然语言层面识别 generated lore、single-source amplification 和 repost pseudo-consensus，并给出正确的证据不足判断；失败主要发生在结构化字段层面，即把应被拒绝或诊断的污染材料放入 `supporting_evidence`。

因此，论文中不宜写成：

> `gpt-5.4` cannot detect generated lore.

更准确的写法是：

> `gpt-5.4` often recognizes generated lore at the belief layer, but the current schema exposes unstable evidence-role assignment in machine-readable fields.

### 4.2 Clarified schema 支持“角色分配失败”解释

本阶段追加了一个小型 schema clarification mini-rerun。它不改变主实验主表，只测试字段语义是否是 generated-lore 低分的重要诱因。clarified schema 把原先容易混用的 `supporting_evidence` 拆为更明确的证据角色：

| 字段 | 语义 |
| --- | --- |
| `clean_supporting_evidence` | 只能放入干净、非污染、直接支持 claim 的证据 |
| `refuting_evidence` | 放入干净、非污染、直接反驳 claim 的证据 |
| `rejected_or_contaminated_evidence` | 放入 generated lore、repost、stale source、pseudo-consensus 或无一手来源链的权威状文本 |
| `diagnostic_evidence` | 放入用于诊断证据环境为何污染或不足的材料，但不作为 claim 支持 |

mini-rerun 的聚合结果如下。

| Schema | Model | n | Parse success | Belief correctness | Polluted supporting | Dual-role pollutant | Role escape / Full escape |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| current | `gpt-5.4` | 40 | 1.000 | 1.000 | 0.900 | 0.875 | 0.100 |
| clarified | `gpt-5.4` | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| current | `claude-opus-4-7` | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 0.600 |
| clarified | `claude-opus-4-7` | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| current | `gemini-3.1-pro-preview` | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 0.425 |
| clarified | `gemini-3.1-pro-preview` | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |

对 `gpt-5.4` 来说，clarified schema 使 polluted-supporting rate 从 0.900 降至 0.000，dual-role pollutant rate 从 0.875 降至 0.000。这不说明主实验打分错误；它说明原 schema 正在测量一个真实的接口风险：模型在自然语言层面知道材料不可靠，但在通用 `supporting_evidence` 字段中不稳定地混入诊断性或被拒绝材料。

### 4.3 主实验主表不应 retroactively 改写

clarified-schema mini-rerun 的用途是解释机制，而不是替换主实验结果。主实验使用的是当时冻结的 schema 和 scoring contract；如果下游系统约定 `supporting_evidence` 是可消费的支持证据，那么污染材料进入该字段就仍然是 failure。

因此，本阶段结论应写成两层：

1. 主实验层面：`gpt-5.4` 在 current schema 的 generated-lore 条件上 evidence cleanliness 失败，operational escape 很低。
2. 机制解释层面：该失败主要不是 belief-layer 误判，而是 evidence-role assignment 不稳定；更明确的字段可显著降低这一错误。

这一区分让论文更可防守：它承认 schema 设计会影响 measured behavior，同时保留 EHA 对机器可审计证据纪律的评价价值。

## 5. 对论文叙事的影响

本阶段工作把 EHA 的论文叙事从“哪个模型分数最高”推进到“同一模型在不同 epistemic layer 上如何失效”。最适合进入正文的主张是：

> In polluted evidence environments, answer correctness is not enough. Models can produce the right verdict while assigning polluted documents to machine-readable support fields, and that mismatch is a concrete risk for tool-using or retrieval-augmented agent systems.

对应到中文论文备忘，可以写成：

> 在污染证据环境中，事实可靠性不能只按最终答案评价。模型可能在自然语言层面知道证据不足，却在结构化证据字段中把污染材料标为支持，从而把被拒绝的材料重新暴露给下游自动系统。

主文建议安排如下：

1. 用 `reports/eha-frontier-reader-facing-narrative-2026-05-15.md` 中的五张图结构组织结果：任务图、能力分解、任务族难度、证据条件分解、prompt intervention slope。
2. 把 `generated_lore` 作为正文 case study，而不是只放在 appendix，因为它清楚展示 belief correctness 与 evidence cleanliness 的分离。
3. 把 clarified-schema mini-rerun 写成 validity analysis：它说明字段语义会影响角色分配，也说明 EHA 评价的是 schema-grounded evidence hygiene。
4. 在限制部分明确：主结果来自合成 mini-web 和固定 schema；open-web fact-checking、真实企业知识库、法律医学等高风险场景不能直接外推。

## 6. 工程与复现状态

本阶段新增的审计模块承担四类工作：读取主实验 generated-lore 记录、计算当前 schema 下的 belief/role 分解、构造 clarified evidence schema 并运行 mini-rerun、输出聚合表和 side note。相关测试覆盖了最关键的边界：污染材料进入 supporting 字段、同一污染材料同时处于 support/rejected 双重角色、clarified schema 不再暴露通用 `supporting_evidence` 字段，以及模型返回被 markdown 包裹时的 JSON 提取。

当前可复现 artifact 包括：

| Artifact | 内容 |
| --- | --- |
| `generated_lore_belief_vs_role_decomposition.csv` | 当前 schema 下 generated-lore 切片的模型级与 prompt 级分解 |
| `generated_lore_belief_vs_role_rows.csv` | 当前 schema 下逐行 role metrics |
| `gpt54_generated_lore_audit_pack.jsonl` | 15 条代表性 GPT-5.4 generated-lore 案例，用于人工审计 |
| `schema_clarification_mini_rerun.csv` | current schema 与 clarified schema 的聚合比较 |
| `schema_clarification_mini_rerun_rows.csv` | 逐行 clarified/current schema role metrics |
| `clarified_predictions.jsonl` | 120 条 clarified-schema mini-rerun 输出 |
| `side_note_update.md` | 可直接并入论文附录或 validity note 的短说明 |

`cost_report.json` 记录 clarified-schema mini-rerun 的花费为 `spent_usd = 0.278807`。`prompt_to_artifact_checklist.md` 记录本阶段目标已完成，并注明完整测试 `uv run pytest -q` 通过 74 个测试，`uv run python -m compileall eha` 通过。

## 7. 局限与替代解释

第一，mini-rerun 只覆盖 generated-lore 条件、20 个任务、2 个 prompt 条件和 3 个模型。它足以支持字段语义解释，但不足以替代完整 frontier 主实验。

第二，clarified schema 的 role escape 与 current schema 的 full escape 不是完全同一个指标。前者专门测试 evidence-role clarity；后者属于主实验 scoring contract。因此两者适合并列解释，不适合直接说 clarified 分数“修正”了主分数。

第三，自动评分依赖污染文档标签与字段规范。EHA 的优势是可审计合成环境，限制是它不能直接代表开放互联网中的事实核查难度、来源检索质量、真实网页噪声或跨语言证据链。

第四，本报告没有引入外部文献。正式论文中关于 RAG factuality、provenance、misinformation robustness、hallucination evaluation、epistemic vigilance 与 agent evaluation 的定位仍需补充人工核验后的引用。

第五，generated-lore 任务中的组织、项目和文档均来自 EHA 合成环境。报告不提出关于真实机构、真实项目或真实事件的事实断言。

## 8. 下一步建议

下一阶段应优先把本阶段发现转化为论文材料。

1. 固定 generated-lore case study 的正文段落：先给主实验低分，再拆 belief correctness 与 evidence cleanliness，最后用 clarified schema 解释字段风险。
2. 从 `gpt54_generated_lore_audit_pack.jsonl` 中选择 2-3 个代表性案例，人工确认自然语言解释、字段错误和 scorer 判定是否一致。
3. 将 active-verification failure 作为第二个机制案例，与 generated-lore evidence-role failure 形成互补：一个是证据角色问题，一个是下一步行动表达问题。
4. 为正式论文补充外部相关工作引用，并把本阶段所有无外部来源的主张限制在“当前合成 EHA 设置”内。

## 9. AI 辅助写作说明

本报告由 AI 助手根据当前仓库内代码、实验 artifact、CSV 汇总、side note、读者叙事草稿和 checklist 起草。报告没有编造外部引用、真实世界事实、未运行模型结果或未生成 artifact；所有数值均来自当前本地实验输出。AI 辅助主要用于阶段性材料整合、论证组织和读者问题重写。
