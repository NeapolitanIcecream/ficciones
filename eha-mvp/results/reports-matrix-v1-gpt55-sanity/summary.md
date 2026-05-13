# EHA Matrix Escape Table v1

## 1. Main Escape-Rate Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-5.5 | hygienic_combo |  |  |  | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.5 | naive_bm25 |  |  |  | 1.000 | 0.000 | 1.000 | 0.667 |
| openai/gpt-5.5 | primary_preserve |  |  |  | 1.000 | 1.000 | 1.000 | 1.000 |

## 2. Claim Accuracy Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-5.5 | hygienic_combo |  |  |  | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.5 | naive_bm25 |  |  |  | 1.000 | 0.000 | 1.000 | 0.667 |
| openai/gpt-5.5 | primary_preserve |  |  |  | 1.000 | 1.000 | 1.000 | 1.000 |

## 3. Contaminated Citation Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-5.5 | hygienic_combo |  |  |  | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5.5 | naive_bm25 |  |  |  | 0.000 | 0.083 | 0.000 | 0.028 |
| openai/gpt-5.5 | primary_preserve |  |  |  | 0.000 | 0.000 | 0.000 | 0.000 |

## 4. Abstention Quality On L5

| model | strategy | difficulty | n | abstention_quality | generated_lore_overclaim_rate |
| --- | --- | --- | --- | --- | --- |
| openai/gpt-5.5 | hygienic_combo | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5.5 | naive_bm25 | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5.5 | primary_preserve | L5 | 24 | 1.000 | 0.000 |

## 5. Difficulty Curves

| model | strategy | difficulty | n | escape_rate | claim_accuracy | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-5.5 | hygienic_combo | L3 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | hygienic_combo | L4 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | hygienic_combo | L5 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | naive_bm25 | L3 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | naive_bm25 | L4 | 24 | 0.000 | 0.000 | 0.083 |
| openai/gpt-5.5 | naive_bm25 | L5 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | primary_preserve | L3 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | primary_preserve | L4 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.5 | primary_preserve | L5 | 24 | 1.000 | 1.000 | 0.000 |

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
  "record_cost_usd": 4.257095,
  "spent_usd": 4.257095,
  "soft_cap_usd": 75.0,
  "hard_cap_usd": 200.0,
  "abort_cap_usd": 300.0
}
```

## 10. Diagnostics Note

Evidence diagnostics are secondary in Matrix v1 and are not used as a blocking gate. The primary metrics are escape rate, claim accuracy, contaminated citation rate, abstention quality, and overconfident wrong rate.
