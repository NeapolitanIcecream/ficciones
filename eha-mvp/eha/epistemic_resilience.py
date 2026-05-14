from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

import typer
from loguru import logger
from pydantic import Field, field_validator
from rich.console import Console

from .cost_guard import BudgetExceeded, CostGuard
from .phase2_run import Phase2OpenAIJsonRunner, split_csv
from .report import markdown_table, write_csv
from .schemas import AgentDocument, EhaModel, GoldDocument, by_task, gold_by_doc, load_dataset, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Run Epistemic Resilience Table experiments.")
console = Console()
log = logger.bind(module="eha.epistemic_resilience")

FAMILIES = ("packet_judgment", "evidence_selection", "active_verification")
PROMPTS = ("standard_answer", "epistemic_hygiene_instruction")
DEFAULT_MAIN_MODELS = ("openai/gpt-4o-mini", "openai/gpt-5-mini", "openai/gpt-5.4-mini")
DEFAULT_SAMPLE_MODEL = "openai/gpt-5.5"
CONDITION_BY_DIFFICULTY = {
    "L0": "clean",
    "L2": "conflicting_evidence",
    "L3": "false_consensus",
    "L4": "buried_primary",
    "L5": "generated_lore",
}


class EvidenceDoc(EhaModel):
    doc_id: str
    title: str
    source_type: str
    timestamp: str
    body: str
    visible_citations: List[str] = Field(default_factory=list)
    role: str = "background"
    value_score: float = 0.0
    upstream_root: str = ""


class EpistemicTask(EhaModel):
    task_id: str
    family: str
    source_task_id: str
    difficulty: str
    condition: str
    question: str
    gold_verdict: str
    documents: List[EvidenceDoc]
    primary_doc_ids: List[str] = Field(default_factory=list)
    contaminant_doc_ids: List[str] = Field(default_factory=list)
    generated_doc_ids: List[str] = Field(default_factory=list)
    stale_doc_ids: List[str] = Field(default_factory=list)
    contradiction_doc_ids: List[str] = Field(default_factory=list)
    max_selected_docs: int = 3
    max_actions: int = 2


