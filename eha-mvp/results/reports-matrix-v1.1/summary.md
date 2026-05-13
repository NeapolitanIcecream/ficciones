# Matrix v1.1 Robustness Pack

## 1. Multi-Seed Critical Replication

| model | strategy | difficulty | n | seed_count | escape_rate | escape_rate_ci_low | escape_rate_ci_high | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | hygienic_combo | L3 | 72 | 3 | 0.931 | 0.875 | 0.986 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L4 | 72 | 3 | 0.903 | 0.833 | 0.972 | 0.000 |
| openai/gpt-4o-mini | hygienic_combo | L5 | 72 | 3 | 0.861 | 0.778 | 0.931 | 0.125 |
| openai/gpt-4o-mini | naive_bm25 | L3 | 72 | 3 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-4o-mini | naive_bm25 | L4 | 72 | 3 | 0.000 | 0.000 | 0.000 | 1.000 |
| openai/gpt-4o-mini | naive_bm25 | L5 | 72 | 3 | 0.028 | 0.000 | 0.069 | 0.854 |
| openai/gpt-4o-mini | primary_preserve | L3 | 72 | 3 | 0.875 | 0.792 | 0.944 | 0.000 |
| openai/gpt-4o-mini | primary_preserve | L4 | 72 | 3 | 0.917 | 0.847 | 0.972 | 0.000 |
| openai/gpt-4o-mini | primary_preserve | L5 | 72 | 3 | 0.958 | 0.903 | 1.000 | 0.036 |
| openai/gpt-5.4-mini | hygienic_combo | L3 | 72 | 3 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L4 | 72 | 3 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | hygienic_combo | L5 | 72 | 3 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L3 | 72 | 3 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L4 | 72 | 3 | 0.000 | 0.000 | 0.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L5 | 72 | 3 | 0.167 | 0.083 | 0.250 | 0.819 |
| openai/gpt-5.4-mini | primary_preserve | L3 | 72 | 3 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | primary_preserve | L4 | 72 | 3 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | primary_preserve | L5 | 72 | 3 | 1.000 | 1.000 | 1.000 | 0.000 |

## 2. Noisy Metadata / Source Spoofing

| metadata_noise | model | strategy | difficulty | n | escape_rate | contaminated_citation_rate | generated_lore_overclaim_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | openai/gpt-5-mini | hygienic_combo | L3 | 24 | 1.000 | 0.000 | 0.000 |
| 0 | openai/gpt-5-mini | hygienic_combo | L4 | 24 | 0.958 | 0.000 | 0.000 |
| 0 | openai/gpt-5-mini | hygienic_combo | L5 | 24 | 1.000 | 0.000 | 0.000 |
| 0 | openai/gpt-5-mini | primary_preserve | L3 | 24 | 0.958 | 0.000 | 0.000 |
| 0 | openai/gpt-5-mini | primary_preserve | L4 | 24 | 1.000 | 0.000 | 0.000 |
| 0 | openai/gpt-5-mini | primary_preserve | L5 | 24 | 1.000 | 0.000 | 0.000 |
| 10 | openai/gpt-5-mini | hygienic_combo | L3 | 24 | 0.875 | 0.000 | 0.000 |
| 10 | openai/gpt-5-mini | hygienic_combo | L4 | 24 | 1.000 | 0.000 | 0.000 |
| 10 | openai/gpt-5-mini | hygienic_combo | L5 | 24 | 1.000 | 0.000 | 0.000 |
| 10 | openai/gpt-5-mini | primary_preserve | L3 | 24 | 1.000 | 0.000 | 0.000 |
| 10 | openai/gpt-5-mini | primary_preserve | L4 | 24 | 0.875 | 0.000 | 0.000 |
| 10 | openai/gpt-5-mini | primary_preserve | L5 | 24 | 1.000 | 0.000 | 0.000 |
| 25 | openai/gpt-5-mini | hygienic_combo | L3 | 24 | 0.958 | 0.000 | 0.000 |
| 25 | openai/gpt-5-mini | hygienic_combo | L4 | 24 | 0.958 | 0.000 | 0.000 |
| 25 | openai/gpt-5-mini | hygienic_combo | L5 | 24 | 1.000 | 0.000 | 0.000 |
| 25 | openai/gpt-5-mini | primary_preserve | L3 | 24 | 1.000 | 0.000 | 0.000 |
| 25 | openai/gpt-5-mini | primary_preserve | L4 | 24 | 0.750 | 0.000 | 0.000 |
| 25 | openai/gpt-5-mini | primary_preserve | L5 | 24 | 1.000 | 0.000 | 0.000 |
| 50 | openai/gpt-5-mini | hygienic_combo | L3 | 24 | 0.958 | 0.000 | 0.000 |
| 50 | openai/gpt-5-mini | hygienic_combo | L4 | 24 | 0.792 | 0.000 | 0.000 |
| 50 | openai/gpt-5-mini | hygienic_combo | L5 | 24 | 1.000 | 0.000 | 0.000 |
| 50 | openai/gpt-5-mini | primary_preserve | L3 | 24 | 1.000 | 0.000 | 0.000 |
| 50 | openai/gpt-5-mini | primary_preserve | L4 | 24 | 0.333 | 0.000 | 0.000 |
| 50 | openai/gpt-5-mini | primary_preserve | L5 | 24 | 1.000 | 0.000 | 0.000 |

