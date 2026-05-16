# Active-Verification Pilot Human-Audit Packet

Use this packet with `active_verification_pilot_human_audit_sample_50.csv`. Fill labels in the CSV, not in this Markdown file.

Label values are `1` for yes and `0` for no. Keep blanks only for rows not reviewed.

A useful action can still be non-executable if the target is bundled, vague, or not a direct tool target.

## Row 01: ert_080 / claude-opus-4-7 / clean / epistemic_hygiene_instruction

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_002` rationale=Confirm the audit_report's raw operating records and reviewer sign-off as the primary basis for the 2024-12-12 completion date.
- `compare_versions` target=`doc_007` rationale=Check whether the 'still pending' planning note predates and was superseded by the December audit completion.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_002, doc_006
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_003, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_002` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_006` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_007` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_003` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`background` source_type=`meeting_minutes` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_004` audit_role=`background` source_type=`quality_digest` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 02: ert_080 / claude-opus-4-7 / clean / standard_answer

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 1.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_003` rationale=Both secondary 'still pending' items trace back to doc_007, an outdated November planning note, indicating a single stale upstream rather than independent corroboration.
- `compare_versions` target=`doc_007` rationale=Compare the November planning note against the January audit record and regulator filing to confirm the pending status was superseded by the December 12 completion.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_002, doc_006
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_003, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_002` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_006` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_007` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_003` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`background` source_type=`meeting_minutes` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_004` audit_role=`background` source_type=`quality_digest` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 03: ert_081 / claude-opus-4-7 / clean / epistemic_hygiene_instruction

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_002` rationale=Verify whether the regulator filing is genuinely independent of doc_007 or merely repeats it, since they share identical wording.
- `compare_versions` target=`doc_003` rationale=The 'still pending' claim is from November 2024, predating the December 12 completion date, so check if it was superseded.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_007, doc_002
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_004, doc_008
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_002` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_003` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`background` source_type=`meeting_minutes` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_001` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 04: ert_081 / claude-opus-4-7 / clean / standard_answer

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_004` rationale=Secondary coverage items doc_004 and doc_008 both trace back to doc_003, an outdated planning note, indicating a single upstream source rather than independent confirmation.
- `compare_versions` target=`doc_007` rationale=Confirm the January 2025 audit report and its regulator filing corroboration reflect the most recent status, superseding the November planning note.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_007, doc_002
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_004, doc_008
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_002` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_003` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`background` source_type=`meeting_minutes` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_001` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 05: ert_082 / claude-opus-4-7 / clean / epistemic_hygiene_instruction

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_008` rationale=Confirm whether the regulator filing is genuinely independent of doc_004 or merely restates it, since the bodies are identical.
- `search_contradiction` target=`doc_007` rationale=The pending claim originates in a pre-audit November 2024 planning note that predates the December 12 completion date, so verify no later contradiction exists.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_004, doc_008
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_005, doc_002
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_004` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_008` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_007` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_005` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`background` source_type=`release_note` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`release_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 06: ert_082 / claude-opus-4-7 / clean / standard_answer

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 1.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_005` rationale=Both secondary 'pending' items cite doc_007, indicating a single upstream source rather than independent corroboration.
- `compare_versions` target=`doc_007` rationale=doc_007 predates the audit completion date (2024-12-12), so its 'pending' claim is stale relative to the primary audit record.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_004, doc_008
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_005, doc_002
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_004` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_008` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_007` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_005` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`background` source_type=`release_note` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`release_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 07: ert_083 / claude-opus-4-7 / clean / epistemic_hygiene_instruction

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_008` rationale=doc_008 cites doc_004, so confirm whether it is independent corroboration or pseudo-consensus repeating the same upstream record.
- `search_contradiction` target=`doc_005` rationale=Check whether the 'still pending' claim has any primary backing beyond stale planning notes copied across doc_007 and doc_001.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_004, doc_008
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_005, doc_007, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_004` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_008` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_005` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_007` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`background` source_type=`customer_note` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`meeting_minutes` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_002` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 08: ert_083 / claude-opus-4-7 / clean / standard_answer

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 1.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=Secondary coverage cites doc_005, an outdated planning note; tracing confirms the 'pending' claim derives from a single stale upstream source.
- `compare_versions` target=`doc_005` rationale=Compare the November 2024 planning note against the January 2025 signed audit record to confirm the status changed before the renewal meeting.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_004, doc_008
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_005, doc_007, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_004` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_008` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_005` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_007` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`background` source_type=`customer_note` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`meeting_minutes` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_002` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 09: ert_080 / deepseek-v4-pro / clean / epistemic_hygiene_instruction

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`audit record for Q4 supplier audit` rationale=Looked for primary audit document to verify completion date directly.
- `trace_source` target=`doc_007` rationale=Traced the 'still pending' claims back to the outdated planning note from November, revealing staleness.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_002, doc_006
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_003, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_002` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_006` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_007` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_003` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`background` source_type=`meeting_minutes` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_004` audit_role=`background` source_type=`quality_digest` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 10: ert_080 / deepseek-v4-pro / clean / standard_answer

