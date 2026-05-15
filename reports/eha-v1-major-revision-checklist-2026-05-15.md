# EHA V1 Major-Revision Checklist

Date: 2026-05-15

Source memo: local `ficciones-research-0515-3.md` review notes

Target draft: `epistemic-hygiene-arena-preprint.md`

Revision artifact directory: `eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/`

## Prompt-To-Artifact Mapping

| Requirement | Evidence | Status |
| --- | --- | --- |
| Continue with major revision, not large new experiment. | No new main experiment or API run was launched. Work uses existing frontier outputs plus derived local analyses and figures. | Done |
| Keep paper framed as epistemic resilience in polluted evidence environments, not leaderboard or RAG hygiene. | Abstract, Introduction, and Discussion use epistemic resilience framing; Introduction includes a reader contract that the paper does not rank frontier models. | Done |
| Shorten abstract to 4-5 sentences and avoid defensive leaderboard phrase. | Abstract is one compact paragraph with four sentences and no "not a leaderboard" wording. | Done |
| Add reader contract in Introduction. | Section 1 states the paper studies failures below answer accuracy in structured evidence and action outputs. | Done |
| Add dataset construction details. | Section 2.1 gives task count, document count range/mean, document types, document roles, condition distribution, and family distribution. | Done |
| Add task instance format. | Section 2.4 includes a simplified JSON task example. | Done |
| Add evidence document types and pollutant/provenance labels. | Section 2.1 and 2.4 list document types and hidden labels. | Done |
| Add output schema and prompt condition details. | Section 2.5 defines action space, standard prompt contract, and hygiene prompt additions. | Done |
| Add scoring contract and define support/reject semantics. | Section 2.6 defines `supporting_evidence`, `rejected_evidence`, metrics, operational vs conditional escape, and action target scoring. | Done |
| Add preflight table. | Section 3.1 has five-model preflight table with parse success, empty outputs, schema missing, response format, temperature, and token cap. | Done |
| Add invocation profile table and no-cap fairness explanation. | Section 3.2 includes invocation notes and visible-output/no-overlength statement. | Done |
| Rewrite results as four findings. | Section 4 is organized as Finding 1-4. | Done |
| Use fixed cohort order, not ranking order. | Section 3 and Section 4 tables use GPT, Claude, Gemini, DeepSeek, Kimi order. | Done |
| Add n or descriptive caveat to main results. | Section 4 states descriptive/not powered for ranking; tables include n in headers or columns. | Done |
| Clarify generated-lore wording: current agent-facing schema exposes evidence-role failures. | Section 4 Finding 3 and Section 5 use this narrower wording. | Done |
| Clarify current vs clarified schema N. | Section 5 states current and clarified generated-lore aggregates each cover 20 tasks × 2 prompts = 40 rows per model. | Done |
| Separate aggregate metrics from illustrative cases. | Section 5 states `ert_032`, `ert_033`, and `ert_096` are audited representatives, not the full rerun. | Done |
| Explain Claude/Gemini generated-lore escape < 1.0 despite no polluted support. | Section 5.1 explains evidence-selection and active-verification sources of failure; derived CSV is `generated_lore_current_schema_failure_decomposition.csv`. | Done |
| Add active-verification scoring rule. | Section 2.6 and Section 6 define exact/machine-checkable action target requirements. | Done |
| Mark `ert_082` active-verification case as illustrative unless more audit supports it. | Section 6 says it is illustrative and adds a 20-row lightweight audit. | Done |
| Add active-verification 10-20 row audit. | `active_verification_action_audit_20.csv` contains 20 rows; Section 6 summarizes labels. | Done |
| Add clarified-schema failure decomposition without API. | `generated_lore_current_schema_failure_decomposition.csv` explains current-schema failure sources. | Done |
| Replace Related Work placeholder with structured outline and TODO citation tags. | Section 7 is now a structured Related Work section with eight subsections and TODO tags, no invented bibliography. | Done |
| Add limitations: mechanism-oriented, not statistically powered for provider ranking. | Section 9 includes this limitation. | Done |
| Add limitations: schema sensitivity is both limitation and agent-interface phenomenon. | Section 9 includes this limitation. | Done |
| Prepare five figure placeholders. | Five SVGs are present in `reports-eha-paper-v1-revision-2026-05-15/`; Section 2 and Section 4 reference them. | Done |

## Generated Revision Artifacts

| File | Purpose |
| --- | --- |
| `generated_lore_current_schema_failure_decomposition.csv` | Explains generated-lore current-schema failures by model and family |
| `active_verification_action_audit_20.csv` | 20-row active-verification action-interface audit |
| `active_verification_action_audit_summary.csv` | Summary of the 20-row action audit |
| `figure_1_eha_task_schematic.svg` | EHA task schematic placeholder |
| `figure_2_capability_decomposition.svg` | Capability decomposition placeholder |
| `figure_3_task_family_breakdown.svg` | Task-family breakdown placeholder |
| `figure_4_generated_lore_role_decomposition.svg` | Generated-lore role decomposition placeholder |
| `figure_5_prompt_hygiene_slope.svg` | Prompt hygiene slope placeholder |
| `report_manifest.json` | Revision artifact manifest |

## Verification Commands

```bash
cat eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/report_manifest.json
cat eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/generated_lore_current_schema_failure_decomposition.csv
cat eha-mvp/results/reports-eha-paper-v1-revision-2026-05-15/active_verification_action_audit_summary.csv
rg -n '^## |^### ' epistemic-hygiene-arena-preprint.md
rg -n 'Dataset Construction|Scoring Contract|Preflight Gate|Finding 1|Finding 2|Finding 3|Finding 4|Related Work|TODO|mechanism-oriented|schema sensitivity' epistemic-hygiene-arena-preprint.md
git diff --check
```

## Residual Work Outside This Revision

- Replace TODO citation tags with verified citations and a bibliography.
- Convert SVG placeholders into final publication figures.
- Add statistical confidence intervals or bootstrap estimates if the paper moves beyond workshop/internal circulation.
