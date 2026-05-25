# EHA-Uncued Robustness Start State

Date: 2026-05-25

Runbook: `reports/eha-uncued-phase1-3-robustness-mini-suite-runbook-2026-05-25.md`

## Repository State

Current branch:

```text
codex/add-reality-testing-benchmarks...origin/codex/add-reality-testing-benchmarks [ahead 4]
```

Recent commits:

```text
92dbf128 docs: add full-paper strengthening runbook
6e4aadf3 phase 1.2: record codex schema audit
a705ab1b phase 1.2: add codex schema audit runbook
825d2dc0 phase 1.1: update handoff and paper artifact status
1beaa997 phase 1.1-6-8: score and verify schema ablation
```

Dirty files observed before Phase 1.3 robustness work:

```text
 M eha-mvp/pyproject.toml
 M paper/main.pdf
 M paper/main.tex
 M paper/sections/00_abstract.tex
 M paper/sections/02_polluted_evidence_environments.tex
 M paper/sections/03_uncued_dataset_design.tex
 M paper/sections/04_leakage_controls.tex
 M paper/sections/05_metrics_scoring.tex
 M paper/sections/06_experimental_setup.tex
 M paper/sections/07_results.tex
 M paper/sections/09_human_scorer_audit.tex
 M paper/sections/10_limitations.tex
 M paper/sections/11_ethics_scope.tex
 M paper/sections/12_artifact.tex
 M paper/tables/active_verification_action_exactness.tex
 M paper/tables/leakage_gate_summary.tex
 M paper/tables/scorer_audit_summary.tex
?? eha-mvp/eha/uncued_examples.py
?? eha-mvp/eha/uncued_statistics.py
?? eha-mvp/results/reports-eha-uncued-statistics-2026-05-25/
?? eha-mvp/tests/test_uncued_examples.py
?? eha-mvp/tests/test_uncued_statistics.py
?? paper/appendices/
?? paper/tables/condition_metrics_with_ci.tex
?? paper/tables/model_metrics_with_ci.tex
?? reports/eha-uncued-bootstrap-uncertainty-2026-05-25.md
?? reports/eha-uncued-full-paper-strengthening-handoff-2026-05-25.md
?? reports/eha-uncued-full-paper-strengthening-start-2026-05-25.md
?? reports/eha-uncued-independent-human-audit-packet-2026-05-25.md
?? reports/eha-uncued-independent-human-audit-runbook-2026-05-25.md
?? reports/eha-uncued-leakage-shortcut-methods-2026-05-25.md
?? reports/eha-uncued-operational-escape-spec-2026-05-25.md
?? reports/eha-uncued-phase1-3-robustness-mini-suite-runbook-2026-05-25.md
?? reports/eha-uncued-task-examples-2026-05-25.md
?? reports/eha-uncued-template-diversity-audit-2026-05-25.md
?? reports/eha_uncued_bootstrap_uncertainty.json
```

## Phase 1 Readiness

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports
```

Result:

```text
Uncued Phase 1 readiness decision=pass.
```

## Regression Tests

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run pytest tests/test_uncued_run.py tests/test_uncued_report.py -q
```

Result:

```text
4 passed in 0.23s
```

## Start-State Decision

Phase 1 readiness passed, and the existing uncued run/report tests passed before new robustness implementation work. The pre-existing dirty worktree is documented above; Phase 1.3 robustness work should avoid mutating old cued artifacts and should not write into `artifact_uncued_phase1`.
