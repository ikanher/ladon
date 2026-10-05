# Owned envelope validation repair — r52

Batch validation is **39% faster on installed Python 3.11 and 41% faster on
Python 3.12** over the frozen real-project population, with identical full
returned content and IDs. The repair also closes a custom-container ownership
bug: a hostile deepcopy hook could previously replace the returned payload
after its identity had been checked. Validation now owns the serialized tree,
checks that same tree, and freezes it without invoking caller copy hooks.
Duplicate serialized object keys are rejected rather than silently collapsed.

Candidate `50b907aae7a07b29e5b899d092319a136ec56fd4` passes **2,973 maintained
tests**, 29 installed CLI contracts, strict quality/package gates and **1,055
relevant installed tests on each supported runtime**. A private matrix Lean-source
fixture compiles the valid application and preserves the exact missing premise
in the nearby application. Live-project freshness and mutation failures remain
visible. This qualifies an ownership and cost repair; reader usefulness remains
unestablished, and umbrella accounting remains **33/50**.

## Why this repair and what changed

The [r51-candidate profile](profile-summary.json) showed 84 single-envelope
validations, 21 batch validations and substantial repeated shape, canonical
encoding and copy work. Delivery took about 21 instrumented seconds within a
51-second instrumented command. Cumulative function times overlap and are not
additive. The profiling command supplied the four already known candidates to
isolate delivery; it was not a fresh-reader or discovery experiment.

The [implementation diff](implementation.patch) changes only `proofir_v3.py`
and `proofir_v3_batch.py`. Each occurrence produces a detached plain JSON tree,
validates its semantics and parsed canonical profile, and retains its canonical
bytes for that request. Complete batch preflight and external-reference closure
still precede final declared-ID checks and returned artifacts. Duplicate
multiplicity, aggregate and individual bounds, conflict detection, order and
ordinary JSON diagnostics are preserved. The returned tree has immutable
containers; a later call observes changed input rather than a persistent cache.
The private final validator hashes the canonical envelope with its first sorted
`artifactId` member removed. That optimization operates only on the jointly
prepared, closed-key tree and encoding. Source/toolchain identity rechecks remain
unchanged.

[Package parity](package-parity.json) shows precisely those two runtime members
and wheel `RECORD` changed against qualified r51; 352 other archive members are
byte-identical. [Source parity](source-parity.json) confirms no build, dependency,
schema or tooling changes and 517 unchanged prior baseline files.

## Frozen red, implementation and independent audit

The initial ownership tests reproduced **eight failures** and preserved eleven
compatibility cases. Custom dictionary/list deepcopy hooks and serialization
hooks could undermine the relationship between validated and returned data. The
root froze those 19 cases, baseline owner modules, fixture hashes and the paired
performance harness before implementation. The unchanged baseline also failed
the separate 20% performance gate; its small self-comparison fluctuation is not
a correctness failure.

The green worker proposed snapshot reuse and a faster route, but root rejected
its final variant because it did not revalidate the parsed canonical profile.
Its roughly 51% timing is **not** the adopted result. The root alternative
retained that validation and passed the ownership cases and frozen timing gate.
The independent auditor then found duplicate serialized keys being silently
normalized by JSON parsing. Four additional tests failed on the first candidate
and were separately frozen; an object-pairs hook now rejects ambiguity before
semantic validation. The initial candidate and its successful package checks
remain [superseded evidence](superseded-candidate.json), not final qualification.

The final auditor found no remaining actionable defect in the assigned repair.
Root independently replayed its differential: 39 ordinary JSON cases across
seven artifact families, duplicate batches, malformed IDs/kinds/coverage and
numeric, depth and Unicode errors have identical content, identities and exact
exception diagnostics. The custom duplicate-key probes now reject. Final
qualification includes all **23 new ownership regression cases**. The
[portfolio](portfolio.jsonl) retains assignments, findings, adjudications and
worker lifecycle. [All 59 frozen paths](frozen-tests-verification.json) retain
their hashes. These finite checks are not an exhaustive proof for arbitrary
Python objects or platforms.

## Paired installed performance

