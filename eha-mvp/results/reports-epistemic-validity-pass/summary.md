# EHA Validity Pass

This is an offline validity pass for Epistemic Resilience Table v1. It does not add tasks, alter gold labels, or make new API calls.

## Outputs

| Artifact | Purpose |
| --- | --- |
| `parse_repair_audit.csv` | Groups original parse failures and token patterns; records that repair was not attempted because raw responses are unavailable. |
| `human_audit_sample.jsonl` | 80-case manual audit pack with task, prediction, scorer metrics, visible evidence, and blank audit form. |
| `evidence_cleanliness_failure_taxonomy.csv` | Row-level taxonomy for dirty supporting evidence. |
| `heuristic_baseline_appendix.csv` | Appendix-ready heuristic-vs-model slice comparison with explicit gold-metadata caveat. |
| `paper_figures_manifest.md` | Figure/table source map and caveats. |
| `prompt_to_artifact_checklist.md` | Requirement-to-artifact checklist for this pass. |
| `audit_manifest.json` | Machine-readable diagnostics for this pass. |
| `human_audit_completed.jsonl` / `.csv` | Completed 80-row human audit produced by tmux Codex CLI `gpt-5.5` xhigh worker. |
| `human_audit_summary.md` | Human-audit method, bucket counts, scorer agreement, edge cases, and paper-use guidance. |
| `../reports-epistemic-parse-repair-gpt5mini/` | Raw-response-preserving parse-repair attempt and API availability blocker report. |

## Key Findings

- `openai/gpt-5-mini` has 124 parse failures in the final 200-record run. The failures are concentrated near the output cap, so low escape should remain a parse/schema caveat until a raw-response-preserving rerun is complete.
- Evidence-cleanliness failures are common enough to justify manual review: 125 total dirty-support rows, including 106 for `openai/gpt-5.4-mini`.
- Dirty-support taxonomy counts: {'contaminated_support': 125, 'generated_lore_cited': 34, 'duplicate_upstream_treated_as_independent': 45, 'stale_evidence_cited': 25}.
- Human audit pack counts: {'generated_lore': 20, 'false_consensus': 20, 'buried_primary': 20, 'active_verification': 20}.
- The heuristic comparison is useful as a plumbing and upper-bound appendix, but it is not a fair model baseline because the heuristic uses gold metadata hidden from the model prompt.
- Human audit is now complete: 80/80 rows audited, reviewed by tmux Codex CLI reviewer with `status: no_issues`. Scorer agreement counts are yes: 25, no: 8, uncertain: 47; the main edge case is polluted support/selection fields where prose often rejects the same evidence.
- Parse repair was attempted for all 124 original `openai/gpt-5-mini` parse failures, with raw prompt/response artifacts preserved. All OpenAI-provider calls were blocked upstream with 403 provider errors, so repaired metrics remain unavailable and should not be interpreted as a failed repair method.

## Heuristic All-Slice Snapshot

| model_or_baseline | prompt_condition | n | epistemic_escape | evidence_cleanliness | primary_seeking_rate | generated_lore_avoidance_rate | uses_gold_metadata | is_model_comparable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| heuristic-sim | epistemic_hygiene_instruction | 100 | 0.760 | 1.000 | 0.320 | 1.000 | 1 | 0 |
| heuristic-sim | standard_answer | 100 | 0.760 | 0.960 | 0.320 | 1.000 | 1 | 0 |

## Completion Boundary

This pass now includes a completed and reviewed 80-row human audit. It does not provide repaired `gpt-5-mini` metrics because the configured OpenAI-provider route is blocked; repaired numbers remain unavailable and are not eligible for the main table.

```json
{
  "name": "EHA Validity Pass",
  "task_content_changed": false,
  "gold_labels_changed": false,
  "api_calls_made": false,
  "inputs": {
    "task_dir": "data/epistemic-resilience-v1",
    "run_dir": "results/runs/epistemic-resilience-v1-api-final",
    "report_dir": "results/reports-epistemic-resilience-v1",
    "heuristic_report_dir": "results/reports-epistemic-resilience-v1-heuristic"
  },
  "outputs": {
    "parse_repair_audit_rows": 114,
    "human_audit_sample_rows": 80,
    "evidence_cleanliness_failure_rows": 125,
    "heuristic_baseline_appendix_rows": 60
  },
  "human_audit_bucket_counts": {
    "generated_lore": 20,
    "false_consensus": 20,
    "buried_primary": 20,
    "active_verification": 20
  },
  "parse_failure_counts_by_model": {
    "openai/gpt-5-mini": 124
  },
  "taxonomy_label_counts": {
    "contaminated_support": 125,
    "generated_lore_cited": 34,
    "duplicate_upstream_treated_as_independent": 45,
    "stale_evidence_cited": 25
  },
  "raw_response_available": false,
  "repair_attempted": false,
  "repair_blocker": "Final run persisted predictions and parse errors, but not raw unparsed response text."
}
```
