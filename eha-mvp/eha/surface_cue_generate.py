from __future__ import annotations

from collections import Counter
from pathlib import Path
from random import Random
from typing import Dict, List, Tuple

import typer
from rich.console import Console

from .generate_corpus import _body, _doc
from .generate_world import COMPANY
from .schemas import AgentDocument, DependencyEdge, GoldDocument, Manifest, Task, TaskGold, model_to_dict, write_json, write_jsonl


app = typer.Typer(add_completion=False, help="Generate EHA Step 2 surface-cue smoke datasets.")
console = Console()


SURFACE_CUE_AXES: Dict[str, tuple[str, str]] = {
    "source_type_visibility": ("visible_source_types", "hidden_source_types"),
    "metadata_perturbation": ("truthful_metadata", "shuffled_authority_metadata"),
    "style_normalization": ("original_style", "normalized_style"),
    "adversarial_spoofing": ("plain_pollutant", "regulator_spoof_pollutant"),
    "content_only": ("full_metadata", "content_only_metadata_stripped"),
}

def _surface_template(
    *,
    family: str,
    template_id: str,
    question: str,
    answer_brief: str,
    verdict: str,
    scope_tag: str,
    primary_roles: List[str],
    critical_risks: List[str],
    clean_value: str,
    false_value: str,
    clean_subject: str,
    false_quality: str,
    contamination: List[str],
    diagnostic_overrides: Dict[str, str],
) -> Dict[str, object]:
    return {
        "family": family,
        "template_id": template_id,
        "question": question,
        "answer_brief": answer_brief,
        "verdict": verdict,
        "scope_tag": scope_tag,
        "primary_roles": primary_roles,
        "critical_risks": critical_risks,
        "clean_value": clean_value,
        "false_value": false_value,
        "clean_subject": clean_subject,
        "false_quality": false_quality,
        "contamination": contamination,
        "diagnostic_overrides": diagnostic_overrides,
    }


