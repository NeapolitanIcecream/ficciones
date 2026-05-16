# Active-Verification Human-Audit Handoff

Date: 2026-05-16

## Purpose

This handoff closes everything around the Step 1 active-verification audit except the independent human/manual labels themselves. The current status is intentionally incomplete:

- `artifact/manifest.json`: `active_verification_human_audit.status = incomplete`
- `artifact/manifest.json`: `active_verification_human_audit.n_labeled = 0`
- `artifact/audits/active_verification_pilot_human_audit_validation.json`: `status = incomplete`, `n_complete_rows = 0`

The current blank rows also fail because `auditor_notes` is empty. The Codex-assisted audit is separate triage evidence and must not be copied into the human-audit CSV as human labels.

## Current Local Review Session

As of 2026-05-16 05:34 Asia/Shanghai, the browser review page is being served in tmux:

- tmux session: `eha-human-audit-review`
- URL: `http://127.0.0.1:8765/audits/active_verification_human_audit_review.html`
- HTTP check: `200 OK`
- initial page state: `0 / 50 rows have all eight binary labels and auditor notes`

To inspect the server:

```bash
tmux capture-pane -pt eha-human-audit-review:0.0 -S -80
```

To stop it after the auditor has downloaded the completed strict CSV:

```bash
tmux send-keys -t eha-human-audit-review C-c
```

## Files For The Human Annotator

Use one of these labeling surfaces:

- Label sheet to fill: `artifact/audits/active_verification_human_audit.csv`
- Optional wide worksheet with row context: `artifact/audits/active_verification_pilot_human_audit_worksheet_50.csv`
- Optional model-blinded worksheet: `artifact/audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv`
- Optional browser review page: `artifact/audits/active_verification_human_audit_review.html`
- Short reviewer brief: `artifact/audits/active_verification_human_audit_reviewer_brief.md`
- Row-by-row context packet: `artifact/audits/active_verification_pilot_human_audit_packet_50.md`
- Model-blinded row packet: `artifact/audits/active_verification_pilot_human_audit_model_blinded_packet_50.md`
- Audit provenance attestation: `artifact/audits/active_verification_human_audit_attestation.md`

Reference-only files:

- Quickstart: `artifact/audits/active_verification_human_audit_readme.md`
- Protocol: `artifact/audits/active_verification_human_audit_protocol.md`
- Guidelines: `artifact/audits/active_verification_human_audit_guidelines.md`
- Paper-update memo: `artifact/audits/active_verification_pilot_human_audit_paper_update.md`
- Context JSONL: `artifact/audits/active_verification_pilot_human_audit_context_50.jsonl`
- Codex triage audit: `artifact/audits/active_verification_pilot_codex_xhigh_audit_50.csv`

## Labeling Contract

For each of the 50 rows, set:

- `audit_status` to `human_labeled`
- `semantically_useful_action` to `0` or `1`
- `machine_executable_action` to `0` or `1`
- `exact_target_present` to `0` or `1`
- `required_action_type_present` to `0` or `1`
- `contradiction_search_needed` to `0` or `1`
- `primary_search_needed` to `0` or `1`
- `trace_source_needed` to `0` or `1`
- `scorer_too_strict` to `0` or `1`
- `auditor_notes` to a short note explaining the judgment

Blank `auditor_notes` rows fail validation. A completed row needs `audit_status = human_labeled`, all eight binary label fields, and a nonblank note.

Do not edit the non-label columns. The validator checks for accidental changes to model/task/action metadata. The three `*_needed` fields are label columns: they are prefilled from the task design to reduce annotation friction, but the human auditor should verify or revise them during review.

Do not sort, delete, duplicate, or reorder rows. The validator compares row order and non-label columns against the original sample sheet. The Codex triage audit is reference-only; do not copy its labels into the human sheet unless an independent human auditor has reviewed the row and agrees with the judgment.

If the wide worksheet is easier to label, fill the same label columns there. The import command below strips the context columns and writes the strict `active_verification_human_audit.csv` without allowing non-label metadata edits.

If the HTML review page is easier, open `artifact/audits/active_verification_human_audit_review.html` locally. It shows row-completion status, can filter by evidence condition, can jump to the next incomplete row, can import an existing strict CSV draft, and enables the `active_verification_human_audit.csv` download only after all 50 rows have all eight binary labels and auditor notes. That downloaded CSV is still subject to the same finalization and validation commands below.

If model identity, prompt condition, or the automatic scorer result could bias the audit, use the model-blinded worksheet or model-blinded packet. The model-blinded worksheet can be imported directly by row order; the packet is a reading surface for transfer into the strict CSV or either worksheet.

