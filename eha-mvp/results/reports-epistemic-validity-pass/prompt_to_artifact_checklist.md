# Validity Pass Prompt-to-Artifact Checklist

| Requirement | Evidence | Status |
| --- | --- | --- |
| Understand the current stage report. | Input report `../../../reports/eha-epistemic-resilience-v1-stage-report-2026-05-14.md` was used to identify the ERT v1 results and caveats. | Done |
| Continue from the user-provided research memo without expanding the benchmark. | This pass creates validation artifacts only; `task_content_changed=false` and `gold_labels_changed=false` in `audit_manifest.json`. | Done |
| Audit `gpt-5-mini` parse failures. | `parse_repair_audit.csv` groups parse success, parse errors, and token usage by model/prompt/family/condition. | Done, offline only |
| Do not claim repaired `gpt-5-mini` metrics without raw responses. | `parse_repair_audit.csv` sets `repair_attempted=0` and `raw_response_available=0`; summary states rerun is required for repair. | Done |
| Export manual audit pack. | `human_audit_sample.jsonl` contains 80 cases across generated_lore, false_consensus, buried_primary, and active_verification. | Done |
| Analyze evidence cleanliness failures. | `evidence_cleanliness_failure_taxonomy.csv` contains row-level dirty-support taxonomy. | Done |
| Promote heuristic smoke test into appendix-quality comparison. | `heuristic_baseline_appendix.csv` reports comparable slices and flags heuristic gold-metadata use. | Done |
| Prepare paper figure/table manifest. | `paper_figures_manifest.md` maps figures to source artifacts and caveats. | Done |
| Preserve machine-readable diagnostics. | `audit_manifest.json` records input paths, row counts, sample counts, and non-mutation flags. | Done |
| Complete human audit through tmux Codex CLI using `gpt-5.5` xhigh. | `human_audit_completed.jsonl`, `human_audit_completed.csv`, and `human_audit_summary.md` contain all 80 audited rows. | Done |
| Review human audit completion. | `audit_manifest.json` records `human_audit_review_status=no_issues`; reviewer verified row counts, required fields, sample preservation, summary counts, and representative rows. | Done |
| Attempt `gpt-5-mini` parse repair with `LLM_API_KEY` / `LLM_BASE_URL`. | `../reports-epistemic-parse-repair-gpt5mini/` contains raw-response-preserving repair attempt for 124 failed rows; `api_availability_check.md` records upstream 403 OpenAI-provider blocker. | Done, blocked by API route |

## Audit Snapshot

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
