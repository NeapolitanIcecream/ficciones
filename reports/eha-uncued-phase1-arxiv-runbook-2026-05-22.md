# EHA-Uncued Phase 1 Runbook

Date: 2026-05-22

Audience: local Codex agent working in `/Users/chenmohan/gits/ficciones`.

Goal: complete the equivalent of the original roadmap Step 1, but on a role-uncued dataset suitable for a workshop/arXiv v1 claim. Finishing this runbook should produce a leakage-controlled pilot, model results, audits, an artifact package, and a paper draft whose experimental section no longer depends on the cued dataset.

## Non-Negotiable Rules

- Treat the current opaque/cued release as internal only. Do not use it as main scientific evidence.
- Do not call frontier models until the no-API leakage, baseline, and human leakage gates pass.
- Prefer rebuilding model-visible documents from structured latent facts and gold evidence graphs. Do not rely on naive text rewrites of the leaked cued body text.
- Keep hidden gold labels internal. Model-visible files must not contain role labels, gold verdicts, contamination labels, or semantic IDs.
- If a gate fails, fix the data generator or scorer and rerun the gate. Do not explain the failure away in the paper.
- Never broaden the paper claim beyond what the pilot supports.

## Target Phase 1 Claim

Use this as the working claim:

> EHA-Uncued is a controlled diagnostic benchmark for evaluating whether LLM agents maintain reliable, auditable evidence behavior in polluted evidence environments when document surfaces do not explicitly label evidence roles.

Allowed claims:

- answer correctness can diverge from evidence-role hygiene;
- evidence-role assignment, uncertainty discipline, and verification actions can be evaluated separately;
- role-uncued data construction reduces surface-cue shortcuts relative to the quarantined cued run;
- the pilot supports a diagnostic benchmark claim, not a universal leaderboard claim.

Forbidden claims:

- broad frontier model ranking;
- open-web misinformation performance;
- deployment safety certification;
- final or complete epistemic resilience benchmark;
- results from the old cued run as main evidence.

## Expected New Commands

Implement these commands if they do not exist yet. Use names close to these so later reports are reproducible.

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-uncued-contract --help
uv run eha-generate-uncued --help
uv run eha-audit-uncued-leakage --help
uv run eha-score-uncued-baselines --help
uv run eha-build-uncued-human-review --help
uv run eha-validate-uncued-human-review --help
uv run eha-run-uncued-pilot --help
uv run eha-report-uncued-pilot --help
uv run eha-package-uncued-phase1 --help
uv run eha-verify-uncued-phase1 --help
```

Suggested module names:

```text
eha-mvp/eha/uncued_contract.py
eha-mvp/eha/uncued_generate.py
eha-mvp/eha/uncued_leakage.py
eha-mvp/eha/uncued_baselines.py
eha-mvp/eha/uncued_human_review.py
eha-mvp/eha/uncued_run.py
eha-mvp/eha/uncued_report.py
eha-mvp/eha/uncued_release.py
```

Add tests under:

```text
eha-mvp/tests/test_uncued_contract.py
eha-mvp/tests/test_uncued_generate.py
eha-mvp/tests/test_uncued_leakage.py
eha-mvp/tests/test_uncued_baselines.py
eha-mvp/tests/test_uncued_human_review.py
eha-mvp/tests/test_uncued_release.py
```

## Output Layout

Use this layout unless the existing codebase strongly suggests a better local convention.

```text
eha-mvp/data/uncued-micro/
eha-mvp/data/uncued-pilot-v1/
eha-mvp/results/reports-eha-uncued-micro-2026-05-22/
eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/
artifact_uncued_phase1/
reports/eha-uncued-data-contract-2026-05-22.md
reports/eha_uncued_leakage_micro.json
reports/eha-uncued-leakage-micro-2026-05-22.md
reports/eha_uncued_baselines_micro.json
reports/eha-uncued-baselines-micro-2026-05-22.md
reports/eha_uncued_human_leakage_review_validation.json
reports/eha-uncued-human-leakage-review-2026-05-22.md
reports/eha_uncued_pilot_run.json
reports/eha-uncued-pilot-run-2026-05-22.md
reports/eha_uncued_pilot_results.json
reports/eha-uncued-pilot-results-2026-05-22.md
reports/eha_uncued_scorer_audit.json
reports/eha-uncued-scorer-audit-2026-05-22.md
reports/uncued_scorer_audit_rows.csv
reports/eha-uncued-phase1-readiness-2026-05-22.md
```

## Gate Summary

The local agent must stop before model calls unless all pre-model gates pass.

| Gate | Pass Requirement |
| --- | --- |
| Contract | `uncued_data_contract.md` exists, with forbidden/allowed cues and thresholds. |
| Literal leakage | 0 hidden label hits, 0 semantic ID hits, 0 direct gold field hits. |
| Semantic leakage | 0 critical hits, 0 high-severity hits in model-visible JSON. |
| Direct answer cue | 0 direct answer cue hits in title/body/question/prompt. |
| Cue baselines | Surface-only baselines stay below thresholds listed below. |
| Human leakage review | 0 critical leaks; no task answerable from wording alone. |
| Clean solvability | Frontier pilot later reaches operational escape >= 0.75 on clean. |
| Nontrivial polluted tasks | No model reaches 1.0 operational escape across all polluted conditions. |
| Scorer audit | 30-50 row manual audit confirms scorer decisions or documents fixes. |

## Phase 0: Repository Baseline

Purpose: record the starting state and avoid mixing old cued results with the new run.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones
git status --short
cd eha-mvp
uv run pytest -q
cd ..
```

Deliverables:

- `reports/eha-uncued-phase1-start-state-2026-05-22.md`
- note current branch, dirty files, test status, and known blockers.

Acceptance:

- Existing tests pass, or failures are documented and shown unrelated to uncued work.
- The report states that `artifact/` and `artifact/data/documents_opaque.jsonl` are quarantined as cued/internal evidence.

Failure handling:

- If unrelated tests fail, do not fix them unless they block uncued code.
- If core EHA tests fail, fix or document before proceeding.

## Phase 1: Quarantine Current Cued Artifacts

Purpose: prevent accidental reuse of the leaked dataset as main evidence.

Actions:

- Add an internal status file such as `artifact/CUED_INTERNAL_ONLY.md`.
- Add or update a manifest field stating `scientific_status = "quarantined_cued_internal"`.
- Add release verifier logic that blocks using `artifact/` as EHA-Uncued Phase 1 evidence.
- Do not delete old artifacts.

Deliverables:

- `artifact/CUED_INTERNAL_ONLY.md`
- `reports/eha-cued-artifact-quarantine-2026-05-22.md`
- tests proving the uncued verifier refuses cued artifacts as main evidence.

Acceptance:

- The report explicitly says old results may be used only as methodological caution or regression tests.
- No new paper table uses old cued model results as main evidence.

## Phase 2: Write The Uncued Data Contract

Purpose: make "uncued" executable, not rhetorical.

Create:

```text
reports/eha-uncued-data-contract-2026-05-22.md
eha-mvp/eha/uncued_contract.py
```

The contract must define:

- L0 hidden-label leakage;
- L1 semantic ID leakage;
- L2 material-role phrase leakage;
- L3 conclusion cue leakage;
- L4 allowed relational evidence;
- allowed metadata for each view;
- forbidden title/body/source-type words;
- direct answer cue patterns;
- baseline thresholds;
- human review rubric;
- model-call go/no-go rule.

Use this terminology:

- `role_uncued`: preferred term.
- `content_neutral`: avoid as the main term, because documents must still contain task-relevant content.

Acceptance:

- `uv run pytest tests/test_uncued_contract.py -q` passes.
- Contract includes machine-readable forbidden term lists.
- Contract has a clear distinction between explicit role labels and legitimate relational evidence.

Minimum forbidden phrase families:

```text
primary, secondary, contaminant, pollutant, generated lore, wiki-style,
authoritative-looking, copied from the same upstream story, raw records,
signed record, reviewer sign-off, does not settle, no primary evidence,
not independent, repeats the same claim, background material,
orientation material, insufficient evidence
```

Refine the exact list to avoid blocking ordinary claim content, but keep all direct role labels forbidden.

## Phase 3: Build A Structured Latent Source

Purpose: avoid reusing leaked prose as the source of truth.

Build from internal structured data:

```text
latent task facts
latent documents
gold evidence graph
dependencies/citations
timestamps
claim values
view definitions
```

Implementation guidance:

- Reuse existing gold schemas where safe.
- If current source data only contains leaked prose, parse or reconstruct the latent facts manually for the micro-pilot first.
- Keep internal document roles in gold files only.
- Generate visible documents from templates that do not contain role labels.

Deliverables:

```text
eha-mvp/data/uncued-micro/latent_tasks.jsonl
eha-mvp/data/uncued-micro/gold_documents.jsonl
eha-mvp/data/uncued-micro/dependency_edges.jsonl
```

Acceptance:

- Latent files contain roles and gold labels.
- Model-visible files do not exist yet or are generated separately.
- Tests show hidden fields do not enter model-visible payloads.

## Phase 4: Generate 10-Task Micro-Pilot

Purpose: test the new generator before spending time on 60 tasks.

Dataset:

- 2 clean;
- 2 conflicting evidence;
- 2 false consensus;
- 2 buried primary;
- 2 generated lore.

Families:

- 4 packet judgment;
- 4 evidence selection;
- 2 active verification.

Views:

- `neutral_metadata_visible`;
- `neutral_metadata_hidden`.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-generate-uncued micro \
  --out-dir data/uncued-micro \
  --task-count 10 \
  --views neutral_metadata_visible,neutral_metadata_hidden \
  --seed 9417
```

Expected output:

```text
tasks.jsonl
documents_neutral_metadata_visible.jsonl
documents_neutral_metadata_hidden.jsonl
gold_documents.jsonl
dependency_edges.jsonl
action_gold.jsonl
manifest.json
```

Acceptance:

- 10 tasks are generated.
- Both views exist.
- Per-task opaque IDs are randomized and citations are remapped.
- Hidden roles and gold labels remain internal.
- Document lengths and style are roughly matched across roles.
- No model-visible document title says its role.

Failure handling:

- If tasks become impossible, add relational evidence: citations, dates, contradictions, or paired claims.
- Do not add phrases like "not primary", "secondary", "does not settle", or "raw record".

## Phase 5: Implement Leakage Checker v2

Purpose: catch leakage before model calls.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-audit-uncued-leakage \
  --dataset-dir data/uncued-micro \
  --out-dir ../reports \
  --views neutral_metadata_visible,neutral_metadata_hidden
```

Checks:

- hidden labels in visible JSON;
- semantic IDs;
- material-role phrases;
- conclusion cues;
- direct answer cues;
- role-bearing source types;
- title cues;
- prompt/schema leakage;
- citation IDs and dependency display;
- repeated template phrases that identify role.

Severity:

- `critical`: directly gives answer or gold role.
- `high`: directly states material role, insufficiency, or independence.
- `medium`: strong but realistic source-quality cue.
- `low`: weak realistic clue; allowed only if balanced.

Deliverables:

- `reports/eha_uncued_leakage_micro.json`
- `reports/eha-uncued-leakage-micro-2026-05-22.md`
- `reports/uncued_leakage_micro_rows.csv`

Acceptance:

- critical hits: 0.
- high hits: 0.
- hidden label hits: 0.
- semantic ID hits: 0.
- direct answer cue hits: 0.
- medium hits are reviewed and either justified as balanced realistic metadata or fixed.

Failure handling:

- Fix generator/templates, not the checker.
- Add regression tests for each discovered leakage phrase.

## Phase 6: Add No-API Shortcut Baselines

Purpose: prove the dataset is not solvable by superficial shortcuts.

Baselines to implement:

- `id_only`;
- `document_order_only`;
- `title_only`;
- `source_type_only`;
- `metadata_only`;
- `timestamp_only`;
- `citation_graph_only`;
- `claim_overlap_only`;
- `cue_phrase_only`;
- `random_valid_schema`;
- `always_insufficient`;
- `simple_heuristic`.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-score-uncued-baselines \
  --dataset-dir data/uncued-micro \
  --out-dir ../reports \
  --views neutral_metadata_visible,neutral_metadata_hidden
