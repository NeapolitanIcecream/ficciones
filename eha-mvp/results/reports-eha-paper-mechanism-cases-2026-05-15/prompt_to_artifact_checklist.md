# Prompt-To-Artifact Checklist: Paper Mechanism Cases

Date: 2026-05-15

Source objective: local 0515-2 research objective note; private local path omitted.

## Success Criteria

| Requirement | Evidence | Status |
| --- | --- | --- |
| Do not rerun the full main experiment. | No new full-run output was created. This package only derives from existing frontier main outputs and the existing generated-lore clarified-schema mini-rerun. | Done |
| Move from experiment scaling to paper material. | Paper-facing draft created at `reports/eha-paper-mechanism-case-section-2026-05-15.md`. | Done |
| Confirm 2-3 representative GPT-5.4 generated-lore cases. | `paper_mechanism_case_studies.jsonl` contains three generated-lore cases: `ert_032`, `ert_033`, `ert_096`. Manual spot checks were made against `gpt54_generated_lore_audit_pack.jsonl` and `clarified_predictions.jsonl`. | Done |
| Each generated-lore case has verdict `insufficient`. | Raw current-schema audit pack shows `model_output.claim_verdict="insufficient"` for `ert_032`, `ert_033`, `ert_096`; clarified predictions also show `prediction.claim_verdict="insufficient"`. | Done |
| Each generated-lore case's natural-language explanation recognizes unreliable sources. | `ert_032` says apparent support is a wiki-style summary and downstream reposts with no primary record. `ert_033` says repeated secondary summaries lack primary documents or official records. `ert_096` says apparent support is an authoritative-looking summary and reposts with no primary documents or independent corroboration. | Done |
| Polluted documents appear in `rejected_evidence`. | Raw audit pack: `ert_032` rejects `eham_120_repost_00...03`; `ert_033` rejects `eham_121_repost_00...03`; `ert_096` rejects `eham_120_repost_00...03`. | Done |
| Same polluted documents also appear in `supporting_evidence`. | Raw audit pack: `ert_032` support includes `eham_120_pollutant_root`, `eham_120_repost_00`; `ert_033` support includes `eham_121_pollutant_root`, `eham_121_repost_00`; `ert_096` support includes `eham_120_pollutant_root`, `eham_120_repost_00`. | Done |
| Clarified schema moves pollutants to `rejected_or_contaminated_evidence` or `diagnostic_evidence`. | Raw clarified predictions: `ert_032`, `ert_033`, `ert_096` all have `clean_supporting_evidence=[]` and list pollutant root/reposts in `rejected_or_contaminated_evidence` and/or `diagnostic_evidence`. | Done |
| Make main figure as layer decomposition: Model, belief correctness, rejected pollutant rate, polluted supporting rate, full escape. | `figure_generated_lore_role_decomposition.csv` contains current-schema rows for `claude-opus-4-7`, `gemini-3.1-pro-preview`, `gpt-5.4` with the required columns. `figure_generated_lore_role_decomposition.svg` provides a first visual draft. The paper draft includes the same table under "Main Figure: Layer Decomposition." | Done |
| Pair active-verification failure as second mechanism case. | `paper_mechanism_case_studies.jsonl` contains `active_verification_agent_interface` case `gpt-5.4`, `ert_082`, `standard_answer`; paper draft includes it as "Mechanism Case 2." | Done |
| Active-verification case should show evidence-role problem plus next-action expression problem. | Generated-lore cases cover evidence-role failure. `ert_082` covers action-expression failure: correct `supported` verdict and clean primary support, but `verification_action_score=0.0` because action targets are bundled strings. | Done |
| Use generated-lore role audit as body case study. | Paper draft places generated-lore as Mechanism Case 1 and gives three concrete cases. | Done |
| Use clarified schema as validity analysis. | Paper draft includes "Validity Analysis Wording" and explicitly states clarified schema is not a replacement score. | Done |
| Avoid bad wording: not "GPT-5.4 cannot detect generated lore." | Paper draft explicitly says not to write this and uses the belief/role distinction. | Done |
| Avoid bad wording: not "clarified schema fixes/changes main score." | Paper draft says clarified schema is validity analysis, not retroactive correction. | Done |
| Use preferred wording: current schema exposes agent-interface risk; clarified schema shows field-semantics/evidence-role relation. | Paper draft includes this wording verbatim in "Validity Analysis Wording." | Done |

## Generated Artifacts

| File | Description |
| --- | --- |
| `figure_capability_decomposition.csv` | Frontier model capability decomposition for broader paper figures |
| `figure_task_family_escape.csv` | Task family difficulty figure data |
| `figure_prompt_slope.csv` | Prompt intervention slope data |
| `figure_generated_lore_role_decomposition.csv` | Required layer-decomposition figure data |
| `figure_generated_lore_role_decomposition.svg` | First visual draft of the layer-decomposition figure |
| `paper_mechanism_case_studies.jsonl` | Structured paper case rows |
| `paper_mechanism_case_studies.csv` | Spreadsheet-friendly version of case rows |
| `report_manifest.json` | Package manifest |
| `prompt_to_artifact_checklist.md` | This checklist |
| `reports/eha-paper-mechanism-case-section-2026-05-15.md` | Reader-facing paper draft section |

## Verification Commands Run

```bash
cat eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/report_manifest.json
head -20 eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/figure_generated_lore_role_decomposition.csv
head -20 eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/paper_mechanism_case_studies.csv
jq -c 'select((.task_id=="ert_032" or .task_id=="ert_033" or .task_id=="ert_096") and .prompt_condition=="standard_answer") | {task_id,family,verdict:.model_output.claim_verdict,answer:.model_output.answer,supporting:.model_output.supporting_evidence,rejected:.model_output.rejected_evidence,polluted_supporting_ids:.scorer_decision.polluted_supporting_ids,dual_role_ids:.scorer_decision.dual_role_pollutant_ids,rejected_pollutant_ids:.scorer_decision.rejected_pollutant_ids}' eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/gpt54_generated_lore_audit_pack.jsonl
jq -c 'select((.task_id=="ert_032" or .task_id=="ert_033" or .task_id=="ert_096") and .model=="gpt-5.4" and .prompt_condition=="standard_answer") | {task_id,family,parse_success,verdict:.prediction.claim_verdict,answer:.prediction.answer,clean_support:.prediction.clean_supporting_evidence,rejected_contaminated:.prediction.rejected_or_contaminated_evidence,diagnostic:.prediction.diagnostic_evidence}' eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/clarified_predictions.jsonl
jq -c 'select(.model=="gpt-5.4" and .task_id=="ert_082" and .prompt_condition=="standard_answer") | {task_id,condition,family,parse_success,predicted_verdict:.prediction.claim_verdict,supporting:.prediction.supporting_evidence,actions:.prediction.actions,json_field_lengths}' eha-mvp/results/reports-eha-frontier-main/predictions.jsonl
rg -n '^ert_082,' eha-mvp/results/reports-eha-frontier-main/frontier_main_scored_predictions.csv
```

## Residual Risks

- The draft section is a paper-writing artifact, not a final camera-ready section. It still needs integration with the paper's introduction, method notation, citations, and final figure rendering.
- The 0515-2 objective asked for mechanism-case material and figure decomposition, not a full literature-review update. External citations remain a separate paper-writing step.
