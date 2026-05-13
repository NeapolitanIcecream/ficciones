from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple

from rank_bm25 import BM25Okapi

from .schemas import AgentDocument, GoldDocument


TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)?")


@dataclass(frozen=True)
class SearchHit:
    doc: AgentDocument
    score: float


def tokenize(text: str) -> List[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def document_text(doc: AgentDocument) -> str:
    citations = " ".join(doc.visible_citations)
    return f"{doc.title} {doc.source_type} {doc.timestamp} {doc.body} {citations}"


def search_episode(
    query: str,
    documents: Sequence[AgentDocument],
    gold_documents: Sequence[GoldDocument],
    top_k: int = 8,
) -> List[SearchHit]:
    if not documents:
        return []
    corpus = [tokenize(document_text(doc)) for doc in documents]
    bm25 = BM25Okapi(corpus)
    scores = list(bm25.get_scores(tokenize(query)))
    gold_by_id: Dict[str, GoldDocument] = {gold.doc_id: gold for gold in gold_documents}
    scored: List[Tuple[float, AgentDocument]] = []
    for score, doc in zip(scores, documents):
        rank_boost = gold_by_id.get(doc.doc_id).rank_boost if doc.doc_id in gold_by_id else 0.0
        scored.append((float(score) + rank_boost, doc))
    scored.sort(key=lambda item: (-item[0], item[1].doc_id))
    return [SearchHit(doc=doc, score=score) for score, doc in scored[:top_k]]


def selected_docs(hits: Iterable[SearchHit]) -> List[AgentDocument]:
    return [hit.doc for hit in hits]
