# EHA 当前阶段性工作报告：从认知韧性表到 Frontier Cohort 主实验预检

日期：2026-05-14

对象：Epistemic Hygiene Arena / Epistemic Resilience Table v1

状态：阶段性研究与工程报告，依据当前仓库内本地代码、实验输出、审计包、模型预检结果和验证命令生成

## 摘要

本阶段的 EHA 工作已经从早期的 RAG 检索卫生实验，推进到一个更明确的研究对象：污染证据环境中的 LLM epistemic resilience。核心问题不再只是模型能否给出正确答案，而是模型能否在可见材料包含伪共识、陈旧证据、生成式传闻、被埋没的一手证据或直接矛盾时，维持正确判断、干净证据使用、有纪律的不确定性处理，以及必要的主动验证动作。

当前主要产物包括 Epistemic Resilience Table v1、有效性审计包、gpt-5-mini parse-repair 复核管线、以及面向下一轮主实验的 frontier cohort structured-output preflight。任务表包含 100 条任务，覆盖 `packet_judgment`、`evidence_selection`、`active_verification` 三类任务族，以及 `clean`、`conflicting_evidence`、`false_consensus`、`buried_primary`、`generated_lore` 五类证据条件。最终 API 结果包包含 624 条预测，成本报告显示 `spent_usd=2.800352`，`aborted=false`。

阶段性结果支持一个较强但仍需限定的论文主张：在污染信息生态中，LLM factual reliability 不应只按最终答案评价，也应按其对证据环境的认知韧性评价。EHA 当前版本已经能够把答案正确性、证据干净程度、弃答纪律、证据选择和主动验证动作拆开观察。与此同时，结果也显示了重要边界：`epistemic_hygiene_instruction` 不是稳定的全局 prompt fix；`active_verification` 与 `generated_lore` 仍是困难切片；`openai/gpt-5-mini` 的低分主要混入了结构化输出失败问题；自动评分对“正文拒绝污染材料但结构化字段仍列入 supporting evidence”的边界案例需要人工审计限定。

本阶段新增的模型预检工作把下一轮主表 cohort 从单一 OpenAI-family 结果推进到跨 provider 的候选设置。最终可进入后续主表的 frontier cohort 为 `gpt-5.4`、`claude-opus-4-7`、`gemini-3.1-pro-preview`、`deepseek-v4-pro`、`kimi-k2.6`。五个模型在 20-task structured-output preflight 上均达到 20/20 parse success、0 empty output、0 schema missing。DeepSeek 与 Kimi 的预检同时确认：部分空输出不是模型不可用，而是固定 `max_completion_tokens` 策略导致；后续实验必须记录 per-model invocation profile，并同时报告 operational 与 conditional 指标。

## 1. 读者、研究问题与当前角色

本报告面向两类读者。第一类是研究 RAG factuality、provenance reasoning、hallucination evaluation、misinformation robustness 与 agent evaluation 的研究者；他们会关心 EHA 是否提出了比“检索到一手证据会更好”更有解释力的评测对象。第二类是构建检索增强系统、事实核查 agent 或企业知识库 agent 的工程实践者；他们会关心系统失败究竟来自模型判断、证据供应、证据字段纪律、结构化输出稳定性，还是主动验证策略不足。

本阶段报告回答六个问题：

1. EHA 是否已经从 RAG retrieval hygiene benchmark 扩展为 epistemic resilience benchmark？
2. 当前任务表、评分指标、实验结果和审计 artifact 是否足以支撑论文写作进入整合阶段？
3. 现有模型结果暴露出哪些不同失败机制？
4. 人工审计和 parse-repair 复核如何限定自动评分结果？
5. 后续跨 provider 主实验应选择哪些模型，以及应如何记录调用策略？
6. 当前结论能写到什么程度，哪些外推仍必须保留为待证主张？

本报告的角色是阶段性研究备忘与论文写作材料，不是最终论文定稿，也不是对开放互联网事实核查能力的外部验证。

## 2. 当前 artifact 范围

本阶段形成了四组关键 artifact。

