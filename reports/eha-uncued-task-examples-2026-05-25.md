# EHA-Uncued Task And Scoring Examples

Date: 2026-05-25

Hidden roles in these examples are shown only for reader auditability. They are scorer-only fields and were not model-visible.

## Clean/Buried-Primary Success

- Task: `uncued_000_visible` / latent `uncued_000`.
- Family/condition/view: `packet_judgment` / `clean` / `neutral_metadata_visible`.
- Question: Did Novalis Robotics log 184 completed checks for Atlas valve checks in March 2025?
- Model: `gemini-3.1-pro-preview`.
- Gold/predicted verdict: `supported` / `supported`.
- Supporting evidence: `uncued_000_d03`.
- Selected docs: `uncued_000_d03`.
- Actions: `[{"action": "search_primary", "target": "monthly ledger for Northline service bay", "rationale": "To verify the 184 completed checks count against the primary source ledger."}]`.
- Scorer components: belief `1.000`, evidence precision `1.000`, polluted support `0.000`, required action recall `n/a`, operational escape `1.000`.
- Model answer: Yes, based on the provided evidence, the operations timeline note confirms that the monthly ledger for the Northline service bay lists 184 completed checks for Atlas valve checks in March 2025.

### Abbreviated Packet

| doc_id | title | source_type | timestamp | hidden_role | supports_gold_verdict | contamination | body |
| --- | --- | --- | --- | --- | --- | --- | --- |
| uncued_000_d01 | Service Ledger Extract | timeline note | 2025-01-16 | context | False |  | A routing note lists Northline service bay as the site for the Atlas valve checks workstream. The note does not provide a closing count. The note uses the same site code, workstream name, and monthly close... |
| uncued_000_d03 | Operations Timeline Note | field note | 2025-01-13 | clean_anchor | True |  | The monthly ledger for Northline service bay lists 184 completed checks for Atlas valve checks in March 2025. The entry is dated after the close of the month and uses the same work order code as the... |
| uncued_000_d04 | Program Registry Entry | operations memo | 2025-01-15 | context | False |  | A shift memo mentions that Atlas valve checks work was concentrated in the final week of March 2025. It tracks handoff timing but not the final tally. The note uses the same site code, workstream name, and... |
| uncued_000_d02 | Field Summary Memo | registry entry | 2025-01-14 | context | False |  | A planning note for Atlas valve checks describes the inspection route at Northline service bay during March 2025. It gives staffing context and does not include a final monthly count. The note uses the same... |

## Generated-Lore Hygiene Failure

- Task: `uncued_048_visible` / latent `uncued_048`.
- Family/condition/view: `packet_judgment` / `generated_lore` / `neutral_metadata_visible`.
- Question: Did Novalis Robotics launch the HelioSplice partner repair program in March 2025?
- Model: `claude-opus-4-7`.
- Gold/predicted verdict: `insufficient` / `insufficient`.
- Supporting evidence: `uncued_048_d01,uncued_048_d04`.
- Selected docs: `uncued_048_d04,uncued_048_d01,uncued_048_d03`.
- Actions: `[{"action": "trace_source", "target": "uncued_048_d01", "rationale": "The roundup is the originating claim; uncued_048_d04 merely cites it. Tracing to a primary operational record is needed to verify the launch."}, {"action": "search_primary", "target": "Novalis Robotics HelioSplice program registry", "rationale": "Registry and field memo show only routine Atlas valve checks with no HelioSplice entry. A primary launch record is required to confirm."}]`.
- Scorer components: belief `1.000`, evidence precision `0.000`, polluted support `1.000`, required action recall `n/a`, operational escape `0.000`.
- Model answer: Evidence is insufficient to confirm the launch. The only affirmative mentions (uncued_048_d01 roundup and uncued_048_d04 recap citing it) form a single unsourced chain, while the program registry (uncued_048_d02) and field memo (uncued_048_d03) covering the...

### Abbreviated Packet

