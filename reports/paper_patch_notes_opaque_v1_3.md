# EHA v1.3 Opaque-Repair Paper Patch Notes

Date: 2026-05-15

## Scope

This patch prepares the paper for the v1.3 opaque-ID repair revision. It does not add a new main experiment. It updates the manuscript so final benchmark claims are based on the opaque frontier main run and the associated validation artifacts.

## Main Evidence

- Final benchmark evidence now comes from `eha-mvp/results/reports-eha-frontier-main-opaque-2026-05-15/`.
- The earlier semantic-ID frontier run is treated as invalidated history and is not used for final benchmark claims.
- The opaque main run contains 1000 scored calls: 5 models x 100 tasks x 2 prompt conditions.
- The opaque main run had 0 parse failures, 0 empty outputs, 0 schema-missing rows, and 0 overlength rows.

## ID Leakage Repair

- Added an `ID Leakage Repair and Opaque-ID Validation` subsection.
- Recorded the full prompt artifact audit over 1000 prompt files:
  - `semantic_doc_id_term_hits=0`
  - `semantic_citation_term_hits=0`
  - `hidden_field_files=0`
  - `title_body_audit_id_hits=0`
  - `message_audit_id_hits=0`
- Replaced model-visible semantic example IDs in the paper body with opaque `doc_###` IDs and separate audit-role annotations.

## Baselines

- Added a no-API opaque baseline table:
  - ID-only operational escape: 0.110
  - Metadata-only operational escape: 0.520
  - Simple heuristic operational escape: 0.560
- Added interpretation:
  - ID-only supports the claim that opaque IDs do not carry useful label leakage.
  - Metadata-only and heuristic baselines show that some visible surface cues remain exploitable.
  - Baseline evidence cleanliness should not be read as robust evidence understanding because conservative baselines can avoid polluted support fields by construction.

## Mechanism Cases

- Updated generated-lore text to use opaque IDs and audit-role annotations.
- Preserved the current-schema finding for `gpt-5.4`: belief correctness 1.000, insufficient verdict 1.000, polluted support 1.000, and full escape 0.000.
- Preserved the clarified-schema interpretation: polluted support falls to 0.000 and role escape rises to 1.000 in the audited rerun.
- Updated active verification from the old 20-row sample narrative to the 200-row opaque-run action audit.
- Added action-gate pass rates:
  - Claude: 0.700
  - GPT-5.4: 0.725
  - DeepSeek: 0.575
  - Gemini: 0.425
  - Kimi: 0.375
- Added the recurring miss: contradiction-seeking in buried-primary, false-consensus, and conflicting-evidence conditions.

## Invocation Diagnostics

- Kept the no-temperature invocation profile in the manuscript.
- Recorded the cap/no-cap finding: capped diagnostics could return empty content with `finish_reason=length`, while no-cap profiles returned parseable JSON for those models.
- The opaque main no-cap settings did not produce runaway visible output: DeepSeek averaged 370.340 visible output tokens, Kimi averaged 377.885, both with `overlength_rate=0.0`.

## Files Touched

- `paper/sections/03_model_cohort.tex`
- `paper/sections/04_results.tex`
- `paper/sections/05_generated_lore_case.tex`
- `paper/sections/06_active_verification_case.tex`
- `paper/sections/09_limitations.tex`
- `paper/sections/10_conclusion.tex`
- `paper/appendix/c_model_invocation.tex`
- `paper/appendix/d_extra_tables.tex`
- `paper/appendix/e_artifacts.tex`
- `paper/tables/opaque_baselines.tex`
- `paper/main.pdf`
