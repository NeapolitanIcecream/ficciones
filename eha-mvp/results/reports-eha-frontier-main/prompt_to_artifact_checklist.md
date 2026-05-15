# Prompt To Artifact Checklist

Objective: prepare the experimental facility required by `/Users/chenmohan/Downloads/ficciones-research-0514-2.md` and supplement it with the token-budget fairness requirements from `/Users/chenmohan/Downloads/ficciones-research-0514-3.md`.

| Requirement | Evidence | Status |
| --- | --- | --- |
| Freeze main cohort: `gpt-5.4`, `claude-opus-4-7`, `gemini-3.1-pro-preview`, `deepseek-v4-pro`, `kimi-k2.6`. | `frontier_main_run_plan.json` lists all 5 models. | Done |
| Use preflight invocation profiles exactly: no temperature; GPT/Claude/Gemini cap 4096 + `json_schema`; DeepSeek no cap + `json_object`; Kimi no cap + `json_schema`. | `frontier_main_run_plan.json` model entries include these profile fields. | Done |
| Do not change task families, schema, or risk labels. | Runner reads `data/epistemic-resilience-v1/tasks.jsonl`; plan shows `task_count=100`, family counts `40/40/20`, condition counts `20` each. | Done |
| Run matrix should be 100 tasks × 5 models × 2 prompts = 1000 calls. | `frontier_main_run_plan.json` has `job_count=1000`; `frontier_main_run_plan.md` states total calls. | Done |
| Include both prompt conditions: `standard_answer`, `epistemic_hygiene_instruction`. | Plan JSON and full-run `report_manifest.json` list both prompt conditions. | Done |
| Parallelize while preserving call success. | `eha.epistemic_frontier_main` runs one sequential stream per model with `parallel_model_streams=5`, `per_model_concurrency=1`, resume, retries, and process timeout. | Done |
| Avoid macOS fork-safety failures under threaded parallelism. | `complete_with_process_timeout()` now prefers `spawn`; valid smoke directory is `reports-eha-frontier-main-smoke-spawn-2026-05-14`. | Done |
| No LLM-based repair in main score. | Runner only retries same profile for transient API/timeout/empty-output; parsing uses first JSON object + schema validation. | Done |
| Universal JSON extractor allowed. | Runner calls `parse_prediction_with_diagnostics()` from preflight module and validates EHA schema. | Done |
| Log per call: model, provider, invocation profile, prompt, family, condition, parse success, empty output, schema missing, JSON extractor, token usage. | `predictions.jsonl` stores these fields; per-call `artifacts/*/*.response.json` stores attempt-level payloads. | Done |
| Report actual visible output length for all main-run calls. | `frontier_main_scored_predictions.csv` includes `visible_output_tokens`; aggregate CSVs include output-length metrics. | Done |
| Report JSON field lengths. | `frontier_main_scored_predictions.csv` includes answer, evidence-assessment, action-rationale, support/reject count fields. | Done |
| Report `overlength_rate`. | `frontier_main_scored_predictions.csv` and aggregate CSVs include `overlength_rate`; full run shows model-level `overlength_rate=0`. | Done |
| Add prompt/schema output constraints: JSON only, no chain-of-thought, short answer/evidence/rationale, max evidence/action counts. | `epistemic_resilience.py` prompt rules and `epistemic_prediction_json_schema()` include these constraints. | Done |
| Add cap-sensitivity subset for no-cap models. | `eha-epistemic-frontier-main budget-plan` writes a 120-call plan for DeepSeek/Kimi across `no_cap`, `cap_8192`, and `cap_4096_diagnostic`. | Done |
| Include budget audit decision rule. | `budget_fairness_audit_plan.json` includes rules for adopting `cap_8192` or retaining no-cap. | Done |
| Add methodology note explaining why fixed cap is not enforced globally. | `reports/eha-token-budget-fairness-plan-2026-05-14.md` includes the report-ready methodology paragraph. | Done |
| Execute full frontier main run. | `predictions.jsonl` has 1000 rows; per-call `artifacts/*/*.response.json` count is 1000; `report_manifest.json` has `record_count=1000`. | Done |
| Execute 120-call token-budget audit. | `../reports-eha-frontier-budget-audit/predictions.jsonl` has 120 rows; `budget_setting_decision.md` selects no-cap for DeepSeek/Kimi. | Done |
| Generate `summary.md`. | Full run generated `summary.md`. | Done |
| Generate `frontier_main_metrics_by_model.csv`. | Full run generated file; tests assert required artifact creation. | Done |
| Generate `frontier_main_metrics_by_family.csv`. | Full run generated file; tests assert required artifact creation. | Done |
| Generate `frontier_main_metrics_by_condition.csv`. | Full run generated file; tests assert required artifact creation. | Done |
| Generate `frontier_main_metrics_by_prompt.csv`. | Full run generated file; tests assert required artifact creation. | Done |
| Generate `operational_vs_conditional_escape.csv`. | Full run generated file; tests assert required artifact creation. | Done |
| Generate `failure_cases_frontier.jsonl`. | Full run generated file; tests assert required artifact creation. | Done |
| Generate `cost_report.json`. | Full run generated file; tests assert required artifact creation. | Done |
| Report `operational_epistemic_escape`, `conditional_epistemic_escape`, `parse_success`, `belief_correctness`, `evidence_cleanliness`, `uncertainty_discipline`, `verification_action_score`. | `report_manifest.json` lists all metrics; CSV headers include them. | Done |
| Verify real API path, not only unit tests. | Full API run completed `100 tasks × 5 models × 2 prompts = 1000` calls; `parse_success=999/1000`; `empty_output=0/1000`; output-length fields are present. | Done |
| Regression tests cover planning, frozen profiles, resume key detection, report artifact generation, and existing preflight/resilience logic. | `uv run pytest -q` passed 70 tests. | Done |
| Compile check. | `uv run python -m compileall eha` passed. | Done |

Remaining required work: none for the requested experiment stage. The full 1000-call main experiment and 120-call budget audit have both been executed, reported, and verified.
