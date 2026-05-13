# EHA Matrix Escape Table v1

## 1. Main Escape-Rate Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | 0.375 | 0.417 | 0.375 | 0.708 | 0.000 | 0.875 | 0.458 |
| openai/gpt-4o-mini | hygienic_combo | 0.667 | 1.000 | 0.833 | 0.917 | 0.917 | 0.792 | 0.854 |
| openai/gpt-4o-mini | naive_bm25 | 1.000 | 1.000 | 0.917 | 0.958 | 0.000 | 0.000 | 0.646 |
| openai/gpt-4o-mini | primary_preserve | 0.792 | 0.958 | 0.833 | 0.875 | 0.958 | 0.875 | 0.882 |
| openai/gpt-5-mini | careful_bm25 | 0.958 | 0.958 | 0.417 | 0.958 | 0.000 | 1.000 | 0.715 |
| openai/gpt-5-mini | hygienic_combo | 1.000 | 0.958 | 0.583 | 0.958 | 1.000 | 1.000 | 0.917 |
| openai/gpt-5-mini | naive_bm25 | 1.000 | 0.917 | 0.000 | 0.875 | 0.000 | 0.000 | 0.465 |
| openai/gpt-5-mini | primary_preserve | 0.958 | 0.958 | 0.333 | 1.000 | 1.000 | 1.000 | 0.875 |
| openai/gpt-5.4-mini | careful_bm25 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.833 |
| openai/gpt-5.4-mini | hygienic_combo | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.083 | 0.681 |
| openai/gpt-5.4-mini | primary_preserve | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## 2. Claim Accuracy Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.833 |
| openai/gpt-4o-mini | hygienic_combo | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.958 | 0.993 |
| openai/gpt-4o-mini | naive_bm25 | 1.000 | 1.000 | 1.000 | 0.958 | 0.000 | 0.375 | 0.722 |
| openai/gpt-4o-mini | primary_preserve | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | careful_bm25 | 0.958 | 1.000 | 0.958 | 1.000 | 0.000 | 1.000 | 0.819 |
| openai/gpt-5-mini | hygienic_combo | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | naive_bm25 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.833 |
| openai/gpt-5-mini | primary_preserve | 0.958 | 1.000 | 0.917 | 1.000 | 1.000 | 1.000 | 0.979 |
| openai/gpt-5.4-mini | careful_bm25 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.833 |
| openai/gpt-5.4-mini | hygienic_combo | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.625 | 0.771 |
| openai/gpt-5.4-mini | primary_preserve | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## 3. Contaminated Citation Table

| model | strategy | L0 | L1 | L2 | L3 | L4 | L5 | avg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | 0.000 | 0.000 | 0.000 | 0.000 | 0.208 | 0.115 | 0.054 |
| openai/gpt-4o-mini | hygienic_combo | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.167 | 0.028 |
| openai/gpt-4o-mini | naive_bm25 | 0.000 | 0.000 | 0.028 | 0.000 | 1.000 | 0.990 | 0.336 |
| openai/gpt-4o-mini | primary_preserve | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.104 | 0.017 |
| openai/gpt-5-mini | careful_bm25 | 0.000 | 0.000 | 0.181 | 0.000 | 0.000 | 0.000 | 0.030 |
| openai/gpt-5-mini | hygienic_combo | 0.000 | 0.000 | 0.139 | 0.000 | 0.000 | 0.000 | 0.023 |
| openai/gpt-5-mini | naive_bm25 | 0.000 | 0.042 | 0.333 | 0.125 | 1.000 | 0.979 | 0.413 |
| openai/gpt-5-mini | primary_preserve | 0.000 | 0.000 | 0.194 | 0.000 | 0.000 | 0.000 | 0.032 |
| openai/gpt-5.4-mini | careful_bm25 | 0.000 | 0.000 | 0.000 | 0.000 | 0.042 | 0.000 | 0.007 |
| openai/gpt-5.4-mini | hygienic_combo | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 | 0.917 | 0.319 |
| openai/gpt-5.4-mini | primary_preserve | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## 4. Abstention Quality On L5