Question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 0.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=Document claims audit still pending but is from November 2024, before the reported completion date. Tracing its source reveals it's an outdated planning note, not reflecting the December 12 completion.
- `search_primary` target=`Novalis Robotics 2024-Q4 supplier audit report` rationale=The official audit report (doc_002) and regulator filing (doc_006) consistently show completion on 2024-12-12. Searching for the primary raw records would further confirm the date and sign-offs.

Gold context for auditor:
- gold_verdict: supported
- primary_doc_ids: doc_002, doc_006
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_003, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_002` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_006` audit_role=`primary` source_type=`regulator_filing` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the supplier audit was completed on 2024-12-12 and cleared for renewal review. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_007` audit_role=`contaminant` source_type=`old_planning_note` title=Authoritative-looking summary claiming still pending in January 2025
  Excerpt: Authoritative-looking summary An outdated planning note says the audit was still pending. This source repeats the wording of the question: Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_003` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 1: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: still pending in January 2025
  Excerpt: Secondary coverage This item repeats that still pending in January 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`background` source_type=`meeting_minutes` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_004` audit_role=`background` source_type=`quality_digest` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 11: ert_084 / claude-opus-4-7 / conflicting_evidence / epistemic_hygiene_instruction

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_008` rationale=Confirm the certification record's reviewer sign-off and raw logs as primary evidence of lapse on 2024-12-31.
- `search_contradiction` target=`doc_007` rationale=The 'valid through 2025' claim relies on a 2024-11 summary citing secondary sources; check for any primary renewal filing that would override the lapse record.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_008, doc_001
- contradiction_doc_ids: doc_008, doc_001
- contaminant_doc_ids: doc_007, doc_003, doc_002
- generated_doc_ids: (none)
- stale_doc_ids: doc_007, doc_003, doc_002

Documents:
- `doc_007` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_003` audit_role=`stale` source_type=`supplier_whitepaper` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`stale` source_type=`wiki_style_summary` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_001` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_004` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`release_note` title=Reference note 11
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 12: ert_084 / claude-opus-4-7 / conflicting_evidence / standard_answer

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=Doc_003 and doc_002 both cite doc_007, indicating a single upstream source rather than independent corroboration.
- `compare_versions` target=`doc_008` rationale=Confirm the certification record's lapse date against the independent version history in doc_001.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_008, doc_001
- contradiction_doc_ids: doc_008, doc_001
- contaminant_doc_ids: doc_007, doc_003, doc_002
- generated_doc_ids: (none)
- stale_doc_ids: doc_007, doc_003, doc_002

Documents:
- `doc_007` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_003` audit_role=`stale` source_type=`supplier_whitepaper` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`stale` source_type=`wiki_style_summary` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_001` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_004` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`release_note` title=Reference note 11
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 13: ert_085 / claude-opus-4-7 / conflicting_evidence / epistemic_hygiene_instruction

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=Confirm the certification record's primary status and reviewer sign-off as the basis for the lapse finding.
- `compare_versions` target=`doc_001` rationale=Cross-check the version history against doc_007 to confirm independent corroboration of the 2024-12-31 lapse.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_007, doc_001
- contradiction_doc_ids: doc_007, doc_001
- contaminant_doc_ids: doc_003, doc_004, doc_008
- generated_doc_ids: (none)
- stale_doc_ids: doc_003, doc_004, doc_008

Documents:
- `doc_003` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`stale` source_type=`wiki_style_summary` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`stale` source_type=`press_release` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_001` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_002` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`quality_digest` title=Reference note 11
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 14: ert_085 / claude-opus-4-7 / conflicting_evidence / standard_answer

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_004` rationale=Secondary coverage cites doc_003; tracing confirms a single upstream rather than independent confirmation.
- `compare_versions` target=`doc_007` rationale=Compare the certification record with later independent corroboration (doc_001) to confirm lapse date and renewal status.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_007, doc_001
- contradiction_doc_ids: doc_007, doc_001
- contaminant_doc_ids: doc_003, doc_004, doc_008
- generated_doc_ids: (none)
- stale_doc_ids: doc_003, doc_004, doc_008

Documents:
- `doc_003` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`stale` source_type=`wiki_style_summary` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`stale` source_type=`press_release` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_001` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_002` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`quality_digest` title=Reference note 11
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 15: ert_086 / claude-opus-4-7 / conflicting_evidence / epistemic_hygiene_instruction

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_006` rationale=Confirm the signed certification record and reviewer sign-off as primary evidence of lapse on 2024-12-31.
- `compare_versions` target=`doc_008` rationale=Check whether the authoritative-looking summary has primary backing or only secondary citations repeated by doc_005 and doc_007.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_006, doc_004
- contradiction_doc_ids: doc_006, doc_004
- contaminant_doc_ids: doc_008, doc_005, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: doc_008, doc_005, doc_007

