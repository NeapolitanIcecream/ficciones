# EHA Phase 2S Failure Cases

## `eha2r_000`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `bm25_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `clean_control`
- Gold claim / predicted claim: `supported` / `supported`
- Gold risks: `-`
- Predicted risks: `-`
- Confidence: `0.950`
- Supporting evidence: `eha2r_000_primary_a,eha2r_000_primary_b`
- Rejected evidence: `eha2r_000_pollutant_root,eha2r_000_repost_00,eha2r_000_repost_01,eha2r_000_repost_02,eha2r_000_repost_03,eha2r_000_repost_04`
- Ledger evidence: `eha2r_000_primary_a,eha2r_000_primary_b`

## `eha2r_002`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `hygienic_combo_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `clean_control`
- Gold claim / predicted claim: `supported` / `supported`
- Gold risks: `-`
- Predicted risks: `-`
- Confidence: `1.000`
- Supporting evidence: `eha2r_002_primary_a,eha2r_002_primary_b`
- Rejected evidence: `eha2r_002_pollutant_root,eha2r_002_repost_03,eha2r_002_repost_01,eha2r_002_context_13,eha2r_002_context_12,eha2r_002_context_11`
- Ledger evidence: `eha2r_002_primary_a,eha2r_002_primary_b,eha2r_002_pollutant_root,eha2r_002_repost_01,eha2r_002_repost_03`

## `eha2r_007`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `primary_preserve_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `clean_control`
- Gold claim / predicted claim: `supported` / `supported`
- Gold risks: `-`
- Predicted risks: `-`
- Confidence: `1.000`
- Supporting evidence: `eha2r_007_primary_a,eha2r_007_primary_b`
- Rejected evidence: `eha2r_007_pollutant_root,eha2r_007_repost_00,eha2r_007_repost_01,eha2r_007_repost_02,eha2r_007_context_06,eha2r_007_context_07`
- Ledger evidence: `eha2r_007_primary_a,eha2r_007_primary_b`

## `eha2r_008`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `primary_preserve_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `conflicting_evidence`
- Confidence: `0.950`
- Supporting evidence: `eha2r_008_primary_a,eha2r_008_primary_b`
- Rejected evidence: `eha2r_008_pollutant_root,eha2r_008_repost_00,eha2r_008_repost_02,eha2r_008_repost_03,eha2r_008_repost_04,eha2r_008_repost_05`
- Ledger evidence: `eha2r_008_primary_a,eha2r_008_primary_b`

## `eha2r_009`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `bm25_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `conflicting_evidence,false_consensus`
- Confidence: `0.900`
- Supporting evidence: `eha2r_009_primary_a,eha2r_009_primary_b`
- Rejected evidence: `eha2r_009_pollutant_root,eha2r_009_repost_01,eha2r_009_repost_02,eha2r_009_repost_03,eha2r_009_repost_04,eha2r_009_repost_06`
- Ledger evidence: `eha2r_009_primary_a,eha2r_009_primary_b`

## `eha2r_014`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `bm25_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `insufficient`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `no_primary_source,false_consensus`
- Confidence: `0.500`
- Supporting evidence: `-`
- Rejected evidence: `eha2r_014_pollutant_root,eha2r_014_repost_01,eha2r_014_repost_02,eha2r_014_repost_03,eha2r_014_repost_04,eha2r_014_repost_05,eha2r_014_repost_06,eha2r_014_repost_00`
- Ledger evidence: `eha2r_014_pollutant_root,eha2r_014_repost_01,eha2r_014_repost_02,eha2r_014_repost_03,eha2r_014_repost_04,eha2r_014_repost_05,eha2r_014_repost_06,eha2r_014_repost_00`

## `eha2r_029`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `bm25_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `insufficient`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `no_primary_source,partial_support`
- Confidence: `0.700`
- Supporting evidence: `-`
- Rejected evidence: `eha2r_029_pollutant_root,eha2r_029_repost_01,eha2r_029_repost_02,eha2r_029_repost_03,eha2r_029_repost_04,eha2r_029_repost_06,eha2r_029_repost_07,eha2r_029_repost_08`
- Ledger evidence: `eha2r_029_pollutant_root,eha2r_029_repost_01,eha2r_029_repost_02,eha2r_029_repost_03,eha2r_029_repost_04,eha2r_029_repost_06,eha2r_029_repost_07,eha2r_029_repost_08`

## `eha2r_031`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `bm25_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `false_consensus_stress`
- Gold claim / predicted claim: `refuted` / `insufficient`
- Gold risks: `conflicting_evidence,false_consensus`
- Predicted risks: `citation_laundering,false_consensus,no_primary_source`
- Confidence: `0.500`
- Supporting evidence: `-`
- Rejected evidence: `eha2r_031_pollutant_root,eha2r_031_repost_00,eha2r_031_repost_01,eha2r_031_repost_02,eha2r_031_repost_04,eha2r_031_repost_05,eha2r_031_repost_06,eha2r_031_repost_07`
- Ledger evidence: `eha2r_031_pollutant_root,eha2r_031_repost_00,eha2r_031_repost_01,eha2r_031_repost_02,eha2r_031_repost_04,eha2r_031_repost_05,eha2r_031_repost_06,eha2r_031_repost_07`

## `eha2r_040`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `hygienic_combo_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `citation_laundering_trace`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `citation_laundering,conflicting_evidence`
- Predicted risks: `-`
- Confidence: `0.900`
- Supporting evidence: `eha2r_040_primary_a,eha2r_040_primary_b`
- Rejected evidence: `eha2r_040_pollutant_root,eha2r_040_repost_00,eha2r_040_repost_01,eha2r_040_citation_target,eha2r_040_context_09,eha2r_040_context_10`
- Ledger evidence: `eha2r_040_primary_a,eha2r_040_primary_b`

## `eha2r_041`

- Module / dataset: `C` / `EHA-v2R-stress-pilot`
- Model / strategy / retriever: `gpt-4o-mini` / `evidence_diagnostics_v11_role_disciplined_contract` / `bm25_top8`
- Prompt: `evidence_diagnostics_v11_role_disciplined_contract`
- Episode type: `citation_laundering_trace`
- Gold claim / predicted claim: `refuted` / `refuted`
- Gold risks: `citation_laundering,conflicting_evidence`
- Predicted risks: `conflicting_evidence,false_consensus`
- Confidence: `0.900`
- Supporting evidence: `eha2r_041_primary_a,eha2r_041_primary_b`
- Rejected evidence: `eha2r_041_pollutant_root,eha2r_041_repost_00,eha2r_041_repost_01,eha2r_041_repost_02,eha2r_041_repost_03,eha2r_041_citation_target`
- Ledger evidence: `eha2r_041_primary_a,eha2r_041_primary_b`
