# EHA-Uncued Artifact Note For Blind Review

Attach this note only for an artifact-aware blind review. For a strict PDF-only review comparable to the previous round, do not attach it.

The paper is anonymized. The authors intend to open-source the experiment repository and artifact. This note is a compact map of the artifact surface so that a reviewer can distinguish "not shown in the PDF" from "not planned for release."

## Artifact Scope

The planned release contains a role-uncued Phase 1 diagnostic pilot artifact:

- role-uncued dataset files;
- model-visible prompt files;
- model response files;
- scored predictions and aggregate CSV/JSON outputs;
- scorer and reporting code;
- leakage, shortcut, scorer-audit, schema-ablation, bootstrap-uncertainty, task-example, template-diversity, and robustness reports;
- verifier scripts for the paper-facing artifact.

The older cued construction is quarantined and is not used as evidence for the paper's current claims.

## Main Verification Commands

Expected repository-root checks:

```bash
cd eha-mvp
uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports
uv run pytest tests/test_uncued_run.py tests/test_uncued_report.py -q
uv run pytest tests/test_uncued_statistics.py tests/test_uncued_examples.py tests/test_uncued_robustness.py -q
cd ../paper
make pdf
```

The artifact also includes a no-dependency smoke check:

```bash
artifact_uncued_phase1/reproduce_minimal.sh
```

## Key Release Surfaces

- `artifact_uncued_phase1/README.md`: artifact overview and local checks.
- `artifact_uncued_phase1/data/`: role-uncued dataset and gold/scorer files.
- `artifact_uncued_phase1/prompts/`: model-visible prompts.
- `artifact_uncued_phase1/outputs/`: predictions, scores, run manifests, cost reports, and aggregate results.
- `artifact_uncued_phase1/scorer/`: scorer and report code snapshot.
- `reports/eha-uncued-operational-escape-spec-2026-05-25.md`: recomputable operational-escape scoring contract.
- `reports/eha-uncued-bootstrap-uncertainty-2026-05-25.md`: latent-task bootstrap uncertainty summary.
- `reports/eha-uncued-task-examples-2026-05-25.md`: worked examples of clean pass, generated-lore hygiene failure, and active-verification success.
- `reports/eha-uncued-leakage-shortcut-methods-2026-05-25.md`: leakage and shortcut-method description.
- `reports/eha-uncued-template-diversity-audit-2026-05-25.md`: synthetic-template regularity audit.
- `reports/eha-uncued-robustness-results-2026-05-25.md`: Phase 1.3 paired robustness mini-suite results.

## Known Limits To Preserve In Review

- The work is a diagnostic pilot, not a production benchmark.
- The task environments are synthetic.
- The independent external human audit has not been executed; current manual checks are local/Codex-assisted.
- Model ranking claims should remain descriptive because the sample is small and intervals are wide.
- Robustness evidence is a named mini-suite, not a full robustness proof.

These limits are part of the intended claim boundary, not hidden caveats.

