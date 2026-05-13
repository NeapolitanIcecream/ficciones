from __future__ import annotations

from eha.run_eval import normalize_prediction_doc_refs
from eha.schemas import DependencyEdge, Prediction


def test_normalize_prediction_doc_refs_extracts_bare_doc_ids_from_explanatory_strings() -> None:
    prediction = Prediction(
        verdict="supported",
        confidence=0.8,
        supporting_evidence=["novalis_001_audit: primary audit record"],
        rejected_evidence=["reject novalis_001_pollutant_root because it is a repost"],
        predicted_dependency_edges=[
            DependencyEdge(from_doc="novalis_001_filing", to_doc="novalis_001_audit", relation="cites"),
            DependencyEdge(from_doc="novalis_001_audit", to_doc="raw_records", relation="cites"),
        ],
        answer="Supported.",
    )

    normalized = normalize_prediction_doc_refs(
        prediction,
        ["novalis_001_audit", "novalis_001_filing", "novalis_001_pollutant_root"],
    )

    assert normalized.supporting_evidence == ["novalis_001_audit"]
    assert normalized.rejected_evidence == ["novalis_001_pollutant_root"]
    assert normalized.predicted_dependency_edges == [
        DependencyEdge(from_doc="novalis_001_filing", to_doc="novalis_001_audit", relation="cites")
    ]
