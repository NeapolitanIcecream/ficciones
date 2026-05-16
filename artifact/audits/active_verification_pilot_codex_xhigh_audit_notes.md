# Active-Verification Pilot Codex XHigh Audit Notes

This is an LLM-assisted Codex audit, not a human audit. I reviewed the 50-row opaque active-verification pilot package row by row using the provided CSV, context JSONL, and human-audit guidelines.

## Method

- Preserved the original blank human-audit sheet and wrote a separate labeled CSV.
- Used the context JSONL audit roles to judge whether action targets were primary, contradiction, contaminant, stale, generated-lore, or background documents.
- Treated semantic usefulness and machine executability separately. A useful action can still fail machine executability if its target is bundled, vague, or not a direct tool target.
- Counted a target as exact only when it was a single `doc_###` or a direct schema-level search target. Multi-doc targets such as `doc_007 vs doc_008`, vague search targets such as `recall rate data`, and prose-extended targets such as `doc_007 upstream citations` were not counted as exact.
- Marked `required_action_type_present=1` only when the row covered the needed primary, contradiction, or trace-source action category under the written contract. For rejected rows, `scorer_too_strict=1` was used only where the action set was useful, executable, and reasonably satisfied the missing category through a direct schema-level target.

## Aggregate Counts

| label | count_1 | count_0 |
|---|---:|---:|
| semantically_useful_action | 50 | 0 |
| machine_executable_action | 47 | 3 |
| exact_target_present | 47 | 3 |
| required_action_type_present | 37 | 13 |
| scorer_too_strict | 2 | 48 |

By condition, all 10 rows in each condition were semantically useful. Machine/exact failures occurred in one conflicting-evidence row, one buried-primary row, and one generated-lore row. Required action type was missing in 3 clean rows and all 10 buried-primary rows. The two scorer-too-strict rows were row 20 and row 29.

## Illustrative Examples

- Row 2 was semantically useful and executable for tracing stale evidence, but it did not target a primary document or direct primary search, so the missing-primary rejection was not too strict.
- Row 19 opened exact primary/contradiction document `doc_008`, but the comparison target `doc_007 vs doc_008` was bundled, so machine/exact labels were withheld for the row.
- Row 20 was marked scorer-too-strict because the direct primary status search plus stale-source trace would execute a reasonable contradiction route even though the scorer missed it.
- Row 29 was marked scorer-too-strict because the primary audit search explicitly identified the contradictory audited figure in `doc_001`.
- Rows 31-40 were useful but lacked an explicit contradiction action, so the automatic missing-contradiction rejection was not marked too strict.
- Row 43 had the right trace-source action type, but `doc_007 upstream citations` was not an exact target, so it was not treated as machine executable under the strict target rule.

## Limitations

This audit is based on the opaque audit package and the visible context supplied in `active_verification_pilot_human_audit_context_50.jsonl`. I did not inspect hidden model reasoning or rerun the original model calls. The labels are row-level judgments over visible action sets, so rows with mixed-quality actions are summarized into single binary fields with the short note carrying the relevant caveat.
