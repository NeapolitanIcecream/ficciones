from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Literal, Mapping, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


Verdict = Literal["supported", "refuted", "insufficient", "mixed"]
ClaimVerdict = Literal["supported", "refuted", "insufficient"]
DiagnosticAnswer = Literal["yes", "no", "uncertain"]
CurrentDiagnosticAnswer = Literal["yes", "no", "not_applicable", "uncertain"]
CriticalRisk = Literal[
    "stale_evidence",
    "conflicting_evidence",
    "generated_lore",
    "no_primary_source",
    "false_consensus",
    "citation_laundering",
    "partial_support",
]
VerificationRisk = Literal[
    "temporal_staleness",
    "source_independence",
    "citation_chain",
    "generated_lore",
    "primary_support",
]
VerificationMethod = Literal[
    "read_docs",
    "trace_citation",
    "compare_versions",
    "request_primary_record",
    "search_contradictions",
]
VerificationEffect = Literal["supports", "weakens", "refutes", "makes_insufficient"]
ScopeTag = Literal[
    "full",
    "partial",
    "stale",
    "conflicting",
    "mixed_evidence",
    "no_primary_source",
    "generated_lore",
    "uncertain",
]
Strategy = Literal["topk_rag", "citation_prompt", "source_independence_prompt", "evidence_graph_prompt"]

VERDICTS = ("supported", "refuted", "insufficient", "mixed")
STRATEGIES = ("topk_rag", "citation_prompt", "source_independence_prompt", "evidence_graph_prompt")


class EhaModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class AgentDocument(EhaModel):
    doc_id: str
    task_id: str
    title: str
    source_type: str
    timestamp: str
    body: str
    visible_citations: List[str] = Field(default_factory=list)


class GoldDocument(EhaModel):
    doc_id: str
    task_id: str
    target_claim_id: str
    stance: str
    supports_gold_verdict: bool
    contamination: List[str] = Field(default_factory=list)
    upstream_root: str
    generated: bool = False
    stale: bool = False
    valid_time: str
    evidence_quality: str
    rank_boost: float = 0.0

    @computed_field
    @property
    def is_contaminated(self) -> bool:
        return bool(self.contamination) or self.generated or self.stale


class DependencyEdge(EhaModel):
    from_doc: str = Field(alias="from")
    to_doc: str = Field(alias="to")
    relation: str


class TaskGold(EhaModel):
    verdict: Verdict
    scope_tag: ScopeTag = "full"
    answer_brief: str
    primary_support: List[str]
    known_contaminants: List[str]
    diagnostics: Dict[str, str] = Field(default_factory=dict)
    critical_risks: List[str] = Field(default_factory=list)


class Task(EhaModel):
    task_id: str
    question: str
    target_claim_id: str
    difficulty: str
    episode_type: str
    pollution_types: List[str]
    duplicate_count: int
    phase: str = "phase1"
    primary_visibility_under_bm25_top8: Optional[bool] = None
    pollutant_root_id: Optional[str] = None
    pollutant_saturation_at_8_target: Optional[float] = None
    stress_score: Optional[int] = None
    primary_refutation_docs: List[str] = Field(default_factory=list)
    gold: TaskGold


class Manifest(EhaModel):
    name: str
    seed: int
    episodes: int
    created_by: str
    notes: str
    episode_type_counts: Dict[str, int]