```

Report separate metrics:

- verdict accuracy;
- evidence precision;
- clean support recall;
- polluted support rate;
- role reconstruction accuracy;
- action target score;
- operational escape.

Do not gate only on operational escape.

Initial gate thresholds for micro and pilot:

| Baseline | Gate |
| --- | --- |
| `id_only` | operational escape <= 0.10 and verdict accuracy <= 0.40 |
| `document_order_only` | operational escape <= 0.15 and verdict accuracy <= 0.45 |
| `title_only` | operational escape <= 0.25 and role reconstruction <= 0.45 |
| `source_type_only`, hidden view | operational escape <= 0.10 |
| `source_type_only`, visible view | operational escape <= 0.25 |
| `metadata_only`, hidden view | operational escape <= 0.20 |
| `metadata_only`, visible view | operational escape <= 0.35 |
| `timestamp_only` | verdict accuracy <= 0.55 |
| `citation_graph_only` | operational escape <= 0.35 and verdict accuracy <= 0.60 |
| `claim_overlap_only` | operational escape <= 0.35 and polluted support rate <= 0.60 |
| `cue_phrase_only` | operational escape <= 0.10 after leakage cleanup |
| `always_insufficient` | operational escape <= 0.30 |
| `simple_heuristic` | must be meaningfully below frontier pilot after model run |

Deliverables:

- `reports/eha_uncued_baselines_micro.json`
- `reports/eha-uncued-baselines-micro-2026-05-22.md`
- `reports/uncued_baseline_rows_micro.csv`

Acceptance:

- All pre-model baseline gates pass.
- If a legitimate relational baseline is high, document whether the benchmark has become a graph-template task. If yes, revise generator before model calls.

## Phase 7: Human Leakage Review For Micro-Pilot

Purpose: have a human inspect whether wording gives away the role or answer.

Build worksheet:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-build-uncued-human-review \
  --dataset-dir data/uncued-micro \
  --out-dir ../reports \
  --sample all \
  --views neutral_metadata_visible,neutral_metadata_hidden
```

Worksheet fields:

- task_id;
- view;
- doc_id;
- title;
- source_type;
- timestamp;
- body_excerpt;
- reviewer_can_guess_role_from_surface;
- reviewer_role_guess;
- reviewer_can_guess_answer_without_relation;
- severe_leakage;
- leakage_reason;
- notes.

Validation command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-validate-uncued-human-review \
  --worksheet-path ../reports/uncued_human_leakage_review_micro.csv \
  --out-dir ../reports
```

Acceptance:

- all micro-pilot documents reviewed;
- critical leaks: 0;
- direct answer cues: 0;
- severe leakage: 0 for micro-pilot;
- role guesses from surface alone do not clearly exceed chance once relation/content is hidden from the reviewer;
- every reviewer note is nonblank when a risk is marked.

Failure handling:

- Fix templates and regenerate.
- Rerun Phases 5-7 until all pass.

## Phase 8: Freeze Micro-Pilot Gate

Purpose: stop uncontrolled iteration.

Create:

```text
reports/eha-uncued-micro-gate-2026-05-22.md
reports/eha_uncued_micro_gate.json
```

Acceptance:

- micro generation manifest hash recorded;
- leakage report hash recorded;
- baseline report hash recorded;
- human review validation hash recorded;
- explicit go/no-go decision.

Gate:

- Proceed to 60-task pilot only if the decision is `go`.

## Phase 9: Generate 60-Task Uncued Pilot

Purpose: create the arXiv-phase dataset.

Dataset:

- 12 clean;
- 12 conflicting evidence;
- 12 false consensus;
- 12 buried primary;
- 12 generated lore.

Families:

- 24 packet judgment;
- 24 evidence selection;
- 12 active verification.

Views:

- required: `neutral_metadata_hidden`;
- required: `neutral_metadata_visible`;
- optional only after required views pass: `metadata_spoofed`, `style_matched`.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-generate-uncued pilot \
  --out-dir data/uncued-pilot-v1 \
  --task-count 60 \
  --views neutral_metadata_visible,neutral_metadata_hidden \
  --seed 20260522
```

Acceptance:

- exact task counts match the plan;
- family and condition balance match the manifest;
- every active-verification task has exact action gold targets;
- both metadata views use the same latent tasks and gold labels;
- all visible IDs are opaque and per-task randomized.

## Phase 10: Rerun Leakage, Baselines, And Human Review On 60 Tasks

Purpose: prove the full pilot passes the same gates as the micro-pilot.

Commands:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp

uv run eha-audit-uncued-leakage \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir ../reports \
  --views neutral_metadata_visible,neutral_metadata_hidden

uv run eha-score-uncued-baselines \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir ../reports \
  --views neutral_metadata_visible,neutral_metadata_hidden

uv run eha-build-uncued-human-review \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir ../reports \
  --sample 50-tasks-200-docs \
  --views neutral_metadata_visible,neutral_metadata_hidden
```

Human review sample:

- 50 tasks if possible;
- at least 200 documents;
- balanced across condition, family, and view;
- include all active-verification tasks if count is small.

Acceptance:

- same leakage and baseline gates as Phases 5-7;
- critical leaks: 0;
- high leaks: 0;
- direct answer cue tasks: 0;
- human severe leakage <= 1% of reviewed documents and 0 direct-answer tasks;
- any medium leakage is listed and justified or fixed.

Stop rule:

- Do not run models if this phase fails.

## Phase 11: Model Preflight And Cost Approval

Purpose: avoid surprise API failures and uncontrolled spend.

Initial cohort:

- `gpt-5.5`;
- `claude-opus-4-7`;
- `gemini-3.1-pro-preview`;
- `deepseek-v4-pro`.

Do not include `kimi-k2.6` in the default Phase 1 pilot. It was slow and comparatively expensive in the previous run. Only add it later as an optional extension if there is a specific reason to compare against it.

Prompt/schema:

- main schema: clarified evidence-role schema;
- current schema only as a small ablation, not main scoring contract;
- main prompt count: 1 initially;
- add hygiene prompt only if budget and time allow.

Preflight command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-epistemic-model-preflight run \
  --task-dir data/uncued-pilot-v1 \
  --models gpt-5.5,claude-opus-4-7,gemini-3.1-pro-preview,deepseek-v4-pro \
  --fallback-models '' \
  --out-dir results/reports-eha-uncued-model-preflight-2026-05-22 \
  --sample-size 20 \
  --prompt-condition standard_answer \
  --max-output-tokens 4096 \
  --soft-cap-usd 3 \
  --hard-cap-usd 5 \
  --abort-cap-usd 8 \
  --timeout-s 240 \
  --response-format json_schema
```

