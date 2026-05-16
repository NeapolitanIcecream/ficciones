# EHA Step 2 Target Context

Date: 2026-05-16

- Status: `incomplete`
- Ready: `false`
- Target venue: `TBD`
- Target deadline: `TBD`
- Submission track: `TBD`
- Decision owner: `TBD`
- API budget confirmed: `false`
- Max Step 2 API budget USD: `0.00`
- Human-review budget confirmed: `false`
- Human-review budget USD: `0.00`
- Explicit approval required before model calls: `true`

This is a no-API decision context for the Step 2 launch gate. It records whether the project has an explicit target venue, deadline, and approved budget before any further model spend.

## Missing Fields

- `target_venue`
- `target_deadline`
- `submission_track`
- `decision_owner`
- `budget_confirmed`
- `human_review_budget_confirmed`
- `max_step2_api_budget_usd`
- `human_review_budget_usd`

## Candidate Paths

### workshop_arxiv_v1_first

- Description: Release Step 1 as a controlled diagnostic benchmark only after the independent human audit is complete.
- API boundary: No new model calls required.

### main_conference_step2_after_gates

- Description: Prepare a larger benchmark/evaluation submission only after Step 1 human audit, surface-cue design review, schema repair, target venue, and budget gates clear.
- API boundary: Requires explicit approval and budget before fixed-slice or larger API runs.

## Non-Claims

- not model evidence
- not permission to run model/API calls
- not a substitute for Step 1 human audit or surface-cue design review
- not a budget approval unless budget_confirmed and human_review_budget_confirmed are true