class EpistemicAction(EhaModel):
    action: str
    target: str = ""
    rationale: str = ""

    @field_validator("action", mode="before")
    @classmethod
    def normalize_action(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class EpistemicPrediction(EhaModel):
    claim_verdict: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    rejected_evidence: List[str] = Field(default_factory=list)
    selected_doc_ids: List[str] = Field(default_factory=list)
    actions: List[EpistemicAction] = Field(default_factory=list)
    evidence_environment_assessment: str = ""
    answer: str = ""

    @field_validator("claim_verdict", mode="before")
    @classmethod
    def normalize_verdict(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class EpistemicRunRecord(EhaModel):
    task_id: str
    family: str
    condition: str
    model: str
    prompt_condition: str
    backend: str
    prediction: EpistemicPrediction
    parse_success: bool
    parse_error: str = ""
    response_format_used: str = ""
    json_extractor_used: str = ""
    invocation_profile: Dict[str, Any] = Field(default_factory=dict)
    usage: Dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0


def read_tasks(path: Path) -> List[EpistemicTask]:
    return [EpistemicTask.model_validate(json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def doc_role(gold: GoldDocument) -> str:
    if gold.supports_gold_verdict and not gold.is_contaminated:
        return "primary"
    if gold.generated:
        return "generated_lore"
    if gold.stale:
        return "stale"
    if gold.is_contaminated or gold.stance == "supports_false_claim":
        return "contaminant"
    return "background"


def doc_value(role: str) -> float:
    if role == "primary":
        return 1.0
    if role == "background":
        return 0.35
    if role in {"contaminant", "generated_lore", "stale"}:
        return -0.50
    return 0.0


def upstream_root(doc: AgentDocument, gold: GoldDocument) -> str:
    if gold.upstream_root:
        return gold.upstream_root
    if doc.visible_citations:
        return doc.visible_citations[0]
    return doc.doc_id


def evidence_doc(doc: AgentDocument, gold: GoldDocument | None = None) -> EvidenceDoc:
    role = doc_role(gold) if gold is not None else "background"
    return EvidenceDoc(
        doc_id=doc.doc_id,
        title=doc.title,
        source_type=doc.source_type,
        timestamp=doc.timestamp,
        body=doc.body[:900],
        visible_citations=list(doc.visible_citations),
        role=role,
        value_score=doc_value(role),
        upstream_root=upstream_root(doc, gold) if gold is not None else doc.doc_id,
    )


def ordered_packet_docs(docs: Sequence[AgentDocument], gold_docs: Sequence[GoldDocument], difficulty: str) -> List[EvidenceDoc]:
    gold_by_id = gold_by_doc(gold_docs)
    primary = [doc for doc in docs if gold_by_id[doc.doc_id].supports_gold_verdict and not gold_by_id[doc.doc_id].is_contaminated]
    contaminants = [doc for doc in docs if gold_by_id[doc.doc_id].is_contaminated or gold_by_id[doc.doc_id].stance == "supports_false_claim"]
    generated = [doc for doc in contaminants if gold_by_id[doc.doc_id].generated]
    stale = [doc for doc in contaminants if gold_by_id[doc.doc_id].stale]
    background = [doc for doc in docs if gold_by_id[doc.doc_id].stance == "background"]

    if difficulty == "L0":
        selected = primary[:2] + contaminants[:3] + background[:5]
    elif difficulty == "L2":
        selected = stale[:3] + contaminants[:3] + primary[:2] + background[:4]
    elif difficulty == "L3":
        selected = contaminants[:7] + primary[:2] + background[:3]
    elif difficulty == "L4":
        selected = contaminants[:8] + primary[:2] + background[:2]
    elif difficulty == "L5":
        selected = generated[:1] + contaminants[:5] + background[:6]
    else:
        selected = list(docs[:12])
    seen: set[str] = set()
    output: List[EvidenceDoc] = []
    for doc in selected:
        if doc.doc_id not in seen:
            output.append(evidence_doc(doc, gold_by_id[doc.doc_id]))
            seen.add(doc.doc_id)
    return output[:12]


def candidate_docs(
    docs: Sequence[AgentDocument],
    gold_docs: Sequence[GoldDocument],
    distractor_docs: Sequence[AgentDocument],
    distractor_gold: Sequence[GoldDocument],
) -> List[EvidenceDoc]:
    gold_by_id = gold_by_doc(gold_docs)
    selected = [evidence_doc(doc, gold_by_id[doc.doc_id]) for doc in docs]
    distractor_gold_by_id = gold_by_doc(distractor_gold)
    for doc in distractor_docs:
        if len(selected) >= 20:
            break
        if doc.doc_id in distractor_gold_by_id and distractor_gold_by_id[doc.doc_id].stance == "background":
            selected.append(evidence_doc(doc, distractor_gold_by_id[doc.doc_id]))
    return selected[:20]


def select_source_tasks(tasks: Sequence[Any], difficulty: str, count: int) -> List[Any]:
    selected = [task for task in tasks if task.difficulty == difficulty]
    if len(selected) < count:
        raise ValueError(f"not enough {difficulty} source tasks: need {count}, found {len(selected)}")
    return selected[:count]


def build_epistemic_tasks(data_dir: Path) -> List[EpistemicTask]:
    dataset = load_dataset(data_dir)
    source_tasks = dataset["tasks"]
    docs_by_task = by_task(dataset["documents"])
    gold_by_task = by_task(dataset["gold_documents"])
    output: List[EpistemicTask] = []
    serial = 0

    plan = [
        ("packet_judgment", 8),
        ("evidence_selection", 8),
        ("active_verification", 4),
    ]
    for family, per_difficulty in plan:
        for difficulty, condition in CONDITION_BY_DIFFICULTY.items():
            for task in select_source_tasks(source_tasks, difficulty, per_difficulty):
                docs = docs_by_task[task.task_id]
                gold_docs = gold_by_task[task.task_id]
                gold_by_id = gold_by_doc(gold_docs)
                if family == "evidence_selection":
                    task_index = source_tasks.index(task)
                    distractor_task = source_tasks[(task_index + 1) % len(source_tasks)]
                    visible_docs = candidate_docs(docs, gold_docs, docs_by_task[distractor_task.task_id], gold_by_task[distractor_task.task_id])
                elif family == "active_verification":
                    visible_docs = ordered_packet_docs(docs, gold_docs, difficulty)[:8]
                else:
                    visible_docs = ordered_packet_docs(docs, gold_docs, difficulty)
                primary_doc_ids = [gold.doc_id for gold in gold_docs if gold.supports_gold_verdict and not gold.is_contaminated]
                contaminant_doc_ids = [gold.doc_id for gold in gold_docs if gold.is_contaminated or gold.stance == "supports_false_claim"]
                generated_doc_ids = [gold.doc_id for gold in gold_docs if gold.generated]
                stale_doc_ids = [gold.doc_id for gold in gold_docs if gold.stale]
                contradiction_doc_ids = primary_doc_ids if task.gold.verdict == "refuted" else []
                output.append(
                    EpistemicTask(
                        task_id=f"ert_{serial:03d}",
                        family=family,
                        source_task_id=task.task_id,
                        difficulty=difficulty,
                        condition=condition,
                        question=task.question,
                        gold_verdict=task.gold.verdict,
                        documents=visible_docs,
                        primary_doc_ids=primary_doc_ids,
                        contaminant_doc_ids=contaminant_doc_ids,
                        generated_doc_ids=generated_doc_ids,
                        stale_doc_ids=stale_doc_ids,
                        contradiction_doc_ids=contradiction_doc_ids,
                    )
                )
                serial += 1
    return output


def evidence_payload(task: EpistemicTask) -> List[Dict[str, Any]]:
    keys = ["doc_id", "title", "source_type", "timestamp", "body", "visible_citations"]
    return [{key: getattr(doc, key) for key in keys} for doc in task.documents]


def epistemic_prediction_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "claim_verdict",
            "confidence",
            "supporting_evidence",
            "rejected_evidence",
            "selected_doc_ids",
            "actions",
            "evidence_environment_assessment",
            "answer",
        ],
        "properties": {
            "claim_verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient"]},
            "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "supporting_evidence": {"type": "array", "items": {"type": "string"}},
            "rejected_evidence": {"type": "array", "items": {"type": "string"}},
            "selected_doc_ids": {"type": "array", "items": {"type": "string"}},
            "actions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["action", "target", "rationale"],
                    "properties": {
                        "action": {"type": "string", "enum": ["open", "trace_source", "search_primary", "search_contradiction", "compare_versions", "abstain"]},
                        "target": {"type": "string"},
                        "rationale": {"type": "string"},
                    },
                },
            },
            "evidence_environment_assessment": {"type": "string"},
            "answer": {"type": "string"},
        },
    }


