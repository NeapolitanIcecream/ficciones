# EHA Step 2 Phase 2S Critical-Risk Repair Audit

Date: 2026-05-16

- Status: `blocked`
- Critical-risk repair ready: `false`

This is a no-API audit over already scored v8-v11 structural calibration rows. It decomposes critical-risk failures into exact rows, false negatives, false positives, and mixed errors so the next schema change has a concrete target.

## Run Summary

| run | n | ready | claim | contam | macro_f1 | exact_rows | fn_rows | fp_rows | mixed_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini | 35 | false | 0.886 | 0.000 | 0.369 | 0.257 | 0.543 | 0.457 | 0.257 |
| reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini | 35 | false | 0.886 | 0.029 | 0.299 | 0.257 | 0.657 | 0.600 | 0.514 |
| reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini | 35 | false | 0.886 | 0.086 | 0.404 | 0.143 | 0.600 | 0.514 | 0.257 |
| reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini | 35 | false | 0.857 | 0.000 | 0.240 | 0.229 | 0.743 | 0.571 | 0.543 |

## Top Repair Focus

| run | top_repair_focus | fn_counts | fp_counts |
| --- | --- | --- | --- |
| reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini | require a visible source-chain problem, not same-root repetition or generic reposting | citation_laundering:5, conflicting_evidence:5, false_consensus:5, generated_lore:2, no_primary_source:1, partial_support:5, stale_evidence:2 | citation_laundering:3, conflicting_evidence:8, false_consensus:2, generated_lore:1, no_primary_source:3, stale_evidence:1 |
| reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini | require repeated same-root apparent support that could dominate the verdict, not ordinary visible repetition | citation_laundering:4, conflicting_evidence:6, false_consensus:3, generated_lore:4, no_primary_source:2, partial_support:5, stale_evidence:4 | citation_laundering:6, conflicting_evidence:7, false_consensus:7, generated_lore:2, no_primary_source:4, stale_evidence:1 |
| reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini | require repeated same-root apparent support that could dominate the verdict, not ordinary visible repetition | citation_laundering:4, conflicting_evidence:6, false_consensus:4, generated_lore:3, no_primary_source:5, partial_support:4, stale_evidence:2 | citation_laundering:3, conflicting_evidence:7, false_consensus:4, generated_lore:3, no_primary_source:2, partial_support:1 |
| reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini | require a visible source-chain problem, not same-root repetition or generic reposting | citation_laundering:5, conflicting_evidence:4, false_consensus:2, generated_lore:4, no_primary_source:4, partial_support:5, stale_evidence:5 | citation_laundering:5, conflicting_evidence:11, false_consensus:11, generated_lore:1, no_primary_source:3, partial_support:1 |

## Recommended Next Contract

- keep support-role guard as a separate deterministic consumer-safety check
- use evidence_diagnostics_v12_critical_risk_contract to add explicit positive and negative examples for false_consensus, citation_laundering, and partial_support
- separate visible rejected pollution from verdict-critical risks in every label definition
- require exact critical-risk rows on a fixed no-API audit before any full C-only API spend

## Non-Claims

- not new model evidence
- not a passing structural repair
- not permission to run a full C-only or 500-1000 task expansion
