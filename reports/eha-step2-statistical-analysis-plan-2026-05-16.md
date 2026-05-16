# EHA Step 2 Statistical Analysis Plan

Date: 2026-05-16

## Purpose

This plan converts the Step 2 roadmap's statistical requirements into a pre-registered analysis contract for a future scaled EHA run. It is not an analysis of current Step 1 results and should not be used to turn the 100-task diagnostic release into a provider ranking.

Executable scaffold:

- Utility module: `eha-mvp/eha/step2_statistics.py`
- Tests: `eha-mvp/tests/test_step2_statistics.py`
- Current scope: task-cluster bootstrap summaries and paired permutation tests. Mixed-effects modeling remains a future analysis step once scaled scored rows exist.

## Unit Of Analysis

The primary unit is the task, not the model call. Rows from the same task share evidence, gold labels, and generator choices, so uncertainty estimates should preserve task-level dependence.

Primary grouping keys:

| Key | Role |
|---|---|
| `task_id` | resampling cluster for task-level uncertainty |
| `model` | system comparison factor |
| `prompt_condition` / `schema_variant` | prompt/schema intervention factor |
| `task_family` / `episode_type` | mechanism family factor |
| `evidence_condition` | pollution environment factor |
| `stress_axis` | Step 2 surface-cue manipulation factor |
| `pair_id` | paired-condition block for surface-cue and schema tests |

## Primary Outcomes

Step 2 should not optimize a single leaderboard metric. Report each outcome separately and treat operational escape as a conjunctive summary.

| Outcome | Type | Main contrast |
|---|---|---|
| `operational_escape` | binary | overall agent-safe success |
| `belief_correctness` / `claim_accuracy` | binary | final answer correctness |
| `evidence_cleanliness` / contaminated support | binary or rate | evidence-role safety |
| `support_role_valid` | binary | clean-only and verdict-direct support |
| `uncertainty_discipline` | binary | abstention/confidence calibration |
| `required_action_recall` | binary or rate | active-verification action coverage |
| `machine_executable_action` | human-audit binary | interface executability |

Secondary outcomes include parse success, schema success, rejected-pollutant rate, clean-support recall, dual-role rate, direct critical-risk macro-F1, and observation macro-F1.

## Confidence Intervals

Use task-cluster bootstrap intervals for primary tables:

1. Resample `task_id` clusters with replacement.
2. Include all model/prompt/schema rows attached to each sampled task.
3. Recompute aggregate metrics within each bootstrap sample.
4. Use 2.5th and 97.5th percentiles for 95 percent intervals.
5. Use at least 2,000 bootstrap samples for final tables; 500 is acceptable only for development smoke tests.

For paired surface-cue or schema contrasts, resample `pair_id` clusters rather than individual rows.

Report:

```text
mean [95% CI low, 95% CI high]
```

Do not sort models by insignificant third-decimal differences.

The scaffold function is `summarize_task_cluster_ci(...)`; it reports row count, task-cluster count, mean, and percentile bootstrap interval for each requested metric.

## Paired Tests

Use paired permutation tests only for pre-specified contrasts where the same task or pair is evaluated under both conditions.

Examples:

| Contrast | Pairing key | Null hypothesis |
|---|---|---|
| hygiene prompt vs standard prompt | `task_id`, `model` | prompt has no effect on the metric |
| clarified schema vs current schema | `task_id`, `model` | schema has no effect on evidence-role failures |
| visible vs hidden source type | `pair_id`, `model` | source-type visibility has no effect |
| truthful vs shuffled metadata | `pair_id`, `model` | metadata perturbation has no effect |
| model A vs model B | `task_id`, condition | models have equal paired success probability |

For binary paired outcomes, report the paired difference in means and a two-sided permutation p-value. Treat p-values as diagnostic evidence, not as standalone claims of model superiority.

The scaffold function is `paired_permutation_test(...)`; it averages duplicate rows within each pair-condition cell, computes treatment-minus-baseline differences, and uses exact sign-flip enumeration for small paired samples.

## Mixed-Effects Model

Use mixed-effects modeling as a robustness analysis, not as the only headline result.

Recommended logistic model for binary outcomes:

```text
outcome ~ model + schema_variant + prompt_condition + task_family
        + evidence_condition + stress_axis
        + model:stress_axis
        + (1 | task_id)
        + (1 | generator_seed)
```

If the final dataset has enough paired surface-cue rows, add:

```text
+ (1 | pair_id)
```

Use regularized or Bayesian estimation if complete separation occurs. Report estimated effects with uncertainty intervals and convergence diagnostics; do not hide failed fits.

## Multiple Comparisons

Pre-specify a small set of headline contrasts before running API calls:

1. Best current schema vs clarified support-role schema on evidence-role failures.
2. Standard prompt vs hygiene prompt on operational escape.
3. Visible vs hidden source type on operational escape.
4. Truthful vs shuffled metadata on claim accuracy and support-role validity.
5. Plain vs authority-spoof pollutant on contaminated support.

All other contrasts are exploratory. For exploratory families, report false-discovery-adjusted q-values or clearly label the table as descriptive.

## Minimum Reporting Tables

| Table | Required columns |
|---|---|
| Main model table | model, n tasks, operational escape mean and 95% CI, belief, support-role valid, action recall |
| Family breakdown | model, task family, n tasks, operational escape and 95% CI |
| Schema ablation | schema variant, model, evidence-role failures, support-role valid, paired difference |
| Surface-cue stress | stress axis, condition, model, paired difference, 95% CI |
| Human baseline | human task type, n rows, human success rate, model comparison, agreement if available |

## Go / No-Go For Analysis Claims

Do not make a scalable benchmark claim unless:

- each headline task family has enough tasks for task-level intervals;
- surface-cue pairs pass balance and leakage checks before API calls;
- at least one independent human/manual audit is complete for active-verification or human baseline claims;
- the analysis code can recompute every reported table from raw scored rows;
- prompt/schema/model comparisons use paired designs whenever possible.

If these conditions are not met, frame Step 2 results as diagnostic or pilot evidence rather than a formal benchmark ranking.