| 工作项 | 主要 artifact | 当前状态 |
| --- | --- | --- |
| Epistemic Resilience Table v1 | `eha-mvp/data/epistemic-resilience-v1/`、`eha-mvp/eha/epistemic_resilience.py`、`eha-mvp/results/reports-epistemic-resilience-v1/` | 100 任务、624 条预测、主表与分组表已生成 |
| 有效性审计 | `eha-mvp/eha/epistemic_validity_pass.py`、`eha-mvp/results/reports-epistemic-validity-pass/` | 80 行人工审计包已完成，审计 review 状态为 `no_issues` |
| Parse repair 复核 | `eha-mvp/eha/epistemic_parse_repair.py`、`eha-mvp/results/reports-epistemic-parse-repair-gpt5mini/` | 对 124 条原始 parse-failed rows 尝试复跑与修复，但上游 403 阻断，未产生 repaired metrics |
| Frontier cohort 预检 | `eha-mvp/eha/epistemic_model_preflight.py`、`eha-mvp/results/reports-epistemic-model-preflight-frontier-final-2026-05-14/` | 五个 provider 候选均通过 20-task structured-output preflight |

当前本地验证命令也已更新。`uv run pytest` 通过 63 个测试；`uv run python -m compileall eha` 通过。相较早期报告中的 45-test 状态，当前测试集已经覆盖新增的 model preflight、parse repair、validity pass 与 JSON runner 适配。

## 3. 评测设计：从答案正确到 epistemic escape

Epistemic Resilience Table v1 的中心指标是 `epistemic_escape`。它不是普通 accuracy，而是按任务族定义的复合成功条件。

对 `packet_judgment`，escape 至少要求 verdict 与 gold verdict 一致，supporting evidence 不依赖污染、陈旧、生成式传闻或错误支持材料，并且在证据不足时能够输出 insufficient。对 `evidence_selection`，escape 更重视证据选择：模型需要选择高价值证据、避免重复 upstream root，并避免选择 generated lore。对 `active_verification`，escape 还要求合适的下一步动作，例如寻找 primary source、检查反证、比较版本或追踪 generated lore 来源。

这一设计把早期 Matrix 系列中的 RAG 机制结果纳入更大框架：检索不是简单地“补充事实”，而是在构造模型可见的 evidence environment。模型可能在多个层面失败：关键证据不可见、证据可见但被污染材料捕获、答案方向正确但证据字段不干净、模型不能稳定产生结构化输出，或模型没有采取必要的主动验证动作。

## 4. Epistemic Resilience Table v1 主结果

任务表来自 Matrix v1 数据的再组织，而不是开放 web 数据。`manifest.json` 记录总任务数为 100；三类任务族分别为 `packet_judgment=40`、`evidence_selection=40`、`active_verification=20`；五类证据条件各 20 条。

最终 API 运行覆盖四个模型和两个 prompt 条件：

| 模型 | 覆盖范围 |
| --- | --- |
| `openai/gpt-4o-mini` | 100 任务 x 2 prompts |
| `openai/gpt-5-mini` | 100 任务 x 2 prompts |
| `openai/gpt-5.4-mini` | 100 任务 x 2 prompts |
| `openai/gpt-5.5` | 12-task family-and-condition-stratified sample x 2 prompts |

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

第一，`epistemic_hygiene_instruction` 不是稳定的全局改进。它改善了 `openai/gpt-5.4-mini` 的 avg epistemic escape，也改善了 `openai/gpt-5.5` 小样本，但在 `openai/gpt-4o-mini` 和 `openai/gpt-5-mini` 上低于 standard prompt。论文中不应把 hygiene instruction 写成 universal prompt fix，而应写成与模型、任务族和输出约束交互的 intervention。

第二，`active_verification` 是当前最困难的任务族之一。完整 100 任务模型中，`openai/gpt-4o-mini` 的 active verification escape 为 0.650 或 0.500；`openai/gpt-5.4-mini` 为 0.100 或 0.200；`openai/gpt-5-mini` 为 0.100 或 0.200。要求模型选择验证动作时，单纯给出 verdict 和引用证据不足以代表 epistemic resilience。

第三，`openai/gpt-5.5` 小样本表现较强，但样本量只有 24 条预测，不能与完整 100 任务运行直接等量比较。后续若要把它纳入主表，应扩展到完整任务集，或明确把它放入 exploratory sample。

## 5. 失败机制：parse failure 与证据字段纪律

把主结果拆开后，不同模型的失败机制并不相同。

