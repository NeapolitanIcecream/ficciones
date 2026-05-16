from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import typer
from rich.console import Console

from .phase2_retrieval import retrieve
from .schemas import AgentDocument, GoldDocument, Task, by_task, write_json
from .surface_cue_generate import SURFACE_CUE_AXES
from .surface_cue_report import (
    action_target_violations,
    load_surface_cue_dataset,
    parse_surface_claim_id,
    visible_leakage_count,
)


app = typer.Typer(add_completion=False, help="Build human design-review packets for EHA Step 2 surface-cue pairs.")
console = Console()


DESIGN_REVIEW_LABEL_FIELDS = [
    "intended_cue_changed_only",
    "verdict_and_evidence_contract_preserved",
    "hidden_label_leakage_found",
    "retrieval_observability_ok",
    "action_target_contract_ok",
    "suitable_for_small_api_pilot",
]
DESIGN_REVIEW_FIELDNAMES = [
    "target_claim_id",
    "family",
    "template_id",
    "surface_axis",
    "condition_a",
    "condition_b",
    "task_id_a",
    "task_id_b",
    "question_a",
    "question_b",
    "gold_verdict",
    "scope_tag",
    "answer_brief",
    "primary_support_count_a",
    "primary_support_count_b",
    "contaminated_doc_count_a",
    "contaminated_doc_count_b",
    "doc_summary_a",
    "doc_summary_b",
    "auto_pair_contract_ok",
    "auto_retrieval_observability_ok",
    "auto_action_target_contract_ok",
    "auto_visible_leakage_count",
    "review_status",
    *DESIGN_REVIEW_LABEL_FIELDS,
    "reviewer_notes",
]


def doc_summary(docs: Sequence[AgentDocument]) -> str:
    return " ; ".join(f"{doc.doc_id}:{doc.source_type}:{doc.title}" for doc in docs)


def contaminated_count(gold_docs: Sequence[GoldDocument]) -> int:
    return sum(1 for gold in gold_docs if gold.is_contaminated)


def retrieved_contract_ok(task: Task, docs: Sequence[AgentDocument], gold_docs: Sequence[GoldDocument]) -> bool:
    hits = retrieve(task.question, docs, gold_docs, "bm25_top8")
    hit_ids = {hit.doc.doc_id for hit in hits}
    gold_by_id = {gold.doc_id: gold for gold in gold_docs}
    clean_ok = bool(set(task.gold.primary_support) & hit_ids) if task.gold.primary_support else not any(gold.supports_gold_verdict for gold in gold_docs)
    contaminated_ok = any(gold_by_id[doc_id].is_contaminated for doc_id in hit_ids)
    return clean_ok and contaminated_ok


def pair_contract_ok(pair: Sequence[Task]) -> bool:
    verdicts = {task.gold.verdict for task in pair}
    answers = {task.gold.answer_brief for task in pair}
    risks = {tuple(task.gold.critical_risks) for task in pair}
    axes = {parse_surface_claim_id(task.target_claim_id)[2] for task in pair}
    return len(pair) == 2 and len(verdicts) == 1 and len(answers) == 1 and len(risks) == 1 and len(axes) == 1


