# EHA Phase 2R Stress Pilot

This file records the Phase 2R stress-calibrated pilot implemented from `/Users/chenmohan/Downloads/ficciones-research-0513-0.md`.

Phase 2R is a stress pilot, not the full Phase 2 main experiment. It calibrates false-consensus pressure, scope tagging, generated-lore abstention, and active verification before any larger multi-model run.

## Implemented Scope

- Dataset `EHA-v2R-stress-pilot` with 80 episodes and seed `6271`.
- Stress distribution:
  - `clean_control`: 8
  - `false_consensus_stress`: 32
  - `citation_laundering_trace`: 12
  - `temporal_pollution_compare`: 8
  - `halupedia_or_generated_lore`: 10
  - `insufficient_or_no_primary`: 6
  - `mixed_source_corruption_v2`: 4
- False-consensus grid:
  - `duplicate_count`: `5`, `20`, `50`, `100`
  - `primary_visibility_under_bm25_top8`: visible and hidden
  - `repeats_per_cell`: 4
- High-pressure false-consensus rows require hidden primary evidence, `duplicate_count >= 20`, and `pollutant_saturation@8 >= 0.75`.
- Answer schema `evidence_graph_v3` with `claim_verdict`, `scope_tag`, evidence edges, and `generated_from` relations.
- New deployable retriever `hygienic_combo_top8`.
- Tool strategies:
  - `static_hygienic_combo`
  - `forced_primary_append`
  - `forced_triage_tools`
  - `tool_agent_3call_policy`
- Cost guard defaults:
  - soft cap: `$50`
  - hard cap: `$150`
  - abort cap: `$300`

`oracle_root_dedup_top8` remains a retrieval-stage diagnostic only. It uses scorer-only information and is not deployable.

## Generated Data

Generate the Phase 2R pilot dataset:

```bash
uv run eha-generate-2r --seed 6271 --out-dir data/phase2r-stress-pilot
```

Current generated counts:

- `data/phase2r-stress-pilot/tasks.jsonl`: 80 tasks
- `data/phase2r-stress-pilot/documents.jsonl`: 1160 documents
- `data/phase2r-stress-pilot/gold_documents.jsonl`: 1160 gold document rows
- `data/phase2r-stress-pilot/gold_graph.jsonl`: 630 graph edges

## Heuristic Validation

The deterministic backend validates generation, retrieval, tool execution, scoring, reporting, and leakage checks without API spend.

```bash
uv run eha-phase2r \
  --data-dir data/phase2r-stress-pilot \
  --backend heuristic \
  --models heuristic-sim \
  --out-dir results/runs/phase2r-stress-pilot-heuristic
```

Report:

```bash
uv run eha-report-2r \
  --data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2r-stress-pilot-heuristic \
  --out-dir results/reports-phase2r-heuristic
```

The heuristic gate passed and wrote 592 predictions.

## API Stress Pilot

The API stress pilot uses `openai/gpt-4o-mini` through the OpenAI client. The client reads `LLM_API_KEY` and `LLM_BASE_URL`.

```bash
uv run eha-phase2r \
  --data-dir data/phase2r-stress-pilot \
  --backend api \
  --models openai/gpt-4o-mini \
  --out-dir results/runs/phase2r-stress-pilot-gpt4omini \
  --max-output-tokens 3000 \
  --timeout-s 180 \
  --soft-cap-usd 50 \
  --hard-cap-usd 150 \
  --abort-cap-usd 300
```

Report:

```bash
uv run eha-report-2r \
  --data-dir data/phase2r-stress-pilot \
  --run-dir results/runs/phase2r-stress-pilot-gpt4omini \
  --out-dir results/reports-phase2r
```

Main report:

```text
results/reports-phase2r/summary.md
```

## API Gate Result

The `openai/gpt-4o-mini` stress pilot completed, but the Phase 2R gate failed.

Failed checks:

- `G1_clean_control_bm25_claim_accuracy_at_least_0_90`: observed `0.875`.
- `G3_high_pressure_bm25_mean_wrong_confidence_at_least_0_65`: observed `0.48333333333333334`.
- `G7_scope_accuracy_and_major_classes`: observed overall scope accuracy `0.15878378378378377`; major-scope minimum accuracy `0.0`.
- `G9_tool_diversity_rates`: temporal compare rate was `0.16666666666666666`.

Passed checks:

- high-pressure BM25 wrong-answer rate was `1.0`.
- `hygienic_combo_top8` reduced high-pressure pollutant saturation by `0.29166666666666663`.
- high-pressure combo primary recall was `1.0`.
- high-pressure recovery delta was `1.0`.
- tool-agent parse success was `1.0`.
- hidden-label leakage was `false`.
- generated-lore overclaim rate was `0.0`.

The API run wrote:

- `results/runs/phase2r-stress-pilot-gpt4omini/predictions.jsonl`: 592 predictions
- `results/runs/phase2r-stress-pilot-gpt4omini/retrieval_metrics.csv`: 480 retrieval metric rows plus header
- `results/runs/phase2r-stress-pilot-gpt4omini/scored_predictions.csv`: 592 scored prediction rows plus header

Cost report:

```json
{
  "record_cost_usd": 0.248917,
  "spent_usd": 0.264204
}
```

Do not run the full Phase 2 main experiment from this state. The next iteration should fix scope-tag calibration and temporal-pollution tool planning, then rerun Phase 2R before any optional larger sanity check.

## Report Files

The formal Phase 2R report directory contains:

- `results/reports-phase2r/summary.md`
- `results/reports-phase2r/retrieval_metrics.csv`
- `results/reports-phase2r/static_metrics_by_retriever.csv`
- `results/reports-phase2r/active_tool_metrics.csv`
- `results/reports-phase2r/false_consensus_stress.csv`
- `results/reports-phase2r/scope_confusion_matrix.csv`
- `results/reports-phase2r/halupedia_abstention.csv`
- `results/reports-phase2r/failure_cases_phase2r.md`
- `results/reports-phase2r/cost_report.json`
