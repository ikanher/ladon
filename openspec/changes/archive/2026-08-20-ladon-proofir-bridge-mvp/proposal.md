# Ladon ProofIR Bridge MVP

## Problem

Ladon reports structural proof-architecture signals, while ProofIR reports
claim, witness, projection, and nonclaim boundaries.  Today those views are
reviewed separately.

The bridge should join them without making Ladon a proof checker and without
putting raw evolving ProofIR dialects into Ladon core.

## Hypothesis

A separate optional tool can consume:

```text
ladon-report.json
proofir-bridge-index.json
```

and emit:

```text
bridge-report.json
reviewer cards
diagnostics
```

The bridge adds context and warnings only.  It must not establish theorem truth,
promote ProofIR status, or treat Ladon edges as proof dependencies.

## Non-Goals

- No raw ProofIR dialect import into Ladon core.
- No broad packet audit.
- No Lean replay.
- No witness recomputation.
- No natural-language semantic checking.
- No architecture scoring beyond a few conservative diagnostics.
