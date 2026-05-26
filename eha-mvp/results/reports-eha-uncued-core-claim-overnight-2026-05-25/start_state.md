# EHA-Uncued Core-Claim Overnight Start State

Date: 2026-05-25

## Repository State

- Repository: `/Users/chenmohan/gits/ficciones`
- Branch: `codex/add-reality-testing-benchmarks`
- HEAD: `4dd786a04d2bee814f8ec199e6b73f56bf6721ae`
- Dirty files before new implementation: `reports/eha-uncued-core-claim-overnight-runbook-2026-05-25.md` was untracked.

Recent commits:

```text
4dd786a0 docs: add GPT-5.5 blind review materials
37170621 phase 1.3: strengthen uncued paper evidence package
92dbf128 docs: add full-paper strengthening runbook
6e4aadf3 phase 1.2: record codex schema audit
a705ab1b phase 1.2: add codex schema audit runbook
825d2dc0 phase 1.1: update handoff and paper artifact status
1beaa997 phase 1.1-6-8: score and verify schema ablation
902b0279 phase 1.1-5: record schema run and deepseek retry
```

## Phase 0 Gate Results

Commands run from `/Users/chenmohan/gits/ficciones/eha-mvp`:

```bash
uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports
uv run eha-verify-uncued-robustness --run-dir results/reports-eha-uncued-robustness-2026-05-25 --reports-dir ../reports
uv run pytest tests/test_uncued_run.py tests/test_uncued_report.py tests/test_uncued_statistics.py tests/test_uncued_examples.py tests/test_uncued_robustness.py -q
```

Results:

- Phase 1 verification: `Uncued Phase 1 readiness decision=pass.`
- Robustness verification: `Robustness verification decision=pass.`
- Focused existing pytest gate: `15 passed in 1.12s`

## Guardrails

- New outputs will be written under `eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/`.
- Existing Phase 1, Phase 1.1, Phase 1.2, and Phase 1.3 result directories will not be mutated.
- Only role-uncued artifacts are in scope.
