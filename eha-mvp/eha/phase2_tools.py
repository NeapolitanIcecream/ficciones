from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

from rank_bm25 import BM25Okapi

from .phase2_retrieval import PRIMARY_SOURCE_TYPES
from .retrieval import document_text, tokenize
from .schemas import AgentDocument


def public_doc_payload(doc: AgentDocument, score: float | None = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "doc_id": doc.doc_id,
        "title": doc.title,
        "source_type": doc.source_type,
        "timestamp": doc.timestamp,
        "visible_citations": list(doc.visible_citations),
        "body_excerpt": doc.body[:700],
    }
    if score is not None:
        payload["score"] = round(score, 4)
    return payload


def rank_public_docs(query: str, documents: Sequence[AgentDocument], top_n: int) -> List[Dict[str, Any]]:
    if not documents:
        return []
    corpus = [tokenize(document_text(doc)) for doc in documents]
    bm25 = BM25Okapi(corpus)
    scores = list(bm25.get_scores(tokenize(query)))
    ranked = sorted(zip(scores, documents), key=lambda item: (-float(item[0]), item[1].doc_id))
    return [public_doc_payload(doc, float(score)) for score, doc in ranked[:top_n]]


class Phase2Toolbox:
    def __init__(self, documents: Sequence[AgentDocument]) -> None:
        self.documents = list(documents)
        self.docs_by_id = {doc.doc_id: doc for doc in documents}

    def trace_citation(self, doc_id: str, depth: int = 2) -> Dict[str, Any]:
        trace: List[Dict[str, Any]] = []
        missing: List[str] = []
        frontier = [doc_id]
        seen: set[str] = set()
        for _ in range(max(0, depth)):
            next_frontier: List[str] = []
            for current_id in frontier:
                if current_id in seen:
                    continue
                seen.add(current_id)
                doc = self.docs_by_id.get(current_id)
                if doc is None:
                    missing.append(current_id)
                    continue
                trace.append({"doc_id": doc.doc_id, "cites": list(doc.visible_citations)})
                for citation in doc.visible_citations:
                    if citation in self.docs_by_id:
                        next_frontier.append(citation)
                    else:
                        missing.append(citation)
            frontier = next_frontier
            if not frontier:
                break
        return {"root_doc": doc_id, "trace": trace, "missing_citations": sorted(set(missing))}

    def request_primary_record(
        self,
        claim_text: str,
        entity: str = "",
        date_range: str = "",
        top_n: int = 3,
    ) -> Dict[str, Any]:
        candidates = [doc for doc in self.documents if doc.source_type in PRIMARY_SOURCE_TYPES]
        query = " ".join(part for part in [claim_text, entity, date_range] if part)
        return {"query": query, "documents": rank_public_docs(query, candidates, top_n)}

    def compare_versions(self, entity: str, topic: str, top_n: int = 5) -> Dict[str, Any]:
        query = f"{entity} {topic} old new revised update version history renewal certification"
        docs = rank_public_docs(query, self.documents, top_n)
        docs.sort(key=lambda item: str(item["timestamp"]))
        return {"query": query, "versions": docs}

    def search_contradictions(self, claim_text: str, top_n: int = 5) -> Dict[str, Any]:
        expanded = " ".join(
            [
                claim_text,
                f"{claim_text} audit",
                f"{claim_text} correction",
                f"{claim_text} regulator",
                f"{claim_text} revised",
                f"{claim_text} not",
                f"{claim_text} incident report",
            ]
        )
        return {"query": expanded, "documents": rank_public_docs(expanded, self.documents, top_n)}

    def execute(self, name: str, args: Mapping[str, Any]) -> Dict[str, Any]:
        if name == "trace_citation":
            return self.trace_citation(str(args.get("doc_id", "")), int(args.get("depth", 2)))
        if name == "request_primary_record":
            return self.request_primary_record(
                claim_text=str(args.get("claim_text", "")),
                entity=str(args.get("entity", "")),
                date_range=str(args.get("date_range", "")),
                top_n=int(args.get("top_n", 3)),
            )
        if name == "compare_versions":
            return self.compare_versions(
                entity=str(args.get("entity", "")),
                topic=str(args.get("topic", "")),
                top_n=int(args.get("top_n", 5)),
            )
        if name == "search_contradictions":
            return self.search_contradictions(str(args.get("claim_text", "")), int(args.get("top_n", 5)))
        return {"error": f"unknown tool: {name}"}
