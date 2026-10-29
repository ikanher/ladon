# Bounded exact JSON connection-job transport

The additive internal transport component is implemented and independently
reviewed. A full formal/authored history pair exceeding the ordinary 8 MiB
wire budget now crosses a supervised worker exactly within that budget. Task
2.2 remains open for the consuming connection/admission pipeline.

## Observable contract

`ladon.bounded_json_transport.pack_json` and `unpack_json` round-trip canonical
JSON objects through a separately versioned closed DAG wire format. Ordinary
strings, including nested JSON-looking history strings, remain opaque. There
are no theorem/profile/loss/name special cases and no new dependencies, caches,
CLI commands, native artifact types or database migrations.

Limits are independently enforced: wire 8 MiB, expanded canonical ASCII JSON
32 MiB, depth 272 (root depth zero), scalar/key UTF-8 bytes 1 MiB, unique DAG
nodes 100,000, edges 500,000, and expanded value occurrences 1,000,000. Configured
limits may only narrow the fixed profile. The 32 MiB decoded aggregate job is
separate from existing per-artifact limits and from the 12 GiB process-tree RSS
cap. Some valid JSON aggregates will not fit the wire limit and are rejected.

Encoder identity traversal checks cycles and computes expanded metrics before
expanded serialization. Decoder bounds bytes before parsing, then checks closed
shape, canonical serialization, scalar types, sorted unique keys, strict backward
integer references, unique nodes, reachability and canonical postorder. Bottom-up
expanded byte/depth/value metrics are checked before expansion; a tiny exponential
DAG cannot allocate an enormous tree. Expanded SHA verification streams tokens
before iterative materialization. Repeated references create fresh mutable
containers so mutation of one decoded owner cannot change another.

The codec preserves integers above 2^53, integer-versus-float types, finite
floating receipts, negative zero and valid Unicode. It does not grant native
schema validity, semantic admission, freshness or authenticated authorship.
Consumers must still validate all native envelopes and exact evidence owners.
Existing native validators still reject unsupported float/shape cases after
transport; their schemas and limits were not changed.

## Root-observed verification

- Frozen red suite first failed on the compiled module's explicit unsupported
  behavior, then passed after root implementation. No frozen assertion changed.
- 61 transport tests passed in 0.57 seconds, including 500 seeded generic
  roundtrips/deterministic encodings inside one test. Controls cover malformed
  schema/tags/refs, orphans/duplicates/order, forged size/digest, cycles, nonfinite
  values, preflight expansion bombs, alias isolation and strict limit types.
- Boundary controls accept exact lowered byte/node/edge/occurrence ceilings,
  accept default depth 272 and reject 273, accept a 1 MiB UTF-8 scalar and reject
  one byte more, check decoder key/scalar bounds, JSON escaping and byte admission
  before parsing. This does not claim exhaustive testing of every hard ceiling.
- 33 existing native history/record/CLI/ownership/persistence/cleanup tests passed
  in 135.48 seconds. Total scoped test count: 94; not a repository-wide pass.
- Ruff, scoped strict quality and compileall passed for both production modules
  and both test files. No test refactor or approval exception was needed.

The exact informed pair contained 9,197,980 expanded canonical bytes. Its wire
encoding has 7,929,713 bytes and 23,505 unique nodes. Root packed it, sent the
complete wire through a bounded subprocess, decoded/repacked it there, received
identical wire bytes, and compared the complete canonical expanded records.
Both original snapshot identities and opaque history strings were preserved.
The worker returned the wire rather than an oversized raw expanded response.

The entire qualification ran in 1.99 seconds, peaking at 136.60 MiB process-tree
RSS; packing took 0.48 seconds and the inner worker 0.94 seconds. It stayed under
a single declared 600-second/12 GiB/8 MiB outer supervision allowance, with no
resource stops or retries. `PAIR-WIRE.json`, receipts and scripts preserve the
measurement; this is cost evidence for one complete pair, not a universal
compression or performance guarantee.

## Independent review and custody

Luna-medium sidecars supplied red/falsification, implementation-route and
independent integrated code/evidence reviews on the canonical board (posts
1984–1997 onward). Workers ran no product tests/builds and edited no production
files. Root executed all checks. Final review found no concrete defect and
independently checked wire size/count/digest against the process receipt.

All 2,670 protected primary inputs, the previously qualified 24 runtime files,
the exact-goal helper, and all eight prior sealed evidence packets remain
unchanged. Adding these Python modules changes conservative prose implementation
identities as designed; saved root-aware prose histories need fresh replay.
Historical inspection retains its existing authority limits.

No original paper/formalization was edited; nothing was committed or pushed.

## Next consuming gate

Task 2.2 still needs a public connection request/result and orchestrator that
consumes the complete transported records, validates original/copy/import owners,
runs fresh formal admission and authored recognition, then uses the checked exact
goal constructor and independent replay under one absolute deadline/RSS/output
lease. Unrelated positive and wrong direction/carrier/set/constant/scope cases,
history/staleness/resource controls and informed route outcomes must qualify
that consumer before any native connection credit. This component grants no
native connection, formal semantic admission, source fidelity, falsity or
independent-discovery result. Child progress stays 4/6, parent 8/12.