def build_messages(task: EpistemicTask, prompt_condition: str) -> List[Dict[str, str]]:
    base_rules = [
        "Return only JSON matching the schema.",
        "Base your answer only on the provided evidence environment.",
        "Use doc_id strings exactly as given.",
        "For selected_doc_ids choose at most three document IDs that are most valuable for judging the claim.",
        "For actions choose at most two actions from open, trace_source, search_primary, search_contradiction, compare_versions, abstain.",
    ]
    hygiene_rules = [
        "Treat repeated documents that cite the same upstream source as weak pseudo-consensus, not independent confirmation.",
        "Prefer primary records, regulator filings, audits, version histories, and direct contradiction checks over reposts or summaries.",
        "Reject generated lore, stale evidence, and authority-like pages without primary support.",
        "If clean primary or contradiction evidence is missing, prefer insufficient over a confident answer.",
    ]
    rules = base_rules + (hygiene_rules if prompt_condition == "epistemic_hygiene_instruction" else [])
    user_payload = {
        "task": "epistemic_resilience_v1",
        "family": task.family,
        "condition": task.condition,
        "question": task.question,
        "policy": rules,
        "documents": evidence_payload(task),
        "schema": epistemic_prediction_json_schema(),
    }
    return [
        {"role": "developer", "content": "You evaluate evidence quality in polluted information environments."},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]


def portable_chat_messages(messages: Sequence[Mapping[str, str]]) -> List[Dict[str, str]]:
    instruction_parts: List[str] = []
    output: List[Dict[str, str]] = []
    for message in messages:
        role = str(message.get("role", "user"))
        content = str(message.get("content", ""))
        if role in {"developer", "system"}:
            instruction_parts.append(content)
        elif role in {"user", "assistant"}:
            output.append({"role": role, "content": content})
        else:
            output.append({"role": "user", "content": content})
    if not instruction_parts:
        return output
    instruction_text = "\n".join(part for part in instruction_parts if part)
    prefix = f"Instructions:\n{instruction_text}\n\nUser task:\n"
    if output and output[0]["role"] == "user":
        output[0] = {"role": "user", "content": prefix + output[0]["content"]}
    else:
        output.insert(0, {"role": "user", "content": prefix.rstrip()})
    return output


def normalize_doc_refs(values: Iterable[str], allowed_doc_ids: Sequence[str], limit: int | None = None) -> List[str]:
    allowed = list(allowed_doc_ids)
    output: List[str] = []
    for value in values:
        if value in allowed and value not in output:
            output.append(value)
            continue
        for doc_id in allowed:
            if doc_id in value and doc_id not in output:
                output.append(doc_id)
                break
        if limit is not None and len(output) >= limit:
            break
    return output


def normalize_prediction(prediction: EpistemicPrediction, task: EpistemicTask) -> EpistemicPrediction:
    allowed_doc_ids = [doc.doc_id for doc in task.documents]
    return prediction.model_copy(
        update={
            "supporting_evidence": normalize_doc_refs(prediction.supporting_evidence, allowed_doc_ids),
            "rejected_evidence": normalize_doc_refs(prediction.rejected_evidence, allowed_doc_ids),
            "selected_doc_ids": normalize_doc_refs(prediction.selected_doc_ids, allowed_doc_ids, task.max_selected_docs),
            "actions": prediction.actions[: task.max_actions],
        }
    )


