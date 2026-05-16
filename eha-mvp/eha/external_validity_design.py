from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Mapping

import typer
from rich.console import Console

from .schemas import write_json


app = typer.Typer(add_completion=False, help="Build no-API EHA Step 2 external-validity design artifacts.")
console = Console()


def candidate_slices() -> List[Dict[str, Any]]:
    return [
        {
            "slice_id": "semi_real_enterprise_wiki",
            "title": "semi-real enterprise wiki",
            "status": "not_started",
            "minimum_pilot_tasks": 40,
            "corpus_assets": ["tickets", "emails", "release notes", "audit logs", "wiki pages", "slack-like summaries"],
            "target_failures": ["buried_primary", "conflicting_evidence", "temporal_drift", "active_verification"],
            "reader_question": "Do EHA failures persist when evidence resembles enterprise knowledge work rather than a compact synthetic mini-web?",
            "human_inputs_required": ["domain-plausibility review", "document realism review", "privacy/sensitive-data check"],
            "artifact_contract": ["task JSONL", "document JSONL", "gold labels", "provenance graph", "surface-cue balance report", "human design-review worksheet"],
            "risks": ["too close to private enterprise data", "overfitting to operational jargon", "harder manual audit burden"],
        },
        {
            "slice_id": "open_web_like_synthetic",
            "title": "open-web-like synthetic corpus",
            "status": "not_started",
            "minimum_pilot_tasks": 40,
            "corpus_assets": ["generated encyclopedia pages", "scraped-like blogs", "SEO reposts", "citation loops", "date-stale pages"],
            "target_failures": ["false_consensus", "citation_laundering", "generated_lore", "stale_evidence"],
            "reader_question": "Do current findings survive an open-web-like ecology with reposting, citation loops, and stale pages?",
            "human_inputs_required": ["web-realism review", "citation-loop review", "surface-cue review"],
            "artifact_contract": ["task JSONL", "document JSONL", "gold labels", "citation graph", "metadata perturbation report", "retrieval observability report"],
            "risks": ["surface cues may dominate", "citation graph may become too template-visible", "generated-lore labels may leak through names"],
        },
        {
            "slice_id": "human_written_pollutants",
            "title": "human-written pollutants",
            "status": "not_started",
            "minimum_pilot_tasks": 20,
            "corpus_assets": ["human-written false summaries", "human-written overclaims", "human-written stale summaries"],
            "target_failures": ["generated_lore", "partial_support", "no_primary_source", "conflicting_evidence"],
            "reader_question": "Do failures depend on templated pollutant language, or do they persist when pollutants are human-written?",
            "human_inputs_required": ["pollutant authoring", "labeler separation from generator", "style leakage review"],
            "artifact_contract": ["authoring brief", "pollutant provenance log", "task JSONL", "document JSONL", "gold labels", "review attestation"],
            "risks": ["costly human writing", "inconsistent style across pollutants", "harder reproducibility unless authoring brief is released"],
        },
        {
            "slice_id": "adaptive_generated_lore",
            "title": "adaptive generated lore",
            "status": "not_started",
            "minimum_pilot_tasks": 30,
            "corpus_assets": ["cross-linked synthetic pages", "cached summaries", "mutually reinforcing lore", "local-canon-consistent aliases"],
            "target_failures": ["generated_lore", "false_consensus", "citation_laundering", "no_primary_source"],
            "reader_question": "Do generated-lore failures become stronger when lore is locally coherent and mutually reinforcing?",
            "human_inputs_required": ["lore consistency review", "leakage review", "source-chain audit"],
            "artifact_contract": ["lore graph", "task JSONL", "document JSONL", "gold labels", "schema-ablation compatibility note"],
            "risks": ["too close to a generated-lore-only benchmark", "may repeat Step 1 mechanism rather than broaden external validity", "source-chain complexity can obscure scoring"],
        },
    ]


def build_external_validity_design() -> Dict[str, Any]:
    return {
        "name": "EHA Step 2 external-validity design",
        "date": "2026-05-16",
        "status": "design_only",
        "api_ready": False,
        "recommended_first_slice": "semi_real_enterprise_wiki",
        "candidate_slices": candidate_slices(),
        "go_no_go_gates_before_api": [
            "complete Step 1 independent human audit",
            "complete 90-pair surface-cue human design review",
            "keep first external-validity pilot at or below 40 tasks",
            "produce a design-review worksheet and validation report for the chosen slice",
            "define target venue and budget before model calls",
        ],
        "non_claims": [
            "not model evidence",
            "not a started external-validity experiment",
            "not a benchmark expansion",
            "do not expand to 500-1000 tasks from this design artifact",
        ],
    }


def render_external_validity_markdown(design: Mapping[str, Any]) -> str:
    lines = [
        "# EHA Step 2 External Validity Design",
        "",
        "Date: 2026-05-16",
        "",
        "This is a no-API design artifact for the Step 2 roadmap. It is not model evidence, not a started external-validity experiment, and not a benchmark expansion.",
        "",
        "## Current Boundary",
        "",
        f"- Status: `{design['status']}`",
        f"- API ready: `{str(design['api_ready']).lower()}`",
        f"- Recommended first slice: `{design['recommended_first_slice']}`",
        "",
        "## Candidate Slices",
        "",
    ]
    for item in design["candidate_slices"]:
        lines.extend(
            [
                f"### {item['title']}",
                "",
                f"- Slice ID: `{item['slice_id']}`",
                f"- Status: `{item['status']}`",
                f"- Minimum pilot tasks: {item['minimum_pilot_tasks']}",
                f"- Reader question: {item['reader_question']}",
                f"- Corpus assets: {', '.join(item['corpus_assets'])}",
                f"- Target failures: {', '.join(item['target_failures'])}",
                f"- Human inputs required: {', '.join(item['human_inputs_required'])}",
                f"- Artifact contract: {', '.join(item['artifact_contract'])}",
                f"- Risks: {', '.join(item['risks'])}",
                "",
            ]
        )
    lines.extend(["## Go / No-Go Gates Before API", ""])
    lines.extend(f"- {gate}" for gate in design["go_no_go_gates_before_api"])
    lines.extend(["", "## Non-Claims", ""])
    lines.extend(f"- {claim}" for claim in design["non_claims"])
    lines.extend(
        [
            "",
            "## Recommended Next Step",
            "",
            "Do not generate an external-validity dataset yet. First complete the Step 1 independent human audit and the 90-pair surface-cue human design review. If both gates clear, begin with the semi-real enterprise wiki slice as a 20-40 task design-reviewed pilot.",
            "",
        ]
    )
    return "\n".join(lines)


def write_external_validity_design(out_dir: Path) -> Dict[str, Any]:
    design = build_external_validity_design()
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "eha_step2_external_validity_design.json", design)
    (out_dir / "eha-step2-external-validity-design-2026-05-16.md").write_text(
        render_external_validity_markdown(design),
        encoding="utf-8",
    )
    return design


@app.command()
def main(out_dir: Path = typer.Option(Path("../reports"), help="Output report directory.")) -> None:
    design = write_external_validity_design(out_dir)
    console.print(
        f"[green]Wrote[/green] external-validity design with {len(design['candidate_slices'])} candidate slices to {out_dir}"
    )


if __name__ == "__main__":
    app()
