# EHA-Uncued Full-Paper Strengthening Handoff

Date: 2026-05-25

## Completed

- Recorded the clean start state and baseline verifier outcomes in `reports/eha-uncued-full-paper-strengthening-start-2026-05-25.md`.
- Added a formal operational-escape specification in `reports/eha-uncued-operational-escape-spec-2026-05-25.md` and `paper/appendices/operational_escape_spec.tex`.
- Added latent-task bootstrap uncertainty tooling and outputs:
  - `eha-mvp/eha/uncued_statistics.py`;
  - `eha-mvp/tests/test_uncued_statistics.py`;
  - `reports/eha_uncued_bootstrap_uncertainty.json`;
  - `reports/eha-uncued-bootstrap-uncertainty-2026-05-25.md`;
  - `paper/tables/model_metrics_with_ci.tex`;
  - `paper/tables/condition_metrics_with_ci.tex`;
  - `eha-mvp/results/reports-eha-uncued-statistics-2026-05-25/`.
- Added task/scoring example extraction and outputs:
  - `eha-mvp/eha/uncued_examples.py`;
  - `eha-mvp/tests/test_uncued_examples.py`;
  - `reports/eha-uncued-task-examples-2026-05-25.md`;
  - `paper/appendices/task_examples.tex`.
- Expanded leakage and shortcut method documentation in `reports/eha-uncued-leakage-shortcut-methods-2026-05-25.md` and `paper/appendices/leakage_shortcut_methods.tex`.
- Fixed the active-verification table so the final operational column is computed on active-verification rows only, not unlabeled all-family model rows.
- Added compact model invocation details in `paper/appendices/invocation_details.tex`.
- Added a template-diversity audit in `reports/eha-uncued-template-diversity-audit-2026-05-25.md` and `paper/appendices/template_diversity.tex`.
- Added an independent human audit design and packet draft without claiming the audit has been run.
- Rewrote paper body language to reduce internal phase/run-log wording and keep model comparisons descriptive.

## New Analyses

- Bootstrap uncertainty: 10,000 iterations, seed `20260525`, resampling 60 latent tasks while keeping hidden/visible views paired.
- Generated-lore belief-to-operational gap: `0.812 [0.714, 0.906]`.
- Overall visible-minus-hidden paired operational delta: `0.029 [-0.021, 0.079]`.
- Template audit: body length 45-67 words, median 55; visible source types balanced at 60 each; strongest repeated relation-control sentence appears in all 240 documents per view.

## Verification

| command | outcome |
| --- | --- |
| `uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports` | pass |
| `uv run eha-verify-uncued-schema-ablation --run-dir results/reports-eha-uncued-schema-ablation-2026-05-23 --reports-dir ../reports` | pass |
| `uv run pytest tests/test_uncued_statistics.py tests/test_uncued_examples.py tests/test_uncued_schema_ablation.py tests/test_uncued_schema_codex_audit.py -q` | `20 passed in 0.97s` |
| `make pdf` from `paper/` | PDF built successfully; only TeX line-break warnings remain |
| `git diff --check` | pass |
| `pdftotext paper/main.pdf - \| rg -n "independent human validation\|deployment certification\|universal leaderboard"` | no matches |

## Remaining Limitations

- No new robustness model calls were run for evidence-order randomization, metadata/source-type masking, prompt paraphrase, or citation masking. These remain P1 follow-up work.
- The independent human audit is designed but not executed. The paper still describes only local leakage review and local scorer-contract audit.
- The pilot remains synthetic and small. Bootstrap intervals address small-n uncertainty over latent tasks but do not turn the pilot into a powered model-ranking benchmark.
- Template regularity remains a limitation even though shortcut baselines do not show a single trivial cue that solves the task.

