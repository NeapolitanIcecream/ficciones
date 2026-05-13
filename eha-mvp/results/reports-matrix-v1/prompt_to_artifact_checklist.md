# Matrix v1 Prompt-To-Artifact Checklist

- Source memos: two local research memos from 2026-05-13 were used as context; the later memo was treated as authoritative. Local absolute paths are intentionally omitted.
- Dataset: `data/matrix-v1` contains 144 tasks, 24 each for L0-L5; `data/matrix-v1-preflight` contains 36 tasks, 6 each for L0-L5.
- Prompt schema: `eha/matrix_prompts.py` and `eha/schemas.py` implement the thin claim-first fields: `claim_verdict`, `confidence`, `supporting_evidence`, `rejected_evidence`, `answer`, `evidence_notes`.
- Prompt policy: `claim_first_citation_v1` encodes claim-first, primary-source preference, repost non-independence, rejected suspicious docs, and insufficient-on-no-primary rules.
- Main strategies: `results/runs/matrix-v1-main/predictions.jsonl` contains S0 `naive_bm25`, S1 `careful_bm25`, S2 `primary_preserve`, and S3 `hygienic_combo`.
- Main models: `results/runs/matrix-v1-main/predictions.jsonl` contains 576 predictions each for `openai/gpt-4o-mini`, `openai/gpt-5-mini`, and `openai/gpt-5.4-mini`.
- Preflight: `results/runs/matrix-v1-preflight-gpt4omini/preflight_gate.json` passed all five gates for `openai/gpt-4o-mini`.
- Sanity check: `results/runs/matrix-v1-gpt55-sanity/predictions.jsonl` contains 216 predictions for `openai/gpt-5.5` on L3-L5 only, using S0/S2/S3.
- Reports: `results/reports-matrix-v1` contains `summary.md`, the four required matrix CSVs, `model_vs_hygiene_comparisons.csv`, `difficulty_curves.csv`, `failure_cases_matrix_v1.md`, and `cost_report.json`.
- Failure cases: `results/reports-matrix-v1/failure_cases_matrix_v1.md` contains 12 scored cases.
- Cost guard: API runs used soft/hard/abort caps of `$75/$200/$300`; final API spend was `$6.98346` across preflight, main, and sanity runs.
- Tests: `uv run pytest` passed 32 tests; `uv run python -m compileall eha` passed.
