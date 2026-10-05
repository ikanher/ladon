# Discovery aggregate and derivation reader progress — 2026-10-02

Compact discovery views now project each visible candidate and scratch receipt
through the shared aggregate transition. Live or stored observations become
derived; the other six dimensions remain unchanged. Cards keep both the derived
receipt identity and original source identity, plus the existing exact
check/environment expansion references. Scratch cards retain all seven axes in
ordinary and minimal byte-budget views. Full canonical population validation
still precedes selection. Missing receipts stay missing, and coverage counts
retain failed and omitted candidates. No discovery-wide accepted operation is
inferred from successful children. Canonical observations remain unchanged.

Text cards display those same identities and dimensions, including separate
scratch observations. Exact subjects remain in canonical evidence for expansion;
compact transport does not shorten a subject and present it as a new receipt.

Stored derivation CLI readers expose a separate weak receipt. Its closed subject
profile is exactly query kind, content-owned artifact reference, and a digest of
the operation, owner, typed start/target references, and bounds. The lookup owner
must match validated content before traversal. Route, slice, and alternative
results remain structural: complete traversal does not mean a theorem check
ran. Their receipt has none binding, not-run outcome, and not-assessed checking
completeness, freshness, and environment matching. Invalid targets yield failed
observations. Receipt fields survive output-byte truncation; canonical database
bytes are unchanged. Native graph APIs retain their existing structural contract.

The isolated implementation snapshot is `5eb32a4`, which does not change the
user's branch or index. Verification outcomes, failed attempts, exact commands,
and source/wheel/log identities are recorded in [the run state](apply-run-state.json).
The focused suite passed 106 tests, and the installed wheel passed 162 relevant
tests on each supported Python version. The clean-candidate gate passed 1,852
maintained tests and 29 installed CLI contracts, including strict quality and
distribution/resource checks. The required benchmark passed with zero
correctness/stability failures and 17/17 coverage.

A detached installed CLI probe with actual pinned Lean binaries accepted the
fixture application and compiled its separate scratch example. Artifact
expansion verified live canonical receipts reload as stored and project to the
same derived receipt identities shown on compact cards. The scratch receipt
retained process-observation authority and partial completeness. An earlier
proxy-path probe was correctly rejected for executable identity mismatch; no
acceptance or authority was inferred from that failed attempt.

Full upstream tasks 3.10 and 3.11 remain open for the final owner compatibility
and monotonicity audit. Traversal quality and compatible complete authority-safe
and discovery child exits still gate canonical claim-target integration. This
slice does not establish kernel truth, initializer isolation, measured
understanding benefit, or umbrella completion. Quantitative metrics remain
deferred.
