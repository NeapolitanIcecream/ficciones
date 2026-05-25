# EHA-Uncued Phase 1.3 Robustness Mini-Suite Results

Date: 2026-05-25

This paired mini-suite checks whether the role-uncued evidence-hygiene result persists under small presentation perturbations. It is not a full robustness proof and does not claim open-web validity.

## Scope And Task Selection

- Run directory: `results/reports-eha-uncued-robustness-2026-05-25`
- Selected source tasks: 20
- Rows: 200 latest records (200 raw records)
- Models: gpt-5.5, gemini-3.1-pro-preview
- Variants: baseline_original, order_randomized, source_type_masked, prompt_paraphrase, citation_masked
- View: `neutral_metadata_visible`
- Prompt condition: `standard_answer`

## Perturbation Definitions

- `baseline_original`: normal role-uncued prompt rebuilt from the frozen slice.
- `order_randomized`: same documents, shuffled order.
- `source_type_masked`: source_type replaced with `document`.
- `prompt_paraphrase`: policy wording paraphrased, schema and evidence fixed.
- `citation_masked`: visible citations removed while document body text is preserved.

## Prompt Audit

- Prompt parity audit passed: True
- Prompt hidden-label audit passed: True
- Stored hidden-label audit passed: True

## Cost And Invocation Profile

- Projected cost: USD 3.431618
- Spent cost: USD 2.614767
- Hard cap: USD 7.0

## Aggregate Metrics By Variant And Model

| variant | model | n | parse_success | belief_correctness | operational_epistemic_escape | evidence_precision | polluted_support_rate | required_action_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_original | gemini-3.1-pro-preview | 20 | 1.000 | 0.900 | 0.250 | 0.675 | 0.300 | 0.750 |
| baseline_original | gpt-5.5 | 20 | 1.000 | 0.950 | 0.250 | 0.750 | 0.250 | 0.375 |
| citation_masked | gemini-3.1-pro-preview | 20 | 1.000 | 0.700 | 0.200 | 0.588 | 0.450 | 0.750 |
| citation_masked | gpt-5.5 | 20 | 1.000 | 1.000 | 0.450 | 0.750 | 0.250 | 0.750 |
| order_randomized | gemini-3.1-pro-preview | 20 | 1.000 | 1.000 | 0.350 | 0.763 | 0.150 | 0.375 |
| order_randomized | gpt-5.5 | 20 | 1.000 | 1.000 | 0.400 | 0.725 | 0.250 | 0.625 |
| prompt_paraphrase | gemini-3.1-pro-preview | 20 | 1.000 | 0.900 | 0.250 | 0.725 | 0.250 | 0.625 |
| prompt_paraphrase | gpt-5.5 | 20 | 1.000 | 1.000 | 0.450 | 0.750 | 0.250 | 0.750 |
| source_type_masked | gemini-3.1-pro-preview | 20 | 1.000 | 0.950 | 0.350 | 0.763 | 0.250 | 0.625 |
| source_type_masked | gpt-5.5 | 20 | 1.000 | 1.000 | 0.350 | 0.750 | 0.250 | 0.500 |

## Paired Deltas

| variant | n | delta_operational_escape | delta_belief_correctness | delta_evidence_precision | delta_polluted_support_rate | pass_to_fail_operational | fail_to_pass_operational |
| --- | --- | --- | --- | --- | --- | --- | --- |
| citation_masked | 40 | 0.075 | -0.075 | -0.047 | 0.075 | 0.050 | 0.125 |
| order_randomized | 40 | 0.125 | 0.075 | 0.013 | -0.075 | 0.025 | 0.150 |
| prompt_paraphrase | 40 | 0.100 | 0.025 | 0.025 | -0.025 | 0.050 | 0.150 |
| source_type_masked | 40 | 0.100 | 0.050 | 0.026 | -0.025 | 0.000 | 0.100 |

## Generated-Lore Belief/Operation Gap

| variant | n | belief_correctness | operational_epistemic_escape | belief_operation_gap |
| --- | --- | --- | --- | --- |
| baseline_original | 10 | 1.000 | 0.000 | 1.000 |
| citation_masked | 10 | 1.000 | 0.000 | 1.000 |
| order_randomized | 10 | 1.000 | 0.100 | 0.900 |
| prompt_paraphrase | 10 | 1.000 | 0.100 | 0.900 |
| source_type_masked | 10 | 1.000 | 0.000 | 1.000 |

## Flip Review Summary

- Paired flip rows: 57
- Reviewed rows: 57

## Claim Boundary

Allowed claim: this paired role-uncued Phase 1.3 mini-suite supports only named perturbation-sensitivity or mini-suite robustness statements. It does not replace Phase 1 main tables and does not establish production or open-web validity.

## Variant Claim Status

| variant | paired_n | mean_delta_operational_escape | mean_delta_belief_correctness | status |
| --- | --- | --- | --- | --- |
| citation_masked | 40 | 0.075 | -0.075 | preserves |
| order_randomized | 40 | 0.125 | 0.075 | preserves |
| prompt_paraphrase | 40 | 0.100 | 0.025 | preserves |
| source_type_masked | 40 | 0.100 | 0.050 | preserves |
