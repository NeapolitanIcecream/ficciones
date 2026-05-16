# EHA Step 2 Phase 2S Support-Role Guard

Date: 2026-05-16

- Status: `ready`
- Guard ready: `true`
- Minimum allow rate: `0.75`

This is a no-API deterministic validation pass over already scored Phase 2S calibration rows. It validates whether supporting-evidence rows can be accepted by a downstream consumer, and blocks rows with contaminated, unknown, extraneous, non-empty insufficient, or non-verdict-direct support.

## Run Summary

| run | n | ready | allow | block | valid | clean | direct | invalid_accepted | valid_blocked |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini | 35 | true | 0.886 | 0.114 | 0.886 | 1.000 | 0.886 | 0.000 | 0.000 |
| reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini | 35 | true | 0.886 | 0.114 | 0.886 | 0.971 | 0.886 | 0.000 | 0.000 |
| reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini | 35 | true | 0.857 | 0.143 | 0.857 | 0.914 | 0.857 | 0.000 | 0.000 |
| reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini | 35 | true | 0.857 | 0.143 | 0.857 | 1.000 | 0.857 | 0.000 | 0.000 |

## Block Reasons

| run | contaminated | unknown | extraneous | nonempty_insufficient | not_direct | missing_fields |
| --- | --- | --- | --- | --- | --- | --- |
| reports-phase2s-v8-structural-schema-calibration-slice-gpt4omini | 0 | 0 | 0 | 1 | 4 |  |
| reports-phase2s-v9-structural-recall-calibration-slice-gpt4omini | 1 | 0 | 0 | 1 | 4 |  |
| reports-phase2s-v10-structural-contract-calibration-slice-gpt4omini | 3 | 0 | 0 | 3 | 5 |  |
| reports-phase2s-v11-role-disciplined-calibration-slice-gpt4omini | 0 | 0 | 0 | 0 | 5 |  |

## Non-Claims

- not new model evidence
- not a repair for wrong claim verdicts
- not a repair for missing critical-risk labels
- not a substitute for human audit or surface-cue design review