Documents:
- `doc_008` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_005` audit_role=`stale` source_type=`press_release` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`stale` source_type=`executive_memo` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_004` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_002` audit_role=`background` source_type=`meeting_minutes` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`customer_note` title=Reference note 11
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_001` audit_role=`background` source_type=`quality_digest` title=Reference note 12
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 16: ert_086 / claude-opus-4-7 / conflicting_evidence / standard_answer

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_005` rationale=Secondary items copy doc_008's wording; tracing confirms a single upstream source rather than independent corroboration.
- `compare_versions` target=`doc_006` rationale=Cross-check the certification record against doc_004's independent corroboration to confirm the lapse date.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_006, doc_004
- contradiction_doc_ids: doc_006, doc_004
- contaminant_doc_ids: doc_008, doc_005, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: doc_008, doc_005, doc_007

Documents:
- `doc_008` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_005` audit_role=`stale` source_type=`press_release` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`stale` source_type=`executive_memo` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_004` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_002` audit_role=`background` source_type=`meeting_minutes` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`customer_note` title=Reference note 11
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_001` audit_role=`background` source_type=`quality_digest` title=Reference note 12
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 17: ert_087 / claude-opus-4-7 / conflicting_evidence / epistemic_hygiene_instruction

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_002` rationale=Confirm the certification record is a primary regulator-signed document showing lapse on 2024-12-31.
- `compare_versions` target=`doc_003` rationale=Check whether doc_008 and doc_007 independently verify or merely repeat doc_003's wording, indicating pseudo-consensus.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_002, doc_001
- contradiction_doc_ids: doc_002, doc_001
- contaminant_doc_ids: doc_003, doc_008, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: doc_003, doc_008, doc_007

Documents:
- `doc_003` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_008` audit_role=`stale` source_type=`executive_memo` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`stale` source_type=`industry_digest` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_001` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_004` audit_role=`background` source_type=`meeting_minutes` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`meeting_minutes` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`release_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 18: ert_087 / claude-opus-4-7 / conflicting_evidence / standard_answer

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_008` rationale=Secondary items doc_008 and doc_007 both cite doc_003, indicating a single upstream source rather than independent corroboration.
- `compare_versions` target=`doc_002` rationale=Confirm the certification record against the independent corroboration in doc_001 to verify the 2024-12-31 lapse.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_002, doc_001
- contradiction_doc_ids: doc_002, doc_001
- contaminant_doc_ids: doc_003, doc_008, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: doc_003, doc_008, doc_007

Documents:
- `doc_003` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_008` audit_role=`stale` source_type=`executive_memo` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`stale` source_type=`industry_digest` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_001` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_004` audit_role=`background` source_type=`meeting_minutes` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`meeting_minutes` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`release_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 19: ert_084 / deepseek-v4-pro / conflicting_evidence / epistemic_hygiene_instruction

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `open` target=`doc_008` rationale=Primary certification record dated 2025-01-15 directly states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved.
- `compare_versions` target=`doc_007 vs doc_008` rationale=doc_007 claims certification valid through 2025 but lacks primary support, while doc_008 is a primary record that refutes it.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_008, doc_001
- contradiction_doc_ids: doc_008, doc_001
- contaminant_doc_ids: doc_007, doc_003, doc_002
- generated_doc_ids: (none)
- stale_doc_ids: doc_007, doc_003, doc_002

Documents:
- `doc_007` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_003` audit_role=`stale` source_type=`supplier_whitepaper` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`stale` source_type=`wiki_style_summary` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_001` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_004` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`release_note` title=Reference note 11
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 20: ert_084 / deepseek-v4-pro / conflicting_evidence / standard_answer

Question: Was Novalis Robotics' EU safety certification still valid in January 2025?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=Trace the origin of the valid-through-2025 claim to assess reliability. doc_007 is an old certificate notice that may not reflect later changes.
- `search_primary` target=`Novalis Robotics EU safety certification record January 2025` rationale=Search for primary certification records to verify the status during the target period.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_008, doc_001
- contradiction_doc_ids: doc_008, doc_001
- contaminant_doc_ids: doc_007, doc_003, doc_002
- generated_doc_ids: (none)
- stale_doc_ids: doc_007, doc_003, doc_002

