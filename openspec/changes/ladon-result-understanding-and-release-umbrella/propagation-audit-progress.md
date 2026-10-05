# Receipt propagation audit — 2026-10-02

Prerequisite tasks 3.10 and 3.11 are complete for the supported receipt contract.
The [machine-readable audit](receipt-propagation-audit.json) binds twelve paths,
thirty source owners, and twenty-seven path-specific test files to isolated
candidate `5d57c77`. It covers live candidate/batch/scratch observations,
canonical storage, exact context and historical selection, stored expansion,
theorem dossiers, lineage, compact aggregates, weak/absent evidence, derivation
CLI queries, JSON/text rendering, and the native compatibility boundary.

The new composition corpus follows all 343 three-boundary paths for each of
nine representative receipt profiles: 3,087 paths and 9,261 edges. It checks
exact dimensions, identity agreement between equivalent transport routes,
unchanged source receipts, and 56 forbidden attempts to restore lost execution
binding. The existing corpus separately covers 1,029 factorized axis-pair and
projection decisions and 26,880 complete states. These are contract checks,
not an enumeration of every full-state parent/child pair or a formal proof.

All 749 selected installed tests pass on Python 3.11 and 3.12. The clean-candidate
gate passes 2,355 maintained tests and 29 installed CLI contracts, including
strict quality, compilation/build, distribution/resource, and collection parity.
Current installed readers also replay five previously captured real-Lean
candidate, scratch, and rejection roles, preserving exact source/stored/derived
identity relationships and rejecting rehashed selection contradictions. This is
a new reader replay over recorded observations, not a new target Lean execution.

The production/package bytes are identical to the previously qualified
`e0f3b04` wheel. Its benchmark and preflight-failure observations retain their
original candidate binding; this audit does not claim they were rerun. Exact
commands, results, hashes, and failed earlier attempts are in
[apply-run-state.json](apply-run-state.json).

Raw audit output remains an immutable source view. Native derivation APIs remain
structural; ordinary stored derivation CLI receipts separately report not-run
theorem checking. Fingerprint search provides candidate relations rather than
receipt authority. No new theorem-checking or producer-authenticity guarantee
is inferred from these boundaries.

The prerequisite umbrella advances to **39/76**. The result umbrella remains
**9/50** and its claim child **5/8**. Execution-context policy and secret
nonleakage qualification, complete child/integration/discovery exits, and
canonical claim integration remain pending. The user-selected matrix-factorization
exposition is now being exercised as qualitative external-project feedback;
quantitative understanding metrics remain deferred.
