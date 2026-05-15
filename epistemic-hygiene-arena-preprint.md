# Epistemic Hygiene Arena: Evaluating LLM Epistemic Resilience in Polluted Evidence Environments

Author: Anonymous

Date: 2026-05-15

Status: first full paper draft based on the EHA frontier cohort run. Citation placeholders are intentionally left unresolved; this draft does not invent bibliographic entries.

## Abstract

Future LLM agents will rarely encounter facts directly. They will encounter search results, knowledge-base fragments, generated pages, repost chains, summaries, stale records, and other model-produced evidence. These are polluted evidence environments: information settings in which some documents are stale, circular, generated, derivative, misleadingly authoritative, or otherwise unreliable despite appearing relevant. We introduce Epistemic Hygiene Arena (EHA), a benchmark for evaluating whether LLMs maintain reliable and auditable beliefs in such environments. EHA evaluates epistemic escape rather than final-answer accuracy alone: whether a model reaches the right verdict, assigns evidence to the right machine-readable roles, abstains under insufficient evidence, and expresses useful verification actions.

We report a frontier cohort run on 100 synthetic evidence tasks, five frontier models, and two prompt conditions, for 1000 model calls. The models are `gpt-5.4`, `claude-opus-4-7`, `gemini-3.1-pro-preview`, `deepseek-v4-pro`, and `kimi-k2.6`. The main result is not a leaderboard. Frontier models differ across layers of epistemic behavior: belief correctness is high and relatively clustered, while evidence cleanliness and active-verification behavior separate the models more sharply. A generated-lore case study shows that `gpt-5.4` can correctly judge all generated-lore cases as insufficient while still placing polluted documents into `supporting_evidence`, creating an evidence-role failure for downstream systems. An active-verification case shows a correct verdict and clean evidence paired with non-executable bundled action targets. EHA therefore exposes failures below answer accuracy: the gap between what a model says, what its structured fields encode, and what an agent system can safely execute.

Keywords: LLM evaluation; epistemic resilience; evidence hygiene; agent evaluation; provenance; polluted evidence; generated lore; active verification.

## 1. Introduction

LLM agents increasingly rely on information environments they do not control. A deployed agent may search the web, inspect a private knowledge base, read generated documentation, summarize forum posts, retrieve from a vector index, or combine snippets produced by other models. This changes the factual-reliability problem. The question is no longer only whether the model has a true answer in its parameters. The question is whether the agent can reason reliably when the evidence environment itself is polluted.

Polluted evidence environments are common in agent settings. Documents may be outdated but still indexed. A weak claim may be repeated by several reposts, creating the appearance of consensus. A generated page may imitate the style of an authoritative source while lacking a provenance chain. A secondary summary may cite another secondary summary, laundering an unsupported claim through a chain of references. A search system may rank those derivative sources above the original record. In such settings, retrieving more text can increase exposure to bad evidence rather than repair uncertainty.

Final-answer accuracy is therefore insufficient. An agent that reaches the right verdict can still fail if it places bad documents into a machine-readable support field. A downstream report generator, memory system, or auditing tool may consume `supporting_evidence` without reading the model's full prose. Likewise, an agent that knows the right answer can still fail if its next action is not executable: a target such as `doc_a, doc_b -> doc_c` may be understandable to a human but unsafe or ambiguous for a tool interface.

EHA evaluates this broader reliability problem. We call the central outcome epistemic escape: the model avoids being captured by the polluted evidence environment. Operationally, this includes correct belief formation, clean evidence-role assignment, uncertainty discipline, and useful active-verification behavior.

One motivating example comes from EHA's generated-lore condition. In a `gpt-5.4` case, the model correctly says there is not reliable evidence that a fictional project occurred. Its prose explains that the apparent support is a wiki-style summary and downstream reposts with no primary record. Yet the same generated-lore root and repost appear in `supporting_evidence`. A human reader can infer that the model distrusts the source. A downstream agent reading only the structured support field may instead treat the polluted document as support. That is the kind of failure EHA is designed to surface.

This paper makes four contributions:

1. It defines polluted evidence environments as a benchmark target for LLM epistemic resilience in agent settings.
2. It introduces EHA, a 100-task synthetic evidence benchmark with three task families, five evidence conditions, structured outputs, and metrics beyond answer accuracy.
3. It reports a five-model frontier cohort run and decomposes results across belief correctness, evidence cleanliness, uncertainty discipline, and active verification.
4. It provides two mechanism case studies: generated-lore evidence-role failure and active-verification action-interface failure.

EHA should not be read as a model leaderboard or as a narrow RAG retrieval-hygiene test. The benchmark asks a different question: when evidence itself is compromised, does the model preserve auditable epistemic behavior across both natural-language answers and machine-readable fields?