| 模型 | 记录数 | Row-level escape | Parse success | Belief correctness | Evidence cleanliness |
| --- | ---: | ---: | ---: | ---: | ---: |
| `openai/gpt-4o-mini` | 200 | 0.805 | 1.000 | 0.920 | 0.950 |
| `openai/gpt-5-mini` | 200 | 0.395 | 0.380 | 0.540 | 0.965 |
| `openai/gpt-5.4-mini` | 200 | 0.530 | 1.000 | 0.960 | 0.470 |
| `openai/gpt-5.5` | 24 | 0.792 | 1.000 | 0.917 | 0.917 |

`openai/gpt-5-mini` 的结果主要受结构化输出失败影响。完整 200 条记录中 parse success 约为 0.380，其中 hygiene prompt 为 0.340，standard prompt 为 0.420。由于 benchmark 把 parse failure 计为失败记录，低 escape 不应直接解释为“证据推理更差”。更准确的说法是：在当前 endpoint、schema 与运行设置下，它未能稳定返回可评分的结构化输出。

`openai/gpt-5.4-mini` 暴露出另一类问题。它的 parse success 与 belief correctness 都高，但 evidence cleanliness 低。它经常判断方向正确，却仍把污染材料、陈旧材料或 generated lore 放进 structured support 字段。这正是 epistemic resilience 指标相对于普通 accuracy 的价值：答案正确不能自动证明证据使用干净。

`generated_lore` 是全表中稳定困难的证据条件之一。即使模型常能给出合理 verdict，generated-lore avoidance、source tracing 或证据选择指标仍会拉低 escape。后续论文可以把它写成“正确答案不足以证明模型抵抗了生成式传闻的证据捕获”。

## 6. 有效性审计与人工复核

有效性审计没有新增任务、没有改变 gold labels，也没有对主结果发起新 API 调用。它的作用是检查当前评分和 artifact 是否可用于论文写作。

审计包输出包括：

| Artifact | 用途 |
| --- | --- |
| `parse_repair_audit.csv` | 聚合原始 parse failures 与 token/error patterns |
| `human_audit_sample.jsonl` | 80-case manual audit pack |
| `evidence_cleanliness_failure_taxonomy.csv` | dirty supporting evidence 的行级 taxonomy |
| `heuristic_baseline_appendix.csv` | 带 gold-metadata caveat 的 heuristic 对照 |
| `human_audit_completed.jsonl` / `.csv` | 已完成的 80 行人工审计 |
| `human_audit_summary.md` | 审计方法、bucket counts、scorer agreement 与 paper-use 建议 |

人工审计覆盖 80 行：`generated_lore`、`false_consensus`、`buried_primary`、`active_verification` 各 20 行。审计 review 状态为 `no_issues`。总的 scorer agreement counts 为 yes: 25、no: 8、uncertain: 47；如果排除 uncertain，则 yes 为 25/33。这个结果不表示 scorer 失效，而是提示当前任务中存在大量结构化字段边界案例：模型正文可能拒绝污染材料，但 `supporting_evidence` 或 `selected_doc_ids` 字段仍把同一材料列进去。自动评分把这类输出视为 evidence hygiene failure 是合理的，但论文中需要说明它评价的是结构化证据字段纪律，而不只是自然语言答案是否合理。

审计还确认了几个重要限定。第一，`generated_lore` 标签没有被发现过严；20/20 行均认为 generated/repost 标签合理。第二，`false_consensus` 行常出现正确 refutation 与混合 support 并存的问题。第三，`buried_primary` 中有一部分 hidden-primary active-verification 行没有把 primary contradiction 放进可见 packet，因此不能把所有 belief penalty 简化解释为模型忽视可见证据。第四，parse failures 仍应作为 operational failure：没有可审计答案、动作、support 或 rejection 字段。

## 7. Parse repair 复核边界

针对 `openai/gpt-5-mini` 的 124 条原始 parse failures，本阶段新增了 raw-response-preserving parse repair 管线。该管线会复跑原任务，保存 prompt/response artifact，再在 direct rerun 失败时尝试 JSON repair retry。

实际结果是：124 条原始 parse-failed rows 均被纳入尝试；direct rerun parse successes 为 0；JSON repair retries attempted 为 124；repair retry successes 为 0；final repaired parse successes 为 0。失败原因不是 repair 方法本身已经被证明无效，而是所有 direct rerun 与 repair retry 都在生成前被上游 `403` provider Terms of Service error 阻断。单独 tiny smoke calls 对多个 OpenAI-provider 路由也出现同类阻断或缺失路由。

