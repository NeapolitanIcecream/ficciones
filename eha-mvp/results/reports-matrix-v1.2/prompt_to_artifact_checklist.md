# 0513-5 Prompt-to-Artifact Checklist

Objective: continue from the 0513-5 research handoff by doing only the small paper-consolidation work it recommends: seed-cluster confidence intervals, a prompt v1.1 + hygiene preflight, an L4 primary-recovery mechanism audit, and manuscript-positioning notes.

## Success Criteria

- Do not launch another large benchmark or expand the taxonomy/diagnostic infrastructure.
- Add cluster-level uncertainty for the v1.1 multi-seed result.
- Run a small prompt v1.1 + hygiene preflight with `primary_preserve` and `hygienic_combo`.
- Audit L4 primary-recovery mechanics without new API calls.
- Produce paper-facing notes that narrow the claim and identify what not to overclaim.
- Verify with tests, compile checks, and artifact-level row-count audits.

## Requirement Mapping

| Requirement | Artifact / command | Evidence |
| --- | --- | --- |
| Avoid another large experiment | `results/runs/matrix-v1.2/prompt-v1_1-hygiene-preflight` | Only 96 new API predictions were run; no new models or difficulty taxonomy. |
| Add cluster bootstrap / seed-cluster CIs | `results/reports-matrix-v1.2/multiseed_cluster_ci.csv` | 18 rows grouped by model/strategy/difficulty; each row has `cluster_count=3` and `*_cluster_ci_low/high` columns. |
| Cluster CI uses v1.1 multi-seed data | `data/matrix-v1.1/multiseed`, `results/runs/matrix-v1.1/multiseed` | Report input manifest records seeds `9201`, `9202`, `9203`; no new API call used for cluster CIs. |
| Prompt v1.1 + hygiene small preflight | `results/runs/matrix-v1.2/prompt-v1_1-hygiene-preflight/predictions.jsonl` | 96 predictions = 48 tasks x 2 strategies; cost report `spent_usd=0.027908`, `aborted=false`. |
| Preflight uses `claim_first_citation_v1_1` | API command used `--claim-first-prompt claim_first_citation_v1_1` | Raw rows in `prompt_hygiene_preflight_rows.csv` include prompt version `claim_first_citation_v1_1`. |
| Preflight strategies: `primary_preserve`, `hygienic_combo` | `prompt_hygiene_preflight.csv` | Strategies present: `primary_preserve`, `hygienic_combo`. |
| Preflight checks required-support discipline | `prompt_hygiene_preflight.csv` | Aggregate includes `has_required_supporting_evidence` and `clean_supporting_evidence`. |
| Preflight checks L4 primary recovery is not hurt | `prompt_hygiene_preflight.csv` | L4 rows include `primary_in_context` and `primary_cited`; v1.1 hygiene rows keep primary evidence in context. |
| L4 primary recovery mechanism audit | `results/reports-matrix-v1.2/l4_primary_recovery_audit.csv` | 12 aggregate rows over Matrix v1 main model/strategy/prompt/retriever groups. |
| L4 audit records whether primary source enters context | `l4_primary_recovery_audit.csv`, `l4_primary_recovery_audit_rows.csv` | Columns include `primary_in_context` and `best_primary_context_rank`. |
| L4 audit records whether model cites, rejects, or ignores primary source | `l4_primary_recovery_audit.csv`, `l4_primary_recovery_audit_rows.csv` | Columns include `primary_cited`, `primary_rejected`, `primary_ignored`. |
| L4 audit avoids new API calls | `results/runs/matrix-v1-main` reused by `eha-matrix-paper-pack` | 288 raw L4 rows are recomputed from existing Matrix v1 predictions. |
| Produce paper-facing consolidation notes | `results/reports-matrix-v1.2/paper_consolidation_notes.md` | Notes state the main claim, centered results, manuscript structure, and claims to avoid. |
| Machine-readable diagnostic artifact | `results/reports-matrix-v1.2/audit_manifest.json` | Captures inputs, output row counts, and cost report for the v1.2 pack. |
| Required report summary | `results/reports-matrix-v1.2/summary.md` | Includes sections for seed-cluster CIs, prompt+hygiene preflight, L4 audit, and new API cost. |
| CLI entry point | `pyproject.toml`; `eha/matrix_paper_pack.py` | Added `eha-matrix-paper-pack = "eha.matrix_paper_pack:app"`. |
| Tests as executable specs | `tests/test_matrix_paper_pack.py` | Tests cover seed-cluster resampling, mechanism scoring, prompt baseline/v1.1 comparison, and L4 audit aggregation. |
| Use `uv` for Python/package execution | Commands run with `uv run` | API preflight, report generation, pytest, and compileall were executed through `uv`. |

## Verification

- `uv run pytest` passed: 40 tests.
- `uv run python -m compileall eha` passed.
- Artifact audit passed: all expected report files exist; expected row counts match; cost report is not aborted.
