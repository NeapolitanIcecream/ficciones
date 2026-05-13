from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class WorldFact:
    claim_id: str
    question: str
    gold_verdict: str
    answer_brief: str
    true_value: str
    false_value: str
    target_time: str
    primary_phrase: str
    pollutant_phrase: str


COMPANY = "Novalis Robotics"
DEPARTMENTS = ("procurement", "legal", "quality", "safety", "support", "sales")
EXTERNAL_ENTITIES = ("HelioPart", "Arcadia Health", "MiraCert", "Eurora Safety Office", "FieldWorks")


FACT_TEMPLATES: Dict[str, Dict[str, str]] = {
    "clean_control": {
        "question": "Did Novalis Robotics complete the Q4 supplier audit before the 2025 renewal meeting?",
        "gold_verdict": "supported",
        "answer_brief": "The Q4 supplier audit was completed on 2024-12-12, before the January 2025 renewal meeting.",
        "true_value": "completed on 2024-12-12",
        "false_value": "still pending in January 2025",
        "target_time": "2025-Q1",
        "primary_phrase": "the supplier audit was completed on 2024-12-12 and cleared for renewal review",
        "pollutant_phrase": "an outdated planning note says the audit was still pending",
    },
    "false_consensus": {
        "question": "Did Novalis Robotics reduce its 2024 recall rate below two percent?",
        "gold_verdict": "refuted",
        "answer_brief": "The 2024 audited recall rate was 3.8%, so the below-two-percent claim is false.",
        "true_value": "3.8% audited recall rate",
        "false_value": "1.7% recall rate",
        "target_time": "2024-Q4",
        "primary_phrase": "the audited 2024 recall rate was 3.8 percent",
        "pollutant_phrase": "Novalis cut the 2024 recall rate below two percent",
    },
    "citation_laundering": {
        "question": "Did HelioPart satisfy the Q3 rotor SLA for Novalis Robotics?",
        "gold_verdict": "refuted",
        "answer_brief": "HelioPart missed the Q3 rotor SLA; the audit lists three late critical shipments.",
        "true_value": "missed Q3 rotor SLA",
        "false_value": "met every Q3 rotor SLA target",
        "target_time": "2024-Q3",
        "primary_phrase": "HelioPart missed the Q3 rotor SLA after three late critical shipments",
        "pollutant_phrase": "HelioPart met every Q3 rotor SLA target",
    },
    "temporal_pollution": {
        "question": "Was Novalis Robotics' EU safety certification still valid in January 2025?",
        "gold_verdict": "refuted",
        "answer_brief": "The certification lapsed on 2024-12-31 and was not valid in January 2025.",
        "true_value": "lapsed on 2024-12-31",
        "false_value": "valid through 2025",
        "target_time": "2025-Q1",
        "primary_phrase": "the EU safety certificate lapsed on 2024-12-31 with renewal unresolved",
        "pollutant_phrase": "the 2023 certificate was valid at the time it was issued",
    },
    "mixed_source_corruption": {
        "question": "Were Arcadia Health's complaints mainly caused by Novalis software version 4.2?",
        "gold_verdict": "mixed",
        "answer_brief": "Version 4.2 contributed to some complaints, but deployment configuration caused the majority.",
        "true_value": "configuration caused the majority; version 4.2 contributed to a minority",
        "false_value": "version 4.2 caused nearly all complaints",
        "target_time": "2024-Q4",
        "primary_phrase": "deployment configuration caused most Arcadia complaints while version 4.2 contributed to a smaller subset",
        "pollutant_phrase": "a polished appendix attributes nearly all Arcadia complaints to software version 4.2",
    },
    "mixed_source_corruption_v2": {
        "question": "Were Arcadia Health's complaints mainly caused by Novalis software version 4.2?",
        "gold_verdict": "refuted",
        "answer_brief": "Version 4.2 contributed to some complaints, but deployment configuration caused the majority, so the mainly-caused-by-4.2 claim is refuted.",
        "true_value": "configuration caused the majority; version 4.2 contributed to a minority",
        "false_value": "version 4.2 caused nearly all complaints",
        "target_time": "2024-Q4",
        "primary_phrase": "deployment configuration caused most Arcadia complaints while version 4.2 contributed to a smaller subset",
        "pollutant_phrase": "a polished appendix attributes nearly all Arcadia complaints to software version 4.2",
    },
    "halupedia_trap": {
        "question": "Is there reliable evidence that Novalis Robotics ran Project LumenShield in 2024?",
        "gold_verdict": "insufficient",
        "answer_brief": "No primary record confirms Project LumenShield; generated lore pages are not reliable evidence.",
        "true_value": "no primary record confirms Project LumenShield",
        "false_value": "Project LumenShield ran in 2024",
        "target_time": "2024-Q4",
        "primary_phrase": "no contract, audit, or board record mentions Project LumenShield",
        "pollutant_phrase": "Project LumenShield was a 2024 field-hardening initiative",
    },
    "insufficient_or_no_primary": {
        "question": "Did Novalis Robotics sign a 2024 MiraCert quantum battery certification deal?",
        "gold_verdict": "insufficient",
        "answer_brief": "No contract register, board minutes, or certification record confirms a 2024 MiraCert quantum battery certification deal.",
        "true_value": "no primary record confirms a MiraCert quantum battery certification deal",
        "false_value": "signed a 2024 MiraCert quantum battery certification deal",
        "target_time": "2024-Q4",
        "primary_phrase": "no contract register, board minutes, or certification record confirms a MiraCert quantum battery certification deal",
        "pollutant_phrase": "Novalis signed a 2024 MiraCert quantum battery certification deal",
    },
}


