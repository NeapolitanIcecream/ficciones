#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def score(task, output):
    gold = task["gold"]
    support = set(output.get("supporting_evidence", []))
    pollutants = set(gold.get("contaminant_doc_ids", [])) | set(gold.get("generated_doc_ids", [])) | set(gold.get("stale_doc_ids", []))
    belief = output.get("claim_verdict") == gold.get("gold_verdict")
    evidence_clean = not bool(support & pollutants)
    uncertainty = output.get("claim_verdict") == "insufficient" if gold.get("gold_verdict") == "insufficient" else output.get("claim_verdict") != "insufficient"
    operational_escape = bool(belief and evidence_clean and uncertainty)
    return {
        "belief_correctness": float(belief),
        "evidence_cleanliness": float(evidence_clean),
        "uncertainty_discipline": float(uncertainty),
        "operational_epistemic_escape": float(operational_escape),
    }


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: scoring_contract.py TASK_JSON MODEL_OUTPUT_JSON")
    task = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    print(json.dumps(score(task, output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