def build_surface_cue_design_review_rows(
    tasks: Sequence[Task],
    documents: Sequence[AgentDocument],
    gold_documents: Sequence[GoldDocument],
    action_rows: Sequence[Mapping[str, Any]],
) -> List[Dict[str, str]]:
    docs_by_task = by_task(documents)
    gold_by_task = by_task(gold_documents)
    tasks_by_claim: Dict[str, List[Task]] = defaultdict(list)
    for task in tasks:
        tasks_by_claim[task.target_claim_id].append(task)
    action_violation_ids = {str(row.get("task_id")) for row in action_target_violations(list(tasks), list(documents), list(action_rows))}

    rows: List[Dict[str, str]] = []
    for claim_id, pair in sorted(tasks_by_claim.items()):
        family, template_id, axis = parse_surface_claim_id(claim_id)
        sorted_pair = sorted(pair, key=lambda task: task.task_id)
        task_a, task_b = sorted_pair
        conditions = SURFACE_CUE_AXES[axis]
        docs_a = docs_by_task[task_a.task_id]
        docs_b = docs_by_task[task_b.task_id]
        gold_a = gold_by_task[task_a.task_id]
        gold_b = gold_by_task[task_b.task_id]
        action_ok = task_a.task_id not in action_violation_ids and task_b.task_id not in action_violation_ids
        leakage_count = visible_leakage_count(sorted_pair, docs_a + docs_b)
        row = {
            "target_claim_id": claim_id,
            "family": family,
            "template_id": template_id,
            "surface_axis": axis,
            "condition_a": conditions[0],
            "condition_b": conditions[1],
            "task_id_a": task_a.task_id,
            "task_id_b": task_b.task_id,
            "question_a": task_a.question,
            "question_b": task_b.question,
            "gold_verdict": task_a.gold.verdict,
            "scope_tag": task_a.gold.scope_tag,
            "answer_brief": task_a.gold.answer_brief,
            "primary_support_count_a": str(len(task_a.gold.primary_support)),
            "primary_support_count_b": str(len(task_b.gold.primary_support)),
            "contaminated_doc_count_a": str(contaminated_count(gold_a)),
            "contaminated_doc_count_b": str(contaminated_count(gold_b)),
            "doc_summary_a": doc_summary(docs_a),
            "doc_summary_b": doc_summary(docs_b),
            "auto_pair_contract_ok": "yes" if pair_contract_ok(sorted_pair) else "no",
            "auto_retrieval_observability_ok": "yes" if retrieved_contract_ok(task_a, docs_a, gold_a) and retrieved_contract_ok(task_b, docs_b, gold_b) else "no",
            "auto_action_target_contract_ok": "yes" if action_ok else "no",
            "auto_visible_leakage_count": str(leakage_count),
            "review_status": "not_started",
            **{field: "" for field in DESIGN_REVIEW_LABEL_FIELDS},
            "reviewer_notes": "",
        }
        rows.append(row)
    return rows


def validate_surface_cue_design_review_rows(rows: Sequence[Mapping[str, str]]) -> Dict[str, Any]:
    missing_label_cells = 0
    invalid_label_cells = 0
    missing_notes = 0
    reviewed = 0
    for row in rows:
        row_complete = True
        for field in DESIGN_REVIEW_LABEL_FIELDS:
            value = str(row.get(field, "")).strip().lower()
            if not value:
                missing_label_cells += 1
                row_complete = False
            elif value not in {"yes", "no"}:
                invalid_label_cells += 1
                row_complete = False
        if not str(row.get("reviewer_notes", "")).strip():
            missing_notes += 1
            row_complete = False
        if str(row.get("review_status", "")).strip().lower() != "reviewed":
            row_complete = False
        if row_complete:
            reviewed += 1
    status = "complete" if reviewed == len(rows) and missing_label_cells == 0 and invalid_label_cells == 0 and missing_notes == 0 else "incomplete"
    return {
        "status": status,
        "n_pairs": len(rows),
        "n_reviewed": reviewed,
        "missing_label_cells": missing_label_cells,
        "invalid_label_cells": invalid_label_cells,
        "missing_notes": missing_notes,
        "required_label_fields": list(DESIGN_REVIEW_LABEL_FIELDS),
    }


