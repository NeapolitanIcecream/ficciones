from __future__ import annotations

from collections import Counter

from eha.uncued_generate import build_uncued_dataset, load_uncued_dataset, write_uncued_dataset
from eha.uncued_leakage import audit_visible_rows


def test_uncued_micro_generation_builds_balanced_role_uncued_views(tmp_path) -> None:
    dataset = build_uncued_dataset(
        phase="micro",
        task_count=10,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=9417,
    )
    write_uncued_dataset(tmp_path, dataset)
    loaded = load_uncued_dataset(tmp_path)

    assert loaded["manifest"]["role_uncued"] is True
    assert len(loaded["tasks"]) == 10
    assert Counter(task["condition"] for task in loaded["latent_tasks"]) == {
        "clean": 2,
        "conflicting_evidence": 2,
        "false_consensus": 2,
        "buried_primary": 2,
        "generated_lore": 2,
    }
    assert Counter(task["family"] for task in loaded["latent_tasks"]) == {
        "packet_judgment": 4,
        "evidence_selection": 4,
        "active_verification": 2,
    }
    assert set(loaded["documents_by_view"]) == {"neutral_metadata_visible", "neutral_metadata_hidden"}
    assert len(loaded["action_gold"]) == 2

    hidden_task_fields = {"family", "condition", "gold_verdict", "known_polluted_doc_ids_by_view"}
    hidden_doc_fields = {"hidden_role", "supports_gold_verdict", "contamination", "internal_doc_id"}
    assert all(hidden_task_fields.isdisjoint(task) for task in loaded["tasks"])
    for docs in loaded["documents_by_view"].values():
        assert all(hidden_doc_fields.isdisjoint(doc) for doc in docs)
        assert all("primary" not in doc["doc_id"] and "pollutant" not in doc["doc_id"] for doc in docs)


def test_uncued_micro_visible_payload_has_no_leakage_hits() -> None:
    dataset = build_uncued_dataset(
        phase="micro",
        task_count=10,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=9417,
    )

    hits = audit_visible_rows(dataset, ["neutral_metadata_visible", "neutral_metadata_hidden"])

    assert hits == []

