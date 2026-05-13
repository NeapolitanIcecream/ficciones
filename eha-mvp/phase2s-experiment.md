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
- Module A: `EHA-v2S-scope-diagnostic`
  - seed `7319`
  - 120 episodes
  - no retrieval; 4-8 relevant docs are provided directly
  - compares `evidence_graph_v3` and `evidence_diagnostics_v1`
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

The heuristic gate passed and wrote 864 predictions.

## API Run

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

The `openai/gpt-4o-mini` Phase 2S API run completed, but the Phase 2S gate failed.

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

Do not start the larger Phase 3 or multi-model main experiment from this state. The next repair should focus on claim-verdict calibration inside Module A, no-primary precision, contaminated citation suppression for `hygienic_combo_top8`, and active-tool harm in Module C.

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
