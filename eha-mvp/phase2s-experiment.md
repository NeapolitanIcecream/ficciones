# EHA Phase 2S Experiment

This file records the Phase 2S repair experiment implemented from `/Users/chenmohan/Downloads/ficciones-research-0513-1.md`.

Phase 2S tests two blockers from Phase 2R: multi-label evidence diagnosis and temporal tool routing. It does not launch the larger multi-model main experiment.

## Implemented Scope

- New schema `evidence_diagnostics_v1`:
  - `claim_verdict`
  - `evidence_diagnostics`
  - `critical_risks`
  - `verification_ledger`
  - `supporting_evidence`
  - `rejected_evidence`
- Calibration prompt `evidence_diagnostics_v2`:
  - keeps the same JSON schema as `evidence_diagnostics_v1`
  - adds claim-first decision order
  - treats `no_primary_source` as a last-resort diagnostic when no current primary record is present
  - requires `partial_support` to name a missing claim component rather than generic caution
  - keeps low-severity uncertainty in `verification_ledger` instead of inflating `critical_risks`
- Calibration prompt `evidence_diagnostics_v3`:
  - adds risk-to-verdict override rules for stale, conflict, citation-laundering, partial-support, generated-lore, and no-primary cases
  - keeps claim-first calibration but prevents critical risks from being suppressed to preserve `supported`
- Calibration prompt `evidence_diagnostics_v4`:
  - keeps the v3 override rules
  - tightens `no_primary_source` so a visible primary record that refutes the claim, or makes support insufficient, is still treated as primary evidence
- Calibration prompt `evidence_diagnostics_v5`:
  - keeps the v4 no-primary boundary
  - experiments with explicit polluted-environment risk reporting for Module C final answers
  - is not part of the default Module A prompt sweep
- Calibration prompt `evidence_diagnostics_v6`:
  - keeps v5 supply-chain risk reporting
  - tightens the boundary between no-primary/generated evidence and true refutation
  - pairs with a stronger same-root routing rule for Module C active runs
- Calibration prompt `evidence_diagnostics_v7`:
  - keeps the v6 routing repair
  - tightens stale, citation-laundering, false-consensus, generated-lore, and partial-support label boundaries
  - is a final C-only diagnostic-label calibration before spending on another full Phase 2S API run
- Module A data observability repair:
  - current primary records now explicitly state whether they support, refute, or fail to establish the target claim
  - this prevents API models from relying on hidden gold metadata or guessing from generic "claim-level status" wording
- Module A: `EHA-v2S-scope-diagnostic`
  - seed `7319`
  - 120 episodes
  - no retrieval; 4-8 relevant docs are provided directly
  - compares `evidence_graph_v3`, `evidence_diagnostics_v1`, `evidence_diagnostics_v2`, `evidence_diagnostics_v3`, and `evidence_diagnostics_v4`
- Module B: `EHA-v2S-temporal-routing`
  - seed `8144`
  - 60 episodes
  - compares `static_hygienic_combo`, `forced_compare_versions`, `route_then_answer_v1`, and previous `tool_agent_3call_policy`
- Module C: integrated regression on existing `EHA-v2R-stress-pilot`
  - seed `6271`
  - 80 episodes
  - static retrievers: `bm25_top8`, `primary_preserve_top8`, `hygienic_combo_top8`
  - active hard subset: 48 Phase 2R hard episodes
  - active strategies: `static_hygienic_combo`, `route_then_answer_v1`, `forced_triage_tools`
- Cost guard:
  - soft cap `$50`
  - hard cap `$150`
  - abort cap `$300`

The API client uses the OpenAI package and reads `LLM_API_KEY` and `LLM_BASE_URL`.
Phase 2S now omits `temperature` by default; pass `--temperature 0.0` only for providers and models that support it.

## Generated Data

Generate both Phase 2S datasets:

