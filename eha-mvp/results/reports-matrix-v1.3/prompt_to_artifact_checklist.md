# 0513-6 Prompt-to-Artifact Checklist

Objective: continue from `/Users/chenmohan/Downloads/ficciones-research-0513-6.md` by entering manuscript work, while doing only the small confirmation experiment it recommends: a full L0-L5 `claim_first_citation_v1_1` + hygiene sweep and stable L4 primary-recovery reporting.

## Success Criteria

- Do not open a new large benchmark, new difficulty taxonomy, new risk-label system, new diagnostics schema, new tool-agent loop, or new model matrix.
- Run the small full L0-L5 confirmation for `claim_first_citation_v1_1` with `primary_preserve` and `hygienic_combo`.
- Verify that the stricter prompt improves evidence discipline without adding abstention/evidence-selection cost.
- Keep L4 primary-recovery metrics in the paper-facing main tables.
- Produce a manuscript draft artifact centered on the evidence-environment thesis.
- Verify all outputs with tests, compile checks, and artifact-level audits.

## Requirement Mapping

| Requirement | Artifact / command | Evidence |
| --- | --- | --- |
| Enter writing stage rather than expanding experiments | `results/reports-matrix-v1.3/manuscript_draft.md` | Draft includes abstract, reader problem, thesis, contributions, central figure, section plan, limitations, and AI-use disclosure. |
| Avoid a new large benchmark | `results/runs/matrix-v1.3/prompt-v1_1-hygiene-full` | Only one small confirmation run: 288 predictions = 144 existing Matrix v1 tasks x 2 hygiene strategies; no new model family, difficulty layer, schema, or risk taxonomy. |
| Full L0-L5 prompt v1.1 + hygiene sweep | API command used `--data-dir data/matrix-v1`, `--strategies primary_preserve,hygienic_combo`, `--claim-first-prompt claim_first_citation_v1_1` | `prompt_hygiene_preflight.csv` includes difficulties `L0`, `L1`, `L2`, `L3`, `L4`, `L5`. |
| Use `gpt-4o-mini` only for the confirmation sweep | `results/runs/matrix-v1.3/prompt-v1_1-hygiene-full/predictions.jsonl` | 288 predictions all scored as `openai/gpt-4o-mini` in `prompt_hygiene_preflight_rows.csv`. |
| Compare prompt v1.1 against baseline prompt v1 | `results/reports-matrix-v1.3/prompt_hygiene_preflight.csv` | Aggregate rows include `claim_first_citation_v1` and `claim_first_citation_v1_1`; 576 raw rows = 288 baseline + 288 v1.1. |
| Confirm evidence discipline | `prompt_hygiene_preflight.csv` | Table includes `has_required_supporting_evidence`, `clean_supporting_evidence`, `contaminated_citation_rate`, and `generated_lore_overclaim_rate`. |
| Confirm no new abstention cost | `prompt_hygiene_preflight.csv`; `manuscript_draft.md` | Aggregate includes `over_abstention_rate`; v1.1 has `over_abstention_rate=0.000` for both hygiene strategies on L0-L2. |
| Confirm no obvious evidence-selection cost | `prompt_hygiene_preflight.csv` | Aggregate includes `primary_in_context`, `primary_cited`, and `primary_ignored`; L4 v1.1 hygiene rows keep `primary_in_context=1.000`. |
| Keep L4 primary recovery metrics in main paper-facing tables | `l4_primary_recovery_audit.csv`; `summary.md` | L4 table includes `primary_in_context`, `primary_cited`, `primary_ignored`, and `mean_best_primary_context_rank`. |
| Preserve seed-cluster CI evidence | `multiseed_cluster_ci.csv` | 18 rows, `cluster_count=3`, with cluster CI columns for the v1.1 multi-seed result. |
| Machine-readable diagnostics | `audit_manifest.json`; `cost_report.json` | Manifest captures inputs and row counts; cost report has `aborted=false`, `spent_usd=0.084495`. |
| Use modern Python workflow with `uv` | Commands run through `uv run` | API run, report generation, tests, and compileall used `uv run`. |
| Tests cover report behavior | `tests/test_matrix_paper_pack.py` | Tests cover cluster resampling, mechanism scoring, baseline/v1.1 prompt comparison including `over_abstention_rate`, and L4 audit aggregation. |
| No invented external citations in manuscript draft | `manuscript_draft.md` | Related-work section uses `[citation needed]` placeholders instead of fabricated references. |

## Verification

- `uv run pytest` passed: 40 tests.
- `uv run python -m compileall eha` passed.
- Final artifact audit passed: all expected v1.3 report files exist; prompt full sweep row counts match; L4 mechanism columns are present; cost report is not aborted.
