# EHA Frontier Results: Reader-Facing Narrative Pass

日期：2026-05-15

## One-Sentence Story

EHA is not a model leaderboard for answer accuracy. It tests whether models stay reliable when the evidence environment itself is polluted: repeated reposts, stale summaries, generated lore, buried primary records, and direct contradictions.

Plainly:

> We are asking whether a model can avoid being led by bad evidence, not merely whether it can produce the right final answer.

## Reader-Facing Definitions

| Term | Reader-facing definition |
| --- | --- |
| Epistemic escape | The model was not captured by the polluted evidence environment. |
| Evidence cleanliness | The model did not place bad sources into machine-readable supporting evidence fields. |
| Generated lore | Authority-like generated text that sounds like a source but lacks real provenance. |
| False consensus | Many documents repeat one upstream claim, creating the illusion of independent agreement. |
| Active verification | The model knows the next useful verification action: trace source, find primary records, search for contradiction, or compare versions. |

## What The 100 Tasks Measure

The task set has three increasingly agentic layers:

| Family | Count | Plain-language question |
| --- | ---: | --- |
| `packet_judgment` | 40 | Given the packet, can the model judge the claim without trusting polluted material? |
| `evidence_selection` | 40 | If it can inspect only a few documents, does it choose primary or high-value evidence rather than noise? |
| `active_verification` | 20 | Does it know what to check next when the evidence environment is uncertain or polluted? |

The five evidence environments are:

| Condition | Plain-language version |
| --- | --- |
| `clean` | The packet is mostly straightforward. |
| `conflicting_evidence` | Documents disagree. |
| `false_consensus` | Reposts make one weak claim look widely confirmed. |
| `buried_primary` | Primary evidence exists but is hidden among weaker material. |
| `generated_lore` | Generated or authority-like pages look useful but have no real source chain. |

## Main Result, Without Turning It Into A Leaderboard

| Model | Operational escape | Belief correctness | Evidence cleanliness | Active verification score |
| --- | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 0.880 | 0.960 | 1.000 | 0.600 |
| `deepseek-v4-pro` | 0.790 | 0.950 | 0.935 | 0.475 |
| `kimi-k2.6` | 0.790 | 0.960 | 0.950 | 0.450 |
| `gemini-3.1-pro-preview` | 0.780 | 0.960 | 1.000 | 0.458 |
| `gpt-5.4` | 0.770 | 0.960 | 0.730 | 0.408 |

The useful interpretation is not "Claude first, GPT last." The useful interpretation is:

> Frontier models fail in different layers of epistemic work. Some answer correctly but expose dirty evidence fields. Some read the packet well but choose weaker next verification actions.

## Five Main Figure Plan

### Figure 1: What EHA Tests

Use a task diagram:

```text
Claim
  -> polluted evidence packet
       primary record
       repost chain
       stale report
       generated lore
       contradiction
  -> model must:
       decide
       cite clean evidence
       abstain when warranted
       choose verification action
```

Purpose: explain the benchmark before showing numbers.

### Figure 2: Capability Decomposition

Plot four bars per model:

| Model | Belief correctness | Evidence cleanliness | Uncertainty discipline | Verification action |
| --- | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 0.960 | 1.000 | 0.960 | 0.600 |
| `deepseek-v4-pro` | 0.950 | 0.935 | 0.950 | 0.475 |
| `gemini-3.1-pro-preview` | 0.960 | 1.000 | 0.960 | 0.458 |
| `gpt-5.4` | 0.960 | 0.730 | 0.960 | 0.408 |
| `kimi-k2.6` | 0.960 | 0.950 | 0.960 | 0.450 |

Purpose: show that answer correctness and evidence discipline are separable.

### Figure 3: Task Family Difficulty

| Model | Packet judgment | Evidence selection | Active verification |
| --- | ---: | ---: | ---: |
| `claude-opus-4-7` | 1.000 | 0.800 | 0.800 |
| `deepseek-v4-pro` | 0.963 | 0.762 | 0.500 |
| `gemini-3.1-pro-preview` | 1.000 | 0.800 | 0.300 |
| `gpt-5.4` | 0.838 | 0.787 | 0.600 |
| `kimi-k2.6` | 1.000 | 0.775 | 0.400 |

Purpose: active verification is the hardest and most agent-like layer.

### Figure 4: Evidence Condition Breakdown

Generated lore should be visually highlighted.

