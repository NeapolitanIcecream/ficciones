# Epistemic Resilience Reframe

## Core Claim

EHA should be framed as a benchmark for LLM epistemic resilience in polluted evidence environments, not as a RAG benchmark whose main result is that primary evidence helps and missing primary evidence hurts.

The research question is:

> Can a model maintain calibrated belief, clean evidence use, and disciplined uncertainty when the visible evidence environment contains reposts, false consensus, stale records, generated lore, buried primary evidence, or direct contradiction?

This moves the central object from retrieval quality to evidential capture. RAG is still important, but as a mechanism that constructs the evidence environment presented to the model.

## Operational Definition

An epistemic escape requires three conditions:

1. Belief correctness: the predicted verdict matches the gold verdict.
2. Evidence cleanliness: the model does not rely on contaminated, stale, generated, or false-support documents as support.
3. Uncertainty discipline: the model abstains when the gold answer is insufficient and does not abstain when the evidence supports a determinate verdict.

For evidence-selection tasks, the escape criterion is source oriented: the model must select high-value evidence, avoid duplicate upstream roots, and avoid generated lore.

For active-verification tasks, the escape criterion also requires appropriate next actions: primary-source seeking, contradiction checks, version comparison, or provenance tracing depending on the evidence condition.

## Table Design

Epistemic Resilience Table v1 uses 100 tasks:

| Family | Count | Purpose |
| --- | ---: | --- |
| Fixed evidence packet judgment | 40 | Judge claims from a bounded packet and avoid dirty support. |
| Next-evidence selection | 40 | Select the highest-value evidence to inspect next. |
| Active verification | 20 | Choose verification actions under polluted evidence. |

The evidence conditions are balanced across the full task set:

| Condition | Count |
| --- | ---: |
| clean | 20 |
| conflicting_evidence | 20 |
| false_consensus | 20 |
| buried_primary | 20 |
| generated_lore | 20 |

The current API run covers:

| Model | Scope |
| --- | --- |
| openai/gpt-4o-mini | 100 tasks x 2 prompts |
| openai/gpt-5-mini | 100 tasks x 2 prompts |
| openai/gpt-5.4-mini | 100 tasks x 2 prompts |
| openai/gpt-5.5 | 12-task family-and-condition-stratified sample x 2 prompts |

Prompt conditions:

| Prompt | Description |
| --- | --- |
| standard_answer | Baseline JSON answer instruction. |
| epistemic_hygiene_instruction | Adds explicit hygiene rules for pseudo-consensus, primary records, generated lore, stale evidence, and abstention. |

## RAG As Case Study

The RAG findings should be repositioned as a case study titled "Retrieval as Evidence Environment Construction."

The manuscript should avoid claiming that the key contribution is simply that primary retrieval improves answers. A stronger and less obvious claim is:

> Retrieval systems do not merely supply facts; they construct the evidential environment in which an LLM's belief, evidence use, and uncertainty discipline are tested.

This permits the RAG experiments to support the broader epistemic-resilience argument: retrieval choices can reduce or amplify evidential capture by false consensus, generated lore, stale sources, and citation laundering.

External literature claims about RAG, source reliability, hallucination, epistemic vigilance, or information pollution should be inserted only with verified citations. Use `[citation needed]` placeholders until the source has been checked.

## Current Empirical Read

The final report is in `results/reports-epistemic-resilience-v1/summary.md`.

The main table now separates task families:

| Model | Prompt | Avg epistemic escape |
| --- | --- | ---: |
| openai/gpt-4o-mini | standard_answer | 0.792 |
| openai/gpt-4o-mini | epistemic_hygiene_instruction | 0.742 |
| openai/gpt-5-mini | standard_answer | 0.375 |
| openai/gpt-5-mini | epistemic_hygiene_instruction | 0.333 |
| openai/gpt-5.4-mini | standard_answer | 0.425 |
| openai/gpt-5.4-mini | epistemic_hygiene_instruction | 0.508 |
| openai/gpt-5.5 | standard_answer | 0.750 |
| openai/gpt-5.5 | epistemic_hygiene_instruction | 0.833 |

Interpretive caveats:

1. The `openai/gpt-5.5` result is a 12-task small sample, not a full 100-task run.
2. The `openai/gpt-5-mini` run had substantial structured-output parse failure under this endpoint and schema. These failures are counted as failed benchmark records and should be reported as an execution caveat.
3. These are synthetic polluted evidence environments. Claims about real-world RAG or human information behavior require verified external citations.

