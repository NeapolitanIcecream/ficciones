# EHA-Uncued Micro Shortcut Baselines

Date: 2026-05-22

## Gate Summary

| passed | baseline_count | gate_count |
| --- | --- | --- |
| True | 12 | 30 |

## Aggregate Metrics

| baseline | view | n | verdict_accuracy | operational_epistemic_escape | role_reconstruction_accuracy | polluted_support_rate |
| --- | --- | --- | --- | --- | --- | --- |
| always_insufficient | neutral_metadata_hidden | 10 | 0.200 | 0.000 | 0.000 | 0.000 |
| always_insufficient | neutral_metadata_visible | 10 | 0.200 | 0.000 | 0.000 | 0.000 |
| citation_graph_only | neutral_metadata_hidden | 10 | 0.200 | 0.000 | 0.000 | 0.000 |
| citation_graph_only | neutral_metadata_visible | 10 | 0.200 | 0.000 | 0.000 | 0.000 |
| claim_overlap_only | neutral_metadata_hidden | 10 | 0.200 | 0.000 | 0.000 | 0.000 |
| claim_overlap_only | neutral_metadata_visible | 10 | 0.200 | 0.000 | 0.000 | 0.000 |
| cue_phrase_only | neutral_metadata_hidden | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| cue_phrase_only | neutral_metadata_visible | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| document_order_only | neutral_metadata_hidden | 10 | 0.300 | 0.100 | 0.000 | 0.200 |
| document_order_only | neutral_metadata_visible | 10 | 0.300 | 0.000 | 0.000 | 0.300 |
| id_only | neutral_metadata_hidden | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| id_only | neutral_metadata_visible | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| metadata_only | neutral_metadata_hidden | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| metadata_only | neutral_metadata_visible | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| random_valid_schema | neutral_metadata_hidden | 10 | 0.400 | 0.000 | 0.000 | 0.000 |
| random_valid_schema | neutral_metadata_visible | 10 | 0.600 | 0.000 | 0.000 | 0.000 |
| simple_heuristic | neutral_metadata_hidden | 10 | 0.500 | 0.400 | 0.000 | 0.200 |
| simple_heuristic | neutral_metadata_visible | 10 | 0.500 | 0.300 | 0.000 | 0.300 |
| source_type_only | neutral_metadata_hidden | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| source_type_only | neutral_metadata_visible | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| timestamp_only | neutral_metadata_hidden | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| timestamp_only | neutral_metadata_visible | 10 | 0.300 | 0.000 | 0.000 | 0.000 |
| title_only | neutral_metadata_hidden | 10 | 0.200 | 0.000 | 0.000 | 0.000 |
| title_only | neutral_metadata_visible | 10 | 0.200 | 0.000 | 0.000 | 0.000 |

## Gate Rows

| baseline | view | metric | value | limit | passed |
| --- | --- | --- | --- | --- | --- |
| always_insufficient | neutral_metadata_hidden | operational_epistemic_escape | 0.000 | 0.300 | True |
| always_insufficient | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.300 | True |
| citation_graph_only | neutral_metadata_hidden | operational_epistemic_escape | 0.000 | 0.350 | True |
| citation_graph_only | neutral_metadata_hidden | verdict_accuracy | 0.200 | 0.600 | True |
| citation_graph_only | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.350 | True |
| citation_graph_only | neutral_metadata_visible | verdict_accuracy | 0.200 | 0.600 | True |
| claim_overlap_only | neutral_metadata_hidden | operational_epistemic_escape | 0.000 | 0.350 | True |
| claim_overlap_only | neutral_metadata_hidden | polluted_support_rate | 0.000 | 0.600 | True |
| claim_overlap_only | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.350 | True |
| claim_overlap_only | neutral_metadata_visible | polluted_support_rate | 0.000 | 0.600 | True |
| cue_phrase_only | neutral_metadata_hidden | operational_epistemic_escape | 0.000 | 0.100 | True |
| cue_phrase_only | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.100 | True |
| document_order_only | neutral_metadata_hidden | operational_epistemic_escape | 0.100 | 0.150 | True |
| document_order_only | neutral_metadata_hidden | verdict_accuracy | 0.300 | 0.450 | True |
| document_order_only | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.150 | True |
| document_order_only | neutral_metadata_visible | verdict_accuracy | 0.300 | 0.450 | True |
| id_only | neutral_metadata_hidden | operational_epistemic_escape | 0.000 | 0.100 | True |
| id_only | neutral_metadata_hidden | verdict_accuracy | 0.300 | 0.400 | True |
| id_only | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.100 | True |
| id_only | neutral_metadata_visible | verdict_accuracy | 0.300 | 0.400 | True |
| metadata_only | neutral_metadata_hidden | operational_epistemic_escape | 0.000 | 0.200 | True |
| metadata_only | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.350 | True |
| source_type_only | neutral_metadata_hidden | operational_epistemic_escape | 0.000 | 0.100 | True |
| source_type_only | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.250 | True |
| timestamp_only | neutral_metadata_hidden | verdict_accuracy | 0.300 | 0.550 | True |
| timestamp_only | neutral_metadata_visible | verdict_accuracy | 0.300 | 0.550 | True |
| title_only | neutral_metadata_hidden | operational_epistemic_escape | 0.000 | 0.250 | True |
| title_only | neutral_metadata_hidden | role_reconstruction_accuracy | 0.000 | 0.450 | True |
| title_only | neutral_metadata_visible | operational_epistemic_escape | 0.000 | 0.250 | True |
| title_only | neutral_metadata_visible | role_reconstruction_accuracy | 0.000 | 0.450 | True |