Documents:
- `doc_007` audit_role=`stale` source_type=`old_certificate_notice` title=Authoritative-looking summary claiming valid through 2025
  Excerpt: Authoritative-looking summary The 2023 certificate was valid at the time it was issued. This source repeats the wording of the question: Was Novalis Robotics' EU safety certification still valid in January 2025? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_003` audit_role=`stale` source_type=`supplier_whitepaper` title=Secondary coverage 1: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`stale` source_type=`wiki_style_summary` title=Secondary coverage 2: valid through 2025
  Excerpt: Secondary coverage This item repeats that valid through 2025. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`primary` source_type=`certification_record` title=Novalis Robotics record for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_001` audit_role=`primary` source_type=`version_history` title=Independent corroboration for 2025-Q1
  Excerpt: Record The signed record states that the EU safety certificate lapsed on 2024-12-31 with renewal unresolved. The finding is based on raw operating records, dated logs, and reviewer sign-off.
- `doc_004` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`customer_note` title=Reference note 10
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_005` audit_role=`background` source_type=`release_note` title=Reference note 11
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 21: ert_088 / claude-opus-4-7 / false_consensus / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_005` rationale=All secondary items trace back to doc_005, which lacks primary citations. Tracing confirms pseudo-consensus rather than independent verification.
- `compare_versions` target=`doc_001` rationale=Verify the audit report's 3.8% figure against any other primary records to confirm the contradiction with the repeated 1.7% claim.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_001
- contradiction_doc_ids: doc_001
- contaminant_doc_ids: doc_005, doc_006, doc_004, doc_003, doc_002, doc_008, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_005` audit_role=`contaminant` source_type=`industry_digest` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 22: ert_088 / claude-opus-4-7 / false_consensus / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_005` rationale=All secondary items cite doc_005, so the apparent consensus collapses to a single upstream claim.
- `search_primary` target=`doc_001` rationale=Audit report with raw records and reviewer sign-off is the strongest primary source for the recall rate.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_001
- contradiction_doc_ids: doc_001
- contaminant_doc_ids: doc_005, doc_006, doc_004, doc_003, doc_002, doc_008, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_005` audit_role=`contaminant` source_type=`industry_digest` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 23: ert_089 / claude-opus-4-7 / false_consensus / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_003` rationale=All secondary documents trace back to doc_003, which cites only secondary summaries with no primary records. Tracing confirms pseudo-consensus.
- `search_primary` target=`doc_004` rationale=Audit report with signed reviewer and raw logs is the strongest primary record and directly contradicts the repeated claim.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_004
- contradiction_doc_ids: doc_004
- contaminant_doc_ids: doc_003, doc_006, doc_005, doc_001, doc_002, doc_008, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_006` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 24: ert_089 / claude-opus-4-7 / false_consensus / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_003` rationale=All secondary items cite doc_003, which itself relies on summaries rather than raw records. Tracing confirms a single upstream origin behind the apparent consensus.
- `search_primary` target=`doc_004` rationale=doc_004 is a signed audit based on raw logs and reviewer sign-off, the strongest primary evidence for the actual 2024 recall rate.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_004
- contradiction_doc_ids: doc_004
- contaminant_doc_ids: doc_003, doc_006, doc_005, doc_001, doc_002, doc_008, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_006` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 25: ert_090 / claude-opus-4-7 / false_consensus / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_005` rationale=All secondary items cite doc_005, which itself cites only secondary summaries. Tracing confirms pseudo-consensus with no primary basis.
- `search_primary` target=`doc_007` rationale=Audit report with raw operating records and reviewer sign-off is the strongest primary source and directly contradicts the 1.7% claim.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_007
- contradiction_doc_ids: doc_007
- contaminant_doc_ids: doc_005, doc_004, doc_008, doc_001, doc_002, doc_006, doc_003
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_004` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 26: ert_090 / claude-opus-4-7 / false_consensus / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_005` rationale=All secondary items copy doc_005's wording; tracing confirms a single upstream origin rather than independent confirmation.
- `search_primary` target=`doc_007` rationale=Audit report with raw logs and sign-off is the authoritative primary source for the recall rate.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_007
- contradiction_doc_ids: doc_007
- contaminant_doc_ids: doc_005, doc_004, doc_008, doc_001, doc_002, doc_006, doc_003
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_004` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 27: ert_091 / claude-opus-4-7 / false_consensus / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=All secondary items cite doc_007, which itself relies on summaries rather than primary records. Tracing confirms pseudo-consensus, not independent confirmation.
- `compare_versions` target=`doc_006` rationale=Audit report contradicts the press chain; verify the signed audit figure against any later restatements before finalizing.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_006
- contradiction_doc_ids: doc_006
- contaminant_doc_ids: doc_007, doc_002, doc_004, doc_001, doc_008, doc_005, doc_003
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`contaminant` source_type=`press_release` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_002` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 28: ert_091 / claude-opus-4-7 / false_consensus / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=All secondary items cite doc_007, which itself relies on summaries rather than raw records. Tracing confirms a single upstream origin.
- `search_primary` target=`doc_006` rationale=The signed audit report based on raw operating records is the authoritative primary source and contradicts the press claim.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_006
- contradiction_doc_ids: doc_006
- contaminant_doc_ids: doc_007, doc_002, doc_004, doc_001, doc_008, doc_005, doc_003
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`contaminant` source_type=`press_release` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_002` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 29: ert_088 / deepseek-v4-pro / false_consensus / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 recall rate audit` rationale=A direct primary source is needed to verify the actual recall rate; doc_001 provides an audited figure contradicting the claimed sub-2% rate.
- `trace_source` target=`doc_005` rationale=Doc_005 lacks citations and appears to be the sole origin of the repeated 1.7% claim; tracing reveals no primary support, indicating a false consensus.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_001
- contradiction_doc_ids: doc_001
- contaminant_doc_ids: doc_005, doc_006, doc_004, doc_003, doc_002, doc_008, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_005` audit_role=`contaminant` source_type=`industry_digest` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 30: ert_088 / deepseek-v4-pro / false_consensus / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`doc_001` rationale=This is the only primary record with audited numbers; verifying it provides the authoritative recall rate.
- `trace_source` target=`doc_005` rationale=The 1.7% claim originates from this summary which lacks raw data; tracing its source reveals it's uncorroborated secondary reporting.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: doc_001
- contradiction_doc_ids: doc_001
- contaminant_doc_ids: doc_005, doc_006, doc_004, doc_003, doc_002, doc_008, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_005` audit_role=`contaminant` source_type=`industry_digest` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`primary` source_type=`audit_report` title=Novalis Robotics record for 2024-Q4
  Excerpt: Record The signed record states that the audited 2024 recall rate was 3.8 percent. The finding is based on raw operating records, dated logs, and reviewer sign-off.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 31: ert_092 / claude-opus-4-7 / buried_primary / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 regulatory recall filings or audited annual report` rationale=No primary record, regulator filing, or audit is present. The claim needs a verifiable raw recall rate disclosure.
