# EHA-Uncued Paper Rewrite Overnight Results

Date: 2026-05-25

## Final Decision

Decision: `ready_for_blind_review`.

The rewritten paper now centers polluted evidence ecologies, provenance discipline, source independence, pollutant rejection, shortcut boundaries, and executable verification behavior. The old belief-correctness versus operational-escape separation is retained only as a schema/scorer-sensitive diagnostic view.

## Audit Sessions

| Audit | Status | Paper impact |
| --- | --- | --- |
| `audit-support-ambiguity` | `pass_with_qualifications` | Added support-ambiguity sensitivity result: 71/72 target generated-lore strict failures close under prose-aware rescoring; one residual dirty-support failure named. |
| `audit-timestamp-semantics` | `issues_found` | Added dataset README and paper qualifications that timestamps are synthetic, model-visible, and non-evidential. |
| `audit-citation-cycles` | `pass_with_qualifications` | Added dataset/paper qualification that false-consensus citation cycles are synthetic polluted echo-chain structure, not independent corroboration. |
| `audit-shortcut-boundary` | `issues_found` | Added shortcut-boundary table and limitations; removed broad shortcut-resistance/model-ranking claims. |
| `audit-claim-consistency` | `issues_found` | Removed old separation headline, provider ordering prose, agent-readiness language, and over-robustness phrasing. |
| `audit-final-paper-claim-consistency` | `pass_with_qualifications` | Found no P0 overclaim and no unresolved P1 conflict after rewrite. |

## Paper Files Edited

- `paper/sections/00_abstract.tex`
- `paper/sections/01_intro.tex`
- `paper/sections/03_uncued_dataset_design.tex`
- `paper/sections/04_leakage_controls.tex`
- `paper/sections/05_metrics_scoring.tex`
- `paper/sections/07_results.tex`
- `paper/sections/08_schema_interface.tex`
- `paper/sections/10_limitations.tex`
- `paper/sections/12_artifact.tex`
- `paper/sections/13_conclusion.tex`
- `paper/appendices/leakage_shortcut_methods.tex`
- `paper/appendices/robustness_mini_suite.tex`
- `paper/tables/evidence_hygiene_vs_belief.tex`
- `paper/tables/robustness_paired_deltas.tex`

## Tables And Artifacts

Added tables:

- `paper/tables/failure_decomposition_summary.tex`
- `paper/tables/support_ambiguity_sensitivity.tex`
- `paper/tables/positive_evidence_contract.tex`
- `paper/tables/shortcut_boundary_summary.tex`

Recaptioned or narrowed:

- `paper/tables/evidence_hygiene_vs_belief.tex`
- `paper/tables/robustness_paired_deltas.tex`

Other closure artifacts:

- `Makefile` delegates root `make pdf` to `paper/Makefile` so the runbook command works.
- `eha-mvp/data/uncued-pilot-v1/README.md` documents timestamp and citation/echo-chain semantics.
- `paper/main.pdf` rebuilt successfully.
- `eha-mvp/results/reports-eha-uncued-paper-rewrite-overnight-2026-05-25/verification.json` records verification evidence.

## Verification

- Core-claim overnight verifier: pass.
- Relevant pytest suite: `30 passed in 2.56s`.
- PDF build: pass; Tectonic emitted underfull/overfull hbox warnings in existing appendix/table text.
- `git diff --check`: pass.

## Remaining Risks

- This is still a synthetic diagnostic pilot, not an open-web benchmark or production-readiness test.
- Shortcut baselines remain competitive overall; above-shortcut evidence is localized.
- Support-ambiguity recovery is a local prose-aware sensitivity audit, not a replacement scorer or independent human validation.
- Timestamp and citation-cycle semantics are now documented, but they remain synthetic-artifact qualifications.
- Model differences remain descriptive.

## Current Git Status

```text
M eha-mvp/pyproject.toml
 M paper/appendices/leakage_shortcut_methods.tex
 M paper/appendices/robustness_mini_suite.tex
 M paper/main.pdf
 M paper/sections/00_abstract.tex
 M paper/sections/01_intro.tex
 M paper/sections/03_uncued_dataset_design.tex
 M paper/sections/04_leakage_controls.tex
 M paper/sections/05_metrics_scoring.tex
 M paper/sections/07_results.tex
 M paper/sections/08_schema_interface.tex
 M paper/sections/10_limitations.tex
 M paper/sections/12_artifact.tex
 M paper/sections/13_conclusion.tex
 M paper/tables/evidence_hygiene_vs_belief.tex
 M paper/tables/robustness_paired_deltas.tex
?? Makefile
?? eha-mvp/data/uncued-pilot-v1/README.md
?? eha-mvp/eha/uncued_core_claim_common.py
?? eha-mvp/eha/uncued_core_claim_report.py
?? eha-mvp/eha/uncued_data_sanity.py
?? eha-mvp/eha/uncued_failure_decomposition.py
?? eha-mvp/eha/uncued_positive_contract.py
?? eha-mvp/eha/uncued_support_ambiguity.py
?? eha-mvp/results/reports-eha-uncued-core-claim-overnight-2026-05-25/
?? eha-mvp/results/reports-eha-uncued-paper-rewrite-overnight-2026-05-25/
?? eha-mvp/tests/test_uncued_core_claim_report.py
?? eha-mvp/tests/test_uncued_data_sanity.py
?? eha-mvp/tests/test_uncued_failure_decomposition.py
?? eha-mvp/tests/test_uncued_positive_contract.py
?? eha-mvp/tests/test_uncued_support_ambiguity.py
?? paper/tables/failure_decomposition_summary.tex
?? paper/tables/positive_evidence_contract.tex
?? paper/tables/shortcut_boundary_summary.tex
?? paper/tables/support_ambiguity_sensitivity.tex
?? reports/eha-uncued-core-claim-overnight-results-2026-05-25.md
?? reports/eha-uncued-core-claim-overnight-runbook-2026-05-25.md
?? reports/eha-uncued-paper-reframing-decision-2026-05-25.md
?? reports/eha-uncued-paper-rewrite-claim-audit-2026-05-25.md
?? reports/eha-uncued-paper-rewrite-overnight-results-2026-05-25.md
?? reports/eha-uncued-paper-rewrite-overnight-runbook-2026-05-25.md
?? reports/eha_uncued_core_claim_overnight_results.json
```