```bash
uv run eha-generate-2s all \
  --scope-seed 7319 \
  --temporal-seed 8144 \
  --scope-out-dir data/phase2s-scope-diagnostic \
  --temporal-out-dir data/phase2s-temporal-routing
```

Current generated counts:

- `data/phase2s-scope-diagnostic/tasks.jsonl`: 120 tasks
- `data/phase2s-temporal-routing/tasks.jsonl`: 60 tasks
- `data/phase2r-stress-pilot/tasks.jsonl`: 80 reused tasks for Module C

## Heuristic Validation

```bash
uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend heuristic \
  --models heuristic-sim \
  --out-dir results/runs/phase2s-heuristic
```

Report:

```bash
uv run eha-report-2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2s-heuristic \
  --out-dir results/reports-phase2s-heuristic
```

The earlier v2 heuristic gate passed and wrote 984 predictions because Module A included the additional `evidence_diagnostics_v2` comparison arm. After v3/v4, a full default heuristic run includes 1,224 predictions; the targeted validation runs below use Module A-only prompt slices to keep iteration cheap.

The 2026-05-16 v2 smoke run was written separately so it does not overwrite the earlier API run:

```bash
uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend heuristic \
  --models heuristic-sim \
  --out-dir results/runs/phase2s-v2-heuristic

uv run eha-report-2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2s-v2-heuristic \
  --out-dir results/reports-phase2s-v2-heuristic
```

This is a wiring and gate smoke test, not API evidence. In that heuristic run, the gate selected `module_a_prompt = evidence_diagnostics_v2`, passed all checks, and wrote:

- `results/runs/phase2s-v2-heuristic/predictions.jsonl`: 984 predictions
- `results/runs/phase2s-v2-heuristic/scored_predictions.csv`: 984 scored rows plus header
- `results/reports-phase2s-v2-heuristic/summary.md`

For a lower-cost calibration run before repeating Module B/C, run Module A only:

```bash
uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend heuristic \
  --models heuristic-sim \
  --modules A \
  --out-dir results/runs/phase2s-v2-module-a-heuristic

uv run eha-report-2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2s-v2-module-a-heuristic \
  --out-dir results/reports-phase2s-v2-module-a-heuristic
```

The Module A-only heuristic run wrote 360 predictions and a scoped `module_a` gate in both `phase2s_gate.json` and `phase2s_module_a_gate.json`.

The 2026-05-16 targeted API Module A run used `gpt-4o-mini`, omitted `temperature`, and kept `max_output_tokens=3000`:

```bash
source ~/.zshrc && uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models gpt-4o-mini \
  --modules A \
  --out-dir results/runs/phase2s-v2-module-a-gpt4omini \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 2 \
  --hard-cap-usd 5 \
  --abort-cap-usd 10

uv run eha-report-2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2s-v2-module-a-gpt4omini \
  --out-dir results/reports-phase2s-v2-module-a-gpt4omini
```

The API scoped gate failed. `evidence_diagnostics_v2` improved `no_primary` precision but overcorrected claim-first calibration: it predicted `supported` for all stale, conflicting, citation-laundering, and partial-support tasks. Treat v2 as a negative result, not as the next full-run prompt.

| Prompt | Claim accuracy | Diagnostic macro-F1 | No-primary precision | Unsafe miss rate |
| --- | ---: | ---: | ---: | ---: |
| `evidence_graph_v3` | 0.433 | 0.302 | 0.667 | 0.467 |
| `evidence_diagnostics_v1` | 0.367 | 0.576 | 0.455 | 0.008 |
| `evidence_diagnostics_v2` | 0.333 | 0.500 | 0.952 | 0.325 |

## 2026-05-16 v3/v4 Module A Calibration

The v3 prompt added risk-to-verdict overrides, but the first API run showed a dataset observability problem: several refuted or insufficient cases had a generic current primary record body that said it "gives the claim-level status" without exposing whether the current status supported or refuted the target claim. The gold metadata was correct, but the visible document text did not make the claim verdict recoverable. A regression test now requires the Module A document text to expose the verdict-relevant primary evidence.

