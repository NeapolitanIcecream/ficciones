# Paper Figures Manifest

| Figure/Table | Source artifact | Use | Caveat |
| --- | --- | --- | --- |
| Main epistemic resilience table | `../reports-epistemic-resilience-v1/main_table.csv` | Primary model x prompt family-average escape table. | Do not interpret as absolute model ranking because parse and schema compliance differ by model. |
| Parse failure caveat table | `parse_repair_audit.csv` | Shows where parse failures concentrate and why repaired metrics are not yet available. | Raw responses were not persisted in the final run; repair requires rerun. |
| Evidence cleanliness failure mechanism table | `evidence_cleanliness_failure_taxonomy.csv` | Audits dirty support citations by condition/family/model. | Automatic taxonomy should be validated against the human sample. |
| Human audit pack | `human_audit_sample.jsonl` | 80-case manual review pack for generated lore, false consensus, buried primary, and active verification. | Requires human completion before being used as validation evidence. |
| Heuristic baseline appendix | `heuristic_baseline_appendix.csv` | Compares existing heuristic smoke-test slices with LLM slices. | The heuristic uses gold metadata and is not a fair model baseline. |
| Generated lore profile | `../reports-epistemic-resilience-v1/by_condition.csv`, `heuristic_baseline_appendix.csv` | Isolates generated-lore avoidance and escape. | Generated-lore labels are synthetic and need manual audit. |
| Active verification profile | `../reports-epistemic-resilience-v1/by_family.csv`, `heuristic_baseline_appendix.csv` | Shows action-selection failures separate from answer correctness. | Active-verification scorer should be checked for prompt/tool affordance artifacts. |
| Matrix L4 evidence-environment case study | `../reports-matrix-v1.3/l4_primary_recovery_audit.csv` | Connects earlier RAG retrieval results to evidence environment construction. | Use as mechanism case study, not as the main ERT v1 result. |
