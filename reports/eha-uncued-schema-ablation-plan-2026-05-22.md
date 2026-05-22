# EHA-Uncued Phase 15 Schema Ablation Decision

Date: 2026-05-22

Status: skipped under the runbook skip rule; deferred to Phase 1.1.

## Decision

Phase 15 is not part of the main arXiv readiness path for this run. The main role-uncued result is complete through Phase 14: model run, scoring, and scorer audit are done. The runbook allows the schema-ablation mini-slice to be skipped when Phase 12-14 consume the time/budget and the main uncued result is complete.

No Phase 15 model calls were made.

## Planned Phase 1.1 Scope

If run later, the mini-slice should remain an ablation, not a replacement for the main result:

- Conditions: generated lore and buried primary.
- Task count: 10-20 tasks.
- Models: one or two models, recommended `gpt-5.5` and `gemini-3.1-pro-preview`.
- Schemas: `clarified`, `current`, `minimal`, `diagnostic_no_hygiene`.
- Budget cap: USD 5.
- Data rule: use only `data/uncued-pilot-v1`; do not reuse cued artifacts.

## Acceptance

- Clearly marked as ablation, not main result: yes.
- Does not reuse cued data: yes.
- Listed as planned Phase 1.1 work: yes.
- Does not block arXiv pilot readiness: yes.

## Caveat

The paper can mention schema/interface analysis as planned follow-up or as a motivation from the older quarantined work, but it must not claim that a role-uncued schema ablation has been run in this Phase 1 package.