- `trace_source` target=`doc_003` rationale=doc_003 is the upstream that all secondary items cite. It presents no primary basis, only repeats the question phrasing. Tracing its origin is required before accepting the figure.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_007, doc_006, doc_005, doc_002, doc_008, doc_004, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`contaminant` source_type=`executive_memo` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_007` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 32: ert_092 / claude-opus-4-7 / buried_primary / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 audited recall data or regulatory filing` rationale=Need primary records (e.g., regulator filings, audited safety reports) rather than executive memos to verify the recall rate claim.
- `trace_source` target=`doc_003` rationale=doc_003 is the upstream node all secondary coverage cites; identifying its underlying data source is essential to assess credibility.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_007, doc_006, doc_005, doc_002, doc_008, doc_004, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`contaminant` source_type=`executive_memo` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_007` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 33: ert_093 / claude-opus-4-7 / buried_primary / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 annual report or regulator recall filings` rationale=No primary record, audit, or regulator filing is present. Need raw recall data to verify the sub-2% figure.
- `trace_source` target=`doc_003` rationale=doc_003 is the upstream of all repeats but cites only secondary summaries. Tracing its origin is needed to test whether any primary source supports the 1.7% claim.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_002, doc_001, doc_006, doc_008, doc_004, doc_005, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`contaminant` source_type=`industry_digest` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_002` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 34: ert_093 / claude-opus-4-7 / buried_primary / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 official recall disclosure or regulatory filing` rationale=All available items trace to a single upstream summary; primary records (regulator filings, audited annual report) are needed to verify the 1.7% figure.
- `trace_source` target=`doc_003` rationale=doc_003 is the apparent origin but cites only secondary summaries with no raw data; tracing its underlying source is required before accepting the claim.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_002, doc_001, doc_006, doc_008, doc_004, doc_005, doc_007
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`contaminant` source_type=`industry_digest` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_002` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 35: ert_094 / claude-opus-4-7 / buried_primary / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 recall rate regulatory filing or audited annual report` rationale=No primary record (regulator filing, audit, or company financial disclosure) is present. A primary source is required to confirm the sub-2% recall claim.
- `trace_source` target=`doc_007` rationale=doc_007 is the upstream of all other items but cites only secondary summaries. Tracing its origin would reveal whether any primary record underlies the 1.7% figure.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_006, doc_008, doc_004, doc_001, doc_003, doc_002, doc_005
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_006` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 36: ert_094 / claude-opus-4-7 / buried_primary / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 official recall disclosure or regulatory filing` rationale=No primary record (regulator filing, audited report) is present. Need raw recall data to verify the sub-2% figure.
- `trace_source` target=`doc_007` rationale=doc_007 is the upstream node all secondary items cite. Tracing its underlying citations would reveal whether any primary evidence exists or if the claim is unsourced.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_006, doc_008, doc_004, doc_001, doc_003, doc_002, doc_005
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_006` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 37: ert_095 / claude-opus-4-7 / buried_primary / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 recall rate regulator filing or annual report` rationale=No primary record is present. A regulator filing, audit, or company annual report is needed to verify the 1.7% figure.
- `trace_source` target=`doc_007` rationale=doc_007 is the upstream summary all other documents cite. Tracing its underlying source would reveal whether any primary basis exists.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_004, doc_005, doc_002, doc_006, doc_001, doc_008, doc_003
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`contaminant` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_004` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 38: ert_095 / claude-opus-4-7 / buried_primary / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 official recall disclosure or regulatory filing` rationale=All available documents trace back to a single wiki-style summary; a primary source (regulator filing, audited annual report) is needed to verify the 1.7% figure.
- `trace_source` target=`doc_007` rationale=doc_007 is the upstream node cited by every secondary item but contains no raw records or citations itself; its provenance must be established.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_004, doc_005, doc_002, doc_006, doc_001, doc_008, doc_003
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`contaminant` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_004` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 39: ert_092 / deepseek-v4-pro / buried_primary / epistemic_hygiene_instruction

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_003` rationale=doc_003 is the single upstream source for all other documents; tracing it may reveal if it is based on primary records or mere hearsay.
- `search_primary` target=`recall rate data` rationale=No primary records such as regulator filings or audits are present; a primary search is essential to verify the 1.7% figure.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_007, doc_006, doc_005, doc_002, doc_008, doc_004, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`contaminant` source_type=`executive_memo` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_007` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 40: ert_092 / deepseek-v4-pro / buried_primary / standard_answer

Question: Did Novalis Robotics reduce its 2024 recall rate below two percent?

Pre-filled needed-action labels to verify:
- primary_search_needed: 1.0
- contradiction_search_needed: 1.0
- trace_source_needed: 0.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 1.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics 2024 recall data` rationale=No primary source is present; all documents are secondary and trace to an unverified memo. Original recall data is needed to evaluate the claim.
- `trace_source` target=`doc_003` rationale=All documents cite doc_003, which itself lacks supporting raw records. Investigating its origin may reveal whether it has any reliable basis.

