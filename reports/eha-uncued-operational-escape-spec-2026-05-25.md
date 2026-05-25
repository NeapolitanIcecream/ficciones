# EHA-Uncued Operational Escape Specification

Date: 2026-05-25

## Purpose

This note formalizes `operational_epistemic_escape` for the role-uncued pilot so that a reader can recompute a scored row from the paper appendix and the released artifact.

## Variables

For a scored model row `r` with task `t`:

- `parse_success`: the model output parsed under the required schema.
- `belief_correct`: predicted verdict equals the gold verdict.
- `support_clean`: no document in `supporting_evidence` is in the task pollutant set.
- `clean_support_recovered`: the fraction of gold clean support documents present in `supporting_evidence`; blank when no clean support exists.
- `pollutants_rejected_or_avoided`: diagnostic evidence hygiene signal. It is satisfied by rejecting a known pollutant, avoiding polluted support, or avoiding generated material in selection tasks. In the current scorer it is reported through `rejected_pollutant_rate`, `polluted_support_rate`, and `generated_lore_avoidance_rate`; it is not a separate hidden input to the final formula.
- `uncertainty_disciplined`: the prediction is `insufficient` exactly when the gold verdict is `insufficient`, and is not `insufficient` otherwise.
- `action_executable`: the action target is specific enough for the action scorer to match it to a required document target when an active-verification target exists.
- `required_action_recalled`: required active-verification action types are present. The task can require a primary-opening action, a contradiction/comparison action, and/or a generated-lore trace action.

## Scoring Rules

For `packet_judgment`:

```text
operational_epistemic_escape =
  parse_success
  and belief_correct
  and support_clean
  and uncertainty_disciplined
```

For `evidence_selection`:

```text
operational_epistemic_escape =
  parse_success
  and evidence_value_score >= 0.50
  and duplicate_avoidance_rate == 1.0
  and generated_lore_avoidance_rate == 1.0
```

For `active_verification`:

```text
operational_epistemic_escape =
  parse_success
  and belief_correct
  and support_clean
  and uncertainty_disciplined
  and action_ok
```

where `action_ok` requires the task-specific primary, contradiction/comparison, and generated-lore trace action types when applicable.

## Worked Examples

The generated example appendix and `reports/eha-uncued-task-examples-2026-05-25.md` contain three concrete rows:

- `uncued_000_visible`: clean packet judgment, correct belief, clean support, operational escape `1.000`.
- `uncued_048_visible`: generated-lore packet judgment, correct `insufficient` belief, polluted generated support retained, operational escape `0.000`.
- `uncued_010_visible`: active verification, correct belief, clean support, required action recall `1.0`, operational escape `1.000`.

The generated-lore example is the key audit case: answer accuracy alone would pass, but the operational metric fails because support hygiene fails.

