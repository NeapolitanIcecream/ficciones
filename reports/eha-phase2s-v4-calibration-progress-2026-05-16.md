# EHA Phase 2S v4 Calibration Progress

Date: 2026-05-16

## Purpose

This note records the follow-up repair after the Phase 2S v2 API calibration failed and the first v3 calibration exposed a data observability problem in Module A. The goal is still narrow: prove a Module A prompt/data repair before spending budget on another full Phase 2S run.

## What Changed

- Added a regression test requiring Module A claim verdicts to be inferable from visible document text.
- Repaired `EHA-v2S-scope-diagnostic` generation so current primary records explicitly say whether they support, refute, or fail to establish the target claim.
- Regenerated `data/phase2s-scope-diagnostic` with seed `7319`.
- Added `evidence_diagnostics_v4`, which keeps v3 risk-to-verdict override rules and tightens `no_primary_source`.
- Updated Module A defaults and gate selection so `evidence_diagnostics_v4` is the newest diagnostic prompt.
- Added configurable Module B/C final-answer diagnostic prompts via `--final-diagnostic-prompt`.
- Added `evidence_diagnostics_v5` as a targeted Module C experiment that tries to keep visible supply-chain pollution labels without putting polluted documents in `supporting_evidence`.
- Added `evidence_diagnostics_v6` plus stronger same-root routing rules to test whether C10 was a routing failure rather than a final-answer failure.
- Added `evidence_diagnostics_v7` as a final C-only label-calibration check for stale, citation-laundering, false-consensus, generated-lore, and partial-support boundaries.
- Added `--calibration-slice` support for a fixed 35-row static Module C slice before spending on another 384-row C-only run.
- Added `evidence_diagnostics_v8_structural`, which separates `environment_observations` from sparse verdict-critical `critical_risks`.
- Added `evidence_diagnostics_v9_structural_recall`, which keeps the v8 structural split but tests whether true citation-laundering, false-consensus, and partial-support blockers can be restored.
- Added direct `critical_risks` scoring and structural observation scoring derived from visible `final_doc_ids`, so reports now separately measure verdict-critical risks and `environment_observations`.
- Added `evidence_diagnostics_v10_structural_contract`, a narrower decision-table prompt for when visible observations must become critical risks.
- Added `evidence_diagnostics_v11_role_disciplined_contract`, which keeps v10's decision table but adds a hard gate preventing polluted, failed-support, stale, generated, corrupted, or no-primary documents from entering `supporting_evidence`.
- Added independent support-role scoring for `supporting_evidence`, reported as `support_role_metrics.csv` and `support_role_failures.csv`, so evidence-list cleanliness can be evaluated without folding it into critical-risk recall.

## Verification

