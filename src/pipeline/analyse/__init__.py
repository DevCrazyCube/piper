"""Phase 5 — analytics. Aggregate-only queries over the curated zone (no raw identifiers).

Each query stays within ONE domain (ADR-0009): health (PMData) or academic (UCI). Group
results apply a k-anonymity HAVING floor so no tiny group can single out an individual.
"""
