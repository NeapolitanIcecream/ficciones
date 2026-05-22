# EHA-Uncued Phase 1 Artifact

This package contains the role-uncued Phase 1 pilot dataset, prompts, model outputs, scorer inputs, gate reports, and verifier scripts.

Scientific status: diagnostic pilot artifact. It is not a deployment certification or a universal model leaderboard.

The older cued artifact is intentionally excluded. Hidden labels and gold/scorer files are included only under non-model-visible paths.

## Local Checks

From the repository root:

```bash
cd eha-mvp
uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports
```

For a no-dependency smoke check, run `artifact_uncued_phase1/reproduce_minimal.sh`.
