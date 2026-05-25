# Codex Schema Ablation Audit Summary

Date: 2026-05-25

This is a Codex manual audit of the role-uncued Phase 1.1 schema-ablation scorer and reporting claims. It is not independent human review.

- Audit scope: full_latest_complete_rows
- Rows audited: 128
- Rows with scorer fix needed: 0
- Material disagreements: 0
- Blocking disagreements: 0
- Paper claims supported: 8
- Paper claims needing revision: 0
- Independent human review: false

A full Codex manual audit of the Phase 1.1 schema-ablation rows found no material scorer disagreements.

## Claim Review

| claim | status | evidence | suggested_text |
| --- | --- | --- | --- |
| Phase 1.1 is exploratory and not a replacement for Phase 1 main results. | supported | Result report and paper schema section label the slice exploratory and bounded. |  |
| Old cued results are not used. | supported | Report and paper quarantine the old cued outputs; audit inputs use uncued-pilot-v1 and the 2026-05-23 run directory. |  |
| The ablation holds evidence fixed and varies structured output interface. | supported | The paper and report state that the evidence packet was held fixed while the structured interface varied. |  |
| Minimal schema placed polluted evidence in support fields on all rows for both evaluated models. | supported | Minimal polluted_in_support by model: {"gemini-3.1-pro-preview": 1.0, "gpt-5.5": 1.0}; audited rows: 128. |  |
| Current and clarified avoided polluted support in this slice. | supported | Current polluted_in_support: {"gemini-3.1-pro-preview": 0.0, "gpt-5.5": 0.0}; clarified polluted_in_support: {"gemini-3.1-pro-preview": 0.0, "gpt-5.5": 0.0}. |  |
| Diagnostic-without-hygiene showed mixed role allocation, especially for GPT-5.5. | supported | Diagnostic_no_hygiene role_escape by model: {"gemini-3.1-pro-preview": 1.0, "gpt-5.5": 0.5}. |  |
| The paper does not claim independent human review for this audit. | supported | The result report sets independent_human_review=false and limitations describe the relevant reviews as local/Codex-assisted. |  |
| The paper does not claim schema wording explains every Phase 1 gap. | supported | The paper explicitly narrows schema wording to an interface-sensitivity factor. |  |
