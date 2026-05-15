# EHA v1.2 Opaque-ID Repair Stage Report

Date: 2026-05-15

## Objective

Complete the first validity repair required by `ficciones-research-0515-7.md`: quarantine the semantic-ID run as non-final evidence, replace model-visible document IDs with opaque per-task IDs, verify hidden fields and semantic IDs are absent from prompts, add leakage baselines, rerun the full frontier cohort, and rerun the generated-lore and active-verification audits on the repaired setup.

## Prompt-To-Artifact Checklist

| Requirement from 0515-7 | Evidence | Status |
| --- | --- | --- |
| Keep current leaky run, but do not use it as final benchmark evidence | `reports/eha-v1.2-id-leakage-audit-2026-05-15.md`; caveat added to `paper/sections/09_limitations.tex` | Done |
| Replace model-visible IDs with opaque per-task IDs | `eha.epistemic_resilience.opaque_doc_id_view`; prompt artifacts show `model_visible_doc_id_policy=opaque_per_task` | Done |
| Ensure IDs contain no role words | `opaque_full_prompt_artifact_audit_summary.json`: `semantic_doc_id_term_hits=0` | Done |
| Randomize ID assignment per task | `opaque_doc_id_view` uses deterministic SHA-256 seeded shuffle per `task_id` | Done |
| Remap visible citations | Full prompt audit: `semantic_citation_term_hits=0`; `non_opaque_citation_count=0` | Done |
| Keep scorer-side gold/audit labels internal | Model outputs are translated back to audit IDs before scoring; postprocess leaves `opaque_doc_ref_hits_in_prediction=0` | Done |
| Strip hidden fields from model-visible prompt | Full prompt audit: `hidden_field_files=0`; `visible_audit_hidden_field_files=0` | Done |
| Replace old IDs in title/body text | Full prompt audit: `title_body_audit_id_hits=0`; `message_audit_id_hits=0` | Done |
| Add ID-only baseline | `id_only_baseline.csv`, `id_only_baseline_summary.csv` | Done |
| Add metadata-only baseline | `metadata_only_baseline.csv`, `metadata_only_baseline_summary.csv` | Done |
| Add simple heuristic baseline | `heuristic_baseline.csv`, `heuristic_baseline_summary.csv` | Done |
| Full 1000-call opaque rerun | `results/reports-eha-frontier-main-opaque-2026-05-15/`, 1000 unique rows, 0 parse failures, 0 empty outputs | Done |
| Opaque generated-lore rerun/audit | `results/reports-eha-generated-lore-role-audit-opaque-2026-05-15/`, 200 current-schema rows + 120 clarified-schema rows | Done |
| Opaque active-verification audit | `results/reports-eha-active-verification-audit-opaque-2026-05-15/`, 200 active-verification rows | Done |
| Empty-output length-limit diagnosis | `reports/supported-mainstream-models-2026-05-14.md`; `model-selection-empty-output-cap-vs-nocap-2026-05-15-rerun.json` | Done |

## Full Opaque Run

Output directory:

```text
eha-mvp/results/reports-eha-frontier-main-opaque-2026-05-15/
```

Run integrity:

- Records: 1000 rows, 1000 unique `(model, task, prompt, budget)` keys, 0 duplicates.
- Per model: 200 rows each for `gpt-5.4`, `claude-opus-4-7`, `gemini-3.1-pro-preview`, `deepseek-v4-pro`, and `kimi-k2.6`.
- Parse failures: 0.
- Empty outputs: 0.
- Schema missing: 0.
- Overlength rate: 0 for every model.
- Recorded cost: `$4.031855`.

Main model metrics:

| Model | n | Operational escape | Belief | Evidence clean | Uncertainty | Verification action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 200 | 0.830 | 0.960 | 0.945 | 0.960 | 0.567 |
| `gemini-3.1-pro-preview` | 200 | 0.800 | 0.960 | 1.000 | 0.960 | 0.458 |
| `deepseek-v4-pro` | 200 | 0.775 | 0.960 | 0.905 | 0.960 | 0.483 |
| `gpt-5.4` | 200 | 0.745 | 0.960 | 0.705 | 0.960 | 0.425 |
| `kimi-k2.6` | 200 | 0.710 | 0.960 | 0.940 | 0.960 | 0.450 |

The repaired results differ materially from the leaky semantic-ID run. The old run should not be used as final evidence.

