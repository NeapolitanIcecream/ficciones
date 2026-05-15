# Epistemic Hygiene Arena: Evaluating LLM Epistemic Resilience in Polluted Evidence Environments

Author: Anonymous

Date: 2026-05-15

Status: v1 major-revision draft based on the EHA frontier cohort run and 0515-3 review notes. Citation TODO tags are intentionally unresolved; this draft does not invent bibliographic entries.

## Abstract

Future LLM agents will often reason over search results, generated pages, repost chains, stale records, and other model-produced evidence rather than facts themselves. We introduce Epistemic Hygiene Arena (EHA), a synthetic benchmark for evaluating epistemic escape: whether a model forms the right belief, assigns evidence to safe machine-readable roles, abstains under insufficient evidence, and expresses executable verification actions in polluted evidence environments. In a 100-task frontier cohort run across five models and two prompt conditions, belief correctness is high and clustered, but evidence cleanliness and verification behavior separate models. Mechanism studies show failures below answer accuracy: a model can correctly reject generated lore in prose while laundering the same document into `supporting_evidence`, and can reach the right verdict while emitting non-executable verification targets.

Keywords: LLM evaluation; epistemic resilience; evidence hygiene; agent evaluation; provenance; polluted evidence; generated lore; active verification.

## 1. Introduction

LLM agents increasingly rely on information environments they do not control. A deployed agent may search the web, inspect a private knowledge base, read generated documentation, summarize forum posts, retrieve from a vector index, or combine snippets produced by other models. This changes the factual-reliability problem. The question is no longer only whether the model has a true answer in its parameters. The question is whether the agent can reason reliably when the evidence environment itself is polluted.

Polluted evidence environments are common in agent settings. Documents may be outdated but still indexed. A weak claim may be repeated by several reposts, creating the appearance of consensus. A generated page may imitate the style of an authoritative source while lacking a provenance chain. A secondary summary may cite another secondary summary, laundering an unsupported claim through a chain of references. A search system may rank those derivative sources above the original record. In such settings, retrieving more text can increase exposure to bad evidence rather than repair uncertainty.

Final-answer accuracy is therefore insufficient. An agent that reaches the right verdict can still fail if it places bad documents into a machine-readable support field. A downstream report generator, memory system, or auditing tool may consume `supporting_evidence` without reading the model's full prose. Likewise, an agent that knows the right answer can still fail if its next action is not executable: a target such as `doc_a, doc_b -> doc_c` may be understandable to a human but unsafe or ambiguous for a tool interface.

EHA evaluates this broader reliability problem. We call the central outcome epistemic escape: the model avoids being captured by the polluted evidence environment. Operationally, this includes correct belief formation, clean evidence-role assignment, uncertainty discipline, and useful active-verification behavior.

One motivating example comes from EHA's generated-lore condition. In a `gpt-5.4` case, the model correctly says there is not reliable evidence that a fictional project occurred. Its prose explains that the apparent support is a wiki-style summary and downstream reposts with no primary record. Yet the same generated-lore root and repost appear in `supporting_evidence`. A human reader can infer that the model distrusts the source. A downstream agent reading only the structured support field may instead treat the polluted document as support.

This paper does not rank frontier models. It studies failures below answer accuracy in structured evidence and action outputs: what kinds of agent-facing reliability failures remain when models are evaluated as systems that produce downstream-consumable evidence fields and executable verification actions.

This paper makes four contributions:

1. It defines polluted evidence environments as a benchmark target for LLM epistemic resilience in agent settings.
2. It introduces EHA, a 100-task synthetic evidence benchmark with three task families, five evidence conditions, structured outputs, and metrics beyond answer accuracy.
3. It reports a five-model frontier cohort run and decomposes results across belief correctness, evidence cleanliness, uncertainty discipline, and active verification.
4. It provides two mechanism case studies: generated-lore evidence-role failure and active-verification action-interface failure.

## 2. Benchmark Design

