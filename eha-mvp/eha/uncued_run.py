from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console


app = typer.Typer(add_completion=False, help="Run EHA-Uncued pilot model calls after pre-model gates pass.")
console = Console()


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Pilot dataset directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Run output directory."),
    models: str = typer.Option("", help="Comma-separated model list."),
    views: str = typer.Option("neutral_metadata_visible,neutral_metadata_hidden", help="Comma-separated views."),
    schema: str = typer.Option("clarified", help="Schema variant."),
    prompt: str = typer.Option("standard_answer", help="Prompt condition."),
    hard_cap_usd: float = typer.Option(15.0, help="Hard cost cap."),
) -> None:
    _ = (dataset_dir, out_dir, models, views, schema, prompt, hard_cap_usd)
    raise typer.BadParameter("EHA-Uncued pilot model calls are blocked until Phase 9-11 gates are complete.")

