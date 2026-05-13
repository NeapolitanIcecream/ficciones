# EHA Phase 2 Failure Cases

## `eha2_000`

- Model / strategy / retriever: `openai/gpt-4o-mini` / `evidence_graph_v2` / `oracle_root_dedup_top8`
- Episode type: `clean_control`
- Gold claim verdict: `supported`
- Predicted claim verdict: `insufficient`
- Gold scope tag: `full`
- Predicted scope tag: `no_primary_source`
- Confidence: `0.000`
- Supporting evidence: `-`
- Rejected evidence: `-`

## `eha2_007`

- Model / strategy / retriever: `openai/gpt-4o-mini` / `evidence_graph_v2` / `bm25_top8`
- Episode type: `false_consensus`
- Gold claim verdict: `refuted`
- Predicted claim verdict: `insufficient`
- Gold scope tag: `conflicting`
- Predicted scope tag: `no_primary_source`
- Confidence: `0.700`
- Supporting evidence: `eha2_007_pollutant_root`
- Rejected evidence: `-`

## `eha2_007`

- Model / strategy / retriever: `openai/gpt-4o-mini` / `evidence_graph_v2` / `bm25_top12`
- Episode type: `false_consensus`
- Gold claim verdict: `refuted`
- Predicted claim verdict: `insufficient`
- Gold scope tag: `conflicting`
- Predicted scope tag: `no_primary_source`
- Confidence: `0.600`
- Supporting evidence: `eha2_007_pollutant_root`
- Rejected evidence: `-`

## `eha2_009`

- Model / strategy / retriever: `openai/gpt-4o-mini` / `evidence_graph_v2` / `bm25_top8`
- Episode type: `false_consensus`
- Gold claim verdict: `refuted`
- Predicted claim verdict: `insufficient`
- Gold scope tag: `conflicting`
- Predicted scope tag: `no_primary_source`
- Confidence: `0.500`
- Supporting evidence: `eha2_009_pollutant_root`
- Rejected evidence: `-`

## `eha2_017`

- Model / strategy / retriever: `openai/gpt-4o-mini` / `evidence_graph_v2` / `primary_preserve_top8`
- Episode type: `temporal_pollution`
- Gold claim verdict: `refuted`
- Predicted claim verdict: `refuted`
- Gold scope tag: `stale`
- Predicted scope tag: `stale`
- Confidence: `0.950`
- Supporting evidence: `eha2_017_primary_b,eha2_017_primary_a,eha2_017_appendix`
- Rejected evidence: `eha2_017_pollutant_root,eha2_017_repost_00,eha2_017_repost_01,eha2_017_repost_02,eha2_017_repost_03`

## `eha2_018`

- Model / strategy / retriever: `openai/gpt-4o-mini` / `evidence_graph_v2` / `bm25_top8`
- Episode type: `temporal_pollution`
- Gold claim verdict: `refuted`
- Predicted claim verdict: `refuted`
- Gold scope tag: `stale`
- Predicted scope tag: `stale`
- Confidence: `0.950`
- Supporting evidence: `eha2_018_primary_a,eha2_018_primary_b,eha2_018_appendix`
- Rejected evidence: `eha2_018_pollutant_root,eha2_018_repost_00,eha2_018_repost_01,eha2_018_repost_02,eha2_018_repost_03`

## `eha2_022`

- Model / strategy / retriever: `openai/gpt-4o-mini` / `evidence_graph_v2` / `bm25_top8`
- Episode type: `halupedia_trap`
- Gold claim verdict: `insufficient`
- Predicted claim verdict: `refuted`
- Gold scope tag: `no_primary_source`
- Predicted scope tag: `mixed_evidence`
- Confidence: `0.900`
- Supporting evidence: `-`
- Rejected evidence: `eha2_022_repost_00,eha2_022_repost_01,eha2_022_repost_02,eha2_022_pollutant_root,eha2_022_background_00,eha2_022_background_01,eha2_022_background_02`

## `eha2_022`

- Model / strategy / retriever: `openai/gpt-4o-mini` / `evidence_graph_v2` / `bm25_top12`
- Episode type: `halupedia_trap`
- Gold claim verdict: `insufficient`
- Predicted claim verdict: `refuted`
- Gold scope tag: `no_primary_source`
- Predicted scope tag: `full`
- Confidence: `0.900`
- Supporting evidence: `eha2_022_primary_a`
- Rejected evidence: `eha2_022_repost_00,eha2_022_repost_01,eha2_022_repost_02,eha2_022_pollutant_root,eha2_022_background_00,eha2_022_background_01,eha2_022_background_02,eha2_022_context_00,eha2_022_context_01,eha2_022_context_02,eha2_022_context_03`
