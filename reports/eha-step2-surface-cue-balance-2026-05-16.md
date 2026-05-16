# EHA Step 2 Surface-Cue Balance Report

Date: 2026-05-16

This no-API report checks whether the Step 2 surface-cue smoke dataset is balanced enough to justify design review. It is not model evidence.

## Counts

- Tasks: 180
- Documents: 900
- Gold documents: 900
- Active-verification action-gold rows: 30

## Balance

- Family counts: {'active_verification': 30, 'conflict': 30, 'generated_lore': 30, 'no_primary': 30, 'partial': 30, 'stale': 30}
- Axis counts: {'adversarial_spoofing': 36, 'content_only': 36, 'metadata_perturbation': 36, 'source_type_visibility': 36, 'style_normalization': 36}
- Verdict counts: {'insufficient': 90, 'refuted': 90}
- Scope counts: {'conflicting': 60, 'generated_lore': 30, 'no_primary_source': 30, 'partial': 30, 'stale': 30}
- Template cells: 18

## Contract Checks

- Pair contract violations: 0
- Visible leakage count: 0
- Action target violations: 0
- Clean-support observable rows: 120 / 120
- Contaminated observable rows: 180 / 180

## Decision

The dataset is ready for human design review. The review handoff is `reports/eha-step2-surface-cue-design-review-packet-2026-05-16.md`, `reports/surface_cue_design_review_worksheet.csv`, `reports/surface_cue_design_review.html`, and `reports/serve_surface_cue_design_review.sh`; current review status is incomplete. The no-API scoring-pipeline scaffold is covered separately in `reports/eha-step2-surface-cue-scoring-pipeline-2026-05-16.md`. It should still not trigger a large API run or 500-1000 task expansion without a separate go/no-go decision.
