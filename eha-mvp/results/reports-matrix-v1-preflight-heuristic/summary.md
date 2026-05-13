# EHA Matrix Escape Table v1

## Preflight Gate

```json
{
  "passed": true,
  "checks": {
    "L0_claim_accuracy_at_least_0_90": true,
    "L0_over_abstention_rate_at_most_0_10": true,
    "L3_L4_bm25_escape_below_hygienic_combo": true,
    "claim_first_ccr_not_above_evidence_graph_v3": true,
    "L5_overclaim_not_worse_than_evidence_graph_v3": true
  },
  "details": {
    "l0_claim_accuracy": 1.0,
    "l0_over_abstention_rate": 0.0,
    "l34_bm25_escape_rate": 0.5,
    "l34_hygienic_combo_escape_rate": 1.0,
    "p1_contaminated_citation_rate": 0.08333333333333333,
    "p0_contaminated_citation_rate": 0.3333333333333333,
    "l5_p1_overclaim_rate": 0.0,
    "l5_p0_overclaim_rate": 1.0
  }
}
```

## 1. Main Escape-Rate Table

_No rows._

## 2. Claim Accuracy Table

_No rows._

## 3. Contaminated Citation Table

_No rows._

## 4. Abstention Quality On L5

| model | strategy | difficulty | n | abstention_quality | generated_lore_overclaim_rate |
| --- | --- | --- | --- | --- | --- |
| heuristic-sim | claim_first_bm25 | L5 | 6 | 1.000 | 0.000 |
| heuristic-sim | claim_first_hygienic | L5 | 6 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_bm25 | L5 | 6 | 0.000 | 1.000 |
| heuristic-sim | evidence_graph_v3_hygienic | L5 | 6 | 0.000 | 1.000 |

## 5. Difficulty Curves

| model | strategy | difficulty | n | escape_rate | claim_accuracy | contaminated_citation_rate |
| --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | claim_first_bm25 | L0 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_bm25 | L1 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_bm25 | L2 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_bm25 | L3 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_bm25 | L4 | 6 | 0.000 | 0.000 | 1.000 |
| heuristic-sim | claim_first_bm25 | L5 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_hygienic | L0 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_hygienic | L1 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_hygienic | L2 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_hygienic | L3 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_hygienic | L4 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | claim_first_hygienic | L5 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_bm25 | L0 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_bm25 | L1 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_bm25 | L2 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_bm25 | L3 | 6 | 0.000 | 0.000 | 1.000 |
| heuristic-sim | evidence_graph_v3_bm25 | L4 | 6 | 0.000 | 0.000 | 1.000 |
| heuristic-sim | evidence_graph_v3_bm25 | L5 | 6 | 0.000 | 0.000 | 1.000 |
| heuristic-sim | evidence_graph_v3_hygienic | L0 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_hygienic | L1 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_hygienic | L2 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_hygienic | L3 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_hygienic | L4 | 6 | 1.000 | 1.000 | 0.000 |
| heuristic-sim | evidence_graph_v3_hygienic | L5 | 6 | 0.000 | 0.000 | 1.000 |

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
  "record_cost_usd": 0.0,
  "spent_usd": 0.0,
  "soft_cap_usd": 75.0,
  "hard_cap_usd": 200.0,
  "abort_cap_usd": 300.0
}
```

## 10. Diagnostics Note

Evidence diagnostics are secondary in Matrix v1 and are not used as a blocking gate. The primary metrics are escape rate, claim accuracy, contaminated citation rate, abstention quality, and overconfident wrong rate.
