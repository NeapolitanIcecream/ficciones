# EHA MVP Summary

## Overall metrics by model and strategy
| model | strategy | n | verdict_accuracy | evidence_validity | contaminated_citation_rate | independent_evidence_score | provenance_recovery_f1 | ece |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | citation_prompt | 60 | 0.300 | 0.721 | 0.279 | 0.769 | 0.000 | 0.669 |
| openai/gpt-4o-mini | evidence_graph_prompt | 60 | 0.417 | 0.783 | 0.200 | 0.983 | 0.269 | 0.488 |
| openai/gpt-4o-mini | source_independence_prompt | 60 | 0.433 | 0.750 | 0.233 | 0.983 | 0.540 | 0.502 |
| openai/gpt-4o-mini | topk_rag | 60 | 0.433 | 0.733 | 0.267 | 0.777 | 0.000 | 0.523 |

## Metrics by model

| model | n | verdict_accuracy | contaminated_citation_rate | provenance_recovery_f1 | ece | cost_usd |
| --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | 240 | 0.396 | 0.245 | 0.202 | 0.546 | 0.000 |

## Citation prompt ablation

| strategy | verdict_accuracy | evidence_validity | contaminated_citation_rate | provenance_recovery_f1 |
| --- | --- | --- | --- | --- |
| citation_prompt | 0.300 | 0.721 | 0.279 | 0.000 |
| evidence_graph_prompt | 0.417 | 0.783 | 0.200 | 0.269 |
| source_independence_prompt | 0.433 | 0.750 | 0.233 | 0.540 |
| topk_rag | 0.433 | 0.733 | 0.267 | 0.000 |

## False consensus by duplicate count

| model | strategy | duplicate_count | n | wrong_answer_rate | mean_wrong_confidence | polluted_mistake_rate |
| --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | citation_prompt | 1 | 3 | 0.000 | 0.000 | 0.000 |
| openai/gpt-4o-mini | citation_prompt | 5 | 6 | 1.000 | 0.950 | 1.000 |
| openai/gpt-4o-mini | citation_prompt | 20 | 3 | 1.000 | 0.950 | 1.000 |
| openai/gpt-4o-mini | citation_prompt | 50 | 3 | 1.000 | 0.950 | 1.000 |
| openai/gpt-4o-mini | evidence_graph_prompt | 1 | 3 | 0.000 | 0.000 | 0.000 |
| openai/gpt-4o-mini | evidence_graph_prompt | 5 | 6 | 1.000 | 0.883 | 1.000 |
| openai/gpt-4o-mini | evidence_graph_prompt | 20 | 3 | 1.000 | 0.900 | 1.000 |
| openai/gpt-4o-mini | evidence_graph_prompt | 50 | 3 | 1.000 | 0.900 | 1.000 |
| openai/gpt-4o-mini | source_independence_prompt | 1 | 3 | 0.000 | 0.000 | 0.000 |
| openai/gpt-4o-mini | source_independence_prompt | 5 | 6 | 1.000 | 0.900 | 1.000 |
| openai/gpt-4o-mini | source_independence_prompt | 20 | 3 | 1.000 | 0.917 | 1.000 |
| openai/gpt-4o-mini | source_independence_prompt | 50 | 3 | 1.000 | 0.917 | 1.000 |
| openai/gpt-4o-mini | topk_rag | 1 | 3 | 0.000 | 0.000 | 0.000 |
| openai/gpt-4o-mini | topk_rag | 5 | 6 | 1.000 | 0.933 | 1.000 |
| openai/gpt-4o-mini | topk_rag | 20 | 3 | 1.000 | 0.933 | 1.000 |
| openai/gpt-4o-mini | topk_rag | 50 | 3 | 1.000 | 0.967 | 1.000 |

## Halupedia trap

| model | strategy | n | verdict_accuracy | qips | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | citation_prompt | 5 | 0.800 | 1.000 | 0.950 |
| openai/gpt-4o-mini | evidence_graph_prompt | 5 | 0.200 | 0.000 | 0.000 |
| openai/gpt-4o-mini | source_independence_prompt | 5 | 0.400 | 0.300 | 0.400 |
| openai/gpt-4o-mini | topk_rag | 5 | 0.600 | 0.800 | 0.800 |

## Cost and token usage

```json
{
  "aborted": false,
  "record_cost_usd": 0.073332,
  "spent_usd": 0.015826,
  "soft_cap_usd": 100.0,
  "hard_cap_usd": 250.0,
  "abort_cap_usd": 300.0
}
```
