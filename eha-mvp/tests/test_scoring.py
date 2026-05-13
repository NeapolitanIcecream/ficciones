from __future__ import annotations

from eha.generate_corpus import generate_dataset
from eha.run_eval import heuristic_prediction
from eha.retrieval import search_episode, selected_docs
from eha.schemas import RunRecord, by_task
from eha.scoring import pilot_gate, score_run


def test_pilot_gate_passes_for_heuristic_smoke_backend() -> None:
    _, tasks, documents, gold_documents, edges = generate_dataset(60, 4242)
    pilot_tasks = tasks[:12]
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    records: list[RunRecord] = []
    for task in pilot_tasks:
        hits = search_episode(task.question, docs_by_task[task.task_id], gold_by_task[task.task_id], top_k=8)
        docs = selected_docs(hits)
        for strategy in ("topk_rag", "citation_prompt", "source_independence_prompt", "evidence_graph_prompt"):
            records.append(
                RunRecord(
                    task_id=task.task_id,
                    model="heuristic-sim",
                    strategy=strategy,
                    backend="heuristic",
                    retrieved_doc_ids=[doc.doc_id for doc in docs],
                    prediction=heuristic_prediction(task, strategy, docs, gold_by_task[task.task_id]),
                    parse_success=True,
                )
            )

    rows = score_run(records, pilot_tasks, gold_documents, edges)
    gate = pilot_gate(rows, pilot_tasks, gold_documents)

    assert gate.passed
    topk_rows = [row for row in rows if row["strategy"] == "topk_rag"]
    graph_rows = [row for row in rows if row["strategy"] == "evidence_graph_prompt"]
    assert sum(row["contaminated_citation_rate"] for row in graph_rows) < sum(
        row["contaminated_citation_rate"] for row in topk_rows
    )