## Prompt Audit

Full prompt audit files:

- `eha-mvp/results/reports-eha-frontier-main-opaque-2026-05-15/opaque_full_prompt_artifact_audit.csv`
- `eha-mvp/results/reports-eha-frontier-main-opaque-2026-05-15/opaque_full_prompt_artifact_audit_summary.json`

Summary:

| Check | Count |
| --- | ---: |
| prompt files audited | 1000 |
| non-opaque policy files | 0 |
| missing mapping files | 0 |
| non-opaque doc IDs | 0 |
| semantic doc-ID term hits | 0 |
| non-opaque visible citations | 0 |
| semantic citation term hits | 0 |
| audit IDs in title/body | 0 |
| audit IDs in model-visible messages | 0 |
| hidden-field files | 0 |

Clarified generated-lore prompt audit:

- `eha-mvp/results/reports-eha-generated-lore-role-audit-opaque-2026-05-15/clarified_prompt_artifact_audit_summary.json`
- 120 prompt files audited; all leak checks are 0.

## Baselines

Validity-defense directory:

```text
eha-mvp/results/reports-eha-paper-v1.2-validity-defense-2026-05-15/
```

| Baseline | n | Operational escape | Belief correctness | Evidence cleanliness | Uncertainty discipline | Verification action |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ID-only | 200 | 0.110 | 0.200 | 1.000 | 0.200 | 0.000 |
| Metadata-only | 200 | 0.520 | 0.320 | 1.000 | 0.640 | 0.467 |
| Simple heuristic | 200 | 0.560 | 0.400 | 1.000 | 0.960 | 0.600 |

These are no-API baselines on the repaired opaque view. They remain comparison anchors, not replacements for the frontier rerun.

## Generated Lore

Output directory:

```text
eha-mvp/results/reports-eha-generated-lore-role-audit-opaque-2026-05-15/
```

Current-schema generated-lore rows cover all five frontier models: 200 rows total. The clarified-schema mini-rerun covers `gpt-5.4`, `claude-opus-4-7`, and `gemini-3.1-pro-preview`: 120 rows total, with 0 parse failures, 0 empty outputs, and 0 opaque-ID remnants in scored predictions.

Key result: under the current schema, `gpt-5.4` recognizes generated lore at the belief layer (`belief_correctness=1.0`, `insufficient_verdict=1.0`) but puts polluted documents into `supporting_evidence` on every generated-lore row (`polluted_supporting_evidence_rate=1.0`, `full_escape=0.0`). Under the clarified schema, `gpt-5.4` has `polluted_supporting_evidence_rate=0.0` and `role_escape=1.0`.

## Active Verification

Output directory:

```text
eha-mvp/results/reports-eha-active-verification-audit-opaque-2026-05-15/
```

The active-verification audit covers 200 rows. Across active-verification rows, action-gate pass rates are: Claude 0.700, GPT-5.4 0.725, DeepSeek 0.575, Gemini 0.425, Kimi 0.375. The largest recurring action miss is contradiction-seeking in buried-primary, false-consensus, and conflicting-evidence conditions.

## Model Endpoint Note

The model-selection report was updated after re-sourcing `~/.zshrc` and rerunning the empty-output models without temperature and without `max_completion_tokens`.

Latest cap/no-cap result:

- With `max_completion_tokens=120`, `gpt-5`, `gpt-5-nano`, `o3`, `o3-mini`, `o1`, `gemini-3-flash-preview`, and `glm-5.1` all returned empty content with `finish_reason=length`.
- With `max_completion_tokens` omitted, all seven returned parseable JSON.
- Therefore these empty outputs are length/budget-profile artifacts, not evidence that the model IDs are unavailable.

## Verification

- `uv run python -m py_compile scripts/concurrent_frontier_fill.py`: passed.
- `uv run pytest tests/test_epistemic_resilience.py tests/test_epistemic_frontier_main.py tests/test_epistemic_model_preflight.py tests/test_epistemic_generated_lore_audit.py`: 26 passed.
- `uv run pytest`: 76 passed.
- `git diff --check`: passed.
- `make` in `paper/`: passed; `paper/main.pdf` rebuilt from opaque-run tables and figures.

## Next Step

Use `paper/main.pdf` and the artifacts above for review. The old semantic-ID main table should remain quarantined as an invalidated run discussed only in limitations or audit history.