The scope dataset was regenerated after this repair:

```bash
uv run eha-generate-2s scope \
  --seed 7319 \
  --out-dir data/phase2s-scope-diagnostic
```

Targeted v3 and v4 runs:

```bash
uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend heuristic \
  --models heuristic-sim \
  --modules A \
  --module-a-prompts evidence_diagnostics_v4 \
  --out-dir results/runs/phase2s-v4-module-a-heuristic-observable

source ~/.zshrc && uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models gpt-4o-mini \
  --modules A \
  --module-a-prompts evidence_diagnostics_v4 \
  --out-dir results/runs/phase2s-v4-module-a-gpt4omini-observable \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 2 \
  --hard-cap-usd 5 \
  --abort-cap-usd 10
```

Reports:

- `results/reports-phase2s-v3-module-a-gpt4omini/summary.md`
- `results/reports-phase2s-v3-module-a-gpt4omini-observable/summary.md`
- `results/reports-phase2s-v4-module-a-gpt4omini-observable/summary.md`

| Run | Prompt | Data | Gate | Claim accuracy | Diagnostic macro-F1 | Stale recall | Conflict recall | Generated-lore recall | No-primary precision | Citation-laundering recall | Unsafe miss rate |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v2 API | `evidence_diagnostics_v2` | old generic primary text | fail | 0.333 | 0.500 | 0.000 | 0.475 | 1.000 | 0.952 | 0.900 | 0.325 |
| v3 API | `evidence_diagnostics_v3` | old generic primary text | fail | 0.467 | 0.688 | 0.550 | 0.900 | 1.000 | 0.909 | 1.000 | 0.058 |
| v3 API observable | `evidence_diagnostics_v3` | repaired visible primary text | fail | 0.967 | 0.711 | 1.000 | 1.000 | 1.000 | 0.870 | 1.000 | 0.000 |
| v4 API observable | `evidence_diagnostics_v4` | repaired visible primary text | pass | 1.000 | 0.748 | 0.900 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 |

Interpretation: v3 solved the verdict/risk interaction once the visible evidence made the target verdict observable. The remaining v3 failure was three `no_primary_source` false positives on tasks that had current primary records. v4 fixes that boundary and passes the Module A scoped gate on the repaired dataset. The next API action should be a full Phase 2S run with v4 selected as the Module A prompt before moving this repair into the main experimental narrative.

## 2026-05-16 Full v4 API Check

The full check used v4 for Module A only and left Module B/C final-answer prompts unchanged. This keeps the run cheaper and isolates whether the Module A fix is enough to clear the existing full gate.

```bash
source ~/.zshrc && uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models gpt-4o-mini \
  --modules A,B,C \
  --module-a-prompts evidence_diagnostics_v4 \
  --out-dir results/runs/phase2s-v4-full-gpt4omini-observable \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 2 \
  --hard-cap-usd 5 \
  --abort-cap-usd 10
```

Report:

- `results/reports-phase2s-v4-full-gpt4omini-observable/summary.md`

The full gate still failed, but the failure is now localized:

- Module A passed all seven A gates with `module_a_prompt = evidence_diagnostics_v4`.
- Module B temporal routing passed all six B gates.
- Module C passed clean-control accuracy, high-pressure BM25 failure preservation, high-pressure recovery delta, hygienic-combo claim accuracy, stale recall, conflict recall, and generated-lore recall.
- Module C failed:
  - `C5_hygienic_combo_contaminated_citation_rate_at_most_0_08`: observed `0.1453125`.
  - `C6_diagnostic_macro_f1_at_least_0_60`: observed `0.40707022599838094`.
  - `C10_active_tool_escape_not_more_than_0_05_below_static`: static hygienic combo escape `0.7291666666666666`, min active escape `0.6458333333333334`.

