# EHA Step 1 Reproducibility Package

This package contains the opaque-ID repaired Step 1 artifacts for the controlled diagnostic EHA paper.
`file_manifest.json` lists every packaged file except itself, with byte size and SHA-256 hash.

Contents:

- `data/`: opaque task packets, document packets, and visible-ID gold labels.
- `prompts/`: standard and epistemic-hygiene prompt contracts.
- `scorer/`: a minimal scoring contract and notes.
- `outputs/`: opaque frontier predictions, scored rows, and copied run/report manifests.
- `baselines/`: no-API baseline scored rows.
- `audits/`: prompt leakage, generated-lore schema, active-verification action audit, the pilot human-audit sheet/context/worksheet/model-blinded worksheet/HTML review page/Markdown packet/model-blinded packet/reviewer brief/paper-update memo/protocol/manifest/attestation/validation report, and any clearly marked Codex-assisted audit outputs.
- `examples/`: a minimal task, model output, and score.

Run the minimal example from this directory:

```bash
./reproduce_minimal.sh
```

Start the active-verification human-audit browser review page from this directory:

```bash
./serve_human_audit_review.sh
```

The script serves only on `127.0.0.1` and opens `audits/active_verification_human_audit_review.html` when the local platform supports `open`.

After an independent human auditor has completed all 50 rows, finalize the label sheet from this directory:

```bash
./finalize_human_audit.sh
```

If the auditor filled the wide worksheet instead of the strict CSV, run:

```bash
./finalize_human_audit.sh --from-worksheet
```

If the auditor filled the model-blinded worksheet, run:

```bash
./finalize_human_audit.sh --from-model-blinded-worksheet
```

The finalization script validates the labels, imports them into the results directory, rebuilds this artifact package, reruns the paper-aware readiness check, and prints the readiness status plus any failing gates. Complete `audits/active_verification_human_audit_attestation.md` before treating the human audit as release-ready.

Human-audit gate:

- Release readiness requires all 50 rows in `audits/active_verification_human_audit.csv` to have `audit_status = human_labeled`, all eight binary labels, and nonblank `auditor_notes`.
- After finalization and artifact rebuild, `artifact/manifest.json` must report `active_verification_human_audit.status = complete` and `n_labeled = 50`.
- The paper must keep human-audit counts separate from Codex-assisted triage counts; if readiness remains `blocked`, do not update paper claims as if human validation is complete.

Check Step 1 release readiness from `eha-mvp/`:

```bash
uv run eha-step1-release step1-readiness-check --artifact-dir ../artifact --paper-dir ../paper --out-dir ../reports
```

After human labels and paper claim updates are complete, run the pre-release verifier from this directory:

```bash
./verify_step1_release.sh
```

For an intentionally blocked dry run before human labels are complete, use:

```bash
./verify_step1_release.sh --allow-blocked
```

The verifier runs the minimal example, the EHA test suite, the paper build, the paper-aware readiness check, and `git diff --check` when the artifact sits inside a git worktree.

Current gate status may be `blocked` until `audits/active_verification_human_audit.csv` is independently human-labeled and finalized. The audit manifest records the eight required label fields, including the three needed-action labels. Codex-assisted audit outputs are triage artifacts, not human validation.

Scope: this package supports a controlled diagnostic benchmark. It is not evidence that any model or agent is certified for legal, medical, financial, or live deployment use.
