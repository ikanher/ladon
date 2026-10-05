# Final execution-environment binding — 2026-10-02

Candidate `ae4aaff91edb0b44bfee179bdac18bab4103b28c` freezes derived
`LEAN_PATH` before version inspection and uses the same environment for Git
source enumeration and bound direct-Lean execution. Preparation rejects a worker
repository different from the context's repository. Single, batch and scratch
checks reject library-root additions, removals and symlink retargets before or
after execution; the adapter does not amend an already-bound environment.

Git selection now uses the captured caller search path once. Its absolute path,
content identity, final environment digest and fallback policy are recorded.
Verification does not reread the host environment or reselect Git. Empty input
selects the recorded filesystem fallback, even when host Git is available.
Changed Git bytes and bounded process failures fail closed. Child Git errors
produce finite diagnostics without echoing output. A localized nonrepository
error that does not match the supported English prefix also fails closed.

The public context adds version 2 metadata for library roots and auxiliary
provenance. Environment values remain privately hashed. Historical records retain
their original identities and reading semantics. This does not bind all `.olean`
contents or Git configuration files, isolate target code, or complete an authority
child exit. See [execution policy](../../../docs/EXECUTION_ENVIRONMENT.md).

## Verification

- Fourteen new final-environment cases reproduce **12 failures and 2 passes**
  against the previous installed candidate `27b57a3`; all fourteen pass now.
- Twenty auxiliary-enumeration tests cover captured environment, executable
  mutation, explicit fallback, real Git exclusions, bounds and finite errors.
- **101 focused checks** and **267 installed checks on each of Python 3.11 and
  3.12** pass. The source-first review found no actionable issue in the three
  execution owners; this review does not substitute for the remaining exit gates.
- The required benchmark passes **17/17** cases with zero correctness or stability
  failures. Scoped Ruff, strict complexity/dead-code checks and compilation pass.
- Fresh ordinary installed commands with Lean 4.32.1 accept the fixture theorem
  and reject a nonexistent candidate. Compact JSON, canonical stored artifacts,
  SQLite, stored receipts and JSON/text expansion contain no injected secret
  values or arbitrary caller key names. Derived `LEAN_PATH` is an intentional
  recorded key. Both checks reference one deduplicated version 2 environment.
- The clean-candidate gate passes **2,406 maintained tests** and **29 installed
  CLI contracts**, strict quality, compilation, distribution/resource and
  collection checks.

The initial strict quality check found that the preparation function exceeded its
complexity limit. The compiled-module requirement check was extracted into a
small helper; the final strict check passes. The old external nonleakage probe
also rejected the newly legitimate derived `LEAN_PATH` key. Its corrected check
still rejects every injected value and every arbitrary key, while permitting the
derived key. A preliminary stored-context audit expected two environment rows;
the registry correctly deduplicates the two checks' identical environment.
These were checker/probe corrections, not Lean proof failures.

Raw commands, before/after output and logs are under
`/tmp/ladon-final-environment-i6ibcjuz`, with digests in
[apply-run-state.json](apply-run-state.json). The wheel is
`/tmp/ladon-isolation-authority-vetts2n2/dist-r20/ladon-0.2.0-py3-none-any.whl`.
This is an isolated local candidate; the user's Git index was not changed.

## Exposition baseline

All **127 frozen files** retain their hashes. All **nine expected cases on each
runtime** retain their outcomes; successful output bytes are unchanged. Exact
commands, package identities and capture hashes are in
[baseline-final-environment-comparison.json](baseline-final-environment-comparison.json).

The completed [fixed-epoch baseline](baselines/fixed-epoch-v1/README.md) remains
partial, model-authored correspondence evidence: 18 inventoried statements,
30 components, 11 linked and 19 unmapped. `result inspect` and `result guide`
remain unavailable baseline outcomes. Final environment binding makes future
checked evidence more precise; it does not improve those coverage results or
supply a new mathematical review.

## Roadmap boundary and next gate

Prerequisite tasks **3.1 and 3.2 are complete**, bringing that umbrella to
**40/76**. The result umbrella remains **9/50**, and its claim child **5/8**.
Task 3.5 remains open: promote the corrected installed nonleakage probe into a
maintained test, cover residual/attempt-log evidence, batch/discovery and scratch,
legacy ambient execution, and terminal failure diagnostics. Check captured
artifacts through renderers without needlessly rerunning Lean. Existing Git
redaction and filter-policy regressions need not be duplicated.

Compatible complete correctness, authority, integration and discovery exits still
precede canonical claim-target integration. Preserve this frozen baseline while
finishing those exits; then implement its component-level differences and dossier
requirements. No public release, capability promotion or full exit is authorized
by these task-scoped checks.
