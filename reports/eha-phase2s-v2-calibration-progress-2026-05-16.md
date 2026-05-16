# EHA Phase 2S v2 Calibration Progress

Date: 2026-05-16

## Purpose

This note records the first repair step after the Phase 2S API report found that `evidence_diagnostics_v1` over-diagnosed evidence risk. The repair target is narrow: make Module A test a claim-first diagnostic prompt before spending API budget on another full Phase 2S run.

## What Changed

- Added `evidence_diagnostics_v2` as a prompt variant that keeps the same Phase 2S JSON schema.
- The v2 prompt requires the model to decide whether current primary evidence directly supports or refutes the target claim before adding risk labels.
- It treats `no_primary_source` as a last-resort diagnostic when no current primary record is present.
- It requires `partial_support` to name a missing claim component instead of acting as generic caution.
- Module A now compares `evidence_graph_v3`, `evidence_diagnostics_v1`, and `evidence_diagnostics_v2`.
- The Phase 2S gate uses `evidence_diagnostics_v2` for Module A when that prompt is present, while older runs without v2 still fall back to `evidence_diagnostics_v1`.
- The runner now accepts `--modules A` for a low-cost Module A-only calibration run before rerunning Module B/C.
- Phase 2S API calls omit `temperature` by default; pass an explicit value only for models that support it.

## Verification

- `uv run pytest tests/test_phase2s.py -q`: 5 passed.
- `uv run pytest -q`: 134 passed.
- `uv run eha-phase2s ... --backend heuristic --out-dir results/runs/phase2s-v2-heuristic`: wrote 984 predictions.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v2-heuristic --out-dir results/reports-phase2s-v2-heuristic`: wrote the report package.
- `results/runs/phase2s-v2-heuristic/phase2s_gate.json`: `passed = true`, `module_a_prompt = evidence_diagnostics_v2`.
- `uv run eha-phase2s ... --backend heuristic --modules A --out-dir results/runs/phase2s-v2-module-a-heuristic`: wrote 360 predictions.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v2-module-a-heuristic --out-dir results/reports-phase2s-v2-module-a-heuristic`: wrote a Module A scoped report.
- `results/runs/phase2s-v2-module-a-heuristic/phase2s_module_a_gate.json`: `scope = module_a`, `passed = true`, `module_a_prompt = evidence_diagnostics_v2`.
- `source ~/.zshrc && uv run eha-phase2s ... --backend api --models gpt-4o-mini --modules A --out-dir results/runs/phase2s-v2-module-a-gpt4omini --max-output-tokens 3000 --soft-cap-usd 2 --hard-cap-usd 5 --abort-cap-usd 10`: wrote 360 predictions with `temperature` omitted.
- `uv run eha-report-2s ... --run-dir results/runs/phase2s-v2-module-a-gpt4omini --out-dir results/reports-phase2s-v2-module-a-gpt4omini`: wrote the API Module A scoped report.
- `results/runs/phase2s-v2-module-a-gpt4omini/phase2s_module_a_gate.json`: `scope = module_a`, `passed = false`, `module_a_prompt = evidence_diagnostics_v2`.

## Heuristic Smoke Result

| Prompt | n | Claim accuracy | Diagnostic macro-F1 | No-primary precision | Unsafe miss rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `evidence_graph_v3` | 120 | 1.000 | 0.857 | 1.000 | 0.000 |
| `evidence_diagnostics_v1` | 120 | 1.000 | 1.000 | 1.000 | 0.000 |
| `evidence_diagnostics_v2` | 120 | 1.000 | 1.000 | 1.000 | 0.000 |

These values are from the heuristic backend. They show the runner, scorer, report, and gate paths are wired correctly; they do not show that an API model will obey the v2 calibration prompt.

## API Module A Result

The targeted API run used `gpt-4o-mini` with `temperature` omitted and `max_output_tokens = 3000`. It cost `0.148394` USD under the local cost estimator and did not abort.

| Prompt | n | Claim accuracy | Diagnostic macro-F1 | Stale recall | Conflict recall | Generated-lore recall | No-primary precision | Unsafe miss rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `evidence_graph_v3` | 120 | 0.433 | 0.302 | 0.000 | 0.000 | 0.000 | 0.667 | 0.467 |
| `evidence_diagnostics_v1` | 120 | 0.367 | 0.576 | 0.650 | 1.000 | 1.000 | 0.455 | 0.008 |
| `evidence_diagnostics_v2` | 120 | 0.333 | 0.500 | 0.000 | 0.475 | 1.000 | 0.952 | 0.325 |

The v2 prompt improved `no_primary` precision relative to v1, but it overcorrected the claim-first rule. In this API run, v2 predicted `supported` for all `stale_evidence`, `conflicting_evidence`, `citation_laundering`, and `partial_support` tasks, while still predicting `insufficient` for `generated_lore_with_no_primary`. This makes v2 a useful negative result, not a successful repair.

## Current Interpretation

The next experimental action should not be a full Phase 2S rerun with v2. The next repair should add a stricter risk-to-verdict rule set: claim-first calibration must still allow stale, conflict, citation-laundering, and partial-support evidence states to change the verdict away from `supported`. The success criterion is not simply gate pass; the key comparison is whether the next prompt improves Module A claim accuracy, diagnostic macro-F1, `no_primary` precision, stale/conflict recall, and `partial_support` false positives without reintroducing the v1 over-diagnosis pattern.

This does not close the Step 1 human-audit blocker. Step 1 readiness remains blocked until the independent active-verification human labels and attestation are completed.

## Follow-up

The v2 negative result was followed by a v3/v4 repair cycle. v3 added risk-to-verdict overrides and exposed that part of the Module A scope dataset did not make refuted/insufficient current-primary verdicts visible in document text. After repairing and regenerating the scope dataset, v4 tightened `no_primary_source` so a primary record that refutes the claim is not treated as absent primary evidence.

The current follow-up evidence is in `reports/eha-phase2s-v4-calibration-progress-2026-05-16.md`. The targeted API run `results/runs/phase2s-v4-module-a-gpt4omini-observable/phase2s_module_a_gate.json` passes the Module A scoped gate with `claim_accuracy = 1.0`, `diagnostic_macro_f1 = 0.7481640310908604`, `no_primary_precision = 1.0`, and `unsafe_scope_miss_rate = 0.0`.
