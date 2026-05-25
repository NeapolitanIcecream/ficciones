# EHA-Uncued Bootstrap Uncertainty

Date: 2026-05-25

## Method

- Resample unit: `latent_task`.
- Latent tasks: `60`.
- Scored rows: `480`.
- Bootstrap iterations: `10000`.
- Seed: `20260525`.
- Each draw keeps the hidden and visible metadata views together inside the sampled latent task.

## Model Metrics

| model | n | operational_epistemic_escape | belief_correctness | evidence_precision |
| --- | --- | --- | --- | --- |
| claude-opus-4-7 | 120 | 0.317 [0.217, 0.425] | 0.933 [0.875, 0.983] | 0.481 [0.362, 0.604] |
| deepseek-v4-pro | 120 | 0.233 [0.142, 0.333] | 0.658 [0.558, 0.758] | 0.441 [0.323, 0.562] |
| gemini-3.1-pro-preview | 120 | 0.433 [0.325, 0.550] | 0.917 [0.867, 0.958] | 0.843 [0.757, 0.918] |
| gpt-5.5 | 120 | 0.525 [0.408, 0.642] | 0.992 [0.975, 1.000] | 0.754 [0.650, 0.850] |

## Condition-Level Operational Escape

| condition | n | operational_epistemic_escape |
| --- | --- | --- |
| clean | 96 | 0.719 [0.536, 0.886] |
| conflicting_evidence | 96 | 0.250 [0.083, 0.433] |
| false_consensus | 96 | 0.302 [0.135, 0.486] |
| buried_primary | 96 | 0.490 [0.225, 0.750] |
| generated_lore | 96 | 0.125 [0.056, 0.200] |

## Generated-Lore Belief-To-Operational Gap

- Gap: `0.812 [0.714, 0.906]`.

## Visible-Hidden Paired Deltas

| model | n | visible_minus_hidden_operational_epistemic_escape |
| --- | --- | --- |
| overall | 240 | 0.029 [-0.021, 0.079] |
| claude-opus-4-7 | 60 | 0.033 [-0.050, 0.133] |
| deepseek-v4-pro | 60 | 0.033 [-0.067, 0.117] |
| gemini-3.1-pro-preview | 60 | 0.033 [-0.067, 0.133] |
| gpt-5.5 | 60 | 0.017 [-0.083, 0.117] |

## Interpretation Boundary

The intervals are task-level pilot uncertainty summaries, not population estimates for a full benchmark. Model ordering should remain descriptive unless a later, larger design supports stronger comparisons.