Gold context for auditor:
- gold_verdict: refuted
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_007, doc_006, doc_005, doc_002, doc_008, doc_004, doc_001
- generated_doc_ids: (none)
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`contaminant` source_type=`executive_memo` title=Authoritative-looking summary claiming 1.7% recall rate
  Excerpt: Authoritative-looking summary Novalis cut the 2024 recall rate below two percent. This source repeats the wording of the question: Did Novalis Robotics reduce its 2024 recall rate below two percent? It presents the result as settled and cites secondary summaries rather than raw records. Executive and industry summaries describe the repeated figure as a confirmed operating result.
- `doc_007` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 1: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 2: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 3: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 4: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 5: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 6: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 7: 1.7% recall rate
  Excerpt: Secondary coverage This item repeats that 1.7% recall rate. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 41: ert_096 / claude-opus-4-7 / generated_lore / epistemic_hygiene_instruction

Question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics regulator filings or audit records referencing Project LumenShield (2024)` rationale=Need a primary record to confirm the project's existence and timing rather than relying on copied summaries.
- `trace_source` target=`doc_007` rationale=doc_007 is the upstream wiki-style summary cited by all secondary coverage; tracing its sources would expose whether any primary basis exists.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_004, doc_008, doc_001, doc_002
- generated_doc_ids: doc_007, doc_004
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming Project LumenShield ran in 2024
  Excerpt: Authoritative-looking summary Project lumenshield was a 2024 field-hardening initiative. This source repeats the wording of the question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`generated_lore` source_type=`press_release` title=Secondary coverage 1: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 3: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 4: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`background` source_type=`release_note` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`quality_digest` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 42: ert_096 / claude-opus-4-7 / generated_lore / standard_answer

Question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=doc_007 is the upstream summary that all secondary coverage cites. Tracing its underlying records would reveal whether any primary source supports the claim.
- `search_primary` target=`Novalis Robotics Project LumenShield 2024 primary records` rationale=No primary documentation (internal records, filings, or first-party announcements) is present. A primary search is needed to confirm or refute the project's existence.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_004, doc_008, doc_001, doc_002
- generated_doc_ids: doc_007, doc_004
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming Project LumenShield ran in 2024
  Excerpt: Authoritative-looking summary Project lumenshield was a 2024 field-hardening initiative. This source repeats the wording of the question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`generated_lore` source_type=`press_release` title=Secondary coverage 1: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 3: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 4: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`background` source_type=`release_note` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`quality_digest` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 43: ert_097 / claude-opus-4-7 / generated_lore / epistemic_hygiene_instruction

Question: Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 0.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 1.0

Model actions:
- `search_primary` target=`MiraCert certification registry or Novalis Robotics 2024 press release/regulatory filing` rationale=No primary record (regulator filing, MiraCert registry entry, or official Novalis announcement) is present. A primary source is needed to confirm the alleged deal.
- `trace_source` target=`doc_007 upstream citations` rationale=doc_007 is the apparent origin; all secondary items cite it. Tracing its actual upstream basis would reveal whether any primary evidence exists.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_004, doc_006, doc_003, doc_005
- generated_doc_ids: doc_007, doc_004
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Authoritative-looking summary Novalis signed a 2024 miracert quantum battery certification deal. This source repeats the wording of the question: Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`generated_lore` source_type=`executive_memo` title=Secondary coverage 1: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 2: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 3: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 4: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`background` source_type=`customer_note` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_002` audit_role=`background` source_type=`quality_digest` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_001` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 44: ert_097 / claude-opus-4-7 / generated_lore / standard_answer

Question: Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=doc_007 is the upstream source all secondary coverage cites; tracing it would reveal whether any primary record (MiraCert registry, Novalis filing) actually exists.
- `search_primary` target=`MiraCert certification registry / Novalis Robotics 2024 disclosures` rationale=Need an independent primary record to confirm or refute the deal, since current evidence is a single-source echo chamber.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_004, doc_006, doc_003, doc_005
- generated_doc_ids: doc_007, doc_004
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Authoritative-looking summary Novalis signed a 2024 miracert quantum battery certification deal. This source repeats the wording of the question: Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`generated_lore` source_type=`executive_memo` title=Secondary coverage 1: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 2: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_003` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 3: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 4: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`background` source_type=`customer_note` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_002` audit_role=`background` source_type=`quality_digest` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_001` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 45: ert_098 / claude-opus-4-7 / generated_lore / epistemic_hygiene_instruction

