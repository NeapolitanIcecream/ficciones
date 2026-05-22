# EHA-Uncued Phase 13 Pilot Results

Date: 2026-05-22

Status: passed.

## Scope

Phase 13 scored the Phase 12 four-model pilot run and generated paper-facing tables.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-report-uncued-pilot \
  --dataset-dir data/uncued-pilot-v1 \
  --run-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --out-dir results/reports-eha-uncued-pilot-2026-05-22
```

Inputs:

- Dataset: `eha-mvp/data/uncued-pilot-v1`
- Run records: `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/predictions.jsonl`
- Records scored: 480

## Required Outputs

All required tables were generated in `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/`:

- `uncued_pilot_scored_predictions.csv`
- `uncued_pilot_metrics_by_model.csv`
- `uncued_pilot_metrics_by_view.csv`
- `uncued_pilot_metrics_by_condition.csv`
- `uncued_pilot_metrics_by_family.csv`
- `uncued_pilot_metrics_by_model_view.csv`
- `uncued_pilot_metrics_by_model_condition.csv`
- `uncued_pilot_baselines_vs_models.csv`
- `uncued_pilot_active_verification_action_metrics.csv`
- `uncued_pilot_acceptance_diagnostics.json`
- `report_manifest.json`
- `summary.md`

## Model Results

| Model | N | Operational Escape | Parse Success | Belief Correctness | Evidence Precision | Clean Support Recall | Polluted Support Rate | Required Action Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 120 | 0.317 | 1.000 | 0.933 | 0.481 | 0.521 | 0.450 | 0.875 |
| `deepseek-v4-pro` | 120 | 0.233 | 1.000 | 0.658 | 0.441 | 0.521 | 0.517 | 0.688 |
| `gemini-3.1-pro-preview` | 120 | 0.433 | 1.000 | 0.917 | 0.843 | 0.938 | 0.125 | 0.812 |
| `gpt-5.5` | 120 | 0.525 | 1.000 | 0.992 | 0.754 | 1.000 | 0.167 | 0.792 |

## View Results

| View | N | Operational Escape | Parse Success | Belief Correctness | Evidence Precision | Polluted Support Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `neutral_metadata_hidden` | 240 | 0.362 | 1.000 | 0.887 | 0.647 | 0.308 |
| `neutral_metadata_visible` | 240 | 0.392 | 1.000 | 0.863 | 0.617 | 0.321 |

## Condition Results

| Condition | N | Operational Escape | Parse Success | Belief Correctness | Evidence Precision | Polluted Support Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `buried_primary` | 96 | 0.490 | 1.000 | 0.979 | 1.000 | 0.000 |
| `clean` | 96 | 0.719 | 1.000 | 0.927 | 0.994 | 0.000 |
| `conflicting_evidence` | 96 | 0.250 | 1.000 | 0.812 | 0.479 | 0.448 |
| `false_consensus` | 96 | 0.302 | 1.000 | 0.719 | 0.659 | 0.323 |
| `generated_lore` | 96 | 0.125 | 1.000 | 0.938 | 0.000 | 0.802 |

## Acceptance

Phase 13 acceptance passed:

- Clean operational escape reaches the threshold for at least one model: `gpt-5.5` has 0.958 on clean and `claude-opus-4-7` has 0.792 on clean.
- No model reaches 1.0 operational escape across all polluted conditions.
- Generated-lore separates belief correctness from evidence/action hygiene: belief correctness 0.938, operational escape 0.125, gap 0.8125.
- Buried-primary separates belief correctness from evidence/action hygiene: belief correctness 0.979, operational escape 0.490, gap 0.4896.
- Metadata-hidden and metadata-visible results are reported separately.
- The simple heuristic is below `gpt-5.5` and `gemini-3.1-pro-preview` on both operational escape and evidence precision in both views.

Caveat: the simple heuristic is not below every model-view pair. It exceeds or ties `claude-opus-4-7` and `deepseek-v4-pro` on the baseline comparison margins. This does not block the Phase 13 acceptance diagnostic as implemented, but it should be stated in any paper draft rather than simplified into "all frontier models beat the heuristic."

## Hashes

| Artifact | SHA-256 |
| --- | --- |
| `uncued_pilot_scored_predictions.csv` | `5d77f0f93eeb80cc42c2e1f9b91f949d9a9e193b07f20e6f14affd1710025a3b` |
| `uncued_pilot_metrics_by_model.csv` | `19186f4acbb85e1634817681ad7a8ee90072db2dc3e7e78b1bc3ab93a36b7433` |
| `uncued_pilot_metrics_by_view.csv` | `9de9fd1b6ab1eb71d82f21984e6162cd5bf06a725eb094d535014af6cb96b451` |
| `uncued_pilot_metrics_by_condition.csv` | `53fa5349b5d866461c77df1cd48aeb07cfe9344010c00245f2edc511da823e77` |
| `uncued_pilot_metrics_by_family.csv` | `81b2c7d5a3fd6e7c7de8be614e2fab4b6c07df2c066ff79f972747a732e52526` |
| `uncued_pilot_metrics_by_model_view.csv` | `ec75f9bfaed08c4db668b71ecd79f228ce210d7ec2550b2c9a7e21478bdc3e2b` |
| `uncued_pilot_metrics_by_model_condition.csv` | `a5f7da11a1a1320cc196ac27d83a9034264f3ca3886ea19dbd389c044ea85aa8` |
| `uncued_pilot_baselines_vs_models.csv` | `b2347b9fb9fdbe09464f52b2c133838acdebe78b2cf497c4c4e01feddbdcf397` |
| `uncued_pilot_active_verification_action_metrics.csv` | `176d40d715c32105e80e8f6d83c7ecdf963b480b1f546ceb485aecb968c49615` |
| `uncued_pilot_acceptance_diagnostics.json` | `acf90690d6cd40897db176b77c02a779c85ea4967e09e537a71f69db87c5bc88` |
| `report_manifest.json` | `62eeddd0eba886c9997e3894300cf0e5fac66fcc3f8af8eca52cf6fd659e2fc6` |
| `summary.md` | `d593fdf80f71b42ae70311a825d432b7b6f9146ebe76fb7956ec827587c8bde9` |

## Decision

Phase 13 passes. The pilot is scored and ready for Phase 14 manual scorer audit.