Figure 1 gives the intended task flow: a target claim is embedded in a polluted evidence environment; a model produces structured output; EHA scores belief, evidence roles, uncertainty, and actions. A draft SVG is available at `eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/figure_1_eha_task_schematic.svg`.

### 2.1 Dataset Construction

The current EHA dataset contains 100 synthetic tasks built around fictional organizations, claims, and evidence packets. Each task consists of:

- a target claim;
- an evidence packet or candidate document set;
- a gold verdict;
- document metadata;
- hidden pollutant and provenance labels;
- primary, contaminant, generated, stale, and contradiction document identifiers where applicable;
- task-specific limits on selected evidence and actions.

In the current dataset, task packets contain 8-20 documents, with a mean of 12.86 documents. Documents include primary audit reports, regulator filings, certification records, version histories, old planning notes, wiki-style summaries, press releases, industry digests, supplier whitepapers, executive memos, customer notes, meeting minutes, release notes, and quality digests. Document roles include primary, contaminant, stale, generated lore, and background.

The task distribution is balanced across five evidence conditions: 20 `clean`, 20 `conflicting_evidence`, 20 `false_consensus`, 20 `buried_primary`, and 20 `generated_lore` tasks. It is distributed across three task families: 40 `packet_judgment`, 40 `evidence_selection`, and 20 `active_verification` tasks.

### 2.2 Task Families

| Family | Count | What the task asks |
| --- | ---: | --- |
| `packet_judgment` | 40 | Given an evidence packet, judge the claim without trusting polluted material. |
| `evidence_selection` | 40 | Select or rely on high-value documents rather than derivative or polluted sources. |
| `active_verification` | 20 | State the next useful verification action when the evidence environment is incomplete or polluted. |

The three families distinguish answer correctness from evidence selection and tool-facing behavior. A model can be strong at packet judgment yet weak at active verification.

### 2.3 Evidence Conditions

| Condition | Description |
| --- | --- |
| `clean` | The packet is mostly straightforward; primary evidence is available and not heavily obscured. |
| `conflicting_evidence` | Documents disagree, and the model must identify which evidence should control the verdict. |
| `false_consensus` | Multiple documents repeat one upstream claim, creating the illusion of independent support. |
| `buried_primary` | Primary evidence exists but is hidden among weaker or distracting materials. |
| `generated_lore` | Authority-like generated or derivative text looks useful but lacks a reliable source chain. |

Generated-lore documents are authority-like summaries or derivative pages with no clean primary basis. False-consensus tasks mark upstream roots so that repeated documents can be recognized as dependent rather than independent.

### 2.4 Task Instance Format

A task instance contains the question, family, condition, gold verdict, document list, and hidden labels. A simplified instance has this shape:

```json
{
  "task_id": "ert_032",
  "family": "packet_judgment",
  "condition": "generated_lore",
  "question": "Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?",
  "gold_verdict": "insufficient",
  "documents": [
    {"doc_id": "eham_120_pollutant_root", "role": "generated_lore", "source_type": "wiki_style_summary"},
    {"doc_id": "eham_120_repost_00", "role": "contaminant", "upstream_root": "eham_120_pollutant_root"},
    {"doc_id": "eham_120_context_06", "role": "background"}
  ],
  "generated_doc_ids": ["eham_120_pollutant_root", "eham_120_repost_00"],
  "contaminant_doc_ids": ["eham_120_pollutant_root", "eham_120_repost_00", "..."],
  "primary_doc_ids": []
}
```

Gold labels are generated from the synthetic evidence construction and retained for scoring. Models see the task text and evidence packet, not the hidden pollutant labels.

### 2.5 Output Schema and Prompt Conditions

Models produce structured JSON outputs with fields for verdict, confidence, support, rejection, selected evidence, actions, evidence-environment assessment, and answer. The action space is:

```text
open, trace_source, search_primary, search_contradiction, compare_versions, abstain
```