Budget estimate:

- Existing opaque run: 1000 calls cost about USD 4.03, about USD 0.004 per call.
- Default pilot: 60 tasks x 2 views x 4 models x 1 prompt = 480 calls, expected about USD 2.00.
- With retries and variance, reserve USD 15.
- With 2 prompts, reserve USD 25.

Acceptance:

- all selected models return valid structured output in preflight;
- run plan states expected calls and hard budget cap;
- user or project owner explicitly approves model calls if required by local policy.

## Phase 12: Run 60-Task Uncued Pilot

Purpose: collect main Phase 1 model results.

Command shape:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-run-uncued-pilot \
  --dataset-dir data/uncued-pilot-v1 \
  --out-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --models gpt-5.5,claude-opus-4-7,gemini-3.1-pro-preview,deepseek-v4-pro \
  --views neutral_metadata_visible,neutral_metadata_hidden \
  --schema clarified \
  --prompt standard_answer \
  --hard-cap-usd 15
```

Required run logging:

- model;
- provider;
- view;
- task_id;
- schema variant;
- prompt condition;
- parse success;
- raw output path or safe raw-output record;
- prediction JSON;
- usage and cost;
- visible prompt leakage audit summary.

Acceptance:

- no model-visible prompt audit hits;
- record count equals tasks x views x models x prompts;
- parse success high enough to score; target >= 0.95;
- failed calls are retried within cap or recorded as failures;
- no hidden labels appear in stored prompts or outputs.

Failure handling:

- If parse failures dominate, repair schema/prompt and rerun only failed slice.
- If budget cap triggers, stop and report partial results.

## Phase 13: Score And Report Pilot Results

Purpose: produce tables for paper use.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-report-uncued-pilot \
  --dataset-dir data/uncued-pilot-v1 \
  --run-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --out-dir results/reports-eha-uncued-pilot-2026-05-22
```

Metrics:

- operational escape;
- parse success;
- belief correctness;
- evidence precision;
- clean support recall;
- polluted support rate;
- rejected pollutant rate;
- dual-role rate;
- support-empty rate;
- uncertainty discipline;
- verification action score;
- exact target rate;
- required action recall;
- cost.

Required tables:

- by model;
- by view;
- by condition;
- by family;
- by model x view;
- by model x condition;
- baselines vs models;
- active-verification action metrics.

Acceptance:

- clean condition operational escape >= 0.75 for at least one frontier model; if not, diagnose task impossibility;
- no model gets 1.0 across all polluted conditions;
- generated-lore and buried-primary show nontrivial separation between belief correctness and evidence/action hygiene;
- metadata-hidden results are reported separately from metadata-visible results;
- simple heuristic remains meaningfully below frontier models on at least operational escape and evidence metrics.

## Phase 14: Manual Scorer Audit

Purpose: show that automatic scoring is not arbitrary.

Sample:

- 30-50 model rows;
- balanced across model, view, condition, and family;
- include active-verification rows;
- include successes and failures.

Fields:

- row_id;
- task_id;
- model;
- view;
- predicted verdict;
- selected evidence;
- rejected evidence;
- actions;
- automatic scores;
- human score agreement yes/no per metric;
- disagreement reason;
- scorer fix needed yes/no.

Acceptance:

- at least 30 rows reviewed;
- scorer disagreement rate reported;
- any systematic scorer bug fixed and affected rows rescored;
- final scorer audit is included in artifact package.

## Phase 15: Schema Ablation Mini-Slice

Purpose: preserve the original Step 1 schema-sensitivity contribution without making it the main experiment.

Scope:

- 10-20 generated-lore and buried-primary tasks;
- one or two models only if budget allows;
- schemas: `clarified`, `current`, `minimal`, `diagnostic_no_hygiene`.

Acceptance:

- clearly marked as ablation, not main result;
- demonstrates whether field design changes evidence-role hygiene;
- does not reuse cued data.

Skip rule:

- If Phase 12-14 already consume the time/budget, skip this and list it as planned Phase 1.1 work. Do not block arXiv pilot readiness if main uncued result is complete.

## Phase 16: Package Uncued Phase 1 Artifact

Purpose: make the pilot reproducible.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-package-uncued-phase1 \
  --dataset-dir data/uncued-pilot-v1 \
  --run-dir results/reports-eha-uncued-pilot-2026-05-22 \
  --out-dir ../artifact_uncued_phase1
```

Package layout:

```text
artifact_uncued_phase1/
  README.md
  manifest.json
  data/
    tasks.jsonl
    documents_neutral_metadata_visible.jsonl
    documents_neutral_metadata_hidden.jsonl
    gold_labels.jsonl
    dependency_edges.jsonl
    action_gold.jsonl
  prompts/
  schemas/
  scorer/
  outputs/
  baselines/
  audits/
  examples/
  reproduce_minimal.sh
  verify_uncued_phase1.sh
```

Acceptance:

- package excludes hidden labels from model-visible files;
- package includes enough gold/scorer data for reproduction;
- minimal example runs locally;
- verifier checks leakage, baselines, manifest hashes, and result file presence.

## Phase 17: Final Phase 1 Verification

Purpose: produce a single go/no-go artifact.

Command:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-verify-uncued-phase1 \
  --artifact-dir ../artifact_uncued_phase1 \
  --reports-dir ../reports \
  --out-dir ../reports
uv run pytest -q
```

Acceptance:

- tests pass;
- artifact verifier passes;
- leakage gates pass;
- baseline gates pass;
- human review gates pass;
- model run complete or partial status is explicit;
- scorer audit complete;
- no main paper table points to old cued results.

Deliverables:

- `reports/eha_uncued_phase1_readiness.json`
- `reports/eha-uncued-phase1-readiness-2026-05-22.md`

## Phase 18: Rewrite The Paper For arXiv v1

Purpose: turn the uncued pilot into a credible paper draft.

Keep from old draft:

- introduction motivation;
- polluted evidence environment framing;
- metric definitions if still valid;
- generated-lore motivation;
- active-verification interface framing;
- related work.

Replace:

- dataset construction;
- all main experiment results;
- leakage validity claims;
- artifact section;
- limitations.

Required paper structure:

```text
1. Introduction
2. Polluted Evidence Environments
3. EHA-Uncued Dataset Design
4. Leakage Controls And Shortcut Baselines
5. Metrics And Scoring Contract
6. Experimental Setup
7. Results
8. Schema/Interface Analysis
9. Human Scorer Audit
10. Limitations
11. Ethics And Scope
12. Artifact
13. Conclusion
```

Required claims:

- the old cued run exposed a benchmark-construction failure and is quarantined;
- the new role-uncued pilot removes direct material-role and conclusion cues;
- shortcut baselines are low enough to justify model evaluation;
- results are diagnostic and pilot-scale;
- the work is not a deployment certification or universal leaderboard.

Required tables/figures:

- leakage gate summary;
- shortcut baseline summary;
- main model metrics by view;
- main model metrics by condition;
- evidence hygiene vs belief correctness;
- active-verification action exactness;
- scorer audit summary.

Acceptance:

- no main result from cued artifacts;
- all examples use role-uncued visible documents;
- limitations clearly state pilot scale and synthetic data limits;
- artifact section points to `artifact_uncued_phase1/`;
- paper compiles if LaTeX is used.

## Phase 19: Final Handoff

Purpose: make the next agent or human reviewer able to continue without reconstructing context.

Create:

```text
reports/eha-uncued-phase1-final-handoff-2026-05-22.md
```

Include:

- what was built;
- exact commands run;
- tests run;
- model calls and total cost;
- gate pass/fail table;
- unresolved risks;
- paper status;
- next recommended step.

Acceptance:

- a fresh local Codex agent can read the handoff and know the state within 10 minutes;
- all paths are absolute or repo-relative and valid;
- any skipped optional work is clearly marked as skipped, not done.

## Model Cost Budget

Use these planning numbers from the existing opaque run:

```text
1000 calls cost about USD 4.03
mean cost per call about USD 0.004
```

Expected costs:

| Run | Calls | Expected Cost | Budget Cap |
| --- | ---: | ---: | ---: |
| Micro-pilot no-API gates | 0 | USD 0 | USD 0 |
| Optional micro model smoke, 10 tasks x 2 views x 4 models | 80 | about USD 0.35 | USD 3 |
| Main pilot, 60 tasks x 2 views x 4 models x 1 prompt | 480 | about USD 2.00 | USD 15 |
| Main pilot with 3-model fallback | 360 | about USD 1.50 | USD 10 |
| Main pilot plus 2 prompts | 960 | about USD 3.90 | USD 25 |
| Schema ablation mini-slice | 80-160 | about USD 0.35-0.70 | USD 5 |

Use hard caps in commands. Stop if costs exceed the cap.

## Completion Definition

The runbook is complete when all of these are true:

- current cued results are quarantined;
- role-uncued data contract exists;
- 10-task micro-pilot passes leakage, baseline, and human review gates;
- 60-task role-uncued pilot is generated;
- pilot passes leakage, baseline, and human review gates;
- approved frontier cohort is run within budget;
- pilot is scored and manually audited;
- `artifact_uncued_phase1/` verifies;
- paper draft is rewritten around uncued results;
- final handoff records exact state, cost, tests, and remaining risks.

## Execution Status: Advanced To Phase 14

Status date: 2026-05-22

This runbook has been advanced through Phase 14. Phases 15-19 have not been started. The four-model Phase 12 pilot run is complete, the Phase 13 scored report tables have been generated, and the Phase 14 scorer audit is complete.

Completed Phase 0-14 artifacts:

- Phase 0 start state: `reports/eha-uncued-phase1-start-state-2026-05-22.md`.
- Phase 1 cued quarantine: `artifact/CUED_INTERNAL_ONLY.md`, `artifact/manifest.json`, `reports/eha-cued-artifact-quarantine-2026-05-22.md`.
- Phase 2 data contract: `reports/eha-uncued-data-contract-2026-05-22.md`, `reports/uncued_data_contract.md`, `reports/eha_uncued_data_contract.json`, `eha-mvp/eha/uncued_contract.py`.
- Phase 3 latent source: `eha-mvp/data/uncued-micro/latent_tasks.jsonl`, `eha-mvp/data/uncued-micro/gold_documents.jsonl`, `eha-mvp/data/uncued-micro/dependency_edges.jsonl`.
- Phase 4 micro-pilot: `eha-mvp/data/uncued-micro/tasks.jsonl`, `documents_neutral_metadata_visible.jsonl`, `documents_neutral_metadata_hidden.jsonl`, `action_gold.jsonl`, `manifest.json`.
- Phase 5 leakage audit: `reports/eha_uncued_leakage_micro.json`, `reports/eha-uncued-leakage-micro-2026-05-22.md`, `reports/uncued_leakage_micro_rows.csv`.
- Phase 6 shortcut baselines: `reports/eha_uncued_baselines_micro.json`, `reports/eha-uncued-baselines-micro-2026-05-22.md`, `reports/uncued_baseline_rows_micro.csv`, `reports/uncued_baseline_aggregate_micro.csv`.
- Phase 7 surface review: `reports/uncued_human_leakage_review_micro.csv`, `reports/eha_uncued_human_leakage_review_validation.json`, `reports/eha-uncued-human-leakage-review-2026-05-22.md`.
- Phase 8 micro gate: `reports/eha_uncued_micro_gate.json`, `reports/eha-uncued-micro-gate-2026-05-22.md`.
- Phase 9 pilot generation: `eha-mvp/data/uncued-pilot-v1/manifest.json`, `tasks.jsonl`, `latent_tasks.jsonl`, `gold_documents.jsonl`, `dependency_edges.jsonl`, `action_gold.jsonl`, `documents_neutral_metadata_visible.jsonl`, `documents_neutral_metadata_hidden.jsonl`.
- Phase 10 pilot gates: `reports/eha_uncued_leakage_pilot.json`, `reports/eha-uncued-leakage-pilot-2026-05-22.md`, `reports/uncued_leakage_pilot_rows.csv`, `reports/eha_uncued_baselines_pilot.json`, `reports/eha-uncued-baselines-pilot-2026-05-22.md`, `reports/uncued_baseline_rows_pilot.csv`, `reports/uncued_baseline_aggregate_pilot.csv`, `reports/uncued_human_leakage_review_pilot.csv`, `reports/eha_uncued_human_leakage_review_pilot_validation.json`, `reports/eha-uncued-human-leakage-review-pilot-2026-05-22.md`, `reports/eha_uncued_pilot_gates.json`, `reports/eha-uncued-pilot-gates-2026-05-22.md`.
- Phase 11 model preflight: `reports/eha_uncued_model_preflight.json`, `reports/eha-uncued-model-preflight-2026-05-22.md`, `eha-mvp/results/reports-eha-uncued-model-preflight-2026-05-22/preflight_predictions.jsonl`, `preflight_rows.csv`, `preflight_summary.csv`, `cohort_decision.md`, `cohort_decision.csv`, `cohort_decision.json`, `cost_report.json`, `audit_manifest.json`.
- Phase 11 DeepSeek retry: `reports/eha_uncued_model_preflight_deepseek_retry.json`, `reports/eha-uncued-model-preflight-deepseek-retry-2026-05-22.md`, `eha-mvp/results/reports-eha-uncued-model-preflight-deepseek-retry-2026-05-22/preflight_predictions.jsonl`, `preflight_rows.csv`, `preflight_summary.csv`, `cohort_decision.md`, `cohort_decision.csv`, `cohort_decision.json`, `cost_report.json`, `audit_manifest.json`.
- Phase 12 pilot run: `reports/eha_uncued_pilot_run.json`, `reports/eha-uncued-pilot-run-2026-05-22.md`, `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/predictions.jsonl`, `run_manifest.json`, `invocation_profiles.json`, `run_summary_by_model.csv`, `prompt_audit_summary.json`, `stored_hidden_label_audit.json`, `cost_report.json`, `phase12_run_summary.md`.
- Phase 13 pilot scoring/reporting: `reports/eha_uncued_pilot_results.json`, `reports/eha-uncued-pilot-results-2026-05-22.md`, `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/uncued_pilot_scored_predictions.csv`, `uncued_pilot_metrics_by_model.csv`, `uncued_pilot_metrics_by_view.csv`, `uncued_pilot_metrics_by_condition.csv`, `uncued_pilot_metrics_by_family.csv`, `uncued_pilot_metrics_by_model_view.csv`, `uncued_pilot_metrics_by_model_condition.csv`, `uncued_pilot_baselines_vs_models.csv`, `uncued_pilot_active_verification_action_metrics.csv`, `uncued_pilot_acceptance_diagnostics.json`, `report_manifest.json`, `summary.md`.
- Phase 14 scorer audit: `reports/eha_uncued_scorer_audit.json`, `reports/eha-uncued-scorer-audit-2026-05-22.md`, `reports/uncued_scorer_audit_rows.csv`, `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/uncued_scorer_audit_rows.csv`, `uncued_scorer_audit_summary.json`.

