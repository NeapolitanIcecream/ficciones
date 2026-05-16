# EHA Step 2 Surface-Cue Scoring Pipeline

Date: 2026-05-16

This no-API report verifies that the surface-cue smoke dataset can be consumed by the Phase 2S scoring contract. The baseline rows are scaffolding and sanity checks, not model evidence.

## Inputs

- Dataset directory: `data/phase2-surface-cue-smoke`
- Tasks: 180
- Documents: 900
- Baseline records: 540
- Baselines: oracle_gold_contract, always_insufficient, source_type_prior

## Baseline Metrics

| strategy | n | claim_accuracy | escape_rate | support_role_valid_rate | support_role_clean_only_rate | contaminated_citation_rate | useful_compare_versions_rate | trace_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_insufficient | 180 | 0.500 | 0.500 | 0.500 | 1.000 | 0.000 | 0.000 | 0.000 |
| oracle_gold_contract | 180 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.167 | 0.167 |
| source_type_prior | 180 | 0.500 | 0.400 | 0.400 | 0.600 | 0.150 | 0.000 | 0.000 |

## Source-Type Prior By Axis

| surface_axis | n | claim_accuracy | support_role_valid_rate | support_role_clean_only_rate | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- |
| adversarial_spoofing | 36 | 0.500 | 0.250 | 0.333 | 0.250 |
| content_only | 36 | 0.500 | 0.500 | 0.833 | 0.000 |
| metadata_perturbation | 36 | 0.500 | 0.250 | 0.333 | 0.500 |
| source_type_visibility | 36 | 0.500 | 0.500 | 0.833 | 0.000 |
| style_normalization | 36 | 0.500 | 0.500 | 0.667 | 0.000 |

## Interpretation

The oracle baseline validates the scorer path. The always-insufficient baseline defines the conservative-abstention floor. The source-type prior is intentionally brittle: it reaches only the abstention-level claim accuracy while adding contaminated support under metadata perturbation and adversarial spoofing. That gives the future API pilot a concrete surface-cue sanity check.
