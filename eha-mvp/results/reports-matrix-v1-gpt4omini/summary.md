# EHA Matrix Escape Table v1

## 1. Main Escape-Rate Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | 0.375 | 0.417 | 0.375 | 0.708 | 0.000 | 0.875 | 0.458 |
| openai/gpt-4o-mini | hygienic_combo | 0.667 | 1.000 | 0.833 | 0.917 | 0.917 | 0.792 | 0.854 |
| openai/gpt-4o-mini | naive_bm25 | 1.000 | 1.000 | 0.917 | 0.958 | 0.000 | 0.000 | 0.646 |
| openai/gpt-4o-mini | primary_preserve | 0.792 | 0.958 | 0.833 | 0.875 | 0.958 | 0.875 | 0.882 |

## 2. Claim Accuracy Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.833 |
| openai/gpt-4o-mini | hygienic_combo | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.958 | 0.993 |
| openai/gpt-4o-mini | naive_bm25 | 1.000 | 1.000 | 1.000 | 0.958 | 0.000 | 0.375 | 0.722 |
| openai/gpt-4o-mini | primary_preserve | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## 3. Contaminated Citation Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | 0.000 | 0.000 | 0.000 | 0.000 | 0.208 | 0.115 | 0.054 |
| openai/gpt-4o-mini | hygienic_combo | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.167 | 0.028 |
| openai/gpt-4o-mini | naive_bm25 | 0.000 | 0.000 | 0.028 | 0.000 | 1.000 | 0.990 | 0.336 |
| openai/gpt-4o-mini | primary_preserve | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.104 | 0.017 |

## 4. Abstention Quality On L5

| model | strategy | difficulty | n | abstention_quality | generated_lore_overclaim_rate |
| --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L5 | 24 | 0.958 | 0.042 |
| openai/gpt-4o-mini | naive_bm25 | L5 | 24 | 0.375 | 0.625 |
| openai/gpt-4o-mini | primary_preserve | L5 | 24 | 1.000 | 0.000 |

## 5. Difficulty Curves

| model | strategy | difficulty | n | escape_rate | claim_accuracy | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | L0 | 24 | 0.375 | 1.000 | 0.000 |
| openai/gpt-4o-mini | careful_bm25 | L1 | 24 | 0.417 | 1.000 | 0.000 |
| openai/gpt-4o-mini | careful_bm25 | L2 | 24 | 0.375 | 1.000 | 0.000 |
| openai/gpt-4o-mini | careful_bm25 | L3 | 24 | 0.708 | 1.000 | 0.000 |
| openai/gpt-4o-mini | careful_bm25 | L4 | 24 | 0.000 | 0.000 | 0.208 |
| openai/gpt-4o-mini | careful_bm25 | L5 | 24 | 0.875 | 1.000 | 0.115 |
| openai/gpt-4o-mini | hygienic_combo | L0 | 24 | 0.667 | 1.000 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L1 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L2 | 24 | 0.833 | 1.000 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L3 | 24 | 0.917 | 1.000 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L4 | 24 | 0.917 | 1.000 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L5 | 24 | 0.792 | 0.958 | 0.167 |
| openai/gpt-4o-mini | naive_bm25 | L0 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-4o-mini | naive_bm25 | L1 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-4o-mini | naive_bm25 | L2 | 24 | 0.917 | 1.000 | 0.028 |
| openai/gpt-4o-mini | naive_bm25 | L3 | 24 | 0.958 | 0.958 | 0.000 |
| openai/gpt-4o-mini | naive_bm25 | L4 | 24 | 0.000 | 0.000 | 1.000 |
| openai/gpt-4o-mini | naive_bm25 | L5 | 24 | 0.000 | 0.375 | 0.990 |
| openai/gpt-4o-mini | primary_preserve | L0 | 24 | 0.792 | 1.000 | 0.000 |
| openai/gpt-4o-mini | primary_preserve | L1 | 24 | 0.958 | 1.000 | 0.000 |
| openai/gpt-4o-mini | primary_preserve | L2 | 24 | 0.833 | 1.000 | 0.000 |
| openai/gpt-4o-mini | primary_preserve | L3 | 24 | 0.875 | 1.000 | 0.000 |
| openai/gpt-4o-mini | primary_preserve | L4 | 24 | 0.958 | 1.000 | 0.000 |
| openai/gpt-4o-mini | primary_preserve | L5 | 24 | 0.875 | 1.000 | 0.104 |

## 6. Weaker Model Plus Hygiene Vs Stronger Model Plus Naive Retrieval

_No rows._

## 7. Model Scale Vs Information Hygiene

Compare `hygienic_combo` rows against `naive_bm25` rows at the same or stronger model. The CSV artifacts keep this analysis machine-readable.

## 8. Qualitative Failure Cases

See `failure_cases_matrix_v1.md` for at least 12 scored cases when available.

## 9. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.164107,
  "spent_usd": 0.164107,
  "soft_cap_usd": 75.0,
  "hard_cap_usd": 200.0,
  "abort_cap_usd": 300.0
}
```

## 10. Diagnostics Note

Evidence diagnostics are secondary in Matrix v1 and are not used as a blocking gate. The primary metrics are escape rate, claim accuracy, contaminated citation rate, abstention quality, and overconfident wrong rate.
