# Paper Claim Scan Packet

Scope: snippets from current paper sections mentioning reframing-sensitive claims. Line numbers are from the current worktree when this packet was generated.

## Reframing Decision Source

- `reports/eha-uncued-paper-reframing-decision-2026-05-25.md`
- `reports/eha-uncued-core-claim-overnight-results-2026-05-25.md`

## paper/sections/00_abstract.tex

### Lines 1-3

```tex
1: \begin{abstract}
2: LLM agents increasingly reason over evidence environments that contain stale records, repost chains, generated pages, contradictory fragments, and source metadata that can become a shortcut. We introduce \eha{}-Uncued, a role-uncued diagnostic pilot for measuring whether a model reaches the right belief while keeping evidence roles clean and expressing useful verification actions. A previous cued construction exposed a benchmark-design failure: visible labels and document roles could leak the intended answer. That run is quarantined and is not used as evidence here. The new pilot removes direct material-role and conclusion cues from model-visible documents, checks leakage and shortcut baselines before model calls, and packages prompts, outputs, scorer artifacts, and readiness diagnostics. In a 60-task, four-model pilot with two neutral metadata views, all model calls parse successfully, but operational epistemic escape remains well below belief correctness. Latent-task bootstrap intervals are reported to keep model differences descriptive. Generated-lore rows are the clearest failure mode: aggregate belief correctness is 0.938 while operational escape is 0.125 because models often keep polluted generated evidence in support fields. The release is diagnostic and pilot-scale. It is not deployment-ready evidence, a general leaderboard, or a claim that synthetic leakage has been fully eliminated.
3: \end{abstract}
```

## paper/sections/01_intro.tex

### Lines 4-6

```tex
4: 
5: \eha{}-Uncued tests this distinction in a small controlled setting. The pilot asks models to judge claims using synthetic evidence packets that contain clean evidence, conflicting evidence, false consensus, buried primary evidence, or generated lore. The model-visible packet does not label documents as primary, contaminant, generated, or gold-supporting. The scorer then separates belief correctness from evidence hygiene and active-verification behavior.
6: 
```

### Lines 8-10

```tex
8: 
9: The study is intentionally modest. It is a diagnostic pilot over 60 latent tasks, two neutral metadata views, four frontier model labels, and one clarified schema. It should be read as evidence that answer accuracy hides operational failures under controlled pollution, not as a stable ranking of model providers.
10: 
```

### Lines 14-16

```tex
14:     \item pre-model leakage and shortcut-baseline gates showing that simple non-API shortcuts remain below the level needed to explain the strongest model results;
15:     \item a four-model pilot showing large gaps between belief correctness and operational epistemic escape, especially on generated-lore rows;
16:     \item a packaged artifact, verifier, and scorer audit that make the pilot reproducible and explicitly bounded.
```

## paper/sections/07_results.tex

### Lines 4-6

```tex
4: 
5: \Cref{tab:model-metrics-by-view} gives the main model metrics by neutral metadata view. Operational escape is lower than belief correctness for every model and view. The model ordering is descriptive: \code{gpt-5.5} has the highest observed operational escape in both views, followed by \code{gemini-3.1-pro-preview}, while Claude and DeepSeek have lower operational escape despite complete parse success.
6: 
```

### Lines 8-10

```tex
8: 
9: \Cref{tab:model-metrics-with-ci} adds task-level bootstrap intervals. The intervals are wide enough that this pilot should not be read as a fine-grained provider ranking. The visible-minus-hidden paired operational delta is small overall, 0.029 with a 95\% bootstrap interval of [-0.021, 0.079], so the two neutral metadata views are best treated as paired robustness views rather than separate leaderboards.
10: 
```

### Lines 12-14

```tex
12: 
13: \Cref{tab:model-metrics-by-condition} shows that the aggregate difficulty is not uniform. Clean rows are much easier, with 0.719 operational escape. Generated-lore rows have 0.938 belief correctness but only 0.125 operational escape because evidence precision collapses to 0.000 and polluted support remains high.
14: 
```

### Lines 16-18

```tex
16: 
17: \Cref{tab:condition-metrics-with-ci} reports the same condition-level operational rates with latent-task bootstrap intervals. Generated lore remains the clearest stress case: the belief-to-operational gap is 0.812 with a 95\% interval of [0.714, 0.906].
18: 
```

### Lines 18-20

