# Rejected context input progress — 2026-10-02

New exact-candidate rejection artifacts own a typed `local-context` subject and
declare it in their CheckRun inputs. The worker uses the existing context
constructor over its observed Lean locals. The shared observation contract
checks this independent ordered shape during live projection, stored expansion,
and theorem dossier reads. Rehashing a receipt cannot conceal a changed name,
type, order, or length. Ambiguous, undeclared, unowned, and malformed context
inputs are rejected. No new ProofIR family or wire version is introduced.

The validator uses the existing normalization and exact-context comparison.
Scratch caller-prefix semantics and provisional application observations are
unchanged. Older rejected artifacts with neither a context input nor an owned
context remain readable; their receipt context is not independently verified.
Read validation preserves canonical bytes and does not execute Lean.

The adversarial suite first reproduced 22 failed rejection expectations and
7 successful controls. After repair, the expanded focused suite passed 208
tests. The first quality check found a C-ranked context validator; extracting
typed row selection brought it within the existing limit without suppression.
The isolated implementation snapshot is `03884ec`. Its installed wheel passed
238 relevant tests on each supported Python version. A fresh real-Lean rejection
recorded the introduced `value : Nat` context; stored expansion preserved the
artifact, and both reader and installed CLI rejected a rehashed `value : Bool`
receipt. Exact commands, candidate/source/wheel identities, failed probes, and
verification outcomes are recorded in [the run state](apply-run-state.json).
The clean-candidate gate passed 1,910 maintained tests and 29 installed CLI
contracts, including strict quality, compilation/build, distribution/resource,
and collection checks. The required benchmark passed with 17/17 coverage and
zero correctness/stability failures. OpenSpec validation and status hygiene pass.

The historical execution-binding audit remains open. Canonical environment
payloads produced by the worker already contain `options.toolchainContext`,
including the recorded selection mode and executable content identities. Stored
readers currently retain the receipt's binding without comparing it to that
environment input. The next repair must use the historical, input-owned artifact,
handle older environments without this metadata explicitly, and preserve bounded,
set-oriented dossier queries. Comparing against the current host or invoking Lean
would not validate the historical observation.

Traversal quality and compatible complete upstream exits also remain open.
This scoped repair does not complete tasks 3.10/3.11 or enable canonical claim
target integration. Quantitative understanding metrics remain deferred.
