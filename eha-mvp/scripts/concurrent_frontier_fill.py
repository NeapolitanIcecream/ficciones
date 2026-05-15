from __future__ import annotations

import argparse
import json
import threading
import time
from collections import Counter, defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from loguru import logger

from eha.cost_guard import CostGuard
from eha.epistemic_frontier_main import (
    PROMPT_CONDITIONS,
    completed_job_keys,
    run_single_job,
    selected_profiles,
    selected_prompts,
    write_frontier_reports,
    write_jsonl_line,
)
from eha.epistemic_resilience import EpistemicRunRecord, read_tasks
from eha.schemas import model_to_dict, write_json


def parse_model_limits(items: Iterable[str]) -> dict[str, int]:
    limits: dict[str, int] = {}
    for item in items:
        if not item:
            continue
        model, _, value = item.partition("=")
        if not model or not value:
            raise ValueError(f"invalid model limit: {item}")
        limits[model] = int(value)
    return limits


def load_records(path: Path) -> list[EpistemicRunRecord]:
    if not path.exists():
        return []
    return [
        EpistemicRunRecord.model_validate(json.loads(line))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def round_robin_by_model(jobs):
    grouped = defaultdict(deque)
    model_order = []
    for job in jobs:
        model = job[0].model
        if model not in grouped:
            model_order.append(model)
        grouped[model].append(job)

    ordered = []
    while grouped:
        for model in list(model_order):
            queue = grouped.get(model)
            if not queue:
                grouped.pop(model, None)
                continue
            ordered.append(queue.popleft())
            if not queue:
                grouped.pop(model, None)
        model_order = [model for model in model_order if model in grouped]
    return ordered


def main() -> None:
    parser = argparse.ArgumentParser(description="Fill missing EHA frontier-main jobs concurrently.")
    parser.add_argument("--task-dir", type=Path, default=Path("data/epistemic-resilience-v1"))
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--models", default="")
    parser.add_argument("--prompt-conditions", default=",".join(PROMPT_CONDITIONS))
    parser.add_argument("--max-workers", type=int, default=20)
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument("--model-limit", action="append", default=[], help="Per-model concurrency limit, e.g. kimi-k2.6=6")
    parser.add_argument("--soft-cap-usd", type=float, default=250.0)
    parser.add_argument("--hard-cap-usd", type=float, default=800.0)
    parser.add_argument("--abort-cap-usd", type=float, default=1000.0)
    args = parser.parse_args()

    logger.remove()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = out_dir / "predictions.jsonl"
    tasks = read_tasks(args.task_dir / "tasks.jsonl")
    profiles = selected_profiles(args.models)
    prompts = selected_prompts(args.prompt_conditions)
    completed = completed_job_keys(predictions_path)

    jobs = []
    for profile in profiles:
        for task in tasks:
            for prompt_condition in prompts:
                key = (profile.model, task.task_id, prompt_condition, profile.budget_setting)
                if key not in completed:
                    jobs.append((profile, task, prompt_condition, key))
    jobs = round_robin_by_model(jobs)

    model_limits = parse_model_limits(args.model_limit)
    semaphores = {profile.model: threading.Semaphore(model_limits.get(profile.model, 2)) for profile in profiles}
    write_lock = threading.Lock()
    cost_lock = threading.Lock()
    cost_guard = CostGuard(soft_cap_usd=args.soft_cap_usd, hard_cap_usd=args.hard_cap_usd, abort_cap_usd=args.abort_cap_usd)
    missing_by_model = Counter(profile.model for profile, _, _, _ in jobs)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scheduler": "concurrent_frontier_fill",
        "out_dir": str(out_dir),
        "initial_completed_count": len(completed),
        "missing_count": len(jobs),
        "missing_by_model": dict(missing_by_model),
        "per_model_concurrency": {model: semaphores[model]._value for model in semaphores},
        "max_workers": args.max_workers,
        "max_attempts": args.max_attempts,
    }
    write_json(out_dir / "concurrent_fill_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False), flush=True)

    start = time.time()
    progress: Counter[str] = Counter()
    failures = []

    def run_job(item):
        profile, task, prompt_condition, key = item
        with semaphores[profile.model]:
            record = run_single_job(
                profile=profile,
                task=task,
                prompt_condition=prompt_condition,
                out_dir=out_dir,
                max_attempts=args.max_attempts,
                cost_guard=cost_guard,
                cost_lock=cost_lock,
            )
            write_jsonl_line(predictions_path, model_to_dict(record), write_lock)
            return key, record

    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as executor:
        futures = [executor.submit(run_job, job) for job in jobs]
        total = len(futures)
        for index, future in enumerate(as_completed(futures), 1):
            _, record = future.result()
            progress[record.model] += 1
            if not record.parse_success or record.empty_output:
                failures.append(
                    {
                        "model": record.model,
                        "task_id": record.task_id,
                        "prompt_condition": record.prompt_condition,
                        "parse_success": record.parse_success,
                        "empty_output": record.empty_output,
                        "parse_error": record.parse_error,
                    }
                )
                print(f"failure {json.dumps(failures[-1], ensure_ascii=False)}", flush=True)
            if index == 1 or index % 25 == 0 or index == total:
                elapsed = round(time.time() - start, 1)
                print(f"progress {index}/{total} elapsed_s={elapsed} by_model={dict(progress)}", flush=True)

    records = load_records(predictions_path)
    cost_report = {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in records), 6), **cost_guard.report()}
    write_frontier_reports(out_dir, records=records, tasks=tasks, cost_report=cost_report)
    result = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(time.time() - start, 3),
        "filled_count": sum(progress.values()),
        "filled_by_model": dict(progress),
        "failures": failures,
        "final_record_count": len(records),
    }
    write_json(out_dir / "concurrent_fill_result.json", result)
    print(f"done {json.dumps(result, ensure_ascii=False)}", flush=True)


if __name__ == "__main__":
    main()
