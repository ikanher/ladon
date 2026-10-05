# Authority prerequisite progress — 2026-10-02

## Implemented behavior

Candidate checking and discovery accept `--require-isolation`. The current
trusted-repository Lean profile reports initializer isolation as absent, so
required-isolation requests fail with exit code 1 and
`target-isolation-unavailable` before executable preflight, target loading,
index access, output-file creation, or evidence publication. The same policy
rejects API requests at construction. Doctor accepts the option and reports
the requested policy without executing the target or running preflight.

The shared transition owner registers seven projection boundaries: live result,
canonical artifact, SQLite row, dossier, aggregate, JSON renderer, and text
renderer. SQLite and dossier projections cannot report live observations.
Aggregates can report derived, failed, or absent observations. Other authority
axes remain independently constrained. The legacy ProofIR authority/completeness
adapter delegates to this owner and accepts an explicit projection kind.

Canonical receipt validation now has one owner shared with semantic observation
closure. Receipt projection verifies shape and identity, preserves exact subjects
and historical binding, and changes the observation state for the requested
reader boundary. Stored semantic-artifact/check expansion exposes this reader
receipt beside the unchanged canonical artifact. Invalid receipt identity or
check/environment/authority ownership rejects the read.

## Verification and fixes to the harness

The factorized transition corpus exercises all 1,029 declared axis-pair and
projection decisions, plus all 26,880 combinations of evidence-state axes.
Independent adversarial assertions prohibit absent/ambient authority promotion,
freshness/environment promotion, and live observations at reader boundaries.
This is a factorized conformance corpus, not a claim to have individually run
every possible pair of full seven-axis states.

Installed checks use Python 3.11 and 3.12 with locked test dependencies, isolated
Python mode, the installed ordinary console, and no `PYTHONPATH`/`PYTHONHOME`.
Policy tests supply explicit tools that would leave a marker if preflight ran,
and check both output formats and all three semantic projections. Stored-reader
tests persist canonical artifacts, expand them through the console, check the
new reader receipt, and verify the registry's original bytes remain intact.

Fresh-candidate testing exposed three pre-existing gate issues:

- Lean security tests need compiled trusted fixture modules. The clean gate now
  explicitly builds its own tracked pinned fixture when Lake is available.
- Replacing HOME hid Rust's installed compiler/cache. The gate retains explicit
  or inferred Rust toolchain/cache locations, as it already does for Elan.
- A release test read an external sibling skill repository. It now requires all
  named commands in Ladon's own README and CLI documentation. External skill
  synchronization remains a separate upstream task.

A subsequent installed test invocation ran the documentation test from a
directory without README.md. The runner was corrected to use the isolated
candidate's root; its Python remains isolated and imports the installed package.
The run-state records failed attempts and their successful replacements.

The clean-candidate gate passed all 1,811 maintained tests plus 29 installed CLI
contracts and the requested schema-resource checks. Installed authority/search/
manifest suites passed 308 tests on each of Python 3.11 and 3.12. The required
installed Lean gate passed. Those checks cover core snapshot
`00ad58ea9b8de771935aedfa91348d2d1c02aaae`.

The existing portable benchmark required separate harness repairs:

- Pin report v2 and inventory scope, rather than inherit changed CLI defaults.
- Bypass source-index caching for equivalent-run comparisons; keep the Lean
  helper cache enabled for the independently checked cache matrix.
- Provide fake Lean as well as fake Lake for direct worker launches, and keep
  deterministic fixture controls in case-local files because worker environments
  intentionally strip arbitrary caller variables.
- Mutate Lake manifests as valid JSON while testing fingerprint invalidation.
- Normalize recorded resource wall time alongside phase/helper timing, preserving
  limits, outcomes, and other evidence in the byte comparison.
- Update the deprecated handwritten-promotion label to the existing target-owned
  policy. An added negative oracle requires legacy promotion to stay absent;
  the raw compatibility population checks remain intact.

Report/oracle regressions passed 43 tests, and oracle/finding regressions passed
25 tests. The required portable benchmark passed on snapshot
`9e4d2ef` with zero correctness failures, 17/17 coverage checks, all three stable
report cases, all five invalidation cases, and timeout/cancellation cleanup.
Installed report/oracle/finding tests passed 52 tests on each supported Python
version against the repaired wheel. The final clean-candidate gate passed on that repaired snapshot: 1,813 maintained
tests, 29 installed CLI contracts, distribution/resource checks, and collection
parity.
Budgets were preserved. These are engineering regression checks, not a new
understanding-metrics program or compatible full child exit receipts.

The verification snapshot is an isolated local Git repository. Its commits do
not alter the user's branch or index. Source and distribution identities,
commands, outcomes, and log hashes are recorded in `apply-run-state.json`.

## Remaining boundary

Upstream tasks 3.7, 3.8, and 3.13 are complete. The full authority child exit is
still open: receipt propagation and monotonic behavior across all dossier,
lineage, aggregate, and renderer owners need their declared integration checks.
The iterative slicer retains C-grade complexity, and its module still contains
a more complex solver; suppression removal is also unfinished.

Compatible full authority-safe and discovery receipts remain required before
canonical claim-target resolution. These repairs do not establish target
initializer isolation, kernel theorem authority, externally measured benefit,
or the umbrella's full completion. Quantitative understanding metrics remain
deferred by the user.

The next continuation implements the dossier and lineage reader slice described
in [reader progress](reader-progress.md); the remaining boundary above still
applies to full child completion.
