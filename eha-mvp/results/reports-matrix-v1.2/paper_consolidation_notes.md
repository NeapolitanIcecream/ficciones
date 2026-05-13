# Paper Consolidation Notes

## Main Claim

LLM factual reliability is not only a model-capability problem; it is also an information-supply-chain problem. In the EHA Matrix, stronger models still fail systematically when retrieval excludes primary evidence and saturates the context with pollutant evidence. Retrieval-layer information hygiene restores escape across seeds, while metadata/source spoofing shows that hygiene mechanisms themselves need to rely on signals harder to forge than simple source labels.

## Results To Center

1. Multi-seed replication: L4 hidden-primary remains the stable failure point for naive BM25. In `multiseed_cluster_ci.csv`, both `openai/gpt-4o-mini` and `openai/gpt-5.4-mini` have L4 `naive_bm25` escape rate `0.000` with seed-cluster CI `0.000-0.000`.
2. Hygiene beats model scale under missing evidence: `primary_preserve` and `hygienic_combo` restore L4 escape because they put primary evidence back into context.
3. Metadata spoofing is a real limitation: the v1.1 noisy stress should be discussed as evidence that simple metadata-based hygiene is insufficient by itself.
4. Prompt v1.1 helps output discipline, not missing evidence. In `prompt_hygiene_preflight.csv`, `claim_first_citation_v1_1` improves required-support behavior for hygiene strategies on the 48-task preflight subset.
5. L4 mechanism audit: in `l4_primary_recovery_audit.csv`, naive/careful BM25 has `primary_in_context=0.000`, while `primary_preserve` and `hygienic_combo` have `primary_in_context=1.000`. This supports the mechanism claim that L4 failure is evidence exclusion, not merely model weakness.

## Manuscript Structure

1. Problem: RAG shifts factual reliability from model internals to the evidence supply chain.
2. Benchmark: EHA Matrix synthetic mini-web, L0-L5 difficulty, escape rate requiring correct claim, clean support, and generated-lore abstention.
3. Main result: Matrix v1 shows hygiene can matter more than model scale under naive retrieval.
4. Robustness: Matrix v1.1/v1.2 show multi-seed cluster CIs and metadata spoofing stress.
5. Mechanism: L4 primary recovery audit explains why hidden-primary failures persist under BM25.
6. Prompt analysis: prompt v1.1 improves citation discipline but cannot recover absent evidence.
7. Limitations: synthetic setting, non-adaptive spoofing, only three seed clusters, generated gold labels, no live web adversary.
8. Conclusion: reliable LLM systems need information hygiene in retrieval and provenance, not only stronger generators.

## Claims To Avoid

- Do not claim this solves RAG poisoning.
- Do not claim stronger models are useless.
- Do not claim all pollution regimes reliably defeat naive RAG; L3 false consensus is not consistently hard after v1.1.
- Do not claim metadata labels alone are enough for hygiene.
