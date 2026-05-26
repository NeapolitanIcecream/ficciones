from __future__ import annotations

import csv
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

from .epistemic_model_preflight import load_preflight_tasks
from .epistemic_resilience import EpistemicTask


REPORT_DATE = "2026-05-25"
RUN_DIR_NAME = f"reports-eha-uncued-core-claim-overnight-{REPORT_DATE}"
DEFAULT_DATASET_DIR = Path("data/uncued-pilot-v1")
DEFAULT_PILOT_RUN_DIR = Path("results/reports-eha-uncued-pilot-2026-05-22")
DEFAULT_ROBUSTNESS_RUN_DIR = Path("results/reports-eha-uncued-robustness-2026-05-25")
DEFAULT_OUT_DIR = Path("results") / RUN_DIR_NAME
DEFAULT_REPORTS_DIR = Path("../reports")

PILOT_SCORED_FILENAMES = ("scored_predictions.csv", "uncued_pilot_scored_predictions.csv")

TEXT_REJECTION_CUES = (
    "unsourced",
    "unsupported",
    "unverified",
    "derivative",
    "generated",
    "same-chain",
    "same chain",
    "recap",
    "roundup",
    "repost",
    "circular",
    "not independent",
    "not treated as independent",
    "not clean support",
    "not valid support",
    "no primary",
    "primary record",
    "primary source",
    "source tracing",
    "trace source",
    "requires primary",
)

PRIMARY_ACTION_CUES = (
    "primary",
    "official",
    "source repository",
    "original notice",
    "event archive",
    "independent confirmation",
    "operational record",
    "launch record",
    "ledger",
)

