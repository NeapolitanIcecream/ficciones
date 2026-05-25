from __future__ import annotations

import csv
import json
import textwrap
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import typer
from rich.console import Console


app = typer.Typer(add_completion=False, help="Extract concise EHA-Uncued task and scoring examples.")
console = Console()

EXAMPLE_ORDER = ("clean_or_buried_primary", "generated_lore_hygiene_failure", "active_verification")
VIEW_FILES = {
    "neutral_metadata_hidden": "documents_neutral_metadata_hidden.jsonl",
    "neutral_metadata_visible": "documents_neutral_metadata_visible.jsonl",
}


def read_jsonl(path: Path) -> list[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_scored_rows(results_dir: Path) -> list[Dict[str, str]]:
    with (results_dir / "uncued_pilot_scored_predictions.csv").open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def base_task_id(row: Mapping[str, Any]) -> str:
    if row.get("base_task_id"):
        return str(row["base_task_id"])
    task_id = str(row["task_id"])
    for suffix in ("_visible", "_hidden"):
        if task_id.endswith(suffix):
            return task_id[: -len(suffix)]
    return task_id


def parse_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def find_example_rows(rows: Sequence[Mapping[str, str]]) -> Dict[str, Mapping[str, str]]:
    clean_or_buried = next(
        row
        for row in rows
        if row["family"] == "packet_judgment"
        and row["condition"] in {"clean", "buried_primary"}
        and parse_float(row["operational_epistemic_escape"]) == 1.0
    )
    generated_failure = next(
        row
        for row in rows
        if row["condition"] == "generated_lore"
        and parse_float(row["belief_correctness"]) == 1.0
        and parse_float(row["operational_epistemic_escape"]) == 0.0
        and parse_float(row["polluted_support_rate"]) > 0.0
    )
    active = next(
        row
        for row in rows
        if row["family"] == "active_verification"
        and row["condition"] in {"generated_lore", "conflicting_evidence", "buried_primary", "false_consensus", "clean"}
    )
    return {
        "clean_or_buried_primary": clean_or_buried,
        "generated_lore_hygiene_failure": generated_failure,
        "active_verification": active,
    }


def load_prediction_map(results_dir: Path) -> Dict[tuple[str, str], Mapping[str, Any]]:
    predictions = {}
    for record in read_jsonl(results_dir / "predictions.jsonl"):
        predictions[(str(record["task_id"]), str(record["model"]))] = record
    return predictions


def load_documents_by_view(dataset_dir: Path) -> Dict[tuple[str, str], list[Mapping[str, Any]]]:
    output: Dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for view, filename in VIEW_FILES.items():
        for doc in read_jsonl(dataset_dir / filename):
            output.setdefault((view, str(doc["task_id"])), []).append(doc)
    return output


def load_gold_roles(dataset_dir: Path) -> Dict[tuple[str, str, str], Mapping[str, Any]]:
    roles = {}
    for row in read_jsonl(dataset_dir / "gold_documents.jsonl"):
        roles[(str(row["view"]), str(row["task_id"]), str(row["doc_id"]))] = row
    return roles


def load_latent_tasks(dataset_dir: Path) -> Dict[str, Mapping[str, Any]]:
    return {str(row["task_id"]): row for row in read_jsonl(dataset_dir / "latent_tasks.jsonl")}


def load_action_gold(dataset_dir: Path) -> Dict[str, Mapping[str, Any]]:
    path = dataset_dir / "action_gold.jsonl"
    if not path.exists():
        return {}
    return {str(row["task_id"]): row for row in read_jsonl(path)}


def truncate(text: str, width: int = 210) -> str:
    text = " ".join(text.split())
    return textwrap.shorten(text, width=width, placeholder="...")


def decode_json_field(value: str) -> Any:
    if not value:
        return []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def example_payloads(
    *,
    dataset_dir: Path,
    results_dir: Path,
) -> list[Dict[str, Any]]:
    rows = load_scored_rows(results_dir)
    selected = find_example_rows(rows)
    predictions = load_prediction_map(results_dir)
    docs_by_view = load_documents_by_view(dataset_dir)
    gold_roles = load_gold_roles(dataset_dir)
    latent_tasks = load_latent_tasks(dataset_dir)
    action_gold = load_action_gold(dataset_dir)

    payloads: list[Dict[str, Any]] = []
    for label in EXAMPLE_ORDER:
        row = selected[label]
        task_id = base_task_id(row)
        view = str(row["view"])
        prediction_record = predictions[(str(row["task_id"]), str(row["model"]))]
        prediction = prediction_record["prediction"]
        docs = docs_by_view[(view, task_id)]
        doc_rows = []
        for doc in docs:
            role = gold_roles.get((view, task_id, str(doc["doc_id"])), {})
            doc_rows.append(
                {
                    "doc_id": doc["doc_id"],
                    "title": doc.get("title", ""),
                    "source_type": doc.get("source_type", ""),
                    "timestamp": doc.get("timestamp", ""),
                    "hidden_role": role.get("hidden_role", ""),
                    "supports_gold_verdict": role.get("supports_gold_verdict", ""),
                    "contamination": ",".join(role.get("contamination", [])),
                    "body": truncate(str(doc.get("body", ""))),
                }
            )
        payloads.append(
            {
                "label": label,
                "row": dict(row),
                "latent_task": latent_tasks[task_id],
                "action_gold": action_gold.get(task_id, {}),
                "prediction": prediction,
                "documents": doc_rows,
                "decoded_actions": decode_json_field(str(row.get("actions", ""))),
            }
        )
    return payloads


def markdown_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> list[str]:
    if not rows:
        return ["_No rows._"]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def write_markdown(path: Path, payloads: Sequence[Mapping[str, Any]]) -> None:
    titles = {
        "clean_or_buried_primary": "Clean/Buried-Primary Success",
        "generated_lore_hygiene_failure": "Generated-Lore Hygiene Failure",
        "active_verification": "Active-Verification Action Case",
    }
    lines = [
        "# EHA-Uncued Task And Scoring Examples",
        "",
        "Date: 2026-05-25",
        "",
        "Hidden roles in these examples are shown only for reader auditability. They are scorer-only fields and were not model-visible.",
        "",
    ]
    for payload in payloads:
        row = payload["row"]
        latent = payload["latent_task"]
        prediction = payload["prediction"]
        lines.extend(
            [
                f"## {titles[payload['label']]}",
                "",
                f"- Task: `{row['task_id']}` / latent `{latent['task_id']}`.",
                f"- Family/condition/view: `{row['family']}` / `{row['condition']}` / `{row['view']}`.",
                f"- Question: {latent['question']}",
                f"- Model: `{row['model']}`.",
                f"- Gold/predicted verdict: `{row['gold_verdict']}` / `{row['predicted_verdict']}`.",
                f"- Supporting evidence: `{row.get('supporting_evidence', '') or '-'}`.",
                f"- Selected docs: `{row.get('selected_doc_ids', '') or '-'}`.",
                f"- Actions: `{json.dumps(payload['decoded_actions'], ensure_ascii=False)}`.",
                f"- Scorer components: belief `{float(row['belief_correctness']):.3f}`, evidence precision `{parse_float(row.get('evidence_precision')):.3f}`, polluted support `{float(row['polluted_support_rate']):.3f}`, required action recall `{row.get('required_action_recall') or 'n/a'}`, operational escape `{float(row['operational_epistemic_escape']):.3f}`.",
                f"- Model answer: {truncate(str(prediction.get('answer', '')), 260)}",
                "",
                "### Abbreviated Packet",
                "",
                *markdown_table(
                    payload["documents"],
                    ["doc_id", "title", "source_type", "timestamp", "hidden_role", "supports_gold_verdict", "contamination", "body"],
                ),
                "",
            ]
        )
        if payload["action_gold"]:
            lines.extend(["### Action Gold", "", "```json", json.dumps(payload["action_gold"], ensure_ascii=False, indent=2), "```", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def latex_escape(value: Any) -> str:
    text = (
        str(value)
        .replace("\u2014", "---")
        .replace("\u2013", "--")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def latex_code(value: Any) -> str:
    text = str(value)
    return text.replace("\\", r"\textbackslash{}").replace("{", r"\{").replace("}", r"\}")


def latex_label(label: str) -> str:
    return label.replace("_", "-")


def write_latex(path: Path, payloads: Sequence[Mapping[str, Any]]) -> None:
    titles = {
        "clean_or_buried_primary": "Clean Or Buried-Primary Success",
        "generated_lore_hygiene_failure": "Correct Belief With Failed Evidence Hygiene",
        "active_verification": "Active-Verification Action Case",
    }
    lines = [
        r"\section{Task And Scoring Examples}",
        r"\label{app:task-examples}",
        "",
        "The examples below expose scorer-only roles for auditability. These roles were not visible to models; model-visible packets contained only the neutral document fields.",
        "",
    ]
    for payload in payloads:
        row = payload["row"]
        latent = payload["latent_task"]
        prediction = payload["prediction"]
        lines.extend(
            [
                rf"\subsection{{{latex_escape(titles[payload['label']])}}}",
                rf"\label{{app:example-{latex_label(payload['label'])}}}",
                r"\begin{description}",
                rf"    \item[Task] \code{{{latex_code(row['task_id'])}}}; family \code{{{latex_code(row['family'])}}}, condition \code{{{latex_code(row['condition'])}}}, view \code{{{latex_code(row['view'])}}}.",
                rf"    \item[Question] {latex_escape(latent['question'])}",
                rf"    \item[Model] \code{{{latex_code(row['model'])}}}. Gold verdict \code{{{latex_code(row['gold_verdict'])}}}; predicted verdict \code{{{latex_code(row['predicted_verdict'])}}}.",
                rf"    \item[Output fields] Support \code{{{latex_code(row.get('supporting_evidence', '') or '-')}}}; selected \code{{{latex_code(row.get('selected_doc_ids', '') or '-')}}}; actions {latex_escape(truncate(json.dumps(payload['decoded_actions'], ensure_ascii=False), 260))}.",
                rf"    \item[Scorer decision] Belief {float(row['belief_correctness']):.3f}; evidence precision {parse_float(row.get('evidence_precision')):.3f}; polluted support {float(row['polluted_support_rate']):.3f}; required action recall {latex_escape(row.get('required_action_recall') or 'n/a')}; operational escape {float(row['operational_epistemic_escape']):.3f}.",
                rf"    \item[Answer excerpt] {latex_escape(truncate(str(prediction.get('answer', '')), 240))}",
                r"\end{description}",
                "",
                r"\begin{quote}\small",
            ]
        )
        for doc in payload["documents"]:
            role_bits = [
                rf"role=\code{{{latex_code(doc['hidden_role'])}}}",
                f"supports={latex_escape(doc['supports_gold_verdict'])}",
            ]
            if doc["contamination"]:
                role_bits.append(rf"contamination=\code{{{latex_code(doc['contamination'])}}}")
            lines.append(
                rf"\textbf{{\code{{{latex_code(doc['doc_id'])}}}}} "
                rf"({latex_escape(doc['title'])}; {latex_escape(doc['source_type'])}; {latex_escape(doc['timestamp'])}; "
                + ", ".join(role_bits)
                + rf"): {latex_escape(doc['body'])}\\"
            )
        lines.extend([r"\end{quote}", ""])
        if payload["action_gold"]:
            action_gold = payload["action_gold"]
            required_types = ", ".join(str(item) for item in action_gold.get("required_action_types", []))
            target_bits = [
                f"{view}: {', '.join(str(item) for item in targets)}"
                for view, targets in action_gold.get("required_target_doc_ids_by_view", {}).items()
            ]
            lines.extend(
                [
                    rf"\noindent Required action types: {latex_escape(required_types)}. Required target documents by view: {latex_escape('; '.join(target_bits))}.",
                    "",
                ]
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Pilot dataset directory."),
    results_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Pilot result directory."),
    markdown_out: Path = typer.Option(Path("../reports/eha-uncued-task-examples-2026-05-25.md"), help="Markdown report path."),
    tex_out: Path = typer.Option(Path("../paper/appendices/task_examples.tex"), help="LaTeX appendix path."),
) -> None:
    payloads = example_payloads(dataset_dir=dataset_dir, results_dir=results_dir)
    write_markdown(markdown_out, payloads)
    write_latex(tex_out, payloads)
    console.print(f"[green]Wrote EHA-Uncued task examples[/green] to {markdown_out} and {tex_out}")


if __name__ == "__main__":
    app()
