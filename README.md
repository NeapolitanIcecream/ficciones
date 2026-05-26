# ficciones

This repository contains the Epistemic Hygiene Arena experiments and paper materials.

## EHA-Uncued Paper Review Entry Point

For the current EHA-Uncued manuscript, start with:

- `paper/main.pdf`: compiled manuscript.
- `paper/`: LaTeX source for the manuscript.
- `artifact_uncued_phase1/`: release-facing role-uncued Phase 1 pilot artifact.
- `reports/eha-uncued-core-claim-overnight-results-2026-05-25.md`: summary of the later support-ambiguity, failure-decomposition, schema-rerun, positive-contract, and shortcut-boundary checks.
- `eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/`: machine-readable CSV/JSON outputs for those checks.

The older `artifact/` directory is a quarantined cued/internal package and is not evidence for the EHA-Uncued paper's main results.

## Reproduce The Release Artifact Checks

From a clean clone:

```bash
cd eha-mvp
uv run eha-verify-uncued-phase1 \
  --artifact-dir ../artifact_uncued_phase1 \
  --reports-dir ../reports \
  --out-dir ../reports
```

Expected analysis counts used by the paper:

- 480 main-pilot rows.
- 200 presentation-perturbation mini-suite rows.
- 144 schema-rerun rows.
- 72 schema-rerun paired comparisons.

The artifact is a diagnostic pilot package, not a deployment certification, open-web benchmark, or stable provider leaderboard.
