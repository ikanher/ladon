## 1. Define The Protocol Before The Helper

- [x] 1.1 Add Python enums/dataclasses/validators for `ladon-lean-semantic-v1`, operations, request IDs, identities, frame variants, terminal counts, status, authority, and bounds.
- [x] 1.2 Specify `exact_expr_fingerprint_v1` and `search_shape_key_v1` encodings and add golden protocol fixtures before Lean implementation.

## 2. Implement Supervised Transport

- [x] 2.1 Add framed NDJSON request writing and incremental response collection through the existing process supervisor.
- [x] 2.2 Validate protocol/operation/request/module identity, frame order, duplicates, counts, limits, and terminal summary.
- [x] 2.3 Preserve validated prefixes as partial diagnostics while rejecting them for complete semantic publication.

## 3. Implement Lean Extraction

- [x] 3.1 Add `ladon_semantic_index_helper.lean` and load only the requested compiled module environment.
- [x] 3.2 Emit owned declarations, all leading binders, direct type/value dependencies, external symbols, structures, constructors, inherited/dependent fields, and source anchors.
- [x] 3.3 Implement versioned structural fingerprints and coarse search shapes without pretty-print/reparse authority.
- [x] 3.4 Emit module-end and summary counts and ensure imported declarations are not duplicated as locally owned rows.

## 4. Add Fixture And Failure Coverage

- [x] 4.1 Create the pinned compact Lean fixture with binder, dependency, structure, inheritance, source, and external-frontier cases.
- [x] 4.2 Test malformed frames, duplicate rows, wrong identities, missing summary, count mismatch, timeout, cancellation, process failure, and output cap.
- [x] 4.3 Assert every timeout/cancellation cleans up the full helper process group.

## 5. Verify The Packet

- [x] 5.1 Run Python fake-protocol tests, pinned Lean integration tests, process-tree/resource gates, compile/quality gates, strict validation, and `git diff --check`.