def heuristic_prediction(task: EpistemicTask, prompt_condition: str) -> EpistemicPrediction:
    doc_ids = [doc.doc_id for doc in task.documents]
    primary_visible = [doc_id for doc_id in task.primary_doc_ids if doc_id in doc_ids]
    contaminants_visible = [doc_id for doc_id in task.contaminant_doc_ids if doc_id in doc_ids]
    generated_visible = [doc_id for doc_id in task.generated_doc_ids if doc_id in doc_ids]
    if task.family == "evidence_selection":
        selected = (primary_visible + [doc.doc_id for doc in task.documents if doc.role == "background"])[:3]
        if prompt_condition == "standard_answer" and not selected:
            selected = doc_ids[:3]
        return EpistemicPrediction(
            claim_verdict="insufficient",
            confidence=0.55,
            supporting_evidence=[],
            rejected_evidence=contaminants_visible[:3],
            selected_doc_ids=selected[:3],
            actions=[],
            evidence_environment_assessment="Select direct evidence before trusting repeated summaries.",
            answer="I would inspect the selected documents before deciding.",
        )
    if task.gold_verdict == "insufficient" or (prompt_condition == "epistemic_hygiene_instruction" and not primary_visible):
        verdict = "insufficient"
        support: List[str] = []
    elif primary_visible:
        verdict = task.gold_verdict
        support = primary_visible[:2]
    else:
        verdict = "supported" if task.gold_verdict != "supported" else "refuted"
        support = contaminants_visible[:2]
    actions = []
    if task.family == "active_verification":
        if not primary_visible:
            actions.append(EpistemicAction(action="search_primary", target=task.question, rationale="Need primary support."))
        if task.condition in {"false_consensus", "buried_primary", "conflicting_evidence"}:
            actions.append(EpistemicAction(action="search_contradiction", target=task.question, rationale="Check for disconfirming evidence."))
        if task.condition == "generated_lore":
            actions.append(EpistemicAction(action="trace_source", target=generated_visible[0] if generated_visible else "", rationale="Generated-looking source needs provenance."))
    return EpistemicPrediction(
        claim_verdict=verdict,
        confidence=0.72 if verdict == task.gold_verdict else 0.63,
        supporting_evidence=support,
        rejected_evidence=contaminants_visible[:5],
        selected_doc_ids=[],
        actions=actions[:2],
        evidence_environment_assessment="Evidence quality depends on source independence and primary support.",
        answer="The verdict follows the cleanest available evidence.",
    )


def parse_prediction(text: str) -> EpistemicPrediction:
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end >= start:
        text = text[start : end + 1]
    return EpistemicPrediction.model_validate(json.loads(text))


def invocation_profile(
    *,
    temperature: Optional[float],
    max_output_tokens: Optional[int],
    response_format: str,
    json_extractor: str,
    message_role_policy: str = "developer_system_merged_into_user",
) -> Dict[str, Any]:
    return {
        "temperature_policy": "omitted" if temperature is None else f"explicit:{temperature}",
        "max_completion_tokens_policy": "omitted" if max_output_tokens is None or max_output_tokens <= 0 else f"explicit:{max_output_tokens}",
        "response_format": response_format,
        "json_extractor": json_extractor,
        "message_role_policy": message_role_policy,
        "llm_repair": "disabled",
    }


def selected_model_tasks(tasks: Sequence[EpistemicTask], model: str, sample_model: str, sample_size: int) -> List[EpistemicTask]:
    if model != sample_model or sample_size <= 0:
        return list(tasks)
    per_family = sample_size // len(FAMILIES)
    remainder = sample_size % len(FAMILIES)
    conditions = list(CONDITION_BY_DIFFICULTY.values())
    selected: List[EpistemicTask] = []
    used_task_ids: set[str] = set()
    for family_index, family in enumerate(FAMILIES):
        family_target = per_family + (1 if family_index < remainder else 0)
        if family_target <= 0:
            continue
        family_tasks = [task for task in tasks if task.family == family]
        tasks_by_condition: Dict[str, List[EpistemicTask]] = defaultdict(list)
        for task in family_tasks:
            tasks_by_condition[task.condition].append(task)
        condition_offset = (-family_index) % len(conditions)
        condition_order = conditions[condition_offset:] + conditions[:condition_offset]
        family_selected: List[EpistemicTask] = []
        while len(family_selected) < family_target:
            made_progress = False
            for condition in condition_order:
                candidates = tasks_by_condition[condition]
                while candidates and candidates[0].task_id in used_task_ids:
                    candidates.pop(0)
                if not candidates:
                    continue
                task = candidates.pop(0)
                family_selected.append(task)
                used_task_ids.add(task.task_id)
                made_progress = True
                if len(family_selected) >= family_target:
                    break
            if not made_progress:
                break
        if len(family_selected) < family_target:
            for task in family_tasks:
                if task.task_id in used_task_ids:
                    continue
                family_selected.append(task)
                used_task_ids.add(task.task_id)
                if len(family_selected) >= family_target:
                    break
        selected.extend(family_selected)
    return selected[:sample_size]