This means v4 repairs Module A and does not break Module B, but the integrated Phase 2R regression still uses `evidence_diagnostics_v1` for Module C final answers. The next repair should expose a shared diagnostic prompt setting for Module B/C final predictions and test whether v4 improves Module C contaminated citation handling and diagnostic macro-F1 without weakening the retrieval-pressure gates.

## 2026-05-16 Module C Final-Prompt Checks

Module B/C final-answer prompts are now configurable with `--final-diagnostic-prompt`. C-only API checks were run with `gpt-4o-mini`, `temperature` omitted, `max_output_tokens=3000`, and 384 predictions each.

```bash
source ~/.zshrc && uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models gpt-4o-mini \
  --modules C \
  --final-diagnostic-prompt evidence_diagnostics_v4 \
  --out-dir results/runs/phase2s-v4-module-c-gpt4omini-observable \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 1 \
  --hard-cap-usd 2 \
  --abort-cap-usd 5

source ~/.zshrc && uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models gpt-4o-mini \
  --modules C \
  --final-diagnostic-prompt evidence_diagnostics_v5 \
  --out-dir results/runs/phase2s-v5-module-c-gpt4omini-observable \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 1 \
  --hard-cap-usd 2 \
  --abort-cap-usd 5

source ~/.zshrc && uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models gpt-4o-mini \
  --modules C \
  --final-diagnostic-prompt evidence_diagnostics_v6 \
  --out-dir results/runs/phase2s-v6-module-c-gpt4omini-observable \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 1 \
  --hard-cap-usd 2 \
  --abort-cap-usd 5

source ~/.zshrc && uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models gpt-4o-mini \
  --modules C \
  --final-diagnostic-prompt evidence_diagnostics_v7 \
  --out-dir results/runs/phase2s-v7-module-c-gpt4omini-observable \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 1 \
  --hard-cap-usd 2 \
  --abort-cap-usd 5
```

Reports:

- `results/reports-phase2s-v4-module-c-gpt4omini-observable/summary.md`
- `results/reports-phase2s-v5-module-c-gpt4omini-observable/summary.md`
- `results/reports-phase2s-v6-module-c-gpt4omini-observable/summary.md`
- `results/reports-phase2s-v7-module-c-gpt4omini-observable/summary.md`
- `../reports/eha-phase2s-v7-diagnostic-bottleneck-2026-05-16.md`

Same C-gate metric extraction:

| Run | Final prompt | C static claim accuracy | C static diagnostic macro-F1 | C static stale recall | C static citation-laundering recall | Generated-lore recall | Hygienic contaminated citation rate | Static hygienic escape | Min active escape | Result |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Full v4 check | `evidence_diagnostics_v1` for B/C | 0.908 | 0.407 | 0.667 | 0.889 | 1.000 | 0.145 | 0.729 | 0.646 | C5/C6/C10 fail |
| C-only v4 | `evidence_diagnostics_v4` | 0.929 | 0.341 | 0.458 | 0.083 | 0.900 | 0.000 | 0.979 | 0.833 | C6/C7/C10 fail |
| C-only v5 | `evidence_diagnostics_v5` | 0.917 | 0.449 | 1.000 | 0.917 | 0.900 | 0.000 | 0.979 | 0.812 | C6/C10 fail |
| C-only v6 | `evidence_diagnostics_v6` + routing repair | 0.929 | 0.484 | 1.000 | 0.917 | 0.533 | 0.000 | 1.000 | 0.979 | C6/C9 fail |
| C-only v7 | `evidence_diagnostics_v7` + routing repair | 0.925 | 0.525 | 1.000 | 0.722 | 0.933 | 0.000 | 0.938 | 0.979 | C6 fail |