The five-artifact population contains four check runs and an environment with
10,523 compiled-module entries, occupying 1,473,229 transport bytes. It was
captured through public registry artifact resolution from the exact emitted
references. Only its [summary and identities](artifacts-summary.json) are
exported; raw payloads remain in the operator cache. The [frozen harness](reproduce/benchmark_validate_batch.py)
verifies coherent baseline and candidate owners and population hashes, warms
both, then alternates five timed pairs. Only `validate_envelope_batch` is timed;
full returned content/ID comparison occurs outside the clock. No CI wall-clock
assertion was added.

| Installed runtime | Baseline median | Final median | Reduction |
| --- | ---: | ---: | ---: |
| CPython 3.11.15 | 0.1779 s | 0.1085 s | 39.02% |
| CPython 3.12.12 | 0.1484 s | 0.0874 s | 41.07% |

The [3.11 samples](py311-performance.json) and [3.12 samples](py312-performance.json)
retain exact source hashes and full vectors. Both return outcome digest
`40dcd9fcacb2618fe7374a57f50e0a9b746fdeafa7110a343b32cb11aa06a0c5`.
Qualification shared the host; the paired measurements establish this internal
cost gate rather than general productivity or an end-to-end speed comparison.

## Real-project checking and retained failures

The live matrix project rejected the old index as stale. A new isolated index
built successfully in 101.18 seconds, but subsequent discovery again rejected
stale sources. Public index inspection reports `stale-source`. Explicit replay
of the known four candidates accepted A in the elaborator, then scratch replay
failed closed with `source tree identity changed`. These failures were retained;
no freshness or source check was weakened, and no existing index was replaced.

To finish the bounded checking regression, root prepared a [private fixture](matrix-snapshot.json)
containing 9,882 copied Lean/build-configuration files (about 202 MiB), excluding
unrelated worktree artifacts. It consumes the original compiled `.lake` through
a symlink; dependencies remain subject to checker identity validation. No build
or source edit was requested in the neighboring project. This is a reduced,
trusted operator fixture, not a frozen copy of every project artifact.

| Explicit candidate replay on private fixture | Outcome | Time | Peak tree RSS |
| --- | --- | ---: | ---: |
| A | Propagation accepted and scratch compiled; three rejects | 18.77 s | 8.35 GiB |
| B | Exact boundary-gap residual; three rejects | 14.08 s | 8.35 GiB |

B retains `0 ≤ Mf.DP.fixedEpochCenterGap point h boundary`; it does not claim
the goal is false. All four mathematical projections—names, application terms,
discharged premises, substitutions, residuals and scratch statuses—match r51.
Source-location and full receipt identities are not compared across the private
root and live project. This replay supplies previously observed candidate names;
it does **not** renew the r51 automatic-discovery result or establish reader
benefit. All retained checking commands stayed below 8.36 GiB tree RSS under the
accepted 32 GiB cap. [Observations](observations.json) contain all seven commands,
including failures, exact contexts, streams and telemetry.

## Qualification and continuation

[Qualification](qualified-candidate.json) binds the final cache-local candidate,
wheel, commands, logs, installed origins and counts. The clean gate covers full
maintained tests, collection parity, strict quality, locked build, wheel/sdist
consistency, packaged schemas and installed CLI contracts. Separate isolated
3.11/3.12 tests cover the affected ProofIR, semantic, discovery, result and
toolchain consumers. [Final verification](verification.json) checks retained
bytes, candidate/runtime parity, frozen tests, historical baseline preservation
and root Git guards. Root HEAD and index are preserved; no global install,
archive or publication occurred.

Retained harness errors are distinct from product failures: the initial artifact
capture tried to canonically encode the whole transport list instead of its
native envelopes; a focused command named nonexistent test files; the auditor
initially selected an ambient old installed package; a whole-worktree fixture
copy encountered a live editor swap file; and report assembly used the wrong
residual field. Corrected operations are recorded separately. The incomplete
private copy was removed; no failed command is counted as a pass.

Next, return to the compact partial-applicability reader hypothesis on the
qualified core. Preserve the r49 attempt and same-guide comparison, require the
reader to retain mathematical scope and reach an explicit new-goal check, and
use fresh context without supplying the answer. Further result-layer features,
provenance and community profiles remain deferred until that task demonstrates
useful decisions. Quantitative reader metrics and human-cohort evaluation stay
separately deferred. Neither this repair nor operator checking closes another
umbrella task.
