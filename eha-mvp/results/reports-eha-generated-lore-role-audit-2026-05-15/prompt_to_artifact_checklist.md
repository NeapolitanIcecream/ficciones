# Prompt To Artifact Checklist

Objective: advance work based on two local 2026-05-15 research notes supplied outside the repository.

## Concrete Success Criteria

1. Reframe the frontier result for external readers instead of treating it as an internal model leaderboard.
2. Explain EHA, generated lore, evidence cleanliness, active verification, and epistemic escape in plain language.
3. Organize the main narrative around reader questions and figure-ready result slices.
4. Add generated-lore interpretation audit for `gpt-5.4`, without rerunning the full main experiment.
5. Produce the named audit artifacts requested in the side note: decomposition CSV, manual audit pack, schema clarification mini-rerun CSV, and side note update.
6. Verify code changes with tests and compile checks.

## Requirement Mapping

| Requirement | Evidence | Status |
| --- | --- | --- |
| Do not rerun the full frontier main experiment. | No new `reports-eha-frontier-main` rerun was started; the mini-rerun output is in `reports-eha-generated-lore-role-audit-2026-05-15/`. | Done |
| Re-explain the experiment for readers who do not know EHA. | `../../../reports/eha-frontier-reader-facing-narrative-2026-05-15.md` starts with a one-sentence story and plain-language definitions. | Done |
| Explain that EHA is not ordinary answer accuracy. | Narrative report sections "One-Sentence Story" and "Main Result, Without Turning It Into A Leaderboard". | Done |
| Add human-readable definitions for generated lore, evidence cleanliness, epistemic escape, false consensus, and active verification. | Narrative report "Reader-Facing Definitions" table. | Done |
| Reorganize results around reader questions / main figures. | Narrative report "Five Main Figure Plan" includes task diagram, capability decomposition, family difficulty, condition breakdown, and prompt slope. | Done |
| Highlight active verification as a difficult agentic layer. | Narrative report Figure 3 and Case 2; source data from `../reports-eha-frontier-main/frontier_main_metrics_by_family.csv`. | Done |
| Highlight generated lore as a key condition. | Narrative report Figure 4 and Case 1; source data from `../reports-eha-frontier-main/frontier_main_metrics_by_condition.csv`. | Done |
| Explain prompt hygiene is not a universal fix. | Narrative report Figure 5 and Case 3 use standard vs hygiene model-level escape values. | Done |
| Explain token-budget fairness in simple terms. | Narrative report "Token-Budget Fairness In One Paragraph"; source from prior budget audit and main output-length metrics. | Done |
| Add GPT-5.4 generated-lore interpretation audit. | New module `../../eha/epistemic_generated_lore_audit.py`; outputs in this directory. | Done |
| Existing-output decomposition for `gpt-5.4` generated-lore records. | `generated_lore_belief_vs_role_decomposition.csv`: `gpt-5.4` all row has n=40, belief_correctness=1.0, insufficient=1.0, polluted_supporting=0.9, dual_role=0.875, full_escape=0.1. | Done |
| Compute belief correctness. | `generated_lore_belief_vs_role_decomposition.csv` column `belief_correctness_rate`. | Done |
| Compute insufficient verdict rate. | `generated_lore_belief_vs_role_decomposition.csv` column `insufficient_verdict_rate`. | Done |
| Compute rejected pollutant rate. | `generated_lore_belief_vs_role_decomposition.csv` column `rejected_pollutant_rate`. | Done |
| Compute polluted supporting evidence rate. | `generated_lore_belief_vs_role_decomposition.csv` column `polluted_supporting_evidence_rate`. | Done |
| Compute dual-role pollutant rate. | `generated_lore_belief_vs_role_decomposition.csv` column `dual_role_pollutant_rate`. | Done |
| Compute full escape. | `generated_lore_belief_vs_role_decomposition.csv` column `full_escape`. | Done |
| Manual audit pack with 15 representative GPT-5.4 generated-lore cases. | `gpt54_generated_lore_audit_pack.jsonl` has 15 lines and includes question, gold labels, model answer, evidence fields, scorer decision, and audit questions. | Done |
| Include 5 standard-answer failures. | Audit pack selection includes standard-answer rows with full_escape=0 or polluted support. | Done |
| Include 5 hygiene cases. | Audit pack selection includes hygiene prompt rows. | Done |
| Include mixed or edge cases. | Audit pack selection includes clean/dual-role edge cases and active-verification examples. | Done |
| Schema clarification mini-rerun. | `clarified_predictions.jsonl` has 120 rows: 20 generated-lore tasks × 2 prompts × 3 models. | Done |
| Mini-rerun models are `gpt-5.4`, `claude-opus-4-7`, `gemini-3.1-pro-preview`. | `clarified_run_manifest.json` lists all three models. | Done |
| Compare current schema vs clarified schema. | `schema_clarification_mini_rerun.csv` has both `current_schema` and `clarified_schema` rows. | Done |
| Clarified schema includes `clean_supporting_evidence`, `refuting_evidence`, `rejected_or_contaminated_evidence`, `diagnostic_evidence`. | `../../eha/epistemic_generated_lore_audit.py` function `clarified_evidence_json_schema()` and tests verify these fields. | Done |
| Main question: does clarified schema reduce GPT-5.4 polluted-supporting rate? | `schema_clarification_mini_rerun.csv`: `gpt-5.4` current all = 0.900; clarified all = 0.000. | Done |
| Produce `generated_lore_belief_vs_role_decomposition.csv`. | File exists; 10 lines. | Done |
| Produce `gpt54_generated_lore_audit_pack.jsonl`. | File exists; 15 lines. | Done |
| Produce `schema_clarification_mini_rerun.csv`. | File exists; 19 lines. | Done |
| Produce `side_note_update.md`. | File exists; 48 lines and includes existing-output decomposition plus mini-rerun table. | Done |
| Do not change the main frontier table retroactively. | Main result files remain separate; new interpretation artifacts live in this audit directory and reports directory. | Done |
| Report as interpretation / validity appendix. | `side_note_update.md` states it does not revise the main frontier table; narrative report frames it as interpretation. | Done |
| Update longer GPT-5.4 side note with clarified rerun result. | `../../../reports/eha-gpt54-generated-lore-evidence-role-side-note-2026-05-15.md` now has section "5.1 Schema clarification mini-rerun". | Done |
| Add tests for new audit behavior. | `../../tests/test_epistemic_generated_lore_audit.py` has 4 tests covering role metrics, schema fields, role escape, and JSON extraction. | Done |
| Run full tests. | `uv run pytest -q` passed 74 tests. | Done |
| Run compile check. | `uv run python -m compileall eha` passed. | Done |

## Output Counts

- `clarified_predictions.jsonl`: 120 rows.
- `schema_clarification_mini_rerun_rows.csv`: 240 data rows plus header.
- `generated_lore_belief_vs_role_rows.csv`: 120 data rows plus header.
- `gpt54_generated_lore_audit_pack.jsonl`: 15 rows.
- Clarified-schema API cost: `spent_usd = 0.278807`.

## Remaining Gaps

None for the 0515-0 / 0515-1 objective. The work produced the requested interpretation artifacts, ran the constrained mini-rerun, avoided full rerun, and verified the new code.