Question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`Novalis Robotics official records or regulator filings on Project LumenShield 2024` rationale=No primary records, audits, or filings are present. Need direct corporate or regulatory confirmation.
- `trace_source` target=`doc_003` rationale=All secondary items trace back to doc_003, which itself cites only secondary summaries. Tracing upstream is required to determine if any primary basis exists.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_005, doc_001, doc_004, doc_006
- generated_doc_ids: doc_003, doc_005
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming Project LumenShield ran in 2024
  Excerpt: Authoritative-looking summary Project lumenshield was a 2024 field-hardening initiative. This source repeats the wording of the question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_005` audit_role=`generated_lore` source_type=`industry_digest` title=Secondary coverage 1: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 3: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 4: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`background` source_type=`customer_note` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_008` audit_role=`background` source_type=`customer_note` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_007` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 46: ert_098 / claude-opus-4-7 / generated_lore / standard_answer

Question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_003` rationale=doc_003 is the upstream summary that all secondary coverage cites. Tracing its underlying records would reveal whether any primary documentation supports the claim.
- `search_primary` target=`Novalis Robotics Project LumenShield 2024 primary records` rationale=No primary source (internal report, regulatory filing, or first-party announcement) is present. A primary search is needed to confirm or refute the claim.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_003, doc_005, doc_001, doc_004, doc_006
- generated_doc_ids: doc_003, doc_005
- stale_doc_ids: (none)

Documents:
- `doc_003` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming Project LumenShield ran in 2024
  Excerpt: Authoritative-looking summary Project lumenshield was a 2024 field-hardening initiative. This source repeats the wording of the question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_005` audit_role=`generated_lore` source_type=`industry_digest` title=Secondary coverage 1: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 2: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 3: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_006` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 4: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`background` source_type=`customer_note` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_008` audit_role=`background` source_type=`customer_note` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_007` audit_role=`background` source_type=`quality_digest` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 47: ert_099 / claude-opus-4-7 / generated_lore / epistemic_hygiene_instruction

Question: Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `search_primary` target=`MiraCert certification registry / Novalis Robotics 2024 filings` rationale=No primary regulator filing, audit, or MiraCert registry record is present. A direct primary search is needed to confirm or refute.
- `trace_source` target=`doc_006` rationale=All secondary items cite doc_006, which itself cites only secondary summaries. Tracing upstream would expose whether any original record exists.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_006, doc_005, doc_008, doc_004, doc_002
- generated_doc_ids: doc_006, doc_005
- stale_doc_ids: (none)

Documents:
- `doc_006` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Authoritative-looking summary Novalis signed a 2024 miracert quantum battery certification deal. This source repeats the wording of the question: Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_005` audit_role=`generated_lore` source_type=`supplier_whitepaper` title=Secondary coverage 1: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 2: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 3: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 4: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`background` source_type=`quality_digest` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_001` audit_role=`background` source_type=`customer_note` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`meeting_minutes` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 48: ert_099 / claude-opus-4-7 / generated_lore / standard_answer

