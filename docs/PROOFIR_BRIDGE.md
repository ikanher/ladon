# Ladon ProofIR Bridge

The first bridge slice is intentionally separate from Ladon core.

```bash
ladon-proofir-bridge \
  --ladon-report ladon-report.json \
  --proofir-index proofir-bridge-index.json \
  --out bridge-report.json
```

## Purpose

Ladon reports structural proof-architecture context.  ProofIR reports claim,
witness, projection, and nonclaim boundaries.  The bridge joins those views and
emits reviewer-facing diagnostics.

The bridge does not:

- prove theorem truth;
- promote ProofIR statuses;
- treat Ladon edges as proof dependencies;
- treat source-hash or source-range joins as proof correctness;
- import raw evolving ProofIR packets into Ladon core.

## Input Boundary

The bridge consumes a compact `proofir_bridge_index`, not raw ProofIR dialects.
ProofIR should own extraction and validation of the index.  Ladon only joins the
small fields needed for architecture review:

- surfaces;
- claims;
- witness endpoints;
- nonclaims;
- projection boundaries.

## Current Diagnostics

The MVP emits conservative diagnostics:

- `proofir.unattached_surface`;
- `proofir.witness_endpoint_without_declaration_join`;
- `proofir.nonclaim_attached_to_root`;
- `proofir.name_only_join_warning`;
- `proofir.packet_stale_source`;
- `proofir.malformed_bridge_index`.

## Trust Rule

Bridge output is review context only:

```text
Ladon structural context only; ProofIR statuses are quoted, not promoted.
```

Source-hash and source-range joins establish attachment confidence only. They
do not establish theorem truth, witness adequacy, artifact authority, or proof
correctness. Name-only joins are warning-only and never evidence.

## Clean-Core Ladon Reports

Lean-backed Ladon reports can include an explicit
`declaration_graph.declarations` table. The bridge prefers those rows and joins
ProofIR surfaces in this order:

1. exact declaration, source path, and source content hash;
2. exact declaration, source path, and source range;
3. exact declaration and module;
4. basename-only warning;
5. unmatched.

Older or derived reports may omit the table. In that case the bridge derives
fallback declaration rows from:

- `declaration_graph.edges`;
- `declaration_graph.chosen_roots`;
- `declaration_graph.top_fan_in`;
- `declaration_graph.top_fan_out`.

Those derived rows can support `exact_module_decl` joins at medium confidence.
They cannot support source-hash or source-range evidence unless the Ladon report
contains those fields explicitly.
