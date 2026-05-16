# Active-Verification Pilot Human-Audit Protocol

Protocol version: 1

## Purpose

This protocol defines the Step 1 single-auditor pilot audit for active-verification actions. It distinguishes three questions:

- whether a proposed action is useful to a human reader;
- whether the same action is machine executable under the written action contract;
- whether the automatic scorer is visibly too strict for that row.

The protocol is part of the release artifact, but it does not create human-validation evidence by itself. The release gate remains blocked until all 50 rows are independently human-labeled and finalized.

## Sample

The audit sample contains 50 active-verification rows from the opaque main run. It is stratified across five evidence conditions with 10 rows per condition:

- `clean`
- `generated_lore`
- `false_consensus`
- `buried_primary`
- `conflicting_evidence`

The rows are reviewed in the fixed order supplied in `active_verification_human_audit.csv`, the wide worksheet, the browser review page, or the model-blinded packet. Do not sort, delete, duplicate, or reorder rows.

## Materials

- Strict label sheet: `active_verification_human_audit.csv`
- Wide worksheet with context: `active_verification_pilot_human_audit_worksheet_50.csv`
- Model-blinded worksheet with row-order transfer: `active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`
- Browser review page: `active_verification_human_audit_review.html`
- Reviewer brief: `active_verification_human_audit_reviewer_brief.md`
- Row packet: `active_verification_pilot_human_audit_packet_50.md`
- Model-blinded row packet: `active_verification_pilot_human_audit_model_blinded_packet_50.md`
- Paper-update memo: `active_verification_pilot_human_audit_paper_update.md`
- Attestation template: `active_verification_human_audit_attestation.md`
- Guidelines: `active_verification_human_audit_guidelines.md`
- Context JSONL: `active_verification_pilot_human_audit_context_50.jsonl`
- Validation report: `active_verification_pilot_human_audit_validation.json` and `_rows.csv`
- Reference-only Codex triage: `active_verification_pilot_codex_xhigh_audit_50.csv`

The context uses opaque model-visible `doc_###` IDs. Audit roles are shown only to the human auditor for review; they were not visible to the model.

## Label Contract

For each row, set `audit_status` to `human_labeled`, fill all eight binary label fields with `0` or `1`, and add a short `auditor_notes` explanation.

Required binary fields:

- `semantically_useful_action`
- `machine_executable_action`
- `exact_target_present`
- `required_action_type_present`
- `contradiction_search_needed`
- `primary_search_needed`
- `trace_source_needed`
- `scorer_too_strict`

The three `*_needed` fields are prefilled from the task design to reduce annotation friction, but they remain human label fields and should be verified or revised.

Model identities, prompt conditions, and automatic scorer outcomes are intentionally omitted from the model-blinded packet and model-blinded worksheet so an auditor can make the usefulness/executability judgments without seeing provider identity or the automatic gate decision.

## Boundary Rules

- A row can be semantically useful but fail machine executability if the target is bundled, vague, or not a direct tool target.
- Mark `scorer_too_strict = 1` only when the rejected action is both useful and reasonably executable under the written contract.
- Do not edit non-label columns. The validator checks row keys, row order, labels, and metadata against the original sample.
- Codex-assisted labels are triage evidence only. They are not human validation and must not be copied into the human sheet unless an independent human auditor has reviewed the row and agrees.

## Finalization Gate

Run `finalize-active-verification-human-audit` after labeling. A valid completed audit requires:

- `active_verification_pilot_human_audit_validation.json` status is `complete`;
- `n_complete_rows = 50`;
- no blank `auditor_notes` rows;
- `active_verification_human_audit_attestation.md` is completed with auditor identity/role, date, review surface, and independent-review statements;
- all five required evidence conditions are present;
- the current label CSV hash matches the validation report;
- the artifact manifest records `active_verification_human_audit.status = complete` and `n_labeled = 50` after rebuilding the release package.

Until those conditions hold, the paper may cite the prepared materials and Codex-assisted triage only as pilot infrastructure, not as independent human-validation evidence.
