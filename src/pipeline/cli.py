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
def bootstrap() -> None:
    """Set the app-role password from AEGIS_APP_PASSWORD (run as admin, after migrate)."""
    from psycopg import sql

    from pipeline.common.config import get_settings
    from pipeline.common.db import pg_admin_connection

    pwd = get_settings().app_password.get_secret_value()
    if not pwd:
        raise typer.BadParameter("AEGIS_APP_PASSWORD is not set")
    user = get_settings().app_user
    with pg_admin_connection() as conn, conn.cursor() as cur:
        cur.execute(sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
            sql.Identifier(user), sql.Literal(pwd)))
    typer.echo(f"app role '{user}' password set; runtime now connects as non-superuser")


@app.command(name="register-device")
def register_device(
    device_id: str = typer.Argument(..., help="unique device id"),
    participant: str = typer.Argument(..., help="source-local subject id this device belongs to"),
    source: str = typer.Option("wearable-live", help="source name"),
) -> None:
    """Register a webhook device: ensures a subject, stores an encrypted HMAC secret."""
    import secrets as pysecrets

    from pipeline.common.crypto import aad_for, get_cipher
    from pipeline.common.db import pg_connection
    from pipeline.process.pseudonymise import get_or_create_subject

    secret = pysecrets.token_hex(32)
    device_cipher = get_cipher("device")
    enc = device_cipher.encrypt(secret.encode(), aad_for("device"))
    with pg_connection() as conn, conn.cursor() as cur:
        get_or_create_subject(cur, get_cipher("identity"), source, participant)
        cur.execute(
            "INSERT INTO meta.device (device_id, enc_secret, source, source_local_id) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (device_id) DO UPDATE SET enc_secret = EXCLUDED.enc_secret",
            (device_id, enc, source, participant),
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
def consent(
    action: str = typer.Argument(..., help="grant | revoke"),
    subject_pid: str = typer.Argument(..., help="subject_pid (UUID)"),
    scope: str = typer.Argument(..., help="sleep|heart_rate|activity|meals|grades|attendance"),
) -> None:
    """Grant/revoke consent for a scope; revoke also removes that scope's curated data."""
    from pipeline.common.db import pg_connection
    from pipeline.process.consent import set_consent

    status = {"grant": "granted", "revoke": "revoked"}.get(action)
    if status is None:
        raise typer.BadParameter("action must be 'grant' or 'revoke'")
    with pg_connection() as conn:
        removed = set_consent(conn, subject_pid, scope, status)
    typer.echo(f"[consent:{action}] {scope} for {subject_pid} — curated rows removed: {removed}")


@app.command()
def export(
    subject_pid: str = typer.Argument(..., help="subject_pid (UUID)"),
    out: str = typer.Option("", help="write JSON to this file instead of stdout"),
) -> None:
    """Export a subject's curated data as JSON (GDPR Art. 15 / 20)."""
    import json
    from pathlib import Path

    from pipeline.common.db import pg_connection
    from pipeline.process.export import export_subject

    with pg_connection() as conn:
        data = export_subject(conn, subject_pid)
    text = json.dumps(data, indent=2)
    if out:
        Path(out).write_text(text)
        typer.echo(f"wrote {out}")
    else:
        typer.echo(text)


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