- `uv run pytest tests/test_phase2s.py::test_phase2s_scope_dataset_makes_verdict_observable_in_document_text -q`: 1 passed.
- `uv run pytest tests/test_phase2s.py -q`: 28 passed.
- `uv run pytest -q`: 194 passed.
- `uv run eha-generate-2s scope --seed 7319 --out-dir data/phase2s-scope-diagnostic`: wrote 120 scope tasks and 656 documents.
- `uv run eha-phase2s ... --backend heuristic --modules A --module-a-prompts evidence_diagnostics_v4 --out-dir results/runs/phase2s-v4-module-a-heuristic-observable`: Module A scoped gate passed.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v4-module-a-heuristic-observable --out-dir results/reports-phase2s-v4-module-a-heuristic-observable`: wrote the heuristic report package.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules A --module-a-prompts evidence_diagnostics_v4 --out-dir results/runs/phase2s-v4-module-a-gpt4omini-observable --max-output-tokens 3000 --soft-cap-usd 2 --hard-cap-usd 5 --abort-cap-usd 10`: wrote 120 API predictions with `temperature` omitted.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v4-module-a-gpt4omini-observable --out-dir results/reports-phase2s-v4-module-a-gpt4omini-observable`: wrote the API report package.
- `results/runs/phase2s-v4-module-a-gpt4omini-observable/phase2s_module_a_gate.json`: `passed = true`, `module_a_prompt = evidence_diagnostics_v4`.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules A,B,C --module-a-prompts evidence_diagnostics_v4 --out-dir results/runs/phase2s-v4-full-gpt4omini-observable --max-output-tokens 3000 --soft-cap-usd 2 --hard-cap-usd 5 --abort-cap-usd 10`: wrote 744 full Phase 2S predictions.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v4-full-gpt4omini-observable --out-dir results/reports-phase2s-v4-full-gpt4omini-observable`: wrote the full report package.
- `results/runs/phase2s-v4-full-gpt4omini-observable/phase2s_gate.json`: `passed = false`; A and B gates passed, Module C gates C5/C6/C10 failed.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules C --final-diagnostic-prompt evidence_diagnostics_v4 --out-dir results/runs/phase2s-v4-module-c-gpt4omini-observable --max-output-tokens 3000 --soft-cap-usd 1 --hard-cap-usd 2 --abort-cap-usd 5`: wrote 384 C-only API predictions.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v4-module-c-gpt4omini-observable --out-dir results/reports-phase2s-v4-module-c-gpt4omini-observable`: wrote the v4 C-only report package.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules C --final-diagnostic-prompt evidence_diagnostics_v5 --out-dir results/runs/phase2s-v5-module-c-gpt4omini-observable --max-output-tokens 3000 --soft-cap-usd 1 --hard-cap-usd 2 --abort-cap-usd 5`: wrote 384 C-only API predictions.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v5-module-c-gpt4omini-observable --out-dir results/reports-phase2s-v5-module-c-gpt4omini-observable`: wrote the v5 C-only report package.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules C --final-diagnostic-prompt evidence_diagnostics_v6 --out-dir results/runs/phase2s-v6-module-c-gpt4omini-observable --max-output-tokens 3000 --soft-cap-usd 1 --hard-cap-usd 2 --abort-cap-usd 5`: wrote 384 C-only API predictions.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v6-module-c-gpt4omini-observable --out-dir results/reports-phase2s-v6-module-c-gpt4omini-observable`: wrote the v6 C-only report package.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules C --final-diagnostic-prompt evidence_diagnostics_v7 --out-dir results/runs/phase2s-v7-module-c-gpt4omini-observable --max-output-tokens 3000 --soft-cap-usd 1 --hard-cap-usd 2 --abort-cap-usd 5`: wrote 384 C-only API predictions; the scoped C gate still failed.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v7-module-c-gpt4omini-observable --out-dir results/reports-phase2s-v7-module-c-gpt4omini-observable`: wrote the v7 C-only report package.
- `uv run eha-phase2s ... --backend heuristic --modules C --final-diagnostic-prompt evidence_diagnostics_v7 --calibration-slice results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv --out-dir results/runs/phase2s-v8-structural-schema-calibration-slice-heuristic`: wrote 35 static C-only calibration predictions and 35 retrieval metric rows.
- `uv run eha-phase2s ... --backend heuristic --modules C --final-diagnostic-prompt evidence_diagnostics_v8_structural --calibration-slice results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv --out-dir results/runs/phase2s-v8-structural-schema-calibration-slice-heuristic-v8`: wrote 35 static C-only calibration predictions and 35 retrieval metric rows.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules C --final-diagnostic-prompt evidence_diagnostics_v8_structural --calibration-slice results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv --out-dir results/runs/phase2s-v8-structural-schema-calibration-slice-gpt4omini --max-output-tokens 3000 --soft-cap-usd 0.2 --hard-cap-usd 0.5 --abort-cap-usd 1`: wrote 35 API predictions; `spent_usd = 0.031281`.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules C --final-diagnostic-prompt evidence_diagnostics_v9_structural_recall --calibration-slice results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv --out-dir results/runs/phase2s-v9-structural-recall-calibration-slice-gpt4omini --max-output-tokens 3000 --soft-cap-usd 0.2 --hard-cap-usd 0.5 --abort-cap-usd 1`: wrote 35 API predictions; `spent_usd = 0.033729`.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules C --final-diagnostic-prompt evidence_diagnostics_v10_structural_contract --calibration-slice results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv --out-dir results/runs/phase2s-v10-structural-contract-calibration-slice-gpt4omini --max-output-tokens 3000 --soft-cap-usd 0.2 --hard-cap-usd 0.5 --abort-cap-usd 1`: wrote 35 API predictions; `spent_usd = 0.034349`.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules C --final-diagnostic-prompt evidence_diagnostics_v11_role_disciplined_contract --calibration-slice results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv --out-dir results/runs/phase2s-v11-role-disciplined-calibration-slice-gpt4omini --max-output-tokens 3000 --soft-cap-usd 0.2 --hard-cap-usd 0.5 --abort-cap-usd 1`: wrote 35 API predictions; `spent_usd = 0.037478`.

## API Module A Comparison

| Run | Prompt | Data | Gate | Claim accuracy | Diagnostic macro-F1 | Stale recall | Conflict recall | Generated-lore recall | No-primary precision | Citation-laundering recall | Unsafe miss rate |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v2 API | `evidence_diagnostics_v2` | old generic primary text | fail | 0.333 | 0.500 | 0.000 | 0.475 | 1.000 | 0.952 | 0.900 | 0.325 |
| v3 API | `evidence_diagnostics_v3` | old generic primary text | fail | 0.467 | 0.688 | 0.550 | 0.900 | 1.000 | 0.909 | 1.000 | 0.058 |
| v3 API observable | `evidence_diagnostics_v3` | repaired visible primary text | fail | 0.967 | 0.711 | 1.000 | 1.000 | 1.000 | 0.870 | 1.000 | 0.000 |
| v4 API observable | `evidence_diagnostics_v4` | repaired visible primary text | pass | 1.000 | 0.748 | 0.900 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

## Interpretation

The original v3 failure was not only a prompt issue. In the old Module A data, current primary records for several refuted or insufficient cases did not visibly state the target verdict, so the API model could not reliably recover the gold claim verdict without hidden metadata. After the data text was repaired, v3 crossed every gate except `no_primary_precision`. The remaining v3 errors were false positives where a current primary record existed but refuted or weakened the claim. v4 fixed that boundary and passed the scoped API gate.

This does not close Step 1. The independent active-verification human audit and attestation are still the release blocker.

## Full Phase 2S Check

The full v4 check used `evidence_diagnostics_v4` for Module A only and left Module B/C final-answer prompts at the existing `evidence_diagnostics_v1` binding. The run confirms that the Module A repair is not enough by itself to close Phase 2S.

Passed:

- A1-A7: Module A passed with `claim_accuracy = 0.9916666666666667`, `diagnostic_macro_f1 = 0.7486873173284323`, `no_primary_precision = 1.0`, and `unsafe_scope_miss_rate = 0.0`.
- B1-B6: temporal routing passed with `compare_versions_rate = 1.0`, `useful_compare_versions_rate = 1.0`, `claim_accuracy = 0.98`, and no hidden-label leakage.
- C1-C4 and C7-C9: clean control, high-pressure recovery, hygienic-combo claim accuracy, stale recall, conflict recall, and generated-lore recall passed.

Failed:

- C5: hygienic-combo contaminated citation rate was `0.1453125`, above the `0.08` maximum.
- C6: Module C static diagnostic macro-F1 was `0.40707022599838094`, below the `0.60` minimum.
- C10: min active tool escape was `0.6458333333333334`, more than `0.05` below static hygienic combo escape `0.7291666666666666`.

Interpretation: v4 should now be propagated beyond Module A. The next repair should make Module B/C final-answer prompts configurable and run a targeted C-only or full API check with v4 final answers before changing the paper narrative.

## Module C v4/v5/v6/v7 Final-Prompt Checks

The Module B/C final prompt is now configurable. Targeted C-only API checks show that simply propagating v4 is not enough, that v5 fixes recall at the cost of precision, that v6 repairs active routing without closing diagnostic labeling, and that v7 recovers generated-lore recall without crossing the macro-F1 gate.

| Run | Final prompt | C static claim accuracy | C static diagnostic macro-F1 | C static stale recall | C static citation-laundering recall | Generated-lore recall | Hygienic contaminated citation rate | Static hygienic escape | Min active escape | C-gate implication |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Full v4 check | `evidence_diagnostics_v1` for B/C | 0.908 | 0.407 | 0.667 | 0.889 | 1.000 | 0.145 | 0.729 | 0.646 | C5/C6/C10 fail |
| C-only v4 | `evidence_diagnostics_v4` | 0.929 | 0.341 | 0.458 | 0.083 | 0.900 | 0.000 | 0.979 | 0.833 | C6/C7/C10 fail |
| C-only v5 | `evidence_diagnostics_v5` | 0.917 | 0.449 | 1.000 | 0.917 | 0.900 | 0.000 | 0.979 | 0.812 | C6/C10 fail |
| C-only v6 | `evidence_diagnostics_v6` + routing repair | 0.929 | 0.484 | 1.000 | 0.917 | 0.533 | 0.000 | 1.000 | 0.979 | C6/C9 fail |
| C-only v7 | `evidence_diagnostics_v7` + routing repair | 0.925 | 0.525 | 1.000 | 0.722 | 0.933 | 0.000 | 0.938 | 0.979 | C6 fail |

Interpretation:

- v4 final answers solve contaminated citations (`0.000` on hygienic combo) but suppress stale/citation-laundering risk labels too aggressively.
- v5 restores stale and citation-laundering recall and keeps contaminated citations at `0.000`, but overlabels visible pollution in clean-control and low-pressure rows. Static macro-F1 rises from `0.341` to `0.449`, still below the `0.60` gate.
- v6 confirms C10 was largely a routing/tool-policy problem: `route_then_answer_v1` empty tool lists fell from 6/48 in v5 to 0/48, and min active escape rose to `0.979`, passing C10 against static escape `1.000`.
- v6 does not close diagnostic labeling. It improves static macro-F1 to `0.484`, but C6 is still below `0.60`, and generated-lore recall falls to `0.533`, failing C9.
- v7 recovers C9: generated-lore recall rises to `0.933`, no-primary precision is `0.814`, and C10 stays passed. It still fails C6 because static macro-F1 reaches only `0.525`, with stale and citation-laundering false positives still dominating the confusion table.
- The v7 bottleneck audit in `reports/eha-phase2s-v7-diagnostic-bottleneck-2026-05-16.md` confirms that the C6 failure is not solved by scoring only `critical_risks`, only `evidence_diagnostics`, or only labels where both channels agree; all three counterfactual modes stay below `0.60`.

Do not spend on another full Phase 2S API run from v7 alone. The active-tool repair should be kept, but the remaining blocker is diagnostic label calibration, especially stale and citation-laundering precision. A full run is only justified after C6 passes in C-only mode.

## v8-v11 Structural Slice Outcome

The fixed 35-row slice confirmed that the structural schema is syntactically viable but not yet a successful measurement repair.

| Run | Rows | Claim accuracy | Contaminated citation rate | Direct critical-risk macro-F1 | Observation macro-F1 | Support-role valid rate | Main result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| v7 baseline on slice | 35 | 0.800 | 0.000 | 0.393 diagnostic macro-F1 | not available | not available | over-expanded stale/citation-laundering/false-consensus |
| v8 structural | 35 | 0.886 | 0.000 | 0.369 | 0.574 | 0.886 | clean controls stay risk-empty, but citation-laundering, false-consensus, and partial-support critical recall drop to 0 |
| v9 structural-recall | 35 | 0.886 | 0.029 | 0.299 | 0.643 | 0.886 | improves observation reporting, but critical-risk contract remains unstable and contaminated citation worsens |
| v10 structural-contract | 35 | 0.886 | 0.086 | 0.404 | 0.666 | 0.857 | improves direct critical-risk macro-F1 but fails the contaminated-citation threshold |
| v11 role-disciplined contract | 35 | 0.857 | 0.000 | 0.240 | 0.582 | 0.857 | hard gate removes contaminated support but suppresses stale, citation-laundering, and partial-support recall |

The next repair should not be a full 384-row API rerun. Explicit observation-gold, direct critical-risk, and support-role scoring are now in place. v10 and v11 show that support-role cleanliness and critical-risk recall are pulling against each other under the current prompt-only contract: v10 improves labels but contaminates support, while v11 restores clean-only support to `1.000` and still loses labels. The next useful design should separate support-role validation from risk-label validation instead of adding another broad prompt paragraph.