class Prediction(EhaModel):
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    rejected_evidence: List[str] = Field(default_factory=list)
    predicted_dependency_edges: List[DependencyEdge] = Field(default_factory=list)
    source_independence: str = ""
    contamination_notes: str = ""
    remaining_uncertainties: str = ""
    answer: str = ""

    @field_validator("verdict", mode="before")
    @classmethod
    def normalize_verdict(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class RunRecord(EhaModel):
    task_id: str
    model: str
    strategy: Strategy
    backend: str
    retrieved_doc_ids: List[str]
    prediction: Prediction
    parse_success: bool
    parse_error: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    prompt_path: Optional[str] = None
    response_path: Optional[str] = None


class Phase2Prediction(EhaModel):
    claim_verdict: ClaimVerdict
    scope_tag: ScopeTag
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_evidence: List[str] = Field(default_factory=list)
    rejected_evidence: List[str] = Field(default_factory=list)
    predicted_dependency_edges: List[DependencyEdge] = Field(default_factory=list)
    source_independence: str = ""
    contamination_notes: str = ""
    remaining_uncertainties: str = ""
    answer: str = ""

    @field_validator("claim_verdict", mode="before")
    @classmethod
    def normalize_claim_verdict(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("scope_tag", mode="before")
    @classmethod
    def normalize_scope_tag(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class ToolCall(EhaModel):
    tool: str
    args: Dict[str, Any] = Field(default_factory=dict)


class EvidenceDiagnostics(EhaModel):
    has_primary_support: DiagnosticAnswer
    primary_support_is_current: CurrentDiagnosticAnswer
    evidence_has_conflict: DiagnosticAnswer
    support_is_partial: DiagnosticAnswer
    sources_are_independent: DiagnosticAnswer
    citation_laundering_detected: DiagnosticAnswer
    generated_lore_detected: DiagnosticAnswer
    no_primary_source_detected: DiagnosticAnswer

    @field_validator("*", mode="before")
    @classmethod
    def normalize_diagnostic_answer(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class VerificationLedgerEntry(EhaModel):
    risk_checked: VerificationRisk
    method: VerificationMethod
    evidence: List[str] = Field(default_factory=list)
    finding: str
    effect_on_verdict: VerificationEffect

    @field_validator("risk_checked", "method", "effect_on_verdict", mode="before")
    @classmethod
    def normalize_ledger_enum(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value


class Phase2SPrediction(EhaModel):
    claim_verdict: ClaimVerdict
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_diagnostics: EvidenceDiagnostics
    critical_risks: List[CriticalRisk] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    rejected_evidence: List[str] = Field(default_factory=list)
    verification_ledger: List[VerificationLedgerEntry] = Field(default_factory=list)
    answer: str = ""

    @field_validator("claim_verdict", mode="before")
    @classmethod
    def normalize_phase2s_claim_verdict(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("critical_risks", mode="before")
    @classmethod
    def normalize_critical_risks(cls, value: Any) -> Any:
        if isinstance(value, list):
            return [item.strip().lower() if isinstance(item, str) else item for item in value]
        return value


class Phase2RunRecord(EhaModel):
    task_id: str
    model: str
    retriever: str
    strategy: str
    backend: str
    initial_doc_ids: List[str]
    final_doc_ids: List[str]
    prediction: Phase2Prediction
    parse_success: bool
    tool_parse_success: bool = True
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    parse_error: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    prompt_path: Optional[str] = None
    response_path: Optional[str] = None


class Phase2SRunRecord(EhaModel):
    task_id: str
    module: str
    dataset: str
    model: str
    retriever: str
    strategy: str
    prompt: str
    backend: str
    initial_doc_ids: List[str]
    final_doc_ids: List[str]
    prediction: Phase2SPrediction
    parse_success: bool
    tool_parse_success: bool = True
    tool_calls: List[ToolCall] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    parse_error: Optional[str] = None
    usage: Dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0
    prompt_path: Optional[str] = None
    response_path: Optional[str] = None


class UsageRecord(EhaModel):
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


def model_to_dict(value: EhaModel) -> Dict[str, Any]:
    return value.model_dump(by_alias=True, exclude_computed_fields=True)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def task_from_dict(row: Mapping[str, Any]) -> Task:
    return Task.model_validate(row)


def document_from_dict(row: Mapping[str, Any]) -> AgentDocument:
    return AgentDocument.model_validate(row)


def gold_document_from_dict(row: Mapping[str, Any]) -> GoldDocument:
    return GoldDocument.model_validate(row)


def edge_from_dict(row: Mapping[str, Any]) -> DependencyEdge:
    return DependencyEdge.model_validate(row)


def prediction_from_dict(row: Mapping[str, Any]) -> Prediction:
    return Prediction.model_validate(row)


def run_record_from_dict(row: Mapping[str, Any]) -> RunRecord:
    return RunRecord.model_validate(row)


def load_dataset(data_dir: Path) -> Dict[str, Any]:
    tasks = [task_from_dict(row) for row in read_jsonl(data_dir / "tasks.jsonl")]
    documents = [document_from_dict(row) for row in read_jsonl(data_dir / "documents.jsonl")]
    gold_docs = [gold_document_from_dict(row) for row in read_jsonl(data_dir / "gold_documents.jsonl")]
    edges = [edge_from_dict(row) for row in read_jsonl(data_dir / "gold_graph.jsonl")]
    manifest = read_json(data_dir / "manifest.json")
    return {
        "manifest": manifest,
        "tasks": tasks,
        "documents": documents,
        "gold_documents": gold_docs,
        "edges": edges,
    }


def by_task(items: Sequence[Any]) -> Dict[str, List[Any]]:
    grouped: Dict[str, List[Any]] = {}
    for item in items:
        grouped.setdefault(item.task_id, []).append(item)
    return grouped


def gold_by_doc(gold_documents: Sequence[GoldDocument]) -> Dict[str, GoldDocument]:
    return {item.doc_id: item for item in gold_documents}


def docs_by_id(documents: Sequence[AgentDocument]) -> Dict[str, AgentDocument]:
    return {item.doc_id: item for item in documents}
