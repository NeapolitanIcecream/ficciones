# Scoring Contract

The Phase 1 scorer evaluates parsed prediction records against role-uncued gold labels.

- `belief_correctness`: claim verdict matches the gold verdict.
- `evidence_precision`: selected supporting evidence avoids polluted evidence and aligns with gold support.
- `operational_escape`: joint success criterion combining belief correctness and evidence hygiene.
- `verification_action_score`: active-verification action quality for tasks that require source tracing.

The Phase 14 scorer audit found no systematic scorer bug and did not require rescoring. The audit is included under `audits/`.
