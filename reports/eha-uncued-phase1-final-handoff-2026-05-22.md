# EHA-Uncued Phase 1 Final Handoff

Date: 2026-05-22

Status: Phase 0-19 complete for the role-uncued Phase 1 arXiv-readiness runbook.

Post-handoff update: the deferred role-uncued schema ablation was completed later as Phase 1.1. See `reports/eha-uncued-phase1-1-final-handoff-2026-05-25.md` for the current post-ablation status.

## What Was Built

- Role-uncued micro and pilot datasets under `eha-mvp/data/uncued-micro/` and `eha-mvp/data/uncued-pilot-v1/`.
- Leakage, shortcut baseline, and local surface-review gates under `reports/`.
- Four-model role-uncued pilot outputs under `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/`.
- DeepSeek-only documented retry and separate Phase 12 invocation profile recording.
- Scored pilot tables and scorer audit artifacts.
- Reproducibility package rooted at `artifact_uncued_phase1/`.
- Readiness verifier outputs: `reports/eha_uncued_phase1_readiness.json` and `reports/eha-uncued-phase1-readiness-2026-05-22.md`.
- Rewritten uncued paper source and PDF under `paper/`.

## Phase Commits

- Phase 0: `bde67470 phase 0: record uncued start state`
- Phase 1: `aed2d77a phase 1: quarantine cued artifact`
- Phase 2: `6576f9e1 phase 2: define uncued data contract`
- Phase 3-4: `b93799ee phase 3-4: generate uncued micro pilot`
- Phase 5: `1dafa7e4 phase 5: audit uncued leakage`
- Phase 6: `f3855433 phase 6: score uncued shortcut baselines`
- Phase 7: `041f5498 phase 7: validate uncued surface review`
- Phase 8: `b7900ea1 phase 8: freeze uncued micro gate`
- Phase 9: `804bf8d2 phase 9: generate uncued pilot dataset`
- Phase 10: `ee84e8f2 phase 10: validate uncued pilot gates`
- Phase 11 preflight: `69e750db phase 11: preflight uncued model cohort`
- Phase 11 DeepSeek retry: `fa613af1 phase 11: document deepseek retry`
- Phase 12: `8354529f phase 12: run uncued pilot`
- Phase 13: `539a5068 phase 13: score uncued pilot`
- Phase 14: `96afd167 phase 14: audit uncued scorer`
- Phase 15: `70bf65d3 phase 15: defer uncued schema ablation`
- Phase 16: `523b523b phase 16: package uncued phase1 artifact`
- Phase 17: `dd204e5f phase 17: verify uncued readiness`
- Phase 18: `48c61a1a phase 18: rewrite uncued arxiv paper`

## Final Commands

```bash
cd /Users/chenmohan/gits/ficciones/eha-mvp
uv run eha-verify-uncued-phase1 --artifact-dir ../artifact_uncued_phase1 --reports-dir ../reports --out-dir ../reports
uv run pytest -q

cd /Users/chenmohan/gits/ficciones/paper
make pdf

cd /Users/chenmohan/gits/ficciones
pdftotext paper/main.pdf - | rg -n "gpt-5\\.4|kimi-k2\\.6|opaque main|1000|100 tasks"
rg -n "gpt-5\\.4|kimi-k2\\.6|opaque main|1000|100 tasks|opaque-run|frontier main" paper/main.tex paper/sections paper/tables -S
git diff --check
```

Final command outcomes:

- Artifact readiness verifier: pass.
- Full test suite: `223 passed in 6.82s`.
- Paper compile: pass; only a bibliography underfull-box warning remains.
- Paper source/PDF old-result audit: no hits for old model/result strings.
- `git diff --check`: pass.

## Model Calls And Cost

- Phase 10 and earlier: USD 0 model/API cost.
- Phase 11 initial four-model preflight: USD 0.656743.
- Phase 11 DeepSeek-only retry: USD 0.083832.
- Phase 12 four-model pilot: USD 3.764007 spent.
- Total recorded model/API spend for Phase 1 path: USD 4.504582.

DeepSeek retry/pilot profile:

- `response_format=json_object`
- `json_extractor=first_json_object`
- temperature omitted
- `max_completion_tokens=4096`
- developer/system merged into user
- LLM repair disabled
- Phase 12 max attempts: 2
- Phase 12 timeout: 240 seconds
- Separate profile artifact: `eha-mvp/results/reports-eha-uncued-pilot-2026-05-22/invocation_profiles.json`

## Gate Table

| Gate | Status | Evidence |
| --- | --- | --- |
| Cued artifact quarantine | pass | `artifact/CUED_INTERNAL_ONLY.md`, `artifact/manifest.json` |
| Micro leakage/baseline/review gate | pass | `reports/eha_uncued_micro_gate.json` |
| Pilot leakage gate | pass | `reports/eha_uncued_leakage_pilot.json` |
| Pilot shortcut baselines | pass | `reports/eha_uncued_baselines_pilot.json` |
| Pilot surface review | pass | `reports/eha_uncued_human_leakage_review_pilot_validation.json` |
| Initial model preflight | blocked then resolved | DeepSeek failed one initial row; retry documented |
| DeepSeek retry | pass | `reports/eha_uncued_model_preflight_deepseek_retry.json` |
| Phase 12 model run | pass | 480/480 records, all parse success |
| Phase 13 scoring | pass | 480 scored rows, acceptance passed |
| Phase 14 scorer audit | pass | 40 reviewed rows, 0 disagreements |
| Phase 15 schema ablation | skipped on Phase 1 path; later completed as Phase 1.1 | Phase 15 made 0 model calls; see `reports/eha-uncued-phase1-1-final-handoff-2026-05-25.md` |
| Phase 16 artifact package | pass | `artifact_uncued_phase1/manifest.json` |
| Phase 17 readiness verifier | pass | `reports/eha_uncued_phase1_readiness.json` |
| Phase 18 paper rewrite | pass | `paper/main.pdf`, uncued-only main results |

## Paper Status

The paper has been rewritten around the role-uncued pilot. It has the required 13-section structure, uses `artifact_uncued_phase1/`, and includes the required tables for leakage, baselines, model metrics by view, condition metrics, belief-vs-hygiene separation, active verification, and scorer audit.

The old cued construction is mentioned only as a quarantined construction failure. Old opaque/cued result tables and figures were removed from the paper source tree.

## Remaining Risks

- The dataset is pilot-scale and synthetic: 60 latent tasks, two views, four model labels.
- The local surface review and scorer audit are not independent human-subject validation.
- Phase 15 schema ablation was intentionally skipped on the main Phase 1 path; it was later completed as exploratory Phase 1.1 evidence.
- Some model-view pairs do not beat the simple heuristic; the paper states the narrower, accurate baseline claim.
- The paper compile has one bibliography underfull-box warning, not a build failure.

## Recommended Next Step

Use the completed Phase 1.1 ablation only as narrow schema/interface sensitivity evidence. The next larger step is an expanded role-uncued task set with independent human audit before making stronger ranking claims.