## 3. Escape Metric Decomposition

| model | strategy | difficulty | n | claim_correct | clean_supporting_evidence | has_required_supporting_evidence | generated_lore_abstention_ok | full_escape |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| openai/gpt-4o-mini | careful_bm25 | L0 | 24 | 1.000 | 1.000 | 0.375 | 1.000 | 0.375 |
| openai/gpt-4o-mini | careful_bm25 | L1 | 24 | 1.000 | 1.000 | 0.417 | 1.000 | 0.417 |
| openai/gpt-4o-mini | careful_bm25 | L2 | 24 | 1.000 | 1.000 | 0.375 | 1.000 | 0.375 |
| openai/gpt-4o-mini | careful_bm25 | L3 | 24 | 1.000 | 1.000 | 0.708 | 1.000 | 0.708 |
| openai/gpt-4o-mini | careful_bm25 | L4 | 24 | 0.000 | 0.792 | 0.208 | 1.000 | 0.000 |
| openai/gpt-4o-mini | careful_bm25 | L5 | 24 | 1.000 | 0.875 | 1.000 | 1.000 | 0.875 |
| openai/gpt-4o-mini | hygienic_combo | L0 | 24 | 1.000 | 1.000 | 0.667 | 1.000 | 0.667 |
| openai/gpt-4o-mini | hygienic_combo | L1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | hygienic_combo | L2 | 24 | 1.000 | 1.000 | 0.833 | 1.000 | 0.833 |
| openai/gpt-4o-mini | hygienic_combo | L3 | 24 | 1.000 | 1.000 | 0.917 | 1.000 | 0.917 |
| openai/gpt-4o-mini | hygienic_combo | L4 | 24 | 1.000 | 1.000 | 0.917 | 1.000 | 0.917 |
| openai/gpt-4o-mini | hygienic_combo | L5 | 24 | 0.958 | 0.833 | 0.958 | 0.958 | 0.792 |
| openai/gpt-4o-mini | naive_bm25 | L0 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | naive_bm25 | L1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-4o-mini | naive_bm25 | L2 | 24 | 1.000 | 0.917 | 1.000 | 1.000 | 0.917 |
| openai/gpt-4o-mini | naive_bm25 | L3 | 24 | 0.958 | 1.000 | 1.000 | 1.000 | 0.958 |
| openai/gpt-4o-mini | naive_bm25 | L4 | 24 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-4o-mini | naive_bm25 | L5 | 24 | 0.375 | 0.000 | 1.000 | 0.375 | 0.000 |
| openai/gpt-4o-mini | primary_preserve | L0 | 24 | 1.000 | 1.000 | 0.792 | 1.000 | 0.792 |
| openai/gpt-4o-mini | primary_preserve | L1 | 24 | 1.000 | 1.000 | 0.958 | 1.000 | 0.958 |
| openai/gpt-4o-mini | primary_preserve | L2 | 24 | 1.000 | 1.000 | 0.833 | 1.000 | 0.833 |
| openai/gpt-4o-mini | primary_preserve | L3 | 24 | 1.000 | 1.000 | 0.875 | 1.000 | 0.875 |
| openai/gpt-4o-mini | primary_preserve | L4 | 24 | 1.000 | 1.000 | 0.958 | 1.000 | 0.958 |
| openai/gpt-4o-mini | primary_preserve | L5 | 24 | 1.000 | 0.875 | 1.000 | 1.000 | 0.875 |
| openai/gpt-5-mini | careful_bm25 | L0 | 24 | 0.958 | 1.000 | 1.000 | 1.000 | 0.958 |
| openai/gpt-5-mini | careful_bm25 | L1 | 24 | 1.000 | 1.000 | 0.958 | 1.000 | 0.958 |
| openai/gpt-5-mini | careful_bm25 | L2 | 24 | 0.958 | 0.458 | 1.000 | 1.000 | 0.417 |
| openai/gpt-5-mini | careful_bm25 | L3 | 24 | 1.000 | 1.000 | 0.958 | 1.000 | 0.958 |
| openai/gpt-5-mini | careful_bm25 | L4 | 24 | 0.000 | 1.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | careful_bm25 | L5 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | hygienic_combo | L0 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | hygienic_combo | L1 | 24 | 1.000 | 1.000 | 0.958 | 1.000 | 0.958 |
| openai/gpt-5-mini | hygienic_combo | L2 | 24 | 1.000 | 0.583 | 1.000 | 1.000 | 0.583 |
| openai/gpt-5-mini | hygienic_combo | L3 | 24 | 1.000 | 1.000 | 0.958 | 1.000 | 0.958 |
| openai/gpt-5-mini | hygienic_combo | L4 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | hygienic_combo | L5 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | naive_bm25 | L0 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | naive_bm25 | L1 | 24 | 1.000 | 0.958 | 0.958 | 1.000 | 0.917 |
| openai/gpt-5-mini | naive_bm25 | L2 | 24 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | naive_bm25 | L3 | 24 | 1.000 | 0.875 | 1.000 | 1.000 | 0.875 |
| openai/gpt-5-mini | naive_bm25 | L4 | 24 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | naive_bm25 | L5 | 24 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5-mini | primary_preserve | L0 | 24 | 0.958 | 1.000 | 1.000 | 1.000 | 0.958 |
| openai/gpt-5-mini | primary_preserve | L1 | 24 | 1.000 | 1.000 | 0.958 | 1.000 | 0.958 |
| openai/gpt-5-mini | primary_preserve | L2 | 24 | 0.917 | 0.417 | 1.000 | 1.000 | 0.333 |
| openai/gpt-5-mini | primary_preserve | L3 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | primary_preserve | L4 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5-mini | primary_preserve | L5 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | careful_bm25 | L0 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | careful_bm25 | L1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | careful_bm25 | L2 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | careful_bm25 | L3 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | careful_bm25 | L4 | 24 | 0.000 | 0.958 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | careful_bm25 | L5 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L0 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L2 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L3 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L4 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | hygienic_combo | L5 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L0 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L2 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L3 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | naive_bm25 | L4 | 24 | 0.000 | 0.000 | 1.000 | 1.000 | 0.000 |
| openai/gpt-5.4-mini | naive_bm25 | L5 | 24 | 0.625 | 0.083 | 1.000 | 0.625 | 0.083 |
| openai/gpt-5.4-mini | primary_preserve | L0 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | primary_preserve | L1 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | primary_preserve | L2 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | primary_preserve | L3 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | primary_preserve | L4 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| openai/gpt-5.4-mini | primary_preserve | L5 | 24 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## 4. Prompt v1.1 Preflight

