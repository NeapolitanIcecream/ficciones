# EHA-Uncued Pilot Dataset

This directory contains the role-uncued pilot dataset used by the EHA-Uncued
synthetic diagnostic pilot. The model-visible files are listed in
`manifest.json`:

- `tasks.jsonl`
- `documents_neutral_metadata_visible.jsonl`
- `documents_neutral_metadata_hidden.jsonl`

Gold labels, document roles, dependency edges, and action targets are scorer
and audit inputs. They are not model-visible prompt fields.

## Timestamp Semantics

Document `timestamp` fields are synthetic, model-visible, and non-evidential.
They are included as neutral metadata for the dataset view, not as publication
dates, observation dates, recency cues, or evidence about answer validity. Task
interpretation should come from the task question and document body text, not
from absolute timestamp chronology.

Some document timestamps intentionally precede or follow the claim month in the
task question. This is a documentation limitation of the synthetic metadata,
not a row-level repair requirement for the pilot.

## Citation And Echo-Chain Semantics

`visible_citations` and `dependency_edges.jsonl` encode synthetic source
relations. False-consensus episodes may contain two-document mutual
visible-citation loops among polluted same-root echo documents. These loops are
part of the synthetic echo-chain structure and should not be interpreted as
independent corroboration or as acyclic provenance trees.

Scoring uses gold support, pollutant labels, and task-family contracts. Shortcut
baselines may consume visible citation structure, but the main scorer does not
require the dependency graph to be acyclic.
