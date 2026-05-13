# EHA Phase 2 Experiment

This file records the Phase 2 pilot implemented from `/Users/chenmohan/Downloads/ficciones-research-0512-4.md`.

Phase 2 moves the benchmark from final-answer prompt hygiene to retrieval-stage hygiene and active verification. The current implementation is a pilot-ready harness, not the full multi-model API run.

## Implemented Scope

- Dataset v2 with 120 generated episodes and seed `5252`.
- Verdict schema v2: `claim_verdict` plus `scope_tag`; top-level `mixed` is no longer used in Phase 2 tasks.
- Five retrievers:
  - `bm25_top8`
  - `bm25_top12`
  - `primary_preserve_top8`
  - `heuristic_root_dedup_top8`
  - `oracle_root_dedup_top8`
- Retrieval-stage metrics:
  - `primary_recall_at_k`
  - `gold_evidence_recall_at_k`
  - `contaminant_fraction_at_k`
  - `unique_upstream_roots_at_k`
  - `source_type_entropy_at_k`
  - `primary_rank`
  - `pollutant_saturation_at_k`
- Corpus-only verification tools:
  - `trace_citation`
  - `request_primary_record`
  - `compare_versions`
  - `search_contradictions`
- Phase 2 scoring:
  - Phase 1 answer/evidence metrics retained where applicable.
  - New metrics include `escape_rate`, `primary_recovery_rate`, `valid_primary_support_rate`, `laundered_support_rate`, tool parse/use metrics, and `time_to_primary`.
- Pilot gate with the seven checks listed in the research memo.

`oracle_root_dedup_top8` is a diagnostic upper bound. It uses hidden upstream roots and is not a deployable retriever.

## Generated Data

Full Phase 2 dataset:

```bash
uv run eha-generate-v2 --episodes 120 --seed 5252 --out-dir data/phase2
```

Pilot dataset:

```bash
uv run eha-generate-v2 --pilot --seed 5252 --out-dir data/phase2-pilot
```

Current generated counts:

- `data/phase2/tasks.jsonl`: 120 tasks
- `data/phase2/documents.jsonl`: 1753 documents
- `data/phase2-pilot/tasks.jsonl`: 24 tasks
- `data/phase2-pilot/documents.jsonl`: 356 documents

## Pilot Run

The current pilot run uses the deterministic `heuristic-sim` backend to validate the Phase 2 data, retrievers, tools, scoring, and report pipeline without spending API budget.

```bash
uv run eha-phase2 \
  --data-dir data/phase2-pilot \
  --backend heuristic \
  --models heuristic-sim \
  --out-dir results/runs/phase2-pilot-heuristic
```

Report command:

```bash
uv run eha-report-v2 \
  --data-dir data/phase2-pilot \
  --run-dir results/runs/phase2-pilot-heuristic \
  --out-dir results/reports-phase2-pilot-heuristic
```

Main report:

```text
results/reports-phase2-pilot-heuristic/summary.md
```

## Pilot Gate Result

The heuristic pilot gate passed.

```json
{
  "clean_control_bm25_accuracy": 1.0,
  "false_consensus_bm25_wrong_answer_rate": 0.75,
  "bm25_primary_recall": 0.75,
  "primary_preserve_primary_recall": 1.0,
  "primary_recall_delta": 0.25,
  "bm25_false_consensus_pollutant_saturation": 0.6875,
  "oracle_false_consensus_pollutant_saturation": 0.125,
  "pollutant_saturation_delta": 0.5625,
  "mixed_source_v2_accuracy": 1.0,
  "tool_agent_json_parse_success": 1.0,
  "tool_outputs_leak_hidden_labels": false
}
```

The pilot produced:

- `results/runs/phase2-pilot-heuristic/predictions.jsonl`: 168 predictions
- `results/runs/phase2-pilot-heuristic/retrieval_metrics.csv`: 120 retrieval metric rows plus header

## API Pilot Result

The `openai/gpt-4o-mini` API pilot has been run on the same 24-episode pilot set.

```bash
uv run eha-phase2 \
  --data-dir data/phase2-pilot \
  --backend api \
  --models openai/gpt-4o-mini \
  --out-dir results/runs/phase2-pilot-gpt4omini \
  --max-output-tokens 3000 \
  --timeout-s 180
```

Report:

```text
results/reports-phase2-pilot-gpt4omini/summary.md
```

The API pilot did not pass the gate. The failed check was:

```text
false_consensus_bm25_wrong_answer_rate_at_least_0_60
```

Observed value:

```text
false_consensus_bm25_wrong_answer_rate = 0.25
```

Other gate checks passed:

- clean-control BM25 accuracy was `1.0`.
- primary-preserve improved false-consensus primary recall from `0.75` to `1.0`.
- oracle root dedup reduced false-consensus pollutant saturation from `0.6875` to `0.125`.
- `mixed_source_corruption_v2` no longer collapsed to all-zero accuracy.
- tool-agent parse success was `1.0`.
- tool outputs did not leak hidden labels.

The API pilot cost report:

```json
{
  "record_cost_usd": 0.061351,
  "spent_usd": 0.067071
}
```

Do not start the full 120-episode, multi-model run from this dataset yet. The next step is to strengthen the false-consensus pilot condition or revise the gate so that BM25 baseline difficulty matches the Phase 2 research question.

## API Pilot Command Template

Use this after reviewing the heuristic pilot outputs. The API client reads only `LLM_API_KEY` and `LLM_BASE_URL`.

```bash
uv run eha-phase2 \
  --data-dir data/phase2-pilot \
  --backend api \
  --models openai/gpt-4o-mini \
  --out-dir results/runs/phase2-pilot-gpt4omini \
  --soft-cap-usd 100 \
  --hard-cap-usd 250 \
  --abort-cap-usd 300
```
