from __future__ import annotations

import csv

from eha.surface_cue_design_review import (
    DESIGN_REVIEW_LABEL_FIELDS,
    DESIGN_REVIEW_FIELDNAMES,
    build_surface_cue_design_review_html,
    build_surface_cue_design_review_packet,
    build_surface_cue_design_review_rows,
    validate_surface_cue_design_review_rows,
    write_surface_cue_design_review_package,
)
from eha.surface_cue_design_review_validate import validate_surface_cue_design_review_csv
from eha.surface_cue_generate import generate_surface_cue_dataset, surface_cue_action_gold_rows, write_surface_cue_dataset
from eha.surface_cue_report import parse_surface_claim_id


def test_surface_cue_design_review_rows_cover_every_pair_once() -> None:
    _, tasks, documents, gold_documents, _ = generate_surface_cue_dataset(seed=9417)
    action_rows = surface_cue_action_gold_rows(tasks)
    rows = build_surface_cue_design_review_rows(tasks, documents, gold_documents, action_rows)

    assert len(rows) == 90
    assert {row["review_status"] for row in rows} == {"not_started"}
    assert all(row[field] == "" for row in rows for field in DESIGN_REVIEW_LABEL_FIELDS)
    assert all(row["auto_pair_contract_ok"] == "yes" for row in rows)
    assert all(row["auto_retrieval_observability_ok"] == "yes" for row in rows)
    assert all(row["auto_action_target_contract_ok"] == "yes" for row in rows)
    assert all(row["auto_visible_leakage_count"] == "0" for row in rows)

    claim_ids = {row["target_claim_id"] for row in rows}
    assert len(claim_ids) == len(rows)
    parsed = [parse_surface_claim_id(claim_id) for claim_id in claim_ids]
    assert len({(family, template) for family, template, _ in parsed}) == 18
    assert len({(family, axis) for family, _, axis in parsed}) == 30


def test_surface_cue_design_review_validation_distinguishes_incomplete_and_complete_rows() -> None:
    _, tasks, documents, gold_documents, _ = generate_surface_cue_dataset(seed=9417)
    action_rows = surface_cue_action_gold_rows(tasks)
    rows = build_surface_cue_design_review_rows(tasks, documents, gold_documents, action_rows)

    incomplete = validate_surface_cue_design_review_rows(rows)
    assert incomplete["status"] == "incomplete"
    assert incomplete["n_pairs"] == 90
    assert incomplete["n_reviewed"] == 0
    assert incomplete["missing_label_cells"] == 90 * len(DESIGN_REVIEW_LABEL_FIELDS)

    completed_rows = []
    for row in rows:
        completed = dict(row)
        completed.update({field: "yes" for field in DESIGN_REVIEW_LABEL_FIELDS})
        completed["review_status"] = "reviewed"
        completed["reviewer_notes"] = "Checked pair contract and visible cue manipulation."
        completed_rows.append(completed)
    complete = validate_surface_cue_design_review_rows(completed_rows)
    assert complete["status"] == "complete"
    assert complete["n_reviewed"] == 90
    assert complete["missing_label_cells"] == 0
    assert complete["missing_notes"] == 0


def test_surface_cue_design_review_package_writes_handoff_artifacts(tmp_path) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=9417)
    dataset_dir = tmp_path / "dataset"
    out_dir = tmp_path / "reports"
    write_surface_cue_dataset(dataset_dir, manifest, tasks, documents, gold_documents, edges)

    summary = write_surface_cue_design_review_package(dataset_dir, out_dir)
    worksheet_path = out_dir / "surface_cue_design_review_worksheet.csv"
    manifest_path = out_dir / "eha_step2_surface_cue_design_review_manifest.json"
    packet_path = out_dir / "eha-step2-surface-cue-design-review-packet-2026-05-16.md"
    html_path = out_dir / "surface_cue_design_review.html"
    launcher_path = out_dir / "serve_surface_cue_design_review.sh"

    assert summary["status"] == "incomplete"
    assert summary["n_pairs"] == 90
    assert worksheet_path.exists()
    assert manifest_path.exists()
    assert packet_path.exists()
    assert html_path.exists()
    assert launcher_path.exists()

    with worksheet_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 90
    assert set(DESIGN_REVIEW_LABEL_FIELDS) <= set(rows[0])

    packet = build_surface_cue_design_review_packet(summary, rows)
    assert packet_path.read_text(encoding="utf-8") == packet
    assert "not model evidence" in packet
    assert "Do not copy labels from model outputs" in packet

    html = html_path.read_text(encoding="utf-8")
    assert build_surface_cue_design_review_html(summary, rows) == html
    assert "surface_cue_design_review_worksheet.csv" in html
    assert "Import CSV" in html
    assert "Download CSV" in html
    assert "Next incomplete" in html
    assert "familyFilter" in html
    assert "axisFilter" in html
    assert "statusFilter" in html
    assert "pilot ready" in html.lower()

    launcher = launcher_path.read_text(encoding="utf-8")
    assert "python3 -m http.server" in launcher
    assert "--bind 127.0.0.1" in launcher
    assert "surface_cue_design_review.html" in launcher


