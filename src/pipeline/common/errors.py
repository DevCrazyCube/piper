"""Pipeline exception types."""

from __future__ import annotations


class PipelineError(Exception):
    """Base class for all pipeline errors."""


class ConfigError(PipelineError):
    """Misconfiguration (missing secret, bad DSN, etc.)."""


class RecordValidationError(PipelineError):
    """A single record failed validation.

    Raised by connectors per-row; the runner catches it and writes the offending
    value to the quarantine / dead-letter table instead of aborting the run
    (ADR-0010 — nothing is silently dropped).
    """

    def __init__(self, reason: str, *, field: str | None = None, raw: object = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.field = field
        self.raw = raw