After all labels and notes are complete, fill `active_verification_human_audit_attestation.md` with the auditor identifier or role, completion date, review surface used, and `yes` confirmations that the review was independent, Codex triage labels were not copied as human labels, all 50 rows were reviewed, and all eight binary fields plus `auditor_notes` were completed. The readiness gate allows placeholders while the human audit is incomplete, but rejects the attestation if placeholders remain after validation reaches `status = complete`.

## Refresh Commands After Labeling

Shortcut from `artifact/`:

```bash
./finalize_human_audit.sh
# or, if the wide worksheet was filled:
./finalize_human_audit.sh --from-worksheet
# or, if the model-blinded worksheet was filled:
./finalize_human_audit.sh --from-model-blinded-worksheet
```

The shortcut imports the worksheet when requested, runs finalization, syncs the completed attestation into the source results directory, rebuilds `artifact/`, reruns the paper-aware readiness check, and prints the readiness status plus failing gate names. The manual command sequence is below for troubleshooting.

After paper claims are updated, the final pre-release verifier can be run from `artifact/`:

```bash
./verify_step1_release.sh
```

Before human labels are complete, the same script can be exercised without failing solely on the expected blocked readiness status:

```bash
./verify_step1_release.sh --allow-blocked
```

It runs the minimal example, `uv run pytest`, the paper build, the paper-aware readiness check, and `git diff --check` when the artifact is inside the git worktree.

From `eha-mvp/`:

```bash
# If you filled the wide worksheet, run this import step first.
# Skip it if active_verification_human_audit.csv was filled directly.
uv run eha-step1-release import-active-verification-human-audit-worksheet \
  --worksheet-csv ../artifact/audits/active_verification_pilot_human_audit_worksheet_50.csv \
  --reference-csv results/reports-eha-active-verification-audit-opaque-2026-05-15/active_verification_pilot_human_audit_sample_50.csv \
  --out-csv ../artifact/audits/active_verification_human_audit.csv

# If you filled the model-blinded worksheet, use this import step instead.
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
```

Expected gate-closing result:

- `active_verification_pilot_human_audit_validation.json` has `status = complete`
- `n_complete_rows = 50`
- no validation errors
- no blank `auditor_notes` rows
- completed `active_verification_human_audit_attestation.md` with no `[TO BE COMPLETED]` placeholders
- `active_verification_pilot_human_audit_labeled_50.csv` exists in the results directory
- `active_verification_pilot_human_audit_summary.json` has `status = complete`
- `n_labeled = 50`

If finalization exits with code `2`, inspect `active_verification_pilot_human_audit_validation_rows.csv`. The command does not import invalid labels.

Then rebuild the release package:

```bash
uv run eha-step1-release artifact-package \
  --task-dir data/epistemic-resilience-v1 \
  --frontier-main-dir results/reports-eha-frontier-main-opaque-2026-05-15 \
  --baseline-dir results/reports-eha-step1-baselines-2026-05-15 \
  --generated-lore-dir results/reports-eha-generated-lore-role-audit-opaque-2026-05-15 \
  --active-verification-dir results/reports-eha-active-verification-audit-opaque-2026-05-15 \
  --out-dir ../artifact
```

Finally rebuild and verify:

```bash
uv run pytest
uv run eha-step1-release step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports
cd ../paper && make
cd ..
git diff --check
cd artifact && ./reproduce_minimal.sh
```

Expected readiness result after valid human labels: `reports/eha_step1_readiness_check.json` should report `status = ready`. If it remains `blocked`, inspect the failing gate before updating the paper claims.

## Paper Updates After Human Labels

After validation and summary are complete, update:

- `paper/sections/06_active_verification_case.tex`
- `paper/sections/09_limitations.tex`
- `reports/eha-step1-completion-audit-2026-05-16.md`
- `reports/eha-step1-roadmap-progress-2026-05-15.md`

The paper should report the human-audit rates separately from the Codex-assisted triage rates. Keep the distinction between human usefulness, machine executability, exact target quality, required action type, and scorer strictness.

The readiness check now enforces this boundary with `paper_human_audit_claim_consistency`: while the human audit is incomplete, the paper must not present it as human validation; after the summary reaches `status = complete` and `n_labeled = 50`, Section 6 must include the human-labeled audit counts separately from the Codex-assisted triage counts.

The generated paper-update memo records the current incomplete state and should not be used for completed claims yet. After finalization, regenerate the artifact package and use that memo for the exact human-audit counts to place in Section 6.
