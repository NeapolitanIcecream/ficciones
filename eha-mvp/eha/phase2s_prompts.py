from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Sequence

from .phase2r_prompts import PHASE2R_SCOPE_TAGS
from .prompts import format_document
from .schemas import AgentDocument, EvidenceDiagnostics, Phase2Prediction, Phase2SPrediction, ToolCall, VerificationLedgerEntry


DIAGNOSTIC_FIELDS = [
    "has_primary_support",
    "primary_support_is_current",
    "evidence_has_conflict",
    "support_is_partial",
    "sources_are_independent",
    "citation_laundering_detected",
    "generated_lore_detected",
    "no_primary_source_detected",
]
ENVIRONMENT_OBSERVATION_FIELDS = [
    "visible_stale_or_superseded_material",
    "visible_conflicting_material",
    "visible_generated_or_synthetic_lore",
    "visible_reposts_or_same_root_repetition",
    "visible_citation_chain_problem",
    "visible_partial_or_scope_limited_support",
]
CRITICAL_RISKS = [
    "stale_evidence",
    "conflicting_evidence",
    "generated_lore",
    "no_primary_source",
    "false_consensus",
    "citation_laundering",
    "partial_support",
]
LEDGER_RISKS = ["temporal_staleness", "source_independence", "citation_chain", "generated_lore", "primary_support"]
LEDGER_METHODS = ["read_docs", "trace_citation", "compare_versions", "request_primary_record", "search_contradictions"]
LEDGER_EFFECTS = ["supports", "weakens", "refutes", "makes_insufficient"]
ROUTING_TOOLS = ["trace_citation", "request_primary_record", "compare_versions", "search_contradictions"]
PHASE2S_DIAGNOSTIC_PROMPTS = (
    "evidence_diagnostics_v1",
    "evidence_diagnostics_v2",
    "evidence_diagnostics_v3",
    "evidence_diagnostics_v4",
    "evidence_diagnostics_v5",
    "evidence_diagnostics_v6",
    "evidence_diagnostics_v7",
    "evidence_diagnostics_v8_structural",
    "evidence_diagnostics_v9_structural_recall",
    "evidence_diagnostics_v10_structural_contract",
    "evidence_diagnostics_v11_role_disciplined_contract",
    "evidence_diagnostics_v12_critical_risk_contract",
)
STRUCTURAL_DIAGNOSTIC_PROMPTS = {
    "evidence_diagnostics_v8_structural",
    "evidence_diagnostics_v9_structural_recall",
    "evidence_diagnostics_v10_structural_contract",
    "evidence_diagnostics_v11_role_disciplined_contract",
    "evidence_diagnostics_v12_critical_risk_contract",
}


def phase2s_prediction_json_schema(prompt: str = "evidence_diagnostics_v1") -> Dict[str, Any]:
    required = [
        "claim_verdict",
        "confidence",
        "evidence_diagnostics",
        "critical_risks",
        "supporting_evidence",
        "rejected_evidence",
        "verification_ledger",
        "answer",
    ]
    properties: Dict[str, Any] = {
        "claim_verdict": {"type": "string", "enum": ["supported", "refuted", "insufficient"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence_diagnostics": {
            "type": "object",
            "additionalProperties": False,
            "required": DIAGNOSTIC_FIELDS,
            "properties": {
                "has_primary_support": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                "primary_support_is_current": {"type": "string", "enum": ["yes", "no", "not_applicable", "uncertain"]},
                "evidence_has_conflict": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                "support_is_partial": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                "sources_are_independent": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                "citation_laundering_detected": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                "generated_lore_detected": {"type": "string", "enum": ["yes", "no", "uncertain"]},
                "no_primary_source_detected": {"type": "string", "enum": ["yes", "no", "uncertain"]},
            },
        },
        "critical_risks": {"type": "array", "items": {"type": "string", "enum": CRITICAL_RISKS}},
        "supporting_evidence": {"type": "array", "items": {"type": "string"}},
        "rejected_evidence": {"type": "array", "items": {"type": "string"}},
        "verification_ledger": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["risk_checked", "method", "evidence", "finding", "effect_on_verdict"],
                "properties": {
                    "risk_checked": {"type": "string", "enum": LEDGER_RISKS},
                    "method": {"type": "string", "enum": LEDGER_METHODS},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "finding": {"type": "string"},
                    "effect_on_verdict": {"type": "string", "enum": LEDGER_EFFECTS},
                },
            },
        },
        "answer": {"type": "string"},
    }
    if prompt in STRUCTURAL_DIAGNOSTIC_PROMPTS:
        required.insert(2, "environment_observations")
        properties["environment_observations"] = {
            "type": "object",
            "additionalProperties": False,
            "required": ENVIRONMENT_OBSERVATION_FIELDS,
            "properties": {field: {"type": "string", "enum": ["yes", "no", "uncertain"]} for field in ENVIRONMENT_OBSERVATION_FIELDS},
        }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


