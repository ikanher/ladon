# Design

## Shape

The first slice is a separate command:

```bash
ladon-proofir-bridge \
  --ladon-report report.json \
  --proofir-index proofir-bridge-index.json \
  --out bridge-report.json
```

It is backed by a pure module:

```text
ladon.proofir_bridge
```

The pure function receives already-loaded dicts and returns a dict report.

## ProofIR Bridge Index

The bridge consumes a compact ProofIR index, not raw ProofIR packets.

Required rows:

```text
surfaces
claims
witnessEndpoints
nonclaims
projectionBoundaries
```

The index is assumed to be produced/checked by ProofIR.  Ladon only validates
the small bridge-index shape it needs.

## Join Confidence

The first confidence classes are:

```text
exact_source_hash_decl: high
exact_source_range_decl: high/medium depending on hash availability
exact_module_decl: medium
basename_only: low warning only
unmatched: diagnostic
```

The report always prints the match kind.

## First Diagnostics

```text
proofir.unattached_surface
proofir.witness_endpoint_without_declaration_join
proofir.nonclaim_attached_to_root
proofir.name_only_join_warning
proofir.packet_stale_source
```

Deferred:

```text
status_hotspot
prose_overclaim_near_kernel
ambiguous_claim_family
```