```tex
18: 
19: \input{tables/evidence_hygiene_vs_belief}
20: 
```

### Lines 20-22

```tex
20: 
21: \Cref{tab:hygiene-vs-belief} makes the separation explicit. The largest belief-to-operation gap appears in generated lore. Buried-primary rows also separate: belief correctness is 0.979, while operational escape is 0.490. This supports the core claim that the task is not just asking whether the model can answer the claim. It asks whether the model can keep the evidence contract clean enough for an agent pipeline.
22: 
```

### Lines 24-26

```tex
24: 
25: \Cref{tab:active-verification-action-exactness} summarizes active-verification action behavior. Exact target rate is 1.000 in this pilot, so the remaining variation comes from required action recall, the action score, and whether the active-verification row also satisfies belief and support hygiene. This result should be read cautiously because the active-verification slice has only 96 rows.
26: 
```

### Lines 26-28

```tex
26: 
27: \input{tables/robustness_paired_deltas}
28: 
```

### Lines 28-29

```tex
28: 
29: \Cref{tab:robustness-paired-deltas} reports a paired Phase 1.3 robustness mini-suite over 20 frozen source tasks, two frontier models, and five presentation variants. All 200 calls parsed, and all 40 task-model groups contained the \code{baseline_original} row plus every perturbation row. Operational deltas were non-negative for evidence-order randomization, source-type masking, prompt paraphrase, and citation masking. The generated-lore belief/operation gap also persisted: the baseline gap was 1.000, source-type masking and citation masking remained at 1.000, and order randomization and prompt paraphrase remained at 0.900. Citation masking should be read as a stress test because visible dependency structure can be task-relevant evidence rather than neutral presentation metadata.
```

## paper/sections/08_schema_interface.tex

### Lines 4-6

```tex
4: 
5: The interface finding that remains valid in this pilot is narrower. Structured fields matter because evidence and action fields can fail while the final verdict succeeds. In generated-lore rows, models often know the right verdict yet fail operational escape because polluted evidence remains in support fields. In active-verification rows, the action schema makes executable next steps measurable instead of leaving them as prose.
6: 
```

## paper/sections/10_limitations.tex

### Lines 2-4

```tex
2: 
3: The pilot is small: 60 latent tasks, two neutral metadata views, four model labels, and one prompt/schema condition. Bootstrap intervals are reported at the latent-task level, but they do not make the pilot statistically powered for fine-grained provider ranking. Reported model differences should be treated as descriptive.
4: 
```

### Lines 8-10

```tex
8: 
9: The Phase 1.1 schema-ablation slice is small: 16 source tasks, one visible metadata view, two main models, and a local Codex-assisted scorer audit. It supports only an interface-sensitivity claim about machine-readable evidence-role allocation. It should not be treated as a new benchmark result, a provider ranking, or evidence that schema wording explains every Phase 1 failure.
10: 
```

### Lines 10-12

```tex
10: 
11: The Phase 1.3 robustness mini-suite is also narrow: 20 source tasks, one visible metadata view, two models, and controlled presentation perturbations. It supports only named mini-suite robustness or sensitivity claims. In particular, citation masking can remove task-relevant dependency information, so sensitivity under that perturbation should not be interpreted as a benchmark failure by itself. The flip review is local and scorer-assisted rather than an independent human audit.
12: 
```

### Lines 12-13

```tex
12: 
13: Finally, the artifact includes hidden labels and gold data for reproducibility, but those files are not model-visible. Any downstream reuse must preserve that separation.
```

## paper/sections/13_conclusion.tex

### Lines 2-4

```tex
2: 
3: \eha{}-Uncued shows that, in a controlled role-uncued pilot, answer accuracy can substantially overstate agent readiness in polluted evidence environments. The clearest evidence is generated lore: models usually reach the right belief, yet operational escape remains low because evidence roles are not clean. Active-verification rows show a second interface requirement: a useful agent must express the next verification action in a machine-checkable form.
4: 
```

### Lines 4-5

```tex
4: 
5: The release should be read as a validity-first pilot. It fixes the direct cueing failure exposed by the older run, packages the uncued artifacts, and records leakage, baseline, model-run, scorer-audit, readiness, and small schema-ablation diagnostics. The next step is not leaderboard expansion alone; it is a larger role-uncued task set with independent human audit and schema/interface choices treated as experimental factors rather than neutral logging details.
```

