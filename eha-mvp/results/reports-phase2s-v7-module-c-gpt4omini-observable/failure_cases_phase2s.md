# EHA Phase 2S Failure Cases

## `eha2r_001`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `primary_preserve_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `clean_control`
- Gold claim / predicted claim: `supported` / `supported`
- Gold risks: `-`
- Predicted risks: `stale_evidence,false_consensus`
- Confidence: `0.900`
- Supporting evidence: `eha2r_001_primary_a,eha2r_001_primary_b`
- Rejected evidence: `eha2r_001_pollutant_root,eha2r_001_repost_00,eha2r_001_repost_01,eha2r_001_repost_02,eha2r_001_repost_04,eha2r_001_repost_03`
- Ledger evidence: `eha2r_001_primary_a,eha2r_001_primary_b,eha2r_001_pollutant_root,eha2r_001_repost_00,eha2r_001_repost_01,eha2r_001_repost_02,eha2r_001_repost_04,eha2r_001_repost_03`

## `eha2r_004`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `bm25_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `clean_control`
- Gold claim / predicted claim: `supported` / `supported`
- Gold risks: `-`
- Predicted risks: `stale_evidence,false_consensus`
- Confidence: `0.900`
- Supporting evidence: `eha2r_004_primary_a,eha2r_004_primary_b`
- Rejected evidence: `eha2r_004_pollutant_root,eha2r_004_repost_01,eha2r_004_repost_02,eha2r_004_repost_03,eha2r_004_repost_00`
- Ledger evidence: `eha2r_004_primary_a,eha2r_004_primary_b,eha2r_004_pollutant_root,eha2r_004_repost_01,eha2r_004_repost_02,eha2r_004_repost_03,eha2r_004_repost_00`

## `eha2r_008`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `bm25_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `stale_evidence,conflicting_evidence,false_consensus`
- Confidence: `0.900`
- Supporting evidence: `eha2r_008_primary_a,eha2r_008_primary_b`
- Rejected evidence: `eha2r_008_pollutant_root,eha2r_008_repost_00,eha2r_008_repost_02,eha2r_008_repost_03,eha2r_008_repost_04,eha2r_008_repost_05`
- Ledger evidence: `eha2r_008_primary_a,eha2r_008_primary_b`

## `eha2r_008`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `primary_preserve_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `conflicting_evidence,false_consensus`
- Confidence: `0.900`
- Supporting evidence: `eha2r_008_primary_a,eha2r_008_primary_b`
- Rejected evidence: `eha2r_008_pollutant_root,eha2r_008_repost_00,eha2r_008_repost_02,eha2r_008_repost_03,eha2r_008_repost_04,eha2r_008_repost_05`
- Ledger evidence: `eha2r_008_primary_a,eha2r_008_primary_b,eha2r_008_pollutant_root,eha2r_008_repost_00,eha2r_008_repost_02,eha2r_008_repost_03,eha2r_008_repost_04,eha2r_008_repost_05`

## `eha2r_008`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `hygienic_combo_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `conflicting_evidence,false_consensus,citation_laundering,stale_evidence`
- Confidence: `0.900`
- Supporting evidence: `eha2r_008_primary_a,eha2r_008_primary_b`
- Rejected evidence: `eha2r_008_pollutant_root,eha2r_008_repost_00,eha2r_008_repost_02,eha2r_008_context_10,eha2r_008_context_11,eha2r_008_context_12`
- Ledger evidence: `eha2r_008_primary_a,eha2r_008_primary_b,eha2r_008_pollutant_root,eha2r_008_repost_00,eha2r_008_repost_02`

## `eha2r_009`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `bm25_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `stale_evidence,conflicting_evidence,citation_laundering,false_consensus`
- Confidence: `0.950`
- Supporting evidence: `eha2r_009_primary_a,eha2r_009_primary_b`
- Rejected evidence: `eha2r_009_pollutant_root,eha2r_009_repost_01,eha2r_009_repost_02,eha2r_009_repost_03,eha2r_009_repost_04,eha2r_009_repost_06`
- Ledger evidence: `eha2r_009_primary_a,eha2r_009_primary_b,eha2r_009_pollutant_root,eha2r_009_repost_01,eha2r_009_repost_02,eha2r_009_repost_03,eha2r_009_repost_04,eha2r_009_repost_06`

## `eha2r_009`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `primary_preserve_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `conflicting_evidence,false_consensus,citation_laundering`
- Confidence: `0.900`
- Supporting evidence: `eha2r_009_primary_a,eha2r_009_primary_b`
- Rejected evidence: `eha2r_009_pollutant_root,eha2r_009_repost_01,eha2r_009_repost_02,eha2r_009_repost_03,eha2r_009_repost_04,eha2r_009_repost_06`
- Ledger evidence: `eha2r_009_primary_a,eha2r_009_primary_b`

## `eha2r_009`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `hygienic_combo_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `stale_evidence,conflicting_evidence`
- Confidence: `0.950`
- Supporting evidence: `eha2r_009_primary_a,eha2r_009_primary_b`
- Rejected evidence: `eha2r_009_pollutant_root,eha2r_009_repost_01,eha2r_009_repost_02,eha2r_009_context_10,eha2r_009_context_11,eha2r_009_context_12`
- Ledger evidence: `eha2r_009_primary_a,eha2r_009_primary_b,eha2r_009_pollutant_root,eha2r_009_repost_01,eha2r_009_repost_02`

## `eha2r_010`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `bm25_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `stale_evidence,conflicting_evidence,false_consensus`
- Confidence: `0.900`
- Supporting evidence: `eha2r_010_primary_a,eha2r_010_primary_b`
- Rejected evidence: `eha2r_010_pollutant_root,eha2r_010_repost_00,eha2r_010_repost_01,eha2r_010_repost_02,eha2r_010_repost_03,eha2r_010_repost_05`
- Ledger evidence: `eha2r_010_primary_a,eha2r_010_primary_b,eha2r_010_pollutant_root,eha2r_010_repost_00,eha2r_010_repost_01,eha2r_010_repost_02,eha2r_010_repost_03,eha2r_010_repost_05`

## `eha2r_010`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v7` / `primary_preserve_top8`
- Prompt: `evidence_diagnostics_v7`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `false_consensus,citation_laundering,stale_evidence`
- Confidence: `0.950`
- Supporting evidence: `eha2r_010_primary_a,eha2r_010_primary_b`
- Rejected evidence: `eha2r_010_pollutant_root,eha2r_010_repost_00,eha2r_010_repost_01,eha2r_010_repost_02,eha2r_010_repost_03,eha2r_010_repost_05`
- Ledger evidence: `eha2r_010_primary_a,eha2r_010_primary_b`
