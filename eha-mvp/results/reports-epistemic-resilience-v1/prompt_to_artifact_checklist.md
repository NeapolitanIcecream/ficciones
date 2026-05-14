# Prompt To Artifact Checklist

Source memo: local research memo `ficciones-research-0513-7.md`

Objective: implement and run an Epistemic Resilience Table v1 that reframes EHA away from a narrow RAG-primary-retrieval result and toward LLM epistemic resilience under polluted evidence environments.

| Requirement | Artifact / Evidence | Status |
| --- | --- | --- |
| Do not center the paper on the obvious RAG claim that primary evidence helps. | `results/reports-epistemic-resilience-v1/epistemic_resilience_reframe.md` reframes RAG as "Retrieval as Evidence Environment Construction." | Done |
| Define the center claim as LLM epistemic resilience / evidential capture. | `epistemic_resilience_reframe.md`, `eha/epistemic_resilience.py`, report title `Epistemic Resilience Table v1`. | Done |
| Define epistemic escape as belief correctness + evidence cleanliness + uncertainty discipline. | `eha/epistemic_resilience.py::score_record`; reported columns in `scored_predictions.csv`. | Done |
| Add a 100-task Epistemic Resilience Table v1. | `data/epistemic-resilience-v1/tasks.jsonl`; manifest has `task_count: 100`. | Done |
| Use task families 40 fixed packet, 40 evidence selection, 20 active verification. | `data/epistemic-resilience-v1/manifest.json` has family counts `40/40/20`; audit verifies this. | Done |
| Balance evidence conditions across clean, conflicting evidence, false consensus, buried primary, generated lore. | `manifest.json` has 20 tasks per condition; `audit_manifest.json` repeats this. | Done |
| Evaluate `gpt-4o-mini`, `gpt-5-mini`, `gpt-5.4-mini`, and a `gpt-5.5` small sample. | Final run `results/runs/epistemic-resilience-v1-api-final/predictions.jsonl` has 200/200/200/24 records. | Done |
| Run both `standard_answer` and `epistemic_hygiene_instruction` prompt conditions. | `run_manifest.json` and `main_table.csv` include both prompts for all models. | Done |
| Main table columns: Model, Prompt, Evidence packet, Evidence selection, Active verification, Avg epistemic escape. | `results/reports-epistemic-resilience-v1/main_table.csv` uses `model`, `prompt`, `packet_judgment`, `evidence_selection`, `active_verification`, `avg_epistemic_escape`. | Done |
| Include evidence-selection metrics: primary seeking, duplicate avoidance, generated-lore avoidance, contradiction seeking, evidence value score. | `scored_predictions.csv`, `by_family.csv`, and `by_condition.csv` include all five metrics. | Done |
| Treat RAG results as a case study rather than the primary contribution. | `epistemic_resilience_reframe.md` contains the case-study section and proposed manuscript language. | Done |
| Avoid invented citations. | Reframe note instructs `[citation needed]` for external literature claims and does not invent references. | Done |
| Use modern Python stack rather than stdlib-only. | CLI uses Typer, Pydantic, Loguru, Rich, OpenAI client. Dependencies managed in `pyproject.toml` / `uv.lock`. | Done |
| Manage Python packages with `uv`. | All verification commands use `uv run`; no pip workflow added. | Done |
| Use the OpenAI LLM client. | API runner uses `from openai import OpenAI` through `Phase2OpenAIJsonRunner`. | Done |
| Use `LLM_API_KEY` and `LLM_BASE_URL` endpoint configuration. | Existing `eha.run_eval.openai_config()` is reused by the new runner. | Done |
| Add tests for the new benchmark logic. | `tests/test_epistemic_resilience.py` covers task counts, stratified sample selection, and scoring. | Done |
| Emit machine-readable diagnostics and audit output. | `eha-epistemic-resilience report` emits `audit_manifest.json` and `cost_report.json`; `eha-audit-epistemic-resilience run` emits `artifact_audit.json`. | Done |
| Verify final artifacts, tests, and compile gate. | `uv run eha-audit-epistemic-resilience` passed and recorded command results in `artifact_audit.json`. | Done |

Important caveats to report:

1. `openai/gpt-5.5` is a 12-task sample, not a full-table estimate.
2. The first gpt-5.5 sample was clean-only; it was superseded by the final family-and-condition-stratified sample in `results/runs/epistemic-resilience-v1-api-final`.
3. `openai/gpt-5-mini` had structured-output parse failures under the configured endpoint. These are counted as failed records and reported through `parse_success`.