Interpretation: v4 removes contaminated citations but suppresses risk labels too much. v5 restores stale and citation-laundering recall while keeping contaminated citations at zero, but it overlabels visible pollution in clean-control rows, so diagnostic macro-F1 remains below the `0.60` gate. v6 confirms that C10 was mostly a routing/tool-policy failure: route-then-answer empty tool lists fell from 6/48 to 0/48, and min active escape rose to `0.979`, passing C10. v6 still fails C6 and C9 because generated-lore recall drops to `0.533` and static macro-F1 remains `0.484`. v7 restores generated-lore recall to `0.933` and keeps C10 passing, but static macro-F1 only rises to `0.525`; stale and citation-laundering false positives remain too high. The v7 bottleneck audit shows this is not just an artifact of unioning `critical_risks` with `evidence_diagnostics`: critical-only, diagnostic-only, and consistency-only counterfactual scores all remain below the C6 gate. Do not run another full Phase 2S API check until C6 passes in C-only mode. The remaining blocker is diagnostic label calibration, not active-tool routing.

## 2026-05-16 v8-v11 Structural-Schema Calibration

The next repair is a structural schema split, not another full v7 rerun. A fixed 35-row static C-only calibration slice now captures v7's known failure modes:

- `results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv`
- `../reports/eha-phase2s-v8-structural-schema-calibration-slice-2026-05-16.md`

The runner now accepts `--calibration-slice`, which filters Module C to the listed `(task_id, retriever)` static rows and skips active-tool rows. The v8 structural schema adds `environment_observations` beside sparse `critical_risks`; v9 keeps the split and tests a recall repair for true citation-laundering, false-consensus, and partial-support blockers; v10 adds a narrower risk decision table; v11 adds a supporting-evidence hard gate. Reports now also compute `support_role_metrics.csv` and `support_role_failures.csv`, so `supporting_evidence` role validity is measured independently from critical-risk labels.

Heuristic smoke run shape:

```bash
uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend heuristic \
  --models heuristic-sim \
  --modules C \
  --final-diagnostic-prompt evidence_diagnostics_v8_structural \
  --calibration-slice results/phase2s-v8-structural-schema-calibration-slice-2026-05-16.csv \
  --out-dir results/runs/phase2s-v8-structural-schema-calibration-slice-heuristic-v8 \
  --max-output-tokens 3000
```

API slice runs:

- `results/runs/phase2s-v8-structural-schema-calibration-slice-gpt4omini`, report `results/reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini`, `spent_usd = 0.031281`.
- `results/runs/phase2s-v9-structural-recall-calibration-slice-gpt4omini`, report `results/reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini`, `spent_usd = 0.033729`.
- `results/runs/phase2s-v10-structural-contract-calibration-slice-gpt4omini`, report `results/reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini`, `spent_usd = 0.034349`.
- `results/runs/phase2s-v11-role-disciplined-calibration-slice-gpt4omini`, report `results/reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini`, `spent_usd = 0.037478`.

| Run | Rows | Claim accuracy | Contaminated citation rate | Direct critical-risk macro-F1 | Observation macro-F1 | Support-role valid rate | Result |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| v7 baseline on slice | 35 | 0.800 | 0.000 | 0.393 diagnostic macro-F1 | not available | not available | fails; overlabels visible pollution |
| v8 structural | 35 | 0.886 | 0.000 | 0.369 | 0.574 | 0.886 | fails; keeps clean controls sparse but loses citation-laundering, false-consensus, and partial-support critical recall |
| v9 structural-recall | 35 | 0.886 | 0.029 | 0.299 | 0.643 | 0.886 | fails; improves observation reporting but not the direct critical-risk contract |
| v10 structural-contract | 35 | 0.886 | 0.086 | 0.404 | 0.666 | 0.857 | fails; improves direct critical-risk macro-F1 but crosses the contaminated citation threshold |
| v11 role-disciplined contract | 35 | 0.857 | 0.000 | 0.240 | 0.582 | 0.857 | fails; hard gate removes contaminated support but suppresses stale, citation-laundering, and partial-support recall |