| Model | Clean | Conflicting | False consensus | Buried primary | Generated lore |
| --- | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 1.000 | 1.000 | 1.000 | 0.800 | 0.600 |
| `deepseek-v4-pro` | 0.875 | 0.825 | 0.950 | 0.800 | 0.500 |
| `gemini-3.1-pro-preview` | 0.950 | 0.900 | 0.825 | 0.800 | 0.425 |
| `gpt-5.4` | 0.975 | 0.975 | 1.000 | 0.800 | 0.100 |
| `kimi-k2.6` | 0.925 | 0.850 | 0.850 | 0.800 | 0.525 |

Purpose: generated lore is where simple answer accuracy can hide evidence-role failures.

### Figure 5: Prompt Intervention Slope

| Model | Standard | Hygiene instruction | Reading |
| --- | ---: | ---: | --- |
| `claude-opus-4-7` | 0.880 | 0.880 | flat |
| `deepseek-v4-pro` | 0.780 | 0.800 | slight gain |
| `gemini-3.1-pro-preview` | 0.780 | 0.780 | flat |
| `gpt-5.4` | 0.750 | 0.790 | gain |
| `kimi-k2.6` | 0.810 | 0.770 | decline |

Purpose: "be careful about evidence" is not a universal prompt fix.

## Case Studies To Put Before Dense Tables

### Case 1: GPT-5.4 Generated Lore Is Not A Belief Failure

In the current-schema main run, GPT-5.4 on generated-lore records has:

| Metric | Value |
| --- | ---: |
| n | 40 |
| belief correctness | 1.000 |
| insufficient verdict rate | 1.000 |
| rejected pollutant rate | 1.000 |
| polluted supporting evidence rate | 0.900 |
| dual-role pollutant rate | 0.875 |
| full escape | 0.100 |

This should change the wording. Do not write: "GPT-5.4 cannot detect generated lore."

Write instead:

> GPT-5.4 often recognizes generated lore at the belief layer, but the current schema exposes unstable evidence-role assignment: polluted material appears in machine-readable support fields even when the prose rejects it.

The clarified-schema mini-rerun supports this interpretation. Under clarified fields (`clean_supporting_evidence`, `rejected_or_contaminated_evidence`, `diagnostic_evidence`), GPT-5.4's polluted-supporting rate on the same generated-lore slice drops from 0.900 to 0.000, with 40/40 parse success.

### Case 2: Active Verification Is An Agent Interface Problem

One active-verification row (`gpt-5.4`, `ert_082`, clean condition) judged the claim correctly and cited clean primary evidence. It still failed the verification-action score because the action target bundled several IDs into one string rather than producing a machine-checkable target.

Interpretation:

> The failure is not ordinary answer correctness. It is whether the model expresses the next action in a form an agent system can safely execute and audit.

This is why active verification should remain a main figure, not an appendix metric.

### Case 3: Prompt Hygiene Is Not A General Cure

The hygiene instruction improves GPT-5.4 from 0.750 to 0.790 and DeepSeek from 0.780 to 0.800, but Kimi declines from 0.810 to 0.770 while Claude and Gemini are flat.

Interpretation:

> Epistemic resilience is not reliably induced by a single sentence telling the model to be careful. It interacts with model habits, schema semantics, and task family.

## Token-Budget Fairness In One Paragraph

DeepSeek and Kimi used no-cap profiles because capped settings caused empty outputs in audit. The full run shows this did not create visible-output inflation: DeepSeek averaged about 400 visible tokens, Kimi about 404, and both had `overlength_rate=0`. This should be reported as provider-compatible stability, not as an unfair longer-answer advantage.

## Revised Abstract Paragraph

Future LLM agents rarely encounter facts directly. They encounter search results, reposts, knowledge-base fragments, generated pages, and other models' summaries. EHA evaluates whether frontier models remain epistemically reliable in such polluted evidence environments: whether they judge claims correctly, cite clean evidence, abstain when evidence is insufficient, and choose useful verification actions. In 100 synthetic evidence tasks across five frontier provider models, failures were not reducible to answer accuracy. Models often knew the right verdict while failing at evidence-role discipline or verification behavior; generated lore exposed a particularly important gap between natural-language recognition and machine-readable evidence hygiene. Prompting models to be careful about evidence helped some models but not others, suggesting that epistemic resilience is a system property of model, schema, and evidence environment rather than a generic prompt fix.

## Artifacts Behind This Narrative

- Main run: `eha-mvp/results/reports-eha-frontier-main/`
- Generated-lore role audit: `eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/`
- Existing-output decomposition: `generated_lore_belief_vs_role_decomposition.csv`
- Manual audit pack: `gpt54_generated_lore_audit_pack.jsonl`
- Clarified-schema mini-rerun: `schema_clarification_mini_rerun.csv`
- Side note update: `side_note_update.md`