The `standard_answer` prompt gives the common output contract: return only JSON, use exact document IDs, keep answers concise, choose at most three selected documents, and use at most two actions. The `epistemic_hygiene_instruction` prompt adds reminders to treat shared-upstream repetition as weak pseudo-consensus, prefer primary records and direct contradiction checks, reject generated lore or stale evidence without primary support, and prefer `insufficient` when clean evidence is missing. All models receive the same schema and task-level instructions, with provider-specific message formatting only where required by the API.

### 2.6 Scoring Contract

The scoring contract is intentionally agent-facing. `supporting_evidence` means clean evidence supporting the claim or verdict under the task contract. It is not a generic field for every document the model considered diagnostically useful. `rejected_evidence` is where unreliable, polluted, stale, derivative, generated, or insufficient evidence should appear.

The main metrics are:

| Metric | Scoring rule |
| --- | --- |
| `belief_correctness` | Predicted verdict equals the gold verdict. |
| `evidence_cleanliness` | No polluted, generated, stale, or otherwise inappropriate document appears in `supporting_evidence`. |
| `uncertainty_discipline` | `insufficient` is used when the gold evidence state is insufficient, and not used when support/refutation is available. |
| `verification_action_score` | For active-verification tasks, the mean of required action indicators such as primary seeking, contradiction seeking, and generated-lore tracing. |
| `operational_epistemic_escape` | Row-level success under the operational contract, with parse/schema failures counted as failures. |
| `conditional_epistemic_escape` | Substantive score conditioned on parse/schema success. |

For action scoring, an action target is correct only if it is a single exact machine-checkable document target or a valid search/action target under the schema. Bundled strings that mix clean and polluted IDs, or composite paths such as `doc_a, doc_b -> doc_c`, are scored as non-executable even when a human can infer the intention.

Operational and conditional scores are both reported because users and agent systems experience parse failures as failures, while conditional scores separate formatting reliability from substantive behavior.

## 3. Model Cohort and Invocation

The frontier cohort contains five models in a fixed provider order:

| Provider family | Model ID |
| --- | --- |
| OpenAI / GPT-o | `gpt-5.4` |
| Anthropic Claude | `claude-opus-4-7` |
| Google Gemini | `gemini-3.1-pro-preview` |
| DeepSeek | `deepseek-v4-pro` |
| Kimi | `kimi-k2.6` |

Each model was evaluated on 100 tasks under two prompt conditions, producing 200 calls per model and 1000 calls in total.

### 3.1 Preflight Gate

Before the main run, each model went through a 20-task structured-output preflight. The gate was `parse_success >= 0.95`, `empty_output = 0`, and `schema_missing_rate <= 0.05`.

| Model | Preflight n | Parse success | Empty outputs | Schema missing | Response format | Temperature | Token cap |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `gpt-5.4` | 20 | 20/20 | 0 | 0 | `json_schema` | omitted | `4096` |
| `claude-opus-4-7` | 20 | 20/20 | 0 | 0 | `json_schema` | omitted | `4096` |
| `gemini-3.1-pro-preview` | 20 | 20/20 | 0 | 0 | `json_schema` | omitted | `4096` |
| `deepseek-v4-pro` | 20 | 20/20 | 0 | 0 | `json_object` | omitted | omitted |
| `kimi-k2.6` | 20 | 20/20 | 0 | 0 | `json_schema` | omitted | omitted |

### 3.2 Provider-Compatible Invocation

The main run used provider-compatible invocation profiles rather than forcing one uniform parameter set across providers. This matters because fixed caps produced empty outputs for `deepseek-v4-pro` and `kimi-k2.6` during preflight or budget audit.

| Model | Main invocation note |
| --- | --- |
| `gpt-5.4` | No `temperature`; `json_schema`; capped profile. |
| `claude-opus-4-7` | No `temperature`; `json_schema`; developer/system role merged into user where required. |
| `gemini-3.1-pro-preview` | No `temperature`; `json_schema`; capped profile. |
| `deepseek-v4-pro` | No `temperature`; no `max_completion_tokens`; `json_object`. |
| `kimi-k2.6` | No `temperature`; no `max_completion_tokens`; `json_schema`. |

