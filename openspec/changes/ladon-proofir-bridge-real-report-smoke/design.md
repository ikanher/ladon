# Design

## Declaration Row Derivation

`ladon.proofir_bridge.declaration_rows` should first prefer an explicit
`declaration_graph.declarations` table when present.

If the table is absent, it should derive declaration rows from current
clean-core fields:

```text
declaration_graph.edges keys
declaration_graph.chosen_roots
declaration_graph.top_fan_in[*].declaration
declaration_graph.top_fan_out[*].declaration
```

Rows derived this way carry:

```text
declaration
module
path, only when the declaration module is the analysis root module and the
      analysis root path is available
```

The derived rows do not invent source ranges or hashes.

## Join Semantics

Clean-core derived rows can support:

```text
exact_module_decl: medium confidence
basename_only: low confidence, warning only
unmatched: diagnostic
```

They do not support high-confidence `exact_source_hash_decl` unless a future
Ladon report includes path/hash rows.

## Quux Smoke Fixture

Add a compact fixture shaped like a real Quux clean-core report for:

```text
Quux.Semantics.ComplexQuadratic
```

The ProofIR bridge index uses real surface and claim ids from the Quux
quadratic ProofIR artifacts, but remains a compact bridge index rather than raw
ProofIR.
