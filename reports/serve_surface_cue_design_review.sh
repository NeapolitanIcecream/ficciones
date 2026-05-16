#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

port="${1:-8766}"
review_path="surface_cue_design_review.html"
url="http://127.0.0.1:${port}/${review_path}"

if [ ! -f "$review_path" ]; then
  echo "Missing ${review_path}. Rebuild the surface-cue design-review package first." >&2
  exit 1
fi

echo "Serving EHA surface-cue design-review page at:"
echo "  ${url}"
echo
echo "Press Ctrl-C here after the reviewer downloads surface_cue_design_review_worksheet.csv."

if command -v open >/dev/null 2>&1; then
  open "$url" >/dev/null 2>&1 || true
fi

python3 -m http.server "$port" --bind 127.0.0.1
