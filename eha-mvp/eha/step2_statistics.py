from __future__ import annotations

from collections import defaultdict
from itertools import product
from random import Random
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = q * (len(ordered) - 1)
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def task_cluster_bootstrap_ci(
    rows: Sequence[Mapping[str, Any]],
    *,
    metric: str,
    cluster_key: str = "task_id",
    seed: int = 1729,
    samples: int = 2000,
) -> Tuple[float, float]:
    clusters: Dict[Any, List[float]] = defaultdict(list)
    for row in rows:
        value = row.get(metric)
        if value in {"", None}:
            continue
        clusters[row[cluster_key]].append(float(value))
    if not clusters:
        return 0.0, 0.0
    cluster_names = sorted(clusters)
    if len(cluster_names) == 1:
        cluster_mean = mean(clusters[cluster_names[0]])
        return cluster_mean, cluster_mean

    rng = Random(seed)
    estimates: List[float] = []
    for _ in range(samples):
        values: List[float] = []
        for _cluster in cluster_names:
            values.extend(clusters[rng.choice(cluster_names)])
        estimates.append(mean(values))
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def summarize_task_cluster_ci(
    rows: Sequence[Mapping[str, Any]],
    *,
    group_keys: Sequence[str],
    metrics: Sequence[str],
    cluster_key: str = "task_id",
    seed: int = 1729,
    samples: int = 2000,
) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)

    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {name: value for name, value in zip(group_keys, key)}
        item["n"] = len(group)
        item["cluster_count"] = len({row[cluster_key] for row in group})
        for metric in metrics:
            values = [float(row[metric]) for row in group if row.get(metric) not in {"", None}]
            low, high = task_cluster_bootstrap_ci(group, metric=metric, cluster_key=cluster_key, seed=seed, samples=samples)
            item[metric] = mean(values)
            item[f"{metric}_ci_low"] = low
            item[f"{metric}_ci_high"] = high
        output.append(item)
    return output


def paired_metric_differences(
    rows: Sequence[Mapping[str, Any]],
    *,
    metric: str,
    condition_key: str,
    baseline_condition: str,
    treatment_condition: str,
    pair_keys: Sequence[str],
) -> List[float]:
    grouped: Dict[tuple[Any, ...], Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        condition = str(row[condition_key])
        if condition not in {baseline_condition, treatment_condition}:
            continue
        value = row.get(metric)
        if value in {"", None}:
            continue
        pair = tuple(row[key] for key in pair_keys)
        grouped[pair][condition].append(float(value))

    diffs: List[float] = []
    for pair in sorted(grouped):
        condition_values = grouped[pair]
        if baseline_condition not in condition_values or treatment_condition not in condition_values:
            continue
        baseline = mean(condition_values[baseline_condition])
        treatment = mean(condition_values[treatment_condition])
        diffs.append(treatment - baseline)
    return diffs


def paired_permutation_test(
    rows: Sequence[Mapping[str, Any]],
    *,
    metric: str,
    condition_key: str,
    baseline_condition: str,
    treatment_condition: str,
    pair_keys: Sequence[str],
    seed: int = 2027,
    samples: int = 10000,
) -> Dict[str, Any]:
    diffs = paired_metric_differences(
        rows,
        metric=metric,
        condition_key=condition_key,
        baseline_condition=baseline_condition,
        treatment_condition=treatment_condition,
        pair_keys=pair_keys,
    )
    observed = mean(diffs)
    if not diffs:
        return {"n_pairs": 0, "mean_difference": 0.0, "p_value": 1.0}

    if len(diffs) <= 16:
        signed_stats = [mean([sign * diff for sign, diff in zip(signs, diffs)]) for signs in product((-1.0, 1.0), repeat=len(diffs))]
    else:
        rng = Random(seed)
        signed_stats = [
            mean([(1.0 if rng.randrange(2) else -1.0) * diff for diff in diffs])
            for _ in range(samples)
        ]
    threshold = abs(observed) - 1e-12
    p_value = sum(1 for stat in signed_stats if abs(stat) >= threshold) / len(signed_stats)
    return {"n_pairs": len(diffs), "mean_difference": observed, "p_value": p_value}
