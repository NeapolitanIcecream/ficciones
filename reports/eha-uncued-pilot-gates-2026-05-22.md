# EHA-Uncued Pilot Pre-Model Gates

Date: 2026-05-22

Decision: `go`

This report records Phase 9-10 evidence for the 60-task EHA-Uncued pilot. No frontier/API model calls were made.

## Pilot Generation

- Dataset directory: `eha-mvp/data/uncued-pilot-v1`.
- Task count: 60.
- Views: `neutral_metadata_visible`, `neutral_metadata_hidden`.
- Condition counts: 12 clean, 12 conflicting evidence, 12 false consensus, 12 buried primary, 12 generated lore.
- Family counts: 24 packet judgment, 24 evidence selection, 12 active verification.
- Action gold rows: 12, one for each active-verification task.
- Documents per view: 240.

## Gate Summary

| Gate | Result |
| --- | --- |
| Leakage audit | passed |
| Critical leakage hits | 0 |
| High leakage hits | 0 |
| Direct-answer cue hits | 0 |
| Shortcut baseline gates | passed, 12 baselines and 30 checks |
| Human-review worksheet | 400 reviewed rows, 50 tasks |
| Human severe leakage | 0 rows, rate 0.0 |
| Human direct-answer cues | 0 rows |

## Human Review Sample

The `50-tasks-200-docs` sample includes 50 tasks and 400 document rows because both required views are reviewed. It includes all 12 active-verification tasks.

Reviewed condition counts:

- clean: 10
- conflicting evidence: 10
- false consensus: 10
- buried primary: 10
- generated lore: 10

Reviewed family counts:

- packet judgment: 19
- evidence selection: 19
- active verification: 12

View rows:

- `neutral_metadata_visible`: 200
- `neutral_metadata_hidden`: 200

## Hashes

- `pilot_generation_manifest`: `67f772df81433360276b662377a9121927ec5194f244406adb911d51d5f466e1`
- `pilot_leakage_report`: `1426c028e3f016c77723cd949846c8c9bc6c54da9eeaa48e881db69eb0c71ed2`
- `pilot_baseline_report`: `e7577c4bae0ddd3ae685b51de42e6321c0026bccf49df250aaa8da25e50c4490`
- `pilot_human_review_validation`: `54daf906fe0845aa857919daf8497cf6e2d4b985479633012394e3a8b868c34d`

## Caveat

The review worksheet records `local_pre_model_surface_review`; it is a pre-model leakage gate artifact, not a paper-level independent human-validation claim.

