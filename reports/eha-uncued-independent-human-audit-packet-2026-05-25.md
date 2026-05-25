# EHA-Uncued Independent Human Audit Packet Draft

Date: 2026-05-25

## Instructions To Annotators

You will see a task question, a packet of model-visible documents, one model output, and scorer-only gold information. Do not use model identity when judging the row. Judge whether the output satisfies the evidence contract, not only whether the final verdict is correct.

## Label Schema

| field | labels |
| --- | --- |
| semantic_verdict | correct / incorrect / unclear |
| support_hygiene | clean / polluted / empty_but_needed / unclear |
| polluted_evidence_rejection | adequate / inadequate / not_applicable |
| uncertainty_discipline | disciplined / undisciplined / unclear |
| action_executable | executable / vague / wrong_target / not_applicable |
| exact_target | yes / no / not_applicable |
| scorer_judgment | acceptable / too_strict / too_lenient / unclear |

## Minimum Packet Fields

Each row packet should include:

- `task_id`, `base_task_id`, family, condition, view;
- task question;
- abbreviated visible document packet;
- scorer-only hidden roles and gold verdict;
- model output fields: verdict, support, rejected evidence, selected docs, actions, answer;
- automatic scorer components and operational escape;
- blank annotator labels and rationale fields.

## Boundary

This packet is not a completed audit. It is ready to be converted into a CSV or annotation form once annotators and sampling seed are chosen.

