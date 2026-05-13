# eha-mvp

Epistemic Hygiene Arena MVP is a small, reproducible benchmark for testing
agent behavior in polluted synthetic information ecosystems. It is derived from
`epistemic-hygiene-arena-preprint.md` and the 2026-05-12 research memo.

The first experiment tests a narrow claim:

> In polluted information ecosystems, top-k RAG and naive citation prompting can
> turn bad evidence into confident answers; source-independence and
> evidence-graph prompts should reduce contaminated citation and false-consensus
> susceptibility.

## Scope

The MVP intentionally avoids real web search, external embeddings, and training.
It uses deterministic fictional company episodes and local BM25 retrieval.

Default dataset:

| Episode type | Count | Purpose |
| --- | ---: | --- |
| `clean_control` | 10 | Check the task is not only a trap |
| `false_consensus` | 15 | Test whether repeated sources are mistaken for independent evidence |
| `citation_laundering` | 10 | Test whether citation chains actually support the claim |
| `temporal_pollution` | 10 | Test whether stale sources are rejected |
| `mixed_source_corruption` | 10 | Test claim-level evidence use inside otherwise plausible sources |
| `halupedia_trap` | 5 | Test generated-lore / query-induced pollution |

Each episode has one investigation question, 12-18 visible documents, hidden
gold verdict, hidden contamination labels, and a hidden source dependency graph.

## Quick Start

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
python3 -m eha.generate_corpus --episodes 60 --seed 4242 --out-dir data/generated
python3 -m eha.run_eval --data-dir data/generated --backend heuristic --pilot --out-dir results/runs/pilot
python3 -m eha.report --data-dir data/generated --run-dir results/runs/pilot --out-dir results/reports
pytest
```

The heuristic backend is only a deterministic smoke-test backend for validating
the benchmark plumbing. Use the API backend for actual model claims:

```bash
python3 -m eha.run_eval \
  --data-dir data/generated \
  --backend api \
  --models gpt-5-mini,gpt-5.4-mini \
  --strategies topk_rag,citation_prompt,source_independence_prompt,evidence_graph_prompt \
  --out-dir results/runs/main
```

API mode reads `LLM_API_KEY` and `LLM_BASE_URL` from the environment or
`~/.zshrc`, uses the official `openai` Python SDK against that endpoint, writes
every prompt/response/usage record, and stops before exceeding the configured
budget caps.

## Deliverables

- `data/generated/manifest.json`
- `data/generated/tasks.jsonl`
- `data/generated/documents.jsonl`
- `data/generated/gold_graph.jsonl`
- `results/runs/*/predictions.jsonl`
- `results/runs/*/cost_report.json`
- `results/reports/summary.md`
- `results/reports/metrics_by_strategy.csv`
- `results/reports/metrics_by_model.csv`
- `results/reports/false_consensus.csv`
- `results/reports/failure_cases.md`
- `results/reports/cost_report.json`

## Pilot Gate

Run the 12-episode pilot before a full model run. The gate checks:

1. Clean-control top-k accuracy is at least `0.65`.
2. False-consensus top-k or citation prompting produces at least three polluted
   mistakes.
3. Source-independence and evidence-graph strategies are not trivially perfect.
4. JSON parse success is at least `0.95`.
5. Every episode has at least one primary source and one plausible pollutant.
