from __future__ import annotations

from collections import Counter, defaultdict

from eha.generate_corpus import generate_dataset
from eha.schemas import model_to_dict


def test_generate_dataset_matches_first_phase_distribution() -> None:
    manifest, tasks, documents, gold_documents, _ = generate_dataset(60, 4242)

    assert manifest.episode_type_counts == {
        "clean_control": 10,
        "false_consensus": 15,
        "citation_laundering": 10,
        "temporal_pollution": 10,
        "mixed_source_corruption": 10,
        "halupedia_trap": 5,
    }
    assert len(tasks) == 60
    assert len(documents) == len(gold_documents)


def test_each_episode_has_expected_document_bounds_and_hidden_labels_do_not_leak() -> None:
    _, tasks, documents, gold_documents, _ = generate_dataset(60, 4242)
    docs_by_task: dict[str, list[object]] = defaultdict(list)
    gold_by_task: dict[str, list[object]] = defaultdict(list)
    for doc in documents:
        docs_by_task[doc.task_id].append(doc)
        visible = model_to_dict(doc)
        assert "contamination" not in visible
        assert "upstream_root" not in visible
        assert "truth" not in visible
        assert "rank_boost" not in visible
    for gold in gold_documents:
        gold_by_task[gold.task_id].append(gold)

    for task in tasks:
        assert 12 <= len(docs_by_task[task.task_id]) <= 18
        assert any(gold.evidence_quality == "primary_record" for gold in gold_by_task[task.task_id])
        assert any(gold.is_contaminated for gold in gold_by_task[task.task_id])


def test_generation_is_deterministic_for_same_seed() -> None:
    first = generate_dataset(12, 1234)
    second = generate_dataset(12, 1234)

    assert [model_to_dict(task) for task in first[1]] == [model_to_dict(task) for task in second[1]]
    assert [model_to_dict(doc) for doc in first[2]] == [model_to_dict(doc) for doc in second[2]]
