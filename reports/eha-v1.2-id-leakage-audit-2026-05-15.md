# EHA v1.2 ID Leakage Audit

Date: 2026-05-15

Inputs:

- Blind review memo: `ficciones-research-blind-0515-0.md`
- GPT-5.5-Pro comment memo: `ficciones-research-0515-6.md`
- Main-run prompt artifacts: `eha-mvp/results/reports-eha-frontier-main/artifacts/**/*.prompt.json`
- Frozen task file: `eha-mvp/data/epistemic-resilience-v1/tasks.jsonl`

## Decision

P0 leakage is confirmed.

The semantic IDs in the PDF examples are not merely post-hoc audit aliases. They are present in actual model-visible prompt JSON for the main frontier run.

This triggers the 0515-6 stop condition: do not proceed to interpret the current main run as final benchmark evidence, and do not spend effort on large follow-on experiments until an opaque-ID rerun plan is in place.

## Objective-To-Artifact Checklist

| 0515-6 requirement | Evidence | Status |
| --- | --- | --- |
| Inspect actual model-visible document IDs in all main-run prompts | 1000 `*.prompt.json` files scanned under `reports-eha-frontier-main/artifacts/` | Done |
| Check for semantic labels such as primary, pollutant, generated, stale, repost, root | `id_leakage_audit_summary.json`, `id_leakage_prompt_examples.csv` | Done |
| If semantic IDs were model-visible, stop and report | This report marks P0 leakage confirmed and stops further benchmark interpretation | Done |
| If IDs were only post-hoc aliases, update paper accordingly | Not applicable; the IDs were model-visible | N/A |
| Add ID-only sanity baseline | Deferred because P0 already confirms visible semantic leakage; it should be run after opaque-ID view generation | Deferred |
| Implement no-API baselines | Deferred until opaque-ID remediation, per 0515-6 priority ordering | Deferred |
| Create reproducibility artifact package | Deferred until opaque-ID remediation so public artifacts do not encode invalid visible IDs | Deferred |
| Add task-level bootstrap / paired tests | Deferred until opaque-ID rerun produces valid scored rows | Deferred |
| Paper wording: reframe schema/interface and caveat validity | `paper/sections/09_limitations.tex` now states the semantic-ID audit result and opaque-ID rerun requirement | Done |

## Evidence

Prompt artifact scan:

| Item | Count |
| --- | ---: |
| Prompt files inspected | 1000 |
| Total visible document instances | 12860 |
| Visible `doc_id` semantic hits | 12780 |
| Visible citation semantic hits | 6110 |
| Visible title semantic hits | 6390 |
| Visible body semantic hits | 11780 |

Examples include:

```text
eham_006_primary_a
eham_006_primary_b
eham_006_pollutant_root
eham_006_repost_00
eham_006_context_08
```

Role predictability from frozen task IDs:

| Token in visible ID | n | Top hidden role | Top-role rate |
| --- | ---: | --- | ---: |
| `primary` | 148 | primary | 1.000 |
| `context` | 491 | background | 1.000 |
| `repost` | 539 | contaminant | 0.865 |
| `pollutant` | 100 | contaminant/generated/stale family | 1.000 for pollutant-like roles |
| `root` | 100 | contaminant/generated/stale family | 1.000 for pollutant-like roles |

Artifacts written:

- `eha-mvp/results/reports-eha-paper-v1.2-validity-defense-2026-05-15/id_leakage_audit_summary.json`
- `eha-mvp/results/reports-eha-paper-v1.2-validity-defense-2026-05-15/id_leakage_prompt_examples.csv`
- `eha-mvp/results/reports-eha-paper-v1.2-validity-defense-2026-05-15/id_token_role_predictability.csv`

## Interpretation

The current run still supports an internal mechanism observation: prose, evidence fields, and action fields can diverge in agent-facing outputs. It does not yet support a strong external benchmark claim, because models could have used visible ID strings or other surface labels to infer roles.

The risk is broader than `doc_id` alone. The prompt payload includes `visible_citations`, `title`, `source_type`, `timestamp`, and `body`. Some of those fields also contain role-like labels such as "Primary record" or cite semantic upstream IDs. An opaque-ID rerun must remap visible citations and scrub audit-only labels from text/metadata where those labels are not intended evidence.

## Required Next Step

Prepare an opaque-ID rerun before adding more benchmark claims.

Minimum remediation:

1. Generate per-task opaque visible IDs, for example `doc_01`, `doc_02`, with randomized order.
2. Remap `visible_citations` to the same opaque namespace.
3. Keep hidden gold labels and original audit aliases only in scorer-side mapping files.
4. Scrub role words from model-visible IDs and audit-only titles/body prefixes.
5. Add an ID-only sanity baseline before rerunning API models.
6. Rerun preflight and main frontier jobs only after the opaque view is verified.

Deferred until after opaque-ID remediation:

- full no-API baselines,
- task-level bootstrap and paired tests,
- prompt-effect confidence intervals,
- broader clarified-schema reruns.
