# Generated-Lore Evidence-Role Audit Side Note

This appendix does not revise the main frontier table. It interprets the generated-lore slice by separating belief correctness from machine-readable evidence-role discipline.

## Existing-Output Decomposition

For `gpt-5.4` on generated-lore records, the model usually recognizes the claim as insufficient but often places polluted material into `supporting_evidence`.

- n: `40`
- belief correctness: `1.000`
- insufficient verdict rate: `1.000`
- rejected pollutant rate: `1.000`
- polluted supporting evidence rate: `0.900`
- dual-role pollutant rate: `0.875`
- full escape: `0.100`

The interpretation should therefore be: GPT-5.4 is not simply fooled by generated lore at the belief layer. The failure is mainly evidence-role confusion in structured fields that downstream systems may consume.

## Why This Matters

A human reader can often see that the prose rejects generated lore. A downstream system may not read the prose; it may read `supporting_evidence`. If polluted sources appear there, the agent interface has converted rejected material into machine-actionable support.

## Schema Clarification Mini-Rerun

| schema_variant | model | prompt_condition | n | belief_correctness_rate | polluted_supporting_evidence_rate | dual_role_pollutant_rate | role_escape | full_escape |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clarified_schema | claude-opus-4-7 | all | 40 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| clarified_schema | claude-opus-4-7 | epistemic_hygiene_instruction | 20 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| clarified_schema | claude-opus-4-7 | standard_answer | 20 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| clarified_schema | gemini-3.1-pro-preview | all | 40 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| clarified_schema | gemini-3.1-pro-preview | epistemic_hygiene_instruction | 20 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| clarified_schema | gemini-3.1-pro-preview | standard_answer | 20 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| clarified_schema | gpt-5.4 | all | 40 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| clarified_schema | gpt-5.4 | epistemic_hygiene_instruction | 20 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| clarified_schema | gpt-5.4 | standard_answer | 20 | 1.000 | 0.000 | 0.000 | 1.000 |  |
| current_schema | claude-opus-4-7 | all | 40 | 1.000 | 0.000 | 0.000 |  | 0.600 |
| current_schema | claude-opus-4-7 | epistemic_hygiene_instruction | 20 | 1.000 | 0.000 | 0.000 |  | 0.600 |
| current_schema | claude-opus-4-7 | standard_answer | 20 | 1.000 | 0.000 | 0.000 |  | 0.600 |
| current_schema | gemini-3.1-pro-preview | all | 40 | 1.000 | 0.000 | 0.000 |  | 0.425 |
| current_schema | gemini-3.1-pro-preview | epistemic_hygiene_instruction | 20 | 1.000 | 0.000 | 0.000 |  | 0.400 |
| current_schema | gemini-3.1-pro-preview | standard_answer | 20 | 1.000 | 0.000 | 0.000 |  | 0.450 |
| current_schema | gpt-5.4 | all | 40 | 1.000 | 0.900 | 0.875 |  | 0.100 |
| current_schema | gpt-5.4 | epistemic_hygiene_instruction | 20 | 1.000 | 0.800 | 0.800 |  | 0.200 |
| current_schema | gpt-5.4 | standard_answer | 20 | 1.000 | 1.000 | 0.950 |  | 0.000 |

## Reporting Rule

Do not say `GPT-5.4 cannot detect generated lore`. Say: `GPT-5.4 often detects generated lore in natural language, but the current schema exposes unstable evidence-role assignment in machine-readable fields.`