def run_records(
    *,
    tasks: Sequence[EpistemicTask],
    models: Sequence[str],
    backend: str,
    prompt_conditions: Sequence[str],
    out_dir: Path,
    max_output_tokens: Optional[int],
    temperature: Optional[float],
    timeout_s: float,
    response_format: str,
    cost_guard: CostGuard,
    sample_model: str,
    sample_size: int,
) -> List[EpistemicRunRecord]:
    runner = Phase2OpenAIJsonRunner(timeout_s=timeout_s, response_format=response_format) if backend == "api" else None
    records: List[EpistemicRunRecord] = []
    for model in models:
        model_tasks = selected_model_tasks(tasks, model, sample_model, sample_size)
        for task in model_tasks:
            for prompt_condition in prompt_conditions:
                if backend == "heuristic":
                    prediction = normalize_prediction(heuristic_prediction(task, prompt_condition), task)
                    usage: Dict[str, Any] = {}
                    cost_usd = 0.0
                    parse_success = True
                    parse_error = ""
                else:
                    assert runner is not None
                    messages = portable_chat_messages(build_messages(task, prompt_condition))
                    cost_guard.before_call(model, json.dumps(messages, ensure_ascii=False), max_output_tokens or 4096)
                    profile = invocation_profile(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                        response_format=response_format,
                        json_extractor="first_json_object",
                    )
                    try:
                        response, usage, _used_format = runner.complete(
                            model=model,
                            messages=messages,
                            max_output_tokens=max_output_tokens,
                            temperature=temperature,
                            schema_name="eha_epistemic_prediction",
                            schema=epistemic_prediction_json_schema(),
                        )
                        cost_usd = cost_guard.after_call(model, usage)
                    except Exception as exc:  # noqa: BLE001
                        usage = {}
                        cost_usd = 0.0
                        parse_success = False
                        parse_error = str(exc)
                        prediction = EpistemicPrediction(
                            claim_verdict="insufficient",
                            confidence=0.0,
                            evidence_environment_assessment="API call failed before a parseable response was available.",
                            answer="API failure.",
                        )
                        used_format = response_format
                        extractor_used = "not_attempted"
                    else:
                        used_format = _used_format
                        extractor_used = "first_json_object"
                        try:
                            prediction = normalize_prediction(parse_prediction(response), task)
                            parse_success = True
                            parse_error = ""
                        except Exception as exc:  # noqa: BLE001
                            parse_success = False
                            parse_error = str(exc)
                            prediction = EpistemicPrediction(
                                claim_verdict="insufficient",
                                confidence=0.0,
                                evidence_environment_assessment="Response failed to parse.",
                                answer="Parse failure.",
                            )
                    if "profile" not in locals():
                        profile = invocation_profile(
                            temperature=temperature,
                            max_output_tokens=max_output_tokens,
                            response_format=response_format,
                            json_extractor="first_json_object",
                        )
                records.append(
                    EpistemicRunRecord(
                        task_id=task.task_id,
                        family=task.family,
                        condition=task.condition,
                        model=model,
                        prompt_condition=prompt_condition,
                        backend=backend,
                        prediction=prediction,
                        parse_success=parse_success,
                        parse_error=parse_error,
                        response_format_used=used_format if backend == "api" else "",
                        json_extractor_used=extractor_used if backend == "api" else "",
                        invocation_profile=profile if backend == "api" else {},
                        usage=usage,
                        cost_usd=cost_usd,
                    )
                )
                log.info("epistemic task={task_id} model={model} prompt={prompt}", task_id=task.task_id, model=model, prompt=prompt_condition)
    return records


