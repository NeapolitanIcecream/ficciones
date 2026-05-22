from __future__ import annotations

from collections import Counter, defaultdict

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


def test_uncued_pilot_generation_matches_phase9_balance_and_action_targets(tmp_path) -> None:
    dataset = build_uncued_dataset(
        phase="pilot",
        task_count=60,
        views=["neutral_metadata_visible", "neutral_metadata_hidden"],
        seed=20260522,
    )
    write_uncued_dataset(tmp_path, dataset)
    loaded = load_uncued_dataset(tmp_path)

    assert loaded["manifest"]["phase"] == "pilot"
    assert len(loaded["tasks"]) == 60
    assert Counter(task["condition"] for task in loaded["latent_tasks"]) == {
        "clean": 12,
        "conflicting_evidence": 12,
        "false_consensus": 12,
        "buried_primary": 12,
        "generated_lore": 12,
    }
    assert Counter(task["family"] for task in loaded["latent_tasks"]) == {
        "packet_judgment": 24,
        "evidence_selection": 24,
        "active_verification": 12,
    }

    by_condition = defaultdict(Counter)
    for task in loaded["latent_tasks"]:
        by_condition[task["condition"]][task["family"]] += 1
    assert all(counts["active_verification"] >= 2 for counts in by_condition.values())
    assert len(loaded["action_gold"]) == 12

    docs_by_view_task = {
        view: defaultdict(set)
        for view in ["neutral_metadata_visible", "neutral_metadata_hidden"]
    }
    for view, docs in loaded["documents_by_view"].items():
        for doc in docs:
            docs_by_view_task[view][doc["task_id"]].add(doc["doc_id"])
        assert all("primary" not in doc["doc_id"] and "pollutant" not in doc["doc_id"] for doc in docs)

    for row in loaded["action_gold"]:
        assert row["machine_executable_target_required"] is True
        assert row["required_action_types"]
        for view, targets in row["required_target_doc_ids_by_view"].items():
            assert targets
            assert set(targets) <= docs_by_view_task[view][row["task_id"]]

    gold_by_task_view = defaultdict(dict)
    for gold in loaded["gold_documents"]:
        gold_by_task_view[(gold["task_id"], gold["view"])][gold["internal_doc_id"]] = (
            gold["hidden_role"],
            gold["supports_gold_verdict"],
            tuple(gold["contamination"]),
        )
    for task in loaded["tasks"]:
        assert (
            gold_by_task_view[(task["task_id"], "neutral_metadata_visible")]
            == gold_by_task_view[(task["task_id"], "neutral_metadata_hidden")]
        )