Phase 8 gate evidence:

- Micro generation manifest hash: `099b7e2774daf1513c8b5fda2d3f9177e6e8247bb0b8d0d244b3f825fd370bb2`.
- Leakage report hash: `08255d36b783e06bf0d0773baee32ed3a80324013974c940f203801d85072602`.
- Baseline report hash: `bb1a55b0a6b0055bcba50394bc7563be06209de5b105469894a6c51211cf5583`.
- Human-review validation hash: `e52f77bc67a9c7e7407a8991dff4632c6d6b2671180b94c9dcf2d4c2606f70fe`.
- Decision: `go`.

Gate results:

- Leakage audit: `passed=true`, `critical_hits=0`, `high_hits=0`, `hidden_label_hits=0`, `semantic_id_hits=0`, `direct_answer_cue_hits=0`.
- Shortcut baselines: `passed=true`, 12 baselines, 30 gate checks.
- Surface review validation: `passed=true`, 80 reviewed rows, `critical_leaks=0`, `direct_answer_cue_rows=0`, `severe_leakage_rows=0`.
- Review caveat: `independent_human_review=false`; the worksheet records `local_pre_model_surface_review`, so this is a micro leakage gate artifact, not a paper-level independent human-validation claim.

Phase 9 pilot generation evidence:

- Task count: 60.
- Views: `neutral_metadata_visible`, `neutral_metadata_hidden`.
- Condition counts: 12 clean, 12 conflicting evidence, 12 false consensus, 12 buried primary, 12 generated lore.
- Family counts: 24 packet judgment, 24 evidence selection, 12 active verification.
- Action gold rows: 12, one for every active-verification task.
- Documents per view: 240.
- Pilot generation manifest hash: `67f772df81433360276b662377a9121927ec5194f244406adb911d51d5f466e1`.

Phase 10 pilot gate evidence:

- Decision: `go`.
- Leakage audit: `passed=true`, `critical_hits=0`, `high_hits=0`, `hidden_label_hits=0`, `semantic_id_hits=0`, `direct_answer_cue_hits=0`, `medium_hits=0`.
- Shortcut baselines: `passed=true`, 12 baselines, 30 gate checks.
- Human review validation: `passed=true`, 400 reviewed document rows, 50 unique tasks, `critical_leaks=0`, `direct_answer_cue_rows=0`, `severe_leakage_rows=0`, `severe_leakage_rate=0.0`.
- Human review sample balance: 10 tasks from each evidence condition, 19 packet-judgment tasks, 19 evidence-selection tasks, all 12 active-verification tasks, and 200 rows from each required view.
- Review caveat: `independent_human_review=false`; this remains a pre-model leakage gate artifact, not a paper-level independent human-validation claim.
- Pilot leakage report hash: `1426c028e3f016c77723cd949846c8c9bc6c54da9eeaa48e881db69eb0c71ed2`.
- Pilot baseline report hash: `e7577c4bae0ddd3ae685b51de42e6321c0026bccf49df250aaa8da25e50c4490`.
- Pilot human-review validation hash: `54daf906fe0845aa857919daf8497cf6e2d4b985479633012394e3a8b868c34d`.
- Model/API cost through Phase 10: USD 0.

Phase 11 model preflight evidence:

- Command included explicit `--task-dir data/uncued-pilot-v1`.
- Models requested: `gpt-5.5`, `claude-opus-4-7`, `gemini-3.1-pro-preview`, `deepseek-v4-pro`.
- Excluded model: `kimi-k2.6`.
- Fallback models: none.
- Prompt condition: `standard_answer`.
- Expected calls: 80 = 20 tasks x 4 models x 1 prompt.
- Hard budget cap: USD 5; abort cap: USD 8; soft cap: USD 3.
- Actual records: 80.
- Actual cost: USD 0.656743.
- Budget status: not aborted and below hard cap.
- Gate rule: `parse_success >= 0.95`, `empty_output = 0`, `schema_missing_rate <= 0.05`, LLM repair disabled.
- `gpt-5.5`: 20/20 parse success, 0 empty outputs, pass.
- `claude-opus-4-7`: 20/20 parse success, 0 empty outputs, pass.
- `gemini-3.1-pro-preview`: 20/20 parse success, 0 empty outputs, pass.
- `deepseek-v4-pro`: 19/20 parse success, 1 empty output, fail.
- Failing DeepSeek row: `uncued_000_hidden`, condition `clean`, parse error `empty output`.
- Preflight summary hash: `beba62e5e93525b2fbdbd631e2c898c542202e21d0230ba27b16b1abcf068334`.
- Cohort decision hash: `6d5f5f8e0804cc9c0a669e827accf50ed7560cdbe7f25dc5b35ec3498f9c5029`.
- Cost report hash: `3881551d2fca58fb3508a9eaf818db6755c0b5aae0e7c351dca72ce60f782bd4`.
- Audit manifest hash: `104c10cd9d575c303e300dede630c0297e7766221c368cac684a2772153246dd`.
- Initial Phase 12 status: blocked for the requested four-model cohort until DeepSeek is retried, replaced, or a three-model Phase 12 scope is approved.

Phase 11 DeepSeek retry evidence:

- Retry command included explicit `--task-dir data/uncued-pilot-v1`.
- Retry model: `deepseek-v4-pro`.
- Retry fallback models: none.
- Retry prompt condition: `standard_answer`.
- Retry invocation profile: temperature omitted, `max_completion_tokens=4096`, `response_format=json_object`, `json_extractor=first_json_object`, developer/system merged into user, LLM repair disabled.
- Expected retry calls: 20 = 20 tasks x 1 model x 1 prompt.
- Retry hard budget cap: USD 1; abort cap: USD 2; soft cap: USD 0.5.
- Actual retry records: 20.
- Actual retry cost: USD 0.083832.
- Retry budget status: not aborted and below hard cap.
- Retry gate result: pass.
- `deepseek-v4-pro`: 19/20 parse success, 0 empty outputs, 0 schema-missing rows.
- Original failing row resolved: `uncued_000_hidden`, condition `clean`, returned structured non-empty output.
- Retry caveat: `uncued_046_visible`, condition `buried_primary`, timed out after 240 seconds; this is an operational parse failure, but the gate passes because `parse_success_rate=0.95`, `empty_output=0`, and `schema_missing_rate=0.0`.
- DeepSeek retry summary hash: `2983f2d75e83de2cb10bc76eee0dca79ff34e07dd3dfbdceb5039c1b7573519e`.
- DeepSeek retry cohort decision hash: `c260f1db92effda3524f6302df635e64f751398e1b2e569390c90ab4c6d64039`.
- DeepSeek retry cost report hash: `58c6aa81b21c878a3d541ba31e2f3b292075e5869fe73c0fad1025dda2c4d2ac`.
- DeepSeek retry audit manifest hash: `914d056a92bcc1a7c5474350ae4119b6fd870011a6e9ac7d67d306247df412ff`.
- Total Phase 11 model-call cost after retry: USD 0.740575.
- Phase 12 status after retry: allowed for the four-model cohort, with the DeepSeek timeout caveat preserved.

Phase 12 pilot run evidence:

- Command included explicit `--dataset-dir data/uncued-pilot-v1`.
- Models requested: `gpt-5.5`, `claude-opus-4-7`, `gemini-3.1-pro-preview`, `deepseek-v4-pro`.
- Views requested: `neutral_metadata_visible`, `neutral_metadata_hidden`.
- Prompt condition: `standard_answer`.
- Schema variant: `clarified`.
- Expected records: 480 = 60 latent tasks x 2 views x 4 models x 1 prompt.
- Actual records: 480.
- Unique model/task/prompt/budget keys: 480.
- Duplicate keys: 0.
- View counts: 240 visible records and 240 hidden records.
- Prompt audit: `passed=true`, `semantic_doc_id_hits=0`, `semantic_visible_citation_hits=0`, `audit_id_hits_in_title_or_body=0`, `hidden_field_hit_count=0`.
- Stored hidden-label audit: `passed=true`, `prompt_hit_count=0`, `output_hit_count=0`.
- Cost status: not aborted; record cost USD 3.759681; spent USD 3.764007; hard cap USD 15; abort cap USD 20.
- `gpt-5.5`: 120/120 parse success, 0 empty outputs, 0 schema-missing rows, cost USD 2.597870.
- `claude-opus-4-7`: 120/120 parse success, 0 empty outputs, 0 schema-missing rows, cost USD 0.177029.
- `gemini-3.1-pro-preview`: 120/120 parse success, 0 empty outputs, 0 schema-missing rows, cost USD 0.475382.
- `deepseek-v4-pro`: 120/120 parse success, 0 empty outputs, 0 schema-missing rows, cost USD 0.509400.
- DeepSeek Phase 12 invocation profile: temperature omitted, `max_completion_tokens=4096`, `response_format=json_object`, `json_extractor=first_json_object`, developer/system merged into user, LLM repair disabled, max attempts 2, timeout 240 seconds.
- DeepSeek invocation profile artifact: `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/invocation_profiles.json`.
- Pilot predictions hash: `e0d6f072c4e260997b68a6055c1583331aa6a355981a2d9f417cf893ed705ca4`.
- Pilot run summary hash: `74a55842eef9c8da2a9a18b90a41919ee71001817cdb4cf9f8405f77a63ee4ac`.
- Prompt audit summary hash: `4110a36d1b165761ff326f862787c89efedc2ff44ceddf5985a29ef31b0ecf2d`.
- Stored hidden-label audit hash: `5069bd02061d2ff590349a12f9cb2922f62f106081445609195fb2c80e845156`.
- Cost report hash: `5d7291ae05a819f20ece4b287261bc4ccf17736e8c8244554ce00ad40728274b`.
- Invocation profiles hash: `d806153c5a797d738bc3fb7e648a8f1c3d8a34a62260fb47474627a4b9783670`.
- Run manifest hash: `913ae8be97d394ace5904209f4d0beb2aa29f2b3c7b3e4c29622b442eb412572`.
- Phase 12 decision: pass; proceed to Phase 13 scoring/reporting.