| model | strategy | difficulty | n | abstention_quality | generated_lore_overclaim_rate |
| --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L5 | 24 | 0.958 | 0.042 |
| openai/gpt-4o-mini | naive_bm25 | L5 | 24 | 0.375 | 0.625 |
| openai/gpt-4o-mini | primary_preserve | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5-mini | careful_bm25 | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5-mini | hygienic_combo | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5-mini | naive_bm25 | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5-mini | primary_preserve | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | careful_bm25 | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L5 | 24 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L5 | 24 | 0.625 | 0.375 |
| openai/gpt-5.4-mini | primary_preserve | L5 | 24 | 1.000 | 0.000 |

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
| openai/gpt-5-mini | careful_bm25 | L0 | 24 | 0.958 | 0.958 | 0.000 |
| openai/gpt-5-mini | careful_bm25 | L1 | 24 | 0.958 | 1.000 | 0.000 |
| openai/gpt-5-mini | careful_bm25 | L2 | 24 | 0.417 | 0.958 | 0.181 |
| openai/gpt-5-mini | careful_bm25 | L3 | 24 | 0.958 | 1.000 | 0.000 |
| openai/gpt-5-mini | careful_bm25 | L4 | 24 | 0.000 | 0.000 | 0.000 |
| openai/gpt-5-mini | careful_bm25 | L5 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | hygienic_combo | L0 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | hygienic_combo | L1 | 24 | 0.958 | 1.000 | 0.000 |
| openai/gpt-5-mini | hygienic_combo | L2 | 24 | 0.583 | 1.000 | 0.139 |
| openai/gpt-5-mini | hygienic_combo | L3 | 24 | 0.958 | 1.000 | 0.000 |
| openai/gpt-5-mini | hygienic_combo | L4 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | hygienic_combo | L5 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | naive_bm25 | L0 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | naive_bm25 | L1 | 24 | 0.917 | 1.000 | 0.042 |
| openai/gpt-5-mini | naive_bm25 | L2 | 24 | 0.000 | 1.000 | 0.333 |
| openai/gpt-5-mini | naive_bm25 | L3 | 24 | 0.875 | 1.000 | 0.125 |
| openai/gpt-5-mini | naive_bm25 | L4 | 24 | 0.000 | 0.000 | 1.000 |
| openai/gpt-5-mini | naive_bm25 | L5 | 24 | 0.000 | 1.000 | 0.979 |
| openai/gpt-5-mini | primary_preserve | L0 | 24 | 0.958 | 0.958 | 0.000 |
| openai/gpt-5-mini | primary_preserve | L1 | 24 | 0.958 | 1.000 | 0.000 |
| openai/gpt-5-mini | primary_preserve | L2 | 24 | 0.333 | 0.917 | 0.194 |
| openai/gpt-5-mini | primary_preserve | L3 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | primary_preserve | L4 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | primary_preserve | L5 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | careful_bm25 | L0 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | careful_bm25 | L1 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | careful_bm25 | L2 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | careful_bm25 | L3 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | careful_bm25 | L4 | 24 | 0.000 | 0.000 | 0.042 |
| openai/gpt-5.4-mini | careful_bm25 | L5 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L0 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L1 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L2 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L3 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L4 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L5 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L0 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L1 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L2 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L3 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L4 | 24 | 0.000 | 0.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L5 | 24 | 0.083 | 0.625 | 0.917 |
| openai/gpt-5.4-mini | primary_preserve | L0 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | primary_preserve | L1 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | primary_preserve | L2 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | primary_preserve | L3 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | primary_preserve | L4 | 24 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | primary_preserve | L5 | 24 | 1.000 | 1.000 | 0.000 |

## 6. Weaker Model Plus Hygiene Vs Stronger Model Plus Naive Retrieval

| comparison | left_escape_rate | right_escape_rate | delta_left_minus_right |
| --- | --- | --- | --- |
| openai/gpt-4o-mini + hygienic_combo vs openai/gpt-5-mini + naive_bm25 | 0.854 | 0.465 | 0.389 |
| openai/gpt-4o-mini + hygienic_combo vs openai/gpt-5.4-mini + naive_bm25 | 0.854 | 0.681 | 0.174 |
| openai/gpt-5-mini + hygienic_combo vs openai/gpt-4o-mini + naive_bm25 | 0.917 | 0.646 | 0.271 |
| openai/gpt-5-mini + hygienic_combo vs openai/gpt-5.4-mini + naive_bm25 | 0.917 | 0.681 | 0.236 |
| openai/gpt-5.4-mini + hygienic_combo vs openai/gpt-4o-mini + naive_bm25 | 1.000 | 0.646 | 0.354 |
| openai/gpt-5.4-mini + hygienic_combo vs openai/gpt-5-mini + naive_bm25 | 1.000 | 0.465 | 0.535 |

## 7. Model Scale Vs Information Hygiene

Compare `hygienic_combo` rows against `naive_bm25` rows at the same or stronger model. The CSV artifacts keep this analysis machine-readable.

## 8. Qualitative Failure Cases

See `failure_cases_matrix_v1.md` for at least 12 scored cases when available.

## 9. Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 2.676095,
  "spent_usd": 2.676095,
  "soft_cap_usd": 75.0,
  "hard_cap_usd": 200.0,
  "abort_cap_usd": 300.0,
  "source_runs": [
    "matrix-v1-gpt4omini",
    "matrix-v1-gpt5mini",
    "matrix-v1-gpt54mini"
  ],
  "source_cost_reports": [
    {
      "aborted": false,
      "record_cost_usd": 0.164107,
      "spent_usd": 0.164107,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 1.338193,
      "spent_usd": 1.338193,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 1.173795,
      "spent_usd": 1.173795,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    }
  ]
}
```

## 10. Diagnostics Note

Evidence diagnostics are secondary in Matrix v1 and are not used as a blocking gate. The primary metrics are escape rate, claim accuracy, contaminated citation rate, abstention quality, and overconfident wrong rate.