## 2. Benchmark Design

### 2.1 Task Families

EHA uses three task families that represent increasingly agent-facing forms of evidence work.

| Family | Count | What the task asks |
| --- | ---: | --- |
| `packet_judgment` | 40 | Given an evidence packet, judge the claim without trusting polluted material. |
| `evidence_selection` | 40 | Select or rely on high-value documents rather than derivative or polluted sources. |
| `active_verification` | 20 | State the next useful verification action when the evidence environment is incomplete or polluted. |

The three families distinguish answer correctness from evidence selection and tool-facing behavior. A model can be strong at packet judgment yet weak at active verification.

### 2.2 Evidence Conditions

Each task belongs to one of five evidence conditions.

| Condition | Description |
| --- | --- |
| `clean` | The packet is mostly straightforward; primary evidence is available and not heavily obscured. |
| `conflicting_evidence` | Documents disagree, and the model must identify which evidence should control the verdict. |
| `false_consensus` | Multiple documents repeat one upstream claim, creating the illusion of independent support. |
| `buried_primary` | Primary evidence exists but is hidden among weaker or distracting materials. |
| `generated_lore` | Authority-like generated or derivative text looks useful but lacks a reliable source chain. |

The task set is synthetic. It uses fictional entities and a controlled evidence environment so that ground truth, pollutant labels, provenance relations, and scoring contracts are inspectable.

### 2.3 Output Contract

Models produce structured JSON outputs. The current main-run schema includes a verdict, confidence, natural-language explanation, machine-readable support fields, rejected evidence, selected document IDs, and actions. This contract is intentionally agent-facing. It evaluates whether a downstream system can safely consume the model output, not just whether a human can infer the intended answer.

### 2.4 Metrics

EHA reports several metrics, each measuring a different epistemic layer.

| Metric | Meaning |
| --- | --- |
| `operational_epistemic_escape` | Row-level success under the operational run contract, counting parse and schema failures as failures. |
| `conditional_epistemic_escape` | Same substantive score after conditioning on parse/schema success. |
| `belief_correctness` | Whether the model's verdict matches the gold verdict. |
| `evidence_cleanliness` | Whether machine-readable evidence fields avoid polluted or inappropriate support. |
| `uncertainty_discipline` | Whether confidence and insufficient-evidence behavior align with the evidence state. |
| `verification_action_score` | Whether active-verification actions are useful and machine-checkable. |

Operational and conditional scores are both necessary. Operational scores represent what a user or agent system actually receives, so parse failures and schema-missing outputs count. Conditional scores separate substantive reasoning quality from formatting reliability.

## 3. Model Cohort and Invocation

The frontier cohort contains five models:

| Provider family | Model ID |
| --- | --- |
| OpenAI / GPT-o | `gpt-5.4` |
| Anthropic Claude | `claude-opus-4-7` |
| Google Gemini | `gemini-3.1-pro-preview` |
| DeepSeek | `deepseek-v4-pro` |
| Kimi | `kimi-k2.6` |

Each model was evaluated on 100 tasks under two prompt conditions, producing 200 calls per model and 1000 calls in total. The prompt conditions were `standard_answer` and `epistemic_hygiene_instruction`.

Before the main run, candidate models went through structured-output preflight. The main run used provider-compatible invocation profiles rather than forcing one uniform parameter set across providers. This mattered for `deepseek-v4-pro` and `kimi-k2.6`: capped settings produced empty outputs in preflight and budget audit. The operational setting therefore omitted `max_completion_tokens` for those models while recording visible output lengths and overlength rates.

This no-cap handling did not create visible-output inflation in the main run. DeepSeek averaged 399.825 visible output tokens, Kimi averaged 404.205, and both had `overlength_rate=0.0`. Across the main run, `empty_output=0/1000`; DeepSeek had one schema-missing row and all other models had full parse success.

## 4. Main Results

The following table is a capability decomposition, not a ranking table.

| Model | Operational escape | Belief correctness | Evidence cleanliness | Uncertainty discipline | Verification action |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 0.880 | 0.960 | 1.000 | 0.960 | 0.600 |
| `deepseek-v4-pro` | 0.790 | 0.950 | 0.935 | 0.950 | 0.475 |
| `gemini-3.1-pro-preview` | 0.780 | 0.960 | 1.000 | 0.960 | 0.458 |
| `gpt-5.4` | 0.770 | 0.960 | 0.730 | 0.960 | 0.408 |
| `kimi-k2.6` | 0.790 | 0.960 | 0.950 | 0.960 | 0.450 |

The important pattern is that belief correctness is high and relatively clustered, while evidence cleanliness and active verification separate models. `gpt-5.4`, for example, has belief correctness equal to several other models but much lower evidence cleanliness. That is the central empirical reason EHA should not be reduced to final-answer accuracy.

