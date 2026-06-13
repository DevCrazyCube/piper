# ADR-0001 — Record architecture decisions

- **Status:** accepted
- **Date:** 2026-06-13
- **Deciders:** Joyren, Claude

## Context
The group's existing presentation was AI-generated from little input and isn't a reliable
spec. To avoid hallucinated scope and to keep the team aligned, significant decisions must be
written down with their rationale and the alternatives we rejected.

## Decision
Use lightweight ADRs in `docs/adr/`, numbered, in the format of `0000-template.md`. Any decision
that changes architecture, tech, security posture, or scope gets an ADR.

## Consequences
- Positive: defensible choices for grading; new teammates can catch up; decisions are traceable.
- Negative: small overhead per decision.

## Alternatives considered
- Only prose docs — harder to see *why* and *what was rejected*.
