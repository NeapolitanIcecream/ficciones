# Paper Patch Notes

Date: 2026-05-15

## Current Status

The semantic-ID main run is quarantined as a leaky-ID run. It should not be used as final benchmark evidence.

The code now supports an opaque model-visible prompt view:

- model-visible `doc_id` values use per-task opaque IDs such as `doc_001`;
- visible citations are remapped into the same opaque namespace;
- audit-only source IDs in title/body text are scrubbed before model calls;
- model outputs are translated back to scorer-side audit IDs before scoring;
- prompt artifacts record the scorer-only visible-to-audit mapping outside the model message payload.

## Paper Changes Already Made

`paper/sections/09_limitations.tex` now states that a post-draft audit found semantic document identifiers in the current main-run prompts and that the present results should be read only as mechanism-finding evidence pending an opaque-ID rerun.

## Paper Changes Still Needed After Opaque Rerun

1. Replace all main tables with opaque-run tables.
2. Replace generated-lore case examples with model-visible opaque IDs plus separate audit alias tables.
3. Add a methods paragraph: early drafts exposed semantic document IDs; all reported main results use opaque per-task document IDs.
4. Add ID-only, metadata-only, and simple heuristic baselines to the results or appendix.
5. Recompute uncertainty intervals and any paired tests from opaque-run scored rows.
6. Remove or rewrite any claim based only on the leaky-ID run.
