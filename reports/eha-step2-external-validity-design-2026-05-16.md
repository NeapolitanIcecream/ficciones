# EHA Step 2 External Validity Design

Date: 2026-05-16

This is a no-API design artifact for the Step 2 roadmap. It is not model evidence, not a started external-validity experiment, and not a benchmark expansion.

## Current Boundary

- Status: `design_only`
- API ready: `false`
- Recommended first slice: `semi_real_enterprise_wiki`

## Candidate Slices

### semi-real enterprise wiki

- Slice ID: `semi_real_enterprise_wiki`
- Status: `not_started`
- Minimum pilot tasks: 40
- Reader question: Do EHA failures persist when evidence resembles enterprise knowledge work rather than a compact synthetic mini-web?
- Corpus assets: tickets, emails, release notes, audit logs, wiki pages, slack-like summaries
- Target failures: buried_primary, conflicting_evidence, temporal_drift, active_verification
- Human inputs required: domain-plausibility review, document realism review, privacy/sensitive-data check
- Artifact contract: task JSONL, document JSONL, gold labels, provenance graph, surface-cue balance report, human design-review worksheet
- Risks: too close to private enterprise data, overfitting to operational jargon, harder manual audit burden

### open-web-like synthetic corpus

- Slice ID: `open_web_like_synthetic`
- Status: `not_started`
- Minimum pilot tasks: 40
- Reader question: Do current findings survive an open-web-like ecology with reposting, citation loops, and stale pages?
- Corpus assets: generated encyclopedia pages, scraped-like blogs, SEO reposts, citation loops, date-stale pages
- Target failures: false_consensus, citation_laundering, generated_lore, stale_evidence
- Human inputs required: web-realism review, citation-loop review, surface-cue review
- Artifact contract: task JSONL, document JSONL, gold labels, citation graph, metadata perturbation report, retrieval observability report
- Risks: surface cues may dominate, citation graph may become too template-visible, generated-lore labels may leak through names

### human-written pollutants

- Slice ID: `human_written_pollutants`
- Status: `not_started`
- Minimum pilot tasks: 20
- Reader question: Do failures depend on templated pollutant language, or do they persist when pollutants are human-written?
- Corpus assets: human-written false summaries, human-written overclaims, human-written stale summaries
- Target failures: generated_lore, partial_support, no_primary_source, conflicting_evidence
- Human inputs required: pollutant authoring, labeler separation from generator, style leakage review
- Artifact contract: authoring brief, pollutant provenance log, task JSONL, document JSONL, gold labels, review attestation
- Risks: costly human writing, inconsistent style across pollutants, harder reproducibility unless authoring brief is released

### adaptive generated lore

- Slice ID: `adaptive_generated_lore`
- Status: `not_started`
- Minimum pilot tasks: 30
- Reader question: Do generated-lore failures become stronger when lore is locally coherent and mutually reinforcing?
- Corpus assets: cross-linked synthetic pages, cached summaries, mutually reinforcing lore, local-canon-consistent aliases
- Target failures: generated_lore, false_consensus, citation_laundering, no_primary_source
- Human inputs required: lore consistency review, leakage review, source-chain audit
- Artifact contract: lore graph, task JSONL, document JSONL, gold labels, schema-ablation compatibility note
- Risks: too close to a generated-lore-only benchmark, may repeat Step 1 mechanism rather than broaden external validity, source-chain complexity can obscure scoring

## Go / No-Go Gates Before API

- complete Step 1 independent human audit
- complete 90-pair surface-cue human design review
- keep first external-validity pilot at or below 40 tasks
- produce a design-review worksheet and validation report for the chosen slice
- define target venue and budget before model calls

## Non-Claims

- not model evidence
- not a started external-validity experiment
- not a benchmark expansion
- do not expand to 500-1000 tasks from this design artifact

## Recommended Next Step

Do not generate an external-validity dataset yet. First complete the Step 1 independent human audit and the 90-pair surface-cue human design review. If both gates clear, begin with the semi-real enterprise wiki slice as a 20-40 task design-reviewed pilot.
