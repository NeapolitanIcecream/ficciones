from __future__ import annotations

from collections import Counter, defaultdict

from eha.phase2_retrieval import retrieve
from eha.schemas import by_task, read_jsonl
from eha.surface_cue_generate import (
    SURFACE_CUE_AXES,
    SURFACE_CUE_FAMILIES,
    generate_surface_cue_dataset,
    surface_cue_action_gold_rows,
    write_surface_cue_dataset,
)


def surface_family(task) -> str:
    suffix = task.target_claim_id.removeprefix("c_surface_")
    for family in sorted(SURFACE_CUE_FAMILIES, key=len, reverse=True):
        if suffix.startswith(f"{family}_"):
            return family
    raise AssertionError(f"unknown surface-cue family in {task.target_claim_id}")


def surface_template_count() -> int:
    return sum(len(templates) for templates in SURFACE_CUE_FAMILIES.values())


def test_surface_cue_dataset_defines_paired_no_api_smoke_grid() -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=9417)
    by_claim = defaultdict(list)
    for task in tasks:
        by_claim[task.target_claim_id].append(task)

    assert manifest.name == "EHA-v2-surface-cue-smoke"
    assert all(len(templates) >= 3 for templates in SURFACE_CUE_FAMILIES.values())
    assert manifest.episodes == surface_template_count() * len(SURFACE_CUE_AXES) * 2
    assert manifest.episode_type_counts == {f"surface_cue_{axis}": surface_template_count() * 2 for axis in SURFACE_CUE_AXES}
    assert len(tasks) == 180
    assert len(documents) == len(gold_documents)
    assert edges
    assert all(task.phase == "phase2_surface_cue" for task in tasks)
    assert {task.gold.verdict for task in tasks} == {"refuted", "insufficient"}
    assert {surface_family(task) for task in tasks} == set(SURFACE_CUE_FAMILIES)
    assert all(len(group) == 2 for group in by_claim.values())

    for group in by_claim.values():
        verdicts = {task.gold.verdict for task in group}
        answers = {task.gold.answer_brief for task in group}
        risks = {tuple(task.gold.critical_risks) for task in group}
        assert len(verdicts) == 1
        assert len(answers) == 1
        assert len(risks) == 1


def test_surface_cue_axes_mutate_only_the_intended_visible_cues() -> None:
    _, tasks, documents, gold_documents, _ = generate_surface_cue_dataset(seed=9417)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)

    def conflict_orders_pair(axis: str):
        pair = [task for task in tasks if task.target_claim_id == f"c_surface_conflict_orders_{axis}"]
        assert len(pair) == 2
        return sorted(pair, key=lambda task: task.task_id)

    visible_source, hidden_source = conflict_orders_pair("source_type_visibility")
    assert {doc.source_type for doc in docs_by_task[hidden_source.task_id]} == {"document"}
    assert "audit_report" in {doc.source_type for doc in docs_by_task[visible_source.task_id]}

    truthful, shuffled = conflict_orders_pair("metadata_perturbation")
    shuffled_docs = {doc.doc_id: doc for doc in docs_by_task[shuffled.task_id]}
    shuffled_gold = {gold.doc_id: gold for gold in gold_by_task[shuffled.task_id]}
    shuffled_false = [doc for doc in shuffled_docs.values() if shuffled_gold[doc.doc_id].is_contaminated and shuffled_gold[doc.doc_id].upstream_root == doc.doc_id][0]
    shuffled_primary = [shuffled_docs[doc_id] for doc_id in shuffled.gold.primary_support]
    assert shuffled_false.timestamp > max(doc.timestamp for doc in shuffled_primary)
    assert shuffled_false.source_type == "regulator_filing"
    assert "regulator_filing" not in {doc.source_type for doc in docs_by_task[truthful.task_id] if doc.doc_id not in truthful.gold.primary_support}

    original_style, normalized_style = conflict_orders_pair("style_normalization")
    original_text = " ".join(doc.body for doc in docs_by_task[original_style.task_id]).lower()
    normalized_text = " ".join(doc.body for doc in docs_by_task[normalized_style.task_id]).lower()
    assert "undeniable" in original_text
    assert "undeniable" not in normalized_text
    assert normalized_text.count("the record states") >= 2

    plain_spoof, regulator_spoof = conflict_orders_pair("adversarial_spoofing")
    spoof_docs = {doc.doc_id: doc for doc in docs_by_task[regulator_spoof.task_id]}
    spoof_gold = {gold.doc_id: gold for gold in gold_by_task[regulator_spoof.task_id]}
    spoof_false = [doc for doc in spoof_docs.values() if spoof_gold[doc.doc_id].is_contaminated and spoof_gold[doc.doc_id].upstream_root == doc.doc_id][0]
    assert spoof_false.source_type == "audit_report"
    assert "compliance bulletin" in spoof_false.title.lower()
    plain_sources = {doc.source_type for doc in docs_by_task[plain_spoof.task_id] if doc.doc_id not in plain_spoof.gold.primary_support}
    assert "audit_report" not in plain_sources

    full_metadata, stripped = conflict_orders_pair("content_only")
    assert {doc.source_type for doc in docs_by_task[stripped.task_id]} == {"document"}
    assert all(doc.title.startswith("Document ") for doc in docs_by_task[stripped.task_id])
    assert all(doc.visible_citations == [] for doc in docs_by_task[stripped.task_id])
    assert any(doc.visible_citations for doc in docs_by_task[full_metadata.task_id])


