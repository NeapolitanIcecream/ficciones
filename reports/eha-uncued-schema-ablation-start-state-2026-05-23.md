# EHA-Uncued Phase 1.1 Schema Ablation Start State

Date: 2026-05-23

## Repository State

- Branch: `codex/add-reality-testing-benchmarks`
- Upstream: `origin/codex/add-reality-testing-benchmarks`
- Dirty files before Phase 0 commit:
  - Modified: `reports/eha-uncued-schema-ablation-plan-2026-05-22.md`
  - Untracked: `reports/eha-uncued-phase1-1-schema-ablation-runbook-2026-05-23.md`

The modified Phase 15 plan only adds the Phase 1.1 runbook path. It is kept as part of the handoff from planned work to this ablation run.

## Data Dependency Boundary

This Phase 1.1 ablation is allowed to use only role-uncued Phase 1 data from:

- `eha-mvp/data/uncued-pilot-v1`
- `artifact_uncued_phase1` only if needed for packaging or verification

The ablation must not use old cued data, old cued model outputs, `artifact/data/documents_opaque.jsonl`, or `data/epistemic-resilience-v1` as scientific evidence.

## Baseline Data Evidence

- Runbook hash: `4c8a16c45dde50a74173e7f20117f40284c94c7f5948f8b079315f36daa3dca5`
- Pilot manifest hash: `67f772df81433360276b662377a9121927ec5194f244406adb911d51d5f466e1`
- Pilot leakage report hash: `1426c028e3f016c77723cd949846c8c9bc6c54da9eeaa48e881db69eb0c71ed2`
- Pilot baseline report hash: `e7577c4bae0ddd3ae685b51de42e6321c0026bccf49df250aaa8da25e50c4490`
- Pilot surface-review validation hash: `54daf906fe0845aa857919daf8497cf6e2d4b985479633012394e3a8b868c34d`

Pilot dataset summary:

- Task count: 60
- Views: `neutral_metadata_visible`, `neutral_metadata_hidden`
- Conditions: 12 each for clean, conflicting evidence, false consensus, buried primary, and generated lore
- Families: 24 packet judgment, 24 evidence selection, 12 active verification

Gate state inherited from Phase 1:

- Pilot leakage gate: passed, 0 critical hits, 0 high hits, 0 hidden-label hits, 0 semantic-ID hits, 0 direct-answer-cue hits
- Pilot shortcut baselines: passed
- Pilot surface review: passed, 400 reviewed rows, 0 critical leaks, 0 direct-answer-cue rows
- Surface-review caveat: `independent_human_review=false`

## Phase 0 Verification

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run pytest tests/test_uncued_run.py tests/test_uncued_report.py tests/test_uncued_scorer_audit.py -q
```

Result:

```text
6 passed in 0.44s
```

## Phase 0 Decision

Pass. The repository has a recorded dirty baseline, Phase 1 role-uncued dependencies are present and passing, and old cued artifacts are excluded from the Phase 1.1 evidence boundary.
