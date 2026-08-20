# Ladon ProofIR Bridge Real Report Smoke

## Problem

The first bridge MVP used synthetic Ladon reports with an explicit
`declaration_graph.declarations` table. Current clean-core Ladon reports expose
root declaration information through `edges`, `chosen_roots`, `top_fan_in`, and
`top_fan_out`, not a full declaration table.

The bridge should consume this real report shape before we ask reviewers for
feedback on a second implementation packet.

## Hypothesis

The bridge can derive conservative declaration rows from the existing clean-core
declaration graph and still join compact ProofIR surfaces by module and
declaration name.

This enables real Quux smoke reports without requiring raw ProofIR import into
Ladon core.

## Non-Goals

- No ProofIR raw dialect compiler inside Ladon.
- No source-hash replay for clean-core reports that do not include hashes.
- No Lean replay.
- No witness recomputation.
- No status promotion from Ladon structure.