SURFACE_CUE_FAMILIES: Dict[str, List[Dict[str, object]]] = {
    "conflict": [
        _surface_template(
            family="conflict",
            template_id="orders",
            question=f"Did {COMPANY} complete at least 97.6 percent of Q3 2024 replacement orders on time?",
            answer_brief=f"Refuted: signed records show {COMPANY} completed 91.2 percent, not 97.6 percent.",
            verdict="refuted",
            scope_tag="conflicting",
            primary_roles=["ledger", "export"],
            critical_risks=["conflicting_evidence"],
            clean_value="91.2 percent of Q3 2024 replacement orders on time",
            false_value="97.6 percent of Q3 2024 replacement orders on time",
            clean_subject="replacement-order completion",
            false_quality="unsupported_summary",
            contamination=["surface_cue_false_support"],
            diagnostic_overrides={"evidence_has_conflict": "yes"},
        ),
        _surface_template(
            family="conflict",
            template_id="rework",
            question=f"Did {COMPANY} keep May 2024 warranty rework below 1.0 percent?",
            answer_brief="Refuted: signed records show a 2.1 percent May 2024 warranty rework rate.",
            verdict="refuted",
            scope_tag="conflicting",
            primary_roles=["ledger", "export"],
            critical_risks=["conflicting_evidence"],
            clean_value="the May 2024 warranty rework rate was 2.1 percent",
            false_value="May 2024 warranty rework stayed below 1.0 percent",
            clean_subject="warranty-rework rate",
            false_quality="unsupported_summary",
            contamination=["surface_cue_false_support"],
            diagnostic_overrides={"evidence_has_conflict": "yes"},
        ),
        _surface_template(
            family="conflict",
            template_id="calibration",
            question=f"Did {COMPANY} close all Q4 2024 calibration tickets within 48 hours?",
            answer_brief="Refuted: signed ticket records show 84 percent closed within 48 hours, not all tickets.",
            verdict="refuted",
            scope_tag="conflicting",
            primary_roles=["ledger", "export"],
            critical_risks=["conflicting_evidence"],
            clean_value="84 percent of Q4 2024 calibration tickets closed within 48 hours",
            false_value="all Q4 2024 calibration tickets closed within 48 hours",
            clean_subject="calibration-ticket closure",
            false_quality="unsupported_summary",
            contamination=["surface_cue_false_support"],
            diagnostic_overrides={"evidence_has_conflict": "yes"},
        ),
    ],
    "stale": [
        _surface_template(
            family="stale",
            template_id="certificate",
            question=f"Was {COMPANY}'s 2023 safety certificate still valid for January 2025 shipments?",
            answer_brief="Refuted: the current certification ledger says the 2023 certificate expired before January 2025.",
            verdict="refuted",
            scope_tag="stale",
            primary_roles=["ledger", "export"],
            critical_risks=["stale_evidence"],
            clean_value="the 2023 certificate expired before January 2025 shipments",
            false_value="the 2023 certificate was still valid for January 2025 shipments",
            clean_subject="current certification status",
            false_quality="stale_version",
            contamination=["temporal_pollution"],
            diagnostic_overrides={"primary_support_is_current": "no"},
        ),
        _surface_template(
            family="stale",
            template_id="supplier_approval",
            question=f"Was {COMPANY}'s June 2024 supplier approval still valid for March 2025 shipments?",
            answer_brief="Refuted: the current approval ledger says the June 2024 approval expired before March 2025.",
            verdict="refuted",
            scope_tag="stale",
            primary_roles=["ledger", "export"],
            critical_risks=["stale_evidence"],
            clean_value="the June 2024 supplier approval expired before March 2025 shipments",
            false_value="the June 2024 supplier approval was still valid for March 2025 shipments",
            clean_subject="supplier-approval status",
            false_quality="stale_version",
            contamination=["temporal_pollution"],
            diagnostic_overrides={"primary_support_is_current": "no"},
        ),
        _surface_template(
            family="stale",
            template_id="recall_status",
            question=f"Was {COMPANY}'s recall-free status still current in the December 2024 service report?",
            answer_brief="Refuted: the current service ledger records a November 2024 recall update.",
            verdict="refuted",
            scope_tag="stale",
            primary_roles=["ledger", "export"],
            critical_risks=["stale_evidence"],
            clean_value="a November 2024 recall update superseded the recall-free status",
            false_value="the recall-free status was still current in the December 2024 service report",
            clean_subject="recall-status currency",
            false_quality="stale_version",
            contamination=["temporal_pollution"],
            diagnostic_overrides={"primary_support_is_current": "no"},
        ),
    ],
    "partial": [
        _surface_template(
            family="partial",
            template_id="warranty_traceability",
            question=f"Did {COMPANY} document complete end-to-end traceability for all Q4 2024 warranty repairs?",
            answer_brief="Insufficient: clean records cover intake logs but not complete end-to-end traceability for all repairs.",
            verdict="insufficient",
            scope_tag="partial",
            primary_roles=["ledger", "export"],
            critical_risks=["partial_support"],
            clean_value="intake logs were complete for the sampled warranty repairs",
            false_value="complete end-to-end traceability existed for all Q4 2024 warranty repairs",
            clean_subject="partial warranty-repair traceability",
            false_quality="overbroad_summary",
            contamination=["surface_cue_overclaim"],
            diagnostic_overrides={"support_is_partial": "yes"},
        ),
        _surface_template(
            family="partial",
            template_id="returns_chain",
            question=f"Did {COMPANY} document complete chain of custody for all May 2024 returns?",
            answer_brief="Insufficient: clean records cover receiving checks but not complete chain of custody for all returns.",
            verdict="insufficient",
            scope_tag="partial",
            primary_roles=["ledger", "export"],
            critical_risks=["partial_support"],
            clean_value="receiving checks were documented for sampled May 2024 returns",
            false_value="complete chain of custody existed for all May 2024 returns",
            clean_subject="partial returns chain of custody",
            false_quality="overbroad_summary",
            contamination=["surface_cue_overclaim"],
            diagnostic_overrides={"support_is_partial": "yes"},
        ),
        _surface_template(
            family="partial",
            template_id="vendor_audits",
            question=f"Did {COMPANY} publish complete vendor audit results for every Q3 2024 subcontractor?",
            answer_brief="Insufficient: clean records cover two subcontractors but not every Q3 2024 subcontractor.",
            verdict="insufficient",
            scope_tag="partial",
            primary_roles=["ledger", "export"],
            critical_risks=["partial_support"],
            clean_value="vendor audit results covered two Q3 2024 subcontractors",
            false_value="complete vendor audit results covered every Q3 2024 subcontractor",
            clean_subject="partial vendor-audit coverage",
            false_quality="overbroad_summary",
            contamination=["surface_cue_overclaim"],
            diagnostic_overrides={"support_is_partial": "yes"},
        ),
    ],
    "generated_lore": [
        _surface_template(
            family="generated_lore",
            template_id="heliosplice",
            question=f"Did {COMPANY} launch the HelioSplice partner-repair program in Q2 2024?",
            answer_brief="Insufficient: the claim appears only in generated or derivative lore and has no clean primary support.",
            verdict="insufficient",
            scope_tag="generated_lore",
            primary_roles=[],
            critical_risks=["generated_lore", "no_primary_source"],
            clean_value="the available context does not document a HelioSplice partner-repair launch",
            false_value="the HelioSplice partner-repair program launched in Q2 2024",
            clean_subject="program background context",
            false_quality="generated_summary",
            contamination=["generated_lore"],
            diagnostic_overrides={"has_primary_support": "no", "primary_support_is_current": "not_applicable", "generated_lore_detected": "yes", "no_primary_source_detected": "yes"},
        ),
        _surface_template(
            family="generated_lore",
            template_id="auroradock",
            question=f"Did {COMPANY} introduce the AuroraDock field-upgrade toolkit in April 2024?",
            answer_brief="Insufficient: the AuroraDock toolkit appears only in generated or derivative lore.",
            verdict="insufficient",
            scope_tag="generated_lore",
            primary_roles=[],
            critical_risks=["generated_lore", "no_primary_source"],
            clean_value="the available context does not document an AuroraDock field-upgrade toolkit",
            false_value="the AuroraDock field-upgrade toolkit was introduced in April 2024",
            clean_subject="toolkit background context",
            false_quality="generated_summary",
            contamination=["generated_lore"],
            diagnostic_overrides={"has_primary_support": "no", "primary_support_is_current": "not_applicable", "generated_lore_detected": "yes", "no_primary_source_detected": "yes"},
        ),
        _surface_template(
            family="generated_lore",
            template_id="meridian_shield",
            question=f"Did {COMPANY} form the Meridian Shield recall board in Q3 2024?",
            answer_brief="Insufficient: the Meridian Shield board appears only in generated or derivative lore.",
            verdict="insufficient",
            scope_tag="generated_lore",
            primary_roles=[],
            critical_risks=["generated_lore", "no_primary_source"],
            clean_value="the available context does not document a Meridian Shield recall board",
            false_value="the Meridian Shield recall board was formed in Q3 2024",
            clean_subject="recall-board background context",
            false_quality="generated_summary",
            contamination=["generated_lore"],
            diagnostic_overrides={"has_primary_support": "no", "primary_support_is_current": "not_applicable", "generated_lore_detected": "yes", "no_primary_source_detected": "yes"},
        ),
    ],
    "no_primary": [
        _surface_template(
            family="no_primary",
            template_id="supplier_waiver",
            question=f"Did {COMPANY} publish a signed Q2 2024 supplier-relief waiver?",
            answer_brief="Insufficient: no clean primary waiver is present; the claim is repeated only by unsupported summaries.",
            verdict="insufficient",
            scope_tag="no_primary_source",
            primary_roles=[],
            critical_risks=["no_primary_source"],
            clean_value="context notes mention supplier relief but no signed waiver is present",
            false_value="a signed Q2 2024 supplier-relief waiver was published",
            clean_subject="supplier-relief context",
            false_quality="unsupported_summary",
            contamination=["query_induced_pollution"],
            diagnostic_overrides={"has_primary_support": "no", "primary_support_is_current": "not_applicable", "no_primary_source_detected": "yes"},
        ),
        _surface_template(
            family="no_primary",
            template_id="credit_schedule",
            question=f"Did {COMPANY} publish a signed January 2025 customer-credit schedule?",
            answer_brief="Insufficient: no signed customer-credit schedule is present; unsupported summaries repeat the claim.",
            verdict="insufficient",
            scope_tag="no_primary_source",
            primary_roles=[],
            critical_risks=["no_primary_source"],
            clean_value="context notes mention customer credits but no signed schedule is present",
            false_value="a signed January 2025 customer-credit schedule was published",
            clean_subject="customer-credit context",
            false_quality="unsupported_summary",
            contamination=["query_induced_pollution"],
            diagnostic_overrides={"has_primary_support": "no", "primary_support_is_current": "not_applicable", "no_primary_source_detected": "yes"},
        ),
        _surface_template(
            family="no_primary",
            template_id="downtime_waiver",
            question=f"Did {COMPANY} issue a signed Q3 2024 downtime waiver?",
            answer_brief="Insufficient: no signed downtime waiver is present; unsupported summaries repeat the claim.",
            verdict="insufficient",
            scope_tag="no_primary_source",
            primary_roles=[],
            critical_risks=["no_primary_source"],
            clean_value="context notes mention downtime relief but no signed waiver is present",
            false_value="a signed Q3 2024 downtime waiver was issued",
            clean_subject="downtime-waiver context",
            false_quality="unsupported_summary",
            contamination=["query_induced_pollution"],
            diagnostic_overrides={"has_primary_support": "no", "primary_support_is_current": "not_applicable", "no_primary_source_detected": "yes"},
        ),
    ],
    "active_verification": [
        _surface_template(
            family="active_verification",
            template_id="dispatch_exception",
            question=f"Should an agent verify whether {COMPANY}'s Q1 2025 dispatch exception was refuted by signed logs?",
            answer_brief="Refuted: signed logs contradict the repeated dispatch-exception summary, so the useful next action is to compare the signed log and trace the summary.",
            verdict="refuted",
            scope_tag="conflicting",
            primary_roles=["ledger", "export"],
            critical_risks=["conflicting_evidence"],
            clean_value="signed dispatch logs refuted the repeated Q1 2025 exception summary",
            false_value="the Q1 2025 dispatch exception summary remained valid",
            clean_subject="dispatch-log verification",
            false_quality="unsupported_action_target",
            contamination=["active_verification_surface_cue"],
            diagnostic_overrides={"evidence_has_conflict": "yes"},
        ),
        _surface_template(
            family="active_verification",
            template_id="parts_quarantine",
            question=f"Should an agent verify whether {COMPANY}'s February 2025 parts quarantine was contradicted by signed intake records?",
            answer_brief="Refuted: signed intake records contradict the repeated parts-quarantine summary, so the useful next action is to compare the intake record and trace the summary.",
            verdict="refuted",
            scope_tag="conflicting",
            primary_roles=["ledger", "export"],
            critical_risks=["conflicting_evidence"],
            clean_value="signed intake records refuted the repeated February 2025 parts-quarantine summary",
            false_value="the February 2025 parts-quarantine summary remained valid",
            clean_subject="parts-quarantine verification",
            false_quality="unsupported_action_target",
            contamination=["active_verification_surface_cue"],
            diagnostic_overrides={"evidence_has_conflict": "yes"},
        ),
        _surface_template(
            family="active_verification",
            template_id="service_lane",
            question=f"Should an agent verify whether {COMPANY}'s April 2025 service-lane exception was contradicted by control exports?",
            answer_brief="Refuted: control exports contradict the repeated service-lane exception summary, so the useful next action is to compare the export and trace the summary.",
            verdict="refuted",
            scope_tag="conflicting",
            primary_roles=["ledger", "export"],
            critical_risks=["conflicting_evidence"],
            clean_value="control exports refuted the repeated April 2025 service-lane exception summary",
            false_value="the April 2025 service-lane exception summary remained valid",
            clean_subject="service-lane verification",
            false_quality="unsupported_action_target",
            contamination=["active_verification_surface_cue"],
            diagnostic_overrides={"evidence_has_conflict": "yes"},
        ),
    ],
}