| doc_id | title | source_type | timestamp | hidden_role | supports_gold_verdict | contamination | body |
| --- | --- | --- | --- | --- | --- | --- | --- |
| uncued_048_d04 | Service Ledger Extract | registry entry | 2025-04-14 | same_root_echo | False | unsupported | A partner recap repeats the HelioSplice partner repair program launch wording from the roundup. Its visible citation points to the roundup item. The note uses the same site code, workstream name, and monthly... |
| uncued_048_d01 | Operations Timeline Note | field note | 2025-04-13 | unsupported_story | False | unsupported | A community roundup says the HelioSplice partner repair program appeared during March 2025. The item gives a program name and month but no linked operational record. The note uses the same site code,... |
| uncued_048_d02 | Program Registry Entry | timeline note | 2025-04-16 | context | False |  | A monthly index names the Atlas valve checks workstream and site. It lists regular service categories but no program launch entry. The note uses the same site code, workstream name, and monthly close date as... |
| uncued_048_d03 | Field Summary Memo | operations memo | 2025-04-15 | context | False |  | A service planning memo for Northline service bay lists routine Atlas valve checks work in March 2025. It does not mention the HelioSplice partner repair program. The note uses the same site code, workstream... |

## Active-Verification Action Case

- Task: `uncued_010_visible` / latent `uncued_010`.
- Family/condition/view: `active_verification` / `clean` / `neutral_metadata_visible`.
- Question: Did Novalis Robotics log 118 completed refurbishments for Nova pump refurbishments in July 2025?
- Model: `claude-opus-4-7`.
- Gold/predicted verdict: `supported` / `supported`.
- Supporting evidence: `uncued_010_d01`.
- Selected docs: `uncued_010_d01,uncued_010_d02,uncued_010_d03`.
- Actions: `[{"action": "trace_source", "target": "uncued_010_d01", "rationale": "Verify the monthly ledger entry's provenance since it is the only document stating the 118 count."}, {"action": "search_primary", "target": "Harbor Annex July 2025 Nova pump refurbishment ledger", "rationale": "Locate the underlying primary ledger to corroborate the count beyond the field summary memo."}]`.
- Scorer components: belief `1.000`, evidence precision `1.000`, polluted support `0.000`, required action recall `1.0`, operational escape `1.000`.
- Model answer: Yes—uncued_010_d01 (Field Summary Memo) records 118 completed Nova pump refurbishments at Harbor Annex for July 2025, and no document contradicts this figure. Other documents corroborate the workstream and site context but lack counts. Confidence is...

### Abbreviated Packet

| doc_id | title | source_type | timestamp | hidden_role | supports_gold_verdict | contamination | body |
| --- | --- | --- | --- | --- | --- | --- | --- |
| uncued_010_d04 | Service Ledger Extract | timeline note | 2025-02-16 | context | False |  | A routing note lists Harbor Annex as the site for the Nova pump refurbishments workstream. The note does not provide a closing count. The note uses the same site code, workstream name, and monthly close date... |
| uncued_010_d03 | Operations Timeline Note | operations memo | 2025-02-15 | context | False |  | A shift memo mentions that Nova pump refurbishments work was concentrated in the final week of July 2025. It tracks handoff timing but not the final tally. The note uses the same site code, workstream name,... |
| uncued_010_d02 | Program Registry Entry | registry entry | 2025-02-14 | context | False |  | A planning note for Nova pump refurbishments describes the inspection route at Harbor Annex during July 2025. It gives staffing context and does not include a final monthly count. The note uses the same site... |
| uncued_010_d01 | Field Summary Memo | field note | 2025-02-13 | clean_anchor | True |  | The monthly ledger for Harbor Annex lists 118 completed refurbishments for Nova pump refurbishments in July 2025. The entry is dated after the close of the month and uses the same work order code as the... |

### Action Gold

```json
{
  "machine_executable_target_required": true,
  "required_action_types": [
    "open_best_visible_record"
  ],
  "required_target_doc_ids_by_view": {
    "neutral_metadata_hidden": [
      "uncued_010_d03"
    ],
    "neutral_metadata_visible": [
      "uncued_010_d01"
    ]
  },
  "task_id": "uncued_010"
}
```
