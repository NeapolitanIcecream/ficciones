# EHA-Uncued Leakage And Shortcut Method Detail

Date: 2026-05-25

## Automatic Leakage Audit

The automatic audit is implemented in `eha-mvp/eha/uncued_leakage.py`. It scans model-visible task fields (`task_id`, `question`) and model-visible document fields (`task_id`, `doc_id`, `title`, `source_type`, `timestamp`, `body`, `visible_citations`) for:

- hidden scorer fields such as construction roles or gold labels;
- forbidden material-role labels such as primary, contaminant, pollutant, generated lore, no primary evidence, and insufficient evidence;
- semantic document identifiers or visible citation IDs that expose latent roles;
- direct-answer cues in task or document text.

For the pilot dataset the audit reports zero total hits, zero critical/high/medium hits, zero hidden-label hits, zero semantic-ID hits, and zero direct-answer-cue hits.

## Local Surface Review

The local pre-model surface review covered 400 document rows and 50 unique latent tasks. It found zero critical leaks, zero severe leakage rows, and zero role-guess hits. The review is a leakage gate only. It is not independent human validation and does not justify claims about external annotator agreement.

The review remained at 50 of 60 latent tasks because it was designed as a pre-model gate before paid model calls, not as a full annotation study. The paper now states this sampling boundary explicitly.

## Shortcut Baselines

The no-API shortcut baselines are implemented in `eha-mvp/eha/uncued_baselines.py`. The pilot reports:

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

The strongest shortcut is `simple_heuristic`, with operational escape `0.350` on the hidden view and `0.333` on the visible view. It uses shallow overlap and visible records, so it can recover some clean/easy rows, but it does not reconstruct roles and still carries polluted support on harder rows. This is a useful failure mode: the gates pass, but the heuristic is strong enough that the paper should not imply every model-view pair clears it.

## Artifact Pointers

Reproducible details are in:

- `artifact_uncued_phase1/audits/eha-uncued-leakage-pilot-2026-05-22.md`;
- `artifact_uncued_phase1/audits/uncued_leakage_pilot_rows.csv`;
- `artifact_uncued_phase1/baselines/eha-uncued-baselines-pilot-2026-05-22.md`;
- `artifact_uncued_phase1/baselines/uncued_baseline_rows_pilot.csv`;
- `artifact_uncued_phase1/scorer/uncued_report.py`;
- `artifact_uncued_phase1/verify_uncued_phase1.sh`.

