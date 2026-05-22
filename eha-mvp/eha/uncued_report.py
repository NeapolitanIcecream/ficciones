from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console


app = typer.Typer(add_completion=False, help="Report EHA-Uncued pilot model results.")
console = Console()


@app.command()
def main(
    dataset_dir: Path = typer.Option(Path("data/uncued-pilot-v1"), help="Pilot dataset directory."),
    run_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Pilot run directory."),
    out_dir: Path = typer.Option(Path("results/reports-eha-uncued-pilot-2026-05-22"), help="Report output directory."),
) -> None:
    _ = (dataset_dir, run_dir, out_dir)
    raise typer.BadParameter("No EHA-Uncued pilot run exists yet; reporting starts after Phase 12.")