The slice is deliberately failure-enriched and is not a replacement benchmark estimate. Current evidence argues against a full C-only API rerun. Direct `critical_risks` scoring, explicit observation-gold scoring, and independent support-role scoring are now implemented in the report path. The support-role clean-only rates are v8 `1.000`, v9 `0.971`, v10 `0.914`, and v11 `1.000`; v11 therefore fixes clean support lists, but not the direct critical-risk recall problem. The next repair should not be another wording-only prompt. It needs a more constrained schema or post-hoc scorer contract that separately validates support roles and risk labels.

## Historical API Run

```bash
uv run eha-phase2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --backend api \
  --models openai/gpt-4o-mini \
  --out-dir results/runs/phase2s-gpt4omini \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 50 \
  --hard-cap-usd 150 \
  --abort-cap-usd 300
```

Report:

```bash
uv run eha-report-2s \
  --scope-data-dir data/phase2s-scope-diagnostic \
  --temporal-data-dir data/phase2s-temporal-routing \
  --phase2r-data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2s-gpt4omini \
  --out-dir results/reports-phase2s
```

Main report:

```text
results/reports-phase2s/summary.md
```

## API Gate Result

The earlier `openai/gpt-4o-mini` Phase 2S API run completed before `evidence_diagnostics_v2` existed, so it only compares `evidence_graph_v3` and `evidence_diagnostics_v1` in Module A. The gate failed.

Passed:

- Module B temporal routing passed all six B gates.
- `route_then_answer_v1` compare_versions rate on temporal cases was `1.0`.
- useful compare_versions rate was `1.0`.
- temporal claim accuracy was `0.96`.
- hidden-label leakage was `false`.
- Module C preserved high-pressure BM25 failure: wrong-answer rate was `0.9166666666666666`.
- Module C hygienic combo recovery delta was `0.9166666666666666`.
- Module C hygienic combo claim accuracy was `1.0`.

Failed:

- Module A claim accuracy was `0.39166666666666666`.
- Module A diagnostic macro-F1 was `0.5812290351588436`.
- Module A no-primary precision was `0.38461538461538464`.
- Module C clean-control BM25 claim accuracy was `0.875`.
- Module C hygienic-combo contaminated citation rate was `0.1640625`.
- Module C diagnostic macro-F1 was `0.4040549107228354`.
- Module C active tool escape rate dropped from `0.75` for `static_hygienic_combo` to `0.6041666666666666` for the weakest active strategy.

The API run wrote:

- `results/runs/phase2s-gpt4omini/predictions.jsonl`: 864 predictions
- `results/runs/phase2s-gpt4omini/scored_predictions.csv`: 864 scored prediction rows plus header
- `results/runs/phase2s-gpt4omini/retrieval_metrics.csv`: 240 Module C retrieval metric rows plus header

Cost report:

```json
{
  "record_cost_usd": 0.382412,
  "spent_usd": 0.422466
}
```

Do not start the larger Phase 3 or multi-model main experiment from the historical API state or from the v2 Module A negative result. The v3/v4 repair above supersedes that earlier next step, but the full v4 check still shows an unresolved Module C blocker.

## Report Files

The formal Phase 2S report directory contains:

- `results/reports-phase2s/summary.md`
- `results/reports-phase2s/scope_diagnostic_metrics.csv`
- `results/reports-phase2s/temporal_routing_metrics.csv`
- `results/reports-phase2s/integrated_regression_metrics.csv`
- `results/reports-phase2s/diagnostic_confusion_by_flag.csv`
- `results/reports-phase2s/tool_routing_metrics.csv`
- `results/reports-phase2s/unsafe_scope_misses.csv`
- `results/reports-phase2s/failure_cases_phase2s.md`
- `results/reports-phase2s/cost_report.json`
