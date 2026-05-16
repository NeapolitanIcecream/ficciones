# EHA Step 2 Surface-Cue Design Review Packet

Date: 2026-05-16

This packet is for human design review of the no-API surface-cue smoke dataset. It is not model evidence and does not replace the Step 1 active-verification human audit.

Do not copy labels from model outputs. Review the paired tasks and document summaries directly.

## Review Goal

For each pair, decide whether the paired rows preserve the same target claim, verdict, evidence contract, retrieval observability, and action-target contract while changing only the intended visible surface cue.

## Required Labels

- `intended_cue_changed_only`: yes/no
- `verdict_and_evidence_contract_preserved`: yes/no
- `hidden_label_leakage_found`: yes/no
- `retrieval_observability_ok`: yes/no
- `action_target_contract_ok`: yes/no
- `suitable_for_small_api_pilot`: yes/no
- `review_status`: set to `reviewed` after all labels and notes are filled
- `reviewer_notes`: required for every pair, including clean passes

## Current Status

- Status: `incomplete`
- Pair rows: 90
- Reviewed pairs: 0
- Missing label cells: 540
- Missing notes: 90

## Browser Review

Use the local browser page for the actual review:

```bash
cd reports
./serve_surface_cue_design_review.sh
```

The page supports family, axis, and status filters; CSV import/export; and a next-incomplete jump. After downloading the completed worksheet, rerun `eha-validate-surface-cue-design-review`.

## Example Pair Rows

| family | template | axis | condition_a | condition_b | task_id_a | task_id_b | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| active_verification | dispatch_exception | adversarial_spoofing | plain_pollutant | regulator_spoof_pollutant | eha2sc_156 | eha2sc_157 | refuted |
| active_verification | dispatch_exception | content_only | full_metadata | content_only_metadata_stripped | eha2sc_158 | eha2sc_159 | refuted |
| active_verification | dispatch_exception | metadata_perturbation | truthful_metadata | shuffled_authority_metadata | eha2sc_152 | eha2sc_153 | refuted |
| active_verification | dispatch_exception | source_type_visibility | visible_source_types | hidden_source_types | eha2sc_150 | eha2sc_151 | refuted |
| active_verification | dispatch_exception | style_normalization | original_style | normalized_style | eha2sc_154 | eha2sc_155 | refuted |
| active_verification | parts_quarantine | adversarial_spoofing | plain_pollutant | regulator_spoof_pollutant | eha2sc_166 | eha2sc_167 | refuted |

## Go / No-Go Rule

A small API pilot should not run from this dataset until all pair rows are reviewed, every required label is present, notes are nonblank, and any `no` labels have been triaged into either generator fixes or explicit documented limitations.
