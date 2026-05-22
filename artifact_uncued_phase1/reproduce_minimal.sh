#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
test -s "$ROOT/manifest.json"
test -s "$ROOT/data/tasks.jsonl"
test -s "$ROOT/data/documents_neutral_metadata_visible.jsonl"
test -s "$ROOT/data/gold_labels.jsonl"
test -s "$ROOT/outputs/predictions.jsonl"
test -s "$ROOT/audits/eha_uncued_scorer_audit.json"
echo "minimal uncued phase1 artifact files present"
