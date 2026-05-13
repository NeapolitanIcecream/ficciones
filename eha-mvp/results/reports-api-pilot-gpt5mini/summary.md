# EHA MVP Summary

## Overall metrics by model and strategy
| model | strategy | n | verdict_accuracy | evidence_validity | contaminated_citation_rate | independent_evidence_score | provenance_recovery_f1 | ece |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-5-mini | citation_prompt | 12 | 0.750 | 1.000 | 0.000 | 1.000 | 0.812 | 0.115 |
| openai/gpt-5-mini | evidence_graph_prompt | 12 | 0.667 | 0.972 | 0.028 | 1.000 | 0.901 | 0.205 |
| openai/gpt-5-mini | source_independence_prompt | 12 | 0.750 | 0.861 | 0.139 | 0.944 | 0.957 | 0.143 |
| openai/gpt-5-mini | topk_rag | 12 | 0.667 | 0.972 | 0.028 | 1.000 | 0.774 | 0.061 |

## Metrics by model

| model | n | verdict_accuracy | contaminated_citation_rate | provenance_recovery_f1 | ece | cost_usd |
| --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-5-mini | 48 | 0.708 | 0.049 | 0.861 | 0.131 | 0.004 |

## Citation prompt ablation

| strategy | verdict_accuracy | evidence_validity | contaminated_citation_rate | provenance_recovery_f1 |
| --- | --- | --- | --- | --- |
| citation_prompt | 0.750 | 1.000 | 0.000 | 0.812 |
| evidence_graph_prompt | 0.667 | 0.972 | 0.028 | 0.901 |
| source_independence_prompt | 0.750 | 0.861 | 0.139 | 0.957 |
| topk_rag | 0.667 | 0.972 | 0.028 | 0.774 |

## False consensus by duplicate count

| model | strategy | duplicate_count | n | wrong_answer_rate | mean_wrong_confidence | polluted_mistake_rate |
| --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-5-mini | citation_prompt | 1 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | citation_prompt | 5 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | citation_prompt | 20 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | evidence_graph_prompt | 1 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | evidence_graph_prompt | 5 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | evidence_graph_prompt | 20 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | source_independence_prompt | 1 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | source_independence_prompt | 5 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | source_independence_prompt | 20 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | topk_rag | 1 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | topk_rag | 5 | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | topk_rag | 20 | 1 | 0.000 | 0.000 | 0.000 |

## Halupedia trap

| model | strategy | n | verdict_accuracy | qips | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- |
| openai/gpt-5-mini | citation_prompt | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | evidence_graph_prompt | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | source_independence_prompt | 1 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | topk_rag | 1 | 0.000 | 0.000 | 0.000 |

## Cost and token usage

```json
{
  "aborted": false,
  "spent_usd": 0.178931,
  "soft_cap_usd": 100.0,
  "hard_cap_usd": 250.0,
  "abort_cap_usd": 300.0
}
```