### 4.1 Task Family Breakdown

| Model | Packet judgment escape | Evidence selection escape | Active verification escape |
| --- | ---: | ---: | ---: |
| `claude-opus-4-7` | 1.000 | 0.800 | 0.800 |
| `deepseek-v4-pro` | 0.963 | 0.762 | 0.500 |
| `gemini-3.1-pro-preview` | 1.000 | 0.800 | 0.300 |
| `gpt-5.4` | 0.838 | 0.787 | 0.600 |
| `kimi-k2.6` | 1.000 | 0.775 | 0.400 |

Packet judgment is generally easier than evidence selection and active verification. Active verification is the most agent-like family because it asks not only what the model believes but what it would do next.

### 4.2 Evidence Condition Breakdown

| Model | Clean | Conflicting evidence | False consensus | Buried primary | Generated lore |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 1.000 | 1.000 | 1.000 | 0.800 | 0.600 |
| `deepseek-v4-pro` | 0.875 | 0.825 | 0.950 | 0.800 | 0.500 |
| `gemini-3.1-pro-preview` | 0.950 | 0.900 | 0.825 | 0.800 | 0.425 |
| `gpt-5.4` | 0.975 | 0.975 | 1.000 | 0.800 | 0.100 |
| `kimi-k2.6` | 0.925 | 0.850 | 0.850 | 0.800 | 0.525 |

Generated lore is the sharpest condition for exposing evidence-role failures. In particular, `gpt-5.4` has generated-lore escape of 0.100 despite belief correctness of 1.000 on that slice. Section 5 analyzes this mechanism.

### 4.3 Prompt Hygiene Result

The hygiene instruction is not a universal fix.

| Model | Standard escape | Hygiene-instruction escape | Direction |
| --- | ---: | ---: | --- |
| `claude-opus-4-7` | 0.880 | 0.880 | Flat |
| `deepseek-v4-pro` | 0.780 | 0.800 | Slight gain |
| `gemini-3.1-pro-preview` | 0.780 | 0.780 | Flat |
| `gpt-5.4` | 0.750 | 0.790 | Gain |
| `kimi-k2.6` | 0.810 | 0.770 | Decline |

The result suggests that epistemic resilience is not reliably induced by a generic instruction to be careful. It depends on model behavior, schema semantics, and task family.

## 5. Mechanism Case Study 1: Generated Lore

The generated-lore condition should not be described as a simple failure to detect bad content. For `gpt-5.4`, the generated-lore slice shows a separation between belief correctness and evidence-role correctness.

| Metric | `gpt-5.4` generated lore |
| --- | ---: |
| `n` | 40 |
| Parse success | 1.000 |
| Belief correctness | 1.000 |
| Insufficient verdict rate | 1.000 |
| Rejected pollutant rate | 1.000 |
| Polluted supporting evidence rate | 0.900 |
| Dual-role pollutant rate | 0.875 |
| Full escape | 0.100 |

The model gives the correct insufficient verdict in every generated-lore row. It also places pollutants into rejected evidence in every row. The failure is that 36/40 rows still place polluted documents into `supporting_evidence`, and 35/40 rows assign the same pollutant both support and rejection roles.

Consider task `ert_032`, which asks whether there is reliable evidence that Novalis Robotics ran Project LumenShield in 2024. The gold verdict is `insufficient`. The `gpt-5.4` answer says that the apparent support is a wiki-style summary and multiple downstream reposts, with no primary document, raw record, or independent contemporaneous evidence. This is the right belief-level response. Yet the structured fields contain:

| Field | Evidence IDs |
| --- | --- |
| `supporting_evidence` | `eham_120_pollutant_root`, `eham_120_repost_00`, `eham_120_context_06` |
| `rejected_evidence` | `eham_120_repost_00`, `eham_120_repost_01`, `eham_120_repost_02`, `eham_120_repost_03` |
| Polluted support | `eham_120_pollutant_root`, `eham_120_repost_00` |
| Dual-role pollutant | `eham_120_repost_00` |

The same pattern appears in task `ert_033`, about a fictional MiraCert certification deal, and in active-verification generated-lore task `ert_096`. In each case, the model's natural-language explanation recognizes unreliable source structure, while the machine-readable support field includes generated-lore roots or reposts.

### 5.1 Clarified-Schema Mini-Rerun

To test whether this was a field-role ambiguity rather than a belief failure, we ran a clarified-schema mini-rerun on the generated-lore slice. The clarified schema separates:

- `clean_supporting_evidence`
- `refuting_evidence`
- `rejected_or_contaminated_evidence`
- `diagnostic_evidence`

The clarified rerun is a validity analysis, not a replacement for the frozen main-run score.

