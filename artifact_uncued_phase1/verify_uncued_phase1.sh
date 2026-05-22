#!/usr/bin/env bash
set -euo pipefail
ARTIFACT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ARTIFACT_ROOT/.." && pwd)"
cd "$REPO_ROOT/eha-mvp"
uv run eha-verify-uncued-phase1 --artifact-dir "$ARTIFACT_ROOT" --reports-dir "$REPO_ROOT/reports" --out-dir "$REPO_ROOT/reports"
