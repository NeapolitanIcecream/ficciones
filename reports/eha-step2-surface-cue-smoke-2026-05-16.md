# EHA Step 2 Surface-Cue Smoke Dataset

Date: 2026-05-16

## Purpose

This is a no-API preparation step for the Step 2 roadmap. It does not expand the benchmark claim and should not be reported as model evidence. Its role is to make the planned surface-cue stress tests executable before spending on model runs.

The smoke dataset tests whether paired rows can vary visible surface cues while preserving the same underlying gold verdict and evidence graph. It now uses three claim templates per task family so the smoke grid is no longer a single-template demonstration.

## Artifact

- Generator: `eha-mvp/eha/surface_cue_generate.py`
- CLI: `uv run eha-generate-surface-cue --seed 9417 --out-dir data/phase2-surface-cue-smoke`
- Output directory: `eha-mvp/data/phase2-surface-cue-smoke`
- Manifest: `eha-mvp/data/phase2-surface-cue-smoke/manifest.json`
- Tests: `eha-mvp/tests/test_surface_cue_generate.py`

Generated output:

| File | Rows |
|---|---:|
| `tasks.jsonl` | 180 |
| `documents.jsonl` | 900 |
| `gold_documents.jsonl` | 900 |
| `gold_graph.jsonl` | 360 |
| `action_gold.jsonl` | 30 |

## Pair Grid

Each `(family, claim template, axis)` cell has two paired tasks. Pair members share the same target claim, gold verdict, answer brief, and support/refutation structure, while changing one intended visible cue family.

| Axis | Conditions | Rows |
|---|---|---:|
| `source_type_visibility` | visible source types vs hidden generic documents | 36 |
| `metadata_perturbation` | truthful metadata vs shuffled title/timestamp/authority cues | 36 |
| `style_normalization` | promotional false-support style vs neutralized style | 36 |
| `adversarial_spoofing` | plain false-support document vs audit/regulator-style spoof | 36 |
| `content_only` | full metadata vs metadata-stripped content-only documents | 36 |

The smoke grid now covers six task families:

| Family | Rows | Verdict / scope |
|---|---:|---|
| `conflict` | 30 | `refuted` / `conflicting` |
| `stale` | 30 | `refuted` / `stale` |
| `partial` | 30 | `insufficient` / `partial` |
| `generated_lore` | 30 | `insufficient` / `generated_lore` |
| `no_primary` | 30 | `insufficient` / `no_primary_source` |
| `active_verification` | 30 | `refuted` / `conflicting` |

Across the full 180 rows, 90 are `refuted` and 90 are `insufficient`.

## Smoke Checks

The tests verify:

- deterministic 6-family x 3-template x 5-axis x 2-condition paired task grid;
- same verdict and answer brief within each pair;
- intended cue mutation for each axis;
- `bm25_top8` observability for clean support when the family has clean support, and contaminated false-support observability for every row;
- exact active-verification action gold for 30 rows, with `compare_versions` and `trace_citation` target document IDs;
- no hidden-label terms such as `supports_gold`, `supports_false_claim`, `contamination`, `known_contaminants`, `pollutant`, `primary_a`, or `primary_b` in model-visible task/document payloads.
- Phase 2S-shaped no-API baseline scoring for oracle, always-insufficient, and source-type-prior strategies.
- pair-level human design-review handoff with 90 worksheet rows and required labels before API use.

## Status

Verification:

- `uv run pytest tests/test_surface_cue_generate.py -q`: 5 passed.
- `uv run pytest tests/test_surface_cue_generate.py tests/test_surface_cue_report.py tests/test_surface_cue_score.py tests/test_surface_cue_design_review.py tests/test_step2_statistics.py -q`: 19 passed.
- `uv run pytest -q`: 194 passed.
- `artifact/verify_step1_release.sh --allow-blocked`: completed with readiness status `blocked`; the remaining blocker is still the independent human audit, not this smoke dataset.

The smoke generator is ready for human design review. The no-API balance report in `reports/eha-step2-surface-cue-balance-2026-05-16.md` records 0 pair-contract violations, 0 visible-leakage hits, 0 action-target violations, 120/120 clean-support observable rows, and 180/180 contaminated-observable rows. The scoring report in `reports/eha-step2-surface-cue-scoring-pipeline-2026-05-16.md` records 540 no-API baseline rows and a source-type-prior failure mode under metadata perturbation and adversarial spoofing. The design-review packet in `reports/eha-step2-surface-cue-design-review-packet-2026-05-16.md`, worksheet `reports/surface_cue_design_review_worksheet.csv`, browser page `reports/surface_cue_design_review.html`, and launcher `reports/serve_surface_cue_design_review.sh` are incomplete with 0/90 reviewed pairs. It is still not Step 2 model evidence:

- it has not been run against any model;
- the templates are synthetic smoke cases, not a human-audited benchmark expansion;
- it should not unlock a 500-1000 task expansion by itself.

The next Step 2 dataset action is filling the 90-pair human design-review worksheet and rerunning `eha-validate-surface-cue-design-review`; the current validation report is `reports/eha-step2-surface-cue-design-review-validation-2026-05-16.md` with `pilot_ready=false`.
