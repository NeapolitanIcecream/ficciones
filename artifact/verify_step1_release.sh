#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
  echo "usage: ./verify_step1_release.sh [--allow-blocked]" >&2
  echo "  --allow-blocked  run checks but do not fail solely because readiness remains blocked" >&2
}

if [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "${1:-}" != "" ] && [ "${1:-}" != "--allow-blocked" ]; then
  usage
  exit 2
fi

allow_blocked=false
if [ "${1:-}" = "--allow-blocked" ]; then
  allow_blocked=true
fi

artifact_dir="$(pwd)"
repo_root="$(cd .. && pwd)"
eha_dir="${EHA_MVP_DIR:-${repo_root}/eha-mvp}"
paper_dir="${PAPER_DIR:-${repo_root}/paper}"
reports_dir="${REPORTS_DIR:-${repo_root}/reports}"
readiness_json="${reports_dir}/eha_step1_readiness_check.json"

if [ ! -d "$eha_dir" ]; then
  echo "Missing eha-mvp directory: ${eha_dir}" >&2
  echo "Set EHA_MVP_DIR if this artifact directory is not next to eha-mvp/." >&2
  exit 1
fi

if [ ! -d "$paper_dir" ]; then
  echo "Missing paper directory: ${paper_dir}" >&2
  echo "Set PAPER_DIR if this artifact directory is not next to paper/." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to read ${readiness_json}." >&2
  exit 1
fi

bash -n "${artifact_dir}/serve_human_audit_review.sh"
bash -n "${artifact_dir}/finalize_human_audit.sh"
bash -n "${artifact_dir}/verify_step1_release.sh"

cd "$artifact_dir"
./reproduce_minimal.sh >/tmp/eha_step1_minimal_score.json

cd "$eha_dir"
uv run pytest

cd "$paper_dir"
make

cd "$eha_dir"
uv run eha-step1-release step1-readiness-check \
  --artifact-dir "$artifact_dir" \
  --paper-dir "$paper_dir" \
  --out-dir "$reports_dir"

status="$(python3 - "$readiness_json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
print(payload.get("status", "missing"))
PY
)"

if [ "$status" != "ready" ] && [ "$allow_blocked" != "true" ]; then
  echo "Step 1 readiness is ${status}; inspect ${readiness_json}." >&2
  exit 2
fi

if git -C "$repo_root" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  (cd "$repo_root" && git diff --check)
fi

echo
echo "Step 1 release verification completed with readiness status: ${status}"
