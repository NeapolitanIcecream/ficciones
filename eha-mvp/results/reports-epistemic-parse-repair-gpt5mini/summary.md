# EHA Parse Repair Audit: openai/gpt-5-mini

This report is separate from the main Epistemic Resilience Table. It reruns only original parse-failed rows, preserves raw prompt/response artifacts, and does not merge repaired metrics into the main table.

## Repair Outcomes

- Attempted original parse-failed rows: 124.
- Direct rerun parse successes: 0.
- JSON repair retries attempted: 124.
- JSON repair retry successes: 0.
- Final repaired parse successes: 0.
- Failure mode: every direct rerun and repair retry failed before generation with an upstream `403` provider Terms of Service error. Separate tiny smoke calls to `openai/gpt-5-mini`, `openai/gpt-5.4-mini`, `~openai/gpt-mini-latest`, `openai/gpt-5-nano`, `openai/gpt-5.4-nano`, `openai/gpt-4.1-mini`, and `openai/gpt-4o-mini` showed the same OpenAI-provider block or missing unprefixed model routes. Therefore this run validates the repair pipeline and artifact preservation, but it does not produce repaired model metrics.

## Original vs Repaired

| scope | value | subvalue | n | repair_attempted_count | original_parse_success | repaired_parse_success | original_epistemic_escape | repaired_epistemic_escape | original_belief_correctness | repaired_belief_correctness | original_evidence_cleanliness | repaired_evidence_cleanliness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | all | all | 200 | 124 | 0.380 | 0.380 | 0.395 | 0.395 | 0.540 | 0.540 | 0.965 | 0.965 |
| family | active_verification | all | 40 | 27 | 0.325 | 0.325 | 0.150 | 0.150 | 0.450 | 0.450 | 0.950 | 0.950 |
| family | evidence_selection | all | 80 | 50 | 0.375 | 0.375 | 0.350 | 0.350 | 0.550 | 0.550 | 0.950 | 0.950 |
| family | packet_judgment | all | 80 | 47 | 0.412 | 0.412 | 0.562 | 0.562 | 0.575 | 0.575 | 0.988 | 0.988 |
| prompt_condition | epistemic_hygiene_instruction | all | 100 | 66 | 0.340 | 0.340 | 0.360 | 0.360 | 0.490 | 0.490 | 0.990 | 0.990 |
| prompt_condition | standard_answer | all | 100 | 58 | 0.420 | 0.420 | 0.430 | 0.430 | 0.590 | 0.590 | 0.940 | 0.940 |

## Cost Report

```json
{
  "aborted": false,
  "record_cost_usd": 0.0,
  "spent_usd": 0.0,
  "soft_cap_usd": 5.0,
  "hard_cap_usd": 15.0,
  "abort_cap_usd": 25.0
}
```
