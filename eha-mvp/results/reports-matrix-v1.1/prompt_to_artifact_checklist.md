# Matrix v1.1 Prompt-to-Artifact Checklist

Objective: deliver the Matrix v1.1 Robustness Pack from the local research request brief without changing the Matrix v1 main result.

## Success Criteria

- Produce the required v1.1 report bundle under `results/reports-matrix-v1.1/`.
- Run the requested API experiments with the specified models, strategies, difficulties, seeds, noise levels, and prompt variant.
- Reuse existing Matrix v1 predictions for escape decomposition; do not spend new API calls for that part.
- Keep Matrix v1 main artifacts unchanged and add v1.1 as a separate report pack.
- Verify implementation with tests, compile checks, and artifact-level row-count audits.

## Requirement Mapping

| Requirement | Artifact / command | Evidence |
| --- | --- | --- |
| Matrix v1.1 Robustness Pack as a separate follow-on, not a Matrix v1 replacement | `results/reports-matrix-v1.1/summary.md` | New report directory; existing `results/reports-matrix-v1/summary.md` left untouched. |
| Multi-seed critical replication: 3 new seeds | `data/matrix-v1.1/multiseed/seed-9201`, `seed-9202`, `seed-9203`; `results/reports-matrix-v1.1/scored_multiseed_predictions.csv` | Raw scored rows contain seeds `9201`, `9202`, `9203`; aggregate rows have `seed_count=3`. |
| Multi-seed scope: L3/L4/L5 only, 24 episodes per level per seed | API runs under `results/runs/matrix-v1.1/multiseed/seed-*`; `scored_multiseed_predictions.csv` | 1296 scored rows = 3 seeds x 2 models x 3 strategies x 3 difficulties x 24 episodes; raw difficulties are only `L3`, `L4`, `L5`. |
| Multi-seed models: `gpt-4o-mini`, `gpt-5.4-mini` | `scored_multiseed_predictions.csv`; `multiseed_replication.csv` | Models present: `openai/gpt-4o-mini`, `openai/gpt-5.4-mini`. |
| Multi-seed strategies: `naive_bm25`, `primary_preserve`, `hygienic_combo` | `scored_multiseed_predictions.csv`; `multiseed_replication.csv` | Strategies present: `naive_bm25`, `primary_preserve`, `hygienic_combo`. |
| Multi-seed metrics with bootstrap CIs | `results/reports-matrix-v1.1/multiseed_replication.csv` | 18 aggregate rows include `escape_rate`, `claim_accuracy`, `contaminated_citation_rate`, `generated_lore_overclaim_rate` and CI columns. |
| Noisy metadata/source spoofing stress on L3-L5 | `data/matrix-v1.1/noisy/noise-00`, `noise-10`, `noise-25`, `noise-50`; `scored_noisy_predictions.csv` | 576 scored rows = 4 noise levels x 1 model x 2 strategies x 3 difficulties x 24 episodes. |
| Noisy metadata levels: 0%, 10%, 25%, 50% | `results/reports-matrix-v1.1/noisy_metadata_stress.csv` | `metadata_noise` values are `0`, `10`, `25`, `50`. |
| Noisy stress model: `gpt-5-mini` | `scored_noisy_predictions.csv`; `noisy_metadata_stress.csv` | Model present: `openai/gpt-5-mini`. |
| Noisy stress strategies: `primary_preserve`, `hygienic_combo` | `scored_noisy_predictions.csv`; `noisy_metadata_stress.csv` | Strategies present: `primary_preserve`, `hygienic_combo`. |
| Noisy stress reports degradation curves | `results/reports-matrix-v1.1/noisy_metadata_stress.csv`; `summary.md` | 24 aggregate rows grouped by `metadata_noise`, model, strategy, difficulty with metric and CI columns. |
| Escape decomposition with no new API calls | `results/reports-matrix-v1.1/escape_decomposition.csv`; `escape_decomposition_rows.csv` | Recomputed from `results/runs/matrix-v1-main`; 1728 raw rows and 72 aggregate rows. |
| Escape components: `claim_correct`, `clean_supporting_evidence`, `has_required_supporting_evidence`, `generated_lore_abstention_ok`, `full_escape` | `escape_decomposition.csv`; `escape_decomposition_rows.csv` | All component columns are present in both raw and aggregate outputs. |
| `claim_first_citation_v1.1` prompt-only preflight | `eha/matrix_prompts.py`; `results/runs/matrix-v1.1/prompt-v1_1-preflight` | Added `claim_first_citation_v1_1`; run produced 48 v1.1 predictions. |
| v1.1 prompt rule: supported/refuted must include at least one clean `doc_id`; no clean support means `insufficient` | `eha/matrix_prompts.py`; `tests/test_matrix_v11.py` | Prompt builder test asserts the strict support instructions appear in v1.1 and not v1. |
| Preflight scope: L0/L3/L4/L5, 12 episodes each | `data/matrix-v1.1/prompt-v1_1-preflight`; `prompt_v1_1_preflight_rows.csv` | Raw rows include difficulties `L0`, `L3`, `L4`, `L5`; summary has 12 rows per prompt/difficulty. |
| Preflight model and strategy: `gpt-4o-mini`, `careful_bm25` only | `prompt_v1_1_preflight_rows.csv`; `prompt_v1_1_preflight.csv` | Model present: `openai/gpt-4o-mini`; strategy present: `careful_bm25`. |
| Required report: `summary.md` | `results/reports-matrix-v1.1/summary.md` | Exists and includes sections for all four analyses plus cost report. |
| Required report: `multiseed_replication.csv` | `results/reports-matrix-v1.1/multiseed_replication.csv` | Exists; 18 aggregate rows. |
| Required report: `noisy_metadata_stress.csv` | `results/reports-matrix-v1.1/noisy_metadata_stress.csv` | Exists; 24 aggregate rows. |
| Required report: `escape_decomposition.csv` | `results/reports-matrix-v1.1/escape_decomposition.csv` | Exists; 72 aggregate rows. |
| Required report: `prompt_v1_1_preflight.csv` | `results/reports-matrix-v1.1/prompt_v1_1_preflight.csv` | Exists; 8 aggregate rows comparing `claim_first_citation_v1` and `claim_first_citation_v1_1`. |
| Required report: `cost_report.json` | `results/reports-matrix-v1.1/cost_report.json` | Exists; `aborted=false`, 8 source reports, total `spent_usd=2.810599`. |
| Use OpenAI-compatible LLM client and configured endpoint | API commands used existing `eha-matrix-v1` OpenAI backend | Successful API runs used configured `LLM_API_KEY` / `LLM_BASE_URL` environment and wrote cost reports. |
| Python dependencies managed by `uv` | All commands below | API runs, report generation, tests, and compile checks were run through `uv run`. |

## Verification

- `uv run pytest` passed: 36 tests.
- `uv run python -m compileall eha` passed.
- Artifact audit passed: all required report files exist; expected raw and aggregate row counts match; no v1.1 run cost report was aborted.
