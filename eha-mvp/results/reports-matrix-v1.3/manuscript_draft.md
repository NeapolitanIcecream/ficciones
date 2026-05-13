# Evidence Environments: Evaluating Retrieval Hygiene Under Polluted Information Ecosystems

## Abstract Draft

Large language model reliability is often framed as a property of the generator: a stronger model should answer more accurately. This paper argues that retrieval-augmented systems also depend on the evidence environment constructed by retrieval. We introduce the EHA Matrix, a synthetic mini-web benchmark that tests whether a model can escape polluted evidence while producing clean supporting citations and abstaining from generated lore. Across Matrix v1, multi-seed robustness checks, metadata-spoofing stress, and a full prompt+hygiene confirmation sweep, the strongest failure mode is not model incapacity alone. In L4 hidden-primary episodes, naive BM25 excludes primary evidence from context; both `gpt-4o-mini` and `gpt-5.4-mini` have escape rate `0.000` with seed-cluster CI `0.000-0.000`. When retrieval restores primary evidence through `primary_preserve` or `hygienic_combo`, L4 escape recovers to roughly `0.917-1.000`. A stricter claim-first prompt improves evidence discipline when primary evidence is already available, but it cannot recover evidence absent from the context. These results support a narrower claim: reliable LLM agents need retrieval-layer information hygiene, not only stronger generators.

## Reader Problem

Target readers know that RAG can improve factuality, and many will expect better models or better prompts to handle noisy evidence. The problem is that this framing treats retrieval as a neutral conduit. In polluted information ecosystems, retrieval constructs the model's evidence environment. If primary evidence is crowded out by reposts, generated lore, or source-spoofed pollutant evidence, even a capable model may be forced to reason from a false context.

This paper helps readers distinguish two failure modes:

1. Evidence discipline failure: the model has adequate evidence but cites, rejects, or abstains poorly.
2. Evidence availability failure: the retrieval layer never supplies the primary evidence needed to answer correctly.

## Thesis

LLM factual reliability in RAG systems is partly an evidence-supply-chain problem. In the EHA Matrix, prompt design improves evidence discipline, but hidden-primary failures are resolved only when retrieval hygiene restores primary evidence to the model's context.

## Contributions

1. A synthetic mini-web benchmark, EHA Matrix, that evaluates escape from polluted evidence rather than answer accuracy alone.
2. A composite escape metric decomposed into claim correctness, clean supporting evidence, required supporting evidence, and generated-lore abstention.
3. Multi-seed robustness evidence with seed-cluster confidence intervals showing that L4 hidden-primary failures are stable under naive BM25.
4. A primary-recovery mechanism audit showing that L4 failures occur because primary evidence is absent from the context, not because models ignore visible primary evidence.
5. A prompt+hygiene confirmation sweep showing that `claim_first_citation_v1_1` improves citation discipline across L0-L5 when paired with hygiene retrievers.

## Central Figure

Figure 1 should plot L4 hidden-primary by strategy:

| strategy | primary_in_context | escape_rate | interpretation |
| --- | --- | --- | --- |
| naive_bm25 | 0.000 | 0.000 | primary evidence excluded |
| careful_bm25 | 0.000 | 0.000 | prompt cannot recover absent evidence |
| primary_preserve | 1.000 | 0.917-1.000 | primary evidence restored |
| hygienic_combo | 1.000 | 0.917-1.000 | primary evidence restored with pollution suppression |

Caption claim: L4 hidden-primary failures are evidence-availability failures. The generator cannot cite or reason from primary evidence that retrieval never places in the context.

## Section Plan

### 1. Introduction

Open with the shift from clean knowledge bases to polluted information ecosystems. State that RAG does not merely add knowledge; it constructs the evidence environment a model inhabits. Introduce hidden-primary as the motivating failure: true primary evidence exists, but retrieval ranks pollutant reposts and false-consensus material above it.

End the introduction with the thesis and contributions. Avoid claiming that the paper solves RAG poisoning. The paper proposes a benchmark and mechanism evidence for information hygiene.

### 2. Related Work To Add

This draft still needs external literature. Add sources for:

- RAG and retrieval-augmented factuality. [citation needed]
- LLM factuality and hallucination benchmarks. [citation needed]
- Data poisoning, misinformation, source spoofing, and citation laundering. [citation needed]
- Provenance, source reliability, and evidence-ranking systems. [citation needed]
- Synthetic benchmark design and limitations. [citation needed]

Do not overstate these sources. Use them to position EHA Matrix as a benchmark for evidence environments, not as a complete security defense.

