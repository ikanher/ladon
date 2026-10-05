# Stored theorem reader progress — 2026-10-02

The theorem dossier now joins native check runs through exact, owner-qualified
subject references and exposes a bounded `checks` section. Its match and parent
truncation accounting use the existing dossier section contract. Canonical check
receipts are validated against their check/environment/authority owner, projected
as stored, and rendered with the seven independent axes. Canonical artifact
bytes remain unchanged. Missing receipts remain null; malformed owners return an
operational `invalid-stored-evidence-receipt` diagnostic through the ordinary CLI.

Generic observations and native check runs remain separate sections. The dossier
query has its own weak receipt: reading stored evidence does not run a theorem
check. It does not combine candidate acceptance into acceptance of the dossier.

The receipt subject validator now recognizes two closed profiles. The original
application profile keeps exact module, candidate, goal, and ordered local
context. The stored-query profile keeps exactly query kind, theorem selector,
and optional source reference. Only theorem-evidence and theorem-lineage query
kinds are registered. Query subjects cannot acquire executed binding, an
accepted outcome, checker authority, exact environment matching, or check and
environment references. Complete checking is also prohibited by the state owner.
Old strict readers reject the new subject profile rather than reinterpret it.

Lineage query receipts identify the stored closure as `lineage:<existing-id>`.
This preserves supported opaque IDs without labelling them as digests. The
existing closure verifier supplies source freshness; source/configuration/
toolchain failures do not become environment-match claims. Dependency acquisition
retains its original authority vocabulary separately. Query receipts remain
none/not-run/not-assessed for checking; graph and summary projections become
derived. A missing closure stays absent. JSON/text transports revalidate through
the shared owner and text includes all dimensions and the exact receipt identity.
Compact semantic cards also validate their authority projection through that
owner and retain receipt identity in both LLM and review output.

Verification passed 181 focused tests, including 19 new adversarial and ordinary
console cases. A real Lean application receipt was reloaded through the native
dossier checks section. Installed wheels passed the same 181 tests on Python
3.11 and 3.12 with isolated Python, no PYTHONPATH/PYTHONHOME, and the installed
ordinary console. Additional detached console probes verified dossier JSON/text
parity and rehashed mismatched-owner rejection on both versions. The required
portable benchmark passed with zero correctness/stability failures and 17/17
coverage; cache and process controls also passed.

The implementation snapshot is `a173875`, an isolated local repository commit
that does not alter the user's branch or index. Commands, source/wheel identities,
failed attempts, logs, and successful replacements are recorded in
[the durable run state](apply-run-state.json). The clean-candidate gate passed 1,832 maintained tests, 29 installed CLI
contracts, strict quality, distribution/resource checks, and collection parity.

The full propagation task and authority child exit remain open. The next scoped
slice implements compact discovery and stored derivation CLI receipts; see
[aggregate progress](aggregate-progress.md). The final owner compatibility and
cross-owner monotonicity audit remains pending. Traversal quality and compatible full child exits
also remain prerequisites for canonical claim-target resolution. This slice
adds no kernel authority, initializer isolation, new understanding metrics, or
full umbrella completion claim.