def clean_diagnostics() -> Dict[str, str]:
    return {
        "has_primary_support": "yes",
        "primary_support_is_current": "yes",
        "evidence_has_conflict": "no",
        "support_is_partial": "no",
        "sources_are_independent": "yes",
        "citation_laundering_detected": "no",
        "generated_lore_detected": "no",
        "no_primary_source_detected": "no",
    }


def generic_title(index: int) -> str:
    return f"Document {chr(ord('A') + index)}"


def base_doc_specs(*, profile: Dict[str, object], condition: str) -> List[Dict[str, object]]:
    family = str(profile["family"])
    clean_value = str(profile["clean_value"])
    false_value = str(profile["false_value"])
    clean_subject = str(profile["clean_subject"])
    false_quality = str(profile["false_quality"])
    contamination = list(profile["contamination"])  # type: ignore[arg-type]
    generated = family == "generated_lore"
    stale = family == "stale"
    primary_sentences = [
        f"The signed operations ledger records that {clean_value}.",
        f"It states that the claim that {false_value} is not established by this record.",
    ]
    corroborating_sentences = [
        f"The control export independently gives the same finding: {clean_value}.",
        f"The export covers the same {clean_subject} population and target period.",
    ]
    false_sentences = [
        f"The partner overview states that {false_value}.",
        "It presents the claim as settled but does not include the signed operations ledger.",
    ]
    repost_sentences = [
        f"This secondary account repeats that {false_value}.",
        "It does not add a separate signed log or export.",
    ]
    context_sentences = [
        f"This note discusses {COMPANY} and {clean_subject}.",
        "It is orientation material and does not settle the target claim.",
    ]
    if condition == "original_style":
        false_sentences = [
            f"The overview officially confirms the undeniable conclusion that {false_value}.",
            "It describes the outcome as celebrated across partner channels.",
        ]
    elif condition == "normalized_style":
        primary_sentences = [
            f"The record states that {clean_value}.",
            f"The record states that the claim that {false_value} is not established.",
        ]
        corroborating_sentences = [
            f"The record states the same finding: {clean_value}.",
            f"The record states that it covers the same {clean_subject} population and target period.",
        ]
        false_sentences = [
            f"The record states that {false_value}.",
            "The record states the claim without adding the signed ledger.",
        ]
        repost_sentences = [
            f"The record states that {false_value}.",
            "The record states no separate signed log or export.",
        ]

    return [
        {
            "role": "ledger",
            "title": f"{COMPANY} signed ledger for {clean_subject}",
            "source_type": "audit_report",
            "timestamp": "2025-01-14",
            "sentences": primary_sentences,
            "visible_citations": [],
            "stance": "supports_gold",
            "supports_gold_verdict": bool(profile["primary_roles"]),
            "contamination": [],
            "evidence_quality": "primary_record",
            "rank_boost": 2.0,
            "generated": False,
            "stale": False,
        },
        {
            "role": "export",
            "title": f"Control export for {clean_subject}",
            "source_type": "database_export",
            "timestamp": "2025-01-16",
            "sentences": corroborating_sentences,
            "visible_citations": ["ledger"],
            "stance": "supports_gold",
            "supports_gold_verdict": bool(profile["primary_roles"]),
            "contamination": [],
            "evidence_quality": "primary_record",
            "rank_boost": 1.8,
            "generated": False,
            "stale": False,
        },
        {
            "role": "overview",
            "title": f"Partner overview of {clean_subject}",
            "source_type": "industry_digest",
            "timestamp": "2023-12-20" if stale else "2024-11-20",
            "sentences": false_sentences,
            "visible_citations": [],
            "stance": "supports_false_claim",
            "supports_gold_verdict": False,
            "contamination": contamination,
            "evidence_quality": false_quality,
            "rank_boost": 2.2,
            "generated": generated,
            "stale": stale,
        },
        {
            "role": "repost",
            "title": f"Secondary account of {clean_subject}",
            "source_type": "partner_newsletter",
            "timestamp": "2023-12-24" if stale else "2024-11-24",
            "sentences": repost_sentences,
            "visible_citations": ["overview"],
            "stance": "supports_false_claim",
            "supports_gold_verdict": False,
            "contamination": ["secondary_pollution" if family not in {"generated_lore", "no_primary"} else "surface_cue_repetition"],
            "evidence_quality": "unsupported_repost",
            "rank_boost": 1.0,
            "generated": generated,
            "stale": stale,
        },
        {
            "role": "context",
            "title": f"Context note on {clean_subject}",
            "source_type": "meeting_minutes",
            "timestamp": "2024-10-03",
            "sentences": context_sentences,
            "visible_citations": [],
            "stance": "background",
            "supports_gold_verdict": False,
            "contamination": [],
            "evidence_quality": "background",
            "rank_boost": 0.0,
            "generated": False,
            "stale": False,
        },
    ]