因此，当前主表不应替换或修正 `openai/gpt-5-mini` 的指标。正确写法是：低 escape 仍保留 parse/schema caveat；修复管线已经建立并能保存 raw artifacts，但 repaired metrics 因 API 路由阻断不可用。

## 8. Frontier cohort structured-output preflight

为了让下一轮主实验摆脱单一模型族和 route-specific parse 问题，本阶段完成了跨 provider structured-output preflight。选择规则是：每个主流 provider 采用当前可路由的 newest flagship candidate；只有通过 20-task structured-output preflight 的模型才能进入后续主表。

Gate 定义如下：

| 条件 | 阈值 |
| --- | ---: |
| `parse_success` | >= 0.95 |
| `empty_output` | 0 |
| `schema_missing_rate` | <= 0.05 |
| LLM repair | disabled |

20-task sample 覆盖 5 个 condition，每个 condition 4 题；任务族分布为 `packet_judgment=8`、`evidence_selection=8`、`active_verification=4`；prompt condition 为 `epistemic_hygiene_instruction`。

最终 cohort decision：

| Provider | Selected model | Preflight result | 调用策略要点 |
| --- | --- | --- | --- |
| OpenAI | `gpt-5.4` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；`max_completion_tokens=4096`；`json_schema` |
| Anthropic | `claude-opus-4-7` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；`max_completion_tokens=4096`；developer/system role 合并进 user；`json_schema` |
| Google | `gemini-3.1-pro-preview` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；`max_completion_tokens=4096`；`json_schema` |
| DeepSeek | `deepseek-v4-pro` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；不传 `max_completion_tokens`；上游使用 `json_object` |
| Kimi | `kimi-k2.6` | 20/20 parse success；0 empty；0 schema missing | 不传 `temperature`；不传 `max_completion_tokens`；`json_schema` |

这个结果有两点方法学含义。第一，`gemini-3.1-pro-preview` 已通过 preflight，因此 Google 主表不需要降级到 `gemini-2.5-pro`。第二，`deepseek-v4-pro` 与 `kimi-k2.6` 的早期 empty output 可以通过 no-cap profile 解决，说明后续主实验不能对所有模型强制相同的短输出上限。主报告应同时给出 `operational_epistemic_escape` 与 `conditional_epistemic_escape`：前者把 parse failure 计为失败，后者只在 parseable outputs 上计算。

## 9. 论文主张与组织建议

当前材料已经足以支持一篇以 epistemic resilience benchmark 为中心的论文草稿，而不是只写成 RAG retrieval benchmark。建议主张收束为：

> 在污染信息生态中，LLM factual reliability 不应只按最终答案评价，也应按其对证据环境的认知韧性评价。检索层、证据包、prompt、结构化输出 schema 与 provider-specific invocation profile 共同构造了模型可见的证据环境；模型可能在答案、证据、弃答或验证动作任一层失败。

建议论文结构如下：

1. Introduction：从污染证据环境中的 factual reliability 问题进入，说明 answer accuracy 不足。
2. Conceptual frame：定义 epistemic resilience、evidence environment、evidential capture 与 epistemic escape。
3. Benchmark design：介绍三类任务族、五类证据条件、合成 mini-web、gold labels 与污染标签。
4. Metrics：解释 belief correctness、evidence cleanliness、uncertainty discipline、source selection 和 active verification metrics。
5. Main results：报告主表、family breakdown、condition breakdown 与 parse-success caveat。
6. Validity checks：呈现 80 行人工审计、dirty-support taxonomy 与 parse-repair 阻断边界。
7. Frontier preflight：说明跨 provider 主实验 cohort、调用策略与 operational/conditional 指标。
8. Limitations：说明合成数据、自动评分、样本量、API route、缺乏外部文献与真实任务验证的边界。
9. Conclusion：回到主张，即事实可靠性评测应同时看答案、证据和验证行动。

## 10. 局限与替代解释

第一，当前数据仍是合成 mini-web。合成数据的优势是 gold verdict、污染标签、source dependency 和任务条件可审计；限制是不能直接代表开放 web、企业知识库、新闻检索、法律医学场景或自适应攻击者环境。

