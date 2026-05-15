# EHA Paper Mechanism Case Section

Date: 2026-05-15

Status: paper-writing draft and appendix material, grounded in local EHA artifacts. This section does not replace the frozen frontier main run; it interprets one mechanism exposed by that run.

## Draft Claim

EHA reveals failures below answer accuracy: models may reach the correct verdict while misassigning polluted documents to machine-readable support fields, creating concrete risks for downstream agent systems.

In polluted evidence environments, the relevant question is not only whether a model says the right thing. A tool-using or retrieval-augmented agent may consume structured fields such as `supporting_evidence`, `rejected_evidence`, and `actions` without reading the surrounding prose. EHA therefore treats evidence-role discipline as part of the output contract. If a model verbally rejects a generated-lore source but still places it in a machine-readable support field, the model has not fully escaped the polluted evidence environment.

## Main Figure: Layer Decomposition

Use the generated-lore slice as a layer decomposition figure rather than a single escape score. The figure should plot the current-schema rows from `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/figure_generated_lore_role_decomposition.csv`. A first SVG draft is available at `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/figure_generated_lore_role_decomposition.svg`.

| Model | Belief correctness | Rejected pollutant rate | Polluted supporting rate | Full escape |
| --- | ---: | ---: | ---: | ---: |
| `claude-opus-4-7` | 1.000 | 1.000 | 0.000 | 0.600 |
| `gemini-3.1-pro-preview` | 1.000 | 1.000 | 0.000 | 0.425 |
| `gpt-5.4` | 1.000 | 1.000 | 0.900 | 0.100 |

This layout makes the mechanism visible. `gpt-5.4` is not failing to infer that generated-lore packets are insufficient; it is failing the machine-readable evidence-role layer. In 40/40 generated-lore records it gave the correct insufficient verdict and placed pollutants in `rejected_evidence`, yet 36/40 records also placed polluted documents in `supporting_evidence`.

The clarified-schema rows in the same CSV should be used as a validity-analysis panel, not as a replacement score. Under clarified fields, `gpt-5.4` has polluted-supporting rate 0.000 and role escape 1.000 on the same generated-lore slice. This supports the interpretation that the current schema exposes an agent-interface risk tied to field semantics and role assignment.

## Mechanism Case 1: Generated Lore As Evidence-Role Failure

The paper should not write that `gpt-5.4` cannot detect generated lore. The confirmed cases show the opposite at the belief layer: the model gives an `insufficient` verdict and explains why the evidence is unreliable. The failure is that the same polluted documents appear in a support field that a downstream system could treat as clean support.

### Case A: `ert_032`, Project LumenShield

Question: "Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?"

Gold verdict: `insufficient`.

Current-schema `gpt-5.4` output gives the correct `insufficient` verdict. The answer says the apparent support is a wiki-style summary and downstream reposts, and that no primary document, raw record, or independent contemporaneous evidence is provided. The field assignment is the failure:

| Field | Evidence IDs |
| --- | --- |
| `supporting_evidence` | `eham_120_pollutant_root`, `eham_120_repost_00`, `eham_120_context_06` |
| `rejected_evidence` | `eham_120_repost_00`, `eham_120_repost_01`, `eham_120_repost_02`, `eham_120_repost_03` |
| Polluted support | `eham_120_pollutant_root`, `eham_120_repost_00` |
| Dual-role pollutant | `eham_120_repost_00` |

The clarified-schema rerun keeps `clean_supporting_evidence` empty. It moves `eham_120_pollutant_root` and reposts into `rejected_or_contaminated_evidence`, with `eham_120_pollutant_root` also listed as diagnostic evidence for the polluted environment.

### Case B: `ert_033`, MiraCert Certification Deal

Question: "Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal?"

Gold verdict: `insufficient`.

Current-schema `gpt-5.4` output again gives `insufficient` and says the packet only shows a repeated claim propagated across secondary summaries, with no primary document, official announcement, certification registry entry, or direct statement. The field assignment repeats the mechanism:

| Field | Evidence IDs |
| --- | --- |
| `supporting_evidence` | `eham_121_pollutant_root`, `eham_121_repost_00`, `eham_121_context_06` |
| `rejected_evidence` | `eham_121_repost_00`, `eham_121_repost_01`, `eham_121_repost_02`, `eham_121_repost_03` |
| Polluted support | `eham_121_pollutant_root`, `eham_121_repost_00` |
| Dual-role pollutant | `eham_121_repost_00` |

The clarified-schema output leaves `clean_supporting_evidence` empty and moves the polluted root and reposts to `rejected_or_contaminated_evidence` or `diagnostic_evidence`.

### Case C: `ert_096`, Active-Verification Generated Lore

Question: "Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?"

Gold verdict: `insufficient`.

This active-verification version shows the same evidence-role failure. The current answer says the apparent support is a single authoritative-looking summary and downstream reposts, with no primary documents, raw records, or independent corroboration. Yet `supporting_evidence` contains `eham_120_pollutant_root` and `eham_120_repost_00`, while `rejected_evidence` also contains the repost chain. The clarified-schema output again keeps `clean_supporting_evidence` empty and assigns the polluted root and reposts to rejected or diagnostic roles.

These three cases make the reader-facing mechanism concrete: the model knows the evidence is unreliable, but the structured fields make the unreliable evidence available to downstream systems as support.

## Mechanism Case 2: Active Verification As Action-Expression Failure

Pair the generated-lore evidence-role problem with an active-verification action-expression problem.

Case: `gpt-5.4`, `ert_082`, `standard_answer`.

Question: "Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?"

Gold verdict: `supported`.

The answer layer is correct. The current output gives `supported` and lists clean primary support: `eham_002_primary_a` and `eham_002_primary_b`. The failure is in the next-action interface:

| Field | Value |
| --- | --- |
| `belief_correctness` | 1.000 |
| `evidence_cleanliness` | 1.000 |
| `verification_action_score` | 0.000 |
| First action target | `eham_002_primary_a, eham_002_primary_b, eham_002_pollutant_root` |
| Second action target | `eham_002_repost_00, eham_002_repost_01 -> eham_002_pollutant_root` |

These bundled target strings are understandable to a human, but they are not exact machine-checkable document IDs or clear `search_primary` actions. The failure is not ordinary answer accuracy. It is whether the model expresses the next action in a form an agent system can execute, audit, and recover from.

Together, the two mechanism cases support the central EHA argument:

> EHA is not just measuring final answers. It is measuring whether an agent-facing model can preserve epistemic discipline across verdicts, evidence roles, and executable verification actions.

## Validity Analysis Wording

Use this wording:

> The current schema exposes an agent-interface risk: polluted material can be verbally rejected yet still enter a support field that downstream systems may consume. The clarified-schema mini-rerun shows that this behavior is closely tied to field semantics and evidence-role assignment. It should be interpreted as validity analysis, not as a retroactive correction of the frozen main-run scores.

Avoid:

- "GPT-5.4 cannot detect generated lore."
- "The clarified schema fixes the main score."
- "The main result was wrong."

## Artifact Index

| Artifact | Role |
| --- | --- |
| `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/figure_generated_lore_role_decomposition.csv` | Main layer-decomposition figure data |
| `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/figure_generated_lore_role_decomposition.svg` | First visual draft of the layer-decomposition figure |
| `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/paper_mechanism_case_studies.jsonl` | Four paper case rows: three generated-lore evidence-role cases and one active-verification action case |
| `eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/gpt54_generated_lore_audit_pack.jsonl` | Raw current-schema audit evidence for representative GPT-5.4 generated-lore cases |
| `eha-mvp/results/reports-eha-generated-lore-role-audit-2026-05-15/clarified_predictions.jsonl` | Raw clarified-schema rerun outputs |
| `eha-mvp/results/reports-eha-frontier-main/predictions.jsonl` | Raw frontier main run predictions, including active-verification case `ert_082` |
| `eha-mvp/results/reports-eha-frontier-main/frontier_main_scored_predictions.csv` | Scored frontier main rows, including `ert_082` verification-action score |