def write_review_rows(path, rows) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DESIGN_REVIEW_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_surface_cue_design_review_csv_validator_writes_completion_status(tmp_path) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=9417)
    dataset_dir = tmp_path / "dataset"
    out_dir = tmp_path / "reports"
    write_surface_cue_dataset(dataset_dir, manifest, tasks, documents, gold_documents, edges)
    write_surface_cue_design_review_package(dataset_dir, out_dir)

    incomplete = validate_surface_cue_design_review_csv(out_dir / "surface_cue_design_review_worksheet.csv", out_dir)
    assert incomplete["status"] == "incomplete"
    assert incomplete["pilot_ready"] is False
    assert (out_dir / "eha_step2_surface_cue_design_review_validation.json").exists()
    assert (out_dir / "eha-step2-surface-cue-design-review-validation-2026-05-16.md").exists()

    with (out_dir / "surface_cue_design_review_worksheet.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    completed_rows = []
    for row in rows:
        completed = dict(row)
        completed.update(
            {
                "intended_cue_changed_only": "yes",
                "verdict_and_evidence_contract_preserved": "yes",
                "hidden_label_leakage_found": "no",
                "retrieval_observability_ok": "yes",
                "action_target_contract_ok": "yes",
                "suitable_for_small_api_pilot": "yes",
                "review_status": "reviewed",
                "reviewer_notes": "Reviewed pair.",
            }
        )
        completed_rows.append(completed)
    completed_path = tmp_path / "completed_review.csv"
    write_review_rows(completed_path, completed_rows)

    complete = validate_surface_cue_design_review_csv(completed_path, out_dir)
    assert complete["status"] == "complete"
    assert complete["n_reviewed"] == 90
    assert complete["pilot_ready"] is True
    validation_md = (out_dir / "eha-step2-surface-cue-design-review-validation-2026-05-16.md").read_text(encoding="utf-8")
    assert "Pilot ready: `true`" in validation_md


def test_surface_cue_design_review_complete_but_not_pilot_ready_when_blocker_label_present(tmp_path) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=9417)
    dataset_dir = tmp_path / "dataset"
    out_dir = tmp_path / "reports"
    write_surface_cue_dataset(dataset_dir, manifest, tasks, documents, gold_documents, edges)
    write_surface_cue_design_review_package(dataset_dir, out_dir)

    with (out_dir / "surface_cue_design_review_worksheet.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    completed_rows = []
    for index, row in enumerate(rows):
        completed = dict(row)
        completed.update(
            {
                "intended_cue_changed_only": "yes",
                "verdict_and_evidence_contract_preserved": "yes",
                "hidden_label_leakage_found": "yes" if index == 0 else "no",
                "retrieval_observability_ok": "yes",
                "action_target_contract_ok": "yes",
                "suitable_for_small_api_pilot": "yes",
                "review_status": "reviewed",
                "reviewer_notes": "Reviewed pair.",
            }
        )
        completed_rows.append(completed)
    completed_path = tmp_path / "completed_with_blocker.csv"
    write_review_rows(completed_path, completed_rows)

    summary = validate_surface_cue_design_review_csv(completed_path, out_dir)
    assert summary["status"] == "complete"
    assert summary["pilot_ready"] is False
    assert "hidden_label_leakage_found_yes" in summary["pilot_blockers"]
