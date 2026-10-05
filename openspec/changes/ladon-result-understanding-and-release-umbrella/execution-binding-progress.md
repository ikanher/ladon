# Historical execution binding progress — 2026-10-02

Live semantic resolution and stored check readers validate receipt selection mode
and CheckRun Lean executable identity against the original, input-owned canonical
environment. They inspect its recorded `options.toolchainContext`, including
required content identities and pin-content digest consistency. Unsupported,
malformed, duplicate-key, or contradictory metadata is rejected. The context
identity is a captured opaque digest: redacted environment values cannot be
reconstructed, and content consistency does not authenticate the producer.

Ambient preflight may select an elan launcher rather than the eventual Lean
binary. New environment artifacts separately capture that worker digest in
`options.observedLeanExecutableDigest`. CheckRun executable identity must match
the recorded worker. Explicit selection also requires equality with the selected
Lean identity. Older ambient records without this field retain binding only if
the selected identity itself matches the worker; an unknown launcher/worker
relation weakens stored binding to `none`.

Scratch and interrupted-batch receipts have an existing process contract: their
CheckRun records the selected executable, while the environment's runtime digest
belongs to an elaboration frame. The validator preserves that relation rather
than inventing another observed worker. A post-gate ambient scratch probe found
this scope mismatch; selected-context validation repaired it, and a maintained
real-Lean test now covers default ambient scratch and stored expansion. These
receipts retain partial process authority, including provisional observations.

Stored reads without independent environment/context evidence return binding
`none` with an explicit limitation. The shared receipt projection owner validates
the weakening; subsequent projections cannot escalate it. The original artifact
and receipt remain immutable, and other axes retain their reported meaning.
No current host paths, executable bytes, or Lean process are consulted on read.
Older context-free semantic fixtures remain useful compatibility controls.

CLI expansion resolves the registered environment and validates exact input
ownership. Dossier check/observation queries select environment artifacts through
declared content references inside their bounded queries. A larger population
test also exposed an existing per-artifact limitation lookup; that lookup now
uses one bounded query. Tests preserve canonical database bytes and account for
the existing disposable connection-local subject relation.

The first new contract suite failed 55 tests: existing live/dossier/CLI readers
missed binding contradictions, and the direct reader lacked the environment
argument and unbound fallback. Follow-up failures identified outdated positive
fixtures, a null fixture accidentally replaced with a valid context, scratch
subjects outside the public theorem selector, and the limitation lookup query
count. The initial full gate then found two real default CLI regressions caused
by conflating selected launcher and worker identities (1,993 tests passed).
Separate worker identity capture restored both cases; the focused real-Lean suite
passed 167 tests, and the expanded focused suite passed 317. The ambient scratch
repair passed 93 focused tests and 319 broader tests; the final process-role
check passed 124 tests. Each failed run and correction is retained in
[the run state](apply-run-state.json). Strict quality passes without new suppression.

The first isolated snapshot (`873e542`) passed 323 relevant installed tests on
each supported Python version and the required benchmark but failed the full
default-CLI gate. Snapshot `c6e74a9` passed 2,004 maintained tests and 29 installed
CLI contracts, then failed the additional ambient scratch probe. The final
snapshot is `7109c18`; it passed 335 relevant installed tests on each supported
Python version, 2,008 maintained tests and 29 installed CLI contracts through the
clean-candidate gate, and the required benchmark with 17/17 coverage and zero
correctness/stability failures. Strict quality, compilation/build,
distribution/resource, collection, and governance checks pass. Fresh real Lean runs
produced an explicit accepted candidate, explicit compiled scratch, and ambient
rejection. Stored expansion preserves canonical bytes and aggregate receipt
parity; the installed CLI rejects correctly rehashed selection swaps for all
three. Scratch remains partial process evidence. Fresh launcher-specific runs
also cover ambient candidate/scratch and their distinct selected/worker roles.

This completes the historical binding repair, not the full propagation or
monotonicity audit. Traversal quality and compatible complete upstream exits
remain open, so canonical claim-target integration stays gated. The result
umbrella is still 9/50 complete; quantitative understanding metrics stay deferred.
