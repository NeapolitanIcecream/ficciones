# Failure Cases

## Correct verdict but contaminated citation

- Task: `novalis_008`
- Model / strategy: `openai/gpt-4o-mini` / `citation_prompt`
- Episode type: `halupedia_trap`
- Gold verdict: `insufficient`
- Predicted verdict: `insufficient`
- Confidence: `0.700`
- Supporting evidence: `novalis_008_repost_00,novalis_008_repost_01,novalis_008_repost_02,novalis_008_repost_03,novalis_008_pollutant_root`
- Rejected evidence: `novalis_008_audit`

## Wrong and high confidence

- Task: `novalis_002`
- Model / strategy: `openai/gpt-4o-mini` / `topk_rag`
- Episode type: `citation_laundering`
- Gold verdict: `refuted`
- Predicted verdict: `supported`
- Confidence: `0.950`
- Supporting evidence: `novalis_002_audit,novalis_002_filing`
- Rejected evidence: `-`

## Same-upstream repetition treated as evidence

- Task: `novalis_005`
- Model / strategy: `openai/gpt-4o-mini` / `topk_rag`
- Episode type: `false_consensus`
- Gold verdict: `refuted`
- Predicted verdict: `supported`
- Confidence: `0.900`
- Supporting evidence: `novalis_005_pollutant_root,novalis_005_repost_00,novalis_005_repost_01,novalis_005_repost_02,novalis_005_repost_03,novalis_005_repost_04,novalis_005_repost_05,novalis_005_repost_06`
- Rejected evidence: `-`

## Stale document confusion

_No matching case in this run._

## Correct generated-lore rejection

- Task: `novalis_008`
- Model / strategy: `openai/gpt-4o-mini` / `citation_prompt`
- Episode type: `halupedia_trap`
- Gold verdict: `insufficient`
- Predicted verdict: `insufficient`
- Confidence: `0.700`
- Supporting evidence: `novalis_008_repost_00,novalis_008_repost_01,novalis_008_repost_02,novalis_008_repost_03,novalis_008_pollutant_root`
- Rejected evidence: `novalis_008_audit`
