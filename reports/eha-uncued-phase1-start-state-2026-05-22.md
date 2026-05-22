# EHA-Uncued Phase 1 Start State

Date: 2026-05-22

Working tree baseline before uncued implementation:

- Branch: `codex/add-reality-testing-benchmarks`.
- Initial dirty state observed for this run: `reports/eha-uncued-phase1-arxiv-runbook-2026-05-22.md` was untracked.
- No EHA-Uncued modules, commands, datasets, or reports existed before this run.

Verification status after implementing the Phase 0-8 micro-gate path:

- `uv run pytest -q`: `208 passed in 6.58s`.
- `git diff --check`: passed.
- Expected uncued CLI help commands are available for contract, generation, leakage audit, baselines, human-review worksheet/validation, pilot run/report placeholders, packaging, and verification.

Quarantine boundary:

- `artifact/` and `artifact/data/documents_opaque.jsonl` are quarantined as cued/internal evidence.
- `artifact/manifest.json` now records `scientific_status = "quarantined_cued_internal"`.
- `artifact/CUED_INTERNAL_ONLY.md` states that old cued results may be used only for methodological caution, regression tests, or historical comparison, not as main EHA-Uncued Phase 1 evidence.

Known blockers:

- No frontier/API model calls have been made in this Phase 0-8 pass.
- The micro surface review is recorded as `local_pre_model_surface_review`; it is a leakage gate artifact, not an independent human-validation claim for paper results.

