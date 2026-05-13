# EHA MVP Summary

## Overall metrics by model and strategy
| model | strategy | n | verdict_accuracy | evidence_validity | contaminated_citation_rate | independent_evidence_score | provenance_recovery_f1 | ece |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | citation_prompt | 12 | 0.250 | 0.194 | 0.806 | 0.528 | 0.000 | 0.515 |
| heuristic-sim | evidence_graph_prompt | 12 | 0.917 | 1.000 | 0.000 | 1.000 | 0.991 | 0.314 |
| heuristic-sim | source_independence_prompt | 12 | 0.917 | 0.917 | 0.083 | 1.000 | 0.991 | 0.240 |
| heuristic-sim | topk_rag | 12 | 0.250 | 0.250 | 0.750 | 0.528 | 0.000 | 0.515 |

## Metrics by model

| model | n | verdict_accuracy | contaminated_citation_rate | provenance_recovery_f1 | ece | cost_usd |
| --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | 48 | 0.583 | 0.410 | 0.495 | 0.214 | 0.000 |

## Citation prompt ablation

| strategy | verdict_accuracy | evidence_validity | contaminated_citation_rate | provenance_recovery_f1 |
| --- | --- | --- | --- | --- |
| citation_prompt | 0.250 | 0.194 | 0.806 | 0.000 |
| evidence_graph_prompt | 0.917 | 1.000 | 0.000 | 0.991 |
| source_independence_prompt | 0.917 | 0.917 | 0.083 | 0.991 |
| topk_rag | 0.250 | 0.250 | 0.750 | 0.000 |

## False consensus by duplicate count

| model | strategy | duplicate_count | n | wrong_answer_rate | mean_wrong_confidence | polluted_mistake_rate |
| --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | citation_prompt | 1 | 1 | 1.000 | 0.730 | 1.000 |
| heuristic-sim | citation_prompt | 5 | 1 | 1.000 | 0.800 | 1.000 |
| heuristic-sim | citation_prompt | 20 | 1 | 1.000 | 0.765 | 1.000 |
| heuristic-sim | evidence_graph_prompt | 1 | 1 | 0.000 | 0.000 | 0.000 |
| heuristic-sim | evidence_graph_prompt | 5 | 1 | 0.000 | 0.000 | 0.000 |
| heuristic-sim | evidence_graph_prompt | 20 | 1 | 0.000 | 0.000 | 0.000 |
| heuristic-sim | source_independence_prompt | 1 | 1 | 0.000 | 0.000 | 0.000 |
| heuristic-sim | source_independence_prompt | 5 | 1 | 0.000 | 0.000 | 0.000 |
| heuristic-sim | source_independence_prompt | 20 | 1 | 0.000 | 0.000 | 0.000 |
| heuristic-sim | topk_rag | 1 | 1 | 1.000 | 0.730 | 1.000 |
| heuristic-sim | topk_rag | 5 | 1 | 1.000 | 0.800 | 1.000 |
| heuristic-sim | topk_rag | 20 | 1 | 1.000 | 0.765 | 1.000 |

## Halupedia trap

| model | strategy | n | verdict_accuracy | qips | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- |
| heuristic-sim | citation_prompt | 1 | 0.000 | 1.000 | 1.000 |
| heuristic-sim | evidence_graph_prompt | 1 | 1.000 | 0.000 | 0.000 |
| heuristic-sim | source_independence_prompt | 1 | 1.000 | 0.000 | 0.000 |
| heuristic-sim | topk_rag | 1 | 0.000 | 1.000 | 1.000 |

## Cost and token usage

```json
{
  "aborted": false,
  "spent_usd": 0.0,
  "soft_cap_usd": 100.0,
  "hard_cap_usd": 250.0,
  "abort_cap_usd": 300.0
}
```
