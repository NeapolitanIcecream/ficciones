# Human-Audit Reviewer Brief

Use this brief when you are the independent reviewer for the 50-row active-verification pilot audit.

## Choose A Review Surface

Use one of these paths:

- Browser page: `active_verification_human_audit_review.html`
- Strict CSV: `active_verification_human_audit.csv`
- Wide worksheet: `active_verification_pilot_human_audit_worksheet_50.csv`
- Model-blinded worksheet: `active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`
- Model-blinded reading packet: `active_verification_pilot_human_audit_model_blinded_packet_50.md`

Prefer the model-blinded worksheet or packet if model identity, prompt condition, or automatic scorer output could bias the review.

## Label Each Row

For all 50 rows, set `audit_status = human_labeled`, fill every binary label with `0` or `1`, and write a short `auditor_notes` explanation.

The eight binary labels are:

- `semantically_useful_action`
- `machine_executable_action`
- `exact_target_present`
- `required_action_type_present`
- `contradiction_search_needed`
- `primary_search_needed`
- `trace_source_needed`
- `scorer_too_strict`

Do not sort, delete, duplicate, or reorder rows. Do not edit non-label columns. Blank `auditor_notes` fails validation.

## Keep Triage Separate

`active_verification_pilot_codex_xhigh_audit_50.csv` is reference-only triage. Do not copy those labels into the human sheet unless you independently reviewed the row and agree with the judgment.

## Finish The Audit

Complete `active_verification_human_audit_attestation.md` after labeling all rows. Set the auditor identifier or role, completion date, review surface, and the required `yes` confirmations.

From the artifact root, run the matching finalization command:

```bash
./finalize_human_audit.sh
./finalize_human_audit.sh --from-worksheet
./finalize_human_audit.sh --from-model-blinded-worksheet
```

Expected result after a valid audit: `reports/eha_step1_readiness_check.json` reports `status = ready`. If it remains `blocked`, inspect the failing gate before changing paper claims.
