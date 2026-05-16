from __future__ import annotations

from eha.external_validity_design import build_external_validity_design, render_external_validity_markdown, write_external_validity_design


def test_external_validity_design_maps_roadmap_options_without_starting_experiment() -> None:
    design = build_external_validity_design()

    assert design["status"] == "design_only"
    assert design["api_ready"] is False
    assert design["recommended_first_slice"] == "semi_real_enterprise_wiki"
    assert {slice_["slice_id"] for slice_ in design["candidate_slices"]} == {
        "semi_real_enterprise_wiki",
        "open_web_like_synthetic",
        "human_written_pollutants",
        "adaptive_generated_lore",
    }
    assert all(slice_["status"] == "not_started" for slice_ in design["candidate_slices"])
    assert all(slice_["minimum_pilot_tasks"] <= 40 for slice_ in design["candidate_slices"])
    assert "complete Step 1 independent human audit" in design["go_no_go_gates_before_api"]
    assert "complete 90-pair surface-cue human design review" in design["go_no_go_gates_before_api"]
    assert "do not expand to 500-1000 tasks from this design artifact" in design["non_claims"]


def test_external_validity_markdown_keeps_design_claim_boundary() -> None:
    design = build_external_validity_design()
    markdown = render_external_validity_markdown(design)

    assert "# EHA Step 2 External Validity Design" in markdown
    assert "not model evidence" in markdown
    assert "not a started external-validity experiment" in markdown
    assert "semi-real enterprise wiki" in markdown
    assert "open-web-like synthetic corpus" in markdown
    assert "human-written pollutants" in markdown
    assert "adaptive generated lore" in markdown
    assert "complete Step 1 independent human audit" in markdown
    assert "complete 90-pair surface-cue human design review" in markdown


def test_external_validity_design_writes_json_and_markdown(tmp_path) -> None:
    summary = write_external_validity_design(tmp_path)

    assert summary["status"] == "design_only"
    assert (tmp_path / "eha_step2_external_validity_design.json").exists()
    report_path = tmp_path / "eha-step2-external-validity-design-2026-05-16.md"
    assert report_path.exists()
    assert report_path.read_text(encoding="utf-8") == render_external_validity_markdown(summary)
