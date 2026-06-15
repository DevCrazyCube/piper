"""Aegis pipeline CLI (ADR-0010). Usage: python -m pipeline ingest <source>."""

from __future__ import annotations

import typer

from pipeline.ingest.base import Connector, run_ingest
from pipeline.ingest.openfoodfacts import OpenFoodFactsConnector
from pipeline.ingest.pmdata import PMDataConnector
from pipeline.ingest.uci_academics import UCIAcademicsConnector
from pipeline.ingest.uci_performance import UCIPerformanceConnector

app = typer.Typer(help="Aegis — Responsible Learning Analytics Pipeline", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Aegis — Responsible Learning Analytics Pipeline."""
    # Presence of a callback keeps subcommands (e.g. `ingest`) required.

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


@app.command()
def curate(
    domain: str = typer.Argument("all", help="health | academic | food | all"),
) -> None:
    """Phase 2: clean, pseudonymise, dedup, and harmonise raw -> curated zone."""
    from pipeline.common.db import pg_connection
    from pipeline.process.curate_academic import curate_academic
    from pipeline.process.curate_food import curate_food
    from pipeline.process.curate_health import curate_pmdata

    domains = {"health": curate_pmdata, "academic": curate_academic, "food": curate_food}
    targets = list(domains) if domain == "all" else [domain]
    for name in targets:
        if name not in domains:
            raise typer.BadParameter(f"unknown domain '{name}'. Choices: {', '.join(domains)}, all")
    for name in targets:
        with pg_connection() as conn:
            counts = domains[name](conn)
        typer.echo(f"[curate:{name}] {counts}")


@app.command()
def erase(subject_pid: str = typer.Argument(..., help="subject_pid (UUID) to erase")) -> None:
    """GDPR Art. 17: erase a subject across curated + raw + identity map; write a receipt."""
    from pipeline.common.db import pg_connection
    from pipeline.process.erase import erase_subject

    with pg_connection() as conn:
        counts = erase_subject(conn, subject_pid)
    typer.echo(f"[erase:{subject_pid}] {counts}")


if __name__ == "__main__":
    app()