def phase2s_routing_json_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["tool_routing_diagnosis", "chosen_tools"],
        "properties": {
            "tool_routing_diagnosis": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "is_current_status_question",
                    "does_evidence_contain_dates_or_versions",
                    "is_temporal_comparison_required",
                    "reason",
                ],
                "properties": {
                    "is_current_status_question": {"type": "boolean"},
                    "does_evidence_contain_dates_or_versions": {"type": "boolean"},
                    "is_temporal_comparison_required": {"type": "boolean"},
                    "reason": {"type": "string"},
                },
            },
            "chosen_tools": {
                "type": "array",
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["tool", "why", "args"],
                    "properties": {
                        "tool": {"type": "string", "enum": ROUTING_TOOLS},
                        "why": {"type": "string"},
                        "args": {"type": "object"},
                    },
                },
            },
        },
    }


def render_documents(label: str, documents: Sequence[AgentDocument]) -> str:
    rendered = "\n\n---\n\n".join(format_document(doc) for doc in documents)
    return f"{label}:\n{rendered}" if rendered else f"{label}: none"


def phase2s_system_prompt(prompt: str = "evidence_diagnostics_v1") -> str:
    if prompt not in PHASE2S_DIAGNOSTIC_PROMPTS:
        prompt = "evidence_diagnostics_v1"
    lines = [
        f"You are an {prompt.replace('_', '-')} verification agent in a synthetic benchmark.",
        "All entities are fictional. Use only provided documents and tool results.",
        "Separate claim correctness from evidence-risk diagnosis.",
        "Use evidence_diagnostics as multi-label evidence state, not as one exclusive scope tag.",
    ]
    if prompt in {
        "evidence_diagnostics_v2",
        "evidence_diagnostics_v3",
        "evidence_diagnostics_v4",
        "evidence_diagnostics_v5",
        "evidence_diagnostics_v6",
        "evidence_diagnostics_v7",
        "evidence_diagnostics_v8_structural",
        "evidence_diagnostics_v9_structural_recall",
        "evidence_diagnostics_v10_structural_contract",
        "evidence_diagnostics_v11_role_disciplined_contract",
        "evidence_diagnostics_v12_critical_risk_contract",
    }:
        lines.extend(
            [
                "First decide whether a current primary record directly supports or refutes the target claim; write diagnostics after that verdict decision.",
                "Do not let generic risk labels reverse a supported claim when clean current primary evidence directly supports the target claim.",
                "Only mark no_primary_source when no provided document or tool result is a primary record directly about the target claim.",
                "Only mark partial_support when you can name the specific claim component that remains unsupported.",
                "Critical risks must be verdict-relevant: they must change the verdict, block support, or require explicit rejection of a document.",
                "Use low-severity uncertainty in verification_ledger rather than inflating critical_risks.",
                "Prioritize clean current primary documents in supporting_evidence and put stale, generated, same-root, or contradicted documents in rejected_evidence.",
            ]
        )
        if prompt in {
            "evidence_diagnostics_v3",
            "evidence_diagnostics_v4",
            "evidence_diagnostics_v5",
            "evidence_diagnostics_v6",
            "evidence_diagnostics_v7",
            "evidence_diagnostics_v8_structural",
            "evidence_diagnostics_v9_structural_recall",
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            lines.extend(
                [
                    "Risk-to-verdict override rules:",
                    "If stale_evidence is critical because the only apparent support is superseded or obsolete, the claim_verdict must not be supported.",
                    "If conflicting_evidence includes clean current evidence that contradicts the target claim, prefer refuted over supported.",
                    "If citation_laundering means the citation chain does not actually support the target claim, use refuted when it points against the claim and insufficient when support is merely missing.",
                    "If partial_support is critical, the claim_verdict should be insufficient unless another clean primary document supports every target-claim component.",
                    "Generated lore or no primary source cannot support the target claim; use insufficient unless clean primary evidence elsewhere directly supports it.",
                    "A clean current primary support can override low-severity background risk, but cannot override stale, conflict, citation-laundering, partial-support, generated-lore, or no-primary critical risks that block the target claim.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v4",
            "evidence_diagnostics_v5",
            "evidence_diagnostics_v6",
            "evidence_diagnostics_v7",
            "evidence_diagnostics_v8_structural",
            "evidence_diagnostics_v9_structural_recall",
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            lines.extend(
                [
                    "Strict no-primary rule:",
                    "A primary record can refute the target claim or show that support is insufficient; that is still primary evidence, not no_primary_source.",
                    "Do not mark no_primary_source when a current primary record, signed record, audit report, database export, or other direct primary document is provided for the target question.",
                    "Only mark no_primary_source when every available claim-bearing document is generated, secondary, a repost, background context, or an unsupported summary and no direct primary record is visible.",
                ]
            )
        if prompt in {"evidence_diagnostics_v5", "evidence_diagnostics_v6", "evidence_diagnostics_v7"}:
            lines.extend(
                [
                    "Polluted-environment risk reporting:",
                    "Critical risks are not only verdict blockers; include visible claim-bearing pollution that explains rejected evidence or tool use even when clean primary evidence decides the verdict.",
                    "If repeated documents share the same root claim, cite the same upstream source, or copy the same claim phrasing, include false_consensus and set sources_are_independent=no.",
                    "If a citation chain, official appendix, or reposted summary carries a claim that its cited source does not independently establish, include citation_laundering and set citation_laundering_detected=yes.",
                    "If a stale or superseded document is visible and claim-bearing, include stale_evidence even when a current primary record resolves the final verdict.",
                    "Do not put polluted documents in supporting_evidence; report them in rejected_evidence and ledger entries with effect_on_verdict=weakens or refutes.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v6",
            "evidence_diagnostics_v7",
            "evidence_diagnostics_v8_structural",
            "evidence_diagnostics_v9_structural_recall",
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            lines.extend(
                [
                    "Precision and verdict-boundary repair:",
                    "For refuted verdicts, supporting_evidence must include clean primary or direct refuting evidence; if no such evidence is visible or returned by tools, use insufficient.",
                    "When request_primary_record returns no documents and all claim-bearing evidence is generated, secondary, reposted, or unsupported, the verdict should be insufficient rather than refuted.",
                    "Do not mark generated_lore_detected=yes merely because a source is secondary, repeated, or stale; reserve generated_lore for fictional/generated/wiki-like unsupported entities or pages with no primary basis.",
                    "Do not mark partial_support unless a specific target-claim component is supported and a different target-claim component is missing.",
                    "Use critical_risks for risks that explain the verdict or required tool use; background rejected evidence can stay in rejected_evidence and the ledger without every possible risk label.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v7",
            "evidence_diagnostics_v8_structural",
            "evidence_diagnostics_v9_structural_recall",
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            lines.extend(
                [
                    "Fine-grained diagnostic label calibration:",
                    "Do not mark stale_evidence for an ordinary pre-event planning note when later clean primary records settle the deadline or completion claim; reserve stale_evidence for current-validity, lapsed, expired, active-status, or version-history claims where an old record appears current but is superseded.",
                    "Do not mark citation_laundering merely because several summaries cite the same root; that is false_consensus. Use citation_laundering when an official appendix, citation target, citation chain, or cited source is visible and fails to establish the claim it is used for.",
                    "Do not mark false_consensus just because a few rejected summaries repeat one claim while clean primary records are visible and decisive. Mark it when same-root repetition dominates the available evidence or explains why tools/rejection were necessary.",
                    "Generated_lore means unsupported generated/wiki-like pages or invented named projects, deals, programs, certifications, or entities with no primary basis; no_primary_source alone is for ordinary claims missing primary support.",
                    "Partial_support applies when clean evidence supports a weaker component but not the target quantifier, scope, or causal strength, such as 'some contribution' versus 'main cause'.",
                ]
            )
        if prompt in STRUCTURAL_DIAGNOSTIC_PROMPTS:
            lines.extend(
                [
                    "Structural observation/risk split:",
                    "environment_observations may acknowledge all visible pollution, including correctly rejected documents.",
                    "critical_risks must stay sparse and verdict-relevant: include only risks that change the verdict, block support, or require specific tool use.",
                    "A visible rejected pollutant can be an environment observation without being a critical risk.",
                    "Clean controls with clean current primary support should normally keep critical_risks empty even when reposts or pollutants are visible and rejected.",
                    "Same-root repetition belongs in visible_reposts_or_same_root_repetition; only add false_consensus when it dominates the evidence or affects support/tooling.",
                    "Citation-laundering requires a visible citation chain, appendix, or cited target that fails to establish the claim; do not use it for ordinary repost repetition or generated lore alone.",
                    "Partial support should be a critical risk when the clean evidence supports only a weaker scope, quantifier, or causal claim than the target.",
                ]
            )
        if prompt == "evidence_diagnostics_v9_structural_recall":
            lines.extend(
                [
                    "Structural recall repair:",
                    "Do not omit a true critical risk just because the same condition is also recorded in environment_observations.",
                    "If same-root repetition dominates available evidence, creates an illusion of independent support, or leaves no clean primary support, include false_consensus in critical_risks.",
                    "If a visible citation target, appendix, or citation chain is used as support but fails to establish the target claim, include citation_laundering in critical_risks even when the final verdict is refuted by primary evidence.",
                    "If clean evidence supports only a weaker claim than the requested quantifier, scope, comparison, or causal strength, include partial_support rather than conflicting_evidence.",
                    "If a true critical risk blocks support, put the corresponding diagnostic field to yes and include the risk in critical_risks; observation-only is reserved for rejected background pollution that does not affect support.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            lines.extend(
                [
                    "Structural critical-risk contract:",
                    "Use environment_observations for visible conditions, but use this decision table for critical_risks.",
                    "false_consensus: include only when repeated same-root summaries dominate apparent support or create an illusion of independent support; do not use it for citation-chain failures, generated/no-primary pages, or mixed-source partial-support rows.",
                    "citation_laundering: include only when a visible cited target, appendix, or citation chain is used as support and the cited target fails to establish the target claim; do not use it for ordinary same-root repetition, generated lore, or corrupted mixed-source tables.",
                    "partial_support: include when clean evidence supports a weaker component but not the requested scope, quantifier, comparison, or causal strength; do not replace it with conflicting_evidence or citation_laundering unless a clean contradiction or failed citation chain is also visible.",
                    "stale_evidence: include for current-validity or version-history claims where old material is superseded; do not turn ordinary stale pollution into conflicting_evidence.",
                    "generated_lore: include for generated/wiki-like or invented entities with no primary basis; pair it with no_primary_source when no direct primary record is visible.",
                    "no_primary_source: include only when no current direct primary record is visible; do not use it when primary records refute or partially support the target claim.",
                    "conflicting_evidence: include only for clean primary or direct evidence that contradicts the target claim, not merely for stale, partial, generated, or citation-laundered support.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            lines.extend(
                [
                    "Structural evidence-role discipline contract:",
                    "Apply the v10 critical-risk decision table, then enforce this supporting_evidence hard gate.",
                    "supporting_evidence may contain only clean documents that directly support the final verdict: clean support for supported verdicts, or clean primary/direct refuting evidence for refuted verdicts.",
                    "Never put pollutant roots, reposts, generated/wiki-like pages, unsupported summaries, failed citation targets, stale superseded records, corrupted appendices, or no-primary documents in supporting_evidence.",
                    "If no clean document directly supports the final verdict, leave supporting_evidence empty; do not cite the document that is being rejected as support for insufficiency or refutation.",
                    "Put every same-root, generated, stale, failed-citation, corrupted, or unsupported claim-bearing document in rejected_evidence or ledger evidence, not supporting_evidence.",
                    "For repeated same-root claims contradicted by clean primary evidence, include both false_consensus and conflicting_evidence as critical risks.",
                    "For visible failed citation chains contradicted by clean primary evidence, include both citation_laundering and conflicting_evidence as critical risks.",
                    "For generated/wiki-like or invented no-primary rows, use generated_lore plus no_primary_source, keep false_consensus and citation_laundering out of critical_risks, and leave supporting_evidence empty.",
                    "For ordinary no-primary rows without generated lore, use no_primary_source only, reject all claim-bearing secondary/repost documents, and leave supporting_evidence empty.",
                    "For temporal supersession rows, use stale_evidence rather than conflicting_evidence unless two clean current primary sources directly disagree.",
                    "For mixed-source or corrupted-table rows where clean evidence supports only a weaker scope, quantity, comparison, or causal claim, use partial_support rather than conflicting_evidence or citation_laundering.",
                ]
            )
        if prompt == "evidence_diagnostics_v12_critical_risk_contract":
            lines.extend(
                [
                    "Critical-risk repair audit contract:",
                    "Before finalizing critical_risks, compare each candidate label against a positive rule and a negative rule.",
                    "false_consensus positive: same-root or copied summaries dominate apparent support or hide absence of clean primary support; negative: repeated rejected pollutants are visible but clean primary evidence is decisive.",
                    "citation_laundering positive: a visible cited target, appendix, or chain is used as support and its cited target fails to establish the claim; negative: ordinary same-root reposting, generated lore, or unrelated background citations.",
                    "partial_support positive: clean evidence supports a weaker scope, quantity, comparison, or causal relation than the target; negative: clean evidence directly refutes the target or no clean primary exists at all.",
                    "conflicting_evidence positive: clean primary or direct evidence contradicts the target claim; negative: the row is only stale, partial, generated, no-primary, or citation-laundered without clean contradiction.",
                    "stale_evidence positive: superseded evidence is being used for a current-status or version-history claim; negative: an old rejected pollutant appears while clean current primary support decides the verdict.",
                    "After applying the rules, remove any critical_risks label whose only basis is a visible rejected pollutant already captured by environment_observations.",
                    "The target for this contract is exact critical-risk rows, not maximal risk recall.",
                ]
            )
    else:
        lines.append(
            "Mark every critical risk that is visible or unresolved: stale_evidence, conflicting_evidence, generated_lore, no_primary_source, false_consensus, citation_laundering, partial_support."
        )
    lines.extend(
        [
            "Use verification_ledger to tie risks, methods, evidence IDs, and verdict effects together.",
            "Use bare document IDs only in evidence arrays and ledger evidence.",
            "If no primary source supports the target claim, prefer insufficient over overclaiming.",
            "Return one JSON object matching this schema:",
            json.dumps(phase2s_prediction_json_schema(prompt), ensure_ascii=False),
        ]
    )
    return "\n".join(lines)


def build_phase2s_messages(
    question: str,
    documents: Sequence[AgentDocument],
    tool_results: Sequence[Mapping[str, Any]] | None = None,
    prompt: str = "evidence_diagnostics_v1",
) -> List[Dict[str, str]]:
    diagnostic_rules = [
        "- Stale: old records or superseded versions are not current support.",
        "- Conflict: clean evidence refutes or contradicts the apparent support.",
        "- Generated lore: wiki-style/generated pages cannot substitute for primary evidence.",
        "- No primary: secondary summaries alone are insufficient for claim-level support.",
        "- Citation laundering: a citation chain can point to irrelevant or unsupported sources.",
        "- False consensus: repeated same-root summaries are not independent support.",
        "- Partial support: a document may support a weaker claim while not supporting the target claim.",
    ]
    if prompt in {
        "evidence_diagnostics_v2",
        "evidence_diagnostics_v3",
        "evidence_diagnostics_v4",
        "evidence_diagnostics_v5",
        "evidence_diagnostics_v6",
        "evidence_diagnostics_v7",
        "evidence_diagnostics_v8_structural",
        "evidence_diagnostics_v9_structural_recall",
        "evidence_diagnostics_v10_structural_contract",
        "evidence_diagnostics_v11_role_disciplined_contract",
        "evidence_diagnostics_v12_critical_risk_contract",
    }:
        diagnostic_rules.extend(
            [
                "- Claim-first calibration: decide the target claim verdict from current primary support before adding risk labels.",
                "- No-primary is a last-resort diagnostic; do not use it when a relevant current primary record is present.",
                "- Partial support requires a named missing claim component, not merely generic caution.",
                "- Risk labels cannot compensate for an unsupported verdict; verdict and diagnostics must agree.",
            ]
        )
        if prompt in {
            "evidence_diagnostics_v3",
            "evidence_diagnostics_v4",
            "evidence_diagnostics_v5",
            "evidence_diagnostics_v6",
            "evidence_diagnostics_v7",
            "evidence_diagnostics_v8_structural",
            "evidence_diagnostics_v9_structural_recall",
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            diagnostic_rules.extend(
                [
                    "- Generated lore or no primary source cannot be supporting evidence for the target claim.",
                    "- Stale support, clean contradiction, unsupported citation chains, and partial support must change the verdict away from supported when they block the target claim.",
                    "- Use refuted for clean contradiction; use insufficient for missing current primary support, partial support, or unsupported citation chains.",
                    "- Keep the risk labels that explain the verdict; do not drop stale/conflict/partial/citation-laundering risks just to preserve a supported verdict.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v4",
            "evidence_diagnostics_v5",
            "evidence_diagnostics_v6",
            "evidence_diagnostics_v7",
            "evidence_diagnostics_v8_structural",
            "evidence_diagnostics_v9_structural_recall",
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            diagnostic_rules.extend(
                [
                    "- Strict no-primary rule: do not mark no_primary_source when a visible primary document addresses the target question, even if that primary document refutes the claim or makes support insufficient.",
                    "- Mark no_primary_source only when there is no current primary record, audit report, signed record, database export, or direct primary document about the target claim.",
                ]
            )
        if prompt in {"evidence_diagnostics_v5", "evidence_diagnostics_v6", "evidence_diagnostics_v7"}:
            diagnostic_rules.extend(
                [
                    "- Polluted-environment risk reporting: keep risk labels for visible claim-bearing pollution even when clean primary evidence resolves the final verdict.",
                    "- False consensus: repeated same-root summaries, copied claim phrasing, or documents citing one upstream root are not independent support; mark false_consensus and sources_are_independent=no.",
                    "- Citation laundering: if an appendix, summary, repost, or citation chain appears to support the claim but its cited source is missing, stale, corrupted, or does not establish the target claim, mark citation_laundering_detected=yes.",
                    "- Stale evidence: if obsolete or superseded claim-bearing evidence is visible, include stale_evidence in critical_risks even when current primary records settle the answer.",
                    "- Verdict discipline remains: polluted documents belong in rejected_evidence, not supporting_evidence.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v6",
            "evidence_diagnostics_v7",
            "evidence_diagnostics_v8_structural",
            "evidence_diagnostics_v9_structural_recall",
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            diagnostic_rules.extend(
                [
                    "- Refuted verdict boundary: cite clean primary or direct refuting evidence in supporting_evidence; without it, choose insufficient.",
                    "- No-primary tool result boundary: if primary search returns no documents and all claim-bearing evidence is generated, secondary, reposted, or unsupported, choose insufficient rather than refuted.",
                    "- Generated lore precision: do not mark generated_lore_detected=yes for ordinary stale, repeated, or secondary evidence unless the content is a generated/wiki-like unsupported entity or page.",
                    "- Partial-support precision: mark partial_support only when one explicit component is supported and another explicit component is missing.",
                    "- Risk precision: not every rejected background document needs every critical_risks label; labels should explain verdict or tool-use necessity.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v7",
            "evidence_diagnostics_v8_structural",
            "evidence_diagnostics_v9_structural_recall",
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            diagnostic_rules.extend(
                [
                    "- Stale precision: do not mark stale_evidence for a pre-event planning/pending note if later primary records settle the deadline or completion claim; mark stale only for current-validity, lapsed, expired, active-status, or version-history conflicts.",
                    "- Citation-laundering precision: same-root repetition alone is false_consensus, not citation_laundering; mark citation_laundering only when a visible cited target, appendix, citation chain, or official-looking cited source fails to support the claim.",
                    "- False-consensus precision: do not mark false_consensus for a few rejected repeats when clean primary records are visible and decisive; mark it when repeated same-root evidence dominates the context or explains why tools/rejection were necessary.",
                    "- Generated-lore recall: unsupported generated/wiki-like pages or invented named projects, deals, programs, certifications, or entities with no primary basis should be generated_lore_detected=yes.",
                    "- Partial-support recall: if clean evidence supports a weaker component but not the target quantifier, scope, or causal strength, mark support_is_partial=yes and include partial_support.",
                ]
            )
        if prompt in STRUCTURAL_DIAGNOSTIC_PROMPTS:
            diagnostic_rules.extend(
                [
                    "- Structural split: fill environment_observations for visible evidence conditions, including rejected pollutants, and keep critical_risks for sparse verdict-critical risks.",
                    "- Observation is not the same as verdict-critical risk: a visible repost, stale note, generated page, or citation chain can be observed without being a critical_risks item.",
                    "- Clean controls with clean primary support should keep critical_risks empty unless a visible issue changes the verdict or requires tool use.",
                    "- Same-root repetition should set visible_reposts_or_same_root_repetition=yes; add false_consensus only if the repetition affects support, rejection, or required tools.",
                    "- Generated lore/no-primary is not automatically citation_laundering; mark citation laundering only for a visible failed citation chain or cited target.",
                    "- Temporal pollution is not automatically conflict; use stale_evidence when superseded material blocks current support.",
                    "- Partial-support critical risk requires a supported weaker claim plus a missing target scope, quantifier, or causal strength.",
                ]
            )
        if prompt == "evidence_diagnostics_v9_structural_recall":
            diagnostic_rules.extend(
                [
                    "- Structural recall repair: do not hide true verdict blockers in environment_observations; repeat them in critical_risks when they affect support.",
                    "- False-consensus recall: when repeated same-root evidence dominates the context, creates an illusion of independent support, or leaves no clean primary support, set sources_are_independent=no and include false_consensus.",
                    "- Citation-laundering recall: when a visible cited target, appendix, or citation chain is used as support but does not establish the target claim, set citation_laundering_detected=yes and include citation_laundering.",
                    "- Partial-support recall: when clean evidence supports a weaker component but not the requested quantifier, scope, comparison, or causal strength, set support_is_partial=yes and include partial_support, not conflicting_evidence.",
                    "- Observation-only is for nonblocking rejected background pollution; a condition that changes verdict, blocks support, or explains required rejection/tooling must also appear in critical_risks.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v10_structural_contract",
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            diagnostic_rules.extend(
                [
                    "- Structural critical-risk contract: fill environment_observations first, then add critical_risks only through the decision table below.",
                    "- false_consensus: repeated same-root summaries must dominate apparent support or create an illusion of independent support; do not use false_consensus for citation-chain failures, generated/no-primary rows, or mixed-source partial-support rows.",
                    "- citation_laundering: require a visible cited target, appendix, or citation chain used as support whose cited target does not establish the target claim; do not use citation_laundering for ordinary repetition, generated lore, or corrupted mixed-source tables.",
                    "- partial_support: when evidence supports a weaker claim but not the requested scope, quantifier, comparison, or causal strength, set support_is_partial=yes and include partial_support; do not substitute conflicting_evidence or citation_laundering unless those failures are independently visible.",
                    "- stale_evidence: use stale_evidence for superseded current-status/version-history support; do not use conflicting_evidence unless a current direct contradiction is visible.",
                    "- generated_lore and no_primary_source: generated/wiki-like or invented evidence with no primary basis should be generated_lore plus no_primary_source; no_primary_source alone is for ordinary claims with no direct primary record.",
                    "- conflicting_evidence: reserve for clean primary or direct evidence that contradicts the target claim; do not use it for partial scope, stale support, generated lore, or failed citation chains alone.",
                ]
            )
        if prompt in {
            "evidence_diagnostics_v11_role_disciplined_contract",
            "evidence_diagnostics_v12_critical_risk_contract",
        }:
            diagnostic_rules.extend(
                [
                    "- Structural evidence-role discipline contract: apply the v10 decision table, then enforce the supporting_evidence hard gate.",
                    "- supporting_evidence may contain only clean documents that directly support the final verdict: clean support for supported verdicts, or clean primary/direct refuting evidence for refuted verdicts.",
                    "- Never put pollutant roots, reposts, generated/wiki-like pages, unsupported summaries, failed citation targets, stale superseded records, corrupted appendices, or no-primary documents in supporting_evidence.",
                    "- If no clean document directly supports the final verdict, leave supporting_evidence empty; do not cite rejected pollution as support for insufficiency or refutation.",
                    "- Repeated same-root claims contradicted by clean primary evidence require false_consensus plus conflicting_evidence in critical_risks.",
                    "- Failed citation chains contradicted by clean primary evidence require citation_laundering plus conflicting_evidence in critical_risks.",
                    "- Generated/wiki-like no-primary rows should use generated_lore plus no_primary_source only; ordinary no-primary rows should use no_primary_source only.",
                    "- Temporal supersession should use stale_evidence rather than conflicting_evidence unless two clean current primary sources directly disagree.",
                    "- Mixed-source or corrupted-table overclaims should use partial_support rather than conflicting_evidence or citation_laundering.",
                ]
            )
        if prompt == "evidence_diagnostics_v12_critical_risk_contract":
            diagnostic_rules.extend(
                [
                    "- Critical-risk repair audit contract: each critical_risks label needs a positive basis and must pass its negative boundary.",
                    "- false_consensus positive/negative: include it when same-root repetition dominates apparent support or hides missing primary evidence; exclude it when repeated pollutants are merely visible and rejected while clean primary evidence is decisive.",
                    "- citation_laundering positive/negative: include it only for a visible cited target, appendix, or citation chain used as support that fails to establish the claim; exclude ordinary reposting, generated lore, and unrelated background citations.",
                    "- partial_support positive/negative: include it when clean evidence supports a weaker scope, quantity, comparison, or causal relation; exclude it when evidence directly refutes the target or when no clean primary exists at all.",
                    "- conflicting_evidence positive/negative: include it for clean primary/direct contradiction; exclude it for stale, partial, generated, no-primary, or citation-laundered rows without clean contradiction.",
                    "- stale_evidence positive/negative: include it when superseded material is used for current-status/version-history support; exclude old rejected pollution when clean current primary evidence decides the verdict.",
                    "- Remove any critical_risks label whose only basis is a visible rejected pollutant already captured by environment_observations.",
                    "- Optimize for exact critical-risk rows on the fixed calibration slice, not for maximal risk-label recall.",
                ]
            )
    parts = [
        f"Investigation question: {question}",
        "Diagnostic rules:",
        "\n".join(diagnostic_rules),
        render_documents("Retrieved documents", documents),
    ]
    if tool_results:
        parts.append("Tool results:\n" + json.dumps(list(tool_results), ensure_ascii=False, indent=2))
    parts.append("Return the final JSON object now.")
    return [
        {"role": "developer", "content": phase2s_system_prompt(prompt)},
        {"role": "user", "content": "\n\n".join(parts)},
    ]


def phase2s_routing_messages(question: str, documents: Sequence[AgentDocument]) -> List[Dict[str, str]]:
    return [
        {
            "role": "developer",
            "content": "\n".join(
                [
                    "You choose up to three corpus-only tool calls before final answer generation.",
                    "You must explicitly decide whether temporal comparison is required.",
                    "Rule: if the question asks about current status, active certification, updated policy, version history, yearly audit, or whether an old claim remains true, and multiple dates or versions appear, call compare_versions.",
                    "Rule: if initial documents repeat the same claim wording, cite the same upstream/root document, or contain mostly secondary summaries with no clean primary record, do not return an empty tool list; call request_primary_record and search_contradictions.",
                    "Rule: if same-root repetition is visible, also trace_citation on the root or a representative cited document when a doc_id is available.",
                    "Rule: if primary search returns no documents, the final answer should normally be insufficient unless a clean direct contradiction is visible.",
                    "Available tools:",
                    "- trace_citation(doc_id, depth=2)",
                    "- request_primary_record(claim_text, entity, date_range, top_n=3)",
                    "- compare_versions(entity, topic, top_n=5)",
                    "- search_contradictions(claim_text, top_n=5)",
                    "Return one JSON object matching this schema:",
                    json.dumps(phase2s_routing_json_schema(), ensure_ascii=False),
                ]
            ),
        },
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    f"Investigation question: {question}",
                    render_documents("Initial documents", documents),
                    "Return the routing JSON now.",
                ]
            ),
        },
    ]


def parse_phase2s_prediction_json(text: str) -> Phase2SPrediction:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    return Phase2SPrediction.model_validate_json(stripped)


def parse_phase2s_routing_json(text: str) -> tuple[List[ToolCall], Dict[str, Any]]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.removeprefix("```json").removeprefix("```").strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
    payload = json.loads(stripped)
    calls = [
        ToolCall(tool=str(item["tool"]), args={**item.get("args", {}), "_why": item.get("why", "")})
        for item in payload.get("chosen_tools", [])[:3]
    ]
    return calls, dict(payload.get("tool_routing_diagnosis", {}))


def diagnostics_from_scope_tag(scope_tag: str) -> EvidenceDiagnostics:
    fields: Dict[str, str] = {
        "has_primary_support": "yes",
        "primary_support_is_current": "yes",
        "evidence_has_conflict": "no",
        "support_is_partial": "no",
        "sources_are_independent": "yes",
        "citation_laundering_detected": "no",
        "generated_lore_detected": "no",
        "no_primary_source_detected": "no",
    }
    if scope_tag == "stale":
        fields["primary_support_is_current"] = "no"
    elif scope_tag == "conflicting":
        fields["evidence_has_conflict"] = "yes"
    elif scope_tag == "partial":
        fields["support_is_partial"] = "yes"
    elif scope_tag == "no_primary_source":
        fields["has_primary_support"] = "no"
        fields["primary_support_is_current"] = "not_applicable"
        fields["no_primary_source_detected"] = "yes"
    elif scope_tag == "generated_lore":
        fields["has_primary_support"] = "no"
        fields["primary_support_is_current"] = "not_applicable"
        fields["generated_lore_detected"] = "yes"
        fields["no_primary_source_detected"] = "yes"
    elif scope_tag == "uncertain":
        fields = {key: "uncertain" for key in DIAGNOSTIC_FIELDS}
        fields["primary_support_is_current"] = "uncertain"
    return EvidenceDiagnostics.model_validate(fields)


def risks_from_scope_tag(scope_tag: str) -> List[str]:
    return {
        "stale": ["stale_evidence"],
        "conflicting": ["conflicting_evidence"],
        "partial": ["partial_support"],
        "no_primary_source": ["no_primary_source"],
        "generated_lore": ["generated_lore", "no_primary_source"],
    }.get(scope_tag, [])


def phase2_prediction_to_phase2s(prediction: Phase2Prediction) -> Phase2SPrediction:
    scope_tag = prediction.scope_tag if prediction.scope_tag in PHASE2R_SCOPE_TAGS else "uncertain"
    diagnostics = diagnostics_from_scope_tag(scope_tag)
    risks = risks_from_scope_tag(scope_tag)
    method = "read_docs"
    ledger = [
        VerificationLedgerEntry(
            risk_checked="primary_support",
            method=method,
            evidence=list(dict.fromkeys(prediction.supporting_evidence + prediction.rejected_evidence)),
            finding=f"Legacy evidence_graph_v3 emitted scope_tag={scope_tag}.",
            effect_on_verdict="supports" if prediction.claim_verdict == "supported" else "refutes" if prediction.claim_verdict == "refuted" else "makes_insufficient",
        )
    ]
    return Phase2SPrediction(
        claim_verdict=prediction.claim_verdict,
        confidence=prediction.confidence,
        evidence_diagnostics=diagnostics,
        critical_risks=risks,  # type: ignore[arg-type]
        supporting_evidence=prediction.supporting_evidence,
        rejected_evidence=prediction.rejected_evidence,
        verification_ledger=ledger,
        answer=prediction.answer,
    )