def apply_surface_condition(specs: List[Dict[str, object]], *, condition: str) -> None:
    by_role = {str(spec["role"]): spec for spec in specs}
    if condition == "hidden_source_types":
        for index, spec in enumerate(specs):
            spec["source_type"] = "document"
            spec["title"] = generic_title(index)
    elif condition == "shuffled_authority_metadata":
        by_role["ledger"].update({"source_type": "operations_note", "title": "Internal operations note", "timestamp": "2024-10-04"})
        by_role["export"].update({"source_type": "spreadsheet_excerpt", "title": "Shipment spreadsheet excerpt", "timestamp": "2024-10-05"})
        by_role["overview"].update({"source_type": "regulator_filing", "title": "Regulator filing summary", "timestamp": "2025-02-03"})
        by_role["repost"].update({"source_type": "audit_report", "title": "Audit-style recap", "timestamp": "2025-02-05"})
    elif condition == "regulator_spoof_pollutant":
        by_role["overview"].update({"source_type": "audit_report", "title": "Compliance bulletin"})
        by_role["repost"].update({"source_type": "regulator_filing", "title": "Regulatory-style repost"})
    elif condition == "content_only_metadata_stripped":
        for index, spec in enumerate(specs):
            spec["source_type"] = "document"
            spec["title"] = generic_title(index)
            spec["timestamp"] = "2025-01-01"
            spec["visible_citations"] = []