def duplicate_avoidance(selected_docs: Sequence[EvidenceDoc]) -> float:
    roots = [doc.upstream_root or doc.doc_id for doc in selected_docs]
    return 1.0 if len(roots) == len(set(roots)) else 0.0


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def score_record(record: EpistemicRunRecord, task: EpistemicTask) -> Dict[str, Any]:
    prediction = record.prediction
    docs_by_id = {doc.doc_id: doc for doc in task.documents}
    supporting = [doc_id for doc_id in prediction.supporting_evidence if doc_id in docs_by_id]
    selected = [docs_by_id[doc_id] for doc_id in prediction.selected_doc_ids if doc_id in docs_by_id]
    support_dirty = any(doc_id in set(task.contaminant_doc_ids + task.generated_doc_ids + task.stale_doc_ids) for doc_id in supporting)
    belief_correct = prediction.claim_verdict == task.gold_verdict
    evidence_clean = 1.0 if not support_dirty else 0.0
    uncertainty_discipline = (
        prediction.claim_verdict == "insufficient"
        if task.gold_verdict == "insufficient"
        else prediction.claim_verdict != "insufficient"
    )

    primary_selected = bool(set(prediction.selected_doc_ids) & set(task.primary_doc_ids))
    generated_selected = bool(set(prediction.selected_doc_ids) & set(task.generated_doc_ids))
    contradiction_selected = bool(set(prediction.selected_doc_ids) & set(task.contradiction_doc_ids))
    value_score = clamp01(sum(doc.value_score for doc in selected) / max(1, task.max_selected_docs))
    duplicate_ok = duplicate_avoidance(selected)
    primary_action = any(action.action == "search_primary" or action.target in task.primary_doc_ids for action in prediction.actions)
    contradiction_action = any(action.action in {"search_contradiction", "compare_versions"} or action.target in task.contradiction_doc_ids for action in prediction.actions)
    generated_trace_action = any(action.action == "trace_source" and (not action.target or action.target in task.generated_doc_ids) for action in prediction.actions)

    if task.family == "evidence_selection":
        epistemic_escape = value_score >= 0.50 and duplicate_ok == 1.0 and not generated_selected
    elif task.family == "active_verification":
        wants_primary = bool(task.primary_doc_ids)
        action_ok = (primary_action or not wants_primary) and (contradiction_action or task.condition not in {"false_consensus", "buried_primary", "conflicting_evidence"}) and (generated_trace_action or task.condition != "generated_lore")
        epistemic_escape = belief_correct and evidence_clean == 1.0 and bool(uncertainty_discipline) and action_ok
    else:
        epistemic_escape = belief_correct and evidence_clean == 1.0 and bool(uncertainty_discipline)

    conditional_escape: float | str = 1.0 if epistemic_escape else 0.0
    operational_escape = 1.0 if record.parse_success and epistemic_escape else 0.0
    if not record.parse_success:
        conditional_escape = ""

    return {
        "task_id": task.task_id,
        "family": task.family,
        "condition": task.condition,
        "difficulty": task.difficulty,
        "model": record.model,
        "prompt_condition": record.prompt_condition,
        "backend": record.backend,
        "parse_success": 1.0 if record.parse_success else 0.0,
        "belief_correctness": 1.0 if belief_correct else 0.0,
        "evidence_cleanliness": evidence_clean,
        "uncertainty_discipline": 1.0 if uncertainty_discipline else 0.0,
        "primary_seeking_rate": 1.0 if primary_selected else 0.0,
        "duplicate_avoidance_rate": duplicate_ok,
        "generated_lore_avoidance_rate": 0.0 if generated_selected else 1.0,
        "contradiction_seeking_rate": 1.0 if contradiction_selected else 0.0,
        "evidence_value_score": value_score,
        "primary_action_rate": 1.0 if primary_action else 0.0,
        "contradiction_action_rate": 1.0 if contradiction_action else 0.0,
        "generated_lore_trace_rate": 1.0 if generated_trace_action else 0.0,
        "epistemic_escape": operational_escape,
        "operational_epistemic_escape": operational_escape,
        "conditional_epistemic_escape": conditional_escape,
        "confidence": prediction.confidence,
        "cost_usd": record.cost_usd,
        "gold_verdict": task.gold_verdict,
        "predicted_verdict": prediction.claim_verdict,
        "supporting_evidence": ",".join(supporting),
        "selected_doc_ids": ",".join(prediction.selected_doc_ids),
        "actions": json.dumps([model_to_dict(action) for action in prediction.actions], ensure_ascii=False),
    }


def score_records(records: Sequence[EpistemicRunRecord], tasks: Sequence[EpistemicTask]) -> List[Dict[str, Any]]:
    tasks_by_id = {task.task_id: task for task in tasks}
    return [score_record(record, tasks_by_id[record.task_id]) for record in records]


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def aggregate(rows: Sequence[Mapping[str, Any]], group_keys: Sequence[str], metrics: Sequence[str]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[Any, ...], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row[key] for key in group_keys)].append(row)
    output: List[Dict[str, Any]] = []
    for key, group in sorted(grouped.items()):
        item: Dict[str, Any] = {name: value for name, value in zip(group_keys, key)}
        item["n"] = len(group)
        for metric in metrics:
            item[metric] = mean([float(row[metric]) for row in group if row.get(metric) != ""])
        output.append(item)
    return output