| prompt_version | difficulty | n | escape_rate | claim_accuracy | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- |
| claim_first_citation_v1 | L0 | 12 | 0.250 | 1.000 | 0.000 |
| claim_first_citation_v1 | L3 | 12 | 0.500 | 1.000 | 0.000 |
| claim_first_citation_v1 | L4 | 12 | 0.000 | 0.000 | 0.333 |
| claim_first_citation_v1 | L5 | 12 | 0.917 | 1.000 | 0.083 |
| claim_first_citation_v1_1 | L0 | 12 | 1.000 | 1.000 | 0.000 |
| claim_first_citation_v1_1 | L3 | 12 | 1.000 | 1.000 | 0.000 |
| claim_first_citation_v1_1 | L4 | 12 | 0.000 | 0.000 | 1.000 |
| claim_first_citation_v1_1 | L5 | 12 | 1.000 | 1.000 | 0.000 |

## 5. Cost Report

```json
{
  "aborted": false,
  "spent_usd": 2.810599,
  "record_cost_usd": 2.8106,
  "source_reports": [
    {
      "aborted": false,
      "record_cost_usd": 0.478988,
      "spent_usd": 0.478988,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 0.443036,
      "spent_usd": 0.443036,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 0.433712,
      "spent_usd": 0.433712,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 0.340801,
      "spent_usd": 0.3408,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 0.354506,
      "spent_usd": 0.354506,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 0.358463,
      "spent_usd": 0.358463,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 0.386827,
      "spent_usd": 0.386827,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    },
    {
      "aborted": false,
      "record_cost_usd": 0.014267,
      "spent_usd": 0.014267,
      "soft_cap_usd": 75.0,
      "hard_cap_usd": 200.0,
      "abort_cap_usd": 300.0
    }
  ]
}
```
