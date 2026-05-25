# EHA-Uncued Phase 1.1 Final Handoff

Date: 2026-05-25

Status: role-uncued schema ablation complete and verified as exploratory Phase 1.1 evidence.

## What Changed

The Phase 1 handoff from 2026-05-22 correctly recorded that Phase 15 was skipped on the main arXiv-readiness path. That is now historical. The deferred role-uncued schema ablation has since been run as Phase 1.1.

Phase 1.1 does not revise the Phase 1 main model table, artifact readiness decision, or headline benchmark claim. It adds a narrow interface-sensitivity result: holding the role-uncued evidence packet fixed, different structured output schemas change machine-readable evidence-role allocation.

## Completed Scope

- Run directory: `eha-mvp/results/reports-eha-uncued-schema-ablation-2026-05-23/`
- Result report: `reports/eha-uncued-schema-ablation-results-2026-05-23.md`
- Result JSON: `reports/eha_uncued_schema_ablation_results.json`
- Verification JSON: `reports/eha_uncued_schema_ablation_verification.json`
- Source data: `eha-mvp/data/uncued-pilot-v1`
- Conditions: `generated_lore`, `buried_primary`
- Selected source tasks: 16
- View: `neutral_metadata_visible`
- Models: `gpt-5.5`, `gemini-3.1-pro-preview`
- Schemas: `current`, `clarified`, `minimal`, `diagnostic_no_hygiene`
- Prompt condition: `standard_answer`
- Latest complete rows: 128
- Raw records: 130
- Cost spent: USD 1.890321

## Verification

`reports/eha_uncued_schema_ablation_verification.json` records `decision=pass`.

Passing gates:

- role-uncued data source only;
- Phase 1 gates present and passing;
- selected conditions restricted to generated lore and buried primary;
- prompt audit passed;
- stored hidden-label audit passed;
- cost under USD 5 hard cap;
- current-schema anchor complete;
- all latest rows parse successfully;
- all four schemas represented;
- results are separate from the Phase 1 artifact;
- report boundary states this is exploratory Phase 1.1 evidence;
- no old cued evidence claim.

## Main Result

The ablation supports a narrow interface claim:

- `minimal` placed polluted evidence in support fields on all rows for both evaluated models and reached zero role escape.
- `current` avoided polluted support in this slice and reached role escape 1.000 for both evaluated models.
- `clarified` avoided polluted support; role escape was 1.000 for Gemini and 0.938 for GPT-5.5.
- `diagnostic_no_hygiene` avoided polluted support but showed mixed role allocation: role escape 1.000 for Gemini and 0.500 for GPT-5.5.

This should be reported as schema/interface sensitivity in machine-readable evidence fields, not as a provider ranking and not as a replacement for the Phase 1 main result.

## Paper Handling

No full paper rewrite is needed. The paper should keep the Phase 1 main tables and claims intact.

Required paper posture:

- mention Phase 1.1 only as a small exploratory ablation;
- keep old cued schema results quarantined;
- state that schema wording is an experimental factor for evidence-role fields;
- do not claim that schema wording explains all Phase 1 gaps;
- do not fold Phase 1.1 rows into the main benchmark table.

The current paper already has this posture in `paper/sections/08_schema_interface.tex` and `paper/sections/10_limitations.tex`. The artifact section should say the Phase 1 artifact remains unchanged and that Phase 1.1 outputs live separately under `reports/` and `eha-mvp/results/`.

## Handoff Handling

The 2026-05-22 Phase 1 handoff should not be treated as the latest project state without this addendum. Its Phase 15 entry remains historically accurate for the main Phase 1 path, but its "run Phase 1.1" recommendation is now stale.

Use this handoff as the current post-ablation status.

## Recommended Next Step

Do not expand the schema-ablation claim without a larger role-uncued slice and independent human review. The next useful work is a larger dataset/human-audit pass, with schema/interface choice treated as an experimental factor from the start.