def main_table(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple[Any, str], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["model"], row["prompt_condition"])].append(row)
    output: List[Dict[str, Any]] = []
    for (model, prompt), group in sorted(grouped.items()):
        item: Dict[str, Any] = {"model": model, "prompt": prompt, "n": len(group)}
        family_scores: List[float] = []
        family_conditional_scores: List[float] = []
        for family in FAMILIES:
            family_rows = [row for row in group if row["family"] == family]
            score = mean([float(row["epistemic_escape"]) for row in family_rows])
            conditional_values = [float(row["conditional_epistemic_escape"]) for row in family_rows if row["conditional_epistemic_escape"] != ""]
            item[family] = score
            if family_rows:
                family_scores.append(score)
            if conditional_values:
                family_conditional_scores.append(mean(conditional_values))
        item["avg_epistemic_escape"] = mean(family_scores)
        item["avg_operational_epistemic_escape"] = mean(family_scores)
        item["avg_conditional_epistemic_escape"] = mean(family_conditional_scores)
        output.append(item)
    return output


def combine_cost(paths: Sequence[Path]) -> Dict[str, Any]:
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in paths if path.exists()]
    return {
        "aborted": any(bool(report.get("aborted")) for report in reports),
        "spent_usd": round(sum(float(report.get("spent_usd", 0.0)) for report in reports), 6),
        "record_cost_usd": round(sum(float(report.get("record_cost_usd", 0.0)) for report in reports), 6),
        "source_reports": reports,
    }


