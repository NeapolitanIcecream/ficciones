# EHA First Full Paper Draft Checklist

Date: 2026-05-15

Source plan: `/Users/chenmohan/Downloads/ficciones-plan-0515-0.md`

Target draft: `epistemic-hygiene-arena-preprint.md`

## Prompt-To-Artifact Mapping

| Requirement | Evidence in draft/artifacts | Status |
| --- | --- | --- |
| Write the first full paper draft for EHA. | `epistemic-hygiene-arena-preprint.md` replaced the older planning-estimate draft with a complete paper draft grounded in current EHA results. | Done |
| Do not frame as a model leaderboard. | Abstract and Introduction say this is not a leaderboard; Main Results labels the table as capability decomposition, not ranking. | Done |
| Do not frame as a RAG retrieval hygiene paper. | Introduction states EHA is not a narrow RAG retrieval-hygiene test; Related Work Placeholder repeats the distinction. | Done |
| Frame as benchmark and analysis of LLM epistemic resilience in polluted evidence environments. | Title, Abstract, Introduction, Discussion, and Conclusion use this framing. | Done |
| Central thesis: factual reliability in agent settings should not be evaluated only by final-answer correctness. | Abstract and Introduction explicitly state final-answer accuracy is insufficient; Discussion develops the claim. | Done |
| Abstract defines polluted evidence environments. | Abstract, paragraph 1. | Done |
| Abstract states EHA evaluates epistemic escape, not just answer accuracy. | Abstract, paragraph 1. | Done |
| Abstract mentions 100 tasks, 5 frontier models, 2 prompt conditions. | Abstract, paragraph 2. | Done |
| Abstract gives main finding on evidence cleanliness and verification behavior. | Abstract, paragraph 2. | Done |
| Abstract highlights generated-lore evidence-role failure and active-verification interface failure. | Abstract, paragraph 2. | Done |
| Introduction starts with agents relying on search results/generated pages/knowledge bases/etc. | Section 1 opening paragraph. | Done |
| Introduction explains why answer accuracy alone is insufficient. | Section 1, paragraphs 3-4. | Done |
| Introduction introduces epistemic escape. | Section 1, paragraph 4. | Done |
| Introduction gives concrete motivating generated-lore/supporting_evidence example. | Section 1, paragraph 5. | Done |
| Benchmark design explains three task families. | Section 2.1 table. | Done |
| Benchmark design explains five evidence conditions. | Section 2.2 table. | Done |
| Benchmark design defines metrics. | Section 2.4 table. | Done |
| Benchmark design explains operational vs conditional parse treatment. | Section 2.4 final paragraph. | Done |
| Model cohort lists five required models. | Section 3 table. | Done |
| Model cohort explains preflight and provider-compatible profiles. | Section 3 paragraphs 3-4. | Done |
| Model cohort explains no-cap handling for DeepSeek/Kimi and output-length fairness audit. | Section 3 paragraphs 3-4; values from main results and budget audit. | Done |
| Main results include model decomposition table. | Section 4 table. | Done |
| Main results include family breakdown. | Section 4.1 table. | Done |
| Main results include condition breakdown. | Section 4.2 table. | Done |
| Main results include prompt hygiene result. | Section 4.3 table and interpretation. | Done |
| Mechanism case study 1 uses GPT-5.4 generated lore. | Section 5. | Done |
| Generated-lore case shows low full escape but perfect belief correctness. | Section 5 table. | Done |
| Generated-lore case explains polluted supporting evidence and dual-role pollutant. | Section 5 text and `ert_032` table. | Done |
| Generated-lore case explains clarified-schema mini-rerun. | Section 5.1 table and interpretation. | Done |
| Generated-lore case emphasizes evidence-role failure, not belief failure. | Section 5, especially paragraphs before and after tables. | Done |
| Mechanism case study 2 uses `ert_082` or best available case. | Section 6 uses `gpt-5.4`, `ert_082`, `standard_answer`. | Done |
| Active-verification case explains correct verdict + clean evidence but invalid/non-executable action target. | Section 6 table and target strings. | Done |
| Active-verification case emphasizes agent-interface risk. | Section 6 final paragraphs. | Done |
| Discussion covers failures below answer accuracy. | Section 7. | Done |
| Discussion covers generated lore as provenance/evidence-role problem. | Section 7. | Done |
| Discussion covers structured fields consumed by downstream agents. | Section 7. | Done |
| Discussion covers prompt hygiene not universal. | Section 7. | Done |
| Limitations include synthetic mini-web. | Section 8. | Done |
| Limitations include fixed schema and scoring contract. | Section 8. | Done |
| Limitations include task size 100. | Section 8. | Done |
| Limitations include active-verification scoring needs more human audit. | Section 8. | Done |
| Limitations include clarified schema as validity analysis, not retroactive replacement. | Section 8. | Done |
| Limitations include no direct claim about open-web misinformation performance. | Section 8. | Done |
| Related work placeholder has citation categories and does not invent citations. | Section 9 uses citation categories only and no fabricated bibliography. | Done |
| Conclusion restates auditable beliefs in polluted evidence environments. | Section 10. | Done |

## Evidence Checked

| Artifact | Checked for |
| --- | --- |
| `eha-mvp/results/reports-eha-frontier-main/frontier_main_metrics_by_model.csv` | Model decomposition values in Section 4 |
| `eha-mvp/results/reports-eha-frontier-main/frontier_main_metrics_by_family.csv` | Family breakdown values in Section 4.1 |
| `eha-mvp/results/reports-eha-frontier-main/frontier_main_metrics_by_condition.csv` | Condition breakdown values in Section 4.2 |
| `eha-mvp/results/reports-eha-frontier-main/frontier_main_metrics_by_prompt.csv` | Prompt hygiene values in Section 4.3 |
| `reports/eha-budget-fairness-audit-results-2026-05-14.md` | No-cap handling and output-length fairness statement |
| `eha-mvp/results/reports-eha-paper-mechanism-cases-2026-05-15/prompt_to_artifact_checklist.md` | Generated-lore and active-verification mechanism evidence |
| `reports/eha-paper-mechanism-case-section-2026-05-15.md` | Mechanism wording and validity-analysis framing |

## Verification Commands

```bash
rg -n '^## ' epistemic-hygiene-arena-preprint.md
rg -n 'leaderboard|RAG retrieval-hygiene|100 tasks|five frontier|two prompt|generated-lore|active-verification|validity analysis|open-web misinformation' epistemic-hygiene-arena-preprint.md
git diff --check
```

## Residual Work Outside This Plan

- Add verified citations and bibliography entries.
- Convert tables and the SVG draft into publication-ready figures.
- Decide final venue/style, author metadata, and citation format.