### 3. Benchmark

Define the EHA Matrix as a synthetic mini-web of task episodes. Each episode contains agent-visible documents, gold documents, dependency/citation relations, and a target claim. The model must answer with a claim verdict and supporting evidence.

Define the six difficulty levels:

- L0: clean or mostly straightforward evidence.
- L1-L2: increasingly noisy or partial support conditions.
- L3: false consensus and repeated pollutant material.
- L4: hidden primary evidence crowded out by pollutant retrieval.
- L5: generated lore packaged as plausible evidence.

Define escape as stricter than accuracy: a run escapes only when the claim verdict is correct, supporting evidence is clean or the model abstains where appropriate, and generated lore is not overclaimed.

### 4. Methods

Compare models under retrieval strategies rather than treating the model as the only variable. The main strategies are:

- `naive_bm25`: standard lexical top-k retrieval.
- `careful_bm25`: BM25 plus a claim-first citation prompt.
- `primary_preserve`: retrieval that preserves primary evidence.
- `hygienic_combo`: primary preservation plus pollution suppression and source diversity.

Report the following metrics in every main table:

- `escape_rate`
- `claim_accuracy`
- `contaminated_citation_rate`
- `generated_lore_overclaim_rate`
- `primary_in_context` for L4
- `primary_cited` for L4
- `primary_ignored` for L4
- `mean_best_primary_context_rank` for L4

### 5. Main Results

Use Matrix v1 and v1.1 as the main evidence. The central result is that retrieval hygiene can matter more than model scaling when retrieval excludes the primary source.

Key result statements:

- In multi-seed L4, `naive_bm25` has escape rate `0.000` for both `gpt-4o-mini` and `gpt-5.4-mini`; seed-cluster CIs are `0.000-0.000`.
- Under `primary_preserve` and `hygienic_combo`, L4 escape recovers to `0.917-1.000`.
- L3 false consensus is not consistently hard after multi-seed replication; do not use L3 as the main failure claim.
- L5 generated lore is a different mechanism: stronger models help reduce overclaim, but clean citation requirements still matter.

### 6. Mechanism: L4 Primary Recovery

This section should be short and central. The audit result is the paper's clearest mechanism evidence:

- For L4, `naive_bm25` and `careful_bm25` have `primary_in_context=0.000`.
- For L4, `primary_preserve` and `hygienic_combo` have `primary_in_context=1.000` and mean best primary context rank `1.000`.
- Once primary evidence is in context, claim accuracy recovers to `1.000` and escape recovers to `0.917-1.000`.

Warrant: this supports the claim that L4 failure is an evidence-availability failure. The model is not primarily failing to use visible primary evidence; retrieval is failing to supply it.

### 7. Prompt Analysis

Use the v1.3 full L0-L5 prompt+hygiene sweep.

Result:

- With `hygienic_combo`, `claim_first_citation_v1_1` reaches escape `1.000` on L0-L5 in the full sweep.
- With `primary_preserve`, v1.1 reaches escape `1.000` on L0-L4 and `0.958` on L5.
- v1.1 drives contaminated citation rate to `0.000` for both hygiene strategies in the full sweep.
- On L0-L2, v1.1 has `over_abstention_rate=0.000` for both hygiene strategies, so the stricter support requirement does not appear to create a new abstention cost on clean/easier episodes.

Interpretation: prompt v1.1 improves evidence discipline when retrieval has already supplied good evidence. It does not replace retrieval hygiene.

### 8. Robustness And Limits

Robustness:

- Multi-seed replication reduces concern that the L4 result is a single-seed artifact.
- Seed-cluster CIs make the uncertainty statement stricter than row-only bootstrap.
- Metadata/source spoofing stress shows that hygiene mechanisms can degrade when metadata is unreliable.

Limitations:

- The mini-web is synthetic and does not cover live open-web adversaries.
- Seed clusters are still few.
- Metadata spoofing is not a fully adaptive attack.
- Gold labels are generated and should be audited if the work targets a higher-stakes venue.
- This is a benchmark and analysis paper, not a complete RAG-poisoning defense.

### 9. Conclusion

Conclude with the central sentence:

LLM reliability is not only a model-capability problem; RAG retrieval decides what evidence the model can see, and when the evidence supply chain excludes primary evidence, stronger models can still be trapped in a false evidence environment.

## AI-Use Disclosure Draft

Parts of the experimental orchestration, report generation, and manuscript drafting were assisted by an AI coding/writing assistant. The authors remain responsible for experimental design, verification, interpretation, and final text. No external source claims or citations should be included in the final paper without human verification.