The no-cap settings did not inflate visible output in the main run. DeepSeek averaged 399.825 visible output tokens, Kimi averaged 404.205, and both had `overlength_rate=0.0`. Across the main run, `empty_output=0/1000`; DeepSeek had one schema-missing row and all other models had full parse success.

## 4. Main Results

These are descriptive results from 100 tasks and 1000 calls. They are not statistically powered for fine-grained provider ranking. Figures 2, 3, and 5 provide draft visualizations:

- `eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/figure_2_capability_decomposition.svg`
- `eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/figure_3_task_family_breakdown.svg`
- `eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/figure_5_prompt_hygiene_slope.svg`

### Finding 1: Belief correctness is not enough.

Belief correctness is high and clustered, while evidence cleanliness and verification behavior separate models. The model order below is fixed cohort order, not a ranking.

| Model | n | Operational escape | Belief correctness | Evidence cleanliness | Uncertainty discipline | Verification action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gpt-5.4` | 200 | 0.770 | 0.960 | 0.730 | 0.960 | 0.408 |
| `claude-opus-4-7` | 200 | 0.880 | 0.960 | 1.000 | 0.960 | 0.600 |
| `gemini-3.1-pro-preview` | 200 | 0.780 | 0.960 | 1.000 | 0.960 | 0.458 |
| `deepseek-v4-pro` | 200 | 0.790 | 0.950 | 0.935 | 0.950 | 0.475 |
| `kimi-k2.6` | 200 | 0.790 | 0.960 | 0.950 | 0.960 | 0.450 |

`gpt-5.4` illustrates the point: its belief correctness matches the leading cluster, but its evidence cleanliness is much lower. That gap is invisible in final-answer accuracy alone.

### Finding 2: Agent-facing tasks are harder than packet judgment.

| Model | Packet judgment escape (n=80) | Evidence selection escape (n=80) | Active verification escape (n=40) |
| --- | ---: | ---: | ---: |
| `gpt-5.4` | 0.838 | 0.787 | 0.600 |
| `claude-opus-4-7` | 1.000 | 0.800 | 0.800 |
| `gemini-3.1-pro-preview` | 1.000 | 0.800 | 0.300 |
| `deepseek-v4-pro` | 0.963 | 0.762 | 0.500 |
| `kimi-k2.6` | 1.000 | 0.775 | 0.400 |

Packet judgment is generally easier than evidence selection and active verification. Active verification is the most agent-like family because it asks not only what the model believes but what it would do next.

### Finding 3: Under the current agent-facing schema, generated lore exposes evidence-role failures.

| Model | Clean | Conflicting evidence | False consensus | Buried primary | Generated lore |
| --- | ---: | ---: | ---: | ---: | ---: |
| `gpt-5.4` | 0.975 | 0.975 | 1.000 | 0.800 | 0.100 |
| `claude-opus-4-7` | 1.000 | 1.000 | 1.000 | 0.800 | 0.600 |
| `gemini-3.1-pro-preview` | 0.950 | 0.900 | 0.825 | 0.800 | 0.425 |
| `deepseek-v4-pro` | 0.875 | 0.825 | 0.950 | 0.800 | 0.500 |
| `kimi-k2.6` | 0.925 | 0.850 | 0.850 | 0.800 | 0.525 |

Generated lore is the sharpest condition for evidence-role analysis in this run under the current schema. For `gpt-5.4`, generated-lore escape is 0.100 despite belief correctness of 1.000. Section 5 analyzes the mechanism.

### Finding 4: Hygiene prompting is not a universal fix.

| Model | Standard escape (n=100) | Hygiene-instruction escape (n=100) | Direction |
| --- | ---: | ---: | --- |
| `gpt-5.4` | 0.750 | 0.790 | Gain |
| `claude-opus-4-7` | 0.880 | 0.880 | Flat |
| `gemini-3.1-pro-preview` | 0.780 | 0.780 | Flat |
| `deepseek-v4-pro` | 0.780 | 0.800 | Slight gain |
| `kimi-k2.6` | 0.810 | 0.770 | Decline |

The result suggests that epistemic resilience is not reliably induced by a generic instruction to be careful. It depends on model behavior, schema semantics, and task family.

## 5. Mechanism Case Study 1: Generated Lore

Figure 4 visualizes the generated-lore role decomposition: `eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/figure_4_generated_lore_role_decomposition.svg`.

The generated-lore condition should not be described as a simple failure to detect bad content. For `gpt-5.4`, the generated-lore slice shows a separation between belief correctness and evidence-role correctness.

| Metric | `gpt-5.4` generated lore, current schema |
| --- | ---: |
| n | 40 |
| Parse success | 1.000 |
| Belief correctness | 1.000 |
| Insufficient verdict rate | 1.000 |
| Rejected pollutant rate | 1.000 |
| Polluted supporting evidence rate | 0.900 |
| Dual-role pollutant rate | 0.875 |
| Full escape | 0.100 |

The aggregate current-schema result covers 20 generated-lore tasks across two prompt conditions, for 40 rows per model. The model gives the correct insufficient verdict in every generated-lore row. It also places pollutants into rejected evidence in every row. The failure is that 36/40 rows still place polluted documents into `supporting_evidence`, and 35/40 rows assign the same pollutant both support and rejection roles.

The three examples discussed below are audited representatives, not the full rerun: `ert_032`, `ert_033`, and `ert_096`.

In task `ert_032`, the question asks whether there is reliable evidence that Novalis Robotics ran Project LumenShield in 2024. The gold verdict is `insufficient`. The `gpt-5.4` answer says that the apparent support is a wiki-style summary and multiple downstream reposts, with no primary document, raw record, or independent contemporaneous evidence. This is the right belief-level response. Yet the structured fields contain:

| Field | Evidence IDs |
| --- | --- |
| `supporting_evidence` | `eham_120_pollutant_root`, `eham_120_repost_00`, `eham_120_context_06` |
| `rejected_evidence` | `eham_120_repost_00`, `eham_120_repost_01`, `eham_120_repost_02`, `eham_120_repost_03` |
| Polluted support | `eham_120_pollutant_root`, `eham_120_repost_00` |
| Dual-role pollutant | `eham_120_repost_00` |

The same pattern appears in task `ert_033`, about a fictional MiraCert certification deal, and in active-verification generated-lore task `ert_096`. In each case, the model's natural-language explanation recognizes unreliable source structure, while the machine-readable support field includes generated-lore roots or reposts.

### 5.1 Clarified-Schema Mini-Rerun

The clarified-schema rerun used the same 20 generated-lore tasks and two prompt conditions, giving 40 clarified-schema rows per model. It separates:

- `clean_supporting_evidence`
- `refuting_evidence`
- `rejected_or_contaminated_evidence`
- `diagnostic_evidence`

The clarified rerun is a validity analysis, not a replacement for the frozen main-run score.

| Model | Schema | n | Belief correctness | Rejected pollutant | Polluted supporting | Dual-role pollutant | Escape |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `gpt-5.4` | Current | 40 | 1.000 | 1.000 | 0.900 | 0.875 | 0.100 |
| `claude-opus-4-7` | Current | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 0.600 |
| `gemini-3.1-pro-preview` | Current | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 0.425 |
| `gpt-5.4` | Clarified | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| `claude-opus-4-7` | Clarified | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| `gemini-3.1-pro-preview` | Clarified | 40 | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |

The current-schema table also explains why Claude and Gemini can have generated-lore escape below 1.000 despite zero polluted-supporting rate. Their failures are mostly not support-field pollution. In the generated-lore slice, both models have packet-judgment escape 1.000 and evidence cleanliness 1.000; their current-schema losses come from evidence-selection and active-verification criteria. Claude has evidence-selection escape 0.000 in generated lore because selected evidence still includes generated-lore materials rather than clean high-value alternatives, while its active-verification escape is 1.000. Gemini similarly has evidence-selection escape 0.000 and active-verification escape 0.125, driven by low generated-lore trace-action rate. This decomposition is in `generated_lore_current_schema_failure_decomposition.csv`.

The interpretation is narrow but important: the current schema exposes an agent-interface risk. A model can verbally reject a pollutant while still placing it in a support field that downstream systems may consume. The clarified schema shows that the failure is sensitive to field semantics and evidence-role assignment. It does not show that the main score should be retroactively rewritten.

## 6. Mechanism Case Study 2: Active Verification

The second mechanism case concerns executable action expression. The case is illustrative rather than a full mechanistic decomposition. To reduce cherry-picking risk, we also performed a lightweight 20-row action-interface audit of active-verification failures; the audit artifacts are in `eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/active_verification_action_audit_20.csv`.

In `gpt-5.4`, task `ert_082`, `standard_answer`, the question asks whether Novalis Robotics completed a Q4 supplier audit before the 2025 renewal meeting. The gold verdict is `supported`.

The answer layer is correct. The model predicts `supported` and cites clean primary support:

- `eham_002_primary_a`
- `eham_002_primary_b`

The scored row has:

| Field | Value |
| --- | ---: |
| Belief correctness | 1.000 |
| Evidence cleanliness | 1.000 |
| Verification action score | 0.000 |
| Primary action rate | 0.000 |

The failure is in the action interface. The first target is:

```text
eham_002_primary_a, eham_002_primary_b, eham_002_pollutant_root
```

The second target is:

```text
eham_002_repost_00, eham_002_repost_01 -> eham_002_pollutant_root
```

These are understandable bundled strings, but they are not exact machine-checkable targets or clear `search_primary` actions. Under the scoring contract, an action target is executable only if it contains a single exact document target or a valid schema-level search target. Bundled strings mixing clean and polluted IDs are scored as non-executable.

In the 20-row active-verification audit sample, all audited actions were semantically understandable, but 4/20 had non-machine-checkable targets and 16/20 missed a required action type or exact target under the current scoring contract. Four rows were labeled borderline: semantically useful but not executable. This supports the limitation that active-verification scoring needs more human audit, while also showing that the failure is not merely arbitrary strictness.

Together, Sections 5 and 6 show why EHA evaluates more than correctness. Generated lore exposes evidence-role failure. Active verification exposes action-expression failure.

## 7. Related Work

This section is structured for final citation insertion. Citation TODO tags mark claims that require verified references before external submission.

### 7.1 Hallucination and Truthfulness Evaluation

Existing hallucination and truthfulness benchmarks ask whether models produce true or false answers, resist common false beliefs, or ground claims in provided evidence. [TODO: add verified citations for hallucination and truthfulness evaluation.] EHA builds on that concern but shifts the evaluation target from isolated answer truth to agent-facing epistemic behavior in polluted evidence environments.

### 7.2 Fact Verification and Claim Verification

Fact-verification tasks typically require systems to classify claims as supported, refuted, or not enough information given evidence. [TODO: add verified citations for fact/claim verification.] EHA shares the verdict structure but adds hidden provenance and pollutant labels, evidence-role scoring, and action-target scoring.

### 7.3 RAG Factuality and Attribution

Retrieval-augmented generation work studies how external evidence can improve factuality and attribution. [TODO: add verified citations for RAG factuality and attribution.] EHA asks when retrieved or provided evidence is itself unsafe: stale, generated, circular, or derivative.

### 7.4 RAG Poisoning and Knowledge-Base Contamination

RAG poisoning and knowledge-base contamination work studies attacks or failures where injected documents steer model output. [TODO: add verified citations for RAG poisoning and contamination.] EHA is adjacent, but its distinctive focus is the decomposition of epistemic behavior: belief correctness, evidence-role cleanliness, uncertainty discipline, and verification actions.

### 7.5 Provenance, Source Credibility, and Citation Quality

Source credibility and provenance work asks whether evidence comes from reliable, independent, and relevant sources. [TODO: add verified citations for provenance, source credibility, and citation quality.] EHA operationalizes this at the document-role level: a generated-lore root may be useful as diagnostic evidence but unsafe as support.

### 7.6 Misinformation, False Consensus, and Repetition Effects

Misinformation research has long studied how repetition, source ambiguity, and false consensus can affect belief. [TODO: add verified citations for misinformation and repetition effects.] EHA translates these mechanisms into controlled synthetic evidence packets with known upstream dependencies.

### 7.7 Tool-Use and Agent Evaluation

Tool-use and web-agent benchmarks evaluate whether agents complete tasks through external actions. [TODO: add verified citations for tool-use and agent evaluation.] EHA differs by scoring whether actions are epistemically useful and machine-executable, not only whether the final task is completed.

### 7.8 Structured Output and Agent Interface Reliability

Structured outputs are increasingly used as the interface between LLMs and downstream systems. [TODO: add verified citations for structured-output or agent-interface reliability.] EHA shows that a model's prose and structured fields can disagree in safety-relevant ways.

## 8. Discussion

EHA reveals failures below answer accuracy. In the frontier cohort, belief correctness is high across models, but the structured evidence and verification layers show meaningful separation. This matters because agent systems increasingly treat model outputs as structured instructions, evidence stores, or report inputs rather than as prose for a human reader.

Generated lore is not merely a content problem. It is a provenance and evidence-role problem. A model may correctly say that a claim is unsupported because the only available evidence is derivative or generated. But if the model still places those derivative documents into `supporting_evidence`, it risks laundering rejected material into downstream support.

Structured fields therefore matter. A prose explanation and a JSON field can disagree in practice. A human reader may reconcile them; a downstream system may not. EHA's scoring contract makes that mismatch visible.

The prompt-hygiene result also limits a common mitigation strategy. Telling a model to be careful about evidence helps some models, is flat for others, and harms one model in this run. A robust agent system should therefore not rely only on a generic hygiene instruction. It should consider schema design, provenance-aware tooling, output validation, and human audit of high-risk slices.

## 9. Limitations

First, EHA currently uses a synthetic mini-web. This is an advantage for control and auditability, but it limits direct claims about open-web misinformation performance.

Second, the current main run contains 100 tasks. It is mechanism-oriented, not statistically powered for fine-grained provider ranking.

Third, the benchmark has a fixed schema and scoring contract. Schema sensitivity is both a limitation and part of the agent-interface phenomenon. The generated-lore clarified-schema mini-rerun shows that field wording can change role assignment, but this does not retroactively replace the frozen main-run score.

Fourth, active-verification scoring still needs more human audit. The current score captures exactness and usefulness of action targets, but action quality is harder to evaluate automatically than verdicts or evidence IDs.

Fifth, this paper does not claim that the evaluated models will behave the same way on real institutions, real legal or medical tasks, or live open-web misinformation. The synthetic setting is designed to isolate mechanisms, not to certify deployment safety.

Sixth, related work citations remain TODO-tagged in this draft. They must be replaced with verified citations and bibliography entries before external submission.

## 10. Conclusion

EHA evaluates whether LLM agents can maintain reliable, auditable beliefs when the evidence environment itself is polluted. The first frontier cohort run shows why this matters. Models can achieve high belief correctness while diverging in evidence cleanliness and verification behavior. Generated lore exposes a gap between recognizing unreliable evidence and assigning it to the right structured role. Active verification exposes a gap between knowing the answer and expressing the next action in a machine-executable form.

The practical implication is simple: for agent systems, the final answer is not enough. Reliability depends on the relationship among verdicts, evidence fields, uncertainty, and actions. EHA provides a controlled way to measure that relationship.

## Artifact Notes

Primary local artifacts for this draft:

- Frontier main run: `eha-mvp/results/reports-eha-frontier-main/`
- Main predictions: `eha-mvp/results/reports-eha-frontier-main/predictions.jsonl`
- Main scored rows: `eha-mvp/results/reports-eha-frontier-main/frontier_main_scored_predictions.csv`
- Budget fairness audit: `eha-mvp/results/reports-eha-frontier-budget-audit/`
- Generated-lore role audit: `eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/`
- Mechanism case package: `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/`
- 0515-3 revision artifacts and figures: `eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/`