Question: Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_006` rationale=doc_006 is the apparent upstream source that all secondary items cite; tracing it would reveal whether any primary record exists.
- `search_primary` target=`MiraCert certification registry / Novalis Robotics 2024 filings` rationale=Need a primary record (registry entry, signed agreement, or official MiraCert announcement) to confirm or refute the claim.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_006, doc_005, doc_008, doc_004, doc_002
- generated_doc_ids: doc_006, doc_005
- stale_doc_ids: (none)

Documents:
- `doc_006` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Authoritative-looking summary Novalis signed a 2024 miracert quantum battery certification deal. This source repeats the wording of the question: Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_005` audit_role=`generated_lore` source_type=`supplier_whitepaper` title=Secondary coverage 1: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`wiki_style_summary` title=Secondary coverage 2: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_004` audit_role=`contaminant` source_type=`press_release` title=Secondary coverage 3: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 4: signed a 2024 MiraCert quantum battery certification deal
  Excerpt: Secondary coverage This item repeats that signed a 2024 MiraCert quantum battery certification deal. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_007` audit_role=`background` source_type=`quality_digest` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_001` audit_role=`background` source_type=`customer_note` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`meeting_minutes` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 49: ert_096 / deepseek-v4-pro / generated_lore / epistemic_hygiene_instruction

Question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=Trace the origin of the claim; it only cites secondary summaries, lacking primary evidence.
- `search_primary` target=`Project LumenShield Novalis Robotics 2024` rationale=Search for primary records like official filings or audits; none were present in the environment.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_004, doc_008, doc_001, doc_002
- generated_doc_ids: doc_007, doc_004
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming Project LumenShield ran in 2024
  Excerpt: Authoritative-looking summary Project lumenshield was a 2024 field-hardening initiative. This source repeats the wording of the question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`generated_lore` source_type=`press_release` title=Secondary coverage 1: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 3: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 4: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`background` source_type=`release_note` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`quality_digest` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:

## Row 50: ert_096 / deepseek-v4-pro / generated_lore / standard_answer

Question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?

Pre-filled needed-action labels to verify:
- primary_search_needed: 0.0
- contradiction_search_needed: 0.0
- trace_source_needed: 1.0

Auto scorer:
- action_gate_pass: 1.0
- missing_primary_action: 0.0
- missing_contradiction_action: 0.0
- missing_trace_source_action: 0.0

Model actions:
- `trace_source` target=`doc_007` rationale=Trace the origin of the claim in doc_007 to verify if it relies on primary records or is circular.
- `search_primary` target=`Novalis Robotics Project LumenShield 2024 records` rationale=Search for direct primary evidence such as official project documents, contracts, or internal records from Novalis Robotics.

Gold context for auditor:
- gold_verdict: insufficient
- primary_doc_ids: (none)
- contradiction_doc_ids: (none)
- contaminant_doc_ids: doc_007, doc_004, doc_008, doc_001, doc_002
- generated_doc_ids: doc_007, doc_004
- stale_doc_ids: (none)

Documents:
- `doc_007` audit_role=`generated_lore` source_type=`wiki_style_summary` title=Authoritative-looking summary claiming Project LumenShield ran in 2024
  Excerpt: Authoritative-looking summary Project lumenshield was a 2024 field-hardening initiative. This source repeats the wording of the question: Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024? It presents the result as settled and cites secondary summaries rather than raw records.
- `doc_004` audit_role=`generated_lore` source_type=`press_release` title=Secondary coverage 1: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_008` audit_role=`contaminant` source_type=`executive_memo` title=Secondary coverage 2: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_001` audit_role=`contaminant` source_type=`industry_digest` title=Secondary coverage 3: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_002` audit_role=`contaminant` source_type=`supplier_whitepaper` title=Secondary coverage 4: Project LumenShield ran in 2024
  Excerpt: Secondary coverage This item repeats that Project LumenShield ran in 2024. It cites source_ref and another summary using the same claim phrasing. The channel looks independent, but the claim text is copied from the same upstream story.
- `doc_005` audit_role=`background` source_type=`release_note` title=Reference note 7
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_006` audit_role=`background` source_type=`quality_digest` title=Reference note 8
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.
- `doc_003` audit_role=`background` source_type=`customer_note` title=Reference note 9
  Excerpt: Reference note This note mentions Novalis Robotics, suppliers, customers, and the same operating period. It is orientation material and does not settle the target claim.

Labels to enter in CSV:
- semantically_useful_action:
- machine_executable_action:
- exact_target_present:
- required_action_type_present:
- contradiction_search_needed:
- primary_search_needed:
- trace_source_needed:
- scorer_too_strict:
- auditor_notes:
