# Matrix Paper Consolidation Pack

## 1. Seed-Cluster Confidence Intervals

| model | strategy | difficulty | n | cluster_count | escape_rate | escape_rate_cluster_ci_low | escape_rate_cluster_ci_high | claim_accuracy | claim_accuracy_cluster_ci_low | claim_accuracy_cluster_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | hygienic_combo | L3 | 72 | 3 | 0.931 | 0.875 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | hygienic_combo | L4 | 72 | 3 | 0.903 | 0.875 | 0.917 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | hygienic_combo | L5 | 72 | 3 | 0.861 | 0.833 | 0.875 | 0.986 | 0.958 | 1.000 |
| openai/gpt-4o-mini | naive_bm25 | L3 | 72 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | naive_bm25 | L4 | 72 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-4o-mini | naive_bm25 | L5 | 72 | 3 | 0.028 | 0.000 | 0.042 | 0.319 | 0.250 | 0.375 |
| openai/gpt-4o-mini | primary_preserve | L3 | 72 | 3 | 0.875 | 0.792 | 0.958 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | primary_preserve | L4 | 72 | 3 | 0.917 | 0.833 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | primary_preserve | L5 | 72 | 3 | 0.958 | 0.958 | 0.958 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L3 | 72 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L4 | 72 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L5 | 72 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L3 | 72 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L4 | 72 | 3 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L5 | 72 | 3 | 0.167 | 0.167 | 0.167 | 0.694 | 0.625 | 0.750 |
| openai/gpt-5.4-mini | primary_preserve | L3 | 72 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | primary_preserve | L4 | 72 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | primary_preserve | L5 | 72 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## 2. Prompt v1.1 + Hygiene Preflight

| prompt_version | strategy | difficulty | n | escape_rate | claim_accuracy | contaminated_citation_rate | generated_lore_overclaim_rate | over_abstention_rate | has_required_supporting_evidence | clean_supporting_evidence | primary_in_context | primary_cited |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| claim_first_citation_v1 | hygienic_combo | L0 | 24 | 0.667 | 1.000 | 0.000 | 0.000 | 0.000 | 0.667 | 1.000 | 1.000 | 0.667 |
| claim_first_citation_v1 | hygienic_combo | L1 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1 | hygienic_combo | L2 | 24 | 0.833 | 1.000 | 0.000 | 0.000 | 0.000 | 0.833 | 1.000 | 1.000 | 0.833 |
| claim_first_citation_v1 | hygienic_combo | L3 | 24 | 0.917 | 1.000 | 0.000 | 0.000 | 0.000 | 0.917 | 1.000 | 1.000 | 0.917 |
| claim_first_citation_v1 | hygienic_combo | L4 | 24 | 0.917 | 1.000 | 0.000 | 0.000 | 0.000 | 0.917 | 1.000 | 1.000 | 0.917 |
| claim_first_citation_v1 | hygienic_combo | L5 | 24 | 0.792 | 0.958 | 0.167 | 0.042 | 0.000 | 0.958 | 0.833 | 0.000 | 0.000 |
| claim_first_citation_v1 | primary_preserve | L0 | 24 | 0.792 | 1.000 | 0.000 | 0.000 | 0.000 | 0.792 | 1.000 | 1.000 | 0.792 |
| claim_first_citation_v1 | primary_preserve | L1 | 24 | 0.958 | 1.000 | 0.000 | 0.000 | 0.000 | 0.958 | 1.000 | 1.000 | 0.958 |
| claim_first_citation_v1 | primary_preserve | L2 | 24 | 0.833 | 1.000 | 0.000 | 0.000 | 0.000 | 0.833 | 1.000 | 1.000 | 0.833 |
| claim_first_citation_v1 | primary_preserve | L3 | 24 | 0.875 | 1.000 | 0.000 | 0.000 | 0.000 | 0.875 | 1.000 | 1.000 | 0.875 |
| claim_first_citation_v1 | primary_preserve | L4 | 24 | 0.958 | 1.000 | 0.000 | 0.000 | 0.000 | 0.958 | 1.000 | 1.000 | 0.958 |
| claim_first_citation_v1 | primary_preserve | L5 | 24 | 0.875 | 1.000 | 0.104 | 0.000 | 0.000 | 1.000 | 0.875 | 0.000 | 0.000 |
| claim_first_citation_v1_1 | hygienic_combo | L0 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | hygienic_combo | L1 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | hygienic_combo | L2 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | hygienic_combo | L3 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | hygienic_combo | L4 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | hygienic_combo | L5 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| claim_first_citation_v1_1 | primary_preserve | L0 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | primary_preserve | L1 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | primary_preserve | L2 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | primary_preserve | L3 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | primary_preserve | L4 | 24 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| claim_first_citation_v1_1 | primary_preserve | L5 | 24 | 0.958 | 0.958 | 0.000 | 0.042 | 0.000 | 0.958 | 1.000 | 0.000 | 0.000 |

## 3. L4 Primary Recovery Audit

| model | strategy | prompt | retriever | n | primary_in_context | primary_cited | primary_ignored | claim_accuracy | escape_rate | contaminated_citation_rate | mean_best_primary_context_rank |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | claim_first_citation_v1 | bm25_top8 | 24 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.208 |  |
| openai/gpt-4o-mini | hygienic_combo | claim_first_citation_v1 | hygienic_combo_top8 | 24 | 1.000 | 0.917 | 0.083 | 1.000 | 0.917 | 0.000 | 1.000 |
| openai/gpt-4o-mini | naive_bm25 | simple_answer_v1 | bm25_top8 | 24 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |  |
| openai/gpt-4o-mini | primary_preserve | claim_first_citation_v1 | primary_preserve_top8 | 24 | 1.000 | 0.958 | 0.042 | 1.000 | 0.958 | 0.000 | 1.000 |
| openai/gpt-5-mini | careful_bm25 | claim_first_citation_v1 | bm25_top8 | 24 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |  |
| openai/gpt-5-mini | hygienic_combo | claim_first_citation_v1 | hygienic_combo_top8 | 24 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| openai/gpt-5-mini | naive_bm25 | simple_answer_v1 | bm25_top8 | 24 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |  |
| openai/gpt-5-mini | primary_preserve | claim_first_citation_v1 | primary_preserve_top8 | 24 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| openai/gpt-5.4-mini | careful_bm25 | claim_first_citation_v1 | bm25_top8 | 24 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.042 |  |
| openai/gpt-5.4-mini | hygienic_combo | claim_first_citation_v1 | hygienic_combo_top8 | 24 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | simple_answer_v1 | bm25_top8 | 24 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |  |
| openai/gpt-5.4-mini | primary_preserve | claim_first_citation_v1 | primary_preserve_top8 | 24 | 1.000 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 1.000 |

## 4. New API Cost

```json
{
  "aborted": false,
  "spent_usd": 0.084495,
  "record_cost_usd": 0.084495,
  "source_reports": [
    {
      "aborted": false,
      "record_cost_usd": 0.084495,
      "spent_usd": 0.084495,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    }
  ]
}
```
