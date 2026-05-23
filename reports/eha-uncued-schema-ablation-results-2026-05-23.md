# EHA-Uncued Phase 1.1 Schema Ablation Results

Date: 2026-05-23

This is exploratory Phase 1.1 evidence. It does not revise the Phase 1 main table and does not use old cued model outputs.

## Scope

- Run directory: `results/reports-eha-uncued-schema-ablation-2026-05-23`
- Selected source tasks: 16
- Rows: 128 latest records (130 raw records)
- Models: gpt-5.5, gemini-3.1-pro-preview
- Schemas: current, clarified, minimal, diagnostic_no_hygiene
- View: `neutral_metadata_visible`
- Prompt condition: `standard_answer`
- Cost spent: USD 1.890321

## Prompt And Leakage Audits

- Prompt audit passed: True
- Stored hidden-label audit passed: True

## By Schema And Model

| schema_variant | model | n | parse_success | schema_missing | belief_correctness | polluted_in_support | role_escape | operational_escape_proxy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clarified | gemini-3.1-pro-preview | 16 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.875 |
| clarified | gpt-5.5 | 16 | 1.000 | 0.000 | 0.938 | 0.000 | 0.938 | 0.938 |
| current | gemini-3.1-pro-preview | 16 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.938 |
| current | gpt-5.5 | 16 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 1.000 |
| diagnostic_no_hygiene | gemini-3.1-pro-preview | 16 | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.875 |
| diagnostic_no_hygiene | gpt-5.5 | 16 | 1.000 | 0.000 | 1.000 | 0.000 | 0.500 | 0.500 |
| minimal | gemini-3.1-pro-preview | 16 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| minimal | gpt-5.5 | 16 | 1.000 | 0.000 | 1.000 | 1.000 | 0.000 | 0.000 |

## Manual Audit Summary

- Review mode: local Codex-assisted manual schema-ablation audit
- Reviewed rows: 16
- Scorer fixes needed: 0
- Independent human review: false

## Reporting Boundary

Allowed claim: in this small role-uncued Phase 1.1 ablation, evidence was held fixed while the structured output interface changed. The result can support only schema/interface sensitivity claims.
