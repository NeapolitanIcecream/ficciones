# Active-Verification Human-Audit Quickstart

This directory contains the Step 1 active-verification pilot audit materials. The release gate remains blocked until the 50-row human-audit sheet is independently labeled and finalized.

## Files

- Label sheet: `active_verification_human_audit.csv`
- Optional wide worksheet: `active_verification_pilot_human_audit_worksheet_50.csv`
- Optional model-blinded worksheet: `active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`
- Browser review page: `active_verification_human_audit_review.html`
- Row packet: `active_verification_pilot_human_audit_packet_50.md`
- Model-blinded row packet: `active_verification_pilot_human_audit_model_blinded_packet_50.md`
- Guidelines: `active_verification_human_audit_guidelines.md`
- Protocol: `active_verification_human_audit_protocol.md`
- Attestation template: `active_verification_human_audit_attestation.md`
- Context JSONL: `active_verification_pilot_human_audit_context_50.jsonl`
- Validation report: `active_verification_pilot_human_audit_validation.json` and `_rows.csv`
- Paper-update memo: `active_verification_pilot_human_audit_paper_update.md`
- reference-only triage: `active_verification_pilot_codex_xhigh_audit_50.csv`

## Labeling Rules

For every row in `active_verification_human_audit.csv`, set `audit_status` to `human_labeled`, verify or revise all eight binary label columns with `0` or `1`, and add a short `auditor_notes` explanation.

If the wide worksheet is easier to review, fill the same label columns there first, then import it into the strict label sheet before finalization.

If the model-blinded worksheet is easier to review, fill the same label columns there first, then import it into the strict label sheet before finalization with `--from-model-blinded-worksheet`. The import relies on `row_index` and row order rather than exposing model identity or prompt condition.

If the HTML review page is easier, open `active_verification_human_audit_review.html` locally. It shows row-completion status, can import an existing strict CSV draft, and enables `active_verification_human_audit.csv` download only after all rows have the eight binary labels and auditor notes.

If model identity or automatic scorer output could bias the review, use `active_verification_pilot_human_audit_model_blinded_packet_50.md` as the reading surface and transfer labels by row order into the strict CSV or wide worksheet.

Do not sort, delete, duplicate, or reorder rows. Do not edit non-label columns. The validator checks row keys, row order, labels, and metadata. The three `*_needed` columns are label columns: they are prefilled for convenience, but the human auditor may change them after review.

Codex-assisted audit files are triage only. Do not copy their labels into the human sheet unless an independent human auditor has reviewed the row and agrees with the judgment.

Before final release, complete `active_verification_human_audit_attestation.md` with the auditor identifier or role, completion date, review surface, and yes/no statements confirming independent review, no copied Codex triage labels, all 50 rows reviewed, and all eight binary fields plus `auditor_notes` completed.

## Finalize After Labeling

Shortcut from the artifact root:

```bash
./finalize_human_audit.sh
# or, if the wide worksheet was filled:
./finalize_human_audit.sh --from-worksheet
# or, if the model-blinded worksheet was filled:
./finalize_human_audit.sh --from-model-blinded-worksheet
```

Run from `eha-mvp/`:

```bash
# If you filled the wide worksheet, run this import step first.
# Skip it if active_verification_human_audit.csv was filled directly.
uv run eha-step1-release import-active-verification-human-audit-worksheet \
  --worksheet-csv ../artifact/audits/active_verification_pilot_human_audit_worksheet_50.csv \
  --reference-csv results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv \
  --out-csv ../artifact/audits/active_verification_human_audit.csv

# If you filled the model-blinded worksheet, run this import step instead.
uv run eha-step1-release import-active-verification-model-blinded-human-audit-worksheet \
  --worksheet-csv ../artifact/audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv \
  --reference-csv results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv \
  --out-csv ../artifact/audits/active_verification_human_audit.csv

uv run eha-step1-release finalize-active-verification-human-audit \
  --labels-csv ../artifact/audits/active_verification_human_audit.csv \
  --reference-csv results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv \
  --out-dir results/reports-eha-active-verification-audit-opaque-2026-05-15

cp ../artifact/audits/active_verification_human_audit_attestation.md \
  results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_human_audit_attestation.md

uv run eha-step1-release artifact-package \
  --task-dir data/epistemic-resilience-v1 \
  --frontier-main-dir results/reports-eha-frontier-main-opaque-2026-05-15 \
  --baseline-dir results/reports-eha-step1-baselines-2026-05-15 \
  --generated-lore-dir results/reports-eha-generated-lore-role-audit-opaque-2026-05-15 \
  --active-verification-dir results/reports-eha-active-verification-audit-opaque-2026-05-15 \
  --out-dir ../artifact

uv run eha-step1-release step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports
```

Expected final state: `reports/eha_step1_readiness_check.json` reports `status = ready`. If it remains `blocked`, inspect the failing gate before changing paper claims. When the audit is complete, use `active_verification_pilot_human_audit_paper_update.md` as the paper-update memo for Section 6 and keep the Codex-assisted triage counts separate.
