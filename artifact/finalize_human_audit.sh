#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

usage() {
  echo "usage: ./finalize_human_audit.sh [--from-worksheet|--from-model-blinded-worksheet]" >&2
  echo "  --from-worksheet                 import audits/active_verification_pilot_human_audit_worksheet_50.csv before finalization" >&2
  echo "  --from-model-blinded-worksheet   import audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv before finalization" >&2
}

if [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "${1:-}" != "" ] && [ "${1:-}" != "--from-worksheet" ] && [ "${1:-}" != "--from-model-blinded-worksheet" ]; then
  usage
  exit 2
fi

artifact_dir="$(pwd)"
repo_root="$(cd .. && pwd)"
eha_dir="${EHA_MVP_DIR:-${repo_root}/eha-mvp}"
paper_dir="${PAPER_DIR:-${repo_root}/paper}"
reports_dir="${REPORTS_DIR:-${repo_root}/reports}"
readiness_json="${reports_dir}/eha_step1_readiness_check.json"
active_dir="results/reports-eha-active-verification-audit-opaque-2026-05-15"
reference_csv="${eha_dir}/${active_dir}/active_verification_pilot_human_audit_sample_50.csv"
labels_csv="${artifact_dir}/audits/active_verification_human_audit.csv"
worksheet_csv="${artifact_dir}/audits/active_verification_pilot_human_audit_worksheet_50.csv"
model_blinded_worksheet_csv="${artifact_dir}/audits/active_verification_pilot_human_audit_model_blinded_worksheet_50.csv"
attestation_md="${artifact_dir}/audits/active_verification_human_audit_attestation.md"

if [ ! -d "$eha_dir" ]; then
  echo "Missing eha-mvp directory: ${eha_dir}" >&2
  echo "Set EHA_MVP_DIR if this artifact directory is not next to eha-mvp/." >&2
  exit 1
fi

if [ ! -f "$reference_csv" ]; then
  echo "Missing reference CSV: ${reference_csv}" >&2
  echo "Rebuild the active-verification audit package before finalizing labels." >&2
  exit 1
fi

if [ ! -f "$labels_csv" ]; then
  echo "Missing label CSV: ${labels_csv}" >&2
  exit 1
fi

cd "$eha_dir"

if [ "${1:-}" = "--from-worksheet" ]; then
  if [ ! -f "$worksheet_csv" ]; then
    echo "Missing worksheet CSV: ${worksheet_csv}" >&2
    exit 1
  fi
  uv run eha-step1-release import-active-verification-human-audit-worksheet \
    --worksheet-csv "$worksheet_csv" \
    --reference-csv "$reference_csv" \
    --out-csv "$labels_csv"
fi

if [ "${1:-}" = "--from-model-blinded-worksheet" ]; then
  if [ ! -f "$model_blinded_worksheet_csv" ]; then
    echo "Missing model-blinded worksheet CSV: ${model_blinded_worksheet_csv}" >&2
    exit 1
  fi
  uv run eha-step1-release import-active-verification-model-blinded-human-audit-worksheet \
    --worksheet-csv "$model_blinded_worksheet_csv" \
    --reference-csv "$reference_csv" \
    --out-csv "$labels_csv"
fi

uv run eha-step1-release finalize-active-verification-human-audit \
  --labels-csv "$labels_csv" \
  --reference-csv "$reference_csv" \
  --out-dir "$active_dir"

if [ ! -f "$attestation_md" ]; then
  echo "Missing human-audit attestation: ${attestation_md}" >&2
  exit 1
fi

cp "$attestation_md" "${active_dir}/active_verification_human_audit_attestation.md"

uv run eha-step1-release artifact-package \
  --task-dir data/epistemic-resilience-v1 \
  --frontier-main-dir results/reports-eha-frontier-main-opaque-2026-05-15 \
  --baseline-dir results/reports-eha-step1-baselines-2026-05-15 \
  --generated-lore-dir results/reports-eha-generated-lore-role-audit-opaque-2026-05-15 \
  --active-verification-dir "$active_dir" \
  --out-dir "$artifact_dir"

uv run eha-step1-release step1-readiness-check \
  --artifact-dir "$artifact_dir" \
  --paper-dir "$paper_dir" \
  --out-dir "$reports_dir"

if command -v python3 >/dev/null 2>&1 && [ -f "$readiness_json" ]; then
  python3 - "$readiness_json" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
status = payload.get("status", "missing")
failing = [
    gate.get("name", "<unnamed>")
    for gate in payload.get("gates", [])
    if gate.get("status") == "fail"
]
print(f"Step 1 readiness status: {status}")
print("Failing gates: " + (", ".join(failing) if failing else "none"))
PY
else
  echo "Step 1 readiness summary unavailable; inspect ${readiness_json}."
fi

echo
echo "Human-audit finalization commands completed."
echo "Inspect ${readiness_json} before changing paper claims."
