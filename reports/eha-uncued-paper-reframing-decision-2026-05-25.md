# EHA-Uncued Core-Claim Overnight Results

Date: 2026-05-25

## 1. Executive judgment

Recommendation: `substantially_reframe`.

The old belief/operation separation should be treated as a diagnostic lens, not as the central scientific claim. The stronger paper frame is polluted evidence ecologies, provenance discipline, source independence, and verification behavior under explicit scorer contracts.

## 2. What the old separation claim can still support

- Correct final answers can coexist with dirty support, weak evidence selection, or incomplete verification paths.
- Generated-lore rows are useful stress tests for source-independence and pollutant rejection behavior.
- The gap remains useful for triage when reported alongside failure decomposition and sensitivity analyses.

## 3. What the old separation claim cannot support

- It does not prove schema-independent cognitive separation.
- It does not establish open-web ecological validity beyond this synthetic pilot.
- It does not support production model ranking.

## 4. Failure decomposition results

- Rows analyzed: `680`
- Operational failures: `433`
- Belief-correct operational failures: `361`
- Other/unclassified rate: `0.0`

## 5. Support-field ambiguity sensitivity results

- Target generated-lore candidate rows: `72`
- Strict failures becoming prose-aware passes: `71`
- Target gap closed share: `0.9861111111111112`
- Interpretation: `gap_mostly_support_field_artifact`

## 6. Decomposed-schema rerun results

- Schema rows: `144`
- Paired deltas: `72`
- Mean delta operational/contract success: `0.013888888888888888`
- Mean delta polluted-in-support: `0.0`

## 7. Positive evidence-contract results

- Mean composite contract: `0.41041666666666665`
- Mean operational escape: `0.3770833333333333`

## 8. Shortcut baseline and ecological validity boundary

- Overall model minus best-shortcut margin: `0.035416666666666666`
- Treat shortcut competitiveness as a validity boundary for the synthetic diagnostic design, not as a solved-problem claim.

## 9. Data sanity audit outcome

- Data sanity decision: `pass_with_qualifications`
- P0 issues: `0`
- P1 issues: `26`

## 10. Recommended paper claims

- Center polluted evidence ecologies and provenance discipline.
- Present belief/operation gaps as diagnostic summaries with named schema/scorer sensitivities.
- Report failure decomposition, support ambiguity sensitivity, decomposed-schema results, and shortcut boundaries together.

## 11. Required paper edits

- Remove any abstract/introduction language implying schema-independent separation.
- Add a results subsection for failure decomposition by model, condition, and family.
- Add a methods/limitations subsection explaining support-field ambiguity and synthetic timestamp limitations.
- Move leaderboard-style language to appendix or remove it.

## 12. Remaining risks before submission

- Prose-aware rescoring remains heuristic and local-audit-only.
- Synthetic chronology should be described as non-evidential unless repaired in the dataset.
- Model ranking remains descriptive unless uncertainty intervals support stronger wording.

## 13. Exact commands to reproduce this overnight run

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-uncued-failure-decomposition --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 --robustness-run-dir results/reports-eha-uncued-robustness-2026-05-25 --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
uv run eha-uncued-support-ambiguity --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 --dataset-dir data/uncued-pilot-v1 --decomposition-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
uv run eha-uncued-positive-contract --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 --dataset-dir data/uncued-pilot-v1 --support-ambiguity-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
uv run eha-plan-uncued-core-claim-schema-rerun --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --seed 20260525
uv run eha-run-uncued-core-claim-schema-rerun --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --hard-cap-usd 20.00
uv run eha-report-uncued-core-claim-schema-rerun --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --dataset-dir data/uncued-pilot-v1
uv run eha-score-uncued-baselines --dataset-dir data/uncued-pilot-v1 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
uv run eha-uncued-data-sanity --dataset-dir data/uncued-pilot-v1 --pilot-run-dir results/reports-eha-uncued-pilot-2026-05-22 --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25
uv run eha-report-uncued-core-claim-overnight --out-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --reports-dir ../reports
uv run eha-verify-uncued-core-claim-overnight --run-dir results/reports-eha-uncued-core-claim-overnight-2026-05-25 --reports-dir ../reports
```
