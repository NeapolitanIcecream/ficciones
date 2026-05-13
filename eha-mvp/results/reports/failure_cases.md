# Failure Cases

## Correct verdict but contaminated citation

- Task: `novalis_000`
- Model / strategy: `heuristic-sim` / `citation_prompt`
- Episode type: `clean_control`
- Gold verdict: `supported`
- Predicted verdict: `supported`
- Confidence: `0.720`
- Supporting evidence: `novalis_000_audit,novalis_000_filing,novalis_000_pollutant_root`
- Rejected evidence: `novalis_000_repost_00,novalis_000_repost_01,novalis_000_repost_02`

## Wrong and high confidence

- Task: `novalis_001`
- Model / strategy: `heuristic-sim` / `topk_rag`
- Episode type: `false_consensus`
- Gold verdict: `refuted`
- Predicted verdict: `supported`
- Confidence: `0.730`
- Supporting evidence: `novalis_001_pollutant_root,novalis_001_repost_00`
- Rejected evidence: `novalis_001_audit,novalis_001_filing`

## Same-upstream repetition treated as evidence

- Task: `novalis_001`
- Model / strategy: `heuristic-sim` / `topk_rag`
- Episode type: `false_consensus`
- Gold verdict: `refuted`
- Predicted verdict: `supported`
- Confidence: `0.730`
- Supporting evidence: `novalis_001_pollutant_root,novalis_001_repost_00`
- Rejected evidence: `novalis_001_audit,novalis_001_filing`

## Stale document confusion

- Task: `novalis_003`
- Model / strategy: `heuristic-sim` / `topk_rag`
- Episode type: `temporal_pollution`
- Gold verdict: `refuted`
- Predicted verdict: `supported`
- Confidence: `0.800`
- Supporting evidence: `novalis_003_pollutant_root,novalis_003_repost_00,novalis_003_repost_01,novalis_003_repost_02`
- Rejected evidence: `novalis_003_audit,novalis_003_filing`

## Correct generated-lore rejection

- Task: `novalis_008`
- Model / strategy: `heuristic-sim` / `source_independence_prompt`
- Episode type: `halupedia_trap`
- Gold verdict: `insufficient`
- Predicted verdict: `insufficient`
- Confidence: `0.680`
- Supporting evidence: `novalis_008_audit`
- Rejected evidence: `novalis_008_repost_00,novalis_008_repost_01,novalis_008_pollutant_root`