EXECUTABLE_ACTIONS = {
    "open",
    "trace_source",
    "search_primary",
    "search_contradiction",
    "compare_versions",
    "abstain",
    "open_best_visible_record",
    "trace_visible_citation",
    "compare_visible_counts",
}


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[Dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv_rows(path: Path) -> list[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def first_existing(paths: Iterable[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError("none of the expected paths exists: " + ", ".join(str(path) for path in paths))


def pilot_scored_path(pilot_run_dir: Path) -> Path:
    return first_existing(pilot_run_dir / name for name in PILOT_SCORED_FILENAMES)


def robustness_rows_path(robustness_run_dir: Path) -> Path:
    return robustness_run_dir / "robustness_rows.csv"


def load_model_rows(pilot_run_dir: Path, robustness_run_dir: Path | None = None) -> list[Dict[str, str]]:
    rows: list[Dict[str, str]] = []
    for row in read_csv_rows(pilot_scored_path(pilot_run_dir)):
        item = dict(row)
        item["source_run"] = "pilot"
        item.setdefault("variant", "")
        rows.append(item)
    if robustness_run_dir is not None and robustness_rows_path(robustness_run_dir).exists():
        for row in read_csv_rows(robustness_rows_path(robustness_run_dir)):
            item = dict(row)
            item["source_run"] = "robustness"
            rows.append(item)
    return rows


def to_float(value: Any, default: float | None = 0.0) -> float | None:
    if value in ("", None, "not_applicable"):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def metric_is_true(value: Any) -> bool:
    return bool(to_float(value, 0.0) and to_float(value, 0.0) >= 0.999)


def split_doc_ids(value: Any) -> list[str]:
    if value in ("", None):
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(item) for item in parsed if str(item)]
    except json.JSONDecodeError:
        pass
    return [part.strip() for part in text.split(",") if part.strip()]


def parse_actions(value: Any) -> list[Dict[str, Any]]:
    if isinstance(value, list):
        return [dict(action) for action in value if isinstance(action, Mapping)]
    if value in ("", None):
        return []
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [dict(action) for action in parsed if isinstance(action, Mapping)]


def normalize_view_task_id(base_task_id: str, view: str) -> str:
    suffix = "hidden" if "hidden" in view else "visible"
    return f"{base_task_id}_{suffix}"


def load_tasks_by_id(dataset_dir: Path) -> dict[str, EpistemicTask]:
    return {task.task_id: task for task in load_preflight_tasks(dataset_dir)}


def task_for_row(row: Mapping[str, Any], tasks_by_id: Mapping[str, EpistemicTask]) -> EpistemicTask:
    task_id = str(row.get("task_id", ""))
    if task_id in tasks_by_id:
        return tasks_by_id[task_id]
    base_task_id = str(row.get("base_task_id") or task_id.rsplit("_", 1)[0])
    view = str(row.get("view", "neutral_metadata_visible"))
    normalized = normalize_view_task_id(base_task_id, view)
    if normalized in tasks_by_id:
        return tasks_by_id[normalized]
    raise KeyError(f"could not resolve task for row task_id={task_id!r} base={base_task_id!r} view={view!r}")


def base_task_id_for_row(row: Mapping[str, Any]) -> str:
    value = str(row.get("base_task_id") or "")
    if value:
        return value
    task_id = str(row.get("task_id", ""))
    return task_id.rsplit("_", 1)[0] if "_" in task_id else task_id


def doc_sets(task: EpistemicTask) -> Dict[str, set[str]]:
    polluted = set(task.contaminant_doc_ids) | set(task.generated_doc_ids) | set(task.stale_doc_ids)
    clean = set(task.primary_doc_ids) - polluted
    roots: dict[str, str] = {doc.doc_id: doc.upstream_root or doc.doc_id for doc in task.documents}
    return {
        "polluted": polluted,
        "clean": clean,
        "generated": set(task.generated_doc_ids),
        "stale": set(task.stale_doc_ids),
        "contaminant": set(task.contaminant_doc_ids),
        "contradiction": set(task.contradiction_doc_ids),
        "all": {doc.doc_id for doc in task.documents},
        "roots": set(roots.values()),
    }


def doc_roots(task: EpistemicTask, doc_ids: Sequence[str]) -> list[str]:
    roots = {doc.doc_id: doc.upstream_root or doc.doc_id for doc in task.documents}
    return [roots.get(doc_id, doc_id) for doc_id in doc_ids]


def support_ids_for_row(row: Mapping[str, Any]) -> list[str]:
    return split_doc_ids(row.get("supporting_evidence") or row.get("support_doc_ids"))


def selected_ids_for_row(row: Mapping[str, Any]) -> list[str]:
    return split_doc_ids(row.get("selected_doc_ids"))


def rejected_ids_for_row(row: Mapping[str, Any], prediction: Mapping[str, Any] | None = None) -> list[str]:
    if prediction:
        for field in ("rejected_evidence", "rejected_or_contaminated_evidence"):
            if field in prediction:
                return split_doc_ids(prediction.get(field))
    return split_doc_ids(row.get("rejected_evidence") or row.get("rejected_doc_ids"))


def prediction_index(run_dir: Path) -> dict[tuple[str, str, str, str], Dict[str, Any]]:
    index: dict[tuple[str, str, str, str], Dict[str, Any]] = {}
    for record in read_jsonl(run_dir / "predictions.jsonl"):
        key = (
            str(record.get("task_id", "")),
            str(record.get("model", "")),
            str(record.get("prompt_condition", "")),
            str(record.get("variant", "")),
        )
        index[key] = record
        if not key[3]:
            continue
        index[(key[0], key[1], key[2], "")] = record
    return index


def merged_prediction_indexes(*run_dirs: Path) -> dict[tuple[str, str, str, str], Dict[str, Any]]:
    merged: dict[tuple[str, str, str, str], Dict[str, Any]] = {}
    for run_dir in run_dirs:
        merged.update(prediction_index(run_dir))
    return merged


def prediction_for_row(row: Mapping[str, Any], index: Mapping[tuple[str, str, str, str], Mapping[str, Any]]) -> Mapping[str, Any]:
    key = (
        str(row.get("task_id", "")),
        str(row.get("model", "")),
        str(row.get("prompt_condition", "")),
        str(row.get("variant", "")),
    )
    record = index.get(key) or index.get((key[0], key[1], key[2], ""))
    if not record:
        return {}
    prediction = record.get("prediction", {})
    return prediction if isinstance(prediction, Mapping) else {}


def combined_prediction_text(prediction: Mapping[str, Any]) -> str:
    chunks: list[str] = []
    for field in ("answer", "evidence_environment_assessment", "evidence_notes", "uncertainty_or_insufficiency_reason"):
        value = prediction.get(field)
        if value:
            chunks.append(str(value))
    for action in parse_actions(prediction.get("actions", [])):
        chunks.append(str(action.get("action", "")))
        chunks.append(str(action.get("target", "")))
        chunks.append(str(action.get("rationale", "")))
    return "\n".join(chunks).lower()


def has_any_cue(text: str, cues: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(cue in lowered for cue in cues)


def aggregate_average(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str], metrics: Sequence[str]) -> list[Dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(str(row.get(key, "")) for key in group_keys)].append(row)
    output: list[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {group_key: key[index] for index, group_key in enumerate(group_keys)}
        item["n"] = len(group)
        for metric in metrics:
            values = [to_float(row.get(metric), None) for row in group]
            numeric = [float(value) for value in values if value is not None]
            item[metric] = sum(numeric) / len(numeric) if numeric else ""
        output.append(item)
    return output


def source_file_hashes(dataset_dir: Path, pilot_run_dir: Path, robustness_run_dir: Path | None = None) -> Dict[str, str]:
    paths = [
        pilot_scored_path(pilot_run_dir),
        dataset_dir / "tasks.jsonl",
        dataset_dir / "latent_tasks.jsonl",
        dataset_dir / "gold_labels.jsonl",
        dataset_dir / "gold_documents.jsonl",
        dataset_dir / "action_gold.jsonl",
        dataset_dir / "dependency_edges.jsonl",
        dataset_dir / "documents_neutral_metadata_visible.jsonl",
        dataset_dir / "documents_neutral_metadata_hidden.jsonl",
    ]
    if robustness_run_dir is not None and robustness_rows_path(robustness_run_dir).exists():
        paths.append(robustness_rows_path(robustness_run_dir))
    return {str(path): file_sha256(path) for path in paths if path.exists()}
