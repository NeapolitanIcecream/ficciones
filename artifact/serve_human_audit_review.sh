#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

port="${1:-8765}"
review_path="audits/active_verification_human_audit_review.html"
url="http://127.0.0.1:${port}/${review_path}"

if [ ! -f "$review_path" ]; then
  echo "Missing ${review_path}. Rebuild the artifact package first." >&2
  exit 1
fi

echo "Serving EHA active-verification human-audit review at:"
echo "  ${url}"
echo
echo "Press Ctrl-C here after the reviewer finishes downloading active_verification_human_audit.csv."

if command -v open >/dev/null 2>&1; then
  open "$url" >/dev/null 2>&1 || true
fi

python3 -m http.server "$port" --bind 127.0.0.1