第二，自动评分需要人工审计限定。`epistemic_escape` 的价值在于分解答案和证据质量，但它也依赖 gold labels、污染标签、doc_id 归一化和 schema 字段解释。人工审计显示，许多 `uncertain` 行来自 structured-field edge cases，而非简单的答案错误。

第三，`openai/gpt-5-mini` 的结果混合了模型行为与结构化输出适配问题。当前修复尝试受 API route 阻断，不能提供 repaired metrics。后续如果路由恢复，应重新运行 raw-response-preserving repair，再决定是否把 repaired slice 放入 appendix。

第四，`openai/gpt-5.5` 在当前 resilience 主表中只有 12-task stratified sample。它可以作为候选表现，但不能作为完整模型排名证据。

第五，frontier cohort preflight 只证明结构化输出可用性，不证明任务能力排序。20-task preflight 的作用是进入主实验前的 route/schema gate，而非最终能力评测。

第六，本报告没有引入外部文献。正式论文需要人工核对 RAG factuality、retrieval robustness、misinformation、provenance、hallucination evaluation、epistemic vigilance 和 synthetic benchmark 相关研究。未经核对的外部主张应保留 `[citation needed]`。

## 11. 下一步建议

下一阶段应优先做四件事。

1. 用已通过 preflight 的 five-provider cohort 跑完整 Epistemic Resilience Table v1，并同时报告 operational 与 conditional 指标。
2. 保留 per-model invocation profile：temperature policy、token cap policy、response format、message role policy、JSON extractor、parse success。
3. 把人工审计中的 edge cases 转化为论文限制和 scorer appendix，不要把 evidence cleanliness penalty 误写成全部自然语言判断失败。
4. 补 related work，并为所有外部理论和经验主张建立可核对文献笔记。

后续可选工作包括：扩展 `openai/gpt-5.5` 到完整 100 任务；在路由恢复后重跑 `openai/gpt-5-mini` parse repair；把 Matrix L4 hidden-primary recovery 写成 evidence environment construction 的 case study；固定一张主表、一张机制图和一张 failure-profile 图，避免结果展示继续膨胀。

## 12. 可复现信息

本报告依据以下仓库内材料：

- `eha-mvp/data/epistemic-resilience-v1/manifest.json`
- `eha-mvp/results/reports-epistemic-resilience-v1/main_table.csv`
- `eha-mvp/results/reports-epistemic-resilience-v1/by_condition.csv`
- `eha-mvp/results/reports-epistemic-resilience-v1/scored_predictions.csv`
- `eha-mvp/results/reports-epistemic-resilience-v1/cost_report.json`
- `eha-mvp/results/reports-epistemic-resilience-v1/audit_manifest.json`
- `eha-mvp/results/reports-epistemic-validity-pass/audit_manifest.json`
- `eha-mvp/results/reports-epistemic-validity-pass/human_audit_summary.md`
- `eha-mvp/results/reports-epistemic-parse-repair-gpt5mini/summary.md`
- `eha-mvp/results/reports-epistemic-model-preflight-frontier-final-2026-05-14/preflight_summary.csv`
- `eha-mvp/results/reports-epistemic-model-preflight-frontier-final-2026-05-14/cohort_decision.md`
- `reports/eha-frontier-cohort-preflight-2026-05-14.md`
- `reports/supported-mainstream-models-2026-05-14.md`

本次报告生成前已运行：

```bash
cd eha-mvp
uv run pytest
uv run python -m compileall eha
```

核查结果：`pytest` 共 63 个测试通过；`compileall` 通过。

## 13. 研究伦理与 AI 辅助写作说明

本报告没有引入真实个人数据、真实机构事实或外部文献断言。实验对象均为 EHA 合成数据中的虚构任务与文档。报告中的数值来自当前仓库的本地实验输出、CSV 汇总、manifest、成本报告、审计记录和预检表。

本报告由 AI 助手根据本地实验材料起草，并按 academic-paper-writing 的读者、问题、证据、限制与替代解释框架组织。报告没有编造实验结果、外部引用或未运行模型结论；凡涉及外推处均以“当前阶段”“合成 mini-web”“小样本”“后续需要人工审计”或“preflight 只证明结构化输出可用性”等方式限定。正式论文若加入外部文献、真实系统含义或安全建议，应由作者逐项核对。
