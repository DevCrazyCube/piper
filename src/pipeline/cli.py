"""Aegis pipeline CLI (ADR-0010). Usage: python -m pipeline ingest <source>."""

from __future__ import annotations

import typer

from pipeline.ingest.base import Connector, run_ingest
from pipeline.ingest.openfoodfacts import OpenFoodFactsConnector
from pipeline.ingest.pmdata import PMDataConnector
from pipeline.ingest.uci_academics import UCIAcademicsConnector
from pipeline.ingest.uci_performance import UCIPerformanceConnector

app = typer.Typer(help="Aegis — Responsible Learning Analytics Pipeline", no_args_is_help=True)

_CONNECTORS: dict[str, type[Connector]] = {
    "pmdata": PMDataConnector,
    "uci-performance": UCIPerformanceConnector,
    "uci-academics": UCIAcademicsConnector,
    "openfoodfacts": OpenFoodFactsConnector,
}


@app.command()
def ingest(
    source: str = typer.Argument(..., help=f"One of: {', '.join(_CONNECTORS)}, or 'all'"),
) -> None:
    """Ingest a source's raw data into the raw zone."""
    targets = list(_CONNECTORS) if source == "all" else [source]
    for name in targets:
        if name not in _CONNECTORS:
            raise typer.BadParameter(f"unknown source '{name}'. Choices: {', '.join(_CONNECTORS)}, all")
    for name in targets:
        ctx = run_ingest(_CONNECTORS[name]())
        typer.echo(
            f"[{name}] in={ctx.rows_in} out={ctx.rows_out} quarantined={ctx.rows_quarantined}"
        )


if __name__ == "__main__":
    app()
