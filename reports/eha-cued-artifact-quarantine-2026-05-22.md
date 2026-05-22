# EHA Cued Artifact Quarantine

Date: 2026-05-22

The existing `artifact/` package is now marked as `scientific_status = "quarantined_cued_internal"` in `artifact/manifest.json`, with `artifact/CUED_INTERNAL_ONLY.md` documenting the restriction.

Policy:

- Old cued/opaque results may be used only as methodological caution, regression-test material, or historical comparison.
- Old cued/opaque results must not be used as main evidence for EHA-Uncued Phase 1.
- The uncued release verifier refuses `artifact/` as EHA-Uncued Phase 1 evidence when this quarantine marker is present.