| Model | Schema | Belief correctness | Rejected pollutant | Polluted supporting | Dual-role pollutant | Escape |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | Current | 1.000 | 1.000 | 0.000 | 0.000 | 0.600 |
| `gemini-3.1-pro-preview` | Current | 1.000 | 1.000 | 0.000 | 0.000 | 0.425 |
| `gpt-5.4` | Current | 1.000 | 1.000 | 0.900 | 0.875 | 0.100 |
| `claude-opus-4-7` | Clarified | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| `gemini-3.1-pro-preview` | Clarified | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |
| `gpt-5.4` | Clarified | 1.000 | 1.000 | 0.000 | 0.000 | 1.000 |

Under the clarified schema, the three confirmed `gpt-5.4` cases keep `clean_supporting_evidence` empty and move pollutant roots or reposts into `rejected_or_contaminated_evidence` or `diagnostic_evidence`.

The interpretation is narrow but important: the current schema exposes an agent-interface risk. A model can verbally reject a pollutant while still placing it in a support field that downstream systems may consume. The clarified schema shows that the failure is closely tied to field semantics and evidence-role assignment. It does not show that the main score should be retroactively rewritten.

## 6. Mechanism Case Study 2: Active Verification

The second mechanism case concerns executable action expression. In `gpt-5.4`, task `ert_082`, `standard_answer`, the question asks whether Novalis Robotics completed a Q4 supplier audit before the 2025 renewal meeting. The gold verdict is `supported`.

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

These are understandable bundled strings, but they are not exact machine-checkable targets or clear `search_primary` actions. This is not an answer-accuracy failure. It is an agent-interface failure: the model has the right belief and clean support but does not express the next verification step in a form a tool system can execute and audit.

Together, Sections 5 and 6 show why EHA evaluates more than correctness. Generated lore exposes evidence-role failure. Active verification exposes action-expression failure.

## 7. Discussion

EHA reveals failures below answer accuracy. In the frontier cohort, belief correctness is high across models, but the structured evidence and verification layers show meaningful separation. This matters because agent systems increasingly treat model outputs as structured instructions, evidence stores, or report inputs rather than as prose for a human reader.

Generated lore is not merely a content problem. It is a provenance and evidence-role problem. A model may correctly say that a claim is unsupported because the only available evidence is derivative or generated. But if the model still places those derivative documents into `supporting_evidence`, it risks laundering rejected material into downstream support.

Structured fields therefore matter. A prose explanation and a JSON field can disagree in practice. A human reader may reconcile them; a downstream system may not. EHA's scoring contract makes that mismatch visible.

The prompt-hygiene result also limits a common mitigation strategy. Telling a model to be careful about evidence helps some models, is flat for others, and harms one model in this run. A robust agent system should therefore not rely only on a generic hygiene instruction. It should consider schema design, provenance-aware tooling, output validation, and human audit of high-risk slices.

## 8. Limitations

First, EHA currently uses a synthetic mini-web. This is an advantage for control and auditability, but it limits direct claims about open-web misinformation performance.

Second, the benchmark has a fixed schema and scoring contract. The generated-lore analysis shows that schema wording can affect role assignment. This is not a defect to hide; it is part of the agent-interface problem. Still, future work should test more schema variants and richer evidence-role taxonomies.

Third, the current main run contains 100 tasks. That is enough for a first mechanism-oriented study, but not enough for broad model ranking or fine-grained provider claims.

Fourth, active-verification scoring still needs more human audit. The current score captures exactness and usefulness of action targets, but action quality is harder to evaluate automatically than verdicts or evidence IDs.

Fifth, the clarified-schema mini-rerun is validity analysis, not a retroactive replacement for the main run. It explains why one failure mode appears; it does not alter the frozen current-schema score.

Sixth, this paper does not claim that the evaluated models will behave the same way on real institutions, real legal or medical tasks, or live open-web misinformation. The synthetic setting is designed to isolate mechanisms, not to certify deployment safety.

## 9. Related Work Placeholder

This draft intentionally does not invent citations. The final paper should add verified citations in at least the following areas:

- Hallucination and truthfulness evaluation.
- Fact verification and evidence-grounded claim classification.
- Retrieval-augmented generation factuality.
- RAG poisoning and knowledge-base contamination.
- Provenance tracking and source credibility.
- Misinformation robustness and false-consensus effects.
- Tool-use and web-agent evaluation.
- Epistemic vigilance, source monitoring, and trust calibration.

The positioning should be precise. EHA overlaps with RAG factuality and misinformation robustness, but it is not only a retrieval-quality benchmark. Its distinctive target is epistemic resilience in polluted evidence environments, including machine-readable evidence roles and executable verification behavior.

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
- Paper mechanism section: `reports/eha-paper-mechanism-case-section-2026-05-15.md`
