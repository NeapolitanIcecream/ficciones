# EHA-Uncued Full-Paper Strengthening Start State

Date: 2026-05-25

## Repository State

Working tree before strengthening edits: clean.

Recent commits:

| commit | subject |
| --- | --- |
| `92dbf128` | docs: add full-paper strengthening runbook |
| `6e4aadf3` | phase 1.2: record codex schema audit |
| `a705ab1b` | phase 1.2: add codex schema audit runbook |
| `825d2dc0` | phase 1.1: update handoff and paper artifact status |
| `1beaa997` | phase 1.1-6-8: score and verify schema ablation |

## Baseline Verification

Commands run from the repository root unless noted:

| command | outcome |
| --- | --- |
| `git status --short` | no output |
| `git log --oneline -5` | recorded above |
| `uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports` from `eha-mvp/` | `Uncued Phase 1 readiness decision=pass.` |
| `uv run eha-verify-uncued-schema-ablation --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --reports-dir ../reports` from `eha-mvp/` | `Schema-ablation verification decision=pass.` |
| `uv run pytest tests/test_uncued_schema_ablation.py tests/test_uncued_schema_codex_audit.py -q` from `eha-mvp/` | `15 passed in 0.83s` |

## Claim Boundary

The strengthened paper must keep the current claim at pilot scale:

- The main evidence is the role-uncued Phase 1 pilot: 60 latent tasks, two neutral metadata views, four model labels, one clarified schema, and one prompt condition.
- The older cued results remain quarantined and are not evidence for the main results.
- Phase 1.1 schema ablation and Phase 1.2 Codex schema audit remain follow-up evidence about interface sensitivity and local scorer QA, not new benchmark-scale model ranking.
- The local leakage review and Codex-assisted scorer audit are QA gates, not independent human validation.
- Model comparisons are descriptive unless uncertainty analysis supports a stronger statement.