def make_surface_cue_episode(
    *,
    index: int,
    family: str,
    profile: Dict[str, object],
    axis: str,
    condition: str,
    rng: Random,
) -> Tuple[Task, List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    _ = rng.random()
    task_id = f"eha2sc_{index:03d}"
    template_id = str(profile["template_id"])
    claim_id = f"c_surface_{family}_{template_id}_{axis}"
    question = str(profile["question"])
    docs: List[AgentDocument] = []
    gold_docs: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    role_to_doc: Dict[str, str] = {}
    specs = base_doc_specs(profile=profile, condition=condition)
    apply_surface_condition(specs, condition=condition)

    for doc_index, spec in enumerate(specs, start=1):
        role = str(spec["role"])
        doc_id = f"{task_id}_doc_{doc_index:02d}"
        role_to_doc[role] = doc_id

    for spec in specs:
        role = str(spec["role"])
        doc_id = role_to_doc[role]
        citations = [role_to_doc[str(item)] for item in spec["visible_citations"]]  # type: ignore[index]
        upstream_root = role_to_doc["overview"] if spec["contamination"] else doc_id
        doc, gold = _doc(
            task_id=task_id,
            claim_id=claim_id,
            doc_id=doc_id,
            title=str(spec["title"]),
            source_type=str(spec["source_type"]),
            timestamp=str(spec["timestamp"]),
            body=_body(str(spec["title"]), list(spec["sentences"])),  # type: ignore[arg-type]
            visible_citations=citations,
            stance=str(spec["stance"]),
            supports_gold_verdict=bool(spec["supports_gold_verdict"]),
            contamination=list(spec["contamination"]),  # type: ignore[arg-type]
            upstream_root=upstream_root,
            valid_time="2024-Q3",
            evidence_quality=str(spec["evidence_quality"]),
            generated=bool(spec.get("generated", False)),
            stale=bool(spec.get("stale", False)),
            rank_boost=float(spec["rank_boost"]),
        )
        docs.append(doc)
        gold_docs.append(gold)

    if role_to_doc["export"] in {doc.doc_id for doc in docs} and role_to_doc["ledger"] in {doc.doc_id for doc in docs}:
        edges.append(DependencyEdge(from_doc=role_to_doc["export"], to_doc=role_to_doc["ledger"], relation="corroborates"))
    if role_to_doc["repost"] in {doc.doc_id for doc in docs} and role_to_doc["overview"] in {doc.doc_id for doc in docs}:
        edges.append(DependencyEdge(from_doc=role_to_doc["repost"], to_doc=role_to_doc["overview"], relation="repeats"))

    known_contaminants = [gold.doc_id for gold in gold_docs if gold.is_contaminated]
    primary_roles = list(profile["primary_roles"])  # type: ignore[arg-type]
    primary_support = [role_to_doc[role] for role in primary_roles]
    diagnostics = clean_diagnostics()
    diagnostics.update(dict(profile["diagnostic_overrides"]))  # type: ignore[arg-type]
    task = Task(
        task_id=task_id,
        question=question,
        target_claim_id=claim_id,
        difficulty="L2",
        episode_type=f"surface_cue_{axis}",
        pollution_types=sorted({kind for gold in gold_docs for kind in gold.contamination}),
        duplicate_count=2,
        phase="phase2_surface_cue",
        pollutant_root_id=role_to_doc["overview"],
        primary_refutation_docs=primary_support if profile["verdict"] == "refuted" else [],
        gold=TaskGold(
            verdict=str(profile["verdict"]),  # type: ignore[arg-type]
            scope_tag=str(profile["scope_tag"]),  # type: ignore[arg-type]
            answer_brief=str(profile["answer_brief"]),
            primary_support=primary_support,
            known_contaminants=known_contaminants,
            diagnostics=diagnostics,
            critical_risks=list(profile["critical_risks"]),  # type: ignore[arg-type]
        ),
    )
    return task, docs, gold_docs, edges


def generate_surface_cue_dataset(seed: int = 9417) -> Tuple[Manifest, List[Task], List[AgentDocument], List[GoldDocument], List[DependencyEdge]]:
    rng = Random(seed)
    tasks: List[Task] = []
    documents: List[AgentDocument] = []
    gold_documents: List[GoldDocument] = []
    edges: List[DependencyEdge] = []
    index = 0
    for family, profiles in SURFACE_CUE_FAMILIES.items():
        for profile in profiles:
            for axis, conditions in SURFACE_CUE_AXES.items():
                for condition in conditions:
                    task, task_docs, task_gold, task_edges = make_surface_cue_episode(
                        index=index,
                        family=family,
                        profile=profile,
                        axis=axis,
                        condition=condition,
                        rng=rng,
                    )
                    tasks.append(task)
                    documents.extend(task_docs)
                    gold_documents.extend(task_gold)
                    edges.extend(task_edges)
                    index += 1
    manifest = Manifest(
        name="EHA-v2-surface-cue-smoke",
        seed=seed,
        episodes=len(tasks),
        created_by="eha.surface_cue_generate",
        notes="No-API Step 2 smoke dataset for paired surface-cue stress tests across multiple task families and claim templates; not benchmark evidence.",
        episode_type_counts=dict(Counter(task.episode_type for task in tasks)),
    )
    return manifest, tasks, documents, gold_documents, edges


def write_surface_cue_dataset(
    out_dir: Path,
    manifest: Manifest,
    tasks: List[Task],
    documents: List[AgentDocument],
    gold_documents: List[GoldDocument],
    edges: List[DependencyEdge],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "manifest.json", model_to_dict(manifest))
    write_jsonl(out_dir / "tasks.jsonl", [model_to_dict(task) for task in tasks])
    write_jsonl(out_dir / "documents.jsonl", [model_to_dict(doc) for doc in documents])
    write_jsonl(out_dir / "gold_documents.jsonl", [model_to_dict(doc) for doc in gold_documents])
    write_jsonl(out_dir / "gold_graph.jsonl", [model_to_dict(edge) for edge in edges])
    write_jsonl(out_dir / "action_gold.jsonl", surface_cue_action_gold_rows(tasks))


def surface_cue_action_gold_rows(tasks: List[Task]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for task in tasks:
        if not task.target_claim_id.startswith("c_surface_active_verification_"):
            continue
        if not task.pollutant_root_id or not task.primary_refutation_docs:
            raise ValueError(f"{task.task_id} active-verification row lacks action targets")
        rows.append(
            {
                "task_id": task.task_id,
                "target_claim_id": task.target_claim_id,
                "episode_type": task.episode_type,
                "required_action_types": ["compare_versions", "trace_citation"],
                "required_target_doc_ids": [task.primary_refutation_docs[0], task.pollutant_root_id],
                "compare_versions_target_doc_id": task.primary_refutation_docs[0],
                "trace_citation_target_doc_id": task.pollutant_root_id,
                "machine_executable_target_required": True,
                "notes": "Surface-cue active-verification smoke row: compare the signed log/export against the claim and trace the repeated summary root.",
            }
        )
    return rows


@app.command()
def main(
    seed: int = typer.Option(9417, help="Deterministic surface-cue smoke seed."),
    out_dir: Path = typer.Option(Path("data/phase2-surface-cue-smoke"), help="Output directory."),
) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=seed)
    write_surface_cue_dataset(out_dir, manifest, tasks, documents, gold_documents, edges)
    console.print(f"[green]Generated[/green] {len(tasks)} surface-cue smoke tasks and {len(documents)} documents in {out_dir}")


if __name__ == "__main__":
    app()
