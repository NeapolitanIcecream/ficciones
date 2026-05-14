# EHA Validity Pass Human Audit Summary

## Method and Inputs
Audited all 80 rows from `human_audit_sample.jsonl` against each row's question, gold setup, parsed prediction, scorer decision, cited documents, and visible documents. Judgments were made at row level, with special attention to whether visible evidence was actually available to the model and whether structured support fields conflicted with the model's prose or rejected-evidence list.

Outputs produced: `human_audit_completed.jsonl`, `human_audit_completed.csv`, and this summary.

## Counts by Audit Bucket
| bucket | rows | verdict reasonable | support actually supports | contamination label reasonable | rejected evidence misclassified | generated-lore too strict | scorer agreement |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| generated_lore | 20 | yes: 20 | no: 20 | yes: 20 | yes: 14, no: 6 | no: 20 | yes: 6, uncertain: 14 |
| false_consensus | 20 | yes: 20 | uncertain: 20 | yes: 20 | yes: 20 | no: 20 | uncertain: 20 |
| buried_primary | 20 | yes: 20 | no: 8, uncertain: 12 | yes: 20 | yes: 13, no: 7 | no: 20 | no: 8, uncertain: 12 |
| active_verification | 20 | yes: 10, no: 10 | yes: 9, no: 10, uncertain: 1 | yes: 20 | yes: 1, no: 19 | no: 20 | yes: 19, uncertain: 1 |

## Overall Audit Field Counts
- `verdict_reasonable`: yes: 70, no: 10
- `supporting_evidence_actually_supports_verdict`: yes: 9, no: 38, uncertain: 33
- `contamination_label_reasonable`: yes: 80
- `rejected_evidence_misclassified_as_support`: yes: 48, no: 32
- `generated_lore_label_too_strict`: no: 80
- `scorer_agreement`: yes: 25, no: 8, uncertain: 47

## Scorer Agreement
- Agreement counts: yes: 25, no: 8, uncertain: 47.
- Agreement rate over all rows: 25/80 = 31.2%.
- Agreement rate excluding uncertain rows: 25/33 = 75.8%.
- `uncertain` mostly marks structured-field edge cases where the model reached the right verdict using primary evidence but also had a rejected contaminant/stale document in `supporting_evidence` or `selected_doc_ids`.

## Major Patterns
- `generated_lore`: All 20 rows have reasonable insufficient verdicts and the generated/repost labels look valid. The main problem is field hygiene: the cited support is generated-lore or contaminant material, and 14 rows explicitly reject or describe weak material that still appears in support/selection. No row showed the generated-lore label itself as too strict.
- `false_consensus`: All 20 rows correctly refute the below-2% recall claim using primary 3.8% records. Contaminant labels are sound because the 1.7% items visibly repeat a single upstream story. The recurring edge case is mixed support: primary records support the verdict, while the contaminant root or repost is also listed as support and often rejected elsewhere.
- `buried_primary`: The 12 rows with visible primary records behave like false-consensus rows: correct refutation but polluted support/selection. The 8 active-verification rows with no visible primary records are important scorer edge cases; the gold setup names hidden primary records, but the visible packet contains only contaminant reposts, so an insufficient verdict is reasonable from the supplied evidence.
- `active_verification`: Ten rows are parse failures and should remain automatic failures. The parsed successful rows generally use primary records correctly for supplier-audit support or lapsed-certificate refutation. One conflicting-evidence row has mixed support because stale material is included alongside primary refutation evidence.

## Scorer Edge Cases
- The largest edge case is rejected/weak evidence counted as support. This appears in 48 rows, especially false-consensus and buried-primary cases where the prose rejects the contaminant chain but the structured support/selected fields still include it.
- Hidden-primary buried rows should not be treated as simple belief errors without qualification. The scorer marks them belief-incorrect against gold `refuted`, but the visible evidence available in the row does not contain the primary contradiction.
- Empty `supporting_evidence` in several parsed supported active-verification rows is not necessarily a substantive support failure because selected/cited primary records and the answer text provide the support. Those rows were judged reasonable when primary records were visible and used in the answer.
- Parse failures are clean automatic failures: no substantive answer, actions, support, or rejection fields are available to audit.

## Limitations and Use in Paper
This is a single-pass human audit over synthetic packets, not an independent fact-check outside the provided setup. It should be used in the paper as a validity check on scorer behavior and evidence-hygiene failure modes, especially to qualify automatic evidence-cleanliness penalties and hidden-primary active-verification cases. It should not be presented as estimating real-world factual accuracy beyond the synthetic EHA environment.
