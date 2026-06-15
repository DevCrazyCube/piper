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


@app.command(name="register-device")
def register_device(
    device_id: str = typer.Argument(..., help="unique device id"),
    participant: str = typer.Argument(..., help="source-local subject id this device belongs to"),
    source: str = typer.Option("wearable-live", help="source name"),
) -> None:
    """Register a webhook device: ensures a subject, stores an encrypted HMAC secret."""
    import secrets as pysecrets

    from pipeline.common.crypto import get_cipher
    from pipeline.common.db import pg_connection
    from pipeline.process.pseudonymise import get_or_create_subject

    secret = pysecrets.token_hex(32)
    cipher = get_cipher()
    with pg_connection() as conn, conn.cursor() as cur:
        get_or_create_subject(cur, cipher, source, participant)
        cur.execute(
            "INSERT INTO meta.device (device_id, enc_secret, source, source_local_id) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (device_id) DO UPDATE SET enc_secret = EXCLUDED.enc_secret",
            (device_id, cipher.encrypt(secret.encode()), source, participant),
        )
    typer.echo(f"registered device '{device_id}' -> {source}/{participant}")
    typer.echo(f"SECRET (shown once, store it on the device): {secret}")


@app.command()
def analyse(
    query: str = typer.Argument("all", help="q1..q5 or all"),
) -> None:
    """Phase 5: run the aggregate-only analytics queries over the curated zone."""
    from pipeline.analyse.queries import QUERIES, run_query
    from pipeline.common.db import pg_connection

    by_key = {q.key: q for q in QUERIES}
    targets = QUERIES if query == "all" else [by_key[query]] if query in by_key else None
    if targets is None:
        raise typer.BadParameter(f"unknown query '{query}'. Choices: {', '.join(by_key)}, all")
    with pg_connection() as conn:
        for q in targets:
            cols, rows = run_query(conn, q)
            typer.echo(f"\n[{q.key}] {q.title}  (domain: {q.domain}, aggregate-only)")
            typer.echo("  " + " | ".join(cols))
            for r in rows:
                typer.echo("  " + " | ".join("" if v is None else str(v) for v in r))
            if not rows:
                typer.echo("  (no rows)")


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
