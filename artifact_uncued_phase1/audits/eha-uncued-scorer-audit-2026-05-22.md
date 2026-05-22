# EHA-Uncued Phase 14 Scorer Audit

Date: 2026-05-22

Reviewed rows: 40
Scorer disagreement rate: 0.000
Systematic scorer bug found: false

This audit uses a balanced 40-row sample from the Phase 13 scored predictions. It independently recomputes the audited metrics from scorer-visible gold fields and model outputs. The audit is local and Codex-assisted; it is not an independent human-subject review.

## Balance

| axis | counts |
| --- | --- |
| model | {"claude-opus-4-7": 10, "deepseek-v4-pro": 10, "gemini-3.1-pro-preview": 10, "gpt-5.5": 10} |
| view | {"neutral_metadata_hidden": 20, "neutral_metadata_visible": 20} |
| condition | {"buried_primary": 8, "clean": 8, "conflicting_evidence": 8, "false_consensus": 8, "generated_lore": 8} |
| family | {"active_verification": 8, "evidence_selection": 16, "packet_judgment": 16} |
| operational_escape | {"0.0": 20, "1.0": 20} |

## Summary JSON

```json
{
  "review_mode": "local_codex_assisted_manual_scorer_audit",
  "independent_human_review": false,
  "reviewed_rows": 40,
  "scorer_disagreement_count": 0,
  "scorer_disagreement_rate": 0.0,
  "systematic_scorer_bug_found": false,
  "rescoring_required": false,
  "by_model": {
    "claude-opus-4-7": 10,
    "deepseek-v4-pro": 10,
    "gemini-3.1-pro-preview": 10,
    "gpt-5.5": 10
  },
  "by_view": {
    "neutral_metadata_hidden": 20,
    "neutral_metadata_visible": 20
  },
  "by_condition": {
    "buried_primary": 8,
    "clean": 8,
    "conflicting_evidence": 8,
    "false_consensus": 8,
    "generated_lore": 8
  },
  "by_family": {
    "active_verification": 8,
    "evidence_selection": 16,
    "packet_judgment": 16
  },
  "by_operational_escape": {
    "0.0": 20,
    "1.0": 20
  },
  "caveat": "This is a local Codex-assisted scorer audit, not an independent human-subject review."
}
```
