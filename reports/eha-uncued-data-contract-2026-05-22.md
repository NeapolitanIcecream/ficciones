# EHA-Uncued Data Contract

Date: 2026-05-22

This contract makes `role_uncued` executable. The dataset may contain task-relevant content, but model-visible surfaces must not explicitly label evidence roles, hidden verdicts, contamination labels, or semantic document IDs.

## Leakage Levels

- L0 hidden-label leakage: hidden role and gold fields are forbidden in model-visible JSON.
- L1 semantic ID leakage: visible IDs and citations must not encode evidence roles.
- L2 material-role phrase leakage: visible text must not state material evidence roles.
- L3 conclusion cue leakage: visible text must not state the answer or verdict.
- L4 allowed relational evidence: timestamps, citations, contradictions, and numeric disagreements are allowed when they do not label roles.

## Machine-Readable Contract

```json
{
  "name": "EHA-Uncued data contract",
  "date": "2026-05-22",
  "preferred_term": "role_uncued",
  "avoid_as_main_term": "content_neutral",
  "levels": {
    "L0_hidden_label_leakage": "model-visible JSON must not expose hidden role or gold fields",
    "L1_semantic_id_leakage": "visible IDs and citations must not encode evidence roles or gold semantics",
    "L2_material_role_phrase_leakage": "visible title/body/source metadata must not state material evidence roles",
    "L3_conclusion_cue_leakage": "visible task text must not state the target answer or verdict",
    "L4_allowed_relational_evidence": [
      "timestamps",
      "citations among visible documents",
      "numeric disagreements",
      "named-entity disagreements",
      "version references that do not label document roles",
      "same-source repetition that is observable from citations rather than role words"
    ]
  },
  "hidden_field_names": [
    "condition",
    "contamination",
    "gold_role",
    "gold_verdict",
    "hidden_role",
    "internal_doc_id",
    "known_contaminants",
    "role",
    "semantic_id",
    "supports_gold_verdict",
    "upstream_root"
  ],
  "semantic_id_terms": [
    "clean",
    "contaminant",
    "generated",
    "gold",
    "lore",
    "pollutant",
    "primary",
    "refute",
    "repost",
    "root",
    "secondary",
    "stale",
    "support"
  ],
  "forbidden_role_phrases": [
    "primary",
    "secondary",
    "contaminant",
    "pollutant",
    "generated lore",
    "wiki-style",
    "authoritative-looking",
    "copied from the same upstream story",
    "raw records",
    "signed record",
    "reviewer sign-off",
    "does not settle",
    "no primary evidence",
    "not independent",
    "repeats the same claim",
    "background material",
    "orientation material",
    "insufficient evidence"
  ],
  "direct_answer_cue_patterns": [
    "\\bthe answer is\\b",
    "\\bcorrect answer\\b",
    "\\bgold verdict\\b",
    "\\bverdict\\s*:",
    "\\bshould answer\\b",
    "\\bmust answer\\b",
    "\\btherefore\\s+(supported|refuted|insufficient)\\b",
    "\\bclaim\\s+is\\s+(supported|refuted|insufficient|true|false)\\b"
  ],
  "allowed_metadata_by_view": {
    "neutral_metadata_visible": [
      "doc_id",
      "title",
      "source_type",
      "timestamp",
      "visible_citations"
    ],
    "neutral_metadata_hidden": [
      "doc_id",
      "title",
      "source_type",
      "timestamp",
      "visible_citations"
    ]
  },
  "baseline_thresholds": {
    "id_only": {
      "operational_epistemic_escape_max": 0.1,
      "verdict_accuracy_max": 0.4
    },
    "document_order_only": {
      "operational_epistemic_escape_max": 0.15,
      "verdict_accuracy_max": 0.45
    },
    "title_only": {
      "operational_epistemic_escape_max": 0.25,
      "role_reconstruction_accuracy_max": 0.45
    },
    "source_type_only:hidden": {
      "operational_epistemic_escape_max": 0.1
    },
    "source_type_only:visible": {
      "operational_epistemic_escape_max": 0.25
    },
    "metadata_only:hidden": {
      "operational_epistemic_escape_max": 0.2
    },
    "metadata_only:visible": {
      "operational_epistemic_escape_max": 0.35
    },
    "timestamp_only": {
      "verdict_accuracy_max": 0.55
    },
    "citation_graph_only": {
      "operational_epistemic_escape_max": 0.35,
      "verdict_accuracy_max": 0.6
    },
    "claim_overlap_only": {
      "operational_epistemic_escape_max": 0.35,
      "polluted_support_rate_max": 0.6
    },
    "cue_phrase_only": {
      "operational_epistemic_escape_max": 0.1
    },
    "always_insufficient": {
      "operational_epistemic_escape_max": 0.3
    }
  },
  "human_review_rubric": {
    "critical": "reviewer can answer the task or identify gold role from wording alone",
    "high": "visible text directly states source independence, insufficiency, or material role",
    "medium": "realistic metadata cue that is strong enough to require balance review",
    "low": "weak cue allowed only if balanced across roles and conditions"
  },
  "model_call_go_no_go_rule": "Do not call frontier models until leakage, shortcut baseline, and surface-review gates pass with zero critical/high leakage and zero direct-answer cue rows."
}
```

## Go/No-Go Rule

Do not call frontier models until leakage, shortcut baseline, and surface-review gates pass with zero critical/high leakage and zero direct-answer cue rows.