def test_surface_cue_smoke_dataset_is_balanced_and_retrieval_observable() -> None:
    _, tasks, documents, gold_documents, _ = generate_surface_cue_dataset(seed=9417)
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    conditions = Counter(task.episode_type for task in tasks)

    assert set(conditions.values()) == {surface_template_count() * 2}
    for task in tasks:
        hits = retrieve(task.question, docs_by_task[task.task_id], gold_by_task[task.task_id], "bm25_top8")
        hit_ids = {hit.doc.doc_id for hit in hits}
        gold_by_id = {gold.doc_id: gold for gold in gold_by_task[task.task_id]}
        if task.gold.primary_support:
            assert set(task.gold.primary_support) & hit_ids
        else:
            assert not any(gold.supports_gold_verdict for gold in gold_by_task[task.task_id])
        assert any(gold_by_id[doc_id].is_contaminated for doc_id in hit_ids)


def test_surface_cue_visible_payload_does_not_leak_hidden_labels() -> None:
    _, tasks, documents, _, _ = generate_surface_cue_dataset(seed=9417)
    forbidden = {
        "supports_gold",
        "supports_false_claim",
        "contamination",
        "known_contaminants",
        "gold verdict",
        "pollutant",
        "primary_a",
        "primary_b",
    }

    assert all("primary" not in doc.doc_id and "pollutant" not in doc.doc_id for doc in documents)
    for task in tasks:
        visible = f"{task.task_id} {task.question}".lower()
        assert not any(token in visible for token in forbidden)
    for doc in documents:
        visible = f"{doc.doc_id} {doc.title} {doc.source_type} {doc.body}".lower()
        assert not any(token in visible for token in forbidden)


def test_surface_cue_action_gold_defines_exact_active_verification_targets(tmp_path) -> None:
    manifest, tasks, documents, gold_documents, edges = generate_surface_cue_dataset(seed=9417)
    docs_by_task = by_task(documents)
    active_tasks = [task for task in tasks if surface_family(task) == "active_verification"]
    rows = surface_cue_action_gold_rows(tasks)

    assert len(rows) == len(active_tasks) == len(SURFACE_CUE_FAMILIES["active_verification"]) * len(SURFACE_CUE_AXES) * 2
    by_task_id = {task.task_id: task for task in active_tasks}
    for row in rows:
        task = by_task_id[row["task_id"]]
        doc_ids = {doc.doc_id for doc in docs_by_task[task.task_id]}
        assert row["required_action_types"] == ["compare_versions", "trace_citation"]
        assert row["compare_versions_target_doc_id"] in task.primary_refutation_docs
        assert row["trace_citation_target_doc_id"] == task.pollutant_root_id
        assert set(row["required_target_doc_ids"]) <= doc_ids
        assert row["machine_executable_target_required"] is True

    write_surface_cue_dataset(tmp_path, manifest, tasks, documents, gold_documents, edges)
    written_rows = list(read_jsonl(tmp_path / "action_gold.jsonl"))
    assert written_rows == rows
