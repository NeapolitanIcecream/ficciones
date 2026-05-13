# Failure Cases

## Correct verdict but contaminated citation

- Task: `novalis_007`
- Model / strategy: `openai/gpt-5-mini` / `source_independence_prompt`
- Episode type: `false_consensus`
- Gold verdict: `refuted`
- Predicted verdict: `refuted`
- Confidence: `0.850`
- Supporting evidence: `novalis_007_pollutant_root,novalis_007_repost_00,novalis_007_repost_01`
- Rejected evidence: `novalis_007_audit,novalis_007_filing`

## Wrong and high confidence

- Task: `novalis_002`
- Model / strategy: `openai/gpt-5-mini` / `evidence_graph_prompt`
- Episode type: `citation_laundering`
- Gold verdict: `refuted`
- Predicted verdict: `supported`
- Confidence: `0.800`
- Supporting evidence: `novalis_002_audit,novalis_002_filing`
- Rejected evidence: `novalis_002_context_00,novalis_002_context_01,novalis_002_context_02,novalis_002_background_00,novalis_002_background_01,novalis_002_background_02`

## Same-upstream repetition treated as evidence

_No matching case in this run._

## Stale document confusion

_No matching case in this run._

## Correct generated-lore rejection

_No matching case in this run._
