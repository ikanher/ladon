# ProofIR v3 umbrella proof state

Updated: 2026-08-10

## Current verdict

The ProofIR v3 architecture remains accepted as a strong alpha design. The r03 expert review requests changes before semantic freeze and keeps Rust on hold. It verified several genuine fixes, then reproduced eight P0 blockers and nine P1 hardening seams. Four exit classes previously recorded as green are now reopened as `partial`.

The umbrella task ledger is **22 complete / 32 total / 10 open**. The current closure slice is implemented and tested: all 25 adversarial vectors reject with frozen diagnostics; application identity includes ordered substitutions and typed local context; the worker emits a versioned universe policy and framed terminal metadata; the fingerprint registry is shared by worker/query code; child query sections propagate parent truncation and large slices use a connection-local relation; publication locks are kernel-held and ownership-safe; and the packet manifest rejects unadvertised files. The repository full suite is **1447 passed** and strict quality is green. Rust remains held.

r03 review evidence remains historical: Python compilation passed; clean packet-local collection failed with 10 import errors because dependencies and the native corpus fixture were omitted; a review-only compatibility overlay produced **49 passed, 3 skipped**; Lean replay was unavailable in the reviewer environment. The previous r04 archive is likewise historical and is not current-checkout evidence. The current checkout has **1447 passed**, strict quality is green, and umbrella OpenSpec validation passes. These observations still do not establish semantic freeze or Rust parity.

## Historical evidence retained

- The pre-review non-Rust suite observation was 1,352 passing tests with strict Python quality and OpenSpec validation green.
- The expert packet-local focused run reported 71 passing tests and 3 failures caused by excerpt omissions.
- The expert successfully validated and projected the supplied environment, claim, and binary-derivation corpus cases into a fresh SQLite database; integrity and foreign-key checks passed.
- The r03 reviewer verified qualified declaration identity, separate residual application acceptance, direct `TermElabM` goal elaboration without generated `sorry`, request-bound framing, typed incremental `checkRunRef` resolution, separated bounds, and improved durable publication.
- These observations support the alpha architecture. They do not establish the stronger semantic-freeze contract introduced by the review.

## Open blocker classes

1. `proofir-v3-typed-schema-and-corpus-hardening` (**green for the r03 scope**): all 25 language-neutral vectors, exact diagnostics, inventory linkage, batch rejection, and nonprojection gates pass.
2. `proofir-v3-declaration-and-application-identity` (**green for the current local-context scope**): declaration identity is fixed and candidate-application identity includes ordered substitutions, typed local declarations, dependencies, and context identity. Relevant-hypothesis minimization remains future work.
3. `proofir-v3-cross-artifact-resolution-and-query-contracts` (**green for the r03 scope**): persisted/incoming closure, registry, truncation truthfulness, portable large-set filtering, source-map identity fields, and focused parity gates pass.
4. `proofir-v3-lean-worker-framed-protocol` (**partial**): direct elaboration, framing, typed context, versioned universe policy, and Lean-owned name parsing pass; target initializer isolation remains open.
5. `proofir-v3-publication-bounds-and-portability` (**green for the r03 scope**): kernel-held locks, token/inode cleanup, concurrent conflict, integrity, bounds, and portability gates pass; broader crash/PID-reuse matrix remains open.
6. `proofir-v3-freeze-evidence-and-review-packet` (**partial**): the manifest validator is strict and the current source/tests are green, but command records and a newly regenerated extracted packet still need to be captured before expert disposition.
7. Secondary seams remain for O(database) incremental resolution, full aggregate-order vectors, target-initializer isolation, Lean-owned name parsing, and expert disposition.

## Required order

1. Make every nested typed model reject the r03 vectors and turn the inventory into executable corpus data.
2. Serialize Lean local context and bind ordered substitutions/context into application and step identity. **Complete for the current worker contract.**
3. Close every artifact-reference family, centralize fingerprint schemes, and repair bounded query accounting/portability.
4. Isolate target initializers, let Lean parse names, and freeze universe-closure semantics.
5. Make lock acquisition, stale recovery, and cleanup ownership-safe under deterministic races.
6. Produce an actual strong-manifest packet with exact command logs and clean extracted replay.
7. Obtain a new expert disposition; lift the Rust hold only if every required r03 finding is closed or explicitly accepted as nonblocking.

## Program nonclaims

- No legacy ProofIR schema, converter, or compatibility projection is required or planned.
- SQLite is a disposable project-local query projection, not canonical ProofIR.
- Checker observations, source attachments, and successful processes are not theorem truth.
- A navigation path is not a complete conjunctive proof slice.
- No Rust parity or semantic-freeze release is currently claimed.
- Quux is a separate research playground and is not inspected, executed, imported, or used for calibration.

## Next admissible action

Next admissible action is to isolate target initializers, capture immutable command/log provenance, regenerate the complete review packet, and request an expert blocker-by-blocker disposition. Do not begin or resume the Rust reference child.