Phase 13 pilot scoring/reporting evidence:

- Command included explicit `--dataset-dir data/uncued-pilot-v1`.
- Run directory: `results/reports-eha-uncued-pilot-2026-05-22`.
- Prediction records loaded: 480.
- Scored rows: 480.
- Required tables present: true.
- Required metrics present: operational escape, parse success, belief correctness, evidence precision, clean support recall, polluted support rate, rejected pollutant rate, dual-role rate, support-empty rate, uncertainty discipline, verification action score, exact target rate, required action recall, and cost.
- Required tables generated: by model, by view, by condition, by family, by model x view, by model x condition, baselines vs models, and active-verification action metrics.
- Clean acceptance: at least one model reaches clean operational escape >= 0.75 (`gpt-5.5` clean = 0.958; `claude-opus-4-7` clean = 0.792).
- Polluted acceptance: no model reaches 1.0 operational escape across all polluted conditions.
- Generated-lore separation: belief correctness 0.938, operational escape 0.125, gap 0.8125.
- Buried-primary separation: belief correctness 0.979, operational escape 0.490, gap 0.4896.
- Metadata-hidden and metadata-visible tables are reported separately.
- Simple heuristic comparison: positive margins for `gpt-5.5` and `gemini-3.1-pro-preview` in both views; nonpositive margins for `claude-opus-4-7` and `deepseek-v4-pro` in both views. Do not state that all model-view pairs beat the heuristic.
- Phase 13 acceptance diagnostic: `phase13_acceptance_passed=true`.
- Scored predictions hash: `5d77f0f93eeb80cc42c2e1f9b91f949d9a9e193b07f20e6f14affd1710025a3b`.
- Metrics by model hash: `19186f4acbb85e1634817681ad7a8ee90072db2dc3e7e78b1bc3ab93a36b7433`.
- Metrics by view hash: `9de9fd1b6ab1eb71d82f21984e6162cd5bf06a725eb094d535014af6cb96b451`.
- Metrics by condition hash: `53fa5349b5d866461c77df1cd48aeb07cfe9344010c00245f2edc511da823e77`.
- Metrics by family hash: `81b2c7d5a3fd6e7c7de8be614e2fab4b6c07df2c066ff79f972747a732e52526`.
- Metrics by model x view hash: `ec75f9bfaed08c4db668b71ecd79f228ce210d7ec2550b2c9a7e21478bdc3e2b`.
- Metrics by model x condition hash: `a5f7da11a1a1320cc196ac27d83a9034264f3ca3886ea19dbd389c044ea85aa8`.
- Baselines vs models hash: `b2347b9fb9fdbe09464f52b2c133838acdebe78b2cf497c4c4e01feddbdcf397`.
- Active-verification action metrics hash: `176d40d715c32105e80e8f6d83c7ecdf963b480b1f546ceb485aecb968c49615`.
- Acceptance diagnostics hash: `acf90690d6cd40897db176b77c02a779c85ea4967e09e537a71f69db87c5bc88`.
- Report manifest hash: `62eeddd0eba886c9997e3894300cf0e5fac66fcc3f8af8eca52cf6fd659e2fc6`.
- Summary hash: `d593fdf80f71b42ae70311a825d432b7b6f9146ebe76fb7956ec827587c8bde9`.
- Phase 13 decision: pass; proceed to Phase 14 manual scorer audit.

Phase 14 scorer audit evidence:

- Command: `uv run eha-audit-uncued-scorer --dataset-dir data/uncued-pilot-v1 --run-dir results/reports-eha-uncued-pilot-2026-05-22 --out-dir ../reports --sample-size 40`.
- Review mode: `local_codex_assisted_manual_scorer_audit`.
- Independent human review: false.
- Reviewed rows: 40.
- Balance by model: 10 rows each for `gpt-5.5`, `claude-opus-4-7`, `gemini-3.1-pro-preview`, and `deepseek-v4-pro`.
- Balance by view: 20 hidden and 20 visible rows.
- Balance by condition: 8 rows each for clean, conflicting evidence, false consensus, buried primary, and generated lore.
- Balance by family: 16 packet-judgment rows, 16 evidence-selection rows, 8 active-verification rows.
- Success/failure coverage: 20 operational escapes and 20 operational failures.
- Required worksheet fields are present: row ID, task ID, model, view, predicted verdict, selected evidence, rejected evidence, actions, automatic scores, per-metric human/manual agreement flags, disagreement reason, and scorer-fix-needed flag.
- Scorer disagreement count: 0.
- Scorer disagreement rate: 0.0.
- Systematic scorer bug found: false.
- Rescoring required: false.
- Caveat: this is a local Codex-assisted scorer audit, not an independent human-subject review.
- Scorer audit rows hash: `030f1891ea2a78b53e8bb8b78dfd1a5c638eb38193cb315517ae7efd883de6b2`.
- Scorer audit JSON hash: `f2732eb0ebf96c024c8e3ec705defce34b09a1c60a582d24d29ae60529b4699b`.
- Scorer audit report hash: `af0d85e88b624919c6ef63adb87986c6a3a8107a52a994b3d4441f571d901d38`.
- Phase 14 decision: pass; include the scorer audit in the Phase 16 artifact package.

Commands verified:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-uncued-contract --help
uv run eha-generate-uncued --help
uv run eha-audit-uncued-leakage --help
uv run eha-score-uncued-baselines --help
uv run eha-build-uncued-human-review --help
uv run eha-validate-uncued-human-review --help
uv run eha-run-uncued-pilot --help
uv run eha-report-uncued-pilot --help
uv run eha-package-uncued-phase1 --help
uv run eha-verify-uncued-phase1 --help
```

Verification:

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run pytest -q
# 219 passed in 5.99s
uv run pytest tests/test_uncued_run.py tests/test_epistemic_frontier_main.py tests/test_epistemic_model_preflight.py -q
# 20 passed in 0.42s
uv run pytest tests/test_uncued_report.py -q
# 1 passed in 0.32s
uv run pytest tests/test_uncued_scorer_audit.py -q
# 2 passed in 0.36s
cd /Users/chenmohan/gits/ficciones
git diff --check
# passed
```

Next required phase:

- Start Phase 15 schema-ablation mini-slice. If skipping under the runbook skip rule, record the skip as planned Phase 1.1 work with an explicit reason.
