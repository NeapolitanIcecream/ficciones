# Active-Verification Pilot Human-Audit Guidelines

This sheet audits whether model actions are useful to a human reader and executable by an agent tool interface.

Label values should be `1` for yes, `0` for no, and blank only when the row has not been reviewed.

Do not sort, delete, duplicate, or reorder rows. Do not edit non-label columns; the validator compares them against the original sample sheet.

The Codex-assisted audit, if consulted, is reference-only triage. Do not copy its labels into this sheet unless an independent human auditor has reviewed the row and agrees with the judgment.

For the sampling design, evidence conditions, finalization gate, and claim boundary, see `active_verification_human_audit_protocol.md`.

Fields:

- `semantically_useful_action`: the proposed action would help a human investigate the evidence state.
- `machine_executable_action`: the action has a clear action type and a target a tool could execute without interpretation.
- `exact_target_present`: the target is a single exact `doc_###` or an explicit schema-level search target.
- `required_action_type_present`: the action type matches the needed primary, contradiction, or trace-source action.
- `contradiction_search_needed`: the task requires seeking or checking contradictory evidence.
- `primary_search_needed`: the task requires seeking, opening, or tracing a primary source.
- `trace_source_needed`: the task requires tracing a claim to its upstream source.
- `scorer_too_strict`: mark `1` only when the automatic scorer rejects an action that is both useful and reasonably executable under the written contract.

Important distinction: an action can be semantically useful but not machine executable. For example, a bundled target such as `doc_001 and doc_004 -> doc_007` may be understandable to a reader but unsafe for a tool call that expects one exact target.

The context JSONL uses opaque model-visible document IDs. `audit_role` is shown only for auditor context; it was not visible to the model.
