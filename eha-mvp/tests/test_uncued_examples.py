from __future__ import annotations

from eha.uncued_examples import find_example_rows, latex_escape


def test_find_example_rows_prefers_generated_lore_hygiene_failure() -> None:
    rows = [
        {
            "task_id": "clean_visible",
            "base_task_id": "clean",
            "family": "packet_judgment",
            "condition": "clean",
            "view": "neutral_metadata_visible",
            "model": "m1",
            "belief_correctness": "1.0",
            "operational_epistemic_escape": "1.0",
            "polluted_support_rate": "0.0",
        },
        {
            "task_id": "lore_visible",
            "base_task_id": "lore",
            "family": "packet_judgment",
            "condition": "generated_lore",
            "view": "neutral_metadata_visible",
            "model": "m1",
            "belief_correctness": "1.0",
            "operational_epistemic_escape": "0.0",
            "polluted_support_rate": "1.0",
        },
        {
            "task_id": "active_visible",
            "base_task_id": "active",
            "family": "active_verification",
            "condition": "conflicting_evidence",
            "view": "neutral_metadata_visible",
            "model": "m1",
            "belief_correctness": "1.0",
            "operational_epistemic_escape": "0.0",
            "polluted_support_rate": "0.0",
        },
    ]

    examples = find_example_rows(rows)

    assert examples["generated_lore_hygiene_failure"]["task_id"] == "lore_visible"
    assert examples["clean_or_buried_primary"]["task_id"] == "clean_visible"
    assert examples["active_verification"]["task_id"] == "active_visible"


def test_latex_escape_escapes_identifiers_without_dropping_text() -> None:
    assert latex_escape("uncued_001_d03 & 50%") == r"uncued\_001\_d03 \& 50\%"