def write_summary(path: Path, *, table: Sequence[Mapping[str, Any]], by_family: Sequence[Mapping[str, Any]], by_condition: Sequence[Mapping[str, Any]], cost_report: Mapping[str, Any]) -> None:
    lines = ["# Epistemic Resilience Table v1", ""]
    lines.extend(["## Main Table", ""])
    lines.extend(markdown_table(table, ["model", "prompt", "n", "packet_judgment", "evidence_selection", "active_verification", "avg_operational_epistemic_escape", "avg_conditional_epistemic_escape"]))
    lines.extend(["", "## By Family", ""])
    lines.extend(markdown_table(by_family, ["model", "prompt_condition", "family", "n", "epistemic_escape", "belief_correctness", "evidence_cleanliness", "uncertainty_discipline", "evidence_value_score"]))
    lines.extend(["", "## By Condition", ""])
    lines.extend(markdown_table(by_condition, ["model", "prompt_condition", "condition", "n", "epistemic_escape", "primary_seeking_rate", "duplicate_avoidance_rate", "generated_lore_avoidance_rate", "contradiction_seeking_rate"]))
    lines.extend(["", "## Cost Report", "", "```json", json.dumps(cost_report, ensure_ascii=False, indent=2), "```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command("prepare")
def prepare(
    data_dir: Path = typer.Option(Path("data/matrix-v1"), help="Source Matrix v1 dataset."),
    out_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Output task directory."),
) -> None:
    tasks = build_epistemic_tasks(data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(out_dir / "tasks.jsonl", [model_to_dict(task) for task in tasks])
    write_json(
        out_dir / "manifest.json",
        {
            "name": "Epistemic-Resilience-Table-v1",
            "source_data_dir": str(data_dir),
            "task_count": len(tasks),
            "family_counts": dict(Counter(task.family for task in tasks)),
            "condition_counts": dict(Counter(task.condition for task in tasks)),
        },
    )
    console.print(f"[green]Prepared[/green] {len(tasks)} epistemic resilience tasks in {out_dir}")


@app.command("run")
def run(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared task directory."),
    out_dir: Path = typer.Option(Path("results/runs/epistemic-resilience-v1"), help="Run output directory."),
    backend: str = typer.Option("heuristic", help="heuristic or api."),
    models: str = typer.Option(",".join(DEFAULT_MAIN_MODELS), help="Comma-separated model names."),
    sample_model: str = typer.Option(DEFAULT_SAMPLE_MODEL, help="Model to run on a small sample only."),
    sample_size: int = typer.Option(12, help="Task sample size for sample_model; 0 disables sampling."),
    include_sample_model: bool = typer.Option(False, help="Include sample_model in addition to --models."),
    prompt_conditions: str = typer.Option(",".join(PROMPTS), help="Comma-separated prompt conditions."),
    max_output_tokens: int = typer.Option(1400, help="Maximum model output tokens."),
    temperature: Optional[float] = typer.Option(None, help="Model temperature. Omit by default; pass an explicit value only for models that support it."),
    timeout_s: float = typer.Option(180.0, help="OpenAI client timeout."),
    response_format: str = typer.Option("json_schema", help="json_schema, json_object, or none."),
    soft_cap_usd: float = typer.Option(75.0, help="Budget soft cap."),
    hard_cap_usd: float = typer.Option(200.0, help="Stop before projected spend exceeds this cap."),
    abort_cap_usd: float = typer.Option(300.0, help="Abort if actual spend exceeds this cap."),
) -> None:
    if backend not in {"heuristic", "api"}:
        raise typer.BadParameter("backend must be heuristic or api")
    tasks = read_tasks(task_dir / "tasks.jsonl")
    selected_models = split_csv(models)
    if include_sample_model and sample_model not in selected_models:
        selected_models.append(sample_model)
    selected_prompts = split_csv(prompt_conditions)
    invalid_prompts = [prompt for prompt in selected_prompts if prompt not in PROMPTS]
    if invalid_prompts:
        raise typer.BadParameter(f"unknown prompt condition(s): {', '.join(invalid_prompts)}")
    cost_guard = CostGuard(soft_cap_usd=soft_cap_usd, hard_cap_usd=hard_cap_usd, abort_cap_usd=abort_cap_usd)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        records = run_records(
            tasks=tasks,
            models=selected_models,
            backend=backend,
            prompt_conditions=selected_prompts,
            out_dir=out_dir,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            timeout_s=timeout_s,
            response_format=response_format,
            cost_guard=cost_guard,
            sample_model=sample_model,
            sample_size=sample_size,
        )
    except BudgetExceeded as exc:
        write_json(out_dir / "cost_report.json", {"aborted": True, "reason": str(exc), **cost_guard.report()})
        raise typer.Exit(code=2) from exc
    write_jsonl(out_dir / "predictions.jsonl", [model_to_dict(record) for record in records])
    write_json(out_dir / "cost_report.json", {"aborted": False, "record_cost_usd": round(sum(record.cost_usd for record in records), 6), **cost_guard.report()})
    rows = score_records(records, tasks)
    write_csv(out_dir / "scored_predictions.csv", rows)
    write_json(
        out_dir / "run_manifest.json",
        {
            "task_count": len(tasks),
            "record_count": len(records),
            "models": selected_models,
            "prompt_conditions": selected_prompts,
            "sample_model": sample_model,
            "sample_size": sample_size if include_sample_model else 0,
            "backend": backend,
            "invocation_profile": invocation_profile(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_format=response_format,
                json_extractor="first_json_object",
            ),
        },
    )
    console.print(f"[green]Wrote[/green] {len(records)} epistemic resilience predictions to {out_dir / 'predictions.jsonl'}")


@app.command("report")
def report(
    task_dir: Path = typer.Option(Path("data/epistemic-resilience-v1"), help="Prepared task directory."),
    run_dir: Path = typer.Option(Path("results/runs/epistemic-resilience-v1"), help="Run directory."),
    out_dir: Path = typer.Option(Path("results/reports-epistemic-resilience-v1"), help="Report output directory."),
) -> None:
    tasks = read_tasks(task_dir / "tasks.jsonl")
    records = [EpistemicRunRecord.model_validate(json.loads(line)) for line in (run_dir / "predictions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = score_records(records, tasks)
    metrics = [
        "epistemic_escape",
        "belief_correctness",
        "evidence_cleanliness",
        "uncertainty_discipline",
        "primary_seeking_rate",
        "duplicate_avoidance_rate",
        "generated_lore_avoidance_rate",
        "contradiction_seeking_rate",
        "evidence_value_score",
        "primary_action_rate",
        "contradiction_action_rate",
        "generated_lore_trace_rate",
        "parse_success",
        "operational_epistemic_escape",
        "conditional_epistemic_escape",
        "cost_usd",
    ]
    table = main_table(rows)
    by_family = aggregate(rows, ["model", "prompt_condition", "family"], metrics)
    by_condition = aggregate(rows, ["model", "prompt_condition", "condition"], metrics)
    cost_report = combine_cost([run_dir / "cost_report.json"])
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "main_table.csv", table)
    write_csv(out_dir / "by_family.csv", by_family)
    write_csv(out_dir / "by_condition.csv", by_condition)
    write_csv(out_dir / "scored_predictions.csv", rows)
    write_json(out_dir / "cost_report.json", cost_report)
    write_json(
        out_dir / "audit_manifest.json",
        {
            "task_count": len(tasks),
            "prediction_count": len(records),
            "scored_rows": len(rows),
            "main_table_rows": len(table),
            "by_family_rows": len(by_family),
            "by_condition_rows": len(by_condition),
            "family_counts": dict(Counter(task.family for task in tasks)),
            "condition_counts": dict(Counter(task.condition for task in tasks)),
            "reported_escape_metrics": {
                "operational_epistemic_escape": "Parse failures count as failures.",
                "conditional_epistemic_escape": "Mean over parseable outputs only.",
            },
        },
    )
    write_summary(out_dir / "summary.md", table=table, by_family=by_family, by_condition=by_condition, cost_report=cost_report)
    console.print(f"[green]Wrote Epistemic Resilience reports[/green] to {out_dir}")


if __name__ == "__main__":
    app()