def write_csv_rows(path: Path, rows: Sequence[Mapping[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DESIGN_REVIEW_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_surface_cue_design_review_packet(summary: Mapping[str, Any], rows: Sequence[Mapping[str, str]]) -> str:
    examples = list(rows)[:6]
    lines = [
        "# EHA Step 2 Surface-Cue Design Review Packet",
        "",
        "Date: 2026-05-16",
        "",
        "This packet is for human design review of the no-API surface-cue smoke dataset. It is not model evidence and does not replace the Step 1 active-verification human audit.",
        "",
        "Do not copy labels from model outputs. Review the paired tasks and document summaries directly.",
        "",
        "## Review Goal",
        "",
        "For each pair, decide whether the paired rows preserve the same target claim, verdict, evidence contract, retrieval observability, and action-target contract while changing only the intended visible surface cue.",
        "",
        "## Required Labels",
        "",
    ]
    for field in DESIGN_REVIEW_LABEL_FIELDS:
        lines.append(f"- `{field}`: yes/no")
    lines.extend(
        [
            "- `review_status`: set to `reviewed` after all labels and notes are filled",
            "- `reviewer_notes`: required for every pair, including clean passes",
            "",
            "## Current Status",
            "",
            f"- Status: `{summary['status']}`",
            f"- Pair rows: {summary['n_pairs']}",
            f"- Reviewed pairs: {summary['n_reviewed']}",
            f"- Missing label cells: {summary['missing_label_cells']}",
            f"- Missing notes: {summary['missing_notes']}",
            "",
            "## Example Pair Rows",
            "",
            "| family | template | axis | condition_a | condition_b | task_id_a | task_id_b | verdict |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in examples:
        lines.append(
            f"| {row['family']} | {row['template_id']} | {row['surface_axis']} | {row['condition_a']} | {row['condition_b']} | {row['task_id_a']} | {row['task_id_b']} | {row['gold_verdict']} |"
        )
    lines.extend(
        [
            "",
            "## Go / No-Go Rule",
            "",
            "A small API pilot should not run from this dataset until all pair rows are reviewed, every required label is present, notes are nonblank, and any `no` labels have been triaged into either generator fixes or explicit documented limitations.",
            "",
        ]
    )
    return "\n".join(lines)


def build_surface_cue_design_review_html(summary: Mapping[str, Any], rows: Sequence[Mapping[str, str]]) -> str:
    rows_json = json.dumps(list(rows), ensure_ascii=False)
    fieldnames_json = json.dumps(DESIGN_REVIEW_FIELDNAMES)
    label_fields_json = json.dumps(DESIGN_REVIEW_LABEL_FIELDS)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>EHA Surface-Cue Design Review</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{ color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    body {{ margin: 0; background: #f7f7f4; color: #1f2933; }}
    header {{ position: sticky; top: 0; z-index: 2; background: #ffffff; border-bottom: 1px solid #d7d7d0; padding: 14px 18px; }}
    h1 {{ font-size: 20px; margin: 0 0 8px; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
    select, button, input[type="file"] {{ font: inherit; min-height: 34px; }}
    button {{ border: 1px solid #9aa4ad; background: #fff; border-radius: 6px; padding: 6px 10px; cursor: pointer; }}
    button:disabled {{ color: #8b949e; cursor: not-allowed; }}
    main {{ max-width: 1280px; margin: 0 auto; padding: 16px; }}
    .status {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0 0; font-size: 13px; }}
    .pill {{ border: 1px solid #c9d1d9; border-radius: 999px; padding: 3px 8px; background: #fafafa; }}
    .pair {{ background: #fff; border: 1px solid #d7d7d0; border-radius: 8px; margin: 12px 0; padding: 14px; }}
    .pair h2 {{ font-size: 16px; margin: 0 0 10px; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
    .task {{ border: 1px solid #e0e0dc; border-radius: 6px; padding: 10px; background: #fbfbf9; }}
    .task h3 {{ font-size: 14px; margin: 0 0 8px; }}
    .meta {{ font-size: 13px; color: #4b5563; line-height: 1.45; }}
    .labels {{ display: grid; grid-template-columns: repeat(3, minmax(160px, 1fr)); gap: 10px; margin-top: 12px; }}
    label {{ display: flex; flex-direction: column; gap: 4px; font-size: 13px; }}
    textarea {{ min-height: 64px; resize: vertical; font: inherit; }}
    .notes {{ margin-top: 10px; }}
    .hidden {{ display: none; }}
    @media (max-width: 760px) {{
      .grid, .labels {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>EHA Step 2 Surface-Cue Design Review</h1>
    <div class="toolbar">
      <select id="familyFilter"><option value="">All families</option></select>
      <select id="axisFilter"><option value="">All axes</option></select>
      <select id="statusFilter"><option value="">All statuses</option><option value="not_started">Not started</option><option value="reviewed">Reviewed</option></select>
      <button id="nextIncomplete">Next incomplete</button>
      <button id="downloadCsv">Download CSV</button>
      <label>Import CSV<input id="importCsv" type="file" accept=".csv,text/csv"></label>
    </div>
    <div class="status">
      <span class="pill" id="reviewStatus">Status: {summary.get('status', 'incomplete')}</span>
      <span class="pill" id="reviewedCount">Reviewed: {summary.get('n_reviewed', 0)} / {summary.get('n_pairs', len(rows))}</span>
      <span class="pill" id="missingLabels">Missing labels: {summary.get('missing_label_cells', 0)}</span>
      <span class="pill" id="missingNotes">Missing notes: {summary.get('missing_notes', 0)}</span>
      <span class="pill" id="pilotReady">Pilot ready: false</span>
    </div>
  </header>
  <main id="pairs"></main>
  <script id="reviewRows" type="application/json">{rows_json}</script>
  <script>
    const fieldnames = {fieldnames_json};
    const labelFields = {label_fields_json};
    let rows = JSON.parse(document.getElementById('reviewRows').textContent);
    const pairs = document.getElementById('pairs');
    const filters = {{
      family: document.getElementById('familyFilter'),
      axis: document.getElementById('axisFilter'),
      status: document.getElementById('statusFilter')
    }};

    function unique(values) {{ return [...new Set(values)].sort(); }}
    function optionize(select, values) {{
      for (const value of values) {{
        const option = document.createElement('option');
        option.value = value;
        option.textContent = value;
        select.appendChild(option);
      }}
    }}
    optionize(filters.family, unique(rows.map(row => row.family)));
    optionize(filters.axis, unique(rows.map(row => row.surface_axis)));

    function escapeHtml(value) {{
      return String(value ?? '').replace(/[&<>"']/g, char => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[char]));
    }}
    function isComplete(row) {{
      return row.review_status === 'reviewed' && row.reviewer_notes.trim() &&
        labelFields.every(field => ['yes', 'no'].includes(String(row[field] || '').toLowerCase()));
    }}
    function pilotReady() {{
      return rows.length > 0 && rows.every(row =>
        isComplete(row) &&
        row.intended_cue_changed_only === 'yes' &&
        row.verdict_and_evidence_contract_preserved === 'yes' &&
        row.hidden_label_leakage_found === 'no' &&
        row.retrieval_observability_ok === 'yes' &&
        row.action_target_contract_ok === 'yes' &&
        row.suitable_for_small_api_pilot === 'yes'
      );
    }}
    function updateStatus() {{
      const reviewed = rows.filter(isComplete).length;
      const missingLabels = rows.reduce((total, row) => total + labelFields.filter(field => !row[field]).length, 0);
      const missingNotes = rows.filter(row => !row.reviewer_notes.trim()).length;
      document.getElementById('reviewStatus').textContent = `Status: ${{reviewed === rows.length && missingLabels === 0 && missingNotes === 0 ? 'complete' : 'incomplete'}}`;
      document.getElementById('reviewedCount').textContent = `Reviewed: ${{reviewed}} / ${{rows.length}}`;
      document.getElementById('missingLabels').textContent = `Missing labels: ${{missingLabels}}`;
      document.getElementById('missingNotes').textContent = `Missing notes: ${{missingNotes}}`;
      document.getElementById('pilotReady').textContent = `Pilot ready: ${{pilotReady()}}`;
    }}
    function rowVisible(row) {{
      return (!filters.family.value || row.family === filters.family.value) &&
        (!filters.axis.value || row.surface_axis === filters.axis.value) &&
        (!filters.status.value || row.review_status === filters.status.value);
    }}
    function labelSelect(row, index, field) {{
      return `<label>${{field}}<select data-index="${{index}}" data-field="${{field}}"><option value=""></option><option value="yes" ${{row[field] === 'yes' ? 'selected' : ''}}>yes</option><option value="no" ${{row[field] === 'no' ? 'selected' : ''}}>no</option></select></label>`;
    }}
    function render() {{
      pairs.innerHTML = '';
      rows.forEach((row, index) => {{
        if (!rowVisible(row)) return;
        const article = document.createElement('article');
        article.className = 'pair';
        article.id = `pair-${{index}}`;
        article.innerHTML = `
          <h2>${{escapeHtml(row.family)}} / ${{escapeHtml(row.template_id)}} / ${{escapeHtml(row.surface_axis)}}</h2>
          <div class="meta">Claim: <code>${{escapeHtml(row.target_claim_id)}}</code> | verdict: <strong>${{escapeHtml(row.gold_verdict)}}</strong> | scope: ${{escapeHtml(row.scope_tag)}} | auto checks: pair=${{escapeHtml(row.auto_pair_contract_ok)}}, retrieval=${{escapeHtml(row.auto_retrieval_observability_ok)}}, action=${{escapeHtml(row.auto_action_target_contract_ok)}}, leakage=${{escapeHtml(row.auto_visible_leakage_count)}}</div>
          <div class="grid">
            <section class="task"><h3>${{escapeHtml(row.condition_a)}} / ${{escapeHtml(row.task_id_a)}}</h3><p>${{escapeHtml(row.question_a)}}</p><p class="meta">${{escapeHtml(row.doc_summary_a)}}</p></section>
            <section class="task"><h3>${{escapeHtml(row.condition_b)}} / ${{escapeHtml(row.task_id_b)}}</h3><p>${{escapeHtml(row.question_b)}}</p><p class="meta">${{escapeHtml(row.doc_summary_b)}}</p></section>
          </div>
          <p class="meta">Answer brief: ${{escapeHtml(row.answer_brief)}}</p>
          <div class="labels">${{labelFields.map(field => labelSelect(row, index, field)).join('')}}</div>
          <label class="notes">review_status<select data-index="${{index}}" data-field="review_status"><option value="not_started" ${{row.review_status !== 'reviewed' ? 'selected' : ''}}>not_started</option><option value="reviewed" ${{row.review_status === 'reviewed' ? 'selected' : ''}}>reviewed</option></select></label>
          <label class="notes">reviewer_notes<textarea data-index="${{index}}" data-field="reviewer_notes">${{escapeHtml(row.reviewer_notes)}}</textarea></label>
        `;
        pairs.appendChild(article);
      }});
      updateStatus();
    }}
    pairs.addEventListener('change', event => {{
      const target = event.target;
      if (target.dataset && target.dataset.field) {{
        rows[Number(target.dataset.index)][target.dataset.field] = target.value;
        updateStatus();
      }}
    }});
    pairs.addEventListener('input', event => {{
      const target = event.target;
      if (target.dataset && target.dataset.field) {{
        rows[Number(target.dataset.index)][target.dataset.field] = target.value;
        updateStatus();
      }}
    }});
    Object.values(filters).forEach(select => select.addEventListener('change', render));
    document.getElementById('nextIncomplete').addEventListener('click', () => {{
      const index = rows.findIndex(row => !isComplete(row));
      if (index >= 0) document.getElementById(`pair-${{index}}`)?.scrollIntoView({{behavior: 'smooth', block: 'start'}});
    }});
    function csvEscape(value) {{
      const text = String(value ?? '');
      return /[",\\n]/.test(text) ? `"${{text.replace(/"/g, '""')}}"` : text;
    }}
    function downloadCsv() {{
      const csv = [fieldnames.join(','), ...rows.map(row => fieldnames.map(field => csvEscape(row[field] || '')).join(','))].join('\\n') + '\\n';
      const blob = new Blob([csv], {{type: 'text/csv'}});
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'surface_cue_design_review_worksheet.csv';
      link.click();
      URL.revokeObjectURL(link.href);
    }}
    document.getElementById('downloadCsv').addEventListener('click', downloadCsv);
    function parseCsvLine(line) {{
      const cells = [];
      let current = '';
      let quoted = false;
      for (let i = 0; i < line.length; i++) {{
        const char = line[i];
        if (char === '"' && quoted && line[i + 1] === '"') {{ current += '"'; i++; }}
        else if (char === '"') quoted = !quoted;
        else if (char === ',' && !quoted) {{ cells.push(current); current = ''; }}
        else current += char;
      }}
      cells.push(current);
      return cells;
    }}
    function importCsv(text) {{
      const lines = text.split(/\\r?\\n/).filter(line => line.length);
      const header = parseCsvLine(lines[0]);
      rows = lines.slice(1).map(line => {{
        const cells = parseCsvLine(line);
        const row = {{}};
        header.forEach((field, index) => row[field] = cells[index] || '');
        return row;
      }});
      render();
    }}
    document.getElementById('importCsv').addEventListener('change', event => {{
      const file = event.target.files[0];
      if (!file) return;
      file.text().then(importCsv);
    }});
    render();
  </script>
</body>
</html>
"""


def build_surface_cue_design_review_launcher() -> str:
    return """#!/usr/bin/env bash
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
"""


def write_surface_cue_design_review_package(dataset_dir: Path, out_dir: Path) -> Dict[str, Any]:
    tasks, documents, gold_documents, action_rows = load_surface_cue_dataset(dataset_dir)
    rows = build_surface_cue_design_review_rows(tasks, documents, gold_documents, action_rows)
    summary = validate_surface_cue_design_review_rows(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(out_dir / "surface_cue_design_review_worksheet.csv", rows)
    write_json(out_dir / "eha_step2_surface_cue_design_review_manifest.json", summary)
    (out_dir / "eha-step2-surface-cue-design-review-packet-2026-05-16.md").write_text(
        build_surface_cue_design_review_packet(summary, rows),
        encoding="utf-8",
    )
    (out_dir / "surface_cue_design_review.html").write_text(
        build_surface_cue_design_review_html(summary, rows),
        encoding="utf-8",
    )
    launcher_path = out_dir / "serve_surface_cue_design_review.sh"
    launcher_path.write_text(build_surface_cue_design_review_launcher(), encoding="utf-8")
    launcher_path.chmod(0o755)
    return summary


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/phase2-surface-cue-smoke"), help="Surface-cue dataset directory."),
    out_dir: Path = typer.Option(Path("../reports"), help="Output report directory."),
) -> None:
    summary = write_surface_cue_design_review_package(dataset_dir, out_dir)
    console.print(
        f"[green]Wrote[/green] surface-cue design-review package with {summary['n_pairs']} pair rows to {out_dir}; status={summary['status']}"
    )


if __name__ == "__main__":
    app()