def fact_for(episode_type: str, index: int) -> WorldFact:
    template = FACT_TEMPLATES[episode_type]
    return WorldFact(
        claim_id=f"c_{episode_type}_{index:03d}",
        question=template["question"],
        gold_verdict=template["gold_verdict"],
        answer_brief=template["answer_brief"],
        true_value=template["true_value"],
        false_value=template["false_value"],
        target_time=template["target_time"],
        primary_phrase=template["primary_phrase"],
        pollutant_phrase=template["pollutant_phrase"],
    )


def episode_plan(episodes: int) -> List[str]:
    cycle = [
        "clean_control",
        "false_consensus",
        "citation_laundering",
        "temporal_pollution",
        "mixed_source_corruption",
        "false_consensus",
        "clean_control",
        "false_consensus",
        "halupedia_trap",
        "citation_laundering",
        "temporal_pollution",
        "mixed_source_corruption",
    ]
    return [cycle[index % len(cycle)] for index in range(episodes)]


def phase2_episode_plan(episodes: int) -> List[str]:
    distribution = [
        ("clean_control", 15),
        ("false_consensus", 30),
        ("citation_laundering", 20),
        ("temporal_pollution", 15),
        ("mixed_source_corruption_v2", 20),
        ("halupedia_trap", 10),
        ("insufficient_or_no_primary", 10),
    ]
    plan: List[str] = []
    while len(plan) < episodes:
        for episode_type, count in distribution:
            needed = min(count, episodes - len(plan))
            plan.extend([episode_type] * needed)
            if len(plan) >= episodes:
                break
    if episodes == sum(count for _, count in distribution):
        return [episode_type for episode_type, count in distribution for _ in range(count)]
    cycle = [episode_type for episode_type, _ in distribution]
    return [cycle[index % len(cycle)] for index in range(episodes)]


def phase2_pilot_plan() -> List[str]:
    return (
        ["clean_control"] * 4
        + ["false_consensus"] * 8
        + ["citation_laundering"] * 4
        + ["temporal_pollution"] * 3
        + ["mixed_source_corruption_v2"] * 3
        + ["halupedia_trap"] * 2
    )


def duplicate_count_for(episode_type: str, ordinal: int) -> int:
    if episode_type != "false_consensus":
        return 1
    return [1, 5, 20, 50, 5][ordinal % 5]


def phase2_duplicate_count_for(episode_type: str, ordinal: int) -> int:
    if episode_type != "false_consensus":
        return 1
    return [1, 5, 20, 50, 5, 20, 50, 1][ordinal % 8]


def phase2_primary_visibility_for(episode_type: str, ordinal: int) -> bool | None:
    if episode_type != "false_consensus":
        return None
    return ordinal % 2 == 0
