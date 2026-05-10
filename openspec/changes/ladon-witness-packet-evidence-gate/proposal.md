# Ladon Witness Packet Evidence Gate

## Why

Ladon originally helped review packets and witness artifacts, but that surface
was removed from the clean core. The literature review argues that analyzer
claims need evidence and validation context, not just warnings.

## What

- Reintroduce `--packet-dir` as a clean-core, generic evidence inspection flag.
- Summarize whether packet directories contain metadata, witness JSON,
  checkers, tests, verification commands, and source/proof-owner references.
- Report an evidence completeness score without claiming correctness.

## Non-Goals

- No packet-specific schema.
- No checker execution.
- No correctness claim for the witnesses.
- No matrix-factorization-specific path assumptions.
